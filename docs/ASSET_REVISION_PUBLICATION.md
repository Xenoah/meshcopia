# Starter repairs and refrigerator production activation

The user approved new Release publication, PR, normal main merge and Pages
publication after reviewing commit `4d537fad080c50ec18f3e515695f4f9f582351c5`
and successful review CI [39129140683](https://github.com/Xenoah/meshcopia/actions/runs/39129140683).
This authorization supersedes the historical review's pending-approval wording.

The fixed tag `cohort-repair-appliances-v1.0.0` points to that reviewed commit.
It contains exactly three FBXs, three minimal ZIPs and `revision-inventory.json`.
The ZIPs contain one FBX and one short LICENSE.txt; the refrigerator's necessary
atlas is embedded. GLB previews, Blender production files and QA stay outside
consumer ZIPs. Existing Releases are never edited, deleted or re-uploaded.

The original454 catalog, old sources and frozen original137/cohort adapters
remain unchanged. They are verified first. The separate revision adapter then
replaces garden-arch and wayfinding-sign with version1.0.2 and adds
household-two-door-refrigerator1.0.0. All454 previous IDs, including vehicles and
the front-loading washer, remain: 455 public assets, 419 models, 36 textures.
Versioned GLB and thumbnail URLs preserve old source and thumbnail bytes.
Historical arch/sign download-data manifests and chunks are also retained;
the active inventory binds only the revised FBX.

Each production build runs, in order:

```sh
npm ci
python3 scripts/prepare-fbx-minimal-activation.py --repo "$PWD" --verification-mode durable-transport-attestation
python3 scripts/asset-revisions/prepare_existing_cohorts.py --repo "$PWD"
python3 scripts/asset-revisions/prepare_activation.py
npm run check
node scripts/measure-distribution.mjs
node scripts/asset-revisions/test-review-browser.mjs --production
```

The revision prep checks successful exact review/transport CI, immutable tag,
Release/attachment identities, locked source/FBX/archive/notice hashes, actual
anonymous attachment bytes and exact ZIP members. Its receipt binds HEAD,
Actions run/attempt/job, every adapter/input, metadata and complete source
inventory. Generation consumes it once. Neither a stored JSON readiness flag
nor an unpublished review package can activate a production model.

Ordinary download uses the verified immutable Release ZIP. Selected mixed ZIPs
use hash-checked same-origin gzip chunks, model-specific folders and one common
LICENSE.txt. Release navigation is not treated as proof of cross-origin fetch.
No raw FBX or distribution ZIP is copied into Pages. All of dist, including
hidden files, is measured against the unchanged950,000,000-byte gate.
The earlier full review build was936,375,610bytes; production size must be
recorded by its own successful build, never inferred from the review artifact.

Publication requires successful production activation CI, normal PR merge and
successful main publication plus post-deployment verification. The live test
loads actual production bytes without remapping the site, checks Japanese
冷蔵庫/洗濯機 search, four model previews, five ordinary ZIPs and the mixed ZIP
on desktop/mobile, cancellation, retry, Back/Escape and selection clearing.
Old arch/sign source URLs are checked byte-for-byte. The Pages deployment SHA
must match main and the verified artifact. Review HTML is never deployable.

Evidence paths: `docs/asset-revisions/publication.json`,
`docs/asset-revisions/revision-inventory.json`, `docs/asset-revision-activation.json`;
CI outputs include `test-results/fbx-distribution-size.json` and
`test-results/asset-revisions/{production-browser,live-browser}/report.json`.

Remaining coverage limits: Blender clean-import and Chromium software-WebGL
rendering do not certify Unity/Godot, real Safari, physics, manufacture or
printing. FBX Phong does not reproduce all glTF PBR behavior. The refrigerator
is a static editable asset; its doors are not an application simulation.
