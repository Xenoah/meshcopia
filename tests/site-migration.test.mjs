import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import {assertCurrentDownloads,assertNoRetiredLinks} from '../scripts/lib/site-migration.mjs';
import {model} from './delivery-fixtures.mjs';

test('API v3 rejects retired download fields and unavailable current FBX',()=>{
 const asset=model(),catalog={schemaVersion:'3.0.0',count:1,assets:[asset]};
 asset.downloads={delivery:asset.downloads.delivery};
 assertCurrentDownloads(catalog);
 for(const field of ['full','models','direct','minimal']){
  asset.downloads[field]={url:'https://example.invalid/retired.zip'};
  assert.throws(()=>assertCurrentDownloads(catalog),/retired download fields/);delete asset.downloads[field];
 }
 delete asset.downloads.delivery;assert.throws(()=>assertCurrentDownloads(catalog));
});

test('retired URL scanner rejects both absolute API links and local UI links',()=>{
 const archives=[{url:'https://xenoah.github.io/meshcopia/assets/chair/chair-1.0.0.zip'}];
 assertNoRetiredLinks('<a href="https://github.com/Xenoah/meshcopia/releases/download/fbx-minimal-v1.0.0/chair.zip">FBX</a>',archives,'fixture');
 for(const url of [archives[0].url,new URL(archives[0].url).pathname]){
  assert.throws(()=>assertNoRetiredLinks(JSON.stringify({url}),archives,'manifest'),/retired URL referenced/);
  assert.throws(()=>assertNoRetiredLinks(`<a href="${url}">old</a>`,archives,'page'),/retired URL referenced/);
 }
});

test('site release packaging creates no empty or legacy consumer collections',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'site-release-migration-'));
 try{
  await mkdir(path.join(root,'dist/api'),{recursive:true});await mkdir(path.join(root,'dist/assets'));
  await writeFile(path.join(root,'.release.json'),JSON.stringify({version:'1.11.0'}));
  await writeFile(path.join(root,'dist/api/catalog.json'),JSON.stringify({schemaVersion:'3.0.0',assets:[]}));
  execFileSync('python3',[path.resolve('scripts/bundle-release.py')],{cwd:root});
  const sums=await readFile(path.join(root,'release/SHA256SUMS'),'utf8');
  assert.match(sums,/meshcopia-1.11.0-site.zip/);assert.match(sums,/catalog.json/);
  assert.doesNotMatch(sums,/-all.zip|-models.zip|-textures.zip/);
  await writeFile(path.join(root,'release/meshcopia-1.11.0-models.zip'),'stale generated output');
  execFileSync('python3',[path.resolve('scripts/bundle-release.py')],{cwd:root});
  await assert.rejects(readFile(path.join(root,'release/meshcopia-1.11.0-models.zip')),{code:'ENOENT'});
  await writeFile(path.join(root,'dist/assets/old.zip'),'retired');
  assert.throws(()=>execFileSync('python3',[path.resolve('scripts/bundle-release.py')],{cwd:root,stdio:'pipe'}));
 }finally{await rm(root,{recursive:true,force:true});}
});
