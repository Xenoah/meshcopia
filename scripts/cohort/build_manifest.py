"""Prepare a reviewed cohort candidate from staged drafts (local, offline).

Writes the final public metadata (only the `status` field changes from draft to
public, byte-for-byte otherwise) and docs/cohorts/<name>/source.json plus a
discovery expected.json. It never converts, packages, uploads or publishes.

Usage:
  python3 scripts/cohort/build_manifest.py --cohort NAME --base COMMIT
"""
import argparse
import json
from pathlib import Path
from common import *


def stage_commits(repo, base, proofs):
    """Map each staged draft ID to the first proven successful source-stage commit."""
    mapping = {}
    for proof in proofs:
        commit(proof['commit'])
        need(is_ancestor(repo, proof['commit'], base), 'Proof commit is not on the base history')
        marker = json.loads(git(repo, 'show', proof['commit'] + ':.source-stage.json'))
        need(marker.get('purpose') == 'draft-raw-source-prepublication', 'Not a source-stage marker')
        for identity in marker['ids']:
            mapping.setdefault(identity, proof['commit'])
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort', required=True); parser.add_argument('--base', required=True)
    args = parser.parse_args(); repo = ROOT; paths = cohort_paths(args.cohort)
    base = git(repo, 'rev-parse', args.base).decode().strip(); commit(base)
    need(git(repo, 'rev-parse', 'HEAD').decode().strip() == base, 'Run from a checkout of the exact base commit')
    proofs = json.loads(git(repo, 'show', base + ':docs/source-stage-proofs.json'))['proofs']
    stages = stage_commits(repo, base, proofs)
    entries = tree(repo, base); rows = []
    for path in sorted(entries):
        if not path.endswith('/asset.json') or not path.startswith('content/assets/'): continue
        data = blob(repo, entries, path); metadata = json.loads(data)
        if metadata.get('type') != 'model' or metadata.get('status') != 'draft': continue
        identity = metadata['id']
        need(identity in stages, 'Draft has no proven source stage: ' + identity)
        text = data.decode('utf-8')
        need(text.count('"status": "draft"') == 1, 'Ambiguous status field: ' + identity)
        final = text.replace('"status": "draft"', '"status": "public"').encode('utf-8')
        final_metadata = json.loads(final)
        need({k: v for k, v in final_metadata.items() if k != 'status'} == {k: v for k, v in metadata.items() if k != 'status'}, 'Status flip changed other metadata')
        (repo / path).write_bytes(final)
        folder = f'content/assets/{identity}/source/'
        files = []
        for name in sorted(p[len(folder):] for p in entries if p.startswith(folder)):
            b = blob(repo, entries, folder + name); files.append({'name': name, 'bytes': len(b), 'sha256': sha(b)})
        glb = blob(repo, entries, folder + identity + '.glb')
        need(metadata.get('preview') == identity + '.glb', 'Model preview must be its GLB')
        ordinary, fbx = notice_texts(final_metadata)
        rows.append({'id': identity, 'version': metadata['version'], 'status': 'public', 'assetMetadata': path,
                     'metadataSha256': sha(final), 'sourceGLB': folder + identity + '.glb', 'sourceSha256': sha(glb),
                     'sourceBytes': len(glb), 'sourceFiles': files, 'stageCommit': stages[identity],
                     'notice': notice_record(ordinary), 'fbxNotice': notice_record(fbx)})
    rows.sort(key=lambda r: r['id'])
    source = {'schemaVersion': 1, 'cohort': args.cohort, 'baseCommit': base, 'modelCount': len(rows),
              'packageVersion': PACKAGE_VERSION, 'pipelineSha256': PIPELINE, 'models': rows}
    check_source(source)
    out = repo / paths['dir']; out.mkdir(parents=True, exist_ok=False)
    dump(repo / paths['source'], source)
    expected = {'schemaVersion': 1, 'reviewStatus': 'discovery', 'cohort': args.cohort, 'baseCommit': base,
                'sourceInventorySha256': file_sha(repo / paths['source']), 'runtimeSha256': file_sha(repo / RUNTIME),
                'pipelineSha256': PIPELINE, 'packageVersion': PACKAGE_VERSION, 'models': []}
    dump(repo / paths['expected'], expected)
    print(json.dumps({'cohort': args.cohort, 'models': len(rows), 'base': base}))


if __name__ == '__main__':
    main()
