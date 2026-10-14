import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import validator from 'gltf-validator';
import {Matrix4,Vector3,Quaternion} from 'three';
import {readCatalog,sha256} from '../scripts/lib/catalog.mjs';

function values(doc,binary,index) {
 const a=doc.accessors[index],v=doc.bufferViews[a.bufferView],count={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];
 const bytes={5121:1,5123:2,5125:4,5126:4}[a.componentType],read={5121:'readUInt8',5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'}[a.componentType];
 assert.ok(bytes&&read&&count);
 const start=(v.byteOffset||0)+(a.byteOffset||0),stride=v.byteStride||count*bytes;
 return Array.from({length:a.count},(_,i)=>Array.from({length:count},(_,j)=>binary[read](start+i*stride+j*bytes)));
}
test('Original city assets are self-contained, grounded, dimensioned and validator-clean',async()=>{
 const assets=(await readCatalog(process.env.CITY_ASSET_ROOT)).filter(a=>a.id.startsWith('city-'));
 const expected=JSON.parse(await readFile(process.env.CITY_ASSET_ROSTER||new URL('../docs/city-assets.json',import.meta.url),'utf8'));
 assert.deepEqual(assets.map(a=>a.id).sort(),expected.ids.slice().sort(),'explicit city collection roster');
 const hashes=new Set();
 for(const a of assets){
  assert.equal(a.type,'model');assert.equal(a.unit,'m');assert.equal(a.upAxis,'Y');assert.equal(a.license,'CC-BY-4.0');
  assert.ok(a.usages.some(u=>u.relationship==='original'&&u.project==='Meshcopia'&&u.selectors.includes(a.id)));
  assert.ok(a.provenance.generatorUrl.startsWith('https://github.com/Xenoah/meshcopia/'));
  const raw=await readFile(path.join(a.dir,'source',a.preview)),hash=sha256(raw);
  assert.equal(hash,a.provenance.sourceSha256);assert.ok(!hashes.has(hash),'duplicate city GLB');hashes.add(hash);
  const report=await validator.validateBytes(new Uint8Array(raw),{uri:a.preview,maxIssues:50,writeTimestamp:false});
  assert.equal(report.issues.numErrors,0,a.id+': '+JSON.stringify(report.issues.messages));
  const size=raw.readUInt32LE(12),doc=JSON.parse(raw.subarray(20,20+size).toString()),binary=raw.subarray(28+size);
  assert.ok(doc.buffers.every(b=>!b.uri));assert.ok((doc.images||[]).every(i=>!i.uri));
  assert.equal(doc.cameras,undefined);assert.equal(doc.animations,undefined);assert.ok(doc.materials.length>0);
  const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];let triangles=0;
  function visit(index,parent){
   const n=doc.nodes[index],local=n.matrix?new Matrix4().fromArray(n.matrix):new Matrix4().compose(new Vector3(...(n.translation||[0,0,0])),new Quaternion(...(n.rotation||[0,0,0,1])),new Vector3(...(n.scale||[1,1,1])));
   const world=parent.clone().multiply(local);
   if(n.mesh!==undefined){
    assert.ok(n.name&&n.name.length>0);
    for(const p of doc.meshes[n.mesh].primitives){
     assert.equal(p.mode??4,4);assert.ok(p.attributes.NORMAL!==undefined);assert.ok(p.attributes.TEXCOORD_0!==undefined);
     const verts=values(doc,binary,p.attributes.POSITION),normals=values(doc,binary,p.attributes.NORMAL),uvs=values(doc,binary,p.attributes.TEXCOORD_0);
     for(const v of uvs)assert.ok(v.every(Number.isFinite));
     for(const v of verts){const q=new Vector3(...v).applyMatrix4(world);for(let i=0;i<3;i++){assert.ok(Number.isFinite(q.getComponent(i)));low[i]=Math.min(low[i],q.getComponent(i));high[i]=Math.max(high[i],q.getComponent(i));}}
     for(const norm of normals)assert.ok(Math.abs(Math.hypot(...norm)-1)<.002,a.id+': non-unit normal');
     const indices=p.indices===undefined?verts.map((_,i)=>i):values(doc,binary,p.indices).map(v=>v[0]);
     assert.equal(indices.length%3,0);triangles+=indices.length/3;
     for(let i=0;i<indices.length;i+=3){
      const x=new Vector3(...verts[indices[i]]),y=new Vector3(...verts[indices[i+1]]),z=new Vector3(...verts[indices[i+2]]);
      assert.ok(y.sub(x).cross(z.sub(x)).lengthSq()>1e-20,a.id+': degenerate triangle in '+n.name);
     }
    }
   }
   for(const child of n.children||[])visit(child,world);
  }
  for(const node of doc.scenes[doc.scene||0].nodes)visit(node,new Matrix4());
  assert.equal(triangles,a.triangles,a.id+': triangle count');
  assert.ok(Math.abs(low[1])<1e-4,a.id+': base not grounded');
  for(let i=0;i<3;i++)assert.ok(Math.abs(high[i]-low[i]-a.dimensions[i])<1e-4,a.id+': dimension axis '+i);
  for(const i of [0,2])assert.ok(Math.abs(high[i]+low[i])<1e-4,a.id+': centered pivot axis '+i);
  const stl=await readFile(path.join(a.dir,'source',a.id+'.stl'));
  assert.equal(stl.readUInt32LE(80),triangles);assert.equal(stl.length,84+50*triangles);
  if(a.provenance.stlSha256)assert.equal(sha256(stl),a.provenance.stlSha256);
  const slo=[Infinity,Infinity,Infinity],shi=[-Infinity,-Infinity,-Infinity];
  for(let t=0;t<triangles;t++)for(let v=0;v<3;v++)for(let axis=0;axis<3;axis++){
   const coordinate=stl.readFloatLE(84+t*50+12+v*12+axis*4);assert.ok(Number.isFinite(coordinate));
   slo[axis]=Math.min(slo[axis],coordinate);shi[axis]=Math.max(shi[axis],coordinate);
  }
  for(let axis=0;axis<3;axis++){assert.ok(Math.abs(slo[axis]-low[axis])<1e-5,a.id+': STL low bound');assert.ok(Math.abs(shi[axis]-high[axis])<1e-5,a.id+': STL high bound');}

 }
});
