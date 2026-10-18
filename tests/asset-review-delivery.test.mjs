import test from 'node:test';
import assert from 'node:assert/strict';
import {model} from './delivery-fixtures.mjs';
import {deliveryReadiness} from '../src/lib/delivery.mjs';
import {primaryDownload} from '../src/lib/downloads.mjs';
import {planBundle} from '../src/lib/batch-download.mjs';
import {spawnSync} from 'node:child_process';
test('unpublished review delivery is rejected by production and requires explicit reviewed mode',()=>{
 const a=model(),d=a.downloads.delivery;
 d.verification={state:'local-review-verified',publicationState:'unpublished-candidate'};
 const root=`https://xenoah.github.io/meshcopia/review-packages/${a.id}/${a.version}/`;
 d.archive.url=root+d.archive.filename;for(const file of d.files)file.url=root+file.name;
 assert.equal(deliveryReadiness(a).ready,false);assert.equal(primaryDownload(a),undefined);assert.throws(()=>planBundle([a]));
 assert.equal(deliveryReadiness(a,{allowReview:true}).ready,true);
 for(const mutate of [x=>x.archive.url='https://example.com/file.zip',x=>x.assetVersion='2.0.0',x=>x.files[0].fetch.url='https://github.com/file',x=>x.verification.releaseTag='fbx-minimal-v1.0.0',x=>delete x.verification.publicationState]){
  const invalid=structuredClone(a);mutate(invalid.downloads.delivery);assert.equal(deliveryReadiness(invalid,{allowReview:true}).ready,false);
 }
});
test('strict prep retry never accepts verification errors or exposes redirect queries',()=>{
 const code=`import contextlib,importlib.util,io,urllib.error
from pathlib import Path
spec=importlib.util.spec_from_file_location('retry','scripts/asset-revisions/prepare_existing_cohorts.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for status,expected_calls in [(500,3),(429,3),(403,1),(404,1)]:
 calls=[];output=io.StringIO()
 def fail(repo):
  calls.append(repo);raise urllib.error.HTTPError('https://release-assets.githubusercontent.com/path?secret=do-not-log',status,'transport',{},None)
 with contextlib.redirect_stdout(output):
  try:module.run(fail,Path('.'),delay=lambda _:None)
  except urllib.error.HTTPError:pass
  else:raise AssertionError('Transport failure was accepted')
 assert len(calls)==expected_calls and 'secret' not in output.getvalue()
calls=[]
def verification_error(repo):
 calls.append(repo);raise ValueError('hash differs')
try:module.run(verification_error,Path('.'),delay=lambda _:None)
except ValueError:pass
else:raise AssertionError('Verification failure was accepted')
assert len(calls)==1
calls=[]
def recovered(repo):
 calls.append(repo)
 if len(calls)==1:raise urllib.error.HTTPError('https://github.com/public',503,'transport',{},None)
 return 'full-verifier-success'
assert module.run(recovered,Path('.'),delay=lambda _:None)=='full-verifier-success' and len(calls)==2
`;
 const result=spawnSync('python3',['-c',code],{encoding:'utf8'});assert.equal(result.status,0,result.stderr);
});
