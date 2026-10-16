import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {verifyCitySourcePaths} from '../scripts/lib/city-source-policy.mjs';
const recipe='scripts/city_expansion/public_fixtures.py',helper='scripts/city_expansion/common.py';
const files=new Map([[recipe,Buffer.from('recipe')],[helper,Buffer.from('helper')],['scripts/city/civic.py',Buffer.from('legacy')]]);
const hash=p=>createHash('sha256').update(files.get(p)).digest('hex');
const make=()=>({id:'city-test',usages:[{sourcePaths:[recipe,helper]}],provenance:{generatorUrl:'https://github.com/Xenoah/meshcopia/blob/main/'+recipe,sourceRecipeSha256:hash(recipe),sourceHelpersSha256:hash(helper)}});
const approved={id:'city-test',recipe,sourceRecipeSha256:hash(recipe),sourceHelpersSha256:hash(helper)};
const read=async p=>{assert.ok(files.has(p),'Missing source '+p);return files.get(p)};
test('city source policy preserves old flat paths and accepts exact expansion recipe/helper bytes',async()=>{await verifyCitySourcePaths({id:'old',usages:[{sourcePaths:['scripts/city/civic.py']}]},read);await verifyCitySourcePaths(make(),read,approved);const a=make();a.provenance.generatorUrl=a.provenance.generatorUrl.replace('/main/','/'+'a'.repeat(40)+'/');await verifyCitySourcePaths(a,read,approved)});
test('expansion provenance refuses missing or drifted recipe/helper digests',async()=>{for(const key of ['sourceRecipeSha256','sourceHelpersSha256']){for(const value of [undefined,'A'.repeat(64),'0'.repeat(64)]){const a=make();a.provenance[key]=value;await assert.rejects(verifyCitySourcePaths(a,read,approved))}}});
test('city source allowance does not accept traversal, other trees, missing recipes or arbitrary origins',async()=>{
 for(const path of ['scripts/city_expansion/../common.py','scripts/city_expansion/nested/a.py','scripts/other/a.py','scripts/city_expansion/A.py','scripts/city_expansion/a.js']){const a=make();a.usages[0].sourcePaths=[path,helper];await assert.rejects(verifyCitySourcePaths(a,read,approved))}
 for(const paths of [[],[helper],[recipe],[recipe,helper,'scripts/city/civic.py']]){const a=make();a.usages[0].sourcePaths=paths;await assert.rejects(verifyCitySourcePaths(a,read,approved))}
 for(const url of ['https://example.com/'+recipe,'https://github.com/Xenoah/meshcopia/blob/main/'+helper,'https://github.com/Xenoah/meshcopia/blob/other/'+recipe]){const a=make();a.provenance.generatorUrl=url;await assert.rejects(verifyCitySourcePaths(a,read,approved))}
});

test('expansion recipes need explicit per-ID reviewed source approval',async()=>{await assert.rejects(verifyCitySourcePaths(make(),read));await assert.rejects(verifyCitySourcePaths(make(),read,{...approved,recipe:helper}));await assert.rejects(verifyCitySourcePaths(make(),read,{...approved,sourceRecipeSha256:'0'.repeat(64)}))});


test('frozen batch namespaces bind same-directory immutable helper and recipe',async()=>{
 const prefix='scripts/city_expansion/frozen/batch-030/';
 const r=prefix+'scripts/city_expansion/document_service_equipment.py',h=prefix+helper;
 const own=new Map([[r,Buffer.from('recipe30')],[h,Buffer.from('helper')]]);
 const a={id:'city-batch30',usages:[{sourcePaths:[r,h]}],provenance:{generatorUrl:'https://github.com/Xenoah/meshcopia/blob/main/'+r,sourceRecipeSha256:createHash('sha256').update(own.get(r)).digest('hex'),sourceHelpersSha256:createHash('sha256').update(own.get(h)).digest('hex')}};
 const ok={id:a.id,recipe:r,sourceRecipeSha256:a.provenance.sourceRecipeSha256,sourceHelpersSha256:a.provenance.sourceHelpersSha256};
 const get=async p=>{assert.ok(own.has(p));return own.get(p)};
 await verifyCitySourcePaths(a,get,ok);
 for(const bad of [h.replace('batch-030','batch-056'),helper,h.replace('batch-030','batch-030/..'),h.replace('batch-030','batch-30'),h.replace('batch-030','batch-030/extra')]){
  const b=structuredClone(a);b.usages[0].sourcePaths=[r,bad];await assert.rejects(verifyCitySourcePaths(b,async p=>own.get(p)||Buffer.from('helper'),ok));
 }
 const other=structuredClone(a);other.provenance.sourceRecipeSha256=createHash('sha256').update('recipe56').digest('hex');await assert.rejects(verifyCitySourcePaths(other,get,ok));
 await assert.rejects(verifyCitySourcePaths(a,get,{...ok,recipe:r.replace('batch-030','batch-056')}));
});
