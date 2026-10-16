"""Minimal FBX verification only. Exact baseline and fresh QA precede packaging."""
import argparse
import shutil
import struct
import zlib
from common import *


def preflight(repo, source, expected, docs, f):
    commit(f)
    need(git(repo, 'rev-parse', 'HEAD').decode().strip() == f, 'Checkout is not exact F')
    need(git(repo, 'rev-parse', '--is-shallow-repository').strip() == b'false', 'Shallow checkout prohibited')
    for args in [('config', '--get', 'extensions.partialClone'), ('config', '--get-regexp', r'^remote\..*\.promisor$')]:
        try:
            git(repo, *args)
            raise ValueError('Partial/promisor repository prohibited')
        except subprocess.CalledProcessError as exc:
            need(exc.returncode == 1, 'Git configuration read failed')
    graft = Path(git(repo, 'rev-parse', '--git-path', 'info/grafts').decode().strip())
    if not graft.is_absolute(): graft = repo / graft
    need(not graft.exists() or not graft.read_text().strip(), 'Grafted history prohibited')
    need(git(repo, 'show', '-s', '--format=%P', f).decode().strip() == BASE, 'F must directly follow exact immutable baseline')
    allowed = read(docs / 'allowed-f-paths.json')
    need(type(allowed) is list and len(allowed) == len(set(allowed)) and set(allowed) == fixed_paths(), 'Invalid/excessive path allowlist')
    changes = git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', BASE, f).decode().split('\0')[:-1]
    need(len(changes) % 2 == 0 and all(s == 'A' for s in changes[::2]) and set(changes[1::2]) == set(allowed), 'F changes must be exactly additive reviewed paths')
    need(git(repo, 'status', '--porcelain', '--untracked-files=no') == b'', 'Dirty tracked checkout')
    original = tree(repo, BASE); current = tree(repo, f)
    for path in allowed:
        need(current[path][:2] == ('100644', 'blob'), 'Overlay symlink/executable/gitlink prohibited')
        need(packages.regular_file(repo / path).read_bytes() == git(repo, 'cat-file', 'blob', current[path][2]), 'Overlay worktree differs from F blob')
    models = {}; textures = []
    for path, item in original.items():
        if re.fullmatch(r'content/assets/[^/]+/asset\.json', path):
            need(item[:2] == ('100644', 'blob'), 'Unsafe asset metadata')
            metadata = json.loads(git(repo, 'cat-file', 'blob', item[2]))
            if metadata.get('status') == 'public':
                if metadata.get('type') == 'model': models[metadata['id']] = metadata
                elif metadata.get('type') == 'texture': textures.append(metadata['id'])
    need(set(models) == {r['id'] for r in source['models']} and len(textures) == 36, 'Original public cohort differs')
    for row in source['models']:
        metadata = models[row['id']]
        need((metadata['id'], metadata['version'], metadata['type'], metadata['status'], metadata['preview']) == (row['id'], row['version'], 'model', 'public', row['id'] + '.glb'), 'Source metadata identity differs')
        checked_blob(repo, original, row['assetMetadata'], row['metadataSha256'])
        check_glb(checked_blob(repo, original, row['sourceGLB'], row['sourceSha256'], row['sourceBytes']))
        old_license, old_attribution = notices.baseline_notices(metadata)
        notice = notices.make_notice(metadata, old_license, old_attribution, fbx_attribution='Changes: ' + CONVERSION_NOTICE + '\n')
        need(notice == row['notice']['text'], 'Notice does not preserve supplied attribution/modifications')
    need(set(source['noticeGeneratorSource']) == {'scripts/generate.mjs', 'scripts/lib/catalog.mjs'}, 'Wrong notice generator binding')
    for path, checksum in source['noticeGeneratorSource'].items():
        checked_blob(repo, original, path, checksum)
    lock = checked_blob(repo, original, 'docs/archive-lock.json', source['protectedArchiveLockSha256'])
    need(len(json.loads(lock)['archives']) == 310, 'Protected archive count differs')
    runtime = read(docs / 'runtime.json')
    need(file_sha(docs / 'runtime.json') == expected['runtimeSha256'], 'Runtime pin differs')
    for name, checksum in runtime['recipe'].items():
        need(file_sha(repo / 'scripts/fbx-verification' / name) == checksum, 'Frozen conversion recipe differs')
    need(sha(json.dumps(runtime['recipe'], sort_keys=True, separators=(',', ':')).encode()) == PIPELINE == runtime['pipelineSha256'], 'Recipe aggregate differs')
    required = {'scripts/fbx-verification/' + n for n in ('runtime_probe.py', 'materialize_imported_images.py', 'verify_fbx_report.py')} | {'docs/fbx-verification/schema/' + n for n in ('fbx-public-qa-schema.json', 'fbx-report-input-schema.json')} | {'scripts/minimal_packages.py', 'scripts/minimal_notices.py', 'scripts/fbx-minimal-verification/setup-runtime.sh', 'tests/test_minimal_packages.py'}
    need(set(runtime['supportFiles']) == required, 'Missing/extra verification-support pins')
    for path, checksum in runtime['supportFiles'].items():
        need(file_sha(repo / path) == checksum, 'Pinned verifier/packager support differs')
    need(runtime['numpyCpuBaseline']['environment']['NPY_DISABLE_CPU_FEATURES'] == 'AVX2,FMA3,AVX512F,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL' and runtime['numpyCpuBaseline']['actualDisabledFeaturesRequired'] is True, 'CPU canonicalization may not be relaxed')
    return original, runtime


def check_glb(data):
    need(len(data) >= 20 and data[:4] == b'glTF' and struct.unpack_from('<I', data, 4)[0] == 2 and struct.unpack_from('<I', data, 8)[0] == len(data), 'Invalid GLB')
    length, kind = struct.unpack_from('<II', data, 12)
    need(kind == 0x4e4f534a and length <= len(data) - 20, 'Invalid GLB JSON chunk')
    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'uri': need(type(item) is str and item.startswith('data:'), 'External GLB dependency prohibited')
                else: visit(item)
        elif isinstance(value, list):
            for item in value: visit(item)
    visit(json.loads(data[20:20 + length]))


def check_receipt(receipt, row, expected):
    want = [{'name': 'LICENSE.txt', 'bytes': row['notice']['bytes'], 'sha256': row['notice']['sha256']}, {'name': row['id'] + '.fbx', 'bytes': expected['fbxBytes'], 'sha256': expected['fbxSha256']}]
    need(receipt['id'] == row['id'] and receipt['kind'] == 'fbx' and receipt['filename'] == expected['filename'] and receipt['entries'] == want, 'Minimal ZIP must have exactly unchanged FBX plus LICENSE.txt')
    need(receipt['archiveBytes'] == expected['archiveBytes'] and receipt['archiveSha256'] == expected['archiveSha256'], 'Reviewed minimal ZIP bytes differ: ' + row['id'])
    need(receipt['notice'] == row['notice'] and receipt['conversionPipelineSha256'] == PIPELINE, 'Notice/recipe package binding differs')
    verification = receipt['verification']
    need(verification['entryCount'] == 2 and all(verification.get(k) is True for k in ('exactAllowlist', 'payloadHashesVerified', 'cleanExtractionVerified', 'dependencyClosureVerified')), 'Strict extracted archive verification missing')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path); parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--preflight-only', action='store_true'); args = parser.parse_args()
    repo = args.repo.resolve(); docs = repo / 'docs/fbx-minimal-verification'
    source_bytes = (docs / 'source137.json').read_bytes(); source = read(docs / 'source137.json'); expected = read(docs / 'expected137.json')
    expected_rows = check_manifests(source, expected, source_bytes)
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == BRANCH and os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Only exact repository branch push permitted')
    f = os.environ.get('GITHUB_SHA', ''); original, runtime = preflight(repo, source, expected, docs, f)
    if args.preflight_only:
        print('Minimal FBX preflight passed; no Blender or publication invoked.'); return
    need(sys.version.split()[0] == runtime['versions']['python'] and zlib.ZLIB_VERSION == zlib.ZLIB_RUNTIME_VERSION == runtime['versions']['zlib'] and sys.flags.optimize == 0, 'Packaging runtime/assertions differ')
    need(file_sha(Path(sys.executable).resolve()) == runtime['packaging']['pythonBinarySha256'] and file_sha(Path('/usr/lib/x86_64-linux-gnu/libz.so.1.3.1')) == runtime['packaging']['zlibBinarySha256'], 'Interpreter/compression binary differs')
    need(file_sha(Path('/usr/bin/blender')) == runtime['binarySha256'], 'Blender binary differs')
    for path, checksum in runtime['exporterFiles'].items(): need(file_sha(Path('/') / path) == checksum, 'Exporter differs')
    for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'): need(re.fullmatch(r'[1-9][0-9]*', os.environ.get(key, '')), 'Missing run identity')
    need(not args.output.exists(), 'Fresh output root required')
    out = args.output.resolve(); out.mkdir(parents=True); private = out / 'internal'; private.mkdir(); public = out / 'artifact'; public.mkdir()
    code = repo / 'scripts/fbx-verification'
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'NPY_DISABLE_CPU_FEATURES': runtime['numpyCpuBaseline']['environment']['NPY_DISABLE_CPU_FEATURES']}
    blender = ['/usr/bin/blender', '-b', '-noaudio', '--factory-startup', '--python-use-system-env', '--python-exit-code', '1']
    subprocess.run(blender + ['--python', str(code / 'runtime_probe.py'), '--', str(docs / 'runtime.json'), str(private / 'runtime.json')], env=env, check=True)
    actual_runtime = read(private / 'runtime.json')
    from verify_fbx_report import verify_report, public_cohort
    from deterministic_fbx import PINNED_SOURCES
    byid = {r['id']: r for r in source['models']}; proofs = []; package_proofs = []; bindings = []
    for identity in list(PILOTS) + sorted(set(byid) - set(PILOTS)):
        need(shutil.disk_usage(out).free > 3_000_000_000, 'Disk reserve reached')
        row = byid[identity]; exp = expected_rows[identity]; work = private / identity; work.mkdir(); fresh = work / 'fresh'; fresh.mkdir()
        data = checked_blob(repo, original, row['sourceGLB'], row['sourceSha256'], row['sourceBytes']); source_glb = work / (identity + '.glb'); source_glb.write_bytes(data)
        command = blender + ['-t', '4', '--python', str(code / 'materialize_imported_images.py'), '--', '--converter-script', str(code / 'convert_and_audit_fbx.py'), '--source', str(source_glb), '--out', str(fresh), '--expected-sha256', row['sourceSha256'], '--unique-image-paths', '--normalize-materials', '--deterministic']
        with (work / 'execution.log').open('w') as log: subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        fbx_path = fresh / (identity + '.fbx'); fbx = fbx_path.read_bytes()
        need(len(fbx) == exp['fbxBytes'] and sha(fbx) == exp['fbxSha256'], 'Frozen v4 FBX differs: ' + identity)
        report_path = fresh / 'roundtrip-report.json'; report = report_path.read_bytes()
        fresh_binding = {'id': identity, 'qaSha256': sha(report), 'sourceGlbSha256': row['sourceSha256'], 'fbxSha256': exp['fbxSha256'], 'fbxBytes': exp['fbxBytes']}
        proof = verify_report(report, fresh_binding, data, fbx, runtime['recipe'], actual_runtime, PINNED_SOURCES, fresh / 'clean-reimport')
        need(proof['cleanImportEvidence']['extractedCopiesAvailable'], 'Missing actual clean-import image bytes')
        proofs.append(proof)
        notice = work / 'LICENSE.txt'; notice.write_bytes(row['notice']['text'].encode('utf-8'))
        plan = packages.make_plan(repo / 'content/assets' / identity, notice, fbx_path=fbx_path, fbx_sha256=exp['fbxSha256'], pipeline_sha256=PIPELINE, fbx_report=report_path)
        receipt = packages.package(plan, output=public / exp['filename']); check_receipt(receipt, row, exp)
        (public / (identity + '.fbx')).write_bytes(fbx)
        package_proofs.append({'id': identity, 'reviewedLocalQaSha256': exp['reviewedQaSha256'], 'freshCiQaSha256': sha(report), 'archiveSha256': exp['archiveSha256'], 'verification': receipt['verification']})
        dump(work / 'receipt.json', receipt)
        bindings.append(model_binding(row, exp))
        if len(proofs) == len(PILOTS): dump(private / 'pilot-gate.json', {'passed': True, 'ids': list(PILOTS), 'fCommit': f})
        print(json.dumps({'id': identity, 'completed': len(proofs), 'expected': 137}), flush=True)
    need(len(proofs) == 137, 'Incomplete verification')
    cohort = public_cohort(proofs, set(byid))
    dump(private / 'qa.json', {'schemaVersion': 1, 'status': 'fresh-fbx-and-minimal-packages-verified', 'fCommit': f, 'sourceCommit': BASE, 'runId': os.environ['GITHUB_RUN_ID'], 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'], 'fbxQa': cohort, 'packages': package_proofs})
    inventory = {'schemaVersion': 1, 'contract': 'meshcopia-fbx-minimal-artifact/1', 'repository': REPO, 'fCommit': f, 'sourceCommit': BASE, 'workflow': WORKFLOW, 'runId': os.environ['GITHUB_RUN_ID'], 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'], 'cohort': 'published137', 'packageVersion': '1.0.0', 'pipelineSha256': PIPELINE, 'sourceInventorySha256': sha(source_bytes), 'expectedManifestSha256': file_sha(docs / 'expected137.json'), 'runtimeSha256': expected['runtimeSha256'], 'models': sorted(bindings, key=lambda x: x['id'])}
    dump(public / 'fbx-minimal-inventory.json', inventory); readable_verified_archives(public, bindings)
    print('137 fresh v4 FBXs and exact two-entry minimal ZIPs verified. QA is separate; no publication enabled.')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('FBX_MINIMAL_VERIFY_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
