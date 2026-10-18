"""Cohort R: transport exact reviewed F bytes into one new immutable release.

Runs only in .github/workflows/release-cohort.yml on cohort/release-<name>,
whose single commit adds the approval, this adapter, its workflow and release
body on top of the exact final F commit. It never converts or repackages:
it re-verifies the successful F run, both artifact envelopes, every payload
byte and ZIP member against the committed manifests, then creates a draft
release, uploads exactly the reviewed files, publishes it once and reads every
attachment back anonymously. Every consequential request is journaled before
it is made and never retried automatically. T evidence is pushed to
evidence/cohort-<name>-transport-<run>-<attempt>; it is not a release asset.
"""
import argparse
import base64
import io
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from common import *

API = 'https://api.github.com/repos/' + REPO
UPLOADS = 'https://uploads.github.com/repos/' + REPO
APPROVAL_FIELDS = ('schemaVersion reviewStatus approvedBy approvalNote repository cohort tag fCommit runId runAttempt jobId '
                   'payloadArtifact qaArtifact inventorySha256 sourceInventorySha256 expectedManifestSha256 runtimeSha256 releaseBodySha256')
R_PATHS = ('.github/workflows/release-cohort.yml', 'scripts/cohort/transport.py')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


OPENER = urllib.request.build_opener(NoRedirect)


class Journal:
    def __init__(self, path): self.path = path
    def write(self, **event):
        with self.path.open('a') as f:
            f.write(json.dumps({'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **event}, sort_keys=True) + '\n'); f.flush(); os.fsync(f.fileno())


def request(url, token=None, method='GET', data=None, content_type=None, accept='application/vnd.github+json', timeout=600):
    headers = {'Accept': accept, 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-cohort-transport'}
    if token: headers['Authorization'] = 'Bearer ' + token
    if content_type: headers['Content-Type'] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with OPENER.open(req, timeout=timeout) as r: return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def api_json(path, token, method='GET', body=None, expect=(200,)):
    status, _, data = request(API + path, token, method, json.dumps(body).encode() if body is not None else None, 'application/json' if body is not None else None)
    need(status in expect, f'Unexpected API status {status} for {method} {path.split("?")[0]}')
    return json.loads(data) if data else None


def download(url, token, target, expected_sha=None, expected_bytes=None):
    """GET with auth only on api.github.com; follow at most two redirects without credentials."""
    current = url; auth = token if url.startswith('https://api.github.com/') else None
    for _ in range(3):
        # Artifact archives require the API media type; release assets the binary one.
        accept = 'application/octet-stream' if '/releases/assets/' in current else ('application/vnd.github+json' if current.startswith('https://api.github.com/') else '*/*')
        req = urllib.request.Request(current, headers={'User-Agent': 'meshcopia-cohort-transport', **({'Authorization': 'Bearer ' + auth} if auth else {}), 'Accept': accept})
        try:
            with OPENER.open(req, timeout=1200) as r:
                h = hashlib.sha256(); n = 0
                with open(target, 'xb') as out:
                    while chunk := r.read(1 << 20):
                        h.update(chunk); n += len(chunk); out.write(chunk)
                need(expected_sha is None or h.hexdigest() == expected_sha, 'Downloaded digest differs: ' + Path(target).name)
                need(expected_bytes is None or n == expected_bytes, 'Downloaded size differs: ' + Path(target).name)
                return n, h.hexdigest()
        except urllib.error.HTTPError as e:
            need(e.code in (301, 302, 303, 307, 308) and e.headers.get('Location', '').startswith('https://'), f'Download failed with status {e.code}')
            current = e.headers['Location']; auth = None
            Path(target).unlink(missing_ok=True)
    raise ValueError('Too many redirects')


def safe_extract(archive, target, expected_names, max_total=6 * 1024 ** 3):
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist(); names = [i.filename for i in infos]
        need(len(names) == len(set(names)) and len({n.casefold() for n in names}) == len(names), 'Duplicate/case-colliding artifact names')
        need(set(names) == set(expected_names), 'Artifact entries differ from the reviewed set')
        need(all('/' not in n and '\\' not in n and not n.startswith('.') and not i.is_dir() and i.flag_bits & 1 == 0 for n, i in zip(names, infos)), 'Unsafe artifact entry')
        need(all((i.external_attr >> 16) & 0o170000 in (0, 0o100000) for i in infos), 'Non-regular artifact entry')
        need(sum(i.file_size for i in infos) <= max_total and all(i.file_size <= packages.MAX_FILE_BYTES for i in infos), 'Artifact exceeds bounds')
        target.mkdir()
        for i in infos:
            with z.open(i) as src, open(target / i.filename, 'xb') as dst: shutil.copyfileobj(src, dst, 1 << 20)


def check_zip(path, members):
    """Exact entries and member bytes; no directories, links or extras."""
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        need([i.filename for i in infos] == sorted(members, key=lambda n: n.encode('utf-8')), 'ZIP entries differ: ' + path.name)
        need(z.testzip() is None, 'ZIP CRC failure: ' + path.name)
        for i in infos:
            need(not i.is_dir() and (i.external_attr >> 16) & 0o170000 in (0, 0o100000), 'Non-regular ZIP member')
            need(sha(z.read(i)) == members[i.filename], 'ZIP member bytes differ: ' + path.name + '/' + i.filename)


def consumer_payload_names(models):
    names = {'cohort-inventory.json'}
    for row in models:
        names.update(row[k]['filename'] for k in ('fbx', 'fbxArchive'))
    need(len(names) == 2 * len(models) + 1, 'Consumer payload name collision')
    return names


def verify_payload(root, inventory, source, expected, repo):
    byid = {r['id']: r for r in source['models']}
    need([m['id'] for m in inventory['models']] == sorted(byid), 'Inventory cohort differs')
    for m in inventory['models']:
        row = byid[m['id']]; exp = expected[m['id']]
        need(m == model_binding(row, {k: exp[k] for k in ('fbx', 'fbxArchive', 'archive')}), 'Inventory binding differs from committed manifests: ' + m['id'])
        for key in ('fbx', 'fbxArchive', 'archive'):
            b, h = packages.hash_file(packages.regular_file(root / m[key]['filename']))
            need(b == m[key]['bytes'] and h == m[key]['sha256'], 'Payload bytes differ: ' + m[key]['filename'])
        check_zip(root / m['fbxArchive']['filename'], {m['id'] + '.fbx': m['fbx']['sha256'], 'LICENSE.txt': row['fbxNotice']['sha256']})
        check_zip(root / m['archive']['filename'], {**{x['name']: x['sha256'] for x in row['sourceFiles']}, 'LICENSE.txt': row['notice']['sha256']})
        for x in row['sourceFiles']:
            need(file_sha(repo / 'content/assets' / m['id'] / 'source' / x['name']) == x['sha256'], 'Checkout source differs: ' + m['id'])


def verify_qa(root, approval, inventory):
    names = [p.name for p in root.iterdir()]
    need('qa.json' in names and 'runtime.json' in names, 'Internal QA files missing')
    qa = read(root / 'qa.json')
    need(qa['status'] == 'fresh-fbx-and-minimal-packages-verified' and qa['cohort'] == approval['cohort'] and qa['fCommit'] == approval['fCommit'] and str(qa['runId']) == str(approval['runId']) and str(qa['runAttempt']) == str(approval['runAttempt']), 'QA identity differs')
    need(qa['reviewStatus'] == 'reproduced-final', 'Only reproduced-final QA can be transported')
    records = qa['fbxQa']['records']; ids = [m['id'] for m in inventory['models']]
    need(sorted(r['id'] for r in records) == ids and all(r['cleanImportEvidence'] == {'reportAttestedClosure': True, 'embeddedBytesIndependentlyChecked': True, 'extractedCopiesAvailable': True} for r in records), 'Clean-import QA closure incomplete')
    byid = {m['id']: m for m in inventory['models']}
    for r in records: need(r['fbx'] == byid[r['id']]['fbx'] and r['sourceGlbSha256'] == byid[r['id']]['sourceGlbSha256'] and r['pipelineSha256'] == PIPELINE, 'QA output binding differs')
    for p in qa['packages']:
        need(p['outputs'] == {k: byid[p['id']][k] for k in ('fbx', 'fbxArchive', 'archive')}, 'QA package binding differs')
        for kind in ('fbx', 'model'):
            v = p['verification'][kind]
            need(all(v.get(k) is True for k in ('exactAllowlist', 'payloadHashesVerified', 'cleanExtractionVerified', 'dependencyClosureVerified')), 'Package verification incomplete')
    return {'status': 'exact-internal-qa-rechecked', 'models': len(records), 'qaSha256': file_sha(root / 'qa.json'), 'blenderRerunByTransport': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path); parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args(); repo = args.repo.resolve(); token = os.environ.pop('GH_TOKEN', ''); need(token, 'Token required')
    work = args.work; work.mkdir(parents=True); journal = Journal(work / 'journal.jsonl')
    branch = os.environ.get('GITHUB_REF', ''); need(branch.startswith('refs/heads/cohort/release-'), 'Wrong branch')
    name = branch[len('refs/heads/cohort/release-'):]; paths = cohort_paths(name)
    need(name == 'new30', 'This consumer-only transport is reviewed for new30')
    head = os.environ['GITHUB_SHA']; commit(head); clean_checkout(repo)
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_EVENT_NAME') == 'push' and git(repo, 'rev-parse', 'HEAD').decode().strip() == head, 'Exact push checkout required')
    approval_path = paths['dir'] + '/approval.json'; body_path = paths['dir'] + '/RELEASE_BODY.md'
    approval = read(repo / approval_path); exact(approval, APPROVAL_FIELDS, 'approval')
    need(approval['schemaVersion'] == 1 and approval['reviewStatus'] == 'approved-for-transport' and approval['repository'] == REPO and approval['cohort'] == name, 'Approval does not authorize this cohort')
    need(approval['tag'] == f'cohort-{name}-v1.0.0', 'Unexpected release tag')
    f = approval['fCommit']; commit(f)
    parents = git(repo, 'show', '-s', '--format=%P', head).decode().split(); need(parents == [f], 'R must directly follow the approved F')
    changes = git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', f, head).decode().split('\0')[:-1]
    need(all(s == 'A' for s in changes[::2]) and set(changes[1::2]) == {*R_PATHS, approval_path, body_path}, 'R must add exactly the reviewed transport paths')
    source_bytes = (repo / paths['source']).read_bytes(); source = read(repo / paths['source']); check_source(source)
    expected = check_expected(read(repo / paths['expected']), source, source_bytes, file_sha(repo / RUNTIME)); need(expected is not None, 'Final expected manifest required')
    need(approval['sourceInventorySha256'] == sha(source_bytes) and approval['expectedManifestSha256'] == file_sha(repo / paths['expected']) and approval['runtimeSha256'] == file_sha(repo / RUNTIME), 'Approval manifest pins differ')
    body = (repo / body_path).read_bytes(); need(sha(body) == approval['releaseBodySha256'] and len(body) < 120_000, 'Release body differs')
    # Successful F run, job and artifact envelopes.
    run = api_json(f'/actions/runs/{approval["runId"]}', token)
    need(run['head_sha'] == f and run['path'] == '.github/workflows/verify-cohort.yml' and run['event'] == 'push' and run['head_branch'] == f'cohort/verify-{name}'
         and run['run_attempt'] == approval['runAttempt'] and run['status'] == 'completed' and run['conclusion'] == 'success' and run['repository']['full_name'] == REPO, 'F run is not the approved successful run')
    jobs = api_json(f'/actions/runs/{approval["runId"]}/attempts/{approval["runAttempt"]}/jobs', token)['jobs']
    verify_job = [j for j in jobs if j['name'] == 'verify']
    need(len(verify_job) == 1 and verify_job[0]['id'] == approval['jobId'] and verify_job[0]['conclusion'] == 'success' and all(s['conclusion'] in ('success', 'skipped') for s in verify_job[0]['steps']), 'F verification job differs')
    need(all(j['conclusion'] == 'success' for j in jobs), 'Every F job must succeed')
    artifacts = {}
    for key in ('payloadArtifact', 'qaArtifact'):
        meta = api_json(f'/actions/artifacts/{approval[key]["id"]}', token); want = approval[key]
        need(meta['name'] == want['name'] and meta['digest'] == want['digest'] and not meta['expired'] and meta['workflow_run']['id'] == approval['runId'] and meta['workflow_run']['head_sha'] == f, 'Artifact envelope differs: ' + key)
        target = work / (key + '.zip'); download(f'{API}/actions/artifacts/{want["id"]}/zip', token, target, want['digest'].split(':', 1)[1])
        artifacts[key] = target
    payload = work / 'payload'
    inventory_names = None
    with zipfile.ZipFile(artifacts['payloadArtifact']) as z: inventory_bytes = z.read('cohort-inventory.json')
    need(sha(inventory_bytes) == approval['inventorySha256'], 'Inventory digest differs from approval'); inventory = json.loads(inventory_bytes)
    need(inventory['fCommit'] == f and str(inventory['runId']) == str(approval['runId']) and inventory['reviewStatus'] == 'reproduced-final' and inventory['cohort'] == name, 'Inventory identity differs')
    need(inventory['sourceInventorySha256'] == approval['sourceInventorySha256'] and inventory['expectedManifestSha256'] == approval['expectedManifestSha256'] and inventory['runtimeSha256'] == approval['runtimeSha256'], 'Inventory pins differ')
    inventory_names = payload_names(inventory['models'])
    safe_extract(artifacts['payloadArtifact'], payload, inventory_names)
    verify_payload(payload, inventory, source, expected, repo)
    qa_root = work / 'qa'
    with zipfile.ZipFile(artifacts['qaArtifact']) as z:
        qa_names = [n for n in z.namelist() if n.count('/') == 0]
        need(set(qa_names) == {'qa.json', 'runtime.json'}, 'Unexpected internal QA top level')
        qa_root.mkdir(); (qa_root / 'qa.json').write_bytes(z.read('qa.json')); (qa_root / 'runtime.json').write_bytes(z.read('runtime.json'))
    internal = verify_qa(qa_root, approval, inventory)
    artifacts['qaArtifact'].unlink()
    # Re-observe run/artifact state after full local validation.
    for key in ('payloadArtifact', 'qaArtifact'):
        meta = api_json(f'/actions/artifacts/{approval[key]["id"]}', token); need(meta['digest'] == approval[key]['digest'] and not meta['expired'], 'Artifact changed during validation')
    tag = approval['tag']
    status, _, _ = request(f'{API}/git/ref/tags/{tag}', token); need(status == 404, 'Tag already exists; never overwrite')
    status, _, _ = request(f'{API}/releases/tags/{tag}', token); need(status == 404, 'Release already exists; never overwrite')
    # Source ZIPs remain in the independently checked review artifact. Consumer
    # publication contains only FBX, FBX+LICENSE ZIPs and the concise inventory.
    files = sorted(consumer_payload_names(inventory['models']))
    journal.write(step='create-draft', tag=tag, target=f)
    release = api_json('/releases', token, 'POST', {'tag_name': tag, 'target_commitish': f, 'name': f'Meshcopia cohort {name} — verified FBX and minimal ZIPs', 'body': body.decode('utf-8'), 'draft': True, 'prerelease': False, 'make_latest': 'false'}, (201,))
    need(release['draft'] is True and release['tag_name'] == tag, 'Draft release creation differs')
    journal.write(step='draft-created', releaseId=release['id'])
    uploaded = {}
    for name_ in files:
        p = payload / name_; data_size = p.stat().st_size
        time.sleep(1.0)  # GitHub guidance: at least one second between content-creating requests.
        journal.write(step='upload', file=name_, bytes=data_size)
        with p.open('rb') as fh:
            status, _, data = request(f'{UPLOADS}/releases/{release["id"]}/assets?name={urllib.parse.quote(name_)}', token, 'POST', fh.read(),
                                      'application/json' if name_.endswith('.json') else 'application/octet-stream', timeout=1800)
        need(status == 201, f'Upload failed ({status}) for {name_}; stop without retry')
        asset = json.loads(data); need(asset['name'] == name_ and asset['size'] == data_size and asset['state'] == 'uploaded', 'Uploaded asset differs: ' + name_)
        uploaded[name_] = asset
    # Verify every draft asset by authenticated readback before publishing.
    listed = []; page = 1
    while True:
        batch = api_json(f'/releases/{release["id"]}/assets?per_page=100&page={page}', token)
        listed += batch; page += 1
        if len(batch) < 100: break
    need(sorted(a['name'] for a in listed) == files, 'Draft asset set differs')
    want = {m[k]['filename']: m[k] for m in inventory['models'] for k in ('fbx', 'fbxArchive')}
    want['cohort-inventory.json'] = {'bytes': len(inventory_bytes), 'sha256': approval['inventorySha256']}
    for a in listed:
        t = work / ('draft-' + a['name']); download(f'{API}/releases/assets/{a["id"]}', token, t, want[a['name']]['sha256'], want[a['name']]['bytes']); t.unlink()
    journal.write(step='publish', releaseId=release['id'])
    published = api_json(f'/releases/{release["id"]}', token, 'PATCH', {'draft': False, 'make_latest': 'false'})
    need(published['draft'] is False and published['tag_name'] == tag, 'Publication differs')
    ref = api_json(f'/git/ref/tags/{tag}', token); need(ref['object']['type'] == 'commit' and ref['object']['sha'] == f, 'Tag must point directly to F')
    journal.write(step='published', releaseId=release['id'])
    assets = []
    for n in files:
        url = f'https://github.com/{REPO}/releases/download/{tag}/{urllib.parse.quote(n)}'
        t = work / ('public-' + n); b, h = download(url, None, t, want[n]['sha256'], want[n]['bytes']); t.unlink()
        assets.append({'name': n, 'bytes': b, 'sha256': h, 'assetId': uploaded[n]['id'], 'url': url, 'anonymousReadback': True})
    job = [j for j in api_json(f'/actions/runs/{os.environ["GITHUB_RUN_ID"]}/attempts/{os.environ["GITHUB_RUN_ATTEMPT"]}/jobs', token)['jobs'] if j['status'] == 'in_progress']
    need(len(job) == 1, 'Cannot identify the transport job')
    evidence = {'schemaVersion': 1, 'status': 'anonymous-byte-readback-passed', 'repository': REPO, 'cohort': name, 'tag': tag, 'fCommit': f,
                'releaseId': release['id'], 'releaseUrl': published['html_url'], 'attachmentCount': len(assets), 'inventorySha256': approval['inventorySha256'],
                'browserDownloadEvidence': 'not-performed-by-transport', 'assets': assets,
                'provenance': {k: approval[k] for k in ('fCommit', 'runId', 'runAttempt', 'jobId', 'payloadArtifact', 'qaArtifact', 'inventorySha256', 'sourceInventorySha256', 'expectedManifestSha256', 'runtimeSha256')},
                'internalQaVerification': internal,
                'transportExecution': {'commit': head, 'runId': int(os.environ['GITHUB_RUN_ID']), 'runAttempt': int(os.environ['GITHUB_RUN_ATTEMPT']), 'jobId': job[0]['id'],
                                       'workflowPath': R_PATHS[0], 'workflowSha256': file_sha(repo / R_PATHS[0]), 'approvalSha256': file_sha(repo / approval_path),
                                       'adapterSha256': {p: file_sha(repo / p) for p in ('scripts/cohort/transport.py', 'scripts/cohort/common.py')}}}
    out = work / 'evidence'; out.mkdir(); dump(out / 'T-evidence.json', evidence); shutil.copyfile(work / 'journal.jsonl', out / 'journal.jsonl')
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'github-actions[bot]', 'GIT_AUTHOR_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
           'GIT_COMMITTER_NAME': 'github-actions[bot]', 'GIT_COMMITTER_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com'}
    for cmd in (['git', 'init', '-q'], ['git', 'add', 'T-evidence.json', 'journal.jsonl'], ['git', 'commit', '-q', '-m', f'evidence: cohort {name} transport']):
        subprocess.run(cmd, cwd=out, env=env, check=True, capture_output=True)
    auth = base64.b64encode(('x-access-token:' + token).encode()).decode(); print('::add-mask::' + auth)
    target = f'refs/heads/evidence/cohort-{name}-transport-{os.environ["GITHUB_RUN_ID"]}-{os.environ["GITHUB_RUN_ATTEMPT"]}'
    subprocess.run(['git', '-c', 'http.https://github.com/.extraheader=AUTHORIZATION: basic ' + auth, 'push', 'https://github.com/' + REPO, 'HEAD:' + target], cwd=out, env=env, check=True, capture_output=True)
    print(json.dumps({'tag': tag, 'releaseId': release['id'], 'attachments': len(assets), 'evidenceBranch': target, 'tEvidenceSha256': file_sha(out / 'T-evidence.json')}))


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('COHORT_TRANSPORT_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
