# Commons cafe original asset selection

Source: [Xenoah/vrcworld_tech-tech-cafe](https://github.com/Xenoah/vrcworld_tech-tech-cafe/tree/784e040a866c0081d6641c03cbf7f23d48a59dc2), pinned commit `784e040a866c0081d6641c03cbf7f23d48a59dc2`.

On 2026-10-14 the repository owner requested reusable original assets from this
world to be published in the CC-BY-4.0 Meshcopia library. This selection contains
12 original static models, extracted from the existing Blender scene.

## Evidence and scope

- `Blender/build_world.py` defines the selected furniture, lighting and equipment
  from original box, cylinder, ring and beam geometry. The saved scene is the
  geometry source; the upstream build script is not executed by the importer.
- `Documentation/texture_provenance.json` and `README_JA.md` document the original
  image-generated textures and their mirror/clamp sampling requirements.
- Every export records the source commit, original object names, collection,
  input SHA-256 hashes and exact embedded PNG hashes in `asset.json`.
- Only selected `MESH` objects enter the exports. No FONT objects, font binaries,
  posters, AudioLink, VRChat SDK, UdonSharp, iwaSync, CVS2, vehicles or drones enter
  the packages. No runtime behavior scripts or sounds are included.
- Architectural textures are mirrored-repeat materials. Their original pixels
  are preserved inside GLB; they are not registered as ordinary-repeat seamless
  texture assets. The existing six periodic texture assets are unchanged.

## Selection

| Asset ID | Reusable object | Original collection | Mesh parts |
| --- | --- | --- | ---: |
| commons-bar-stool | Upholstered bar stool | FURN_Bar | 4 |
| commons-lounge-chair | Lounge chair | FURN_Cafe | 6 |
| commons-lounge-sofa | Two-seat sofa | MODE_Lounge | 8 |
| commons-round-table | Round cafe table, without tabletop props | FURN_Cafe | 4 |
| commons-pendant-light | Shade, suspension and diffuser | FURN_Bar | 3 |
| commons-coffee-cup | Cup, coffee surface and ring saucer | FURN_Cafe | 3 |
| commons-leaf-planter | Pot, soil, nine stems and leaves | FURN_Cafe | 20 |
| commons-espresso-machine | Fictional espresso machine | FURN_Bar | 4 |
| commons-coffee-grinder | Grinder and hopper | FURN_Bar | 2 |
| commons-pa-speaker | PA enclosure and grille | AV_Stage | 15 |
| commons-dj-controller | Fictional RELAY R2 controller | AV_DJ | 46 |
| commons-display-plinth | Cylindrical plinth and emissive rim | AV_Stage | 2 |

The chair, sofa and controller are rotated to a convenient front orientation.
Each asset is centered horizontally with its base at Y=0. Units remain meters.
Existing bevel modifiers are evaluated. GLB retains original UVs, separate parts,
embedded textures and mirror/clamp samplers; STL retains the same geometry and
Y-up coordinates without colors, materials or UVs. Catalog triangle counts and
dimensions are measured from the exported geometry.

Thumbnails are Blender Cycles studio renders of the extracted meshes. Studio
camera, lights and floor are used only for thumbnails. The emissive surfaces are
materials, not exported runtime lights. These are low-poly decorative game
props, not working machines or validated manufacturing/3D-printing models.

## Reproduce

Use Python 3.11 in a separate environment:

```sh
python -m pip install bpy==4.5.14 numpy==1.26.4 Pillow==11.2.1
python scripts/import-commons-cafe.py --fetch --inspect
python scripts/import-commons-cafe.py --fetch
npm run import:all-inbox -- --apply
npm run check
```

The importer refuses existing IDs and checks pinned input hashes before opening
the Blender scene with scripts disabled. To reproduce in a separate checkout,
remove only the exported `commons-*` asset folders in that checkout first.
`--source-root <checkout>` can use a local source checkout instead of fetching.
CI performs the initial extraction only when `.import-commons-cafe` exists,
removes that marker, validates the assets, and commits the imported collection.
Subsequent builds use the committed source files and require no Blender install.

Verification gates include metadata/license checks, GLB format validation,
embedded-image hashes, mirror/clamp sampling, GLB/STL triangle consistency,
archive attribution/dependencies, internal links, and Chromium loading of every
new model. Browser screenshots are attached to the release. Unity/VRChat runtime
and physical devices are outside this extraction's verification.

Observed: RC workflow `38554056814` passed all gates, loaded every new GLB in
Chromium, published the site and created `v1.1.0-rc.1`. The imported asset commit
is `ad3e370721ce0d575c907ea65783e1d5c8ba55a3`. All 12 Blender thumbnails were
visually inspected. The final release corrects a catalog card label that had
assumed every model supplied OBJ; cards now list their actual available formats.
