# Minimal FBX F → R/P contract

## F identity and envelope

- Base and exact parent: `4ab5342568a4227215b295b40a47c27698cc930a`.
- Branch: `fbx/verify-minimal137-v1`.
- Workflow: `.github/workflows/verify-fbx-minimal.yml`.
- Payload artifact: `fbx-minimal137-${F}-${runId}-${runAttempt}`.
- Separate internal artifact: `fbx-minimal-internal-qa-${F}-${runId}-${runAttempt}`.
- Both artifact IDs and GitHub artifact digests appear in the successful run's
  step summary. Pin the exact F/run/attempt and artifact envelope in approval.
  Require the whole job to conclude successfully, including separate QA upload.

## Payload artifact: exactly 275 ordinary top-level files

- 137 `<id>.fbx`, each byte-identical to its reviewed v4 expected digest.
- 137 `<id>-<assetVersion>-fbx-minimal-1.0.0.zip`, each containing exactly the
  top-level FBX and one short LICENSE.txt, with no directories or other entries.
- One `fbx-minimal-inventory.json`.

The inventory has schemaVersion 1 and contract
`meshcopia-fbx-minimal-artifact/1`. It binds repository, F/source commit, workflow,
run ID/attempt, cohort `published137`, packageVersion `1.0.0`, pipeline SHA-256,
source inventory/expected manifest/runtime hashes and 137 ID-sorted `models`.
Each model contains exactly id, version, sourceGlbSha256, fbx, archive, notice.
`fbx` and `archive` contain filename, bytes, sha256. `notice` contains filename
(always LICENSE.txt), bytes, sha256 and exact retained UTF-8 text. There are no
release URLs until a separate R policy chooses a new immutable release tag.

## Required next R/P adapter behavior

Create a new minimal-F adapter. Do not weaken the legacy eight-entry validator,
reuse its `qa.json` expectations, or change frozen historical archives.

1. Independently verify approved F/run/attempt/job success and both returned
   artifact IDs/digests. Pin the exact inventory byte digest from that run.
2. Extract the payload artifact safely. Reject directories, symlinks, duplicate
   or case-colliding names, traversal, extras/missing files and oversized data.
3. Check the inventory's exact schema and equality with committed F source,
   expected and runtime identities. Check every FBX and ZIP byte count/hash.
4. Independently parse each ZIP, requiring exactly `<id>.fbx` and LICENSE.txt,
   no wrapper, and exact FBX/notice bytes. Never select files by loose glob.
5. Verify the separate QA artifact has the same F/source/run/attempt, exactly
   the 137 source/output bindings, all strict two-entry package checks and
   completed fresh clean-import image closure. Treat raw QA as internal evidence;
   do not move its reports, logs, schemas or receipts into consumer ZIPs/releases.
6. Publish only the reviewed immutable payload set under the separately approved
   new tag; never overwrite a legacy version/hash. Do not publish QA as a release
   asset. Whether the concise inventory is retained in the release or solely
   transport evidence must be an explicit R policy choice.
7. Anonymous-readback every intended release asset and bind the receipt to its
   actual remote bytes before P can enable availability/UI links. P must use
   the new minimal filenames and release-hosted URL resolver, preserve protected
   historical links and accurately scope browser/Blender/consumer claims.

This document is a handoff contract, not an implemented or approved publisher.
F has read-only contents permissions and no main/tag/release/Pages write step.
