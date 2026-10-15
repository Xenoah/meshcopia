"""LOCAL ONLY: validate an actual successful verification artifact; emit pending review."""
import argparse
from pathlib import Path
import tempfile
import zipfile
import transport as t


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'artifact-metadata', 'artifact-zip', 'repo', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args(); run = t.read(a.run); artifact = t.read(a.artifact_metadata); docs = a.repo / 'docs/minimal-verification'
    with zipfile.ZipFile(a.artifact_zip) as z:
        inventory = z.read('minimal-inventory.json')
    record = {'schemaVersion': 1, 'reviewStatus': 'pending-review', 'repository': t.REPO,
              'verificationCommit': run['head_sha'], 'tag': t.TAG, 'runId': run['id'], 'runAttempt': run['run_attempt'],
              'workflowPath': t.WORKFLOW, 'workflowSha256': t.file_sha(a.repo / t.WORKFLOW),
              'artifactId': artifact['id'], 'artifactName': artifact['name'], 'artifactSha256': t.file_sha(a.artifact_zip),
              'inventorySha256': t.sha(inventory), 'sourceInventorySha256': t.file_sha(docs / 'source173.json'),
              'expectedManifestSha256': t.file_sha(docs / 'expected173.json'),
              'releaseBodySha256': t.file_sha(a.repo / 'docs/minimal-transport/RELEASE_BODY.md'),
              'approvedIds': [r['id'] for r in t.read(docs / 'source173.json')['assets']]}
    t.check_run(record, run, artifact)
    for path, checksum in ((t.WORKFLOW, record['workflowSha256']), ('docs/minimal-verification/source173.json', record['sourceInventorySha256']), ('docs/minimal-verification/expected173.json', record['expectedManifestSha256'])):
        t.need(t.sha(t.git(a.repo, 'show', record['verificationCommit'] + ':' + path)) == checksum, 'Local reviewed file differs from verification commit')
    source, expected = t.approval_check({**record, 'reviewStatus': 'approved-for-transport'}, (docs / 'source173.json').read_bytes(), (docs / 'expected173.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='minimal-approval-') as directory:
        t.unpack(record, source, expected, a.artifact_zip, Path(directory) / 'payload', a.repo, materialize=False)
    with a.out.open('xb') as handle: handle.write(t.canonical(record))
    print('Actual successful artifact validated; pending-review candidate only. No external writes.')


if __name__ == '__main__':
    main()
