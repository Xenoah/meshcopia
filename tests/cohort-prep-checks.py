import copy,importlib.util,json,tempfile,zipfile,stat
from pathlib import Path
spec=importlib.util.spec_from_file_location('prep','scripts/prepare-cohort-activation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
repo=Path('.').resolve();config=m.validate_config(json.loads((repo/m.CONFIG).read_bytes()))
def rejects(fn):
 try:fn()
 except (ValueError,AssertionError,KeyError):return
 raise AssertionError('Accepted invalid proof')
for c in config['cohorts']:
 m.verify_pins(repo,c)
 bad=copy.deepcopy(c);bad['inputs']['T-evidence.json']='0'*64;rejects(lambda:m.verify_pins(repo,bad))
run={'id':1,'run_attempt':1,'head_sha':'a'*40,'repository':{'full_name':m.REPO},'head_repository':{'full_name':m.REPO},'path':'wf','head_branch':'branch','event':'push','status':'completed','conclusion':'success'}
kwargs=dict(sha_='a'*40,name='F',run_id=1,attempt=1,workflow='wf',branch='branch');m.verify_run(run,**kwargs)
for key,value in [('conclusion','failure'),('head_sha','b'*40),('run_attempt',2),('path','other')]:
 bad=copy.deepcopy(run);bad[key]=value;rejects(lambda:m.verify_run(bad,**kwargs))
job={'id':2,'run_id':1,'run_attempt':1,'head_sha':'a'*40,'name':'verify','status':'completed','conclusion':'success','steps':[{'name':'required','conclusion':'success'}]};m.verify_job(job,run,2,'verify',['required'])
for value in ['failure','skipped']:
 bad=copy.deepcopy(job);bad['steps'][0]['conclusion']=value;rejects(lambda:m.verify_job(bad,run,2,'verify',['required']))
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder)/'model.zip';data=b'fbx';notice=b'notice';members={'model.fbx':{'bytes':3,'sha256':m.sha(data)},'LICENSE.txt':{'bytes':6,'sha256':m.sha(notice),'text':'notice'}}
 def write(extra=False,symlink=False):
  with zipfile.ZipFile(p,'w') as z:
   info=zipfile.ZipInfo('model.fbx');info.external_attr=(stat.S_IFLNK|0o777)<<16 if symlink else (stat.S_IFREG|0o644)<<16;z.writestr(info,data);z.writestr('LICENSE.txt',notice)
   if extra:z.writestr('preview.glb',b'not a consumer file')
 write();m.verify_zip(p,members)
 for kwargs in [{'extra':True},{'symlink':True}]:write(**kwargs);rejects(lambda:m.verify_zip(p,members))
 write();bad=copy.deepcopy(members);bad['LICENSE.txt']['text']='wrong';rejects(lambda:m.verify_zip(p,bad))
print('cohort immutable proofs and rejection cases passed')
