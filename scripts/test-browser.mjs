// Executed on the GitHub Actions runner, not the managed authoring environment.
import {chromium} from '@playwright/test';
import {createServer} from 'node:http';import {readFile,mkdir,stat} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
const root=path.resolve('dist');
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm','.glb':'model/gltf-binary','.zip':'application/zip'};
const server=createServer(async(req,res)=>{try{const u=new URL(req.url,'http://127.0.0.1');if(!u.pathname.startsWith('/meshcopia/')){res.writeHead(404).end();return}let file=path.resolve(root,decodeURIComponent(u.pathname.slice('/meshcopia/'.length)));if(!file.startsWith(root+path.sep)&&file!==root)throw Error('path');if((await stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(await readFile(file))}catch{res.writeHead(404).end('Not found')}});
await new Promise(resolve=>server.listen(4173,'127.0.0.1',resolve));await mkdir('test-results',{recursive:true});
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1440,height:1050},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
const home='http://127.0.0.1:4173/meshcopia/';
try{
 await page.goto(home);await page.waitForSelector('[data-card]');
 await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
 assert.equal(await page.locator('[data-card]:visible').count(),14);
 await page.screenshot({path:'test-results/desktop-catalog.png',fullPage:true});
 await page.locator('[data-type-filter="model"]').click();assert.equal(await page.locator('[data-card]:visible').count(),8);
 await page.locator('#asset-search').fill('chair GLB');assert.equal(await page.locator('[data-card]:visible').count(),1);
 await page.locator('#asset-search').fill('no-such-asset');assert.equal(await page.locator('[data-card]:visible').count(),0);assert.ok(await page.locator('#empty-state').isVisible());
 await page.locator('#clear-filters').click();assert.equal(await page.locator('[data-card]:visible').count(),14);
 await page.locator('[data-preview="studio-chair"]').click();await page.waitForSelector('#quick-dialog .model-viewer-3d[data-loaded="true"]',{timeout:30000});
 await page.locator('#quick-dialog [data-action="wire"]').click();assert.equal(await page.locator('#quick-dialog [data-action="wire"]').getAttribute('aria-pressed'),'true');await page.locator('#quick-close').click();
 await page.locator('[data-preview="atelier-lamp"]').click();await page.waitForSelector('#quick-dialog .model-viewer-3d[data-loaded="true"]');await page.locator('#quick-close').click();
 await page.goto(home+'assets/studio-chair/');await page.waitForSelector('.model-viewer-3d[data-loaded="true"]');
 for(const format of ['stl','obj','glb']){await page.locator(`[data-format="${format}"]`).click();await page.waitForFunction(type=>{const r=document.querySelector('.model-viewer-3d');return r.dataset.modelType===type&&r.dataset.loaded==='true'},format);}
 await page.locator('[data-action="spin"]').click();await page.locator('[data-action="spin"]').click();
 await page.locator('[data-setting="material"]').selectOption('clay');await page.locator('[data-setting="material"]').selectOption('original');await page.locator('[data-setting="lighting"]').selectOption('soft');
 await page.screenshot({path:'test-results/desktop-model.png',fullPage:true});
 const downloadPromise=page.waitForEvent('download');await page.locator('.download-primary').click();const download=await downloadPromise;const downloadPath=await download.path();assert.equal((await readFile(downloadPath)).readUInt32LE(0),0x04034b50);
 await page.locator('.credit-card [data-copy]').click();assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/CC BY 4.0/);
 await page.goto(home+'assets/cedar-boards/');await page.locator('[data-tiling="2"]').click();assert.equal(await page.locator('#texture-surface').evaluate(el=>el.style.backgroundSize),'50%');
 await page.locator('#texture-channel').selectOption({label:'Normal'});await page.locator('[data-tiling="sphere"]').click();await page.waitForSelector('#texture-sphere .model-viewer-3d[data-loaded="true"]',{timeout:30000});
 await page.screenshot({path:'test-results/desktop-texture.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.goto(home);await page.waitForFunction(()=>[...document.images].filter(i=>i.loading!=='lazy').every(i=>i.complete));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile horizontal overflow');
 await page.screenshot({path:'test-results/mobile-catalog.png',fullPage:true});
 await page.locator('[data-type-filter="texture"]').click();assert.equal(await page.locator('[data-card]:visible').count(),6);
 await page.locator('#language-toggle').click();assert.equal(await page.locator('html').getAttribute('lang'),'en');
 await page.goto(home+'assets/studio-chair/');await page.waitForSelector('.model-viewer-3d[data-loaded="true"]');
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'mobile detail horizontal overflow');
 await page.screenshot({path:'test-results/mobile-model.png',fullPage:true});
 assert.deepEqual(errors,[]);
 console.log('PASS: desktop/mobile catalog, search, filters, dialog reuse, GLB/STL/OBJ, viewer controls, ZIP, clipboard, texture tiling/PBR sphere and language.');
}catch(error){await page.screenshot({path:'test-results/failure.png',fullPage:true}).catch(()=>{});throw error}finally{await browser.close();server.close()}
