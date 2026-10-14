import { readFileSync } from 'node:fs';

// Do not remove published id@version pairs: their versioned URLs and historical
// catalogs commit to the original STORE archive bytes. Only never-published
// package versions may opt in to the new deterministic compression profile.
const legacyStorePackages = new Set(JSON.parse(readFileSync(
  new URL('./legacy-store-packages.json', import.meta.url), 'utf8'
)));

export function zipOptionsForPackage({ id, version }) {
  return { compress: !legacyStorePackages.has(`${id}@${version}`) };
}
