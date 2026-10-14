"""Original generic pruned street tree, CC BY 4.0.

Deterministic geometry, original baked bark maps and leaf vertex colors.
No external input assets.
Run with Blender: blender -b --python scripts/city/street_tree.py -- \
    --output /absolute/staging/directory --samples 384 --size 1024

Two coherent mesh/material groups: wood and individual folded leaf blades.
Leaves are intentionally thin, double-sided surfaces, not opaque canopy blobs.
The GLB is the authoritative geometry; STL is made from its exact reimport.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import random
import numpy as np
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
import common

SEED = 14062026
SLUG = 'city-pruned-street-tree'
UP = Vector((0, 0, 1))
RNG = random.Random(SEED)
COUNTS = {'trunks': 0, 'scaffoldBranches': 0, 'secondaryBranches': 0,
          'tertiaryBranches': 0, 'fineShoots': 0, 'leaves': 0,
          'prunedStubs': 0}


def clamp(x, a, b):
    return max(a, min(b, x))


def frame(direction):
    """A stable right-handed radial basis for a tube tangent."""
    tangent = Vector(direction).normalized()
    reference = UP if abs(tangent.z) < .94 else Vector((0, 1, 0))
    u = reference.cross(tangent).normalized()
    v = tangent.cross(u).normalized()
    return u, v, tangent


def curve(a, b, start_direction=None, bend=.12, rings=7):
    a, b = Vector(a), Vector(b)
    delta = b - a
    direction = delta.normalized()
    tangent = Vector(start_direction).normalized() if start_direction else direction
    c1 = a + (tangent * .66 + direction * .34).normalized() * delta.length * .32
    c2 = b - direction * delta.length * .29 - UP * bend
    return [a * (1-t)**3 + c1 * (3*t*(1-t)**2) + c2 * (3*t*t*(1-t)) + b * t**3
            for t in [i/(rings-1) for i in range(rings)]]


def along(points, t):
    k = t * (len(points)-1)
    i = min(int(k), len(points)-2)
    return points[i].lerp(points[i+1], k-i), (points[i+1]-points[i]).normalized()


def crown_limit(point, padding=.0):
    """Irregular rounded pruning envelope, never used as visible geometry."""
    p = Vector(point)
    center = Vector((.055, -.025, 4.50))
    q = p-center
    az = math.atan2(q.y, q.x)
    ripple = 1 + .055*math.sin(3*az+.7) + .032*math.sin(7*az-1.2)
    radii = Vector((1.93*ripple-padding, 1.84*ripple-padding, 1.43-padding))
    distance = math.sqrt(sum((q[i]/radii[i])**2 for i in range(3)))
    if distance > 1:
        q /= distance
    return center+q


class Geometry:
    def __init__(self, name):
        self.name = name
        self.vertices, self.faces, self.colors, self.uvs, self.smooth = [], [], [], [], []

    def vertex(self, point, color, uv=(0, 0)):
        self.vertices.append(tuple(point))
        self.colors.append((*color[:3], 1.0))
        self.uvs.append(uv)
        return len(self.vertices)-1

    def face(self, vertices, smooth=True):
        self.faces.append(tuple(vertices))
        self.smooth.append(smooth)

    def object(self, material, vertex_colors=True):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        uv = mesh.uv_layers.new(name='UVMap')
        for loop in mesh.loops:
            uv.data[loop.index].uv = self.uvs[loop.vertex_index]
        if vertex_colors:
            color = mesh.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='POINT')
            for i, value in enumerate(self.colors):
                color.data[i].color = value
            mesh.color_attributes.active_color = color
        for face, smooth in zip(mesh.polygons, self.smooth):
            face.use_smooth = smooth
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        mesh.materials.append(material)
        return obj


def vertex_material(name, fallback, roughness, double_sided=False):
    material = common.mat(name, (*fallback, 1), rough=roughness)
    node = material.node_tree.nodes.new('ShaderNodeVertexColor')
    node.layer_name = 'Color'
    material.node_tree.links.new(node.outputs['Color'], material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    material.use_backface_culling = not double_sided
    return material


def periodic_noise(height, width, rows, columns, rng):
    """Periodic smooth value noise, evaluated directly without external images."""
    lattice = rng.random((rows, columns)).astype(np.float32)
    y = (np.arange(height, dtype=np.float32)+.5)*rows/height
    x = (np.arange(width, dtype=np.float32)+.5)*columns/width
    yi, xi = np.floor(y).astype(int), np.floor(x).astype(int)
    yf, xf = y-yi, x-xi
    yf, xf = yf*yf*(3-2*yf), xf*xf*(3-2*xf)
    a = lattice[yi[:, None] % rows, xi[None, :] % columns]
    b = lattice[yi[:, None] % rows, (xi[None, :]+1) % columns]
    c = lattice[(yi[:, None]+1) % rows, xi[None, :] % columns]
    d = lattice[(yi[:, None]+1) % rows, (xi[None, :]+1) % columns]
    return ((a*(1-xf)+b*xf)*(1-yf[:, None])+(c*(1-xf)+d*xf)*yf[:, None])


def packed_image(name, array, noncolor=False):
    height, width = array.shape[:2]
    image = bpy.data.images.new(name, width=width, height=height, alpha=False)
    image.colorspace_settings.name = 'Non-Color' if noncolor else 'sRGB'
    rgba = np.ones((height, width, 4), dtype=np.float32)
    rgba[:, :, :3] = array
    image.pixels.foreach_set(rgba.ravel())
    image.file_format = 'PNG'
    image.pack()
    return image


def bark_cells(height, width, rows, columns, rng, warp):
    """Tiled, jittered elongated bark plates: boundary distance and plate tone."""
    cx = rng.random((rows, columns))*.78+.11
    cy = rng.random((rows, columns))*.78+.11
    tone = rng.random((rows, columns))
    yy, xx = np.meshgrid((np.arange(height)+.5)*rows/height,
                         (np.arange(width)+.5)*columns/width, indexing='ij')
    xx = xx+1.15*(warp-.5)
    yy = yy+.42*(warp-.5)
    ix, iy = np.floor(xx).astype(int), np.floor(yy).astype(int)
    nearest, second = np.full_like(xx, 100.0), np.full_like(xx, 100.0)
    shade = np.zeros_like(xx)
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            gx, gy = ix+dx, iy+dy
            distance = (xx-gx-cx[gy % rows, gx % columns])**2+(yy-gy-cy[gy % rows, gx % columns])**2
            closer = distance < nearest
            second = np.where(closer, nearest, np.minimum(second, distance))
            shade = np.where(closer, tone[gy % rows, gx % columns], shade)
            nearest = np.minimum(nearest, distance)
    return np.sqrt(second)-np.sqrt(nearest), shade


def bark_material():
    """Original baked color/normal detail, exported as embedded PNG images."""
    height, width = 1024, 512
    rng = np.random.default_rng(SEED+81)
    broad = periodic_noise(height, width, 7, 9, rng)
    grain = periodic_noise(height, width, 68, 117, rng)
    fine = periodic_noise(height, width, 211, 231, rng)
    warp = periodic_noise(height, width, 9, 13, rng)
    cell_warp = .27*warp+.73*periodic_noise(height, width, 67, 113, rng)
    boundary, plate_tone = bark_cells(height, width, 19, 37, rng, cell_warp)
    fine_boundary, _ = bark_cells(height, width, 37, 67, rng, grain)
    furrow = np.exp(-(boundary/(.023+.027*grain))**2)
    furrow *= np.clip((periodic_noise(height, width, 31, 43, rng)-.24)*2.6, .06, 1)
    hairline = np.exp(-(fine_boundary/.018)**2)*np.clip((broad-.42)*2.4, 0, 1)
    shade = .76+.17*broad+.16*plate_tone+.14*grain+.055*fine-.16*furrow-.045*hairline
    color = np.stack((shade*.405, shade*.355, shade*.292), axis=2)
    # Subtle weathered grey patches without a photo/scanned texture dependency.
    weather = np.clip((broad-.61)*1.6, 0, .27)[:, :, None]
    color = color*(1-weather)+np.array((.48, .465, .415))*weather
    relief = .045*(1-np.exp(-boundary/.15))+.020*plate_tone+.065*grain+.025*fine-.055*furrow-.018*hairline
    dx = (np.roll(relief, -1, axis=1)-np.roll(relief, 1, axis=1))*2.8
    dy = (np.roll(relief, -1, axis=0)-np.roll(relief, 1, axis=0))*2.8
    normal = np.stack((-dx, -dy, np.ones_like(dx)), axis=2)
    normal /= np.linalg.norm(normal, axis=2)[:, :, None]
    material = common.mat('Original bark | embedded procedural PBR', (.15, .12, .08, 1), rough=.87)
    material.use_backface_culling = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get('Principled BSDF')
    color_node = nodes.new('ShaderNodeTexImage')
    color_node.image = packed_image('Original bark base color', np.clip(color, 0, 1))
    color_node.interpolation = 'Linear'
    color_node.extension = 'REPEAT'
    links.new(color_node.outputs['Color'], shader.inputs['Base Color'])
    normal_node = nodes.new('ShaderNodeTexImage')
    normal_node.image = packed_image('Original bark tangent normal', normal*.5+.5, True)
    normal_node.interpolation = 'Linear'
    normal_node.extension = 'REPEAT'
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.inputs['Strength'].default_value = .65
    links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    return material


def bark_color(point, angle, branch_age, salt):
    p = Vector(point)
    # Fallback wood colors for editing; the delivered bark uses embedded maps.
    grain = .5*math.sin(angle*7 + p.z*1.9 + salt) + .28*math.sin(angle*15 - p.z*7.4 + salt*2)
    mottle = math.sin(p.x*13.7+p.y*7.8+p.z*8.2) * math.sin(p.z*17.3-p.y*19.1)
    shade = 1 + .17*grain + .12*mottle
    young = 1 - branch_age
    return ((.155+.040*young)*shade, (.128+.029*young)*shade, (.091+.006*young)*shade)


def wood_tube(mesh, points, r0, r1, sides, age=.7, trunk=False, salt=0, cut=False):
    """Capped tubes with tapered, lightly furrowed surfaces and explicit UVs."""
    points = [Vector(p) for p in points]
    rings = []
    length = 0
    previous_u = None
    for i, point in enumerate(points):
        t = i/(len(points)-1)
        if i:
            length += (point-points[i-1]).length
        tangent = points[min(i+1, len(points)-1)]-points[max(0, i-1)]
        u, v, tangent = frame(tangent)
        if previous_u is not None:
            projected_u = previous_u-tangent*previous_u.dot(tangent)
            if projected_u.length > .01:
                u = projected_u.normalized()
                v = tangent.cross(u).normalized()
        previous_u = u
        radius = r1 + (r0-r1)*(1-t)**.83
        if trunk:
            # Grounded root flare, smoothly fading into the exposed stem.
            radius = .020 + .148*(1-clamp(point.z/5.2, 0, 1))**.78
            radius += .075*math.exp(-point.z*8)
        ring = []
        for j in range(sides+1):
            angle = math.tau*j/sides
            uneven = 1 + .035*math.sin(angle*5 + t*2 + salt) + .018*math.sin(angle*11-t*6)
            if trunk:
                uneven += .20*max(0, math.cos(angle*5+.8))*math.exp(-point.z*4.6)
            pos = point + (u*math.cos(angle)+v*math.sin(angle))*radius*uneven
            color = bark_color(pos, angle, age, salt)
            ring.append(mesh.vertex(pos, color, (j/sides, length/1.65)))
        rings.append(ring)
    for i in range(len(rings)-1):
        for j in range(sides):
            mesh.face((rings[i][j], rings[i][j+1], rings[i+1][j+1], rings[i+1][j]))
    for end in [0, -1]:
        center_color = (.21, .155, .088) if cut and end == -1 else bark_color(points[end], 0, age, salt)
        center = mesh.vertex(points[end], center_color, (.5, .5))
        ring = rings[end]
        for j in range(sides):
            face = (center, ring[j+1], ring[j]) if end == 0 else (center, ring[j], ring[j+1])
            mesh.face(face, False)
    return points


def leaf(mesh, base, direction, size, roll, hue, young=False):
    """Eight triangles: pointed blade, two folded interior stations, no alpha card."""
    base, direction = Vector(base), Vector(direction).normalized()
    # Leaf normals tend toward sky, with varied rolls rather than a planar spray.
    normal = (UP-direction*UP.dot(direction)).normalized()
    if normal.length < .1:
        normal = Vector((0, 1, 0))
    width_direction = direction.cross(normal).normalized()
    normal = (normal*math.cos(roll)+width_direction*math.sin(roll)).normalized()
    width_direction = direction.cross(normal).normalized()
    length = size
    width = size*RNG.uniform(.45, .58)
    # Smooth coherent variation; each blade gets its own UV patch and color.
    rgb = Vector((.080, .217, .033) if not young else (.123, .274, .054))*hue
    ids = []
    ids.append(mesh.vertex(base, rgb*.75, (.5, 0)))
    for t, width_factor in [(.32, .91), (.70, .80)]:
        center = base+direction*(length*t)+normal*(length*(.10*math.sin(math.pi*t)-.08*t*t))
        for side in [-1, 0, 1]:
            pos = center+width_direction*(side*width*width_factor/2)
            # Raised midrib; cupped edge and a slight asymmetric curl.
            pos += normal*(-abs(side)*length*.055 + side*length*.008)
            tone = rgb*(.87 if side else 1.17)*(1+.055*t)
            ids.append(mesh.vertex(pos, tone, ((side+1)/2, t)))
    tip = base+direction*length-normal*(length*.055)
    ids.append(mesh.vertex(tip, rgb*1.05, (.5, 1)))
    # Winding points toward the intended upper surface normal.
    for f in [(0, 2, 1), (0, 3, 2), (1, 2, 5), (1, 5, 4),
              (2, 3, 6), (2, 6, 5), (4, 5, 7), (5, 6, 7)]:
        mesh.face(tuple(ids[i] for i in f), True)
    COUNTS['leaves'] += 1


def shoot(wood, foliage, base, direction, length, salt, vigorous=False):
    direction = Vector(direction).normalized()
    end = crown_limit(Vector(base)+direction*length)
    if (end-Vector(base)).length < .10:
        return
    points = curve(base, end, direction, bend=.025, rings=3)
    wood_tube(wood, points, .0034 if not vigorous else .0042, .00085, 4, age=.1, salt=salt)
    COUNTS['fineShoots'] += 1
    phase = RNG.uniform(0, math.tau)
    n = RNG.choice([9, 10, 11])
    for j in range(n):
        t = .16+.80*j/(n-1)
        origin, tangent = along(points, t)
        u, v, _ = frame(tangent)
        angle = phase+j*2.399963
        radial = (u*math.cos(angle)+v*math.sin(angle))
        # Most leaves fan outward from their bearing shoot with modest droop.
        leafdir = (radial*.83+tangent*.56+UP*RNG.uniform(-.1, .30)).normalized()
        leaf(foliage, origin, leafdir, RNG.uniform(.125, .178)*(1-.13*t),
             RNG.uniform(-.55, .55), RNG.uniform(.82, 1.15), young=(t>.8 and RNG.random()<.35))
    origin, tangent = along(points, 1)
    leaf(foliage, origin, (tangent+UP*.08).normalized(), RNG.uniform(.115, .15),
         RNG.uniform(-.4, .4), RNG.uniform(.95, 1.15), young=True)


def branch_crown(wood, foliage, primary, phi, index):
    outward = Vector((math.cos(phi), math.sin(phi), 0))
    side = Vector((-math.sin(phi), math.cos(phi), 0))
    # Alternating secondaries make an airy, asymmetrical branch hierarchy.
    for j, t in enumerate([.37, .53, .69, .84, .98]):
        base, tangent = along(primary, t)
        sign = -1 if j%2 else 1
        lateral = RNG.uniform(.40, .65)*sign
        outward_length = RNG.uniform(.38, .65)
        rise = RNG.uniform(.12, .46)
        if index < 3 and j in [1, 3]:
            rise -= .27
        end = crown_limit(base+outward*outward_length+side*lateral+UP*rise, .07)
        secondary = curve(base, end, tangent, .045, 6)
        radius = .026*(1-.44*t)*(1-.035*index)
        wood_tube(wood, secondary, radius, .0049, 8, age=.48, salt=index*13+j)
        COUNTS['secondaryBranches'] += 1
        secdir = (end-base).normalized()
        for k, st in enumerate([.37, .58, .79, .98]):
            root, tand = along(secondary, st)
            angle = phi + sign*.6 + (1 if k%2 else -1)*RNG.uniform(.6, 1.1)
            heading = Vector((math.cos(angle), math.sin(angle), RNG.uniform(.12, .66)))
            length = RNG.uniform(.36, .52)
            tip = crown_limit(root+heading.normalized()*length, .015)
            tertiary = curve(root, tip, tand, .035, 4)
            wood_tube(wood, tertiary, .0064*(1-.28*st), .0019, 5, age=.25, salt=index*17+j*3+k)
            COUNTS['tertiaryBranches'] += 1
            # Three distinct shoots per tertiary, not a repeated visible mesh cluster.
            for m, tt in enumerate([.39, .70, .97]):
                shootroot, tangent3 = along(tertiary, tt)
                angle3 = angle + [-1.00, .91, .07][m] + RNG.uniform(-.24, .24)
                direction = Vector((math.cos(angle3), math.sin(angle3), RNG.uniform(-.22, .80)))
                direction = (direction.normalized()*.70+tangent3*.30).normalized()
                shoot(wood, foliage, shootroot, direction, RNG.uniform(.25, .39), index*100+j*20+k*3+m)


def generate():
    global RNG
    RNG = random.Random(SEED)
    for key in COUNTS:
        COUNTS[key] = 0
    common.reset()
    wood, foliage = Geometry('Street tree | trunk, branches and twigs'), Geometry('Street tree | folded individual leaves')
    # Tapered slightly wandering stem, with a clear pedestrian-height lower trunk.
    zs = [0, .045, .11, .22, .40, .65, .95, 1.30, 1.65, 2.0, 2.30, 2.58, 2.87, 3.17, 3.48, 3.80, 4.12, 4.43, 4.73, 5.04]
    trunk = [Vector((.040*math.sin(z*1.35)+.012*z, .028*math.sin(z*1.7), z)) for z in zs]
    trunk[0].x = trunk[0].y = trunk[1].x = trunk[1].y = 0
    wood_tube(wood, trunk, .24, .012, 36, age=1, trunk=True, salt=.4)
    COUNTS['trunks'] = 1
    scaffolds = [(0.03, 2.18, 1.15, 3.45), (2.41, 2.38, 1.17, 3.59),
                 (4.87, 2.58, 1.20, 3.83), (1.12, 2.78, 1.12, 4.13),
                 (3.46, 3.00, 1.17, 4.35), (5.92, 3.22, 1.07, 4.61),
                 (2.04, 3.50, .92, 4.87), (4.45, 3.76, .81, 5.06),
                 (.58, 4.03, .59, 5.35), (3.0, 4.31, .19, 5.55)]
    for i, (phi, height, reach, end_height) in enumerate(scaffolds):
        # Exact stem attachment instead of a floating nearby branch origin.
        index = max(j for j, p in enumerate(trunk) if p.z <= height)
        amount = (height-trunk[index].z)/(trunk[index+1].z-trunk[index].z)
        root = trunk[index].lerp(trunk[index+1], amount)
        target = Vector((math.cos(phi)*reach, math.sin(phi)*reach, end_height))
        initial = Vector((math.cos(phi)*.33, math.sin(phi)*.33, .84)).normalized()
        primary = curve(root, target, initial, .11, 10)
        wood_tube(wood, primary, .068*(1-i*.052), .011*(1-i*.025), 15 if i<5 else 12, age=.82, salt=phi)
        COUNTS['scaffoldBranches'] += 1
        branch_crown(wood, foliage, primary, phi, i)
    # Discreet pruned older branches: closed cut ends remain visible below foliage.
    for i, (height, phi, radius, length) in enumerate([(1.61, -1.13, .025, .053), (2.05, 2.03, .033, .070), (2.67, 4.75, .029, .084)]):
        index = max(j for j, p in enumerate(trunk) if p.z <= height)
        root = trunk[index].lerp(trunk[index+1], (height-trunk[index].z)/(trunk[index+1].z-trunk[index].z))
        radial = Vector((math.cos(phi), math.sin(phi), .20)).normalized()
        root += radial*.07
        endpoint = root+radial*(.065+length)
        wood_tube(wood, curve(root, endpoint, radial, 0, 4), radius*1.12, radius, 18, age=.9, salt=i, cut=True)
        COUNTS['prunedStubs'] += 1
    wood.object(bark_material(), vertex_colors=False)
    foliage.object(vertex_material('Original green leaves | vertex-colored double-sided PBR', (.08, .22, .035), .72, True))
    return dict(COUNTS)



def publish_tree_asset(slug,title,title_en,description,description_en,tags,out_dir,generator,azimuth=-55,elevation=24):
    """Isolated common.publish_asset derivative: explicit UV tangent export.
    Shared common.py is unchanged. Always reimport the exact GLB before rendering.
    """
    folder=Path(out_dir)/slug;source=folder/'source';source.mkdir(parents=True,exist_ok=True)
    obs,dims=common._prepare()
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    glb=source/f'{slug}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_tangents=True,export_extras=False,export_cameras=False,export_lights=False)
    common.reset();bpy.ops.import_scene.gltf(filepath=str(glb))
    common.export_stl_from_scene(source/f'{slug}.stl')
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in obs:o.data.calc_loop_triangles()
    tris=sum(len(o.data.loop_triangles) for o in obs)
    bounds=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
    lo=[min(v[i] for v in bounds) for i in range(3)];hi=[max(v[i] for v in bounds) for i in range(3)]
    d=[round(hi[i]-lo[i],6) for i in (0,2,1)]
    metadata=dict(id=slug,type='model',title=title,titleEn=title_en,description=description+' ゲーム・可視化向け。製造・構造設計・3Dプリント用途は未検証。',descriptionEn=description_en+' For games and visualization; not validated for manufacture, structural engineering or 3D printing.',category='urban',tags=['city','street','original',*tags],author='Xenoah',license='CC-BY-4.0',version='1.0.0',status='draft',created='2026-10-14',updated='2026-10-14',thumbnail='preview.png',preview=f'{slug}.glb',unit='m',upAxis='Y',triangles=tris,dimensions=d,uv='Per-component primitive or automatically unwrapped UVs. Overlapping between components; not a packed unique lightmap atlas. Solid-color PBR materials; no external textures. STL has no colors or UVs.',provenance=dict(method='Original AI-agent-authored procedural city geometry',tool=f'Blender {bpy.app.version_string}; Meshcopia city generator 1.0',rights='Original geometry and material design created for Xenoah Meshcopia under the owner request for CC-BY-4.0 publication. No third-party meshes, scans, brands, logos or font files.',generatorUrl=f'https://github.com/Xenoah/meshcopia/blob/main/{generator}',sourceSha256=hashlib.sha256(glb.read_bytes()).hexdigest()),usages=[dict(relationship='original',project='Meshcopia',sourceUrl='https://github.com/Xenoah/meshcopia',sourcePaths=[generator,'scripts/city/common.py'],selectors=[slug],context='Original city asset created for this library. No external deployment or reuse claimed.')])
    metadata['provenance']['stlSha256']=hashlib.sha256((source/f'{slug}.stl').read_bytes()).hexdigest()
    (folder/'asset.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    common.render(folder/'preview.png',azimuth,elevation)
    qa=Path(out_dir)/'_qa';qa.mkdir(exist_ok=True)
    common.render(qa/f'{slug}-back.png',azimuth+180,elevation)
    report=dict(id=slug,triangles=tris,dimensions=d,meshes=len(obs),materials=len(bpy.data.materials),boundsZUp=[lo,hi],glbSha256=metadata['provenance']['sourceSha256'],bytes=glb.stat().st_size)
    (qa/f'{slug}.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CITY_ASSET_COMPLETE '+json.dumps(report),flush=True)
    return report


def main():
    arguments = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', '--out', dest='output', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=384)
    parser.add_argument('--size', type=int, default=1024)
    args = parser.parse_args(arguments)
    if (args.output/SLUG).exists():
        parser.error('Refusing to overwrite an existing asset directory')
    args.output.mkdir(parents=True, exist_ok=True)
    counts = generate()
    os.environ['CITY_RENDER_SAMPLES'] = str(args.samples)
    original_render = common.render
    def render(path, azimuth=-55, elevation=24, size=800):
        return original_render(path, azimuth, elevation, args.size)
    common.render = render
    report = publish_tree_asset(
        SLUG, '剪定された街路樹', 'Pruned street tree',
        '緩やかに先細る幹、階層状の枝と小枝、個別に折れ曲がった葉を持つオリジナルの汎用街路樹。丸い樹冠は不規則に剪定され、樹種は特定していません。葉は両面表示の薄い面で、風アニメーションやLODは含みません。',
        'Original generic street tree with a root flare, tapered branching hierarchy, fine bearing shoots and individually folded leaf blades. Its irregular rounded crown represents pruning without claiming a particular species. Leaves are thin double-sided surfaces; no wind animation, LODs or species accuracy is supplied.',
        ['tree', 'foliage', 'landscape', 'vegetation', '街路樹', '植栽'],
        args.output, 'scripts/city/street_tree.py', azimuth=-58, elevation=16)
    metadata_path = args.output/SLUG/'asset.json'
    metadata = json.loads(metadata_path.read_text())
    metadata['uv'] = 'Explicit cylindrical wood UVs and per-leaf blade UVs. Islands overlap by design and are not a unique lightmap atlas. Original procedural bark base-color and tangent-space normal maps are embedded in the GLB; leaf color variation is stored in exported COLOR_0 vertex colors. Standard opaque PBR materials, with explicit exported tangent vectors and no external resources. Leaf geometry is intentionally open and the leaf material is double-sided; STL preserves the same geometry but has no colors, UVs or double-sided material semantics.'
    metadata['provenance']['method'] = 'Original deterministic procedural branching and folded-leaf geometry, original procedural bark maps and vertex-colored leaves'
    metadata['provenance']['tool'] = f'Blender {bpy.app.version_string}; Meshcopia street tree generator 1.0; seed {SEED}'
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    report.update({'construction': counts, 'seed': SEED, 'renderSamples': args.samples,
                   'renderResolution': [args.size, args.size], 'denoising': False,
                   'renderSource': 'Exact exported GLB, reimported before both views',
                   'limitations': ['Generic visualization tree, not species-accurate',
                                   'Thin open leaf surfaces, not a watertight printable model',
                                   'No LOD, rig or wind animation',
                                   'Intersecting branching solids are grouped, not boolean-unioned',
                                   'No runtime performance or manufacturing claim']})
    (args.output/'_qa'/f'{SLUG}.json').write_text(json.dumps(report, indent=2)+'\n')
    print('TREE_COMPLETE '+json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
