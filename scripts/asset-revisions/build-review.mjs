// Apply an explicitly unpublished overlay AFTER the unmodified production
// generation/check. No frozen adapter is bypassed and no Release is invented.
import {readFile,writeFile,mkdir,cp,lstat} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {readAsset,sha256,attributionFor,SITE} from '../lib/catalog.mjs';
import {prepareDeliveryPayloads} from '../lib/delivery-chunks.mjs';
import {DELIVERY_POLICY,deliveryReadiness} from '../../src/lib/delivery.mjs';
const input=path.resolve(process.argv[2]??'.cache/asset-revision-qa/candidate-final');
const manifest=JSON.parse(await readFile(path.join(input,'candidate-packages.json')));
assert.equal(manifest.publicationState,'unpublished-candidate');
assert.deepEqual(manifest.records.map(r=>r.id).sort(),['garden-arch','household-two-door-refrigerator','wayfinding-sign']);
const catalog=JSON.parse(await readFile('src/data/catalog.json')),baseline=JSON.parse(await readFile('dist/api/catalog.json'));
assert.equal(baseline.count,454);assert.equal(catalog.length,454);assert.deepEqual(catalog,baseline.assets);
for(const a of catalog.filter(a=>a.type==='model'))assert.equal(a.downloads.delivery.verification.state,'published-verified');
const payloadRoot='.cache/asset-revision-review-payloads';await mkdir(payloadRoot,{recursive:true});
for(const r of manifest.records){
 const bytes=await readFile(path.join(input,r.fbx));assert.equal(bytes.length,r.fbxBytes);assert.equal(sha256(bytes),r.fbxSha256);
 await writeFile(`${payloadRoot}/${r.fbxSha256}.fbx`,bytes);
}
const chunks=await prepareDeliveryPayloads(manifest.records.map(r=>({id:r.id,direct:{bytes:r.fbxBytes,sha256:r.fbxSha256}})),{source:payloadRoot,site:SITE});
await cp(chunks.directory,'public/download-data',{recursive:true});
for(const r of manifest.records){
 const dir=`asset-revisions/repair-appliances-v1/${r.id}`,asset=await readAsset(dir),{dir:unused,sources,...metadata}=asset;
 assert.equal(sha256(await readFile(path.join(dir,'asset.json'))),r.metadataSha256);assert.equal(metadata.version,r.assetVersion);
 assert.equal(sha256(await readFile(path.join(dir,'source',metadata.preview))),r.sourceGlbSha256);
 const reportBytes=await readFile(path.join(input,r.roundtripReport)),report=JSON.parse(reportBytes);assert.equal(sha256(reportBytes),r.roundtripReportSha256);assert.equal(report.passed,true);assert.equal(report.sourceGlbSha256,r.sourceGlbSha256);assert.equal(report.fbxSha256,r.fbxSha256);
 for(const format of ['glb','fbx']){
  const audit=JSON.parse(await readFile(`test-results/asset-revisions/imports/${r.id}-fixed-${format}.json`));assert.equal(audit.triangles,metadata.triangles);
  assert.ok(audit.parts.every(p=>p.worldDeterminant>0&&p.degenerateFaces===0&&p.components.every(c=>c.closedOriented&&c.orientation==='outward')));
  metadata.dimensions.forEach((d,i)=>assert.ok(Math.abs(d-audit.dimensionsMetersYUp[i])<.00005));
 }
 const old=catalog.find(a=>a.id===r.id),destination=`public/assets/${r.id}`,url=`${SITE}/assets/${r.id}`;
 await mkdir(`${destination}/source`,{recursive:true});const files=[...(old?.files??[])];
 for(const name of sources){const data=await readFile(path.join(dir,'source',name));assert.ok(!files.some(f=>f.name===name),'Never replace a legacy source URL');await cp(path.join(dir,'source',name),`${destination}/source/${name}`);files.push({name,format:path.extname(name).slice(1).toUpperCase(),bytes:data.length,sha256:sha256(data),url:`${url}/source/${name}`})}
 const thumbnail=`thumbnail-${metadata.version}.webp`;await cp(path.join(dir,metadata.thumbnail),`${destination}/${thumbnail}`);
 const deliveryRoot=`${SITE}/review-packages/${r.id}/${r.assetVersion}/`,deliveryDir=`public/review-packages/${r.id}/${r.assetVersion}`;await mkdir(deliveryDir,{recursive:true});
 const archive=await readFile(path.join(input,r.archive));assert.equal(archive.length,r.archiveBytes);assert.equal(sha256(archive),r.archiveSha256);
 const archiveName=path.basename(r.archive);await writeFile(`${deliveryDir}/${archiveName}`,archive);await cp(path.join(input,r.fbx),`${deliveryDir}/${r.id}.fbx`);
 const item={...metadata,thumbnail:`${url}/${thumbnail}`,pageUrl:`${url}/`,manifestUrl:`${SITE}/api/assets/${r.id}.json`,attribution:attributionFor(metadata),licenseUrl:'https://creativecommons.org/licenses/by/4.0/',previewUrl:`${url}/source/${metadata.preview}`,files,downloads:{delivery:{schemaVersion:1,id:r.id,assetVersion:r.assetVersion,packageVersion:'1.0.0',contentPolicy:DELIVERY_POLICY,sourceFiles:files,archive:{filename:archiveName,url:deliveryRoot+archiveName,bytes:r.archiveBytes,sha256:r.archiveSha256},files:[{name:r.id+'.fbx',format:'FBX',url:deliveryRoot+r.id+'.fbx',bytes:r.fbxBytes,sha256:r.fbxSha256,fetch:chunks.files.get(r.id)}],notice:{filename:'LICENSE.txt',text:r.notice,bytes:r.noticeBytes,sha256:r.noticeSha256},verification:{state:'local-review-verified',publicationState:'unpublished-candidate'}}}};
 assert.ok(deliveryReadiness(item,{allowReview:true}).ready);assert.equal(deliveryReadiness(item).ready,false);
 const index=catalog.findIndex(a=>a.id===r.id);if(index<0)catalog.push(item);else catalog[index]=item;
 await writeFile(`public/api/assets/${r.id}.json`,JSON.stringify(item,null,2)+'\n');
}
assert.equal(catalog.length,455);for(const a of baseline.assets)assert.ok(catalog.some(b=>b.id===a.id),'No existing model may be removed');
await writeFile('src/data/catalog.json',JSON.stringify(catalog,null,2)+'\n');
await writeFile('public/api/catalog.json',JSON.stringify({schemaVersion:'3.0.0-review',publicationState:'unpublished-candidate',name:'Meshcopia unpublished review',license:'CC-BY-4.0',count:catalog.length,assets:catalog},null,2)+'\n');
await writeFile('public/api/catalog.ndjson',catalog.map(a=>JSON.stringify(a)).join('\n')+'\n');
const projection=JSON.parse(await readFile('src/data/fbx-minimal-downloads.json'));
projection.formats=projection.formats.filter(r=>!manifest.records.some(candidate=>candidate.id===r.id));
projection.coverage={publicModels:419,fbxReadyModels:projection.formats.length,unpublishedReviewModels:3};
projection.publicationState='unpublished-candidate';
for(const file of ['src/data/fbx-minimal-downloads.json','public/api/fbx-minimal-downloads.json'])await writeFile(file,JSON.stringify(projection,null,2)+'\n');
const build=spawnSync('node',['node_modules/astro/astro.js','build'],{stdio:'inherit',env:{...process.env,PUBLIC_ASSET_REVIEW:'1'}});assert.equal(build.status,0);
await writeFile('dist/robots.txt','User-agent: *\nDisallow: /\n');
console.log('Unpublished 455-item review build; 454 existing IDs retained, two revised, one refrigerator added.');
