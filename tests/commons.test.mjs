import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import validator from 'gltf-validator';
import {readCatalog,sha256,attributionFor} from '../scripts/lib/catalog.mjs';

const sourceCommit='784e040a866c0081d6641c03cbf7f23d48a59dc2';
const expected=['bar-stool','lounge-chair','lounge-sofa','round-table','pendant-light','coffee-cup','leaf-planter','espresso-machine','coffee-grinder','pa-speaker','dj-controller','display-plinth','low-table','round-stage','equipment-rack','dj-desk','coffee-bag','bottle-set','book-set','table-candle','halo-light','poster-frame','bar-counter','floating-bookshelf'].map(id=>'commons-'+id).sort();

test('cafe collection preserves pinned provenance, original embedded PNGs and portable GLB files',async()=>{
 const assets=(await readCatalog()).filter(a=>a.type==='model'&&a.id.startsWith('commons-'));
 assert.deepEqual(assets.map(a=>a.id).sort(),expected);
 for(const a of assets){
  assert.equal(a.provenance.sourceCommit,sourceCommit);
  assert.equal(a.provenance.sourceUrl,`https://github.com/Xenoah/vrcworld_tech-tech-cafe/tree/${sourceCommit}`);
  assert.ok(a.provenance.sourceObjects.length>0);
  assert.equal(new Set(a.provenance.sourceObjects).size,a.provenance.sourceObjects.length);
  assert.ok(a.provenance.sourceObjects.every(name=>(/^(FURN_|LGT_|AV_)/.test(name)||name==='BarTopReturn')));
  const credit=attributionFor(a);assert.ok(credit.includes(a.provenance.sourceUrl));assert.ok(credit.includes(a.provenance.changes));
  assert.deepEqual(a.sources,[`${a.id}.glb`,`${a.id}.stl`]);
  const raw=await readFile(path.join(a.dir,'source',a.preview));
  const report=await validator.validateBytes(new Uint8Array(raw),{uri:a.preview,maxIssues:20,writeTimestamp:false});
  assert.equal(report.issues.numErrors,0,`${a.id}: ${JSON.stringify(report.issues.messages)}`);
  const length=raw.readUInt32LE(12),doc=JSON.parse(raw.subarray(20,20+length).toString()),binary=raw.subarray(28+length);
  assert.equal(doc.cameras,undefined);assert.equal(doc.animations,undefined);
  assert.ok(doc.buffers.every(b=>!b.uri));
  const hashes=(doc.images||[]).map(image=>{
   assert.equal(image.uri,undefined);
   const view=doc.bufferViews[image.bufferView],start=view.byteOffset||0;
   const digest=sha256(binary.subarray(start,start+view.byteLength));
   assert.ok(Object.entries(a.provenance.sourceFiles).some(([file,hash])=>file.endsWith('.png')&&hash===digest));
   return digest;
  }).sort();
  assert.deepEqual(hashes,a.provenance.embeddedImageSha256);
  for(const sampler of doc.samplers||[]){assert.ok([33648,33071].includes(sampler.wrapS));assert.ok([33648,33071].includes(sampler.wrapT));}
  assert.ok(a.dimensions.every(d=>Number.isFinite(d)&&d>0));
  const stl=await readFile(path.join(a.dir,'source',`${a.id}.stl`));
  const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<stl.readUInt32LE(80);i++)for(let v=0;v<3;v++)for(let axis=0;axis<3;axis++){
   const coordinate=stl.readFloatLE(84+i*50+12+v*12+axis*4);assert.ok(Number.isFinite(coordinate));
   low[axis]=Math.min(low[axis],coordinate);high[axis]=Math.max(high[axis],coordinate);
  }
  assert.ok(Math.abs(low[1])<1e-5,`${a.id}: base must be Y=0`);
  for(let axis=0;axis<3;axis++)assert.ok(Math.abs(high[axis]-low[axis]-a.dimensions[axis])<2e-5,`${a.id}: dimension mismatch`);
 }
});

test('standalone cafe PNGs retain original bytes, rectangular dimensions and recorded wrap modes',async()=>{
 const expected={
  'warm-oak':['mirror',1254,1254,'cc38376743e54a2f0c72be72ee0c2e699a62d3de15d67c621277ecb38111c36d'],
  'mineral-plaster':['mirror',1254,1254,'2d835bd37e136fec4cd64709fef9173f554707ea2c28607693018b8cdcc4c1f3'],
  'basalt-terrazzo':['mirror',1254,1254,'a7eebda5bbb2404426a9a4a60e3b9434e30274167d7641a3338f426770bded54'],
  'blackened-steel':['mirror',1254,1254,'ccb94abc7aeabb72a9398d67a0f6904b1fff755c987ddce7f9d2800172d61b1e'],
  'satin-brass':['mirror',1254,1254,'03ac661503ff10aff54d0e881620a714a25aba843293c0580f7a945af9a4269c'],
  'teal-woven':['mirror',1254,1254,'9ccf88a755b0ecc9c44e6a44c51b460135395300d59f68e91353471a42d627cd'],
  'relay-controller':['clamp',1774,887,'c3209959d4d66776dc51f78d7b321a0b9359edc313057ac858cc251b4a9c03c6'],
  'bar-labels':['clamp',1536,1024,'6a0d1ffe7da88a68f3e8cd0f9b126bef3b3201f3acbc44f05a713b8e842c1da8'],
  'cafe-props':['clamp',1774,887,'bc3f26f6ec15b16436345e5cef34bbf245d22b7d2bcd90fa6fb033177cd99313']
 };
 const assets=(await readCatalog()).filter(a=>a.type==='texture'&&a.id.startsWith('commons-'));
 assert.deepEqual(assets.map(a=>a.id).sort(),Object.keys(expected).map(id=>'commons-'+id).sort());
 for(const a of assets){
  const [mode,width,height,hash]=expected[a.id.slice(8)];
  assert.equal(a.provenance.sourceCommit,sourceCommit);assert.equal(a.provenance.sourcePixelsUnchanged,true);
  assert.equal(a.wrapMode,mode);assert.equal(a.seamless,mode!=='clamp');
  assert.deepEqual([a.width,a.height],[width,height]);assert.equal(a.resolution,Math.max(width,height));
  assert.deepEqual(Object.keys(a.maps),['baseColor']);assert.equal(a.normalConvention,undefined);
  assert.deepEqual(a.sources,[a.maps.baseColor]);
  const png=await readFile(path.join(a.dir,'source',a.maps.baseColor));
  assert.equal(png.subarray(1,4).toString(),'PNG');assert.equal(sha256(png),hash);
  assert.deepEqual([png.readUInt32BE(16),png.readUInt32BE(20)],[width,height]);
  assert.ok(attributionFor(a).includes(a.provenance.sourceUrl));
 }
});
