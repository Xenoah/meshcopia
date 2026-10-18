import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {validateBytes} from 'gltf-validator';
import {readAsset} from '../lib/catalog.mjs';
const baseline='fd595dfdc8b17fe515a618bf2f309e9cc61a7491';
const diff=spawnSync('git',['diff',baseline,'--','content/assets','scripts/create-starter-assets.py','scripts/fbx-verification','scripts/lib/fbx-minimal-downloads.mjs','scripts/lib/cohort-downloads.mjs','docs/cohorts','docs/fbx-minimal-verification','docs/fbx-minimal-activation','.release.json'],{encoding:'utf8'});
assert.equal(diff.status,0);assert.equal(diff.stdout,'','Published sources and frozen adapters must remain unchanged');
const assets=await Promise.all(['garden-arch','wayfinding-sign','household-two-door-refrigerator'].map(id=>readAsset(`asset-revisions/repair-appliances-v1/${id}`)));
await mkdir('test-results/asset-revisions',{recursive:true});
const results=[];
for(const a of assets){const data=await readFile(`${a.dir}/source/${a.preview}`),report=await validateBytes(new Uint8Array(data),{uri:a.preview,maxIssues:1000});assert.equal(report.issues.numErrors,0,JSON.stringify(report.issues));results.push({id:a.id,version:a.version,triangles:a.triangles,dimensions:a.dimensions,issues:report.issues})}
await writeFile('test-results/asset-revisions/gltf-validation.json',JSON.stringify(results,null,2)+'\n');
console.log('Three candidate GLBs validated; all published model, vehicle, metadata and frozen adapter files unchanged.');
