// Run from the integrated repository after npm run check. No fixtures or routing
// substitutions: download checks use actual browser GETs to immutable Releases.
import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const {primaryDownload,directModelFiles,downloadHref}=await import(pathToFileURL(path.resolve('src/lib/downloads.mjs')));
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const {chromium}=createRequire(path.resolve('package.json'))('@playwright/test');
const root=path.resolve('dist');
const catalog=JSON.parse(await readFile('dist/api/catalog.json','utf8')).assets;
const side=JSON.parse(await readFile('dist/api/fbx-minimal-downloads.json','utf8'));
assert.deepEqual(side.coverage,{publicModels:137,fbxReadyModels:137});assert.equal(side.formats.length,137);assert.deepEqual(side.formats.map(x=>x.id).sort(),catalog.filter(x=>x.type==='model').map(x=>x.id).sort());
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.wasm':'application/wasm'};
const server=createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1');assert.ok(url.pathname.startsWith('/meshcopia/'));
  let file=path.resolve(root,decodeURIComponent(url.pathname.slice('/meshcopia/'.length)));
  assert.ok(file===root||file.startsWith(root+path.sep));
  if((await stat(file)).isDirectory())file=path.join(file,'index.html');
  res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(await readFile(file));
 }catch{res.writeHead(404).end('Not found')}
});
await new Promise(resolve=>server.listen(4174,'127.0.0.1',resolve));
await mkdir('test-results',{recursive:true});
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const evidence={browserFbxRendering:false,scope:'Local built pages; actual anonymous immutable Release browser downloads',coverage:side.coverage,pages:[],originalButtonsChecked:[],downloads:[]};
try{
 const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const home='http://127.0.0.1:4174/meshcopia/';
 for(const record of side.formats){
  await page.goto(home+`assets/${record.id}/`,{waitUntil:'domcontentloaded'});
  const original=catalog.find(a=>a.id===record.id);assert.ok(original);
  const selected=primaryDownload(original);assert.ok(selected);
  assert.equal(await page.locator('.download-primary').count(),1);
  assert.equal(await page.locator('.download-primary').getAttribute('href'),downloadHref(selected.url));
  const direct=directModelFiles(original);assert.equal(await page.locator('.direct-formats a.direct-download').count(),direct.length);
  for(const [index,file] of direct.entries())assert.equal(await page.locator('.direct-formats a.direct-download').nth(index).getAttribute('href'),downloadHref(file.url));
  const box=page.locator('.fbx-download');assert.equal(await box.count(),1);
  assert.equal(await box.locator('.fbx-compatibility').count(),1);
  assert.match(await box.locator('.fbx-compatibility').getAttribute('data-en'),/materials, transparency and face culling.*GLB.*PBR/);
  assert.equal(await box.locator('a.button').getAttribute('href'),record.archive.url);
  assert.equal(await box.locator('a.direct-download').getAttribute('href'),record.direct.url);
  assert.equal(await page.locator('[data-format="fbx"]').count(),0,'FBX unexpectedly added to browser viewer');
  for(const limitation of record.limitations)assert.ok((await box.textContent()).includes(limitation));
  evidence.pages.push(record.id);evidence.originalButtonsChecked.push(record.id);
 }
 // Representative plain, textured and large/complex sources. All275 attachment
 // bytes are independently checked by the production build gate; these actual
 // browser clicks establish browser delivery for both buttons in each case.
 for(const id of ['atelier-lamp','commons-bar-stool','yokocho-noh-pavilion']){
  const record=side.formats.find(r=>r.id===id);assert.ok(record);
  await page.goto(home+`assets/${id}/`);
  await page.locator('.fbx-download > summary').click();
  for(const [selector,expected] of [['.fbx-download a.button',record.archive],['.fbx-download a.direct-download',record.direct]]){
   const pending=page.waitForEvent('download',{timeout:120000});await page.locator(selector).click();const download=await pending;
   assert.equal(await download.failure(),null);const data=await readFile(await download.path());const digest=createHash('sha256').update(data).digest('hex');
   assert.equal(data.length,expected.bytes);assert.equal(digest,expected.sha256);
   if(expected===record.archive)execFileSync('python3',['-c',"import importlib.util,json,sys;from pathlib import Path;spec=importlib.util.spec_from_file_location('prep','scripts/prepare-fbx-minimal-activation.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p.verify_two_entry_zip(Path(sys.argv[1]),json.load(sys.stdin))",await download.path()],{input:JSON.stringify({id:record.id,fbx:record.direct,notice:record.notice}),stdio:['pipe','pipe','pipe']});

   evidence.downloads.push({id,url:download.url(),bytes:data.length,sha256:digest,suggestedFilename:download.suggestedFilename()});await download.delete();
  }
 }
 await page.setViewportSize({width:390,height:844});await page.goto(home+'assets/commons-bar-stool/');await page.locator('.fbx-download > summary').click();await page.locator('.fbx-download').scrollIntoViewIfNeeded();
 assert.ok(await page.locator('.fbx-download').isVisible());assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.screenshot({path:'test-results/mobile-fbx-downloads.png',fullPage:true});
 const nojs=await browser.newContext({javaScriptEnabled:false});const nojsPage=await nojs.newPage();await nojsPage.goto(home+'assets/commons-bar-stool/');await nojsPage.locator('.fbx-download > summary').click();assert.ok(await nojsPage.locator('.fbx-download a.button').isVisible());assert.ok(await nojsPage.locator('.fbx-download a.direct-download').isVisible());await nojs.close();
 assert.deepEqual(errors,[]);await writeFile('test-results/fbx-minimal-browser-evidence.json',JSON.stringify(evidence,null,2)+'\n');
 console.log('PASS:137 FBX detail links,6 real browser downloads, mobile and no-JS links.');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
