import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import os from 'node:os';
import path from 'node:path';
import {validateMinimalActivation,validateMinimalProjection,bindMinimalDownload} from '../scripts/lib/minimal-downloads.mjs';
import {sha256} from '../scripts/lib/catalog.mjs';
import {MINIMAL_CONTENT_POLICY} from '../src/lib/downloads.mjs';

test('empty activation remains compatible and has no network or Python prerequisites',()=>{
  assert.deepEqual(validateMinimalActivation({schemaVersion:1,repository:'Xenoah/meshcopia',activations:[]}).activations,[]);
  for(const value of [{schemaVersion:1,repository:'Xenoah/meshcopia',activations:[],offline:true},{schemaVersion:1,repository:'Xenoah/meshcopia',activations:[{},{}]}])assert.throws(()=>validateMinimalActivation(value));
});
test('projection pins source bytes; final binding preserves original compatibility downloads',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'minimal-projection-'));
  try {
    await mkdir(path.join(root,'source'));await writeFile(path.join(root,'source/mesh.glb'),'fixture');
    const notice='Fixture author\nCC BY 4.0 https://creativecommons.org/licenses/by/4.0/\n';
    const file={name:'mesh.glb',bytes:7,sha256:sha256('fixture')};
    const binding={schemaVersion:1,id:'fixture',assetVersion:'1.0.0',packageVersion:'1.0.0',contentPolicy:MINIMAL_CONTENT_POLICY,noticeFile:'LICENSE.txt',notice:{filename:'LICENSE.txt',text:notice,bytes:Buffer.byteLength(notice),sha256:sha256(notice)},url:'https://github.com/Xenoah/meshcopia/releases/download/fixture-v1.0.0/fixture-1.0.0-minimal-1.0.0.zip',bytes:500,sha256:sha256('new archive'),sourceFiles:[file],verification:{state:'published-verified',releaseTag:'fixture-v1.0.0',archiveSha256:sha256('new archive')}};
    const source={id:'fixture',version:'1.0.0',type:'model',status:'public',sources:['mesh.glb'],dir:root};
    const verified=await validateMinimalProjection([binding],[source]);
    const old={full:{url:'https://xenoah.github.io/meshcopia/old.zip',bytes:700,sha256:sha256('old archive')}};
    const catalog={...source,files:[file],downloads:old};const next=bindMinimalDownload(catalog,verified);
    assert.deepEqual(next.downloads.full,old.full);assert.equal(catalog.downloads.minimal,undefined);assert.equal(next.downloads.minimal,binding);
    assert.equal(bindMinimalDownload(catalog,new Map()),catalog);
    await assert.rejects(validateMinimalProjection([binding,binding],[source]),/Duplicate/);
    await assert.rejects(validateMinimalProjection([binding],[{...source,status:'draft'}]),/current public/);
    await writeFile(path.join(root,'source/mesh.glb'),'changed');await assert.rejects(validateMinimalProjection([binding],[source]),/source-inventory/);
  } finally {await rm(root,{recursive:true,force:true})}
});
test('generation verifies before any cleanup; dist retains old checks and independently verifies minimal bytes',async()=>{
  const generate=await readFile(new URL('../scripts/generate.mjs',import.meta.url),'utf8');
  assert.ok(generate.indexOf('await prepareMinimalDownloads(assets)')<generate.indexOf("await rm('public/assets'"));assert.match(generate,/bindMinimalDownload\(\{\.\.\.metadata/);assert.ok(generate.indexOf('await assertCompleteModelDeliveries(')<generate.indexOf("await rm('public/assets'"));
  const dist=await readFile(new URL('../scripts/check-dist.mjs',import.meta.url),'utf8');
  for(const retained of ["entries.has('LICENSE.txt')","entries.has('ATTRIBUTION.txt')","entries.get('ATTRIBUTION.txt').toString(),a.attribution+'\\n'","await verifyArchiveLock("])assert.ok(dist.includes(retained),retained);
  assert.match(dist,/prepareMinimalDownloads\(await readCatalog\(\)\)/);assert.match(dist,/Minimal binding differs from current verified public Release/);assert.match(dist,/Verified minimal cohort omitted/);
});
test('Python public activation validator passes fixture and corruption tests',()=>{
  execFileSync('python3',[fileURLToPath(new URL('./test_minimal_activation.py',import.meta.url))],{stdio:'pipe',maxBuffer:4*1024*1024});
});
