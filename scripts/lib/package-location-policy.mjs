// Shared build-time URL policy. Never strip an arbitrary origin from a download.
export const repository = 'Xenoah/meshcopia';
export const site = 'https://xenoah.github.io/meshcopia';
const slug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const version = /^\d+\.\d+\.\d+(?:-rc\.\d+)?$/;
export const packageKey = p => `${p.id}@${p.version}/${p.kind}`;
export const packageFilename = p => `${p.id}-${p.version}${p.kind === 'models' ? '-models' : ''}.zip`;
export const packagePath = p => `assets/${p.id}/${packageFilename(p)}`;
const require = (condition, message) => { if (!condition) throw new Error(message); };
export function pinnedURL(p) {
  require(slug.test(p.id) && version.test(p.version) && ['full','models'].includes(p.kind), 'Invalid package identity');
  require(typeof p.tag === 'string' && /^v/.test(p.tag) && version.test(p.tag.slice(1)), 'Invalid immutable release tag');
  return `https://github.com/${repository}/releases/download/${p.tag}/${packageFilename(p)}`;
}
export function validateLocations(lock, { protectedVersions = [], archives = [] } = {}) {
  require(lock.schemaVersion === 1 && lock.repository === repository && Array.isArray(lock.packages), 'Invalid package location manifest');
  const keys = new Set(), frozen = new Set(protectedVersions), prior = new Map(archives.map(a => [packageKey(a),a]));
  for (const p of lock.packages) {
    const key = packageKey(p);
    require(!frozen.has(`${p.id}@${p.version}`), `Protected package cannot move: ${key}`);
    require(!keys.has(key), `Duplicate package location: ${key}`); keys.add(key);
    require(p.filename === packageFilename(p) && p.url === pinnedURL(p), `Noncanonical release binding: ${key}`);
    require(Number.isSafeInteger(p.bytes) && p.bytes > 0 && p.bytes < 2 ** 31 && /^[0-9a-f]{64}$/.test(p.sha256), `Invalid package digest: ${key}`);
    if (prior.has(key)) for (const field of ['url','bytes','sha256']) require(prior.get(key)[field] === p[field], `Locked package binding changed: ${key}/${field}`);
  }
  // A model's full and models-only ZIPs must start on the same immutable tag.
  for (const p of lock.packages) {
    const pair = lock.packages.find(q => q.id === p.id && q.version === p.version && q.kind !== p.kind);
    require(pair && pair.tag === p.tag, `Incomplete package pair: ${packageKey(p)}`);
  }
  return lock;
}
export function assertLocationsAppendOnly(previous, next) {
  validateLocations(previous); validateLocations(next);
  const indexed = new Map(next.packages.map(p => [packageKey(p),p]));
  for (const p of previous.packages) require(JSON.stringify(indexed.get(packageKey(p))) === JSON.stringify(p), `Immutable package location changed or removed: ${packageKey(p)}`);
}
export function downloadHref(raw, locations, base = site) {
  require(typeof raw === 'string' && !/[\\\s]/.test(raw) && !/%(?:2e|2f|5c|25)/i.test(raw), 'Unsafe download URL');
  // Reject dot segments before URL normalisation, not only afterwards.
  require(!raw.split(/[/?#]/).some(segment => segment === '.' || segment === '..'), 'Unsafe download traversal');
  const configured = new URL(base), url = new URL(raw, configured.href + '/');
  require(url.protocol === 'https:' && !url.username && !url.password && !url.search && !url.hash && !url.port, 'Unsafe download URL');
  if (url.origin === configured.origin && url.pathname.startsWith(configured.pathname.replace(/\/$/,'') + '/') && (raw.startsWith('/') && !raw.startsWith('//') || raw === url.href)) return url.pathname;
  require(raw === url.href && locations.packages.some(p => p.url === raw && p.url === pinnedURL(p)), 'Unapproved external download URL');
  return raw;
}

export function pagesBudget(bytes) {
  require(Number.isSafeInteger(bytes) && bytes >= 0, 'Invalid Pages byte count');
  require(bytes < 1_000_000_000, `Pages capacity exceeded: ${bytes} bytes; publication blocked`);
  return bytes >= 900_000_000 ? 'warning' : 'ok';
}

// Operational headroom is intentionally stricter than the platform hard cap.
// Reaching this boundary requires a separately reviewed capacity/layout decision.
export function assertPagesOperatingBudget(bytes) {
  const status=pagesBudget(bytes); // Keep the independent 1 GB hard gate.
  require(bytes < 950_000_000, `Pages operating ceiling reached: ${bytes} bytes; publication blocked pending capacity review`);
  return status;
}
