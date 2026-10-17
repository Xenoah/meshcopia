import {completeTexture} from './delivery-fixtures.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {formatBytes,bundleSizeSummary} from '../src/lib/file-size.mjs';
import {planBundle,POLICY} from '../src/lib/batch-download.mjs';
// Deterministic UI handler tests, not a substitute for real mobile/browser QA.
function asset(id){const text='CC BY 4.0\n',f={name:'model.glb',bytes:10,sha256:'1'.repeat(64),url:`https://xenoah.github.io/meshcopia/assets/${id}/source/model.glb`};return completeTexture({id,title:id,titleEn:id,status:'public',version:'1.0.0',files:[f],downloads:{minimal:{id,assetVersion:'1.0.0',contentPolicy:POLICY,noticeFile:'LICENSE.txt',sourceFiles:[f],notice:{filename:'LICENSE.txt',text,bytes:text.length,sha256:'2'.repeat(64)}}}});}
async function setup(){
 const events=new Map(),elements=[],assets=[asset('one'),asset('two')];
 const document={documentElement:{lang:'ja'},addEventListener:(n,f)=>events.set(n,f)};
 class Element{
  constructor(tag){this.tag=tag;this.children=[];this.listeners=new Map();this.hidden=false;elements.push(this);}
  append(...children){this.children.push(...children)} before(){} setAttribute(){} removeAttribute(name){delete this[name]}
  replaceChildren(...children){this.children=children} querySelectorAll(selector){return selector==='button'?this.children.flatMap(e=>[...(e.tag==='button'?[e]:[]),...e.querySelectorAll(selector)]):[]}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null}
  addEventListener(name,handler){this.listeners.set(name,handler)} emit(name){return this.listeners.get(name)?.()}
  focus(){document.activeElement=this} showModal(){this.open=true} close(){this.open=false;this.emit('close')}
 }
 const grid=new Element('grid'),catalog=new Element('script');catalog.textContent=JSON.stringify(assets);
 document.body=new Element('body');document.createElement=tag=>new Element(tag);document.getElementById=id=>id==='asset-grid'?grid:id==='catalog-data'?catalog:elements.find(e=>e.id===id);
 const source=(await readFile(new URL('../src/lib/batch-download-ui.js',import.meta.url),'utf8')).replace(/^import .*;\n/gm,'').replace('export function initBatchDownload','function initBatchDownload');
 const globals={document,window:{addEventListener(){}},history:{state:null,pushState(){},back(){}},sessionStorage:{getItem:()=>JSON.stringify(['one','two']),setItem(){}},location:{href:'https://xenoah.github.io/meshcopia/'},bundleLimit:()=>128*1024**2,formatBytes,bundleSizeSummary,planBundle,minimalDownloadReadiness:()=>({ready:true}),buildBundle:async()=>new Blob([new Uint8Array(1234)]),AbortController,URL};
 new Function(...Object.keys(globals),source+'\ninitBatchDownload();')(...Object.values(globals));
 const dialog=document.getElementById('batch-selection-dialog'),counter=document.getElementById('batch-download-bar').children[0];
 return {document,dialog,counter,events,clear:dialog.children[3],download:dialog.children[4],save:dialog.children[6],list:dialog.children[2]};
}
test('small multi-selection switches estimate to actual Blob size; language, remove and clear reset it',async()=>{
 const x=await setup();assert.match(x.counter.textContent,/2 件選択 · ZIP 約 [1-9]\d* B/);
 x.document.documentElement.lang='en';x.events.get('meshcopia-language')();assert.match(x.counter.textContent,/2 selected · ZIP est\./);
 await x.download.emit('click');assert.equal(x.counter.textContent,'2 selected · ZIP 1.2 KB');assert.equal(x.save.hidden,false);
 await x.list.children[0].children[1].emit('click');assert.match(x.counter.textContent,/1 selected · ZIP est\./);assert.equal(x.save.hidden,true);assert.equal(x.save.href,undefined);
 x.clear.emit('click');assert.equal(x.counter.textContent,'0 selected');assert.equal(x.download.disabled,true);
});
