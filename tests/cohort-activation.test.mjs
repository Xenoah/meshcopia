import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {loadCohortPolicy,validateCohortActivation,assertPublicationScope,originalSourceUrl,cohortHash,stable,cohortCoreInputs,cohortInputNames} from '../scripts/lib/cohort-policy.mjs';
import {validateCohortReceipt} from '../scripts/lib/cohort-downloads.mjs';
const policy=await loadCohortPolicy();
test('activation contains exactly original173 plus independently verified 251 and 30',()=>{
 assert.deepEqual(policy.config.cohorts.map(c=>[c.name,c.modelCount]),[['new251',251],['new30',30]]);assert.equal(policy.publicIds.length,454);assert.equal(new Set(policy.publicIds).size,454);
 const bad=structuredClone(policy.config);bad.cohorts.push(bad.cohorts[0]);assert.throws(()=>validateCohortActivation(bad),/Duplicate cohort/i);
 for(const change of [c=>c.modelCount=301,c=>c.verificationCommit='main',c=>c.publicPayloads=['archive'],c=>c.inputs={}]){const copy=structuredClone(policy.config);change(copy.cohorts[0]);assert.throws(()=>validateCohortActivation(copy));}
});
test('publication scope rejects omitted, extra and duplicate IDs',()=>{
 const assets=policy.publicIds.map((id,i)=>({id,status:'public',type:i<36?'texture':'model'}));assertPublicationScope(assets,policy);
 for(const bad of [assets.slice(1),[...assets,assets[0]],[...assets.slice(1),{...assets[0],id:'unknown'}]])assert.throws(()=>assertPublicationScope(bad,policy));
});
test('new previews remain on Pages and production originals use exact staged Git URLs',()=>{
 const row=policy.cohorts[0].source.models[0],asset={id:row.id,preview:'preview.glb'};
 assert.equal(originalSourceUrl(asset,{name:'preview.glb'},policy),`https://xenoah.github.io/meshcopia/assets/${row.id}/source/preview.glb`);
 assert.equal(originalSourceUrl(asset,{name:'mesh.stl'},policy),`https://raw.githubusercontent.com/Xenoah/meshcopia/${row.stageCommit}/content/assets/${row.id}/source/mesh.stl`);
 assert.equal(originalSourceUrl({id:'studio-chair',preview:'model.glb'},{name:'model.stl'},policy),'https://xenoah.github.io/meshcopia/assets/studio-chair/source/model.stl');
});
async function fixture(){
 const runtime=JSON.parse(await readFile('docs/fbx-minimal-verification/runtime.json'));
 const names=[...new Set([...cohortCoreInputs,...Object.keys(runtime.supportFiles),...Object.keys(runtime.recipe).map(k=>'scripts/fbx-verification/'+k),...policy.config.cohorts.flatMap(c=>cohortInputNames.map(n=>`docs/cohorts/${c.name}/${n}`))])].sort();
 const r={schemaVersion:1,createdBy:'same-job-cohort-prep/1',head:'test-head',activationSha256:cohortHash(policy.bytes),execution:{runId:null,runAttempt:null,job:null},inputs:await Promise.all(names.map(async path=>({path,sha256:cohortHash(await readFile(path))}))),projection:[],projectionSha256:'',sourceBindings:[],provenance:[]};
 for(const {activation:c,source} of policy.cohorts){
  const expected=JSON.parse(await readFile(`docs/cohorts/${c.name}/expected.json`)),evidence=JSON.parse(await readFile(`docs/cohorts/${c.name}/T-evidence.json`));
  r.provenance.push({name:c.name,releaseId:c.releaseId,fCommit:c.verificationCommit,transportExecution:evidence.transportExecution});
  for(const row of source.models){const out=expected.models.find(x=>x.id===row.id),root=`https://github.com/Xenoah/meshcopia/releases/download/${c.releaseTag}/`;
   r.sourceBindings.push({id:row.id,assetVersion:row.version,metadataSha256:row.metadataSha256,sources:row.sourceFiles});
   r.projection.push({id:row.id,sourceCommit:row.stageCommit,sources:row.sourceFiles,notice:row.fbxNotice,direct:{...out.fbx,url:root+out.fbx.filename},archive:{...out.fbxArchive,url:root+out.fbxArchive.filename},verification:{releaseTag:c.releaseTag,releaseId:c.releaseId,fCommit:c.verificationCommit,inventorySha256:c.inputs['cohort-inventory.json']}});
  }
 }
 r.projectionSha256=cohortHash(stable(r.projection));return r;
}
test('same-job receipt binds complete inputs, sources and exact immutable FBX outputs',async()=>{
 const receipt=await fixture(),options={head:'test-head',policy,execution:{runId:null,runAttempt:null,job:null}};await validateCohortReceipt(receipt,options);
 for(const mutate of [r=>r.head='stale',r=>r.execution.job='other',r=>r.inputs.pop(),r=>r.inputs[0].sha256='0'.repeat(64),r=>r.projection[0].direct.sha256='0'.repeat(64),r=>r.projection[0].archive.bytes++,r=>r.projection[0].notice.text='forged',r=>r.sourceBindings[0].sources=[],r=>r.projection.push(r.projection[0])]){
  const bad=structuredClone(receipt);mutate(bad);bad.projectionSha256=cohortHash(stable(bad.projection));await assert.rejects(validateCohortReceipt(bad,options));
 }
});
test('Python immutable proofs, failed jobs and malformed consumer ZIPs are rejected',()=>{
 execFileSync('python3',['tests/cohort-prep-checks.py'],{stdio:'pipe'});
});
