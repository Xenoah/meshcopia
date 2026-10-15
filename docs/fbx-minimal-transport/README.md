# Original 137 minimal FBX release transport

This is a separate R adapter for `fbx-minimal-v1.0.0`. It accepts only an exact,
successful minimal-F run and its two reviewed artifact envelopes. It does not
convert files, enable site links, or approve its own candidate.

## Frozen F and public contract

- Repository: `Xenoah/meshcopia`.
- Source baseline: `4ab5342568a4227215b295b40a47c27698cc930a`.
- Verification F: `83a1daedf3ad7563fa55bf0cca40ca749689e139`.
- Verification branch: `fbx/verify-minimal137-v1`.
- Workflow: `.github/workflows/verify-fbx-minimal.yml`.
- Successful run: `38817061339`, attempt `1`, job `116704284987`.
- Payload artifact: `12010989935`, 1,171,848,758 bytes,
  SHA-256 `178be79de9eec1ab7864e0abebdc4763b6f39bb0daa9a7e73c3b9d4eb9b1b70a`.
- Internal QA artifact: `12012245462`, 1,234,276 bytes,
  SHA-256 `e5b68771738c24b9087fe4380f68e8edc933e490b235df48c91c7154507ce2eb`.

These observations identify the candidate; they are not publication approval.
Recheck current run, job and unexpired artifact metadata before approval and R.
The payload artifact name is `fbx-minimal137-${F}-${runId}-${runAttempt}`; the
internal name is `fbx-minimal-internal-qa-${F}-${runId}-${runAttempt}`.

Exactly 275 flat public attachments are permitted:

1. 137 `<id>.fbx` files, byte-identical to the reviewed expected digests.
2. 137 `<id>-<assetVersion>-fbx-minimal-1.0.0.zip` files. Each ZIP has exactly two
   top-level entries: `<id>.fbx` and one short `LICENSE.txt`.
3. `fbx-minimal-inventory.json`, copied byte-for-byte from F. It is the concise
   machine inventory required for binding, not QA or production metadata.

The inventory contract is documented in
`docs/fbx-minimal-verification/ARTIFACT_CONTRACT.md`. Exact source, expected and
runtime inputs are `source137.json`, `expected137.json`, `runtime.json` in that
same directory. No QA reports, logs, receipts, schemas, scripts or extra notices
may be added to the public set. Existing immutable releases are untouched.

## Local candidate preparation, then separate review

Stage the eight R code/document files below alongside the exact F checkout.
Do not add an approval file or push R yet. Save the actual successful run JSON,
single verification job JSON and both artifact metadata responses. Obtain the
original artifact bytes and independently check their API SHA-256 digests.
If a transfer tool has a size limit, bounded parts may carry the unchanged
original outer ZIP; concatenate those exact bytes and require the original
artifact digest before this command. Split-part artifacts are never substituted
as the approved F artifact and are never release attachments.

Run without network access or credentials:

```sh
python3 scripts/fbx-minimal-transport/prepare_approval.py \
  --repo /path/to/exact-F-with-R-source \
  --run /evidence/F-run.json --job /evidence/F-job.json \
  --payload-metadata /evidence/F-payload-artifact.json \
  --qa-metadata /evidence/F-internal-artifact.json \
  --payload-zip /evidence/F-payload-artifact.zip \
  --qa-zip /evidence/F-internal-artifact.zip \
  --out /evidence/fbx-minimal-approval.pending.json
```

The command checks F source/helper bytes, run/job/artifact ownership, every
payload hash, all 137 nested two-entry ZIPs, and the entire internal QA proof.
It streams one model at a time and discards temporary media. Its new output is
always `pending-review`; it cannot publish. An existing output is not replaced.
Do not manufacture any digest or mark a candidate reviewed before these checks.

The exact approval schema is `schemaVersion: 1`, `reviewStatus`, `repository`,
`tag`, `releaseBodySha256`, `approvedIds`, and these 19 provenance fields:

```text
fCommit runId runAttempt jobId workflowPath workflowSha256
payloadArtifactId payloadArtifactName payloadArtifactSha256
qaArtifactId qaArtifactName qaArtifactSha256
inventorySha256 qaSummarySha256 qaRuntimeSha256 qaPilotGateSha256
sourceInventorySha256 expectedManifestSha256 runtimeSha256
```

IDs/attempt are positive integers; `approvedIds` is the complete sorted 137-ID
cohort. Unknown fields fail. Reviewer approval must cover exact F/run/attempt/job,
both original artifact IDs/digests, inventory and internal component digests,
all source/runtime/code pins and the release body. Only after independent review
may the publisher copy the candidate as
`docs/fbx-minimal-transport/approval.json` and change only `reviewStatus` to
`approved-for-transport`.

## R commit and execution

R must have exactly one parent, the approved F, on
`fbx/release-minimal137-v1`. Only these nine added regular mode-100644 paths are
allowed; no modifications to existing F or source files:

```text
.github/workflows/release-fbx-minimal.yml
scripts/fbx-minimal-transport/transport.py
scripts/fbx-minimal-transport/qa.py
scripts/fbx-minimal-transport/prepare_approval.py
scripts/fbx-minimal-transport/test_transport.py
scripts/fbx-minimal-transport/test_qa.py
docs/fbx-minimal-transport/README.md
docs/fbx-minimal-transport/RELEASE_BODY.md
docs/fbx-minimal-transport/approval.json
```

Do not copy `__pycache__`, local artifacts, QA or generated media into R. Run:

```sh
python3 -m unittest discover -s scripts/fbx-minimal-transport -p 'test_*.py' -v
```

The workflow grants `contents: write` and `actions: read` only to its release
job; the ephemeral token is passed only to the transport step. Checkout does not
persist credentials. No settings or stored credentials are changed. R uses
stdlib Python for byte verification, not Blender or the packaging writer; the
exact F conversion/runtime/binary/helper identities remain checked from proof.

R checks a clean, non-shallow/non-promisor checkout with Git replacements/grafts
disabled, the exact nine-path direct-parent change, every fixed F source file,
all pinned support/recipe files and original GLB/metadata bytes against baseline.
It observes current run/job/both artifacts before download and again after full
local validation. Every required verification and upload job step must succeed.

Only when the tag and release are both absent does R create a draft targeting F.
It uploads exactly the 275 files, verifies every draft byte readback and digest,
rechecks draft metadata and any tag target, then publishes with `make_latest:
false`. It verifies the final tag points directly to F and anonymously downloads
all 275 public attachments for exact byte/hash checks. A successful create,
upload or publish response alone is never treated as completed publication.

Every consequential request is journaled and fsynced before it is made. Network
writes are never automatically retried. On an uncertain result, stop and inspect
the saved journal and current release state. Do not rerun to resume, overwrite,
replace or delete an existing tag/release/asset; require a separately reviewed
recovery plan. A partial draft or published release is a blocker, not permission
to repair it automatically.

## Internal QA boundary and resource bounds

The separate internal ZIP must contain exactly 414 ordinary JSON files:
`qa.json`, `runtime.json`, `pilot-gate.json`, plus each ID's `receipt.json`,
`fresh/roundtrip-report.json`, and `fresh/materialized-imported-images.json`.
No directory records, links, traversal, duplicates/case collisions, encrypted or
unsupported-compression entries are accepted. Total expanded internal data is
bounded to 256 MiB and each JSON to 16 MiB. Public files are each bounded to
95 MiB and the outer payload to 3 GiB. Outer hashes, reads and uploads stream;
only one bounded raw FBX is held for container parsing at a time.

F freshly ran pinned Blender conversion/reimport and materialized actual packed
imported images, then independently checked their live bytes. R rechecks exact
fresh report bindings, strict boolean CPU flags, numeric geometry/material
measurements, axes/units, independent raw FBX embedded-image bytes, the wrapper
hash/materialization closure and package receipts. All three F live-closure
projection flags must be typed true. R does not possess the temporary live
image files and does not claim another Blender run or fresh materialization.
Its evidence labels that part `attested-by-exact-successful-F`.

Pure local reuse API, with no token, network calls or conversion:

```python
verify_internal_qa(archive, approval, source, expected, runtime, repo,
                   fbx_directory=directory)
# Or payload_archive=original_payload_zip; exactly one provider is required.
```

Import it from `scripts/fbx-minimal-transport/qa.py` in a fresh Python process
alongside the exact pinned F helper modules and schemas. Callers must first
verify source/code hashes and actual F/job/artifact ownership. A provider's FBX
bytes are independently hashed. The helper returns an explicit internal proof;
it does not issue approval or validate browser behavior.

## T evidence and later site activation

The Actions-only T artifact contains `T-evidence.json` and `journal.jsonl`.
Neither is a public release attachment. Successful T JSON has exact top-level
keys `schemaVersion`, `status`, `repository`, `tag`, `fCommit`, `releaseId`,
`releaseUrl`, `attachmentCount`, `inventorySha256`, `browserDownloadEvidence`,
`assets`, `provenance`, `internalQaVerification`, `transportExecution`. Status is
`anonymous-byte-readback-passed`; count is 275; browser evidence is explicitly
`not-performed-by-transport`. Each asset has `name`, `bytes`, `sha256`, `assetId`,
`url`, `anonymousReadback: true`. Provenance has the 19 approval keys above.

Internal proof has `status: exact-internal-qa-rechecked`, `models: 137`,
`qaArtifactSha256`, `qaSummarySha256`,
`freshImportedImageProof: attested-by-exact-successful-F`,
`rawReportAndContainerRechecked: true`, `blenderRerunByTransport: false`.

`transportExecution` has exactly `commit`, `runId`, `runAttempt`, `jobId`,
`workflowPath`, `workflowSha256`, `approvalSha256`, `adapterSha256`. The workflow
is `.github/workflows/release-fbx-minimal.yml`; `adapterSha256` has exactly the
repository-relative `scripts/fbx-minimal-transport/transport.py` and
`scripts/fbx-minimal-transport/qa.py` keys. These are SHA-256 hashes of actual R
checkout bytes. R obtains its current run/attempt and unique transport job from
the explicit run-attempt API, requires matching repository/branch/head/workflow
and in-progress status, and records the returned job ID. This record does not
assert eventual success; P must independently observe completed success later.

Initial R always downloads and fully revalidates both exact original F
artifacts. Initial P verification likewise uses the full internal QA artifact
and exact public bytes. A dedicated authorized read-only preparation step may
obtain the exact Actions artifact, run the pure helper, discard raw QA and hand
a same-job input/HEAD-bound local receipt to the site build. No token goes to
the helper or build, and no raw QA is committed or published.

Later P builds may explicitly select reviewed durable-attestation mode so they
do not depend on temporary Actions QA artifact retention. This is not a fallback
on HTTP errors or expiry. P must authenticate the exact successful R run,
attempt and job, require all three workflow steps (tests, transport/readback,
evidence upload) to succeed, compare Git-pinned reviewed R workflow/helpers and
approval hashes, and require T provenance to equal that approval. The pinned
code's initial full raw-QA verification is the attestation being reused; T flags
alone are insufficient. Every build must still independently read all 275
release attachments and check exact source, expected, runtime and payload/notice
identities and immutable tag history. Durable mode does not claim renewed raw-QA
inspection, fresh Blender execution or fresh imported-image materialization.
Availability remains unset until real T and P/browser evidence pass. Consumer
limitations in the release body must stay visible and accurate.
