import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {validateSourceStageProofs,assertSuccessfulSourceStageRun,assertSourceStageUnchanged} from '../scripts/lib/source-stage-proof.mjs';
const proof={commit:'a'.repeat(40),runId:123};const run={id:123,repository:{full_name:'Xenoah/meshcopia'},head_repository:{full_name:'Xenoah/meshcopia'},path:'.github/workflows/publish.yml',event:'push',head_branch:'main',head_sha:proof.commit,status:'completed',conclusion:'success'};
test('raw source proof binds the successful expected workflow to the exact immutable source SHA',()=>{assertSuccessfulSourceStageRun(proof,run);for(const [key,value] of Object.entries({id:124,path:'other.yml',event:'pull_request',head_branch:'other',head_sha:'b'.repeat(40),status:'in_progress',conclusion:'failure',repository:{full_name:'other/repo'},head_repository:{full_name:'other/repo'}}))assert.throws(()=>assertSuccessfulSourceStageRun(proof,{...run,[key]:value}),key)});
test('source proofs reject malformed and ambiguous identities',()=>{const doc={schemaVersion:1,repository:'Xenoah/meshcopia',proofs:[proof]};validateSourceStageProofs(doc);assert.throws(()=>validateSourceStageProofs({...doc,proofs:[proof,proof]}));for(const p of [{...proof,runId:0},{...proof,runId:'123'},{...proof,commit:'main'}])assert.throws(()=>validateSourceStageProofs({...doc,proofs:[p]}))});
test('source-only CI cannot create a different commit after verification',()=>{assertSourceStageUnchanged(true,false);assertSourceStageUnchanged(false,true);assert.throws(()=>assertSourceStageUnchanged(true,true))});
test('workflow checks authoritative source proof before build and prohibits source-stage import commits',async()=>{const s=await readFile('.github/workflows/publish.yml','utf8');assert.ok(s.indexOf('node scripts/check-source-stage-proof.mjs')<s.indexOf('run: npm run check'));assert.ok(s.includes('SOURCE_ONLY: ${{ steps.source-stage.outputs.source_only }}'));assert.ok(s.indexOf('node scripts/check-source-stage-unchanged.mjs')<s.indexOf("git commit -m 'feat(assets)"))});
import {readSourceStageRun,verifyCurrentSourceStages,emptySourceStageProofs} from '../scripts/lib/source-stage-proof.mjs';
const marker={schemaVersion:1,purpose:'draft-raw-source-prepublication',ids:['city-test']};
function options(){return {doc:{...emptySourceStageProofs(),proofs:[{...proof,status:'completed',conclusion:'success'}]},pins:[{id:'city-test',version:'1.0.0',commit:proof.commit}],packages:[{id:'city-test',version:'1.0.0',tag:'v1.10.0'}],tag:'v1.10.0',readAt:async(commit,file)=>{assert.equal(commit,proof.commit);if(file==='.source-stage.json')return marker;if(file==='docs/scaling-protected-ids.json')return {ids:[]};return {id:'city-test',type:'model',status:'draft'}},loadRun:async()=>run}}
test('default-off source proof needs no network and cannot affect old catalog/archive payloads',async()=>{const never=async()=>{throw Error('must not run')};assert.deepEqual(await verifyCurrentSourceStages({doc:emptySourceStageProofs(),pins:[],packages:[],tag:'v1.9.0',readAt:never,loadRun:never}),{pins:0,runs:0})});
test('promotion verifies remote success rather than claimed manifest success, and fails closed',async()=>{
 assert.deepEqual(await verifyCurrentSourceStages(options()),{pins:1,runs:1});
 for(const value of [{...run,conclusion:'failure'},{...run,head_sha:'b'.repeat(40)},{...run,status:'queued'}])await assert.rejects(verifyCurrentSourceStages({...options(),loadRun:async()=>value}));
 await assert.rejects(verifyCurrentSourceStages({...options(),loadRun:async()=>{throw Error('network unavailable')}}));
 await assert.rejects(verifyCurrentSourceStages({...options(),doc:emptySourceStageProofs()}));
});
test('successful Actions run alone cannot replace the committed source-stage marker and draft IDs',async()=>{
 const o=options();for(const changed of [{...marker,ids:['different']},{...marker,purpose:'other'}])await assert.rejects(verifyCurrentSourceStages({...o,readAt:async(c,f)=>f==='.source-stage.json'?changed:o.readAt(c,f)}));
 await assert.rejects(verifyCurrentSourceStages({...o,readAt:async(c,f)=>f.includes('asset.json')?{id:'city-test',type:'model',status:'public'}:o.readAt(c,f)}));
 await assert.rejects(verifyCurrentSourceStages({...o,readAt:async(c,f)=>f==='.source-stage.json'?Promise.reject(Error('marker absent')):o.readAt(c,f)}));
});
test('source-run transport uses exact public API route and fails closed on HTTP errors',async()=>{
 for(const status of [301,403,404,429,500])await assert.rejects(readSourceStageRun(proof,async()=>({status,json:async()=>run})));
 let called=false;assert.deepEqual(await readSourceStageRun(proof,async(url,init)=>{called=true;assert.equal(url,'https://api.github.com/repos/Xenoah/meshcopia/actions/runs/123');assert.equal(init.credentials,'omit');assert.equal(init.redirect,'error');assert.equal(init.headers.Authorization,undefined);return {status:200,json:async()=>run}}),run);assert.ok(called);
});
