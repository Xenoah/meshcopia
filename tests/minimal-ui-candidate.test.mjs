import {completeTexture} from './delivery-fixtures.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,writeFile,rm} from 'node:fs/promises';
import {createHash,webcrypto} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import os from 'node:os';
import path from 'node:path';
import {validateMinimalActivation} from '../scripts/lib/minimal-downloads.mjs';
import {planBundle,buildBundle,POLICY} from '../src/lib/batch-download.mjs';

test('combined candidate keeps one catalog init and one batch init',async()=>{
  const index=await readFile(new URL('../src/pages/index.astro',import.meta.url),'utf8');
  assert.equal((index.match(/initCatalog\(\)/g)||[]).length,1);
  assert.equal((index.match(/initBatchDownload\(\)/g)||[]).length,1);
  assert.match(index,/import \{initBatchDownload\} from '\.\.\/lib\/batch-download-ui'/);
  assert.match(index,/id="catalog-data"/);assert.match(index,/id="quick-dialog"/);
});
test('all contributor entrypoints refer to one shared production document',async()=>{
  for(const name of ['README.md','AGENTS.md','CLAUDE.md']) {
    const text=await readFile(new URL('../'+name,import.meta.url),'utf8');
    assert.ok(text.includes('docs/ASSET_PRODUCTION_RULES.md'),name);
  }
  const rules=await readFile(new URL('../docs/ASSET_PRODUCTION_RULES.md',import.meta.url),'utf8');
  assert.match(rules,/FBX as the consumer model format/);assert.match(rules,/clean scene/);assert.match(rules,/single root `LICENSE\.txt`/);
});
test('ordinary activation retains the strict schema and production validation hooks',async()=>{
  const activation=JSON.parse(await readFile(new URL('../docs/minimal-activation.json',import.meta.url),'utf8'));
  validateMinimalActivation(activation);
  const generate=await readFile(new URL('../scripts/generate.mjs',import.meta.url),'utf8');
  assert.match(generate,/assertCompleteModelDeliveries/);assert.match(generate,/prepareMinimalDownloads/);
  assert.match(generate,/prepareFbxMinimalDownloads/);assert.doesNotMatch(generate,/prepareSidecars|alternate-formats/);
  const detail=await readFile(new URL('../src/pages/assets/[id].astro',import.meta.url),'utf8');assert.match(detail,/fbx-download/);assert.doesNotMatch(detail,/alternate-formats/);
});
test('live browser entrypoint delegates to the non-injected post-deployment gate',async()=>{
  const source=await readFile(new URL('./live-browser-proof.mjs',import.meta.url),'utf8');
  assert.match(source,/process.argv.push\('--live'\)/);
  assert.match(source,/test-minimal-downloads-browser.mjs/);
  assert.doesNotMatch(source,/createObjectURL|downloads.minimal=/);
});
test('full-P verification workflow has read-only permissions and no publication actions',async()=>{
  const workflow=await readFile(new URL('../.github/workflows/verify-minimal-ui.yml',import.meta.url),'utf8');
  assert.match(workflow,/branches: \[minimal\/verify-p-v1\]/);assert.match(workflow,/workflow_dispatch:/);
  assert.equal((workflow.match(/contents: read/g)||[]).length,2);
  assert.doesNotMatch(workflow,/contents: write|pages:|id-token:|packages: write|deploy-pages|upload-pages|release:bundle|git push|GH_TOKEN|secrets\./);
  assert.match(workflow,/persist-credentials: false/);
  for(const command of ['node scripts/check-full-p-inputs.mjs','npm run check','node scripts/test-browser.mjs','node scripts/test-minimal-downloads-browser.mjs'])assert.ok(workflow.includes(command),command);
  assert.ok(workflow.indexOf('npm run check')<workflow.indexOf('node scripts/test-minimal-downloads-browser.mjs'));
  assert.match(workflow,/actions\/upload-artifact@v4/);assert.match(workflow,/if: always\(\)/);
});
test('browser-evidence recorder validates ZIP payloads and retains fixture limitations (synthetic inputs)',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'minimal-browser-evidence-fixture-'));
  const digest=data=>createHash('sha256').update(data).digest('hex');
  try {
    const assets=['sage-terrazzo','studio-chair'].map(id=>{
      const data=Buffer.from(id),name=id==='studio-chair'?'model.glb':'color.png';
      const file={name,bytes:data.length,sha256:digest(data),url:`https://xenoah.github.io/meshcopia/assets/${id}/source/${name}`};
      const text=`Fixture only: ${id}\nCC BY 4.0\n`;
      return completeTexture({id,status:'public',version:'1.0.0',files:[file],downloads:{minimal:{id,assetVersion:'1.0.0',contentPolicy:POLICY,noticeFile:'LICENSE.txt',sourceFiles:[file],notice:{filename:'LICENSE.txt',text,bytes:Buffer.byteLength(text),sha256:digest(text)}}}});
    });
    const plan=planBundle(assets),blob=await buildBundle(plan,{cryptoImpl:webcrypto,fetchImpl:async url=>new Response(assets.find(a=>url.includes('/'+a.id+'/')).id)});
    for(const name of ['live-browser-proof.zip','batch-desktop.zip','batch-mobile.zip'])await writeFile(path.join(root,name),Buffer.from(await blob.arrayBuffer()));
    for(const name of ['batch-desktop.png','batch-mobile.png'])await writeFile(path.join(root,name),'synthetic image fixture');
    const proof={origin:'https://xenoah.github.io',ids:assets.map(a=>a.id),entries:plan.entries.map(({name,bytes,sha256})=>({name,bytes,sha256})),extractionVerified:true,raw:{status:200,type:'cors',url:'https://raw.githubusercontent.com/Xenoah/meshcopia/main/content/assets/studio-chair/source/model.glb'}};
    await writeFile(path.join(root,'live-browser-proof.json'),JSON.stringify(proof));
    const script=fileURLToPath(new URL('../scripts/record-download-browser-evidence.mjs',import.meta.url));
    execFileSync(process.execPath,[script],{cwd:root,stdio:'pipe'});
    const report=JSON.parse(await readFile(path.join(root,'test-results/minimal-ui-browser.json'),'utf8'));
    assert.equal(report.scope.fixtureNoticeText,true);assert.equal(report.scope.fixtureReadiness,true);assert.equal(report.scope.productionActivation,'empty');assert.equal(report.scope.releaseZipReadback,false);assert.equal(report.scope.sitePublication,false);assert.equal(report.files.length,6);
    proof.entries[0].sha256='0'.repeat(64);await writeFile(path.join(root,'live-browser-proof.json'),JSON.stringify(proof));
    assert.throws(()=>execFileSync(process.execPath,[script],{cwd:root,stdio:'pipe'}));
  } finally {await rm(root,{recursive:true,force:true})}
});
