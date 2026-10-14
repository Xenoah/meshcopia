import { assertArchiveRuntime, archiveRuntime } from './lib/archive-runtime.mjs';
assertArchiveRuntime();
console.log(`Verified archive runtime ${archiveRuntime.profile}`);
