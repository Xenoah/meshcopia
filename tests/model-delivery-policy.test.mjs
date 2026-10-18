import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {assertCompleteModelDeliveries} from '../scripts/lib/model-delivery-policy.mjs';
const baseline=JSON.parse(await readFile(new URL('../docs/model-delivery-baseline.json',import.meta.url),'utf8'));
const data=Buffer.from('test-fixture-source');
const source={name:'future-model.glb',bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')};
const asset={id:'future-model',version:'1.0.0',type:'model',status:'public',sources:[source.name]};
const opts={baseline,readSource:async()=>data,readMetadata:async()=>Buffer.from('{}')};
test('new public model cannot omit verified FBX',async()=>assert.rejects(assertCompleteModelDeliveries([asset],opts),/requires.*verified FBX/));
test('draft source stages do not pretend to be complete published deliveries',async()=>assertCompleteModelDeliveries([{...asset,status:'draft'}],opts));
test('independently verified matching source/version can complete delivery',async()=>assertCompleteModelDeliveries([asset],{...opts,verifiedFbx:[{id:asset.id,assetVersion:asset.version,sources:[source]}]}));
test('stale source hash and stale version cannot satisfy coverage',async()=>{for(const x of [{id:asset.id,assetVersion:'0.9.0',sources:[source]},{id:asset.id,assetVersion:asset.version,sources:[{...source,sha256:'0'.repeat(64)}]}])await assert.rejects(assertCompleteModelDeliveries([asset],{...opts,verifiedFbx:[x]}),/requires/)});
test('historical exception cannot be expanded',async()=>assert.rejects(assertCompleteModelDeliveries([],{...opts,baseline:{...baseline,models:[...baseline.models,{id:'future-model'}]}}),/exception changed/));

test('verified source comparison ignores JSON object key order while binding every source byte',async()=>{const reordered={bytes:source.bytes,name:source.name,sha256:source.sha256};await assertCompleteModelDeliveries([asset],{...opts,verifiedFbx:[{id:asset.id,assetVersion:asset.version,sources:[reordered]}]});for(const changed of [{...reordered,bytes:source.bytes+1},{...reordered,name:'other.glb'}])await assert.rejects(assertCompleteModelDeliveries([asset],{...opts,verifiedFbx:[{id:asset.id,assetVersion:asset.version,sources:[changed]}]}),/requires/);});
