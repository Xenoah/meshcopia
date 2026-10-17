import {prepareDeliveryPayloads} from './lib/delivery-chunks.mjs';
import {bindDelivery} from './lib/delivery.mjs';
import {prepareFbxMinimalDownloads,writeFbxMinimalDownloads} from './lib/fbx-minimal-downloads.mjs';
import {assertCompleteModelDeliveries} from './lib/model-delivery-policy.mjs';
import {prepareMinimalDownloads,bindMinimalDownload} from './lib/minimal-downloads.mjs';
import { mkdir, rm, cp, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { readCatalog, attributionFor, sha256, SITE, LICENSE_URL, MODEL_EXT } from './lib/catalog.mjs';
import { writeStoreZip } from './lib/zip-store.mjs';
import { zipOptionsForPackage } from './lib/zip-policy.mjs';
import { assertArchiveRuntime } from './lib/archive-runtime.mjs';
import { verifyArchiveLock, archiveLockPath } from './lib/archive-lock.mjs';

const assets = await readCatalog(); // Validate before changing generated output.
const verifiedFbx = await prepareFbxMinimalDownloads(assets); // Trusted same-job prep, then current source/history checks.
await assertCompleteModelDeliveries(assets,{verifiedFbx,baseline:JSON.parse(await readFile('docs/model-delivery-baseline.json','utf8'))});
const minimalDownloads = await prepareMinimalDownloads(assets); // Verify public bytes before cleanup.
const deliveryPayloads = await prepareDeliveryPayloads(verifiedFbx,{site:SITE});
if (assets.some(a => a.status !== 'draft' && zipOptionsForPackage(a).compress)) assertArchiveRuntime();
await rm('public/assets', {recursive:true,force:true});
await rm('public/api', {recursive:true,force:true});
await rm('public/download-data', {recursive:true,force:true});
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
  await cp(path.join(dir,'source'), `${out}/source`, {recursive:true});
  await cp(path.join(dir,asset.thumbnail), `${out}/thumbnail${path.extname(asset.thumbnail)}`);
  const attribution = attributionFor(asset);
  const license = `${asset.titleEn}\nCopyright (c) ${asset.created.slice(0,4)} ${asset.author}\nLicensed under Creative Commons Attribution 4.0 International (CC BY 4.0).\n${LICENSE_URL}\n${LICENSE_URL}legalcode.en\n\nYou may share and adapt, including commercially. Give appropriate credit, link the license, and indicate changes. No additional restrictions. No warranties. This notice is a summary; the linked legal code controls.\n`;
  const common = [{name:'LICENSE.txt',data:license},{name:'ATTRIBUTION.txt',data:attribution+'\n'}];
  const readme = `# ${asset.titleEn}\n\n${asset.description}\n\n${asset.descriptionEn}\n\n${attribution}\n\nAsset ID: ${asset.id}\nVersion: ${asset.version}\nType: ${asset.type}\n${asset.type==='model' ? `Unit: ${asset.unit}; up axis: ${asset.upAxis}\n` : `Resolution: ${asset.width} x ${asset.height}px; wrap mode (both axes): ${asset.wrapMode}; seamless under this mode: ${asset.seamless}\nMaps: ${Object.keys(asset.maps).join(', ')}; base color: sRGB; normal convention: ${asset.normalConvention||'no normal map'}\n${asset.usageEn||''}\n`}\nProvenance: ${asset.provenance.method} / ${asset.provenance.tool}\n${asset.provenance.rights}\n\nSource and reusable generator: https://github.com/Xenoah/meshcopia\n`;
  const entries = [], files = [];
  for (const file of sources) {
    const data = await readFile(path.join(dir,'source',file));
    entries.push({name:`source/${file}`,data});
    files.push({name:file,format:path.extname(file).slice(1).toUpperCase(),bytes:data.length,sha256:sha256(data),url:`${url}/source/${file.split('/').map(encodeURIComponent).join('/')}`});
  }
  const fullName = `${asset.id}-${asset.version}.zip`;
  const zipOptions = zipOptionsForPackage(asset);
  await writeStoreZip(`${out}/${fullName}`, [...entries,...common,{name:'README.md',data:readme},{name:'asset.json',data:JSON.stringify(metadata,null,2)},{name:`preview${path.extname(asset.thumbnail)}`,data:await readFile(path.join(dir,asset.thumbnail))}], zipOptions);
  const fullData = await readFile(`${out}/${fullName}`);
  const downloads = {full:{url:`${url}/${fullName}`,bytes:fullData.length,sha256:sha256(fullData)}};
  if (asset.type === 'model') {
    // Preserve companion maps/buffers/MTL: models-only excludes presentation/docs,
    // never dependencies needed to use a downloaded model.
    const name = `${asset.id}-${asset.version}-models.zip`;
    await writeStoreZip(`${out}/${name}`, [...entries,...common], zipOptions);
    const data = await readFile(`${out}/${name}`);
    downloads.models = {url:`${url}/${name}`,bytes:data.length,sha256:sha256(data)};
    const direct = files.find(f => f.name===asset.preview && ['GLB','STL','STEP','STP'].includes(f.format));
    if (direct) downloads.direct = direct;
  }
  const item = bindDelivery(bindMinimalDownload({...metadata,thumbnail:`${url}/thumbnail${path.extname(asset.thumbnail)}`,pageUrl:`${url}/`,manifestUrl:`${SITE}/api/assets/${asset.id}.json`,attribution,licenseUrl:LICENSE_URL,files,downloads},minimalDownloads),verifiedFbx,deliveryPayloads.files);
  if (asset.preview) item.previewUrl = files.find(f=>f.name===asset.preview).url;
  if (asset.maps) item.mapUrls = Object.fromEntries(Object.entries(asset.maps).map(([k,f])=>[k, files.find(item=>item.name===f).url]));
  catalog.push(item);
  await writeFile(`public/api/assets/${asset.id}.json`,JSON.stringify(item,null,2)+'\n');
}
await verifyArchiveLock({root:'public',catalog,lock:JSON.parse(await readFile(archiveLockPath,'utf8')),requireComplete:false});
await writeFile('src/data/catalog.json',JSON.stringify(catalog,null,2)+'\n');
const publicAssets = catalog.filter(a=>a.status==='public');
await writeFile('public/api/catalog.json',JSON.stringify({schemaVersion:'2.1.0',name:'Meshcopia',license:'CC-BY-4.0',count:publicAssets.length,assets:publicAssets},null,2)+'\n');
await writeFile('public/api/catalog.ndjson',publicAssets.map(a=>JSON.stringify(a)).join('\n')+'\n');
console.log(`Generated ${catalog.length} asset pages/manifests and ZIPs; ${publicAssets.length} listed publicly.`);

await writeFbxMinimalDownloads(verifiedFbx,assets);
