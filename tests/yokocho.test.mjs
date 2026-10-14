import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import validator from 'gltf-validator';
import {readCatalog,sha256,attributionFor} from '../scripts/lib/catalog.mjs';
const sourceCommit='97091c96cf66a0f67b952827a753a448768f175a';

test('Yokocho collection has explicit original provenance and unique useful downloads', async()=>{
 const assets=(await readCatalog()).filter(a=>a.id.startsWith('yokocho-'));
 assert.equal(assets.filter(a=>a.type==='model').length,39);
 assert.equal(assets.filter(a=>a.type==='texture').length,21);
 const seen=new Set();
 for(const a of assets){
  if(a.id.startsWith('yokocho-entry-')){
   assert.equal(a.provenance.sourceCommit,undefined);
   assert.ok(a.provenance.sourceUrl.endsWith('docs/YOKOCHO_IMPORT.md#entry-plaza'));
  }else{
   assert.equal(a.provenance.sourceCommit,sourceCommit);
   assert.equal(a.provenance.sourceUrl,`https://github.com/Xenoah/vrcworld_jujo-yokocho/tree/${sourceCommit}`);
  }
  assert.equal(a.usages[0].relationship,'original');
  assert.ok(a.usages[0].sourcePaths.length>0);
  assert.ok(attributionFor(a).includes(a.provenance.sourceUrl));
  assert.ok(a.provenance.changes);
  const raw=await readFile(path.join(a.dir,'source',a.type==='model'?a.preview:a.maps.baseColor));
  const hash=sha256(raw); assert.ok(!seen.has(hash),`${a.id}: exact duplicate primary file`); seen.add(hash);
  if(a.type==='texture'){
   assert.equal(a.provenance.sourcePixelsUnchanged,true);
   assert.deepEqual(Object.keys(a.maps),['baseColor']);
   assert.equal(a.colorSpaces.baseColor,'sRGB');
   assert.equal(a.normalConvention,undefined);
   assert.ok(Object.values(a.provenance.sourceFiles).includes(hash));
   assert.deepEqual([raw.readUInt32BE(16),raw.readUInt32BE(20)],[a.width,a.height]);
   continue;
  }
  assert.ok(a.provenance.sourceObjects.length>0);
  assert.equal(new Set(a.provenance.sourceObjects).size,a.provenance.sourceObjects.length);
  assert.ok(a.uv);
  const report=await validator.validateBytes(new Uint8Array(raw),{uri:a.preview,maxIssues:30,writeTimestamp:false});
  assert.equal(report.issues.numErrors,0,`${a.id}: ${JSON.stringify(report.issues.messages)}`);
  const length=raw.readUInt32LE(12),doc=JSON.parse(raw.subarray(20,20+length).toString()),binary=raw.subarray(28+length);
  assert.equal(doc.cameras,undefined);assert.equal(doc.animations,undefined);
  assert.ok(doc.buffers.every(b=>!b.uri));
  for(const image of doc.images||[]){
   assert.equal(image.uri,undefined);
   const view=doc.bufferViews[image.bufferView],start=view.byteOffset||0;
   const imageHash=sha256(binary.subarray(start,start+view.byteLength));
   assert.ok(Object.entries(a.provenance.sourceFiles).some(([file,hash])=>file.endsWith('.png')&&hash===imageHash),`${a.id}: unverified embedded image`);
  }
  const stl=await readFile(path.join(a.dir,'source',`${a.id}.stl`));
  assert.equal(stl.readUInt32LE(80),a.triangles);
  const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<a.triangles;i++)for(let v=0;v<3;v++)for(let axis=0;axis<3;axis++){
   const coordinate=stl.readFloatLE(84+i*50+12+v*12+axis*4);assert.ok(Number.isFinite(coordinate));
   low[axis]=Math.min(low[axis],coordinate);high[axis]=Math.max(high[axis],coordinate);
  }
  assert.ok(Math.abs(low[1])<1e-4,`${a.id}: ground pivot`);
  for(let axis=0;axis<3;axis++)assert.ok(Math.abs(high[axis]-low[axis]-a.dimensions[axis])<1e-4,`${a.id}: dimension mismatch`);
 }
});
