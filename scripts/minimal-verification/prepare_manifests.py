"""LOCAL ONLY: derive pending minimal-package manifests. No retained ZIPs or publication."""
import argparse
from pathlib import Path
import platform
import sys
import tempfile
import zlib
from common import *
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import minimal_packages as packages
import minimal_notices as notices


def snapshot(repo):
    base_tree = tree(repo, BASE)
    rows = []
    for path, (mode, kind, oid) in sorted(base_tree.items()):
        if re.fullmatch(r'content/assets/[^/]+/asset\.json', path):
            need((mode, kind) == ('100644', 'blob'), 'Unsafe baseline metadata')
            raw = git(repo, 'cat-file', 'blob', oid); metadata = json.loads(raw)
            if metadata.get('status') != 'public':
                continue
            identity = metadata['id']; prefix = f'content/assets/{identity}/source/'
            need(path == f'content/assets/{identity}/asset.json', 'Wrong metadata path')
            need((repo / path).read_bytes() == raw, 'Local metadata differs from baseline')
            source_files = []
            for filename, (mode, kind, file_oid) in sorted(base_tree.items()):
                if filename.startswith(prefix):
                    need((mode, kind) == ('100644', 'blob'), 'Unsafe baseline source file')
                    local = packages.rooted_file(repo, filename)
                    data = git(repo, 'cat-file', 'blob', file_oid)
                    need(file_sha(local) == sha(data), 'Local source differs from baseline')
                    source_files.append({'name': filename[len(prefix):], 'bytes': len(data), 'sha256': sha(data)})
            need(packages.source_listing(repo / prefix) == [r['name'] for r in source_files], 'Untracked/extra source input')
            old_license, old_attribution = notices.baseline_notices(metadata)
            text = notices.make_notice(metadata, old_license, old_attribution)
            rows.append({'id': identity, 'version': metadata['version'], 'kind': metadata['type'], 'status': 'public',
                         'metadataSha256': sha(raw), 'allSourceFiles': source_files,
                         'noticeBasis': 'reconstructed-from-pinned-baseline-generators',
                         'notice': {'filename': 'LICENSE.txt', 'text': text, 'bytes': len(text.encode()), 'sha256': sha(text.encode())}})
    return sorted(rows, key=lambda r: r['id'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--runtime', required=True, type=Path)
    p.add_argument('--receipts', type=Path, help='Reuse the verified path-independent reference receipts; never rebuild when supplied')
    a = p.parse_args(); repo = a.repo.resolve()
    runtime = read(a.runtime)
    need(platform.python_version() == runtime['python'] and zlib.ZLIB_VERSION == zlib.ZLIB_RUNTIME_VERSION == runtime['zlib'], 'Reference runtime must match exact pinned Python/zlib')
    a.out.mkdir(parents=True, exist_ok=False)
    source = {'schemaVersion': 1, 'sourceCommit': BASE, 'cohort': 'published173',
              'protectedArchiveLockSha256': sha(git(repo, 'show', BASE + ':docs/archive-lock.json')),
              'noticeGeneratorSource': {path: sha(git(repo, 'show', BASE + ':' + path)) for path in ('scripts/generate.mjs', 'scripts/lib/catalog.mjs')},
              'assets': snapshot(repo)}
    expected_rows = []
    receipts = {r['id']: r for r in read(a.receipts)['assets']} if a.receipts else None
    if receipts is not None: need(set(receipts) == {r['id'] for r in source['assets']}, 'Receipt cohort differs')
    with tempfile.TemporaryDirectory(prefix='minimal-reference-') as directory:
        for row in source['assets']:
            notice = Path(directory) / 'LICENSE.txt'; notice.write_text(row['notice']['text'], encoding='utf-8')
            plan = packages.make_plan(repo / 'content/assets' / row['id'], notice)
            receipt = receipts[row['id']] if receipts is not None else packages.package(plan, temporary_directory=directory)
            need(receipt['filename'] == plan['filename'] and receipt['kind'] == plan['kind'] and receipt['notice'] == row['notice'], 'Receipt identity/notice differs')
            need(receipt['entries'] == [{k: e[k] for k in ('name', 'bytes', 'sha256')} for e in plan['entries']], 'Receipt source payload closure differs')
            need(receipt['verification'].get('exactAllowlist') is True and receipt['verification'].get('payloadHashesVerified') is True, 'Unverified reference receipt')
            row['sourceFiles'] = sorted(receipt['sourceFiles'], key=lambda r: r['name'])
            expected_rows.append({'id': row['id'], 'filename': receipt['filename'], 'archiveBytes': receipt['archiveBytes'],
                                  'archiveSha256': receipt['archiveSha256'], 'noticeSha256': row['notice']['sha256']})
    source_bytes = canonical(source)
    expected = {'schemaVersion': 1, 'reviewStatus': 'pending-review', 'sourceCommit': BASE, 'cohort': 'published173',
                'sourceInventorySha256': sha(source_bytes), 'packagerSha256': file_sha(Path(packages.__file__)),
                'noticeGeneratorSha256': file_sha(Path(notices.__file__)), 'runtimeSha256': file_sha(a.runtime), 'assets': expected_rows}
    check_manifests(source, {**expected, 'reviewStatus': 'final-reviewed'}, source_bytes)
    (a.out / 'source173.json').write_bytes(source_bytes)
    (a.out / 'expected173.json').write_bytes(canonical(expected))
    print('Generated 173 source bindings and exact ZIP hashes; pending review, no retained archives or external writes.')


if __name__ == '__main__':
    main()
