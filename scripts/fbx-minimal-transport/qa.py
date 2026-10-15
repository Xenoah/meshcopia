"""Pure local, bounded verification of the exact separate internal FBX QA artifact.

No Blender invocation. Fresh imported packed-image materialization is attested by
an exact successful pinned F; raw report/container/CPU/measurements are rechecked.
"""
from pathlib import Path
import hashlib
import json
import stat
import sys
import tempfile
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'fbx-minimal-verification'))
import common as f
from verify_fbx_report import verify_report, public_cohort, CPU_BASELINE
from deterministic_fbx import PINNED_SOURCES

MAX_QA_TOTAL = 256 * 1024**2
MAX_JSON = 16 * 1024**2
MAX_PAYLOAD_FILE = 95 * 1024**2
CHUNK = 1024**2


def need(value, message): f.need(value, message)
def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path):
    need(path.is_file() and not path.is_symlink(), 'Expected regular file')
    with path.open('rb') as src: return hashlib.file_digest(src, 'sha256').hexdigest()


def json_bytes(data):
    def unique(items):
        result = {}
        for key, value in items:
            need(key not in result, 'Duplicate JSON key'); result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def stream_member(archive, info, target, expected_size=None, expected_sha=None):
    need(info.orig_filename == info.filename and not info.is_dir() and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG) and info.compress_type in (0, 8) and not info.flag_bits & 1, 'Unsafe artifact member')
    if expected_size is not None: need(info.file_size == expected_size, 'Artifact member size differs')
    digest = hashlib.sha256(); size = 0
    with archive.open(info) as src, target.open('xb') as dst:
        while block := src.read(CHUNK):
            size += len(block); need(size <= info.file_size, 'Expanded member exceeds size'); digest.update(block); dst.write(block)
    need(size == info.file_size, 'Truncated artifact member')
    if expected_sha is not None: need(digest.hexdigest() == expected_sha, 'Artifact member digest differs')


def qa_names(ids):
    return {'qa.json', 'runtime.json', 'pilot-gate.json'} | {identity + '/' + suffix for identity in ids for suffix in ('receipt.json', 'fresh/roundtrip-report.json', 'fresh/materialized-imported-images.json')}


def extract_qa(archive_path, approval, ids, destination):
    need(file_sha(archive_path) == approval['qaArtifactSha256'], 'Internal QA artifact digest differs')
    allowed = qa_names(ids)
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist(); names = [i.filename for i in infos]
        need(len(infos) == len(allowed) == 414 and set(names) == allowed and len(set(n.casefold() for n in names)) == len(names), 'Internal QA path set differs')
        need(sum(i.file_size for i in infos) <= MAX_QA_TOTAL, 'Internal QA too large')
        for info in infos:
            f.packages.safe_relative(info.filename)
            need(0 < info.file_size <= MAX_JSON, 'Internal JSON size invalid')
            target = destination / info.filename; target.parent.mkdir(parents=True, exist_ok=True)
            stream_member(archive, info, target)
    for name, key in (('qa.json', 'qaSummarySha256'), ('runtime.json', 'qaRuntimeSha256'), ('pilot-gate.json', 'qaPilotGateSha256')):
        need(file_sha(destination / name) == approval[key], 'Internal QA component digest differs: ' + name)


def check_runtime(actual, runtime):
    f.exact(actual, 'blender blenderBuildHash blenderBinarySha256 python numpy zlib platform', 'actual runtime')
    need(all(type(v) is str and v for v in actual.values()), 'Runtime values must be strings')
    for key in ('blender', 'numpy', 'zlib'): need(actual[key] == runtime['versions'][key], 'Actual runtime version differs: ' + key)
    need(actual['python'].split()[0] == runtime['versions']['python'] and actual['blenderBinarySha256'] == runtime['binarySha256'], 'Actual interpreter/Blender differs')
    need(actual['platform'].startswith('Linux-') and actual['platform'].endswith('-x86_64-with-glibc' + runtime['versions']['glibc']), 'Actual platform/libc differs')


def check_verification(v, payload_bytes):
    f.exact(v, 'entryCount payloadBytes exactAllowlist payloadHashesVerified cleanExtractionVerified dependencyClosureVerified applicationImportTested', 'package verification')
    need(type(v['entryCount']) is int and v['entryCount'] == 2 and type(v['payloadBytes']) is int and v['payloadBytes'] == payload_bytes, 'Package byte/count proof differs')
    need(all(v[k] is True for k in ('exactAllowlist', 'payloadHashesVerified', 'cleanExtractionVerified', 'dependencyClosureVerified')) and v['applicationImportTested'] is False, 'Strict package proof/claim differs')


def check_materialization(value, report, runtime):
    f.exact(value, 'images count noPixelReencoding importerPackedBytesMaterializedByValidationWrapper wrapperSha256', 'materialization proof')
    need(value['noPixelReencoding'] is True and value['importerPackedBytesMaterializedByValidationWrapper'] is True, 'Fresh packed-image materialization missing')
    need(value['wrapperSha256'] == runtime['supportFiles']['scripts/fbx-verification/materialize_imported_images.py'], 'Image wrapper digest differs')
    need(type(value['images']) is list and type(value['count']) is int and value['count'] == len(value['images']), 'Materialized image count differs')
    expected = {row['relativeFilename']: row for row in report['container']['embeddedImages']}
    actual = {}
    for row in value['images']:
        f.exact(row, 'relativePath bytes sha256 source', 'materialized image')
        need(row['relativePath'] not in actual and row['source'] == 'actual-clean-import-bpy-packed-image', 'Duplicate/non-imported materialized image')
        f.packages.safe_relative(row['relativePath']); f.digest(row['sha256']); f.size(row['bytes'])
        actual[row['relativePath']] = row
    need(set(actual) == set(expected), 'Materialized/embedded image closure differs')
    for name, row in actual.items():
        need(row['bytes'] == expected[name]['embeddedBytes'] and row['sha256'] == expected[name]['sha256'], 'Materialized image bytes differ')


def verify_model(identity, row, exp, root, runtime, actual_runtime, projected, package_proof, fbx_bytes, repo):
    path = root / identity / 'fresh/roundtrip-report.json'; report_raw = path.read_bytes(); report = json_bytes(report_raw)
    f.exact(package_proof, 'id reviewedLocalQaSha256 freshCiQaSha256 archiveSha256 verification', 'package proof')
    need(package_proof['id'] == identity and package_proof['reviewedLocalQaSha256'] == exp['reviewedQaSha256'] and package_proof['freshCiQaSha256'] == sha(report_raw) and package_proof['archiveSha256'] == exp['archiveSha256'], 'Fresh report/package binding differs')
    need(report['passed'] is True and report['allImportedImagesInsideCleanReimport'] is True, 'Fresh report did not pass live image closure')
    source_path = f.packages.regular_file(repo / row['sourceGLB'])
    need(source_path.stat().st_size == row['sourceBytes'] and file_sha(source_path) == row['sourceSha256'], 'Source GLB drift')
    clean = Path('/result/verified/internal') / identity / 'fresh/clean-reimport'
    need(report['sourceGlb'] == str(clean.parent.parent / (identity + '.glb')), 'Fresh source execution path differs')
    binding = {'id': identity, 'qaSha256': sha(report_raw), 'sourceGlbSha256': row['sourceSha256'], 'fbxSha256': exp['fbxSha256'], 'fbxBytes': exp['fbxBytes']}
    recalculated = verify_report(report_raw, binding, source_path.read_bytes(), fbx_bytes, runtime['recipe'], actual_runtime, PINNED_SOURCES, clean)
    need(type(projected['cleanImportEvidence']) is dict and set(projected['cleanImportEvidence']) == {'reportAttestedClosure', 'embeddedBytesIndependentlyChecked', 'extractedCopiesAvailable'} and all(v is True for v in projected['cleanImportEvidence'].values()), 'Successful F live-import evidence missing')
    # R does not possess extracted images and must not claim to have recreated them.
    recalculated['cleanImportEvidence']['extractedCopiesAvailable'] = True
    need(recalculated == projected, 'Fresh projected QA differs from independently checked raw report/container')
    check_materialization(json_bytes(path.with_name('materialized-imported-images.json').read_bytes()), report, runtime)
    receipt = json_bytes((root / identity / 'receipt.json').read_bytes())
    f.exact(receipt, 'schema packagingRevision packageVersion id kind filename archiveBytes archiveSha256 planSha256 conversionPipelineSha256 entries sourceFiles notice verification retainedArchive', 'receipt')
    need(receipt['schema'] == 'meshcopia-minimal-package-receipt/1' and type(receipt['packagingRevision']) is int and receipt['packagingRevision'] == 1 and receipt['packageVersion'] == '1.0.0' and receipt['id'] == identity and receipt['kind'] == 'fbx' and receipt['retainedArchive'] is True, 'Receipt identity differs')
    f.digest(receipt['planSha256'])
    raw = {'name': identity + '.fbx', 'bytes': exp['fbxBytes'], 'sha256': exp['fbxSha256']}
    entries = [{'name': 'LICENSE.txt', 'bytes': row['notice']['bytes'], 'sha256': row['notice']['sha256']}, raw]
    need(receipt['filename'] == exp['filename'] and receipt['archiveBytes'] == exp['archiveBytes'] and receipt['archiveSha256'] == exp['archiveSha256'] and receipt['conversionPipelineSha256'] == f.PIPELINE, 'Receipt package/recipe binding differs')
    need(receipt['entries'] == entries and receipt['sourceFiles'] == [raw] and receipt['notice'] == row['notice'], 'Receipt payload/notice differs')
    check_verification(receipt['verification'], exp['fbxBytes'] + row['notice']['bytes'])
    check_verification(package_proof['verification'], exp['fbxBytes'] + row['notice']['bytes'])
    need(receipt['verification'] == package_proof['verification'], 'Receipt/root package proof differs')


def verify_internal_qa(archive, approval, source, expected, runtime, repo, *, fbx_directory=None, payload_archive=None):
    """Verify exact internal envelope, then bounded raw report/FBX checks per model.

    Caller must already verify F/job/artifact ownership and source/code pins.
    Exactly one raw FBX provider is required. No external calls or conversions.
    """
    need((fbx_directory is None) != (payload_archive is None), 'Choose exactly one raw FBX provider')
    ids = [r['id'] for r in source['models']]
    with tempfile.TemporaryDirectory(prefix='fbx-minimal-qa-') as directory:
        root = Path(directory); extract_qa(Path(archive), approval, ids, root)
        actual_runtime = json_bytes((root / 'runtime.json').read_bytes()); check_runtime(actual_runtime, runtime)
        pilot = json_bytes((root / 'pilot-gate.json').read_bytes())
        need(pilot == {'passed': True, 'ids': list(f.PILOTS), 'fCommit': approval['fCommit']} and pilot['passed'] is True, 'Pilot gate differs')
        summary = json_bytes((root / 'qa.json').read_bytes())
        f.exact(summary, 'schemaVersion status fCommit sourceCommit runId runAttempt fbxQa packages', 'internal summary')
        for key, value in {'schemaVersion': 1, 'status': 'fresh-fbx-and-minimal-packages-verified', 'fCommit': approval['fCommit'], 'sourceCommit': f.BASE, 'runId': str(approval['runId']), 'runAttempt': str(approval['runAttempt'])}.items(): need(summary[key] == value and type(summary[key]) is type(value), 'Internal summary identity differs: ' + key)
        records = summary['fbxQa']['records']; public_cohort(records, set(ids))
        need(summary['fbxQa'] == public_cohort(records, set(ids)), 'Unexpected root QA projection')
        byid = {r['id']: r for r in records}; packages = {r['id']: r for r in summary['packages']}
        need(len(records) == len(byid) == len(summary['packages']) == len(packages) == 137 and set(byid) == set(packages) == set(ids), 'Internal QA incomplete/duplicate cohort')
        # Stream from the outer artifact; only one <=95 MiB raw FBX enters parser memory.
        with zipfile.ZipFile(payload_archive) if payload_archive is not None else __import__('contextlib').nullcontext() as outer:
            for row, exp in zip(source['models'], expected['models']):
                identity = row['id']; name = identity + '.fbx'
                need(0 < exp['fbxBytes'] <= MAX_PAYLOAD_FILE, 'FBX exceeds bounded parser size')
                if outer is not None:
                    temporary = root / 'model.fbx'; stream_member(outer, outer.getinfo(name), temporary, exp['fbxBytes'], exp['fbxSha256']); path = temporary
                else:
                    path = f.packages.regular_file(Path(fbx_directory) / name)
                    need(path.stat().st_size == exp['fbxBytes'] and file_sha(path) == exp['fbxSha256'], 'Raw FBX provider bytes differ')
                verify_model(identity, row, exp, root, runtime, actual_runtime, byid[identity], packages[identity], path.read_bytes(), Path(repo))
                if outer is not None: temporary.unlink()
    return {'status': 'exact-internal-qa-rechecked', 'models': 137, 'qaArtifactSha256': approval['qaArtifactSha256'], 'qaSummarySha256': approval['qaSummarySha256'], 'freshImportedImageProof': 'attested-by-exact-successful-F', 'rawReportAndContainerRechecked': True, 'blenderRerunByTransport': False}
