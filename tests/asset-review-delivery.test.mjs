import test from 'node:test';
import assert from 'node:assert/strict';
import {model} from './delivery-fixtures.mjs';
import {deliveryReadiness} from '../src/lib/delivery.mjs';
import {primaryDownload} from '../src/lib/downloads.mjs';
import {planBundle} from '../src/lib/batch-download.mjs';
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
