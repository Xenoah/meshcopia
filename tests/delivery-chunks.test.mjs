import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {webcrypto} from 'node:crypto';
import {prepareDeliveryPayloads} from '../scripts/lib/delivery-chunks.mjs';
import {model,hash} from './delivery-fixtures.mjs';
import {planBundle,buildBundle} from '../src/lib/batch-download.mjs';
test('bounded content chunks reproduce exact FBX and deduplicate across models',async()=>{
 const source=await mkdtemp(path.join(tmpdir(),'meshcopia-chunks-'));let prepared;
 try {
  const data=Buffer.alloc(1200000,42),digest=hash(data);
  await writeFile(path.join(source,digest+'.fbx'),data);
  prepared=await prepareDeliveryPayloads(['chair','table'].map(id=>({id,direct:{bytes:data.length,sha256:digest}})),{source});
  assert.equal(prepared.files.get('chair').sha256,prepared.files.get('table').sha256);
  assert.ok((await readdir(prepared.directory)).length<5);
  const a=model('chair',data);a.downloads.delivery.files[0].fetch=prepared.files.get('chair');
  const fetchImpl=async url=>new Response(await readFile(path.join(prepared.directory,new URL(url).pathname.split('/').pop())));
  assert.ok((await buildBundle(planBundle([a]),{fetchImpl,cryptoImpl:webcrypto})).size>data.length);
  const manifest=JSON.parse(await readFile(path.join(prepared.directory,prepared.files.get('chair').sha256+'.json')));
  await writeFile(path.join(prepared.directory,manifest.chunks[0].packedSha256+'.gz'),'corrupt');
  await assert.rejects(buildBundle(planBundle([a]),{fetchImpl,cryptoImpl:webcrypto}));
  await writeFile(path.join(source,digest+'.fbx'),'changed');
  await assert.rejects(prepareDeliveryPayloads([{id:'chair',direct:{bytes:data.length,sha256:digest}}],{source}));
 } finally {await rm(source,{recursive:true,force:true});if(prepared)await rm(prepared.directory,{recursive:true,force:true});}
});
