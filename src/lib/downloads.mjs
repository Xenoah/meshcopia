import {deliveryReadiness} from './delivery.mjs';
// This module selects downloads; it does not publish or verify remote bytes.
// Only the verified publisher projection may populate downloads.minimal.
export const MINIMAL_CONTENT_POLICY = 'asset-files-required-dependencies-single-notice-v1';
const SITE_ORIGIN = 'https://xenoah.github.io';
const RELEASE_ROOT = 'https://github.com/Xenoah/meshcopia/releases/download/';
const HASH = /^[a-f0-9]{64}$/;
const VERSION = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/;
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const positiveBytes = n => Number.isSafeInteger(n) && n > 0;
const safePath = value => typeof value === 'string' && !!value && !/[\\\x00-\x1f\x7f:?#]/.test(value) && value.split('/').every(part => part && part !== '.' && part !== '..');
const inventory = files => files.map(({name,bytes,sha256})=>({name,bytes,sha256})).sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0);
const validInventory = files => Array.isArray(files) && files.length > 0 && new Set(files.map(f=>f?.name)).size === files.length && files.every(f=>f && safePath(f.name) && positiveBytes(f.bytes) && HASH.test(f.sha256));

/** Preserve the host for Release files. Only same-site URLs become local paths. */
export function downloadHref(value) {
  if (typeof value !== 'string' || !value || /[\x00-\x20\x7f\\]/.test(value)) return undefined;
  try {
    const url = new URL(value, SITE_ORIGIN);
    if (url.protocol !== 'https:' || url.username || url.password) return undefined;
    return url.origin === SITE_ORIGIN ? url.pathname + url.search + url.hash : url.href;
  } catch { return undefined; }
}

/** Fail-closed structural gate, after the publisher's independent verification. */
export function minimalDownloadReadiness(asset) {
  const binding = asset?.downloads?.minimal;
  const fail = reason => ({ready:false,reason});
  if (!binding) return fail('absent');
  if (!['model','texture'].includes(asset.type) || !ID.test(asset.id) || !VERSION.test(asset.version) || binding.schemaVersion !== 1 || binding.id !== asset.id || binding.assetVersion !== asset.version || !VERSION.test(binding.packageVersion)) return fail('identity');
  if (binding.contentPolicy !== MINIMAL_CONTENT_POLICY || binding.noticeFile !== 'LICENSE.txt') return fail('contents-policy');
  if (!positiveBytes(binding.bytes) || !HASH.test(binding.sha256)) return fail('archive');
  const notice = binding.notice;
  if (notice?.filename !== binding.noticeFile || typeof notice.text !== 'string' || !notice.text.trim() || !positiveBytes(notice.bytes) || new TextEncoder().encode(notice.text).length !== notice.bytes || !HASH.test(notice.sha256)) return fail('notice');
  if (!validInventory(asset.files) || !validInventory(binding.sourceFiles) || JSON.stringify(inventory(asset.files)) !== JSON.stringify(inventory(binding.sourceFiles))) return fail('source-inventory');
  const verification = binding.verification;
  if (verification?.state !== 'published-verified' || verification.archiveSha256 !== binding.sha256) return fail('verification');
  const tag = verification.releaseTag;
  // Explicit versioned tag only; the publisher separately proves immutability.
  if (typeof tag !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(tag) || !/\d+\.\d+\.\d+/.test(tag)) return fail('release');
  const filename = `${asset.id}-${asset.version}-minimal-${binding.packageVersion}.zip`;
  if (binding.url !== `${RELEASE_ROOT}${tag}/${filename}`) return fail('release');
  if (['full','models'].some(kind=>asset.downloads[kind] && (asset.downloads[kind].url === binding.url || asset.downloads[kind].sha256 === binding.sha256))) return fail('legacy-archive');
  return {ready:true,reason:'published-verified',download:binding};
}

/** One ordinary ZIP. Compatibility API fields are never a second UI choice. */
export function primaryDownload(asset) {
  if (asset?.type === 'model') {
    const ready = deliveryReadiness(asset);
    if (!ready.ready) return undefined;
    return {...ready.download.archive,kind:'fbx',minimal:true,
      labelJa:'FBX ZIPをダウンロード',labelEn:'Download FBX ZIP',
      contentsJa:'FBX・必要なテクスチャ・LICENSE.txt（ライセンス・クレジット）',
      contentsEn:'FBX, required textures and LICENSE.txt (license and attribution)'};
  }
  const readiness = minimalDownloadReadiness(asset);
  if (readiness.ready) return {
    ...readiness.download, kind:'minimal', minimal:true,
    labelJa:'素材 ZIPをダウンロード', labelEn:'Download asset ZIP',
    contentsJa:'素材ファイル・必要な関連ファイル・LICENSE.txt（ライセンス・クレジット）',
    contentsEn:'Asset files, required dependencies and LICENSE.txt (license and attribution)',
  };
  const kind = (asset?.type === 'model' ? ['models','full'] : ['full']).find(key=> {
    const file = asset?.downloads?.[key];
    return file && downloadHref(file.url) && positiveBytes(file.bytes);
  });
  if (!kind) return undefined;
  const legacy = asset.downloads[kind];
  return {
    ...legacy, kind, minimal:false,
    labelJa:kind === 'models' ? '3Dモデル ZIP（従来版）' : asset.type === 'texture' ? 'テクスチャ ZIP（従来版）' : '素材 ZIP（従来版）',
    labelEn:kind === 'models' ? 'Model ZIP (legacy)' : asset.type === 'texture' ? 'Texture ZIP (legacy)' : 'Asset ZIP (legacy)',
    contentsJa:kind === 'models' ? '3Dモデル・必要な関連ファイル・LICENSE.txt・ATTRIBUTION.txt' : '素材ファイル・プレビュー・メタデータ・README・LICENSE.txt・ATTRIBUTION.txt',
    contentsEn:kind === 'models' ? 'Model files, required dependencies, LICENSE.txt and ATTRIBUTION.txt' : 'Asset files, preview, metadata, README, LICENSE.txt and ATTRIBUTION.txt',
  };
}

export function primaryDownloadBytes(asset) {
  const selected = primaryDownload(asset);
  // Incomplete search-only records may carry sizes without URLs.
  return selected?.bytes ?? Infinity;
}

/** Standalone FBX is offered only when the verified package has no companions. */
export function directModelFiles(asset) {
  const ready = deliveryReadiness(asset);
  return ready.ready && ready.download.files.length === 1 ? ready.download.files : [];
}
