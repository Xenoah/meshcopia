import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {filesIn,sha256} from './catalog.mjs';
import {measureDist} from './download-browser-contract.mjs';
import {primaryDownload} from '../../src/lib/downloads.mjs';

export function assertCurrentDownloads(catalog){
 assert.equal(catalog.schemaVersion,'3.0.0','Current catalog must declare the breaking migration');
 assert.equal(catalog.count,catalog.assets.length);
 for(const asset of catalog.assets){
  assert.deepEqual(Object.keys(asset.downloads),[asset.type==='model'?'delivery':'minimal'],`${asset.id}: retired download fields`);
  assert.ok(primaryDownload(asset),`${asset.id}: missing verified current download`);
 }
}

export function assertNoRetiredLinks(text,archives,label){
 for(const archive of archives){
  const pathname=new URL(archive.url).pathname;
  assert.ok(!text.includes(archive.url)&&!text.includes(pathname),`${label}: retired URL referenced: ${pathname}`);
 }
}

export async function verifySiteMigration({root='dist'}={}){
 const catalog=JSON.parse(await readFile(path.join(root,'api/catalog.json'),'utf8'));
 assertCurrentDownloads(catalog);
 const rawLock=await readFile('docs/archive-lock.json');
 const baseline=JSON.parse(await readFile('docs/fbx-minimal-activation/original-api-baseline.json','utf8'));
 assert.equal(sha256(rawLock),baseline.archiveLockSha256,'Historical archive ledger must remain recoverable and unchanged');
 const lock=JSON.parse(rawLock);
 const output=await filesIn(root);
 const retired=lock.archives.map(a=>new URL(a.url).pathname.replace(/^\/meshcopia\//,''));
 for(const name of retired)assert.ok(!output.includes(name),`Retired archive was generated: ${name}`);
 for(const name of output){
  assert.ok(!/\.(zip|fbx)$/i.test(name),`Unexpected duplicate archive/raw FBX in Pages: ${name}`);
  if(/\.(html|json|ndjson|js|txt|xml)$/i.test(name))assertNoRetiredLinks(await readFile(path.join(root,name),'utf8'),lock.archives,name);
 }
 const dist=await measureDist(root);
 return {schemaVersion:1,catalogSchemaVersion:catalog.schemaVersion,
  publicAssets:catalog.assets.length,models:catalog.assets.filter(a=>a.type==='model').length,
  textures:catalog.assets.filter(a=>a.type==='texture').length,
  retiredArchiveCount:lock.archives.length,retiredArchiveBytes:lock.archives.reduce((n,a)=>n+a.bytes,0),
  historicalArchiveLedgerUnchanged:true,retiredFilesPresent:0,retiredLinksPresent:0,
  checkedOutputFiles:output.length,dist,
  scope:'Built candidate only; retired Pages URLs may return 404 after deployment; source files, Git history and existing Releases retained; no deployment'};
}
