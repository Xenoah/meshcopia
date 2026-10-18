import {readFile,stat} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {filesIn,sha256,readCatalog} from './lib/catalog.mjs';
import {prepareMinimalDownloads,minimalIdentity} from './lib/minimal-downloads.mjs';
import {verifySiteMigration} from './lib/site-migration.mjs';
import {loadCohortPolicy,assertPublicationScope,originalSourceUrl,originalThumbnailUrl} from './lib/cohort-policy.mjs';
const policy=await loadCohortPolicy();
const base=process.env.PUBLIC_BASE_PATH??'/meshcopia';
const verifiedMinimal=await prepareMinimalDownloads(await readCatalog());
const catalog=JSON.parse(await readFile('dist/api/catalog.json','utf8'));
const ndjson=(await readFile('dist/api/catalog.ndjson','utf8')).trim().split('\n').map(line=>JSON.parse(line));
assert.deepEqual(ndjson,catalog.assets);
assert.equal(catalog.schemaVersion,'3.0.0');assertPublicationScope(catalog.assets,policy);
let count=0;
async function resolveFile(url){const u=new URL(url,'https://xenoah.github.io'+base+'/');assert.ok(u.pathname.startsWith(base+'/'),`Wrong base path: ${url}`);let file='dist/'+decodeURIComponent(u.pathname.slice(base.length+1));if(u.pathname.endsWith('/'))file+='index.html';await stat(file);return file;}
for(const a of catalog.assets){
 assert.ok(Array.isArray(a.usages));
 const original=JSON.parse(await readFile(`content/assets/${a.id}/asset.json`,'utf8'));
 assert.deepEqual(a.usages,original.usages??[]);
 const manifest=JSON.parse(await readFile(await resolveFile(a.manifestUrl),'utf8'));assert.deepEqual(manifest.usages,a.usages);
 const html=await readFile(await resolveFile(a.pageUrl),'utf8');assert.ok(html.includes('id="usage-heading"'));
 if(a.type==='texture'){
  assert.deepEqual(a.downloads.minimal,verifiedMinimal.get(minimalIdentity(a)),'Minimal binding differs from current verified public Release');
  assert.deepEqual(manifest.downloads.minimal,a.downloads.minimal,'Per-asset minimal binding mismatch');
 }
 assert.equal(a.status,'public');await resolveFile(a.pageUrl);assert.equal(a.thumbnail,originalThumbnailUrl(original,policy));if(!a.thumbnail.startsWith('https://raw.githubusercontent.com/'))await resolveFile(a.thumbnail);await resolveFile(a.manifestUrl);
 for(const f of a.files){assert.equal(f.url,originalSourceUrl(original,f,policy));const data=await readFile(f.url.startsWith('https://raw.githubusercontent.com/')?`content/assets/${a.id}/source/${f.name}`:await resolveFile(f.url));assert.equal(data.length,f.bytes);assert.equal(sha256(data),f.sha256);count++;}
}
assert.equal(catalog.assets.filter(a=>a.downloads.minimal).length,catalog.assets.filter(a=>a.type==='texture').length,'Verified texture cohort omitted from public catalog');
let links=0;
for(const file of (await filesIn('dist')).filter(f=>f.endsWith('.html'))){const html=await readFile(path.join('dist',file),'utf8');for(const match of html.matchAll(/(?:href|src)="([^"]+)"/g)){const value=match[1].replace(/&amp;/g,'&');if(value.startsWith(base+'/')){await resolveFile(value);links++;}}}
assert.ok((await readFile('dist/sitemap.xml','utf8')).includes(base+'/assets/studio-chair/'));
await verifySiteMigration();
console.log(`Verified ${catalog.assets.length} public assets, ${count} original file hashes, ${verifiedMinimal.size} verified Release minimal ZIPs and ${links} current internal links; retired ZIPs absent.`);

// Current delivery binds exact FBX bytes; production originals stay separate.
const {bindDelivery}=await import('./lib/delivery.mjs');
const {buildBundle,planBundle}=await import('../src/lib/batch-download.mjs');
const {webcrypto}=await import('node:crypto');
const fbxProjection=JSON.parse(await readFile('dist/api/fbx-minimal-downloads.json','utf8'));
const {fbxMinimalForAsset}=await import('../src/lib/fbx-minimal-downloads.mjs');
assert.deepEqual(fbxProjection,JSON.parse(await readFile('src/data/fbx-minimal-downloads.json','utf8')),'Built FBX projection differs from generated binding');
assert.equal(fbxProjection.schemaVersion,1);
assert.equal(fbxProjection.coverage.publicModels,catalog.assets.filter(a=>a.type==='model').length);
assert.equal(fbxProjection.coverage.fbxReadyModels,new Set(fbxProjection.formats.map(x=>x.id)).size);
for(const record of fbxProjection.formats){
 const asset=catalog.assets.find(a=>a.id===record.id&&a.version===record.assetVersion);
 assert.ok(fbxMinimalForAsset(asset,fbxProjection),'Invalid FBX public projection');
 const {delivery,...legacy}=asset.downloads;
 assert.deepEqual(delivery,bindDelivery({...asset,downloads:legacy},[record],new Map([[asset.id,delivery.files[0].fetch]])).downloads.delivery);
 const manifest=JSON.parse(await readFile(await resolveFile(asset.manifestUrl),'utf8'));
 assert.deepEqual(manifest.downloads.delivery,delivery);
 // Reconstruct every model from the actual built chunks, not the prep cache.
 // The same browser reader verifies compressed, expanded and final FBX hashes.
 await buildBundle(planBundle([asset],{limit:Number.MAX_SAFE_INTEGER}),{cryptoImpl:webcrypto,fetchImpl:async url=>new Response(await readFile(await resolveFile(url)))});
 const page=await readFile(await resolveFile(asset.pageUrl),'utf8');
 assert.ok(page.includes(record.archive.url)&&page.includes(record.direct.url));
 assert.ok(!page.includes('data-format="fbx"'),'Minimal FBX must remain download-only');
}
assert.ok(!Object.hasOwn(fbxProjection,'releases')&&!Object.hasOwn(fbxProjection,'provenance'),'Private QA ledger leaked');
