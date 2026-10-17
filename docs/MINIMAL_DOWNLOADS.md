# FBX-first delivery and API v3 migration

API v3 exposes `downloads.delivery` for models and `downloads.minimal` for
standalone textures. It removes `downloads.full`, `models`, `direct` and the
model's former all-source `minimal` binding. The generator no longer creates
legacy full/models ZIP copies in Pages. Old Pages URL compatibility is not
promised; current UI and API must contain no retired ZIP links. Production
originals, preview files, Git history, the historical archive ledger and existing
Release attachments are retained. No other distribution repository is created.

Do not edit generated catalogs, add placeholder records, guess a Release ID or
accept an unverified URL. Every current binding requires the same independent
public-byte verification as before this migration.

## Current model delivery contract

`downloads.delivery` is emitted only after mandatory same-job FBX prep, current
source/metadata checks and the model delivery gate. It contains:

- `schemaVersion: 1`, exact `id`, `assetVersion`, `packageVersion`.
- `contentPolicy: fbx-required-textures-single-notice-v1`.
- `sourceFiles`: original source inventory bound by the successful FBX proof;
  these files remain in root `asset.files` for production-original/preview access.
  They are separate from the consumer inventory and their URLs are not guaranteed forever.
- `archive`: the existing verified immutable FBX ZIP URL, filename, bytes, sha256.
- `files`: exact consumer files with name, format, bytes, sha256, direct Release URL
  and `fetch` transport. Currently all137 have embedded images and exactly one FBX.
  A future external-texture model requires its own reviewed dependency adapter.
- `notice` and `verification`: exact existing FBX notice and publication binding.

The current fetch transport is `chunks-gzip-v1`: a same-site immutable JSON
manifest, with its own bytes/SHA-256. It names bounded gzip chunks by compressed
hash and records compressed/expanded counts and hashes. Chunks have content-defined
64–512 KiB boundaries to share identical embedded data across FBXs. The browser
verifies the manifest, every compressed/expanded chunk and final FBX before saving.
It issues at most four parallel chunk reads, bounds expanded memory, rejects
redirects, uses no credentials and fails the entire ZIP on missing/corrupt bytes.
No preview, QA or transport manifest enters the consumer ZIP. The original137
payload is reused byte-for-byte, never re-exported or re-licensed.

`public/download-data` is generated output, not a committed source. Prep's local
FBX payload cache is usable only after fresh verification and receipt consumption;
it is not an offline bypass. The generator rehashes all payloads before replacing
output. check-dist reconstructs all137 from the actual built chunks independently.

The browser diagnostic in CI39042567048 confirmed missing CORS headers on both
the direct Release URL and the API's redirected binary; neither a clickable
link nor a successful server-side download establishes CORS support. No API fetch
or third-party proxy is used by the shipped bundle builder. Deployment is blocked
until the complete build fits the existing Pages budget. The approved migration
removes old Pages ZIP copies instead of creating another host. See FBX_DISTRIBUTION_REVIEW.md.

## Texture minimal and historical verification contract

Only textures expose this binding in API v3. The pinned verifier still checks the
original173 Release and its source identities, including historical model ZIPs;
verification does not require exposing those model URLs in the current API.

The record has these fields (the accompanying JSON Schema is normative for
shape; `minimalDownloadReadiness()` additionally checks current-asset joins):

- `schemaVersion`: `1`
- `id`: the exact catalog asset ID
- `assetVersion`: the exact catalog asset version
- `packageVersion`: canonical semver; the first packaging revision is `1.0.0`
- `contentPolicy`: `asset-files-required-dependencies-single-notice-v1`
- `noticeFile`: `LICENSE.txt`
- `notice`: `{filename: "LICENSE.txt", text, bytes, sha256}`. `text` is the exact
  short legal notice saved in the ZIP, including any trailing newline; bytes are
  its UTF-8 byte length. The publisher hashes those exact bytes. The notice
  combines the author, official license URL, verified asset detail URL, and any
  legally required copyright/change/disclaimer information. No new legal claims
  should be invented by the UI or batch builder.
- `url`, `bytes`, `sha256`: the verified ZIP download and its exact bytes/hash
- `sourceFiles`: `[{name, bytes, sha256}]`, exactly matching every current
  `asset.files[]` entry on those three fields, including dependencies. Order does
  not matter. Names are relative source filenames; URLs remain in `asset.files`.
- `verification`: `{state: "published-verified", releaseTag, archiveSha256}`.
  The archive hash must equal the top-level `sha256`.

The only accepted URL is:

`https://github.com/Xenoah/meshcopia/releases/download/<releaseTag>/<id>-<assetVersion>-minimal-<packageVersion>.zip`

The tag must be an explicit versioned tag. `latest`, branch URLs, different
repositories, query redirects and legacy asset URLs are rejected. The new
archive hash must differ from the corresponding legacy `full` and `models`
archives. A tag name alone is not an active binding or evidence of publication.

## Publisher gate before projection

The publisher owns verification and must complete all of the following before
writing a texture `downloads.minimal` into generated API/catalog records:

1. Pin the original asset identity/version and exact source-byte inventory.
2. Inspect the ZIP entries. They must be precisely the original relative
   filenames from `sourceFiles`, plus `LICENSE.txt`. Do not add a new `source/`
   or asset-ID wrapper. Existing relative subdirectories needed by a model stay
   unchanged. No README, metadata, preview, QA report, manifest, conversion
   report, checksum sidecar or second notice belongs in this user ZIP.
3. Verify every payload byte/hash and dependency path. Verify the single notice
   text's UTF-8 bytes/hash against both the binding and archive entry. Check its
   author, license, verified detail URL and required retained legal statements.
4. Publish a new immutable archive version, without replacing or deleting any
   legacy archive. Verify the actual public Release URL's downloaded bytes,
   archive contents and identity against the reviewed local artifact. A draft
   release, upload success, HEAD request, boolean flag, or local fixture is not
   sufficient evidence.
5. Only then emit `state: "published-verified"` and the matching archive digest.
   Persist the real verification evidence in the publication workflow, outside
   this minimal user ZIP. Invalid expected bindings should block publication.

The UI helper is synchronous and browser-safe. It validates the binding shape,
identity, URL, exact source inventory, notice UTF-8 length and digest shapes; it
does **not** fetch a Release, inspect ZIP contents, cryptographically verify the
notice text, or authenticate a publisher's claim. Its input must be the trusted,
independently verified publisher projection. An invented `verification` object
does not constitute verification.

## UI and API behavior

- Card download, detail primary ZIP and size sorting use one selector. Models
  require valid `downloads.delivery`; missing/stale FBX shows unavailable and
  unknown size, never 0 MB or an all-format fallback. Textures retain their
  verified minimal download, with no retired-archive fallback.
- The model primary ZIP is FBX plus required textures and one short LICENSE.
  A standalone FBX link is offered only when no companions are required.
- Preview GLBs and original-format files remain in the viewer and legacy-file
  disclosure. Retired Pages ZIP fields are removed. Existing Release attachments remain unchanged.
- Selection uses delivery.files for models and minimal.sourceFiles for textures.
  It makes one ZIP, one folder per asset, and one combined root LICENSE from the
  exact notices. Failure never produces a partial download. Escape/Back cancel
  active work, preserve selection and restore focus; retry starts a fresh job.
- Size estimation includes actual payload bytes, UTF-8 filenames and STORE ZIP
  overhead. Final size is Blob.size. Unknown inventory is explicitly unavailable.
- `downloadHref()` preserves external Release hosts.

## Integration with other overlays

`docs/minimal-activation.json` contains the reviewed actual activation. An empty
activation performs no network reads and adds no new catalog fields. Only after
real transport evidence exists may the publisher add the exact record below:

- `cohort`: `published173`
- `releaseTag`: `minimal-v1.0.0`
- `releaseId`: the actual positive GitHub Release ID
- `verificationCommit`: the exact successful F commit (40-character hash)
- `inventorySha256`: the actual public `minimal-inventory.json` digest
- `transportEvidenceFile`: a checked-in file below `docs/minimal-publication/`
- `transportEvidenceSha256`: the exact checked-in T-evidence file digest

The document itself has `schemaVersion: 1`, `repository: "Xenoah/meshcopia"`
and `activations`. Placeholder activation and T evidence are prohibited. The
first adapter intentionally covers only the reviewed original 173-asset cohort.
Future cohorts, including the separately published new251 assets, need their own reviewed
source/expected-data adapter using the same consumer binding contract.

Before output cleanup, `generate.mjs` calls `prepareMinimalDownloads()`. A
nonempty activation invokes `verify-minimal-activation.py`, which anonymously
fetches the real release, direct tag target, exact successful verification run,
all attachment pages, public inventory, and every ZIP. It joins the pinned T
readback evidence and F's source173/expected173 manifests; checks current and
baseline metadata, full source inventory, pinned verifier modules, dependency
closure, single legal notice and live canonical detail URL; and passes the
downloaded ZIP through the packager's strict archive validator. Only one ZIP is
stored in a temporary directory at a time, with bounded streaming reads and
exact byte/hash checks. There is no cache, environment override, fixture mode,
offline flag or skipped nonempty verifier. A transport/network failure blocks
generation before cleanup. This may add several minutes of public reads to a
nonempty build.

Each texture receives its verified minimal binding before per-asset
JSON/catalog/NDJSON are written. `check-dist.mjs` independently invokes the same
real public verifier and checks exact catalog and manifest bindings. It checks current originals and links, reconstructs every consumer FBX from built
chunks, and asserts that retired Pages ZIP files/links are absent. The historical
archive ledger remains unchanged and append-only history is still checked; old
API byte equality and regenerating all310 old ZIPs are no longer publication
requirements. No consumer ZIP is copied into Pages. Existing Releases are unchanged.

The combined candidate includes the production model-delivery gate, its baseline
and shared `docs/ASSET_PRODUCTION_RULES.md`. The generator calls that gate before
cleanup; no permissive fallback is provided if these files are missing.

The minimal FBX integration uses `docs/fbx-minimal-activation.json` and a separate
verified `api/fbx-minimal-downloads.json` projection. Only that independently
verified projection is passed to the model-delivery gate. Its two-entry FBX ZIP
has its own filename contract; model delivery binds those same verified FBX bytes explicitly for ordinary and
selected ZIPs. Old eight-entry FBX ZIPs are never labeled minimal.
See [FBX activation](fbx-minimal-activation/README.md) for exact F/R/T bindings and
the same-job, single-use prep receipt. The batch-download modules retain one
`initBatchDownload()` call alongside the existing catalog initializer.

The read-only full-site workflow `.github/workflows/verify-minimal-ui.yml`
verifies the actual ordinary activation and builds once after mandatory durable
FBX prep. `.github/workflows/verify-fbx-minimal-ui.yml` adds the current migration
gate and all-model FBX browser/download checks. Neither workflow publishes
or deploys. Both require real public bytes; fixture-only UI proof is not release
proof. Production applies the same durable prep, current-URL migration gate, original viewer, ordinary
selected-download, FBX browser, texture and size-budget gates before publishing.
The browser evidence does not claim FBX rendering or new251 site availability.

For this FBX-first candidate, `.github/workflows/verify-fbx-distribution.yml`
runs on the dedicated branch with read-only permissions. It additionally records
Release fetch diagnostics, tests missing FBX and interrupted retries, measures
the entire candidate build and keeps the capacity gate blocking. See
[the review report](FBX_DISTRIBUTION_REVIEW.md) for exact commits, results and the
unresolved hosting requirement; passing functional tests is not deployment proof.

## Publication and recovery

API v3 is a breaking download-contract migration, not a redirect promise. Callers
read the current catalog and verify its current bytes/hash fields. Old Pages ZIP
URLs may return404 after deployment. The existing static source/preview/image URLs
are still served and checked; retiring duplicate ZIPs does not remove viewer files.

The site release bundler emits only the site archive, catalog and checksums. It
does not create empty or nested old all/models/textures collections. Single-asset
consumer ZIPs remain in their existing verified Releases, and selected collections
are built in the browser. Recovery of a historical site build uses its exact Git
revision, pinned runtime and archive ledger; do not overwrite public Releases or
insert retired ZIP links into the current UI to satisfy an old compatibility test.
