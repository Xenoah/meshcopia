"""Synthetic-only read-only prep boundary tests. No real QA or release claims."""
import hashlib,importlib.util,io,json,os,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('prep',Path(__file__).parents[1]/'scripts/prepare-fbx-minimal-activation.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def proof(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
class Prep(unittest.TestCase):
 def remote(self):
  f='a'*40;tag=p.TAG;models=[{'id':f'fixture-{i}','fbx':{'filename':f'fixture-{i}.fbx',**proof(b'FBX')},'archive':{'filename':f'fixture-{i}-1.0.0-fbx-minimal-1.0.0.zip',**proof(b'ZIP')}} for i in range(137)];inv={'models':models,'runId':'123','runAttempt':'2'};raw=json.dumps(inv).encode();a={'verificationCommit':f,'releaseId':5,'inventorySha256':p.sha(raw)}
  provenance={'fCommit':f,'runId':123,'runAttempt':2,'jobId':8};url=f'https://github.com/{p.REPO}/releases/tag/{tag}';release={'id':5,'tag_name':tag,'draft':False,'prerelease':False,'html_url':url};ref={'ref':'refs/tags/'+tag,'object':{'type':'commit','sha':f}};run={'id':123,'run_attempt':2,'head_sha':f,'head_branch':p.BRANCH,'event':'push','path':p.WORKFLOW,'status':'completed','conclusion':'success','repository':{'full_name':p.REPO},'head_repository':{'full_name':p.REPO}};job={'id':8,'run_id':123,'run_attempt':2,'head_sha':f,'status':'completed','conclusion':'success','steps':[{'name':'Store internal QA separately','conclusion':'success'}]}
  attachments=[];evidence_assets=[];items=[x[k] for x in models for k in ('fbx','archive')]+[{'filename':'fbx-minimal-inventory.json',**proof(raw)}]
  for n,item in enumerate(items):
   file_url=f'https://github.com/{p.REPO}/releases/download/{tag}/'+item['filename'];attachments.append({'id':n+1,'name':item['filename'],'size':item['bytes'],'digest':'sha256:'+item['sha256'],'browser_download_url':file_url,'state':'uploaded'});evidence_assets.append({'assetId':n+1,'name':item['filename'],'bytes':item['bytes'],'sha256':item['sha256'],'url':file_url,'anonymousReadback':True})
  evidence={'schemaVersion':1,'status':'anonymous-byte-readback-passed','repository':p.REPO,'tag':tag,'fCommit':f,'releaseId':5,'releaseUrl':url,'attachmentCount':275,'inventorySha256':p.sha(raw),'browserDownloadEvidence':'not-performed-by-transport','assets':evidence_assets,'provenance':provenance,'internalQaVerification':{},'transportExecution':{}}
  return a,evidence,inv,raw,release,ref,run,[job],attachments
 def execution(self):
  execution={'commit':'b'*40,'runId':234,'runAttempt':2,'jobId':345,'workflowPath':p.R_WORKFLOW,'workflowSha256':'c'*64,'approvalSha256':'d'*64,'adapterSha256':{key:'e'*64 for key in p.R_ADAPTERS}}
  run={'id':234,'run_attempt':2,'head_sha':'b'*40,'head_branch':'fbx/release-minimal137-v1','event':'push','path':p.R_WORKFLOW,'status':'completed','conclusion':'success','repository':{'full_name':p.REPO},'head_repository':{'full_name':p.REPO}}
  names=['Test exact artifact and fresh QA safeguards without external calls','Transport exact reviewed bytes and verify anonymous public readbacks','Preserve internal T evidence and consequential-step journal only']
  job={'id':345,'run_id':234,'run_attempt':2,'head_sha':'b'*40,'name':'transport','status':'completed','conclusion':'success','steps':[{'name':name,'status':'completed','conclusion':'success'} for name in names]}
  return execution,run,job
 def test_successful_durable_execution(self):p.validate_transport_execution_identity(*self.execution())
 def test_durable_execution_mutations(self):
  mutations=[lambda e,r,j:e.update(commit='x'),lambda e,r,j:e.update(runAttempt=True),lambda e,r,j:e.update(workflowPath='other'),lambda e,r,j:e['adapterSha256'].update(extra='e'*64),lambda e,r,j:r.update(conclusion='failure'),lambda e,r,j:r.update(status='in_progress'),lambda e,r,j:r.update(run_attempt=1),lambda e,r,j:r.update(head_branch='main'),lambda e,r,j:r.update(event='workflow_dispatch'),lambda e,r,j:r['head_repository'].update(full_name='fork/repo'),lambda e,r,j:j.update(id=1),lambda e,r,j:j.update(head_sha='c'*40),lambda e,r,j:j['steps'][1].update(conclusion='skipped'),lambda e,r,j:j['steps'].pop(),lambda e,r,j:j['steps'].append(j['steps'][0])]
  for n,mutate in enumerate(mutations):
   with self.subTest(case=n):
    args=self.execution();mutate(*args)
    with self.assertRaises(ValueError):p.validate_transport_execution_identity(*args)
 def test_durable_pins_code_approval_and_qa_result(self):
  from types import SimpleNamespace
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);execution,run,job=self.execution();provenance={'qaArtifactSha256':'1'*64,'qaSummarySha256':'2'*64};approval={**provenance,'fixtureApproved':True}
   contents={p.R_WORKFLOW:b'fixture workflow',p.R_APPROVAL:json.dumps(approval).encode(),**{name:('fixture '+name).encode() for name in p.R_ADAPTERS}}
   for name,data in contents.items():target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
   execution['workflowSha256']=p.sha(contents[p.R_WORKFLOW]);execution['approvalSha256']=p.sha(contents[p.R_APPROVAL]);execution['adapterSha256']={name:p.sha(contents[name]) for name in p.R_ADAPTERS}
   summary={'status':'exact-internal-qa-rechecked','models':137,**provenance,'freshImportedImageProof':'attested-by-exact-successful-F','rawReportAndContainerRechecked':True,'blenderRerunByTransport':False}
   evidence={'transportExecution':execution,'provenance':provenance,'internalQaVerification':summary}
   adapter=SimpleNamespace(PROVENANCE_FIELDS=tuple(provenance),approval_check=lambda a,*args:self.assertEqual(a,approval));reader=SimpleNamespace(json=lambda url:job if '/actions/jobs/' in url else run);pinned={'source':b'S','expected':b'E','runtime':b'R'}
   call=lambda:p.verify_transport_attestation(root,evidence,adapter,reader,pinned,'source','expected','runtime')
   with patch.object(p,'blob',side_effect=lambda repo,commit,name:contents[name]):
    self.assertEqual(call(),execution)
    for name in contents:
     (root/name).write_bytes(b'CHANGED')
     with self.assertRaises(ValueError):call()
     (root/name).write_bytes(contents[name])
    evidence['provenance']={**provenance,'qaSummarySha256':'3'*64}
    with self.assertRaises(ValueError):call()
    evidence['provenance']=provenance;summary['rawReportAndContainerRechecked']=1
    with self.assertRaises(ValueError):call()
 def test_no_implicit_mode_or_durable_artifact_fallback(self):
  with self.assertRaises(ValueError):p.prepare(Path('/unused'),verification_mode='fallback')
  with self.assertRaises(ValueError):p.prepare(Path('/unused'),Path('/unused.zip'),'durable-transport-attestation')
 def test_exact_275_remote_join(self):p.validate_remote(*self.remote())
 def test_remote_identity_and_readback_mutations(self):
  mutations=[lambda a:a[1].update(status='uploaded-only'),lambda a:a[1]['assets'][0].update(anonymousReadback=False),lambda a:a[4].update(draft=True),lambda a:a[5]['object'].update(sha='b'*40),lambda a:a[6].update(run_attempt=1),lambda a:a[6].update(head_branch='main'),lambda a:a[6]['head_repository'].update(full_name='fork/repo'),lambda a:a[7][0].update(conclusion='failure'),lambda a:a[8].pop(),lambda a:a[8][0].update(digest='sha256:'+'0'*64),lambda a:a[1].update(extra='unreviewed')]
  for n,mutate in enumerate(mutations):
   with self.subTest(case=n):
    args=self.remote();mutate(args)
    with self.assertRaises(ValueError):p.validate_remote(*args)
 def test_two_entries_and_exact_notice(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'test.zip';data=b'SYNTHETIC FBX';notice=b'Fixture notice\n';row={'id':'fixture','fbx':proof(data),'notice':{**proof(notice),'text':notice.decode()}}
   with zipfile.ZipFile(out,'w') as z:z.writestr('fixture.fbx',data);z.writestr('LICENSE.txt',notice)
   p.verify_two_entry_zip(out,row)
   row['notice']['text']='Changed'
   with self.assertRaises(ValueError):p.verify_two_entry_zip(out,row)
 def test_legacy_eight_entries_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'test.zip'
   with zipfile.ZipFile(out,'w') as z:
    for i in range(8):z.writestr('fixture/file'+str(i),b'fixture')
   with self.assertRaises(ValueError):p.verify_two_entry_zip(out,{'id':'fixture','fbx':proof(b'x'),'notice':proof(b'y')})
 def test_traversal_duplicate_and_symlink_rejected(self):
  for bad in ('../fixture.fbx','LICENSE.txt','link'):
   with self.subTest(name=bad),tempfile.TemporaryDirectory() as tmp:
    out=Path(tmp)/'bad.zip'
    with zipfile.ZipFile(out,'w') as z:z.writestr(bad,b'X');z.writestr('LICENSE.txt',b'Y')
    with self.assertRaises(ValueError):p.verify_two_entry_zip(out,{'id':'fixture','fbx':proof(b'X'),'notice':{**proof(b'Y'),'text':'Y'}})
 def test_atomic_receipt_and_no_clobber(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);receipt={'fixture':True};p.write_receipt(root,receipt);self.assertEqual(json.loads((root/p.RECEIPT).read_text()),receipt)
   with self.assertRaises(ValueError):p.write_receipt(root,{'replacement':True})
   self.assertEqual(json.loads((root/p.RECEIPT).read_text()),receipt)
 def test_partial_write_cannot_publish_receipt(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   with patch.object(p.os,'fsync',side_effect=OSError('fixture disk failure')):
    with self.assertRaises(OSError):p.write_receipt(root,{'fixture':True})
   self.assertFalse((root/p.RECEIPT).exists());self.assertEqual(list((root/'.cache').iterdir()),[])
 def test_atomic_link_failure_cannot_publish_receipt(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   with patch.object(p.os,'link',side_effect=OSError('fixture failure')):
    with self.assertRaises(OSError):p.write_receipt(root,{'fixture':True})
   self.assertFalse((root/p.RECEIPT).exists());self.assertEqual(list((root/'.cache').iterdir()),[])
 def test_stale_receipt_removed_even_empty_activation(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'docs').mkdir();(root/p.ACTIVATION).write_text(json.dumps({'schemaVersion':1,'repository':p.REPO,'activations':[]}));(root/'.cache').mkdir();(root/p.RECEIPT).write_text('STALE')
   result=p.prepare(root);self.assertEqual(result['verifiedModels'],0);self.assertFalse((root/p.RECEIPT).exists())
 def test_symlink_cache_never_deleted_or_followed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);outside=root/'outside';outside.mkdir();(outside/'fbx-minimal-verified.json').write_text('KEEP');(root/'.cache').symlink_to(outside,target_is_directory=True)
   with self.assertRaises(ValueError):p.prepare(root)
   self.assertEqual((outside/'fbx-minimal-verified.json').read_text(),'KEEP')
 def test_authenticated_path_allowlist(self):
  reader=p.ArtifactReader('SYNTHETIC-NOT-A-TOKEN')
  for bad in ['/releases/1','/actions/artifacts/1/zip?leak=x','https://evil.invalid/actions/artifacts/1','/actions/artifacts/01']:
   with self.assertRaises(ValueError):reader.request(bad)
  reader.clear();self.assertEqual(reader.token,'')
 def test_redirect_uses_fresh_headerless_request(self):
  class Response(io.BytesIO):
   code=302;status=200
   headers={'Location':'https://productionresultssafixture.blob.core.windows.net/blob?sig=SYNTHETIC-SIGNED-QUERY'}
  seen=[]
  class Opener:
   def open(self,request,timeout):
    seen.append(request)
    return Response(b'') if len(seen)==1 else Response(b'QA')
  with tempfile.TemporaryDirectory() as tmp,patch.object(p.urllib.request,'build_opener',return_value=Opener()):
   p.ArtifactReader('SYNTHETIC-TOKEN').download(7,Path(tmp)/'qa.zip',2,p.sha(b'QA'))
  self.assertEqual(seen[0].get_header('Authorization'),'Bearer SYNTHETIC-TOKEN')
  self.assertIsNone(seen[1].get_header('Authorization'))
  self.assertEqual(seen[0].full_url,p.API+'/actions/artifacts/7/zip')
 def test_transport_errors_redact_url_query_and_token(self):
  class Opener:
   def open(self,*args,**kwargs):raise OSError('https://private.invalid/?sig=SECRET token=SECRET')
  with patch.object(p.urllib.request,'build_opener',return_value=Opener()):
   with self.assertRaisesRegex(ValueError,'^Actions artifact transport failed$'):p.ArtifactReader('SECRET').request('/actions/artifacts/7')
 def test_token_removed_before_empty_prep(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'GITHUB_TOKEN':'SYNTHETIC','GH_TOKEN':'SYNTHETIC'},clear=False):
   root=Path(tmp);(root/'docs').mkdir();(root/p.ACTIVATION).write_text(json.dumps({'schemaVersion':1,'repository':p.REPO,'activations':[]}));p.prepare(root);self.assertNotIn('GITHUB_TOKEN',os.environ);self.assertNotIn('GH_TOKEN',os.environ)
 def test_artifact_digest_mismatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):p.stream_checked(io.BytesIO(b'BAD'),Path(tmp)/'blob',3,'0'*64)
 def test_duplicate_json_rejected(self):
  with self.assertRaises(ValueError):p.parse(b'{"k":1,"k":2}')
if __name__=='__main__':unittest.main()
