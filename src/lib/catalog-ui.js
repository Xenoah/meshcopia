import {renderTextureTiles,textureWrap,textureSize} from './texture.js';
import {primaryDownloadBytes} from './downloads.mjs';
export function filterAssets(assets, {query='',type='all',category='all',sort='newest'}={}) {
 const terms=query.trim().toLowerCase().split(/\s+/).filter(Boolean);
 return assets.filter(a=>(type==='all'||a.type===type)&&(category==='all'||a.category===category)&&terms.every(term=>`${a.title} ${a.titleEn} ${(a.tags||[]).join(' ')} ${(a.usages||[]).flatMap(u=>[u.project,u.context,u.sourceUrl,u.sourceRef,...(u.sourcePaths||[]),...(u.selectors||[])]).filter(Boolean).join(' ')} ${[...(a.files||[]),...(a.downloads?.delivery?.files||[])].map(f=>f.format).join(' ')}`.toLowerCase().includes(term))).sort((a,b)=>sort==='name'?a.titleEn.localeCompare(b.titleEn):sort==='size'?primaryDownloadBytes(a)-primaryDownloadBytes(b):b.updated.localeCompare(a.updated)||a.type.localeCompare(b.type)||a.titleEn.localeCompare(b.titleEn));
}
export function initCatalog(){
 const assets=JSON.parse(document.getElementById('catalog-data').textContent);
 const search=document.getElementById('asset-search'),sort=document.getElementById('asset-sort'),grid=document.getElementById('asset-grid');
 const cards=new Map([...grid.children].map(el=>[el.querySelector('[data-preview]').dataset.preview,el]));
 let state={query:'',type:'all',category:'all',sort:'newest'};
 function readURL(){const p=new URLSearchParams(location.search);state={query:p.get('q')||'',type:['model','texture'].includes(p.get('type'))?p.get('type'):'all',category:p.get('category')||'all',sort:['name','size'].includes(p.get('sort'))?p.get('sort'):'newest'};search.value=state.query;sort.value=state.sort;}
 function render(sync=true){
  const result=filterAssets(assets,state),visible=new Set(result.map(a=>a.id));
  for(const [id,el] of cards)el.hidden=!visible.has(id);
  result.forEach(a=>grid.append(cards.get(a.id)));
  document.getElementById('result-count').textContent=document.documentElement.lang==='en'?`${result.length} assets`:`${result.length} 件の素材`;
  document.getElementById('empty-state').hidden=!!result.length;
  document.querySelectorAll('[data-type-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.typeFilter===state.type)));
  document.querySelectorAll('.category-buttons [data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.category===state.category)));
  if(sync){const p=new URLSearchParams();if(state.query)p.set('q',state.query);if(state.type!=='all')p.set('type',state.type);if(state.category!=='all')p.set('category',state.category);if(state.sort!=='newest')p.set('sort',state.sort);history.replaceState(null,'',`${location.pathname}${p.size?'?'+p:''}${location.hash}`);}
 }
 search.addEventListener('input',()=>{state.query=search.value;render()});sort.addEventListener('change',()=>{state.sort=sort.value;render()});
 document.querySelectorAll('[data-type-filter]').forEach(b=>b.addEventListener('click',()=>{state.type=b.dataset.typeFilter;state.category='all';render()}));
 document.querySelectorAll('.category-buttons [data-category]').forEach(b=>b.addEventListener('click',()=>{state.category=b.dataset.category;render()}));
 const reset=()=>{state={query:'',type:'all',category:'all',sort:'newest'};search.value='';sort.value='newest';render()};
 document.getElementById('clear-filters').addEventListener('click',reset);document.querySelector('[data-reset]').addEventListener('click',reset);
 window.addEventListener('popstate',()=>{readURL();render(false)});document.addEventListener('meshcopia-language',()=>render(false));
 document.addEventListener('keydown',e=>{if(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)&&!document.activeElement.isContentEditable){e.preventDefault();search.focus()}});
 readURL();render(false);
 const dialog=document.getElementById('quick-dialog'),root=dialog.querySelector('.model-viewer-3d');
 document.querySelectorAll('[data-preview]').forEach(button=>button.addEventListener('click',()=>{
  const a=assets.find(a=>a.id===button.dataset.preview);document.getElementById('quick-title').textContent=document.documentElement.lang==='en'?a.titleEn:a.title;
  document.getElementById('quick-details').href=new URL(a.pageUrl).pathname;
  document.getElementById('quick-model').hidden=a.type!=='model';const texture=document.getElementById('quick-texture');texture.hidden=a.type!=='texture';
  const wrap=textureWrap(a),en=document.documentElement.lang==='en';
  dialog.querySelector('.dialog-footer p').textContent=a.type==='model'?(en?'Drag to orbit · Scroll to zoom':'ドラッグで回転・スクロールで拡大'):wrap==='clamp'?(en?'Atlas · Clamp · original aspect ratio':'アトラス · Clamp · 元の縦横比'):wrap==='mirror'?(en?'2 × 2 · Mirrored repeat':'2 × 2 · 鏡像リピート'):(en?'2 × 2 · Repeat':'2 × 2 · 通常リピート');
  dialog.showModal();
  if(a.type==='model'){root.dataset.modelSrc=new URL(a.previewUrl).pathname;root.dataset.modelType=a.preview.split('.').pop().replace('stp','step');root.dataset.modelName=a.title;root.querySelector('canvas').setAttribute('aria-label',`${a.title} 3Dプレビュー`);window.dispatchEvent(new CustomEvent('archive-model-viewer-activate',{detail:{root}}));}
  else {const [width,height]=textureSize(a);renderTextureTiles(texture,{url:new URL(a.mapUrls.baseColor).pathname,wrapMode:wrap,count:2,width,height,title:a.title});}
 }));
 document.getElementById('quick-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
 dialog.addEventListener('close',()=>window.dispatchEvent(new CustomEvent('meshcopia-viewer-pause',{detail:{root}})));
}
