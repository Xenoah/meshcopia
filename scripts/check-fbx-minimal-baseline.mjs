// Read-only post-build regression. Baseline is preserved local stage6 output,
// not a fresh release download. Only additive minimal/delivery fields are
// projected away; every remaining original byte must match.
import assert from 'node:assert/strict';
import {readFile,readdir,stat,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const baseline=JSON.parse(await readFile(new URL('../docs/fbx-minimal-activation/original-api-baseline.json',import.meta.url),'utf8'));
const hash=b=>createHash('sha256').update(b).digest('hex');
const withoutMinimal=a=>{const copy=structuredClone(a);if(copy.downloads){delete copy.downloads.minimal;delete copy.downloads.delivery;}return copy;};
assert.equal(hash(await readFile('docs/archive-lock.json')),baseline.archiveLockSha256);
assert.equal(JSON.parse(await readFile('docs/archive-lock.json','utf8')).archives.length,310);
for(const row of baseline.files){
 const raw=await readFile(path.join('dist',row.path),'utf8');let projected;
 if(row.path==='api/catalog.ndjson')projected=raw.trim().split('\n').map(x=>JSON.stringify(withoutMinimal(JSON.parse(x)))).join('\n')+'\n';
 else {const data=JSON.parse(raw);const original=row.path==='api/catalog.json'?{...data,assets:data.assets.map(withoutMinimal)}:withoutMinimal(data);projected=JSON.stringify(original,null,2)+'\n';}
 assert.equal(Buffer.byteLength(projected),row.bytes,`Original projection byte size: ${row.path}`);
 assert.equal(hash(projected),row.sha256,`Original projection identity: ${row.path}`);
}
async function files(root){const out=[];for(const e of await readdir(root,{withFileTypes:true})){const p=path.join(root,e.name);if(e.isDirectory())out.push(...await files(p));else{assert.ok(e.isFile(),'Unexpected symlink/nonregular output');out.push(p);}}return out;}
const api=(await files('dist/api')).map(x=>path.relative('dist',x));
assert.deepEqual(api.sort(),[...baseline.files.map(x=>x.path),'api/fbx-minimal-downloads.json'].sort());
const side=JSON.parse(await readFile('dist/api/fbx-minimal-downloads.json','utf8'));const catalog=JSON.parse(await readFile('dist/api/catalog.json','utf8'));
assert.deepEqual(side.coverage,{publicModels:137,fbxReadyModels:137});assert.equal(side.formats.length,137);
assert.deepEqual(side.formats.map(x=>x.id).sort(),catalog.assets.filter(x=>x.type==='model').map(x=>x.id).sort());
assert.ok(!Object.hasOwn(side,'provenance')&&!Object.hasOwn(side,'releases'));
let bytes=0;for(const p of await files('dist')){assert.notEqual(path.extname(p).toLowerCase(),'.fbx','Bulk FBX in Pages');bytes+=(await stat(p)).size;}

const report={scope:baseline.scope,originalApiProjectionsByteIdentical:175,onlyIgnoredFields:['downloads.minimal','downloads.delivery'],originalArchiveLedgerUnchanged:310,fbxReadyModels:137,distBytes:bytes};
await mkdir('test-results',{recursive:true});await writeFile('test-results/fbx-minimal-baseline.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
assert.ok(bytes<950_000_000,`Pages operational budget exceeded: ${bytes}`);
