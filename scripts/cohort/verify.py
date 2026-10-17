"""Cohort F: fresh FBX conversion, clean-import QA and strict minimal packaging.

Runs inside the digest-pinned Debian runtime prepared by the unchanged
scripts/fbx-minimal-verification/setup-runtime.sh. It reads only the exact F
checkout, never publishes, and writes:
  <out>/artifact/  <id>.fbx, <id>-<v>-fbx-minimal-1.0.0.zip,
                   <id>-<v>-minimal-1.0.0.zip, cohort-inventory.json
  <out>/internal/  qa.json, runtime.json and per-model reports/receipts.
A `discovery` expected manifest records fresh outputs for review; a
`reproduced-final` manifest requires byte-identical outputs.
"""
import argparse
import shutil
import subprocess
import zlib
from common import *

SCRIPTS = ['scripts/cohort/common.py', 'scripts/cohort/verify.py', 'scripts/cohort/build_manifest.py',
           'scripts/cohort/test_cohort.py', 'scripts/cohort/record.py']


def allowed_paths(name):
    p = cohort_paths(name)
    return set(SCRIPTS) | {'.github/workflows/verify-cohort.yml', p['source'], p['expected'], p['dir'] + '/README.md'}


def preflight(repo, name, source, expected_doc, f):
    commit(f); clean_checkout(repo)
    need(git(repo, 'rev-parse', 'HEAD').decode().strip() == f, 'Checkout is not exact F')
    base = source['baseCommit']
    need(subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', base, f]).returncode == 0, 'Base is not an ancestor of F')
    chain = git(repo, 'rev-list', '--first-parent', f'{base}..{f}').decode().split()
    merges = git(repo, 'rev-list', '--merges', f'{base}..{f}').decode().split()
    need(chain and not merges, 'F must be a linear additive history over the base')
    old, new = tree(repo, base), tree(repo, f)
    rows = {r['assetMetadata']: r for r in source['models']}
    allowed = allowed_paths(name)
    changed = {p for p in set(old) | set(new) if old.get(p) != new.get(p)}
    for path in changed:
        if path in rows:
            before = blob(repo, old, path); after = blob(repo, new, path, rows[path]['metadataSha256'])
            need(after == before.replace(b'"status": "draft"', b'"status": "public"', 1) and b'"status": "draft"' in before, 'Only the status field may change: ' + path)
        else:
            need(path in allowed and path not in old, 'F changes must be the reviewed additive cohort paths: ' + path)
            need(new[path][:2] == ('100644', 'blob'), 'Overlay symlink/executable prohibited')
    need(set(rows) <= changed, 'Every cohort model must be finalized in F')
    for row in source['models']:
        metadata = json.loads(blob(repo, new, row['assetMetadata'], row['metadataSha256']))
        need((metadata['id'], metadata['version'], metadata['type'], metadata['status'], metadata['preview']) == (row['id'], row['version'], 'model', 'public', row['id'] + '.glb'), 'Metadata identity differs')
        check_notice(row['notice'], metadata, False); check_notice(row['fbxNotice'], metadata, True)
        folder = f'content/assets/{row["id"]}/source/'
        names = sorted(p[len(folder):] for p in new if p.startswith(folder))
        need(names == [x['name'] for x in row['sourceFiles']], 'Source inventory differs: ' + row['id'])
        for x in row['sourceFiles']: blob(repo, new, folder + x['name'], x['sha256'], x['bytes'])
        marker = json.loads(git(repo, 'show', row['stageCommit'] + ':.source-stage.json'))
        need(row['id'] in marker['ids'], 'Stage commit does not stage this ID')
        for x in row['sourceFiles']:
            need(sha(git(repo, 'show', f'{row["stageCommit"]}:{folder}{x["name"]}')) == x['sha256'], 'Stage commit bytes differ: ' + row['id'])
    runtime = read(repo / RUNTIME)
    for fname, checksum in runtime['recipe'].items():
        need(file_sha(repo / 'scripts/fbx-verification' / fname) == checksum, 'Frozen conversion recipe differs')
    need(sha(json.dumps(runtime['recipe'], sort_keys=True, separators=(',', ':')).encode()) == PIPELINE == runtime['pipelineSha256'], 'Recipe aggregate differs')
    for path, checksum in runtime['supportFiles'].items():
        need(file_sha(repo / path) == checksum, 'Pinned verifier/packager support differs: ' + path)
    need(runtime['numpyCpuBaseline']['environment']['NPY_DISABLE_CPU_FEATURES'] == 'AVX2,FMA3,AVX512F,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL', 'CPU canonicalization may not be relaxed')
    return runtime


def check_outputs(receipt, row, kind, name, data_bytes, data_sha):
    note = row['fbxNotice'] if kind == 'fbx' else row['notice']
    need(receipt['id'] == row['id'] and receipt['kind'] == kind and receipt['filename'] == name, 'Receipt identity differs')
    need(receipt['notice'] == note, 'Notice package binding differs')
    want = [{'name': 'LICENSE.txt', 'bytes': note['bytes'], 'sha256': note['sha256']}]
    if kind == 'fbx':
        want.append({'name': row['id'] + '.fbx', 'bytes': data_bytes, 'sha256': data_sha})
    else:
        want += [{'name': x['name'], 'bytes': x['bytes'], 'sha256': x['sha256']} for x in row['sourceFiles']]
    need(receipt['entries'] == sorted(want, key=lambda e: e['name'].encode('utf-8')), 'ZIP must contain exactly the payload and one LICENSE.txt')
    v = receipt['verification']
    need(v['entryCount'] == len(want) and all(v.get(k) is True for k in ('exactAllowlist', 'payloadHashesVerified', 'cleanExtractionVerified', 'dependencyClosureVerified')), 'Strict extracted archive verification missing')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path); parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cohort', required=True); parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args(); repo = args.repo.resolve(); paths = cohort_paths(args.cohort)
    source_bytes = (repo / paths['source']).read_bytes(); source = read(repo / paths['source']); expected_doc = read(repo / paths['expected'])
    byid = check_source(source); need(source['cohort'] == args.cohort, 'Cohort name differs')
    expected = check_expected(expected_doc, source, source_bytes, file_sha(repo / RUNTIME))
    branch = f'refs/heads/cohort/verify-{args.cohort}'
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == branch and os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Only exact repository branch push permitted')
    f = os.environ.get('GITHUB_SHA', ''); runtime = preflight(repo, args.cohort, source, expected_doc, f)
    if args.preflight_only:
        print(f'Cohort {args.cohort} preflight passed for {len(byid)} models; no Blender or publication invoked.'); return
    need(sys.version.split()[0] == runtime['versions']['python'] and zlib.ZLIB_VERSION == zlib.ZLIB_RUNTIME_VERSION == runtime['versions']['zlib'] and sys.flags.optimize == 0, 'Packaging runtime/assertions differ')
    need(file_sha(Path(sys.executable).resolve()) == runtime['packaging']['pythonBinarySha256'] and file_sha(Path('/usr/lib/x86_64-linux-gnu/libz.so.1.3.1')) == runtime['packaging']['zlibBinarySha256'], 'Interpreter/compression binary differs')
    need(file_sha(Path('/usr/bin/blender')) == runtime['binarySha256'], 'Blender binary differs')
    for path, checksum in runtime['exporterFiles'].items(): need(file_sha(Path('/') / path) == checksum, 'Exporter differs')
    for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'): need(re.fullmatch(r'[1-9][0-9]*', os.environ.get(key, '')), 'Missing run identity')
    need(not args.output.exists(), 'Fresh output root required')
    out = args.output.resolve(); out.mkdir(parents=True); private = out / 'internal'; private.mkdir(); public = out / 'artifact'; public.mkdir()
    code = repo / 'scripts/fbx-verification'
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'NPY_DISABLE_CPU_FEATURES': runtime['numpyCpuBaseline']['environment']['NPY_DISABLE_CPU_FEATURES']}
    blender = ['/usr/bin/blender', '-b', '-noaudio', '--factory-startup', '--python-use-system-env', '--python-exit-code', '1']
    subprocess.run(blender + ['--python', str(code / 'runtime_probe.py'), '--', str(repo / RUNTIME), str(private / 'runtime.json')], env=env, check=True)
    actual_runtime = read(private / 'runtime.json')
    from verify_fbx_report import verify_report, public_cohort
    from deterministic_fbx import PINNED_SOURCES
    proofs, bindings, packages_qa = [], [], []
    for identity in sorted(byid):
        need(shutil.disk_usage(out).free > 3_000_000_000, 'Disk reserve reached')
        row = byid[identity]; work = private / identity; work.mkdir(); fresh = work / 'fresh'; fresh.mkdir()
        data = (repo / row['sourceGLB']).read_bytes(); need(sha(data) == row['sourceSha256'], 'Source GLB differs')
        source_glb = work / (identity + '.glb'); source_glb.write_bytes(data)
        command = blender + ['-t', '4', '--python', str(code / 'materialize_imported_images.py'), '--', '--converter-script', str(code / 'convert_and_audit_fbx.py'),
                             '--source', str(source_glb), '--out', str(fresh), '--expected-sha256', row['sourceSha256'], '--unique-image-paths', '--normalize-materials', '--deterministic']
        with (work / 'execution.log').open('w') as log: result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            tail = (work / 'execution.log').read_text(errors='replace').splitlines()[-40:]
            print('\n'.join(line[:300] for line in tail), flush=True)
            raise ValueError(f'Blender conversion failed for {identity} (exit {result.returncode})')
        names = archive_names(identity, row['version'])
        fbx_path = fresh / names['fbx']; fbx = fbx_path.read_bytes(); fbx_record = {'filename': names['fbx'], 'bytes': len(fbx), 'sha256': sha(fbx)}
        if expected is not None:
            need(fbx_record == expected[identity]['fbx'], 'Reviewed FBX bytes differ: ' + identity)
        report_path = fresh / 'roundtrip-report.json'; report = report_path.read_bytes()
        binding = {'id': identity, 'qaSha256': sha(report), 'sourceGlbSha256': row['sourceSha256'], 'fbxSha256': fbx_record['sha256'], 'fbxBytes': fbx_record['bytes']}
        proof = verify_report(report, binding, data, fbx, runtime['recipe'], actual_runtime, PINNED_SOURCES, fresh / 'clean-reimport')
        need(proof['cleanImportEvidence']['extractedCopiesAvailable'], 'Missing actual clean-import image bytes')
        proofs.append(proof)
        outputs = {'fbx': fbx_record}; receipts = {}
        for kind, note_key, out_key in (('fbx', 'fbxNotice', 'fbxArchive'), ('model', 'notice', 'archive')):
            notice = work / f'LICENSE-{kind}.txt'; notice.write_bytes(row[note_key]['text'].encode('utf-8'))
            plan_dir = work / f'notice-{kind}'; plan_dir.mkdir(); notice_path = plan_dir / 'LICENSE.txt'; shutil.copyfile(notice, notice_path)
            if kind == 'fbx':
                plan = packages.make_plan(repo / 'content/assets' / identity, notice_path, fbx_path=fbx_path, fbx_sha256=fbx_record['sha256'], pipeline_sha256=PIPELINE, fbx_report=report_path)
            else:
                plan = packages.make_plan(repo / 'content/assets' / identity, notice_path)
            receipt = packages.package(plan, output=public / names[out_key])
            check_outputs(receipt, row, kind, names[out_key], fbx_record['bytes'], fbx_record['sha256'])
            outputs[out_key] = {'filename': names[out_key], 'bytes': receipt['archiveBytes'], 'sha256': receipt['archiveSha256']}
            if expected is not None:
                need(outputs[out_key] == expected[identity][out_key], f'Reviewed {out_key} bytes differ: {identity}')
            receipts[kind] = receipt
        (public / names['fbx']).write_bytes(fbx)
        dump(work / 'receipt.json', receipts)
        packages_qa.append({'id': identity, 'freshCiQaSha256': sha(report), 'outputs': outputs,
                            'verification': {k: receipts[k]['verification'] for k in receipts}})
        bindings.append(model_binding(row, outputs))
        print(json.dumps({'id': identity, 'completed': len(proofs), 'expected': len(byid)}), flush=True)
    need(len(proofs) == len(byid), 'Incomplete verification')
    cohort_qa = public_cohort(proofs, set(byid))
    dump(private / 'qa.json', {'schemaVersion': 1, 'status': 'fresh-fbx-and-minimal-packages-verified', 'cohort': args.cohort, 'fCommit': f,
                               'baseCommit': source['baseCommit'], 'runId': os.environ['GITHUB_RUN_ID'], 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'],
                               'reviewStatus': expected_doc['reviewStatus'], 'fbxQa': cohort_qa, 'packages': packages_qa})
    inventory = {'schemaVersion': 1, 'contract': 'meshcopia-cohort-artifact/1', 'repository': REPO, 'cohort': args.cohort, 'fCommit': f,
                 'baseCommit': source['baseCommit'], 'workflow': '.github/workflows/verify-cohort.yml', 'runId': os.environ['GITHUB_RUN_ID'],
                 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'], 'reviewStatus': expected_doc['reviewStatus'], 'packageVersion': PACKAGE_VERSION,
                 'pipelineSha256': PIPELINE, 'sourceInventorySha256': sha(source_bytes), 'expectedManifestSha256': file_sha(repo / paths['expected']),
                 'runtimeSha256': file_sha(repo / RUNTIME), 'models': sorted(bindings, key=lambda x: x['id'])}
    dump(public / 'cohort-inventory.json', inventory)
    need({p.name for p in public.iterdir()} == payload_names(bindings) and all(p.is_file() and not p.is_symlink() for p in public.iterdir()), 'Unexpected/missing public artifact entry')
    for p in public.iterdir(): p.chmod(0o644)
    print(f'{len(byid)} fresh FBXs and exact minimal ZIPs verified ({expected_doc["reviewStatus"]}). QA is separate; nothing published.')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('COHORT_VERIFY_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__ + ': ' + str(error)[:300]), file=sys.stderr)
        raise SystemExit(1)
