"""Shared helpers for original street objects authored by Claude, CC BY 4.0.

Claude (an Anthropic AI model) wrote these generators at Xenoah's request for
Meshcopia. Author in Blender Z-up metres; the GLB export converts to Y-up.
Every output is a draft until its complete deliverable set (GLB, STL and a
separately verified FBX) has passed the repository's publication gates.
"""
from pathlib import Path
import bpy, bmesh, math, json, hashlib, os, struct
from mathutils import Vector

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'package.json').is_file() and (p / 'content').is_dir())
CREATED = '2026-10-17'


def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for x in list(blocks):
            if x.users == 0: blocks.remove(x)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1


def mat(name, color, metal=0.0, rough=0.5, alpha=1.0, emission=None, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color[:3], 1)
    p.inputs['Metallic'].default_value = metal; p.inputs['Roughness'].default_value = rough
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
        try: m.surface_render_method = 'BLENDED'
        except AttributeError: pass
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[:3], 1)
        p.inputs['Emission Strength'].default_value = strength
    m.diffuse_color = (*color[:3], alpha)
    return m


def finish(o, name, material=None, bevel=0.0, smooth=False, segments=2):
    o.name = name
    if material: o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new('Edge chamfers', 'BEVEL'); mod.width = bevel; mod.segments = segments
        mod.limit_method = 'ANGLE'
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    if bevel:
        mod = o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL'); mod.keep_sharp = True; mod.weight = 50
    return o


def box(name, loc, size, material=None, bevel=0.006, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot: o.rotation_euler = rot
    return finish(o, name, material, min(bevel, min(size) * .3), False)


def cyl(name, loc, radius, depth, material=None, axis='Z', verts=32, bevel=0.002, top=None):
    """Cylinder or truncated cone. End caps stay flat-shaded, sides smooth."""
    if top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=top, depth=depth, location=loc)
    o = bpy.context.object
    if axis == 'X': o.rotation_euler[1] = math.pi / 2
    if axis == 'Y': o.rotation_euler[0] = math.pi / 2
    finish(o, name, material, min(bevel, depth * .2, radius * .2), True)
    for f in o.data.polygons: f.use_smooth = len(f.vertices) == 4
    return o


def sphere(name, loc, scale, material=None, segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc); o = bpy.context.object; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, material, 0, True)


def torus(name, loc, major, minor, material=None, rotation=None, segments=48, minor_segments=12):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments, minor_segments=minor_segments, location=loc, major_radius=major, minor_radius=minor)
    o = bpy.context.object
    if rotation: o.rotation_euler = rotation
    return finish(o, name, material, 0, True)


def rod(name, a, b, r, material=None, verts=20):
    a, b = Vector(a), Vector(b)
    o = cyl(name, (a + b) / 2, r, (b - a).length, material, verts=verts, bevel=min(.001, r * .15))
    o.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler(); return o


def bar(name, a, b, w, d, material=None, bevel=0.002):
    a, b = Vector(a), Vector(b)
    o = box(name, (a + b) / 2, (w, d, (b - a).length), material, bevel)
    o.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler(); return o


def tube(name, points, radius, material=None, resolution=3, verts_u=12):
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions = '3D'; c.resolution_u = verts_u
    c.bevel_depth = radius; c.bevel_resolution = resolution; c.use_fill_caps = True
    s = c.splines.new('POLY'); s.points.add(len(points) - 1)
    for p, co in zip(s.points, points): p.co = (*co, 1)
    o = bpy.data.objects.new(name, c); bpy.context.collection.objects.link(o)
    if material: c.materials.append(material)
    return o


def smooth_tube(name, points, radius, material=None, resolution=3, verts_u=12):
    """Bezier tube with automatic handles for bent rails and cables."""
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions = '3D'; c.resolution_u = verts_u
    c.bevel_depth = radius; c.bevel_resolution = resolution; c.use_fill_caps = True
    s = c.splines.new('BEZIER'); s.bezier_points.add(len(points) - 1)
    for p, co in zip(s.bezier_points, points):
        p.co = co; p.handle_left_type = p.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, c); bpy.context.collection.objects.link(o)
    if material: c.materials.append(material)
    return o


def mesh(name, verts, faces, material=None, bevel=0.0, smooth=False):
    m = bpy.data.meshes.new(name); m.from_pydata(verts, [], faces); m.update()
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(m); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(m); bm.free()
    return finish(o, name, material, bevel, smooth)


def prism(name, outline, z0, z1, material=None, bevel=0.0, smooth=False):
    """Extrude a counter-clockwise XY outline between two heights."""
    n = len(outline)
    verts = [(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh(name, verts, faces, material, bevel, smooth)


def slab(name, outline_xz, y0, y1, material=None, bevel=0.0):
    """Extrude an XZ outline along Y (for flat signs and panels)."""
    n = len(outline_xz)
    verts = [(x, y0, z) for x, z in outline_xz] + [(x, y1, z) for x, z in outline_xz]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    faces += [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    return mesh(name, verts, faces, material, bevel, False)


def lathe(name, profile, material=None, segments=64):
    """Revolve (radius, z) pairs around Z; radius 0 closes a pole."""
    vs = []; rings = []
    for r, z in profile:
        if r == 0: rings.append([len(vs)]); vs.append((0, 0, z))
        else:
            rings.append(list(range(len(vs), len(vs) + segments)))
            vs.extend((r * math.cos(i * math.tau / segments), r * math.sin(i * math.tau / segments), z) for i in range(segments))
    fs = []
    for a, b in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1 and len(b) == 1: continue
            if len(a) == 1: fs.append((a[0], b[i], b[j]))
            elif len(b) == 1: fs.append((a[i], b[0], a[j]))
            else: fs.append((a[i], b[i], b[j], a[j]))
    return mesh(name, vs, fs, material, 0, True)


def bolt(name, loc, radius=.008, depth=.006, material=None, axis='Z'):
    return cyl(name, loc, radius, depth, material, axis, 6, .0006)


def array_x(fn, count, start, step):
    return [fn(i, start + i * step) for i in range(count)]


def look_at(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def _prepare():
    obs = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE')]
    assert obs, 'No exportable objects'
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.convert(target='MESH')
    obs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    for o in obs:
        if not o.data.uv_layers:
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=.02); bpy.ops.object.mode_set(mode='OBJECT')
    bounds = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    lo = Vector([min(v[i] for v in bounds) for i in range(3)]); hi = Vector([max(v[i] for v in bounds) for i in range(3)])
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for o in obs: o.location -= offset
    bpy.context.view_layer.update()
    # Group by material set without welding: split normals, UV0 and
    # intentional intersections stay as authored.
    groups = {}
    for o in obs: groups.setdefault(tuple(m.name for m in o.data.materials), []).append(o)
    for key, parts in sorted(groups.items()):
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts: o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        if len(parts) > 1: bpy.ops.object.join()
        parts[0].name = 'Assembly | ' + ' + '.join(key)
    bpy.context.view_layer.update()
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def render(path, azimuth=-55, elevation=24, size=800):
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == 'MESH']
    bounds = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = Vector([min(v[i] for v in bounds) for i in range(3)]); hi = Vector([max(v[i] for v in bounds) for i in range(3)])
    center = (lo + hi) / 2; span = max(hi - lo)
    bpy.ops.object.camera_add(); cam = bpy.context.object; cam.name = 'QA camera'; cam.data.type = 'ORTHO'
    az = math.radians(azimuth); el = math.radians(elevation)
    direction = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    cam.location = center + direction * span * 4; look_at(cam, center); scene.camera = cam
    cam.data.clip_end = span * 10
    bpy.context.view_layer.update(); inv = cam.matrix_world.inverted()
    projected = [inv @ v for v in bounds]
    cam.data.ortho_scale = max(max(v.x for v in projected) - min(v.x for v in projected), max(v.y for v in projected) - min(v.y for v in projected)) * 1.22
    lamps = []
    for pos, power, scale in [((-.8, -1.2, 2.2), 350, 1.4), ((1.5, -.3, 1.2), 150, 1.2), ((.4, 1.5, 2), 300, 1.1)]:
        bpy.ops.object.light_add(type='AREA', location=center + Vector(pos) * span); l = bpy.context.object
        l.data.energy = power * span * span; l.data.shape = 'DISK'; l.data.size = scale * span; look_at(l, center); lamps.append(l)
    if scene.world is None: scene.world = bpy.data.worlds.new('QA world')
    scene.world.color = (.18, .18, .18)
    scene.render.engine = 'CYCLES'; scene.cycles.samples = int(os.environ.get('STREET_RENDER_SAMPLES', '64')); scene.cycles.use_denoising = False
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = size; scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = -1.0; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    for o in [cam, *lamps]: bpy.data.objects.remove(o, do_unlink=True)


def export_stl_from_scene(path):
    """Binary STL from the exact reimported GLB: metres and Y-up like the GLB.
    Geometry only; not a printability assertion."""
    triangles = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH': continue
        obj.data.calc_loop_triangles()
        for face in obj.data.loop_triangles:
            vertices = []
            for index in face.vertices:
                v = obj.matrix_world @ obj.data.vertices[index].co
                vertices.append(Vector((v.x, v.z, -v.y)))
            normal = (vertices[1] - vertices[0]).cross(vertices[2] - vertices[0])
            normal = normal.normalized() if normal.length > 0 else Vector((0, 0, 0))
            triangles.append(struct.pack('<12fH', *normal, *(value for v in vertices for value in v), 0))
    header = b'Meshcopia original by Claude, CC BY 4.0; metres Y-up; not print validated'.ljust(80, b'\0')
    Path(path).write_bytes(header + struct.pack('<I', len(triangles)) + b''.join(triangles))
    return len(triangles)


def normalize_triangle_records(path):
    """Canonical index order only; positions, normals, UVs, materials and winding unchanged."""
    data = bytearray(Path(path).read_bytes())
    json_size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + json_size]); bin_start = 20 + json_size + 8; processed = set()
    for m in doc.get('meshes', []):
        for prim in m.get('primitives', []):
            assert prim.get('mode', 4) == 4, 'Only triangle primitives are supported'
            aid = prim['indices']
            if aid in processed: continue
            processed.add(aid); acc = doc['accessors'][aid]; view = doc['bufferViews'][acc['bufferView']]
            assert acc['count'] % 3 == 0 and not acc.get('sparse')
            code = {5121: 'B', 5123: 'H', 5125: 'I'}[acc['componentType']]; size = struct.calcsize(code)
            assert view.get('byteStride', size) == size
            start = bin_start + view.get('byteOffset', 0) + acc.get('byteOffset', 0)
            values = struct.unpack_from('<' + code * acc['count'], data, start); triangles = []
            for i in range(0, len(values), 3):
                tri = values[i:i + 3]; small = tri.index(min(tri)); triangles.append(tri[small:] + tri[:small])
            triangles.sort(); flat = [v for tri in triangles for v in tri]
            struct.pack_into('<' + code * len(flat), data, start, *flat)
    Path(path).write_bytes(data)


def build_asset(spec, out_dir, generator):
    """Export GLB, derive STL from the reimported GLB, render previews, write draft metadata."""
    slug = spec['id']
    folder = Path(out_dir) / slug; source = folder / 'source'; source.mkdir(parents=True, exist_ok=True)
    obs = _prepare()
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    glb = source / f'{slug}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_extras=False, export_cameras=False, export_lights=False)
    normalize_triangle_records(glb)
    reset(); bpy.ops.import_scene.gltf(filepath=str(glb))
    export_stl_from_scene(source / f'{slug}.stl')
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in obs: o.data.calc_loop_triangles()
    tris = sum(len(o.data.loop_triangles) for o in obs)
    bounds = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    lo = [min(v[i] for v in bounds) for i in range(3)]; hi = [max(v[i] for v in bounds) for i in range(3)]
    d = [round(hi[i] - lo[i], 6) for i in (0, 2, 1)]
    dim = ' × '.join(f'{v:.3f}' for v in d)
    transparent = spec.get('transparentNote')
    ja = spec['description'] + ' ' + (transparent[0] + ' ' if transparent else '') + 'ゲーム・可視化向け。製造・構造設計・3Dプリント用途は未検証。'
    en = spec['descriptionEn'] + ' ' + (transparent[1] + ' ' if transparent else '') + 'For games and visualization; not validated for manufacture, structural engineering or 3D printing.'
    ja += (f' 外接寸法（X×Y×Z）{dim} m、{tris:,}三角形。単位m・Y-up、水平中央の接地用原点、最下点Y=0。部品ごとの重複UV0と単色PBR材質を収録し、'
           '画像テクスチャ・UV2・コライダー・LOD・リグ・動作は付属しません。静的表示用でUnity/VRChat実機検証は未実施。'
           'STLはm・Y-up座標の形状のみで色・材質・UV・階層を含みません。')
    en += (f' Bounding dimensions (X×Y×Z): {dim} m; {tris:,} triangles. Metres, Y-up, horizontally centered placement origin with minimum Y=0, '
           'not an articulation or mounting pivot. Includes overlapping component UV0 and constant-color PBR materials, with no image textures, '
           'unique UV2, colliders, LOD, rig or runtime behavior. Static visualization only; Unity/VRChat editor and runtime tests have not been performed. '
           'STL uses metre-valued Y-up coordinates and contains geometry only, without color, materials, UVs or hierarchy.')
    helper = Path(__file__).resolve(); helper_rel = helper.relative_to(ROOT).as_posix()
    metadata = dict(
        id=slug, type='model', title=spec['title'], titleEn=spec['titleEn'], description=ja, descriptionEn=en,
        category='urban', tags=['city', 'street', 'original', 'claude', *spec['tags']], author='Claude', license='CC-BY-4.0',
        version='1.0.0', status='draft', created=CREATED, updated=CREATED, thumbnail='preview.png', preview=f'{slug}.glb',
        unit='m', upAxis='Y', triangles=tris, dimensions=d,
        uv='Per-component primitive or automatically unwrapped UVs. Overlapping between components; not a packed unique lightmap atlas. '
           'Solid-color PBR materials; no external textures. STL has no colors or UVs.',
        provenance=dict(
            method='Original procedural street-object geometry authored by Claude (Anthropic AI model)',
            tool=f'Blender {bpy.app.version_string}; Meshcopia Claude street-object generator 1.0',
            rights='Original geometry and material design written by Claude at the request of Xenoah for CC-BY-4.0 publication in Meshcopia. '
                   'No third-party meshes, scans, brands, logos, lettering or font files.',
            generatorUrl=f'https://github.com/Xenoah/meshcopia/blob/main/{generator}',
            sourceSha256=hashlib.sha256(glb.read_bytes()).hexdigest(),
            sourceRecipeSha256=hashlib.sha256((ROOT / generator).read_bytes()).hexdigest(),
            sourceHelpersSha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
            alternateFormat='STL triangulated from the exact reimported GLB, metre-valued Y-up coordinates. No printability or manufacture validation.',
            stlSha256=hashlib.sha256((source / f'{slug}.stl').read_bytes()).hexdigest()),
        usages=[dict(relationship='original', project='Meshcopia', sourceUrl='https://github.com/Xenoah/meshcopia',
                     sourcePaths=[generator, helper_rel], selectors=[slug],
                     context='Original street object authored by Claude for this library. No external deployment or reuse claimed.')])
    (folder / 'asset.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    az, el = spec.get('view', (-55, 24))
    render(folder / 'preview.png', az, el)
    qa = Path(out_dir) / '_qa'; qa.mkdir(exist_ok=True)
    render(qa / f'{slug}-back.png', az + 180, el)
    report = dict(id=slug, triangles=tris, dimensions=d, meshes=len(obs), materials=len(bpy.data.materials),
                  glbSha256=metadata['provenance']['sourceSha256'], bytes=glb.stat().st_size)
    (qa / f'{slug}.json').write_text(json.dumps(report, indent=2) + '\n')
    print('STREET_ASSET_COMPLETE ' + json.dumps(report), flush=True)
    return report
