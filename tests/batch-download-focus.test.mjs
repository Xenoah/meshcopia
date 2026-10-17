// Deterministic synthetic DOM/history model of actual source handlers.
// Native dialog closure queues its `close` event; history traversal is also queued.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {formatBytes,bundleSizeSummary} from '../src/lib/file-size.mjs';
const sourcePath=new URL('../src/lib/batch-download-ui.js',import.meta.url);
async function setup(){
 const queue=[],elements=[],windowEvents=new Map(),documentEvents=new Map();
 const document={activeElement:null,documentElement:{lang:'ja'}};
 const listeners=(map,name,handler)=>map.set(name,[...(map.get(name)||[]),handler]);
 const dispatch=(map,name,detail={})=>{const event={type:name,defaultPrevented:false,preventDefault(){this.defaultPrevented=true},...detail};for(const fn of map.get(name)||[])fn(event);return event;};
 class Element{
  constructor(tag,id){Object.assign(this,{tagName:tag.toUpperCase(),id,children:[],dataset:{},listeners:new Map(),open:false,value:'',textContent:'',hidden:false});elements.push(this);}
  append(...children){this.children.push(...children)} before(){} setAttribute(){} removeAttribute(){}
  replaceChildren(...children){this.children=children} querySelectorAll(){return []} querySelector(selector){return this.children.find(e=>e.className===selector.slice(1))||null;}
  addEventListener(name,handler){listeners(this.listeners,name,handler)} emit(name,detail){return dispatch(this.listeners,name,detail);}
  focus(){if(!this.disabled)document.activeElement=this}
  set disabled(value){this._disabled=value;if(value&&document.activeElement===this)document.activeElement=null}
  get disabled(){return !!this._disabled}
  showModal(){this.previouslyFocused=document.activeElement;this.open=true}
  close(){if(!this.open)return;this.open=false;this.previouslyFocused?.focus();queue.push({type:'close',run:()=>this.emit('close')});}
  cancel(){if(!this.emit('cancel').defaultPrevented)this.close();}
 }
 const grid=new Element('div','asset-grid'),catalog=new Element('script','catalog-data');catalog.textContent='[]';
 const search=new Element('input','asset-search'),sort=new Element('select','asset-sort'),counterValue=new Element('div','result-count'),empty=new Element('div','empty-state'),reset=new Element('button','clear-filters'),reset2=new Element('button');
 const quick=new Element('dialog','quick-dialog'),root=new Element('div');root.className='model-viewer-3d';quick.append(root);new Element('button','quick-close');
 document.body=new Element('body');document.createElement=tag=>new Element(tag);document.getElementById=id=>elements.find(e=>e.id===id);
 document.querySelector=selector=>selector==='[data-reset]'?reset2:null;document.querySelectorAll=()=>[];document.addEventListener=(name,handler)=>listeners(documentEvents,name,handler);
 const window={addEventListener:(name,handler)=>listeners(windowEvents,name,handler),dispatchEvent(){}};
 const location={href:'https://xenoah.github.io/meshcopia/?q=studio+chair'};
 const setURL=url=>{const parsed=new URL(url,location.href);for(const name of ['href','search','pathname','hash'])location[name]=parsed[name];};setURL(location.href);
 const entries=[{state:null,url:location.href}];let index=0;
 const history={backs:0,get state(){return entries[index].state},pushState(state,unused,url){entries.splice(++index);entries.push({state,url:new URL(url,location.href).href});setURL(entries[index].url);},replaceState(state,unused,url){entries[index]={state,url:new URL(url,location.href).href};setURL(entries[index].url)},back(){this.backs++;queue.push({type:'traversal',run:()=>traverse(-1)})}};
 function traverse(delta){index+=delta;assert.ok(index>=0&&index<entries.length);setURL(entries[index].url);dispatch(windowEvents,'popstate');}
 const catalogSource=(await readFile(new URL('../src/lib/catalog-ui.js',import.meta.url),'utf8')).replace(/^import .*;\n/gm,'').replace(/export function /g,'function ');
 new Function('document','window','history','location',catalogSource+'\ninitCatalog();')(document,window,history,location);
 const source=(await readFile(sourcePath,'utf8')).replace(/^import .*;\n/gm,'').replace('export function initBatchDownload','function initBatchDownload');
 new Function('document','window','history','sessionStorage','location','bundleLimit','formatBytes','bundleSizeSummary',source+'\ninitBatchDownload();')(document,window,history,{getItem:()=>null,setItem(){}},location,()=>128*1024**2,formatBytes,bundleSizeSummary);
 const dialog=document.getElementById('batch-selection-dialog'),counter=document.getElementById('batch-download-bar').children[0],close=dialog.children[1];
 const flush=type=>{const at=queue.findIndex(item=>item.type===type);assert.ok(at>=0,`Expected queued ${type}`);queue.splice(at,1)[0].run();};
 const fill=value=>{search.focus();search.value=value;search.emit('input');};
 const open=()=>{counter.focus();counter.emit('click');};
 return {document,dialog,counter,close,history,search,location,queue,flush,fill,open,back:()=>traverse(-1),forward:()=>traverse(1),pop:()=>dispatch(windowEvents,'popstate')};
}


for(const method of ['Close','Escape'])test(`${method} keeps the catalog inert until history settles, then preserves the next search`,async()=>{
 const x=await setup();x.open();assert.equal(x.search.value,'studio chair');
 if(method==='Close')x.close.emit('click');else x.dialog.cancel();
 assert.equal(x.dialog.open,true,'Modal must remain open during asynchronous Back');
 assert.equal(x.counter.disabled,true,'Opener is synchronously gated before traversal');
 assert.equal(x.history.backs,1);assert.equal(x.document.activeElement,x.close);
 x.close.emit('click');x.dialog.cancel();assert.equal(x.history.backs,1,'Repeated dismissals cannot queue extra Back calls');
 x.flush('traversal');assert.equal(x.dialog.open,false);assert.equal(x.counter.disabled,false);assert.equal(x.document.activeElement,x.counter);
 x.fill('');assert.equal(x.search.value,'');assert.equal(x.location.search,'');
 x.flush('close');assert.equal(x.search.value,'');assert.equal(x.location.search,'');
 assert.equal(x.document.activeElement,x.search,'Queued close event cannot steal later input focus');
 assert.equal(x.history.backs,1);assert.equal(x.queue.length,0);
});

test('browser Back closes and focuses opener; immediate Forward survives the queued close event',async()=>{
 const x=await setup();x.open();x.back();assert.equal(x.dialog.open,false);assert.equal(x.document.activeElement,x.counter);
 x.forward();assert.equal(x.dialog.open,true);assert.equal(x.document.activeElement,x.close);
 x.flush('close');assert.equal(x.dialog.open,true);assert.equal(x.document.activeElement,x.close);assert.equal(x.history.backs,0);
 x.back();x.flush('close');assert.equal(x.dialog.open,false);assert.equal(x.document.activeElement,x.counter);
 x.forward();assert.equal(x.dialog.open,true);assert.equal(x.document.activeElement,x.close);
});

test('queued close after browser Back cannot consume an immediate new selection-dialog entry',async()=>{
 const x=await setup();x.open();x.back();x.open();assert.equal(x.dialog.open,true);
 x.flush('close');assert.equal(x.dialog.open,true);assert.equal(x.counter.disabled,false);
 assert.equal(x.history.backs,0);assert.equal(x.document.activeElement,x.close);
});

test('unrelated popstate does not steal focus when selection dialog is already closed',async()=>{
 const x=await setup();x.fill('new query');x.pop();assert.equal(x.document.activeElement,x.search);
 assert.equal(x.search.value,'new query');assert.equal(x.dialog.open,false);assert.equal(x.history.backs,0);
});

test('dismissal without a selection history entry closes directly without navigating away',async()=>{
 const x=await setup();x.open();x.history.replaceState(null,'',x.location.href);x.close.emit('click');
 assert.equal(x.dialog.open,false);assert.equal(x.counter.disabled,false);assert.equal(x.document.activeElement,x.counter);
 x.flush('close');assert.equal(x.history.backs,0);
});
