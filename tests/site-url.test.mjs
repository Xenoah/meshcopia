import test from 'node:test';
import assert from 'node:assert/strict';
import {toLocalSiteUrl} from '../src/lib/site-url.mjs';
test('Pages source URLs remain local without losing queries and fragments',()=>{
 assert.equal(toLocalSiteUrl('https://xenoah.github.io/meshcopia/assets/studio-chair/source/model.glb?x=1#mesh'),'/meshcopia/assets/studio-chair/source/model.glb?x=1#mesh');
 assert.equal(toLocalSiteUrl('/meshcopia/thumbnail.png'),'/meshcopia/thumbnail.png');
});
test('external thumbnails and model previews retain their exact immutable host',()=>{
 for(const name of ['preview.png','source/model.stl']){
  const url=`https://raw.githubusercontent.com/Xenoah/meshcopia/${'a'.repeat(40)}/content/assets/city-example/${name}`;
  assert.equal(toLocalSiteUrl(url),url);
 }
 assert.equal(toLocalSiteUrl('https://example.org/model.glb'),'https://example.org/model.glb');
});
test('asset URL presentation rejects executable and local file protocols',()=>{
 for(const url of ['javascript:alert(1)','data:text/html,hello','file:///tmp/test'])assert.throws(()=>toLocalSiteUrl(url),/Unsupported/);
});
