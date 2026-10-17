import {deliveryReadiness} from './delivery.mjs';
import {minimalDownloadReadiness} from './downloads.mjs';
// Browser-only STORE ZIP builder. Fetch only the consumer manifest's payloads.
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
  const model=a.type==='model';
  const readiness=model?deliveryReadiness(a):minimalDownloadReadiness(a);
  if(!readiness.ready)fail('unavailable',a.id);
  const d=model?{...readiness.download,sourceFiles:readiness.download.files,noticeFile:'LICENSE.txt'}:readiness.download;
  const payloads=model?d.files:a.files;
  if(a.status!=='public'||!d||d.id!==a.id||d.assetVersion!==a.version||(!model&&d.contentPolicy!==POLICY)||d.noticeFile!=='LICENSE.txt'||!Array.isArray(d.sourceFiles)||!d.sourceFiles.length||d.sourceFiles.length!==payloads?.length)fail('unavailable',a.id);
  const inventory=new Map(payloads.map(f=>[f.name,f]));if(inventory.size!==payloads.length)fail('duplicate');
  for(const source of d.sourceFiles){
   metadata(source);safePath(source.name);const f=inventory.get(source.name);
   if(!f||f.bytes!==source.bytes||f.sha256!==source.sha256||/\.(zip|js|py|ts|sh|exe|json|md)$/i.test(source.name)||source.name.toLowerCase()==='license.txt')fail('metadata');
   const base=new URL(baseURL),url=new URL(model?f.fetch.url:f.url,baseURL);
   if(model){const expectedRoot=new URL('.',base).pathname+'download-data/';if(!url.pathname.startsWith(expectedRoot))fail('url');url.protocol=base.protocol;url.host=base.host;}
   if(!model&&(url.username||url.password||!((url.origin===base.origin&&url.pathname.startsWith(`${new URL('.',base).pathname}assets/${a.id}/source/`))||(url.protocol==='https:'&&url.hostname==='raw.githubusercontent.com'&&url.pathname.startsWith('/Xenoah/meshcopia/')))))fail('url');
   add({...source,name:`${a.id}/${source.name}`,url:url.href,...(model?{transport:f.fetch}:{})});
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
   if(entry.transport){
    const manifestBytes=await fetchBytes(entry.url,entry.transport.bytes,{signal,fetchImpl});
    await verifyHash(manifestBytes,entry.transport.sha256,cryptoImpl);
    let manifest;try{manifest=JSON.parse(new TextDecoder().decode(manifestBytes));}catch{fail('integrity');}
    if(manifest.schemaVersion!==1||manifest.bytes!==entry.bytes||manifest.sha256!==entry.sha256||!Array.isArray(manifest.chunks)||!manifest.chunks.length||manifest.chunks.length>4096)fail('integrity');
    let total=0;for(const c of manifest.chunks){
     if(!Number.isSafeInteger(c.bytes)||c.bytes<=0||c.bytes>524288||!Number.isSafeInteger(c.packedBytes)||c.packedBytes<=0||c.packedBytes>525000||!(/^[a-f0-9]{64}$/.test(c.sha256))||!(/^[a-f0-9]{64}$/.test(c.packedSha256)))fail('integrity');
     total+=c.bytes;
    }
    if(total!==entry.bytes)fail('integrity');
    if(typeof DecompressionStream==='undefined')fail('unsupported');
    data=new Uint8Array(entry.bytes);let next=0,complete=0,failed=false;
    const offsets=[];total=0;for(const c of manifest.chunks){offsets.push(total);total+=c.bytes;}
    // At most four bounded compressed chunks plus the planned output buffer.
    const jobs=Array.from({length:Math.min(4,manifest.chunks.length)},async()=>{
     try{while(!failed&&next<manifest.chunks.length){
      const index=next++,c=manifest.chunks[index];checkAbort(signal);
      const url=new URL(c.packedSha256+'.gz',entry.url).href;
      const packed=await fetchBytes(url,c.packedBytes,{signal,fetchImpl});await verifyHash(packed,c.packedSha256,cryptoImpl);
      const expanded=await readBounded(new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip')),c.bytes,signal);
      await verifyHash(expanded,c.sha256,cryptoImpl);checkAbort(signal);data.set(expanded,offsets[index]);complete+=c.bytes;
      onProgress({bytes:done+complete,total:plan.bytes,index:0,count:plan.entries.length});
     }}catch(error){failed=true;throw error;}
    });
    // Await all workers on failure: an old job must never race a retry's UI.
    const results=await Promise.allSettled(jobs);const error=results.find(r=>r.status==='rejected');if(error)throw error.reason;
   }else data=await fetchBytes(entry.url,entry.bytes,{signal,fetchImpl,onProgress:position=>onProgress({bytes:done+position,total:plan.bytes,index,count:plan.entries.length})});
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

async function verifyHash(data,expected,cryptoImpl){const actual=[...new Uint8Array(await cryptoImpl.subtle.digest('SHA-256',data))].map(b=>b.toString(16).padStart(2,'0')).join('');if(actual!==expected)fail('integrity');}
async function readBounded(stream,length,signal,onProgress=()=>{}){
 const reader=stream.getReader(),data=new Uint8Array(length);let position=0;
 try{while(true){checkAbort(signal);const {done,value}=await reader.read();if(done)break;if(position+value.byteLength>length)fail('integrity');data.set(value,position);position+=value.byteLength;onProgress(position);}if(position!==length)fail('integrity');return data;}
 finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
}
async function fetchBytes(url,length,{signal,fetchImpl,onProgress}){
 let response;try{response=await fetchImpl(url,{signal,mode:'cors',credentials:'omit',cache:'no-cache',redirect:'error',referrerPolicy:'no-referrer'});}catch(e){if(signal?.aborted)throw e;fail('network');}
 if(!response.ok||response.type==='opaque'||!response.body)fail('network');
 return readBounded(response.body,length,signal,onProgress);
}
