import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { assertArchiveRuntime, archiveRuntime, compressionOptions } from '../scripts/lib/archive-runtime.mjs';
import { archiveRecords, archivePath, assertAppendOnly, validateArchiveLock, verifyArchiveLock } from '../scripts/lib/archive-lock.mjs';
import { writeStoreZip } from '../scripts/lib/zip-store.mjs';

const digest = b => createHash('sha256').update(b).digest('hex');
const clone = o => structuredClone(o);

test('Archive runtime is exact, with no floating Node/zlib/platform fallback', async () => {
  assertArchiveRuntime();
  assert.equal((await readFile(new URL('../.node-version',import.meta.url),'utf8')).trim(), archiveRuntime.node);
  assert.deepEqual(compressionOptions, {level:6,strategy:0,windowBits:15,memLevel:8});
  for (const key of ['node','zlib','platform','arch']) {
    assert.throws(() => assertArchiveRuntime({...archiveRuntime,[key]:'wrong'}), /Archive runtime .* mismatch/);
  }
  const workflow = await readFile(new URL('../.github/workflows/publish.yml',import.meta.url),'utf8');
  assert.ok(workflow.includes("node-version-file: '.node-version'"));
  assert.ok(workflow.includes('node scripts/check-archive-runtime.mjs'));
  assert.ok(workflow.includes('node scripts/check-archive-lock.mjs --check-history'));
  assert.ok(!workflow.includes('--append-new'), 'CI must never bless new hashes automatically');
  assert.ok(workflow.includes('node scripts/test-browser.mjs'), 'Browser publication gate is retained');
});

test('Archive lock preserves legacy STORE and canonical DEFLATE, rejects drift and unsealed additions', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(),'meshcopia-archive-lock-'));
  try {
    const catalog = [];
    for (const [id, compress] of [['city-bollard',false],['new-fixture',true]]) {
      const asset={id,version:'1.0.0',downloads:{}};
      await mkdir(path.join(root,'assets',id),{recursive:true});
      const relative=archivePath({...asset,kind:'full'});
      await writeStoreZip(path.join(root,relative),[{name:'source/model.stl',data:'triangle '.repeat(500)}],{compress});
      const data=await readFile(path.join(root,relative));
      asset.downloads.full={url:'https://xenoah.github.io/meshcopia/'+relative,bytes:data.length,sha256:digest(data)};
      catalog.push(asset);
    }
    const records=archiveRecords(catalog);
    const lock={schemaVersion:1,archives:records};
    assert.deepEqual(await verifyArchiveLock({root,catalog,lock}),[]);
    const legacy={schemaVersion:1,archives:records.filter(a=>a.id==='city-bollard')};
    assert.equal(legacy.archives[0].profile,'store-v1');
    assert.equal(records.find(a=>a.id==='new-fixture').profile,archiveRuntime.profile);
    await assert.rejects(verifyArchiveLock({root,catalog,lock:legacy}),/Unsealed archive/);
    assert.equal((await verifyArchiveLock({root,catalog,lock:legacy,requireComplete:false})).length,1);
    assertAppendOnly(legacy,lock);
    for (const key of ['sha256','bytes','profile','url','version']) {
      const bad=clone(lock);bad.archives[0][key]=key==='bytes'?1:key==='sha256'?'0'.repeat(64):'changed';
      assert.throws(()=>assertAppendOnly(lock,bad));
    }
    assert.throws(()=>assertAppendOnly(lock,legacy),/changed or removed/);
    assert.throws(()=>validateArchiveLock({...lock,archives:[...records,records[0]]}),/Duplicate/);
    const badUrl=clone(lock);badUrl.archives[0].url='https://attacker.invalid/'+archivePath(records[0]);
    assert.throws(()=>validateArchiveLock(badUrl),/canonical/);
    const target=path.join(root,archivePath(records[0]));
    const bytes=await readFile(target); bytes[40]^=1; await writeFile(target,bytes);
    await assert.rejects(verifyArchiveLock({root,catalog,lock}),/hash drift/);
    // A malicious or accidental catalog hash refresh cannot bless changed bytes.
    const changed=clone(catalog);changed.find(a=>a.id===records[0].id).downloads.full.sha256=digest(bytes);
    await assert.rejects(verifyArchiveLock({root,catalog:changed,lock}),/hash drift/);
    await rm(target);
    await assert.rejects(verifyArchiveLock({root,catalog,lock}),/ENOENT/);
  } finally { await rm(root,{recursive:true,force:true}); }
});

test('Frozen 119 compatibility packages retain their 202 exact archive identities', async () => {
  const frozen=new Set(JSON.parse(await readFile(new URL('../scripts/lib/legacy-store-packages.json',import.meta.url),'utf8')));
  const lock=JSON.parse(await readFile(new URL('../docs/archive-lock.json',import.meta.url),'utf8'));
  const legacy=lock.archives.filter(a=>frozen.has(`${a.id}@${a.version}`));
  assert.equal(legacy.length,202);
  assert.ok(legacy.every(a=>a.profile==='store-v1'));
  const identity=legacy.map(a=>[a.id,a.version,a.kind,a.url,a.bytes,a.sha256].join('\t')).sort().join('\n');
  assert.equal(digest(identity),'8e2ad8cfc104ac10176d621756e7d55533aee623493210338c11c56008b020a4');
});

test('Historical ledger cannot be reset by deletion and recreation in a multi-commit push', async () => {
  const root=await mkdtemp(path.join(os.tmpdir(),'meshcopia-ledger-git-'));
  const script=fileURLToPath(new URL('../scripts/check-archive-lock.mjs',import.meta.url));
  const git=(...args)=>execFileSync('git',['-c','user.name=Fixture','-c','user.email=fixture@example.invalid',...args],{cwd:root,stdio:'pipe'});
  try {
    git('init'); await mkdir(path.join(root,'docs'));
    const a={id:'example',version:'1.0.0',kind:'full',url:'https://xenoah.github.io/meshcopia/assets/example/example-1.0.0.zip',bytes:1,sha256:'a'.repeat(64),profile:'store-v1'};
    await writeFile(path.join(root,'docs/archive-lock.json'),JSON.stringify({schemaVersion:1,archives:[a]}));
    git('add','.');git('commit','-m','Initial fixture lock');
    git('rm','docs/archive-lock.json');git('commit','-m','Delete fixture ledger');
    await mkdir(path.join(root,'docs'),{recursive:true});
    await writeFile(path.join(root,'docs/archive-lock.json'),JSON.stringify({schemaVersion:1,archives:[]}));
    const result=spawnSync(process.execPath,[script,'--check-history'],{cwd:root,encoding:'utf8'});
    assert.notEqual(result.status,0);assert.match(result.stderr,/Immutable archive lock changed or removed/);
    await writeFile(path.join(root,'docs/archive-lock.json'),JSON.stringify({schemaVersion:1,archives:[a]}));
    assert.equal(spawnSync(process.execPath,[script,'--check-history'],{cwd:root,encoding:'utf8'}).status,0);
  } finally {await rm(root,{recursive:true,force:true});}
});

test('Archive history includes a merged side branch even when the merge keeps main ledger bytes', async () => {
  const root=await mkdtemp(path.join(os.tmpdir(),'meshcopia-ledger-merge-'));
  const script=fileURLToPath(new URL('../scripts/check-archive-lock.mjs',import.meta.url));
  const git=(...args)=>execFileSync('git',['-c','user.name=Fixture','-c','user.email=fixture@example.invalid',...args],{cwd:root,stdio:'pipe'});
  const file=path.join(root,'docs/archive-lock.json');
  const entry=id=>({id,version:'1.0.0',kind:'full',url:`https://xenoah.github.io/meshcopia/assets/${id}/${id}-1.0.0.zip`,bytes:1,sha256:'a'.repeat(64),profile:'store-v1'});
  const a=entry('first'),b=entry('second');
  try {
    git('init','-b','main');await mkdir(path.join(root,'docs'));
    await writeFile(file,JSON.stringify({schemaVersion:1,archives:[a]}));
    git('add','.');git('commit','-m','Initial lock');
    git('checkout','-b','side');
    await writeFile(file,JSON.stringify({schemaVersion:1,archives:[a,b]}));
    git('add','.');git('commit','-m','Append side-branch lock');
    git('checkout','main');await writeFile(path.join(root,'README'),'fixture');
    git('add','.');git('commit','-m','Unrelated main change');
    git('merge','--no-ff','-s','ours','side','-m','Merge retaining main tree');
    const result=spawnSync(process.execPath,[script,'--check-history'],{cwd:root,encoding:'utf8'});
    assert.notEqual(result.status,0);assert.match(result.stderr,/Immutable archive lock changed or removed/);
    await writeFile(file,JSON.stringify({schemaVersion:1,archives:[a,b]}));
    assert.equal(spawnSync(process.execPath,[script,'--check-history'],{cwd:root,encoding:'utf8'}).status,0);
  } finally {await rm(root,{recursive:true,force:true});}
});
