import {model} from './delivery-fixtures.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,mkdir,writeFile,rm,symlink} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';import {execFileSync} from 'node:child_process';
import {writeStoreZip} from '../scripts/lib/zip-store.mjs';
import {SITE,RELEASE,sha256,assertNotice,assertActivatedCatalog,expectedDetail,expectedZipEntries,verifyBrowserZip,measureDist} from '../scripts/lib/download-browser-contract.mjs';
const notice=text=>({filename:'LICENSE.txt',text,bytes:Buffer.byteLength(text),sha256:sha256(text)});
function asset(id,type='model'){
 const data=Buffer.from(type),name=type==='model'?'model.glb':'color.png',file={name,format:type==='model'?'GLB':'PNG',bytes:data.length,sha256:sha256(data),url:`${SITE}assets/${id}/source/${name}`};
 const result={id,type,version:'1.0.0',status:'public',files:[file],downloads:{minimal:{schemaVersion:1,id,assetVersion:'1.0.0',packageVersion:'1.0.0',contentPolicy:'asset-files-required-dependencies-single-notice-v1',noticeFile:'LICENSE.txt',notice:notice(`Fixture legal notice: ${id}\n`),sourceFiles:[file],bytes:1,sha256:'1'.repeat(64),url:`https://github.com/Xenoah/meshcopia/releases/download/minimal-v1.0.0/${id}-1.0.0-minimal-1.0.0.zip`,verification:{state:'published-verified',releaseTag:RELEASE.releaseTag,archiveSha256:'1'.repeat(64)}}}};
 if(type==='model'){result.downloads.delivery=model(id,type).downloads.delivery;result.downloads.delivery.sourceFiles=[file];result.downloads.delivery.notice=result.downloads.minimal.notice;delete result.downloads.minimal;}
 return result;
}
test('catalog contract rejects missing readiness, changed original bytes and partial cohorts',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'p-catalog-test-'));try{
  await mkdir(path.join(root,'source'));await writeFile(path.join(root,'source/model.glb'),'model');await writeFile(path.join(root,'source/color.png'),'texture');
  const assets=Array.from({length:173},(_,i)=>asset(`asset-${i}`,i<137?'model':'texture'));
  const sources=assets.map(a=>({...a,dir:root,sources:a.files.map(f=>f.name)}));await assertActivatedCatalog(assets,sources);
  await assert.rejects(()=>assertActivatedCatalog(assets.slice(1),sources));
  const changed=structuredClone(assets);changed[0].files[0].bytes++;await assert.rejects(()=>assertActivatedCatalog(changed,sources));
  const absent=structuredClone(assets);delete absent[0].downloads.delivery;await assert.rejects(()=>assertActivatedCatalog(absent,sources));
 }finally{await rm(root,{recursive:true,force:true});}
});
test('ZIP checker binds exact original payloads and one exact aggregate legal notice',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'p-zip-test-'));try{
  const assets=[asset('chair'),asset('stone','texture')];const entries=expectedZipEntries(assets);
  assert.equal(entries.at(-1).name,'LICENSE.txt');assert.equal(entries.at(-1).sha256,sha256('=== chair ===\nFixture legal notice: chair\n\n\n=== stone ===\nFixture legal notice: stone\n'));
  const payload=assets.map(a=>({name:`${a.id}/${(a.downloads.delivery?.files??a.files)[0].name}`,data:Buffer.from(a.type)}));
  const legal={name:'LICENSE.txt',data:assets.map(a=>`=== ${a.id} ===\n${(a.downloads.delivery??a.downloads.minimal).notice.text}`).join('\n\n')};
  const file=path.join(root,'bulk.zip');await writeStoreZip(file,[...payload,legal]);await verifyBrowserZip(file,assets);
  await writeStoreZip(file,[...payload,{...legal,data:legal.data+'changed'}]);await assert.rejects(()=>verifyBrowserZip(file,assets));
  await writeStoreZip(file,[...payload,legal,{name:'README.md',data:'extra'}]);await assert.rejects(()=>verifyBrowserZip(file,assets));
  const single=path.join(root,'single.zip'),a=assets[0];await writeStoreZip(single,[{name:(a.downloads.delivery?.files??a.files)[0].name,data:a.type},{name:'LICENSE.txt',data:a.downloads.delivery.notice.text}]);const bytes=await readFile(single);a.downloads.delivery.archive.bytes=bytes.length;a.downloads.delivery.archive.sha256=sha256(bytes);await verifyBrowserZip(single,[a],{individual:true});a.downloads.delivery.archive.sha256='0'.repeat(64);await assert.rejects(()=>verifyBrowserZip(single,[a],{individual:true}));
 }finally{await rm(root,{recursive:true,force:true});}
});
test('notice hash and original standalone links are verified without generating replacements',()=>{
 const a=asset('chair');assertNotice(a.downloads.delivery.notice);assert.deepEqual(expectedDetail(a).direct,[a.downloads.delivery.files[0].url]);a.downloads.delivery.notice.text+='changed';assert.throws(()=>assertNotice(a.downloads.delivery.notice));
});
test('Pages measurement rejects symlinks and retains the 950000000-byte ceiling',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'p-dist-test-'));try{
  await writeFile(path.join(root,'file'),'123');assert.deepEqual(await measureDist(root),{bytes:3,files:1,budgetBytes:950000000});await symlink('file',path.join(root,'link'));await assert.rejects(()=>measureDist(root));
 }finally{await rm(root,{recursive:true,force:true});}
});
test('full browser test parses and cannot inject candidate readiness or application modules',async()=>{
 const file=new URL('../scripts/test-minimal-downloads-browser.mjs',import.meta.url);execFileSync(process.execPath,['--check',file.pathname]);const source=await readFile(file,'utf8');
 assert.doesNotMatch(source,/downloads\.minimal\s*=|catalog-data['"]\)\.textContent\s*=|import\(URL\.createObjectURL|addInitScript|setContent\(/);
 assert.match(source,/for\(const a of catalog\)/);assert.match(source,/verifyBrowserZip/);assert.match(source,/toBeFocused/);assert.match(source,/route\.abort\('failed'\)/);
 const inputs=await readFile(new URL('../scripts/check-full-p-inputs.mjs',import.meta.url),'utf8');for(const name of ['scripts/minimal-verification/common.py','scripts/minimal_packages.py','scripts/minimal_notices.py'])assert.ok(inputs.includes(name));
});
