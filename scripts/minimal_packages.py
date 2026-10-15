#!/usr/bin/env python3
"""Local-only, exact-allowlist minimal asset ZIP packaging; never changes inputs.

Every plan and receipt lives outside the archive. Compression/ZIP serialization
is independent of Python zipfile's writer. Reproduction requires zlib 1.3.1.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import struct
import tempfile
import unicodedata
import zipfile
import zlib

SCHEMA = 'meshcopia-minimal-package/1'
REVISION = 1
PACKAGE_VERSION = '1.0.0'
ZLIB_VERSION = '1.3.1'
CHUNK = 1024 * 1024
MAX_FILE_BYTES = 95 * 1024 * 1024
MAX_PACKAGE_BYTES = 2 * 1024 * 1024 * 1024
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}
MODEL_EXT = {'.glb', '.gltf', '.obj', '.stl'}
UNSUPPORTED_MODEL_EXT = {'.fbx', '.blend', '.3mf', '.step', '.stp'}
DEPENDENCY_EXT = IMAGE_EXT | {'.bin', '.mtl'}
ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
VERSION = re.compile(r'\d+\.\d+\.\d+\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
RESERVED = re.compile(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z', re.I)


class PackageError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PackageError(message)


def safe_relative(value):
    require(isinstance(value, str) and bool(value), 'Path must be a nonempty string')
    require(value == unicodedata.normalize('NFC', value), f'Non-NFC path: {value!r}')
    require(not re.search(r'[\x00-\x1f\x7f\\:%?#<>"|*]', value), f'Unsafe path: {value!r}')
    require(not value.startswith('/'), f'Absolute path: {value!r}')
    for part in value.split('/'):
        require(part not in ('', '.', '..'), f'Unsafe path component: {value!r}')
        require(not part.endswith((' ', '.')) and not RESERVED.fullmatch(part), f'Unsafe portable filename: {value!r}')
    require(len(value.encode('utf-8')) <= 65535, 'ZIP path too long')
    return value


def rooted_file(root, relative):
    safe_relative(relative)
    root = Path(root).absolute()
    require(root.resolve(strict=True) == root and root.is_dir(), f'Root must be a real directory, not a symlink: {root}')
    current = root
    for part in relative.split('/'):
        current /= part
        require(not current.is_symlink(), f'Symlinks are prohibited: {current}')
    info = current.stat()
    require(stat.S_ISREG(info.st_mode), f'Expected regular file: {current}')
    require(0 < info.st_size <= MAX_FILE_BYTES, f'Invalid file size: {current}')
    return current


def regular_file(path):
    path = Path(path).absolute()
    return rooted_file(path.parent, path.name)


def hash_file(path):
    h = hashlib.sha256()
    size = 0
    with Path(path).open('rb') as src:
        for block in iter(lambda: src.read(CHUNK), b''):
            size += len(block)
            h.update(block)
    return size, h.hexdigest()


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def load_json(path):
    return json.loads(regular_file(path).read_text(encoding='utf-8'), object_pairs_hook=unique_json)


def record(path, name=None):
    path = regular_file(path)
    size, digest = hash_file(path)
    result = {'path': str(path), 'bytes': size, 'sha256': digest}
    if name is not None:
        result['name'] = safe_relative(name)
    return result


def source_listing(root):
    """Audit entire source tree for links; include only selected payload later."""
    root = Path(root).absolute()
    require(root.resolve(strict=True) == root, 'Source root contains a symlink')
    names = []
    for parent, dirs, files in os.walk(root, followlinks=False):
        for leaf in dirs + files:
            candidate = Path(parent) / leaf
            safe_relative(candidate.relative_to(root).as_posix())
            require(not candidate.is_symlink(), f'Source symlink is prohibited: {candidate}')
        for leaf in files:
            candidate = Path(parent) / leaf
            name = candidate.relative_to(root).as_posix()
            rooted_file(root, name)
            names.append(name)
    require(len({name.casefold() for name in names}) == len(names), 'Source paths collide case-insensitively')
    return sorted(names, key=lambda s: s.encode('utf-8'))


def relative_dependency(owner, reference):
    safe_relative(reference)
    joined = (PurePosixPath(owner).parent / reference).as_posix()
    return safe_relative(joined)


def gltf_document(path):
    if path.suffix.lower() == '.gltf':
        data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_json)
    else:
        with path.open('rb') as f:
            header = f.read(12)
            require(len(header) == 12, 'Truncated GLB header')
            magic, version, length = struct.unpack('<4sII', header)
            require(magic == b'glTF' and version == 2 and length == path.stat().st_size, 'Invalid GLB header')
            chunk_header = f.read(8)
            require(len(chunk_header) == 8, 'Missing GLB JSON chunk')
            size, kind = struct.unpack('<I4s', chunk_header)
            require(kind == b'JSON' and 0 < size <= length - 20, 'Invalid GLB JSON chunk')
            require(size % 4 == 0, 'GLB chunks must be four-byte aligned')
            data = json.loads(f.read(size).decode('utf-8'), object_pairs_hook=unique_json)
            if f.tell() < length:
                binary_header = f.read(8)
                require(len(binary_header) == 8, 'Truncated GLB binary chunk')
                binary_size, binary_kind = struct.unpack('<I4s', binary_header)
                require(binary_kind == b'BIN\x00' and binary_size % 4 == 0 and f.tell() + binary_size == length,
                        'Unexpected GLB chunk or size')
    require(isinstance(data, dict) and data.get('asset', {}).get('version') == '2.0', 'Only glTF 2.0 is supported')
    return data


def dependencies(root, name):
    path = rooted_file(root, name)
    suffix = path.suffix.lower()
    refs = []
    if suffix in {'.glb', '.gltf'}:
        data = gltf_document(path)
        # URI fields in extensions are audited too; unknown file types fail shut.
        def visit(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == 'uri':
                        require(isinstance(v, str), 'glTF URI must be a string')
                        if v.startswith('data:'):
                            require(re.match(r'data:(?:application/octet-stream|application/gltf-buffer|image/(?:png|jpeg|webp));base64,[A-Za-z0-9+/]*={0,2}\Z', v) is not None, 'Unsupported embedded URI')
                        else:
                            refs.append(relative_dependency(name, v))
                    else:
                        visit(v)
            elif isinstance(node, list):
                for item in node:
                    visit(item)
        visit(data)
    elif suffix in {'.obj', '.mtl'}:
        for line in path.read_text(encoding='utf-8').splitlines():
            words = shlex.split(line, comments=True, posix=True)
            if not words:
                continue
            directive = words.pop(0).lower()
            if suffix == '.obj' and directive == 'mtllib':
                require(words, 'OBJ mtllib has no target')
                refs.extend(relative_dependency(name, value) for value in words)
            elif suffix == '.mtl' and (directive.startswith('map_') or directive in {'bump', 'disp', 'decal', 'refl', 'norm'}):
                fixed = {'-blendu': 1, '-blendv': 1, '-boost': 1, '-mm': 2, '-texres': 1, '-clamp': 1, '-bm': 1, '-imfchan': 1, '-type': 1, '-cc': 1}
                while words and words[0].startswith('-'):
                    option = words.pop(0).lower()
                    if option in {'-o', '-s', '-t'}:
                        consumed = 0
                        while words and consumed < 3:
                            try:
                                float(words[0])
                            except ValueError:
                                break
                            words.pop(0)
                            consumed += 1
                        require(consumed > 0, f'Missing MTL option value: {option}')
                    else:
                        require(option in fixed and len(words) > fixed[option], f'Unsupported or incomplete MTL option: {option}')
                        del words[:fixed[option]]
                require(len(words) == 1, 'MTL image target must be one unambiguous path (quote spaces)')
                refs.append(relative_dependency(name, words[0]))
    for ref in refs:
        expected = {'.mtl'} if suffix == '.obj' else (IMAGE_EXT if suffix == '.mtl' else IMAGE_EXT | {'.bin'})
        require(PurePosixPath(ref).suffix.lower() in expected, f'Unsupported dependency type: {name} -> {ref}')
        rooted_file(root, ref)
    return sorted(set(refs), key=lambda s: s.encode('utf-8'))


def payload_closure(asset_dir, metadata):
    root = asset_dir / 'source'
    all_names = source_listing(root)
    if metadata['type'] == 'texture':
        maps = metadata.get('maps')
        require(isinstance(maps, dict) and maps.get('baseColor'), 'Texture needs declared baseColor map')
        names = set()
        for value in maps.values():
            safe_relative(value)
            require(PurePosixPath(value).suffix.lower() in IMAGE_EXT, 'Texture maps must be supported images')
            rooted_file(root, value)
            names.add(value)
        return [{'source': name, 'name': PurePosixPath(name).name} for name in sorted(names, key=lambda s: s.encode('utf-8'))], []
    require(not any(PurePosixPath(name).suffix.lower() in UNSUPPORTED_MODEL_EXT for name in all_names),
            'An original source format needs an explicit dependency verifier before packaging')
    roots = [name for name in all_names if PurePosixPath(name).suffix.lower() in MODEL_EXT]
    require(roots, 'No supported model files')
    require(metadata.get('preview') in roots, 'Declared model preview must be a supported model root')
    included, graph, destinations = set(), {}, {}
    # Put each model at top level. Keep only dependency-relative folders.
    for model in roots:
        prefix = PurePosixPath(model).parent
        pending = [model]
        while pending:
            name = pending.pop()
            mapped = PurePosixPath(name).relative_to(prefix).as_posix()
            key = mapped.casefold()
            require(key not in destinations or destinations[key]['source'] == name,
                    f'Flattening would collide: {name} -> {mapped}')
            destinations[key] = {'source': name, 'name': mapped}
            if name in included:
                continue
            included.add(name)
            refs = dependencies(root, name)
            graph[name] = {'file': name, 'requires': refs}
            pending.extend(refs)
    mapped = sorted(destinations.values(), key=lambda row: row['name'].encode('utf-8'))
    return mapped, sorted(graph.values(), key=lambda row: row['file'].encode('utf-8'))


def validate_notice(path):
    data = regular_file(path).read_bytes()
    require(len(data) <= 32 * 1024, 'LICENSE.txt must remain a short notice (max 32 KiB)')
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise PackageError('LICENSE.txt must be UTF-8') from exc
    require('\x00' not in text and text.endswith('\n'), 'LICENSE.txt requires valid text and a final newline')
    require('https://creativecommons.org/licenses/by/4.0/' in text and 'CC BY 4.0' in text, 'Missing CC BY 4.0 name or official license link')
    require(not any(part in text for part in ('/workspace/', '/tmp/', '/home/', '/Users/', 'file://')), 'Local path leaked into license notice')
    return data


def make_plan(asset_dir, license_path, *, fbx_path=None, fbx_sha256=None,
              pipeline_sha256=None, fbx_report=None, allow_draft=False):
    asset_dir = Path(asset_dir).absolute()
    metadata_path = rooted_file(asset_dir, 'asset.json')
    metadata = load_json(metadata_path)
    asset_id, version = metadata.get('id'), metadata.get('version')
    require(isinstance(asset_id, str) and ID.fullmatch(asset_id) and asset_id == asset_dir.name, 'Invalid asset ID')
    require(isinstance(version, str) and VERSION.fullmatch(version), 'Invalid asset version')
    require(metadata.get('type') in {'model', 'texture'}, 'Unsupported asset type')
    require(metadata.get('license') == 'CC-BY-4.0', 'Only explicitly CC-BY-4.0 metadata is accepted')
    require(metadata.get('status') in ({'public', 'hidden', 'draft'} if allow_draft else {'public', 'hidden'}), 'Draft/private asset requires explicit local preparation flag')
    notice = validate_notice(license_path)
    text = notice.decode('utf-8')
    from minimal_notices import modification_text
    require(bool(metadata.get('author')) and f"{metadata['author']} / Meshcopia" in text,
            'Creator/designated attribution is missing from the notice')
    require(f"Copyright (c) {metadata['created'][:4]} {metadata['author']}" in text.splitlines(),
            'Actual baseline copyright notice is missing')
    require(f'Source: https://xenoah.github.io/meshcopia/assets/{asset_id}/' in text.splitlines(),
            'Canonical source/detail URL is missing')
    require('Provided as-is, without warranties' in text and re.search(r'^Changes: .+', text, re.M),
            'Warranty disclaimer or modification indication is missing')
    provenance = metadata.get('provenance', {})
    require(not provenance.get('sourceUrl') or f"Original source: {provenance['sourceUrl']}" in text.splitlines(),
            'Original source URL is missing')
    require(not provenance.get('changes') or modification_text(provenance['changes']) in text,
            'Existing modification description is missing')
    entries = [record(license_path, 'LICENSE.txt')]
    graph = []
    kind = metadata['type']
    if fbx_path is not None:
        require(kind == 'model', 'FBX packaging needs model metadata')
        require(isinstance(fbx_sha256, str) and HASH.fullmatch(fbx_sha256), 'Canonical FBX SHA-256 is required')
        require(isinstance(pipeline_sha256, str) and HASH.fullmatch(pipeline_sha256), 'Conversion pipeline SHA-256 is required')
        fbx = regular_file(fbx_path)
        require(fbx.suffix.lower() == '.fbx', 'FBX payload needs .fbx extension')
        with fbx.open('rb') as f:
            require(f.read(23) == b'Kaydara FBX Binary  \x00\x1a\x00', 'Expected binary FBX')
        entry = record(fbx, f'{asset_id}.fbx')
        require(entry['sha256'] == fbx_sha256, 'Canonical FBX SHA-256 mismatch')
        require(fbx_report is not None, 'Reviewed clean-reimport FBX report is required')
        report = load_json(fbx_report)
        recipe = report.get('recipeSha256')
        require(isinstance(recipe, dict) and bool(recipe) and all(isinstance(value, str) and HASH.fullmatch(value) for value in recipe.values()),
                'FBX report has no valid conversion recipe')
        recipe_hash = hashlib.sha256(json.dumps(recipe, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        require(recipe_hash == pipeline_sha256, 'FBX report conversion recipe does not match the pinned pipeline')
        require(str(metadata.get('preview', '')).endswith('.glb') and
                hash_file(rooted_file(asset_dir / 'source', metadata['preview']))[1] == report.get('sourceGlbSha256'),
                'FBX report does not bind the current original GLB')
        require('Converted unchanged source GLB geometry to FBX, with documented compatible material/texture derivatives.' in text,
                'Prior FBX conversion/material/texture modification indication is missing')
        require(report.get('id') == asset_id and report.get('passed') is True and
                report.get('fbxSha256') == fbx_sha256 and report.get('fbxBytes') == entry['bytes'] and
                report.get('container', {}).get('selfContainedImages') is True and
                report.get('container', {}).get('noWorkspacePathInBinary') is True,
                'FBX report must verify this exact self-contained payload')
        entries.append(entry)
        kind = 'fbx'
    else:
        require(fbx_sha256 is None and pipeline_sha256 is None and fbx_report is None, 'FBX evidence supplied without an FBX')
        names, graph = payload_closure(asset_dir, metadata)
        for mapping in names:
            item = record(asset_dir / 'source' / mapping['source'], mapping['name'])
            item['sourceName'] = mapping['source']
            entries.append(item)
    entries.sort(key=lambda item: item['name'].encode('utf-8'))
    # Prove that stripping useless enclosing directories preserves every URI.
    by_source = {entry['sourceName']: entry['name'] for entry in entries if 'sourceName' in entry}
    for edge in graph:
        owner_source = PurePosixPath(edge['file'])
        owner_output = PurePosixPath(by_source[edge['file']])
        for dependency in edge['requires']:
            reference = PurePosixPath(dependency).relative_to(owner_source.parent).as_posix()
            require((owner_output.parent / reference).as_posix() == by_source[dependency],
                    f'Packaging would break a relative dependency: {edge["file"]} -> {dependency}')
    require(len({row['name'].casefold() for row in entries}) == len(entries), 'Archive names collide')
    require(sum(row['bytes'] for row in entries) <= MAX_PACKAGE_BYTES, 'Package exceeds bounded size')
    filename = f'{asset_id}-{version}-' + ('fbx-' if kind == 'fbx' else '') + f'minimal-{PACKAGE_VERSION}.zip'
    return {
        'schema': SCHEMA, 'packagingRevision': REVISION, 'packageVersion': PACKAGE_VERSION, 'id': asset_id,
        'version': version, 'kind': kind, 'filename': filename,
        'inputs': {'assetDirectory': str(asset_dir), 'metadata': record(metadata_path),
                   'license': record(license_path), 'allowDraftPreparation': bool(allow_draft),
                   'fbx': str(Path(fbx_path).absolute()) if fbx_path is not None else None,
                   'canonicalFbxSha256': fbx_sha256, 'conversionPipelineSha256': pipeline_sha256,
                   'fbxReport': record(fbx_report) if fbx_report is not None else None},
        'zipProfile': {'compression': 'raw-deflate', 'level': 9, 'memLevel': 8, 'strategy': 0,
                       'zlibVersion': ZLIB_VERSION, 'timestamp': '1980-01-01T00:00:00Z',
                       'permissions': '100644', 'utf8': True, 'zip64': False},
        'dependencies': graph, 'entries': entries,
    }


def validate_plan(plan):
    require(plan.get('schema') == SCHEMA and plan.get('packagingRevision') == REVISION, 'Unsupported plan schema/revision')
    config = plan['inputs']
    expected = make_plan(config['assetDirectory'], config['license']['path'],
                         fbx_path=config['fbx'], fbx_sha256=config['canonicalFbxSha256'],
                         pipeline_sha256=config['conversionPipelineSha256'],
                         fbx_report=config['fbxReport']['path'] if config['fbxReport'] else None,
                         allow_draft=config['allowDraftPreparation'])
    require(expected == plan, 'Plan differs from freshly resolved, hashed input closure')
    return expected


def write_archive(target, plan):
    """Write to a seekable binary handle, one source chunk at a time."""
    validate_plan(plan)
    require(zlib.ZLIB_VERSION == ZLIB_VERSION and zlib.ZLIB_RUNTIME_VERSION == ZLIB_VERSION,
            f'Pinned zlib {ZLIB_VERSION} is required (build/runtime {zlib.ZLIB_VERSION}/{zlib.ZLIB_RUNTIME_VERSION})')
    require(target.tell() == 0, 'Output must start at byte zero')
    central = []
    for entry in plan['entries']:
        name = entry['name'].encode('utf-8')
        offset = target.tell()
        # ZIP 2.0, UTF-8, DEFLATE, 1980-01-01, no extras or data descriptor.
        local = lambda crc, compressed: struct.pack('<IHHHHHIIIHH', 0x04034B50, 20, 0x800, 8, 0, 33, crc, compressed, entry['bytes'], len(name), 0) + name
        target.write(local(0, 0))
        payload_start = target.tell()
        compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
        checksum, size, digest = 0, 0, hashlib.sha256()
        with regular_file(entry['path']).open('rb') as src:
            for block in iter(lambda: src.read(CHUNK), b''):
                size += len(block)
                require(size <= entry['bytes'], 'Source grew during packaging')
                digest.update(block)
                checksum = zlib.crc32(block, checksum)
                target.write(compressor.compress(block))
        target.write(compressor.flush())
        require(size == entry['bytes'] and digest.hexdigest() == entry['sha256'], f'Input changed during packaging: {entry["name"]}')
        end = target.tell()
        compressed = end - payload_start
        target.seek(offset)
        target.write(local(checksum, compressed))
        target.seek(end)
        central.append(struct.pack('<IHHHHHHIIIHHHHHII', 0x02014B50, (3 << 8) | 20, 20, 0x800, 8, 0, 33, checksum, compressed, size, len(name), 0, 0, 0, 0, 0o100644 << 16, offset) + name)
    central_start = target.tell()
    for header in central:
        target.write(header)
    central_size = target.tell() - central_start
    require(target.tell() < 2 ** 32 and len(central) < 65535, 'ZIP64 is deliberately unsupported')
    target.write(struct.pack('<IHHHHIIH', 0x06054B50, 0, 0, len(central), len(central), central_size, central_start, 0))
    target.flush()


def verify_archive(source, plan):
    """Reject missing/extra entries, traversal, dependencies, notice or byte drift.

    The supplied plan is re-resolved from immutable local inputs before trusting
    its allowlist. Verification does not extract archive contents.
    """
    validate_plan(plan)
    expected = {entry['name']: entry for entry in plan['entries']}
    if hasattr(source, 'seek'):
        source.seek(0)
    with zipfile.ZipFile(source, 'r') as archive:
        require(not archive.comment, 'ZIP comments are forbidden')
        infos = archive.infolist()
        names = [info.filename for info in infos]
        for name in names:
            safe_relative(name)
        require(names == sorted(expected, key=lambda s: s.encode('utf-8')), 'ZIP must contain exactly the sorted payload allowlist plus one LICENSE.txt')
        require(len(names) == len(set(name.casefold() for name in names)), 'Duplicate or colliding ZIP entries')
        cursor = 0
        central_headers = []
        for info in infos:
            require(info.header_offset == cursor, 'ZIP contains a prefix, gap, or unlisted entry')
            name_bytes = info.filename.encode('utf-8')
            require(info.compress_size <= info.file_size + 1024 * 1024, 'Unexpected compressed payload size')
            canonical_local = struct.pack('<IHHHHHIIIHH', 0x04034B50, 20, 0x800, 8, 0, 33,
                                          info.CRC, info.compress_size, info.file_size, len(name_bytes), 0) + name_bytes
            archive.fp.seek(cursor)
            require(archive.fp.read(len(canonical_local)) == canonical_local, 'Noncanonical local ZIP header')
            central_headers.append(struct.pack('<IHHHHHHIIIHHHHHII', 0x02014B50, (3 << 8) | 20, 20, 0x800, 8, 0, 33,
                                               info.CRC, info.compress_size, info.file_size, len(name_bytes), 0, 0, 0, 0,
                                               0o100644 << 16, cursor) + name_bytes)
            cursor += len(canonical_local) + info.compress_size
            require(info.orig_filename == info.filename, 'NUL-truncated ZIP name')
            require(not info.is_dir() and not info.extra and not info.comment, 'Directories, ZIP extras and comments are prohibited')
            require(info.flag_bits == 0x800 and info.compress_type == 8, 'Unexpected ZIP flags/compression')
            require(info.date_time == (1980, 1, 1, 0, 0, 0) and info.create_system == 3 and info.external_attr == 0o100644 << 16, 'Noncanonical ZIP attributes')
            entry = expected[info.filename]
            require(info.file_size == entry['bytes'], f'Uncompressed size mismatch: {info.filename}')
            digest, size = hashlib.sha256(), 0
            with archive.open(info) as src:
                for block in iter(lambda: src.read(CHUNK), b''):
                    size += len(block)
                    require(size <= entry['bytes'], 'Expanded ZIP exceeds expected file size')
                    digest.update(block)
            require(size == entry['bytes'] and digest.hexdigest() == entry['sha256'], f'Payload hash mismatch: {info.filename}')
        central_data = b''.join(central_headers)
        archive.fp.seek(cursor)
        expected_tail = central_data + struct.pack('<IHHHHIIH', 0x06054B50, 0, 0, len(infos), len(infos), len(central_data), cursor, 0)
        require(archive.fp.read(len(expected_tail) + 1) == expected_tail, 'Noncanonical central directory, trailing data, or ZIP comment')
    return {'entryCount': len(expected), 'payloadBytes': sum(row['bytes'] for row in expected.values()), 'exactAllowlist': True, 'payloadHashesVerified': True}


def verify_extracted_package(source, plan, *, temporary_directory=None):
    """Verify first, then extract one bounded package to a fresh temporary tree.

    This proves file identity and dependency resolvability, not DCC import quality.
    No original source directory is consulted by the extracted dependency parser.
    """
    result = verify_archive(source, plan)
    if hasattr(source, 'seek'):
        source.seek(0)
    with tempfile.TemporaryDirectory(prefix='minimal-extracted-', dir=temporary_directory) as folder:
        root = Path(folder)
        with zipfile.ZipFile(source, 'r') as archive:
            for info in archive.infolist():
                destination = root.joinpath(*safe_relative(info.filename).split('/'))
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, destination.open('xb') as out:
                    while block := src.read(CHUNK):
                        out.write(block)
        for entry in plan['entries']:
            size, digest = hash_file(root / entry['name'])
            require(size == entry['bytes'] and digest == entry['sha256'], 'Clean extraction changed payload bytes')
        if plan['kind'] == 'model':
            by_source = {entry['sourceName']: entry['name'] for entry in plan['entries'] if 'sourceName' in entry}
            for edge in plan['dependencies']:
                actual = dependencies(root, by_source[edge['file']])
                expected = sorted((by_source[name] for name in edge['requires']), key=lambda name: name.encode('utf-8'))
                require(actual == expected, 'Extracted relative dependency closure changed')
        result.update(cleanExtractionVerified=True, dependencyClosureVerified=True,
                      applicationImportTested=False)
    return result


def write_new_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out:
        out.write(json_bytes(data))


def package(plan, *, output=None, receipt_path=None, temporary_directory=None):
    """Build and verify once; discard ZIP unless a new output is explicit."""
    if output is not None:
        output = Path(output).absolute()
        require(output.name == plan['filename'], 'Output must use immutable plan filename')
        require(not output.exists() and not output.is_symlink(), f'Refusing to replace existing output: {output}')
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_directory = output.parent
    if receipt_path is not None:
        require(not Path(receipt_path).exists() and not Path(receipt_path).is_symlink(), 'Refusing to replace existing receipt')
    with tempfile.NamedTemporaryFile(mode='w+b', prefix='.minimal-package-', suffix='.zip', dir=temporary_directory) as tmp:
        write_archive(tmp, plan)
        verified = verify_extracted_package(tmp, plan, temporary_directory=temporary_directory)
        size, digest = hash_file(tmp.name)
        receipt = {'schema': 'meshcopia-minimal-package-receipt/1', 'packagingRevision': REVISION,
                   'packageVersion': PACKAGE_VERSION, 'id': plan['id'], 'kind': plan['kind'], 'filename': plan['filename'],
                   'archiveBytes': size, 'archiveSha256': digest,
                   'planSha256': hashlib.sha256(json_bytes(plan)).hexdigest(),
                   'conversionPipelineSha256': plan['inputs']['conversionPipelineSha256'],
                   'entries': [{k: e[k] for k in ('name', 'bytes', 'sha256')} for e in plan['entries']],
                   'sourceFiles': [{'name': e.get('sourceName', e['name']), 'bytes': e['bytes'], 'sha256': e['sha256']}
                                   for e in plan['entries'] if e['name'] != 'LICENSE.txt'],
                   'notice': {'filename': 'LICENSE.txt', 'text': Path(plan['inputs']['license']['path']).read_text(encoding='utf-8'),
                              'bytes': plan['inputs']['license']['bytes'], 'sha256': plan['inputs']['license']['sha256']},
                   'verification': verified, 'retainedArchive': output is not None}
        if output is not None:
            os.link(tmp.name, output)  # Atomic, same-filesystem, and cannot overwrite.
        if receipt_path is not None:
            write_new_json(receipt_path, receipt)
        return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan', help='Resolve and hash an exact local payload closure')
    p.add_argument('--asset-dir', required=True)
    p.add_argument('--license', required=True)
    p.add_argument('--manifest', required=True)
    p.add_argument('--fbx')
    p.add_argument('--fbx-sha256')
    p.add_argument('--pipeline-sha256')
    p.add_argument('--fbx-report')
    p.add_argument('--allow-draft-preparation', action='store_true')
    p = sub.add_parser('build', help='Build and verify; no retained ZIP without --output')
    p.add_argument('--manifest', required=True)
    p.add_argument('--output')
    p.add_argument('--receipt', required=True)
    p.add_argument('--temporary-directory')
    p = sub.add_parser('verify', help='Verify an archive against freshly resolved plan inputs')
    p.add_argument('--manifest', required=True)
    p.add_argument('--archive', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'plan':
            plan = make_plan(args.asset_dir, args.license, fbx_path=args.fbx, fbx_sha256=args.fbx_sha256,
                             pipeline_sha256=args.pipeline_sha256, fbx_report=args.fbx_report, allow_draft=args.allow_draft_preparation)
            write_new_json(args.manifest, plan)
            print(json.dumps({'id': plan['id'], 'filename': plan['filename'], 'entries': len(plan['entries'])}))
        elif args.command == 'build':
            print(json.dumps(package(load_json(args.manifest), output=args.output, receipt_path=args.receipt,
                                     temporary_directory=args.temporary_directory), sort_keys=True))
        else:
            print(json.dumps(verify_archive(args.archive, load_json(args.manifest)), sort_keys=True))
    except (PackageError, OSError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'minimal package rejected: {exc}\n')


if __name__ == '__main__':
    main()
