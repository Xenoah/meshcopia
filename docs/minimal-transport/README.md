# Exact-artifact minimal package transport

This local overlay contains no `approval.json` and authorizes no external write. Source hashes and run IDs must be observed, never fabricated. F verification and R publication are separate reviewed commits/branches. Only the parent publisher performs an approved push.

## Two gates

1. F: verified source remains the original 173 assets at baseline `4ab5342568a4227215b295b40a47c27698cc930a`, with the exact 14-file additive verification overlay. The first verification commit F1 was directly on that baseline. The sole repair exception is one separately reviewed F2 commit directly on exact F1 `edab3c5dad80dc327dc34c398693a3fbff71219c`, subject to the four-path repair boundary below. Push only to `minimal/verify-existing173-v1`. The selected F must finish successfully with the exact 173-payload artifact and separate internal QA. Expected hashes must already be reviewed. F never publishes.
2. R: after reviewing the real successful F/run/attempt/artifact, add exactly the seven R paths named in transport.py directly on F. R alone contains `release-minimal.yml`, transport scripts, this runbook, `RELEASE_BODY.md` and an approved exact-artifact record. Push to `minimal/release-existing173-v1` only when publication is authorized. That push publishes; it is not a harmless preparatory action.

### Sole F2 repair boundary

F1 run `38815594106` reproduced all 173 reviewed ZIP hashes but failed artifact upload because generated ZIPs were owned by root with mode 0600. That failed run does not satisfy the successful-run/artifact gate and cannot be approved for transport.

The narrowly scoped F2 candidate makes validated, generated public ZIPs readable with mode 0644 before artifact upload. Its only modified paths relative to exact F1 are:

- `.github/workflows/verify-minimal.yml`
- `scripts/minimal-verification/verify.py`
- `scripts/minimal-verification/test_verification.py`
- `docs/minimal-verification/README.md`

F2 must have exactly F1 as its single parent, F1 must have the exact baseline as its single parent, and the cumulative baseline-to-F2 change must remain the original 14 additive files. Source assets, notices, expected ZIP hashes, packager and runtime pins remain unchanged. No other repair parent, additional repair commit, merge or changed path is permitted by this exception. F2's actual commit/run/attempt/artifact identity remains pending until observed and independently reviewed; do not substitute F1's failed run or infer an artifact digest.

Transport itself requires R to be a single-parent direct child of the exact successful F named by its approval. It does not require that F to be a direct child of the source baseline: `sourceCommit` continues to identify unchanged original assets, while `verificationCommit` binds the reviewed successful F2. Candidate preparation, workflow digest checks, artifact ownership and release target must all use that same actual F2. This documentation change creates no approval and broadens no other gate.

Do not add these R files to F. Do not push this combined overlay wholesale. The runtime source and original assets remain unchanged from F. R cannot modify an existing file, merge another parent, or alter any source/verification manifest. The ephemeral job token has contents:write and actions:read only in the release job. Checkout does not persist credentials; no new credentials/settings are created.

## Prepare a pending approval candidate

Download the exact successful Actions run JSON, artifact metadata and original artifact ZIP. Run:

```
python3 scripts/minimal-transport/prepare_approval.py --run run.json \
  --artifact-metadata artifact.json --artifact-zip artifact.zip \
  --repo <review-tree> --out candidate.json
```

It verifies the successful commit/run/attempt, artifact identity/API digest, exact174-entry artifact, every payload digest, canonical inventory and nested minimal ZIP allowlist/source/notice bytes. It emits `pending-review` only. Independently review it, full F/R diffs, release body and QA. Only a separate explicit review may save `docs/minimal-transport/approval.json` as `approved-for-transport`. Generating the candidate is not approval.

Required record: schemaVersion1, reviewStatus, repository, verificationCommit, tag, workflowPath, workflowSha256, runId, runAttempt, artifactId, artifactName, artifactSha256, inventorySha256, sourceInventorySha256, expectedManifestSha256, releaseBodySha256, approvedIds. Numeric identifiers are positive integers; SHA256 values are bare lowercase hex. Tag is `minimal-v1.0.0`. The artifact must belong to the successful original repository push on the exact verification branch.

## Release contents and safeguards

Exactly173 minimal ZIPs and one concise `minimal-inventory.json` are copied unchanged from F. No QA or additional release metadata attachments are uploaded. The inventory carries exact ZIP URLs/hashes/bytes and sourceFiles/notice text for later UI activation. It is copied verbatim, not regenerated by transport.

Existing tag or release causes a stop. Transport creates a new draft, fsyncs a journal before every consequential request, uploads each attachment once, reads and hashes every draft attachment, rechecks draft metadata/tag, then publishes with `make_latest=false`. Finally it anonymously fetches and hashes all174 public attachments and checks the tag still targets F. Authenticated requests never forward credentials to signed-blob redirects.

No retry, delete, overwrite, resume or rebuilding is implemented. An uncertain write stops immediately. Inspect its journal and current remote state before proposing a separately reviewed recovery; never blindly rerun. A post-publication anonymous readback failure does not mean publication was rolled back. An expired artifact requires a fresh explicit verification/review plan.

Internal `T-evidence.json` records status `anonymous-byte-readback-passed`, repository, tag, verificationCommit, releaseId, releaseUrl, attachmentCount174, inventorySha256, browserDownloadEvidence=`not-performed-by-transport`, and assets with name/bytes/sha256/assetId/url/anonymousReadback=true. The journal and evidence stay in a separate Actions evidence artifact. They are not appended to the immutable public release.

UI P activation is separate. It must bind actual T evidence, real anonymous release bytes and source/notice closure before enabling minimal links. Transport alone proves neither browser downloading nor application import. Old immutable ZIPs remain in place.

## Local tests

```
PYTHONPATH=<packager-overlay>/scripts /usr/bin/python3 -m unittest discover -s scripts/minimal-transport -p 'test_*.py' -v
```
