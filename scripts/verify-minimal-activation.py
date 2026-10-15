#!/usr/bin/env python3
"""Read-only activation gate. No cached/offline/publication bypass is provided."""
import argparse
import hashlib
import html.parser
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

REPO = 'Xenoah/meshcopia'
TAG = 'minimal-v1.0.0'
BASE = '4ab5342568a4227215b295b40a47c27698cc930a'
WORKFLOW = '.github/workflows/verify-minimal.yml'
API = f'https://api.github.com/repos/{REPO}'
POLICY = 'asset-files-required-dependencies-single-notice-v1'
MAX_JSON = 16 * 1024 * 1024


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_json(data):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, 'Duplicate JSON key')
            out[key] = value
        return out
    return json.loads(data, object_pairs_hook=unique)


def local_file(repo, relative):
    need(isinstance(relative, str) and not relative.startswith('/') and all(p not in ('', '.', '..') for p in relative.split('/')), 'Unsafe local evidence path')
    result = repo
    for part in relative.split('/'):
        result = result / part
        need(not result.is_symlink(), 'Symlink in evidence/source path')
    need(result.is_file(), f'Missing activation input: {relative}')
    return result


def git_blob(repo, commit, relative):
    need(re.fullmatch('[0-9a-f]{40}', commit), 'Invalid pinned commit')
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    return subprocess.check_output(['git', '--no-replace-objects', '-c', 'safe.directory=' + str(repo), '-C', str(repo), 'show', commit + ':' + relative], env=env)


def validate_activation(config):
    need(set(config) == {'schemaVersion', 'repository', 'activations'} and config['schemaVersion'] == 1 and config['repository'] == REPO, 'Invalid activation document')
    rows = config['activations']
    need(isinstance(rows, list) and len(rows) <= 1, 'Only the reviewed published173 adapter is supported')
    for a in rows:
        need(set(a) == {'cohort', 'releaseTag', 'releaseId', 'verificationCommit', 'inventorySha256', 'transportEvidenceFile', 'transportEvidenceSha256'}, 'Invalid activation fields')
        need(a['cohort'] == 'published173' and a['releaseTag'] == TAG, 'Unsupported activation cohort/tag')
        need(type(a['releaseId']) is int and a['releaseId'] > 0, 'Invalid release ID')
        need(isinstance(a['verificationCommit'], str) and re.fullmatch('[0-9a-f]{40}', a['verificationCommit']), 'Invalid verification commit')
        for key in ('inventorySha256', 'transportEvidenceSha256'):
            need(isinstance(a[key], str) and re.fullmatch('[0-9a-f]{64}', a[key]), 'Invalid evidence digest')
        need(isinstance(a['transportEvidenceFile'], str) and re.fullmatch(r'docs/minimal-publication/[a-zA-Z0-9][a-zA-Z0-9._-]*\.json', a['transportEvidenceFile']), 'Invalid evidence path')
    return rows


def trusted_url(url):
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ''
    need(parsed.scheme == 'https' and not parsed.username and not parsed.password and parsed.port in (None, 443), 'Unsafe anonymous URL')
    need(host in ('api.github.com', 'github.com', 'xenoah.github.io') or host.endswith('.githubusercontent.com'), 'Unexpected anonymous redirect host')


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        trusted_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PublicReader:
    """Anonymous bounded reads. Never reads an environment credential."""
    def __init__(self):
        self.opener = urllib.request.build_opener(SafeRedirect)

    def open(self, url):
        trusted_url(url)
        response = self.opener.open(urllib.request.Request(url, headers={'User-Agent': 'meshcopia-minimal-activation', 'Accept': 'application/vnd.github+json' if url.startswith(API) else '*/*'}), timeout=180)
        need(response.status == 200, 'Anonymous download did not return 200')
        return response

    def bytes(self, url, limit=MAX_JSON):
        with self.open(url) as response:
            data = response.read(limit + 1)
        need(len(data) <= limit, 'Public document exceeds limit')
        return data

    def json(self, url):
        return parse_json(self.bytes(url))

    def file(self, url, target, length, digest):
        total = 0
        checksum = hashlib.sha256()
        with self.open(url) as response, target.open('xb') as out:
            while block := response.read(1024 * 1024):
                total += len(block)
                need(total <= length, 'Public ZIP exceeds pinned size')
                checksum.update(block)
                out.write(block)
        need(total == length and checksum.hexdigest() == digest, 'Public ZIP byte/hash mismatch')


def validate_remote(a, evidence, inventory, release, ref, run, attachments, inventory_bytes):
    need(evidence.get('schemaVersion') == 1 and evidence.get('status') == 'anonymous-byte-readback-passed', 'Transport byte readback has not passed')
    for key, expected in [('repository', REPO), ('tag', TAG), ('verificationCommit', a['verificationCommit']), ('releaseId', a['releaseId']), ('inventorySha256', a['inventorySha256']), ('attachmentCount', 174)]:
        need(evidence.get(key) == expected, f'Transport evidence mismatch: {key}')
    need(evidence.get('browserDownloadEvidence') == 'not-performed-by-transport', 'Unexpected transport/browser evidence contract')
    release_url = f'https://github.com/{REPO}/releases/tag/{TAG}'
    need(evidence.get('releaseUrl') == release_url and release.get('html_url') == release_url, 'Wrong release URL')
    need(release.get('id') == a['releaseId'] and release.get('tag_name') == TAG and release.get('draft') is False and release.get('prerelease') is False and release.get('target_commitish') == a['verificationCommit'], 'Release identity/state mismatch')
    need(ref.get('ref') == 'refs/tags/' + TAG and ref.get('object') == {'type': 'commit', 'sha': a['verificationCommit'], 'url': API + '/git/commits/' + a['verificationCommit']}, 'Release tag does not resolve directly to verified commit')
    need(sha(inventory_bytes) == a['inventorySha256'], 'Public inventory digest mismatch')
    need(inventory.get('schemaVersion') == 1 and inventory.get('packageVersion') == '1.0.0' and inventory.get('repository') == REPO and inventory.get('tag') == TAG and inventory.get('cohort') == 'published173' and inventory.get('sourceCommit') == BASE and inventory.get('verificationCommit') == a['verificationCommit'] and inventory.get('workflow') == WORKFLOW, 'Inventory identity mismatch')
    need(isinstance(inventory.get('runId'), str) and re.fullmatch('[1-9][0-9]*', inventory['runId']) and isinstance(inventory.get('runAttempt'), str) and re.fullmatch('[1-9][0-9]*', inventory['runAttempt']), 'Invalid verification run identity')
    need(run.get('id') == int(inventory['runId']) and run.get('run_attempt') == int(inventory['runAttempt']) and run.get('head_sha') == a['verificationCommit'] and run.get('head_branch') == 'minimal/verify-existing173-v1' and run.get('event') == 'push' and run.get('path') == WORKFLOW and run.get('status') == 'completed' and run.get('conclusion') == 'success', 'Verification run has not passed for this exact commit/attempt')
    need(run.get('repository', {}).get('full_name') == REPO and run.get('head_repository', {}).get('full_name') == REPO, 'Verification run repository mismatch')
    rows = inventory.get('assets')
    need(isinstance(rows, list) and len(rows) == 173, 'Incomplete published173 inventory')
    wanted = {row['filename']: {'name': row['filename'], 'bytes': row['bytes'], 'sha256': row['sha256'], 'url': row['url']} for row in rows}
    need(len(wanted) == 173, 'Duplicate package filename')
    wanted['minimal-inventory.json'] = {'name': 'minimal-inventory.json', 'bytes': len(inventory_bytes), 'sha256': sha(inventory_bytes), 'url': f'https://github.com/{REPO}/releases/download/{TAG}/minimal-inventory.json'}
    actual = {item['name']: item for item in attachments}
    proof = {item['name']: item for item in evidence.get('assets', [])}
    need(len(attachments) == len(actual) == len(proof) == len(evidence.get('assets', [])) == 174 and set(actual) == set(proof) == set(wanted), 'Incomplete/duplicate/unexpected Release attachment inventory')
    for name, item in wanted.items():
        remote, saved = actual[name], proof[name]
        need(type(remote.get('id')) is int and remote['id'] > 0 and remote.get('state') == 'uploaded' and remote.get('size') == item['bytes'] and remote.get('digest') == 'sha256:' + item['sha256'] and remote.get('browser_download_url') == item['url'], 'Remote attachment identity/hash mismatch')
        need(saved.get('assetId') == remote['id'] and saved.get('anonymousReadback') is True and all(saved.get(k) == v for k, v in item.items()), 'Transport attachment proof mismatch')
    return rows


class CanonicalLinks(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.urls.append(attrs.get('href'))


def load_pinned_module(repo, commit, relative, module_name):
    target = local_file(repo, relative)
    need(target.read_bytes() == git_blob(repo, commit, relative), f'Activation verifier dependency differs from pinned F: {relative}')
    spec = importlib.util.spec_from_file_location(module_name, target)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def verify_activation(repo, a):
    raw_evidence = local_file(repo, a['transportEvidenceFile']).read_bytes()
    need(len(raw_evidence) <= MAX_JSON and sha(raw_evidence) == a['transportEvidenceSha256'], 'Transport evidence file digest mismatch')
    evidence = parse_json(raw_evidence)
    reader = PublicReader()
    release = reader.json(API + '/releases/' + str(a['releaseId']))
    ref = reader.json(API + '/git/ref/tags/' + TAG)
    raw_inventory = reader.bytes(f'https://github.com/{REPO}/releases/download/{TAG}/minimal-inventory.json')
    inventory = parse_json(raw_inventory)
    # Bound and validate path components before constructing any run URL.
    for key in ('runId', 'runAttempt'):
        need(isinstance(inventory.get(key), str) and re.fullmatch('[1-9][0-9]*', inventory[key]), 'Invalid run ID')
    run = reader.json(API + '/actions/runs/' + inventory['runId'] + '/attempts/' + inventory['runAttempt'])
    attachments = []
    for page in range(1, 12):
        part = reader.json(API + f'/releases/{a["releaseId"]}/assets?per_page=100&page={page}')
        need(isinstance(part, list), 'Invalid attachment page')
        attachments.extend(part)
        if len(part) < 100:
            break
    else:
        raise ValueError('Release attachment pagination limit exceeded')
    rows = validate_remote(a, evidence, inventory, release, ref, run, attachments, raw_inventory)
    f = a['verificationCommit']
    common = load_pinned_module(repo, f, 'scripts/minimal-verification/common.py', 'minimal_activation_common')
    packages = load_pinned_module(repo, f, 'scripts/minimal_packages.py', 'minimal_packages')
    notices = load_pinned_module(repo, f, 'scripts/minimal_notices.py', 'minimal_notices')
    source_bytes = git_blob(repo, f, 'docs/minimal-verification/source173.json')
    expected_bytes = git_blob(repo, f, 'docs/minimal-verification/expected173.json')
    source, expected = parse_json(source_bytes), parse_json(expected_bytes)
    common.check_manifests(source, expected, source_bytes)
    need(sum(row['archiveBytes'] for row in expected['assets']) <= 4 * 1024**3, 'Activation archive cohort exceeds bounded transfer size')
    need(inventory['sourceInventorySha256'] == sha(source_bytes) and inventory['expectedManifestSha256'] == sha(expected_bytes), 'Public inventory differs from pinned manifests')
    for key, relative in [('packagerSha256', 'scripts/minimal_packages.py'), ('noticeGeneratorSha256', 'scripts/minimal_notices.py'), ('runtimeSha256', 'docs/minimal-verification/runtime.json')]:
        need(expected[key] == sha(git_blob(repo, f, relative)), 'Pinned verifier/runtime digest mismatch')
        if key != 'noticeGeneratorSha256':
            need(inventory[key] == expected[key], 'Inventory verifier/runtime digest mismatch')
    need(rows == [common.package_binding(row, exp) for row, exp in zip(source['assets'], expected['assets'])], 'Public packages differ from reviewed pinned source/notice/ZIP inventory')
    bindings = []
    with tempfile.TemporaryDirectory(prefix='meshcopia-minimal-activation-') as folder:
        work = Path(folder)
        notice_path = work / 'LICENSE.txt'
        archive_path = work / 'package.zip'
        for row, published in zip(source['assets'], rows):
            asset_dir = repo / 'content/assets' / row['id']
            metadata_bytes = local_file(repo, f'content/assets/{row["id"]}/asset.json').read_bytes()
            need(sha(metadata_bytes) == row['metadataSha256'], 'Current asset metadata differs from pinned source')
            need(metadata_bytes == git_blob(repo, BASE, f'content/assets/{row["id"]}/asset.json'), 'Current asset metadata differs from immutable baseline')
            metadata = parse_json(metadata_bytes)
            need((metadata['id'], metadata['version'], metadata['type'], metadata['status']) == (row['id'], row['version'], row['kind'], 'public'), 'Current asset identity differs')
            names = packages.source_listing(asset_dir / 'source')
            need(names == [item['name'] for item in row['allSourceFiles']], 'Current complete source inventory differs')
            for item in row['allSourceFiles']:
                current = packages.record(local_file(repo, f'content/assets/{row["id"]}/source/{item["name"]}'), item['name'])
                need(all(current[key] == item[key] for key in ('name', 'bytes', 'sha256')), 'Current source bytes differ')
            # First adapter intentionally requires an exact match to catalog a.files.
            need(row['sourceFiles'] == row['allSourceFiles'], 'Selected payload is not the complete ordinary catalog inventory')
            old_license, old_attribution = notices.baseline_notices(metadata)
            need(notices.make_notice(metadata, old_license, old_attribution) == row['notice']['text'], 'Retained legal notice differs from pinned source')
            detail_url = f'https://xenoah.github.io/meshcopia/assets/{row["id"]}/'
            page = CanonicalLinks()
            page.feed(reader.bytes(detail_url, 2 * 1024 * 1024).decode('utf-8'))
            need(page.urls == [detail_url] and detail_url in row['notice']['text'], 'Notice detail URL is not the verified live canonical asset page')
            notice_path.write_bytes(row['notice']['text'].encode('utf-8'))
            plan = packages.make_plan(asset_dir, notice_path)
            need([{k: item[k] for k in ('name', 'bytes', 'sha256')} for item in plan['entries'] if item['name'] != 'LICENSE.txt'] == row['sourceFiles'], 'Current dependency closure/output paths differ from binding')
            reader.file(published['url'], archive_path, published['bytes'], published['sha256'])
            try:
                packages.verify_archive(archive_path, plan)
            finally:
                archive_path.unlink()
            bindings.append({'schemaVersion': 1, 'id': row['id'], 'assetVersion': row['version'], 'packageVersion': '1.0.0', 'contentPolicy': POLICY, 'noticeFile': 'LICENSE.txt', 'notice': row['notice'], 'url': published['url'], 'bytes': published['bytes'], 'sha256': published['sha256'], 'sourceFiles': row['sourceFiles'], 'verification': {'state': 'published-verified', 'releaseTag': TAG, 'archiveSha256': published['sha256']}})
    return bindings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    config = parse_json(local_file(repo, 'docs/minimal-activation.json').read_bytes())
    bindings = []
    for activation in validate_activation(config):
        bindings.extend(verify_activation(repo, activation))
    print(json.dumps(bindings, ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()
