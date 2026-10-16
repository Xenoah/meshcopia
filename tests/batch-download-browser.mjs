// Integration fixture only: no mutation of the published site or catalog.
import {chromium,expect} from '@playwright/test';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
try{
 for(const mobile of [false,true]){
 const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1440,height:1000},isMobile:mobile,hasTouch:mobile,acceptDownloads:true});const page=await context.newPage();
 await page.goto('https://xenoah.github.io/meshcopia/',{waitUntil:'networkidle'});
 const core=await fs.readFile(new URL('../src/lib/batch-download.mjs',import.meta.url),'utf8'),ui=await fs.readFile(new URL('../src/lib/batch-download-ui.js',import.meta.url),'utf8'),sizes=await fs.readFile(new URL('../src/lib/file-size.mjs',import.meta.url),'utf8'),readiness=await fs.readFile(new URL('../src/lib/downloads.mjs',import.meta.url),'utf8'),css=await fs.readFile(new URL('../src/lib/batch-download.css',import.meta.url),'utf8');
 await page.evaluate(async ({core,ui,readiness,sizes,css})=>{
 const assets=JSON.parse(document.getElementById('catalog-data').textContent);
 for(const a of assets.filter(a=>['studio-chair','sage-terrazzo'].includes(a.id))){const text=`${a.titleEn}\nCreator: ${a.author}\nSource: ${a.pageUrl}\nCC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nCredit creator and source, indicate changes.\n`;const bytes=new TextEncoder().encode(text),hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');const sha256='1'.repeat(64);a.downloads.minimal={schemaVersion:1,id:a.id,assetVersion:a.version,packageVersion:'1.0.0',contentPolicy:'asset-files-required-dependencies-single-notice-v1',noticeFile:'LICENSE.txt',bytes:100,sha256,url:`https://github.com/Xenoah/meshcopia/releases/download/test-1.0.0/${a.id}-${a.version}-minimal-1.0.0.zip`,verification:{state:'published-verified',releaseTag:'test-1.0.0',archiveSha256:sha256},sourceFiles:a.files.map(({name,bytes,sha256})=>({name,bytes,sha256})),notice:{filename:'LICENSE.txt',text,bytes:bytes.length,sha256:hash}};}
 document.getElementById('catalog-data').textContent=JSON.stringify(assets);
 const url=s=>URL.createObjectURL(new Blob([s],{type:'text/javascript'}));const module=ui.replace("'./batch-download.mjs'",JSON.stringify(url(core))).replace("'./downloads.mjs'",JSON.stringify(url(readiness))).replace("'./file-size.mjs'",JSON.stringify(url(sizes.replace("'./batch-download.mjs'",JSON.stringify(url(core)))))).replace("import './batch-download.css';",'');const style=document.createElement('style');style.textContent=css;document.head.append(style);(await import(url(module))).initBatchDownload();
 },{core,ui,readiness,sizes,css});
 const chair=page.locator('[data-asset-select="studio-chair"]'),texture=page.locator('[data-asset-select="sage-terrazzo"]'),counter=page.locator('#batch-download-bar button');
 await chair.check();await texture.check();assert.match(await counter.textContent(),/2/);
 await page.locator('#asset-search').fill('studio chair');assert.equal(await texture.isVisible(),false);assert.match(await counter.textContent(),/2/);await counter.click();
 const dialog=page.locator('#batch-selection-dialog');assert.equal(await dialog.locator('li').count(),2);
 await page.keyboard.press('Escape');await expect(dialog).toBeHidden();await expect(counter).toBeEnabled();await expect(counter).toBeFocused();
 await counter.click();await page.goBack();await expect(dialog).toBeHidden();await expect(counter).toBeEnabled();await expect(counter).toBeFocused();assert.match(await counter.textContent(),/2/);await counter.click();await dialog.locator('li button').first().click();assert.equal(await dialog.locator('li').count(),1);
 await dialog.getByRole('button',{name:'選択解除',exact:true}).click();assert.equal(await dialog.locator('li').count(),0);await dialog.getByRole('button',{name:'閉じる',exact:true}).click();
 await page.locator('#asset-search').fill('');await chair.focus();await page.keyboard.press('Space');assert.equal(await chair.isChecked(),true);await texture.check();await counter.click();
 const prepare=dialog.getByRole('button',{name:'選択素材を1 ZIPにまとめる',exact:true});
 // Cancellation and repeated activation are bounded to a single in-flight job.
 let calls=0;await page.route('**/source/*.glb',async route=>{calls++;await new Promise(r=>setTimeout(r,1500));await route.abort().catch(()=>{});});
 await prepare.click();assert.equal(await prepare.isDisabled(),true);await prepare.dispatchEvent('click');
 await dialog.getByRole('button',{name:'キャンセル',exact:true}).click();await dialog.getByRole('status').filter({hasText:'キャンセルしました'}).waitFor();assert.ok(calls<=1);assert.equal(await dialog.locator('li').count(),2);await page.unroute('**/source/*.glb');
 // Failed response: no save link and retry retained.
 await page.route('**/source/*.glb',route=>route.abort());await prepare.click();await dialog.getByRole('status').filter({hasText:'失敗'}).waitFor();assert.equal(await dialog.getByRole('link',{name:'1 ZIPを保存'}).count(),0);await page.unroute('**/source/*.glb');
 await prepare.click();await dialog.getByRole('link',{name:'1 ZIPを保存',exact:true}).waitFor();
 const pending=page.waitForEvent('download');await dialog.getByRole('link',{name:'1 ZIPを保存',exact:true}).click();const downloaded=await pending;assert.equal(downloaded.suggestedFilename(),'meshcopia-selected-2.zip');await downloaded.saveAs(new URL(`../batch-${mobile?'mobile':'desktop'}.zip`,import.meta.url).pathname);
 await page.screenshot({path:new URL(`../batch-${mobile?'mobile':'desktop'}.png`,import.meta.url).pathname});await context.close();console.log(mobile?'mobile passed':'desktop passed');
 }
}finally{await browser.close();}
