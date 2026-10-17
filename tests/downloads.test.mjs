import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {MINIMAL_CONTENT_POLICY,minimalDownloadReadiness,primaryDownload,primaryDownloadBytes,downloadHref,directModelFiles} from '../src/lib/downloads.mjs';
import {filterAssets} from '../src/lib/catalog-ui.js';

// Synthetic records only. They are not actual publication/verification evidence.
const digest = text=>createHash('sha256').update(text).digest('hex');
const clone = value=>structuredClone(value);
function fixture(type='model') {
  const id=`fixture-${type}`, version='1.0.0';
  const files=(type==='model'?['mesh.glb','mesh.obj','mesh.mtl','maps/color.png','mesh.stl','mesh.step']:['color.png','normal.png']).map(name=>({name,format:name.split('.').pop().toUpperCase(),bytes:20,sha256:digest(name),url:`https://xenoah.github.io/meshcopia/assets/${id}/source/${name}`}));
  const downloads={full:{url:`https://xenoah.github.io/meshcopia/assets/${id}/${id}-${version}.zip`,bytes:4000,sha256:digest('legacy full')}};
  if(type==='model')downloads.models={url:`https://xenoah.github.io/meshcopia/assets/${id}/${id}-${version}-models.zip`,bytes:3000,sha256:digest('legacy models')};
  return {id,version,type,status:'public',title:id,titleEn:id,tags:[],updated:'2026-10-15',files,downloads};
}
function bind(asset) {
  const text=`Fixture creator / ${asset.id}\nCC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nhttps://xenoah.github.io/meshcopia/assets/${asset.id}/\nChanges: none. No warranties.\n`;
  asset.downloads.minimal={schemaVersion:1,id:asset.id,assetVersion:asset.version,packageVersion:'1.0.0',contentPolicy:MINIMAL_CONTENT_POLICY,noticeFile:'LICENSE.txt',notice:{filename:'LICENSE.txt',text,bytes:Buffer.byteLength(text,'utf8'),sha256:digest(text)},url:`https://github.com/Xenoah/meshcopia/releases/download/fixture-minimal-v1.0.0/${asset.id}-${asset.version}-minimal-1.0.0.zip`,bytes:2000,sha256:digest('fixture minimal'),sourceFiles:asset.files.map(({name,bytes,sha256})=>({name,bytes,sha256})),verification:{state:'published-verified',releaseTag:'fixture-minimal-v1.0.0',archiveSha256:digest('fixture minimal')}};
  return asset;
}

test('models without verified FBX are unavailable; legacy fields stay intact',()=>{const a=bind(fixture());assert.equal(primaryDownload(a),undefined);assert.equal(primaryDownloadBytes(a),Infinity);assert.ok(a.downloads.models);});
test('textures retain a truthful preview/metadata legacy description until bound',()=>{
  const a=fixture('texture'), selected=primaryDownload(a);assert.equal(selected.kind,'full');assert.equal(selected.minimal,false);
  assert.equal(selected.labelEn,'Texture ZIP (legacy)');assert.equal(selected.contentsEn,'Asset files, preview, metadata, README, LICENSE.txt and ATTRIBUTION.txt');
});
for(const type of ['texture'])test(`${type}: verified binding becomes the sole primary ZIP without mutating legacy fields`,()=>{
  const a=bind(fixture(type)), before=clone(a);const selected=primaryDownload(a);
  assert.equal(minimalDownloadReadiness(a).ready,true);assert.equal(selected.kind,'minimal');assert.equal(selected.minimal,true);assert.equal(selected.url,a.downloads.minimal.url);assert.equal(primaryDownloadBytes(a),2000);
  assert.equal(selected.labelJa,'素材 ZIPをダウンロード');assert.equal(selected.labelEn,'Download asset ZIP');assert.equal(selected.contentsEn,'Asset files, required dependencies and LICENSE.txt (license and attribution)');
  assert.equal(selected.contentsJa,'素材ファイル・必要な関連ファイル・LICENSE.txt（ライセンス・クレジット）');assert.deepEqual(a,before);
});

const invalidCases=[
 ['schema',a=>a.downloads.minimal.schemaVersion=2,'identity'],
 ['wrong ID',a=>a.downloads.minimal.id='another-asset','identity'],
 ['old asset version',a=>a.downloads.minimal.assetVersion='0.9.0','identity'],
 ['noncanonical package version',a=>a.downloads.minimal.packageVersion='01.0.0','identity'],
 ['unknown asset type',a=>a.type='other','identity'],
 ['wrong content policy',a=>a.downloads.minimal.contentPolicy='models-only','contents-policy'],
 ['second notice convention',a=>a.downloads.minimal.noticeFile='ATTRIBUTION.txt','contents-policy'],
 ['missing notice',a=>delete a.downloads.minimal.notice,'notice'],
 ['wrong notice name',a=>a.downloads.minimal.notice.filename='README.md','notice'],
 ['empty notice',a=>a.downloads.minimal.notice.text='','notice'],
 ['notice size mismatch',a=>a.downloads.minimal.notice.bytes++,'notice'],
 ['notice malformed hash',a=>a.downloads.minimal.notice.sha256='bad','notice'],
 ['empty archive',a=>a.downloads.minimal.bytes=0,'archive'],
 ['unsafe integer bytes',a=>a.downloads.minimal.bytes=Number.MAX_SAFE_INTEGER+1,'archive'],
 ['malformed archive hash',a=>a.downloads.minimal.sha256='not-a-hash','archive'],
 ['missing companion',a=>a.downloads.minimal.sourceFiles.pop(),'source-inventory'],
 ['extra documentation payload',a=>a.downloads.minimal.sourceFiles.push({name:'README.md',bytes:3,sha256:digest('doc')}),'source-inventory'],
 ['duplicate source',a=>a.downloads.minimal.sourceFiles.push(a.downloads.minimal.sourceFiles[0]),'source-inventory'],
 ['changed source bytes',a=>a.downloads.minimal.sourceFiles[0].bytes++,'source-inventory'],
 ['changed source hash',a=>a.downloads.minimal.sourceFiles[0].sha256=digest('changed'),'source-inventory'],
 ['unsafe source path',a=>{a.downloads.minimal.sourceFiles[0].name='../mesh.glb';a.files[0].name='../mesh.glb'},'source-inventory'],
 ['missing published verification',a=>delete a.downloads.minimal.verification,'verification'],
 ['pending verification',a=>a.downloads.minimal.verification.state='pending','verification'],
 ['wrong verified digest',a=>a.downloads.minimal.verification.archiveSha256=digest('other'),'verification'],
 ['mutable latest',a=>a.downloads.minimal.verification.releaseTag='latest','release'],
 ['branch name',a=>a.downloads.minimal.verification.releaseTag='main','release'],
 ['wrong repository',a=>a.downloads.minimal.url=a.downloads.minimal.url.replace('Xenoah/meshcopia','other/meshcopia'),'release'],
 ['wrong release',a=>a.downloads.minimal.url=a.downloads.minimal.url.replace('fixture-minimal-v1.0.0','fixture-minimal-v1.1.0'),'release'],
 ['wrong archive filename',a=>a.downloads.minimal.url=a.downloads.minimal.url.replace('-minimal-1.0.0.zip','.zip'),'release'],
 ['query redirect',a=>a.downloads.minimal.url+='?redirect=old','release'],
 ['legacy full URL',a=>a.downloads.minimal.url=a.downloads.full.url,'release'],
 ['old full bytes at a new URL',a=>{a.downloads.minimal.sha256=a.downloads.full.sha256;a.downloads.minimal.verification.archiveSha256=a.downloads.full.sha256},'legacy-archive'],
 ['old two-notice model bytes at new URL',a=>{a.downloads.minimal.sha256=a.downloads.models.sha256;a.downloads.minimal.verification.archiveSha256=a.downloads.models.sha256},'legacy-archive'],
];
for(const [name,change,reason] of invalidCases)test(`fail closed: ${name}`,()=>{
  const a=bind(fixture());change(a);assert.deepEqual(minimalDownloadReadiness(a),{ready:false,reason});assert.notEqual(primaryDownload(a)?.kind,'minimal');
});
test('source inventory order is immaterial, and Unicode notice bytes are UTF-8',()=>{
  const a=bind(fixture());a.downloads.minimal.sourceFiles.reverse();const notice=a.downloads.minimal.notice;notice.text+='作者: テスト\n';notice.bytes=Buffer.byteLength(notice.text,'utf8');notice.sha256=digest(notice.text);assert.equal(minimalDownloadReadiness(a).ready,true);
  notice.bytes=notice.text.length;assert.equal(minimalDownloadReadiness(a).reason,'notice');
});
test('current file changes invalidate a previously bound archive',()=>{
  const a=bind(fixture());a.files[0].sha256=digest('updated current source');assert.equal(minimalDownloadReadiness(a).reason,'source-inventory');assert.equal(primaryDownload(a),undefined);
});
test('missing or malformed ordinary downloads remain unavailable or use honest full fallback',()=>{
  assert.equal(primaryDownload({type:'model'}),undefined);assert.equal(primaryDownload(undefined),undefined);assert.equal(primaryDownloadBytes({}),Infinity);
  const a=fixture('texture');assert.equal(primaryDownload(a).kind,'full');assert.equal(primaryDownload(a).labelEn,'Texture ZIP (legacy)');
  a.downloads.full.url='http://unsafe.example/file.zip';assert.equal(primaryDownload(a),undefined);
});
test('Release origin is never stripped; same-site direct files stay base-path local',()=>{
  const a=bind(fixture());assert.equal(downloadHref(a.downloads.minimal.url),a.downloads.minimal.url);
  assert.equal(downloadHref(a.files[0].url),'/meshcopia/assets/fixture-model/source/mesh.glb');
  assert.equal(downloadHref('/meshcopia/assets/model.zip'),'/meshcopia/assets/model.zip');
  for(const url of ['javascript:alert(1)','http://example.com/a.zip','https://user:pass@github.com/a.zip','https://github.com/a\\b','data:application/zip;base64,a',''])assert.equal(downloadHref(url),undefined);
});
test('original models stay separate from primary direct FBX links',()=>{assert.deepEqual(directModelFiles(fixture()),[]);});
test('catalog size ordering follows the same selected ZIP as cards and detail pages',()=>{
  const legacy=fixture('texture'), migrated=bind(fixture('texture'));migrated.id='migrated';migrated.downloads.minimal.id='migrated';migrated.downloads.minimal.url=migrated.downloads.minimal.url.replace('fixture-texture-','migrated-');legacy.downloads.full.bytes=2500;migrated.downloads.full.bytes=9000;
  assert.deepEqual(filterAssets([legacy,migrated],{sort:'size'}).map(a=>a.id),[migrated.id,legacy.id]);
  migrated.downloads.minimal.verification.state='pending';assert.deepEqual(filterAssets([legacy,migrated],{sort:'size'}).map(a=>a.id),[legacy.id,migrated.id]);
});
test('ordinary Astro controls share selector and retain no second full/models ZIP button',async()=>{
  const detail=await readFile(new URL('../src/pages/assets/[id].astro',import.meta.url),'utf8');
  const card=await readFile(new URL('../src/components/AssetCard.astro',import.meta.url),'utf8');
  for(const source of [detail,card]){
    assert.match(source,/primaryDownload\(a\)/);assert.match(source,/downloadHref\(download\.url\)/);assert.doesNotMatch(source,/href=\{local\(a\.downloads\.(full|models)\.url\)\}/);
    assert.doesNotMatch(source,/全モデル形式|全体ZIP|Models only ZIP|All model formats/);
  }
  assert.equal((detail.match(/class="button primary download-primary"/g)||[]).length,1);
  assert.match(detail,/directModelFiles\(a\)/);assert.match(detail,/data-en="Individual formats"/);assert.match(detail,/Individual files still require attribution/);
  assert.match(card,/data-bytes=\{primaryDownloadBytes\(a\)\}/);assert.match(detail,/class="preview-tabs"/);assert.match(detail,/class="credit-card"/);
});
