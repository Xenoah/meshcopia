// Read the real published Pages site. No routes, injected catalog or local mount.
import {chromium,expect} from '@playwright/test';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const id='city-front-loading-washing-machine',site='https://xenoah.github.io/meshcopia/';
const meta=JSON.parse(await readFile(`content/assets/${id}/asset.json`));
const expected=JSON.parse(await readFile('docs/cohorts/new251/expected.json')).models.find(a=>a.id===id);
const out='test-results/asset-revisions/live-washer';await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1440,height:1050},serviceWorkers:'block'}),page=await context.newPage();
const proof={state:'running',id,site,livePublicSite:true,requestInterception:false,query:'洗濯機'};
try{
 const response=await page.goto(site,{waitUntil:'domcontentloaded'});assert.equal(response.status(),200);
 await expect(page.locator('#batch-download-bar')).toBeVisible();
 const assets=JSON.parse(await page.locator('#catalog-data').textContent()),asset=assets.find(a=>a.id===id);assert.ok(asset);
 assert.equal(asset.title,meta.title);assert.equal(asset.version,meta.version);assert.equal(asset.status,'public');
 proof.publicCount=assets.length;proof.title=asset.title;proof.category=asset.category;
 const card=page.locator(`[data-card]:has([data-preview="${id}"])`);
 await card.scrollIntoViewIfNeeded();await expect(card).toBeVisible();
 await page.locator('#asset-search').fill('洗濯機');await expect(card).toBeVisible();
 proof.searchUrl=page.url();proof.visibleIds=await page.locator('[data-card]:visible [data-preview]').evaluateAll(nodes=>nodes.map(n=>n.dataset.preview));assert.ok(proof.visibleIds.includes(id));
 assert.ok(await card.locator('img').evaluate(async im=>{await im.decode();return im.naturalWidth>0}));
 await page.locator('#catalog').screenshot({path:`${out}/search-washing-machine.png`});
 const glbResponse=page.waitForResponse(r=>r.url()===asset.previewUrl&&r.status()===200);
 await card.locator('.card-title').click();await page.waitForURL(site+`assets/${id}/`);await expect(page.locator('.model-viewer-status')).toHaveText('GLB preview',{timeout:60000});
 const glb=await (await glbResponse).body();assert.equal(createHash('sha256').update(glb).digest('hex'),expected.sourceGlbSha256);
 proof.pageUrl=page.url();proof.previewGlb={bytes:glb.length,sha256:expected.sourceGlbSha256};
 const archive=asset.downloads.delivery.archive;assert.equal(archive.url,`https://github.com/Xenoah/meshcopia/releases/download/cohort-new251-v1.0.0/${expected.fbxArchive.filename}`);assert.equal(archive.bytes,expected.fbxArchive.bytes);assert.equal(archive.sha256,expected.fbxArchive.sha256);
 await expect(page.locator('.download-primary')).toHaveAttribute('href',archive.url);proof.download=archive;
 const manifest=await page.evaluate(async id=>{const response=await fetch(`/meshcopia/api/assets/${id}.json`,{cache:'no-store'});if(!response.ok)throw Error('Public manifest unavailable');return response.json()},id);assert.deepEqual(manifest,asset);
 await page.screenshot({path:`${out}/public-washing-machine.png`});
 proof.state='passed';await writeFile(`${out}/report.json`,JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
}catch(error){proof.state='failed';proof.error=error.stack;await writeFile(`${out}/failure.json`,JSON.stringify(proof,null,2)+'\n');throw error}finally{await context.close();await browser.close()}
