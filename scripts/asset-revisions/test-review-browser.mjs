import {chromium,expect} from '@playwright/test';
import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import path from 'node:path';
import {gunzipSync} from 'node:zlib';
import assert from 'node:assert/strict';
import {isDeepStrictEqual} from 'node:util';
import {formatBytes} from '../../src/lib/file-size.mjs';
import {SITE,sha256,verifyBrowserZip,expectedZipEntries,measureDist} from '../lib/download-browser-contract.mjs';
import {serveReview} from './serve-review.mjs';
const live=process.argv.includes('--live'),production=live||process.argv.includes('--production');
const root=path.resolve('dist'),out='test-results/asset-revisions/'+(live?'live-browser':production?'production-browser':'browser');await mkdir(out,{recursive:true});
const document=JSON.parse(await readFile('dist/api/catalog.json')),assets=document.assets;
if(production){assert.equal(document.schemaVersion,'3.0.0');assert.ok(!document.publicationState);for(const a of assets.filter(a=>a.type==='model'))assert.equal(a.downloads.delivery.verification.state,'published-verified');}else assert.equal(document.publicationState,'unpublished-candidate');assert.equal(document.count,455);
const retained=[];
if(production){
 const old=JSON.parse(await readFile('docs/fbx-minimal-verification/expected137.json')).models.filter(r=>['garden-arch','wayfinding-sign'].includes(r.id));
 for(const name of (await readdir(root+'/download-data')).filter(n=>n.endsWith('.json'))){const bytes=await readFile(root+'/download-data/'+name),m=JSON.parse(bytes),r=old.find(r=>r.fbxSha256===m.sha256);if(!r)continue;
  assert.equal(name,sha256(bytes)+'.json');const parts=[],urls=[{url:SITE+'download-data/'+name,bytes:bytes.length,sha256:sha256(bytes)}];
  for(const c of m.chunks){const b=await readFile(root+'/download-data/'+c.packedSha256+'.gz');assert.equal(b.length,c.packedBytes);assert.equal(sha256(b),c.packedSha256);const raw=gunzipSync(b);assert.equal(raw.length,c.bytes);assert.equal(sha256(raw),c.sha256);parts.push(raw);urls.push({url:SITE+'download-data/'+c.packedSha256+'.gz',bytes:b.length,sha256:sha256(b)});}
  const fbx=Buffer.concat(parts);assert.equal(fbx.length,r.fbxBytes);assert.equal(sha256(fbx),r.fbxSha256);retained.push({id:r.id,urls});
 }
 assert.deepEqual(retained.map(r=>r.id).sort(),['garden-arch','wayfinding-sign']);
}
const selected=['garden-arch','wayfinding-sign','household-two-door-refrigerator','city-front-loading-washing-machine','sage-terrazzo'].map(id=>assets.find(a=>a.id===id));
const entries=expectedZipEntries(selected),estimate=22+entries.reduce((n,e)=>n+e.bytes+76+2*Buffer.byteLength(e.name),0);
const evidence={state:'running',publicationPerformed:false,sourceCommit:process.env.GITHUB_SHA??null,assets:assets.length,dist:await measureDist(root),liveSite:live,localHttpsStaticServer:!live,canonicalOriginPreserved:true,individual:[],bulk:[],previews:[],oldUrls:[],retainedTransports:[]};
const server=live?null:await serveReview(root);let browser;
async function context(mobile=false){
 return browser.newContext({acceptDownloads:true,ignoreHTTPSErrors:!live,serviceWorkers:'block',viewport:mobile?{width:390,height:844}:{width:1440,height:1050},isMobile:mobile,hasTouch:mobile});
}
try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:[...(server?.args??[]),'--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
 for(const mobile of [false,true]){
  const ctx=await context(mobile),page=await ctx.newPage(),mode=mobile?'mobile':'desktop',errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(SITE);await expect(page.locator('#batch-download-bar')).toBeVisible();
  console.log(`REVIEW_BROWSER_STAGE ${mode} catalog-loaded`);
  assert.equal(await page.locator('#asset-grid [data-card]').count(),455);if(production)assert.equal(await page.locator('[role="note"]').count(),0);else assert.equal(await page.locator('[role="note"]').textContent(),'未公開の検証ビルド — 修正版と冷蔵庫の候補。公開サイトへの反映は未実施です。');
  // The page sorts public entries by type/title; the API retains source order.
  // Compare every complete record by ID, without formatting megabytes of array diff.
  const embedded=JSON.parse(await page.locator('#catalog-data').textContent()),byId=new Map(embedded.map(a=>[a.id,a]));
  assert.equal(embedded.length,assets.length);assert.equal(byId.size,assets.length);
  for(const a of assets)assert.ok(isDeepStrictEqual(byId.get(a.id),a),`Embedded catalog differs for ${a.id}`);
  console.log(`REVIEW_BROWSER_STAGE ${mode} all-records-verified-by-id`);
  for(const [query,id] of [['冷蔵庫','household-two-door-refrigerator'],['洗濯機','city-front-loading-washing-machine']]){await page.locator('#asset-search').fill(query);await expect(page.locator(`[data-preview="${id}"]`)).toBeVisible();console.log(`REVIEW_BROWSER_STAGE ${mode} search-verified ${id}`)}
  await page.locator('#asset-search').fill('');
  for(const a of selected){console.log(`REVIEW_BROWSER_STAGE ${mode} selecting ${a.id}`);await page.locator(`[data-asset-select="${a.id}"]`).check();const decoded=await page.locator(`[data-card]:has([data-preview="${a.id}"]) img`).evaluate(async im=>{await Promise.race([im.decode(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Thumbnail decode timed out: '+im.currentSrc)),20000))]);return im.naturalWidth>0&&im.naturalHeight>0});assert.ok(decoded,`Thumbnail decode failed: ${a.id}`);console.log(`REVIEW_BROWSER_STAGE ${mode} thumbnail-verified ${a.id}`)}
  const counter=page.locator('#batch-download-bar button'),dialog=page.locator('#batch-selection-dialog');await expect(counter).toHaveText(`5 件選択 · ZIP 約 ${formatBytes(estimate)}`);
  console.log(`REVIEW_BROWSER_STAGE ${mode} five-selected estimate=${estimate}`);
  await counter.click();await page.goBack();await expect(dialog).toBeHidden();await expect(counter).toBeEnabled();
  await counter.click();await page.keyboard.press('Escape');await expect(dialog).toBeHidden();await counter.click();
  const prepare=dialog.getByRole('button',{name:'選択素材を1 ZIPにまとめる',exact:true}),save=dialog.getByRole('link',{name:'1 ZIPを保存',exact:true}),source=selected[0].downloads.delivery.files[0].fetch.url;
  let release,calls=0;const held=new Promise(resolve=>release=resolve);const hold=async route=>{calls++;await held;await route.abort().catch(()=>{})};await page.route(source,hold);
  await prepare.click();await expect.poll(()=>calls).toBe(1);await dialog.getByRole('button',{name:'キャンセル',exact:true}).click();await expect(dialog.getByRole('status')).toContainText('キャンセルしました');await expect(save).toHaveCount(0);release();await page.unroute(source,hold,{behavior:'wait'});
  const fail=route=>route.abort('failed');await page.route(source,fail);await prepare.click();await expect(dialog.getByRole('status')).toContainText('失敗');await expect(save).toHaveCount(0);await page.unroute(source,fail);
  await prepare.click();await expect(save).toBeVisible({timeout:90000});await expect(counter).toHaveText(`5 件選択 · ZIP ${formatBytes(estimate)}`);
  const pending=page.waitForEvent('download');await save.click();const download=await pending,file=`${out}/mixed-${mode}.zip`;assert.equal(await download.failure(),null);await download.saveAs(file);const proof=await verifyBrowserZip(file,selected);assert.equal(proof.bytes,estimate);evidence.bulk.push({mode,estimate,...proof});
  console.log(`REVIEW_BROWSER_STAGE ${mode} mixed-zip-verified bytes=${proof.bytes}`);
  await dialog.locator('li button').first().click();await expect(counter).toHaveText(/^4 件選択/);await dialog.getByRole('button',{name:'選択解除',exact:true}).click();await expect(dialog.locator('li')).toHaveCount(0);await dialog.getByRole('button',{name:'閉じる',exact:true}).click();
  for(const id of ['garden-arch','wayfinding-sign','household-two-door-refrigerator','city-front-loading-washing-machine']){
   const asset=assets.find(a=>a.id===id);const previewResponse=page.waitForResponse(r=>r.url()===asset.previewUrl&&r.status()===200);await page.goto(SITE+`assets/${id}/`);await expect(page.locator('.model-viewer-status')).toHaveText('GLB preview',{timeout:60000});
   await page.waitForFunction(()=>[...document.querySelectorAll('canvas')].some(c=>c.width>0&&c.height>0));
   const observedPreview=await previewResponse;assert.equal(observedPreview.url(),asset.previewUrl);
   // Chromium may discard the DevTools response body for a cached/consumed GLB.
   // Keep the renderer's actual 200 response assertion, then independently read
   // and hash the same real URL in the browser without substituting any bytes.
   const previewBytes=await page.evaluate(async url=>{const r=await fetch(url,{credentials:'omit',cache:'no-store',redirect:'error'});if(!r.ok)throw Error('Preview byte verification HTTP '+r.status);const b=await r.arrayBuffer();return {bytes:b.byteLength,sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('')};},asset.previewUrl),previewFile=asset.files.find(f=>f.url===asset.previewUrl);assert.equal(previewBytes.bytes,previewFile.bytes);assert.equal(previewBytes.sha256,previewFile.sha256);
   await expect(page.locator('.download-primary')).toHaveAttribute('href',asset.downloads.delivery.archive.url.replace('https://xenoah.github.io',''));
   if(!mobile){
    const pending=page.waitForEvent('download');await page.locator('.download-primary').click();const download=await pending,file=`${out}/${id}.zip`;assert.equal(await download.failure(),null);await download.saveAs(file);const proof=await verifyBrowserZip(file,[asset],{individual:true});
    if(asset.downloads.delivery.verification.state==='local-review-verified')assert.ok(server.served.some(r=>r.path===new URL(asset.downloads.delivery.archive.url).pathname&&r.bytes===proof.bytes));
    evidence.individual.push({id,url:download.url(),...proof});
   }
   await page.screenshot({path:`${out}/${id}-${mode}.png`});evidence.previews.push({id,mode,url:asset.previewUrl,bytes:previewBytes.bytes,sha256:previewFile.sha256});
   console.log(`REVIEW_BROWSER_STAGE ${mode} ${id} preview-verified`);
  }
  if(!mobile){const asset=assets.find(a=>a.id==='sage-terrazzo');await page.goto(SITE+'assets/sage-terrazzo/');const pending=page.waitForEvent('download');await page.locator('.download-primary').click();const download=await pending,file=`${out}/sage-terrazzo.zip`;assert.equal(await download.failure(),null);await download.saveAs(file);evidence.individual.push({id:asset.id,...await verifyBrowserZip(file,[asset],{individual:true})})}
  if(!mobile)for(const id of ['garden-arch','wayfinding-sign'])for(const f of assets.find(a=>a.id===id).files.filter(f=>!f.name.includes('1.0.2'))){
   const built=await page.evaluate(async url=>{const r=await fetch(url);return {status:r.status,bytes:[...new Uint8Array(await r.arrayBuffer())]}},f.url);assert.equal(built.status,200);assert.equal(built.bytes.length,f.bytes);assert.equal(sha256(Buffer.from(built.bytes)),f.sha256);
   const response=await page.request.get(f.url);assert.ok(response.ok());const bytes=await response.body();assert.equal(bytes.length,f.bytes);assert.equal(sha256(bytes),f.sha256);evidence.oldUrls.push({url:f.url,bytes:bytes.length,sha256:f.sha256,candidateAndPublicBytesVerified:true})
  }
  if(!mobile)for(const r of retained){for(const f of r.urls){const b=await page.evaluate(async url=>{const response=await fetch(url);if(!response.ok)throw Error('Retained transport HTTP '+response.status);return [...new Uint8Array(await response.arrayBuffer())]},f.url);assert.equal(b.length,f.bytes);assert.equal(sha256(Buffer.from(b)),f.sha256);}evidence.retainedTransports.push(r);}
  assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await ctx.close();
 }
 evidence.state='passed';await writeFile(`${out}/report.json`,JSON.stringify(evidence,null,2)+'\n');
 console.log('ASSET_REVISION_BROWSER '+JSON.stringify(evidence));
}catch(e){evidence.state='failed';evidence.error=e.stack;await writeFile(`${out}/failure.json`,JSON.stringify(evidence,null,2)+'\n');throw e}finally{await browser?.close();await server?.close()}
