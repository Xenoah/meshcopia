"""F-only verifier. Never publishes. Missing reviewed inputs stop before Blender."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, re, shutil, struct, subprocess, sys, zipfile, io, zlib
BASE='4ab5342568a4227215b295b40a47c27698cc930a'
BRANCH='refs/heads/fbx/verify-existing137-v1'
PILOTS=('city-pruned-street-tree','city-vending-machine','commons-round-table','yokocho-bottle-keep-wall','yokocho-geometric-backbar','yokocho-noh-pavilion','atelier-lamp')
NAMES=('README.md','asset.json','CONVERSION.json','CONVERSION_NOTES.md','LICENSE.txt','ATTRIBUTION.txt','FILES.sha256')
HERE=Path(__file__).resolve().parent

def need(x,m):
 if not x:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def safe(s):
 need(isinstance(s,str) and s and not s.startswith('/') and '\\' not in s and ':' not in s and all(x not in ('','.','..') for x in s.split('/')) and not any(ord(c)<32 for c in s),'Unsafe path')
 return s
def git(repo,*args):
 env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
 env.update(GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
 return subprocess.check_output(['git','--no-replace-objects','-c','safe.directory='+str(repo),'-C',str(repo),*args],env=env)
def digest_file(p):
 need(p.is_file() and not p.is_symlink(),'Missing file or symlink');return sha(p.read_bytes())
def local(root,rel):
 p=root/safe(rel);need(p.resolve().is_relative_to(root.resolve()),'Path escapes root');need(not any(x.is_symlink() for x in [p,*p.parents] if x!=root.parent),'Symlink path');return p

def check_expected(e,inv):
 ids={r['id'] for r in inv['models']}
 need(e.get('schemaVersion')==1 and e.get('reviewStatus')=='final-reviewed' and e.get('baseCommit')==BASE and e.get('cohort')=='published137','Expected manifest not finalized/reviewed original137')
 need(e.get('pipelineSha256')=='89cdfcdcb1d84495c2fcecf34d944143a38137488dd62ef7b510a6b8576249ac','Expected recipe mismatch')
 rows=e.get('models',[]);need(len(rows)==137 and {r['id'] for r in rows}==ids,'Expected manifest must contain exact 137 distinct IDs')
 need(e.get('sourceInventorySha256')==sha(json.dumps(inv,ensure_ascii=False,indent=2).encode()+b'\n'),'Expected source inventory mismatch')
 byid={r['id']:r for r in inv['models']}
 for r in rows:
  need(r.get('sourceGlbSha256')==byid[r['id']]['sourceSha256'],'Expected source hash differs from original inventory')
  for k in ('fbxSha256','archiveSha256','reviewedQaSha256','sourceGlbSha256'):
   need(re.fullmatch('[0-9a-f]{64}',r.get(k,'')) is not None,'Missing expected '+k)
  need(type(r.get('fbxBytes')) is int and r['fbxBytes']>0 and type(r.get('archiveBytes')) is int and r['archiveBytes']>0,'Invalid byte sizes')
  need(set(r.get('packageInputs',{}))==set(NAMES),'Missing exact seven frozen package inputs')
  need(re.fullmatch('[0-9a-f]{64}',r.get('packageInputManifestSha256','')) is not None,'Missing package input manifest hash')
  for h in r['packageInputs'].values():need(re.fullmatch('[0-9a-f]{64}',h) is not None,'Invalid package input digest')
 return {r['id']:r for r in rows}

def validate_source_binding(row):
 identity=row['id'];need(re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',identity) is not None,'Invalid model ID')
 prefix='content/assets/'+identity+'/'
 need(row['sourceGLB']==prefix+'source/'+identity+'.glb' and row['assetMetadata']==prefix+'asset.json','Cross-model/noncanonical input path')
 files={x['path']:x for x in row['files']};need(len(files)==len(row['files']),'Duplicate source inventory entry')
 need(all(p==row['assetMetadata'] or p.startswith(prefix+'source/') for p in files),'Cross-model source entry')
 need(files[row['sourceGLB']]['sha256']==row['sourceSha256'] and files[row['assetMetadata']]['sha256']==row['metadataSha256'],'Convenience input hashes differ from complete inventory')

def validate_overlay_entry(raw,path):
 entries=raw.split(b'\0');need(len(entries)==2 and entries[-1]==b'','Missing/ambiguous overlay blob')
 header,name=entries[0].split(b'\t',1);mode,kind,oid=header.decode().split()
 need(mode=='100644' and kind=='blob' and name.decode()==path and re.fullmatch('[0-9a-f]{40}',oid) is not None,'Overlay symlink/gitlink/executable or path substitution')

def validate_lineage(chain,base,tip,expected_parent):
 need(chain and chain[-1][0]==tip,'Missing F lineage')
 last=base
 for commit,parents in chain:
  need(parents==[last],'Nonlinear or merged F history');last=commit
 need(chain[-1][1]==[expected_parent],'F exact reviewed parent differs')

def check_git(repo,inv,f,allowed,expected_parent):
 need(re.fullmatch('[0-9a-f]{40}',f) is not None,'Invalid F SHA')
 need(git(repo,'rev-parse','--is-shallow-repository').strip()==b'false','Shallow checkout prohibited')
 for args in [('config','--get','extensions.partialClone'),('config','--get-regexp','^remote\\..*\\.promisor$')]:
  try:
   git(repo,*args);raise ValueError('Partial/promisor repository prohibited')
  except subprocess.CalledProcessError as exc:need(exc.returncode==1,'Git config read failed')
 graft=git(repo,'rev-parse','--git-path','info/grafts').decode().strip();gp=repo/graft
 need(not gp.exists() or not gp.read_text().strip(),'Grafted history prohibited')
 need(git(repo,'rev-parse','HEAD').decode().strip()==f,'Checkout is not exact F')
 for path in allowed:
  safe(path);need(re.fullmatch('[A-Za-z0-9._/-]+',path) is not None,'Noncanonical approved path')
 need(re.fullmatch('[0-9a-f]{40}',expected_parent) is not None,'Exact expected parent required')
 git(repo,'merge-base','--is-ancestor',BASE,f)
 commits=git(repo,'rev-list','--reverse',BASE+'..'+f).decode().split()
 chain=[(c,git(repo,'show','-s','--format=%P',c).decode().split()) for c in commits]
 validate_lineage(chain,BASE,f,expected_parent)
 for c,parents in chain:
  edge=git(repo,'diff-tree','--no-commit-id','--name-status','-r','-z',parents[0],c).split(b'\0');edge=[x.decode() for x in edge if x]
  need(len(edge)%2==0,'Invalid edge diff')
  for status,path in zip(edge[::2],edge[1::2]):
   need(status in ('A','M') and path in allowed,'Unapproved repair edge or deletion/rename')
   for ref in ([parents[0],c] if status=='M' else [c]):
    validate_overlay_entry(git(repo,'ls-tree','-z',ref,'--',path),path)
 changes=git(repo,'diff-tree','--no-commit-id','--name-status','-r','-z',BASE,f).split(b'\0');changes=[x.decode() for x in changes if x]
 need(len(changes)%2==0,'Invalid diff records')
 need(set(changes[1::2])==allowed,'F changed-path set differs from exact reviewed list')
 for status,path in zip(changes[::2],changes[1::2]):need(status=='A' and path in allowed and (path.startswith('scripts/fbx-verification/') or path.startswith('docs/fbx-verification/') or path=='.github/workflows/verify-fbx.yml') and not any(x in path.lower() for x in ('approval','publication','release.json')),'Non-additive/unapproved F path: '+path)
 need(git(repo,'status','--porcelain','--untracked-files=no')==b'','Dirty CI checkout')
 need(not git(repo,'ls-tree','-r','--name-only',f,'--','docs/fbx-publication','fbx-publication-approval.json').strip(),'Publication marker forbidden')
 raw=git(repo,'ls-tree','-r','-z',BASE);tree={}
 for entry in raw.split(b'\0'):
  if not entry:continue
  head,path=entry.split(b'\t',1);mode,kind,oid=head.decode().split();path=path.decode();tree[path]=(mode,kind,oid)
 catalog=[]
 for path,(mode,kind,oid) in tree.items():
  if re.fullmatch(r'content/assets/[^/]+/asset\.json',path):
   need(mode=='100644' and kind=='blob','Unsafe metadata blob');m=json.loads(git(repo,'cat-file','blob',oid));catalog.append(m)
 public=[m for m in catalog if m.get('status')=='public'];need({m['id'] for m in public if m['type']=='model'}=={r['id'] for r in inv['models']} and len([m for m in public if m['type']=='texture'])==36,'Base public cohort differs')
 for row in inv['models']:
  validate_source_binding(row)
  prefix='content/assets/'+row['id']+'/source/'
  actual={p for p in tree if p.startswith(prefix)}
  need(actual=={x['path'] for x in row['files'] if x['path'].startswith(prefix)},'Incomplete pinned source directory')
  for item in row['files']:
   path=safe(item['path']);mode,kind,oid=tree[path];need(mode=='100644' and kind=='blob','Source must be ordinary blob')
   data=git(repo,'cat-file','blob',oid);need(len(data)==item['bytes'] and sha(data)==item['sha256'],'Pinned source hash mismatch')
 lock=git(repo,'show',BASE+':docs/archive-lock.json');need(sha(lock)==inv['protectedArchiveLockSha256'] and len(json.loads(lock)['archives'])==310,'Protected archive lock mismatch')
 return tree

def check_glb(data):
 need(data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2 and struct.unpack_from('<I',data,8)[0]==len(data),'Invalid GLB')
 n,t=struct.unpack_from('<II',data,12);need(t==0x4e4f534a,'Missing GLB JSON');g=json.loads(data[20:20+n])
 for row in g.get('buffers',[])+g.get('images',[]):need('uri' not in row or row['uri'].startswith('data:'),'External GLB dependency prohibited')


def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--preflight-only',action='store_true');a=p.parse_args();repo=a.repo.resolve();docs=repo/'docs/fbx-verification';inv=read(docs/'source137.json')
 expected=docs/'expected137.json'
 need(expected.is_file(),'PENDING: finalized reviewed expected137.json absent; no conversion attempted')
 rows=check_expected(read(expected),inv);runtime=read(docs/'runtime.json');allowed=set(read(docs/'allowed-f-paths.json'))
 need(os.environ.get('GITHUB_REPOSITORY')=='Xenoah/meshcopia' and os.environ.get('GITHUB_REF')==BRANCH and os.environ.get('GITHUB_EVENT_NAME')=='push','Only exact repository branch push is permitted')
 f=os.environ.get('GITHUB_SHA','');tree=check_git(repo,inv,f,allowed,read(docs/'workflow-policy.json')['expectedParent'])
 for name,h in runtime['recipe'].items():need(digest_file(HERE/name)==h,'Recipe hash mismatch')
 need(sha(json.dumps(runtime['recipe'],sort_keys=True,separators=(',',':')).encode())==runtime['pipelineSha256'],'Recipe aggregate mismatch')
 # Validate every fixed package input before any expensive conversion.
 for identity,row in rows.items():
  mp=local(docs,'package-inputs/'+identity+'/package-inputs.json');need(digest_file(mp)==row['packageInputManifestSha256'],'Package manifest differs');pm=read(mp);need(pm['originalGlbSha256']==row['sourceGlbSha256'] and pm['cohort']=='published137' and pm['archiveRevision']==3 and pm['id']==identity and pm['fbxSha256']==row['fbxSha256'] and pm['archiveSha256']==row['archiveSha256'] and set(pm['metadataFiles'])==set(NAMES),'Package manifest binding mismatch')
  for name,h in row['packageInputs'].items():need(digest_file(local(docs,'package-inputs/'+identity+'/'+name))==h,'Frozen package input mismatch')
 if a.preflight_only:print('F preflight passed; no Blender invoked');return
 need(sys.version.split()[0]==runtime['versions']['python'] and zlib.ZLIB_RUNTIME_VERSION==runtime['versions']['zlib'] and sys.flags.optimize==0,'Packaging Python/zlib/assertion runtime differs')
 need(not a.output.exists(),'Fresh output root required; never overwrite/reuse prior conversion')
 need(digest_file(Path('/usr/bin/blender'))==runtime['binarySha256'],'Blender binary mismatch')
 for path,h in runtime['exporterFiles'].items():need(digest_file(Path('/')/path)==h,'Exporter mismatch')
 a.output.mkdir(parents=True);out=a.output.resolve();(out/'private').mkdir();(out/'artifact').mkdir()
 subprocess.run(['/usr/bin/blender','-b','-noaudio','--factory-startup','--python-use-system-env','--python-exit-code','1','--python',str(HERE/'runtime_probe.py'),'--',str(docs/'runtime.json'),str(out/'private/runtime.json')],env={**os.environ,'PYTHONHASHSEED':'0'},check=True)
 actual_runtime=read(out/'private/runtime.json')
 from rebuild_fbx_zip import rebuild
 from verify_fbx_report import verify_report,public_cohort
 from verify_fixed_package import verify_fixed_package
 from deterministic_fbx import PINNED_SOURCES
 public=[];entries=[];byid={r['id']:r for r in inv['models']};ordered=list(PILOTS)+sorted(set(byid)-set(PILOTS))
 for identity in ordered:
  need(shutil.disk_usage(out).free>3_000_000_000,'Disk reserve reached; unfinished output preserved')
  row=byid[identity];ex=rows[identity];work=out/'private'/identity;work.mkdir();source=work/(identity+'.glb');data=git(repo,'cat-file','blob',tree[row['sourceGLB']][2]);check_glb(data);source.write_bytes(data)
  trial=work/'fresh';trial.mkdir()
  cmd=['/usr/bin/blender','-b','-noaudio','--factory-startup','--python-use-system-env','--python-exit-code','1','-t','4','--python',str(HERE/'convert_and_audit_fbx.py'),'--','--source',str(source),'--out',str(trial),'--expected-sha256',row['sourceSha256'],'--unique-image-paths','--normalize-materials','--deterministic']
  with (work/'execution.log').open('w') as log:subprocess.run(cmd,env={**os.environ,'PYTHONHASHSEED':'0'},stdout=log,stderr=subprocess.STDOUT,check=True)
  fbx=(trial/(identity+'.fbx')).read_bytes()
  if sha(fbx)!=ex['fbxSha256'] or len(fbx)!=ex['fbxBytes']:
   if identity==PILOTS[0]:
    from fbx_diagnostic import compare
    print('FBX_BOUNDED_DIAGNOSTIC '+json.dumps(compare(fbx,read(docs/'diagnostic-first-pilot.json')),sort_keys=True),flush=True)
   need(False,'Reviewed FBX bytes differ: '+identity)
  raw=(trial/'roundtrip-report.json').read_bytes();fresh={'id':identity,'qaSha256':sha(raw),'sourceGlbSha256':row['sourceSha256'],'fbxSha256':ex['fbxSha256'],'fbxBytes':ex['fbxBytes']}
  qa=verify_report(raw,fresh,data,fbx,runtime['recipe'],actual_runtime,PINNED_SOURCES,trial/'clean-reimport');need(qa['cleanImportEvidence']['extractedCopiesAvailable'],'Missing clean-import image bytes');public.append(qa)
  inputs={name:local(docs,'package-inputs/'+identity+'/'+name).read_bytes() for name in NAMES};blob=rebuild(docs/'package-inputs'/identity,trial/(identity+'.fbx'));need(sha(blob)==ex['archiveSha256'] and len(blob)==ex['archiveBytes'],'Reviewed ZIP bytes differ: '+identity)
  # Frozen conversion metadata describes reviewed LOCAL QA, not newly generated CI QA.
  meta=json.loads(git(repo,'cat-file','blob',tree[row['assetMetadata']][2]));verify_fixed_package(blob,identity,fbx,ex,inputs,meta,git(repo,'show',BASE+':LICENSE'),(docs/'CONVERSION_NOTES.template.md').read_bytes())
  for name,b in [(identity+'.fbx',fbx),(identity+'-fbx-v3.zip',blob)]:
   (out/'artifact'/name).write_bytes(b);entries.append({'path':name,'bytes':len(b),'sha256':sha(b)})
  if len(public)==7:dump(out/'private/pilot-gate.json',{'passed':True,'ids':list(PILOTS),'fCommit':f})
  print(json.dumps({'id':identity,'completed':len(public),'expected':137}),flush=True)
 need(len(public)==137,'Incomplete output')
 shared=public_cohort(public,set(byid));dump(out/'artifact/qa.json',shared);b=(out/'artifact/qa.json').read_bytes();entries.append({'path':'qa.json','bytes':len(b),'sha256':sha(b)})
 dump(out/'artifact/inventory.json',{'schemaVersion':1,'repository':'Xenoah/meshcopia','fCommit':f,'sourceCommit':BASE,'workflow':'.github/workflows/verify-fbx.yml','runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'expectedManifestSha256':digest_file(expected),'sourceInventorySha256':digest_file(docs/'source137.json'),'pipelineSha256':runtime['pipelineSha256'],'packageMetadataProvenance':'Fixed reviewed local QA; fresh CI QA is separately hash-bound in qa.json','models':137,'entries':sorted(entries,key=lambda r:r['path']),'inventoryExcludesOwnDigest':True})
 print('Verified all 137. Artifact only; no release, tag, main or Pages writes.')
if __name__=='__main__':
 try:main()
 except Exception as e:print('F_VERIFY_STOP: '+str(e),file=sys.stderr);sys.exit(1)
