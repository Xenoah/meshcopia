import {planBundle,buildBundle,bundleLimit} from './batch-download.mjs';
import {minimalDownloadReadiness} from './downloads.mjs';
import {formatBytes,bundleSizeSummary} from './file-size.mjs';
import './batch-download.css';
export function initBatchDownload(){
 const grid=document.getElementById('asset-grid'),catalog=document.getElementById('catalog-data');
 if(!grid||!catalog||document.getElementById('batch-download-bar'))return;
 const assets=JSON.parse(catalog.textContent),byId=new Map(assets.map(a=>[a.id,a])),selected=new Set(),controls=new Map();
 const key='meshcopia-selection-v1';let controller=null,blobURL=null,message='',progressValue=null,finalBytes=null;
 const english=()=>document.documentElement.lang==='en';const t=(ja,en)=>english()?en:ja;
 const bar=document.createElement('section');bar.id='batch-download-bar';bar.className='batch-download-bar';
 const count=document.createElement('button'),clear=document.createElement('button'),download=document.createElement('button'),cancel=document.createElement('button'),save=document.createElement('a'),status=document.createElement('p'),help=document.createElement('p'),progress=document.createElement('progress');
 clear.type=download.type=cancel.type='button';download.className='button primary';clear.className=cancel.className='button';save.className='button primary';status.role='status';status.setAttribute('aria-live','polite');progress.max=100;progress.hidden=true;save.hidden=true;
 const dialog=document.createElement('dialog'),heading=document.createElement('h2'),close=document.createElement('button'),list=document.createElement('ul');dialog.className='batch-dialog';dialog.id='batch-selection-dialog';heading.id='batch-selection-title';dialog.setAttribute('aria-labelledby',heading.id);close.type='button';close.className='button';dialog.append(heading,close,list,clear,download,cancel,save,progress,status,help);document.body.append(dialog);bar.append(count);grid.before(bar);count.type='button';count.className='button primary';count.setAttribute('aria-haspopup','dialog');count.setAttribute('aria-controls',dialog.id);count.addEventListener('click',()=>{if(dialog.open)return;history.pushState({...history.state,meshcopiaSelection:true},'',location.href);dialog.showModal();close.focus();});close.addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{if(history.state?.meshcopiaSelection){count.disabled=true;history.back();}else count.focus();});window.addEventListener('popstate',()=>{const restoreFocus=count.disabled;count.disabled=false;if(history.state?.meshcopiaSelection){if(!dialog.open){dialog.showModal();close.focus();}}else if(dialog.open)dialog.close();else if(restoreFocus)count.focus();});
 const ready=a=>{try{return minimalDownloadReadiness(a).ready&&!!planBundle([a]);}catch{return false;}};
 try{const saved=JSON.parse(sessionStorage.getItem(key)||'[]');if(Array.isArray(saved))saved.slice(0,50).forEach(id=>{if(byId.has(id)&&ready(byId.get(id)))selected.add(id)});}catch{}
 function invalidate(){if(blobURL){URL.revokeObjectURL(blobURL);blobURL=null;}save.hidden=true;save.removeAttribute('href');message='';progressValue=null;finalBytes=null;}
 function persist(){try{sessionStorage.setItem(key,JSON.stringify([...selected]));}catch{}}
 for(const card of grid.querySelectorAll('[data-card]')){
  const id=card.querySelector('[data-preview]')?.dataset.preview,a=byId.get(id);if(!a)continue;
  const label=document.createElement('label'),box=document.createElement('input'),text=document.createElement('span');label.className='batch-select';box.type='checkbox';box.checked=selected.has(id);box.dataset.assetSelect=id;label.append(box,text);card.append(label);controls.set(id,{box,text,label,a,available:ready(a)});
  box.addEventListener('change',()=>{if(controller)return;invalidate();if(box.checked)selected.add(id);else selected.delete(id);persist();render();});
 }
 function render(){
  const {inputBytes:bytes,zipBytes}=bundleSizeSummary([...selected].map(id=>byId.get(id)));
  const size=formatBytes(finalBytes??zipBytes,t('容量不明','Size unknown'));
  const sizeLabel=finalBytes!==null?`ZIP ${size}`:t(`ZIP 約 ${size}`,`ZIP est. ${size}`);
  count.textContent=t(`${selected.size} 件選択`,`${selected.size} selected`)+(selected.size?` · ${sizeLabel}`:'');
  heading.textContent=t('選択中の素材','Selected assets');close.textContent=t('閉じる','Close');
  if(!controller||!list.children.length){list.replaceChildren();for(const id of selected){const a=byId.get(id),li=document.createElement('li'),name=document.createElement('span'),remove=document.createElement('button');name.textContent=english()?a.titleEn:a.title;remove.type='button';remove.textContent=t('解除','Remove');remove.disabled=!!controller;remove.setAttribute('aria-label',t(`${a.title}の選択を解除`,`Remove ${a.titleEn}`));remove.addEventListener('click',()=>{selected.delete(id);invalidate();persist();render();(list.querySelector('button')||close).focus();});li.append(name,remove);list.append(li);}}list.querySelectorAll('button').forEach(b=>b.disabled=!!controller);
  bar.setAttribute('aria-label',t('選択素材を1個のZIPにまとめる','Bundle selected assets into one ZIP'));
  clear.textContent=t('選択解除','Clear selection');download.textContent=t('選択素材を1 ZIPにまとめる','Bundle selection into one ZIP');cancel.textContent=t('キャンセル','Cancel');save.textContent=t('1 ZIPを保存','Save one ZIP');
  clear.disabled=!!controller||!selected.size;download.disabled=!!controller||!selected.size;cancel.hidden=!controller;progress.hidden=!controller;progress.setAttribute('aria-label',t('ZIP作成の進捗','ZIP progress'));if(progressValue!==null)progress.value=progressValue;
  help.textContent=t(`絞り込み後も選択を保持。素材ごとのフォルダーに必要ファイル、全素材共通のLICENSE.txtを1枚。作成前はZIP容量の見積もり、作成後は実容量を表示。ZIPは無圧縮で作成します。最大50件・元ファイル${bundleLimit()/1024**2} MiB。`, `Selection stays across filters. Asset folders contain required files, with one combined LICENSE.txt. Estimated ZIP size before building; actual size afterward. The combined ZIP is uncompressed. Up to 50 assets / ${bundleLimit()/1024**2} MiB of input files.`);
  for(const [id,c] of controls){c.box.checked=selected.has(id);c.box.disabled=!!controller||!c.available||(!c.box.checked&&selected.size>=50);c.text.textContent=c.available?t('選択','Select'):t('一括準備中','Bundle unavailable');c.box.setAttribute('aria-label',t(`${c.a.title}を選択`, `Select ${c.a.titleEn}`));c.label.title=c.available?'':t('検証済みの最小パッケージがまだありません','A verified minimal package is not available yet');}
  if(bytes===null){download.disabled=true;status.textContent=t('容量を確認できません。選択を解除して再試行してください。','Size unavailable. Clear the selection and retry.');}else if(bytes>bundleLimit()){download.disabled=true;status.textContent=t('容量上限を超えています。選択数を減らしてください。','Size limit exceeded. Select fewer assets.');}else status.textContent=message;
 }
 clear.addEventListener('click',()=>{if(controller)return;selected.clear();invalidate();persist();render();});cancel.addEventListener('click',()=>controller?.abort());
 download.addEventListener('click',async()=>{
  if(controller||!selected.size)return;invalidate();controller=new AbortController();const current=controller;render();
  try{const chosen=[...selected].map(id=>byId.get(id));if(chosen.some(a=>!ready(a)))throw new Error('unavailable');const plan=planBundle(chosen);const blob=await buildBundle(plan,{signal:current.signal,onProgress:p=>{progressValue=Math.floor(p.bytes/p.total*100);message=t(`取得・検証中 ${progressValue}% (${p.index}/${p.count})`,`Fetching and verifying ${progressValue}% (${p.index}/${p.count})`);render();}});
   if(current.signal.aborted)return;finalBytes=blob.size;blobURL=URL.createObjectURL(blob);save.href=blobURL;save.download=`meshcopia-selected-${selected.size}.zip`;save.hidden=false;message=t('ZIPの準備完了。「1 ZIPを保存」を押してください。','ZIP ready. Choose “Save one ZIP”.');
  }catch(e){message=current.signal.aborted?t('キャンセルしました。選択は保持しています。','Cancelled. Your selection is kept.'):t('作成に失敗しました。ファイルは保存していません。通信または素材の整合性を確認して、再試行してください。','Could not create the ZIP. No file was saved. Check your connection or asset availability and retry.');}
  finally{controller=null;render();}
 });
 // Explicit save click preserves mobile user activation; preparation never triggers downloads.
 save.addEventListener('click',()=>{message=t('保存を開始しました。','Save started.');render();});
 window.addEventListener('pagehide',()=>{controller?.abort();invalidate();});window.addEventListener('pageshow',render);
 document.addEventListener('meshcopia-language',render);render();
}
