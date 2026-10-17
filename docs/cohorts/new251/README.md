# Cohort new251

The 232 original city models staged in source stages 1–6 and 19 street objects
authored by Claude in stage 7 (batches 059–060), all as drafts on `main`.
Every model is published at version 1.0.0 with its existing GLB and STL bytes.

- `source.json` binds each model's final public metadata (only `status` changed
  from `draft`), complete source inventory, raw-hosting stage commit and the
  two retained `LICENSE.txt` notices (ordinary ZIP and FBX ZIP).
- `expected.json` starts as `discovery`. After a successful discovery F run its
  reviewed FBX/ZIP sizes and SHA-256 are pinned as `reproduced-final`; the final
  F run must reproduce every byte.

See [docs/COHORT_PUBLICATION.md](../../COHORT_PUBLICATION.md) for the F → R → P
process. This directory is review input, not an approval or availability record.
