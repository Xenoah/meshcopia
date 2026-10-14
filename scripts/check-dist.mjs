import {readFile,stat} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {filesIn,sha256} from './lib/catalog.mjs';
const base=process.env.PUBLIC_BASE_PATH??'/meshcopia';
const catalog=JSON.parse(await readFile('dist/api/catalog.json','utf8'));
let count=0;
async function resolveFile(url){const u=new URL(url,'https://xenoah.github.io'+base+'/');assert.ok(u.pathname.startsWith(base+'/'),`Wrong base path: ${url}`);let file='dist/'+decodeURIComponent(u.pathname.slice(base.length+1));if(u.pathname.endsWith('/'))file+='index.html';await stat(file);return file;}
for(const a of catalog.assets){
 assert.equal(a.status,'public');await resolveFile(a.pageUrl);await resolveFile(a.thumbnail);await resolveFile(a.manifestUrl);
 for(const f of [...a.files,...Object.values(a.downloads)]){const data=await readFile(await resolveFile(f.url));assert.equal(data.length,f.bytes);assert.equal(sha256(data),f.sha256);count++;}
 for(const [kind,f] of Object.entries(a.downloads)){if(kind==='direct')continue;const b=await readFile(await resolveFile(f.url));const names=[];let offset=0;while(b.readUInt32LE(offset)===0x04034b50){const size=b.readUInt32LE(offset+18),len=b.readUInt16LE(offset+26),extra=b.readUInt16LE(offset+28);const name=b.subarray(offset+30,offset+30+len).toString();names.push(name);offset+=30+len+extra+size;}assert.ok(names.includes('LICENSE.txt'));assert.ok(names.includes('ATTRIBUTION.txt'));for(const source of a.files)assert.ok(names.includes('source/'+source.name));if(kind==='models'){assert.ok(!names.includes('README.md'));assert.ok(!names.some(n=>n.startsWith('preview.')));}}
}
let links=0;
for(const file of (await filesIn('dist')).filter(f=>f.endsWith('.html'))){const html=await readFile(path.join('dist',file),'utf8');for(const match of html.matchAll(/(?:href|src)="([^"]+)"/g)){const value=match[1].replace(/&amp;/g,'&');if(value.startsWith(base+'/')){await resolveFile(value);links++;}}}
assert.ok((await readFile('dist/sitemap.xml','utf8')).includes(base+'/assets/studio-chair/'));
console.log(`Verified ${catalog.assets.length} public assets, ${count} file/ZIP hashes, ZIP contents and ${links} internal links.`);
