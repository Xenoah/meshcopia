# FBX distribution candidate (not deployed)

Base: `7262f3e34559234de636cd5351d89fc733df008d` (stage10).
Implementation branch: `codex/fbx-distribution`. Main, Pages and existing Releases
are not changed by this branch's read-only workflow.

## Scope and measured constraints

- Site activation remains original173: 137 models and 36 standalone textures.
- new251 F run39035757342 and transfer39036941196 were both successful when
  rechecked. Release `cohort-new251-v1.0.0` has754 public attachments. This is
  separate from site activation. The 30 source-only stage8–10 additions are not
  covered by that251. No old232 candidate is used.
- Baseline full Astro build: **939,340,180 bytes / 1,197 files**, measured from
  actual `dist/` in [baseline job117422108922](https://github.com/Xenoah/meshcopia/actions/runs/39041621871/job/117422108922).
  Remaining operational headroom: **10,659,820 bytes** below950,000,000.
- Verified existing FBX payload total: **599,103,132 bytes**. Existing immutable
  FBX ZIP total: **572,507,759 bytes**. Reusing those ZIP URLs avoids making
  duplicate consumer archives; original full/models archives remain unchanged.
- Content-defined gzip chunks reduce the extra FBX payload storage to roughly
  **138.4 MB**, plus small manifests. This still exceeds current Pages headroom.
- Actual anonymous browser fetch of the Release API failed in
  [CI39041367750](https://github.com/Xenoah/meshcopia/actions/runs/39041367750).
  Therefore the shipped builder never fetches a Release URL or assumes its CORS.

## Implementation and verification

`downloads.delivery` binds ordinary FBX ZIPs and exact batch payloads to the
existing successful source/version-bound verification. Root `files`, previewUrl,
legacy ZIP fields and archive lock remain compatible. Textures keep their image
downloads. A missing/stale FBX disables model delivery and shows unknown size.

Batch transport reconstructs unchanged FBX from same-site gzip chunks; no new
export or importer claim is made. Final ZIP is uncompressed STORE with one model
folder per selection and one exact combined LICENSE. Size estimates include ZIP
headers and UTF-8 names, and the finished UI uses actual Blob.size.

The read-only workflow runs mandatory anonymous prep, all unit tests, build,
check-dist reconstruction of every FBX, actual single/selected browser ZIPs,
cancel/retry/Back/remove/clear/mobile/no-JS and viewer/texture regressions. Its
final capacity gate must remain blocking. Results are recorded in CI artifacts;
fixture tests do not establish publication or live-site availability.

## Required before publication

1. Review the candidate and its exact final CI evidence. No automatic merge or
   deploy is requested by this change.
2. Resolve payload hosting: current Pages cannot retain every legacy URL and
   accommodate all new FBX data, even after deduplication. Use a separately
   reviewed immutable host with actual browser CORS and byte readback, or an
   approved capacity/URL migration. Do not disable the budget, overwrite Releases,
   delete originals or silently disable large-model downloads to pass it.
3. Bind that actual transport, rerun complete size and real browser checks, then
   obtain publication authorization. No guessed hostname or future-success flag
   is included here.
4. Integrate new251 only via its own reviewed adapter and capacity plan after
   reconciling Claude's latest main. No new251 or stage8–10 publication is claimed.

Local cloud network access blocks GitHub API and live Pages requests. Full real
release and browser verification therefore runs in read-only GitHub Actions.
The cloud workspace still runs source, unit and local browser fixture tests.
