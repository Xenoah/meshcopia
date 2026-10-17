// A clickable Release URL alone is not evidence of readable CORS bytes.
import {chromium} from '@playwright/test';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const proof=JSON.parse(await readFile('docs/fbx-minimal-publication/fbx-minimal-v1.0.0-T-evidence.json'));
const rows=['atelier-lamp.fbx','commons-bar-stool.fbx'].map(name=>proof.assets.find(x=>x.name===name));
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
try {
 const page=await browser.newPage();
 await page.goto('https://xenoah.github.io/meshcopia/',{waitUntil:'domcontentloaded'});
 const results=await page.evaluate(async rows=>{
  const results=[];
  for(const row of rows){
   const url=`https://api.github.com/repos/Xenoah/meshcopia/releases/assets/${row.assetId}`;
   const response=await fetch(url,{headers:{Accept:'application/octet-stream'},mode:'cors',credentials:'omit',cache:'no-cache',referrerPolicy:'no-referrer'});
   const data=await response.arrayBuffer();
   const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(b=>b.toString(16).padStart(2,'0')).join('');
   results.push({name:row.name,url,status:response.status,type:response.type,bytes:data.byteLength,sha256});
  }
  return results;
 },rows);
 for(const [i,row] of results.entries()){
  assert.equal(row.status,200);assert.equal(row.type,'cors');
  assert.equal(row.bytes,rows[i].bytes);assert.equal(row.sha256,rows[i].sha256);
 }
 await mkdir('test-results',{recursive:true});
 await writeFile('test-results/fbx-transport.json',JSON.stringify({origin:'https://xenoah.github.io',results},null,2)+'\n');
 console.log('Verified anonymous browser CORS and exact FBX bytes:',results.map(x=>x.name).join(', '));
} finally {await browser.close();}
