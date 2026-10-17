"""Copy the concise cohort inventory and artifact envelopes to an evidence branch.

Runs in the `record` job after a successful F verification. It checks that the
downloaded payload artifact contains exactly the inventory-declared files with
matching sizes and hashes, then commits only `cohort-inventory.json` and an
`envelope.json` to the new branch evidence/cohort-<name>-<run>-<attempt>.
No QA reports, payload files, releases or Pages are written. Never retried.
"""
import argparse
import base64
import os
import subprocess
from common import *


def run(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', required=True, type=Path); parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args(); payload = args.payload.resolve()
    cohort = os.environ['COHORT']; need(NAME.fullmatch(cohort), 'Invalid cohort')
    for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'PAYLOAD_ID', 'QA_ID'):
        need(re.fullmatch(r'[1-9][0-9]*', os.environ.get(key, '')), 'Missing identity ' + key)
    for key in ('PAYLOAD_DIGEST', 'QA_DIGEST'):
        # upload-artifact reports the bare SHA-256; the REST API reports `sha256:<hex>`.
        value = os.environ.get(key, '')
        if re.fullmatch(r'[0-9a-f]{64}', value): os.environ[key] = 'sha256:' + value
        need(re.fullmatch(r'sha256:[0-9a-f]{64}', os.environ.get(key, '')), 'Missing digest ' + key)
    inventory_bytes = packages.regular_file(payload / 'cohort-inventory.json').read_bytes(); inventory = json.loads(inventory_bytes)
    need(inventory['cohort'] == cohort and inventory['fCommit'] == os.environ['GITHUB_SHA'] and inventory['runId'] == os.environ['GITHUB_RUN_ID'] and inventory['runAttempt'] == os.environ['GITHUB_RUN_ATTEMPT'], 'Inventory identity differs')
    need({p.name for p in payload.iterdir()} == payload_names(inventory['models']), 'Payload set differs from inventory')
    for m in inventory['models']:
        for key in ('fbx', 'fbxArchive', 'archive'):
            b, h = packages.hash_file(packages.regular_file(payload / m[key]['filename']))
            need(b == m[key]['bytes'] and h == m[key]['sha256'], 'Payload bytes differ: ' + m[key]['filename'])
    envelope = {'schemaVersion': 1, 'repository': REPO, 'cohort': cohort, 'fCommit': os.environ['GITHUB_SHA'], 'workflow': '.github/workflows/verify-cohort.yml',
                'runId': int(os.environ['GITHUB_RUN_ID']), 'runAttempt': int(os.environ['GITHUB_RUN_ATTEMPT']),
                'payloadArtifact': {'id': int(os.environ['PAYLOAD_ID']), 'name': f'cohort-{cohort}-{os.environ["GITHUB_SHA"]}-{os.environ["GITHUB_RUN_ID"]}-{os.environ["GITHUB_RUN_ATTEMPT"]}', 'digest': os.environ['PAYLOAD_DIGEST']},
                'qaArtifact': {'id': int(os.environ['QA_ID']), 'name': f'cohort-internal-qa-{cohort}-{os.environ["GITHUB_SHA"]}-{os.environ["GITHUB_RUN_ID"]}-{os.environ["GITHUB_RUN_ATTEMPT"]}', 'digest': os.environ['QA_DIGEST']},
                'inventorySha256': sha(inventory_bytes), 'reviewStatus': inventory['reviewStatus'],
                'note': 'Review evidence only; not a release, approval or availability record.'}
    work = args.work; work.mkdir(parents=True)
    (work / 'cohort-inventory.json').write_bytes(inventory_bytes); dump(work / 'envelope.json', envelope)
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'github-actions[bot]', 'GIT_AUTHOR_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
           'GIT_COMMITTER_NAME': 'github-actions[bot]', 'GIT_COMMITTER_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com'}
    run('git', 'init', '-q', str(work), env=env)
    run('git', 'add', 'cohort-inventory.json', 'envelope.json', cwd=work, env=env)
    run('git', 'commit', '-q', '-m', f'evidence: cohort {cohort} F run {os.environ["GITHUB_RUN_ID"]}', cwd=work, env=env)
    branch = f'evidence/cohort-{cohort}-{os.environ["GITHUB_RUN_ID"]}-{os.environ["GITHUB_RUN_ATTEMPT"]}'
    auth = base64.b64encode(('x-access-token:' + os.environ.pop('PUSH_TOKEN')).encode()).decode()
    print('::add-mask::' + auth)
    run('git', '-c', 'http.https://github.com/.extraheader=AUTHORIZATION: basic ' + auth, 'push', 'https://github.com/' + REPO, 'HEAD:refs/heads/' + branch, cwd=work, env=env)
    print(json.dumps({'branch': branch, 'inventorySha256': envelope['inventorySha256'], 'models': len(inventory['models'])}))


if __name__ == '__main__':
    try: main()
    except Exception as error:
        message = str(error) if isinstance(error, ValueError) else type(error).__name__
        print('::error title=COHORT_RECORD_STOP::' + message.replace('%', '%25').replace('\n', ' ')[:500])
        raise SystemExit(1)
