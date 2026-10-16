import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import common as c
import verify as v


class MinimalFTests(unittest.TestCase):
    def setUp(self):
        self.docs = c.ROOT / 'docs/fbx-minimal-verification'
        self.source = c.read(self.docs / 'source137.json')
        self.expected = c.read(self.docs / 'expected137.json')

    def check(self):
        raw = c.canonical(self.source); self.expected['sourceInventorySha256'] = c.sha(raw)
        return c.check_manifests(self.source, self.expected, raw)

    def test_exact_reviewed_contract(self): self.assertEqual(len(self.check()), 137)
    def test_duplicate_source_ids_rejected(self):
        self.source['models'][1]['id'] = self.source['models'][0]['id']
        with self.assertRaises(ValueError): self.check()
    def test_duplicate_expected_ids_rejected(self):
        self.expected['models'][1]['id'] = self.expected['models'][0]['id']
        with self.assertRaises(ValueError): self.check()
    def test_pending_review_rejected(self):
        self.expected['reviewStatus'] = 'pending'
        with self.assertRaises(ValueError): self.check()
    def test_source_inventory_hash_rejected(self):
        with self.assertRaises(ValueError): c.check_manifests(self.source, self.expected, b'{}\n')
    def test_v3_recipe_rejected(self):
        self.expected['pipelineSha256'] = 'a' * 64
        with self.assertRaises(ValueError): self.check()
    def test_legacy_eight_entry_metadata_rejected(self):
        self.expected['models'][0]['packageInputs'] = {'README.md': 'a' * 64}
        with self.assertRaises(ValueError): self.check()
    def test_new232_cohort_rejected(self):
        self.source['cohort'] = 'new232'
        with self.assertRaises(ValueError): self.check()
    def test_cross_model_source_rejected(self):
        self.source['models'][0]['sourceGLB'] = self.source['models'][1]['sourceGLB']
        with self.assertRaises(ValueError): self.check()
    def test_traversal_path_rejected(self):
        self.source['models'][0]['sourceGLB'] = '../asset.glb'
        with self.assertRaises(ValueError): self.check()
    def test_legacy_filename_rejected(self):
        self.expected['models'][0]['filename'] = 'atelier-lamp-fbx-v4.zip'
        with self.assertRaises(ValueError): self.check()
    def test_boolean_byte_count_rejected(self):
        self.expected['models'][0]['fbxBytes'] = True
        with self.assertRaises(ValueError): self.check()
    def test_oversize_byte_count_rejected(self):
        self.expected['models'][0]['fbxBytes'] = 96 * 1024 * 1024
        with self.assertRaises(ValueError): self.check()
    def test_source_hash_binding_rejected(self):
        self.expected['models'][0]['sourceGlbSha256'] = '0' * 64
        with self.assertRaises(ValueError): self.check()
    def test_wrong_license_name_rejected(self):
        self.source['models'][0]['notice']['filename'] = 'ATTRIBUTION.txt'
        with self.assertRaises(ValueError): self.check()
    def test_notice_bytes_mutation_rejected(self):
        self.source['models'][0]['notice']['text'] += 'Different\n'
        with self.assertRaises(ValueError): self.check()
    def test_missing_conversion_notice_rejected(self):
        note = self.source['models'][0]['notice']; note['text'] = note['text'].replace(c.CONVERSION_NOTICE, '')
        note['bytes'] = len(note['text'].encode()); note['sha256'] = c.sha(note['text'].encode()); self.expected['models'][0]['noticeSha256'] = note['sha256']
        with self.assertRaises(ValueError): self.check()
    def test_unexpected_notice_field_rejected(self):
        self.source['models'][0]['notice']['qa'] = 'details'
        with self.assertRaises(ValueError): self.check()
    def test_allowlist_no_old_fixed_inputs_or_publication(self):
        paths = c.fixed_paths()
        self.assertEqual(set(c.read(self.docs / 'allowed-f-paths.json')), paths)
        self.assertFalse(any('package-inputs' in p or 'approval' in p or 'release' in p for p in paths))
        self.assertLess(len(paths), 30)
    def test_runtime_support_hashes_match_frozen_files(self):
        runtime = c.read(self.docs / 'runtime.json')
        for name, checksum in runtime['recipe'].items(): self.assertEqual(c.file_sha(c.ROOT / 'scripts/fbx-verification' / name), checksum)
        for path, checksum in runtime['supportFiles'].items(): self.assertEqual(c.file_sha(c.ROOT / path), checksum)
    def test_public_binding_omits_qa_and_local_metadata(self):
        row = c.model_binding(self.source['models'][0], self.expected['models'][0])
        self.assertEqual(set(row), {'id', 'version', 'sourceGlbSha256', 'fbx', 'archive', 'notice'})
        self.assertNotIn('qa', c.canonical(row).decode().lower())
    def test_wrong_direct_parent_rejected(self):
        def fake_git(repo, *args):
            if args == ('rev-parse', 'HEAD'): return b'7' * 40
            if args == ('rev-parse', '--is-shallow-repository'): return b'false'
            if args[0] == 'config': raise c.subprocess.CalledProcessError(1, args)
            if args == ('rev-parse', '--git-path', 'info/grafts'): return b'info/grafts'
            if args == ('show', '-s', '--format=%P', '7' * 40): return b'8' * 40
            self.fail(str(args))
        with tempfile.TemporaryDirectory() as directory, patch.object(v, 'git', side_effect=fake_git):
            with self.assertRaisesRegex(ValueError, 'directly follow'): v.preflight(Path(directory), self.source, self.expected, self.docs, '7' * 40)
    def test_public_artifact_extra_qa_rejected(self):
        bindings = [c.model_binding(s, e) for s, e in zip(self.source['models'], self.expected['models'])]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'fbx-minimal-inventory.json').touch()
            for row in bindings:
                for key in ('fbx', 'archive'): (root / row[key]['filename']).touch()
            c.check_payload_names(root, bindings)
            (root / 'qa.json').touch()
            with self.assertRaises(ValueError): c.check_payload_names(root, bindings)
    def test_only_verified_zip_modes_are_changed(self):
        bindings = [c.model_binding(s, e) for s, e in zip(self.source['models'], self.expected['models'])]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'fbx-minimal-inventory.json').touch()
            for row in bindings:
                for key in ('fbx', 'archive'):
                    path = root / row[key]['filename']; path.write_bytes(b'verified'); path.chmod(0o600)
            c.readable_verified_archives(root, bindings)
            for row in bindings:
                self.assertEqual((root / row['archive']['filename']).stat().st_mode & 0o777, 0o644)
                self.assertEqual((root / row['fbx']['filename']).stat().st_mode & 0o777, 0o600)
                self.assertEqual((root / row['archive']['filename']).read_bytes(), b'verified')
    def test_extra_file_blocks_permission_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / 'secret.zip'; path.write_bytes(b'secret'); path.chmod(0o600)
            with self.assertRaises(ValueError): c.readable_verified_archives(root, [])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
    def receipt(self):
        source = self.source['models'][0]; exp = self.expected['models'][0]
        return {'id': source['id'], 'kind': 'fbx', 'filename': exp['filename'], 'archiveBytes': exp['archiveBytes'], 'archiveSha256': exp['archiveSha256'], 'notice': source['notice'], 'conversionPipelineSha256': c.PIPELINE,
                'entries': [{'name': 'LICENSE.txt', 'bytes': source['notice']['bytes'], 'sha256': source['notice']['sha256']}, {'name': source['id'] + '.fbx', 'bytes': exp['fbxBytes'], 'sha256': exp['fbxSha256']}],
                'verification': {'entryCount': 2, 'exactAllowlist': True, 'payloadHashesVerified': True, 'cleanExtractionVerified': True, 'dependencyClosureVerified': True}}
    def test_exact_two_entry_receipt(self): v.check_receipt(self.receipt(), self.source['models'][0], self.expected['models'][0])
    def test_receipt_extra_readme_rejected(self):
        receipt = self.receipt(); receipt['entries'].append({'name': 'README.md', 'bytes': 3, 'sha256': 'a' * 64})
        with self.assertRaises(ValueError): v.check_receipt(receipt, self.source['models'][0], self.expected['models'][0])
    def test_receipt_changed_payload_rejected(self):
        receipt = self.receipt(); receipt['entries'][1]['sha256'] = 'b' * 64
        with self.assertRaises(ValueError): v.check_receipt(receipt, self.source['models'][0], self.expected['models'][0])
    def test_receipt_extraction_not_verified_rejected(self):
        receipt = self.receipt(); receipt['verification']['cleanExtractionVerified'] = False
        with self.assertRaises(ValueError): v.check_receipt(receipt, self.source['models'][0], self.expected['models'][0])


if __name__ == '__main__': unittest.main()
