"""Original compact city fixtures for Meshcopia, CC BY 4.0.

All geometry and solid-colour PBR materials are authored here. No imported
models, scans, image textures, fonts, logos, or electrical functionality.
Blender authoring is metres Z-up; common exports metres Y-up GLB and STL.
"""
from pathlib import Path
import argparse, hashlib, json, math, os, sys
import bpy, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

TAU = math.tau
GROUP = 'Unassigned'

def group(name):
    global GROUP
    GROUP = name

def tag(obj):
    obj['assembly'] = GROUP
    return obj

def box(name, loc, size, material, bevel=.002, rotation=None):
    return tag(common.box(name, loc, size, material, bevel, rotation))

def cyl(name, loc, radius, depth, material, axis=(0,0,1), n=32, bevel=.001):
    obj = common.cylinder(name, loc, radius, depth, material, n, bevel=bevel)
    obj.rotation_euler = Vector(axis).to_track_quat('Z','Y').to_euler()
    # Flat caps and smooth cylindrical sides avoid inflated looking fasteners.
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return tag(obj)

def rod(name, a, b, radius, material, n=20):
    a,b = Vector(a),Vector(b)
    return cyl(name, (a+b)/2, radius, (b-a).length, material, b-a, n,
               min(.0015, radius*.12))

def beam(name, a, b, width, depth, material, bevel=.002):
    a,b = Vector(a),Vector(b)
    obj = box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel)
    obj.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    return obj

def tube(name, points, radius, material, resolution=2):
    return tag(common.tube(name,points,radius,material,resolution))

def mesh(name, verts, faces, material, smooth=False):
    obj = tag(common.mesh(name,verts,faces,material,smooth=smooth))
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(obj.data);bm.free()
    return obj

def ring(name, loc, outer, inner, depth, material, axis=(0,0,1), n=48):
    """A thick annulus with real opening, separate flat annular end faces."""
    verts=[]
    for z,r in ((-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)):
        verts += [(r*math.cos(i*TAU/n),r*math.sin(i*TAU/n),z) for i in range(n)]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                  (n+i,n+j,3*n+j,3*n+i),(i,2*n+i,2*n+j,j)]
    obj=mesh(name,verts,faces,material)
    for i,p in enumerate(obj.data.polygons):p.use_smooth=(i%4<2)
    obj.location=loc;obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return obj

def torus(name,loc,major,minor,material,axis=(0,0,1),n=48,sides=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=sides,
        major_radius=major,minor_radius=minor,location=loc)
    obj=bpy.context.object;obj.name=name;obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    obj.data.materials.append(material)
    for p in obj.data.polygons:p.use_smooth=True
    return tag(obj)

def screw(name, loc, radius, material, axis=(0,-1,0)):
    """Shallow cylindrical screw head plus a genuine recessed straight slot."""
    axis=Vector(axis).normalized()
    obj=cyl(name,loc,radius,radius*.48,material,axis,n=16,bevel=radius*.10)
    q=axis.to_track_quat('Z','Y')
    # A dark inset is a visible recess, not a texture or a font glyph.
    slot=box(name+' recessed drive',Vector(loc)+axis*radius*.242,
             (radius*1.16,radius*.20,radius*.07),PALETTE['rubber'],radius*.04)
    slot.rotation_euler=q.to_euler()
    return obj

def hexbolt(name,loc,radius,material,axis=(0,0,1)):
    axis=Vector(axis).normalized()
    cyl(name+' washer',Vector(loc)-axis*radius*.28,radius*1.28,radius*.16,
        material,axis,n=20,bevel=radius*.035)
    return cyl(name+' hex head',loc,radius,radius*.55,material,axis,n=6,
               bevel=radius*.06)

def palette():
    return {
        'dish':common.mat('Warm white painted reflector',(.71,.73,.69),.12,.40),
        'dish_back':common.mat('Cool gray reflector rear coat',(.39,.44,.44),.30,.47),
        'steel':common.mat('Satin galvanized steel',(.44,.51,.54),.78,.33),
        'bright':common.mat('Machined stainless steel',(.58,.63,.65),.85,.27),
        'dark':common.mat('Graphite powder coat',(.052,.070,.076),.38,.43),
        'rubber':common.mat('Black elastomer seals',(.018,.024,.026),0,.82),
        'feed':common.mat('Light gray receiver polymer',(.62,.65,.62),0,.43),
        'yellow':common.mat('Crossing enclosure warm yellow',(.92,.51,.035),.08,.39),
        'button':common.mat('Satin tactile button metal',(.34,.41,.43),.75,.35),
        'lens':common.mat('Unlit smoked green status lens',(.035,.095,.075),.10,.26),
    }

def satellite_dish(p):
    """Offset-style dish, fixed tilt, complete compact mounting and feed assembly."""
    c=Vector((0,.015,.84));tilt=math.radians(27)
    u=Vector((1,0,0));v=Vector((0,math.sin(tilt),math.cos(tilt)))
    n=u.cross(v);rx=.342;rz=.372
    def at(x,z,depth):return c+u*x+v*z+n*depth
    # Single watertight reflector shell. Front and back are separated by 5 mm.
    group('Reflector / thick concave shell')
    sectors=72;rings=12;thickness=.005
    verts=[]
    for side in (0,1):
        verts.append(tuple(at(0,0,-side*thickness)))
        for j in range(1,rings+1):
            r=j/rings;h=.094*r*r-side*thickness
            verts += [tuple(at(rx*r*math.cos(i*TAU/sectors),
                               rz*r*math.sin(i*TAU/sectors),h)) for i in range(sectors)]
    count=1+rings*sectors;faces=[];mi=[]
    for side in (0,1):
        off=side*count
        for i in range(sectors):
            j=(i+1)%sectors
            face=(off,off+1+i,off+1+j)
            faces.append(face if side==0 else tuple(reversed(face)));mi.append(side)
        for row in range(rings-1):
            a=off+1+row*sectors;b=a+sectors
            for i in range(sectors):
                j=(i+1)%sectors;face=(a+i,b+i,b+j,a+j)
                faces.append(face if side==0 else tuple(reversed(face)));mi.append(side)
    for i in range(sectors):
        j=(i+1)%sectors;a=1+(rings-1)*sectors
        faces.append((a+i,a+count+i,a+count+j,a+j));mi.append(1)
    dish=mesh('Five millimetre elliptical reflector shell',verts,faces,p['dish'],True)
    dish.data.materials.append(p['dish_back'])
    for poly,mat_index in zip(dish.data.polygons,mi):poly.material_index=mat_index
    group('Reflector / rolled perimeter bead')
    verts=[];faces=[];sides=8
    for i in range(sectors):
        a=i*TAU/sectors;radial=(u*math.cos(a)+v*math.sin(a)).normalized()
        for j in range(sides):
            b=j*TAU/sides;pos=at(rx*math.cos(a),rz*math.sin(a),.0915)
            verts.append(tuple(pos+radial*(.0048*math.cos(b))+n*(.0048*math.sin(b))))
    for i in range(sectors):
        for j in range(sides):
            faces.append((i*sides+j,((i+1)%sectors)*sides+j,
                ((i+1)%sectors)*sides+(j+1)%sides,i*sides+(j+1)%sides))
    mesh('Continuous rolled reflector edge',verts,faces,p['dish'],True)
    group('Reflector / rear stiffening ribs')
    for spoke in range(6):
        a=TAU*spoke/6+math.pi/6;verts=[]
        tangent=u*(-math.sin(a))+v*math.cos(a)
        for i in range(13):
            r=.21+.735*i/12;pos=at(rx*r*math.cos(a),rz*r*math.sin(a),.094*r*r-.005)
            for sign,dep in ((-1,0),(1,0),(1,-.017),(-1,-.017)):
                verts.append(tuple(pos+tangent*sign*.0075+n*dep))
        faces=[(3,2,1,0),(48,49,50,51)]
        for i in range(12):
            for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
        mesh('Radial formed rear rib '+str(spoke+1),verts,faces,p['dish_back'])
    # Oriented plate and trunnion fasteners connect the reflector to the mast.
    group('Mount / reflector back plate')
    q=Matrix((u,v,n)).transposed().to_quaternion()
    for name,dep,size in [('Reflector mounting doubler',-.018,(.18,.19,.014)),
                          ('Rear bracket spacer',-.050,(.105,.14,.050))]:
        obj=box(name,at(0,0,dep),size,p['steel'],.004);obj.rotation_euler=q.to_euler()
    for x in (-.066,.066):
        for z in (-.070,.070):hexbolt('Reflector backing fixing',at(x,z,-.031),.009,p['bright'],-n)
    group('Mount / adjustable tilt trunnion')
    pivot=Vector((0,.155,.775))
    for x in (-.057,.057):
        box('Tilt yoke cheek',(x,.157,.746),(.012,.105,.155),p['steel'],.004)
        cyl('Tilt friction disc',(x*1.19,.149,.787),.046,.010,p['dark'],axis=(1,0,0),n=32,bevel=.0015)
        hexbolt('Tilt trunnion clamp',(x*1.42,.149,.787),.015,p['bright'],axis=(math.copysign(1,x),0,0))
    beam('Trunnion connector',at(0,0,-.071),(0,.149,.787),.075,.044,p['steel'])
    group('Mount / mast and roof foot')
    box('Chamfered roof mounting foot',(0,.215,.010),(.235,.235,.020),p['steel'],.007)
    cyl('Vertical mounting mast',(0,.215,.407),.024,.784,p['steel'],n=32,bevel=.0015)
    cyl('Closed mast top cap',(0,.215,.803),.025,.011,p['dark'],n=32,bevel=.002)
    box('Mast saddle web',(0,.208,.704),(.096,.042,.184),p['steel'],.004)
    for x in (-.080,.080):
        for y in (.135,.295):hexbolt('Foot plate anchor',(x,y,.027),.010,p['bright'])
    for x in (-.041,.041):
        beam('Foot gusset',(x,.205,.032),(x,.218,.148),.008,.052,p['steel'],.001)
    group('Mount / mast U-bolt clamps')
    for z in (.652,.754):
        points=[(-.041,.155,z),(-.041,.215,z)]
        points += [(.041*math.cos(a),.215+.041*math.sin(a),z) for a in [math.pi-i*math.pi/16 for i in range(17)]]
        points += [(.041,.155,z)]
        tube('Bent mast U-bolt',points,.004,p['bright'],resolution=1)
        box('Clamp bridge',(0,.158,z),(.105,.013,.027),p['steel'],.002)
        for x in (-.041,.041):hexbolt('Mast clamp nut',(x,.146,z),.009,p['bright'],axis=(0,-1,0))
    group('Feed / formed receiver arm')
    arm=[(0,.159,.679),(0,-.053,.475),(0,-.430,.475),(0,-.522,.591)]
    for i in range(len(arm)-1):beam('Rectangular receiver support arm '+str(i+1),arm[i],arm[i+1],.025,.032,p['steel'],.0025)
    for loc in (arm[0],arm[1],arm[2]):
        cyl('Feed arm pivot sleeve',loc,.021,.041,p['dark'],axis=(1,0,0),n=24,bevel=.002)
        for side in (-1,1):hexbolt('Feed arm pivot fixing',Vector(loc)+Vector((side*.024,0,0)),.010,p['bright'],axis=(side,0,0))
    group('Feed / receiver and collar')
    feed=Vector((0,-.490,.652));aim=(c-feed).normalized()
    cyl('Polymer low noise receiver casing',feed,.039,.105,p['feed'],aim,n=40,bevel=.005)
    cyl('Receiver front sealing cap',feed+aim*.058,.040,.013,p['dish'],aim,n=40,bevel=.002)
    ring('Receiver collar band',feed-aim*.014,.044,.039,.022,p['dark'],aim,n=40)
    beam('Receiver collar support',(0,-.521,.584),feed-aim*.014,.025,.023,p['dark'],.003)
    cyl('Cable gland rear fitting',feed-aim*.061,.009,.017,p['steel'],-aim,n=16,bevel=.001)
    for side in (-1,1):hexbolt('Receiver collar screw',feed-aim*.014+Vector((side*.049,0,0)),.007,p['bright'],axis=(side,0,0))
    group('Feed / routed visual cable')
    start=feed-aim*.073
    cable=[tuple(start),(0,-.545,.572),(.018,-.491,.489),(.018,-.400,.454),
           (.018,-.095,.454),(.018,-.033,.465),(.018,.161,.651),(.033,.223,.642),
           (.034,.239,.540),(.032,.240,.370)]
    tube('Coaxial cable with service bend',cable,.0032,p['rubber'],resolution=1)
    for y in (-.31,-.13):
        box('Receiver arm cable clip',(.013,y,.463),(.038,.008,.038),p['dark'],.002)

def crossing_pushbutton(p):
    """Standalone generic visual enclosure, not a complete pole or signal."""
    group('Enclosure / rear mounting flange')
    flange=box('Radiused mounting flange',(0,.049,.170),(.190,.014,.340),p['dark'],.009)
    # Four actual through-bores, not dark painted disks on the back plate.
    for x in (-.076,.076):
        for z in (.018,.322):
            cutter=cyl('Temporary flange bore',(x,.049,z),.0065,.050,p['dark'],axis=(0,1,0),n=20,bevel=0)
            mod=flange.modifiers.new('Through mounting bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
            bpy.context.view_layer.objects.active=flange;bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter,do_unlink=True)
    group('Enclosure / closed yellow housing')
    box('Chamfered cast main housing',(0,.002,.170),(.154,.081,.278),p['yellow'],.013)
    box('Rear weather seal',(0,.041,.170),(.142,.006,.264),p['rubber'],.010)
    box('Inset rear cover',(0,.047,.170),(.134,.010,.255),p['dark'],.009)
    group('Enclosure / removable front cover')
    box('Front cover gasket',(0,-.0395,.170),(.145,.004,.267),p['rubber'],.012)
    box('Raised yellow front cover',(0,-.047,.170),(.146,.014,.267),p['yellow'],.011)
    group('Enclosure / cover fixings')
    for x in (-.056,.056):
        for z in (.060,.280):screw('Front cover captive screw',(x,-.056,z),.0055,p['bright'])
    group('Button / recessed seal and protective guard')
    center=Vector((0,-.060,.159));axis=Vector((0,-1,0))
    cyl('Recessed switch well',center,.053,.012,p['rubber'],axis,n=48,bevel=.002)
    ring('Protective raised guard ring',(0,-.066,.159),.052,.0405,.015,p['bright'],axis,n=56)
    # Real guard thickness and recess retain a readable side silhouette.
    torus('Rounded guard outer lip',(0,-.073,.159),.0487,.0033,p['bright'],axis,n=56,sides=8)
    ring('Inner elastomer button seal',(0,-.0635,.159),.0408,.0360,.006,p['rubber'],axis,n=48)
    group('Button / static tactile press cap')
    cyl('Recessed tactile press cap',(0,-.063,.159),.0364,.010,p['button'],axis,n=56,bevel=.0025)
    for dz in (-.010,0,.010):
        box('Tactile grip ridge',(0,-.069,.159+dz),(.034,.0025,.0034),p['bright'],.001)
    group('Enclosure / generic pedestrian relief')
    # Original geometric pictogram; deliberately not a standards or accessibility claim.
    cyl('Pedestrian relief head',(.005,-.0568,.248),.008,.0025,p['dark'],axis,n=20,bevel=.0004)
    for name,a,b,r in [
        ('Relief torso',(.002,-.057,.237),(-.004,-.057,.216),.0046),
        ('Relief upper arm',(-.001,-.057,.232),(-.014,-.057,.222),.0032),
        ('Relief forward forearm',(-.014,-.057,.222),(-.023,-.057,.224),.0030),
        ('Relief opposite arm',(.001,-.057,.232),(.015,-.057,.223),.0030),
        ('Relief forward leg',(-.004,-.057,.217),(-.019,-.057,.202),.0034),
        ('Relief back leg',(-.002,-.057,.218),(.014,-.057,.203),.0034),
    ]:rod(name,a,b,r,p['dark'],n=10)
    # Leave clear separation above the guard; the relief must not hide behind it.
    for obj in bpy.context.scene.objects:
        if obj.get('assembly')=='Enclosure / generic pedestrian relief':obj.location.z+=.018
    group('Enclosure / unlit indicator and drain details')
    box('Indicator recessed surround',(0,-.056,.082),(.045,.005,.013),p['rubber'],.005)
    box('Smoked unlit status lens',(0,-.059,.082),(.035,.003,.0065),p['lens'],.002)
    # Two downward drain recess details on the underside, no internals simulated.
    for x in (-.040,.040):
        box('Underside drain recess',(x,-.005,.0318),(.012,.020,.002),p['rubber'],.001)
    group('Mount / rear pads and cable entry')
    for z in (.085,.255):
        box('Rear stand-off mounting pad',(0,.062,z),(.112,.018,.044),p['dark'],.005)
        for x in (-.039,.039):screw('Rear pad fixing',(x,.073,z),.006,p['bright'],axis=(0,1,0))
    # Closed compression gland protrudes rearward, with no cable tail or pole.
    cyl('Rear cable entry hex nut',(0,.060,.169),.017,.010,p['steel'],axis=(0,1,0),n=6,bevel=.001)
    cyl('Rear cable compression gland',(0,.073,.169),.0125,.022,p['rubber'],axis=(0,1,0),n=24,bevel=.0015)
    cyl('Closed cable-entry plug',(0,.085,.169),.009,.004,p['dark'],axis=(0,1,0),n=24,bevel=.001)

def bake_and_group():
    """Static components grouped into named assemblies, not hundreds of nodes."""
    obs=[o for o in bpy.context.scene.objects if o.type in ('MESH','CURVE')]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.convert(target='MESH')
    for o in list(bpy.context.selected_objects):
        bpy.context.view_layer.objects.active=o
        if not o.data.uv_layers:
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.02)
            bpy.ops.object.mode_set(mode='OBJECT')
    groups={}
    for o in bpy.context.scene.objects:
        if o.type=='MESH':groups.setdefault(o.get('assembly','Other components'),[]).append(o)
    for name,items in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in items:o.select_set(True)
        bpy.context.view_layer.objects.active=items[0]
        if len(items)>1:bpy.ops.object.join()
        o=bpy.context.view_layer.objects.active;o.name=name;o.data.name=name+' mesh'
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return {name:len(items) for name,items in groups.items()}

ASSETS=[
    ('city-satellite-dish','取付マスト付き小型衛星アンテナ','Compact satellite dish',satellite_dish,
     '厚みのある楕円反射板、巻き縁、背面リブ、角度調整金具、取付マスト、受信部と支持アームを備える静的な小型アンテナ。受信機能や電気的性能はありません。 アニメーションや実行時の動作はなく、大量配置時の性能は未計測です。',
     'A static compact dish with thick elliptical reflector, rolled edge, rear ribs, tilt bracket, mounting mast, receiver and support arm. No reception function or electrical performance is provided. No animation or runtime behavior; performance with mass placement has not been measured.',
     ['satellite','roof','antenna','receiver','mount'], -57, 22),
    ('city-crossing-pushbutton','歩行者横断用押しボタン筐体','Pedestrian crossing pushbutton enclosure',crossing_pushbutton,
     '面取りされた黄色の筐体、保護ベゼル、奥まった触知ボタン、取付フランジと背面接続部を備える単体の静的小道具。支柱や信号機は含みません。信号制御・電気機能・アクセシビリティ規格への適合はありません。 歩行者ピクトグラムはオリジナルの装飾形状で、規格適合マークではありません。アニメーションや実行時の動作はなく、大量配置時の性能は未計測です。',
     'A standalone static prop with chamfered yellow housing, protective bezel, recessed tactile button, mounting flange and rear connection detail. No pole or signal is included. It provides no traffic-control or electrical function and makes no accessibility-compliance claim. The pedestrian pictogram is original decorative geometry, not a standards-compliance mark. No animation or runtime behavior; performance with mass placement has not been measured.',
     ['crossing','pushbutton','pedestrian','enclosure','street-furniture'], -64, 18),
]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
    parser.add_argument('--only',nargs='*',default=[])
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    global PALETTE
    for slug,title,en,builder,ja,desc,tags,az,el in ASSETS:
        if args.only and slug not in args.only:continue
        if (args.output/slug).exists():raise FileExistsError('Refusing to overwrite '+str(args.output/slug))
        common.reset();PALETTE=palette();builder(PALETTE);assemblies=bake_and_group()
        common.publish_asset(slug,title,en,ja,desc,tags,args.output,'scripts/city/compact_fixtures.py',azimuth=az,elevation=el)
        path=args.output/slug/'asset.json';meta=json.loads(path.read_text())
        meta['provenance']['generatorSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        meta['provenance']['helperSha256']=hashlib.sha256(Path(common.__file__).read_bytes()).hexdigest()
        meta['provenance']['alternateFormat']='Binary STL written from the exact reimported GLB world-space triangles. Metres, Y-up; no colors or UVs. Static visual prop, not manufacturing or electrical engineering data.'
        meta['uv']='UV0 is present on every primitive: primitive UVs and per-component automatic unwraps overlap between parts; no unique packed bake or lightmap atlas. Named static assemblies; unrigged, no animations. Original solid-color PBR materials, no image textures. STL has no colors or UVs.'
        meta['usages'][0]['selectors']=[slug,builder.__name__]
        meta['usages'][0]['context']='Original procedural city visual prop authored for Meshcopia. Selector identifies its exact generator entry and function. No external deployment or reuse claimed. Generator is not yet pinned to a published commit.'
        path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        (args.output/'_qa'/(slug+'-assemblies.json')).write_text(json.dumps(assemblies,indent=2)+'\n')
    print('FIXTURE_GENERATION_COMPLETE',flush=True)

if __name__=='__main__':main()
