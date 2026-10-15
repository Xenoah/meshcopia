import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
const browser=await chromium.launch({...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),headless:true,args:['--no-sandbox']});
try{
 const page=await browser.newPage();await page.goto('https://xenoah.github.io/meshcopia/',{waitUntil:'domcontentloaded'});
 const source=await fs.readFile(new URL('../src/lib/batch-download.mjs',import.meta.url),'utf8');
 const result=await page.evaluate(async source=>{
  const lib=await import(URL.createObjectURL(new Blob([source],{type:'text/javascript'})));
  const catalog=await(await fetch('/meshcopia/api/catalog.json')).json();
  const expectedIds=['studio-chair','sage-terrazzo'];
  const assets=catalog.assets.filter(a=>expectedIds.includes(a.id));
  if(assets.length!==expectedIds.length||!expectedIds.every(id=>assets.some(a=>a.id===id)))throw new Error('Missing or duplicate expected live proof assets');
  for(const a of assets){const text=`${a.titleEn}\nCreator: ${a.author}\nSource: ${a.pageUrl}\nLicense: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nCredit the creator and source; identify changes.\n`;const data=new TextEncoder().encode(text);const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(b=>b.toString(16).padStart(2,'0')).join('');a.downloads.minimal={id:a.id,assetVersion:a.version,contentPolicy:lib.POLICY,noticeFile:'LICENSE.txt',notice:{filename:'LICENSE.txt',text,bytes:data.length,sha256},sourceFiles:a.files.map(({name,bytes,sha256})=>({name,bytes,sha256}))};}
  const plan=lib.planBundle(assets);const blob=await lib.buildBundle(plan);const array=new Uint8Array(await blob.arrayBuffer());let binary='';for(const byte of array)binary+=String.fromCharCode(byte);
  const chair=assets.find(a=>a.id==='studio-chair');const raw=chair.files.find(f=>f.name.endsWith('.glb'));if(!raw)throw new Error('studio-chair GLB is missing');const rawURL=`https://raw.githubusercontent.com/Xenoah/meshcopia/main/content/assets/${chair.id}/source/${raw.name}`;const response=await fetch(rawURL,{mode:'cors'});const rawBytes=await response.arrayBuffer();const rawHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',rawBytes))].map(b=>b.toString(16).padStart(2,'0')).join('');if(response.status!==200||rawHash!==raw.sha256)throw new Error('raw source integrity failure');
  return {origin:location.origin,ids:assets.map(a=>a.id),entries:plan.entries.map(({name,bytes,sha256})=>({name,bytes,sha256})),bytes:blob.size,zip:btoa(binary),raw:{url:rawURL,status:response.status,type:response.type,bytes:rawBytes.byteLength,sha256:rawHash}};
 },source);
 await fs.writeFile(new URL('../live-browser-proof.zip',import.meta.url),Buffer.from(result.zip,'base64'));delete result.zip;
 const {spawnSync}=await import('node:child_process');const check=spawnSync('python3',['-c',"import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None; names=z.namelist(); assert names.count('LICENSE.txt')==1; assert len(names)==9; assert all(n=='LICENSE.txt' or n.count('/')==1 for n in names); assert not any(n.endswith('.zip') for n in names); print(names)",new URL('../live-browser-proof.zip',import.meta.url).pathname]);if(check.status!==0)throw new Error(check.stderr.toString());result.extractionVerified=true;
 await fs.writeFile(new URL('../live-browser-proof.json',import.meta.url),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}finally{await browser.close();}
