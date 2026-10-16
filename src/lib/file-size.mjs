import {planBundle} from './batch-download.mjs';

/** Decimal units match the B / KB / MB labels. Unknown is never displayed as zero. */
export function formatBytes(bytes, unknown = '—') {
 if (!Number.isSafeInteger(bytes) || bytes < 0) return unknown;
 if (bytes < 1000) return `${bytes} B`;
 const units = ['KB', 'MB', 'GB', 'TB', 'PB'];
 let value = bytes / 1000, unit = 0;
 while (value >= 999.95 && unit < units.length - 1) { value /= 1000; unit++; }
 return `${value.toFixed(1)} ${units[unit]}`;
}

/** Estimate the combined STORE ZIP from its own entries, not individual ZIPs.
 * Include both filename copies, local/central headers and end-of-directory.
 * The final display always uses the built Blob.size instead. */
export function bundleSizeSummary(assets) {
 if (!assets.length) return {inputBytes: 0, zipBytes: 0};
 try {
  const plan = planBundle(assets, {limit: Number.MAX_SAFE_INTEGER});
  const zipBytes = plan.bytes + 22 + plan.entries.reduce((sum, entry) => sum + 76 + 2 * new TextEncoder().encode(entry.name).length, 0);
  return {inputBytes: plan.bytes, zipBytes};
 } catch { return {inputBytes: null, zipBytes: null}; }
}
