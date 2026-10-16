import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
test('FBX notice wraps long URLs without removing text or hiding overflow',async()=>{
 const source=await readFile(new URL('../src/pages/assets/[id].astro',import.meta.url),'utf8');
 assert.match(source,/<pre>\{fbx\.notice\.text\}<\/pre>/);
 const rule=source.match(/\.fbx-download pre\s*\{([^}]+)\}/)?.[1];assert.ok(rule);
 assert.match(rule,/white-space:\s*pre-wrap/);assert.match(rule,/overflow-wrap:\s*anywhere/);
 assert.doesNotMatch(rule,/overflow(?:-x)?:\s*(?:hidden|clip)|text-overflow|line-clamp/);
});
test('expanded real notice is measured at390 and320 with diagnostics before strict assertion',async()=>{
 const source=await readFile(new URL('../scripts/test-fbx-minimal-downloads-browser.mjs',import.meta.url),'utf8');
 assert.match(source,/for\(const width of \[390,320\]\)/);
 const assertion=source.indexOf('assert.ok(dimensions.documentWidth<=dimensions.viewportWidth+1');assert.ok(assertion>0);
 assert.ok(source.indexOf('mobile-fbx-layout-${width}.json')<assertion);assert.ok(source.indexOf("width===390?'test-results/mobile-fbx-downloads.png'")<assertion);
 assert.match(source,/activationSha256/);assert.match(source,/Notice text changed or truncated/);
});
