import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { sha256, filesIn } from './catalog.mjs';
import { zipOptionsForPackage } from './zip-policy.mjs';
import { archiveRuntime } from './archive-runtime.mjs';

export const archiveLockPath = 'docs/archive-lock.json';
const origin = 'https://xenoah.github.io/meshcopia/';
export const archiveKey = a => `${a.id}@${a.version}/${a.kind}`;
export const archivePath = a => `assets/${a.id}/${a.id}-${a.version}${a.kind === 'models' ? '-models' : ''}.zip`;

export function validateArchiveLock(lock) {
  assert.equal(lock.schemaVersion, 1, 'Unsupported archive lock schema');
  assert.ok(Array.isArray(lock.archives), 'Missing archive lock entries');
  const keys = new Set();
  for (const a of lock.archives) {
    assert.match(a.id, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
    assert.match(a.version, /^\d+\.\d+\.\d+$/);
    assert.ok(['full', 'models'].includes(a.kind));
    assert.equal(a.url, origin + archivePath(a), 'Archive URL must be canonical and versioned');
    assert.ok(Number.isSafeInteger(a.bytes) && a.bytes > 0);
    assert.match(a.sha256, /^[0-9a-f]{64}$/);
    assert.ok(typeof a.profile === 'string' && a.profile.length > 0);
    const key = archiveKey(a);
    assert.ok(!keys.has(key), `Duplicate archive lock entry: ${key}`);
    keys.add(key);
  }
  return lock;
}

export function assertAppendOnly(previous, next) {
  validateArchiveLock(previous); validateArchiveLock(next);
  const indexed = new Map(next.archives.map(a => [archiveKey(a), a]));
  for (const a of previous.archives) {
    assert.deepEqual(indexed.get(archiveKey(a)), a,
      `Immutable archive lock changed or removed: ${archiveKey(a)}. Restore the original bytes; do not refresh the hash.`);
  }
}

export function archiveRecords(catalog) {
  return catalog.flatMap(a => Object.entries(a.downloads)
    .filter(([kind]) => kind === 'full' || kind === 'models')
    .map(([kind, d]) => ({id:a.id, version:a.version, kind, url:d.url,
      bytes:d.bytes, sha256:d.sha256,
      profile:zipOptionsForPackage(a).compress ? archiveRuntime.profile : 'store-v1'})))
    .sort((a,b) => archiveKey(a).localeCompare(archiveKey(b), 'en'));
}

export async function verifyArchiveLock({root='dist', catalog, lock, requireComplete=true}) {
  validateArchiveLock(lock);
  const records = archiveRecords(catalog);
  validateArchiveLock({schemaVersion:1, archives:records});
  const indexed = new Map(records.map(a => [archiveKey(a), a]));
  // Includes every frozen version, even if removed/hidden/updated in the catalog.
  // A version update cannot silently delete its historical URL.
  for (const a of lock.archives) {
    const data = await readFile(path.join(root, archivePath(a)));
    assert.equal(data.length, a.bytes, `Locked archive size drift: ${archiveKey(a)}`);
    assert.equal(sha256(data), a.sha256, `Locked archive hash drift: ${archiveKey(a)}`);
    if (indexed.has(archiveKey(a))) assert.deepEqual(indexed.get(archiveKey(a)), a,
      `Catalog/lock mismatch: ${archiveKey(a)}`);
  }
  const locked = new Set(lock.archives.map(archiveKey));
  const missing = records.filter(a => !locked.has(archiveKey(a)));
  for (const a of records) {
    const data = await readFile(path.join(root, archivePath(a)));
    assert.equal(data.length, a.bytes, `Catalog archive size drift: ${archiveKey(a)}`);
    assert.equal(sha256(data), a.sha256, `Catalog archive hash drift: ${archiveKey(a)}`);
  }
  const listedPaths = new Set([...lock.archives, ...records].map(archivePath));
  for (const file of await filesIn(path.join(root, 'assets'))) {
    if (file.endsWith('.zip')) assert.ok(listedPaths.has('assets/' + file), `Unlisted ZIP: ${file}`);
  }
  if (requireComplete) assert.equal(missing.length, 0,
    `Unsealed archive versions: ${missing.map(archiveKey).join(', ')}. Review and explicitly append new locks before publication.`);
  return missing;
}
