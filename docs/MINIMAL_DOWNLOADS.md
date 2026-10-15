# Ordinary minimal ZIP binding

This is an optional, publisher-verified projection on each generated catalog
asset: `asset.downloads.minimal`. It applies to both models and textures. Do not
edit generated catalogs by hand. Do not add a placeholder record, a guessed
Release ID, or an unverified URL. No actual binding is included in this overlay.

## Exact contract

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
archives. The candidate tag discussed for the first release is not an active
binding or evidence of publication.

## Publisher gate before projection

The publisher owns verification and must complete all of the following before
writing `downloads.minimal` into generated API/catalog records:

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

- Card download, detail primary ZIP and size sorting use the same selector.
- A valid binding shows one `素材 ZIPをダウンロード` / `Download asset ZIP`.
  Its contents are labeled exactly as asset files, required dependencies and
  `LICENSE.txt` containing license and attribution.
- Before migration, models use the existing `downloads.models` with the label
  `3Dモデル ZIP（従来版）` / `Model ZIP (legacy)` and explicitly list both
  `LICENSE.txt` and `ATTRIBUTION.txt`. Textures use `downloads.full`, labeled
  `テクスチャ ZIP（従来版）` / `Texture ZIP (legacy)`, and explicitly list the
  preview, metadata, README and both notices. The old bytes are never labeled
  minimal. A model lacking a usable models ZIP can use an honestly labeled
  legacy full ZIP. Missing usable downloads show an unavailable state.
- No second ordinary full/models ZIP button is shown. Compatibility API fields
  and all legacy immutable archives remain untouched.
- Prominent direct original-format links are GLB, STL and STEP/STP when those
  files actually exist. OBJ/glTF companion files remain available via the ZIP
  and the existing individual-file disclosure, with a dependency warning.
- `downloadHref()` preserves the full external Release URL. Do not route it
  through the existing `local()` helper, which strips the host.
- A batch ZIP consumer must require `minimalDownloadReadiness(asset).ready`,
  join `sourceFiles` to `asset.files` by exact filename, and independently hash
  the fetched source bytes and UTF-8 notice bytes before creating its ZIP. It
  must not silently use the UI's legacy fallback for a minimal batch request.

## Integration with other overlays

`docs/minimal-activation.json` starts with an empty `activations` array. Empty
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
and `activations`. No placeholder activation or T evidence is supplied. The
first adapter intentionally covers only the reviewed original 173-asset cohort.
Future cohorts, including the requested new 232 assets, need their own reviewed
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

The generated item receives its verified minimal binding before per-asset
JSON/catalog/NDJSON are written. `check-dist.mjs` independently invokes the same
real public verifier and checks exact catalog and manifest bindings. It retains
all previous full/models ZIP hash, content, attribution and immutable-lock
checks, without trying to resolve a Release ZIP as a local Pages file. No new
ZIP is built or copied into Pages by these hooks. No original archive generator
or legacy archive bytes are changed.

The combined candidate includes the production model-delivery gate, its baseline
and shared `docs/ASSET_PRODUCTION_RULES.md`. The generator calls that gate before
cleanup; no permissive fallback is provided if these files are missing.

Old P-FBX activation is deliberately not part of this combined candidate. A
future FBX integration must pass only its independently verified projection to
the model-delivery gate. Its archive needs a separate FBX-minimal binding and
filename contract; this ordinary selector must not label an old eight-entry FBX
ZIP minimal. The combined candidate includes the batch-download modules and one
`initBatchDownload()` call alongside the existing catalog initializer.

The verification-only workflow `.github/workflows/verify-minimal-ui.yml` keeps
activation empty and uses no release or Pages permissions. It runs unit/source
checks, real public-source bulk ZIP verification and desktop/mobile fixture UI
tests. Fixture notice/readiness data remains in the browser's test context; the
workflow never writes a production binding, builds a site, publishes a release
or deploys Pages. Its browser evidence is scoped to the two tested live source
assets, and does not prove Release ZIP readback, new232 or FBX availability.
