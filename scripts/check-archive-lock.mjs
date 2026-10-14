import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { archiveLockPath, archiveKey, assertAppendOnly, verifyArchiveLock } from './lib/archive-lock.mjs';
import { assertArchiveRuntime } from './lib/archive-runtime.mjs';

const args = process.argv.slice(2);
assert.ok(args.length <= 1 && args.every(a => ['--append-new', '--check-history'].includes(a)), 'Unsupported archive-lock arguments');
const lock = JSON.parse(await readFile(archiveLockPath, 'utf8'));
if (args.includes('--check-history')) {
  // Inspect all reachable historical ledger revisions, not only HEAD^; a
  // multi-commit push must not delete and re-create an old ledger to reset it.
  const commits = execFileSync('git', ['log', '--full-history', '--format=%H', '--', archiveLockPath], {encoding:'utf8'}).trim().split('\n').filter(Boolean);
  for (const commit of commits) {
    const names = execFileSync('git', ['ls-tree', '--name-only', commit, '--', archiveLockPath], {encoding:'utf8'}).trim();
    if (!names) continue; // A deletion revision does not erase earlier locks.
    const previous = JSON.parse(execFileSync('git', ['show', `${commit}:${archiveLockPath}`], {encoding:'utf8'}));
    assertAppendOnly(previous, lock);
  }
  console.log(`Verified append-only archive ledger against ${commits.length} historical revisions.`);
} else {
  const catalog = JSON.parse(await readFile('src/data/catalog.json', 'utf8'));
  const append = args.includes('--append-new');
  if (append) assertArchiveRuntime();
  const missing = await verifyArchiveLock({catalog, lock, requireComplete:!append});
  if (append) {
    // Deliberate local operation only. CI never updates or blesses this ledger.
    const next = {...lock, archives:[...lock.archives, ...missing].sort((a,b) => archiveKey(a).localeCompare(archiveKey(b), 'en'))};
    assertAppendOnly(lock, next);
    await writeFile(archiveLockPath, JSON.stringify(next, null, 2)+'\n');
    console.log(`Appended ${missing.length} new archive locks. Review/commit these before publication; no existing hash was replaced.`);
  } else console.log(`Verified ${lock.archives.length} frozen archive hashes and sizes.`);
}
