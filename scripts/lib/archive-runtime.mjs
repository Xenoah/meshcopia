import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

export const archiveRuntime = Object.freeze(JSON.parse(readFileSync(
  new URL('./archive-runtime.json', import.meta.url), 'utf8'
)));
export const compressionOptions = Object.freeze(Object.fromEntries(
  ['level', 'strategy', 'windowBits', 'memLevel'].map(key => [key, archiveRuntime[key]])
));

// No environment override: development can inspect STORE archives anywhere,
// but producing DEFLATE bytes requires the exact reviewed canonical profile.
export function assertArchiveRuntime(actual = {
  node: process.versions.node, zlib: process.versions.zlib,
  platform: process.platform, arch: process.arch
}) {
  for (const key of ['node', 'zlib', 'platform', 'arch']) {
    assert.equal(actual[key], archiveRuntime[key],
      `Archive runtime ${key} mismatch: expected ${archiveRuntime[key]}, got ${actual[key]}. Use the pinned official runtime; never refresh existing archive hashes.`);
  }
}
