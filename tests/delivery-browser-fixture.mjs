// Synthetic local fixture: exercises the shipped UI/transport, not publication.
import {chromium,expect} from '@playwright/test';
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {model,transport,hash} from './delivery-fixtures.mjs';
import {bundleSizeSummary} from '../src/lib/file-size.mjs';
import assert from 'node:assert/strict';
const assets=[model('chair'),model('table'),model('missing')];delete assets[2].downloads.delivery;
const data=transport('model');let mode='ok';
const server=createServer(async(req,res)=>{
 const pathname=new URL(req.url,'http://localhost').pathname;
 try {
  if(pathname==='/meshcopia/'){
   res.setHeader('Content-Type','text/html');res.end(`<html lang="ja"><body><div id="asset-grid">${assets.map(a=>`<article data-card><button data-preview="${a.id}">${a.id}</button></article>`).join('')}</div><script id="catalog-data" type="application/json">${JSON.stringify(assets)}</script><script type="module">import {initBatchDownload} from './modules/batch-download-ui.js';initBatchDownload();</script></body></html>`);
  }else if(pathname.startsWith('/meshcopia/modules/')){
   const name=pathname.split('/').pop();assert.ok(/^[a-z-]+\.(js|mjs)$/.test(name));let text=await readFile(new URL('../src/lib/'+name,import.meta.url),'utf8');
   text=text.replace("import './batch-download.css';",'');res.setHeader('Content-Type','text/javascript');res.end(text);
  }else if(pathname.startsWith('/meshcopia/download-data/')){
   if(mode==='fail')return res.writeHead(404).end();
   if(mode==='delay'){setTimeout(()=>{if(!res.destroyed)res.writeHead(503).end();},500);return;}
   res.end(pathname.endsWith('.json')?data.manifest:data.packed);
  }else res.writeHead(404).end();
 }catch{res.writeHead(500).end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
try{
 for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:844},acceptDownloads:true});
  await page.goto(`http://127.0.0.1:${server.address().port}/meshcopia/`);
  const counter=page.locator('#batch-download-bar button'),dialog=page.locator('#batch-selection-dialog'),prepare=dialog.getByRole('button',{name:'選択素材を1 ZIPにまとめる',exact:true});
  await expect(page.locator('[data-asset-select="missing"]')).toBeDisabled();
  await page.locator('[data-asset-select="chair"]').check();await page.locator('[data-asset-select="table"]').check();
  const bytes=bundleSizeSummary(assets.slice(0,2)).zipBytes;
  await expect(counter).toHaveText(`2 件選択 · ZIP 約 ${bytes} B`);await counter.click();
  mode='delay';await prepare.click();await dialog.getByRole('button',{name:'キャンセル',exact:true}).click();await expect(dialog.getByRole('status')).toContainText('キャンセルしました');
  mode='fail';await prepare.click();await expect(dialog.getByRole('status')).toContainText('失敗');await expect(dialog.getByRole('link')).toHaveCount(0);
  mode='delay';await prepare.click();await page.goBack();await expect(dialog).toBeHidden();await expect(counter).toBeFocused();await counter.click();await expect(dialog.getByRole('status')).toContainText('キャンセルしました');
  mode='ok';await prepare.click();const save=dialog.getByRole('link',{name:'1 ZIPを保存',exact:true});await expect(save).toBeVisible();
  const pending=page.waitForEvent('download');await save.click();const result=await pending;const zip=await readFile(await result.path());assert.equal(zip.length,bytes);
  await dialog.locator('li button').first().click();await expect(save).toBeHidden();await expect(dialog.locator('li')).toHaveCount(1);
  await dialog.getByRole('button',{name:'選択解除',exact:true}).click();await expect(counter).toHaveText('0 件選択');
  await page.close();
 }
 await mkdir('test-results',{recursive:true});await writeFile('test-results/delivery-browser-fixture.json',JSON.stringify({fixture:true,publication:false,checks:['missing-FBX-disabled','exact-ZIP-size','cancel','failure-no-save','retry','Back-cancels','remove-invalidates-save','clear','desktop','mobile']}));
 console.log('Passed synthetic local delivery browser fixture (desktop/mobile).');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
