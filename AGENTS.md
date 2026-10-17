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
   exports are optional when specifically requested; preserve existing files/URLs.
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
  historical immutable ZIPs keep their original bytes and notice layout.
- Models use `downloads.delivery` for ordinary and selected FBX downloads;
  textures retain `downloads.minimal`. Missing verified FBX is unavailable, never
  an implicit all-format fallback. Delivery transport must pass the full Pages
  budget and actual browser byte tests before deployment.
- Minimal ZIP activation requires the verified binding in
  docs/MINIMAL_DOWNLOADS.md. Keep legacy full/models API fields compatible.
- Individual file downloads show attribution beside the button; the raw model
  itself may not embed the license, so downstream consumers must preserve it.

## Verification and releases

Run `npm ci`, then the mandatory anonymous durable prep described in
`docs/fbx-minimal-activation/README.md`, then `npm run check`. This validates metadata, source safety, GLB headers,
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
