import assert from 'node:assert/strict';
import {DELIVERY_POLICY,deliveryReadiness} from '../../src/lib/delivery.mjs';
// Call only with prepareFbxMinimalDownloads() output. That gate independently
// checks live attachment IDs/digests against this exact, pinned transport evidence.
export function bindDelivery(asset,verifiedFbx,evidence) {
 const record=verifiedFbx.find(f=>f.id===asset.id&&f.assetVersion===asset.version);
 if(!record)return asset;
 assert.equal(record.selfContained,true,'External FBX dependencies need a reviewed adapter');
 const attachment=evidence.assets.filter(f=>f.name===record.direct.filename);
 assert.equal(attachment.length,1);
 const proof=attachment[0];
 for(const key of ['bytes','sha256','url'])assert.equal(proof[key],record.direct[key]);
 assert.ok(Number.isSafeInteger(proof.assetId)&&proof.assetId>0);
 const delivery={schemaVersion:1,id:asset.id,assetVersion:asset.version,packageVersion:record.packageVersion,
  contentPolicy:DELIVERY_POLICY,sourceFiles:record.sources,archive:record.archive,
  files:[{name:record.direct.filename,format:'FBX',bytes:record.direct.bytes,sha256:record.direct.sha256,url:record.direct.url,
   fetch:{url:`https://api.github.com/repos/Xenoah/meshcopia/releases/assets/${proof.assetId}`,accept:'application/octet-stream'}}],
  notice:record.notice,verification:record.verification};
 const result={...asset,downloads:{...asset.downloads,delivery}};
 assert.ok(deliveryReadiness(result).ready,'Invalid consumer FBX inventory');
 return result;
}
