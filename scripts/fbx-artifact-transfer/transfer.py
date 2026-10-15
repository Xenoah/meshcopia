"""Internal transfer only: GET a pinned successful Actions artifact, slice/rejoin bytes.

No conversion, extraction of consumer payloads, release/tag/Pages writes, token
persistence, automatic redirects, or retry. Original FBX and ZIP bytes are opaque.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = 'Xenoah/meshcopia'
REPO_ID = 1418685897
F = '83a1daedf3ad7563fa55bf0cca40ca749689e139'
BRANCH = 'refs/heads/fbx/review-minimal-artifact-v1'
WORKFLOW = '.github/workflows/review-fbx-minimal-artifact.yml'
SOURCE_WORKFLOW = '.github/workflows/verify-fbx-minimal.yml'
SOURCE_BRANCH = 'fbx/verify-minimal137-v1'
RUN = 38817061339
ATTEMPT = 1
ARTIFACT = 12010989935
BYTES = 1171848758
SHA256 = '178be79de9eec1ab7864e0abebdc4763b6f39bb0daa9a7e73c3b9d4eb9b1b70a'
ARTIFACT_NAME = f'fbx-minimal137-{F}-{RUN}-{ATTEMPT}'
PART_BYTES = 384 * 1024 * 1024  # ZIP-envelope headroom below 400 MiB and 512 MiB.
CHUNK = 1024 * 1024
API = 'https://api.github.com/repos/' + REPO
PATHS = {WORKFLOW, 'scripts/fbx-artifact-transfer/transfer.py', 'scripts/fbx-artifact-transfer/test_transfer.py'}
ORIGINAL = {'repository': REPO, 'verificationCommit': F, 'workflow': SOURCE_WORKFLOW,
            'runId': RUN, 'runAttempt': ATTEMPT, 'artifactId': ARTIFACT,
            'artifactName': ARTIFACT_NAME, 'bytes': BYTES, 'sha256': SHA256}


def need(ok, message):
    if not ok: raise ValueError(message)


def canonical(value): return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
def sha_file(path):
    total = 0; checksum = hashlib.sha256()
    with regular(path).open('rb') as handle:
        while data := handle.read(CHUNK): total += len(data); checksum.update(data)
    return total, checksum.hexdigest()


def regular(path):
    path = Path(path).absolute()
    need(path.is_file() and not path.is_symlink() and path.resolve() == path, 'Expected ordinary non-symlink file')
    return path


def check_identity(run, artifact):
    need(run['id'] == RUN and run['run_attempt'] == ATTEMPT, 'Original run identity differs')
    need(run['repository']['full_name'] == run['head_repository']['full_name'] == REPO and run['repository']['id'] == run['head_repository']['id'] == REPO_ID, 'Original repository differs')
    need(run['head_sha'] == F and run['head_branch'] == SOURCE_BRANCH and run['path'] == SOURCE_WORKFLOW and run['event'] == 'push', 'Original workflow/source differs')
    need(run['status'] == 'completed' and run['conclusion'] == 'success', 'Original verification not successful')
    need(artifact['id'] == ARTIFACT and artifact['name'] == ARTIFACT_NAME and artifact['expired'] is False, 'Original artifact identity/expiry differs')
    need(type(artifact['size_in_bytes']) is int and artifact['size_in_bytes'] == BYTES and artifact['digest'] == 'sha256:' + SHA256, 'Original artifact byte/digest pin differs')
    owner = artifact['workflow_run']
    need(owner['id'] == RUN and owner['head_sha'] == F and owner['head_branch'] == SOURCE_BRANCH and owner['repository_id'] == owner['head_repository_id'] == REPO_ID, 'Artifact belongs to another run/source')
    need(artifact['archive_download_url'] == API + f'/actions/artifacts/{ARTIFACT}/zip', 'Unexpected download API route')


def checked_signed_url(url):
    need(type(url) is str and len(url) <= 16384 and not re.search(r'[\x00-\x20\x7f\\]', url), 'Invalid signed redirect')
    parsed = urllib.parse.urlsplit(url)
    need(parsed.scheme == 'https' and parsed.username is None and parsed.password is None and parsed.port in (None, 443) and not parsed.fragment, 'Unsafe signed redirect')
    need(re.fullmatch(r'productionresultssa[a-z0-9]+\.blob\.core\.windows\.net', parsed.hostname or '') is not None, 'Unapproved artifact storage host')
    need(parsed.path.startswith('/') and parsed.query and not any(x in ('.', '..') for x in urllib.parse.unquote(parsed.path).split('/')), 'Invalid signed artifact path')
    return url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class ReadOnlyGitHub:
    def __init__(self, token, opener=None):
        need(bool(token) and '\n' not in token and '\r' not in token, 'Missing ephemeral Actions token')
        self.token = token
        self.opener = opener or urllib.request.build_opener(NoRedirect)

    def get(self, path):
        need(path in (f'/actions/runs/{RUN}', f'/actions/artifacts/{ARTIFACT}', f'/actions/artifacts/{ARTIFACT}/zip'), 'Unapproved API GET')
        request = urllib.request.Request(API + path, method='GET', headers={'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'meshcopia-readonly-artifact-transfer'})
        return self.opener.open(request, timeout=180)

    def json(self, path):
        with self.get(path) as response:
            data = response.read(2 * 1024 * 1024 + 1)
            need(len(data) <= 2 * 1024 * 1024, 'API response too large')
            return json.loads(data)

    def download(self, target):
        # An authenticated API request is never automatically redirected.
        try:
            response = self.get(f'/actions/artifacts/{ARTIFACT}/zip')
        except urllib.error.HTTPError as error:
            need(error.code == 302, 'Artifact API GET did not provide expected redirect')
            location = checked_signed_url(error.headers.get('Location'))
            # New Request has NO token, Cookie, or authenticated API headers.
            request = urllib.request.Request(location, method='GET', headers={'User-Agent': 'meshcopia-artifact-byte-reader'})
            response = self.opener.open(request, timeout=180)
        else:
            response.close()
            raise ValueError('Expected one signed storage redirect')
        with response, Path(target).open('xb') as out:
            need(response.status == 200, 'Signed download response differs')
            length = response.headers.get('Content-Length')
            need(length is None or length == str(BYTES), 'Signed response length differs')
            total = 0; checksum = hashlib.sha256()
            while data := response.read(CHUNK):
                total += len(data); need(total <= BYTES, 'Artifact exceeds exact bound')
                checksum.update(data); out.write(data)
        need(total == BYTES and checksum.hexdigest() == SHA256, 'Downloaded artifact bytes/digest differ')


def split_archive(source, output, expected_bytes, expected_sha, part_bytes=PART_BYTES):
    need(type(part_bytes) is int and 0 < part_bytes <= PART_BYTES, 'Invalid part size')
    need(sha_file(source) == (expected_bytes, expected_sha), 'Original archive bytes/digest differ before split')
    output = Path(output).absolute(); need(output.resolve() == output, 'Output symlink prohibited'); output.mkdir(exist_ok=False)
    records = []; total = 0
    with regular(source).open('rb') as src:
        while total < expected_bytes:
            number = len(records) + 1; directory = output / f'part-{number:02}'; directory.mkdir()
            filename = f'artifact-{ARTIFACT}.part-{number:02}.bin'; target = directory / filename
            size = 0; checksum = hashlib.sha256()
            with target.open('xb') as dst:
                while size < min(part_bytes, expected_bytes - total):
                    data = src.read(min(CHUNK, part_bytes - size, expected_bytes - total - size))
                    need(bool(data), 'Original archive truncated during split'); size += len(data); checksum.update(data); dst.write(data)
            records.append({'index': number, 'filename': filename, 'offset': total, 'bytes': size, 'sha256': checksum.hexdigest()}); total += size
        need(src.read(1) == b'', 'Original archive grew during split')
    verify_parts([output / f'part-{r["index"]:02}' / r['filename'] for r in records], records, expected_bytes, expected_sha)
    return records


def verify_parts(paths, records, expected_bytes, expected_sha, destination=None):
    need(len(paths) == len(records) and len(records) > 0, 'Part count differs')
    total = 0; full = hashlib.sha256()
    for index, (path, record) in enumerate(zip(paths, records), 1):
        need(set(record) == {'index', 'filename', 'offset', 'bytes', 'sha256'} and record['index'] == index and record['offset'] == total, 'Part order/offset/schema differs')
        need(record['filename'] == f'artifact-{ARTIFACT}.part-{index:02}.bin' and Path(path).name == record['filename'], 'Part filename differs')
        need(type(record['bytes']) is int and 0 < record['bytes'] <= PART_BYTES, 'Part exceeds bounded size')
        need(type(record['sha256']) is str and re.fullmatch('[0-9a-f]{64}', record['sha256']), 'Invalid part digest')
        size = 0; checksum = hashlib.sha256()
        with regular(path).open('rb') as src:
            while data := src.read(CHUNK):
                size += len(data); need(size <= record['bytes'] and total + size <= expected_bytes, 'Part length exceeds exact bound')
                checksum.update(data); full.update(data)
                if destination is not None: destination.write(data)
        need(size == record['bytes'] and checksum.hexdigest() == record['sha256'], 'Part bytes/digest differ'); total += size
    need(total == expected_bytes and full.hexdigest() == expected_sha, 'Concatenation differs from original artifact')


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    return subprocess.check_output(['git', '--no-replace-objects', '-c', 'safe.directory=' + str(repo), '-C', str(repo), *args], env=env)


def preflight(repo):
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == BRANCH and os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Wrong transfer context')
    f = os.environ.get('GITHUB_SHA', ''); need(re.fullmatch('[0-9a-f]{40}', f), 'Missing exact transfer commit')
    need(git(repo, 'rev-parse', 'HEAD').decode().strip() == f and git(repo, 'show', '-s', '--format=%P', f).decode().strip() == F, 'Transfer must directly follow exact successful F')
    need(git(repo, 'rev-parse', '--is-shallow-repository').strip() == b'false', 'Shallow checkout prohibited')
    need(git(repo, 'status', '--porcelain', '--untracked-files=no') == b'', 'Dirty checkout')
    changes = git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z', F, f).decode().split('\0')[:-1]
    need(len(changes) == 6 and set(changes[1::2]) == PATHS and changes[::2] == ['A'] * 3, 'Only three exact additive helper files permitted')
    for path in PATHS:
        raw = git(repo, 'ls-tree', '-z', f, '--', path).split(b'\0')
        need(len(raw) == 2 and raw[-1] == b'', 'Invalid helper tree entry')
        header, name = raw[0].split(b'\t', 1); mode, kind, oid = header.decode().split()
        need(mode == '100644' and kind == 'blob' and name.decode() == path, 'Unsafe helper tree mode/path')
        need(regular(repo / path).read_bytes() == git(repo, 'cat-file', 'blob', oid), 'Helper worktree differs')
    return f


def validate_manifest(manifest):
    need(set(manifest) == {'schemaVersion', 'purpose', 'original', 'transfer', 'partSizeLimit', 'parts', 'concatenationVerified'}, 'Manifest schema differs')
    need(manifest['schemaVersion'] == 1 and manifest['purpose'] == 'internal-byte-preserving-artifact-transfer' and manifest['original'] == ORIGINAL, 'Original binding differs')
    transfer = manifest['transfer']; need(set(transfer) == {'commit', 'workflow', 'runId', 'runAttempt'}, 'Transfer binding schema differs')
    need(re.fullmatch('[0-9a-f]{40}', transfer['commit']) and transfer['workflow'] == WORKFLOW and re.fullmatch('[1-9][0-9]*', transfer['runId']) and re.fullmatch('[1-9][0-9]*', transfer['runAttempt']), 'Invalid transfer identity')
    need(manifest['partSizeLimit'] == PART_BYTES and manifest['concatenationVerified'] is True and len(manifest['parts']) == 3, 'Expected three verified parts')


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    download = sub.add_parser('download-split'); download.add_argument('--repo', type=Path, required=True); download.add_argument('--output', type=Path, required=True)
    gate = sub.add_parser('preflight'); gate.add_argument('--repo', type=Path, required=True)
    join = sub.add_parser('reassemble'); join.add_argument('--manifest', type=Path, required=True); join.add_argument('--part', type=Path, action='append', required=True); join.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'reassemble':
        manifest = json.loads(regular(args.manifest).read_bytes()); validate_manifest(manifest)
        verify_parts(args.part, manifest['parts'], BYTES, SHA256)
        need(args.output.absolute().resolve() == args.output.absolute(), 'Output symlink prohibited')
        with args.output.open('xb') as dst: verify_parts(args.part, manifest['parts'], BYTES, SHA256, dst)
        need(sha_file(args.output) == (BYTES, SHA256), 'Written reassembly differs')
        print('Original artifact exactly reassembled: ' + SHA256); return
    f = preflight(args.repo.resolve())
    if args.command == 'preflight': print('Exact three-file read-only transfer preflight passed.'); return
    for name in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'): need(re.fullmatch('[1-9][0-9]*', os.environ.get(name, '')), 'Missing transfer run identity')
    need(args.output.absolute().resolve() == args.output.absolute(), 'Output symlink prohibited'); args.output.mkdir(exist_ok=False)
    api = ReadOnlyGitHub(os.environ.pop('GH_TOKEN', ''))
    check_identity(api.json(f'/actions/runs/{RUN}'), api.json(f'/actions/artifacts/{ARTIFACT}'))
    archive = args.output / 'original-artifact.zip'; api.download(archive)
    check_identity(api.json(f'/actions/runs/{RUN}'), api.json(f'/actions/artifacts/{ARTIFACT}'))
    parts = split_archive(archive, args.output / 'parts', BYTES, SHA256); need(len(parts) == 3, 'Expected exactly three parts')
    manifest = {'schemaVersion': 1, 'purpose': 'internal-byte-preserving-artifact-transfer', 'original': ORIGINAL,
                'transfer': {'commit': f, 'workflow': WORKFLOW, 'runId': os.environ['GITHUB_RUN_ID'], 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT']},
                'partSizeLimit': PART_BYTES, 'parts': parts, 'concatenationVerified': True}
    validate_manifest(manifest); raw = canonical(manifest)
    for part in parts: (args.output / 'parts' / f'part-{part["index"]:02}' / 'transfer-manifest.json').write_bytes(raw)
    print('Verified original artifact and exact three-part concatenation; manifest SHA-256: ' + hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    try: main()
    except Exception as error:
        # Never serialize HTTP errors, signed URLs, Request objects, or tokens.
        print('ARTIFACT_TRANSFER_STOP: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
