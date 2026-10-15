"""Exact reviewed artifact transport. No rebuild, overwrite, delete, resume or retry."""
import argparse
import contextlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'minimal-verification'))
from common import *
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import minimal_packages as packages

RELEASE_NAME = 'Minimal asset downloads 1.0.0 — original 173 assets'
API = 'https://api.github.com/repos/' + REPO


def approval_check(a, source_bytes, expected_bytes):
    need(a['schemaVersion'] == 1 and a['reviewStatus'] == 'approved-for-transport', 'Transport approval missing')
    need(a['repository'] == REPO and a['tag'] == TAG and a['workflowPath'] == WORKFLOW, 'Wrong repository/tag/workflow')
    commit(a['verificationCommit'])
    for key in ('workflowSha256', 'artifactSha256', 'inventorySha256', 'sourceInventorySha256', 'expectedManifestSha256', 'releaseBodySha256'):
        digest(a[key])
    for key in ('runId', 'runAttempt', 'artifactId'):
        need(type(a[key]) is int and a[key] > 0, 'Invalid run/artifact identity')
    need(a['artifactName'] == f"minimal-existing173-{a['verificationCommit']}-{a['runId']}-{a['runAttempt']}", 'Wrong artifact name')
    need(sha(source_bytes) == a['sourceInventorySha256'] and sha(expected_bytes) == a['expectedManifestSha256'], 'Pinned manifest mismatch')
    source, expected = json.loads(source_bytes), json.loads(expected_bytes)
    check_manifests(source, expected, source_bytes)
    need([r['id'] for r in source['assets']] == a['approvedIds'], 'Wrong approved 173 cohort')
    return source, expected


def check_run(a, run, artifact):
    f = a['verificationCommit']
    need(run['id'] == a['runId'] and run['run_attempt'] == a['runAttempt'], 'Run identity mismatch')
    need(run['repository']['full_name'] == REPO and run['head_repository']['full_name'] == REPO, 'Run repository mismatch')
    need(run['head_sha'] == f and run['head_branch'] == VERIFY_BRANCH and run['event'] == 'push', 'Run source mismatch')
    need(run['path'] == WORKFLOW and run['status'] == 'completed' and run['conclusion'] == 'success', 'Verification is not successful')
    need(artifact['id'] == a['artifactId'] and artifact['name'] == a['artifactName'] and artifact['expired'] is False, 'Artifact identity/expiry mismatch')
    need(artifact['digest'] == 'sha256:' + a['artifactSha256'], 'Artifact API digest mismatch')
    owner = artifact['workflow_run']
    need(owner['id'] == a['runId'] and owner['head_sha'] == f and owner['head_branch'] == VERIFY_BRANCH, 'Artifact ownership mismatch')
    need(owner['repository_id'] == run['repository']['id'] and owner['head_repository_id'] == run['head_repository']['id'], 'Artifact repository ID mismatch')


def expected_inventory(a, source, expected):
    return {'schemaVersion': 1, 'packageVersion': '1.0.0', 'repository': REPO, 'tag': TAG, 'cohort': 'published173',
            'sourceCommit': BASE, 'verificationCommit': a['verificationCommit'], 'workflow': WORKFLOW,
            'runId': str(a['runId']), 'runAttempt': str(a['runAttempt']),
            'sourceInventorySha256': a['sourceInventorySha256'], 'expectedManifestSha256': a['expectedManifestSha256'],
            'packagerSha256': expected['packagerSha256'], 'runtimeSha256': expected['runtimeSha256'],
            'assets': [package_binding(row, exp) for row, exp in zip(source['assets'], expected['assets'])]}


def unpack(a, source, expected, archive, out, repo, materialize=True):
    need(file_sha(archive) == a['artifactSha256'], 'Downloaded artifact digest mismatch')
    entries = {r['filename']: {'name': r['filename'], 'bytes': r['archiveBytes'], 'sha256': r['archiveSha256']} for r in expected['assets']}
    allowed = set(entries) | {'minimal-inventory.json'}
    need(len(allowed) == COUNT + 1, 'Duplicate package names')
    with zipfile.ZipFile(archive) as z, tempfile.TemporaryDirectory(prefix='minimal-readback-') as temporary:
        infos = z.infolist()
        need(len(infos) == len(allowed) and {i.filename for i in infos} == allowed, 'Unexpected/duplicate artifact paths')
        need(sum(i.file_size for i in infos) <= MAX_TOTAL, 'Artifact too large')
        for info in infos:
            need(info.orig_filename == info.filename and not info.is_dir() and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG) and info.compress_type in (0, 8) and not info.flag_bits & 1, 'Unsupported artifact entry')
            need(0 < info.file_size <= MAX_FILE, 'Invalid artifact entry size')
        need(z.getinfo('minimal-inventory.json').file_size <= 2 * 1024**2, 'Binding inventory too large')
        raw = z.read('minimal-inventory.json')
        need(sha(raw) == a['inventorySha256'], 'Binding inventory digest mismatch')
        need(raw == canonical(expected_inventory(a, source, expected)), 'Binding inventory does not exactly match approved source/notice/ZIP hashes')
        entries['minimal-inventory.json'] = {'name': 'minimal-inventory.json', 'bytes': len(raw), 'sha256': sha(raw)}
        out.mkdir(exist_ok=False)
        notice = Path(temporary) / 'LICENSE.txt'
        byname = {exp['filename']: row for row, exp in zip(source['assets'], expected['assets'])}
        for name, entry in sorted(entries.items()):
            info = z.getinfo(name); need(info.file_size == entry['bytes'], 'ZIP declared size differs')
            target = out / name if materialize else Path(temporary) / name
            with z.open(info) as src, target.open('xb') as dst:
                total = 0; checksum = hashlib.sha256()
                while chunk := src.read(1024 * 1024):
                    total += len(chunk); need(total <= entry['bytes'], 'ZIP length exceeded'); checksum.update(chunk); dst.write(chunk)
            need(total == entry['bytes'] and checksum.hexdigest() == entry['sha256'], 'Payload hash/length mismatch')
            if name in byname:
                row = byname[name]; notice.write_text(row['notice']['text'], encoding='utf-8')
                plan = packages.make_plan(repo / 'content/assets' / row['id'], notice)
                packages.verify_archive(target, plan)
            if not materialize: target.unlink()
    return sorted(entries.values(), key=lambda r: r['name'])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, path, method='GET', value=None, raw=None):
        url = path if path.startswith('https://') else API + path
        parsed = urllib.parse.urlsplit(url)
        need(parsed.scheme == 'https' and parsed.netloc in ('api.github.com', 'uploads.github.com'), 'Invalid authenticated destination')
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-minimal-transport'}
        data = canonical(value) if value is not None else raw
        if data is not None: headers['Content-Type'] = 'application/json' if value is not None else 'application/octet-stream'
        return self.opener.open(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=180)

    def json(self, path, method='GET', value=None):
        with self.request(path, method, value) as response: return json.load(response)

    def download(self, path, target, limit):
        try:
            response = self.request(path)
        except urllib.error.HTTPError as error:
            need(error.code == 302, 'Authenticated download failed')
            url = error.headers['Location']; need(urllib.parse.urlsplit(url).scheme == 'https', 'Insecure redirect')
            # Signed artifact/blob URL gets NO Authorization or other authenticated headers.
            response = urllib.request.urlopen(url, timeout=180)
        stream_file(response, target, limit)


def stream_file(response, target, limit):
    with response, target.open('xb') as handle:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk); need(total <= limit, 'Download exceeds bound'); handle.write(chunk)
    return total


def absence(api):
    for path in ('/git/ref/tags/' + TAG, '/releases/tags/' + TAG):
        try: api.json(path)
        except urllib.error.HTTPError as error:
            need(error.code == 404, 'Absence check failed')
        else: raise ValueError('Tag/release already exists; inspect, never overwrite')


def check_draft(api, release_id, body, f):
    current = api.json('/releases/' + str(release_id))
    need(current['id'] == release_id and current['draft'] is True and current['target_commitish'] == f and current['tag_name'] == TAG, 'Draft identity changed before finalization')
    need(current['name'] == RELEASE_NAME and current['body'] == body and current['prerelease'] is False, 'Draft public metadata changed before finalization')
    # GitHub may create a lightweight tag when creating or publishing the draft.
    # An existing tag must already resolve directly to F before publication.
    try:
        ref = api.json('/git/ref/tags/' + TAG)
    except urllib.error.HTTPError as error:
        need(error.code == 404, 'Prepublication tag lookup failed')
    else:
        need(ref['object']['type'] == 'commit' and ref['object']['sha'] == f, 'Tag changed before finalization')


def journal(path, phase, **values):
    with path.open('a') as handle:
        handle.write(json.dumps({'phase': phase, **values}, sort_keys=True) + '\n'); handle.flush(); os.fsync(handle.fileno())


def assets(api, release_id):
    result = []; page = 1
    while True:
        part = api.json(f'/releases/{release_id}/assets?per_page=100&page={page}')
        result.extend(part)
        if len(part) < 100: break
        page += 1; need(page <= 11, 'Too many release attachments')
    return result


def verify_assets(api, release, expected, work, anonymous=False):
    remote = assets(api, release['id']); index = {r['name']: r for r in remote}
    need(len(remote) == len(index) == len(expected) and set(index) == {r['name'] for r in expected}, 'Release attachment inventory mismatch')
    evidence = []
    for entry in expected:
        asset = index[entry['name']]
        need(asset['state'] == 'uploaded' and asset['size'] == entry['bytes'], 'Remote attachment state/size mismatch')
        need(asset.get('digest') == 'sha256:' + entry['sha256'], 'Remote attachment digest mismatch')
        temp = work / 'readback.bin'
        if anonymous:
            url = f"https://github.com/{REPO}/releases/download/{TAG}/{entry['name']}"
            need(asset['browser_download_url'] == url, 'Unexpected public attachment URL')
            stream_file(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'meshcopia-public-readback'}), timeout=180), temp, entry['bytes'])
        else:
            # Asset API needs octet-stream accept, unlike metadata API.
            url = f'https://api.github.com/repos/{REPO}/releases/assets/{asset["id"]}'
            api.download_asset(url, temp, entry['bytes'])
        need(temp.stat().st_size == entry['bytes'] and file_sha(temp) == entry['sha256'], 'Remote byte readback mismatch')
        temp.unlink()
        evidence.append({**entry, 'assetId': asset['id'], 'url': asset['browser_download_url'], 'anonymousReadback': anonymous})
    return evidence


def download_asset(self, url, target, limit):
    need(url.startswith(f'https://api.github.com/repos/{REPO}/releases/assets/') and url[len(f'https://api.github.com/repos/{REPO}/releases/assets/'):].isdigit(), 'Invalid authenticated asset destination')
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/octet-stream', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-minimal-transport'})
    try: response = self.opener.open(request, timeout=180)
    except urllib.error.HTTPError as error:
        need(error.code == 302, 'Asset byte download failed')
        location = error.headers['Location']; need(urllib.parse.urlsplit(location).scheme == 'https', 'Insecure asset redirect')
        response = urllib.request.urlopen(location, timeout=180)
    stream_file(response, target, limit)


GitHub.download_asset = download_asset


def publish(api, body, entries, work, approval):
    f = approval['verificationCommit']
    log = work / 'journal.jsonl'
    absence(api); journal(log, 'create-draft-requested', verificationCommit=f, tag=TAG)
    release = api.json('/releases', 'POST', {'tag_name': TAG, 'target_commitish': f, 'name': RELEASE_NAME, 'body': body.decode(), 'draft': True, 'prerelease': False, 'generate_release_notes': False})
    need(release['draft'] is True and release['tag_name'] == TAG and release['target_commitish'] == f, 'Created draft differs')
    journal(log, 'draft-created', releaseId=release['id'])
    for entry in entries:
        journal(log, 'upload-requested', name=entry['name'])
        url = f'https://uploads.github.com/repos/{REPO}/releases/{release["id"]}/assets?name=' + urllib.parse.quote(entry['name'])
        with api.request(url, 'POST', raw=(work / 'payload' / entry['name']).read_bytes()) as response: uploaded = json.load(response)
        journal(log, 'uploaded', name=entry['name'], assetId=uploaded['id'])
    verify_assets(api, release, entries, work)
    journal(log, 'draft-byte-readback-passed', releaseId=release['id'], attachments=len(entries))
    check_draft(api, release['id'], body.decode(), f)
    journal(log, 'publish-requested', releaseId=release['id'])
    published = api.json('/releases/' + str(release['id']), 'PATCH', {'draft': False, 'make_latest': 'false'})
    need(published['draft'] is False and published['id'] == release['id'] and published['tag_name'] == TAG and published['html_url'] == f'https://github.com/{REPO}/releases/tag/{TAG}', 'Publication response not final/exact')
    ref = api.json('/git/ref/tags/' + TAG); need(ref['object']['type'] == 'commit' and ref['object']['sha'] == f, 'Published tag differs from F')
    journal(log, 'published', releaseId=release['id'])
    proof = verify_assets(api, published, entries, work, anonymous=True)
    evidence = {'schemaVersion': 1, 'status': 'anonymous-byte-readback-passed', 'repository': REPO, 'tag': TAG, 'verificationCommit': f, 'releaseId': release['id'], 'releaseUrl': published['html_url'], 'attachmentCount': len(proof), 'inventorySha256': file_sha(work / 'payload/minimal-inventory.json'), 'browserDownloadEvidence': 'not-performed-by-transport', 'assets': proof}
    (work / 'T-evidence.json').write_bytes(canonical(evidence)); journal(log, 'anonymous-readback-passed', releaseId=release['id'])
    print('Published 173 exact reviewed minimal ZIPs and one binding inventory; all anonymous byte readbacks passed. UI activation remains separate.')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--repo', type=Path, required=True); parser.add_argument('--work', type=Path, required=True); args = parser.parse_args()
    repo = args.repo.resolve(); docs = repo / 'docs/minimal-verification'
    a = read(repo / 'docs/minimal-transport/approval.json')
    source, expected = approval_check(a, (docs / 'source173.json').read_bytes(), (docs / 'expected173.json').read_bytes())
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_REF') == 'refs/heads/' + RELEASE_BRANCH, 'Wrong release execution context')
    check_repository(repo)
    f = a['verificationCommit']; head = os.environ['GITHUB_SHA']
    need(git(repo, 'rev-parse', 'HEAD').decode().strip() == head and git(repo, 'show', '-s', '--format=%P', head).decode().strip() == f, 'Release must directly follow exact verified commit, without merge')
    need(git(repo, 'status', '--porcelain', '--untracked-files=no') == b'', 'Dirty transport checkout')
    changed = git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', f, head).decode().split('\0')[:-1]
    allowed = {'.github/workflows/release-minimal.yml', 'scripts/minimal-transport/transport.py', 'scripts/minimal-transport/prepare_approval.py', 'scripts/minimal-transport/test_transport.py', 'docs/minimal-transport/README.md', 'docs/minimal-transport/RELEASE_BODY.md', 'docs/minimal-transport/approval.json'}
    need(len(changed) % 2 == 0 and all(s == 'A' for s in changed[::2]) and set(changed[1::2]) == allowed, 'Release changes unapproved paths')
    release_tree = tree(repo, head)
    need(all(release_tree[path][:2] == ('100644', 'blob') for path in allowed), 'Unsafe transport tree mode')
    need(sha(git(repo, 'show', f + ':' + WORKFLOW)) == a['workflowSha256'], 'Verification workflow digest mismatch')
    need(file_sha(Path(packages.__file__)) == expected['packagerSha256'], 'Packager changed')
    body = (repo / 'docs/minimal-transport/RELEASE_BODY.md').read_bytes(); need(sha(body) == a['releaseBodySha256'], 'Release body changed')
    work = args.work; work.mkdir(exist_ok=False, parents=True)
    api = GitHub(os.environ['GH_TOKEN'])
    check_run(a, api.json('/actions/runs/' + str(a['runId'])), api.json('/actions/artifacts/' + str(a['artifactId'])))
    archive = work / 'artifact.zip'; api.download('/actions/artifacts/' + str(a['artifactId']) + '/zip', archive, MAX_TOTAL)
    entries = unpack(a, source, expected, archive, work / 'payload', repo); archive.unlink()
    check_run(a, api.json('/actions/runs/' + str(a['runId'])), api.json('/actions/artifacts/' + str(a['artifactId'])))
    publish(api, body, entries, work, a)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('MINIMAL_TRANSPORT_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__))
        raise SystemExit(1)
