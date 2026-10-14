import {readFile,stat} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {filesIn,sha256} from './lib/catalog.mjs';
import {readZipEntries} from './lib/zip-read.mjs';
import {verifyArchiveLock,archiveLockPath} from './lib/archive-lock.mjs';
const base=process.env.PUBLIC_BASE_PATH??'/meshcopia';
const catalog=JSON.parse(await readFile('dist/api/catalog.json','utf8'));
const ndjson=(await readFile('dist/api/catalog.ndjson','utf8')).trim().split('\n').map(line=>JSON.parse(line));
assert.deepEqual(ndjson,catalog.assets);
assert.equal(catalog.schemaVersion,'2.1.0');
let count=0;
async function resolveFile(url){const u=new URL(url,'https://xenoah.github.io'+base+'/');assert.ok(u.pathname.startsWith(base+'/'),`Wrong base path: ${url}`);let file='dist/'+decodeURIComponent(u.pathname.slice(base.length+1));if(u.pathname.endsWith('/'))file+='index.html';await stat(file);return file;}
for(const a of catalog.assets){
 assert.ok(Array.isArray(a.usages));
 const original=JSON.parse(await readFile(`content/assets/${a.id}/asset.json`,'utf8'));
 assert.deepEqual(a.usages,original.usages??[]);
 const manifest=JSON.parse(await readFile(await resolveFile(a.manifestUrl),'utf8'));assert.deepEqual(manifest.usages,a.usages);
 const html=await readFile(await resolveFile(a.pageUrl),'utf8');assert.ok(html.includes('id="usage-heading"'));
 assert.equal(a.status,'public');await resolveFile(a.pageUrl);await resolveFile(a.thumbnail);await resolveFile(a.manifestUrl);
 for(const f of [...a.files,...Object.values(a.downloads)]){const data=await readFile(await resolveFile(f.url));assert.equal(data.length,f.bytes);assert.equal(sha256(data),f.sha256);count++;}
 for(const [kind,f] of Object.entries(a.downloads)){
  if(kind==='direct')continue;
  const entries=readZipEntries(await readFile(await resolveFile(f.url)));
  assert.ok(entries.has('LICENSE.txt'));assert.ok(entries.has('ATTRIBUTION.txt'));
  assert.ok(entries.get('LICENSE.txt').toString().includes('CC BY 4.0'));
  assert.equal(entries.get('ATTRIBUTION.txt').toString(),a.attribution+'\n');
  for(const source of a.files){
   const data=entries.get('source/'+source.name);assert.ok(data,`Missing ZIP source: ${source.name}`);
   assert.equal(data.length,source.bytes);assert.equal(sha256(data),source.sha256);
  }
  if(kind==='models'){
   assert.equal(entries.size,a.files.length+2);
   assert.ok(!entries.has('README.md'));assert.ok(![...entries.keys()].some(n=>n.startsWith('preview.')));
  }else{
   const metadata=JSON.parse(entries.get('asset.json').toString());assert.deepEqual(metadata.usages,a.usages);
   assert.ok(entries.has('README.md'));assert.equal(entries.size,a.files.length+5);
   const thumbnail=await readFile(await resolveFile(a.thumbnail));
   assert.deepEqual(entries.get('preview'+path.extname(a.thumbnail)),thumbnail);
  }
 }
}
let links=0;
for(const file of (await filesIn('dist')).filter(f=>f.endsWith('.html'))){const html=await readFile(path.join('dist',file),'utf8');for(const match of html.matchAll(/(?:href|src)="([^"]+)"/g)){const value=match[1].replace(/&amp;/g,'&');if(value.startsWith(base+'/')){await resolveFile(value);links++;}}}
assert.ok((await readFile('dist/sitemap.xml','utf8')).includes(base+'/assets/studio-chair/'));
await verifyArchiveLock({catalog:JSON.parse(await readFile('src/data/catalog.json','utf8')),lock:JSON.parse(await readFile(archiveLockPath,'utf8'))});
console.log(`Verified ${catalog.assets.length} public assets, ${count} file/ZIP hashes, ZIP contents, immutable archive locks and ${links} internal links.`);
