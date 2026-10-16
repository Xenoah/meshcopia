import assert from 'node:assert/strict';
import {readFile,lstat,mkdir,writeFile,unlink} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fbxMinimalForAsset} from '../../src/lib/fbx-minimal-downloads.mjs';
const execute=promisify(execFile);
export const activationPath='docs/fbx-minimal-activation.json';
export const receiptPath='.cache/fbx-minimal-verified.json';
const hash=b=>createHash('sha256').update(b).digest('hex');
const stable=x=>Array.isArray(x)?`[${x.map(stable).join(',')}]`:x&&typeof x==='object'?`{${Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')}}`:JSON.stringify(x);
const inventory=xs=>[...xs].sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0);
const safe=p=>typeof p==='string'&&!p.startsWith('/')&&!/[\\\x00-\x1f:]/.test(p)&&p.split('/').every(x=>x&&x!=='.'&&x!=='..');
export async function regularRead(relative){
 assert.ok(safe(relative),'Unsafe receipt input path');
 let current='.';for(const part of relative.split('/')){current=path.join(current,part);assert.ok(!(await lstat(current)).isSymbolicLink(),'Symlink in receipt input');}
 assert.ok((await lstat(relative)).isFile(),'Receipt input is not regular');return readFile(relative);
}
export function validateFbxMinimalActivation(config){
 assert.deepEqual(Object.keys(config).sort(),['activations','repository','schemaVersion']);assert.equal(config.schemaVersion,1);assert.equal(config.repository,'Xenoah/meshcopia');assert.ok(Array.isArray(config.activations)&&config.activations.length<=1);
 for(const a of config.activations){
  assert.deepEqual(Object.keys(a).sort(),['cohort','inventorySha256','releaseId','releaseTag','transportEvidenceFile','transportEvidenceSha256','verificationCommit']);
  assert.equal(a.cohort,'published137');assert.equal(a.releaseTag,'fbx-minimal-v1.0.0');assert.ok(Number.isSafeInteger(a.releaseId)&&a.releaseId>0);assert.match(a.verificationCommit,/^[a-f0-9]{40}$/);
  for(const k of ['inventorySha256','transportEvidenceSha256'])assert.match(a[k],/^[a-f0-9]{64}$/);
  assert.match(a.transportEvidenceFile,/^docs\/fbx-minimal-publication\/[A-Za-z0-9][A-Za-z0-9._-]*\.json$/);
 }
 return config;
}
async function git(...args){
 const env=Object.fromEntries(Object.entries(process.env).filter(([k])=>!k.toUpperCase().startsWith('GIT_')));
 Object.assign(env,{GIT_NO_REPLACE_OBJECTS:'1',GIT_OPTIONAL_LOCKS:'0',GIT_TERMINAL_PROMPT:'0',GIT_NO_LAZY_FETCH:'1',GIT_CONFIG_NOSYSTEM:'1',GIT_CONFIG_GLOBAL:'/dev/null'});
 return (await execute('git',['--no-replace-objects',...args],{env,maxBuffer:32*1024*1024})).stdout.trim();
}
export async function verifyFbxMinimalHistory(config){
 assert.equal(await git('rev-parse','--is-shallow-repository'),'false','Full history required');
 const head=await git('rev-parse','HEAD');
 const graft=await git('rev-parse','--git-path','info/grafts');
 try{assert.equal((await readFile(graft,'utf8')).trim(),'','Grafted history prohibited');}catch(e){if(e.code!=='ENOENT')throw e;}
 for(const args of [['config','--get','extensions.partialClone'],['config','--get-regexp','^remote\\..*\\.promisor$']]){try{await git(...args);throw Error('Partial/promisor Git prohibited');}catch(e){if(e.code!==1)throw e;}}
 const retained=new Set();
 for(const commit of (await git('rev-list','HEAD')).split('\n').filter(Boolean)){
  if(!await git('ls-tree',commit,'--',activationPath))continue;
  const old=validateFbxMinimalActivation(JSON.parse(await git('show',`${commit}:${activationPath}`)));
  for(const a of old.activations){assert.ok(config.activations.some(x=>stable(x)===stable(a)),'Immutable FBX activation changed or removed');if(commit!==head)retained.add(a.releaseTag);}
 }
 return {head,retained};
}
export async function validatePrepReceipt(receipt,{head,activationBytes,read=regularRead,execution={runId:process.env.GITHUB_RUN_ID??null,runAttempt:process.env.GITHUB_RUN_ATTEMPT??null,job:process.env.GITHUB_JOB??null}}){
 assert.deepEqual(Object.keys(receipt).sort(),['activationSha256','createdBy','execution','head','inputs','projection','projectionSha256','provenance','schemaVersion','sourceBindings','verificationMode']);
 assert.ok(['full-internal-qa','durable-transport-attestation'].includes(receipt.verificationMode),'Invalid verification mode');
 assert.deepEqual(receipt.execution,execution,'Receipt belongs to another execution job');
 assert.equal(receipt.schemaVersion,1);assert.equal(receipt.createdBy,'same-job-fbx-minimal-prep/1');assert.equal(receipt.head,head,'Stale FBX receipt HEAD');assert.equal(receipt.activationSha256,hash(activationBytes),'Stale activation receipt');
 assert.equal(receipt.projectionSha256,hash(stable(receipt.projection)),'Receipt projection changed');
 assert.ok(Array.isArray(receipt.inputs)&&receipt.inputs.length>0);assert.equal(new Set(receipt.inputs.map(x=>x.path)).size,receipt.inputs.length,'Duplicate receipt input');
 for(const row of receipt.inputs){assert.deepEqual(Object.keys(row).sort(),['path','sha256']);assert.ok(safe(row.path));assert.equal(hash(await read(row.path)),row.sha256,`Stale FBX input: ${row.path}`);}
 assert.ok(Array.isArray(receipt.sourceBindings));assert.equal(new Set(receipt.sourceBindings.map(x=>x.id)).size,receipt.sourceBindings.length);
 assert.equal(receipt.projection.length,137);assert.equal(receipt.sourceBindings.length,137);
 assert.equal(new Set(receipt.projection.map(x=>x.id)).size,137,'Duplicate projection ID');
 assert.deepEqual(receipt.projection.map(x=>x.id).sort(),receipt.sourceBindings.map(x=>x.id).sort(),'Projection/source binding ID set differs');
 return receipt;
}
export async function validateCurrentFbxSources(asset,bound,{read=regularRead}={}){
 assert.equal(hash(await read(path.relative(process.cwd(),path.join(asset.dir,'asset.json')))),bound.metadataSha256,'Current FBX metadata changed');
 const sources=[];for(const name of asset.sources){const bytes=await read(path.relative(process.cwd(),path.join(asset.dir,'source',name)));sources.push({name,bytes:bytes.length,sha256:hash(bytes)});}
 assert.equal(stable(inventory(sources)),stable(inventory(bound.sources)),'Current FBX complete source inventory changed');
}
export async function prepareFbxMinimalDownloads(assets){
 const activationBytes=await regularRead(activationPath);const config=validateFbxMinimalActivation(JSON.parse(activationBytes));const {head,retained}=await verifyFbxMinimalHistory(config);
 if(!config.activations.length)return [];
 const receipt=await validatePrepReceipt(JSON.parse(await regularRead(receiptPath)),{head,activationBytes});
 const runtime=JSON.parse(await regularRead('docs/fbx-minimal-verification/runtime.json'));
 const required=['.github/workflows/release-fbx-minimal.yml','docs/fbx-minimal-transport/approval.json','docs/fbx-minimal-activation.json','scripts/prepare-fbx-minimal-activation.py','scripts/verify-minimal-activation.py','scripts/lib/fbx-minimal-downloads.mjs','src/lib/fbx-minimal-downloads.mjs','scripts/fbx-minimal-transport/qa.py','scripts/fbx-minimal-transport/transport.py','scripts/fbx-minimal-verification/common.py','docs/fbx-minimal-verification/source137.json','docs/fbx-minimal-verification/expected137.json','docs/fbx-minimal-verification/runtime.json','.github/workflows/verify-fbx-minimal.yml',config.activations[0].transportEvidenceFile,...Object.keys(runtime.supportFiles),...Object.keys(runtime.recipe).map(n=>'scripts/fbx-verification/'+n)];
 assert.deepEqual(receipt.inputs.map(x=>x.path).sort(),[...new Set(required)].sort(),'Receipt input coverage differs');

 const a=config.activations[0];assert.ok(receipt.inputs.some(x=>x.path===a.transportEvidenceFile&&x.sha256===a.transportEvidenceSha256),'Missing exact T evidence binding');
 assert.equal(receipt.provenance.fCommit,a.verificationCommit);assert.equal(receipt.provenance.releaseId,a.releaseId);assert.equal(receipt.provenance.inventorySha256,a.inventorySha256);
 const evidence=JSON.parse(await regularRead(a.transportEvidenceFile));assert.equal(stable({...evidence.provenance,releaseId:a.releaseId,transportExecution:evidence.transportExecution}),stable(receipt.provenance),'Receipt QA/run provenance changed');
 const current=[];
 for(const record of receipt.projection){
  const bound=receipt.sourceBindings.find(x=>x.id===record.id);assert.ok(bound&&bound.assetVersion===record.assetVersion);assert.equal(stable(inventory(bound.sources)),stable(inventory(record.sources)));
  const asset=assets.find(x=>x.id===record.id&&x.version===record.assetVersion&&x.type==='model'&&x.status==='public');
  if(!retained.has(a.releaseTag))assert.ok(asset,'New minimal FBX requires current public identity/version');
  if(!asset)continue;
  await validateCurrentFbxSources(asset,bound);
  assert.ok(fbxMinimalForAsset(asset,{formats:[record]}),'Invalid verified FBX projection');current.push(record);
 }
 await unlink(receiptPath); // One build consumes one prep receipt; never reuse as offline proof.
 return current;
}
export async function writeFbxMinimalDownloads(formats,assets){
 const projection={schemaVersion:1,coverage:{publicModels:assets.filter(a=>a.status==='public'&&a.type==='model').length,fbxReadyModels:new Set(formats.map(x=>x.id)).size},formats};
 for(const dir of ['src/data','public/api']){await mkdir(dir,{recursive:true});await writeFile(`${dir}/fbx-minimal-downloads.json`,JSON.stringify(projection,null,2)+'\n');}
}
