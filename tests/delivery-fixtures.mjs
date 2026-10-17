// Synthetic bytes only. Never used by a production build or publication proof.
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {DELIVERY_POLICY} from '../src/lib/delivery.mjs';
export const hash=b=>createHash('sha256').update(b).digest('hex');
export function completeTexture(a) {
 a.type='texture';
 const d=a.downloads.minimal;
 Object.assign(d,{schemaVersion:1,packageVersion:'1.0.0',bytes:200,sha256:hash('archive'),
  url:`https://github.com/Xenoah/meshcopia/releases/download/fixture-v1.0.0/${a.id}-${a.version}-minimal-1.0.0.zip`,
  verification:{state:'published-verified',releaseTag:'fixture-v1.0.0',archiveSha256:hash('archive')}});
 return a;
}
export function transport(payload) {const raw=Buffer.from(payload),packed=gzipSync(raw),manifest=Buffer.from(JSON.stringify({schemaVersion:1,bytes:raw.length,sha256:hash(raw),chunks:[{bytes:raw.length,sha256:hash(raw),packedBytes:packed.length,packedSha256:hash(packed)}]}));return {raw,packed,manifest,fetch:{kind:'chunks-gzip-v1',url:`https://xenoah.github.io/meshcopia/download-data/${hash(manifest)}.json`,bytes:manifest.length,sha256:hash(manifest)}};}
export function fixtureFetch(payload='model') {const t=transport(payload);return async url=>new Response(url.endsWith('.json')?t.manifest:t.packed);}
export function model(id='chair',payload='model') {
 const source={name:'preview.glb',bytes:7,sha256:hash('preview'),url:`https://xenoah.github.io/meshcopia/assets/${id}/source/preview.glb`};
 const text=`${id} by Fixture creator\nCC BY 4.0\n`,root='https://github.com/Xenoah/meshcopia/releases/download/fbx-minimal-v1.0.0/';
 const a={id,title:id,titleEn:id,tags:[],updated:'2026-10-17',status:'public',type:'model',version:'1.0.0',files:[source],downloads:{}};
 a.downloads.delivery={schemaVersion:1,id,assetVersion:a.version,packageVersion:'1.0.0',contentPolicy:DELIVERY_POLICY,sourceFiles:[{...source}],
  files:[{name:`${id}.fbx`,format:'FBX',bytes:Buffer.byteLength(payload),sha256:hash(payload),url:root+id+'.fbx',fetch:transport(payload).fetch}],
  archive:{filename:`${id}-1.0.0-fbx-minimal-1.0.0.zip`,url:root+`${id}-1.0.0-fbx-minimal-1.0.0.zip`,bytes:100,sha256:hash('zip')},
  notice:{filename:'LICENSE.txt',text,bytes:Buffer.byteLength(text),sha256:hash(text)},verification:{state:'published-verified',releaseTag:'fbx-minimal-v1.0.0'}};
 return a;
}
