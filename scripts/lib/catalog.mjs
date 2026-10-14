import { readdir, readFile, lstat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';

export const ROOT = process.cwd();
export const LICENSE = 'CC-BY-4.0';
export const LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/';
export const SITE = (process.env.PUBLIC_SITE || 'https://xenoah.github.io').replace(/\/$/, '') + (process.env.PUBLIC_BASE_PATH ?? '/meshcopia');
export const MODEL_EXT = new Set(['.glb','.gltf','.bin','.obj','.mtl','.stl','.fbx','.step','.stp','.blend','.3mf']);
export const IMAGE_EXT = new Set(['.png','.jpg','.jpeg','.webp']);
const ALLOWED = new Set([...MODEL_EXT, ...IMAGE_EXT]);
export const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
export const sha256 = data => createHash('sha256').update(data).digest('hex');

export function safeRelative(value) {
  if (typeof value !== 'string' || !value || value.includes('\\') || value.startsWith('/') || value.split('/').some(s => !s || s === '.' || s === '..') || /[\x00-\x1f:?#]/.test(value)) throw new Error(`Unsafe relative path: ${value}`);
  return value;
}

export async function filesIn(dir, prefix = '') {
  const entries = await readdir(path.join(dir, prefix), {withFileTypes: true});
  const files = [];
  for (const entry of entries.sort((a,b) => a.name.localeCompare(b.name, 'en'))) {
    const name = prefix ? `${prefix}/${entry.name}` : entry.name;
    safeRelative(name);
    if (entry.isSymbolicLink()) throw new Error(`Symlinks are not allowed: ${name}`);
    if (entry.isDirectory()) files.push(...await filesIn(dir, name));
    else if (entry.isFile()) files.push(name);
    else throw new Error(`Unsupported file: ${name}`);
  }
  return files;
}

export async function readAsset(dir) {
  const a = JSON.parse(await readFile(path.join(dir, 'asset.json'), 'utf8'));
  const fail = message => { throw new Error(`${a.id || dir}: ${message}`); };
  if (!slugPattern.test(a.id) || a.id !== path.basename(dir)) fail('id must match folder name (lowercase kebab-case)');
  if (!['model','texture'].includes(a.type)) fail('type must be model or texture');
  for (const key of ['title','titleEn','description','descriptionEn','category','author','version','created','updated']) if (typeof a[key] !== 'string' || !a[key].trim()) fail(`Missing ${key}`);
  for (const key of ['created','updated']) if (!/^\d{4}-\d{2}-\d{2}$/.test(a[key]) || Number.isNaN(Date.parse(a[key]))) fail(`Invalid ${key}`);
  if (!/^\d+\.\d+\.\d+$/.test(a.version)) fail('version must be semver');
  if (a.license !== LICENSE) fail('Only explicitly licensed CC-BY-4.0 assets can be published');
  if (!['public','draft','hidden'].includes(a.status)) fail('Invalid status');
  if (!Array.isArray(a.tags) || a.tags.some(t => typeof t !== 'string')) fail('tags must be strings');
  if (!a.provenance?.method || !a.provenance?.tool || !a.provenance?.rights) fail('provenance (method/tool/rights) is required');
  if (!IMAGE_EXT.has(path.extname(a.thumbnail))) fail('thumbnail must be PNG, JPEG or WebP');
  safeRelative(a.thumbnail);
  const thumbnail = await lstat(path.join(dir, a.thumbnail));
  if (!thumbnail.isFile() || thumbnail.isSymbolicLink()) fail('thumbnail must be a regular file');
  const sources = await filesIn(path.join(dir, 'source'));
  if (!sources.length) fail('source is empty');
  const sourceRoot = await realpath(path.join(dir, 'source'));
  if (sourceRoot !== path.resolve(dir, 'source')) fail('source must not be a symlink');
  for (const file of sources) {
    if (!ALLOWED.has(path.extname(file).toLowerCase())) fail(`Disallowed source extension: ${file}`);
    const size = (await lstat(path.join(dir, 'source', file))).size;
    if (!size || size > 95 * 1024 * 1024) fail(`Invalid file size: ${file}`);
  }
  if (a.type === 'model') {
    if (!['m','cm','mm'].includes(a.unit) || !['Y','Z'].includes(a.upAxis)) fail('unit and upAxis required');
    if (!a.preview || !sources.includes(safeRelative(a.preview))) fail('preview not found');
    if (!['.glb','.gltf','.obj','.fbx','.step','.stp','.stl'].includes(path.extname(a.preview))) fail('Unsupported preview format');
    if (!Number.isInteger(a.triangles) || a.triangles < 1) fail('triangles required');
  } else {
    if (a.seamless !== true || !Number.isInteger(a.resolution) || a.resolution < 1) fail('seamless and resolution required');
    if (!a.maps?.baseColor) fail('baseColor map required');
    for (const f of Object.values(a.maps)) if (!sources.includes(safeRelative(f)) || !IMAGE_EXT.has(path.extname(f))) fail(`Missing map: ${f}`);
  }
  return {...a, dir, sources};
}

export async function readCatalog(root = path.join(ROOT, 'content/assets')) {
  const entries = await readdir(root, {withFileTypes: true});
  const assets = [];
  for (const entry of entries.sort((a,b) => a.name.localeCompare(b.name, 'en'))) {
    if (entry.name.startsWith('.')) continue;
    if (!entry.isDirectory() || entry.isSymbolicLink()) throw new Error(`Expected asset directory: ${entry.name}`);
    assets.push(await readAsset(path.join(root, entry.name)));
  }
  return assets;
}

export function attributionFor(a) {
  return `${a.titleEn} by ${a.author} / Meshcopia\n${SITE}/assets/${a.id}/\nCC BY 4.0 — ${LICENSE_URL}\nChanges: none. If modified, replace this line with a description of your changes.`;
}
