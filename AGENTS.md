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
   GLB is preferred for a self-contained download. OBJ must include MTL and
   textures. Keep external resources within `source/` using relative paths.
4. For textures, specify maps, resolution, normal convention and color spaces.
   Check both edge pairs for all maps and inspect 2×2 tiling.
5. `npm run import:inbox -- <id>` then `--apply`. Existing IDs are rejected;
   edit existing assets deliberately and increment the asset version.
6. Run `npm run check`. Review changed assets, metadata and generated ZIPs.
7. Commit and push main when requested. Use `.release.json` to request a release.
   The release workflow refuses a tag/version mismatch or a failed check.

## Publication semantics

- `public`: included in UI, JSON, sitemap, ZIPs and release collections.
- `draft`: excluded entirely from generated downloads and pages.
- `hidden`: not listed; public by URL. Never use it for private content.
- Every ZIP includes LICENSE.txt and ATTRIBUTION.txt.
- Models-only ZIP retains dependencies and license, omits presentation files.
- Individual file downloads show attribution beside the button; the raw model
  itself may not embed the license, so downstream consumers must preserve it.

## Verification and releases

`npm ci && npm run check` validates metadata, source safety, GLB headers,
catalog filtering, ZIP structure, links and hashes. CI also verifies texture
edges and runs Chromium interactions with software WebGL before creating a
release. Keep screenshots as CI artifacts and release notes honest about limits.
Do not claim FBX/STEP browser coverage without an appropriate fixture.

For previews, use the environment's supported browser workflow. Do not add
tracking or remote runtime dependencies. Three.js is lazy-loaded and only active
viewers render. Preserve reduced-motion support, no-JS links, dialogs and labels.

## Repository origin

Viewer and ZIP code descend from Xenoah/archive-3dmodels, commit
7d52500c361200884d56e8361757953474dfdb68. That repository remains separate.
