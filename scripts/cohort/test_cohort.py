"""Offline safeguards for the cohort manifests; no Blender, network or Git writes."""
import copy
import unittest
from common import *

META = {'id': 'city-test-object', 'type': 'model', 'title': 'テスト', 'titleEn': 'Test object', 'author': 'Claude',
        'license': 'CC-BY-4.0', 'version': '1.0.0', 'status': 'public', 'created': '2026-10-17', 'preview': 'city-test-object.glb',
        'provenance': {'method': 'x', 'tool': 'y', 'rights': 'z'}}


def row():
    ordinary, fbx = notice_texts(META)
    return {'id': 'city-test-object', 'version': '1.0.0', 'status': 'public', 'assetMetadata': 'content/assets/city-test-object/asset.json',
            'metadataSha256': 'a' * 64, 'sourceGLB': 'content/assets/city-test-object/source/city-test-object.glb', 'sourceSha256': 'b' * 64,
            'sourceBytes': 10, 'sourceFiles': [{'name': 'city-test-object.glb', 'bytes': 10, 'sha256': 'b' * 64}, {'name': 'city-test-object.stl', 'bytes': 5, 'sha256': 'c' * 64}],
            'stageCommit': 'd' * 40, 'notice': notice_record(ordinary), 'fbxNotice': notice_record(fbx)}


def source():
    return {'schemaVersion': 1, 'cohort': 'new-test', 'baseCommit': 'e' * 40, 'modelCount': 1, 'packageVersion': '1.0.0', 'pipelineSha256': PIPELINE, 'models': [row()]}


class CohortTests(unittest.TestCase):
    def test_notices_retain_author_detail_url_and_conversion(self):
        ordinary, fbx = notice_texts(META)
        for text in (ordinary, fbx):
            self.assertIn('Test object by Claude / Meshcopia', text)
            self.assertIn('Copyright (c) 2026 Claude', text)
            self.assertIn('Source: https://xenoah.github.io/meshcopia/assets/city-test-object/', text)
            self.assertIn('without warranties', text)
        self.assertIn(CONVERSION_NOTICE, fbx); self.assertNotIn(CONVERSION_NOTICE, ordinary)
        check_notice(notice_record(ordinary), META, False)
        with self.assertRaises(ValueError): check_notice(notice_record(ordinary), META, True)
        with self.assertRaises(ValueError): check_notice(notice_record(ordinary + 'extra\n'), META, False)

    def test_source_manifest_shape(self):
        check_source(source())
        for mutate in (lambda s: s.update(modelCount=2), lambda s: s['models'][0].update(status='draft'),
                       lambda s: s['models'][0].update(sourceGLB='content/assets/other/source/x.glb'),
                       lambda s: s['models'][0].update(extra=1), lambda s: s.update(pipelineSha256='0' * 64),
                       lambda s: s['models'][0]['sourceFiles'].reverse(), lambda s: s['models'][0].update(stageCommit='main'),
                       lambda s: s['models'][0]['sourceFiles'].pop(0), lambda s: s.update(cohort='Bad Name')):
            bad = source(); mutate(bad)
            with self.assertRaises(ValueError): check_source(bad)

    def test_expected_discovery_and_final(self):
        s = source(); b = canonical(s)
        e = {'schemaVersion': 1, 'reviewStatus': 'discovery', 'cohort': 'new-test', 'baseCommit': 'e' * 40, 'sourceInventorySha256': sha(b),
             'runtimeSha256': 'f' * 64, 'pipelineSha256': PIPELINE, 'packageVersion': '1.0.0', 'models': []}
        self.assertIsNone(check_expected(e, s, b, 'f' * 64))
        names = archive_names('city-test-object', '1.0.0')
        final = dict(e, reviewStatus='reproduced-final', models=[{'id': 'city-test-object', 'sourceGlbSha256': 'b' * 64,
                     **{k: {'filename': names[k], 'bytes': 7, 'sha256': '1' * 64} for k in ('fbx', 'fbxArchive', 'archive')}}])
        self.assertIn('city-test-object', check_expected(final, s, b, 'f' * 64))
        for mutate in (lambda x: x.update(reviewStatus='approved'), lambda x: x.update(sourceInventorySha256='0' * 64),
                       lambda x: x['models'][0]['fbx'].update(filename='x.fbx'), lambda x: x['models'][0].update(sourceGlbSha256='0' * 64),
                       lambda x: x.update(runtimeSha256='0' * 64), lambda x: x['models'].clear()):
            bad = copy.deepcopy(final); mutate(bad)
            with self.assertRaises(ValueError): check_expected(bad, s, b, 'f' * 64)
        with self.assertRaises(ValueError): check_expected(dict(e, models=final['models']), s, b, 'f' * 64)

    def test_payload_names_are_exact_and_collision_free(self):
        names = archive_names('city-test-object', '1.0.0')
        m = {k: {'filename': names[k]} for k in ('fbx', 'fbxArchive', 'archive')}
        self.assertEqual(payload_names([m]), {'cohort-inventory.json', 'city-test-object.fbx', 'city-test-object-1.0.0-fbx-minimal-1.0.0.zip', 'city-test-object-1.0.0-minimal-1.0.0.zip'})
        with self.assertRaises(ValueError): payload_names([m, m])


if __name__ == '__main__':
    unittest.main()
