"""Transport exact successful minimal-FBX artifacts; never convert, overwrite or retry."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import qa
f = qa.f
need = f.need
sha = f.sha
canonical = f.canonical
read = f.read
file_sha = qa.file_sha
REPO = f.REPO
TAG = 'fbx-minimal-v1.0.0'
BRANCH = 'fbx/release-minimal137-v1'
VERIFY_BRANCH = 'fbx/verify-minimal137-v1'
WORKFLOW = f.WORKFLOW
RELEASE_NAME = 'Minimal FBX downloads 1.0.0 — original 137 models'
API = 'https://api.github.com/repos/' + REPO
MAX_FILE = 95 * 1024**2
MAX_TOTAL = 3 * 1024**3
PROVENANCE_FIELDS = ('fCommit', 'runId', 'runAttempt', 'jobId', 'workflowPath', 'workflowSha256', 'payloadArtifactId', 'payloadArtifactName', 'payloadArtifactSha256', 'qaArtifactId', 'qaArtifactName', 'qaArtifactSha256', 'inventorySha256', 'qaSummarySha256', 'qaRuntimeSha256', 'qaPilotGateSha256', 'sourceInventorySha256', 'expectedManifestSha256', 'runtimeSha256')


def approval_check(a, source_bytes, expected_bytes, runtime_bytes):
    f.exact(a, 'schemaVersion reviewStatus repository tag releaseBodySha256 approvedIds ' + ' '.join(PROVENANCE_FIELDS), 'transport approval')
    need(a['schemaVersion'] == 1 and a['reviewStatus'] == 'approved-for-transport', 'Transport approval missing')
    need(a['repository'] == REPO and a['tag'] == TAG and a['workflowPath'] == WORKFLOW, 'Wrong repository/tag/workflow')
    f.commit(a['fCommit'])
    for key in PROVENANCE_FIELDS + ('releaseBodySha256',):
        if key.endswith('Sha256'): f.digest(a[key])
    for key in ('runId', 'runAttempt', 'jobId', 'payloadArtifactId', 'qaArtifactId'): need(type(a[key]) is int and a[key] > 0, 'Invalid run/job/artifact identity')
    need(a['payloadArtifactId'] != a['qaArtifactId'], 'Payload and internal QA must be different artifacts')
    for prefix, name in (('payload', 'fbx-minimal137'), ('qa', 'fbx-minimal-internal-qa')):
        need(a[prefix + 'ArtifactName'] == f"{name}-{a['fCommit']}-{a['runId']}-{a['runAttempt']}", 'Wrong artifact name')
    need(sha(source_bytes) == a['sourceInventorySha256'] and sha(expected_bytes) == a['expectedManifestSha256'] and sha(runtime_bytes) == a['runtimeSha256'], 'Manifest/runtime digest mismatch')
    source, expected, runtime = map(qa.json_bytes, (source_bytes, expected_bytes, runtime_bytes))
    f.check_manifests(source, expected, source_bytes)
    need(expected['runtimeSha256'] == a['runtimeSha256'] and [r['id'] for r in source['models']] == a['approvedIds'], 'Wrong runtime/cohort approval')
    return source, expected, runtime


def check_run(a, run):
    need(run['id'] == a['runId'] and run['run_attempt'] == a['runAttempt'], 'Run identity differs')
    need(run['repository']['full_name'] == run['head_repository']['full_name'] == REPO, 'Run repository differs')
    need(run['head_sha'] == a['fCommit'] and run['head_branch'] == VERIFY_BRANCH and run['event'] == 'push', 'Run source differs')
    need(run['path'] == WORKFLOW and run['status'] == 'completed' and run['conclusion'] == 'success', 'Whole F run is not successful')


def check_job(a, job):
    need(job['id'] == a['jobId'] and job['run_id'] == a['runId'] and job['run_attempt'] == a['runAttempt'] and job['head_sha'] == a['fCommit'], 'Job identity differs')
    need(job['name'] == 'verify' and job['status'] == 'completed' and job['conclusion'] == 'success', 'F verification job not successful')
    required = {'Gate baseline, exact additive paths and reviewed minimal inputs before Blender', 'Fresh conversion, independent QA and strict two-entry packaging in pinned runtime', 'Store exact public payload review artifact, never publish', 'Store internal QA separately, never in consumer ZIPs or a release', 'Record exact payload and QA artifact envelopes'}
    steps = {s['name']: s for s in job['steps']}
    need(len(steps) == len(job['steps']) and required <= set(steps) and all(steps[name]['status'] == 'completed' and steps[name]['conclusion'] == 'success' for name in required), 'Required F proof/upload step missing or unsuccessful')


def check_artifact(a, run, artifact, prefix):
    need(prefix in ('payload', 'qa'), 'Unknown artifact kind')
    need(artifact['id'] == a[prefix + 'ArtifactId'] and artifact['name'] == a[prefix + 'ArtifactName'] and artifact['expired'] is False, 'Artifact identity/expiry differs')
    need(artifact['digest'] == 'sha256:' + a[prefix + 'ArtifactSha256'], 'Artifact API digest differs')
    owner = artifact['workflow_run']
    need(owner['id'] == a['runId'] and owner['head_sha'] == a['fCommit'] and owner['head_branch'] == VERIFY_BRANCH and owner['repository_id'] == run['repository']['id'] and owner['head_repository_id'] == run['head_repository']['id'], 'Artifact ownership differs')


def check_source(repo, a, source, expected, runtime):
    ftree = f.tree(repo, a['fCommit'])
    for path in f.fixed_paths():
        need(ftree[path][:2] == ('100644', 'blob') and file_sha(repo / path) == sha(f.git(repo, 'show', a['fCommit'] + ':' + path)), 'Verification overlay worktree differs from exact F')
    for name, key in ((WORKFLOW, 'workflowSha256'), ('docs/fbx-minimal-verification/source137.json', 'sourceInventorySha256'), ('docs/fbx-minimal-verification/expected137.json', 'expectedManifestSha256'), ('docs/fbx-minimal-verification/runtime.json', 'runtimeSha256')):
        need(sha(f.git(repo, 'show', a['fCommit'] + ':' + name)) == a[key] and file_sha(repo / name) == a[key], 'F source/code worktree differs: ' + name)
    need(runtime['pipelineSha256'] == f.PIPELINE and sha(json.dumps(runtime['recipe'], sort_keys=True, separators=(',', ':')).encode()) == f.PIPELINE, 'Frozen conversion recipe differs')
    pins = {**runtime['supportFiles'], **{'scripts/fbx-verification/' + k: v for k, v in runtime['recipe'].items()}}
    for path, checksum in pins.items():
        need(file_sha(repo / path) == checksum and sha(f.git(repo, 'show', a['fCommit'] + ':' + path)) == checksum, 'Pinned F helper/recipe differs')
    for row in source['models']:
        for path, checksum in ((row['sourceGLB'], row['sourceSha256']), (row['assetMetadata'], row['metadataSha256'])):
            need(file_sha(f.packages.rooted_file(repo, path)) == checksum and sha(f.git(repo, 'show', f.BASE + ':' + path)) == checksum, 'Original source/metadata differs')


def expected_inventory(a, source, expected):
    return {'schemaVersion': 1, 'contract': 'meshcopia-fbx-minimal-artifact/1', 'repository': REPO, 'fCommit': a['fCommit'], 'sourceCommit': f.BASE, 'workflow': WORKFLOW, 'runId': str(a['runId']), 'runAttempt': str(a['runAttempt']), 'cohort': 'published137', 'packageVersion': '1.0.0', 'pipelineSha256': f.PIPELINE, 'sourceInventorySha256': a['sourceInventorySha256'], 'expectedManifestSha256': a['expectedManifestSha256'], 'runtimeSha256': a['runtimeSha256'], 'models': [f.model_binding(row, exp) for row, exp in zip(source['models'], expected['models'])]}


def unpack_payload(a, source, expected, archive, qa_archive, out, repo, materialize=True):
    need(file_sha(archive) == a['payloadArtifactSha256'] and file_sha(qa_archive) == a['qaArtifactSha256'], 'Payload/QA artifact digest differs')
    entries = {item['filename']: {'name': item['filename'], 'bytes': item['bytes'], 'sha256': item['sha256']} for row, exp in zip(source['models'], expected['models']) for item in (f.model_binding(row, exp)['fbx'], f.model_binding(row, exp)['archive'])}
    allowed = set(entries) | {'fbx-minimal-inventory.json'}
    need(len(allowed) == 275, 'Unexpected/duplicate model attachment names')
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(qa_archive) as internal, tempfile.TemporaryDirectory(prefix='fbx-minimal-payload-') as directory:
        infos = z.infolist(); names = [i.filename for i in infos]
        need(len(infos) == 275 and set(names) == allowed and len(set(n.casefold() for n in names)) == len(names), 'Payload artifact path set differs')
        need(sum(i.file_size for i in infos) <= MAX_TOTAL, 'Payload artifact too large')
        for info in infos:
            f.packages.safe_relative(info.filename)
            need(info.orig_filename == info.filename and not info.is_dir() and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG) and info.compress_type in (0, 8) and not info.flag_bits & 1 and 0 < info.file_size <= MAX_FILE, 'Unsafe payload artifact entry')
        info = z.getinfo('fbx-minimal-inventory.json'); need(info.file_size <= 2 * 1024**2, 'Inventory too large')
        raw = z.read(info); need(sha(raw) == a['inventorySha256'] and raw == canonical(expected_inventory(a, source, expected)), 'Inventory binding differs')
        entries['fbx-minimal-inventory.json'] = {'name': 'fbx-minimal-inventory.json', 'bytes': len(raw), 'sha256': sha(raw)}
        out.mkdir(exist_ok=False); work = Path(directory)
        if materialize: (out / 'fbx-minimal-inventory.json').write_bytes(raw)
        for row, exp in zip(source['models'], expected['models']):
            identity = row['id']; raw_path = (out if materialize else work) / (identity + '.fbx'); zip_path = (out if materialize else work) / exp['filename']
            for path in (raw_path, zip_path):
                item = entries[path.name]; qa.stream_member(z, z.getinfo(path.name), path, item['bytes'], item['sha256'])
            report_name = identity + '/fresh/roundtrip-report.json'; report_info = internal.getinfo(report_name)
            need(0 < report_info.file_size <= qa.MAX_JSON, 'Report too large')
            report = work / 'report.json'; qa.stream_member(internal, report_info, report)
            note = work / 'LICENSE.txt'; note.write_bytes(row['notice']['text'].encode())
            plan = f.packages.make_plan(repo / 'content/assets' / identity, note, fbx_path=raw_path, fbx_sha256=exp['fbxSha256'], pipeline_sha256=f.PIPELINE, fbx_report=report)
            need(len(plan['entries']) == 2 and {x['name'] for x in plan['entries']} == {'LICENSE.txt', identity + '.fbx'}, 'Not a two-entry minimal FBX plan')
            f.packages.verify_archive(zip_path, plan)
            report.unlink(); note.unlink()
            if not materialize: raw_path.unlink(); zip_path.unlink()
    return sorted(entries.values(), key=lambda r: r['name'])


def check_repository(repo):
    need(f.git(repo, 'rev-parse', '--is-shallow-repository').strip() == b'false', 'Shallow checkout prohibited')
    for args in (('config', '--get', 'extensions.partialClone'), ('config', '--get-regexp', r'^remote\..*\.promisor$')):
        try: f.git(repo, *args)
        except f.subprocess.CalledProcessError as error: need(error.returncode == 1, 'Configuration read failed')
        else: raise ValueError('Partial/promisor repository prohibited')
    graft = Path(f.git(repo, 'rev-parse', '--git-path', 'info/grafts').decode().strip())
    if not graft.is_absolute(): graft = repo / graft
    need(not graft.exists() or not graft.read_text().strip(), 'Grafted history prohibited')
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
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-fbx-minimal-transport'}
        data = canonical(value) if value is not None else raw
        if data is not None: headers['Content-Type'] = 'application/json' if value is not None else 'application/octet-stream'
        return self.opener.open(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=180)

    def upload(self, url, path):
        need(url.startswith(f'https://uploads.github.com/repos/{REPO}/releases/'), 'Invalid upload target')
        handle = path.open('rb')
        request = urllib.request.Request(url, data=handle, headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-fbx-minimal-transport', 'Content-Type': 'application/octet-stream', 'Content-Length': str(path.stat().st_size)}, method='POST')
        try:
            response = self.opener.open(request, timeout=180)
        finally:
            handle.close()
        return response

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
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/octet-stream', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-fbx-minimal-transport'})
    try: response = self.opener.open(request, timeout=180)
    except urllib.error.HTTPError as error:
        need(error.code == 302, 'Asset byte download failed')
        location = error.headers['Location']; need(urllib.parse.urlsplit(location).scheme == 'https', 'Insecure asset redirect')
        response = urllib.request.urlopen(location, timeout=180)
    stream_file(response, target, limit)


GitHub.download_asset = download_asset


def publish(api, body, entries, work, approval):
    f = approval['fCommit']
    log = work / 'journal.jsonl'
    absence(api); journal(log, 'create-draft-requested', fCommit=f, tag=TAG)
    release = api.json('/releases', 'POST', {'tag_name': TAG, 'target_commitish': f, 'name': RELEASE_NAME, 'body': body.decode(), 'draft': True, 'prerelease': False, 'generate_release_notes': False})
    need(release['draft'] is True and release['tag_name'] == TAG and release['target_commitish'] == f, 'Created draft differs')
    journal(log, 'draft-created', releaseId=release['id'])
    for entry in entries:
        journal(log, 'upload-requested', name=entry['name'])
        url = f'https://uploads.github.com/repos/{REPO}/releases/{release["id"]}/assets?name=' + urllib.parse.quote(entry['name'])
        with api.upload(url, work / 'payload' / entry['name']) as response: uploaded = json.load(response)
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
    evidence = {'schemaVersion': 1, 'status': 'anonymous-byte-readback-passed', 'repository': REPO, 'tag': TAG, 'fCommit': f, 'releaseId': release['id'], 'releaseUrl': published['html_url'], 'attachmentCount': len(proof), 'inventorySha256': file_sha(work / 'payload/fbx-minimal-inventory.json'), 'browserDownloadEvidence': 'not-performed-by-transport', 'assets': proof}
    evidence['provenance'] = {key: approval[key] for key in PROVENANCE_FIELDS}
    evidence['internalQaVerification'] = approval['_verifiedQa']
    evidence['transportExecution'] = approval['_transportExecution']
    (work / 'T-evidence.json').write_bytes(canonical(evidence)); journal(log, 'anonymous-readback-passed', releaseId=release['id'])
    print('Published exact 137 raw FBXs, 137 minimal ZIPs and one inventory. All 275 anonymous readbacks passed. QA stays internal.')



def observe(a, api):
    run = api.json('/actions/runs/' + str(a['runId'])); check_run(a, run)
    check_job(a, api.json('/actions/jobs/' + str(a['jobId'])))
    for prefix in ('payload', 'qa'): check_artifact(a, run, api.json('/actions/artifacts/' + str(a[prefix + 'ArtifactId'])), prefix)


def execution_record(repo, api):
    """Bind this currently running R; later P independently requires its success."""
    commit = os.environ['GITHUB_SHA']; f.commit(commit)
    ids = {}
    for name, key in (('GITHUB_RUN_ID', 'runId'), ('GITHUB_RUN_ATTEMPT', 'runAttempt')):
        value = os.environ[name]
        need(re.fullmatch(r'[1-9][0-9]*', value) is not None, 'Invalid R execution ID')
        ids[key] = int(value)
    workflow = '.github/workflows/release-fbx-minimal.yml'
    path = f"/actions/runs/{ids['runId']}/attempts/{ids['runAttempt']}"
    run = api.json(path)
    need(type(run['id']) is int and type(run['run_attempt']) is int and run['id'] == ids['runId'] and run['run_attempt'] == ids['runAttempt'], 'R run identity differs')
    need(run['repository']['full_name'] == run['head_repository']['full_name'] == REPO and run['head_sha'] == commit and run['head_branch'] == BRANCH and run['path'] == workflow and run['event'] == 'push', 'R run source differs')
    need(run['status'] == 'in_progress' and run['conclusion'] is None, 'R run not currently executing')
    jobs = api.json(path + '/jobs?per_page=100')
    need(type(jobs['total_count']) is int and jobs['total_count'] == 1 and type(jobs['jobs']) is list and len(jobs['jobs']) == 1, 'R must have exactly one job')
    job = jobs['jobs'][0]
    need(type(job['id']) is int and job['id'] > 0 and type(job['run_id']) is int and type(job['run_attempt']) is int and job['run_id'] == ids['runId'] and job['run_attempt'] == ids['runAttempt'] and job['head_sha'] == commit and job['name'] == 'transport', 'R job identity differs')
    need(job['status'] == 'in_progress' and job['conclusion'] is None, 'R job not currently executing')
    return {'commit': commit, **ids, 'jobId': job['id'], 'workflowPath': workflow, 'workflowSha256': file_sha(repo / workflow), 'approvalSha256': file_sha(repo / 'docs/fbx-minimal-transport/approval.json'), 'adapterSha256': {name: file_sha(repo / name) for name in ('scripts/fbx-minimal-transport/transport.py', 'scripts/fbx-minimal-transport/qa.py')}}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--repo', type=Path, required=True); parser.add_argument('--work', type=Path, required=True); args = parser.parse_args()
    repo = args.repo.resolve(); docs = repo / 'docs/fbx-minimal-verification'; approval = read(repo / 'docs/fbx-minimal-transport/approval.json')
    source, expected, runtime = approval_check(approval, (docs / 'source137.json').read_bytes(), (docs / 'expected137.json').read_bytes(), (docs / 'runtime.json').read_bytes())
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong release execution context')
    check_repository(repo); head = os.environ['GITHUB_SHA']; fc = approval['fCommit']
    need(f.git(repo, 'rev-parse', 'HEAD').decode().strip() == head and f.git(repo, 'show', '-s', '--format=%P', head).decode().strip() == fc, 'R must directly follow exact approved F without merge')
    allowed = {'.github/workflows/release-fbx-minimal.yml'} | {'scripts/fbx-minimal-transport/' + n for n in ('transport.py', 'qa.py', 'prepare_approval.py', 'test_transport.py', 'test_qa.py')} | {'docs/fbx-minimal-transport/' + n for n in ('README.md', 'RELEASE_BODY.md', 'approval.json')}
    changes = f.git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', fc, head).decode().split('\0')[:-1]
    need(len(changes) == len(allowed) * 2 and all(s == 'A' for s in changes[::2]) and set(changes[1::2]) == allowed, 'R changed paths differ')
    current = f.tree(repo, head); need(all(current[path][:2] == ('100644', 'blob') for path in allowed), 'Unsafe R tree entry')
    need(f.git(repo, 'status', '--porcelain', '--untracked-files=no') == b'', 'Dirty tracked checkout')
    check_source(repo, approval, source, expected, runtime)
    body = (repo / 'docs/fbx-minimal-transport/RELEASE_BODY.md').read_bytes(); need(sha(body) == approval['releaseBodySha256'], 'Release body differs')
    work = args.work; work.mkdir(exist_ok=False, parents=True); api = GitHub(os.environ['GH_TOKEN']); observe(approval, api)
    payload = work / 'payload-artifact.zip'; internal = work / 'internal-qa-artifact.zip'
    api.download('/actions/artifacts/' + str(approval['payloadArtifactId']) + '/zip', payload, MAX_TOTAL)
    api.download('/actions/artifacts/' + str(approval['qaArtifactId']) + '/zip', internal, qa.MAX_QA_TOTAL)
    entries = unpack_payload(approval, source, expected, payload, internal, work / 'payload', repo)
    proof = qa.verify_internal_qa(internal, approval, source, expected, runtime, repo, fbx_directory=work / 'payload')
    observe(approval, api)
    execution = execution_record(repo, api)
    publish(api, body, entries, work, {**approval, '_verifiedQa': proof, '_transportExecution': execution})


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('FBX_MINIMAL_TRANSPORT_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__))
        raise SystemExit(1)
