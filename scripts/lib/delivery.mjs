import assert from 'node:assert/strict';
import {DELIVERY_POLICY,deliveryReadiness} from '../../src/lib/delivery.mjs';
// Call only with prepareFbxMinimalDownloads() output. That gate independently
// checks live attachment IDs/digests. Chunk bytes are bound to the same FBX hash.
export function bindDelivery(asset,verifiedFbx,transports) {
 const record=verifiedFbx.find(f=>f.id===asset.id&&f.assetVersion===asset.version);
 if(!record)return asset;
 assert.equal(record.selfContained,true,'External FBX dependencies need a reviewed adapter');
 const transport=transports.get(asset.id);assert.ok(transport,'Missing verified payload transport');
 const delivery={schemaVersion:1,id:asset.id,assetVersion:asset.version,packageVersion:record.packageVersion,
  contentPolicy:DELIVERY_POLICY,sourceFiles:record.sources,archive:record.archive,
  files:[{name:record.direct.filename,format:'FBX',bytes:record.direct.bytes,sha256:record.direct.sha256,url:record.direct.url,
   fetch:transport}],
  notice:record.notice,verification:record.verification};
 const result={...asset,downloads:{...asset.downloads,delivery}};
 assert.ok(deliveryReadiness(result).ready,'Invalid consumer FBX inventory');
 return result;
}
