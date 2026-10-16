import test from 'node:test';import assert from 'node:assert/strict';import {validateSourceStage} from '../scripts/lib/source-stage.mjs';
const marker={schemaVersion:1,purpose:'draft-raw-source-prepublication',ids:['new-model']};const asset={id:'new-model',type:'model',status:'draft'};
test('source-only phase admits only bounded wholly new draft models',()=>{assert.equal(validateSourceStage(marker,[asset],[]),true);for(const status of ['public','hidden'])assert.throws(()=>validateSourceStage(marker,[{...asset,status}],[]));assert.throws(()=>validateSourceStage(marker,[asset],['new-model']));assert.throws(()=>validateSourceStage({...marker,ids:[]},[],[]));assert.throws(()=>validateSourceStage({...marker,ids:['new-model','new-model']},[asset],[]))});
test('source-only workflow skips release and Pages without weakening promotion order',async()=>{const {readFile}=await import('node:fs/promises');const s=await readFile('.github/workflows/publish.yml','utf8');assert.ok(s.includes('needs: [verify, release]'));assert.ok(s.match(/release:\n    needs: verify\n    if: .*source_only/));assert.ok(s.match(/pages:\n    needs: \[verify, release\]\n    if: .*source_only/));assert.ok(s.includes('node scripts/check-source-stage.mjs'))});
test('only absent marker disables source stage; falsey or malformed JSON fails closed',async()=>{
 const {mkdtemp,mkdir,writeFile,rm}=await import('node:fs/promises');const {spawnSync}=await import('node:child_process');const {tmpdir}=await import('node:os');const path=await import('node:path');const {fileURLToPath}=await import('node:url');
 const dir=await mkdtemp(path.join(tmpdir(),'meshcopia-source-marker-'));
 const script=fileURLToPath(new URL('../scripts/check-source-stage.mjs',import.meta.url));
 try{
  await mkdir(path.join(dir,'docs'));await mkdir(path.join(dir,'content/assets'),{recursive:true});
  await writeFile(path.join(dir,'docs/scaling-protected-ids.json'),JSON.stringify({ids:[]}));
  let result=spawnSync(process.execPath,[script],{cwd:dir,encoding:'utf8'});assert.equal(result.status,0,result.stderr);assert.equal(result.stdout,'false\n');
  for(const raw of ['null','false','0','""','[]','{}','{broken']){
   await writeFile(path.join(dir,'.source-stage.json'),raw);
   result=spawnSync(process.execPath,[script],{cwd:dir,encoding:'utf8'});
   assert.notEqual(result.status,0,`Present marker ${raw} must fail`);assert.equal(result.stdout,'');
   assert.match(result.stderr,raw==='{broken'?/SyntaxError/:/marker must be an object|AssertionError/);
  }
 }finally{await rm(dir,{recursive:true,force:true})}
});
test('workflow source-stage output propagates validator errors and publishes only explicit false',async()=>{
 const {readFile,mkdtemp,rm}=await import('node:fs/promises');const {spawnSync}=await import('node:child_process');const {tmpdir}=await import('node:os');const path=await import('node:path');
 const workflow=await readFile('.github/workflows/publish.yml','utf8');
 assert.ok((workflow.match(/source_only == 'false'/g)||[]).length>=5);
 assert.ok(!workflow.includes("source_only != 'true'"));
 const block=workflow.match(/id: source-stage\n        shell: bash\n        run: \|\n([\s\S]*?)(?=      - )/);
 assert.ok(block,'Source-stage command must use an explicit fail-closed shell block');
 const script=block[1].replace(/^          /gm,'');
 const dir=await mkdtemp(path.join(tmpdir(),'meshcopia-source-output-'));
 try{
  for(const [index,[value,status,allowed]] of [['true',0,true],['false',0,true],['',0,false],['invalid',0,false],['true',1,false],['',1,false]].entries()){
   const output=path.join(dir,String(index));
   const result=spawnSync('bash',['-c',`node() { printf '%s\\n' "$FIXTURE_OUTPUT"; return "$FIXTURE_STATUS"; }\n${script}`],{encoding:'utf8',env:{...process.env,GITHUB_OUTPUT:output,FIXTURE_OUTPUT:value,FIXTURE_STATUS:String(status)}});
   const written=await readFile(output,'utf8').catch(e=>{if(e.code!=='ENOENT')throw e;return ''});
   if(allowed){assert.equal(result.status,0,result.stderr);assert.equal(written,`source_only=${value}\n`)}
   else{assert.notEqual(result.status,0);assert.equal(written,'','Failed validation must not produce an output for publication')}
  }
 }finally{await rm(dir,{recursive:true,force:true})}
});
