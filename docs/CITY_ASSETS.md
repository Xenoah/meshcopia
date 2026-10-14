# Original city collection

These original procedural models were created for Meshcopia, not extracted from Yokocho or Commons. Generator source is in `scripts/city/`. Each model records its exact selector and generator in `usages`.

## Recovery checkpoint

The initial local execution environment became unavailable during final preview refinement. The recovered source is reconstructed from authored code and known edits; it is not asserted to be byte-identical to the lost working files. New outputs are generated with the pinned official `bpy==4.5.14` package and held as `draft`. Earlier Blender 4.3.2 tests do not certify these rebuilt bytes.

The once-only `.generate-city-drafts.json` roster runs the generators, reimports each delivered GLB, renders the exact mesh, records SHA-256, and stages the result for normal inbox validation. `docs/city-qa/` holds review images and measurements. Drafts are excluded from the public catalog and download bundles. A separate metadata change is required after visual and geometry review. No new release is requested by this recovery checkpoint.

## Geometry and intended use

Meters, Y-up GLB, centered horizontal pivot and base at Y=0. Named parts retain practical hardware detail. Solid-color PBR materials and per-component UVs are included; UVs are not a unique packed lightmap atlas. No external model, scan, brand logo, or font binary is included. Static game/visualization props only; no manufacturing, accessibility certification, structural, hydraulic, electrical, traffic-control or 3D-printing validation.

## Regeneration

Use Python 3.11 with the official pinned packages from the workflow, or a compatible Blender installation. Example: `python scripts/city/access.py --output _inbox --only city-bollard`. Existing asset IDs must not be overwritten implicitly. New outputs default to draft and must be reviewed before publication. Generator changes are not proof that existing downloadable bytes changed.
