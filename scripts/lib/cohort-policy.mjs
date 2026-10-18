import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
export const cohortActivationPath='docs/cohort-activation.json';
export const cohortInputNames=['source.json','expected.json','approval.json','T-evidence.json','cohort-inventory.json'];
export const cohortCoreInputs=[cohortActivationPath,'scripts/prepare-cohort-activation.py','scripts/cohort/common.py','scripts/lib/cohort-downloads.mjs','scripts/lib/cohort-policy.mjs','scripts/verify-minimal-activation.py','src/lib/fbx-minimal-downloads.mjs','src/lib/delivery.mjs','docs/fbx-minimal-verification/runtime.json'];
export const cohortHash=b=>createHash('sha256').update(b).digest('hex');
export const stable=x=>Array.isArray(x)?`[${x.map(stable).join(',')}]`:x&&typeof x==='object'?`{${Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')}}`:JSON.stringify(x);
const exact=(obj,keys)=>assert.deepEqual(Object.keys(obj).sort(),keys.split(' ').sort());
export function validateCohortActivation(config){
 exact(config,'schemaVersion repository cohorts');assert.equal(config.schemaVersion,1);assert.equal(config.repository,'Xenoah/meshcopia');assert.ok(Array.isArray(config.cohorts));
 const names=new Set();
 for(const c of config.cohorts){
  exact(c,'name modelCount releaseTag releaseId verificationCommit transportCommit evidenceCommit publicPayloads inputs');
  assert.match(c.name,/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/);assert.ok(!names.has(c.name),'Duplicate cohort');names.add(c.name);
  assert.ok(Number.isSafeInteger(c.modelCount)&&c.modelCount>0&&c.modelCount<=300);
  assert.equal(c.releaseTag,`cohort-${c.name}-v1.0.0`);assert.ok(Number.isSafeInteger(c.releaseId)&&c.releaseId>0);
  for(const k of ['verificationCommit','transportCommit','evidenceCommit'])assert.match(c[k],/^[a-f0-9]{40}$/);
  assert.ok(['fbx,fbxArchive','fbx,fbxArchive,archive'].includes(c.publicPayloads?.join(',')));
  assert.deepEqual(Object.keys(c.inputs).sort(),[...cohortInputNames].sort());for(const h of Object.values(c.inputs))assert.match(h,/^[a-f0-9]{64}$/);
 }
 return config;
}
export async function loadCohortPolicy(){
 const bytes=await readFile(cohortActivationPath),config=validateCohortActivation(JSON.parse(bytes));
 const originalIds=JSON.parse(await readFile('docs/scaling-protected-ids.json','utf8')).ids;
 assert.equal(originalIds.length,173);const ids=new Set(originalIds);assert.equal(ids.size,173);
 const cohorts=[];
 for(const activation of config.cohorts){
  const sources=await readFile(`docs/cohorts/${activation.name}/source.json`);assert.equal(cohortHash(sources),activation.inputs['source.json']);
  const source=JSON.parse(sources);assert.equal(source.cohort,activation.name);assert.equal(source.modelCount,activation.modelCount);assert.equal(source.models.length,activation.modelCount);
  for(const r of source.models){assert.ok(!ids.has(r.id),'Duplicate original/cohort model ID');ids.add(r.id);}
  cohorts.push({activation,source});
 }
 return {bytes,config,cohorts,originalIds,publicIds:[...ids].sort(),newIds:cohorts.flatMap(c=>c.source.models.map(r=>r.id)).sort()};
}
export function assertPublicationScope(assets,policy){
 assert.deepEqual(assets.filter(a=>a.status==='public').map(a=>a.id).sort(),policy.publicIds,'Public assets differ from the explicit verified cohorts');
 assert.equal(assets.filter(a=>a.status==='public'&&a.type==='texture').length,36);
}

export function originalSourceUrl(asset,file,policy){
 const row=policy.cohorts.flatMap(c=>c.source.models).find(r=>r.id===asset.id);
 const encoded=file.name.split('/').map(encodeURIComponent).join('/');
 return row&&file.name!==asset.preview?`https://raw.githubusercontent.com/Xenoah/meshcopia/${row.stageCommit}/content/assets/${asset.id}/source/${encoded}`:`https://xenoah.github.io/meshcopia/assets/${asset.id}/source/${encoded}`;
}

export function originalThumbnailUrl(asset,policy){
 const row=policy.cohorts.flatMap(c=>c.source.models).find(r=>r.id===asset.id);
 return row?`https://raw.githubusercontent.com/Xenoah/meshcopia/${row.stageCommit}/content/assets/${asset.id}/${encodeURIComponent(asset.thumbnail)}`:`https://xenoah.github.io/meshcopia/assets/${asset.id}/thumbnail${asset.thumbnail.slice(asset.thumbnail.lastIndexOf('.'))}`;
}
