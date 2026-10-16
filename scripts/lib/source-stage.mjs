import assert from 'node:assert/strict';
export function validateSourceStage(marker,assets,protectedIds){
 assert.ok(marker&&typeof marker==='object'&&!Array.isArray(marker),'Source-stage marker must be an object');
 assert.equal(marker.schemaVersion,1);assert.equal(marker.purpose,'draft-raw-source-prepublication');
 assert.ok(Array.isArray(marker.ids)&&marker.ids.length>0&&marker.ids.length<=50,'Source-only stages are limited to 1–50 new draft models');assert.equal(new Set(marker.ids).size,marker.ids.length);
 for(const id of marker.ids){assert.match(id,/^[a-z0-9]+(?:-[a-z0-9]+)*$/);assert.ok(!protectedIds.includes(id),`Existing asset in source-only stage: ${id}`);const a=assets.find(a=>a.id===id);assert.ok(a&&a.type==='model'&&a.status==='draft',`Source-only asset must remain a draft model: ${id}`)}
 return true;
}
