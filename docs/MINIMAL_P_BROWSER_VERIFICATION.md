# Activated ordinary-download P verification

This supplements the original viewer/texture regressions. It verifies the exact
built site with real minimal173 activation before main/Pages deployment. It does
not generate new source assets, change the Release, publish Pages, or claim FBX
or new232 coverage. FBX has its own independent activation and browser gates.

## Required actual inputs

- A real `docs/minimal-activation.json` entry and hash-bound T receipt for
  Release `414332464`, tag `minimal-v1.0.0`.
- Verification F commit `32f60a0adb144155574136a14476c30010e0d84b` and public
  inventory SHA-256
  `6cd163e6683650a77e52649d8740feb19d614204473269a635789756fd39e463`.
- Exact F Git blobs at `scripts/minimal-verification/common.py`,
  `scripts/minimal_packages.py`, and `scripts/minimal_notices.py`. The adapter
  loads these locally and independently checks them against F; merely having
  the F commit in Git does not materialize these dependencies.
- All unchanged original assets and protected historical archives. Preserve the
  existing `950000000`-byte Pages ceiling. No new ordinary ZIP lives in Pages.

The input checker verifies receipt identity/digest and local pinned modules. It
does not substitute for the anonymous release/ZIP checks performed by generation
and `check-dist`. There is no offline/cache bypass in the production adapter.

## Exact candidate CI

The supplemental `.github/workflows/verify-minimal-ui.yml` replaces the initial
empty-activation-only verification workflow. It runs on `minimal/verify-p-v1` or
manual dispatch at the selected candidate ref. Top-level and job permissions are
only `contents: read`; checkout does not retain credentials. No import, source
generation, commit, release, Pages upload or deployment step is present.

After locked Node/Python dependencies are installed, it runs:

```sh
node scripts/check-full-p-inputs.mjs
node scripts/check-archive-runtime.mjs
node scripts/check-archive-lock.mjs --check-history
npm run check
python3 scripts/check-textures.py
node scripts/check-full-p-inputs.mjs --dist
npx playwright install --with-deps chromium
node scripts/test-browser.mjs
node scripts/test-minimal-downloads-browser.mjs
```

`npm run check` intentionally performs the full build and independent public
readbacks. The same checked source commit must reach main; a later code, source,
activation or workflow change requires a new verification run. Read the final
artifact, not just the green job: `minimal-p-proof-<commit>-<run>-<attempt>`.
Partial evidence is retained on failure; only a completed supplemental browser
run writes `test-results/minimal-p-downloads/report.json` with status `passed`.

The former `scripts/check-download-ui-source.mjs` remains an explicitly
empty-stage-only helper and is not run by the full-P workflow. Its stage-specific
unit test is replaced by strict activation-schema validation; actual nonempty
activation is required by full-P preflight and real build verification.

## Browser scope and expected results

- Exactly 173 cards and detail pages: 137 models, 36 textures; one ordinary
  minimal ZIP link per card/detail, exact Release URL, and original source links.
- All standalone original GLB/STL/STEP/STP detail links match their unchanged
  source inventories. Dependent formats remain in the source disclosure/ZIP.
- Three actual browser downloads from GitHub Releases: studio-chair,
  cedar-boards, commons-bar-labels. Whole ZIP byte count/hash and every member
  byte count/hash must match the activated catalog. Each has only source files
  and the exact single top-level LICENSE.txt.
- Actual-ready studio-chair + sage-terrazzo selected through the shipped UI on
  desktop and 390px mobile. No test code supplies readiness, legal text, catalog
  entries or UI modules. Count/list, filter persistence, Escape/Back focus,
  removal/clear, keyboard selection, cancellation, duplicate activation,
  network failure, retry and explicit save are checked.
- Only cancellation/error requests are fault-injected. Successful source and
  Release requests return real bytes. Both saved combined ZIPs must contain
  exactly the original source files in one ID folder per asset and one root
  LICENSE.txt with exact concatenated verified notices. Python independently
  checks member sets, CRC, all bytes/hashes, notice digest and no extra docs.
- The original viewer/mobile test is unchanged and runs separately. The Pages
  measurement sums all regular dist file bytes, rejects symlinks/nonregular
  entries, and fails above 950000000 bytes.

Before deployment, the browser mounts unmodified built files at the canonical
HTTPS origin through a byte-preserving static route. This exercises the actual
same-origin source safety checks without changing absolute catalog URLs. The
report explicitly distinguishes this from a live deployed-site test. GitHub
Release URLs never use that route. After deployment, the same script can run as
`node scripts/test-minimal-downloads-browser.mjs --live`; it requires the live
catalog to equal the exact previously built catalog and uses no static route.

Screenshots and all five downloaded archives are kept beside the scoped report.
A passing result is predeployment browser evidence, not a publication claim.

## Focus regression retained

The first real UI CI exposed a production focus bug: closing the selection
dialog focused its opener immediately before disabling it for history traversal.
The opener now receives focus after `popstate` re-enables it. Browser assertions
wait for hidden/enabled/focused final state; the focus requirement is unchanged.
Two deterministic tests execute the real handlers for closing, reopening,
Back and Forward. The successful empty-stage retry covered this same fix; the
activated full-P run must still rerun it with real bindings.
