import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const legacy=/^scripts\/city\/[a-z0-9_]+\.py$/;
const expansion=/^scripts\/city_expansion\/(?:frozen\/batch-[0-9]{3}\/scripts\/city_expansion\/)?[a-z0-9_]+\.py$/;
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
// Only legacy, flat expansion, and exact batch-isolated original recipe trees.
// A new expansion recipe must bind its exact immutable helper and recipe bytes.
export async function verifyCitySourcePaths(asset,readSource,approved){
 const paths=[...new Set((asset.usages||[]).flatMap(u=>u.sourcePaths||[]))];
 assert.ok(paths.length>0,asset.id+': missing reproducibility source paths');
 for(const file of paths){
  assert.ok(legacy.test(file)||expansion.test(file),asset.id+': unexpected source path '+file);
  assert.ok((await readSource(file)).length>0,asset.id+': empty generator source '+file);
 }
 if(!paths.some(file=>expansion.test(file)))return;
 assert.ok(paths.every(file=>expansion.test(file)),asset.id+': mixed legacy/expansion source paths');
 const match=asset.provenance?.generatorUrl?.match(/^https:\/\/github\.com\/Xenoah\/meshcopia\/blob\/(?:main|[0-9a-f]{40})\/(scripts\/city_expansion\/(?:frozen\/batch-[0-9]{3}\/scripts\/city_expansion\/)?[a-z0-9_]+\.py)$/);
 assert.ok(match,asset.id+': noncanonical expansion generator URL');
 assert.ok(approved&&approved.id===asset.id,asset.id+': expansion source is not in the reviewed source roster');
 const recipe=match[1],helper=recipe.slice(0,recipe.lastIndexOf('/')+1)+'common.py';
 assert.equal(recipe,approved.recipe,asset.id+': unreviewed recipe path');
 assert.notEqual(recipe,helper,asset.id+': helper is not a model recipe');
 assert.deepEqual(paths.slice().sort(),[recipe,helper].sort(),asset.id+': expansion must name exactly its recipe and common helper');
 for(const [file,key] of [[recipe,'sourceRecipeSha256'],[helper,'sourceHelpersSha256']]){
  assert.equal(asset.provenance[key],approved[key],asset.id+': unreviewed '+key);
  assert.match(asset.provenance[key]||'',/^[0-9a-f]{64}$/,asset.id+': missing '+key);
  assert.equal(digest(await readSource(file)),asset.provenance[key],asset.id+': generator drift '+file);
 }
}
