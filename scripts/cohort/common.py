"""Strict bindings shared by the new-cohort verification (F), transport (R)
and site-preparation (P) adapters. Nothing in this module publishes or uploads.

A cohort is an explicit, reviewed list of models that were staged as drafts on
`main`. Its manifests live in docs/cohorts/<name>/ and bind exact metadata,
source bytes, retained notices and (after a successful discovery run) the exact
FBX and ZIP outputs. The original 137/173 adapters are not modified or reused
for their frozen counts; only their unchanged recipe, verifier and packager
modules are imported.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

REPO = 'Xenoah/meshcopia'
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/fbx-verification'))
import minimal_packages as packages  # noqa: E402
import minimal_notices as notices  # noqa: E402

PIPELINE = '9c14ed64ff019ef1fc6cdf4d86df1c4504f1cd1a675c4cb1bd4ac3c2f37cb500'
RUNTIME = 'docs/fbx-minimal-verification/runtime.json'
CONVERSION_NOTICE = 'Converted unchanged source GLB geometry to FBX, with documented compatible material/texture derivatives.'
PACKAGE_VERSION = '1.0.0'
ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
NAME = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')
SITE = 'https://xenoah.github.io/meshcopia'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
def compact(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
def read(path): return packages.load_json(path)
def file_sha(path): return packages.hash_file(packages.regular_file(path))[1]
def dump(path, value): Path(path).write_bytes(canonical(value))
def digest(value): need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA-256')
def commit(value): need(type(value) is str and re.fullmatch('[0-9a-f]{40}', value), 'Invalid commit')
def size(value): need(type(value) is int and 0 < value <= packages.MAX_FILE_BYTES, 'Invalid bounded byte size')
def exact(value, fields, label): need(type(value) is dict and set(value) == set(fields.split()), 'Unknown/missing ' + label + ' fields')


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    return subprocess.check_output(['git', '--no-replace-objects', '-c', 'safe.directory=' + str(repo), '-C', str(repo), *args], env=env)


def is_ancestor(repo, ancestor, descendant):
    try:
        git(repo, 'merge-base', '--is-ancestor', ancestor, descendant); return True
    except subprocess.CalledProcessError as exc:
        need(exc.returncode == 1, 'Git ancestry check failed'); return False


def tree(repo, revision):
    result = {}
    for item in git(repo, 'ls-tree', '-r', '-z', revision).split(b'\0'):
        if item:
            header, name = item.split(b'\t', 1)
            result[name.decode()] = tuple(header.decode().split())
    return result


def blob(repo, entries, path, checksum=None, byte_count=None):
    packages.safe_relative(path)
    need(path in entries and entries[path][:2] == ('100644', 'blob'), 'Missing/unsafe pinned input: ' + path)
    data = git(repo, 'cat-file', 'blob', entries[path][2])
    need(checksum is None or sha(data) == checksum, 'Pinned bytes differ: ' + path)
    need(byte_count is None or len(data) == byte_count, 'Pinned byte count differs: ' + path)
    return data


def clean_checkout(repo):
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
    need(git(repo, 'status', '--porcelain', '--untracked-files=no') == b'', 'Dirty tracked checkout')


def cohort_paths(name):
    need(type(name) is str and NAME.fullmatch(name), 'Invalid cohort name')
    base = f'docs/cohorts/{name}'
    return {'dir': base, 'source': base + '/source.json', 'expected': base + '/expected.json'}


def notice_texts(metadata):
    """Exact retained short notices for the ordinary and FBX minimal ZIPs."""
    old_license, old_attribution = notices.baseline_notices(metadata)
    ordinary = notices.make_notice(metadata, old_license, old_attribution)
    fbx = notices.make_notice(metadata, old_license, old_attribution, fbx_attribution='Changes: ' + CONVERSION_NOTICE + '\n')
    need(CONVERSION_NOTICE in fbx and CONVERSION_NOTICE not in ordinary, 'Notice derivation mismatch')
    return ordinary, fbx


def notice_record(text):
    data = text.encode('utf-8')
    return {'filename': 'LICENSE.txt', 'text': text, 'bytes': len(data), 'sha256': sha(data)}


def check_notice(note, metadata, fbx):
    exact(note, 'filename text bytes sha256', 'notice')
    data = note['text'].encode('utf-8') if type(note['text']) is str else b''
    need(note['filename'] == 'LICENSE.txt' and 0 < len(data) == note['bytes'] <= 32 * 1024 and sha(data) == note['sha256'], 'Notice bytes/hash differ')
    ordinary, converted = notice_texts(metadata)
    need(note['text'] == (converted if fbx else ordinary), 'Notice does not equal the retained baseline attribution')


def archive_names(identity, version):
    return {'fbx': f'{identity}.fbx',
            'fbxArchive': f'{identity}-{version}-fbx-minimal-{PACKAGE_VERSION}.zip',
            'archive': f'{identity}-{version}-minimal-{PACKAGE_VERSION}.zip'}


SOURCE_FIELDS = 'schemaVersion cohort baseCommit modelCount packageVersion pipelineSha256 models'
SOURCE_ROW = 'id version status assetMetadata metadataSha256 sourceGLB sourceSha256 sourceBytes sourceFiles stageCommit notice fbxNotice'
EXPECTED_FIELDS = 'schemaVersion reviewStatus cohort baseCommit sourceInventorySha256 runtimeSha256 pipelineSha256 packageVersion models'
EXPECTED_ROW = 'id sourceGlbSha256 fbx fbxArchive archive'


def check_source(source):
    exact(source, SOURCE_FIELDS, 'source manifest')
    need(source['schemaVersion'] == 1 and NAME.fullmatch(source['cohort']) and source['packageVersion'] == PACKAGE_VERSION and source['pipelineSha256'] == PIPELINE, 'Wrong cohort schema/recipe/package')
    commit(source['baseCommit'])
    rows = source['models']
    need(type(rows) is list and 0 < len(rows) == source['modelCount'] <= 300, 'Bounded explicit model list required')
    ids = [r.get('id') for r in rows]
    need(ids == sorted(set(ids)), 'Duplicate/unsorted cohort IDs')
    for row in rows:
        exact(row, SOURCE_ROW, 'source row')
        identity = row['id']
        need(type(identity) is str and ID.fullmatch(identity), 'Invalid model identity')
        need(type(row['version']) is str and packages.VERSION.fullmatch(row['version']), 'Invalid version')
        need(row['status'] == 'public', 'Cohort metadata must be the final public metadata')
        need(row['assetMetadata'] == f'content/assets/{identity}/asset.json' and row['sourceGLB'] == f'content/assets/{identity}/source/{identity}.glb', 'Noncanonical path')
        digest(row['metadataSha256']); digest(row['sourceSha256']); size(row['sourceBytes']); commit(row['stageCommit'])
        files = row['sourceFiles']
        need(type(files) is list and files and [f.get('name') for f in files] == sorted({f.get('name') for f in files}), 'Sorted unique source inventory required')
        for f in files:
            exact(f, 'name bytes sha256', 'source file'); packages.safe_relative(f['name']); size(f['bytes']); digest(f['sha256'])
        need({'name': identity + '.glb', 'bytes': row['sourceBytes'], 'sha256': row['sourceSha256']} in files, 'Source GLB missing from inventory')
    return {r['id']: r for r in rows}


def check_expected(expected, source, source_bytes, runtime_sha):
    exact(expected, EXPECTED_FIELDS, 'expected manifest')
    need(expected['schemaVersion'] == 1 and expected['cohort'] == source['cohort'] and expected['baseCommit'] == source['baseCommit'], 'Expected manifest belongs to another cohort')
    need(expected['sourceInventorySha256'] == sha(source_bytes) and expected['runtimeSha256'] == runtime_sha and expected['pipelineSha256'] == PIPELINE and expected['packageVersion'] == PACKAGE_VERSION, 'Expected manifest bindings differ')
    need(expected['reviewStatus'] in ('discovery', 'reproduced-final'), 'Unknown review status')
    if expected['reviewStatus'] == 'discovery':
        need(expected['models'] == [], 'Discovery manifest cannot pre-assert outputs')
        return None
    rows = expected['models']
    need([r.get('id') for r in rows] == [r['id'] for r in source['models']], 'Expected rows must equal the source cohort')
    byid = {r['id']: r for r in source['models']}
    for row in rows:
        exact(row, EXPECTED_ROW, 'expected row')
        names = archive_names(row['id'], byid[row['id']]['version'])
        need(row['sourceGlbSha256'] == byid[row['id']]['sourceSha256'], 'Expected source binding differs')
        for key in ('fbx', 'fbxArchive', 'archive'):
            exact(row[key], 'filename bytes sha256', key)
            need(row[key]['filename'] == names[key], 'Noncanonical output name'); size(row[key]['bytes']); digest(row[key]['sha256'])
    return {r['id']: r for r in rows}


def model_binding(row, outputs):
    """Concise public inventory record: no QA, local paths or generator data."""
    return {'id': row['id'], 'version': row['version'], 'metadataSha256': row['metadataSha256'],
            'sourceGlbSha256': row['sourceSha256'], 'sourceFiles': row['sourceFiles'],
            'fbx': outputs['fbx'], 'fbxArchive': outputs['fbxArchive'], 'archive': outputs['archive'],
            'notice': {k: row['notice'][k] for k in ('filename', 'bytes', 'sha256')},
            'fbxNotice': {k: row['fbxNotice'][k] for k in ('filename', 'bytes', 'sha256')}}


def payload_names(models):
    names = {'cohort-inventory.json'}
    for m in models:
        names |= {m['fbx']['filename'], m['fbxArchive']['filename'], m['archive']['filename']}
    need(len(names) == 3 * len(models) + 1, 'Payload name collision')
    return names
