import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import { writeStoreZip, crc32 } from '../scripts/lib/zip-store.mjs';
import { readZipEntries } from '../scripts/lib/zip-read.mjs';
import { zipOptionsForPackage } from '../scripts/lib/zip-policy.mjs';

// Produced by the previous STORE-only writer, not by the implementation under test.
const legacy = Buffer.from('UEsDBBQAAAgAAAAAIQCcDrx2CgAAAAoAAAANAAAA44OG44K544OILm9iam8gZXhhbXBsZQpQSwMEFAAACAAAAAAhAMyzGSMJAAAACQAAAAsAAABMSUNFTlNFLnR4dENDLUJZLTQuMFBLAQIUABQAAAgAAAAAIQCcDrx2CgAAAAoAAAANAAAAAAAAAAAAAAAAAAAAAADjg4bjgrnjg4gub2JqUEsBAhQAFAAACAAAAAAhAMyzGSMJAAAACQAAAAsAAAAAAAAAAAAAAAAANQAAAExJQ0VOU0UudHh0UEsFBgAAAAACAAIAdAAAAGcAAAAAAA==', 'base64');

test('ZIP validator accepts legacy STORE archives and UTF-8 filenames', () => {
  const files = readZipEntries(legacy);
  assert.equal(files.get('テスト.obj').toString(), 'o example\n');
  assert.equal(files.get('LICENSE.txt').toString(), 'CC-BY-4.0');
  assert.equal(crc32(Buffer.from('123456789')), 0xcbf43926);
});

test('ZIPs compress only when smaller, preserve bytes and remain deterministic', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'meshcopia-deflate-'));
  try {
    const entries = [
      { name: '日本語/mesh.stl', data: Buffer.from('repeated mesh coordinates\n'.repeat(1000)) },
      { name: 'incompressible.bin', data: Buffer.from(Array.from({ length: 256 }, (_, i) => i)) },
      { name: 'empty.txt', data: Buffer.alloc(0) },
      { name: 'LICENSE.txt', data: 'CC-BY-4.0' }
    ];
    await writeStoreZip(`${dir}/a.zip`, entries, { compress: true });
    await writeStoreZip(`${dir}/b.zip`, entries, { compress: true });
    const bytes = await readFile(`${dir}/a.zip`);
    assert.deepEqual(bytes, await readFile(`${dir}/b.zip`));
    assert.ok(bytes.length < 1500);
    const files = readZipEntries(bytes);
    assert.equal(files.size, entries.length);
    for (const entry of entries) assert.deepEqual(files.get(entry.name), Buffer.from(entry.data));
    let offset = 0;
    for (const method of [8, 0, 0, 0]) {
      assert.equal(bytes.readUInt16LE(offset + 8), method);
      assert.equal(bytes.readUInt16LE(offset + 6), 0x0800);
      offset += 30 + bytes.readUInt16LE(offset + 26) + bytes.readUInt16LE(offset + 28) + bytes.readUInt32LE(offset + 18);
    }

    // Alter both size headers, so validation must check actual expanded bytes.
    const wrongSize = Buffer.from(bytes);
    const central = wrongSize.readUInt32LE(wrongSize.length - 6);
    wrongSize.writeUInt32LE(entries[0].data.length + 1, 22);
    wrongSize.writeUInt32LE(entries[0].data.length + 1, central + 24);
    assert.throws(() => readZipEntries(wrongSize), /expanded size/);
    const wrongCrc = Buffer.from(bytes);
    wrongCrc.writeUInt32LE(0, 14); wrongCrc.writeUInt32LE(0, central + 16);
    assert.throws(() => readZipEntries(wrongCrc), /CRC differs/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('Published package versions keep STORE bytes; only new versions opt in', async () => {
  const keys = JSON.parse(await readFile(new URL('../scripts/lib/legacy-store-packages.json', import.meta.url), 'utf8'));
  assert.deepEqual(keys, [...new Set(keys)].sort());
  assert.equal(keys.length, 119, 'The v1.4.0 STORE compatibility list is frozen');
  assert.equal(createHash('sha256').update(keys.join('\n')).digest('hex'), 'a3f4dc4c4d62299f9c78859e6439a54bdbf6990fcf493740eb569780cbd971ae');
  for (const key of keys) {
    const [id, version] = key.split('@');
    assert.match(id, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
    assert.match(version, /^\d+\.\d+\.\d+$/);
    assert.deepEqual(zipOptionsForPackage({ id, version }), { compress: false });
  }
  const [id] = keys[0].split('@');
  assert.deepEqual(zipOptionsForPackage({ id, version: '99.0.0' }), { compress: true });
  assert.deepEqual(zipOptionsForPackage({ id: 'never-published-fixture', version: '1.0.0' }), { compress: true });
  const dir = await mkdtemp(path.join(os.tmpdir(), 'meshcopia-store-'));
  try {
    const entries = [{ name: 'テスト.obj', data: 'o example\n' }, { name: 'LICENSE.txt', data: 'CC-BY-4.0' }];
    await writeStoreZip(`${dir}/default.zip`, entries);
    await writeStoreZip(`${dir}/published.zip`, entries, zipOptionsForPackage({ id, version: keys[0].split('@')[1] }));
    assert.deepEqual(await readFile(`${dir}/default.zip`), legacy);
    assert.deepEqual(await readFile(`${dir}/published.zip`), legacy);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('ZIP validator rejects corrupt payloads, headers and directory offsets', () => {
  const corrupt = Buffer.from(legacy);
  corrupt[30 + corrupt.readUInt16LE(26)] ^= 1;
  assert.throws(() => readZipEntries(corrupt), /CRC differs/);
  const method = Buffer.from(legacy); method.writeUInt16LE(99, 8);
  assert.throws(() => readZipEntries(method), /Unsupported ZIP compression/);
  const wrongOffset = Buffer.from(legacy);
  const central = wrongOffset.readUInt32LE(wrongOffset.length - 6);
  wrongOffset.writeUInt32LE(1, central + 42);
  assert.throws(() => readZipEntries(wrongOffset), /local offset/);
  assert.throws(() => readZipEntries(legacy.subarray(0, legacy.length - 1)), /end record/);
});
