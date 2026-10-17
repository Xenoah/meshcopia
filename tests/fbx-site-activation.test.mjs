import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {validateFbxMinimalActivation} from '../scripts/lib/fbx-minimal-downloads.mjs';
const read=p=>readFile(new URL('../'+p,import.meta.url));
const json=async p=>JSON.parse(await read(p));
const sha=b=>createHash('sha256').update(b).digest('hex');

test('actual FBX activation binds reviewed release, T and all 275 attachment identities',async()=>{
 const c=validateFbxMinimalActivation(await json('docs/fbx-minimal-activation.json'));assert.equal(c.activations.length,1);const a=c.activations[0];
 assert.equal(a.releaseId,414350272);assert.equal(a.verificationCommit,'83a1daedf3ad7563fa55bf0cca40ca749689e139');assert.equal(a.transportEvidenceSha256,'5d262d7a914fb9cd60f53d7d68f0ee1c3d11c8cd5cbfd733a12b5496cb356fb4');
 const raw=await read(a.transportEvidenceFile);assert.equal(sha(raw),a.transportEvidenceSha256);const t=JSON.parse(raw);
 assert.equal(t.releaseId,a.releaseId);assert.equal(t.tag,a.releaseTag);assert.equal(t.fCommit,a.verificationCommit);assert.equal(t.inventorySha256,a.inventorySha256);
 assert.equal(t.transportExecution.commit,'0c8048cf635cd84369d2301ebf291b61684ca616');assert.equal(t.transportExecution.runId,38820201372);assert.equal(t.transportExecution.runAttempt,1);assert.equal(t.transportExecution.jobId,116714655304);
 assert.equal(t.assets.length,275);assert.equal(new Set(t.assets.map(x=>x.name)).size,275);assert.equal(new Set(t.assets.map(x=>x.assetId)).size,275);
 const expected=await json('docs/fbx-minimal-verification/expected137.json');assert.equal(expected.models.length,137);
 for(const m of expected.models){const f=t.assets.find(x=>x.name===m.id+'.fbx'),z=t.assets.find(x=>x.name===m.filename);assert.ok(f&&z);assert.equal(f.bytes,m.fbxBytes);assert.equal(f.sha256,m.fbxSha256);assert.equal(z.bytes,m.archiveBytes);assert.equal(z.sha256,m.archiveSha256);}
 for(const x of t.assets){assert.equal(x.anonymousReadback,true);assert.equal(x.url,`https://github.com/Xenoah/meshcopia/releases/download/${a.releaseTag}/${x.name}`);}
 assert.equal(t.assets.find(x=>x.name==='fbx-minimal-inventory.json').sha256,a.inventorySha256);
});

test('successful F/R source pins and ordinary packaging helpers are exact',async()=>{
 const [a]=(await json('docs/fbx-minimal-activation.json')).activations,t=await json(a.transportEvidenceFile),p=t.provenance,r=t.transportExecution;
 const pins={'docs/fbx-minimal-verification/source137.json':p.sourceInventorySha256,'docs/fbx-minimal-verification/expected137.json':p.expectedManifestSha256,'docs/fbx-minimal-verification/runtime.json':p.runtimeSha256,[p.workflowPath]:p.workflowSha256,[r.workflowPath]:r.workflowSha256,'docs/fbx-minimal-transport/approval.json':r.approvalSha256,...r.adapterSha256};
 const rt=await json('docs/fbx-minimal-verification/runtime.json');Object.assign(pins,rt.supportFiles,Object.fromEntries(Object.entries(rt.recipe).map(([k,v])=>['scripts/fbx-verification/'+k,v])));
 for(const [file,digest] of Object.entries(pins))assert.equal(sha(await read(file)),digest,file);
 const approval=await json('docs/fbx-minimal-transport/approval.json');for(const [k,v] of Object.entries(p))assert.deepEqual(approval[k],v,k);
});

test('every active full-site workflow requires explicit token-free durable prep before one check',async()=>{
 for(const file of ['publish.yml','verify-minimal-ui.yml','verify-fbx-minimal-ui.yml']){
  const w=(await read('.github/workflows/'+file)).toString(),prep='python3 scripts/prepare-fbx-minimal-activation.py --repo "$GITHUB_WORKSPACE" --verification-mode durable-transport-attestation';
  assert.equal((w.match(/run: npm run check\n/g)||[]).length,1,file);assert.equal(w.split(prep).length-1,1,file);assert.ok(w.indexOf(prep)<w.indexOf('run: npm run check'),file);
  assert.doesNotMatch(w,/GITHUB_TOKEN:|actions: read|GITHUB_ENV|--qa-artifact|full-internal-qa/);
 }
});

test('FBX site verification is branch-bounded, read-only and checks output without rebuilding',async()=>{
 const w=(await read('.github/workflows/verify-fbx-minimal-ui.yml')).toString();assert.match(w,/branches: \[fbx\/verify-p-v1\]/);assert.match(w,/github.ref == 'refs\/heads\/fbx\/verify-p-v1'/);
 assert.equal((w.match(/contents: read/g)||[]).length,2);assert.match(w,/persist-credentials: false/);assert.match(w,/fetch-depth: 0/);
 assert.doesNotMatch(w,/contents: write|pages:|id-token:|packages: write|deploy-pages|upload-pages|release:bundle|git push|GH_TOKEN|secrets\.|npm run (build|generate)/);
 for(const cmd of ['node scripts/check-archive-runtime.mjs','node scripts/check-archive-lock.mjs --check-history','python3 scripts/check-textures.py','node scripts/check-fbx-minimal-baseline.mjs','node scripts/test-browser.mjs','node scripts/test-minimal-downloads-browser.mjs','node scripts/test-fbx-minimal-downloads-browser.mjs'])assert.ok(w.includes(cmd),cmd);
 assert.doesNotMatch(w.slice(w.indexOf('run: npm run check')+1),/prepare-fbx-minimal-activation\.py/);assert.match(w,/path: test-results\//);assert.doesNotMatch(w,/path:.*\.cache/);
});

test('FBX compatibility note preserves original selectors and honest importer limits',async()=>{
 const s=(await read('src/pages/assets/[id].astro')).toString();for(const text of ['primaryDownload(a)','directModelFiles(a)','fbxMinimalForAsset(a,fbxProjection)','FBX materials, transparency and face culling can vary by importer.','GLB is retained for previews.','Matching appearance in Unity or Godot is not guaranteed.'])assert.ok(s.includes(text),text);
 assert.match(s,/class="fbx-download"/);assert.doesNotMatch(s,/data-format="fbx"/);
 const b=(await read('scripts/test-fbx-minimal-downloads-browser.mjs')).toString();assert.match(b,/for\(const record of side.formats\)/);assert.match(b,/waitForEvent\('download'/);assert.match(b,/verify_two_entry_zip/);assert.match(b,/javaScriptEnabled:false/);assert.doesNotMatch(b,/\.route\(|Authorization|GITHUB_TOKEN|GH_TOKEN/);
});

test('site release identity is consistently 1.11.0',async()=>{
 const p=await json('package.json'),l=await json('package-lock.json'),r=await json('.release.json');assert.equal(p.version,'1.11.0');assert.equal(l.version,p.version);assert.equal(l.packages[''].version,p.version);assert.equal(r.version,p.version);assert.equal(r.notes,'docs/releases/v1.11.0.md');assert.ok((await read(r.notes)).toString().includes('GLB'));
});
