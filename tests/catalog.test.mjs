import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,rm,symlink} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
import {readCatalog,readAsset,safeRelative} from '../scripts/lib/catalog.mjs';
import {filterAssets} from '../src/lib/catalog-ui.js';
import {writeStoreZip} from '../scripts/lib/zip-store.mjs';

test('unsafe asset paths cannot escape the package',()=>{
 for(const value of ['../secret','a/../../b','/tmp/a','a\\b','a//b','a/./b','file:thing','a?x','a#x','a\0b'])assert.throws(()=>safeRelative(value));
 assert.equal(safeRelative('textures/base color.png'),'textures/base color.png');
});
test('all source assets have declared rights and structurally valid GLB/STL data',async()=>{
 const assets=await readCatalog();assert.ok(assets.length>=14);
 for(const a of assets){
  assert.equal(a.license,'CC-BY-4.0');
  if(a.type!=='model')continue;
  const b=await readFile(path.join(a.dir,'source',a.preview));assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.readUInt32LE(4),2);assert.equal(b.readUInt32LE(8),b.length);
  const json=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());assert.equal(json.asset.version,'2.0');
  const count=json.meshes.reduce((n,m)=>n+m.primitives.reduce((sum,p)=>sum+json.accessors[p.indices??p.attributes.POSITION].count/3,0),0);assert.equal(count,a.triangles);
  const stl=await readFile(path.join(a.dir,'source',`${a.id}.stl`));assert.equal(stl.readUInt32LE(80),a.triangles);assert.equal(stl.length,84+50*a.triangles);
 }
});
test('public search covers Japanese, English and formats, with cumulative filters',async()=>{
 const assets=(await readCatalog()).map(a=>({...a,files:a.sources.map(name=>({format:name.split('.').pop().toUpperCase()})),downloads:{full:{bytes:a.id.length}}}));
 assert.ok(filterAssets(assets,{query:'椅子'}).some(a=>a.id==='studio-chair'));
 assert.ok(filterAssets(assets,{query:'chair glb'}).some(a=>a.id==='studio-chair'));
 assert.deepEqual(filterAssets(assets,{type:'texture'}).map(a=>a.id).sort(),assets.filter(a=>a.type==='texture').map(a=>a.id).sort());
 const furniture=filterAssets(assets,{type:'model',category:'furniture'});assert.ok(furniture.length>=2);assert.ok(furniture.every(a=>a.type==='model'&&a.category==='furniture'));
 assert.equal(filterAssets(assets,{query:'not-a-real-item'}).length,0);assert.equal(filterAssets(assets,{type:'model',query:'seamless'}).length,0);
 const sorted=filterAssets(assets,{sort:'size'});assert.ok(sorted.every((a,i)=>!i||a.downloads.full.bytes>=sorted[i-1].downloads.full.bytes));
});
test('ZIPs are deterministic and use UTF-8 names',async()=>{
 const dir=await mkdtemp(path.join(os.tmpdir(),'meshcopia-zip-'));
 try{const entries=[{name:'テスト.obj',data:'o example\n'},{name:'LICENSE.txt',data:'CC-BY-4.0'}];await writeStoreZip(`${dir}/a.zip`,entries);await writeStoreZip(`${dir}/b.zip`,entries);const a=await readFile(`${dir}/a.zip`);assert.deepEqual(a,await readFile(`${dir}/b.zip`));assert.equal(a.readUInt32LE(0),0x04034b50);assert.equal(a.readUInt16LE(6),0x0800);}finally{await rm(dir,{recursive:true,force:true})}
});
test('metadata gate rejects unlicensed assets, missing files and symlinks',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'meshcopia-gate-')),dir=`${root}/test-asset`;
 try{await mkdir(`${dir}/source`,{recursive:true});const a={...(await readCatalog())[0],id:'test-asset',thumbnail:'preview.webp',preview:'test.glb',type:'model',unit:'m',upAxis:'Y',triangles:1};delete a.dir;delete a.sources;
 await writeFile(`${dir}/source/test.glb`,'test');await writeFile(`${dir}/preview.webp`,'test');const save=()=>writeFile(`${dir}/asset.json`,JSON.stringify(a));await save();
 a.license='CC-BY-NC-4.0';await save();await assert.rejects(()=>readAsset(dir),/Only explicitly/);
 a.license='CC-BY-4.0';a.preview='missing.glb';await save();await assert.rejects(()=>readAsset(dir),/preview not found/);
 a.preview='test.glb';await save();await symlink('/etc/hosts',`${dir}/source/escape.png`);await assert.rejects(()=>readAsset(dir),/Symlinks/);
 }finally{await rm(root,{recursive:true,force:true})}
});
