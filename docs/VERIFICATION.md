# v1.0.0 verification

## Automated gates

- `npm run check`: metadata validation; source-path/symlink tests; original GLB
  header, length and triangle count; STL structure; search/filter intersection;
  deterministic UTF-8 ZIPs; rejected licensing/missing source; full static build;
  local links and SHA-256 for all 86 distributed files/archives.
- `python3 scripts/check-textures.py`: 24 PNG maps decoded, dimensions checked,
  opposite rows and columns byte-identical. This checks wrap boundaries, not a
  claim of photograph-level realism or an imperceptible repetition period.
- `node scripts/test-browser.mjs` in GitHub Actions: Chromium with software WebGL,
  1440px desktop and 390px mobile; search/filter/empty/reset, dialog reuse,
  GLB/STL/OBJ switching, material and lighting controls, download bytes, clipboard,
  texture tiling and PBR sphere, language and horizontal-overflow checks.

## Observed

RC workflow `38548128143` passed verification and produced `v1.0.0-rc.1`.
Its screenshots were inspected. Lazy images outside the viewport were missing
from some full-page captures; the final capture workflow scrolls through images
and waits for `decode()` while the actual UI keeps lazy loading.
The mobile download placement and viewer UI reset were corrected for v1.0.0.

Final workflow `38548933654` passed verification and created stable `v1.0.0`
at commit `ee5b2732b111162b5552ac805f8010b24dd9c867`. Each release includes
actual Chromium screenshots.

On 2026-10-14, the repository owner enabled GitHub Pages with GitHub Actions.
Workflow `38550590415` passed verification, Pages deployment, and the existing
release check. The live site is https://xenoah.github.io/meshcopia/.
Production HTTP checks returned 200 for the homepage and 14-entry JSON catalog.
The atelier-lamp full ZIP, models-only ZIP and direct GLB, plus the
brushed-aluminum texture ZIP, were downloaded from that live site. All four
matched their catalog sizes and SHA-256 hashes; all three ZIPs passed CRC checks
and contained LICENSE.txt and ATTRIBUTION.txt.

## Limits

- No Android/iOS physical-device test; mobile test is Chromium viewport emulation.
- FBX/STEP loader support is inherited, but no first-release fixture exercises it.
- No 3D printing, collision mesh, production UV unwrap, or structural validation.
- STEP conversion runs in the browser; large CAD models may block the main thread.
- All displayed/source materials are original procedural examples, not scans.
