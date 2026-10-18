import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const digest=b=>createHash('sha256').update(b).digest('hex');
const canonical=xs=>JSON.stringify(xs.map(({name,bytes,sha256})=>({name,bytes,sha256})).sort((a,b)=>a.name.localeCompare(b.name,'en')));
// verifiedFbx must be the result of the independent FBX publication/QA validator,
// never a direct parse of an unverified JSON file or a caller's readiness flag.
export async function assertCompleteModelDeliveries(assets,{baseline,verifiedFbx=[],readSource=(a,n)=>readFile(path.join(a.dir,'source',n)),readMetadata=a=>readFile(path.join(a.dir,'asset.json'))}={}){
 assert.equal(baseline?.schemaVersion,1,'Missing production baseline');
 assert.equal(digest(JSON.stringify(baseline)),'f4c28ab677b02badf4a7e12f971683539b3fa180b7d2f34f7156adcdb0626aaf','Historical production exception changed; never expand to bypass FBX delivery');
 const old=new Map(baseline.models.map(x=>[x.id,x]));
 assert.equal(old.size,baseline.models.length,'Duplicate production baseline');
 for(const a of assets.filter(x=>x.type==='model'&&x.status==='public')){
  const sources=[];
  for(const name of a.sources){const b=await readSource(a,name);sources.push({name,bytes:b.length,sha256:digest(b)});}
  const historical=old.get(a.id);
  if(historical&&historical.assetVersion===a.version&&historical.metadataSha256===digest(await readMetadata(a))&&canonical(historical.sources)===canonical(sources))continue;
  const matches=verifiedFbx.filter(x=>x.id===a.id&&x.assetVersion===a.version&&canonical(x.sources)===canonical(sources));
  assert(matches.length>0,`Model ${a.id}@${a.version} requires source/version-bound verified FBX before publication; draft source preparation is allowed.`);
 }
}
