import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {readCatalog,sha256} from '../scripts/lib/catalog.mjs';
import {readProductionCatalog,loadProductionPolicy,revisionConfig,revisionIds,originalThumbnailUrl} from '../scripts/lib/production-catalog.mjs';
import {validateRevisionReceipt,revisionInputs,inventoryPath} from '../scripts/asset-revisions/activation.mjs';

test('approved overlay preserves every existing ID and old source byte while binding three versioned previews',async()=>{
 const base=await readCatalog(),assets=await readProductionCatalog(base),p=await loadProductionPolicy();
 assert.equal(base.length,454);assert.equal(assets.length,455);assert.equal(p.publicIds.length,455);
 for(const old of base){const a=assets.find(a=>a.id===old.id);assert.ok(a);if(!revisionIds.includes(a.id))assert.deepEqual(a,old);else for(const name of old.sources)assert.deepEqual(await readFile(`${a.dir}/source/${name}`),await readFile(`${old.dir}/source/${name}`));}
 for(const id of revisionIds){const a=assets.find(a=>a.id===id);assert.equal(a.version,id==='household-two-door-refrigerator'?'1.0.0':'1.0.2');assert.equal(a.preview,id==='household-two-door-refrigerator'?`${id}.glb`:`${id}-${a.version}.glb`);assert.ok(originalThumbnailUrl(a,p).endsWith(`thumbnail-${a.version}.webp`));assert.ok(a.sources.every(n=>!n.endsWith('.fbx')&&!n.endsWith('.blend')));}
});

test('revision receipt rejects stale execution, missing input, tampered payload and incomplete legacy inventory',async()=>{
 const assets=await readProductionCatalog(),config=await revisionConfig(),inputs=await revisionInputs(),inventory=JSON.parse(await readFile(inventoryPath));
 const projection=[];
 for(const r of inventory.records){const a=assets.find(a=>a.id===r.id),sources=[];for(const name of a.sources){const b=await readFile(`${a.dir}/source/${name}`);sources.push({name,bytes:b.length,sha256:sha256(b)});}
  const root=`https://github.com/Xenoah/meshcopia/releases/download/${config.releaseTag}/`,archive=`${r.id}-${r.assetVersion}-fbx-minimal-1.0.0.zip`;
  projection.push({id:r.id,assetVersion:r.assetVersion,format:'FBX',packageVersion:'1.0.0',selfContained:true,sources,direct:{filename:r.id+'.fbx',url:root+r.id+'.fbx',bytes:r.fbxBytes,sha256:r.fbxSha256},archive:{filename:archive,url:root+archive,bytes:r.archiveBytes,sha256:r.archiveSha256},notice:{filename:'LICENSE.txt',text:r.notice,bytes:r.noticeBytes,sha256:r.noticeSha256},verification:{state:'published-verified',releaseTag:config.releaseTag},limitations:['unit-test fixture only']});
 }
 const execution={runId:'fixture',runAttempt:'1',job:'fixture'},head='fixture';
 const receipt={schemaVersion:1,createdBy:'same-job-revision-prep/1',head,execution,releaseId:config.releaseId,inventorySha256:config.inventorySha256,projection,projectionSha256:sha256(JSON.stringify(projection)),inputs:await Promise.all(inputs.map(async path=>({path,sha256:sha256(await readFile(path))})))};
 const options={head,execution,inputs,config,assets};assert.deepEqual(await validateRevisionReceipt(receipt,options),projection);
 for(const mutate of [r=>r.head='stale',r=>r.execution.runAttempt='0',r=>r.inputs.pop(),r=>r.inputs[0].sha256='0'.repeat(64),r=>r.releaseId++,r=>r.projection.pop(),r=>r.projection[0].sources.pop(),r=>r.projection[0].archive.sha256='0'.repeat(64),r=>r.projection[0].direct.bytes++,r=>r.projection[0].notice.text+='changed',r=>r.projection[0].verification.state='local-review-verified']){
  const bad=structuredClone(receipt);mutate(bad);bad.projectionSha256=sha256(JSON.stringify(bad.projection));await assert.rejects(()=>validateRevisionReceipt(bad,options));
 }
});
