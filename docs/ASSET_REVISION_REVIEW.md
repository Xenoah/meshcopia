# Starter winding repairs and household refrigerator — unpublished review

Base: `fd595dfdc8b17fe515a618bf2f309e9cc61a7491` (454 public assets).
Branch: `codex/repair-starters-add-appliances`. No merge, deployment or Release
creation/update is authorized by this review. No vehicle or unrelated asset is
removed. All `content/assets` files and frozen original137/new-cohort adapters
remain byte-for-byte unchanged.

## Diagnosis and candidates

The eight starters came from `scripts/create-starter-assets.py`. Their GLB
materials used double-sided rendering. Their stored normals agree with triangle
winding; none has a negative node/object transform. The published FBXs were
reproduced byte-for-byte from the existing frozen converter, so this diagnosis
also covers those exact FBX payloads, without claiming a new Release fetch.

| Asset | Diagnosis / action | Candidate |
| --- | --- | --- |
| studio-chair | Closed outward surfaces; retained | unchanged 1.0.1 |
| atelier-lamp | Closed outward shell including inner shade; retained | unchanged 1.0.1 |
| slat-bench | Closed outward boards/legs; retained | unchanged 1.0.1 |
| terracotta-planter | Inner and outer pot walls correctly oriented; retained | unchanged 1.0.1 |
| market-crate | Closed outward individual boards; openings retained | unchanged 1.0.1 |
| garden-arch | Curved strip wound inward; reverse that strip only. Remove four concealed pillar-top triangles at matching interfaces, retaining all coordinates and the walk-through opening | 1.0.2, 212 triangles |
| field-terminal | Closed outward components; retained | unchanged 1.0.1 |
| wayfinding-sign | `vertical=True` swaps Y/Z (a reflection), but the generator did not reverse the ring faces. Reverse only the ring; retain positions and its opening | 1.0.2, 1,420 triangles |

Do not automatically reverse every mesh or infer orientation of an open surface
from signed volume alone. Inspection welds position copies only for topology
analysis; it never edits originals. The repaired arch forms one continuous
closed surface, rather than adding coincident caps at its pillar interfaces.

`city-front-loading-washing-machine` is already public in new251. It is a
22,096-triangle front-loading washer with a real open drum, separate open door,
gasket, controls and rear details. Its current FBX is retained and checked against
the immutable expected hash. Its existing public detail page is
<https://xenoah.github.io/meshcopia/assets/city-front-loading-washing-machine/>.
The current category is `urban`; search all assets for the Japanese term `洗濯機`
or use <https://xenoah.github.io/meshcopia/?q=%E6%B4%97%E6%BF%AF%E6%A9%9F#catalog>.
The live-site browser probe verifies listing → Japanese search → detail → GLB,
without intercepting requests or substituting a local catalog.
No separate unpublished household set was found in
the workspace or remote branch inventory. `city-refrigerated-display-case` is
an existing commercial display case, not a household refrigerator.

The new `household-two-door-refrigerator` candidate has 11,432 triangles,
122 mesh objects and overall Y-up dimensions **0.601 × 1.850 × 0.775 m**,
including hinges/handles/rear hardware. It has an actual empty food compartment,
shelves, crispers, door pockets, gaskets, handles, compressor, condenser, pipes,
stowed cable and feet. The closed default pose retains an editable upper-door
hinge. QA opens that same imported hinge around world up; this is not a separate
interior mockup. One original 512×512 control-panel atlas is embedded. Shelves
use opaque tinted material; no operating appliance logic is claimed.

## Storage and verification

`asset-revisions/repair-appliances-v1/<id>/` is **inactive staging**, outside the
production catalog loader. `asset.json` describes the proposed public entry;
its presence here is not publication. `source/` retains GLB previews,
`production/` retains editable Blender files and original artwork, and the
candidate lock binds metadata, source, FBX, ZIP and notice hashes.

The unchanged converter runs in Blender 4.3.2 with its pinned NumPy/CPU/zlib
environment. Clean FBX reimport checks positions, winding, normals, UVs,
materials, image pixels, axes, dimensions and isolated embedded-image recovery.
Additional import audits inspect closed components and world transforms.
The consumer ZIP contains exactly `<id>.fbx` and one short `LICENSE.txt`; the
control atlas is embedded in the FBX. No GLB, blend, metadata or QA goes into ZIPs.

Three.js GLTFLoader and FBXLoader renders force **every material to FrontSide**.
Texture loads complete before capture. Exterior, rear/underside and actual
cavity views are kept in CI artifacts. FBX materials are not lossless glTF PBR;
the frozen FBX exporter writes `CullingOff`, so targets may need culling enabled.
The geometry is checked with culling enabled rather than relying on that flag.
Unity, Godot, manufacturing, collision/LOD and 3D printing are not certified.

Review images: [starter before/after](asset-revisions/starter-winding-comparison.webp)
and [actual appliance GLB/FBX](asset-revisions/appliances-fbx-glb.webp).
These sheets use local actual renders; fresh CI captures remain separate artifacts.

## Separate review build

1. Run `.github/workflows/verify-asset-revisions.yml` on the dedicated branch.
2. Reproduce the eight original FBXs and washer, generate the three unpublished
   candidate FBXs/ZIPs, verify `candidate-lock.json`, import and render them.
3. Run the **ordinary mandatory anonymous original137 and cohort prep**, then
   `npm run check`, against the unchanged 454-item production catalog.
   The review workflow invokes the unchanged cohort verifier through a wrapper
   that reports sanitized HTTP status/host/path and retries the entire strict
   prep at most three times for transient server/rate-limit errors. Verification
   failures are never retried as success or replaced by cached evidence.
4. Measure the actual complete baseline dist. Run
   `node scripts/asset-revisions/build-review.mjs` only after that successful build.
5. The review overlay preserves all 454 existing IDs and old source URLs,
   replaces only two versions and adds the refrigerator (455 total). It retains
   old chunks and adds candidate ZIPs/FBXs and versioned previews/thumbnails.
6. The explicit review build has a visible unpublished banner, noindex and a
   distinct `3.0.0-review` catalog. `local-review-verified` has no Release tag and
   is rejected by normal production delivery checks. Production generation
   refuses `PUBLIC_ASSET_REVIEW=1`; do not use it as a deployment configuration.
7. Browser tests use the actual built UI/bytes at the canonical origin, checking
   ordinary ZIPs, mixed candidate/washer/texture bulk ZIPs, one common notice,
   exact byte counts, cancellation, failure/retry, Back/Escape, deselection,
   search, mobile, actual previews and preserved old source URL hashes.
8. Enforce the unchanged **950,000,000-byte** full-dist budget. This review
   includes extra standalone candidate FBXs/ZIPs and preserves replaced chunks,
   so its size is conservative. Measure it; do not infer capacity from GLBs alone.
9. Save model QA and the complete verified build as CI artifacts before browser
   work. A separate dependent runner downloads that exact commit's build and
   performs the browser tests. This preserves evidence if a runner is stopped;
   artifact upload does not publish the candidate to Pages or Releases.

The last published dist was 933,823,099 bytes, with 16,176,901 bytes of operating
headroom. New measured baseline/candidate reports are CI artifacts; do not reuse
these historical numbers as an actual measurement of the candidate.

## Before publication (separate approval)

- Review the exact branch commit, render evidence, fresh tests and full sizes.
- Publish the locked new versions as a **new immutable Release** via separately
  authorized F/R work. Never replace existing attachments or tags.
- Add a revision-specific activation binding backed by fresh anonymous fetches
  and current metadata/source inventories. Keep original137 and cohort adapters
  frozen; do not relax their matching or substitute review evidence for publication.
- Activate the approved revisions outside the review-only mechanism, preserve
  old source URLs, repeat normal/full-browser/capacity checks, and only then
  request the separately authorized merge/deployment and post-deployment check.

The new refrigerator's intended detail URL is not claimed to exist publicly yet.
