import {createHash} from 'node:crypto';
import {gzipSync,gunzipSync} from 'node:zlib';
import {readFile,mkdir,writeFile,lstat,mkdtemp} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const hash=b=>createHash('sha256').update(b).digest('hex');
const gear=Uint32Array.from({length:256},(_,i)=>parseInt(hash('meshcopia-chunk-v1:'+i).slice(0,8),16));
// Content-defined boundaries align again inside shared embedded images even
// when the FBX headers/geometry preceding them differ. No FBX re-export occurs.
export function* chunks(bytes) {
 let start=0,h=0;
 for(let i=0;i<bytes.length;i++){
  h=((h<<1)+gear[bytes[i]])>>>0;
  if((i-start>=65535&&!(h&131071))||i-start>=524287||i===bytes.length-1){yield bytes.subarray(start,i+1);start=i+1;h=0;}
 }
}
export async function prepareDeliveryPayloads(records,{source='.cache/fbx-delivery-payloads',site='https://xenoah.github.io/meshcopia'}={}) {
 await mkdir('.cache',{recursive:true});
 const directory=await mkdtemp('.cache/delivery-chunks-'),files=new Map(),seen=new Set();
 for(const record of records){
  const expected=record.direct,file=path.join(source,expected.sha256+'.fbx');
  assert.ok((await lstat(source)).isDirectory()&&!(await lstat(source)).isSymbolicLink());
  assert.ok((await lstat(file)).isFile()&&!(await lstat(file)).isSymbolicLink());
  const bytes=await readFile(file);assert.equal(bytes.length,expected.bytes);assert.equal(hash(bytes),expected.sha256,'Prepared FBX bytes changed');
  const segments=[];
  for(const data of chunks(bytes)){
   const packed=gzipSync(data,{level:6,mtime:0}),sha256=hash(packed);
   assert.deepEqual(gunzipSync(packed),data);
   if(!seen.has(sha256)){await writeFile(path.join(directory,sha256+'.gz'),packed,{flag:'wx'});seen.add(sha256);}
   segments.push({bytes:data.length,sha256:hash(data),packedBytes:packed.length,packedSha256:sha256});
  }
  const manifest=Buffer.from(JSON.stringify({schemaVersion:1,bytes:bytes.length,sha256:hash(bytes),chunks:segments})+'\n');
  const sha256=hash(manifest);await writeFile(path.join(directory,sha256+'.json'),manifest);
  files.set(record.id,{kind:'chunks-gzip-v1',url:`${site}/download-data/${sha256}.json`,bytes:manifest.length,sha256});
 }
 return {directory,files};
}
