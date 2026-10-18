import {isFbxReleaseTag} from './fbx-minimal-downloads.mjs';
// Publisher-generated consumer inventory, separate from preview/original files.
export const DELIVERY_POLICY = 'fbx-required-textures-single-notice-v1';
const hash = /^[a-f0-9]{64}$/;
const size = n => Number.isSafeInteger(n) && n > 0;
const inventory = files => JSON.stringify(files.map(({name,bytes,sha256})=>({name,bytes,sha256})).sort((a,b)=>a.name.localeCompare(b.name,'en')));
const validInventory=files=>Array.isArray(files)&&files.length>0&&new Set(files.map(f=>f?.name)).size===files.length&&files.every(f=>f&&typeof f.name==='string'&&size(f.bytes)&&hash.test(f.sha256));
const safe = name => typeof name === 'string' && !/[\\\x00-\x20:?#]/.test(name) && name.split('/').every(p=>p && p!=='.' && p!=='..');
export function deliveryReadiness(asset) {
 const d=asset?.downloads?.delivery, fail=reason=>({ready:false,reason});
 if(asset?.type!=='model'||asset.status!=='public'||!d)return fail('absent');
 if(d.schemaVersion!==1||d.id!==asset.id||d.assetVersion!==asset.version||d.contentPolicy!==DELIVERY_POLICY||!/^\d+\.\d+\.\d+$/.test(d.packageVersion))return fail('identity');
 if(!validInventory(d.sourceFiles)||!validInventory(asset.files)||inventory(d.sourceFiles)!==inventory(asset.files))return fail('source-inventory');
 const tag=d.verification?.releaseTag;
 if(d.verification?.state!=='published-verified'||!isFbxReleaseTag(tag))return fail('verification');
 const root=`https://github.com/Xenoah/meshcopia/releases/download/${tag}/`;
 if(!size(d.archive?.bytes)||!hash.test(d.archive.sha256)||d.archive.filename!==`${asset.id}-${asset.version}-fbx-minimal-${d.packageVersion}.zip`||d.archive.url!==root+d.archive.filename)return fail('archive');
 if(!validInventory(d.files)||new Set(d.files.map(f=>f.name.toLowerCase())).size!==d.files.length)return fail('files');
 if(d.files.filter(f=>/\.fbx$/i.test(f.name)).length!==1)return fail('fbx');
 for(const f of d.files){
  if(!safe(f.name)||!size(f.bytes)||!hash.test(f.sha256)||!(/\.(fbx|png|jpe?g|webp|tga|tiff?|exr)$/i.test(f.name)))return fail('files');
  if(f.url!==root+f.name||f.fetch?.kind!=='chunks-gzip-v1'||!size(f.fetch.bytes)||f.fetch.bytes>1048576||!hash.test(f.fetch.sha256)||!new RegExp('^https://xenoah\\.github\\.io(?:/[a-zA-Z0-9_-]+)*/download-data/'+f.fetch.sha256+'\\.json$').test(f.fetch.url))return fail('transport');
 }
 const n=d.notice;
 if(n?.filename!=='LICENSE.txt'||typeof n.text!=='string'||!n.text.trim()||!size(n.bytes)||n.bytes>32768||new TextEncoder().encode(n.text).length!==n.bytes||!hash.test(n.sha256))return fail('notice');
 return {ready:true,download:d};
}
