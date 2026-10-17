Immutable cohort release for 251 new Meshcopia models (cohort `new251`):
232 original city models by Xenoah and 19 street objects authored by Claude.

For each model `<id>` at version 1.0.0 this release contains exactly:

- `<id>.fbx` — static, metre-unit, Y-up FBX with embedded images, converted from
  the unchanged source GLB in the pinned Blender 4.3.2 runtime and verified by a
  clean reimport.
- `<id>-1.0.0-fbx-minimal-1.0.0.zip` — that FBX and one `LICENSE.txt`.
- `<id>-1.0.0-minimal-1.0.0.zip` — the original GLB and STL and one `LICENSE.txt`.

`cohort-inventory.json` binds every file's size and SHA-256 to the reviewed
source manifest. All files are CC BY 4.0; keep the attribution in `LICENSE.txt`.

Limitations: FBX materials, transparency and face culling can vary by importer;
prefer GLB for the original PBR appearance. Tangents are not exported. Unity,
Godot, VRChat, browser FBX rendering, 3D printing and manufacture have not been
tested. Models are static visualization assets without colliders, LOD or rigs.
