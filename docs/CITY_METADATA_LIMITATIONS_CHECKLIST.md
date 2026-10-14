# City metadata: integration gate

Supporting checklist, not a schema change or publication approval.

- [ ] Final manifest selects every ID and exact GLB, STL, preview and metadata
  hash. Never treat `status: public` in reference metadata as approval to publish
  a new variant. Preserve already frozen assets unless separately authorized.
- [ ] `unit: m`, `upAxis: Y`, dimensions and triangles match the delivered geometry.
  STL numeric units/axes and lack of appearance/hierarchy are disclosed.
- [ ] `description` / `descriptionEn` distinguish static visualization from a
  working, rideable, articulated, medical, safety-certified or printable product.
  Say when named companion objects are absent.
- [ ] `uv` states overlapping component UV0 and no supplied unique lightmap UV2.
  Keep the tree's exception: embedded original bark color/normal maps, tangents,
  vertex colors and intentionally open double-sided foliage. Do not apply the
  generic "solid-color/no textures" wording to it.
- [ ] Describe base-centered placement separately from actual hinge/mount pivots.
  No colliders, LOD, rig, wind or runtime behavior is implied by object names.
- [ ] `provenance.sourceSha256` and `stlSha256` match final bytes; retain generator,
  postprocessor, Blender version, seed and rights. Pin a source revision only
  after verifying that it contains the exact producing source. Do not invent refs.
- [ ] Grouping counts are labeled mesh nodes/primitive instances, not measured
  draw calls or FPS. State whether geometry was simplified. Preserve the source
  baseline hash and normals/UV/material equivalence evidence.
- [ ] License and attribution survive individual and bundled distribution;
  embedded/extracted textures retain their provenance and sampling requirements.
- [ ] Validation, preview and reproduction reports identify their input SHA-256.
  A file called "final" can still describe an obsolete variant. New bytes need
  fresh applicable validation, including normal-map tangent checks.
- [ ] Publish status/counts, browser/CI claims and Unity/VRChat claims are separate.
  A valid GLB or local render never upgrades an unrun engine test to "passed".

When adopting these documents, run the repository's normal `npm run check` and
review generated manifest/ZIP notices. This documentation-only proposal does not
change any asset, generated output, version, release request or publication state.
