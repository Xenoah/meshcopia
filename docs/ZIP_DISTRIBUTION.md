# ZIP distribution and historical recovery

The current policy is FBX-first delivery with API **3.0.0**. See
[MINIMAL_DOWNLOADS.md](MINIMAL_DOWNLOADS.md) and
[ASSET_PRODUCTION_RULES.md](ASSET_PRODUCTION_RULES.md).

## Current Pages output

The generator does not create legacy full/models ZIPs. The310 historical copies
are omitted from Pages and their URLs/fields are absent from the current UI/API.
Old Pages URL compatibility is not guaranteed. Do not serve an HTML redirect as
if it were ZIP bytes or restore a retired fallback to pass an old compatibility
assertion. Production originals and preview/texture files remain available.

Models use the existing verified immutable FBX ZIPs, containing FBX and required
textures plus one short LICENSE.txt. Standalone textures use verified minimal
image ZIPs. Selected downloads produce one browser ZIP with one folder per asset
and one combined LICENSE. No nested archive collection is generated. The site
release bundler emits a site archive, catalog and checksums; existing Release
attachments are not changed or deleted.

`npm run check` verifies current files, Release bindings and source identity,
reconstructs all active FBX files from built chunks, checks every current internal
link, rejects retired files/links and measures the whole site against950,000,000
bytes. `node scripts/check-fbx-minimal-baseline.mjs` is now the migration gate,
not an assertion that API v3 is byte-identical to the old API.

## Retained historical formats and ledger

`docs/archive-lock.json` remains an unchanged, append-only historical record of
310 old ZIP identities. Source files, Git history and existing Release artifacts
are retained. `node scripts/check-archive-lock.mjs --check-history` compares all
reachable historical ledger revisions; deletion/recreation cannot erase prior
identities. Historical archive writer/validator fixtures still check hashes,
member names, attribution, local/central headers, sizes, CRCs and corruption.
The ledger is not itself a backup.

The historical STORE compatibility boundary contains107 previously published
asset/version pairs plus12 frozen v1.4.0 candidates. Their exact `id@version` list
in `scripts/lib/legacy-store-packages.json` and the fixed regression digest remain
unchanged. Records being frozen were not, by themselves, publication evidence.
Outside that boundary, historical full/models archives use raw DEFLATE level6
and STORE for entries that would not shrink. Reconstruct a historical site from
its exact Git revision, runtime and original inputs; do not overwrite a public
version with different bytes or update a saved hash to hide drift.

## Canonical runtime

The official Node **22.23.3** Linux x64 runtime and zlib **1.3.1-e00f703** remain
pinned in `.node-version` and `scripts/lib/archive-runtime.json`. Historical
compression fixes level6, strategy0, windowBits15 and memLevel8 with no environment
bypass. The archive writer independently enforces this profile. Its distribution
URL and SHA-256 are recorded in the runtime profile. A Node24 Actions runner is
separate from the pinned Node used to build/test the project.

This runtime was originally observed in
[CI38588682287](https://github.com/Xenoah/meshcopia/actions/runs/38588682287),
[job115937436469](https://github.com/Xenoah/meshcopia/actions/runs/38588682287/job/115937436469).
The profile remains relevant to historical recovery and tests; it no longer
requires regenerating all310 old ZIPs on every current Pages build.

The old `check-archive-lock.mjs` output-hash/`--append-new` operations are tools
for historical archive output. They are not the current Pages publication gate.
A future consumer package or runtime change needs a reviewed new immutable
version, actual byte readback and the appropriate source/version-bound adapter.
Archive sealing alone does not authorize publication.
