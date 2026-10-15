# Asset production and delivery rules

This is the shared production specification for human contributors, Codex,
Claude and other development tools. Read it together with repository AGENTS.md.
It does not change authentication, authorization or publishing permissions.

## Complete model delivery

Every new model generation task must deliver FBX alongside the existing GLB/STL
and any other requested formats. “Together” means one complete deliverable set,
not that export processes must run at the same instant. A successful GLB export
alone is not completion. Preserve originals and their explicit license/provenance.

Use the reviewed conversion/export recipe. Reuse already verified, unchanged
outputs when their source and output hashes still match; do not regenerate a
whole collection merely to change package layout or documentation.

Before marking a model deliverable complete, import its FBX into a clean scene
and verify actual material/texture assignments, dimensions and units, up/forward
axis orientation, geometry and image dependency closure. Record the source/output
hashes, exact tool/recipe versions, measured results and known limitations in
internal verification evidence. A successful exporter exit is insufficient.
Texture/material approximations must be stated truthfully on the asset page.
Do not claim Unity/Unreal/FPS or browser FBX rendering without actual tests.

New or updated model publication must have a source/version-bound verified FBX
in the deliverable set. Historical unchanged published assets are not silently
rejected or rewritten; their original bytes and links remain protected while
verified alternate formats are added. Draft source-preparation stages may remain
unpublished until the complete deliverable is verified. Existing prepared models
may reuse their hash-matched FBX and QA evidence.

## Single-asset download ZIP

- Put usable model files or declared texture maps at the ZIP top level.
- Retain subdirectories only where actual model/texture references require them.
  Never add an asset-name wrapper, `source/` wrapper or double root just for packaging.
- Include exactly one short `LICENSE.txt`. Preserve supplied creator/designated
  credits, actual copyright, license name and official URL, a verified asset
  detail/download-source URL, warranty-disclaimer reference, and previous/current
  modification notices required by the license. Do not invent copyright claims.
- Exclude README, previews, asset metadata, conversion/QA reports, hash lists,
  generator scripts and other development files. Keep those originals and
  internal verification records separately; excluding them is not deleting them.
- Do not re-encode/re-export payloads just to simplify the ZIP. Preserve payload
  bytes and required relative references. Reject unsafe paths, symlinks, duplicate
  or case-colliding names, missing dependencies and unexpected extra entries.
- Verify actual archive bytes/member hashes, safe extraction and dependency
  resolution. Exercise representative clean imports from the extracted packages;
  retain and accurately scope the evidence.

For CC BY 4.0, consult the actual supplied notices and official Sections 3(a) and 5:
https://creativecommons.org/licenses/by/4.0/legalcode.en
A short notice may link to the license; it must not drop supplied attribution,
required modification history or disclaimer references. Never leave references
to removed local documentation files in the notice.

## Multiple selected assets: one ZIP

Generate one ZIP, not a ZIP containing other ZIPs. Use one folder per asset to
avoid filename collisions. Keep a single root `LICENSE.txt` that aggregates the
exact retained notice for every selected asset, including each source URL.
Do not duplicate LICENSE inside every folder. Verify every fetched source and
notice byte count/hash before including it. No silent partial archive on error.

Show the selected count at the upper right; activating it opens the selection
list with individual removal, clear and download controls. Cover keyboard,
Escape/Back, mobile layout, repeated activation, cancellation, network failure,
retry, memory/size limits and download correctness in actual browser tests.
No source is eligible for browser ZIP assembly until its readable URL/CORS and
identity/hash binding have been verified.

## Immutable publication and honest availability

Never overwrite an existing versioned public ZIP, release or locked archive hash.
Publish simplified packages under a new package revision and switch ordinary UI
links only after actual successful CI, anonymous byte readback and browser checks.
Keep protected historical links working. A model page should present one clear
ordinary ZIP plus appropriate self-contained format downloads, without competing
“full” and “models-only” choices. Release-hosted ZIPs must not be mistaken for
Pages-local paths. Stay within the Pages size budget.

Metadata, release records and QA assertions must describe actual verified state.
Prepared manifests, local tests and unexecuted browser fixtures are not evidence
that a release or feature is publicly available.
