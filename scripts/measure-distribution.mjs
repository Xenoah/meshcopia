import {readFile,readdir,lstat,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {measureDist} from './lib/download-browser-contract.mjs';
const dist=await measureDist('dist',{enforceBudget:false});
async function size(root){let bytes=0;for(const row of await readdir(root,{withFileTypes:true})){const file=path.join(root,row.name);bytes+=row.isDirectory()?await size(file):(await lstat(file)).size;}return bytes;}
const catalog=JSON.parse(await readFile('dist/api/catalog.json')).assets;
const archives=JSON.parse(await readFile('docs/archive-lock.json')).archives;
const models=catalog.filter(a=>a.type==='model'),sum=f=>models.reduce((n,a)=>n+f(a),0);
const report={publicAssets:catalog.length,models:models.length,textures:catalog.length-models.length,previousPublishedDistBytes:546137684,beforeThumbnailOffloadBytes:1078999992,operationalHeadroomBytes:950000000-dist.bytes,addedSincePreviousPublicationBytes:dist.bytes-546137684,externalOriginalBytes:sum(a=>a.files.filter(f=>f.url.startsWith('https://raw.githubusercontent.com/')).reduce((n,f)=>n+f.bytes,0)),baselineCommit:'7262f3e34559234de636cd5351d89fc733df008d',baselineDistBytes:939340180,
 previousFbxCandidateDistBytes:1079586102,
 ...dist,savedFromPreMigrationBytes:939340180-dist.bytes,savedFromPreviousFbxCandidateBytes:1079586102-dist.bytes,
 retiredPagesArchives:archives.length,retiredPagesArchiveBytes:archives.reduce((n,a)=>n+a.bytes,0),
 chunkTransportBytes:await size('dist/download-data'),
 originalModelSourceBytes:sum(a=>a.files.reduce((n,f)=>n+f.bytes,0)),
 fbxPayloadBytes:sum(a=>a.downloads.delivery.files.reduce((n,f)=>n+f.bytes,0)),
 previousOrdinaryModelZipBytes:181983181,
 fbxOrdinaryModelZipBytes:sum(a=>a.downloads.delivery.archive.bytes),
 operationalBudgetBytes:950000000,hardBudgetBytes:1000000000,
 deployable:dist.bytes<950000000,
 scope:'Actual complete built dist; retired full/models Pages ZIPs excluded; original173 plus explicitly verified cohorts; measurement does not perform deployment'};
await mkdir('test-results',{recursive:true});
await writeFile('test-results/fbx-distribution-size.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
assert.ok(report.deployable,`Publication blocked: full dist ${dist.bytes} exceeds 950000000 bytes`);
