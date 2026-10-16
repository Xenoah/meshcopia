// Output is ONLY true/false. A present marker or pending mutation input must
// validate completely before the workflow can publish an output.
import assert from 'node:assert/strict';
import {readFile,lstat,readdir} from 'node:fs/promises';
import {readCatalog} from './lib/catalog.mjs';
import {validateSourceStage} from './lib/source-stage.mjs';
let marker,present=true;
try{marker=JSON.parse(await readFile('.source-stage.json','utf8'))}catch(e){if(e.code!=='ENOENT')throw e;present=false}
if(!present)console.log('false');else{
 const frozen=JSON.parse(await readFile('docs/scaling-protected-ids.json','utf8'));
 validateSourceStage(marker,await readCatalog(),frozen.ids);
 for(const file of ['.bootstrap-starter','.import-commons-cafe','.import-commons-expansion','.import-yokocho','.generate-city-drafts.json']){
  const exists=await lstat(file).then(()=>true,e=>{if(e.code!=='ENOENT')throw e;return false});
  assert.ok(!exists,`Source-only stage cannot include pending generation/import marker: ${file}`);
 }
 const inbox=await readdir('_inbox',{withFileTypes:true}).catch(e=>{if(e.code!=='ENOENT')throw e;return []});
 assert.ok(!inbox.some(e=>e.isDirectory()||e.isSymbolicLink()),'Source-only stage cannot include pending inbox assets or symlinks');
 console.log('true');
}
