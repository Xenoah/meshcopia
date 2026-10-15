"""Create new FBX sidecars from unchanged GLBs; inspect a clean FBX reimport.

Run with Blender 4.3.2. This is interchange QA, not a Unity/runtime certification.
No source asset is saved or modified. FBX material conversion is lossy by design.
"""
from pathlib import Path
import argparse, hashlib, json, os, platform, re, struct, sys, zlib
import bpy
import numpy as np
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

# Revision 4: float32 power dispatch changes 16-bit gamma-bake rounding.
# Set this in the process environment BEFORE Blender/NumPy initialize. Merely
# assigning it here is too late; fail closed on missing or ineffective settings.
BASELINE_DISABLED_CPU_FEATURES = (
    'AVX2', 'FMA3', 'AVX512F', 'AVX512_SKX', 'AVX512_CLX',
    'AVX512_CNL', 'AVX512_ICL',
)
configured_cpu_features = set(os.environ.get('NPY_DISABLE_CPU_FEATURES', '').split(','))
assert set(BASELINE_DISABLED_CPU_FEATURES) <= configured_cpu_features, (
    'Launch Blender with NPY_DISABLE_CPU_FEATURES=' + ','.join(BASELINE_DISABLED_CPU_FEATURES))
actual_cpu_features = np._core._multiarray_umath.__cpu_features__
assert all(name in actual_cpu_features and not actual_cpu_features[name]
           for name in BASELINE_DISABLED_CPU_FEATURES), 'NumPy baseline CPU guard failed'
cpu_baseline = {'policy': 'numpy-float32-gamma-baseline-v4',
                'requiredDisabledFeatures': list(BASELINE_DISABLED_CPU_FEATURES),
                'actualRequiredFeatureFlags': {name: bool(actual_cpu_features[name])
                                               for name in BASELINE_DISABLED_CPU_FEATURES}}

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--expected-sha256', default='')
parser.add_argument('--unique-image-paths', action='store_true')
parser.add_argument('--existing-fbx', default='')
parser.add_argument('--normalize-materials', action='store_true')
parser.add_argument('--deterministic', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source = Path(args.source).resolve()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
sha = lambda data: hashlib.sha256(data).hexdigest()
source_hash = sha(source.read_bytes())
if args.expected_sha256:
    assert source_hash == args.expected_sha256
fbx = Path(args.existing_fbx).resolve() if args.existing_fbx else out / (source.stem + '.fbx')
assert args.existing_fbx or not fbx.exists(), 'Never overwrite an existing sidecar; use a separate trial directory.'


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0


def snapshot():
    positions, normals, uvs, assignments, colors = [], [], [], [], []
    objects, material_records, attribute_colors = [], {}, []
    all_coords = []
    for obj in sorted((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: o.name):
        mesh = obj.data
        mesh.calc_loop_triangles()
        xyz = np.array([obj.matrix_world @ v.co for v in mesh.vertices], dtype=np.float64)
        all_coords.append(xyz)
        normal_matrix = np.array(obj.matrix_world.to_3x3().inverted().transposed(), dtype=np.float64)
        cn = np.array([n.vector[:] for n in mesh.corner_normals], dtype=np.float64) @ normal_matrix.T
        lens = np.linalg.norm(cn, axis=1)
        cn /= np.maximum(lens[:, None], 1e-30)
        uv = np.array([x.uv[:] for x in mesh.uv_layers.active.data], dtype=np.float64) if mesh.uv_layers.active else None
        color_attr = mesh.color_attributes.active_color
        col = np.array([x.color[:] for x in color_attr.data], dtype=np.float64) if color_attr else None
        if col is not None: attribute_colors.append(col)
        objects.append({'name': obj.name, 'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles),
                        'uvLayers': len(mesh.uv_layers), 'materialSlots': len(obj.material_slots),
                        'colorLayers': len(mesh.color_attributes),
                        'triangleVertexIndexSha256': sha(np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int64).tobytes()),
                        'uvLayerHashes': {layer.name: sha(np.array([v.uv[:] for v in layer.data],dtype=np.float32).tobytes()) for layer in mesh.uv_layers}})
        for tri in mesh.loop_triangles:
            co = xyz[list(tri.vertices)]
            # The exporter retains triangle and vertex ordering. Index-based
            # correspondence avoids ambiguous floating-point spatial sorting
            # on symmetrical/overlapping surfaces. Counts and names are checked.
            order = np.argsort(tri.vertices)
            loops = np.array(tri.loops)[order]
            positions.append(co[order].reshape(-1))
            normals.append(cn[loops].reshape(-1))
            uvs.append(uv[loops].reshape(-1) if uv is not None else [float('nan')] * 6)
            ci = np.array(tri.vertices)[order] if color_attr and color_attr.domain == 'POINT' else loops
            colors.append(col[ci].reshape(-1) if col is not None else np.ones(12))
            mat = obj.material_slots[tri.material_index].material if obj.material_slots else None
            assignments.append(mat.name if mat else '')
    for mat in sorted(bpy.data.materials, key=lambda m: m.name):
        if not mat.users:
            continue
        w = PrincipledBSDFWrapper(mat, is_readonly=True)
        images = []
        for node in (mat.node_tree.nodes if mat.node_tree else []):
            if node.type == 'TEX_IMAGE' and node.image:
                img = node.image
                pixels = np.empty(len(img.pixels), dtype=np.float32)
                img.pixels.foreach_get(pixels)
                images.append({'name': img.name, 'size': list(img.size), 'channels': img.channels,
                               'pixelSha256': sha(pixels.tobytes()), 'filepath': img.filepath,
                               'packed': bool(img.packed_file), 'extension': node.extension,
                               'colorSpace': img.colorspace_settings.name})
        vals = {}
        for key in ('base_color', 'metallic', 'roughness', 'alpha', 'ior', 'emission_color', 'emission_strength', 'transmission', 'specular', 'normalmap_strength'):
            value = getattr(w, key, None)
            if value is not None:
                vals[key] = list(value) if not isinstance(value, (float, int)) else value
        connections = {}
        for role in ('base_color', 'metallic', 'roughness', 'alpha', 'emission_color', 'normalmap', 'specular'):
            tex = getattr(w, role + '_texture', None)
            if tex is not None and tex.image is not None:
                im = tex.image
                pixels = np.empty(len(im.pixels), dtype=np.float32); im.pixels.foreach_get(pixels)
                connections[role] = {'pixelSha256': sha(pixels.tobytes()), 'size': list(im.size),
                    'colorSpace': im.colorspace_settings.name if role != 'alpha' else 'linear alpha', 'extension': tex.extension,
                    'alphaRange': [float(pixels[3::4].min()), float(pixels[3::4].max())],
                    'scale': list(tex.scale), 'translation': list(tex.translation), 'rotation': list(tex.rotation)}
        material_records[mat.name] = {'values': vals, 'backfaceCulling': mat.use_backface_culling,
                                      'images': images, 'textureConnections': connections}
    xyz = np.concatenate(all_coords)
    pos = np.array(positions)
    no = np.array(normals)
    uv = np.array(uvs)
    # Diagnostic geometry hash; numeric comparisons below use original floats.
    quantized = np.rint(pos / 1e-6).astype(np.int64)
    assignments = np.array(assignments)
    summary = {'objects': objects, 'meshObjectCount': len(objects), 'triangleCount': len(pos),
               'vertexCount': sum(o['vertices'] for o in objects), 'materials': material_records,
               'boundsBlenderZUpMeters': [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()],
               'dimensionsBlenderZUpMeters': np.ptp(xyz, axis=0).tolist(),
               'geometryQuantizedMicrometerSha256': sha(quantized.tobytes()),
               'uvMissingCorners': int(np.isnan(uv).sum() // 2),
               'uvRange': [np.nanmin(uv).item(), np.nanmax(uv).item()],
               'nonFinitePositions': int((~np.isfinite(pos)).sum()),
               'nonFiniteNormals': int((~np.isfinite(no)).sum()),
               'nonFiniteUvs': int((~np.isfinite(uv)).sum()),
               'zeroLengthNormals': int((np.linalg.norm(no.reshape(-1,3),axis=1)<1e-8).sum())}
    return summary, pos, no, uv, assignments, np.array(colors), (np.concatenate(attribute_colors) if attribute_colors else np.empty((0,4)))


reset()
bpy.ops.import_scene.gltf(filepath=str(source))
source_before = snapshot()
normalization = None
if args.normalize_materials:
    sys.path.insert(0,str(Path(__file__).parent))
    from normalize_fbx_materials import normalize
    normalization = normalize(source, out)
before = snapshot() if normalization else source_before
if args.unique_image_paths:
    for image in bpy.data.images:
        if image.packed_file:
            # FBX uses filenames as embedded-video identifiers. Empty glTF paths
            # otherwise collide and can assign the last image to every material.
            safe = re.sub(r'[^a-zA-Z0-9_-]+', '_', image.name)
            raw_hash = sha(image.packed_file.data)
            suffix = '.jpg' if bytes(image.packed_file.data[:2]) == b'\xff\xd8' else '.png'
            image.filepath_raw = str(out / 'textures' / (safe + '_' + raw_hash[:16] + suffix))
export_settings = dict(global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                       use_space_transform=True, bake_space_transform=False,
                       object_types={'MESH', 'EMPTY'}, use_mesh_modifiers=True,
                       mesh_smooth_type='OFF', use_tspace=False, use_triangles=True,
                       colors_type='LINEAR',
                       add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True,
                       axis_forward='-Z', axis_up='Y')
determinism = None
if not args.existing_fbx:
    if args.deterministic:
        sys.path.insert(0,str(Path(__file__).parent))
        from deterministic_fbx import deterministic_fbx_export
        with deterministic_fbx_export() as determinism:
            bpy.ops.export_scene.fbx(filepath=str(fbx), **export_settings)
    else:
        bpy.ops.export_scene.fbx(filepath=str(fbx), **export_settings)
fbx_hash = sha(fbx.read_bytes())
# A hardlink is a separate location without a duplicate binary allocation.
# Embedded textures must reimport from this initially empty directory.
isolation = out / 'clean-reimport'
isolation.mkdir()
isolated_fbx = isolation / fbx.name
os.link(fbx, isolated_fbx)
reset()
bpy.ops.import_scene.fbx(filepath=str(isolated_fbx), use_manual_orientation=False,
                         use_image_search=False, use_custom_normals=True, global_scale=1.0, colors_type='LINEAR')
after = snapshot()
geometry = {}
same_shape = before[1].shape == after[1].shape
geometry['triangleCountEqual'] = before[0]['triangleCount'] == after[0]['triangleCount']
geometry['vertexCountEqual'] = before[0]['vertexCount'] == after[0]['vertexCount']
geometry['meshObjectCountEqual'] = before[0]['meshObjectCount'] == after[0]['meshObjectCount']
geometry['meshObjectNamesEqual'] = [o['name'] for o in before[0]['objects']] == [o['name'] for o in after[0]['objects']]
geometry['maxBoundsDeltaMeters'] = float(np.max(np.abs(np.array(before[0]['boundsBlenderZUpMeters']) - np.array(after[0]['boundsBlenderZUpMeters']))))
if same_shape:
    geometry['maxCorrespondingCornerPositionDeltaMeters'] = float(np.max(np.abs(before[1] - after[1])))
    geometry['maxCorrespondingCornerUvDelta'] = float(np.nanmax(np.abs(before[3] - after[3])))
    geometry['maxCorrespondingCornerColorDelta'] = float(np.max(np.abs(before[5] - after[5])))
    dots = np.sum(before[2].reshape(-1, 3) * after[2].reshape(-1, 3), axis=1)
    geometry['maxCorrespondingCornerNormalAngleDegrees'] = float(np.degrees(np.arccos(np.clip(dots.min(), -1, 1))))
    geometry['materialAssignmentsEqual'] = bool(np.array_equal(before[4], after[4]))
geometry['windingAndVertexIndicesPreserved'] = [o['triangleVertexIndexSha256'] for o in before[0]['objects']] == [o['triangleVertexIndexSha256'] for o in after[0]['objects']]
geometry['colorLayerCountsPreserved'] = [o['colorLayers'] for o in before[0]['objects']] == [o['colorLayers'] for o in after[0]['objects']]
geometry['allGeometryAttributesFinite'] = all(d[0][k] == 0 for d in (before,after) for k in ('nonFinitePositions','nonFiniteNormals','nonFiniteUvs','zeroLengthNormals'))
geometry['sourceGeometryUnchangedByNormalization'] = np.array_equal(source_before[1],before[1]) and np.array_equal(source_before[2],before[2]) and [o['triangleVertexIndexSha256'] for o in source_before[0]['objects']] == [o['triangleVertexIndexSha256'] for o in before[0]['objects']]
geometry['positionToleranceMeters'] = max(5e-5, max(before[0]['dimensionsBlenderZUpMeters']) * 5e-6)
geometry['passed'] = bool(same_shape and geometry['triangleCountEqual'] and geometry['vertexCountEqual'] and geometry['meshObjectCountEqual']
                          and geometry['meshObjectNamesEqual'] and geometry['windingAndVertexIndicesPreserved']
                          and geometry['allGeometryAttributesFinite'] and geometry['sourceGeometryUnchangedByNormalization'] and geometry['colorLayerCountsPreserved']
                          and geometry['maxBoundsDeltaMeters'] < geometry['positionToleranceMeters']
                          and geometry.get('maxCorrespondingCornerPositionDeltaMeters', 1) < geometry['positionToleranceMeters']
                          and geometry.get('maxCorrespondingCornerUvDelta', 1) < 2e-5
                          and geometry.get('maxCorrespondingCornerColorDelta', 1) < 2e-5
                          and geometry.get('maxCorrespondingCornerNormalAngleDegrees', 180) < .1
                          and geometry.get('materialAssignmentsEqual', False))
# Store original glTF linear float colors directly. Blender's default SRGB
# option quantizes colors to BYTE_COLOR; LINEAR import retains FLOAT_COLOR.
# These attributes are for editing; the baked basic color does not need them.
from io_scene_fbx import parse_fbx
fbx_tree, fbx_version = parse_fbx.parse(str(fbx))
file_colors = []
def collect_colors(element):
    if element.id == b'LayerElementColor':
        for child in element.elems:
            if child.id == b'Colors': file_colors.append(np.array(child.props[0],dtype=np.float64).reshape(-1,4))
    for child in element.elems: collect_colors(child)
collect_colors(fbx_tree)
expected_colors = np.unique(before[6], axis=0)
raw_colors = np.unique(np.concatenate(file_colors),axis=0) if file_colors else np.empty((0,4))
expected_encoded=expected_colors.copy()
color_delta=float(np.max(abs(raw_colors-expected_encoded))) if raw_colors.shape==expected_encoded.shape and len(raw_colors) else (0. if raw_colors.shape==expected_encoded.shape else None)
color_verification={'sourceUniqueColors':len(expected_colors),'fbxUniqueColors':len(raw_colors),
                    'encoding':'FBX LINEAR float colors, matching source glTF linear colors',
                    'maxRawEncodedColorDelta':color_delta,'fileColorValuesPreserved':color_delta is not None and color_delta<2e-6,
                    'linearBlenderReimportMaxDelta':geometry.get('maxCorrespondingCornerColorDelta'),
                    'reimportLimitation':'For original editable vertex colors choose LINEAR FBX color import. Basic appearance uses derived textures/materials and does not depend on vertex-color shader setup.'}
images = [i for m in after[0]['materials'].values() for i in m['images']]
for i in images:
    i['resolvedInsideCleanReimport'] = Path(bpy.path.abspath(i['filepath'])).resolve().is_relative_to(isolation)
material_comparison = {}
for name, bmat in before[0]['materials'].items():
    amat = after[0]['materials'].get(name, {})
    bc = bmat['textureConnections']; ac = amat.get('textureConnections', {})
    extra = set(ac) - set(bc)
    harmless_alpha = extra == {'alpha'} and ac['alpha']['alphaRange'] == [1.0,1.0] and bmat['values']['alpha'] == 1.0
    links_equal = all(k in ac and v == ac[k] for k,v in bc.items()) and (not extra or harmless_alpha)
    material_comparison[name] = {
        'imagePixelsPreserved': {i['pixelSha256'] for i in bmat['images']} == {i['pixelSha256'] for i in amat.get('images', [])},
        'textureExtensionsBefore': [i['extension'] for i in bmat['images']],
        'textureExtensionsAfter': [i['extension'] for i in amat.get('images', [])],
        'valuesBefore': bmat['values'], 'valuesAfter': amat.get('values', {}),
        'textureConnectionsEqual': links_equal,
        'additionalUniformOpaqueAlphaLink': bool(harmless_alpha),
        'materialValuesMaxDelta': max((float(np.max(np.abs(np.array(v) - np.array(amat.get('values', {}).get(k, np.nan))))) for k,v in bmat['values'].items()), default=0),
        'backfaceCullingPreserved': bmat['backfaceCulling'] == amat.get('backfaceCulling')}
# FBX normals/UVs are authoritative; explicit tangent arrays are intentionally absent.
flat_elements = []
def flatten(el):
    flat_elements.append(el)
    for child in el.elems: flatten(child)
flatten(fbx_tree)
properties = next(el for el in fbx_tree.elems if el.id == b'GlobalSettings')
properties = next(el for el in properties.elems if el.id == b'Properties70')
axes = {el.props[0].decode(): el.props[-1] for el in properties.elems if el.id == b'P' and el.props[0] in (b'UpAxis',b'UpAxisSign',b'FrontAxis',b'FrontAxisSign',b'CoordAxis',b'CoordAxisSign',b'UnitScaleFactor')}
embedded = []
for el in flat_elements:
    if el.id == b'Video':
        values = {ch.id:ch.props for ch in el.elems}
        content = values.get(b'Content', [b''])[0]
        embedded.append({'relativeFilename': values.get(b'RelativeFilename',[b''])[0].decode(), 'embeddedBytes': len(content), 'sha256': sha(content)})
container_qa = {'fbxVersion': fbx_version, 'globalSettings': axes,
    'metersAndYUp': axes.get('UnitScaleFactor') == 100 and axes.get('UpAxis') == 1 and axes.get('UpAxisSign') == 1,
    'tangentExported': any(el.id == b'LayerElementTangent' for el in flat_elements),
    'binormalExported': any(el.id == b'LayerElementBinormal' for el in flat_elements),
    'embeddedImages': embedded,
    'selfContainedImages': all(e['embeddedBytes'] > 0 and e['relativeFilename'].startswith('textures/') and '..' not in Path(e['relativeFilename']).parts for e in embedded),
    'noWorkspacePathInBinary': b'/workspace/' not in fbx.read_bytes() and b'/tmp/' not in fbx.read_bytes()}
source_obj = {o['name']:o for o in source_before[0]['objects']}
uv_preservation = []
for obj in after[0]['objects']:
    original_hashes = list(source_obj[obj['name']]['uvLayerHashes'].values())
    retained_hashes = list(obj['uvLayerHashes'].values())
    uv_preservation.append({'object':obj['name'],'allSourceUvLayersRetained':all(h in retained_hashes for h in original_hashes)})
material_pass = all(m['imagePixelsPreserved'] and m['textureConnectionsEqual'] and m['materialValuesMaxDelta'] < 2e-5 for m in material_comparison.values())
all_pass = bool(geometry['passed'] and color_verification['fileColorValuesPreserved'] and material_pass and
    container_qa['metersAndYUp'] and container_qa['selfContainedImages'] and container_qa['noWorkspacePathInBinary'] and
    not container_qa['tangentExported'] and not container_qa['binormalExported'] and all(v['allSourceUvLayersRetained'] for v in uv_preservation) and
    all(i['resolvedInsideCleanReimport'] for i in images))
raw = source.read_bytes()
gltf_json = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
report = {'schemaVersion': 2, 'passed': all_pass, 'container': container_qa, 'sourceUvPreservation': uv_preservation,
          'recipeSha256': {p.name: sha(p.read_bytes()) for p in Path(__file__).parent.glob('*.py') if p.name in ('convert_and_audit_fbx.py','normalize_fbx_materials.py','deterministic_fbx.py')},
          'id': source.stem, 'sourceGlb': str(source), 'sourceGlbSha256': source_hash,
          'fbx': fbx.name, 'fbxBytes': fbx.stat().st_size, 'fbxSha256': fbx_hash,
          'blenderVersion': bpy.app.version_string, 'cpuBaseline': cpu_baseline,
          'runtime': {'blender':bpy.app.version_string,'blenderBuildHash':bpy.app.build_hash.decode(),'blenderBinarySha256':sha(Path(bpy.app.binary_path).read_bytes()),'python':sys.version,'numpy':np.__version__,'zlib':zlib.ZLIB_RUNTIME_VERSION,'platform':platform.platform()},
          'exportSettings': {k: sorted(v) if isinstance(v, set) else v for k, v in export_settings.items()},
          'before': before[0], 'after': after[0], 'geometry': geometry,
          'originalGlbImportedScene': source_before[0], 'fbxMaterialNormalization': normalization,
          'deterministicExport': determinism, 'vertexColorFileVerification': color_verification,
          'uniquePackedImageFilenames': args.unique_image_paths,
          'sourceGltfMaterials': gltf_json.get('materials', []),
          'sourceGltfExtensionsUsed': gltf_json.get('extensionsUsed', []),
          'materialComparison': material_comparison,
          'allImportedImagesInsideCleanReimport': all(i['resolvedInsideCleanReimport'] for i in images),
          'limits': ['Blender-to-Blender interchange check only; Unity and other consumers not tested.',
                     'FBX Phong materials are not lossless glTF metallic-roughness PBR. See per-material comparison.',
                     'Split normals and UVs are stored; tangent/binormal arrays are not serialized. Consumers recompute tangents from normals/UVs.',
                     'FBX exporter writes CullingOff; source single-sided material culling is not preserved and must be configured by the target application if needed.',
                     'No source GLB/STL/metadata or pre-existing ZIP was modified.']}
assert sha(source.read_bytes()) == source_hash
(out / 'roundtrip-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('FBX_QA_RESULT ' + json.dumps({'id': source.stem, 'bytes': fbx.stat().st_size, **geometry, 'passed': all_pass,
                                    'imagesInIsolation': report['allImportedImagesInsideCleanReimport']}), flush=True)

assert all_pass, 'FBX aggregate QA failed; inspect the preserved roundtrip-report.json.'
