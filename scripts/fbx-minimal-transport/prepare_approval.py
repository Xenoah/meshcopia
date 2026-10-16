"""LOCAL ONLY: validate both actual successful F artifacts; emit pending-review only."""
import argparse
from pathlib import Path
import tempfile
import zipfile
import transport as t


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'job', 'payload-metadata', 'qa-metadata', 'payload-zip', 'qa-zip', 'repo', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args(); repo = a.repo.resolve(); docs = repo / 'docs/fbx-minimal-verification'
    run, job, payload, internal = map(t.read, (a.run, a.job, a.payload_metadata, a.qa_metadata))
    record = {'schemaVersion': 1, 'reviewStatus': 'pending-review', 'repository': t.REPO, 'tag': t.TAG, 'fCommit': run['head_sha'], 'runId': run['id'], 'runAttempt': run['run_attempt'], 'jobId': job['id'], 'workflowPath': t.WORKFLOW, 'workflowSha256': t.file_sha(repo / t.WORKFLOW),
              'payloadArtifactId': payload['id'], 'payloadArtifactName': payload['name'], 'payloadArtifactSha256': t.file_sha(a.payload_zip),
              'qaArtifactId': internal['id'], 'qaArtifactName': internal['name'], 'qaArtifactSha256': t.file_sha(a.qa_zip),
              'sourceInventorySha256': t.file_sha(docs / 'source137.json'), 'expectedManifestSha256': t.file_sha(docs / 'expected137.json'), 'runtimeSha256': t.file_sha(docs / 'runtime.json'),
              'releaseBodySha256': t.file_sha(repo / 'docs/fbx-minimal-transport/RELEASE_BODY.md'), 'approvedIds': [r['id'] for r in t.read(docs / 'source137.json')['models']]}
    for path, names in ((a.payload_zip, [('fbx-minimal-inventory.json', 'inventorySha256')]), (a.qa_zip, [('qa.json', 'qaSummarySha256'), ('runtime.json', 'qaRuntimeSha256'), ('pilot-gate.json', 'qaPilotGateSha256')])):
        with zipfile.ZipFile(path) as z:
            for name, key in names:
                info = z.getinfo(name); t.need(0 < info.file_size <= t.qa.MAX_JSON, 'Internal component size invalid'); record[key] = t.sha(z.read(info))
    t.check_run(record, run); t.check_job(record, job)
    t.check_artifact(record, run, payload, 'payload'); t.check_artifact(record, run, internal, 'qa')
    source, expected, runtime = t.approval_check({**record, 'reviewStatus': 'approved-for-transport'}, (docs / 'source137.json').read_bytes(), (docs / 'expected137.json').read_bytes(), (docs / 'runtime.json').read_bytes())
    t.check_source(repo, record, source, expected, runtime)
    with tempfile.TemporaryDirectory(prefix='fbx-minimal-approval-') as directory:
        t.unpack_payload(record, source, expected, a.payload_zip, a.qa_zip, Path(directory) / 'payload', repo, materialize=False)
        t.qa.verify_internal_qa(a.qa_zip, record, source, expected, runtime, repo, payload_archive=a.payload_zip)
    with a.out.open('xb') as handle: handle.write(t.canonical(record))
    print('Both actual successful artifacts validated. Candidate remains pending-review. No publication or retained media copies.')


if __name__ == '__main__': main()
