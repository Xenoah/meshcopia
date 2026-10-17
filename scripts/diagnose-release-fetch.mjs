// Read-only diagnostic, not an activation gate or an alternative transport.
import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage(),errors=[];
 page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text().replace(/https?:\/\/[^\s'"<>]+/g,text=>{try{const u=new URL(text);return u.origin+u.pathname;}catch{return '[URL]';}}));});
 await page.goto('https://xenoah.github.io/meshcopia/',{waitUntil:'domcontentloaded'});
 const results=await page.evaluate(async()=>{
  const rows=[];
  for(const url of ['https://github.com/Xenoah/meshcopia/releases/download/fbx-minimal-v1.0.0/atelier-lamp.fbx','https://api.github.com/repos/Xenoah/meshcopia/releases/assets/645427356']){
   try{const r=await fetch(url,{mode:'cors',credentials:'omit',headers:{Accept:'application/octet-stream'}});rows.push({url,status:r.status,type:r.type,bytes:(await r.arrayBuffer()).byteLength});}
   catch{rows.push({url,readable:false});}
  }
  return rows;
 });
 const report={origin:'https://xenoah.github.io',results,errors};
 await mkdir('test-results',{recursive:true});await writeFile('test-results/release-fetch-diagnostic.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}
