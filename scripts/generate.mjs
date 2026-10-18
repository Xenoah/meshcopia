import {readProductionCatalog,loadProductionPolicy,originalThumbnailUrl,revisionIds} from './lib/production-catalog.mjs';
import {prepareRevisionDownloads} from './asset-revisions/activation.mjs';
import {prepareDeliveryPayloads} from './lib/delivery-chunks.mjs';
import {prepareCohortDownloads} from './lib/cohort-downloads.mjs';
import {bindDelivery} from './lib/delivery.mjs';
import {prepareFbxMinimalDownloads,writeFbxMinimalDownloads} from './lib/fbx-minimal-downloads.mjs';
import {assertCompleteModelDeliveries} from './lib/model-delivery-policy.mjs';
import {prepareMinimalDownloads,bindMinimalDownload} from './lib/minimal-downloads.mjs';
import { mkdir, rm, cp, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { readCatalog, attributionFor, sha256, SITE, LICENSE_URL } from './lib/catalog.mjs';
import {primaryDownload} from '../src/lib/downloads.mjs';
import assert from 'node:assert/strict';

assert.notEqual(process.env.PUBLIC_ASSET_REVIEW,'1','Production generation refuses review mode; use the separate asset revision review builder.');

const baseAssets = await readCatalog(); // Validate before changing generated output.
const baseFbx = [...await prepareFbxMinimalDownloads(baseAssets),...await prepareCohortDownloads(baseAssets)];
const assets=await readProductionCatalog(baseAssets), policy=await loadProductionPolicy();
const revisions=await prepareRevisionDownloads(assets);
const verifiedFbx=[...baseFbx.filter(r=>!revisions.some(x=>x.id===r.id)),...revisions];
assert.equal(new Set(verifiedFbx.map(r=>r.id)).size,verifiedFbx.length,'Duplicate FBX cohort IDs');
await assertCompleteModelDeliveries(assets,{verifiedFbx,baseline:JSON.parse(await readFile('docs/model-delivery-baseline.json','utf8'))});
const minimalDownloads = await prepareMinimalDownloads(baseAssets); // Verify public bytes before cleanup.
const deliveryPayloads = await prepareDeliveryPayloads(verifiedFbx,{site:SITE});
await rm('public/assets', {recursive:true,force:true});
await rm('public/api', {recursive:true,force:true});
await rm('public/download-data', {recursive:true,force:true});
await rm('public/review-packages', {recursive:true,force:true});
await cp(deliveryPayloads.directory,'public/download-data',{recursive:true});
await rm(deliveryPayloads.directory,{recursive:true,force:true});
await mkdir('public/assets', {recursive:true});
await mkdir('public/api/assets', {recursive:true});
await mkdir('src/data', {recursive:true});
await mkdir('public/vendor/occt-import-js', {recursive:true});
for (const file of ['occt-import-js.js','occt-import-js.wasm']) await cp(`node_modules/occt-import-js/dist/${file}`, `public/vendor/occt-import-js/${file}`);
await mkdir('public/vendor/licenses', {recursive:true});
for (const [source,name] of [['node_modules/three/LICENSE','three-MIT.txt'],['node_modules/astro/LICENSE','astro-MIT.txt'],['node_modules/occt-import-js/LICENSE.md','occt-import-js-LGPL-2.1.md'],['THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md']]) await cp(source,`public/vendor/licenses/${name}`);
const catalog = [];
for (const asset of assets) {
  if (asset.status === 'draft') continue;
  const {dir, sources, ...metadata} = asset;
  const out = `public/assets/${asset.id}`;
  const url = `${SITE}/assets/${asset.id}`;
  await mkdir(out, {recursive:true});
  const record=verifiedFbx.find(r=>r.id===asset.id);
  const revision=Boolean(policy.revision&&revisionIds.includes(asset.id)), cohort=!revision&&record?.verification.releaseTag.startsWith('cohort-');
  // New cohorts keep production originals at immutable Git URLs. Only their
  // unchanged GLB preview is copied into Pages; existing source URLs stay put.
  await mkdir(`${out}/source`,{recursive:true});
  if(cohort)await cp(path.join(dir,'source',asset.preview),`${out}/source/${asset.preview}`);
  else await cp(path.join(dir,'source'), `${out}/source`, {recursive:true});
  if(!cohort){
    const old=baseAssets.find(a=>a.id===asset.id);
    if(revision&&old)await cp(path.join(old.dir,old.thumbnail),`${out}/thumbnail${path.extname(old.thumbnail)}`);
    await cp(path.join(dir,asset.thumbnail),`${out}/${revision?'thumbnail-'+asset.version+'.webp':'thumbnail'+path.extname(asset.thumbnail)}`);
  }
  const thumbnail=originalThumbnailUrl(asset,policy);
  const attribution = attributionFor(asset);
  const files = [];
  for (const file of sources) {
    const data = await readFile(path.join(dir,'source',file));
    const sourceUrl=cohort&&file!==asset.preview?`https://raw.githubusercontent.com/Xenoah/meshcopia/${record.sourceCommit}/content/assets/${asset.id}/source/${file.split('/').map(encodeURIComponent).join('/')}`:`${url}/source/${file.split('/').map(encodeURIComponent).join('/')}`;
    files.push({name:file,format:path.extname(file).slice(1).toUpperCase(),bytes:data.length,sha256:sha256(data),url:sourceUrl});
  }
  // Production originals and previews remain separate from consumer delivery.
  // Retired full/models ZIP URLs are deliberately absent from API v3 and output.
  const original = {...metadata,thumbnail,pageUrl:`${url}/`,manifestUrl:`${SITE}/api/assets/${asset.id}.json`,attribution,licenseUrl:LICENSE_URL,files,downloads:{}};
  const item = asset.type === 'model'
    ? bindDelivery(original,verifiedFbx,deliveryPayloads.files)
    : bindMinimalDownload(original,minimalDownloads);
  assert.ok(primaryDownload(item),`Missing verified consumer download: ${asset.id}`);
  if (asset.preview) item.previewUrl = files.find(f=>f.name===asset.preview).url;
  if (asset.maps) item.mapUrls = Object.fromEntries(Object.entries(asset.maps).map(([k,f])=>[k, files.find(item=>item.name===f).url]));
  catalog.push(item);
  await writeFile(`public/api/assets/${asset.id}.json`,JSON.stringify(item,null,2)+'\n');
}
await writeFile('src/data/catalog.json',JSON.stringify(catalog,null,2)+'\n');
const publicAssets = catalog.filter(a=>a.status==='public');
await writeFile('public/api/catalog.json',JSON.stringify({schemaVersion:'3.0.0',name:'Meshcopia',license:'CC-BY-4.0',count:publicAssets.length,assets:publicAssets},null,2)+'\n');
await writeFile('public/api/catalog.ndjson',publicAssets.map(a=>JSON.stringify(a)).join('\n')+'\n');
console.log(`Generated ${catalog.length} asset pages/manifests; ${publicAssets.length} listed publicly; no legacy ZIP copies.`);

await writeFbxMinimalDownloads(verifiedFbx,assets);
