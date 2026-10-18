# Meshcopia agent instructions

## Goal

Maintain a free, trustworthy asset library for humans and agents. Static Astro
site on GitHub Pages at `/meshcopia/`; assets are CC-BY-4.0. Preserve the viewer,
direct downloads, machine-readable catalog, and mobile accessibility.

## Source of truth

- `content/assets/<id>/asset.json`: metadata.
- `content/assets/<id>/source/`: actual asset files and required dependencies.
- `content/assets/<id>/preview.webp` (or another declared raster filename): an
  honest, clearly framed thumbnail of the asset, never a different concept image.
- `_inbox/<id>/`: the same structure, waiting for import.
- Generated `public/assets/`, `public/api/`, `src/data/catalog.json`, `dist/`
  must not be edited or committed.

## Add/update workflow

1. Read `docs/asset-schema.json`. Use `npm run new:asset -- <id> model|texture`.
2. Supply original asset files, a thumbnail, explicit CC-BY-4.0 permission,
   creator and generation/source provenance. Do not silently relicense NC or
   third-party assets. Do not invent verification claims.
3. For a model, report actual triangles, unit, up axis, dimensions and UV limits.
   Use verified FBX for consumer delivery, with required textures. Retain GLB
   for browser previews and production originals/QA separately. STL/OBJ and other
   exports are optional when specifically requested; preserve source files/history.
   Keep dependencies relative and inside their respective package.
4. For textures, specify maps, width/height, resolution (longest edge), wrapMode,
   normal convention when a normal map exists, and color spaces. Repeat textures
   must match both edge pairs. Mirror textures need alternating flips in 2×2
   tiling and must say mirror explicitly. Clamp atlases use seamless:false,
   retain their aspect ratio, and must never be presented as seamless materials.
   Inspect each preview and preserve original files when claiming unchanged pixels.
5. `npm run import:inbox -- <id>` then `--apply`. Existing IDs are rejected;
   edit existing assets deliberately and increment the asset version.
6. Run `npm run check`. Review changed assets, metadata and generated ZIPs.
7. Commit and push main when requested. Use `.release.json` to request a release.
   The release workflow refuses a tag/version mismatch or a failed check.

## Publication semantics

- `public`: included in UI, JSON, sitemap, ZIPs and release collections.
- `draft`: excluded entirely from generated downloads and pages.
- `hidden`: not listed; public by URL. Never use it for private content.
- Follow docs/ASSET_PRODUCTION_RULES.md for production, format QA and consumer
  ZIP layout. New consumer ZIPs use one short LICENSE.txt with attribution;
  existing immutable Release attachments keep their bytes and notice layout.
  Legacy Pages full/models ZIPs are retired in API v3 and are not generated.
  Old Pages URL compatibility is not guaranteed; current UI/API must not link
  retired output. Keep source assets, Git history and the historical archive ledger.
- Models use `downloads.delivery` for ordinary and selected FBX downloads;
  textures retain `downloads.minimal`. Missing verified FBX is unavailable, never
  an implicit all-format fallback. Delivery transport must pass the full Pages
  budget and actual browser byte tests before deployment.
- Minimal ZIP activation requires the verified binding in
  docs/MINIMAL_DOWNLOADS.md. API v3 exposes only model downloads.delivery or
  texture downloads.minimal; do not restore full/models/direct fallbacks.
- Individual file downloads show attribution beside the button; the raw model
  itself may not embed the license, so downstream consumers must preserve it.

## Verification and releases

Starter repairs and the refrigerator use the separate production overlay in
[docs/ASSET_REVISION_PUBLICATION.md](docs/ASSET_REVISION_PUBLICATION.md).
Only the exact locked three versions under `asset-revisions/repair-appliances-v1`
are activated by `docs/asset-revision-activation.json`; other staging stays inactive.
Review states never count as publication. Keep frozen original137/cohort adapters
and all `content/assets` originals unchanged. Preserve vehicles and all existing IDs.

Run `npm ci`, then the mandatory anonymous durable prep described in
`docs/fbx-minimal-activation/README.md`, then `python3 scripts/prepare-cohort-activation.py --repo "$PWD"`, then `python3 scripts/asset-revisions/prepare_activation.py`, then `npm run check`.
The original prep must run first because it recreates the verified FBX cache.
The cohort prep binds each separately reviewed F/R run, exact immutable Release,
clean-import QA attestation, metadata and complete source inventory. It checks
all new public FBX/ZIP, external original and staged thumbnail bytes anonymously and produces a single-use same-job receipt.
This validates metadata, source safety, GLB headers,
catalog filtering, current Release ZIP contents, retired URL absence, links,
hashes and the complete Pages budget. CI also verifies texture
edges and runs Chromium interactions with software WebGL before creating a
release. Keep screenshots as CI artifacts and release notes honest about limits.
Do not claim FBX/STEP browser coverage without an appropriate fixture.

For previews, use the environment's supported browser workflow. Do not add
tracking or remote runtime dependencies. Three.js is lazy-loaded and only active
viewers render. Preserve reduced-motion support, no-JS links, dialogs and labels.

## Repository origin

Viewer and ZIP code descend from Xenoah/archive-3dmodels, commit
7d52500c361200884d56e8361757953474dfdb68. That repository remains separate.
