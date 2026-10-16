// Source-only candidate verification. This does not generate assets or build a site.
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {transform} from '@astrojs/compiler';

const {validateMinimalActivation}=await import('./lib/minimal-downloads.mjs');
const {validateFbxMinimalActivation}=await import('./lib/fbx-minimal-downloads.mjs');
const activation=JSON.parse(await readFile('docs/minimal-activation.json','utf8'));
validateMinimalActivation(activation);
const fbxActivation=validateFbxMinimalActivation(JSON.parse(await readFile('docs/fbx-minimal-activation.json','utf8')));
const index=await readFile('src/pages/index.astro','utf8');
for(const name of ['initCatalog','initBatchDownload'])assert.equal((index.match(new RegExp(`${name}\\(\\)`,'g'))||[]).length,1,`${name} must initialize exactly once`);
for(const file of ['AGENTS.md','README.md','CLAUDE.md'])assert.ok((await readFile(file,'utf8')).includes('docs/ASSET_PRODUCTION_RULES.md'),`${file} must link the shared production rules`);
assert.ok(!(await readFile('scripts/generate.mjs','utf8')).includes('prepareSidecars'),'Old FBX P must not be mixed into this ordinary download candidate');
const syntaxFiles=['src/lib/downloads.mjs','src/lib/catalog-ui.js','src/lib/batch-download.mjs','src/lib/batch-download-ui.js','scripts/lib/minimal-downloads.mjs','scripts/lib/model-delivery-policy.mjs','scripts/generate.mjs','scripts/check-dist.mjs','scripts/record-download-browser-evidence.mjs','tests/live-browser-proof.mjs','tests/batch-download-browser.mjs','src/lib/fbx-minimal-downloads.mjs','scripts/lib/fbx-minimal-downloads.mjs','scripts/check-fbx-minimal-baseline.mjs','scripts/test-fbx-minimal-downloads-browser.mjs'];
for(const file of syntaxFiles)execFileSync(process.execPath,['--check',file],{stdio:'pipe'});
const astro=[];
for(const file of ['src/components/AssetCard.astro','src/pages/assets/[id].astro','src/pages/agents.astro','src/pages/index.astro']) {
  const source=await readFile(file,'utf8');
  const result=await transform(source,{filename:file});
  // Existing JSON data script intentionally needs no script processing. Keep
  // its known informational hint visible; reject every other diagnostic.
  const unexpected=result.diagnostics.filter(d=>!(file==='src/pages/index.astro'&&d.severity===4&&d.code===4000&&source.split('\n')[d.location?.line-1]?.includes('<script id="catalog-data" type="application/json"')));
  assert.deepEqual(unexpected,[],`${file} unexpected compiler diagnostics`);
  astro.push({file,diagnostics:result.diagnostics});
}
await mkdir('test-results',{recursive:true});
const report={scope:'source-only; no build, publication, browser or release claim',activation:activation.activations.length?'configured-not-verified':'empty',fbxActivation:fbxActivation.activations.length?'configured-not-verified':'empty',syntaxFiles,astro,sourceCommit:process.env.GITHUB_SHA??null};
await writeFile('test-results/minimal-ui-source.json',JSON.stringify(report,null,2)+'\n');
console.log('Candidate source checks passed; these checks do not verify configured publication evidence.');
