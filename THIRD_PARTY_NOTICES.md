# Third-party software and attribution

- **archive-3dmodels** — Xenoah. Reference commit `7d52500c361200884d56e8361757953474dfdb68`. The same repository owner requested this derivative. The Three.js viewer and store-ZIP writer were adapted. No original CC BY-NC models are redistributed here. https://github.com/Xenoah/archive-3dmodels
- **Astro** — Astro contributors, MIT. https://github.com/withastro/astro/blob/main/LICENSE
- **Three.js** — three.js authors, MIT. https://github.com/mrdoob/three.js/blob/dev/LICENSE
- **Khronos glTF Validator** — Apache-2.0. Build/test dependency used to validate exported GLB files; not loaded by the website. https://github.com/KhronosGroup/glTF-Validator
- **occt-import-js** — LGPL-2.1, unmodified JS/WASM copied from the locked npm dependency. Source, build instructions and license: https://github.com/kovacsv/occt-import-js . Browser JS/WASM is replaceable in `public/vendor/occt-import-js/` and `dist/vendor/occt-import-js/`. Rebuild with `npm ci && npm run build` or substitute compatible JS/WASM files.
- **Open CASCADE Technology** — used by occt-import-js. LGPL-2.1 with additional exception; see occt-import-js source/dependency documentation. https://github.com/Open-Cascade-SAS/OCCT

Exact installed dependency versions and transitive dependencies are recorded in
`package-lock.json`. Dependency license files are preserved in node_modules and
relevant runtime licenses are copied into distribution packages by the build.
The CC BY license on Meshcopia does not replace these software licenses.
