# Original 137 FBX minimal verification

This independent verification branch starts directly at immutable baseline
`4ab5342568a4227215b295b40a47c27698cc930a`. It does not resume the abandoned
metadata-heavy F tree or modify the frozen legacy F/R/P eight-entry contract.
The exact branch is `fbx/verify-minimal137-v1`; its sole workflow is
`.github/workflows/verify-fbx-minimal.yml`. Publication is a separate reviewed step.

The concise manifests bind the exact 137 original published models, source GLB
and metadata hashes, unchanged v4 FBX hashes, previously reviewed minimal ZIP
hashes, and one short retained notice each. No 959 legacy metadata package inputs
are needed. The 310 protected original archive locks and all baseline files stay
unchanged. The existing 173 ordinary minimal-package branch is independent.

## Verification sequence

1. Before Blender, require the exact repo/ref/push, direct baseline parent, no
   shallow/partial/promisor/grafted checkout, clean tracked state, and the exact
   additive ordinary-file allowlist. Check pinned GLBs, baseline metadata,
   baseline notice generators, notices, archive lock, runtime and helper hashes.
2. In the digest-pinned official Debian image, verify downloaded package hashes,
   installed Blender/exporter files, Python/zlib binaries and exact versions.
3. Set PYTHONHASHSEED=0 and the frozen NumPy disabled-feature list before Blender
   starts. The probe and converter check actual disabled feature flags. No
   opportunistic host-dependent CPU path or fallback recipe is allowed.
4. Freshly convert every source with the unchanged v4 converter, normalizer and
   deterministic exporter. Materialize actual clean-import packed image bytes
   with the unchanged evidence wrapper. Require exact reviewed FBX bytes/hashes.
5. Run the unchanged independent report adapter: source/output/recipe/runtime
   binding; geometry, normals, UVs, material parameters and actual assignments;
   dimensions, orientation and units; embedded images, dependency closure and
   materialized imported image hashes. Numerical per-corner measurements are
   converter-attested, not independently remeasured by the adapter.
6. Use the unchanged minimal packager to make exactly `<id>.fbx` + `LICENSE.txt`.
   It verifies serialized archive bytes, entry allowlist, payload hashes, safe
   extraction and dependencies. Require the reviewed new minimal ZIP hash/size.
   The clean import occurred before packaging; extraction proves identical FBX
   bytes. Do not claim a second post-ZIP application import occurred in this job.
7. After all checks, set only the verified allowlisted generated ZIPs to mode
   0644 inside Docker, so the host runner can upload root-owned temporary-file
   outputs. This does not alter archive bytes or touch sources/secrets.
   Upload 275 payload/inventory files as one review artifact. Upload raw reports,
   materialization records, receipts and QA separately as an internal review
   artifact. Internal denotes purpose, not a promise of private GitHub access.
   No raw sources, extracted textures, logs or partial payloads are uploaded.

The v4 recipe remains
`9c14ed64ff019ef1fc6cdf4d86df1c4504f1cd1a675c4cb1bd4ac3c2f37cb500`.
Only the street-tree FBX changed from v3. Other source/output hashes remain frozen.
Do not accept a hash mismatch by editing expected data in CI.

## Local checks

From a candidate checkout of the exact new additive F commit:

```sh
python3 -m unittest discover -s tests -p test_minimal_packages.py -v
python3 -m unittest discover -s scripts/fbx-minimal-verification -p 'test_*.py' -v
GITHUB_REPOSITORY=Xenoah/meshcopia \
GITHUB_REF=refs/heads/fbx/verify-minimal137-v1 GITHUB_EVENT_NAME=push \
GITHUB_SHA="$(git rev-parse HEAD)" \
python3 scripts/fbx-minimal-verification/verify.py --repo "$PWD" \
  --output /tmp/unused-fbx-minimal-preflight --preflight-only
```

Packaging tests require zlib 1.3.1. Preflight performs no conversion and creates no
output. Full workflow execution is still required before calling F successful.
Baseline-only or overlay-only directories cannot satisfy a commit preflight.
New commits with a different parent or changed-path set require new review.

## Later new-232 path

Do not regenerate the 232 prepared models for a package-layout change. A separate
new-232 adapter should bind each prepared source/version, its existing v3 FBX and
hash-matched QA, then use the same strict minimal packager and retained notices.
The independent survey found no CPU-sensitive path in that 232-model recipe;
this is not permission to substitute v3 QA into this original-137 v4 verifier.
Use the matching v3 validator/runtime contract, verify source/output/QA hashes and
materialized clean-import evidence, and fail closed where evidence is absent.
Keep the two cohort/recipe manifests explicit. No 232 conversion or publication
is part of this overlay. Existing prepared FBX bytes are the reusable outputs.
