import {chromium,expect} from '@playwright/test';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {formatBytes} from '../../src/lib/file-size.mjs';
import {SITE,sha256,verifyBrowserZip,expectedZipEntries,measureDist} from '../lib/download-browser-contract.mjs';
const root=path.resolve('dist'),out='test-results/asset-revisions/browser';await mkdir(out,{recursive:true});
const document=JSON.parse(await readFile('dist/api/catalog.json')),assets=document.assets;
assert.equal(document.publicationState,'unpublished-candidate');assert.equal(document.count,455);
const selected=['garden-arch','household-two-door-refrigerator','city-front-loading-washing-machine','sage-terrazzo'].map(id=>assets.find(a=>a.id===id));
const entries=expectedZipEntries(selected),estimate=22+entries.reduce((n,e)=>n+e.bytes+76+2*Buffer.byteLength(e.name),0);
const evidence={state:'running',publicationPerformed:false,sourceCommit:process.env.GITHUB_SHA??null,assets:assets.length,dist:await measureDist(root),individual:[],bulk:[],previews:[],oldUrls:[]};
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm','.glb':'model/gltf-binary','.zip':'application/zip'};
async function context(mobile=false){
 const ctx=await browser.newContext({acceptDownloads:true,serviceWorkers:'block',viewport:mobile?{width:390,height:844}:{width:1440,height:1050},isMobile:mobile,hasTouch:mobile});
 // Actual built bytes mounted at the canonical origin, preserving fetch rules.
 await ctx.route(`${SITE}**`,async route=>{try{let file=path.resolve(root,decodeURIComponent(new URL(route.request().url()).pathname.slice('/meshcopia/'.length)));assert.ok(file===root||file.startsWith(root+path.sep));if((await stat(file)).isDirectory())file=path.join(file,'index.html');await route.fulfill({status:200,contentType:types[path.extname(file)]??'application/octet-stream',body:await readFile(file)})}catch{await route.fulfill({status:404,body:'Missing built file'})}});return ctx;
}
try{
 for(const mobile of [false,true]){
  const ctx=await context(mobile),page=await ctx.newPage(),mode=mobile?'mobile':'desktop',errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(SITE);await expect(page.locator('#batch-download-bar')).toBeVisible();
  assert.equal(await page.locator('#asset-grid [data-card]').count(),455);assert.equal(await page.locator('[role="note"]').textContent(),'未公開の検証ビルド — 修正版と冷蔵庫の候補。公開サイトへの反映は未実施です。');
  assert.deepEqual(JSON.parse(await page.locator('#catalog-data').textContent()),assets);
  for(const [query,id] of [['冷蔵庫','household-two-door-refrigerator'],['洗濯機','city-front-loading-washing-machine']]){await page.locator('#asset-search').fill(query);await expect(page.locator(`[data-preview="${id}"]`)).toBeVisible()}
  await page.locator('#asset-search').fill('');
  for(const a of selected)await page.locator(`[data-asset-select="${a.id}"]`).check();
  const counter=page.locator('#batch-download-bar button'),dialog=page.locator('#batch-selection-dialog');await expect(counter).toHaveText(`4 件選択 · ZIP 約 ${formatBytes(estimate)}`);
  await counter.click();await page.goBack();await expect(dialog).toBeHidden();await expect(counter).toBeEnabled();
  await counter.click();await page.keyboard.press('Escape');await expect(dialog).toBeHidden();await counter.click();
  const prepare=dialog.getByRole('button',{name:'選択素材を1 ZIPにまとめる',exact:true}),save=dialog.getByRole('link',{name:'1 ZIPを保存',exact:true}),source=selected[0].downloads.delivery.files[0].fetch.url;
  let release,calls=0;const held=new Promise(resolve=>release=resolve);const hold=async route=>{calls++;await held;await route.abort().catch(()=>{})};await page.route(source,hold);
  await prepare.click();await expect.poll(()=>calls).toBe(1);await dialog.getByRole('button',{name:'キャンセル',exact:true}).click();await expect(dialog.getByRole('status')).toContainText('キャンセルしました');await expect(save).toHaveCount(0);release();await page.unroute(source,hold,{behavior:'wait'});
  const fail=route=>route.abort('failed');await page.route(source,fail);await prepare.click();await expect(dialog.getByRole('status')).toContainText('失敗');await expect(save).toHaveCount(0);await page.unroute(source,fail);
  await prepare.click();await expect(save).toBeVisible({timeout:90000});await expect(counter).toHaveText(`4 件選択 · ZIP ${formatBytes(estimate)}`);
  const pending=page.waitForEvent('download');await save.click();const download=await pending,file=`${out}/mixed-${mode}.zip`;assert.equal(await download.failure(),null);await download.saveAs(file);const proof=await verifyBrowserZip(file,selected);assert.equal(proof.bytes,estimate);evidence.bulk.push({mode,estimate,...proof});
  await dialog.locator('li button').first().click();await expect(counter).toHaveText(/^3 件選択/);await dialog.getByRole('button',{name:'選択解除',exact:true}).click();await expect(dialog.locator('li')).toHaveCount(0);await dialog.getByRole('button',{name:'閉じる',exact:true}).click();
  for(const id of ['garden-arch','wayfinding-sign','household-two-door-refrigerator','city-front-loading-washing-machine']){
   const asset=assets.find(a=>a.id===id);await page.goto(SITE+`assets/${id}/`);await expect(page.locator('.model-viewer-status')).toHaveText('GLB preview',{timeout:60000});
   await page.waitForFunction(()=>[...document.querySelectorAll('canvas')].some(c=>c.width>0&&c.height>0));
   await expect(page.locator('.download-primary')).toHaveAttribute('href',asset.downloads.delivery.archive.url.replace('https://xenoah.github.io',''));
   if(!mobile&&id!=='city-front-loading-washing-machine'){
    const pending=page.waitForEvent('download');await page.locator('.download-primary').click();const download=await pending,file=`${out}/${id}.zip`;assert.equal(await download.failure(),null);await download.saveAs(file);evidence.individual.push({id,...await verifyBrowserZip(file,[asset],{individual:true})});
   }
   await page.screenshot({path:`${out}/${id}-${mode}.png`});evidence.previews.push({id,mode});
  }
  if(!mobile)for(const id of ['garden-arch','wayfinding-sign'])for(const f of assets.find(a=>a.id===id).files.filter(f=>!f.name.includes('1.0.2'))){const response=await page.request.get(f.url);assert.ok(response.ok());const bytes=await response.body();assert.equal(bytes.length,f.bytes);assert.equal(sha256(bytes),f.sha256);evidence.oldUrls.push({url:f.url,bytes:bytes.length,sha256:f.sha256})}
  assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await ctx.close();
 }
 evidence.state='passed';await writeFile(`${out}/report.json`,JSON.stringify(evidence,null,2)+'\n');
}catch(e){evidence.state='failed';evidence.error=e.stack;await writeFile(`${out}/failure.json`,JSON.stringify(evidence,null,2)+'\n');throw e}finally{await browser.close()}
