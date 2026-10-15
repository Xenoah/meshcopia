"""Shared fail-closed original173 minimal-package contract (stdlib only)."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

BASE = '4ab5342568a4227215b295b40a47c27698cc930a'
REPO = 'Xenoah/meshcopia'
TAG = 'minimal-v1.0.0'
VERIFY_BRANCH = 'minimal/verify-existing173-v1'
RELEASE_BRANCH = 'minimal/release-existing173-v1'
WORKFLOW = '.github/workflows/verify-minimal.yml'
COUNT = 173
KINDS = {'model': 137, 'texture': 36}
MAX_FILE = 2 * 1024**3 - 1
MAX_TOTAL = 4 * 1024**3


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def file_sha(path):
    need(path.is_file() and not path.is_symlink(), 'Expected regular file')
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def digest(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA256')
    return value


def commit(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value), 'Invalid commit')
    return value


def safe(value):
    need(isinstance(value, str) and re.fullmatch('[a-zA-Z0-9._/-]+', value) and all(p not in ('', '.', '..') for p in value.split('/')), 'Unsafe path')
    return value


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    return subprocess.check_output(['git', '--no-replace-objects', '-c', 'safe.directory=' + str(repo), '-C', str(repo), *args], env=env)



def check_repository(repo):
    need(git(repo, 'rev-parse', '--is-shallow-repository').strip() == b'false', 'Shallow checkout prohibited')
    for args in (('config', '--get', 'extensions.partialClone'), ('config', '--get-regexp', r'^remote\..*\.promisor$')):
        try:
            git(repo, *args)
        except subprocess.CalledProcessError as error:
            need(error.returncode == 1, 'Repository configuration read failed')
        else:
            raise ValueError('Partial/promisor repository prohibited')
    graft_path = Path(git(repo, 'rev-parse', '--git-path', 'info/grafts').decode().strip())
    if not graft_path.is_absolute(): graft_path = repo / graft_path
    need(not graft_path.exists() or not graft_path.read_text().strip(), 'Grafted history prohibited')


def tree(repo, ref):
    result = {}
    for raw in git(repo, 'ls-tree', '-r', '-z', ref).split(b'\0'):
        if raw:
            header, name = raw.split(b'\t', 1)
            mode, kind, oid = header.decode().split()
            result[name.decode()] = (mode, kind, oid)
    return result


def check_manifests(source, expected, source_bytes):
    need(source.get('schemaVersion') == 1 and source.get('sourceCommit') == BASE and source.get('cohort') == 'published173', 'Wrong source cohort/base')
    need(expected.get('schemaVersion') == 1 and expected.get('sourceCommit') == BASE and expected.get('cohort') == 'published173', 'Wrong expected cohort/base')
    need(expected.get('reviewStatus') == 'final-reviewed', 'Expected ZIP hashes are not reviewed')
    need(expected.get('sourceInventorySha256') == sha(source_bytes), 'Source manifest hash mismatch')
    digest(expected['packagerSha256']); digest(expected['runtimeSha256'])
    rows = source['assets']; ex = expected['assets']
    ids = [r['id'] for r in rows]
    need(ids == sorted(ids) and len(ids) == len(set(ids)) == COUNT, 'Wrong/duplicate/unsorted original173 IDs')
    need({kind: sum(r['kind'] == kind for r in rows) for kind in KINDS} == KINDS, 'Wrong 137 model / 36 texture cohort')
    need(len(ex) == COUNT and [r['id'] for r in ex] == ids, 'Expected cohort differs')
    for row, exp in zip(rows, ex):
        need(re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', row['id']) and re.fullmatch(r'\d+\.\d+\.\d+', row['version']), 'Unsafe asset identity')
        need(row['status'] == 'public' and row['kind'] in KINDS, 'Nonpublic/unsupported asset')
        need(exp['filename'] == f"{row['id']}-{row['version']}-minimal-1.0.0.zip", 'Noncanonical minimal filename')
        digest(exp['archiveSha256'])
        need(type(exp['archiveBytes']) is int and 0 < exp['archiveBytes'] <= MAX_FILE, 'Invalid archive size')
        notice = row['notice']; raw = notice['text'].encode('utf-8')
        need(notice['filename'] == 'LICENSE.txt' and notice['bytes'] == len(raw) and notice['sha256'] == sha(raw), 'Notice text/hash mismatch')
        need(0 < len(raw) <= 16384, 'Notice is missing or too long')
        need(exp['noticeSha256'] == notice['sha256'], 'Expected notice differs')
        digest(row['metadataSha256'])
        files = row['sourceFiles']; names = [f['name'] for f in files]
        need(names == sorted(names) and len(names) == len(set(names)) and names, 'Source inventory incomplete/duplicate')
        for file in files:
            safe(file['name']); digest(file['sha256'])
            need(type(file['bytes']) is int and 0 < file['bytes'] <= MAX_FILE, 'Source file size invalid')
    return {row['id']: row for row in ex}


def package_binding(row, expected):
    name = expected['filename']
    return {'id': row['id'], 'version': row['version'], 'kind': row['kind'], 'filename': name,
            'bytes': expected['archiveBytes'], 'sha256': expected['archiveSha256'],
            'url': f'https://github.com/{REPO}/releases/download/{TAG}/{name}',
            'sourceFiles': row['sourceFiles'], 'notice': row['notice']}
