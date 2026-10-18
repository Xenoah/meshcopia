# Claude instructions

Follow [AGENTS.md](AGENTS.md) and the shared
[Asset production and delivery rules](docs/ASSET_PRODUCTION_RULES.md).
The shared document is the single source of truth for complete model deliveries
(FBX for consumers, GLB for previews, and separate clean-import QA), minimal ZIP layouts, retained licensing,
and multi-selection downloads. Preserve all existing repository safety,
verification, provenance and immutable-publication requirements.

The original137 adapter stays frozen. New251 and the later stage8–10 new30 use
`docs/cohort-activation.json` and the independent same-job cohort prep adapter;
release publication and site activation require separate evidence. Keep source
bytes and recoverable Git history; do not replace/delete existing Release
attachments. Old Pages URL compatibility is not guaranteed. API v3 retires
full/models ZIP output and fields; current UI/API must use verified FBX delivery
or standalone texture downloads. Do not create another distribution repository.
## Starter/appliance revisions

Follow [docs/ASSET_REVISION_PUBLICATION.md](docs/ASSET_REVISION_PUBLICATION.md).
The independently verified overlay activates exactly two starter 1.0.2 revisions
and one refrigerator 1.0.0, giving 455 public assets. Existing washer, vehicles,
all other IDs, legacy source URLs and original137/cohort adapters stay intact.
Run original137 prep, cohort prep, then revision prep in the same build job.
Never use `local-review-verified` or the historical review build for production.
