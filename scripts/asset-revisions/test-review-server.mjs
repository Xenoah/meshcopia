// Fast transport regression before costly full-catalog verification.
// The loopback option diagnoses local TLS where the environment forces a proxy;
// CI always uses the canonical origin, exactly as the complete UI test does.
import {chromium} from '@playwright/test';
import {readFile,writeFile,mkdtemp,rm,cp} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import {sha256,SITE} from '../lib/download-browser-contract.mjs';
import {serveReview} from './serve-review.mjs';
const input='.cache/asset-revision-qa/candidate-final',records=JSON.parse(await readFile(`${input}/candidate-packages.json`)).records;
const folder=await mkdtemp(path.join(tmpdir(),'meshcopia-download-probe-'));
for(const r of records)await cp(`${input}/${r.archive}`,`${folder}/${r.id}.zip`);
await writeFile(`${folder}/index.html`,records.map(r=>`<a href="${r.id}.zip" download>${r.id}</a>`).join('\n'));
const server=await serveReview(folder),loopback=process.argv.includes('--loopback');let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:loopback?[]:server.args});
 const context=await browser.newContext({acceptDownloads:true,ignoreHTTPSErrors:true}),page=await context.newPage();
 await page.goto(loopback?`https://localhost:${server.port}/meshcopia/`:SITE);
 for(const r of records){
  const pending=page.waitForEvent('download',{timeout:20000});await page.getByRole('link',{name:r.id,exact:true}).click();const d=await pending;
  assert.equal(await d.failure(),null);const bytes=await readFile(await d.path());assert.equal(bytes.length,r.archiveBytes);assert.equal(sha256(bytes),r.archiveSha256);
  assert.ok(server.served.some(request=>request.path===`/meshcopia/${r.id}.zip`&&request.bytes===r.archiveBytes));
 }
 console.log(JSON.stringify({scope:'Real HTTPS native-download transport probe; not the complete catalog UI',canonicalOrigin:!loopback,downloads:records.map(r=>({id:r.id,bytes:r.archiveBytes,sha256:r.archiveSha256}))}));
}finally{await browser?.close();await server.close();await rm(folder,{recursive:true,force:true})}
