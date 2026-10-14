import test from 'node:test';
import assert from 'node:assert/strict';
import {validateUsages,readCatalog} from '../scripts/lib/catalog.mjs';
import {filterAssets} from '../src/lib/catalog-ui.js';

test('usage metadata is optional, supports multiple records and preserves unknowns',()=>{
 assert.deepEqual(validateUsages(undefined),[]);
 assert.deepEqual(validateUsages([]),[]);
 const records=[{relationship:'original',project:'Example'},{relationship:'reuse',project:'Another work',sourceUrl:'https://example.com/source',sourceRef:'v1',sourcePaths:['Assets/Room.blend'],selectors:['Chair.001'],context:'Room 3'}];
 assert.deepEqual(validateUsages(records),records);
 assert.equal(records[0].sourceRef,undefined);
});
test('usage validation rejects unsafe links, paths and malformed records',()=>{
 const valid={relationship:'original',project:'Example'};
 for(const sourceUrl of ['javascript:alert(1)','data:text/html,test','file:///tmp/test','//example.com','https://user:password@example.com','https://example.com\\evil','https://example.com\n'])assert.throws(()=>validateUsages([{...valid,sourceUrl}]));
 for(const sourcePath of ['/workspace/source','C:\\source','../source','a/../b','a//b'])assert.throws(()=>validateUsages([{...valid,sourcePaths:[sourcePath]}]));
 for(const change of [{relationship:'deployed'},{project:''},{sourceRef:null},{context:23},{selectors:['']},{sourcePaths:'Assets/file'},{unknown:true}])assert.throws(()=>validateUsages([{...valid,...change}]));
 for(const value of [null,{},[null],[[]]])assert.throws(()=>validateUsages(value));
});
test('all baseline usage backfills are evidence-bound and searchable',async()=>{
 const assets=await readCatalog();
 for(const a of assets.filter(a=>a.id.startsWith('commons-'))){
  assert.equal(a.usages[0].sourceRef,a.provenance.sourceCommit);
  assert.equal(a.usages[0].sourceUrl,a.provenance.sourceUrl);
  if(a.type==='model')assert.deepEqual(a.usages[0].selectors,a.provenance.sourceObjects);
 }
 const results=filterAssets(assets,{query:'FURN_Bar FURN_StoolSeat'});
 assert.ok(results.some(a=>a.id==='commons-bar-stool'));
 assert.equal(filterAssets(assets,{query:'FURN_Bar',type:'texture'}).length,0);
 const chair=assets.find(a=>a.id==='studio-chair');assert.equal(chair.usages[0].project,'Meshcopia');assert.equal(chair.usages[0].sourceRef,undefined);
 const legacy={...chair};delete legacy.usages;assert.equal(filterAssets([legacy],{query:'chair'}).length,1);
 const reuse={...chair,usages:[{relationship:'reuse',project:'Second project',context:'Gallery east',sourcePaths:['Assets/Sculpture.blend']}]};
 assert.equal(filterAssets([reuse],{query:'Second Gallery Sculpture'}).length,1);
});
