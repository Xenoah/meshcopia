"""Strict minimal-F bindings. Nothing in this module publishes or uploads."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

BASE = '4ab5342568a4227215b295b40a47c27698cc930a'
REPO = 'Xenoah/meshcopia'
BRANCH = 'refs/heads/fbx/verify-minimal137-v1'
WORKFLOW = '.github/workflows/verify-fbx-minimal.yml'
PIPELINE = '9c14ed64ff019ef1fc6cdf4d86df1c4504f1cd1a675c4cb1bd4ac3c2f37cb500'
CONVERSION_NOTICE = 'Converted unchanged source GLB geometry to FBX, with documented compatible material/texture derivatives.'
PILOTS = ('city-pruned-street-tree', 'city-vending-machine', 'commons-round-table', 'yokocho-bottle-keep-wall', 'yokocho-geometric-backbar', 'yokocho-noh-pavilion', 'atelier-lamp')
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/fbx-verification'))
import minimal_packages as packages
import minimal_notices as notices


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
def read(path): return packages.load_json(path)
def file_sha(path): return packages.hash_file(packages.regular_file(path))[1]
def dump(path, value): path.write_bytes(canonical(value))
def digest(value): need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA-256')
def commit(value): need(type(value) is str and re.fullmatch('[0-9a-f]{40}', value), 'Invalid commit')
def size(value): need(type(value) is int and 0 < value <= packages.MAX_FILE_BYTES, 'Invalid bounded byte size')
def exact(value, fields, label): need(type(value) is dict and set(value) == set(fields.split()), 'Unknown/missing ' + label + ' fields')


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    return subprocess.check_output(['git', '--no-replace-objects', '-c', 'safe.directory=' + str(repo), '-C', str(repo), *args], env=env)


def tree(repo, revision):
    result = {}
    for item in git(repo, 'ls-tree', '-r', '-z', revision).split(b'\0'):
        if item:
            header, name = item.split(b'\t', 1)
            result[name.decode()] = tuple(header.decode().split())
    return result


def checked_blob(repo, entries, path, checksum, byte_count=None):
    packages.safe_relative(path)
    need(path in entries and entries[path][:2] == ('100644', 'blob'), 'Missing/unsafe pinned input')
    data = git(repo, 'cat-file', 'blob', entries[path][2])
    need(sha(data) == checksum and (byte_count is None or len(data) == byte_count), 'Pinned source bytes differ')
    return data


def fixed_paths():
    return {WORKFLOW, 'scripts/minimal_packages.py', 'scripts/minimal_notices.py', 'tests/test_minimal_packages.py'} | {
        'scripts/fbx-verification/' + n for n in ('convert_and_audit_fbx.py', 'normalize_fbx_materials.py', 'deterministic_fbx.py', 'runtime_probe.py', 'materialize_imported_images.py', 'verify_fbx_report.py')
    } | {'docs/fbx-verification/schema/' + n for n in ('fbx-public-qa-schema.json', 'fbx-report-input-schema.json')} | {
        'scripts/fbx-minimal-verification/' + n for n in ('common.py', 'verify.py', 'setup-runtime.sh', 'test_verification.py')
    } | {'docs/fbx-minimal-verification/' + n for n in ('README.md', 'ARTIFACT_CONTRACT.md', 'source137.json', 'expected137.json', 'runtime.json', 'allowed-f-paths.json')}


def check_manifests(source, expected, source_bytes):
    exact(source, 'schemaVersion baseCommit cohort modelCount textureCount protectedArchiveCount protectedArchiveLockSha256 noticeGeneratorSource models', 'source manifest')
    exact(expected, 'schemaVersion reviewStatus baseCommit cohort packageVersion pipelineSha256 sourceInventorySha256 runtimeSha256 models', 'expected manifest')
    need(source['schemaVersion'] == expected['schemaVersion'] == 1 and source['baseCommit'] == expected['baseCommit'] == BASE, 'Wrong source baseline/schema')
    need(source['cohort'] == expected['cohort'] == 'published137' and source['modelCount'] == 137 and source['textureCount'] == 36 and source['protectedArchiveCount'] == 310, 'Wrong original cohort')
    need(expected['reviewStatus'] == 'final-reviewed' and expected['packageVersion'] == '1.0.0' and expected['pipelineSha256'] == PIPELINE, 'Unreviewed inputs or changed recipe/package')
    need(expected['sourceInventorySha256'] == sha(source_bytes), 'Source inventory hash differs')
    digest(expected['runtimeSha256']); digest(source['protectedArchiveLockSha256'])
    need(type(source['models']) is list and type(expected['models']) is list and len(source['models']) == len(expected['models']) == 137, 'Need exact 137 records')
    ids = [r['id'] for r in source['models']]
    need(ids == sorted(set(ids)) and ids == [r['id'] for r in expected['models']], 'Duplicate/unsorted/different cohort IDs')
    for row, exp in zip(source['models'], expected['models']):
        exact(row, 'id version sourceGLB sourceSha256 assetMetadata metadataSha256 sourceBytes notice', 'source row')
        exact(exp, 'id sourceGlbSha256 fbxBytes fbxSha256 reviewedQaSha256 filename archiveBytes archiveSha256 noticeSha256', 'expected row')
        identity = row['id']
        need(type(identity) is str and packages.ID.fullmatch(identity), 'Invalid model identity')
        need(type(row['version']) is str and packages.VERSION.fullmatch(row['version']), 'Invalid source version')
        need(row['sourceGLB'] == f'content/assets/{identity}/source/{identity}.glb' and row['assetMetadata'] == f'content/assets/{identity}/asset.json', 'Cross-model/noncanonical source path')
        for key in ('sourceSha256', 'metadataSha256'): digest(row[key])
        for key in ('sourceGlbSha256', 'fbxSha256', 'reviewedQaSha256', 'archiveSha256', 'noticeSha256'): digest(exp[key])
        need(row['sourceSha256'] == exp['sourceGlbSha256'], 'Source/output binding differs')
        size(row['sourceBytes']); size(exp['fbxBytes']); size(exp['archiveBytes'])
        need(exp['filename'] == f'{identity}-{row["version"]}-fbx-minimal-1.0.0.zip', 'Wrong minimal archive identity')
        note = row['notice']; exact(note, 'filename text bytes sha256', 'notice')
        need(note['filename'] == 'LICENSE.txt' and type(note['text']) is str, 'One LICENSE.txt required')
        blob = note['text'].encode('utf-8'); digest(note['sha256'])
        need(type(note['bytes']) is int and 0 < len(blob) == note['bytes'] <= 32 * 1024 and sha(blob) == note['sha256'] == exp['noticeSha256'], 'Notice bytes/hash differ')
        need(note['text'].endswith('\n') and CONVERSION_NOTICE in note['text'], 'Missing retained FBX modification notice')
    return {r['id']: r for r in expected['models']}


def model_binding(row, expected):
    """Concise transport binding; no raw QA, generator metadata or local paths."""
    return {'id': row['id'], 'version': row['version'], 'sourceGlbSha256': row['sourceSha256'],
            'fbx': {'filename': row['id'] + '.fbx', 'bytes': expected['fbxBytes'], 'sha256': expected['fbxSha256']},
            'archive': {'filename': expected['filename'], 'bytes': expected['archiveBytes'], 'sha256': expected['archiveSha256']},
            'notice': row['notice']}


def check_payload_names(public, models):
    expected = {'fbx-minimal-inventory.json'} | {x['fbx']['filename'] for x in models} | {x['archive']['filename'] for x in models}
    actual = {p.name for p in public.iterdir()}
    need(len(expected) == 275 and actual == expected and all(p.is_file() and not p.is_symlink() for p in public.iterdir()), 'Unexpected/missing public artifact entry')


def readable_verified_archives(public, models):
    """Only the already-verified allowlisted ZIPs need root-to-runner readability."""
    check_payload_names(public, models)
    for row in models:
        (public / row['archive']['filename']).chmod(0o644)
