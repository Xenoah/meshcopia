import copy
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import minimal_packages as mp
from minimal_notices import baseline_notices, make_notice


def glb(document=None):
    data = json.dumps(document or {'asset': {'version': '2.0'}, 'scenes': []}).encode()
    data += b' ' * (-len(data) % 4)
    return struct.pack('<4sIII4s', b'glTF', 2, 20 + len(data), len(data), b'JSON') + data


class MinimalPackages(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.asset = self.root / 'test-model'
        self.source = self.asset / 'source'
        self.source.mkdir(parents=True)
        self.meta = {'id': 'test-model', 'version': '1.0.0', 'type': 'model', 'status': 'public',
                     'license': 'CC-BY-4.0', 'author': 'Xenoah', 'titleEn': 'Test model',
                     'created': '2026-10-14', 'preview': 'test-model.glb',
                     'provenance': {'sourceUrl': 'https://example.com/original', 'changes': 'Original meshes extracted; UVs retained.'}}
        self.save_metadata()
        (self.source / 'test-model.glb').write_bytes(glb())
        self.notice = self.root / 'license.txt'
        previous = baseline_notices(self.meta)
        self.notice.write_text(make_notice(self.meta, *previous), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def save_metadata(self):
        (self.asset / 'asset.json').write_text(json.dumps(self.meta))

    def plan(self, **kwargs):
        return mp.make_plan(self.asset, self.notice, **kwargs)

    def archive(self, plan=None):
        buffer = io.BytesIO()
        mp.write_archive(buffer, plan or self.plan())
        return buffer.getvalue()

    def test_model_rootless_and_notice_only(self):
        (self.source / 'README.md').write_text('must stay out')
        (self.source / 'roundtrip-report.json').write_text('{}')
        (self.source / 'generate.py').write_text('not distributable')
        (self.asset / 'preview.webp').write_bytes(b'preview')
        plan = self.plan()
        self.assertEqual([r['name'] for r in plan['entries']], ['LICENSE.txt', 'test-model.glb'])
        self.assertEqual(plan['filename'], 'test-model-1.0.0-minimal-1.0.0.zip')
        result = mp.verify_extracted_package(io.BytesIO(self.archive(plan)), plan)
        self.assertTrue(result['cleanExtractionVerified'])
        self.assertFalse(result['applicationImportTested'])

    def test_texture_maps_only_flattened(self):
        self.meta.update(type='texture', maps={'baseColor': 'maps/albedo.png', 'normal': 'maps/normal.png'})
        self.save_metadata()
        (self.source / 'maps').mkdir()
        for name in ['albedo.png', 'normal.png', 'not-needed.png']:
            (self.source / 'maps' / name).write_bytes(b'unchanged original PNG ' + name.encode())
        plan = self.plan()
        self.assertEqual([r['name'] for r in plan['entries']], ['LICENSE.txt', 'albedo.png', 'normal.png'])
        self.assertTrue(mp.verify_extracted_package(io.BytesIO(self.archive(plan)), plan)['dependencyClosureVerified'])

    def test_obj_mtl_texture_closure_preserves_required_folders(self):
        (self.source / 'test-model.glb').unlink()
        (self.source / 'unnecessary').mkdir()
        (self.source / 'unnecessary/materials').mkdir()
        (self.source / 'unnecessary/materials/images').mkdir()
        (self.source / 'unnecessary/a.obj').write_text('mtllib materials/a.mtl\nv 0 0 0\n')
        (self.source / 'unnecessary/materials/a.mtl').write_text('newmtl a\nmap_Kd -s 1 1 1 images/color.png\n')
        (self.source / 'unnecessary/materials/images/color.png').write_bytes(b'original pixel bytes')
        self.meta['preview'] = 'unnecessary/a.obj'
        self.save_metadata()
        plan = self.plan()
        self.assertEqual([r['name'] for r in plan['entries']], ['LICENSE.txt', 'a.obj', 'materials/a.mtl', 'materials/images/color.png'])
        self.assertTrue(mp.verify_extracted_package(io.BytesIO(self.archive(plan)), plan)['dependencyClosureVerified'])

    def test_gltf_external_buffer_and_image_closure(self):
        (self.source / 'test-model.glb').unlink()
        (self.source / 'test.gltf').write_text(json.dumps({'asset': {'version': '2.0'}, 'buffers': [{'uri': 'mesh.bin'}], 'images': [{'uri': 'image.png'}]}))
        (self.source / 'mesh.bin').write_bytes(b'123456')
        (self.source / 'image.png').write_bytes(b'pixel bytes')
        self.meta['preview'] = 'test.gltf'
        self.save_metadata()
        self.assertEqual(len(self.plan()['entries']), 4)

    def test_deterministic_bytes_independent_of_mtime(self):
        first = self.archive()
        os.utime(self.source / 'test-model.glb', (1_000_000, 1_000_000))
        self.assertEqual(first, self.archive())

    def test_input_change_invalidates_plan(self):
        plan = self.plan()
        (self.source / 'test-model.glb').write_bytes(glb({'asset': {'version': '2.0'}, 'nodes': []}))
        with self.assertRaises(mp.PackageError):
            self.archive(plan)

    def test_notice_change_invalidates_plan(self):
        plan = self.plan()
        with self.notice.open('a') as f:
            f.write('Extra notice.\n')
        with self.assertRaises(mp.PackageError):
            mp.verify_archive(io.BytesIO(b'not a zip'), plan)

    def test_rejects_missing_dependency(self):
        (self.source / 'test-model.glb').write_bytes(glb({'asset': {'version': '2.0'}, 'images': [{'uri': 'missing.png'}]}))
        with self.assertRaises((mp.PackageError, FileNotFoundError)):
            self.plan()

    def test_rejects_unsafe_dependency_uris(self):
        for name in ('../outside.png', '/tmp/a.png', 'C:/image.png', 'https://example.com/a.png', 'images\\a.png', '%2e%2e/a.png', 'a.png?x=1'):
            with self.subTest(name=name):
                (self.source / 'test-model.glb').write_bytes(glb({'asset': {'version': '2.0'}, 'images': [{'uri': name}]}))
                with self.assertRaises(mp.PackageError):
                    self.plan()

    def test_rejects_ambiguous_duplicate_json_keys(self):
        raw = b'{"asset":{"version":"2.0"},"images":[],"images":[{"uri":"outside.png"}]}'
        raw += b' ' * (-len(raw) % 4)
        (self.source / 'test-model.glb').write_bytes(struct.pack('<4sIII4s', b'glTF', 2, 20 + len(raw), len(raw), b'JSON') + raw)
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_symlink_even_if_excluded(self):
        (self.source / 'unneeded.py').symlink_to(self.notice)
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_symlink_source_root(self):
        self.source.rename(self.asset / 'original')
        self.source.symlink_to(self.asset / 'original', target_is_directory=True)
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_casefold_collision(self):
        (self.source / 'Test-Model.glb').write_bytes(glb())
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_flattened_collision(self):
        self.meta.update(type='texture', maps={'baseColor': 'one/a.png', 'normal': 'two/a.png'})
        self.save_metadata()
        for name in ('one', 'two'):
            (self.source / name).mkdir()
            (self.source / name / 'a.png').write_bytes(name.encode())
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_reserved_portable_paths(self):
        for name in ('CON.png', 'LPT1', 'a.', 'a ', 'a//b', 'a/../b', 'a\x00b', 'a\\b', '/a', 'a:b', 'a#b', 'a%20b'):
            with self.subTest(name=name), self.assertRaises(mp.PackageError):
                mp.safe_relative(name)

    def test_rejects_scripts_as_declared_map(self):
        self.meta.update(type='texture', maps={'baseColor': 'generator.py'})
        self.save_metadata()
        (self.source / 'generator.py').write_text('script')
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_scripts_as_model_dependency(self):
        (self.source / 'test-model.glb').write_bytes(glb({'asset': {'version': '2.0'}, 'extensions': {'X': {'uri': 'generator.py'}}}))
        (self.source / 'generator.py').write_text('script')
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_rejects_extra_archive_files(self):
        plan = self.plan()
        for extra in ('README.md', 'ATTRIBUTION.txt', 'asset.json', 'FILES.sha256', 'preview.webp', 'qa/report.json', 'production.py', '../escape'):
            with self.subTest(extra=extra):
                buf = io.BytesIO(self.archive(plan))
                with zipfile.ZipFile(buf, 'a') as z:
                    z.writestr(extra, b'extra')
                with self.assertRaises(mp.PackageError):
                    mp.verify_archive(buf, plan)

    def test_rejects_trailing_junk_or_prefix(self):
        plan = self.plan()
        data = self.archive(plan)
        for changed in (data + b'extra', b'prefix' + data):
            with self.assertRaises(mp.PackageError):
                mp.verify_archive(io.BytesIO(changed), plan)

    def test_rejects_forged_extra_plan(self):
        plan = self.plan()
        plan['entries'].append({'name': 'README.md', **mp.record(self.notice)})
        with self.assertRaises(mp.PackageError):
            self.archive(plan)

    def test_rejects_unpinned_compressor(self):
        with mock.patch.object(mp.zlib, 'ZLIB_RUNTIME_VERSION', 'future'), self.assertRaises(mp.PackageError):
            self.archive()

    def test_discard_retains_only_receipt(self):
        plan = self.plan()
        receipt_path = self.root / 'receipt.json'
        receipt = mp.package(plan, receipt_path=receipt_path, temporary_directory=self.root)
        self.assertFalse(receipt['retainedArchive'])
        self.assertEqual(list(self.root.glob('*.zip')), [])
        self.assertEqual(list(self.root.glob('minimal-extracted-*')), [])
        self.assertEqual(receipt['notice']['text'], self.notice.read_text())
        self.assertEqual(len(receipt['sourceFiles']), 1)

    def test_existing_archive_and_receipt_never_overwritten(self):
        plan = self.plan()
        output = self.root / plan['filename']
        output.write_bytes(b'old immutable archive')
        with self.assertRaises(mp.PackageError):
            mp.package(plan, output=output)
        self.assertEqual(output.read_bytes(), b'old immutable archive')
        receipt = self.root / 'receipt.json'
        receipt.write_bytes(b'old receipt')
        with self.assertRaises(mp.PackageError):
            mp.package(plan, receipt_path=receipt)

    def test_wrong_output_filename_rejected(self):
        with self.assertRaises(mp.PackageError):
            mp.package(self.plan(), output=self.root / 'old-name.zip')

    def test_drafts_explicit_and_local_only(self):
        self.meta['status'] = 'draft'
        self.save_metadata()
        with self.assertRaises(mp.PackageError):
            self.plan()
        self.assertTrue(self.plan(allow_draft=True)['inputs']['allowDraftPreparation'])

    def test_fbx_exact_two_entries_with_pinned_report(self):
        fbx = self.root / 'test-model.fbx'
        fbx.write_bytes(b'Kaydara FBX Binary  \x00\x1a\x00' + b'canonical binary')
        digest = hashlib.sha256(fbx.read_bytes()).hexdigest()
        report = self.root / 'report.json'
        recipe = {'converter.py': 'a' * 64}
        pipeline = hashlib.sha256(json.dumps(recipe, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self.notice.open('a') as f:
            f.write('Additional changes: Converted unchanged source GLB geometry to FBX, with documented compatible material/texture derivatives.\n')
        report.write_text(json.dumps({'id': 'test-model', 'passed': True, 'fbxSha256': digest, 'fbxBytes': fbx.stat().st_size,
                                      'recipeSha256': recipe, 'sourceGlbSha256': mp.hash_file(self.source / 'test-model.glb')[1],
                                      'container': {'selfContainedImages': True, 'noWorkspacePathInBinary': True}}))
        plan = self.plan(fbx_path=fbx, fbx_sha256=digest, pipeline_sha256=pipeline, fbx_report=report)
        self.assertEqual([r['name'] for r in plan['entries']], ['LICENSE.txt', 'test-model.fbx'])
        self.assertEqual(plan['filename'], 'test-model-1.0.0-fbx-minimal-1.0.0.zip')
        self.assertTrue(mp.verify_archive(io.BytesIO(self.archive(plan)), plan)['payloadHashesVerified'])
        with self.assertRaises(mp.PackageError):
            self.plan(fbx_path=fbx, fbx_sha256=digest, pipeline_sha256='b' * 64, fbx_report=report)
        with self.assertRaises(mp.PackageError):
            self.plan(fbx_path=fbx, fbx_sha256='b' * 64, pipeline_sha256=pipeline, fbx_report=report)

    def test_notice_cannot_bypass_required_legal_fields(self):
        original = self.notice.read_text()
        for prefix in ('Copyright ', 'Source: ', 'Original source: ', 'Provided as-is', 'Changes: '):
            with self.subTest(prefix=prefix):
                self.notice.write_text('\n'.join(line for line in original.splitlines() if not line.startswith(prefix)) + '\n')
                with self.assertRaises(mp.PackageError):
                    self.plan()
        self.notice.write_text(original)

    def test_unknown_model_dependency_formats_fail_closed(self):
        (self.source / 'unknown.fbx').write_bytes(b'no implicit dependency assumption')
        with self.assertRaises(mp.PackageError):
            self.plan()

    def test_notice_preserves_actual_credit_changes_and_copyright(self):
        previous = baseline_notices(self.meta)
        text = make_notice(self.meta, *previous, fbx_attribution='Changes: Converted unchanged source GLB geometry to FBX, with documented compatible material/texture derivatives.\nOriginal GLB SHA-256: abc\n')
        self.assertIn('Copyright (c) 2026 Xenoah', text)
        self.assertIn('Test model by Xenoah / Meshcopia', text)
        self.assertIn('Original meshes extracted; UVs retained.', text)
        self.assertIn('compatible material/texture derivatives', text)
        self.assertIn('https://example.com/original', text)
        self.assertNotIn('SHA-256', text)
        self.assertNotIn('asset.json', text)

    def test_notice_keeps_distinct_previous_changes(self):
        license_text, attribution = baseline_notices(self.meta)
        attribution = attribution.replace(self.meta['provenance']['changes'], 'Previous modification.')
        text = make_notice(self.meta, license_text, attribution)
        self.assertIn('Previous modification.', text)
        self.assertIn(self.meta['provenance']['changes'], text)

    def test_notice_rejects_missing_credit_or_wrong_source(self):
        license_text, attribution = baseline_notices(self.meta)
        for bad in (attribution.replace('/ Meshcopia', ''), attribution.replace('/test-model/', '/other/')):
            with self.assertRaises(mp.PackageError):
                make_notice(self.meta, license_text, bad)


if __name__ == '__main__':
    unittest.main()
