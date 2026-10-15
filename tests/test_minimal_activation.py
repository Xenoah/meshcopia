"""Synthetic fixtures only; these tests are not public release evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/verify-minimal-activation.py'
spec = importlib.util.spec_from_file_location('minimal_activation', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture():
    commit = '1' * 40
    release_id = 123
    rows = []
    for i in range(173):
        name = f'fixture-{i}-1.0.0-minimal-1.0.0.zip'
        rows.append({'id': f'fixture-{i}', 'version': '1.0.0', 'kind': 'model' if i < 137 else 'texture', 'filename': name, 'bytes': 3, 'sha256': gate.sha(b'zip'), 'url': f'https://github.com/{gate.REPO}/releases/download/{gate.TAG}/{name}', 'sourceFiles': [], 'notice': {}})
    inventory = {'schemaVersion': 1, 'packageVersion': '1.0.0', 'repository': gate.REPO, 'tag': gate.TAG, 'cohort': 'published173', 'sourceCommit': gate.BASE, 'verificationCommit': commit, 'workflow': gate.WORKFLOW, 'runId': '456', 'runAttempt': '2', 'sourceInventorySha256': 'a'*64, 'expectedManifestSha256': 'b'*64, 'packagerSha256': 'c'*64, 'runtimeSha256': 'd'*64, 'assets': rows}
    raw = json.dumps(inventory).encode()
    a = {'cohort': 'published173', 'releaseTag': gate.TAG, 'releaseId': release_id, 'verificationCommit': commit, 'inventorySha256': gate.sha(raw), 'transportEvidenceFile': 'docs/minimal-publication/fixture-T.json', 'transportEvidenceSha256': 'f'*64}
    release_url = f'https://github.com/{gate.REPO}/releases/tag/{gate.TAG}'
    release = {'id': release_id, 'tag_name': gate.TAG, 'draft': False, 'prerelease': False, 'target_commitish': commit, 'html_url': release_url}
    ref = {'ref': 'refs/tags/' + gate.TAG, 'object': {'type': 'commit', 'sha': commit, 'url': gate.API + '/git/commits/' + commit}}
    run = {'id': 456, 'run_attempt': 2, 'head_sha': commit, 'head_branch': 'minimal/verify-existing173-v1', 'event': 'push', 'path': gate.WORKFLOW, 'status': 'completed', 'conclusion': 'success', 'repository': {'full_name': gate.REPO}, 'head_repository': {'full_name': gate.REPO}}
    entries = [{'name': row['filename'], 'bytes': row['bytes'], 'sha256': row['sha256'], 'url': row['url']} for row in rows]
    entries.append({'name': 'minimal-inventory.json', 'bytes': len(raw), 'sha256': gate.sha(raw), 'url': f'https://github.com/{gate.REPO}/releases/download/{gate.TAG}/minimal-inventory.json'})
    attachments = [{'id': i+1, 'name': item['name'], 'size': item['bytes'], 'digest': 'sha256:' + item['sha256'], 'browser_download_url': item['url'], 'state': 'uploaded'} for i, item in enumerate(entries)]
    evidence = {'schemaVersion': 1, 'status': 'anonymous-byte-readback-passed', 'repository': gate.REPO, 'tag': gate.TAG, 'verificationCommit': commit, 'releaseId': release_id, 'releaseUrl': release_url, 'attachmentCount': 174, 'inventorySha256': gate.sha(raw), 'browserDownloadEvidence': 'not-performed-by-transport', 'assets': [{**item, 'assetId': i+1, 'anonymousReadback': True} for i, item in enumerate(entries)]}
    return [a, evidence, inventory, release, ref, run, attachments, raw]


class ActivationTests(unittest.TestCase):
    def test_empty_is_explicit_and_requires_no_network(self):
        self.assertEqual(gate.validate_activation({'schemaVersion': 1, 'repository': gate.REPO, 'activations': []}), [])

    def test_config_is_exact_and_rejects_unsupported_or_unsafe_input(self):
        a = fixture()[0]
        valid = {'schemaVersion': 1, 'repository': gate.REPO, 'activations': [a]}
        self.assertEqual(gate.validate_activation(valid), [a])
        mutations = [lambda x: x.update(offline=True), lambda x: x['activations'].append(a), lambda x: x['activations'][0].update(cohort='new232'), lambda x: x['activations'][0].update(releaseTag='latest'), lambda x: x['activations'][0].update(releaseId=True), lambda x: x['activations'][0].update(verificationCommit='main'), lambda x: x['activations'][0].update(transportEvidenceFile='../proof.json'), lambda x: x['activations'][0].update(inventorySha256='bad')]
        for change in mutations:
            value = copy.deepcopy(valid)
            change(value)
            with self.assertRaises(ValueError):
                gate.validate_activation(value)

    def test_exact_173_zip_plus_inventory_join(self):
        args = fixture()
        self.assertEqual(gate.validate_remote(*args), args[2]['assets'])

    def test_every_remote_identity_and_readback_join_fails_closed(self):
        changes = {
            'transport status': lambda x: x[1].update(status='uploaded'),
            'transport repo': lambda x: x[1].update(repository='other/repo'),
            'transport tag': lambda x: x[1].update(tag='other-v1.0.0'),
            'transport commit': lambda x: x[1].update(verificationCommit='2'*40),
            'transport release': lambda x: x[1].update(releaseId=999),
            'transport inventory': lambda x: x[1].update(inventorySha256='3'*64),
            'transport count': lambda x: x[1].update(attachmentCount=173),
            'fake browser proof': lambda x: x[1].update(browserDownloadEvidence='passed'),
            'release URL': lambda x: x[3].update(html_url='https://example.invalid/release'),
            'draft': lambda x: x[3].update(draft=True),
            'prerelease': lambda x: x[3].update(prerelease=True),
            'release commit': lambda x: x[3].update(target_commitish='main'),
            'release ID': lambda x: x[3].update(id=999),
            'tag type': lambda x: x[4]['object'].update(type='tag'),
            'tag commit': lambda x: x[4]['object'].update(sha='2'*40),
            'inventory bytes': lambda x: x.__setitem__(7, b'{}'),
            'inventory repo': lambda x: x[2].update(repository='other/repo'),
            'inventory base': lambda x: x[2].update(sourceCommit='2'*40),
            'inventory workflow': lambda x: x[2].update(workflow='other.yml'),
            'run ID': lambda x: x[5].update(id=999),
            'run attempt': lambda x: x[5].update(run_attempt=3),
            'run commit': lambda x: x[5].update(head_sha='2'*40),
            'run branch': lambda x: x[5].update(head_branch='main'),
            'run event': lambda x: x[5].update(event='workflow_dispatch'),
            'run path': lambda x: x[5].update(path='other.yml'),
            'run status': lambda x: x[5].update(status='in_progress'),
            'run conclusion': lambda x: x[5].update(conclusion='failure'),
            'run fork': lambda x: x[5].update(head_repository={'full_name': 'other/repo'}),
            'missing ZIP': lambda x: x[6].pop(),
            'duplicate ZIP': lambda x: x[6].append(x[6][0]),
            'attachment state': lambda x: x[6][0].update(state='new'),
            'attachment size': lambda x: x[6][0].update(size=4),
            'attachment hash': lambda x: x[6][0].update(digest='sha256:' + 'e'*64),
            'attachment URL': lambda x: x[6][0].update(browser_download_url='https://example.invalid/file.zip'),
            'readback ID': lambda x: x[1]['assets'][0].update(assetId=999),
            'nonanonymous readback': lambda x: x[1]['assets'][0].update(anonymousReadback=False),
            'readback hash': lambda x: x[1]['assets'][0].update(sha256='e'*64),
            'readback bytes': lambda x: x[1]['assets'][0].update(bytes=4),
            'readback URL': lambda x: x[1]['assets'][0].update(url='https://example.invalid/file.zip'),
        }
        for label, change in changes.items():
            with self.subTest(label=label):
                args = fixture()
                change(args)
                with self.assertRaises(ValueError):
                    gate.validate_remote(*args)

    def test_streamed_zip_is_size_and_hash_bounded(self):
        class Response:
            def __init__(self, data): self.data = data
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): value, self.data = self.data[:size], self.data[size:]; return value
        reader = gate.PublicReader()
        with tempfile.TemporaryDirectory() as folder:
            for i, (data, length, digest, valid) in enumerate([(b'zip', 3, gate.sha(b'zip'), True), (b'zip!', 3, gate.sha(b'zip'), False), (b'zi', 3, gate.sha(b'zip'), False), (b'bad', 3, gate.sha(b'zip'), False)]):
                reader.open = lambda url, data=data: Response(data)
                target = Path(folder) / str(i)
                if valid:
                    reader.file('https://github.com/fixture', target, length, digest)
                    self.assertEqual(target.read_bytes(), data)
                else:
                    with self.assertRaises(ValueError): reader.file('https://github.com/fixture', target, length, digest)

    def test_anonymous_redirects_cannot_leave_trusted_https_hosts(self):
        for url in ['https://github.com/Xenoah/meshcopia', 'https://api.github.com/repos/Xenoah/meshcopia', 'https://release-assets.githubusercontent.com/file', 'https://xenoah.github.io/meshcopia/']:
            gate.trusted_url(url)
        for url in ['http://github.com/file', 'https://github.com.evil.invalid/file', 'https://evilgithubusercontent.com/file', 'https://user:pass@github.com/file', 'https://github.com:444/file']:
            with self.assertRaises(ValueError): gate.trusted_url(url)

    def test_duplicate_json_keys_and_symlinked_proof_are_rejected(self):
        with self.assertRaises(ValueError): gate.parse_json(b'{"x":1,"x":2}')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'source').write_text('proof')
            (root / 'link').symlink_to(root / 'source')
            with self.assertRaises(ValueError): gate.local_file(root, 'link')

    def test_detail_page_must_identify_exact_canonical_asset_url(self):
        parser = gate.CanonicalLinks()
        parser.feed('<link rel="canonical" href="https://xenoah.github.io/meshcopia/assets/fixture/">')
        self.assertEqual(parser.urls, ['https://xenoah.github.io/meshcopia/assets/fixture/'])


if __name__ == '__main__':
    unittest.main()
