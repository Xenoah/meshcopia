#!/usr/bin/env python3
"""Anonymous, same-job site preparation for separately verified model cohorts.

The frozen original137/173 adapters remain unchanged. Each cohort must match
its exact successful F and R runs, immutable manifests and transport readback.
All public payloads are downloaded and hashed again; FBX ZIP members and original
source ZIPs are checked independently. No Release writes, credentials or offline
receipt bypass are supported here.
"""
import argparse
import importlib.util
import os
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'cohort'))
from common import *

CONFIG = 'docs/cohort-activation.json'
RECEIPT = '.cache/cohort-verified.json'
API = 'https://api.github.com/repos/' + REPO
INPUT_NAMES = ['source.json', 'expected.json', 'approval.json', 'T-evidence.json', 'cohort-inventory.json']
CORE_INPUTS = [CONFIG, 'scripts/prepare-cohort-activation.py', 'scripts/cohort/common.py',
               'scripts/lib/cohort-downloads.mjs', 'scripts/lib/cohort-policy.mjs',
               'scripts/verify-minimal-activation.py', 'src/lib/fbx-minimal-downloads.mjs',
               'src/lib/delivery.mjs', RUNTIME]


def local(repo, name):
    packages.safe_relative(name)
    p = repo
    for part in name.split('/'):
        p /= part
        need(not p.is_symlink(), 'Symlink in cohort input: ' + name)
    need(p.is_file(), 'Missing regular cohort input: ' + name)
    return p


def validate_config(doc):
    exact(doc, 'schemaVersion repository cohorts', 'cohort activation')
    need(doc['schemaVersion'] == 1 and doc['repository'] == REPO and isinstance(doc['cohorts'], list), 'Invalid activation identity')
    names = set()
    for c in doc['cohorts']:
        exact(c, 'name modelCount releaseTag releaseId verificationCommit transportCommit evidenceCommit publicPayloads inputs', 'cohort activation row')
        need(isinstance(c['name'], str) and NAME.fullmatch(c['name']) and c['name'] not in names, 'Invalid/duplicate cohort')
        names.add(c['name'])
        need(type(c['modelCount']) is int and 0 < c['modelCount'] <= 300, 'Invalid cohort count')
        need(c['releaseTag'] == f'cohort-{c["name"]}-v1.0.0' and type(c['releaseId']) is int and c['releaseId'] > 0, 'Invalid cohort Release')
        for k in ('verificationCommit', 'transportCommit', 'evidenceCommit'): commit(c[k])
        need(c['publicPayloads'] in (['fbx', 'fbxArchive'], ['fbx', 'fbxArchive', 'archive']), 'Invalid public payload contract')
        need(set(c['inputs']) == set(INPUT_NAMES), 'Incomplete cohort proof inputs')
        for h in c['inputs'].values(): digest(h)
    return doc


def verify_run(run, *, sha_, name, run_id, attempt, workflow, branch):
    need(run.get('id') == run_id and run.get('run_attempt') == attempt and run.get('head_sha') == sha_, 'Run identity differs: ' + name)
    need(run.get('repository', {}).get('full_name') == run.get('head_repository', {}).get('full_name') == REPO, 'Run repository differs')
    need(run.get('path') == workflow and run.get('head_branch') == branch and run.get('event') == 'push', 'Run trigger differs: ' + name)
    need(run.get('status') == 'completed' and run.get('conclusion') == 'success', 'Run not successful: ' + name)


def verify_job(job, run, job_id, name, required):
    need(job.get('id') == job_id and job.get('run_id') == run['id'] and job.get('run_attempt') == run['run_attempt'] and job.get('head_sha') == run['head_sha'], 'Job identity differs')
    need(job.get('name') == name and job.get('status') == 'completed' and job.get('conclusion') == 'success', 'Job not successful')
    steps = {s['name']: s for s in job['steps']}
    need(len(steps) == len(job['steps']) and all(s['conclusion'] in ('success', 'skipped') for s in job['steps']), 'Job contains failed/duplicate steps')
    for label in required: need(steps.get(label, {}).get('conclusion') == 'success', 'Required verification step missing: ' + label)


def verify_zip(path, members):
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        need(len(infos) == len(members) and {i.filename for i in infos} == set(members), 'ZIP members differ: ' + path.name)
        for i in infos:
            need(i.orig_filename == i.filename and not i.is_dir() and not i.flag_bits & 1 and i.compress_type in (0, 8)
                 and stat.S_IFMT(i.external_attr >> 16) in (0, stat.S_IFREG), 'Unsafe ZIP member')
            row = members[i.filename]
            need(i.file_size == row['bytes'], 'ZIP member size differs')
            data = archive.read(i)
            need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'ZIP member hash differs')
            if i.filename == 'LICENSE.txt': need(data == row['text'].encode('utf-8'), 'ZIP notice differs')


def verify_pins(repo, c):
    prefix = 'docs/cohorts/' + c['name'] + '/'
    raw = {n: local(repo, prefix + n).read_bytes() for n in INPUT_NAMES}
    for n, b in raw.items(): need(sha(b) == c['inputs'][n], 'Pinned cohort input changed: ' + n)
    source, expected, approval, evidence, inventory = [json.loads(raw[n]) for n in INPUT_NAMES]
    check_source(source); need(source['cohort'] == c['name'] and source['modelCount'] == c['modelCount'], 'Cohort identity/count differs')
    f, r = c['verificationCommit'], c['transportCommit']
    for n in ('source.json', 'expected.json'): need(raw[n] == git(repo, 'show', f + ':' + prefix + n), 'F manifest differs')
    need(raw['approval.json'] == git(repo, 'show', r + ':' + prefix + 'approval.json'), 'R approval differs')
    need(raw['T-evidence.json'] == git(repo, 'show', c['evidenceCommit'] + ':T-evidence.json'), 'T evidence commit differs')
    runtime_bytes = local(repo, RUNTIME).read_bytes()
    need(runtime_bytes == git(repo, 'show', f + ':' + RUNTIME), 'Cohort runtime differs')
    runtime = json.loads(runtime_bytes)
    exp = check_expected(expected, source, raw['source.json'], sha(runtime_bytes)); need(exp is not None, 'Discovery output cannot be activated')
    p, execution = evidence['provenance'], evidence['transportExecution']
    need(evidence['status'] == 'anonymous-byte-readback-passed' and evidence['repository'] == REPO and evidence['cohort'] == c['name'], 'T identity differs')
    need(evidence['tag'] == approval['tag'] == c['releaseTag'] and evidence['releaseId'] == c['releaseId'] and evidence['fCommit'] == f, 'T release identity differs')
    need(evidence['browserDownloadEvidence'] == 'not-performed-by-transport', 'Unexpected browser claim')
    need(approval['reviewStatus'] == 'approved-for-transport' and approval['repository'] == REPO and approval['cohort'] == c['name'], 'R approval identity differs')
    need(all(approval[k] == v for k, v in p.items()), 'T provenance differs from approved F')
    need(p['fCommit'] == f and p['sourceInventorySha256'] == sha(raw['source.json']) and p['expectedManifestSha256'] == sha(raw['expected.json'])
         and p['runtimeSha256'] == sha(runtime_bytes) and p['inventorySha256'] == sha(raw['cohort-inventory.json']) == evidence['inventorySha256'], 'T manifest pins differ')
    for k in ('runId', 'runAttempt', 'jobId'): need(type(p[k]) is int and p[k] > 0 and type(execution[k]) is int and execution[k] > 0, 'Invalid execution ID')
    need(execution['commit'] == r and execution['workflowPath'] == '.github/workflows/release-cohort.yml', 'R execution differs')
    need(execution['approvalSha256'] == sha(raw['approval.json']), 'R approval hash differs')
    need(set(execution['adapterSha256']) == {'scripts/cohort/common.py', 'scripts/cohort/transport.py'}, 'Unexpected R adapters')
    for name, checksum in {execution['workflowPath']: execution['workflowSha256'], **execution['adapterSha256']}.items():
        need(sha(git(repo, 'show', r + ':' + name)) == checksum, 'Executed R input differs')
    need(local(repo, 'scripts/cohort/common.py').read_bytes() == git(repo, 'show', f + ':scripts/cohort/common.py'), 'Cohort pure verifier differs from F')
    need(sha(local(repo, 'scripts/cohort/common.py').read_bytes()) == execution['adapterSha256']['scripts/cohort/common.py'], 'R pure verifier differs')
    need(git(repo, 'show', '-s', '--format=%P', r).decode().split() == [f], 'R is not directly based on exact F')
    body = git(repo, 'show', r + ':' + prefix + 'RELEASE_BODY.md'); need(sha(body) == approval['releaseBodySha256'], 'Release body pin differs')
    qa = evidence['internalQaVerification']
    need(set(qa) == {'status', 'models', 'qaSha256', 'blenderRerunByTransport'} and qa['status'] == 'exact-internal-qa-rechecked'
         and qa['models'] == c['modelCount'] and qa['blenderRerunByTransport'] is False, 'Clean-import QA attestation differs')
    digest(qa['qaSha256'])
    for kind in ('payloadArtifact', 'qaArtifact'):
        a = p[kind]; exact(a, 'id name digest', 'QA artifact identity')
        need(type(a['id']) is int and a['id'] > 0 and re.fullmatch('sha256:[0-9a-f]{64}', a['digest']), 'Invalid QA artifact identity')
        tag = 'cohort-' if kind == 'payloadArtifact' else 'cohort-internal-qa-'
        need(a['name'] == f'{tag}{c["name"]}-{f}-{p["runId"]}-{p["runAttempt"]}', 'QA artifact name differs')
    need(p['payloadArtifact']['id'] != p['qaArtifact']['id'], 'QA must be separate')
    desired = {'schemaVersion': 1, 'contract': 'meshcopia-cohort-artifact/1', 'repository': REPO, 'cohort': c['name'], 'fCommit': f,
               'baseCommit': source['baseCommit'], 'workflow': '.github/workflows/verify-cohort.yml', 'runId': str(p['runId']), 'runAttempt': str(p['runAttempt']),
               'reviewStatus': 'reproduced-final', 'packageVersion': PACKAGE_VERSION, 'pipelineSha256': PIPELINE,
               'sourceInventorySha256': sha(raw['source.json']), 'expectedManifestSha256': sha(raw['expected.json']), 'runtimeSha256': sha(runtime_bytes),
               'models': [model_binding(row, {k: exp[row['id']][k] for k in ('fbx', 'fbxArchive', 'archive')}) for row in source['models']]}
    need(raw['cohort-inventory.json'] == canonical(desired), 'Inventory differs from reviewed manifests')
    pins = {**runtime['supportFiles'], **{'scripts/fbx-verification/' + k: v for k, v in runtime['recipe'].items()}}
    for name, checksum in pins.items(): need(file_sha(local(repo, name)) == checksum == sha(git(repo, 'show', f + ':' + name)), 'Recipe/support input changed')
    return source, inventory, evidence, pins


def verify_remote(reader, c, inventory, evidence, inventory_bytes):
    p, execution = evidence['provenance'], evidence['transportExecution']
    for name, proof, commit_, branch, workflow, job_name, required in [
        ('F', p, c['verificationCommit'], 'cohort/verify-' + c['name'], '.github/workflows/verify-cohort.yml', 'verify',
         ['Fresh conversion, independent QA and strict minimal packaging in the pinned runtime', 'Store internal QA separately, never in consumer ZIPs or a release']),
        ('R', execution, c['transportCommit'], 'cohort/release-' + c['name'], '.github/workflows/release-cohort.yml', 'transport',
         ['Transport exact reviewed bytes and verify anonymous public readbacks', 'Preserve the consequential-step journal'])]:
        run = reader.json(API + f'/actions/runs/{proof["runId"]}/attempts/{proof["runAttempt"]}')
        verify_run(run, sha_=commit_, name=name, run_id=proof['runId'], attempt=proof['runAttempt'], workflow=workflow, branch=branch)
        verify_job(reader.json(API + f'/actions/jobs/{proof["jobId"]}'), run, proof['jobId'], job_name, required)
    release = reader.json(API + f'/releases/{c["releaseId"]}')
    need(release['id'] == c['releaseId'] and release['tag_name'] == c['releaseTag'] and release['draft'] is False and release['prerelease'] is False, 'Release is not public')
    need(release['html_url'] == evidence['releaseUrl'] == f'https://github.com/{REPO}/releases/tag/{c["releaseTag"]}', 'Release URL differs')
    ref = reader.json(API + '/git/ref/tags/' + c['releaseTag'])
    need(ref['object']['type'] == 'commit' and ref['object']['sha'] == c['verificationCommit'], 'Immutable tag differs')
    root = f'https://github.com/{REPO}/releases/download/{c["releaseTag"]}/'
    need(reader.bytes(root + 'cohort-inventory.json') == inventory_bytes, 'Anonymous inventory differs')
    expected = {m[k]['filename']: m[k] for m in inventory['models'] for k in c['publicPayloads']}
    expected['cohort-inventory.json'] = {'filename': 'cohort-inventory.json', 'bytes': len(inventory_bytes), 'sha256': sha(inventory_bytes)}
    assets = []
    for page in range(1, 12):
        batch = reader.json(API + f'/releases/{c["releaseId"]}/assets?per_page=100&page={page}'); need(type(batch) is list, 'Invalid asset list')
        assets += batch
        if len(batch) < 100: break
    else: raise ValueError('Release attachment pagination exceeded')
    remote = {a['name']: a for a in assets}; saved = {a['name']: a for a in evidence['assets']}
    need(len(assets) == len(remote) == len(evidence['assets']) == len(saved) == len(expected) == evidence['attachmentCount']
         and set(remote) == set(saved) == set(expected), 'Attachment inventory differs')
    for name, x in expected.items():
        a, t = remote[name], saved[name]
        need(a['state'] == 'uploaded' and a['size'] == x['bytes'] and a['digest'] == 'sha256:' + x['sha256'] and a['browser_download_url'] == root + name, 'Remote payload metadata differs')
        need(t == {'anonymousReadback': True, 'assetId': a['id'], 'bytes': x['bytes'], 'name': name, 'sha256': x['sha256'], 'url': root + name}, 'T attachment binding differs')
    return root


def prepare(repo):
    clean_checkout(repo)
    cache = repo / '.cache'; cache.mkdir(exist_ok=True); need(not cache.is_symlink(), 'Unsafe cache')
    receipt_path = repo / RECEIPT
    if receipt_path.exists(): need(receipt_path.is_file() and not receipt_path.is_symlink(), 'Unsafe stale receipt'); receipt_path.unlink()
    config_bytes = local(repo, CONFIG).read_bytes(); config = validate_config(json.loads(config_bytes))
    head = git(repo, 'rev-parse', 'HEAD').decode().strip()
    # Retained activations cannot be removed or rewritten by a later build.
    for revision in git(repo, 'log', '--full-history', '--format=%H', '--', CONFIG).decode().splitlines():
        if not git(repo, 'ls-tree', revision, '--', CONFIG).strip(): continue
        old = validate_config(json.loads(git(repo, 'show', revision + ':' + CONFIG)))
        need(all(c in config['cohorts'] for c in old['cohorts']), 'Immutable cohort activation removed or changed')
    spec = importlib.util.spec_from_file_location('cohort_anonymous_reader', repo / 'scripts/verify-minimal-activation.py')
    ordinary = importlib.util.module_from_spec(spec); spec.loader.exec_module(ordinary); reader = ordinary.PublicReader()
    prepared = [(c, verify_pins(repo, c)) for c in config['cohorts']]
    inputs = set(CORE_INPUTS)
    for c, (source, _, _, pins) in prepared:
        inputs.update(pins); inputs.update('docs/cohorts/' + c['name'] + '/' + n for n in INPUT_NAMES)
        for row in source['models']:
            meta = json.loads(local(repo, row['assetMetadata']).read_bytes())
            inputs.add(f'content/assets/{row["id"]}/' + meta['thumbnail'])
    input_hashes = [{'path': name, 'sha256': file_sha(local(repo, name))} for name in sorted(inputs)]
    projection, bindings, provenance, ids = [], [], [], set()
    payloads = cache / 'fbx-delivery-payloads'; payloads.mkdir(exist_ok=True); need(not payloads.is_symlink(), 'Unsafe payload cache')
    with tempfile.TemporaryDirectory(prefix='cohort-prep-') as folder:
        work = Path(folder)
        for c, (source, inventory, evidence, _) in prepared:
            root = verify_remote(reader, c, inventory, evidence, local(repo, 'docs/cohorts/' + c['name'] + '/cohort-inventory.json').read_bytes())
            provenance.append({'name': c['name'], 'releaseId': c['releaseId'], 'fCommit': c['verificationCommit'], 'transportExecution': evidence['transportExecution']})
            for row, published in zip(source['models'], inventory['models']):
                identity = row['id']; need(identity not in ids, 'Duplicate active cohort ID'); ids.add(identity)
                metadata = local(repo, row['assetMetadata']).read_bytes()
                need(sha(metadata) == row['metadataSha256'] and metadata == git(repo, 'show', c['verificationCommit'] + ':' + row['assetMetadata']), 'Current model metadata differs')
                meta = json.loads(metadata); need(meta['status'] == 'public' and meta['type'] == 'model', 'Model is not public')
                thumbnail_path = f'content/assets/{identity}/' + meta['thumbnail']
                thumbnail = local(repo, thumbnail_path).read_bytes()
                need(thumbnail == git(repo, 'show', row['stageCommit'] + ':' + thumbnail_path), 'Thumbnail differs from fixed stage commit')
                target = work / 'thumbnail'; reader.file(f'https://raw.githubusercontent.com/{REPO}/{row["stageCommit"]}/{thumbnail_path}', target, len(thumbnail), sha(thumbnail)); target.unlink()
                prefix = f'content/assets/{identity}/source/'
                need(packages.source_listing(repo / prefix) == [x['name'] for x in row['sourceFiles']], 'Current complete source listing differs')
                check_notice(row['notice'], meta, False); check_notice(row['fbxNotice'], meta, True)
                for x in row['sourceFiles']:
                    data = local(repo, prefix + x['name']).read_bytes()
                    need(len(data) == x['bytes'] and sha(data) == x['sha256'] and data == git(repo, 'show', row['stageCommit'] + ':' + prefix + x['name']), 'Source bytes or raw hosting pin differ')
                    # New non-preview originals stay available through immutable Git URLs.
                    if x['name'] != meta['preview']:
                        target = work / ('source-' + x['name']); reader.file(f'https://raw.githubusercontent.com/{REPO}/{row["stageCommit"]}/{prefix}{x["name"]}', target, x['bytes'], x['sha256']); target.unlink()
                for kind in c['publicPayloads']:
                    x = published[kind]; target = work / x['filename']; reader.file(root + x['filename'], target, x['bytes'], x['sha256'])
                    if kind == 'fbx':
                        dest = payloads / (x['sha256'] + '.fbx'); need(not dest.is_symlink(), 'Unsafe cached FBX')
                        if dest.exists(): need(file_sha(dest) == x['sha256'], 'Cached FBX changed')
                        else: shutil.copyfile(target, dest)
                    elif kind == 'fbxArchive': verify_zip(target, {identity + '.fbx': published['fbx'], 'LICENSE.txt': row['fbxNotice']})
                    else: verify_zip(target, {**{x['name']: x for x in row['sourceFiles']}, 'LICENSE.txt': row['notice']})
                    target.unlink()
                bindings.append({'id': identity, 'assetVersion': row['version'], 'metadataSha256': row['metadataSha256'], 'sources': row['sourceFiles']})
                projection.append({'id': identity, 'assetVersion': row['version'], 'format': 'FBX', 'packageVersion': PACKAGE_VERSION,
                    'sourceCommit': row['stageCommit'], 'sources': row['sourceFiles'], 'direct': {**published['fbx'], 'url': root + published['fbx']['filename']},
                    'archive': {**published['fbxArchive'], 'url': root + published['fbxArchive']['filename']}, 'notice': row['fbxNotice'], 'selfContained': True,
                    'limitations': ['FBX materials, transparency and face culling can vary by importer; GLB is retained for previews.', 'Tangents are not exported. Unity, Godot, VRChat, printing and manufacture have not been tested.'],
                    'verification': {'state': 'published-verified', 'releaseTag': c['releaseTag'], 'releaseId': c['releaseId'], 'fCommit': c['verificationCommit'], 'inventorySha256': c['inputs']['cohort-inventory.json']}})
    need(input_hashes == [{'path': x['path'], 'sha256': file_sha(local(repo, x['path']))} for x in input_hashes] and head == git(repo, 'rev-parse', 'HEAD').decode().strip(), 'Checkout changed during prep')
    receipt = {'schemaVersion': 1, 'createdBy': 'same-job-cohort-prep/1', 'head': head, 'activationSha256': sha(config_bytes),
               'execution': {'runId': os.environ.get('GITHUB_RUN_ID'), 'runAttempt': os.environ.get('GITHUB_RUN_ATTEMPT'), 'job': os.environ.get('GITHUB_JOB')},
               'inputs': input_hashes, 'projection': projection, 'projectionSha256': sha(compact(projection)), 'sourceBindings': bindings, 'provenance': provenance}
    with receipt_path.open('xb') as file: file.write(compact(receipt) + b'\n')
    print(json.dumps({'verifiedModels': len(projection), 'cohorts': [c['name'] for c in config['cohorts']], 'receipt': RECEIPT,
                      'scope': 'fresh anonymous payload/source checks and exact successful F/R attestation; same-checkout same-job handoff'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--repo', required=True, type=Path); args = parser.parse_args()
    try: prepare(args.repo.resolve())
    except Exception as error:
        # Never expose redirect URLs or request headers from a failed network read.
        print('COHORT_PREP_STOP: ' + (str(error)[:300] if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1) from None
