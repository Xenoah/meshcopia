"""Original Meshcopia city infrastructure assemblies. Blender 4.3+, metres/Z-up authoring.
No third-party meshes, images, fonts, brands or designs. Export uses common.py.
"""
import bpy, bmesh, math, sys, os
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def mat(name,color,metal=.0,rough=.5):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m

def mesh(name,verts,faces,m,bevel=0):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.data.materials.append(m)
    if bevel: bevel_obj(ob,bevel)
    return ob

def bevel_obj(ob,width=.003,segments=3):
    mod=ob.modifiers.new('Machined edge radius','BEVEL');mod.width=width;mod.segments=segments
    mod=ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
    return ob

def box(name,p,s,m,b=.003,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);ob=bpy.context.object;ob.name=name;ob.dimensions=s
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(m)
    if b:bevel_obj(ob,min(b,min(s)*.22))
    if rot:ob.rotation_euler=rot
    return ob

def cylinder(name,p,r,d,m,axis='Z',vertices=48,bevel=.0015,r2=None):
    if r2 is None:bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d,location=p)
    else:bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r2,depth=d,location=p)
    ob=bpy.context.object;ob.name=name
    if axis=='Y':ob.rotation_euler[0]=math.pi/2
    if axis=='X':ob.rotation_euler[1]=math.pi/2
    ob.data.materials.append(m)
    if bevel:bevel_obj(ob,min(bevel,d*.2,r*.2),2)
    for f in ob.data.polygons:f.use_smooth=len(f.vertices)==4
    return ob

def ring(name,p,r,t,m,axis='Z',n=64,k=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=k,location=p,major_radius=r,minor_radius=t)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(m)
    if axis=='Y':ob.rotation_euler[0]=math.pi/2
    if axis=='X':ob.rotation_euler[1]=math.pi/2
    for f in ob.data.polygons:f.use_smooth=True
    return ob

def rod(name,a,b,r,m,n=16):
    a,b=Vector(a),Vector(b);ob=cylinder(name,(a+b)/2,r,(b-a).length,m,vertices=n,bevel=min(r*.2,.002));ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return ob

def annulus(name,p,outer,inner,depth,m,axis='Z',n=80):
    verts=[]
    for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
        for i in range(n):
            a=math.tau*i/n;v=Vector((r*math.cos(a),r*math.sin(a),z))
            if axis=='Y':v=Vector((v.x,-v.z,v.y))
            verts.append(tuple(v+Vector(p)))
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
    return mesh(name,verts,faces,m,.0008)

def bolt(name,p,m,axis='Z',r=.007):
    cylinder(name+' washer',p,r*1.5,r*.3,m,axis,24,.0004)
    q=list(p);q['XYZ'.index(axis)]+= -r*.32 if axis=='Y' else r*.32
    cylinder(name+' hex head',q,r,r*.7,m,axis,6,.0004)

def cut(obj,cutter):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Fabricated opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)

def palette():
    return dict(iron=mat('Cast iron / graphite',(.025,.032,.035),.65,.78),edge=mat('Worn iron edge',(.060,.070,.069),.72,.62),dark=mat('Recess and rubber',(.018,.026,.032),.05,.86),steel=mat('Zinc coated steel',(.42,.49,.53),.85,.38),paint=mat('Warm powder coated steel',(.72,.735,.69),.25,.43),black=mat('Charcoal powder coat',(.012,.019,.024),.28,.46),rust=mat('Iron oxide patina',(.21,.112,.058),.2,.86),copper=mat('Copper refrigerant tube',(.45,.235,.105),.8,.38))

def storm_drain():
    p=palette();m=p['iron']
    # Rectangular cast frame with genuine open well and inset grate.
    for x in [-.288,.288]:box('Outer frame long rail',(x,0,.046),(.044,.812,.092),m,.004)
    for y in [-.384,.384]:box('Outer frame end rail',(0,y,.046),(.532,.044,.092),m,.004)
    for x in [-.262,.262]:box('Inset grate bearing lip',(x,0,.026),(.023,.724,.022),p['rust'],.001)
    for y in [-.351,.351]:box('Removable grate end spine',(0,y,.061),(.52,.032,.065),p['edge'],.003)
    for x in [-.248,.248]:box('Removable grate side spine',(x,0,.061),(.024,.69,.065),p['edge'],.003)
    for i in range(15):
        y=-.315+i*.045
        box('Cast cross bar %02d'%i,(0,y,.066),(.485,.021,.054),m,.003)
    box('Central under brace',(0,0,.034),(.026,.69,.021),m,.002)
    for x in [-.286,.286]:
        for y in [-.34,.34]:bolt('Frame anchor',(x,y,.094),p['steel'],r=.006)
    for x in [-.18,.18]:
        for y in [-.35,.35]:box('Anti slip cast notch',(x,y,.095),(.033,.018,.003),m,.0007)
    return ('city-storm-drain','道路排水グレーチング','Road storm drain grate','実際に開いたスリット、脱着式の鋳鉄格子、支持リブと固定ボルトを備えた道路排水口。','A cast-iron street grate with genuine open slots, removable grate bars, supporting ribs and frame anchors.',['drain','grate','infrastructure','road','鋳鉄','排水'])

def inspection_cover():
    p=palette();m=p['iron']
    annulus('Seating frame',(0,0,.035),.365,.324,.07,m)
    annulus('Frame polished seating rim',(0,0,.071),.355,.33,.008,p['edge'])
    disk=cylinder('Removable inspection lid',(0,0,.045),.321,.059,m,vertices=96,bevel=.002)
    # Recessed lift slots are physically cut through the lid; no painted shadows.
    for x in [-.236,.236]:
        c=box('Lift slot cutter',(x,0,.072),(.022,.078,.08),m,0)
        cut(disk,c)
        for y in [-.05,.05]:box('Lift recess cast shoulder',(x,y,.076),(.044,.013,.008),p['edge'],.002)
    annulus('Lid concentric ridge',(0,0,.078),.308,.302,.006,p['edge'])
    annulus('Center medallion ridge',(0,0,.077),.07,.065,.005,p['edge'])
    cylinder('Unbranded central medallion',(0,0,.076),.059,.003,p['edge'],vertices=64,bevel=.0004)
    # Unique staggered chevron traction field, built as actual relief geometry.
    for ix in range(-6,7):
        for iy in range(-6,7):
            x=ix*.044;y=iy*.044+(ix%2)*.022
            if .09<math.hypot(x,y)<.286 and not (abs(x)>.207 and abs(y)<.067):
                ob=box('Raised diamond tread',(x,y,.078),(.026,.011,.005),p['edge'],.001,rot=(0,0,math.pi/4 if ix%2 else -math.pi/4))
    for a in [math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]:
        bolt('Frame fixing',(math.cos(a)*.343,math.sin(a)*.343,.077),p['steel'],r=.005)
    # Underside ribs remain honest in rear/bottom inspection.
    for a in [0,math.pi/3,2*math.pi/3]:box('Underside stiffener',(0,0,.014),(.57,.024,.021),m,.002,rot=(0,0,a))
    return ('city-inspection-cover','丸形点検マンホール蓋','Round inspection cover','独自の滑り止め凹凸、貫通した引き上げ穴、座枠と裏面補強リブ付きの丸形点検蓋。','A round cast inspection cover with original raised traction tread, through lift slots, seating frame and underside ribs.',['manhole','inspection','cover','cast iron','road','マンホール'])

def ventilation_outlet():
    p=palette();m=p['steel']
    # Front is negative Y; 0.6 x 0.45 m folded-metal wall termination.
    for x in [-.285,.285]:box('Outer side flange',(x,0,.225),(.03,.025,.45),m,.003)
    for z in [.015,.435]:box('Outer horizontal flange',(0,0,z),(.54,.025,.03),m,.003)
    for x in [-.263,.263]:box('Duct side return',(x,.073,.225),(.014,.15,.364),p['black'],.002)
    for z in [.036,.414]:box('Duct horizontal return',(0,.073,z),(.54,.15,.014),p['black'],.002)
    # All seven overlapping louvers have actual sloped panels, folded lips and spaces.
    for i in range(7):
        z=.073+i*.05
        box('Louver blade %02d'%i,(0,.014,z),(.524,.075,.009),m,.0015,rot=(math.radians(30),0,0))
        box('Louver rolled drip lip %02d'%i,(0,-.020,z-.019),(.524,.008,.012),p['paint'],.0015)
    # Rear insect screen has modeled horizontal and vertical wires, not an opaque plane.
    for i in range(19):rod('Rear insect screen vertical',(-.243+i*.027,.139,.043),(-.243+i*.027,.139,.407),.0015,p['dark'],8)
    for i in range(14):rod('Rear insect screen horizontal',(-.254,.139,.05+i*.027),(.254,.139,.05+i*.027),.0015,p['dark'],8)
    for x in [-.284,.284]:
        for z in [.026,.424]:bolt('Flange screw',(x,-.016,z),p['edge'],'Y',.0055)
    return ('city-ventilation-outlet','壁面換気ルーバー','Wall ventilation louver','7枚の傾斜羽根、水切り端部、奥行きのある枠とメッシュ防虫網を備えた金属製換気口。','A folded-metal wall outlet with seven sloping louvers, drip lips, deep frame and a fully modeled rear insect screen.',['ventilation','louver','wall','metal','exterior','換気口'])

def hvac_condenser():
    p=palette();m=p['paint']
    # Freestanding condenser: left fan, right electrical/service compartment.
    for x in [-.30,.30]:
        box('Galvanized base skid',(x,.02,.026),(.075,.42,.052),p['steel'],.005)
        for y in [-.135,.165]:box('Vibration isolation pad',(x,y,.063),(.067,.06,.025),p['dark'],.004)
    box('Bottom tray',(0,0,.095),(.86,.345,.035),m,.01)
    box('Top weather cap',(0,0,.662),(.89,.365,.038),m,.012)
    for x in [-.425,.425]:box('Cabinet side wall',(x,0,.379),(.025,.342,.536),m,.008)
    box('Rear coil backing',(0,.151,.376),(.808,.018,.516),p['dark'],.002)
    for i in range(48):box('Heat exchanger vertical fin %02d'%i,(-.391+i*.0166,.169,.376),(.004,.025,.49),p['steel'],.0005)
    for z in [.145,.605]:box('Coil protective cross rail',(0,.19,z),(.806,.018,.012),p['black'],.002)
    # Front is a genuine cut panel, with recessed fan behind its opening.
    front=box('Fan front sheet',(-.105,-.17,.38),(.64,.022,.53),m,0)
    cutter=cylinder('Fan aperture cutter',(-.105,-.17,.38),.223,.1,m,'Y',80,0);cut(front,cutter);bevel_obj(front,.003)
    box('Electrical access panel',(.326,-.181,.38),(.171,.025,.524),m,.005)
    box('Panel vertical joint',(.23,-.187,.38),(.008,.004,.51),p['dark'],.001)
    # Rear fan body and separated broad swept blades.
    cylinder('Fan motor',(-.105,-.09,.38),.057,.12,p['black'],'Y',40,.003)
    for i in range(5):
        a=i*math.tau/5;verts=[]
        for y in [-.113,-.105]:
            for r,t in [(.043,-.15),(.19,.02),(.205,.30),(.14,.58),(.06,.44)]:
                verts.append((-.105+r*math.cos(a+t),y+.021*(r/.2),.38+r*math.sin(a+t)))
        faces=[(4,3,2,1,0),(5,6,7,8,9)]+[(j,(j+1)%5,(j+1)%5+5,j+5) for j in range(5)]
        mesh('Swept axial fan blade %02d'%i,verts,faces,p['black'],.002)
    annulus('Fan opening rolled bezel',(-.105,-.192,.38),.231,.219,.02,m,'Y')
    for i in range(7):ring('Concentric fan safety guard %02d'%i,(-.105,-.209,.38),.04+i*.028,.0027,p['steel'],'Y',64,6)
    for i in range(8):
        a=i*math.tau/8
        rod('Guard radial spoke',(-.105,-.211,.38),(-.105+.213*math.cos(a),-.211,.38+.213*math.sin(a)),.0027,p['steel'],8)
    cylinder('Guard central cap',(-.105,-.218,.38),.032,.014,p['steel'],'Y',32,.002)
    for x in [-.397,.20,.39]:
        for z in [.142,.615]:bolt('Cabinet screw',(x,-.197,z),p['steel'],'Y',.004)
    # Side service vent slats and refrigerant valves are real assemblies.
    for z in [.43,.46,.49,.52,.55]:box('Side electrical cooling slot',(.442,.035,z),(.006,.19,.012),p['dark'],.003)
    for z in [.22,.31]:
        rod('Copper refrigerant stub',(.434,.07,z),(.502,.07,z),.009,p['copper'])
        cylinder('Brass service union',(.484,.07,z),.017,.03,p['copper'],'X',6,.001)
        cylinder('Valve cap',(.514,.07,z),.018,.025,p['black'],'X',12,.002)
    box('Side service protector',(.458,.08,.16),(.075,.17,.028),m,.005)
    return ('city-hvac-condenser','屋外エアコン室外機','Outdoor HVAC condenser','ファン開口部、回転羽根、同心円ガード、背面熱交換フィン、防振脚、配管バルブ付きの室外機。配管金具は外観表現用の近似形状。','An outdoor condenser with open fan aperture, swept fan blades, concentric guard, rear heat-exchanger fins, isolation feet and visually approximated service valves.',['air conditioner','HVAC','condenser','utility','building','室外機'])

def hood(name,x,z,r,length,m):
    # An open 240-degree tubular visor; lower gap sheds rain and exposes the lens.
    n=36;verts=[]
    for y,rad in [(0,r),(-length,r),(0,r-.006),(-length,r-.006)]:
        for i in range(n+1):
            a=math.radians(-30)+math.radians(240)*i/n
            verts.append((x+rad*math.cos(a),-.195+y,z+rad*math.sin(a)))
    k=n+1;faces=[]
    for i in range(n):faces.extend([(i,i+1,k+i+1,k+i),(2*k+i+1,2*k+i,3*k+i,3*k+i+1),(k+i,k+i+1,3*k+i+1,3*k+i),(i+1,i,2*k+i,2*k+i+1)])
    faces.extend([(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)])
    return mesh(name,verts,faces,m,.001)

def traffic_signal():
    p=palette();m=p['black']
    box('Signal foundation flange',(0,.13,.032),(.30,.30,.064),m,.016)
    for x in [-.103,.103]:
        for y in [.027,.233]:bolt('Pole anchor',(x,y,.071),p['steel'],r=.014)
    cylinder('Signal post',(0,.13,1.635),.058,3.14,p['steel'],vertices=48,bevel=.004,r2=.046)
    cylinder('Post lower sleeve',(0,.13,.24),.071,.35,m,vertices=48,bevel=.006)
    cylinder('Post cap',(0,.13,3.219),.049,.035,m,vertices=48,bevel=.005)
    box('Pole access gasket',(0,.071,.5),(.051,.007,.18),p['dark'],.009)
    box('Pole access door',(0,.065,.5),(.043,.009,.165),p['steel'],.008)
    bolt('Access screw',(0,.056,.56),m,'Y',.004)
    for z in [2.07,2.94]:
        cylinder('Post mounting collar',(0,.13,z),.069,.055,m,vertices=32,bevel=.004)
        rod('Head mounting arm',(0,.13,z),(0,-.035,z),.025,m)
    box('Signal housing',(0,-.084,2.505),(.315,.18,1.11),m,.045)
    box('Black contrast backplate',(0,-.014,2.505),(.46,.026,1.25),m,.038)
    box('Rear service lid',(0,.016,2.505),(.269,.018,.96),p['black'],.018)
    for x in [-.10,.10]:
        for z in [2.07,2.94]:bolt('Rear case fixing',(x,.029,z),p['steel'],'Y',r=.005)
    colors=[('Red lens',(.52,.022,.015)),('Amber lens',(.87,.33,.017)),('Green lens',(.018,.32,.14))]
    for i,(name,col) in enumerate(colors):
        z=2.845-i*.34;glass=mat(name,col,.2,.24)
        cylinder('Lens mounting bezel',(0,-.184,z),.126,.025,p['edge'],'Y',64,.004)
        cylinder(name,(0,-.201,z),.111,.017,glass,'Y',64,.004)
        for rr in [.035,.067,.095]:ring('Lens molded concentric prism',(0,-.212,z),rr,.0014,glass,'Y',64,6)
        hood('Deep rain and sun visor',0,z,.134,.19,m)
    for z in [2.18,2.83]:box('Housing side hinge',(.16,-.08,z),(.018,.045,.06),p['edge'],.004)
    return ('city-traffic-signal','縦型三灯交通信号機','Three-aspect traffic signal','独立した三色レンズ、庇、裏面点検蓋、取り付け金具とアンカーボルトを備えた自立式信号機。消灯した静的装飾モデルで、点灯制御や動作シミュレーションは含まない。','A complete freestanding three-aspect traffic signal with individual colored lenses, open visors, rear service lid, brackets and anchor bolts. Static unlit decorative prop; no operational timing or signal simulation.',['traffic signal','pole','street','road','signal','信号機'])

def streetlight():
    p=palette();m=p['black']
    box('Streetlight base flange',(0,0,.035),(.34,.34,.07),m,.017)
    for x in [-.118,.118]:
        for y in [-.118,.118]:bolt('Lamp post foundation anchor',(x,y,.078),p['steel'],r=.015)
    cylinder('Tapered lamp column',(0,0,2.68),.078,5.22,m,vertices=48,bevel=.004,r2=.043)
    cylinder('Protective base collar',(0,0,.16),.09,.18,m,vertices=48,bevel=.008)
    box('Post access panel gasket',(0,-.076,.63),(.065,.009,.25),p['dark'],.016)
    box('Post access panel',(0,-.083,.63),(.056,.01,.235),p['steel'],.012)
    for z in [.54,.72]:bolt('Post access fastener',(0,-.09,z),m,'Y',.004)
    # Tangent-continuous swept elbow from mast to cantilever, original profile.
    points=[(0,0,5.10),(0,0,5.25)]
    radius=.26
    for i in range(1,13):
        a=(math.pi/2)*i/12;points.append((radius*(1-math.cos(a)),0,5.25+radius*math.sin(a)))
    points.extend([(.62,0,5.51),(.92,0,5.51)])
    cu=bpy.data.curves.new('Swept streetlight arm profile','CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=.042;cu.bevel_resolution=4;cu.use_fill_caps=True
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for v,pnt in zip(sp.points,points):v.co=(*pnt,1)
    ob=bpy.data.objects.new('Continuous curved outreach arm',cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(m)
    # Low-drag luminaire with a stepped, genuinely inset LED optical assembly.
    box('Luminaire mounting socket',(.94,0,5.51),(.18,.11,.10),m,.025)
    box('Luminaire tapered upper shell',(1.19,0,5.51),(.64,.25,.095),p['steel'],.042)
    box('Luminaire lower seal',(1.23,0,5.463),(.54,.217,.012),p['dark'],.025)
    box('Recessed optical carrier',(1.23,0,5.455),(.50,.194,.012),p['black'],.025)
    optic=mat('Frosted warm optical lenses',(.91,.91,.79),.05,.22)
    for x in [1.05,1.17,1.29,1.41]:
        for y in [-.053,.053]:
            box('Individual LED optic',(x,y,5.444),(.085,.069,.015),optic,.014)
            box('LED aperture inset',(x,y,5.435),(.047,.039,.005),p['paint'],.008)
    for x in [1.03,1.45]:
        for y in [-.086,.086]:bolt('Luminaire shell fastener',(x,y,5.56),m,r=.004)
    for i in range(7):box('Luminaire cooling rib',(1.06+i*.052,0,5.563),(.018,.18,.016),p['steel'],.004)
    cylinder('Photocell pedestal',(1.00,0,5.574),.03,.025,m,vertices=32,bevel=.004)
    cylinder('Dusk sensor cap',(1.00,0,5.591),.026,.018,optic,vertices=32,bevel=.005)
    return ('city-streetlight','片持ちLED街路灯','Modern LED streetlight','連続した曲線アーム、薄型照明ヘッド、独立したLED光学部、点検扉とアンカー付きの街路灯。','A modern streetlight with a continuous curved arm, slim luminaire, individual LED optics, service door and anchored base.',['streetlight','lamp','lighting','street','LED','街路灯'])


def render_underside_qa(slug,out_dir):
    """Fresh exact-GLB underside view, not a second top view. Presentation-only fill light."""
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bounds=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    lo=Vector([min(v[i] for v in bounds) for i in range(3)])
    hi=Vector([max(v[i] for v in bounds) for i in range(3)])
    span=max(hi-lo);center=(lo+hi)/2
    bpy.ops.object.light_add(type='AREA',location=center+Vector((-.5,-.5,-1.8))*span)
    fill=bpy.context.object;fill.name='Underside QA fill';fill.data.energy=150*span*span;fill.data.size=span*1.5
    fill.rotation_euler=(center-fill.location).to_track_quat('-Z','Y').to_euler()
    qa=Path(out_dir)/'_qa';qa.mkdir(parents=True,exist_ok=True)
    render(qa/(slug+'-underside.png'),azimuth=-55,elevation=-48)
    bpy.data.objects.remove(fill,do_unlink=True)

BUILDERS=[storm_drain,inspection_cover,ventilation_outlet,hvac_condenser,traffic_signal,streetlight]

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--only');parser.add_argument('--output','--out',dest='output',default=str(Path.cwd()/'city-staging'/'infrastructure'))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    for builder in BUILDERS:
        if args.only and args.only not in (builder.__name__,'city-'+builder.__name__.replace('_','-')):continue
        reset();spec=builder();el=48 if builder in (storm_drain,inspection_cover) else 24
        publish_asset(*spec,out_dir=args.output,generator='scripts/city/infrastructure.py',elevation=el,azimuth=-70 if builder==traffic_signal else -55)
        if builder in (storm_drain,inspection_cover):render_underside_qa(spec[0],args.output)
