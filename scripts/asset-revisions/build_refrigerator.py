"""Build an original 0.60m domestic refrigerator with editable, real interior geometry.

Blender 4.3.2. The closed payload retains a hinge pivot; QA opens that same door.
Every wall is a solid mesh, with no negative scale or double-sided workaround.
"""
from pathlib import Path
import json, math, sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]; ID='household-two-door-refrigerator'
DEST=ROOT/'asset-revisions/repair-appliances-v1'/ID
SOURCE=DEST/'source';PRODUCTION=DEST/'production';SOURCE.mkdir(parents=True,exist_ok=True);PRODUCTION.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1

def material(name,color,roughness=.5,metallic=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=metallic
    m.diffuse_color=(*color,1);return m
enamel=material('Warm white enamel',(.82,.84,.81),.28,.08)
liner=material('Food compartment liner',(.70,.75,.72),.56)
metal=material('Brushed steel hardware',(.48,.53,.56),.24,.85)
black=material('Compressor and grille',(.025,.033,.038),.67,.18)
rubber=material('Door gasket and feet',(.065,.072,.074),.9)
shelf=material('Opaque pale-aqua shelf representation',(.44,.62,.62),.3)
copper=material('Copper pipe',(.51,.23,.09),.36,.8)
panel=material('Original temperature control atlas',(1,1,1),.4)
image=bpy.data.images.load(str(PRODUCTION/'control-panel.png'));image.pack();image.colorspace_settings.name='sRGB'
node=panel.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.interpolation='Linear';node.extension='EXTEND'
panel.node_tree.links.new(node.outputs['Color'],panel.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

def finish(obj,name,mat,bevel=0,parent=None):
    obj.name=name;obj.data.name=name+' mesh';obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if bevel:
        mod=obj.modifiers.new('Manufactured edge radius','BEVEL');mod.width=bevel;mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if parent:
        matrix=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=matrix
    return obj
def box(name,center,size,mat=enamel,bevel=.003,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);obj=bpy.context.object;obj.scale=size
    return finish(obj,name,mat,min(bevel,min(size)*.24),parent)
def cylinder(name,center,radius,depth,mat=metal,direction=(0,0,1),vertices=24,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,end_fill_type='NGON',location=center)
    obj=bpy.context.object;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=Vector(direction).to_track_quat('Z','Y')
    obj=finish(obj,name,mat,0,parent)
    for face in obj.data.polygons:face.use_smooth=len(face.vertices)==4
    return obj
def pipe(name,points,radius,mat):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=radius;curve.bevel_resolution=2;curve.use_fill_caps=True
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object,name,mat)

# Separate insulated shell walls leave a genuine empty food compartment.
box('Insulated left wall',(-.285,.005,.955),(.03,.60,1.75))
box('Insulated right wall',(.285,.005,.955),(.03,.60,1.75))
box('Insulated back wall',(0,.28,.955),(.54,.05,1.75))
box('Insulated roof',(0,.005,1.825),(.57,.60,.05))
box('Chassis',(0,.005,.09),(.54,.56,.08),black)
box('Freezer floor',(0,.005,.15),(.54,.55,.04),liner)
box('Insulated compartment divider',(0,.005,.615),(.54,.55,.05),liner)
box('Fridge interior rear panel',(0,.247,1.22),(.50,.016,1.13),liner)
for z in [.82,1.12,1.42]:
    box(f'Shelf {z:.2f}',(0,.05,z),(.49,.37,.012),shelf,.002)
    box(f'Shelf front trim {z:.2f}',(0,-.14,z),(.49,.015,.024),enamel,.002)
    for x in [-.252,.252]:
        for y in [-.16,.18]:box('Shelf support',(x,y,z-.013),(.015,.04,.02),liner,.001)
for x in [-.124,.124]:
    box('Crisper floor',(x,.015,.667),(.235,.40,.012),shelf,.002)
    box('Crisper front',(x,-.183,.723),(.235,.012,.12),shelf,.002)
    box('Crisper back',(x,.211,.723),(.235,.012,.12),liner,.002)
    for sx in [-1,1]:box('Crisper side',(x+sx*.115,.015,.723),(.009,.40,.12),shelf,.001)
    box('Crisper grip',(x,-.196,.768),(.10,.018,.014),liner,.003)
for n in range(8):box('Interior air return recess',(0,.235,1.55+n*.017),(.16,.004,.006),black,.001)
box('Interior ceiling lamp',(0,.01,1.789),(.16,.12,.012),liner,.003)

hinge=bpy.data.objects.new('FRIDGE_DOOR_HINGE',None);scene.collection.objects.link(hinge);hinge.location=(-.29,-.32,.64)
hinge['qa_open_angle_degrees']=-105.0;hinge['closed_angle_degrees']=0.0
box('Upper door outer skin',(0,-.326,1.238),(.576,.055,1.19),enamel,.008,hinge)
box('Upper door inner liner',(0,-.290,1.238),(.534,.023,1.145),liner,.004,hinge)
for x in [-.265,.265]:box('Door vertical gasket',(x,-.273,1.238),(.011,.012,1.12),rubber,.002,hinge)
for z in [.682,1.794]:box('Door horizontal gasket',(0,-.273,z),(.53,.012,.011),rubber,.002,hinge)
for z in [.83,1.16,1.51]:
    box('Door pocket floor',(0,-.229,z),(.462,.09,.012),liner,.003,hinge)
    box('Door pocket front rail',(0,-.181,z+.035),(.462,.011,.08),shelf,.002,hinge)
    for x in [-.226,.226]:box('Door pocket end',(x,-.229,z+.035),(.01,.09,.08),liner,.002,hinge)
for z in [.71,1.77]:cylinder('Upper hinge knuckle',(-.29,-.32,z),.011,.05,metal,parent=hinge)
for z in [1.03,1.42]:cylinder('Door handle standoff',(.239,-.374,z),.012,.045,metal,direction=(0,1,0),parent=hinge)
cylinder('Upper door handle',(.239,-.398,1.225),.012,.41,metal,parent=hinge)
box('Freezer drawer front',(0,-.326,.367),(.576,.055,.444),enamel,.008)
box('Freezer gasket',(0,-.295,.367),(.54,.012,.413),rubber,.003)
for x in [-.16,.16]:cylinder('Freezer handle standoff',(x,-.374,.50),.012,.045,metal,direction=(0,1,0))
cylinder('Freezer drawer handle',(0,-.398,.50),.012,.35,metal,direction=(1,0,0))
box('Control panel bezel',(.12,-.358,1.62),(.127,.014,.157),black,.005,hinge)
control=box('CONTROL_ATLAS_FRONT',(.12,-.367,1.62),(.112,.003,.142),black,.0003,hinge);control.data.materials.append(panel)

for x in [-.24,.24]:
    for y in [-.23,.23]:
        cylinder('Levelling foot',(x,y,.025),.026,.05,rubber)
        cylinder('Foot threaded stem',(x,y,.061),.008,.025,metal,vertices=16)
box('Rear machinery tray',(0,.265,.19),(.49,.20,.025),black)
cylinder('Sealed compressor',(0,.282,.286),.083,.19,black,direction=(1,0,0),vertices=32)
for x in [-.215,.215]:cylinder('Condenser vertical rail',(x,.322,1.12),.006,1.23,black,vertices=12)
for i in range(24):cylinder('Condenser horizontal tube',(0,.326,.55+i*.047),.0045,.44,black,direction=(1,0,0),vertices=12)
pipe('Compressor copper connection',[(.11,.29,.29),(.17,.31,.29),(.19,.32,.36),(.19,.326,.55)],.006,copper)
for x in [-.25,.25]:
    for z in [.22,.43,1.74]:cylinder('Rear casing fastener',(x,.312,z),.006,.007,metal,direction=(0,1,0),vertices=12)
cord=[(.13,.315,.29),(.10,.34,.266)]+[(.08+(.09+.012*i/48)*math.cos(math.pi/2+i*1.5*math.pi/48),.35,.18+.065*math.sin(math.pi/2+i*1.5*math.pi/48)) for i in range(49)]+[(.21,.35,.19)]
pipe('Stowed power lead',cord,.0035,rubber)
box('Unbranded lead end cap',(.216,.35,.19),(.023,.016,.023),rubber,.003)

meshes=[o for o in scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
uv=control.data.uv_layers.active
for face in control.data.polygons:
    face.material_index=1 if face.normal.y<-.99 else 0
    if face.material_index:
        for li in face.loop_indices:
            co=control.data.vertices[control.data.loops[li].vertex_index].co
            uv.data[li].uv=(co.x/.112+.5,co.z/.142+.5)
for obj in meshes:
    assert obj.matrix_world.to_3x3().determinant()>0
    obj.data.calc_loop_triangles()
coords=[obj.matrix_world@v.co for obj in meshes for v in obj.data.vertices]
lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
dimensions=[hi[0]-lo[0],hi[2]-lo[2],hi[1]-lo[1]];triangles=sum(len(o.data.loop_triangles) for o in meshes)
scene['assetId']=ID;scene['overallDimensionsMetersYUp']=dimensions;scene['consumerState']='closed doors; separate editable upper door hinge; static appearance prop'
bpy.ops.wm.save_as_mainfile(filepath=str(PRODUCTION/(ID+'.blend')))
bpy.ops.export_scene.gltf(filepath=str(SOURCE/(ID+'.glb')),export_format='GLB',export_yup=True,export_cameras=False,export_lights=False,export_apply=True,export_normals=True,export_texcoords=True,export_materials='EXPORT',export_animations=False)
meta={'id':ID,'type':'model','title':'家庭用2ドア冷蔵庫','titleEn':'Household two-door refrigerator','description':'幅0.60mのオリジナル家庭用冷蔵庫。上扉・下段冷凍引出し、実際に空いた庫内、棚・野菜室・ドアポケット、ガスケット、ハンドル、背面コンプレッサーと配管、放熱管、電源コード、調整脚を収録。上扉は独立したヒンジ原点を保持し、標準状態は閉扉。表示パネルに自作512pxテクスチャを使用。棚・ポケットは不透明な淡色樹脂表現。冷却・電装・扉操作の実行ロジックは含みません。製造設計・安全性・3Dプリントは未検証。','descriptionEn':'Original 0.60m-wide domestic refrigerator with separate upper door and lower freezer front, real empty compartments, shelves, crispers, door pockets, gaskets, handles, rear compressor and pipes, condenser, stowed power lead and levelling feet. The upper door retains an editable hinge pivot; the delivered pose is closed. Includes an original 512px control-panel atlas. Shelves and pockets use opaque tinted-plastic representations. Static appearance asset; no cooling, electrical or door-control logic. Not verified for manufacturing, safety or 3D printing.','category':'furniture','tags':['refrigerator','fridge','冷蔵庫','家電','kitchen','キッチン','furniture','household'],'author':'Xenoah','license':'CC-BY-4.0','version':'1.0.0','status':'public','created':'2026-10-18','updated':'2026-10-18','thumbnail':'preview.webp','unit':'m','upAxis':'Y','triangles':triangles,'dimensions':[round(x,6) for x in dimensions],'preview':ID+'.glb','uv':'UV0 per part; dedicated original 512px control-panel atlas. Other surfaces use solid PBR materials. No UV2, collider, LOD or animation.','provenance':{'method':'AI-agent-authored original procedural geometry and texture','tool':'Meshcopia appliance recipe 1 / Blender 4.3.2','rights':'Original geometry and control-panel artwork for Meshcopia. No third-party model, photograph, brand or certification mark.'},'usages':[{'relationship':'original','project':'Meshcopia appliance revision','sourceUrl':'https://github.com/Xenoah/meshcopia','sourcePaths':['scripts/asset-revisions/build_refrigerator.py','scripts/asset-revisions/make_appliance_texture.py'],'selectors':[ID],'context':'Original domestic appliance for this library, with retained editable Blender production source.'}]}
(DEST/'asset.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('REFRIGERATOR',json.dumps({'triangles':triangles,'dimensionsMetersYUp':dimensions,'meshObjects':len(meshes),'allPositiveTransforms':True,'textureSize':[512,512]}))
