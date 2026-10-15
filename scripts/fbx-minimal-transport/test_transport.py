import copy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile
import transport as t


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        docs = t.f.ROOT / 'docs/fbx-minimal-verification'
        self.source = t.read(docs / 'source137.json'); self.expected = t.read(docs / 'expected137.json'); self.runtime = t.read(docs / 'runtime.json')
        for r in self.expected['models']: r.update(fbxBytes=3, fbxSha256=t.sha(b'fbx'), archiveBytes=3, archiveSha256=t.sha(b'zip'))
        self.a = {'schemaVersion': 1, 'reviewStatus': 'approved-for-transport', 'repository': t.REPO, 'tag': t.TAG, 'fCommit': '7'*40, 'runId': 12, 'runAttempt': 2, 'jobId': 56, 'workflowPath': t.WORKFLOW, 'workflowSha256': 'a'*64, 'payloadArtifactId': 34, 'payloadArtifactName': 'fbx-minimal137-'+'7'*40+'-12-2', 'payloadArtifactSha256': 'b'*64, 'qaArtifactId': 35, 'qaArtifactName': 'fbx-minimal-internal-qa-'+'7'*40+'-12-2', 'qaArtifactSha256': 'c'*64, 'inventorySha256': 'd'*64, 'qaSummarySha256': 'e'*64, 'qaRuntimeSha256': 'f'*64, 'qaPilotGateSha256': '0'*64, 'sourceInventorySha256': t.sha(t.canonical(self.source)), 'expectedManifestSha256': t.sha(t.canonical(self.expected)), 'runtimeSha256': t.sha(t.canonical(self.runtime)), 'releaseBodySha256': '1'*64, 'approvedIds': [r['id'] for r in self.source['models']]}
        # Runtime/source manifests bind exact checked-in bytes, whose JSON layout may differ.
        self.a['runtimeSha256'] = t.file_sha(docs / 'runtime.json'); self.runtime_raw = (docs / 'runtime.json').read_bytes()
        self.run = {'id': 12, 'run_attempt': 2, 'repository': {'full_name': t.REPO, 'id': 1}, 'head_repository': {'full_name': t.REPO, 'id': 1}, 'head_sha': self.a['fCommit'], 'head_branch': t.VERIFY_BRANCH, 'event': 'push', 'path': t.WORKFLOW, 'status': 'completed', 'conclusion': 'success'}
        names = ['Gate baseline, exact additive paths and reviewed minimal inputs before Blender', 'Fresh conversion, independent QA and strict two-entry packaging in pinned runtime', 'Store exact public payload review artifact, never publish', 'Store internal QA separately, never in consumer ZIPs or a release', 'Record exact payload and QA artifact envelopes']
        self.job = {'id':56,'run_id':12,'run_attempt':2,'head_sha':self.a['fCommit'],'name':'verify','status':'completed','conclusion':'success','steps':[{'name':n,'status':'completed','conclusion':'success'} for n in names]}
        self.files = {r['id']+'.fbx':b'fbx' for r in self.expected['models']}; self.files.update({r['filename']:b'zip' for r in self.expected['models']})
        self.inv = copy.deepcopy(t.expected_inventory(self.a,self.source,self.expected))

    def tearDown(self): self.temp.cleanup()
    def artifact_meta(self,prefix):
        return {'id':self.a[prefix+'ArtifactId'],'name':self.a[prefix+'ArtifactName'],'expired':False,'digest':'sha256:'+self.a[prefix+'ArtifactSha256'],'workflow_run':{'id':12,'head_sha':self.a['fCommit'],'head_branch':t.VERIFY_BRANCH,'repository_id':1,'head_repository_id':1}}
    def archives(self, extra=None, mutate=None):
        self.files['fbx-minimal-inventory.json'] = t.canonical(self.inv); self.a['inventorySha256']=t.sha(self.files['fbx-minimal-inventory.json'])
        payload=self.root/'payload.zip'; internal=self.root/'qa.zip'
        with zipfile.ZipFile(payload,'w') as z:
            for name,data in self.files.items():
                info=zipfile.ZipInfo(name)
                if mutate:info,data=mutate(info,data)
                z.writestr(info,data)
            if extra:z.writestr(*extra)
        with zipfile.ZipFile(internal,'w') as z:
            for name in t.qa.qa_names(self.a['approvedIds']):z.writestr(name,b'{}')
        self.a['payloadArtifactSha256']=t.file_sha(payload);self.a['qaArtifactSha256']=t.file_sha(internal)
        return payload,internal
    def unpack(self,materialize=True,**kw):
        payload,internal=self.archives(**kw)
        def plan(asset,note,**kwargs):return {'entries':[{'name':'LICENSE.txt'},{'name':asset.name+'.fbx'}]}
        with patch.object(t.f.packages,'make_plan',side_effect=plan),patch.object(t.f.packages,'verify_archive') as verify:
            result=t.unpack_payload(self.a,self.source,self.expected,payload,internal,self.root/'out',self.root,materialize)
            self.assertEqual(verify.call_count,137);return result
    def test_valid_approval(self):t.approval_check(self.a,t.canonical(self.source),t.canonical(self.expected),self.runtime_raw)
    def test_pending_approval(self):
        self.a['reviewStatus']='pending-review'
        with self.assertRaises(ValueError):t.approval_check(self.a,t.canonical(self.source),t.canonical(self.expected),self.runtime_raw)
    def test_same_qa_payload_artifact_rejected(self):
        self.a['qaArtifactId']=34
        with self.assertRaises(ValueError):t.approval_check(self.a,t.canonical(self.source),t.canonical(self.expected),self.runtime_raw)
    def test_extra_approval_field_rejected(self):
        self.a['skipQa']=True
        with self.assertRaises(ValueError):t.approval_check(self.a,t.canonical(self.source),t.canonical(self.expected),self.runtime_raw)
    def test_valid_run_job_both_artifacts(self):
        t.check_run(self.a,self.run);t.check_job(self.a,self.job)
        for prefix in ('payload','qa'):t.check_artifact(self.a,self.run,self.artifact_meta(prefix),prefix)
    def test_whole_run_failed(self):
        with self.assertRaises(ValueError):t.check_run(self.a,{**self.run,'conclusion':'failure'})
    def test_job_wrong_attempt(self):
        with self.assertRaises(ValueError):t.check_job(self.a,{**self.job,'run_attempt':3})
    def test_qa_upload_missing(self):
        self.job['steps'].pop(3)
        with self.assertRaises(ValueError):t.check_job(self.a,self.job)
    def test_qa_upload_failed(self):
        self.job['steps'][3]['conclusion']='failure'
        with self.assertRaises(ValueError):t.check_job(self.a,self.job)
    def test_qa_other_run(self):
        m=self.artifact_meta('qa');m['workflow_run']['id']=13
        with self.assertRaises(ValueError):t.check_artifact(self.a,self.run,m,'qa')
    def test_artifact_expired(self):
        m=self.artifact_meta('payload');m['expired']=True
        with self.assertRaises(ValueError):t.check_artifact(self.a,self.run,m,'payload')
    def test_artifact_fork(self):
        m=self.artifact_meta('qa');m['workflow_run']['head_repository_id']=9
        with self.assertRaises(ValueError):t.check_artifact(self.a,self.run,m,'qa')
    def test_exact_275_only(self):
        rows=self.unpack();self.assertEqual(len(rows),275)
        self.assertEqual({r['name'] for r in rows if r['name'].endswith('.json')},{'fbx-minimal-inventory.json'})
    def test_no_retained_media_for_review(self):self.unpack(False);self.assertEqual(list((self.root/'out').iterdir()),[])
    def test_no_public_qa(self):
        with self.assertRaises(ValueError):self.unpack(extra=('qa.json',b'{}'))
    def test_duplicate_name(self):
        with self.assertRaises(ValueError):self.unpack(extra=('fbx-minimal-inventory.json',b'{}'))
    def test_traversal(self):
        with self.assertRaises(ValueError):self.unpack(extra=('../private.json',b'{}'))
    def test_symlink(self):
        def change(i,d):i.external_attr=0o120777<<16;return i,d
        with self.assertRaises(ValueError):self.unpack(mutate=change)
    def test_unsupported_compression(self):
        def change(i,d):i.compress_type=zipfile.ZIP_BZIP2;return i,d
        with self.assertRaises(ValueError):self.unpack(mutate=change)
    def test_payload_hash_drift(self):
        self.files[self.a['approvedIds'][0]+'.fbx']=b'bad'
        with self.assertRaises(ValueError):self.unpack()
    def test_inventory_notice_drift(self):
        self.inv['models'][0]['notice']['text']+='bad'
        with self.assertRaises(ValueError):self.unpack()
    def test_nested_zip_validator_blocks(self):
        payload,internal=self.archives()
        with patch.object(t.f.packages,'make_plan',side_effect=ValueError('extra metadata')),self.assertRaises(ValueError):t.unpack_payload(self.a,self.source,self.expected,payload,internal,self.root/'out',self.root)
    def test_existing_tag_never_overwritten(self):
        class API:
            def json(self,*args,**kwargs):return {'id':1}
        with self.assertRaises(ValueError):t.absence(API())
    def test_only404_is_absence(self):
        class API:
            def json(self,path,*args,**kwargs):raise urllib.error.HTTPError(path,403,'denied',{},None)
        with self.assertRaises(ValueError):t.absence(API())
    def test_crosshost_auth_blocked(self):
        with self.assertRaises(ValueError):t.GitHub('unused').request('https://evil.invalid/')
    def test_download_size_bound(self):
        with self.assertRaises(ValueError):t.stream_file(io.BytesIO(b'long'),self.root/'out',3)
    def test_uncertain_create_not_retried(self):
        class API:
            count=0
            def json(self,path,method='GET',value=None):
                if method=='POST':self.count+=1;raise urllib.error.URLError('uncertain')
                raise urllib.error.HTTPError(path,404,'missing',{},None)
        api=API()
        with self.assertRaises(urllib.error.URLError):t.publish(api,b'reviewed',[],self.root,self.a)
        self.assertEqual(api.count,1)
    def test_uncertain_upload_not_retried(self):
        fc=self.a['fCommit']
        class API:
            count=0
            def json(self,path,method='GET',value=None):
                if method=='POST':return {'id':1,'draft':True,'tag_name':t.TAG,'target_commitish':fc}
                raise urllib.error.HTTPError(path,404,'missing',{},None)
            def upload(self,*args):self.count+=1;raise urllib.error.URLError('uncertain')
        api=API()
        with self.assertRaises(urllib.error.URLError):t.publish(api,b'reviewed',[{'name':'x'}],self.root,self.a)
        self.assertEqual(api.count,1)



class ExecutionRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.commit = '8' * 40
        self.workflow = '.github/workflows/release-fbx-minimal.yml'
        for name in (self.workflow, 'docs/fbx-minimal-transport/approval.json', 'scripts/fbx-minimal-transport/transport.py', 'scripts/fbx-minimal-transport/qa.py'):
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(name.encode())
        self.run = {'id': 123, 'run_attempt': 1, 'repository': {'full_name': t.REPO}, 'head_repository': {'full_name': t.REPO}, 'head_sha': self.commit, 'head_branch': t.BRANCH, 'path': self.workflow, 'event': 'push', 'status': 'in_progress', 'conclusion': None}
        self.job = {'id': 456, 'run_id': 123, 'run_attempt': 1, 'head_sha': self.commit, 'name': 'transport', 'status': 'in_progress', 'conclusion': None}
        self.jobs = {'total_count': 1, 'jobs': [self.job]}
        self.env = {'GITHUB_SHA': self.commit, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1'}
        self.requests = []
    def tearDown(self): self.temp.cleanup()
    def record(self):
        outer = self
        class API:
            def json(self, path):
                outer.requests.append(path)
                return outer.jobs if path.endswith('/jobs?per_page=100') else outer.run
        with patch.dict(t.os.environ, self.env, clear=True): return t.execution_record(self.root, API())
    def test_actual_execution_shape_hashes(self):
        record = self.record()
        self.assertEqual(set(record), {'commit', 'runId', 'runAttempt', 'jobId', 'workflowPath', 'workflowSha256', 'approvalSha256', 'adapterSha256'})
        self.assertEqual(record['jobId'], 456)
        self.assertEqual(record['adapterSha256'], {name: t.sha(name.encode()) for name in ('scripts/fbx-minimal-transport/transport.py', 'scripts/fbx-minimal-transport/qa.py')})
        self.assertEqual(record['approvalSha256'], t.sha(b'docs/fbx-minimal-transport/approval.json'))
        self.assertEqual(self.requests, ['/actions/runs/123/attempts/1', '/actions/runs/123/attempts/1/jobs?per_page=100'])
    def test_wrong_run_attempt(self):
        self.run['run_attempt'] = 2
        with self.assertRaises(ValueError): self.record()
    def test_wrong_R_branch(self):
        self.run['head_branch'] = t.VERIFY_BRANCH
        with self.assertRaises(ValueError): self.record()
    def test_wrong_R_workflow(self):
        self.run['path'] = t.WORKFLOW
        with self.assertRaises(ValueError): self.record()
    def test_fork_R(self):
        self.run['head_repository']['full_name'] = 'other/repo'
        with self.assertRaises(ValueError): self.record()
    def test_wrong_R_head(self):
        self.run['head_sha'] = '9'*40
        with self.assertRaises(ValueError): self.record()
    def test_completed_run_is_not_current_execution(self):
        self.run.update(status='completed', conclusion='success')
        with self.assertRaises(ValueError): self.record()
    def test_wrong_job_attempt(self):
        self.job['run_attempt'] = 2
        with self.assertRaises(ValueError): self.record()
    def test_job_id_boolean_rejected(self):
        self.job['id'] = True
        with self.assertRaises(ValueError): self.record()
    def test_two_jobs_rejected(self):
        self.jobs.update(total_count=2, jobs=[self.job, self.job])
        with self.assertRaises(ValueError): self.record()
    def test_wrong_job_name(self):
        self.job['name'] = 'verify'
        with self.assertRaises(ValueError): self.record()
    def test_wrong_job_commit(self):
        self.job['head_sha'] = '9'*40
        with self.assertRaises(ValueError): self.record()
    def test_invalid_environment_attempt(self):
        self.env['GITHUB_RUN_ATTEMPT'] = '01'
        with self.assertRaises(ValueError): self.record()

if __name__=='__main__':unittest.main()
