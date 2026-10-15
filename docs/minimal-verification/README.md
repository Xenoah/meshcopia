# Original173 minimal package verification

This is verification-only preparation for 137 existing public models and 36 existing public textures at source commit `4ab5342568a4227215b295b40a47c27698cc930a`. It does not publish or activate download links. New232 assets and FBX packages require separate cohorts and review. Old ZIPs, raw source bytes, asset versions and archive-lock records remain untouched.

## Inputs and boundaries

Create one additive commit F directly on that baseline, on `minimal/verify-existing173-v1`. Add exactly the 14 files listed by `allowed-f-paths.json`, including the separately prepared `scripts/minimal_packages.py`, `scripts/minimal_notices.py` and `tests/test_minimal_packages.py`. Do not include release workflow, approval, UI, old FBX metadata, media, cached archives or reference receipts. `source173.json` and `expected173.json` contain only concise pinned inputs, notices and output hashes. The expected manifest must be independently reviewed and changed from `pending-review` to `final-reviewed` before F. No script grants that review automatically.

`source173.json` binds baseline metadata, the entire original source directory, the selected payload closure, exact merged LICENSE.txt text and SHA256, notice-generator source and immutable archive lock. Notices are reproducible from pinned baseline templates; local receipt review separately confirmed equality to the notices extracted from previous immutable archives. `expected173.json` binds source173, the packager and notice-generator scripts, runtime.json and each output ZIP filename/size/hash.

Preparation command, using one existing set of reference receipts rather than rebuilding:

```
PYTHONPATH=<packager-overlay>/scripts /usr/bin/python3 scripts/minimal-verification/prepare_manifests.py \
  --repo <baseline-checkout> --out <new-candidate-directory> \
  --runtime docs/minimal-verification/runtime.json --receipts <original173-receipts.json>
```

Omit `--receipts` only when a new full reference pass is explicitly needed. Outputs remain pending review; only temporary ZIPs are produced and discarded. Paths in local plans/receipts never enter public ZIPs or the public inventory.

## Reproduction and artifacts

CI checks lineage, exact additive path set, unchanged baseline source blobs, notice generation, reviewed input hashes and source allowlists before runtime setup. It runs inside the pinned official Debian image, installs only exact hash-checked Python3.13 and zlib packages, and checks Python3.13.5/zlib1.3.1 plus interpreter/libz binary hashes. No Blender or new credential is needed. Package writer uses pinned raw DEFLATE and canonical ZIP serialization, retains only top-level asset files, required relative dependencies and one LICENSE.txt, then strictly verifies member bytes and clean extraction/dependency closure. Reproduced bytes must match every reviewed expected hash.

The successful payload Actions artifact `minimal-existing173-<F>-<runId>-<attempt>` contains exactly 174 flat files:173 `<id>-<assetVersion>-minimal-1.0.0.zip` and `minimal-inventory.json`. This one inventory contains the exact public URL, ZIP size/hash, source files and notice for binding download buttons later. It also binds source commit, F, run and manifest hashes. No QA, manifests, scripts or metadata are included inside consumer ZIPs. QA stays in a distinct internal Actions artifact. Failure never uploads partial ZIPs or enables availability.

A successful verification run is not transport approval. Observe and independently review the exact run, attempt, artifact ID, original artifact digest and inventory digest before preparing a separate R commit. See the transport runbook, which belongs only to R.
