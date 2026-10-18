import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,mkdir,writeFile,rm,symlink} from 'node:fs/promises';
import {spawnSync,execFileSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateSourceStage} from '../scripts/lib/source-stage.mjs';
import {assertSuccessfulSourceStageRun} from '../scripts/lib/source-stage-proof.mjs';
const sourceScript=fileURLToPath(new URL('../scripts/check-source-stage.mjs',import.meta.url));
const unchangedScript=fileURLToPath(new URL('../scripts/check-source-stage-unchanged.mjs',import.meta.url));
const workflow=await readFile(new URL('../.github/workflows/publish.yml',import.meta.url),'utf8');
const steps=workflow.split(/(?=^      - )/m).slice(1).map(s=>s.split(/^  (?:pages|release):/m)[0]);
const step=name=>{const value=steps.find(s=>s.includes(`- name: ${name}\n`));assert.ok(value,name);return value;};
const run=(file,cwd,env={})=>spawnSync(process.execPath,[file],{cwd,encoding:'utf8',env:{...process.env,...env}});
const marker=ids=>({schemaVersion:1,purpose:'draft-raw-source-prepublication',ids});

test('all import/generation, commit and publication paths explicitly require false; QA remains on',()=>{
 for(const name of ['Generate original starter assets (once)','Set up original cafe extraction (once)','Extract the pinned original cafe collection (once)','Import more original cafe meshes and textures (once)','Import reviewed original Yokocho assets (once)','Set up original city draft generation (once)','Generate original city drafts for review (once)','Import inbox','Commit imported original assets','Build release archives'])assert.match(step(name),/if: steps\.source-stage\.outputs\.source_only == 'false'/,name);
 for(const s of steps.filter(s=>s.includes('actions/upload-')&&!s.includes('name: browser-qa')&&!s.includes('name: city-draft-qa')))assert.match(s,/if: .*?(?:steps\.source-stage|needs\.verify)\.outputs\.source_only == 'false'/);
 for(const name of ['Verify durable minimal FBX proof and all public bytes','Validate, test and build','Verify texture maps, current delivery URLs and Pages budget','Browser interactions and screenshots','Verify ordinary selected downloads and exact displayed ZIP sizes','Verify all FBX links and actual anonymous FBX downloads'])assert.doesNotMatch(step(name),/\n        if:/,name);
 for(const name of ['Preserve QA evidence','Preserve city draft QA evidence'])assert.match(step(name),/if: always\(\)/);
 assert.match(workflow,/pages:\n    needs: \[verify, release\]\n    if: needs\.verify\.outputs\.source_only == 'false'/);
 assert.match(workflow,/release:\n    needs: verify\n    if: needs\.verify\.outputs\.source_only == 'false'/);
 assert.doesNotMatch(workflow,/source_only != 'true'|freeze-inventory|stage-release-manifest/);
 assert.ok(workflow.indexOf('id: source-stage')<workflow.indexOf('Generate original starter assets'));
 assert.ok(workflow.indexOf('Verify source unchanged after QA')>workflow.indexOf('Verify all FBX links'));
 assert.ok(workflow.indexOf('Verify source unchanged after QA')<workflow.indexOf('Commit imported original assets'));
 assert.ok(workflow.indexOf('Record verified source SHA')>workflow.indexOf('Commit imported original assets'));
 assert.doesNotMatch(step('Record verified source SHA'),/\n        if:|PUSH_TOKEN|git (?:add|commit|push)/);
 assert.match(step('Record verified source SHA'),/id: commit\n.*git rev-parse HEAD/s);
 const tokenSteps=steps.filter(s=>s.includes('PUSH_TOKEN:'));assert.equal(tokenSteps.length,1);assert.match(tokenSteps[0],/if: steps\.source-stage\.outputs\.source_only == 'false'/);
 assert.equal((workflow.match(/persist-credentials: false/g)||[]).length,3);
});

test('live verification is read-only and checks the deployed artifact after Pages succeeds',()=>{
 const live=workflow.split('  verify-live:\n')[1];assert.ok(live);
 assert.match(live,/needs: \[verify, pages\]/);assert.match(live,/if: needs\.verify\.outputs\.source_only == 'false'/);
 assert.match(live,/ref: \$\{\{ needs\.verify\.outputs\.sha \}\}/);
 assert.match(live,/name: github-pages/);assert.match(live,/contents: read/);
 assert.doesNotMatch(live,/contents: write|pages: write|id-token: write|run-id:|repository:/);
 for(const script of ['check-live-pages.mjs','test-minimal-downloads-browser.mjs --live','test-fbx-minimal-downloads-browser.mjs --live','test-browser.mjs --live'])assert.ok(live.includes(script));
});

test('source-only identity gate accepts only exact main push HEAD; dispatch is not a proof',()=>{
 const shell=step('Require exact main push for source-only stage').split('        run: |\n')[1].replace(/^          /gm,'');
 for(const [event,ref,actual,expected,ok] of [['push','refs/heads/main','a'.repeat(40),'a'.repeat(40),true],['workflow_dispatch','refs/heads/main','a'.repeat(40),'a'.repeat(40),false],['push','refs/heads/other','a'.repeat(40),'a'.repeat(40),false],['push','refs/heads/main','b'.repeat(40),'a'.repeat(40),false]]){
  const result=spawnSync('bash',['-c',`git() { printf '%s\\n' "$FIXTURE_HEAD"; }\n${shell}`],{encoding:'utf8',env:{...process.env,GITHUB_EVENT_NAME:event,GITHUB_REF:ref,GITHUB_SHA:expected,FIXTURE_HEAD:actual}});assert.equal(result.status===0,ok,result.stderr);
 }
 const proof={commit:'a'.repeat(40),runId:1},run={id:1,repository:{full_name:'Xenoah/meshcopia'},head_repository:{full_name:'Xenoah/meshcopia'},path:'.github/workflows/publish.yml',event:'push',head_branch:'main',head_sha:proof.commit,status:'completed',conclusion:'success'};
 assertSuccessfulSourceStageRun(proof,run);assert.throws(()=>assertSuccessfulSourceStageRun(proof,{...run,event:'workflow_dispatch'}));
});

test('separate SHA output is exact and fails closed on missing or failed HEAD lookup',async()=>{
 const shell=step('Record verified source SHA').split('        run: |\n')[1].replace(/^          /gm,'');
 const root=await mkdtemp(path.join(tmpdir(),'source-sha-output-'));
 try{
  for(const [index,[head,status,ok]] of [['a'.repeat(40),0,true],['',0,false],['main',0,false],['a'.repeat(40),1,false]].entries()){
   const output=path.join(root,String(index));
   const result=spawnSync('bash',['-c',`git() { printf '%s\\n' "$FIXTURE_HEAD"; return "$FIXTURE_STATUS"; }\n${shell}`],{encoding:'utf8',env:{...process.env,GITHUB_OUTPUT:output,FIXTURE_HEAD:head,FIXTURE_STATUS:String(status)}});
   const actual=await readFile(output,'utf8').catch(e=>{if(e.code!=='ENOENT')throw e;return ''});
   assert.equal(result.status===0,ok,result.stderr);assert.equal(actual,ok?`sha=${head}\n`:'');
  }
 }finally{await rm(root,{recursive:true,force:true});}
});

test('pending bootstrap/import/generation inputs fail before source-only output',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'source-inputs-'));
 try{
  await mkdir(path.join(root,'docs'));await mkdir(path.join(root,'_inbox'));await mkdir(path.join(root,'content/assets/fixture/source'),{recursive:true});
  const a={id:'fixture',type:'model',status:'draft',title:'Fixture',titleEn:'Fixture',description:'Fixture',descriptionEn:'Fixture',category:'fixture',author:'Fixture',version:'1.0.0',created:'2026-01-01',updated:'2026-01-01',license:'CC-BY-4.0',tags:[],provenance:{method:'fixture',tool:'fixture',rights:'fixture'},thumbnail:'preview.png',preview:'fixture.glb',unit:'m',upAxis:'Y',triangles:1};
  await writeFile(path.join(root,'content/assets/fixture/asset.json'),JSON.stringify(a));await writeFile(path.join(root,'content/assets/fixture/preview.png'),'fixture');await writeFile(path.join(root,'content/assets/fixture/source/fixture.glb'),'fixture');
  await writeFile(path.join(root,'docs/scaling-protected-ids.json'),JSON.stringify({ids:[]}));await writeFile(path.join(root,'.source-stage.json'),JSON.stringify(marker(['fixture'])));
  let result=run(sourceScript,root);assert.equal(result.status,0,result.stderr);assert.equal(result.stdout,'true\n');
  for(const name of ['.bootstrap-starter','.import-commons-cafe','.import-commons-expansion','.import-yokocho','.generate-city-drafts.json']){
   await writeFile(path.join(root,name),'fixture');result=run(sourceScript,root);assert.notEqual(result.status,0,name);assert.equal(result.stdout,'');assert.match(result.stderr,/pending generation\/import marker/);await rm(path.join(root,name));
  }
  await mkdir(path.join(root,'_inbox/pending'));result=run(sourceScript,root);assert.notEqual(result.status,0);assert.equal(result.stdout,'');assert.match(result.stderr,/pending inbox/);await rm(path.join(root,'_inbox/pending'),{recursive:true});
  await symlink('../content/assets/fixture',path.join(root,'_inbox/link'));result=run(sourceScript,root);assert.notEqual(result.status,0);assert.equal(result.stdout,'');await rm(path.join(root,'_inbox/link'));
  await rm(path.join(root,'.source-stage.json'));await writeFile(path.join(root,'.bootstrap-starter'),'fixture');result=run(sourceScript,root);assert.equal(result.status,0,result.stderr);assert.equal(result.stdout,'false\n');
 }finally{await rm(root,{recursive:true,force:true});}
});

test('post-QA guard rejects staged, unstaged, untracked changes and changed HEAD; permits ignored QA',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'source-clean-'));
 const git=(...args)=>execFileSync('git',args,{cwd:root,stdio:'pipe'}).toString().trim();
 try{
  git('init','-b','main');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');
  await writeFile(path.join(root,'.gitignore'),await readFile(new URL('../.gitignore',import.meta.url)));await writeFile(path.join(root,'source.txt'),'reviewed');git('add','.');git('commit','-m','fixture');const head=git('rev-parse','HEAD');
  const check=env=>run(unchangedScript,root,{SOURCE_ONLY:'true',SOURCE_HEAD:head,...env});
  assert.equal(check().status,0);for(const value of ['',undefined,'invalid'])assert.notEqual(check({SOURCE_ONLY:value}).status,0);assert.notEqual(check({SOURCE_HEAD:''}).status,0);
  await mkdir(path.join(root,'test-results'));await writeFile(path.join(root,'test-results/qa.json'),'{}');await mkdir(path.join(root,'src/data'),{recursive:true});await writeFile(path.join(root,'src/data/fbx-minimal-downloads.json'),'{}');assert.equal(check().status,0);
  await writeFile(path.join(root,'source.txt'),'drift');assert.notEqual(check().status,0);git('add','source.txt');assert.notEqual(check().status,0);git('reset','--hard','HEAD');
  await writeFile(path.join(root,'new-source.txt'),'new');assert.notEqual(check().status,0);await rm(path.join(root,'new-source.txt'));
  git('commit','--allow-empty','-m','changed-head');assert.notEqual(check().status,0);assert.equal(check({SOURCE_ONLY:'false'}).status,0);
 }finally{await rm(root,{recursive:true,force:true});}
});

test('six bounded markers accept accumulated drafts without expanding protected public cohort',()=>{
 const protectedIds=Array.from({length:173},(_,i)=>`old-${i}`),drafts=Array.from({length:232},(_,i)=>({id:`new-${i}`,type:'model',status:'draft'}));
 let count=0;for(const size of [12,44,44,44,44,44]){const selected=drafts.slice(count,count+size);count+=size;assert.equal(validateSourceStage(marker(selected.map(a=>a.id)),drafts.slice(0,count),protectedIds),true);}
 assert.equal(count,232);assert.throws(()=>validateSourceStage(marker(drafts.slice(0,51).map(a=>a.id)),drafts,protectedIds));
});
