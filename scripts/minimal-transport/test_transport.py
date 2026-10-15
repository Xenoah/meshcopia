"""No-network transport regression tests; nested ZIP strictness is covered by packager tests."""
import copy
import io
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile
import transport as t


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.f = '7' * 40
        notice = {'filename': 'LICENSE.txt', 'text': 'notice\n', 'bytes': 7, 'sha256': t.sha(b'notice\n')}
        files = [{'name': 'asset.glb', 'bytes': 3, 'sha256': t.sha(b'raw')}]
        rows = [{'id': f'asset-{i:03}', 'version': '1.0.0', 'kind': 'model' if i < 137 else 'texture', 'status': 'public', 'metadataSha256': 'a' * 64, 'sourceFiles': copy.deepcopy(files), 'notice': copy.deepcopy(notice)} for i in range(173)]
        self.source = {'schemaVersion': 1, 'sourceCommit': t.BASE, 'cohort': 'published173', 'assets': rows}
        self.expected = {'schemaVersion': 1, 'reviewStatus': 'final-reviewed', 'sourceCommit': t.BASE, 'cohort': 'published173', 'sourceInventorySha256': t.sha(t.canonical(self.source)), 'packagerSha256': 'b' * 64, 'runtimeSha256': 'c' * 64,
                         'assets': [{'id': r['id'], 'filename': r['id'] + '-1.0.0-minimal-1.0.0.zip', 'archiveBytes': 3, 'archiveSha256': t.sha(b'zip'), 'noticeSha256': notice['sha256'], 'sourceFiles': copy.deepcopy(files)} for r in rows]}
        self.a = {'schemaVersion': 1, 'reviewStatus': 'approved-for-transport', 'repository': t.REPO, 'verificationCommit': self.f, 'tag': t.TAG, 'workflowPath': t.WORKFLOW, 'workflowSha256': 'd' * 64, 'artifactSha256': 'e' * 64, 'inventorySha256': 'f' * 64, 'releaseBodySha256': '0' * 64, 'sourceInventorySha256': t.sha(t.canonical(self.source)), 'expectedManifestSha256': t.sha(t.canonical(self.expected)), 'runId': 12, 'runAttempt': 2, 'artifactId': 34, 'artifactName': f'minimal-existing173-{self.f}-12-2', 'approvedIds': [r['id'] for r in rows]}
        self.files = {r['filename']: b'zip' for r in self.expected['assets']}
        self.inv = copy.deepcopy(t.expected_inventory(self.a, self.source, self.expected))
        self.run = {'id': 12, 'run_attempt': 2, 'repository': {'full_name': t.REPO, 'id': 1}, 'head_repository': {'full_name': t.REPO, 'id': 1}, 'head_sha': self.f, 'head_branch': t.VERIFY_BRANCH, 'event': 'push', 'path': t.WORKFLOW, 'status': 'completed', 'conclusion': 'success'}
        self.artifact = {'id': 34, 'name': self.a['artifactName'], 'expired': False, 'digest': 'sha256:' + self.a['artifactSha256'], 'workflow_run': {'id': 12, 'head_sha': self.f, 'head_branch': t.VERIFY_BRANCH, 'repository_id': 1, 'head_repository_id': 1}}

    def tearDown(self): self.temp.cleanup()

    def archive(self, mutate=None, extra=None):
        self.files['minimal-inventory.json'] = t.canonical(self.inv)
        self.a['inventorySha256'] = t.sha(self.files['minimal-inventory.json'])
        path = self.root / 'artifact.zip'
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
            for name, data in self.files.items():
                info = zipfile.ZipInfo(name)
                if mutate: info, data = mutate(info, data)
                z.writestr(info, data)
            if extra: z.writestr(*extra)
        self.a['artifactSha256'] = t.file_sha(path)
        return path

    def unpack(self, materialize=True, **kwargs):
        with patch.object(t.packages, 'make_plan', return_value={}), patch.object(t.packages, 'verify_archive') as verify:
            rows = t.unpack(self.a, self.source, self.expected, self.archive(**kwargs), self.root / 'payload', self.root, materialize=materialize)
            self.assertEqual(verify.call_count, 173)
            return rows

    def test_valid_approval(self): t.approval_check(self.a, t.canonical(self.source), t.canonical(self.expected))
    def test_pending_approval_blocked(self):
        self.a['reviewStatus'] = 'pending-review'
        with self.assertRaises(ValueError): t.approval_check(self.a, t.canonical(self.source), t.canonical(self.expected))
    def test_unreviewed_hashes_blocked(self):
        self.expected['reviewStatus'] = 'pending-review'; self.a['expectedManifestSha256'] = t.sha(t.canonical(self.expected))
        with self.assertRaises(ValueError): t.approval_check(self.a, t.canonical(self.source), t.canonical(self.expected))
    def test_wrong_ids_blocked(self):
        self.a['approvedIds'][0] = 'new-asset'
        with self.assertRaises(ValueError): t.approval_check(self.a, t.canonical(self.source), t.canonical(self.expected))
    def test_source_drift_blocked(self):
        with self.assertRaises(ValueError): t.approval_check(self.a, t.canonical(self.source) + b' ', t.canonical(self.expected))
    def test_exact_174_public_files_only(self):
        entries = self.unpack(); self.assertEqual(len(entries), 174)
        self.assertEqual((self.root / 'payload' / self.expected['assets'][0]['filename']).read_bytes(), b'zip')
        self.assertEqual({p.suffix for p in (self.root / 'payload').iterdir()}, {'.json', '.zip'})
        self.assertEqual({r['name'] for r in entries if not r['name'].endswith('.zip')}, {'minimal-inventory.json'})
    def test_review_without_retaining_archives(self):
        self.unpack(materialize=False); self.assertEqual(list((self.root / 'payload').iterdir()), [])
    def test_nested_archive_verifier_failure_blocks(self):
        with patch.object(t.packages, 'make_plan', return_value={}), patch.object(t.packages, 'verify_archive', side_effect=ValueError('extra consumer metadata')):
            with self.assertRaises(ValueError): t.unpack(self.a, self.source, self.expected, self.archive(), self.root / 'payload', self.root)
    def test_internal_qa_never_accepted_as_release_payload(self):
        with self.assertRaises(ValueError): self.unpack(extra=('qa.json', b'{}'))
    def test_duplicate_name(self):
        with self.assertRaises(ValueError): self.unpack(extra=('minimal-inventory.json', b'{}'))
    def test_traversal(self):
        def change(i, d):
            if i.filename == 'minimal-inventory.json': i.filename = '../minimal-inventory.json'
            return i, d
        with self.assertRaises(ValueError): self.unpack(mutate=change)
    def test_symlink(self):
        def change(i, d): i.external_attr = (stat.S_IFLNK | 0o777) << 16; return i, d
        with self.assertRaises(ValueError): self.unpack(mutate=change)
    def test_unsupported_compression(self):
        def change(i, d): i.compress_type = zipfile.ZIP_BZIP2; return i, d
        with self.assertRaises(ValueError): self.unpack(mutate=change)
    def test_payload_hash(self):
        self.files[self.expected['assets'][0]['filename']] = b'bad'
        with self.assertRaises(ValueError): self.unpack()
    def test_payload_size(self):
        self.files[self.expected['assets'][0]['filename']] = b'longer'
        with self.assertRaises(ValueError): self.unpack()
    def test_notice_binding(self):
        self.inv['assets'][0]['notice']['text'] = 'changed\n'
        with self.assertRaises(ValueError): self.unpack()
    def test_source_binding(self):
        self.inv['assets'][0]['sourceFiles'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.unpack()
    def test_inventory_run_binding(self):
        self.inv['runAttempt'] = '1'
        with self.assertRaises(ValueError): self.unpack()
    def test_artifact_hash(self):
        archive = self.archive(); self.a['artifactSha256'] = '0' * 64
        with self.assertRaises(ValueError): t.unpack(self.a, self.source, self.expected, archive, self.root / 'payload', self.root)
    def test_valid_run(self): t.check_run(self.a, self.run, self.artifact)
    def test_run_wrong_attempt(self):
        with self.assertRaises(ValueError): t.check_run(self.a, {**self.run, 'run_attempt': 3}, self.artifact)
    def test_run_not_successful(self):
        for status in ('queued', 'in_progress', 'waiting'):
            with self.subTest(status=status), self.assertRaises(ValueError): t.check_run(self.a, {**self.run, 'status': status}, self.artifact)
    def test_run_wrong_commit(self):
        with self.assertRaises(ValueError): t.check_run(self.a, {**self.run, 'head_sha': '0' * 40}, self.artifact)
    def test_artifact_expired(self):
        with self.assertRaises(ValueError): t.check_run(self.a, self.run, {**self.artifact, 'expired': True})
    def test_artifact_fork(self):
        bad = copy.deepcopy(self.artifact); bad['workflow_run']['head_repository_id'] = 99
        with self.assertRaises(ValueError): t.check_run(self.a, self.run, bad)
    def test_only_confirmed_absence_permitted(self):
        class Missing:
            def json(self, path): raise urllib.error.HTTPError(path, 404, 'missing', {}, None)
        t.absence(Missing())
        class Forbidden:
            def json(self, path): raise urllib.error.HTTPError(path, 403, 'forbidden', {}, None)
        with self.assertRaises(ValueError): t.absence(Forbidden())
    def test_existing_never_overwritten(self):
        class Existing:
            def json(self, path): return {'id': 1}
        with self.assertRaises(ValueError): t.absence(Existing())
    def test_no_authenticated_cross_host(self):
        with self.assertRaises(ValueError): t.GitHub('unused').request('https://evil.invalid/')
    def test_no_automatic_authenticated_redirect(self):
        request = urllib.request.Request('https://api.github.com/', headers={'Authorization': 'secret'})
        self.assertIsNone(t.NoRedirect().redirect_request(request, None, 302, '', {}, 'https://evil.invalid/'))
    def test_download_bound(self):
        with self.assertRaises(ValueError): t.stream_file(io.BytesIO(b'1234'), self.root / 'download', 3)
    def test_changed_draft_blocks(self):
        class API:
            def json(self, path): return {'id': 1, 'draft': True, 'target_commitish': self_f, 'tag_name': t.TAG, 'name': t.RELEASE_NAME, 'body': 'changed', 'prerelease': False}
        self_f = self.f
        with self.assertRaises(ValueError): t.check_draft(API(), 1, 'reviewed', self.f)
    def test_uncertain_create_not_retried(self):
        class API:
            writes = 0
            def json(self, path, method='GET', value=None):
                if method != 'GET': self.writes += 1; raise urllib.error.URLError('uncertain')
                raise urllib.error.HTTPError(path, 404, 'missing', {}, None)
        api = API()
        with self.assertRaises(urllib.error.URLError): t.publish(api, b'reviewed', [], self.root, self.a)
        self.assertEqual(api.writes, 1)
        self.assertEqual(t.read(self.root / 'journal.jsonl')['phase'], 'create-draft-requested')
    def test_uncertain_upload_not_retried(self):
        f = self.f
        class API:
            uploads = 0
            def json(self, path, method='GET', value=None):
                if method == 'POST': return {'id': 1, 'draft': True, 'tag_name': t.TAG, 'target_commitish': f}
                raise urllib.error.HTTPError(path, 404, 'missing', {}, None)
            def request(self, *args, **kwargs): self.uploads += 1; raise urllib.error.URLError('uncertain')
        api = API(); (self.root / 'payload').mkdir(); (self.root / 'payload/test').write_bytes(b'x')
        with self.assertRaises(urllib.error.URLError): t.publish(api, b'reviewed', [{'name': 'test'}], self.root, self.a)
        self.assertEqual(api.uploads, 1)
    def test_changed_draft_never_published(self):
        f = self.f
        class API:
            patches = 0
            def json(self, path, method='GET', value=None):
                if method == 'POST': return {'id': 1, 'draft': True, 'tag_name': t.TAG, 'target_commitish': f}
                if method == 'PATCH': self.patches += 1
                if path == '/releases/1': return {'id': 1, 'draft': True, 'tag_name': t.TAG, 'target_commitish': f, 'name': t.RELEASE_NAME, 'body': 'changed', 'prerelease': False}
                raise urllib.error.HTTPError(path, 404, 'missing', {}, None)
        api = API()
        with patch.object(t, 'verify_assets', return_value=[]), self.assertRaises(ValueError): t.publish(api, b'reviewed', [], self.root, self.a)
        self.assertEqual(api.patches, 0)


if __name__ == '__main__': unittest.main()
