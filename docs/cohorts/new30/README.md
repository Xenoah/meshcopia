# Cohort new30

Exactly the 30 draft models from source stages 8–10, separate from the already
published `new251` Release. The source stage runs passed for all three stages;
`source.json` pins each model to its stage commit, unchanged GLB/STL inventory,
status-only public metadata and retained notices.

The discovery run performs fresh FBX conversion and clean reimport in the same
pinned runtime as new251. Its outputs must be reviewed and reproduced exactly
in a final verification run before immutable publication. The site adapter
must independently revalidate the resulting Release and use FBX plus LICENSE
for consumer ZIPs, same-origin verified chunks for selected ZIPs, and GLB for
previews. Original files and internal QA remain separate. This verification
branch does not deploy Pages or publish a Release.
