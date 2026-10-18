import {loadProductionPolicy,assertPublicationScope} from './lib/production-catalog.mjs';
const policy=await loadProductionPolicy(),publicCount=policy.publicIds.length,modelCount=publicCount-36;
// Migration successor to the original API byte-compatibility check.
// API v3 deliberately retires Pages ZIP URLs, while retaining original sources,
// historical archive records and immutable public Release attachments.
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {verifySiteMigration} from './lib/site-migration.mjs';
const report=await verifySiteMigration();
const side=JSON.parse(await readFile('dist/api/fbx-minimal-downloads.json','utf8'));
const catalog=JSON.parse(await readFile('dist/api/catalog.json','utf8'));
assert.deepEqual(side.coverage,{publicModels:modelCount,fbxReadyModels:modelCount});
assert.equal(report.publicAssets,publicCount);assert.equal(report.textures,36);
assert.deepEqual(side.formats.map(x=>x.id).sort(),catalog.assets.filter(x=>x.type==='model').map(x=>x.id).sort());
assert.ok(!Object.hasOwn(side,'provenance')&&!Object.hasOwn(side,'releases'));
await mkdir('test-results',{recursive:true});
await writeFile('test-results/fbx-distribution-migration.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
