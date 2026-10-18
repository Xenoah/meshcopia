import assert from 'node:assert/strict';
import {unlink} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {regularRead,validateCurrentFbxSources} from './fbx-minimal-downloads.mjs';
import {cohortHash,stable,loadCohortPolicy,cohortCoreInputs,cohortInputNames,assertPublicationScope} from './cohort-policy.mjs';
import {fbxMinimalForAsset} from '../../src/lib/fbx-minimal-downloads.mjs';
export const cohortReceiptPath='.cache/cohort-verified.json';
export async function validateCohortReceipt(receipt,{head,policy,read=regularRead,execution={runId:process.env.GITHUB_RUN_ID??null,runAttempt:process.env.GITHUB_RUN_ATTEMPT??null,job:process.env.GITHUB_JOB??null}}){
 assert.deepEqual(Object.keys(receipt).sort(),['schemaVersion','createdBy','head','activationSha256','execution','inputs','projection','projectionSha256','sourceBindings','provenance'].sort());
 assert.equal(receipt.schemaVersion,1);assert.equal(receipt.createdBy,'same-job-cohort-prep/1');assert.equal(receipt.head,head,'Stale cohort receipt HEAD');
 assert.deepEqual(receipt.execution,execution,'Receipt belongs to another job');assert.equal(receipt.activationSha256,cohortHash(policy.bytes));
 assert.equal(receipt.projectionSha256,cohortHash(stable(receipt.projection)),'Cohort projection changed');
 assert.deepEqual(receipt.projection.map(r=>r.id).sort(),policy.newIds);assert.deepEqual(receipt.sourceBindings.map(r=>r.id).sort(),policy.newIds);
 assert.equal(new Set(receipt.projection.map(r=>r.id)).size,policy.newIds.length,'Duplicate cohort projection');
 assert.equal(new Set(receipt.sourceBindings.map(r=>r.id)).size,policy.newIds.length,'Duplicate cohort source binding');
 const runtime=JSON.parse(await read('docs/fbx-minimal-verification/runtime.json'));
 const required=[...cohortCoreInputs,...Object.keys(runtime.supportFiles),...Object.keys(runtime.recipe).map(k=>'scripts/fbx-verification/'+k),...policy.config.cohorts.flatMap(c=>cohortInputNames.map(n=>`docs/cohorts/${c.name}/${n}`))];
 for(const {source} of policy.cohorts)for(const row of source.models){const meta=JSON.parse(await read(row.assetMetadata));required.push(`content/assets/${row.id}/${meta.thumbnail}`);}
 assert.deepEqual(receipt.inputs.map(r=>r.path).sort(),[...new Set(required)].sort(),'Incomplete cohort receipt inputs');
 for(const input of receipt.inputs){assert.deepEqual(Object.keys(input).sort(),['path','sha256']);assert.equal(cohortHash(await read(input.path)),input.sha256,`Cohort input changed: ${input.path}`);}
 const provenance=[];
 for(const {activation:c,source} of policy.cohorts){
  const evidence=JSON.parse(await read(`docs/cohorts/${c.name}/T-evidence.json`));
  const expected=JSON.parse(await read(`docs/cohorts/${c.name}/expected.json`));
  provenance.push({name:c.name,releaseId:c.releaseId,fCommit:c.verificationCommit,transportExecution:evidence.transportExecution});
  for(const row of source.models){
   const binding=receipt.sourceBindings.find(r=>r.id===row.id),record=receipt.projection.find(r=>r.id===row.id);
   assert.deepEqual(binding,{id:row.id,assetVersion:row.version,metadataSha256:row.metadataSha256,sources:row.sourceFiles});
   assert.equal(record.verification.releaseTag,c.releaseTag);assert.equal(record.verification.releaseId,c.releaseId);assert.equal(record.verification.fCommit,c.verificationCommit);
   assert.equal(record.verification.inventorySha256,c.inputs['cohort-inventory.json']);assert.equal(record.sourceCommit,row.stageCommit);
   assert.deepEqual(record.sources,row.sourceFiles);assert.deepEqual(record.notice,row.fbxNotice);
   const output=expected.models.find(r=>r.id===row.id),root=`https://github.com/Xenoah/meshcopia/releases/download/${c.releaseTag}/`;
   assert.ok(output);assert.deepEqual(record.direct,{...output.fbx,url:root+output.fbx.filename});
   assert.deepEqual(record.archive,{...output.fbxArchive,url:root+output.fbxArchive.filename});
  }
 }
 assert.deepEqual(receipt.provenance,provenance);return receipt;
}
export async function prepareCohortDownloads(assets){
 const policy=await loadCohortPolicy();assertPublicationScope(assets,policy);
 const head=execFileSync('git',['--no-replace-objects','rev-parse','HEAD'],{encoding:'utf8'}).trim();
 const receipt=await validateCohortReceipt(JSON.parse(await regularRead(cohortReceiptPath)),{head,policy});
 for(const record of receipt.projection){
  const asset=assets.find(a=>a.id===record.id&&a.version===record.assetVersion&&a.status==='public'&&a.type==='model');assert.ok(asset);
  await validateCurrentFbxSources(asset,receipt.sourceBindings.find(r=>r.id===record.id));
  assert.ok(fbxMinimalForAsset(asset,{formats:[record]}),'Invalid verified cohort projection');
 }
 await unlink(cohortReceiptPath);return receipt.projection;
}
