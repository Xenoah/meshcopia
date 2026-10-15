// Browser-only STORE ZIP builder. No archive fetches, proxy, or runtime CDN.
export const POLICY='asset-files-required-dependencies-single-notice-v1';
const encoder=new TextEncoder();
export class BundleError extends Error { constructor(code,detail=''){super(detail||code);this.code=code;} }
const fail=(code,detail)=>{throw new BundleError(code,detail)};
export function safePath(name){
 if(typeof name!=='string'||!name||name.length>220||name!==name.normalize('NFC')||/[\\\x00-\x1f\x7f:< >"|?*]/.test(name)||name.startsWith('/')||name.split('/').some(p=>!p||p==='.'||p==='..'||/[. ]$/.test(p)||/^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)/i.test(p)))fail('path',String(name));
 return name;
}
function metadata(file){if(!Number.isSafeInteger(file?.bytes)||file.bytes<0||!/^[a-f0-9]{64}$/.test(file.sha256||''))fail('metadata');}
export function bundleLimit(nav=globalThis.navigator){return /Android|iPhone|iPad|Mobile/i.test(nav?.userAgent||'')||(nav?.deviceMemory&&nav.deviceMemory<=4)?48*1024**2:128*1024**2;}
export function planBundle(assets,{limit=bundleLimit(),baseURL=globalThis.location?.href||'https://xenoah.github.io/meshcopia/'}={}){
 if(!assets.length||assets.length>50)fail('count');
 const ids=new Set(),paths=new Set(),entries=[],notices=[];let bytes=0;
 for(const a of assets){
  if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(a.id)||ids.has(a.id))fail('duplicate');ids.add(a.id);
  const d=a.downloads?.minimal;
  if(a.status!=='public'||!d||d.id!==a.id||d.assetVersion!==a.version||d.contentPolicy!==POLICY||d.noticeFile!=='LICENSE.txt'||!Array.isArray(d.sourceFiles)||!d.sourceFiles.length||d.sourceFiles.length!==a.files?.length)fail('unavailable',a.id);
  const inventory=new Map(a.files.map(f=>[f.name,f]));if(inventory.size!==a.files.length)fail('duplicate');
  for(const source of d.sourceFiles){
   metadata(source);safePath(source.name);const f=inventory.get(source.name);
   if(!f||f.bytes!==source.bytes||f.sha256!==source.sha256||/\.(zip|js|py|ts|sh|exe|json|md)$/i.test(source.name)||source.name.toLowerCase()==='license.txt')fail('metadata');
   const url=new URL(f.url,baseURL),base=new URL(baseURL);
   if(url.username||url.password||!((url.origin===base.origin&&url.pathname.startsWith(`${new URL('.',base).pathname}assets/${a.id}/source/`))||(url.protocol==='https:'&&url.hostname==='raw.githubusercontent.com'&&url.pathname.startsWith('/Xenoah/meshcopia/'))))fail('url');
   add({...source,name:`${a.id}/${source.name}`,url:url.href});
  }
  const notice=d.notice;metadata(notice);if(notice.filename!=='LICENSE.txt'||typeof notice.text!=='string'||notice.bytes>32768)fail('notice');
  const data=encoder.encode(notice.text);if(data.byteLength!==notice.bytes)fail('notice');notices.push({id:a.id,data,sha256:notice.sha256});
 }
 const noticeData=encoder.encode(notices.map(n=>`=== ${n.id} ===\n${new TextDecoder().decode(n.data)}`).join('\n\n'));
 add({name:'LICENSE.txt',bytes:noticeData.length,data:noticeData,notices});
 function add(entry){const path=safePath(entry.name).toLowerCase();if(paths.has(path))fail('duplicate');paths.add(path);bytes+=entry.bytes;if(bytes>limit)fail('size');entries.push(entry);}
 if(entries.length>2000)fail('count');return {entries,bytes,limit};
}
const table=Uint32Array.from({length:256},(_,n)=>{let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;return c>>>0});
function crc32(data){let c=0xffffffff;for(const b of data)c=table[(c^b)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
function checkAbort(signal){if(signal?.aborted)throw new DOMException('Cancelled','AbortError');}
function header(size,fields){const data=new Uint8Array(size),v=new DataView(data.buffer);for(const [offset,value,width] of fields)width===2?v.setUint16(offset,value,true):v.setUint32(offset,value,true);return data;}
export async function buildBundle(plan,{signal,fetchImpl=globalThis.fetch,cryptoImpl=globalThis.crypto,onProgress=()=>{}}={}){
 if(!cryptoImpl?.subtle)fail('unsupported');
 const parts=[],central=[];let offset=0,done=0,index=0;
 for(const entry of plan.entries){
  checkAbort(signal);let data=entry.data;
  if(!data){
   let response;try{response=await fetchImpl(entry.url,{signal,mode:'cors',credentials:'omit',cache:'no-cache',redirect:'follow',referrerPolicy:'no-referrer'});}catch(e){if(signal?.aborted)throw e;fail('network',entry.name);}
   if(!response.ok||response.type==='opaque'||!response.body)fail('network',entry.name);
   const reader=response.body.getReader();data=new Uint8Array(entry.bytes);let position=0;
   try{while(true){checkAbort(signal);const {done:ended,value}=await reader.read();if(ended)break;if(position+value.byteLength>entry.bytes)fail('integrity',entry.name);data.set(value,position);position+=value.byteLength;onProgress({bytes:done+position,total:plan.bytes,index,count:plan.entries.length});}if(position!==entry.bytes)fail('integrity',entry.name);}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
  }
  checkAbort(signal);const hash=[...new Uint8Array(await cryptoImpl.subtle.digest('SHA-256',data))].map(b=>b.toString(16).padStart(2,'0')).join('');
  if(entry.notices){for(const n of entry.notices){const h=[...new Uint8Array(await cryptoImpl.subtle.digest('SHA-256',n.data))].map(b=>b.toString(16).padStart(2,'0')).join('');if(h!==n.sha256)fail('integrity','LICENSE.txt');}}else if(hash!==entry.sha256)fail('integrity',entry.name);checkAbort(signal);
  const name=encoder.encode(entry.name),crc=crc32(data),size=data.byteLength;
  const local=header(30,[[0,0x04034b50,4],[4,20,2],[6,0x800,2],[12,33,2],[14,crc,4],[18,size,4],[22,size,4],[26,name.length,2]]);
  const directory=header(46,[[0,0x02014b50,4],[4,20,2],[6,20,2],[8,0x800,2],[14,33,2],[16,crc,4],[20,size,4],[24,size,4],[28,name.length,2],[42,offset,4]]);
  parts.push(local,name,data);central.push(directory,name);offset+=30+name.length+size;done+=size;index++;onProgress({bytes:done,total:plan.bytes,index,count:plan.entries.length});
  // Yield so cancellation and mobile painting remain responsive between files.
  await new Promise(resolve=>setTimeout(resolve,0));
 }
 checkAbort(signal);const centralSize=central.reduce((sum,p)=>sum+p.length,0);
 const end=header(22,[[0,0x06054b50,4],[8,index,2],[10,index,2],[12,centralSize,4],[16,offset,4]]);
 return new Blob([...parts,...central,end],{type:'application/zip'});
}
