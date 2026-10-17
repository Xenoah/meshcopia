import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {model,hash,fixtureFetch} from './delivery-fixtures.mjs';
import {deliveryReadiness} from '../src/lib/delivery.mjs';
import {primaryDownload,primaryDownloadBytes,directModelFiles} from '../src/lib/downloads.mjs';
import {planBundle,buildBundle} from '../src/lib/batch-download.mjs';
import {filterAssets} from '../src/lib/catalog-ui.js';
import {bundleSizeSummary} from '../src/lib/file-size.mjs';
test('ordinary/direct/batch use the FBX inventory and exact byte size; previews stay separate',async()=>{
 const a=model(),b=model('table');
 assert.equal(primaryDownload(a).url,a.downloads.delivery.archive.url);
 assert.equal(filterAssets([a],{query:'fbx'}).length,1);assert.equal(primaryDownloadBytes(a),100);assert.deepEqual(directModelFiles(a),a.downloads.delivery.files);
 const plan=planBundle([a,b]);assert.deepEqual(plan.entries.map(x=>x.name),['chair/chair.fbx','table/table.fbx','LICENSE.txt']);
 const zip=await buildBundle(plan,{cryptoImpl:webcrypto,fetchImpl:async(url,options)=>{
  assert.match(url,/^https:\/\/xenoah.github.io\/meshcopia\/download-data\/[a-f0-9]{64}\.(json|gz)$/);
  assert.equal(options.credentials,'omit');return fixtureFetch()(url);
 }});
 assert.equal(zip.size,bundleSizeSummary([a,b]).zipBytes);
 const check=spawnSync('python3',['-c',"import io,sys,zipfile;z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));assert z.testzip() is None;assert set(z.namelist())=={'chair/chair.fbx','table/table.fbx','LICENSE.txt'};assert z.read('chair/chair.fbx')==b'model';assert b'table by Fixture' in z.read('LICENSE.txt')"],{input:Buffer.from(await zip.arrayBuffer())});
 assert.equal(check.status,0,check.stderr.toString());
});
test('missing/stale/unsafe FBX cannot silently fall back to original models',()=>{
 for(const change of [a=>delete a.downloads.delivery,a=>a.downloads.delivery.assetVersion='2.0.0',a=>a.files[0].sha256=hash('changed'),a=>a.downloads.delivery.files=[],a=>a.downloads.delivery.files[0].name='preview.glb',a=>a.downloads.delivery.files[0].fetch.url='https://github.com/release',a=>a.downloads.delivery.notice.text+='changed',a=>a.status='draft',a=>a.downloads.delivery.files=[null],a=>a.downloads.delivery.sourceFiles=[null]]) {
  const a=model();a.downloads.models={url:'https://example.com/old.zip',bytes:999};change(a);
  assert.equal(deliveryReadiness(a).ready,false);assert.equal(primaryDownload(a),undefined);assert.equal(primaryDownloadBytes(a),Infinity);assert.throws(()=>planBundle([a]));assert.deepEqual(bundleSizeSummary([a]),{inputBytes:null,zipBytes:null});
 }
});
test('required image dependencies stay in model folder and suppress standalone FBX',()=>{
 const a=model(),d=a.downloads.delivery;
 d.files.push({...d.files[0],name:'color.png',format:'PNG',url:d.files[0].url.replace('chair.fbx','color.png')});
 assert.ok(deliveryReadiness(a).ready);assert.deepEqual(directModelFiles(a),[]);
 assert.deepEqual(planBundle([a]).entries.map(x=>x.name),['chair/chair.fbx','chair/color.png','LICENSE.txt']);
});
test('rate limit, CORS, JSON metadata and changed FBX bytes never produce a partial ZIP',async()=>{
 for(const fetchImpl of [async()=>new Response('',{status:403}),async()=>{throw new TypeError('CORS')},async()=>new Response('{}'),async()=>new Response('wrong')])await assert.rejects(buildBundle(planBundle([model()]),{cryptoImpl:webcrypto,fetchImpl}));
});
