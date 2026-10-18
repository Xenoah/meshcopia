import assert from 'node:assert/strict';
import {readFile,unlink} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {sha256,filesIn} from '../lib/catalog.mjs';
import {regularRead} from '../lib/fbx-minimal-downloads.mjs';
import {revisionConfig,revisionConfigPath,revisionLockPath,revisionIds} from '../lib/production-catalog.mjs';
import {fbxMinimalForAsset} from '../../src/lib/fbx-minimal-downloads.mjs';
export const receiptPath='.cache/asset-revision-verified.json';
export const evidencePath='docs/asset-revisions/publication.json';
export const inventoryPath='docs/asset-revisions/revision-inventory.json';
export async function revisionInputs(){
 const core=[revisionConfigPath,revisionLockPath,evidencePath,inventoryPath,'scripts/asset-revisions/publication.py','scripts/asset-revisions/prepare_activation.py','scripts/asset-revisions/activation.mjs','scripts/lib/production-catalog.mjs','scripts/generate.mjs','scripts/lib/delivery.mjs','scripts/lib/delivery-chunks.mjs','src/lib/delivery.mjs','src/lib/fbx-minimal-downloads.mjs'];
 for(const id of revisionIds){const root=`asset-revisions/repair-appliances-v1/${id}`;core.push(...(await filesIn(root)).filter(f=>!f.endsWith('.blend1')).map(f=>`${root}/${f}`));if(id!=='household-two-door-refrigerator'){const old=`content/assets/${id}`;core.push(...(await filesIn(old)).map(f=>`${old}/${f}`));}}
 return core.sort();
}
export async function validateRevisionReceipt(receipt,{head,execution,inputs,read=regularRead,config,assets}){
 assert.equal(receipt.schemaVersion,1);assert.equal(receipt.createdBy,'same-job-revision-prep/1');assert.equal(receipt.head,head,'Stale revision receipt HEAD');assert.deepEqual(receipt.execution,execution,'Revision receipt belongs to another execution');
 assert.equal(receipt.releaseId,config.releaseId);assert.equal(receipt.inventorySha256,config.inventorySha256);
 assert.deepEqual(receipt.inputs.map(r=>r.path),inputs,'Revision input coverage differs');
 for(const row of receipt.inputs)assert.equal(sha256(await read(row.path)),row.sha256,`Stale revision input: ${row.path}`);
 assert.deepEqual(receipt.projection.map(r=>r.id),revisionIds);
 assert.equal(sha256(JSON.stringify(receipt.projection)),receipt.projectionSha256);
 const inventory=JSON.parse(await read(inventoryPath));assert.equal(sha256(await read(inventoryPath)),config.inventorySha256);
 for(const r of receipt.projection){
  const a=assets.find(a=>a.id===r.id),bound=inventory.records.find(x=>x.id===r.id);assert.ok(a&&bound);assert.equal(a.version,bound.assetVersion);assert.equal(r.assetVersion,a.version);
  assert.equal(r.verification.releaseTag,config.releaseTag);assert.ok(fbxMinimalForAsset(a,{formats:[r]}));
  const sources=[];for(const name of a.sources){const b=await readFile(`${a.dir}/source/${name}`);sources.push({name,bytes:b.length,sha256:sha256(b)});}
  const canonical=xs=>JSON.stringify(xs.map(({name,bytes,sha256})=>({name,bytes,sha256})).sort((a,b)=>a.name.localeCompare(b.name,'en')));
  assert.equal(canonical(r.sources),canonical(sources),'Revision complete source inventory changed');
  assert.deepEqual(r.direct,{filename:r.id+'.fbx',url:`https://github.com/Xenoah/meshcopia/releases/download/${config.releaseTag}/${r.id}.fbx`,bytes:bound.fbxBytes,sha256:bound.fbxSha256});
  const filename=`${r.id}-${r.assetVersion}-fbx-minimal-1.0.0.zip`;
  assert.deepEqual(r.archive,{filename,url:`https://github.com/Xenoah/meshcopia/releases/download/${config.releaseTag}/${filename}`,bytes:bound.archiveBytes,sha256:bound.archiveSha256});
  assert.deepEqual(r.notice,{filename:'LICENSE.txt',text:bound.notice,bytes:bound.noticeBytes,sha256:bound.noticeSha256});
 }
 return receipt.projection;
}
export async function prepareRevisionDownloads(assets){
 const config=await revisionConfig();if(!config)return [];
 const evidence=await regularRead(evidencePath);assert.equal(sha256(evidence),config.evidenceSha256);const proof=JSON.parse(evidence);assert.equal(proof.state,'anonymous-byte-readback-passed');assert.equal(proof.releaseId,config.releaseId);assert.equal(proof.inventorySha256,config.inventorySha256);
 const records=await validateRevisionReceipt(JSON.parse(await regularRead(receiptPath)),{head:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),execution:{runId:process.env.GITHUB_RUN_ID??null,runAttempt:process.env.GITHUB_RUN_ATTEMPT??null,job:process.env.GITHUB_JOB??null},inputs:await revisionInputs(),config,assets});
 await unlink(receiptPath);return records;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href&&process.argv.includes('--inputs'))console.log(JSON.stringify(await revisionInputs()));
