"""Verification only. An independent additive branch from the immutable asset baseline."""
import argparse
from pathlib import Path
import platform
import sys
import zlib
from common import *
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import minimal_packages as packages
import minimal_notices as notices


REPAIR_PARENT = 'edab3c5dad80dc327dc34c398693a3fbff71219c'
REPAIR_PATHS = {'.github/workflows/verify-minimal.yml', 'scripts/minimal-verification/verify.py',
                'scripts/minimal-verification/test_verification.py', 'docs/minimal-verification/README.md'}


def check_lineage(repo, f):
    parent = git(repo, 'show', '-s', '--format=%P', f).decode().strip()
    need(parent in (BASE, REPAIR_PARENT), 'Verification must directly follow baseline or exact reviewed repair parent')
    if parent == REPAIR_PARENT:
        need(git(repo, 'show', '-s', '--format=%P', parent).decode().strip() == BASE, 'Repair parent lineage differs')
        delta = git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', parent, f).decode().split('\0')[:-1]
        need(len(delta) == 2 * len(REPAIR_PATHS) and all(s == 'M' for s in delta[::2]) and set(delta[1::2]) == REPAIR_PATHS,
             'Repair changes exceed exact reviewed paths')


def preflight(repo, source, expected, docs, f):
    commit(f)
    need(git(repo, 'rev-parse', 'HEAD').decode().strip() == f, 'Checkout is not verification commit')
    need(git(repo, 'rev-parse', '--is-shallow-repository').strip() == b'false', 'Shallow checkout prohibited')
    need(git(repo, 'status', '--porcelain', '--untracked-files=no') == b'', 'Dirty tracked checkout')
    # The sole reviewed repair preserves the cumulative additive baseline boundary.
    check_lineage(repo, f)
    allowed = read(docs / 'allowed-f-paths.json')
    fixed = {'.github/workflows/verify-minimal.yml', 'scripts/minimal_packages.py', 'scripts/minimal_notices.py', 'tests/test_minimal_packages.py'} | {'scripts/minimal-verification/' + name for name in ('common.py', 'verify.py', 'prepare_manifests.py', 'setup-runtime.sh', 'test_verification.py')} | {'docs/minimal-verification/' + name for name in ('README.md', 'runtime.json', 'source173.json', 'expected173.json', 'allowed-f-paths.json')}
    need(isinstance(allowed, list) and len(allowed) == len(set(allowed)) and set(allowed) == fixed, 'Invalid/excessive verification path allowlist')
    need(not any('approval' in path.lower() or 'release' in path.lower() for path in allowed), 'Publication paths forbidden in verification')
    actual = git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', BASE, f).decode().split('\0')[:-1]
    need(len(actual) % 2 == 0 and all(s == 'A' for s in actual[::2]) and set(actual[1::2]) == set(allowed), 'Verification changes are not exactly additive reviewed paths')
    check_repository(repo)
    current = tree(repo, f); original = tree(repo, BASE)
    for path in allowed:
        safe(path); need(current[path][:2] == ('100644', 'blob'), 'Unsafe overlay entry')
    ids = []
    for path, entry in original.items():
        if re.fullmatch(r'content/assets/[^/]+/asset\.json', path):
            metadata = json.loads(git(repo, 'cat-file', 'blob', entry[2]))
            if metadata.get('status') == 'public': ids.append(metadata['id'])
    need(sorted(ids) == [r['id'] for r in source['assets']], 'Source inventory does not equal baseline public IDs')
    for row in source['assets']:
        root = f"content/assets/{row['id']}/"
        need(file_sha(packages.rooted_file(repo, root + 'asset.json')) == row['metadataSha256'], 'Metadata drift')
        metadata = packages.load_json(repo / root / 'asset.json')
        need((metadata['id'], metadata['version'], metadata['type'], metadata['status']) == (row['id'], row['version'], row['kind'], row['status']), 'Source identity drift')
        files = row['allSourceFiles']
        need(packages.source_listing(repo / root / 'source') == [r['name'] for r in files], 'Incomplete/extra source listing')
        for item in files:
            rel = root + 'source/' + safe(item['name']); path = packages.rooted_file(repo, rel)
            need(original[rel][:2] == ('100644', 'blob') and current[rel] == original[rel], 'Original source blob drift')
            need(path.stat().st_size == item['bytes'] and file_sha(path) == item['sha256'], 'Original source bytes drift')
        old_license, old_attribution = notices.baseline_notices(metadata)
        need(row['noticeBasis'] == 'reconstructed-from-pinned-baseline-generators' and notices.make_notice(metadata, old_license, old_attribution) == row['notice']['text'], 'Notice generator result differs')
    need(set(source['noticeGeneratorSource']) == {'scripts/generate.mjs', 'scripts/lib/catalog.mjs'}, 'Incomplete baseline notice generator binding')
    for path, checksum in source['noticeGeneratorSource'].items():
        need(sha(git(repo, 'show', BASE + ':' + safe(path))) == checksum, 'Baseline notice generator differs')
    need(sha(git(repo, 'show', BASE + ':docs/archive-lock.json')) == source['protectedArchiveLockSha256'], 'Original immutable archive lock differs')
    need(file_sha(Path(packages.__file__)) == expected['packagerSha256'], 'Packager differs')
    need(file_sha(Path(notices.__file__)) == expected['noticeGeneratorSha256'], 'Notice generator differs')
    need(file_sha(docs / 'runtime.json') == expected['runtimeSha256'], 'Runtime pin differs')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True, type=Path); p.add_argument('--output', required=True, type=Path)
    p.add_argument('--preflight-only', action='store_true'); a = p.parse_args()
    repo = a.repo.resolve(); docs = repo / 'docs/minimal-verification'
    source_bytes = (docs / 'source173.json').read_bytes(); source = read(docs / 'source173.json'); expected = read(docs / 'expected173.json')
    byid = check_manifests(source, expected, source_bytes)
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == 'refs/heads/' + VERIFY_BRANCH and os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Wrong verification execution context')
    f = os.environ.get('GITHUB_SHA', ''); preflight(repo, source, expected, docs, f)
    if a.preflight_only:
        print('Verification preflight passed. No files published.'); return
    runtime = read(docs / 'runtime.json')
    need(platform.python_version() == runtime['python'] and zlib.ZLIB_VERSION == zlib.ZLIB_RUNTIME_VERSION == runtime['zlib'] and sys.flags.optimize == 0, 'Pinned runtime differs')
    need(file_sha(Path(sys.executable).resolve()) == runtime['pythonBinarySha256'] and file_sha(Path('/usr/lib/x86_64-linux-gnu/libz.so.1.3.1')) == runtime['zlibBinarySha256'], 'Pinned interpreter/compression binary differs')
    out = a.output; out.mkdir(exist_ok=False, parents=True)
    public = out / 'artifact'; public.mkdir(); private = out / 'internal'; private.mkdir()
    qa = []; bindings = []
    for row in source['assets']:
        notice = private / 'LICENSE.txt'; notice.write_text(row['notice']['text'], encoding='utf-8')
        plan = packages.make_plan(repo / 'content/assets' / row['id'], notice)
        exp = byid[row['id']]
        receipt = packages.package(plan, output=public / exp['filename'])
        need(receipt['archiveBytes'] == exp['archiveBytes'] and receipt['archiveSha256'] == exp['archiveSha256'], 'Reproduced ZIP differs from exact reviewed hash: ' + row['id'])
        need(sorted(receipt['sourceFiles'], key=lambda r: r['name']) == row['sourceFiles'] and receipt['notice'] == row['notice'], 'Package binding differs')
        qa.append({'id': row['id'], 'sha256': receipt['archiveSha256'], **receipt['verification']})
        bindings.append(package_binding(row, exp))
    notice.unlink()
    inventory = {'schemaVersion': 1, 'packageVersion': '1.0.0', 'repository': REPO, 'tag': TAG, 'cohort': 'published173',
                 'sourceCommit': BASE, 'verificationCommit': f, 'workflow': WORKFLOW, 'runId': os.environ['GITHUB_RUN_ID'],
                 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'], 'sourceInventorySha256': sha(source_bytes),
                 'expectedManifestSha256': file_sha(docs / 'expected173.json'), 'packagerSha256': expected['packagerSha256'],
                 'runtimeSha256': expected['runtimeSha256'], 'assets': bindings}
    (public / 'minimal-inventory.json').write_bytes(canonical(inventory))
    (private / 'qa.json').write_bytes(canonical({'schemaVersion': 1, 'status': 'exact-minimal-packages-verified', 'assets': qa}))
    print('173 minimal packages reproduced and strictly verified. Internal QA is separate; no publication enabled.')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('MINIMAL_VERIFY_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__))
        raise SystemExit(1)
