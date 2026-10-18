// Executed on the GitHub Actions runner, not the managed authoring environment.
import {inspectImageDecode} from './lib/browser-image-check.mjs';
import {testUsagesBrowser} from './test-usages-browser.mjs';
import {chromium} from '@playwright/test';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
const live=process.argv.includes('--live'),root=path.resolve('dist');
const catalog=JSON.parse(await readFile(path.join(root,'api/catalog.json'),'utf8')).assets;
const countType=type=>catalog.filter(a=>a.type===type).length;
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm','.glb':'model/gltf-binary','.zip':'application/zip'};
const server=createServer(async(req,res)=>{try{const u=new URL(req.url,'http://127.0.0.1');if(!u.pathname.startsWith('/meshcopia/')){res.writeHead(404).end();return}let file=path.resolve(root,decodeURIComponent(u.pathname.slice('/meshcopia/'.length)));if(!file.startsWith(root+path.sep)&&file!==root)throw Error('path');if((await stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(await readFile(file))}catch{res.writeHead(404).end('Not found')}});
if(!live)await new Promise(resolve=>server.listen(4173,'127.0.0.1',resolve));await mkdir('test-results',{recursive:true});
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1440,height:1050},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage();const errors=[];const imageResponses=new Map();const imageDecodeChecks=[];
page.on('response',r=>{if(r.request().resourceType()==='image')imageResponses.set(r.url(),{status:r.status(),contentType:r.headers()['content-type']??null,contentLength:r.headers()['content-length']??null});});
page.on('requestfailed',r=>{if(r.resourceType()==='image')imageResponses.set(r.url(),{requestFailure:r.failure()?.errorText??'unknown'});});
page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
const home=live?'https://xenoah.github.io/meshcopia/':'http://127.0.0.1:4173/meshcopia/';
async function loadImages(){
 const images=await page.locator('img:visible').all();
 const batch={page:page.url(),expectedImages:images.length,images:[]};
 imageDecodeChecks.push(batch);
 await page.evaluate(()=>{
  window.__imageCheckTransitions=[];
  window.__imageCheckObserver?.disconnect();
  window.__imageCheckObserver=new MutationObserver(records=>{
   for(const r of records){if(r.target instanceof HTMLImageElement&&window.__imageCheckTransitions.length<1000)window.__imageCheckTransitions.push({attribute:r.attributeName,oldValue:r.oldValue,newValue:r.target.getAttribute(r.attributeName),currentSrc:r.target.currentSrc,complete:r.target.complete,naturalWidth:r.target.naturalWidth,naturalHeight:r.target.naturalHeight});}
  });
  window.__imageCheckObserver.observe(document,{subtree:true,attributes:true,attributeOldValue:true,attributeFilter:['src','srcset','sizes','loading']});
 });
 let current={};
 try{
  // Bound decoded-image pressure without skipping any image or accepting a failed decode.
  for(let index=0;index<images.length;index++){
   const img=images[index];current={index};
   current.beforeWait=(await img.evaluate(inspectImageDecode,{decode:false})).before;
   await img.scrollIntoViewIfNeeded();
   const handle=await img.elementHandle();
   assert.ok(handle,'image disappeared before load wait');
   try{await page.waitForFunction(el=>el.isConnected&&el.complete&&el.naturalWidth>0&&el.naturalHeight>0,handle,{timeout:30000});}finally{await handle.dispose();}
   current.decode=await img.evaluate(inspectImageDecode);
   const url=current.decode.after?.currentSrc||current.decode.before.currentSrc;
   current.http=imageResponses.get(url)??null;
   batch.images.push(current);
   assert.equal(current.decode.ok,true,`Image decode failed: ${JSON.stringify(current)}`);
  }
  batch.finalImages=await page.locator('img:visible').count();
  assert.equal(batch.finalImages,images.length,'Visible image DOM changed while verifying images');
  batch.domTransitions=await page.evaluate(()=>window.__imageCheckTransitions);
  await writeFile('test-results/image-decode-checks.json',JSON.stringify(imageDecodeChecks,null,2));
  await page.evaluate(async()=>{document.activeElement?.blur();window.scrollTo({top:0,behavior:'instant'});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))});
 }catch(error){
  current.afterFailure=images[current.index]?await images[current.index].evaluate(inspectImageDecode,{decode:false}).catch(e=>({inspectionError:e.message})):null;
  const url=current.afterFailure?.before?.currentSrc||current.beforeWait?.currentSrc;
  current.http=imageResponses.get(url)??current.http??null;
  batch.failure={message:error.message,current};
  batch.domTransitions=await page.evaluate(()=>window.__imageCheckTransitions).catch(()=>[]);
  await writeFile('test-results/image-decode-failure.json',JSON.stringify(batch,null,2));
  await writeFile('test-results/image-decode-checks.json',JSON.stringify(imageDecodeChecks,null,2));
  throw error;
 }finally{await page.evaluate(()=>window.__imageCheckObserver?.disconnect()).catch(()=>{});}
}
try{
 await testUsagesBrowser(page,home);
 await page.goto(home);await page.waitForSelector('[data-card]');
 await loadImages();
 assert.equal(await page.locator('[data-card]:visible').count(),catalog.length);
 for(const a of catalog.filter(a=>a.type==='model'&&a.id.startsWith('commons-'))){const card=page.locator('[data-card]').filter({has:page.locator(`[data-preview="${a.id}"]`)});assert.equal(await card.locator('.card-info p').textContent(),`${a.triangles.toLocaleString()} tris · FBX`);}
 for(const a of catalog.filter(a=>a.type==='texture')){
  const card=page.locator('[data-card]').filter({has:page.locator(`[data-preview="${a.id}"]`)});
  assert.equal((await card.locator('.format-badge').textContent()).trim(),{repeat:'SEAMLESS',mirror:'MIRROR',clamp:'ATLAS'}[a.wrapMode]);
  assert.ok((await card.locator('.card-info p').textContent()).includes(`${a.width} × ${a.height}`));
 }
 await page.screenshot({path:'test-results/desktop-catalog.png',fullPage:false});
 await page.screenshot({path:'test-results/desktop-catalog-full.png',fullPage:true});
 await page.locator('[data-type-filter="model"]').click();assert.equal(await page.locator('[data-card]:visible').count(),countType('model'));
 await page.locator('#asset-search').fill('chair FBX');assert.ok(await page.locator('[data-preview="studio-chair"]').isVisible());
 await page.locator('#asset-search').fill('chair GLB');assert.ok(await page.locator('[data-preview="studio-chair"]').isVisible());assert.equal(await page.locator('[data-preview="atelier-lamp"]').isVisible(),false);
 await page.locator('#asset-search').fill('no-such-asset');assert.equal(await page.locator('[data-card]:visible').count(),0);assert.ok(await page.locator('#empty-state').isVisible());
 await page.locator('#clear-filters').click();assert.equal(await page.locator('[data-card]:visible').count(),catalog.length);
 await page.locator('[data-preview="studio-chair"]').click();await page.waitForSelector('#quick-dialog .model-viewer-3d[data-loaded="true"]',{timeout:30000});
 await page.locator('#quick-dialog [data-action="wire"]').click();assert.equal(await page.locator('#quick-dialog [data-action="wire"]').getAttribute('aria-pressed'),'true');await page.locator('#quick-close').click();
 await page.locator('[data-preview="atelier-lamp"]').click();await page.waitForSelector('#quick-dialog .model-viewer-3d[data-loaded="true"]');assert.equal(await page.locator('#quick-dialog [data-action="wire"]').getAttribute('aria-pressed'),'false');await page.locator('#quick-close').click();
 for(const [id,count] of [['commons-warm-oak',4],['commons-bar-labels',1]]){
  await page.locator(`[data-preview="${id}"]`).click();
  await page.waitForSelector('#quick-texture img');assert.equal(await page.locator('#quick-texture img').count(),count);
  if(count===4)assert.equal(await page.locator('#quick-texture img').nth(1).evaluate(el=>el.style.transform),'scale(-1, 1)');
  else assert.equal(await page.locator('#quick-texture').evaluate(el=>el.style.aspectRatio),'1536 / 1024');
  await page.locator('#quick-close').click();
 }
 await page.goto(home+'assets/studio-chair/');await page.waitForSelector('.model-viewer-3d[data-loaded="true"]');
 for(const format of ['stl','obj','glb']){await page.locator(`[data-format="${format}"]`).click();await page.waitForFunction(type=>{const r=document.querySelector('.model-viewer-3d');return r.dataset.modelType===type&&r.dataset.loaded==='true'},format);}
 await page.locator('[data-action="spin"]').click();await page.locator('[data-action="spin"]').click();
 await page.locator('[data-setting="material"]').selectOption('clay');await page.locator('[data-setting="material"]').selectOption('original');await page.locator('[data-setting="lighting"]').selectOption('soft');
 await loadImages();await page.screenshot({path:'test-results/desktop-model.png',fullPage:true});
 const downloadPromise=page.waitForEvent('download');await page.locator('.download-primary').click();const download=await downloadPromise;const downloadPath=await download.path();assert.equal((await readFile(downloadPath)).readUInt32LE(0),0x04034b50);
 await page.locator('.credit-card [data-copy]').click();assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/CC BY 4.0/);
 for(const asset of catalog.filter(a=>a.type==='model'&&a.id.startsWith('commons-'))){
  await page.goto(home+`assets/${asset.id}/`);
  await page.waitForSelector('.model-viewer-3d[data-loaded="true"]',{timeout:45000});
  assert.equal(await page.locator('[data-format="glb"]').getAttribute('aria-pressed'),'true');
  await page.locator('.provenance summary').click();
  assert.equal(await page.locator('.provenance a').first().getAttribute('href'),asset.provenance.sourceUrl);
  await page.locator('.provenance summary').click();
  await loadImages();await page.screenshot({path:`test-results/${asset.id}.png`,fullPage:false});
 }
 await page.goto(home+'assets/cedar-boards/');await page.locator('[data-tiling="2"]').click();assert.equal(await page.locator('#texture-surface img').count(),4);
 await page.locator('#texture-channel').selectOption({label:'Normal'});await page.locator('[data-tiling="sphere"]').click();await page.waitForSelector('#texture-sphere .model-viewer-3d[data-loaded="true"]',{timeout:30000});
 await loadImages();await page.screenshot({path:'test-results/desktop-texture.png',fullPage:true});
 for(const asset of catalog.filter(a=>a.type==='texture'&&a.id.startsWith('commons-'))){
  await page.goto(home+`assets/${asset.id}/`);await page.waitForSelector('#texture-surface img');
  if(asset.wrapMode==='mirror'){
   await page.locator('[data-tiling="4"]').click();assert.equal(await page.locator('#texture-surface img').count(),16);
   assert.equal(await page.locator('#texture-surface img').nth(5).evaluate(el=>el.style.transform),'scale(-1, -1)');
   await page.locator('[data-tiling="2"]').click();assert.equal(await page.locator('#texture-surface img').count(),4);
  }else{
   assert.equal(await page.locator('[data-tiling="2"],[data-tiling="sphere"]').count(),0);
   assert.equal(await page.locator('#texture-surface img').count(),1);
   const ratio=await page.locator('#texture-surface').evaluate(el=>el.clientWidth/el.clientHeight);
   assert.ok(Math.abs(ratio-asset.width/asset.height)<.02,'atlas aspect ratio must be preserved');
  }
  assert.equal(await page.locator('#texture-channel option').count(),1,'base-color only');
  await loadImages();await page.screenshot({path:`test-results/${asset.id}.png`,fullPage:false});
  if(asset.wrapMode==='mirror'){
   await page.locator('[data-tiling="sphere"]').click();await page.waitForSelector('#texture-sphere .model-viewer-3d[data-loaded="true"]',{timeout:30000});
   if(asset.id==='commons-warm-oak')await page.screenshot({path:'test-results/commons-mirror-sphere.png',fullPage:false});
  }
 }
 // Exercise every imported Yokocho GLB and unchanged texture, not just the starter fixtures.
 for(const asset of catalog.filter(a=>a.id.startsWith('yokocho-'))){
  await page.goto(home+`assets/${asset.id}/`);
  if(asset.type==='model'){
   await page.waitForSelector('.model-viewer-3d[data-loaded="true"]',{timeout:45000});
   assert.equal(await page.locator('[data-format="glb"]').getAttribute('aria-pressed'),'true');
  }else{
   await page.waitForSelector('#texture-surface img');
   assert.equal(await page.locator('#texture-channel option').count(),1);
   if(asset.wrapMode==='mirror'){
    await page.locator('[data-tiling="2"]').click();
    assert.equal(await page.locator('#texture-surface img').count(),4);
    assert.equal(await page.locator('#texture-surface img').nth(3).evaluate(el=>el.style.transform),'scale(-1, -1)');
   }else{
    assert.equal(await page.locator('[data-tiling="2"],[data-tiling="sphere"]').count(),0);
    const ratio=await page.locator('#texture-surface').evaluate(el=>el.clientWidth/el.clientHeight);
    assert.ok(Math.abs(ratio-asset.width/asset.height)<.02);
   }
  }
  await loadImages();
  await page.screenshot({path:`test-results/${asset.id}.png`,fullPage:false});
 }
 // Exercise every published original city model in both distributed formats.
 for(const asset of catalog.filter(a=>a.type==='model'&&a.id.startsWith('city-'))){
  await page.goto(home+`assets/${asset.id}/`);
  await page.waitForSelector('.model-viewer-3d[data-loaded="true"]',{timeout:45000});
  assert.equal(await page.locator('[data-format="glb"]').getAttribute('aria-pressed'),'true');
  for(const format of ['stl','glb']){
   await page.locator(`[data-format="${format}"]`).click();
   await page.waitForFunction(type=>{const r=document.querySelector('.model-viewer-3d');return r.dataset.modelType===type&&r.dataset.loaded==='true'},format);
  }
  await page.locator('[data-action="wire"]').click();
  assert.equal(await page.locator('[data-action="wire"]').getAttribute('aria-pressed'),'true');
  await page.locator('[data-action="wire"]').click();
  await loadImages();await page.screenshot({path:`test-results/${asset.id}.png`,fullPage:false});
 }
 await page.goto(home+'assets/commons-bar-labels/');await page.locator('.file-list summary').click();
 const pngEvent=page.waitForEvent('download');await page.locator('.file-list a').click();const pngDownload=await pngEvent;
 const png=await readFile(await pngDownload.path());assert.equal(createHash('sha256').update(png).digest('hex'),catalog.find(a=>a.id==='commons-bar-labels').files[0].sha256);
 await page.setViewportSize({width:390,height:844});await page.goto(home);await page.waitForFunction(()=>[...document.images].filter(i=>i.loading!=='lazy').every(i=>i.complete));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile horizontal overflow');
 await loadImages();await page.screenshot({path:'test-results/mobile-catalog.png',fullPage:true});
 await page.locator('[data-type-filter="texture"]').click();assert.equal(await page.locator('[data-card]:visible').count(),countType('texture'));
 await page.locator('#language-toggle').click();assert.equal(await page.locator('html').getAttribute('lang'),'en');
 await page.goto(home+'assets/studio-chair/');await page.waitForSelector('.model-viewer-3d[data-loaded="true"]');
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile detail horizontal overflow');
 await loadImages();await page.screenshot({path:'test-results/mobile-model.png',fullPage:true});
 for(const id of ['commons-warm-oak','commons-bar-labels']){
  await page.goto(home+`assets/${id}/`);await loadImages();
  if(id==='commons-warm-oak')await page.locator('[data-tiling="2"]').click();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile texture overflow');
  await page.screenshot({path:`test-results/mobile-${id}.png`,fullPage:true});
 }
 assert.deepEqual(errors,[]);
 console.log('PASS: desktop/mobile catalog, search, filters, dialog reuse, GLB/STL/OBJ, viewer controls, ZIP, clipboard, repeat/mirror/clamp textures, original PNG download, material sphere and language.');
}catch(error){await page.screenshot({path:'test-results/failure.png',fullPage:true}).catch(()=>{});throw error}finally{await browser.close();if(!live)server.close()}
