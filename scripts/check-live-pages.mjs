// Read only: compare the deployed API and anonymous same-origin transport with
// the exact Pages artifact from this publication run. No routing or mock bytes.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {chromium} from '@playwright/test';
import {SITE,sha256,measureDist} from './lib/download-browser-contract.mjs';
const expected=await readFile('dist/api/catalog.json');
const catalog=JSON.parse(expected);
assert.equal(catalog.schemaVersion,'3.0.0');assert.equal(catalog.count,173);
const dist=await measureDist('dist');
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({serviceWorkers:'block'}),page=await context.newPage();
 await page.goto(SITE,{waitUntil:'domcontentloaded'});
 const record=await page.evaluate(async({site,asset})=>{
  async function get(url){
   const response=await fetch(url,{credentials:'omit',cache:'no-store',redirect:'error'});
   if(!response.ok||response.type==='opaque')throw Error(`Anonymous GET failed: ${response.status} ${url}`);
   const bytes=new Uint8Array(await response.arrayBuffer());
   const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
   return {url:response.url,status:response.status,type:response.type,bytes:bytes.length,sha256,contentType:response.headers.get('content-type'),contentEncoding:response.headers.get('content-encoding'),data:bytes};
  }
  const api=await get(site+'api/catalog.json');delete api.data;
  const manifest=await get(asset.downloads.delivery.files[0].fetch.url);
  const first=JSON.parse(new TextDecoder().decode(manifest.data)).chunks[0];delete manifest.data;
  const chunk=await get(new URL(first.packedSha256+'.gz',manifest.url).href);delete chunk.data;
  return {api,manifest,chunk,expectedChunk:first,credentials:'omit',routingSubstitution:false};
 },{site:SITE,asset:catalog.assets.find(a=>a.id==='studio-chair')});
 assert.equal(record.api.sha256,sha256(expected));assert.equal(record.api.bytes,expected.length);
 const transport=catalog.assets.find(a=>a.id==='studio-chair').downloads.delivery.files[0].fetch;
 assert.equal(record.manifest.sha256,transport.sha256);assert.equal(record.manifest.bytes,transport.bytes);
 assert.equal(record.chunk.sha256,record.expectedChunk.packedSha256);assert.equal(record.chunk.bytes,record.expectedChunk.packedBytes);
 for(const item of [record.api,record.manifest,record.chunk])assert.equal(new URL(item.url).origin,new URL(SITE).origin);
 const evidence={status:'passed',sourceCommit:process.env.GITHUB_SHA,runId:process.env.GITHUB_RUN_ID,publicAssets:catalog.count,models:catalog.assets.filter(a=>a.type==='model').length,textures:catalog.assets.filter(a=>a.type==='texture').length,dist,...record};
 await mkdir('test-results',{recursive:true});await writeFile('test-results/live-pages.json',JSON.stringify(evidence,null,2)+'\n');
 console.log(JSON.stringify(evidence,null,2));
}finally{await browser.close();}
