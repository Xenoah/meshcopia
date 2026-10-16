import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import qa

class QaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        docs=qa.f.ROOT/'docs/fbx-minimal-verification';self.source=qa.f.read(docs/'source137.json');self.expected=qa.f.read(docs/'expected137.json');self.runtime=qa.f.read(docs/'runtime.json')
        for row in self.expected['models']:row.update(fbxBytes=3,fbxSha256=qa.sha(b'fbx'))
        self.a={'fCommit':'7'*40,'runId':12,'runAttempt':2};self.ids=[r['id'] for r in self.source['models']]
        self.actual={'blender':'4.3.2','blenderBuildHash':'Unknown','blenderBinarySha256':self.runtime['binarySha256'],'python':'3.13.5 example','numpy':'2.2.4','zlib':'1.3.1','platform':'Linux-6.18-x86_64-with-glibc2.41'}
        self.cohort={'schemaVersion':1,'scope':'test','records':[{'id':i} for i in self.ids]}
        self.summary={'schemaVersion':1,'status':'fresh-fbx-and-minimal-packages-verified','fCommit':self.a['fCommit'],'sourceCommit':qa.f.BASE,'runId':'12','runAttempt':'2','fbxQa':self.cohort,'packages':[{'id':i} for i in self.ids]}
        self.pilot={'passed':True,'ids':list(qa.f.PILOTS),'fCommit':self.a['fCommit']}
        self.files={name:b'{}' for name in qa.qa_names(self.ids)};self.fbx=self.root/'fbx';self.fbx.mkdir()
        for i in self.ids:(self.fbx/(i+'.fbx')).write_bytes(b'fbx')
    def tearDown(self):self.temp.cleanup()
    def archive(self,extra=None,mutate=None):
        for name,value,key in (('qa.json',self.summary,'qaSummarySha256'),('runtime.json',self.actual,'qaRuntimeSha256'),('pilot-gate.json',self.pilot,'qaPilotGateSha256')):
            self.files[name]=qa.f.canonical(value);self.a[key]=qa.sha(self.files[name])
        archive=self.root/'qa.zip'
        with zipfile.ZipFile(archive,'w') as z:
            for name,data in self.files.items():
                info=zipfile.ZipInfo(name)
                if mutate:info,data=mutate(info,data)
                z.writestr(info,data)
            if extra:z.writestr(*extra)
        self.a['qaArtifactSha256']=qa.file_sha(archive);return archive
    def verify(self,**kw):
        archive=self.archive(**kw)
        with patch.object(qa,'public_cohort',return_value=self.cohort),patch.object(qa,'verify_model') as check:
            result=qa.verify_internal_qa(archive,self.a,self.source,self.expected,self.runtime,self.root,fbx_directory=self.fbx)
            self.assertEqual(check.call_count,137);return result
    def test_exact414_and137_model_checks(self):self.assertEqual(self.verify()['models'],137)
    def test_extra_internal_file_rejected(self):
        with self.assertRaises(ValueError):self.verify(extra=('unexpected.log',b'x'))
    def test_duplicate_internal_file_rejected(self):
        with self.assertRaises(ValueError):self.verify(extra=('qa.json',b'{}'))
    def test_missing_internal_file_rejected(self):
        self.files.pop(self.ids[0]+'/receipt.json')
        with self.assertRaises(ValueError):self.verify()
    def test_internal_symlink_rejected(self):
        def change(i,d):i.external_attr=0o120777<<16;return i,d
        with self.assertRaises(ValueError):self.verify(mutate=change)
    def test_internal_wrong_run(self):
        self.summary['runAttempt']='1'
        with self.assertRaises(ValueError):self.verify()
    def test_internal_wrong_f(self):
        self.summary['fCommit']='0'*40
        with self.assertRaises(ValueError):self.verify()
    def test_wrong_runtime(self):
        self.actual['zlib']='1.3.2'
        with self.assertRaises(ValueError):self.verify()
    def test_duplicate_root_model(self):
        self.summary['packages'][1]['id']=self.ids[0]
        with self.assertRaises(ValueError):self.verify()
    def test_integer_true_pilot_rejected(self):
        self.pilot['passed']=1
        with self.assertRaises(ValueError):self.verify()
    def test_changed_raw_fbx_rejected(self):
        (self.fbx/(self.ids[0]+'.fbx')).write_bytes(b'bad')
        with self.assertRaises(ValueError):self.verify()
    def test_internal_archive_digest(self):
        archive=self.archive();self.a['qaArtifactSha256']='0'*64
        with self.assertRaises(ValueError):qa.verify_internal_qa(archive,self.a,self.source,self.expected,self.runtime,self.root,fbx_directory=self.fbx)
    def test_summary_digest(self):
        archive=self.archive();self.a['qaSummarySha256']='0'*64
        with self.assertRaises(ValueError):qa.verify_internal_qa(archive,self.a,self.source,self.expected,self.runtime,self.root,fbx_directory=self.fbx)
    def test_choose_one_provider(self):
        with self.assertRaises(ValueError):qa.verify_internal_qa(self.root/'none',self.a,self.source,self.expected,self.runtime,self.root)
    def verification(self):return {'entryCount':2,'payloadBytes':10,'exactAllowlist':True,'payloadHashesVerified':True,'cleanExtractionVerified':True,'dependencyClosureVerified':True,'applicationImportTested':False}
    def test_strict_two_entry_receipt(self):qa.check_verification(self.verification(),10)
    def test_integer_true_receipt_rejected(self):
        for key in ('exactAllowlist','payloadHashesVerified','cleanExtractionVerified','dependencyClosureVerified'):
            v=self.verification();v[key]=1
            with self.subTest(key=key),self.assertRaises(ValueError):qa.check_verification(v,10)
    def test_no_fake_application_import_claim(self):
        v=self.verification();v['applicationImportTested']=True
        with self.assertRaises(ValueError):qa.check_verification(v,10)
    def materialization(self):
        return {'images':[{'relativePath':'textures/x.png','bytes':3,'sha256':qa.sha(b'png'),'source':'actual-clean-import-bpy-packed-image'}],'count':1,'noPixelReencoding':True,'importerPackedBytesMaterializedByValidationWrapper':True,'wrapperSha256':self.runtime['supportFiles']['scripts/fbx-verification/materialize_imported_images.py']}
    def report(self):return {'container':{'embeddedImages':[{'relativeFilename':'textures/x.png','embeddedBytes':3,'sha256':qa.sha(b'png')}]}}
    def test_materialized_actual_image_closure(self):qa.check_materialization(self.materialization(),self.report(),self.runtime)
    def test_wrong_wrapper_rejected(self):
        m=self.materialization();m['wrapperSha256']='0'*64
        with self.assertRaises(ValueError):qa.check_materialization(m,self.report(),self.runtime)
    def test_integer_true_materialization_rejected(self):
        m=self.materialization();m['noPixelReencoding']=1
        with self.assertRaises(ValueError):qa.check_materialization(m,self.report(),self.runtime)
    def test_synthetic_embedded_bytes_not_live_proof(self):
        m=self.materialization();m['images'][0]['source']='extracted-by-fbx-parser'
        with self.assertRaises(ValueError):qa.check_materialization(m,self.report(),self.runtime)
    def test_missing_live_image_rejected(self):
        m=self.materialization();m['images']=[];m['count']=0
        with self.assertRaises(ValueError):qa.check_materialization(m,self.report(),self.runtime)
    def test_wrong_live_image_hash_rejected(self):
        m=self.materialization();m['images'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):qa.check_materialization(m,self.report(),self.runtime)
    def test_duplicate_json_rejected(self):
        with self.assertRaises(ValueError):qa.json_bytes(b'{"id":1,"id":2}')

if __name__=='__main__':unittest.main()
