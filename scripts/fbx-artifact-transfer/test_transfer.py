import copy
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
import transfer as t


class Response(io.BytesIO):
    status = 200
    headers = {}


class FakeOpener:
    def __init__(self, location, payload=b'test'):
        self.location = location; self.payload = payload; self.requests = []
    def open(self, request, timeout):
        self.requests.append(request)
        if len(self.requests) == 1:
            raise urllib.error.HTTPError(request.full_url, 302, 'Found', {'Location': self.location}, None)
        return Response(self.payload)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name); self.data = b'0123456789ABCDEF'; self.source = self.root / 'artifact.zip'; self.source.write_bytes(self.data)
        self.checksum = hashlib.sha256(self.data).hexdigest()
    def split(self):
        records = t.split_archive(self.source, self.root / 'split', len(self.data), self.checksum, 6)
        paths = [self.root / 'split' / f'part-{x["index"]:02}' / x['filename'] for x in records]
        return records, paths
    def test_exact_three_part_reassembly(self):
        records, paths = self.split(); self.assertEqual([x['bytes'] for x in records], [6, 6, 4])
        out = io.BytesIO(); t.verify_parts(paths, records, len(self.data), self.checksum, out); self.assertEqual(out.getvalue(), self.data)
    def test_bad_original_hash_blocks_split(self):
        with self.assertRaises(ValueError): t.split_archive(self.source, self.root / 'split', len(self.data), '0' * 64, 6)
        self.assertFalse((self.root / 'split').exists())
    def test_bad_original_size_blocks_split(self):
        with self.assertRaises(ValueError): t.split_archive(self.source, self.root / 'split', 15, self.checksum, 6)
    def test_changed_part_rejected(self):
        records, paths = self.split(); paths[1].write_bytes(b'xxxxxx')
        with self.assertRaises(ValueError): t.verify_parts(paths, records, 16, self.checksum)
    def test_short_part_rejected(self):
        records, paths = self.split(); paths[1].write_bytes(b'x')
        with self.assertRaises(ValueError): t.verify_parts(paths, records, 16, self.checksum)
    def test_long_part_rejected(self):
        records, paths = self.split(); paths[1].write_bytes(b'x' * 7)
        with self.assertRaises(ValueError): t.verify_parts(paths, records, 16, self.checksum)
    def test_missing_part_rejected(self):
        records, paths = self.split()
        with self.assertRaises(ValueError): t.verify_parts(paths[:-1], records, 16, self.checksum)
    def test_reordered_parts_rejected(self):
        records, paths = self.split()
        with self.assertRaises(ValueError): t.verify_parts(paths[::-1], records, 16, self.checksum)
    def test_changed_offset_rejected(self):
        records, paths = self.split(); records[1]['offset'] += 1
        with self.assertRaises(ValueError): t.verify_parts(paths, records, 16, self.checksum)
    def test_traversal_filename_rejected(self):
        records, paths = self.split(); records[0]['filename'] = '../secret'
        with self.assertRaises(ValueError): t.verify_parts(paths, records, 16, self.checksum)
    def test_symlink_part_rejected(self):
        records, paths = self.split(); target = self.root / 'target'; target.write_bytes(paths[0].read_bytes()); paths[0].unlink(); paths[0].symlink_to(target)
        with self.assertRaises(ValueError): t.verify_parts(paths, records, 16, self.checksum)
    def test_output_never_overwritten(self):
        self.split()
        with self.assertRaises(FileExistsError): self.split()
    def test_signed_azure_host_accepted(self):
        url = 'https://productionresultssa1.blob.core.windows.net/actions-results/a?sig=opaque'
        self.assertEqual(t.checked_signed_url(url), url)
    def test_unsafe_redirects_rejected(self):
        for url in ('http://productionresultssa1.blob.core.windows.net/a?sig=x', 'https://evil.example/a?sig=x', 'https://productionresultssa1.blob.core.windows.net.evil.example/a?sig=x', 'https://user:password@productionresultssa1.blob.core.windows.net/a?sig=x', 'https://productionresultssa1.blob.core.windows.net:444/a?sig=x', 'https://productionresultssa1.blob.core.windows.net/../a?sig=x', 'https://productionresultssa1.blob.core.windows.net/a', 'https://productionresultssa1.blob.core.windows.net/a?sig=x#fragment'):
            with self.subTest(url=url), self.assertRaises(ValueError): t.checked_signed_url(url)
    def test_no_token_forwarded_to_signed_storage(self):
        opener = FakeOpener('https://productionresultssa1.blob.core.windows.net/actions-results/a?sig=opaque')
        api = t.ReadOnlyGitHub('test-ephemeral-token', opener)
        with self.assertRaises(ValueError): api.download(self.root / 'download')  # Tiny payload fails fixed real hash/size.
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(opener.requests[0].get_header('Authorization'), 'Bearer test-ephemeral-token')
        self.assertIsNone(opener.requests[1].get_header('Authorization')); self.assertIsNone(opener.requests[1].get_header('Cookie'))
        self.assertEqual(set(opener.requests[1].headers), {'User-agent'})
        self.assertTrue(all(x.get_method() == 'GET' for x in opener.requests))
    def test_unsafe_redirect_stops_before_unauthenticated_request(self):
        opener = FakeOpener('https://evil.example/a?sig=x'); api = t.ReadOnlyGitHub('token', opener)
        with self.assertRaises(ValueError): api.download(self.root / 'download')
        self.assertEqual(len(opener.requests), 1)
    def test_api_paths_are_exact_read_only_allowlist(self):
        api = t.ReadOnlyGitHub('token', FakeOpener(''))
        for path in ('https://evil.example', '/releases', '/actions/runs/1', f'/actions/artifacts/{t.ARTIFACT}?token=x'):
            with self.assertRaises(ValueError): api.get(path)
    def test_redirect_handler_never_follows(self): self.assertIsNone(t.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.example'))
    def identity(self):
        run = {'id': t.RUN, 'run_attempt': t.ATTEMPT, 'repository': {'id': t.REPO_ID, 'full_name': t.REPO}, 'head_repository': {'id': t.REPO_ID, 'full_name': t.REPO}, 'head_sha': t.F, 'head_branch': t.SOURCE_BRANCH, 'path': t.SOURCE_WORKFLOW, 'event': 'push', 'status': 'completed', 'conclusion': 'success'}
        artifact = {'id': t.ARTIFACT, 'name': t.ARTIFACT_NAME, 'expired': False, 'size_in_bytes': t.BYTES, 'digest': 'sha256:' + t.SHA256, 'workflow_run': {'id': t.RUN, 'head_sha': t.F, 'head_branch': t.SOURCE_BRANCH, 'repository_id': t.REPO_ID, 'head_repository_id': t.REPO_ID}, 'archive_download_url': t.API + f'/actions/artifacts/{t.ARTIFACT}/zip'}
        return run, artifact
    def test_exact_successful_identity(self): t.check_identity(*self.identity())
    def test_failed_or_rerun_identity_rejected(self):
        for key, value in [('conclusion', 'failure'), ('run_attempt', 2), ('head_sha', '0' * 40), ('event', 'pull_request')]:
            run, artifact = self.identity(); run[key] = value
            with self.assertRaises(ValueError): t.check_identity(run, artifact)
    def test_expired_or_replaced_artifact_rejected(self):
        for key, value in [('expired', True), ('id', 1), ('size_in_bytes', 1), ('digest', 'sha256:' + '0' * 64)]:
            run, artifact = self.identity(); artifact[key] = value
            with self.assertRaises(ValueError): t.check_identity(run, artifact)
    def test_production_size_is_exactly_three_under400_mib_parts(self):
        self.assertEqual((t.BYTES + t.PART_BYTES - 1) // t.PART_BYTES, 3)
        self.assertLess(t.PART_BYTES, 400 * 1024 * 1024)


if __name__ == '__main__': unittest.main()
