// Production revision overlay. Historical content/assets and frozen cohort
// validators remain intact; only approved versioned sources are added.
import assert from 'node:assert/strict';
import {readFile,mkdir,cp,rm} from 'node:fs/promises';
import path from 'node:path';
import {readCatalog,readAsset,sha256,filesIn} from './catalog.mjs';
import {loadCohortPolicy,originalSourceUrl,originalThumbnailUrl as cohortThumbnail} from './cohort-policy.mjs';
export {assertPublicationScope,originalSourceUrl} from './cohort-policy.mjs';
export const revisionConfigPath='docs/asset-revision-activation.json';
export const revisionLockPath='asset-revisions/repair-appliances-v1/candidate-lock.json';
export const revisionIds=['garden-arch','household-two-door-refrigerator','wayfinding-sign'];
export async function revisionConfig(){
 try{
  const c=JSON.parse(await readFile(revisionConfigPath));
  assert.equal(c.schemaVersion,1);assert.equal(c.releaseTag,'cohort-repair-appliances-v1.0.0');assert.ok(Number.isSafeInteger(c.releaseId)&&c.releaseId>0);
  assert.equal(c.reviewCommit,'4d537fad080c50ec18f3e515695f4f9f582351c5');assert.equal(c.reviewRunId,39129140683);
  for(const key of ['lockSha256','inventorySha256','evidenceSha256'])assert.match(c[key],/^[a-f0-9]{64}$/);
  assert.equal(sha256(await readFile(revisionLockPath)),c.lockSha256);return c;
 }catch(e){if(e.code==='ENOENT'&&e.path===revisionConfigPath)return null;throw e;}
}
export async function loadProductionPolicy(){
 const p=await loadCohortPolicy(),revision=await revisionConfig();
 if(!revision)return p;
 assert.equal(p.publicIds.length,454);assert.ok(!p.publicIds.includes(revisionIds[1]));
 return {...p,revision,publicIds:[...p.publicIds,revisionIds[1]].sort()};
}
export function originalThumbnailUrl(a,p){return p.revision&&revisionIds.includes(a.id)?`https://xenoah.github.io/meshcopia/assets/${a.id}/thumbnail-${a.version}.webp`:cohortThumbnail(a,p);}
export async function readProductionCatalog(base){
 base??=await readCatalog();if(!await revisionConfig())return base;
 const lock=JSON.parse(await readFile(revisionLockPath));assert.deepEqual(lock.records.map(r=>r.id),revisionIds);
 const result=[...base];
 for(const r of lock.records){
  const staged=`asset-revisions/repair-appliances-v1/${r.id}`;
  assert.deepEqual((await filesIn(staged)).filter(f=>!f.endsWith('.blend1')),r.retainedFiles.map(f=>f.path).sort((a,b)=>a.localeCompare(b,'en')),'Unreviewed revision files');
  for(const f of r.retainedFiles){const b=await readFile(`${staged}/${f.path}`);assert.equal(b.length,f.bytes);assert.equal(sha256(b),f.sha256,'Reviewed revision changed');}
  const incoming=await readAsset(staged),old=base.find(a=>a.id===r.id),target=`.cache/revision-sources/${r.id}`;
  assert.equal(incoming.version,r.assetVersion);assert.equal(sha256(await readFile(`${staged}/asset.json`)),r.metadataSha256);
  await rm(target,{recursive:true,force:true});await mkdir(`${target}/source`,{recursive:true});
  if(old)await cp(`${old.dir}/source`,`${target}/source`,{recursive:true});
  for(const name of incoming.sources){assert.ok(!old?.sources.includes(name),'Never replace a legacy source URL');await cp(`${staged}/source/${name}`,`${target}/source/${name}`);}
  await cp(`${staged}/asset.json`,`${target}/asset.json`);await cp(`${staged}/${incoming.thumbnail}`,`${target}/${incoming.thumbnail}`);
  const asset=await readAsset(path.resolve(target)),index=result.findIndex(a=>a.id===r.id);if(index<0)result.push(asset);else result[index]=asset;
 }
 return result;
}
