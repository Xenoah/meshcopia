import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import common as c
import verify as v


class VerificationTests(unittest.TestCase):
    def setUp(self):
        notice = {'filename': 'LICENSE.txt', 'text': 'notice\n', 'bytes': 7, 'sha256': c.sha(b'notice\n')}
        source_files = [{'name': 'asset.glb', 'bytes': 3, 'sha256': c.sha(b'raw')}]
        rows = [{'id': f'asset-{i:03}', 'version': '1.0.0', 'kind': 'model' if i < 137 else 'texture', 'status': 'public', 'metadataSha256': 'a' * 64, 'sourceFiles': copy.deepcopy(source_files), 'notice': copy.deepcopy(notice)} for i in range(173)]
        self.source = {'schemaVersion': 1, 'sourceCommit': c.BASE, 'cohort': 'published173', 'assets': rows}
        self.expected = {'schemaVersion': 1, 'reviewStatus': 'final-reviewed', 'sourceCommit': c.BASE, 'cohort': 'published173', 'sourceInventorySha256': c.sha(c.canonical(self.source)), 'packagerSha256': 'b' * 64, 'runtimeSha256': 'c' * 64,
                         'assets': [{'id': r['id'], 'filename': r['id'] + '-1.0.0-minimal-1.0.0.zip', 'archiveBytes': 3, 'archiveSha256': c.sha(b'zip'), 'noticeSha256': notice['sha256']} for r in rows]}

    def check(self):
        raw = c.canonical(self.source); self.expected['sourceInventorySha256'] = c.sha(raw)
        return c.check_manifests(self.source, self.expected, raw)

    def test_exact_repair_parent_and_paths(self):
        delta = ''.join('M\0' + p + '\0' for p in sorted(v.REPAIR_PATHS)).encode()
        with patch.object(v, 'git', side_effect=[v.REPAIR_PARENT.encode(), c.BASE.encode(), delta]):
            v.check_lineage(Path('.'), '7' * 40)
    def test_repair_cannot_change_expectations(self):
        paths = (v.REPAIR_PATHS - {'docs/minimal-verification/README.md'}) | {'docs/minimal-verification/expected173.json'}
        delta = ''.join('M\0' + p + '\0' for p in sorted(paths)).encode()
        with patch.object(v, 'git', side_effect=[v.REPAIR_PARENT.encode(), c.BASE.encode(), delta]):
            with self.assertRaisesRegex(ValueError, 'exact reviewed paths'): v.check_lineage(Path('.'), '7' * 40)
    def test_repair_parent_must_itself_follow_baseline(self):
        with patch.object(v, 'git', side_effect=[v.REPAIR_PARENT.encode(), b'8' * 40]):
            with self.assertRaisesRegex(ValueError, 'lineage'): v.check_lineage(Path('.'), '7' * 40)

    def test_valid_exact_173_contract(self): self.assertEqual(len(self.check()), 173)
    def test_pending_never_verifies(self):
        self.expected['reviewStatus'] = 'pending-review'
        with self.assertRaises(ValueError): self.check()
    def test_wrong_base_blocked(self):
        self.source['sourceCommit'] = '0' * 40
        with self.assertRaises(ValueError): self.check()
    def test_new_cohort_blocked(self):
        self.source['cohort'] = 'new232'
        with self.assertRaises(ValueError): self.check()
    def test_model_texture_count_enforced(self):
        self.source['assets'][0]['kind'] = 'texture'
        with self.assertRaises(ValueError): self.check()
    def test_duplicate_ids(self):
        self.source['assets'][1]['id'] = self.source['assets'][0]['id']
        with self.assertRaises(ValueError): self.check()
    def test_hidden_asset(self):
        self.source['assets'][0]['status'] = 'hidden'
        with self.assertRaises(ValueError): self.check()
    def test_original_asset_version_preserved(self):
        self.source['assets'][0]['version'] = '2.0.0'
        with self.assertRaises(ValueError): self.check()
    def test_notice_hash(self):
        self.source['assets'][0]['notice']['text'] += 'x'
        with self.assertRaises(ValueError): self.check()
    def test_one_short_license(self):
        self.source['assets'][0]['notice']['filename'] = 'ATTRIBUTION.txt'
        with self.assertRaises(ValueError): self.check()
    def test_notice_expected_binding(self):
        self.expected['assets'][0]['noticeSha256'] = '0' * 64
        with self.assertRaises(ValueError): self.check()
    def test_extra_source_traversal(self):
        self.source['assets'][0]['sourceFiles'][0]['name'] = '../secret'
        with self.assertRaises(ValueError): self.check()
    def test_nonminimal_archive_name(self):
        self.expected['assets'][0]['filename'] = 'full.zip'
        with self.assertRaises(ValueError): self.check()
    def test_public_inventory_has_only_binding_fields(self):
        item = c.package_binding(self.source['assets'][0], self.expected['assets'][0])
        self.assertEqual(set(item), {'id', 'version', 'kind', 'filename', 'bytes', 'sha256', 'url', 'sourceFiles', 'notice'})
        self.assertTrue(item['url'].startswith(f'https://github.com/{c.REPO}/releases/download/{c.TAG}/'))
        self.assertNotIn('qa', c.canonical(item).decode())
    def test_nonbaseline_parent_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(v, 'git', side_effect=[b'7' * 40, b'false', b'', b'8' * 40]):
            with self.assertRaisesRegex(ValueError, 'directly follow baseline'):
                v.preflight(Path(directory), self.source, self.expected, Path(directory), '7' * 40)
    def test_extra_f_path_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(v, 'git', side_effect=[b'7' * 40, b'false', b'', c.BASE.encode()]):
            docs = Path(directory); (docs / 'allowed-f-paths.json').write_bytes(c.canonical(['docs/fbx-verification/old-details.json']))
            with self.assertRaisesRegex(ValueError, 'path allowlist'):
                v.preflight(docs, self.source, self.expected, docs, '7' * 40)


if __name__ == '__main__': unittest.main()
