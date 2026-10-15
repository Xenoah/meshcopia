import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,lstat,readdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {minimalDownloadReadiness} from '../../src/lib/downloads.mjs';

export const sha256=data=>createHash('sha256').update(data).digest('hex');
export const SITE='https://xenoah.github.io/meshcopia/';
export const PAGES_BUDGET=950000000;
export const RELEASE={releaseId:414332464,releaseTag:'minimal-v1.0.0',verificationCommit:'32f60a0adb144155574136a14476c30010e0d84b',inventorySha256:'6cd163e6683650a77e52649d8740feb19d614204473269a635789756fd39e463'};
const inventory=files=>files.map(({name,bytes,sha256})=>({name,bytes,sha256})).sort((a,b)=>a.name.localeCompare(b.name,'en'));

export function assertNotice(notice){
 assert.equal(notice.filename,'LICENSE.txt');const bytes=Buffer.from(notice.text,'utf8');
 assert.equal(bytes.length,notice.bytes);assert.equal(sha256(bytes),notice.sha256);return bytes;
}
export async function assertActivatedCatalog(catalog,sources){
 assert.equal(catalog.length,173);assert.equal(new Set(catalog.map(a=>a.id)).size,173);
 assert.equal(catalog.filter(a=>a.type==='model').length,137);assert.equal(catalog.filter(a=>a.type==='texture').length,36);
 const publicSources=sources.filter(a=>a.status==='public');assert.equal(publicSources.length,173);
 for(const a of catalog){
  const original=publicSources.find(s=>s.id===a.id);assert.ok(original,a.id);assert.equal(a.version,original.version);assert.equal(a.status,'public');
  const files=await Promise.all(original.sources.map(async name=>{const data=await readFile(path.join(original.dir,'source',name));return {name,bytes:data.length,sha256:sha256(data)};}));
  assert.deepEqual(inventory(a.files),inventory(files),`${a.id}: original files changed`);
  for(const f of a.files)assert.equal(f.url,`${SITE}assets/${a.id}/source/${f.name.split('/').map(encodeURIComponent).join('/')}`);
  assert.ok(minimalDownloadReadiness(a).ready,`${a.id}: minimal package unavailable`);
  assert.equal(a.downloads.minimal.verification.releaseTag,RELEASE.releaseTag);assertNotice(a.downloads.minimal.notice);
 }
 return catalog;
}
export function expectedDetail(a){return {id:a.id,zip:a.downloads.minimal.url,files:a.files.map(f=>f.url).sort(),direct:(a.type==='model'?a.files.filter(f=>['GLB','STL','STEP','STP'].includes(f.format)):[]).map(f=>f.url).sort()};}
export function expectedZipEntries(assets,{individual=false}={}){
 assert.ok(assets.length>0);if(individual)assert.equal(assets.length,1);
 const entries=assets.flatMap(a=>a.files.map(f=>({name:individual?f.name:`${a.id}/${f.name}`,bytes:f.bytes,sha256:f.sha256})));
 for(const a of assets)assertNotice(a.downloads.minimal.notice);
 const text=individual?assets[0].downloads.minimal.notice.text:assets.map(a=>`=== ${a.id} ===\n${a.downloads.minimal.notice.text}`).join('\n\n');
 const data=Buffer.from(text,'utf8');entries.push({name:'LICENSE.txt',bytes:data.length,sha256:sha256(data)});return entries;
}
export async function verifyBrowserZip(filename,assets,{individual=false}={}){
 const data=await readFile(filename);const archive={bytes:data.length,sha256:sha256(data)};
 if(individual){assert.equal(archive.bytes,assets[0].downloads.minimal.bytes);assert.equal(archive.sha256,assets[0].downloads.minimal.sha256);}
 const entries=expectedZipEntries(assets,{individual});
 const python="import json,sys,zipfile,hashlib,stat\nexpected={r['name']:r for r in json.load(sys.stdin)}\nwith zipfile.ZipFile(sys.argv[1]) as z:\n names=z.namelist()\n assert len(names)==len(set(names)) and set(names)==set(expected), names\n assert z.testzip() is None\n for info in z.infolist():\n  assert not info.is_dir() and not stat.S_ISLNK(info.external_attr>>16) and not(info.flag_bits&1)\n  data=z.read(info.filename); row=expected[info.filename]\n  assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],info.filename\n assert names.count('LICENSE.txt')==1\n";
 const result=spawnSync('python3',['-c',python,filename],{input:JSON.stringify(entries),encoding:'utf8'});
 assert.equal(result.status,0,`Browser ZIP member verification failed: ${result.stderr}`);return {...archive,entries};
}
export async function measureDist(root){
 let bytes=0,files=0;
 async function visit(file){const info=await lstat(file);assert.ok(!info.isSymbolicLink(),`Symlink in dist: ${file}`);if(info.isDirectory()){for(const name of await readdir(file))await visit(path.join(file,name));}else{assert.ok(info.isFile(),`Nonregular dist entry: ${file}`);bytes+=info.size;files++;}}
 await visit(root);assert.ok(bytes<=PAGES_BUDGET,`Pages budget exceeded: ${bytes} > ${PAGES_BUDGET}`);return {bytes,files,budgetBytes:PAGES_BUDGET};
}
