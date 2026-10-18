# Origin and documented usage (introduced in catalog 2.1.0)

`usages` is an optional array on an asset, additive to catalog 2.0.0. It appears
unchanged in current JSON/NDJSON and individual manifests. Historical full ZIPs
also included it in `asset.json`; API v3 no longer generates those Pages ZIPs.
Consumer FBX/image ZIPs contain no metadata file.
The loader normalizes an omitted array to `[]`. Both mean **not recorded**, not
“never used”. Old assets remain valid. Existing fields and rights checks remain.

```json
{
  "usages": [{
    "relationship": "original",
    "project": "Commons cafe",
    "sourceUrl": "https://github.com/Xenoah/vrcworld_tech-tech-cafe/tree/784e040a866c0081d6641c03cbf7f23d48a59dc2",
    "sourceRef": "784e040a866c0081d6641c03cbf7f23d48a59dc2",
    "sourcePaths": ["Blender/The_Commons_Compact.blend"],
    "selectors": ["FURN_StoolSeat"],
    "context": "Original Blender collection: FURN_Bar"
  }]
}
```

- `relationship` and nonempty `project` are required per record. `original`
  identifies the work the asset was created for; `reuse` is a documented later use.
  Add separate records for multiple projects/locations. Do not replace origin
  when adding reuse. Library inclusion is not proof of deployment.
- Optional `sourceUrl` is a public HTTP(S) source or evidence URL. Prefer HTTPS
  and a pinned commit URL. Credentials, script/data/file URLs are rejected.
- Optional `sourceRef` is the exact immutable commit/version when known. Do not
  imply an uncommitted add-on exists at an upstream commit. Omit unknown refs;
  keep the evidence source and any limitations explicit in `context`.
- `sourcePaths` are paths relative to the stated repository, not temporary
  extraction prefixes, machine paths, or traversal paths. For example use
  `Assets/...`, not `tree-baseline-v219/TreeTopYokocho/Assets/...`.
- `selectors` are exact source object names/identifiers. They are text, never
  executed. `context` describes documented collection, scene, room or use.
- Omit unknown optional values, rather than null, empty strings, guessed names,
  local filesystem paths, or private URLs. Empty lists are allowed.
- `provenance` still records creation tools, source hashes, modifications and
  rights. A usage record is **not** a license grant or an authorship claim.
  Texture `usage` / `usageEn` still describe sampling instructions, not projects.

The detail page shows records independently of the provenance disclosure. Search
matches project, context, source URL/ref, paths and selectors alongside existing
name/tag/format filters. No new network calls or remote runtime dependencies.

## Backfill and regeneration

All 47 baseline assets receive metadata-only patch version increments. The 33
Commons records come from their existing pinned provenance and the documented
selection in COMMONS_IMPORT.md. Exact source objects/collections are preserved;
textures identify their upstream PNG, without inventing deployed scenes. The 14
starter assets identify Meshcopia as the original library project, the existing
generator path and asset ID, explicitly recording no external usage. No source
ref is invented for them. Asset bytes, image hashes and licensing are unchanged.
The three source generators emit equivalent records for fresh imports.

For new extraction batches, populate records from final verified extraction
records, not partial staging output. Normalize repository-relative paths, retain
an immutable ref only for files actually present there, and keep original-only
rights evidence separate. Increment version/updated for edits to existing assets.

`npm run check` exercises record validation, legacy defaults, multiple usages,
unsafe URLs/paths, search, and propagation into current built JSON/manifests. Historical ZIP metadata remains
in existing Releases/history, outside the current consumer ZIP layout.
