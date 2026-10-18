import {completeTexture} from './delivery-fixtures.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {formatBytes,bundleSizeSummary} from '../src/lib/file-size.mjs';
import {planBundle,buildBundle,POLICY} from '../src/lib/batch-download.mjs';
const hash=s=>createHash('sha256').update(s).digest('hex');
function asset(id){const data='small model',text='CC BY 4.0\n';const f={name:'模型.glb',bytes:Buffer.byteLength(data),sha256:hash(data),url:`https://xenoah.github.io/meshcopia/assets/${id}/source/model.glb`};return completeTexture({id,status:'public',version:'1.0.0',files:[f],downloads:{minimal:{id,assetVersion:'1.0.0',contentPolicy:POLICY,noticeFile:'LICENSE.txt',bytes:1,sourceFiles:[f],notice:{filename:'LICENSE.txt',text,bytes:Buffer.byteLength(text),sha256:hash(text)}}}});}
test('dynamic decimal units never round a positive small selection to zero MB',()=>{for(const [n,s] of [[0,'0 B'],[1,'1 B'],[999,'999 B'],[1000,'1.0 KB'],[19024,'19.0 KB'],[999949,'999.9 KB'],[999950,'1.0 MB'],[1000000,'1.0 MB'],[1000000000,'1.0 GB']])assert.equal(formatBytes(n),s);});
test('missing, invalid or unsafe bytes are unknown, not zero',()=>{for(const n of [undefined,null,NaN,Infinity,-1,1.5,'1024',Number.MAX_SAFE_INTEGER+1])assert.equal(formatBytes(n),'—');assert.equal(formatBytes(null,'Size unknown'),'Size unknown');});
test('estimated STORE size includes UTF-8 names and matches final actual blob bytes',async()=>{const assets=[asset('one'),asset('two')];const summary=bundleSizeSummary(assets),plan=planBundle(assets);const blob=await buildBundle(plan,{cryptoImpl:webcrypto,fetchImpl:async()=>new Response('small model')});assert.equal(summary.inputBytes,plan.bytes);assert.equal(summary.zipBytes,blob.size);assert.ok(summary.zipBytes>summary.inputBytes);assert.notEqual(summary.zipBytes,2);});
test('empty, missing metadata and post-remove estimates are explicit',()=>{assert.deepEqual(bundleSizeSummary([]),{inputBytes:0,zipBytes:0});const a=asset('one'),b=asset('two');assert.ok(bundleSizeSummary([a,b]).zipBytes>bundleSizeSummary([a]).zipBytes);delete a.files[0].bytes;assert.deepEqual(bundleSizeSummary([a,b]),{inputBytes:null,zipBytes:null});assert.deepEqual(bundleSizeSummary([undefined]),{inputBytes:null,zipBytes:null});});
