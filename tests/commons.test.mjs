import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import validator from 'gltf-validator';
import {readCatalog,sha256,attributionFor} from '../scripts/lib/catalog.mjs';

const sourceCommit='784e040a866c0081d6641c03cbf7f23d48a59dc2';
const expected=['bar-stool','lounge-chair','lounge-sofa','round-table','pendant-light','coffee-cup','leaf-planter','espresso-machine','coffee-grinder','pa-speaker','dj-controller','display-plinth'].map(id=>'commons-'+id).sort();

test('cafe collection preserves pinned provenance, original embedded PNGs and portable GLB files',async()=>{
 const assets=(await readCatalog()).filter(a=>a.id.startsWith('commons-'));
 assert.deepEqual(assets.map(a=>a.id).sort(),expected);
 for(const a of assets){
  assert.equal(a.provenance.sourceCommit,sourceCommit);
  assert.equal(a.provenance.sourceUrl,`https://github.com/Xenoah/vrcworld_tech-tech-cafe/tree/${sourceCommit}`);
  assert.ok(a.provenance.sourceObjects.length>0);
  assert.equal(new Set(a.provenance.sourceObjects).size,a.provenance.sourceObjects.length);
  assert.ok(a.provenance.sourceObjects.every(name=>/^(FURN_|LGT_|AV_)/.test(name)));
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
