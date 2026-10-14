// Executed on the GitHub Actions runner, not the managed authoring environment.
import {chromium} from '@playwright/test';
import {createServer} from 'node:http';import {readFile,mkdir,stat} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
const root=path.resolve('dist');
const catalog=JSON.parse(await readFile(path.join(root,'api/catalog.json'),'utf8')).assets;
const countType=type=>catalog.filter(a=>a.type===type).length;
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm','.glb':'model/gltf-binary','.zip':'application/zip'};
const server=createServer(async(req,res)=>{try{const u=new URL(req.url,'http://127.0.0.1');if(!u.pathname.startsWith('/meshcopia/')){res.writeHead(404).end();return}let file=path.resolve(root,decodeURIComponent(u.pathname.slice('/meshcopia/'.length)));if(!file.startsWith(root+path.sep)&&file!==root)throw Error('path');if((await stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(await readFile(file))}catch{res.writeHead(404).end('Not found')}});
await new Promise(resolve=>server.listen(4173,'127.0.0.1',resolve));await mkdir('test-results',{recursive:true});
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1440,height:1050},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
const home='http://127.0.0.1:4173/meshcopia/';
async function loadImages(){
 for(const img of await page.locator('img:visible').all()) await img.scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>[...document.images].filter(i=>i.getClientRects().length).every(i=>i.complete&&i.naturalWidth>0));
 await page.evaluate(async()=>{await Promise.all([...document.images].filter(i=>i.getClientRects().length).map(i=>i.decode()));document.activeElement?.blur();window.scrollTo({top:0,behavior:'instant'});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))});
}
try{
 await page.goto(home);await page.waitForSelector('[data-card]');
 await loadImages();
 assert.equal(await page.locator('[data-card]:visible').count(),catalog.length);
 for(const a of catalog.filter(a=>a.id.startsWith('commons-'))){const card=page.locator('[data-card]').filter({has:page.locator(`[data-preview="${a.id}"]`)});assert.equal(await card.locator('.card-info p').textContent(),`${a.triangles.toLocaleString()} tris · GLB / STL`);}
 await page.screenshot({path:'test-results/desktop-catalog.png',fullPage:false});
 await page.screenshot({path:'test-results/desktop-catalog-full.png',fullPage:true});
 await page.locator('[data-type-filter="model"]').click();assert.equal(await page.locator('[data-card]:visible').count(),countType('model'));
 await page.locator('#asset-search').fill('chair GLB');assert.ok(await page.locator('[data-preview="studio-chair"]').isVisible());assert.equal(await page.locator('[data-preview="atelier-lamp"]').isVisible(),false);
 await page.locator('#asset-search').fill('no-such-asset');assert.equal(await page.locator('[data-card]:visible').count(),0);assert.ok(await page.locator('#empty-state').isVisible());
 await page.locator('#clear-filters').click();assert.equal(await page.locator('[data-card]:visible').count(),catalog.length);
 await page.locator('[data-preview="studio-chair"]').click();await page.waitForSelector('#quick-dialog .model-viewer-3d[data-loaded="true"]',{timeout:30000});
 await page.locator('#quick-dialog [data-action="wire"]').click();assert.equal(await page.locator('#quick-dialog [data-action="wire"]').getAttribute('aria-pressed'),'true');await page.locator('#quick-close').click();
 await page.locator('[data-preview="atelier-lamp"]').click();await page.waitForSelector('#quick-dialog .model-viewer-3d[data-loaded="true"]');assert.equal(await page.locator('#quick-dialog [data-action="wire"]').getAttribute('aria-pressed'),'false');await page.locator('#quick-close').click();
 await page.goto(home+'assets/studio-chair/');await page.waitForSelector('.model-viewer-3d[data-loaded="true"]');
 for(const format of ['stl','obj','glb']){await page.locator(`[data-format="${format}"]`).click();await page.waitForFunction(type=>{const r=document.querySelector('.model-viewer-3d');return r.dataset.modelType===type&&r.dataset.loaded==='true'},format);}
 await page.locator('[data-action="spin"]').click();await page.locator('[data-action="spin"]').click();
 await page.locator('[data-setting="material"]').selectOption('clay');await page.locator('[data-setting="material"]').selectOption('original');await page.locator('[data-setting="lighting"]').selectOption('soft');
 await loadImages();await page.screenshot({path:'test-results/desktop-model.png',fullPage:true});
 const downloadPromise=page.waitForEvent('download');await page.locator('.download-primary').click();const download=await downloadPromise;const downloadPath=await download.path();assert.equal((await readFile(downloadPath)).readUInt32LE(0),0x04034b50);
 await page.locator('.credit-card [data-copy]').click();assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/CC BY 4.0/);
 for(const asset of catalog.filter(a=>a.id.startsWith('commons-'))){
  await page.goto(home+`assets/${asset.id}/`);
  await page.waitForSelector('.model-viewer-3d[data-loaded="true"]',{timeout:45000});
  assert.equal(await page.locator('[data-format="glb"]').getAttribute('aria-pressed'),'true');
  await page.locator('.provenance summary').click();
  assert.equal(await page.locator('.provenance a').first().getAttribute('href'),asset.provenance.sourceUrl);
  await page.locator('.provenance summary').click();
  await loadImages();await page.screenshot({path:`test-results/${asset.id}.png`,fullPage:false});
 }
 await page.goto(home+'assets/cedar-boards/');await page.locator('[data-tiling="2"]').click();assert.equal(await page.locator('#texture-surface').evaluate(el=>el.style.backgroundSize),'50%');
 await page.locator('#texture-channel').selectOption({label:'Normal'});await page.locator('[data-tiling="sphere"]').click();await page.waitForSelector('#texture-sphere .model-viewer-3d[data-loaded="true"]',{timeout:30000});
 await loadImages();await page.screenshot({path:'test-results/desktop-texture.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.goto(home);await page.waitForFunction(()=>[...document.images].filter(i=>i.loading!=='lazy').every(i=>i.complete));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile horizontal overflow');
 await loadImages();await page.screenshot({path:'test-results/mobile-catalog.png',fullPage:true});
 await page.locator('[data-type-filter="texture"]').click();assert.equal(await page.locator('[data-card]:visible').count(),countType('texture'));
 await page.locator('#language-toggle').click();assert.equal(await page.locator('html').getAttribute('lang'),'en');
 await page.goto(home+'assets/studio-chair/');await page.waitForSelector('.model-viewer-3d[data-loaded="true"]');
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile detail horizontal overflow');
 await loadImages();await page.screenshot({path:'test-results/mobile-model.png',fullPage:true});
 assert.deepEqual(errors,[]);
 console.log('PASS: desktop/mobile catalog, search, filters, dialog reuse, GLB/STL/OBJ, viewer controls, ZIP, clipboard, texture tiling/PBR sphere and language.');
}catch(error){await page.screenshot({path:'test-results/failure.png',fullPage:true}).catch(()=>{});throw error}finally{await browser.close();server.close()}
