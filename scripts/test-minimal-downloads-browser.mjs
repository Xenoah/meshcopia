import {primaryDownload} from '../src/lib/downloads.mjs';
// Full-P regression: use the built, actually activated catalog and shipped JS.
// No injected catalog, readiness, notices, UI, source responses or ZIP payloads.
import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import path from 'node:path';
import {formatBytes,bundleSizeSummary} from '../src/lib/file-size.mjs';
import {readCatalog} from './lib/catalog.mjs';
import {SITE,RELEASE,sha256,assertActivatedCatalog,expectedDetail,verifyBrowserZip,measureDist} from './lib/download-browser-contract.mjs';

const live=process.argv.includes('--live'),root=path.resolve('dist'),out='test-results/minimal-p-downloads';
const catalogBytes=await readFile(path.join(root,'api/catalog.json'));
assert.equal(JSON.parse(catalogBytes).schemaVersion,'3.0.0');
const catalog=await assertActivatedCatalog(JSON.parse(catalogBytes).assets,await readCatalog());
const dist=await measureDist(root);await mkdir(out,{recursive:true});
const selected=['studio-chair','sage-terrazzo'].map(id=>{const a=catalog.find(a=>a.id===id);assert.ok(a,id);return a;});
const evidence={schemaVersion:1,status:'running',sourceCommit:process.env.GITHUB_SHA??null,runId:process.env.GITHUB_RUN_ID??null,runAttempt:process.env.GITHUB_RUN_ATTEMPT??null,release:RELEASE,catalogSha256:sha256(catalogBytes),dist,scope:{builtDist:true,canonicalOriginRemount:!live,liveSite:live,injectedReadiness:false,injectedNoticeText:false,injectedUI:false,originalAssets:173,models:137,textures:36,fbxCoverage:true,new251Coverage:false,publicationPerformedByThisScript:false},links:[],bulk:[],individual:[],screenshots:[],smallSizes:[]};
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm','.glb':'model/gltf-binary','.zip':'application/zip'};
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
async function context(options={}){
 const context=await browser.newContext({acceptDownloads:true,serviceWorkers:'block',...options});
 if(!live)await context.route(`${SITE}**`,async route=>{
  // Byte-preserving static mount at the production origin. The production
  // same-origin source safety rule is exercised, rather than bypassed.
  const pathname=new URL(route.request().url()).pathname;
  let file=path.resolve(root,decodeURIComponent(pathname.slice('/meshcopia/'.length)));
  assert.ok(file===root||file.startsWith(root+path.sep),'Unsafe dist path');
  try{if((await stat(file)).isDirectory())file=path.join(file,'index.html');await route.fulfill({status:200,contentType:types[path.extname(file)]||'application/octet-stream',body:await readFile(file),headers:{'cache-control':'no-store'}});}
  catch(error){await route.fulfill({status:404,body:`Missing built file: ${path.relative(root,file)}`});}
 });
 return context;
}
async function catalogPage(page){
 await page.goto(SITE,{waitUntil:'domcontentloaded'});await expect(page.locator('#batch-download-bar')).toBeVisible();
 const embedded=await page.locator('#catalog-data').textContent();
 assert.deepEqual(JSON.parse(embedded).sort((a,b)=>a.id.localeCompare(b.id)),[...catalog].sort((a,b)=>a.id.localeCompare(b.id)),'Browser catalog must exactly match verified built catalog');
 if(await page.locator('html').getAttribute('lang')==='en')await page.locator('#language-toggle').click();
}
try{
 const linkContext=await context({viewport:{width:1440,height:1050}}),page=await linkContext.newPage();
 await catalogPage(page);
 const retired=JSON.parse(await readFile('docs/archive-lock.json')).archives.filter(a=>a.id==='studio-chair'||a.id==='cedar-boards');
 evidence.retiredRequests=await page.evaluate(async urls=>Promise.all(urls.map(async url=>({url,status:(await fetch(url,{cache:'no-store'})).status}))),retired.map(a=>a.url));
 for(const row of evidence.retiredRequests)assert.equal(row.status,404,'Retired ZIP must not be served');
 const cards=await page.locator('#asset-grid [data-card]').evaluateAll(cards=>cards.map(card=>({id:card.querySelector('[data-preview]')?.dataset.preview,zipSize:card.querySelector('.card-zip-size')?.textContent,links:[...card.querySelectorAll('.card-download')].map(a=>({url:a.href,kind:a.dataset.downloadKind}))})));
 assert.equal(cards.length,173);assert.equal(new Set(cards.map(c=>c.id)).size,173);
 for(const a of catalog){assert.deepEqual(cards.find(c=>c.id===a.id)?.links,[{url:primaryDownload(a).url,kind:primaryDownload(a).kind}],a.id);assert.equal(cards.find(c=>c.id===a.id)?.zipSize,`ZIP容量: ${formatBytes(primaryDownload(a).bytes)}`,a.id+' ZIP bytes');}
 for(const [type,count] of [['all',173],['model',137],['texture',36]])assert.equal(Number(await page.locator(`[data-type-filter="${type}"] small`).textContent()),count);
 // Fetch and parse every real generated detail page without repeatedly loading
 // 173 viewers. Existing test-browser.mjs retains the full viewer regression.
 for(const a of catalog){
  const actual=await page.evaluate(async id=>{
   const response=await fetch(`/meshcopia/assets/${id}/`);if(!response.ok)throw Error(`Detail ${id}: ${response.status}`);
   const doc=new DOMParser().parseFromString(await response.text(),'text/html');
   const urls=selector=>[...doc.querySelectorAll(selector)].map(a=>new URL(a.getAttribute('href'),location.href).href).sort();
   return {id,primary:[...doc.querySelectorAll('.download-primary')].map(a=>({url:new URL(a.getAttribute('href'),location.href).href,kind:a.dataset.downloadKind})),files:urls('.file-list a'),direct:urls('.direct-formats a.direct-download')};
  },a.id);
  const expected=expectedDetail(a);assert.deepEqual(actual.primary,[{url:expected.zip,kind:primaryDownload(a).kind}],a.id);
  assert.deepEqual(actual.files,expected.files,`${a.id}: original file links`);assert.deepEqual(actual.direct,expected.direct,`${a.id}: standalone original formats`);
  evidence.links.push({id:a.id,primary:actual.primary[0],originalFileLinks:actual.files.length,standaloneFormatLinks:actual.direct.length});
 }
 // Real GitHub Release requests are never mounted, fulfilled or mocked.
 for(const id of ['studio-chair','cedar-boards','commons-bar-labels']){
  const a=catalog.find(a=>a.id===id);assert.ok(a,id);await page.goto(`${SITE}assets/${id}/`,{waitUntil:'domcontentloaded'});
  const primary=page.locator('.download-primary');await expect(primary).toHaveAttribute('href',primaryDownload(a).url);
  const pending=page.waitForEvent('download',{timeout:90000});await primary.click();const download=await pending;
  assert.equal(await download.failure(),null);assert.equal(download.suggestedFilename(),new URL(primaryDownload(a).url).pathname.split('/').pop());
  const filename=`${out}/${download.suggestedFilename()}`;await download.saveAs(filename);
  evidence.individual.push({id,requestedUrl:primaryDownload(a).url,browserDownloadUrl:download.url(),file:filename,...await verifyBrowserZip(filename,[a],{individual:true})});
 }
 await linkContext.close();
 for(const mobile of [false,true]){
  const mode=mobile?'mobile':'desktop',ctx=await context({viewport:mobile?{width:390,height:844}:{width:1440,height:1050},isMobile:mobile,hasTouch:mobile}),page=await ctx.newPage();
  const pageErrors=[];page.on('pageerror',e=>pageErrors.push(e.message));let downloads=0;page.on('download',()=>downloads++);
  await catalogPage(page);const chair=page.locator('[data-asset-select="studio-chair"]'),texture=page.locator('[data-asset-select="sage-terrazzo"]'),counter=page.locator('#batch-download-bar button'),dialog=page.locator('#batch-selection-dialog');
  await expect(chair).toBeEnabled();await expect(texture).toBeEnabled();await chair.check();await texture.check();await expect(counter).toHaveText(/^2 件選択/);
  await page.locator('#asset-search').fill('studio chair');await expect(texture).toBeHidden();await expect(counter).toHaveText(/^2 件選択/);await counter.click();
  await expect(dialog.locator('li span')).toHaveText(selected.map(a=>a.title));
  await page.keyboard.press('Escape');await expect(dialog).toBeHidden();await expect(counter).toBeEnabled();await expect(counter).toBeFocused();
  await counter.click();await page.goBack();await expect(dialog).toBeHidden();await expect(counter).toBeEnabled();await expect(counter).toBeFocused();
  await counter.click();await dialog.locator('li button').first().click();await expect(dialog.locator('li span')).toHaveText([selected[1].title]);await expect(counter).toHaveText(/^1 件選択/);
  await dialog.getByRole('button',{name:'選択解除',exact:true}).click();await expect(dialog.locator('li')).toHaveCount(0);await expect(counter).toHaveText(/^0 件選択/);
  await dialog.getByRole('button',{name:'閉じる',exact:true}).click();await expect(counter).toBeEnabled();await expect(counter).toBeFocused();
  await page.locator('#asset-search').fill('');await chair.focus();await page.keyboard.press('Space');await expect(chair).toBeChecked();await texture.check();await counter.click();
  const prepare=dialog.getByRole('button',{name:'選択素材を1 ZIPにまとめる',exact:true}),save=dialog.getByRole('link',{name:'1 ZIPを保存',exact:true}),source=selected[0].downloads.delivery.files[0].fetch.url;
  // Only interrupted-flow requests are fault-injected. Successful source bytes,
  // notices, readiness, application code and archive responses remain real.
  let release,completed,calls=0;
  const held=new Promise(resolve=>release=resolve),finished=new Promise(resolve=>completed=resolve);
  const hold=async route=>{calls++;await held;await route.abort('aborted').catch(()=>{});completed();};
  await page.route(source,hold);
  try{
   await prepare.click();await expect.poll(()=>calls).toBe(1);await expect(prepare).toBeDisabled();await prepare.dispatchEvent('click');
   await dialog.getByRole('button',{name:'キャンセル',exact:true}).click();await expect(dialog.getByRole('status')).toContainText('キャンセルしました');
   assert.equal(calls,1);await expect(dialog.locator('li span')).toHaveText(selected.map(a=>a.title));await expect(save).toHaveCount(0);assert.equal(downloads,0);
  }finally{release();if(calls)await finished;await page.unroute(source,hold);}
  const fail=route=>route.abort('failed');await page.route(source,fail);
  await prepare.click();await expect(dialog.getByRole('status')).toContainText('失敗');await expect(save).toHaveCount(0);await expect(prepare).toBeEnabled();assert.equal(downloads,0);await page.unroute(source,fail);
  await prepare.click();await expect(save).toBeVisible({timeout:90000});await expect(dialog.locator('li span')).toHaveText(selected.map(a=>a.title));
  const pending=page.waitForEvent('download');await save.click();const download=await pending;assert.equal(download.suggestedFilename(),'meshcopia-selected-2.zip');assert.equal(await download.failure(),null);assert.equal(downloads,1);
  const filename=`${out}/bulk-${mode}.zip`;await download.saveAs(filename);
  evidence.bulk.push({mode,ids:selected.map(a=>a.id),file:filename,...await verifyBrowserZip(filename,selected),checks:['ready-without-injection','selected-count-list','filter-retains-selection','Escape-focus','Back-focus','remove','clear','keyboard-selection','cancel-retains-selection','one-inflight-job','network-error-no-save','retry','explicit-single-save']});
  // Regression for the reported tiny-model selection: actual shipped UI, no injection.
  await dialog.getByRole('button',{name:'選択解除',exact:true}).click();
  await dialog.getByRole('button',{name:'閉じる',exact:true}).click();await expect(counter).toBeEnabled();
  await page.locator('#asset-search').fill('');
  const small=['studio-chair','field-terminal'].map(id=>catalog.find(a=>a.id===id));
  await chair.check();await page.locator('[data-asset-select="field-terminal"]').check();
  const estimate=bundleSizeSummary(small).zipBytes;assert.ok(estimate>0);
  await expect(counter).toHaveText(`2 件選択 · ZIP 約 ${formatBytes(estimate)}`);
  await counter.click();await prepare.click();await expect(save).toBeVisible({timeout:90000});
  await expect(counter).toHaveText(`2 件選択 · ZIP ${formatBytes(estimate)}`);
  const smallPending=page.waitForEvent('download');await save.click();const smallDownload=await smallPending;
  assert.equal(await smallDownload.failure(),null);const smallFile=`${out}/small-${mode}.zip`;await smallDownload.saveAs(smallFile);
  const smallProof=await verifyBrowserZip(smallFile,small);assert.equal(smallProof.bytes,estimate);
  evidence.smallSizes.push({mode,estimate,display:await counter.textContent(),file:smallFile,...smallProof});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'Horizontal overflow');assert.deepEqual(pageErrors,[]);
  const screenshot=`${out}/${mode}.png`;await page.screenshot({path:screenshot});const bytes=await readFile(screenshot);evidence.screenshots.push({file:screenshot,bytes:bytes.length,sha256:sha256(bytes)});await ctx.close();
 }
 evidence.status='passed';await writeFile(`${out}/report.json`,JSON.stringify(evidence,null,2)+'\n');console.log('Full-P minimal downloads passed: 173 link inventories, 3 real Release downloads, desktop/mobile actual-ready bulk ZIPs.');
}catch(error){evidence.status='failed';evidence.error=error.stack;await writeFile(`${out}/failure.json`,JSON.stringify(evidence,null,2)+'\n');throw error;}
finally{await browser.close();}
