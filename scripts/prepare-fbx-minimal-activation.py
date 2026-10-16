#!/usr/bin/env python3
"""Dedicated same-job FBX prep. Token is confined to exact Actions reads.

Emits a LOCAL trust handoff, not portable/signed proof. CI must clear stale
receipts, execute this full verifier, then invoke token-free npm in this checkout.
Local --qa-artifact uses identical digest and QA verification, never a projection.
"""
import argparse, hashlib, importlib.util, json, os, re, stat, subprocess, sys, tempfile, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path
if not __debug__:raise RuntimeError('Optimized Python is prohibited')
REPO='Xenoah/meshcopia';API=f'https://api.github.com/repos/{REPO}'
TAG='fbx-minimal-v1.0.0';BRANCH='fbx/verify-minimal137-v1';WORKFLOW='.github/workflows/verify-fbx-minimal.yml'
ACTIVATION='docs/fbx-minimal-activation.json';RECEIPT='.cache/fbx-minimal-verified.json';BASE='4ab5342568a4227215b295b40a47c27698cc930a'
MAX_JSON=16*1024**2
R_WORKFLOW='.github/workflows/release-fbx-minimal.yml'
R_APPROVAL='docs/fbx-minimal-transport/approval.json'
R_ADAPTERS=['scripts/fbx-minimal-transport/transport.py','scripts/fbx-minimal-transport/qa.py']
MODES=('full-internal-qa','durable-transport-attestation')
CORE_INPUTS=[ACTIVATION,'scripts/prepare-fbx-minimal-activation.py','scripts/verify-minimal-activation.py','scripts/lib/fbx-minimal-downloads.mjs','src/lib/fbx-minimal-downloads.mjs','scripts/fbx-minimal-transport/qa.py','scripts/fbx-minimal-verification/common.py','docs/fbx-minimal-verification/source137.json','docs/fbx-minimal-verification/expected137.json','docs/fbx-minimal-verification/runtime.json']
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def parse(raw):
 def pairs(items):
  out={}
  for key,value in items:need(key not in out,'Duplicate JSON key');out[key]=value
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def file_hash(path):
 h=hashlib.sha256()
 with path.open('rb') as file:
  while chunk:=file.read(1024**2):h.update(chunk)
 return h.hexdigest()
def safe_local(repo,relative):
 need(type(relative) is str and not relative.startswith('/') and all(x not in ('','.','..') for x in relative.split('/')) and '\\' not in relative,'Unsafe local input')
 p=repo
 for part in relative.split('/'):p=p/part;need(not p.is_symlink(),'Symlink in input')
 need(p.is_file(),'Required input missing');return p
def git(repo,*args):
 env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_') and k not in ('GITHUB_TOKEN','GH_TOKEN')}
 env.update(GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
 return subprocess.check_output(['git','--no-replace-objects','-C',str(repo),*args],env=env,stderr=subprocess.DEVNULL)
def blob(repo,commit,path):need(re.fullmatch('[a-f0-9]{40}',commit),'Invalid commit');return git(repo,'show',commit+':'+path)
def module(repo,path,name,commit=None):
 target=safe_local(repo,path)
 if commit:need(target.read_bytes()==blob(repo,commit,path),'Verifier differs from pinned F')
 spec=importlib.util.spec_from_file_location(name,target);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
class ArtifactReader:
 """Auth never follows redirects, never accepts caller URLs, never logs secrets."""
 def __init__(self,token):need(type(token) is str and token,'Read-only Actions token missing');self.token=token
 def request(self,suffix):
  need(re.fullmatch(r'/actions/artifacts/[1-9][0-9]*(?:/zip)?',suffix),'Unexpected authenticated API path')
  req=urllib.request.Request(API+suffix,headers={'Authorization':'Bearer '+self.token,'User-Agent':'meshcopia-fbx-minimal-prep','Accept':'application/vnd.github+json'})
  try:return urllib.request.build_opener(NoRedirect).open(req,timeout=120)
  except urllib.error.HTTPError as e:
   if e.code==302:return e
   raise ValueError('Actions artifact request failed') from None
  except Exception:raise ValueError('Actions artifact transport failed') from None
 def metadata(self,id):
  with self.request(f'/actions/artifacts/{id}') as response:
   need(response.code==200,'Unexpected artifact metadata redirect');data=response.read(MAX_JSON+1)
  need(len(data)<=MAX_JSON,'Artifact metadata too large');return parse(data)
 def download(self,id,target,length,digest):
  with self.request(f'/actions/artifacts/{id}/zip') as response:
   need(response.code==302,'Expected isolated artifact redirect');location=response.headers.get('Location','')
  u=urllib.parse.urlsplit(location);host=u.hostname or ''
  need(u.scheme=='https' and not u.username and not u.password and u.port in (None,443) and (re.fullmatch(r'productionresultssa[a-z0-9]*\.blob\.core\.windows\.net',host) or host=='results-receiver.actions.githubusercontent.com'),'Unexpected artifact redirect host')
  # Fresh request has no Authorization header. No further automatic redirect.
  try:
   with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(location,headers={'User-Agent':'meshcopia-fbx-minimal-prep'}),timeout=180) as response:
    need(response.status==200,'Artifact byte response failed');stream_checked(response,target,length,digest)
  except Exception:raise ValueError('Artifact anonymous byte download failed') from None
 def clear(self):self.token=''
def stream_checked(response,target,length,digest):
 need(type(length) is int and 0<length<=2*1024**3,'Invalid artifact byte bound');total=0;h=hashlib.sha256()
 with target.open('xb') as out:
  while block:=response.read(1024**2):
   total+=len(block);need(total<=length,'Artifact exceeds pinned size');out.write(block);h.update(block)
 need(total==length and h.hexdigest()==digest,'Artifact bytes/digest mismatch')
def validate_activation(config):
 need(set(config)=={'schemaVersion','repository','activations'} and config['schemaVersion']==1 and config['repository']==REPO,'Invalid FBX activation')
 need(type(config['activations']) is list and len(config['activations'])<=1,'Only one minimal FBX activation is supported')
 if not config['activations']:return None
 a=config['activations'][0];need(set(a)=={'cohort','releaseTag','releaseId','verificationCommit','inventorySha256','transportEvidenceFile','transportEvidenceSha256'},'Invalid activation fields')
 need(a['cohort']=='published137' and a['releaseTag']==TAG and type(a['releaseId']) is int and a['releaseId']>0,'Activation identity mismatch')
 need(re.fullmatch('[a-f0-9]{40}',a['verificationCommit']) and all(re.fullmatch('[a-f0-9]{64}',a[k]) for k in ('inventorySha256','transportEvidenceSha256')),'Invalid activation digest')
 need(re.fullmatch(r'docs/fbx-minimal-publication/[A-Za-z0-9][A-Za-z0-9._-]*\.json',a['transportEvidenceFile']),'Unsafe T evidence path');return a

def validate_remote(a,evidence,inventory,raw,release,ref,run,jobs,assets):
 need(set(evidence)==set('schemaVersion status repository tag fCommit releaseId releaseUrl attachmentCount inventorySha256 browserDownloadEvidence assets provenance internalQaVerification transportExecution'.split()) and type(evidence['schemaVersion']) is int and evidence['schemaVersion']==1,'Invalid T evidence shape')
 need(evidence['browserDownloadEvidence']=='not-performed-by-transport','Unexpected browser evidence claim')
 need(evidence['releaseUrl']==release.get('html_url')==f'https://github.com/{REPO}/releases/tag/{TAG}','Release URL mismatch')
 need(evidence.get('status')=='anonymous-byte-readback-passed' and evidence.get('repository')==REPO and evidence.get('tag')==TAG,'T readback missing')
 need(evidence.get('fCommit')==a['verificationCommit'] and evidence.get('releaseId')==a['releaseId'] and evidence.get('inventorySha256')==a['inventorySha256'] and evidence.get('attachmentCount')==275,'T identity mismatch')
 need(release.get('id')==a['releaseId'] and release.get('tag_name')==TAG and release.get('draft') is False and release.get('prerelease') is False,'Release state mismatch')
 need(ref.get('ref')=='refs/tags/'+TAG and ref.get('object',{}).get('type')=='commit' and ref['object']['sha']==a['verificationCommit'],'Tag target mismatch')
 need(sha(raw)==a['inventorySha256'],'Inventory hash mismatch')
 for k in ('runId','runAttempt'):need(type(inventory.get(k)) is str and re.fullmatch('[1-9][0-9]*',inventory[k]),'Invalid run identity')
 need(run.get('id')==int(inventory['runId']) and run.get('run_attempt')==int(inventory['runAttempt']) and run.get('head_sha')==a['verificationCommit'] and run.get('head_branch')==BRANCH and run.get('event')=='push' and run.get('path')==WORKFLOW and run.get('status')=='completed' and run.get('conclusion')=='success','Exact F run not successful')
 need(run.get('repository',{}).get('full_name')==run.get('head_repository',{}).get('full_name')==REPO,'Run repository mismatch')
 provenance=evidence['provenance'];need(provenance['runId']==run['id'] and provenance['runAttempt']==run['run_attempt'] and provenance['fCommit']==a['verificationCommit'],'T run provenance mismatch')
 matching=[j for j in jobs if j.get('id')==provenance['jobId']];need(len(matching)==1,'Exact F job missing');job=matching[0]
 need(job.get('run_id')==run['id'] and job.get('run_attempt')==run['run_attempt'] and job.get('head_sha')==run['head_sha'] and job.get('status')=='completed' and job.get('conclusion')=='success','Exact F job failed')
 need(all(step.get('conclusion') in ('success','skipped') for step in job.get('steps',[])) and any(step.get('conclusion')=='success' and 'internal' in step.get('name','').lower() for step in job.get('steps',[])),'Internal QA upload step not proven')
 wanted={}
 for row in inventory['models']:
  for kind in ('fbx','archive'):
   f=row[kind];need(f['filename'] not in wanted,'Duplicate attachment');wanted[f['filename']]={'name':f['filename'],'bytes':f['bytes'],'sha256':f['sha256'],'url':f'https://github.com/{REPO}/releases/download/{TAG}/'+f['filename']}
 wanted['fbx-minimal-inventory.json']={'name':'fbx-minimal-inventory.json','bytes':len(raw),'sha256':sha(raw),'url':f'https://github.com/{REPO}/releases/download/{TAG}/fbx-minimal-inventory.json'}
 actual={x['name']:x for x in assets};saved={x['name']:x for x in evidence['assets']}
 need(len(assets)==len(actual)==len(evidence['assets'])==len(saved)==len(wanted)==275 and set(actual)==set(saved)==set(wanted),'Attachment set mismatch')
 for name,proof in wanted.items():
  r,s=actual[name],saved[name];need(type(r.get('id')) is int and r['id']>0,'Invalid attachment ID');need(r.get('state')=='uploaded' and r.get('size')==proof['bytes'] and r.get('digest')=='sha256:'+proof['sha256'] and r.get('browser_download_url')==proof['url'],'Remote attachment mismatch')
  need(s.get('assetId')==r.get('id') and s.get('anonymousReadback') is True and all(s.get(k)==v for k,v in proof.items()),'T asset identity mismatch')
 return provenance

def validate_transport_execution_identity(execution,run,job):
 need(set(execution)==set('commit runId runAttempt jobId workflowPath workflowSha256 approvalSha256 adapterSha256'.split()),'Invalid durable transport identity')
 need(type(execution['commit']) is str and re.fullmatch('[a-f0-9]{40}',execution['commit']),'Invalid R commit')
 for key in ('runId','runAttempt','jobId'):need(type(execution[key]) is int and execution[key]>0,'Invalid R execution ID')
 need(execution['workflowPath']==R_WORKFLOW and set(execution['adapterSha256'])==set(R_ADAPTERS),'Invalid R code paths')
 for checksum in [execution['workflowSha256'],execution['approvalSha256'],*execution['adapterSha256'].values()]:need(type(checksum) is str and re.fullmatch('[a-f0-9]{64}',checksum),'Invalid R code digest')
 need(run.get('id')==execution['runId'] and run.get('run_attempt')==execution['runAttempt'] and run.get('head_sha')==execution['commit'] and run.get('head_branch')=='fbx/release-minimal137-v1' and run.get('event')=='push' and run.get('path')==R_WORKFLOW and run.get('status')=='completed' and run.get('conclusion')=='success','Exact R execution not successful')
 need(run.get('repository',{}).get('full_name')==run.get('head_repository',{}).get('full_name')==REPO,'R repository mismatch')
 need(job.get('id')==execution['jobId'] and job.get('run_id')==execution['runId'] and job.get('run_attempt')==execution['runAttempt'] and job.get('head_sha')==execution['commit'] and job.get('name')=='transport' and job.get('status')=='completed' and job.get('conclusion')=='success','Exact R job not successful')
 required={'Test exact artifact and fresh QA safeguards without external calls','Transport exact reviewed bytes and verify anonymous public readbacks','Preserve internal T evidence and consequential-step journal only'}
 steps={x['name']:x for x in job.get('steps',[])}
 need(len(steps)==len(job.get('steps',[])) and required<=set(steps) and all(steps[n].get('status')=='completed' and steps[n].get('conclusion')=='success' for n in required),'R QA/readback/evidence step not successful')

def pin_transport_inputs(repo,evidence):
 execution=evidence['transportExecution'];commit=execution['commit']
 need(set(execution)==set('commit runId runAttempt jobId workflowPath workflowSha256 approvalSha256 adapterSha256'.split()) and execution['workflowPath']==R_WORKFLOW and set(execution['adapterSha256'])==set(R_ADAPTERS),'Invalid R proof input shape')
 paths={R_WORKFLOW:execution['workflowSha256'],R_APPROVAL:execution['approvalSha256'],**execution['adapterSha256']}
 for path,checksum in paths.items():need(sha(blob(repo,commit,path))==checksum and file_hash(safe_local(repo,path))==checksum,'Reviewed R code/approval differs from successful execution')
 return execution

def verify_transport_attestation(repo,evidence,transport,reader,pinned,src_path,exp_path,runtime_path):
 execution=pin_transport_inputs(repo,evidence)
 approval=parse(safe_local(repo,R_APPROVAL).read_bytes())
 transport.approval_check(approval,pinned[src_path],pinned[exp_path],pinned[runtime_path])
 need({key:approval[key] for key in transport.PROVENANCE_FIELDS}==evidence['provenance'],'Successful R approval differs from T/F bindings')
 run=reader.json(API+f"/actions/runs/{execution['runId']}/attempts/{execution['runAttempt']}")
 job=reader.json(API+f"/actions/jobs/{execution['jobId']}")
 validate_transport_execution_identity(execution,run,job)
 p=evidence['provenance']
 expected={'status':'exact-internal-qa-rechecked','models':137,'qaArtifactSha256':p['qaArtifactSha256'],'qaSummarySha256':p['qaSummarySha256'],'freshImportedImageProof':'attested-by-exact-successful-F','rawReportAndContainerRechecked':True,'blenderRerunByTransport':False}
 need(canonical(evidence['internalQaVerification'])==canonical(expected),'R internal QA attestation differs')
 return execution

def verify_two_entry_zip(path,row):
 wanted={row['id']+'.fbx':row['fbx'],'LICENSE.txt':row['notice']}
 with zipfile.ZipFile(path) as z:
  infos=z.infolist();need(len(infos)==2 and {i.filename for i in infos}==set(wanted),'Minimal FBX ZIP must have exact two flat files')
  for i in infos:
   need(i.orig_filename==i.filename and not i.is_dir() and not i.flag_bits&1 and i.compress_type in (0,8) and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG),'Unsafe ZIP member')
   p=wanted[i.filename];need(i.file_size==p['bytes'],'ZIP member size mismatch');b=z.read(i);need(len(b)==p['bytes'] and sha(b)==p['sha256'],'ZIP member bytes differ')
   if i.filename=='LICENSE.txt':need(b==p['text'].encode(),'ZIP notice text differs')

def write_receipt(repo,receipt):
 cache=repo/'.cache';cache.mkdir(exist_ok=True);need(not cache.is_symlink(),'Symlink cache prohibited');target=repo/RECEIPT
 need(not target.exists() and not target.is_symlink(),'Stale receipt was not cleared')
 fd,temp=tempfile.mkstemp(prefix='fbx-minimal-',suffix='.tmp',dir=cache)
 try:
  with os.fdopen(fd,'wb') as stream:stream.write(canonical(receipt)+b'\n');stream.flush();os.fsync(stream.fileno())
  os.link(temp,target)  # Atomic no-clobber publication on the same filesystem.
  try:
   directory=os.open(cache,os.O_RDONLY)
   try:os.fsync(directory)
   finally:os.close(directory)
  except Exception:
   target.unlink();raise
 finally:
  if os.path.exists(temp):os.unlink(temp)

def prepare(repo,qa_artifact=None,verification_mode='full-internal-qa'):
 need(verification_mode in MODES,'Explicit valid verification mode required')
 need(qa_artifact is None or verification_mode=='full-internal-qa','Durable mode cannot accept internal QA artifact')
 # Remove credential from the process environment before importing any helper or
 # spawning Git. It is used only by ArtifactReader for exact API endpoints.
 token=os.environ.pop('GITHUB_TOKEN','');os.environ.pop('GH_TOKEN',None)
 need(not (repo/'.cache').is_symlink(),'Symlink cache prohibited')
 target=repo/RECEIPT
 if target.exists() or target.is_symlink():
  need(not target.is_symlink() and target.is_file(),'Unsafe stale receipt');target.unlink()
 activation_bytes=safe_local(repo,ACTIVATION).read_bytes();a=validate_activation(parse(activation_bytes))
 if a is None:return {'verifiedModels':0,'scope':'empty activation; stale receipt invalidated'}
 need(git(repo,'rev-parse','--is-shallow-repository').strip()==b'false','Full Git history required')
 head=git(repo,'rev-parse','HEAD').decode().strip()
 ordinary=module(repo,'scripts/verify-minimal-activation.py','ordinary_minimal_activation');reader=ordinary.PublicReader()
 raw_t=safe_local(repo,a['transportEvidenceFile']).read_bytes();need(len(raw_t)<=MAX_JSON and sha(raw_t)==a['transportEvidenceSha256'],'T evidence digest mismatch');evidence=parse(raw_t)
 p=evidence['provenance'];f=a['verificationCommit']
 for key in ('runId','runAttempt','jobId','payloadArtifactId','qaArtifactId'):need(type(p.get(key)) is int and p[key]>0,'Invalid T provenance ID')
 for key,value in p.items():
  if key.endswith('Sha256'):need(type(value) is str and re.fullmatch('[a-f0-9]{64}',value),'Invalid T provenance digest')
 need(p['fCommit']==f and p['workflowPath']==WORKFLOW and p['inventorySha256']==a['inventorySha256'],'T pinned identity mismatch')
 # Establish fixed F inputs before executing the pure R QA verifier.
 src_path='docs/fbx-minimal-verification/source137.json';exp_path='docs/fbx-minimal-verification/expected137.json';runtime_path='docs/fbx-minimal-verification/runtime.json'
 pinned={}
 for path,key in ((src_path,'sourceInventorySha256'),(exp_path,'expectedManifestSha256'),(runtime_path,'runtimeSha256'),(WORKFLOW,'workflowSha256')):
  b=blob(repo,f,path);need(sha(b)==p[key] and safe_local(repo,path).read_bytes()==b,'Pinned F source mismatch');pinned[path]=b
 source,expected,runtime=[parse(pinned[x]) for x in (src_path,exp_path,runtime_path)]
 pins={**runtime['supportFiles'],**{'scripts/fbx-verification/'+k:v for k,v in runtime['recipe'].items()}}
 for path,digest in pins.items():need(sha(blob(repo,f,path))==digest and file_hash(safe_local(repo,path))==digest,'Pinned F support/recipe differs')
 common_path='scripts/fbx-minimal-verification/common.py';need(safe_local(repo,common_path).read_bytes()==blob(repo,f,common_path),'Pinned minimal F adapter differs')
 inputs=sorted(set([R_WORKFLOW,R_APPROVAL]+CORE_INPUTS+[a['transportEvidenceFile'],WORKFLOW,'scripts/fbx-minimal-transport/transport.py']+list(pins)))
 initial_inputs=[{'path':x,'sha256':file_hash(safe_local(repo,x))} for x in inputs]
 pin_transport_inputs(repo,evidence) # Check R helper bytes before importing them.
 sys.path.insert(0,str(repo/'scripts/fbx-minimal-transport'))
 transport=module(repo,'scripts/fbx-minimal-transport/transport.py','fbx_minimal_transport_adapter')
 need(set(p)==set(transport.PROVENANCE_FIELDS),'Unexpected T provenance shape')
 need(p['payloadArtifactId']!=p['qaArtifactId'],'QA and payload artifact must differ')
 for prefix,name in [('payload','fbx-minimal137'),('qa','fbx-minimal-internal-qa')]:need(p[prefix+'ArtifactName']==f"{name}-{f}-{p['runId']}-{p['runAttempt']}",'Artifact envelope name mismatch')
 transport.f.check_manifests(source,expected,pinned[src_path]);transport.check_source(repo,p,source,expected,runtime)
 execution=verify_transport_attestation(repo,evidence,transport,reader,pinned,src_path,exp_path,runtime_path)
 raw=reader.bytes(f'https://github.com/{REPO}/releases/download/{TAG}/fbx-minimal-inventory.json');inventory=parse(raw)
 need(raw==transport.canonical(transport.expected_inventory(p,source,expected)),'Concise inventory differs from exact F inputs')
 run=reader.json(API+f"/actions/runs/{p['runId']}/attempts/{p['runAttempt']}")
 job=reader.json(API+f"/actions/jobs/{p['jobId']}")
 release=reader.json(API+f"/releases/{a['releaseId']}");ref=reader.json(API+'/git/ref/tags/'+TAG)
 assets=[]
 for page in range(1,12):
  chunk=reader.json(API+f"/releases/{a['releaseId']}/assets?per_page=100&page={page}");need(type(chunk) is list,'Invalid asset page');assets+=chunk
  if len(chunk)<100:break
 else:raise ValueError('Attachment pagination overflow')
 validate_remote(a,evidence,inventory,raw,release,ref,run,[job],assets);transport.check_run(p,run);transport.check_job(p,job)
 need(sum(r['fbx']['bytes']+r['archive']['bytes'] for r in inventory['models'])<=3*1024**3,'Public payload cohort too large')
 with tempfile.TemporaryDirectory(prefix='meshcopia-fbx-minimal-prep-') as folder:
  work=Path(folder)
  if verification_mode=='durable-transport-attestation':
   token='';qa_file=None
  elif qa_artifact is None:
   auth=ArtifactReader(token)
   try:
    for prefix in ('payload','qa'):
     meta=auth.metadata(p[prefix+'ArtifactId']);transport.check_artifact(p,run,meta,prefix)
     if prefix=='qa':qa_meta=meta
    qa_file=work/'internal.zip';auth.download(p['qaArtifactId'],qa_file,qa_meta['size_in_bytes'],p['qaArtifactSha256'])
   finally:auth.clear();token=''
  else:
   token='';qa_file=qa_artifact.resolve();need(qa_artifact.is_file() and not qa_artifact.is_symlink(),'Local QA artifact must be regular');need(file_hash(qa_file)==p['qaArtifactSha256'],'Local retained QA artifact digest mismatch')
  fbxdir=work/'fbx';fbxdir.mkdir();projection=[];source_bindings=[]
  for row in inventory['models']:
   for kind in ('fbx','archive'):
    obj=row[kind];url=f'https://github.com/{REPO}/releases/download/{TAG}/'+obj['filename'];out=(fbxdir if kind=='fbx' else work)/obj['filename'];reader.file(url,out,obj['bytes'],obj['sha256'])
    if kind=='archive':verify_two_entry_zip(out,row);out.unlink()
   id=row['id'];metadata_path=f'content/assets/{id}/asset.json';metadata=blob(repo,BASE,metadata_path)
   need(safe_local(repo,metadata_path).read_bytes()==metadata,'Current metadata differs from pinned baseline')
   m=parse(metadata);need(m['id']==id and m['version']==row['version'] and m['status']=='public' and m['type']=='model','Current public source identity differs')
   prefix=f'content/assets/{id}/source/';tree=git(repo,'ls-tree','-r','-z',BASE,'--',prefix);sources=[]
   for item in tree.split(b'\0'):
    if not item:continue
    header,name=item.split(b'\t',1);path=name.decode();need(header.split()[:2]==[b'100644',b'blob'] and path.startswith(prefix),'Unsafe pinned source')
    data=blob(repo,BASE,path);need(safe_local(repo,path).read_bytes()==data,'Current source bytes differ');sources.append({'name':path[len(prefix):],'bytes':len(data),'sha256':sha(data)})
   sources.sort(key=lambda x:x['name']);need(transport.f.packages.source_listing(repo/prefix)==[x['name'] for x in sources],'Complete source listing differs')
   source_bindings.append({'id':id,'assetVersion':row['version'],'metadataSha256':sha(metadata),'sources':sources})
   projection.append({'id':id,'assetVersion':row['version'],'format':'FBX','packageVersion':'1.0.0','sourceCommit':BASE,'sources':sources,'direct':{**row['fbx'],'url':f'https://github.com/{REPO}/releases/download/{TAG}/'+row['fbx']['filename']},'archive':{**row['archive'],'url':f'https://github.com/{REPO}/releases/download/{TAG}/'+row['archive']['filename']},'notice':row['notice'],'selfContained':True,'limitations':list(sys.modules['verify_fbx_report'].LIMITS),'verification':{'state':'published-verified','releaseTag':TAG,'releaseId':a['releaseId'],'fCommit':f,'inventorySha256':a['inventorySha256']}})
  if verification_mode=='full-internal-qa':
   verified=transport.qa.verify_internal_qa(qa_file,p,source,expected,runtime,repo,fbx_directory=fbxdir)
   need(verified==evidence['internalQaVerification'],'Rechecked internal QA differs from T evidence')
 # Raw downloaded QA and FBX bytes have now been discarded. Nothing is written
 # into public/, src/data/ or consumer metadata by this credentialed prep step.
 need(initial_inputs==[{'path':x,'sha256':file_hash(safe_local(repo,x))} for x in inputs],'Verifier input changed during prep')
 receipt={'schemaVersion':1,'verificationMode':verification_mode,'createdBy':'same-job-fbx-minimal-prep/1','execution':{'runId':os.environ.get('GITHUB_RUN_ID'),'runAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'job':os.environ.get('GITHUB_JOB')},'head':head,'activationSha256':sha(activation_bytes),'inputs':initial_inputs,'projection':projection,'projectionSha256':sha(canonical(projection)),'sourceBindings':source_bindings,'provenance':{**p,'releaseId':a['releaseId'],'transportExecution':execution}}
 need(git(repo,'rev-parse','HEAD').decode().strip()==head and safe_local(repo,ACTIVATION).read_bytes()==activation_bytes,'Checkout changed during prep')
 write_receipt(repo,receipt)
 return {'verifiedModels':len(projection),'verificationMode':verification_mode,'anonymousAttachments':275,'receipt':RECEIPT,'scope':'same-checkout same-job trust handoff; not portable release proof'}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',required=True,type=Path);parser.add_argument('--qa-artifact',type=Path,help='Exact retained internal artifact only; identical full verifier runs');parser.add_argument('--verification-mode',choices=MODES,default='full-internal-qa');args=parser.parse_args()
 try:print(json.dumps(prepare(args.repo.resolve(),args.qa_artifact,args.verification_mode)))
 except Exception:
  # Network exceptions can contain signed URLs, query parameters or headers.
  # Do not print raw exception chains or externally supplied artifact contents.
  print('FBX_MINIMAL_PREP_STOP: verification failed; no new receipt accepted',file=sys.stderr);raise SystemExit(1) from None
if __name__=='__main__':main()
