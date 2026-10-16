import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,mkdtemp,mkdir,writeFile,rm,symlink} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
import {validateFbxMinimalActivation,validatePrepReceipt,regularRead,validateCurrentFbxSources} from '../scripts/lib/fbx-minimal-downloads.mjs';
import {fbxMinimalForAsset} from '../src/lib/fbx-minimal-downloads.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
const empty={schemaVersion:1,repository:'Xenoah/meshcopia',activations:[]};
const activation={...empty,activations:[{cohort:'published137',releaseTag:'fbx-minimal-v1.0.0',releaseId:1,verificationCommit:'a'.repeat(40),inventorySha256:'b'.repeat(64),transportEvidenceFile:'docs/fbx-minimal-publication/test.json',transportEvidenceSha256:'c'.repeat(64)}]};
const stable=x=>Array.isArray(x)?`[${x.map(stable).join(',')}]`:x&&typeof x==='object'?`{${Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')}}`:JSON.stringify(x);
function receipt(){const projection=Array.from({length:137},(_,i)=>({id:'fixture-'+i}));return {schemaVersion:1,verificationMode:'full-internal-qa',createdBy:'same-job-fbx-minimal-prep/1',execution:{runId:null,runAttempt:null,job:null},head:'a'.repeat(40),activationSha256:hash('ACTIVATION'),inputs:[{path:'docs/proof.json',sha256:hash('INPUT')}],projection,projectionSha256:hash(stable(projection)),sourceBindings:projection.map(x=>({...x})),provenance:{}};}
const verify=r=>validatePrepReceipt(r,{head:'a'.repeat(40),activationBytes:Buffer.from('ACTIVATION'),read:async()=>Buffer.from('INPUT')});
test('checked-in activation schema and strict minimal-only config',async()=>{validateFbxMinimalActivation(JSON.parse(await readFile(new URL('../docs/fbx-minimal-activation.json',import.meta.url))));validateFbxMinimalActivation(empty);validateFbxMinimalActivation(activation);for(const fn of [a=>a.activations[0].releaseTag='fbx-v1.0.0',a=>a.activations[0].extra=true,a=>a.activations[0].transportEvidenceFile='../qa.json',a=>a.activations.push(a.activations[0])]){const x=structuredClone(activation);fn(x);assert.throws(()=>validateFbxMinimalActivation(x));}});
test('same-job receipt accepts exact bound input',()=>verify(receipt()));
for(const [label,change] of [
 ['invalid verification mode',r=>r.verificationMode='fallback'],['other execution job',r=>r.execution.runId='different'],['stale HEAD',r=>r.head='b'.repeat(40)],['stale activation',r=>r.activationSha256='b'.repeat(64)],['stale evidence/input',r=>r.inputs[0].sha256='b'.repeat(64)],['altered projection',r=>r.projection[0].id='altered'],['missing input',r=>r.inputs=[]],['duplicate input',r=>r.inputs.push(r.inputs[0])],['unsafe input',r=>r.inputs[0].path='../outside'],['partial receipt',r=>delete r.projection],['wrong writer',r=>r.createdBy='caller-provided'],['duplicate source binding',r=>r.sourceBindings[1]=r.sourceBindings[0]],['mismatched source binding',r=>r.sourceBindings[0].id='other']])test(`reject ${label}`,async()=>{const r=receipt();change(r);await assert.rejects(()=>verify(r));});
test('missing receipt and symlink input rejected',async()=>{await assert.rejects(()=>regularRead('.cache/does-not-exist-fbx-test.json'));const root=await mkdtemp(path.join(process.cwd(),'fbx-symlink-fixture-'));try{await writeFile(path.join(root,'real'),'text');await symlink('real',path.join(root,'link'));await assert.rejects(()=>regularRead(path.relative(process.cwd(),path.join(root,'link'))),/Symlink/);}finally{await rm(root,{recursive:true,force:true});}});
test('minimal UI selector permits exact verified source/version only',()=>{const asset={id:'fixture',version:'1.0.0',type:'model',status:'public'};const root='https://github.com/Xenoah/meshcopia/releases/download/fbx-minimal-v1.0.0/';const file=n=>({filename:n,url:root+n,bytes:1,sha256:'a'.repeat(64)});const record={id:'fixture',assetVersion:'1.0.0',format:'FBX',packageVersion:'1.0.0',selfContained:true,direct:file('fixture.fbx'),archive:file('fixture-1.0.0-fbx-minimal-1.0.0.zip'),notice:{filename:'LICENSE.txt'},limitations:['Synthetic test only'],verification:{state:'published-verified',releaseTag:'fbx-minimal-v1.0.0'}};assert.equal(fbxMinimalForAsset(asset,{formats:[record]}),record);assert.equal(fbxMinimalForAsset({...asset,status:'draft'},{formats:[record]}),undefined);assert.equal(fbxMinimalForAsset({...asset,version:'2.0.0'},{formats:[record]}),undefined);assert.equal(fbxMinimalForAsset(asset,{formats:[record,record]}),undefined);assert.equal(fbxMinimalForAsset(asset,{formats:[{...record,archive:file('fixture-legacy8.zip')}]}),undefined);});
test('generator supplies only verified projection to production policy before cleanup',async()=>{const code=await readFile(new URL('../scripts/generate.mjs',import.meta.url),'utf8');assert.ok(code.indexOf('await prepareFbxMinimalDownloads(assets)')<code.indexOf('await assertCompleteModelDeliveries'));assert.match(code,/assertCompleteModelDeliveries\(assets,\{verifiedFbx,baseline:/);assert.ok(code.indexOf('await assertCompleteModelDeliveries')<code.indexOf("await rm('public/assets'"));assert.match(code,/await writeFbxMinimalDownloads\(verifiedFbx,assets\)/);});
test('durable production prep is mandatory and token-free before build',async()=>{const code=await readFile(new URL('../.github/workflows/publish.yml',import.meta.url),'utf8');assert.equal((code.match(/GITHUB_TOKEN:/g)||[]).length,0);assert.doesNotMatch(code,/actions: read/);assert.match(code,/--verification-mode durable-transport-attestation/);assert.ok(code.indexOf('prepare-fbx-minimal-activation.py')<code.indexOf('run: npm run check'));assert.doesNotMatch(code,/GITHUB_ENV|echo.*GITHUB_TOKEN/);assert.equal((code.match(/persist-credentials: false/g)||[]).length,2);assert.match(code,/PUSH_TOKEN: \$\{\{ github.token \}\}/);});

test('current metadata, source bytes and complete inventory must still match prep',async()=>{
 const asset={dir:path.join(process.cwd(),'content/assets/fixture'),sources:['a.glb']};const bound={metadataSha256:hash('META'),sources:[{name:'a.glb',bytes:4,sha256:hash('GLB!')}]};
 const read=async p=>Buffer.from(p.endsWith('asset.json')?'META':'GLB!');await validateCurrentFbxSources(asset,bound,{read});
 for(const changed of [async()=>Buffer.from('CHANGED'),async p=>Buffer.from(p.endsWith('asset.json')?'META':'DRIFT')])await assert.rejects(()=>validateCurrentFbxSources(asset,bound,{read:changed}));
 await assert.rejects(()=>validateCurrentFbxSources({...asset,sources:['a.glb','extra.png']},bound,{read}));
});

test('full Git history retains a side-branch activation hidden by merge tree and excludes new HEAD from retained baseline',async()=>{
 const {execFileSync}=await import('node:child_process');const {verifyFbxMinimalHistory}=await import('../scripts/lib/fbx-minimal-downloads.mjs');
 const root=await mkdtemp(path.join(os.tmpdir(),'fbx-history-'));const previous=process.cwd();
 const git=(...args)=>execFileSync('git',args,{cwd:root,stdio:'pipe'}).toString().trim();
 try{
  git('init','-b','main');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');await mkdir(path.join(root,'docs'));await writeFile(path.join(root,'docs/fbx-minimal-activation.json'),JSON.stringify(empty));git('add','.');git('commit','-m','empty');
  git('checkout','-b','side');await writeFile(path.join(root,'docs/fbx-minimal-activation.json'),JSON.stringify(activation));git('add','.');git('commit','-m','new');
  process.chdir(root);assert.deepEqual([...(await verifyFbxMinimalHistory(activation)).retained],[]);process.chdir(previous);
  git('checkout','main');git('merge','--no-ff','-s','ours','side','-m','retain main tree');
  process.chdir(root);await assert.rejects(()=>verifyFbxMinimalHistory(empty),/Immutable/);assert.deepEqual([...(await verifyFbxMinimalHistory(activation)).retained],['fbx-minimal-v1.0.0']);
 }finally{process.chdir(previous);await rm(root,{recursive:true,force:true});}
});
