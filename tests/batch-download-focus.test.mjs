import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {formatBytes,bundleSizeSummary} from '../src/lib/file-size.mjs';

// Execute the real UI handlers in a small deterministic DOM/history model.
// A disabled focused button loses focus, matching the CI browser regression.
async function setup(){
 const events=new Map(),elements=[];
 const document={activeElement:null,documentElement:{lang:'ja'},addEventListener(){}};
 class Element{
  constructor(tag){this.tag=tag;this.children=[];this.listeners=new Map();this.open=false;elements.push(this);}
  append(...children){this.children.push(...children)} before(){} setAttribute(){} removeAttribute(){}
  replaceChildren(...children){this.children=children} querySelectorAll(){return []} querySelector(){return null}
  addEventListener(name,handler){this.listeners.set(name,handler)} emit(name){this.listeners.get(name)?.()}
  focus(){if(!this.disabled)document.activeElement=this}
  set disabled(value){this._disabled=value;if(value&&document.activeElement===this)document.activeElement=null}
  get disabled(){return !!this._disabled}
  showModal(){this.open=true} close(){this.open=false;this.emit('close')}
 }
 const grid=new Element('grid'),catalog=new Element('script');catalog.textContent='[]';
 document.body=new Element('body');document.createElement=tag=>new Element(tag);
 document.getElementById=id=>id==='asset-grid'?grid:id==='catalog-data'?catalog:elements.find(e=>e.id===id);
 const window={addEventListener:(name,handler)=>events.set(name,handler)};
 const history={state:null,backs:0,pushState(state){this.state=state},back(){this.backs++}};
 const source=(await readFile(new URL('../src/lib/batch-download-ui.js',import.meta.url),'utf8')).replace(/^import .*;\n/gm,'').replace('export function initBatchDownload','function initBatchDownload');
 new Function('document','window','history','sessionStorage','location','bundleLimit','formatBytes','bundleSizeSummary',source+'\ninitBatchDownload();')(document,window,history,{getItem:()=>null,setItem(){}},{href:'https://xenoah.github.io/meshcopia/'},()=>128*1024**2,formatBytes,bundleSizeSummary);
 const dialog=document.getElementById('batch-selection-dialog'),counter=document.getElementById('batch-download-bar').children[0];
 return {document,dialog,counter,history,pop:()=>events.get('popstate')()};
}
test('closing the selection dialog restores focus only after back traversal re-enables the opener',async()=>{
 const x=await setup();x.counter.focus();x.counter.emit('click');assert.equal(x.dialog.open,true);
 x.dialog.close();assert.equal(x.history.backs,1);assert.equal(x.counter.disabled,true);
 x.history.state=null;x.pop();assert.equal(x.counter.disabled,false);assert.equal(x.document.activeElement,x.counter);
 x.counter.emit('click');assert.equal(x.dialog.open,true,'Opener works again after Escape/Close');
});
test('browser Back closes and focuses opener; Forward reopens and focuses Close',async()=>{
 const x=await setup();x.counter.emit('click');x.history.state=null;x.pop();
 assert.equal(x.dialog.open,false);assert.equal(x.document.activeElement,x.counter);assert.equal(x.history.backs,0);
 x.history.state={meshcopiaSelection:true};x.pop();assert.equal(x.dialog.open,true);assert.equal(x.document.activeElement,x.dialog.children[1]);
});
