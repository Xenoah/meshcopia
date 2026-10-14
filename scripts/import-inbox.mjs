import { readdir, rename, access, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { readAsset } from './lib/catalog.mjs';
const apply = process.argv.includes('--apply');
const requested = process.argv.slice(2).find(a=>!a.startsWith('-'));
if (requested && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(requested)) throw new Error('Invalid asset id');
const all = await readdir('_inbox',{withFileTypes:true});
const pending = all.filter(a=>a.isDirectory() && !a.isSymbolicLink() && (!requested || a.name===requested));
if (requested && !pending.length) throw new Error(`Inbox asset not found: ${requested}`);
for (const entry of pending) {
  await readAsset(path.resolve('_inbox',entry.name));
  try {await access(`content/assets/${entry.name}`); throw new Error(`Asset already exists: ${entry.name}. Update its version and files in content/assets explicitly.`);} catch(e) {if(e.code!=='ENOENT') throw e;}
}
await mkdir('content/assets',{recursive:true});
for (const entry of pending) {
  if (apply) await rename(`_inbox/${entry.name}`,`content/assets/${entry.name}`);
  console.log(`${apply?'Imported':'Validated (dry run)'}: ${entry.name}`);
}
console.log(`${pending.length} asset(s).${apply?'':' Pass --apply to import.'}`);
