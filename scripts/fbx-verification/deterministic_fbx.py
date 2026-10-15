"""Guarded, process-local deterministic FBX export for Meshcopia's GLB pilot.

Required launch (the Blender flag is essential, not just the environment):
    PYTHONHASHSEED=0 blender --background --factory-startup \\
      --python-use-system-env --python your_driver.py -- ...

Import a GLB into an empty factory scene, then wrap ONE export:
    with deterministic_fbx_export() as provenance:
        bpy.ops.export_scene.fbx(filepath=out, path_mode='COPY',
                                 embed_textures=True, bake_anim=False, ...)

Same GLB bytes, deterministic scene preparation/options, output basename,
Blender build, addon sources and runtime are required. Use a fresh process for
EACH asset/export: the official exporter caches UUIDs process-wide. This is not
a promise of cross-version, cross-platform or arbitrary-.blend reproducibility.

The supported operator has no timestamp override and _gen_vid_path always
writes an absolute path even with RELATIVE/STRIP path modes. Therefore exactly
two addon functions are wrapped temporarily, only after source-hash checks:
* Header time becomes 1970-01-01 10:00:00, matching encode_bin's fixed
  CreationTime/footer epoch. This is a reproducibility marker, NOT asset age.
* Packed PNG/JPEG media paths become content-derived POSIX relative references
  in both absolute-named and relative-named FBX fields. Embedded bytes are not
  altered; no external texture files are read, written or copied by this hook.

System addon files, source assets and Blender image paths are never modified.
The standard header's constant '/foobar.fbx' placeholder is left unchanged;
it is not a real machine/source path. ApplicationNativeFile must stay empty.
"""
from contextlib import contextmanager
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import os
import re
import sys

FIXED_HEADER_TIME = datetime(1970, 1, 1, 10, 0, 0)
PINNED_SOURCES = {
    'export_fbx_bin.py': 'fd494ffc3d8d01e21b028fa05b8bb7739afecfc09e0c8f2e09ef451b5b0e9e05',
    'fbx_utils.py': 'ffabd204b2cce48670b47de6bb77e8dba06daa77b7efab037c4f157f1ffa80b6',
    'encode_bin.py': '3322a809e0073947e107de8f7e5839dff0956578271e88506eab7a7627f3323f',
}
_active = False


@contextmanager
def deterministic_fbx_export():
    """Temporarily normalize metadata/media paths; yield a JSON-safe audit dict.

    Fails closed for a different Blender/addon, randomized Python hashes,
    nonempty .blend filepath, nested use or unpacked/unknown image formats.
    Does not change geometry, materials, texture pixels or export options.
    """
    import bpy
    from io_scene_fbx import export_fbx_bin
    global _active
    if bpy.app.version != (4, 3, 2):
        raise RuntimeError('This pilot is pinned to Blender 4.3.2.')
    if (os.environ.get('PYTHONHASHSEED') != '0' or sys.flags.hash_randomization
            or '--python-use-system-env' not in sys.argv):
        raise RuntimeError('Launch with PYTHONHASHSEED=0 and --python-use-system-env.')
    if bpy.data.filepath:
        raise RuntimeError('Import the GLB into a fresh unnamed factory scene.')
    if _active:
        raise RuntimeError('Nested deterministic FBX export contexts are unsupported.')
    addon_dir = Path(export_fbx_bin.__file__).parent
    actual_hashes = {name: sha256((addon_dir / name).read_bytes()).hexdigest()
                     for name in PINNED_SOURCES}
    if actual_hashes != PINNED_SOURCES:
        raise RuntimeError('FBX addon source hashes differ; re-audit before updating pins.')
    original_header = export_fbx_bin.fbx_header_elements
    original_path = export_fbx_bin._gen_vid_path
    paths = {}
    audit = {
        'blenderVersion': bpy.app.version_string,
        'blenderBuildHash': bpy.app.build_hash.decode('ascii'),
        'pythonVersion': sys.version.split()[0],
        'pythonHashSeed': '0',
        'fixedHeaderTime': FIXED_HEADER_TIME.isoformat(),
        'addonSourceSha256': actual_hashes,
        'embeddedTextureReferences': [],
    }

    def fixed_header(root, scene_data, time=None):
        return original_header(root, scene_data, time=FIXED_HEADER_TIME)

    def portable_path(img, scene_data):
        media = scene_data.settings.media_settings
        if media.path_mode != 'COPY' or not media.embed_textures:
            raise RuntimeError('Portable packed textures require COPY + embed_textures=True.')
        if img not in paths:
            if not img.packed_file:
                raise RuntimeError('Only packed GLB textures are supported: ' + img.name)
            data = bytes(img.packed_file.data)
            if data.startswith(b'\x89PNG\r\n\x1a\n'):
                suffix = '.png'
            elif data.startswith(b'\xff\xd8\xff'):
                suffix = '.jpg'
            else:
                raise RuntimeError('Unsupported packed image encoding: ' + img.name)
            digest = sha256(data).hexdigest()
            name = re.sub(r'[^a-zA-Z0-9_-]+', '_', img.name).strip('_') or 'image'
            relative = 'textures/' + name + '_' + digest + suffix
            paths[img] = relative
            audit['embeddedTextureReferences'].append({
                'image': img.name, 'relativePath': relative,
                'packedBytes': len(data), 'packedSha256': digest,
            })
        # The official exporter uses the first field as a deduplication key.
        # A content-derived name prevents different images sharing one path.
        return paths[img], paths[img]

    _active = True
    export_fbx_bin.fbx_header_elements = fixed_header
    export_fbx_bin._gen_vid_path = portable_path
    try:
        yield audit
    finally:
        export_fbx_bin.fbx_header_elements = original_header
        export_fbx_bin._gen_vid_path = original_path
        _active = False
