import {chromium} from '@playwright/test';
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out=path.resolve(process.argv[2]??'test-results/asset-revisions/renders'),candidate=process.argv[3]??'.cache/asset-revision-qa/candidate-final';
await mkdir(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.png':'image/png','.glb':'model/gltf-binary'};
const server=createServer(async(req,res)=>{try{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));assert.ok(file.startsWith(root+path.sep));assert.ok((await stat(file)).isFile());res.setHeader('Content-Type',types[path.extname(file)]??'application/octet-stream');res.end(await readFile(file))}catch{res.writeHead(404).end()}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:['--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:900,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`http://127.0.0.1:${server.address().port}/scripts/asset-revisions/render.html`);await page.waitForFunction(()=>window.ready);
 const starters=['studio-chair','atelier-lamp','slat-bench','terracotta-planter','market-crate','garden-arch','field-terminal','wayfinding-sign'];
 const specs=[];
 for(const id of starters){
  const meta=JSON.parse(await readFile(`content/assets/${id}/asset.json`));
  for(const format of ['glb','fbx']){
   const source=format==='glb'?`/content/assets/${id}/source/${meta.preview}`:`/.cache/asset-revision-qa/original-fbx-attempt2/${id}/${id}.fbx`;
   specs.push({name:`${id}-original-${format}-outside`,source,caption:`${id} original ${format}`,direction:[2,1.4,3]});
   specs.push({name:`${id}-original-${format}-reverse`,source,caption:`${id} original ${format} rear / underside`,direction:[-2,-.5,-3]});
   if(id==='garden-arch')specs.push({name:`${id}-original-${format}-inside`,source,caption:`${id} original inside ${format}`,camera:[0,.9,0],target:[0,2.5,.05],fov:100});
   if(id==='wayfinding-sign')specs.push({name:`${id}-original-${format}-inside`,source,caption:`${id} original ring inside ${format}`,camera:[0,1.12,0],target:[0,1.22,.01],fov:110});
   if(id==='terracotta-planter')specs.push({name:`${id}-original-${format}-cavity`,source,caption:`${id} original inner wall ${format}`,camera:[0,.46,0],target:[.25,.47,0],fov:100});
   if(id==='atelier-lamp')specs.push({name:`${id}-original-${format}-cavity`,source,caption:`${id} original shade inner wall ${format}`,camera:[0,.8,0],target:[.20,.82,0],fov:100});
   if(id==='market-crate')specs.push({name:`${id}-original-${format}-cavity`,source,caption:`${id} original inside boards ${format}`,camera:[0,.25,0],target:[.35,.25,0],fov:100});
  }
 }
 for(const id of ['garden-arch','wayfinding-sign','household-two-door-refrigerator'])for(const format of ['glb','fbx']){
  const meta=JSON.parse(await readFile(`asset-revisions/repair-appliances-v1/${id}/asset.json`));
  const source=format==='glb'?`/asset-revisions/repair-appliances-v1/${id}/source/${meta.preview}`:`/${candidate}/${id}/conversion/${id}.fbx`;
  specs.push({name:`${id}-fixed-${format}-outside`,source,caption:`${id} candidate ${format}`});
  specs.push({name:`${id}-fixed-${format}-rear`,source,caption:`${id} candidate ${format} rear`,direction:[-2,1.4,-3]});
  if(id.includes('refrigerator'))specs.push({name:`${id}-fixed-${format}-interior`,source,caption:`${id} actual door opened for QA ${format}`,openDoor:true,direction:[1.3,.8,3]});
  if(id==='garden-arch')specs.push({name:`${id}-fixed-${format}-inside`,source,caption:`${id} walk-through interior ${format}`,camera:[0,.9,0],target:[0,2.5,.05],fov:100});
  if(id==='wayfinding-sign')specs.push({name:`${id}-fixed-${format}-inside`,source,caption:`${id} ring inside ${format}`,camera:[0,1.12,0],target:[0,1.22,.01],fov:110});
 }
 const washer='city-front-loading-washing-machine';
 for(const format of ['glb','fbx']){
  const source=format==='glb'?`/content/assets/${washer}/source/${washer}.glb`:`/.cache/asset-revision-qa/washer/conversion/${washer}.fbx`;
  specs.push({name:`washer-${format}-outside`,source,caption:`Existing washing machine ${format}`});
  specs.push({name:`washer-${format}-drum`,source,caption:`Existing washing machine drum ${format}`,direction:[0,.1,3]});
 }
 const result=[];
 for(const spec of specs){const row=await page.evaluate(spec=>window.renderAsset(spec),spec);assert.equal(row.negativeTransforms,0);assert.ok(row.changedPixels>300,`Empty render ${spec.name}`);await page.screenshot({path:path.join(out,spec.name+'.png')});if(spec.name.endsWith('-fixed-glb-outside'))await page.locator('canvas').screenshot({path:path.join(out,spec.name+'-thumbnail.png')});result.push({...spec,...row});console.log(spec.name,row.changedPixels)}
 assert.deepEqual(errors,[]);await writeFile(path.join(out,'render-evidence.json'),JSON.stringify({scope:'Actual GLB and FBX loaded in Three.js with every material forced to FrontSide; no double-sided workaround',renderer:'Chromium SwiftShader',renders:result},null,2)+'\n');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
