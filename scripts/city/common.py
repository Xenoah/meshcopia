"""Original Meshcopia city production helpers, CC BY 4.0.
Recovered after executor failure; all rebuilt outputs require fresh QA.
Author in Blender Z-up meters; GLB export converts to Y-up meters.
"""
from pathlib import Path
import bpy, math, json, hashlib, os
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        for x in list(datablocks):
            if x.users==0: datablocks.remove(x)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1

def mat(name,color,metal=0,rough=.5):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color[:3],color[3] if len(color)>3 else 1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    m.diffuse_color=p.inputs['Base Color'].default_value
    return m

def finish(o,name,material=None,bevel=0,smooth=False):
    o.name=name
    if material: o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Machined edge chamfers','BEVEL');mod.width=bevel;mod.segments=3
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    if bevel:
        mod=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
    return o

def box(name,loc,size,material=None,bevel=.008,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot:o.rotation_euler=rot
    return finish(o,name,material,min(bevel,min(size)*.3),False)

def cylinder(name,loc,radius,depth,material=None,vertices=48,rotation=None,bevel=.003):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object
    if rotation:o.rotation_euler=rotation
    return finish(o,name,material,min(bevel,depth*.2,radius*.2),True)

def sphere(name,loc,scale,material=None,segments=32,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,material,0,True)

def torus(name,loc,major,minor,material=None,rotation=None,segments=48):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments,minor_segments=12,location=loc,major_radius=major,minor_radius=minor)
    o=bpy.context.object
    if rotation:o.rotation_euler=rotation
    return finish(o,name,material,0,True)

def tube(name,points,radius,material=None,resolution=3):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=radius;c.bevel_resolution=resolution;c.use_fill_caps=True
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o)
    if material:c.materials.append(material)
    return o

def mesh(name,verts,faces,material=None,bevel=0,smooth=False):
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o)
    return finish(o,name,material,bevel,smooth)

def bolt(name,loc,radius=.012,depth=.009,material=None,rotation=None):
    return cylinder(name,loc,radius,depth,material,vertices=6,rotation=rotation,bevel=.001)

def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def _prepare():
    obs=[o for o in bpy.context.scene.objects if o.type in ('MESH','CURVE','FONT')]
    assert obs,'No exportable objects'
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.object.convert(target='MESH')
    obs=[o for o in bpy.context.selected_objects if o.type=='MESH']
    for o in obs:
        bpy.context.view_layer.objects.active=o
        if not o.data.uv_layers:
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    bounds=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
    lo=Vector([min(v[i] for v in bounds) for i in range(3)]);hi=Vector([max(v[i] for v in bounds) for i in range(3)])
    offset=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    for o in obs:o.location-=offset
    bpy.context.view_layer.update()
    return obs,hi-lo

def render(path,azimuth=-55,elevation=24,size=800):
    scene=bpy.context.scene
    meshes=[o for o in scene.objects if o.type=='MESH']
    bounds=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    lo=Vector([min(v[i] for v in bounds) for i in range(3)]);hi=Vector([max(v[i] for v in bounds) for i in range(3)])
    center=(lo+hi)/2;span=max(hi-lo)
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='QA camera';cam.data.type='ORTHO'
    az=math.radians(azimuth);el=math.radians(elevation)
    direction=Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))
    cam.location=center+direction*span*4;look_at(cam,center);scene.camera=cam
    bpy.context.view_layer.update();inv=cam.matrix_world.inverted()
    projected=[inv@v for v in bounds];cam.data.ortho_scale=max(max(v.x for v in projected)-min(v.x for v in projected),max(v.y for v in projected)-min(v.y for v in projected))*1.30
    lamps=[]
    for pos,power,scale in [((-.8,-1.2,2.2),350,1.4),((1.5,-.3,1.2),150,1.2),((.4,1.5,2),300,1.1)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*span);l=bpy.context.object;l.data.energy=power*span*span;l.data.shape='DISK';l.data.size=scale*span;look_at(l,center);lamps.append(l)
    scene.world.color=(.18,.18,.18)
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
    scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.0;scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    for o in [cam,*lamps]:bpy.data.objects.remove(o,do_unlink=True)

def publish_asset(slug,title,title_en,description,description_en,tags,out_dir,generator,azimuth=-55,elevation=24):
    """Build a draft, not approval to publish. Reimport exact bytes for all renders."""
    folder=Path(out_dir)/slug;source=folder/'source';source.mkdir(parents=True,exist_ok=True)
    obs,dims=_prepare()
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    glb=source/f'{slug}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=False,export_cameras=False,export_lights=False)
    reset();bpy.ops.import_scene.gltf(filepath=str(glb))
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in obs:o.data.calc_loop_triangles()
    tris=sum(len(o.data.loop_triangles) for o in obs)
    bounds=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
    lo=[min(v[i] for v in bounds) for i in range(3)];hi=[max(v[i] for v in bounds) for i in range(3)]
    d=[round(hi[i]-lo[i],6) for i in (0,2,1)]
    metadata=dict(id=slug,type='model',title=title,titleEn=title_en,description=description+' ゲーム・可視化向け。製造・構造設計・3Dプリント用途は未検証。',descriptionEn=description_en+' For games and visualization; not validated for manufacture, structural engineering or 3D printing.',category='urban',tags=['city','street','original',*tags],author='Xenoah',license='CC-BY-4.0',version='1.0.0',status='draft',created='2026-10-14',updated='2026-10-14',thumbnail='preview.png',preview=f'{slug}.glb',unit='m',upAxis='Y',triangles=tris,dimensions=d,uv='Per-component primitive or automatically unwrapped UVs. Overlapping between components; not a packed unique lightmap atlas. Solid-color PBR materials; no external textures.',provenance=dict(method='Original AI-agent-authored procedural city geometry',tool=f'Blender {bpy.app.version_string}; Meshcopia city generator 1.0',rights='Original geometry and material design created for Xenoah Meshcopia under the owner request for CC-BY-4.0 publication. No third-party meshes, scans, brands, logos or font files.',generatorUrl=f'https://github.com/Xenoah/meshcopia/blob/main/{generator}',sourceSha256=hashlib.sha256(glb.read_bytes()).hexdigest()),usages=[dict(relationship='original',project='Meshcopia',sourceUrl='https://github.com/Xenoah/meshcopia',sourcePaths=[generator,'scripts/city/common.py'],selectors=[slug],context='Original city asset created for this library. No external deployment or reuse claimed.')])
    (folder/'asset.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    render(folder/'preview.png',azimuth,elevation)
    qa=Path(out_dir)/'_qa';qa.mkdir(exist_ok=True)
    render(qa/f'{slug}-back.png',azimuth+180,elevation)
    report=dict(id=slug,triangles=tris,dimensions=d,meshes=len(obs),materials=len(bpy.data.materials),boundsZUp=[lo,hi],glbSha256=metadata['provenance']['sourceSha256'],bytes=glb.stat().st_size)
    (qa/f'{slug}.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CITY_ASSET_COMPLETE '+json.dumps(report),flush=True)
    return report
