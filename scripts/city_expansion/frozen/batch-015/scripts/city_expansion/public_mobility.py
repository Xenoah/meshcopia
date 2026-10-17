"""Four original static public-space equipment props, CC BY 4.0, Xenoah.

Appearance geometry only: no clinical, child-use, mobility-assistance, load or
safety function, certification, engineering drawings or operating guidance.
Blender 4.3.2, original meshes, constant-color PBR. common.py stays read-only.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(
        steel=mat('Brushed satin aluminum', (.54,.59,.61), .78,.30),
        dark=mat('Graphite frame fittings', (.052,.065,.073), .35,.43),
        rubber=mat('Charcoal rubber wheels and grips', (.017,.024,.029), 0,.76),
        vinyl=mat('Black upholstery', (.035,.046,.055), 0,.65),
        blue=mat('Midnight blue powder coat', (.035,.12,.19), .3,.37),
        teal=mat('Muted teal woven textile', (.065,.28,.29), 0,.91),
        seam=mat('Dark textile bound edges', (.025,.105,.12), 0,.83),
        red=mat('Warm burgundy frame enamel', (.30,.055,.058), .35,.40),
        grey=mat('Warm grey frame enamel', (.59,.64,.63), .3,.44),
        light=mat('Pale caster hubs', (.42,.48,.49), .15,.44),
        chrome=mat('Polished support piston', (.72,.77,.79), .94,.20),
        amber=mat('Muted amber latch detail', (.62,.29,.065), .1,.53),
    )


def cyl(name, pos, radius, depth, material, axis='Z', verts=32, bevel=.0015):
    o=cylinder(name,pos,radius,depth,material,verts,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name, a, b, radius, material, verts=16):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,radius,(b-a).length,material,verts=verts,bevel=min(.001,radius*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def beam(name, a, b, width, depth, material, bevel=.003):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def ring(name, pos, major, minor, material, axis='Z', n=64, m=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,location=pos,major_radius=major,minor_radius=minor)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,name,material,smooth=True)


def path(name, points, radius, material, closed=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1
    c.bevel_depth=radius;c.bevel_resolution=2;c.use_fill_caps=not closed
    s=c.splines.new('POLY');s.points.add(len(points)-1);s.use_cyclic_u=closed
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material)
    return o


def pin(name,pos,material,axis='X',radius=.012):
    cyl(name+' pin cap',pos,radius,.008,material,axis,24,.001)


def cushion(name,pos,size,material,corner=.035):
    # Closed rounded loft with flat end faces, deterministic smooth side normals.
    x,y,z=pos;w,l,t=size;n=32;vs=[]
    for zz,inset in [(-t/2,.007),(-t/2+.006,0),(t/2-.008,0),(t/2,.009)]:
        for cx,cy,start in [(w/2-corner,l/2-corner,0),(-w/2+corner,l/2-corner,90),(-w/2+corner,-l/2+corner,180),(w/2-corner,-l/2+corner,270)]:
            for j in range(8):
                a=math.radians(start+90*j/7)
                vs.append((x+cx+(corner-inset)*math.cos(a),y+cy+(corner-inset)*math.sin(a),z+zz))
    fs=[tuple(reversed(range(n)))];fs += [tuple(range(3*n,4*n))]
    for k in range(3):
        for i in range(n):fs.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
    o=mesh(name,vs,fs,material)
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def panel_between(name,a,b,width,thick,material):
    # A restrained upholstered panel with full closed volume.
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,thick,(b-a).length),material,min(.014,thick*.25))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def basket(name,pos,bottom_size,top_size,height,material,edge):
    x,y,z=pos;bw,bl=bottom_size;tw,tl=top_size;wall=.007
    vs=[]
    for zz,w,l in [(z,bw,bl),(z+height,tw,tl),(z+height,tw-2*wall,tl-2*wall),(z+wall,bw-2*wall,bl-2*wall)]:
        vs += [(x+sx*w/2,y+sy*l/2,zz) for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    fs=[(3,2,1,0),(12,13,14,15)]
    for i in range(4):
        j=(i+1)%4
        fs += [(i,j,4+j,4+i),(4+i,4+j,8+j,8+i),(8+i,8+j,12+j,12+i)]
    mesh(name+' closed cloth shell',vs,fs,material,.003)
    path(name+' upper bound rim',[(x-tw/2,y-tl/2,z+height),(x+tw/2,y-tl/2,z+height),(x+tw/2,y+tl/2,z+height),(x-tw/2,y+tl/2,z+height)],.006,edge,True)


def wheel(name,x,y,r,width,p,top=None,yaw=0,hubmat=None):
    # Full cylindrical tire, recessed hubs and mechanically legible paired fork.
    start=list(bpy.context.scene.objects);z=r
    cyl(name+' rubber tire',(x,y,z),r,width,p['rubber'],'X',48,.003)
    for s in [-1,1]:
        cyl(name+' inset hub',(x+s*(width/2+.001),y,z),r*.60,.007,hubmat or p['light'],'X',32,.001)
        cyl(name+' axle cap',(x+s*(width/2+.006),y,z),r*.21,.009,p['dark'],'X',24,.001)
    if top:
        for s in [-1,1]:
            beam(name+' caster fork cheek',(x+s*(width/2+.012),y,z),(x+s*(width/2+.012),y+.022,top-.022),.012,.027,p['dark'],.002)
        box(name+' fork crown',(x,y+.02,top-.023),(width+.047,.046,.014),p['dark'],.003)
        cyl(name+' swivel race',(x,y+.02,top-.009),.027,.019,p['steel'],verts=24)
        cyl(name+' caster vertical stem',(x,y+.02,top+.01),.014,.026,p['steel'],verts=20)
    if yaw:
        T=Matrix.Translation((x,y,0));R=Matrix.Rotation(yaw,4,'Z')
        for o in [o for o in bpy.context.scene.objects if o not in start]:o.matrix_world=T@R@T.inverted()@o.matrix_world


def wheelchair():
    p=palette()
    # Separate large spoked rear wheels, raised handrims, small leading casters.
    for s in [-1,1]:
        x=s*.295;y=.125;z=.302
        ring('Rear wheelchair tire',(x,y,z),.278,.024,p['rubber'],'X',72,10)
        ring('Rear wheel structural rim',(x,y,z),.263,.010,p['steel'],'X',72)
        cyl('Rear hub body',(x,y,z),.034,.075,p['dark'],'X',32)
        for i in range(16):
            a=math.tau*i/16
            rod('Cross-laced rear spoke',(x+s*(.017 if i%2 else -.017),y,z),(x,y+.260*math.sin(a),z+.260*math.cos(a)),.0023,p['steel'],8)
        ring('Outboard continuous handrim',(s*.347,y,z),.242,.010,p['steel'],'X',72)
        for i in range(6):
            a=math.tau*i/6
            rod('Handrim offset mount',(x,y+.243*math.sin(a),z+.243*math.cos(a)),(s*.347,y+.243*math.sin(a),z+.243*math.cos(a)),.005,p['dark'],12)
        pin('Rear axle cap',(s*.340,y,z),p['steel'],radius=.014)
        path('Main side chair frame',[(s*.236,.26,.86),(s*.236,.235,.49),(s*.236,-.265,.49),(s*.236,-.335,.29),(s*.236,-.355,.195)],.016,p['blue'])
        rod('Rear downward axle strut',(s*.236,.22,.49),(s*.236,.125,.29),.018,p['blue'])
        rod('Lower chair side brace rail',(s*.236,.17,.29),(s*.236,-.335,.30),.013,p['blue'])
        rod('Rear wheel short axle',(s*.226,.125,.302),(s*.319,.125,.302),.014,p['steel'],24)
        wheel('Leading wheelchair caster',s*.236,-.385,.070,.033,p,.178,yaw=s*.10)
        rod('Caster frame neck',(s*.236,-.363,.18),(s*.236,-.345,.24),.022,p['steel'],24)
        # Upholstered arm pad, open supporting rails and rear attendant grips.
        path('Armrest supporting U',[(s*.245,.20,.50),(s*.245,.20,.665),(s*.245,-.205,.665),(s*.245,-.205,.50)],.012,p['steel'])
        cushion('Armrest pad',(s*.245,-.005,.684),(.063,.39,.030),p['vinyl'],.023)
        path('Rear push handle bend',[(s*.236,.256,.83),(s*.236,.275,.916),(s*.236,.39,.916)],.014,p['blue'])
        rod('Rear push handle rubber sleeve',(s*.236,.300,.916),(s*.236,.402,.916),.019,p['rubber'],24)
        # Footrests have two individual folded plates and hanging tubular stems.
        path('Footrest hanger',[(s*.211,-.27,.46),(s*.211,-.38,.32),(s*.16,-.49,.155)],.013,p['steel'])
        box('Separate footrest platform',(s*.132,-.525,.142),(.175,.175,.021),p['dark'],.009)
        for yy in [-.57,-.53,-.49]:box('Footplate shallow tread',(s*.132,yy,.154),(.134,.009,.005),p['rubber'],.001)
        pin('Footrest hanger visual hinge',(s*.233,-.27,.45),p['steel'],radius=.015)
        box('Brake lever hinge block',(s*.248,-.11,.435),(.025,.045,.043),p['dark'],.004)
        rod('Parked manual wheel-brake lever',(s*.253,-.11,.45),(s*.253,-.20,.536),.008,p['steel'],16)
        rod('Brake lever grip',(s*.253,-.19,.526),(s*.253,-.218,.555),.012,p['rubber'],16)
        box('Wheel side clothing guard',(s*.234,.024,.568),(.010,.32,.126),p['dark'],.007)
    cushion('Wheelchair seat',(0,-.022,.489),(.445,.425,.032),p['vinyl'],.028)
    panel_between('Wheelchair upholstered back',(0,.218,.515),(0,.266,.858),.438,.032,p['vinyl'])
    for x in [-.19,.19]:
        path('Back upholstery side piping',[(x,.200,.53),(x,.248,.845)],.003,p['seam'])
    rod('Lower rear cross member',(-.236,.17,.29),(.236,.17,.29),.013,p['blue'])
    beam('Crossed folding seat support A',(-.236,-.18,.297),(.21,-.18,.47),.019,.024,p['steel'])
    beam('Crossed folding seat support B',(.236,-.15,.297),(-.21,-.15,.47),.019,.024,p['steel'])
    rod('Under-seat rear brace',(-.21,.17,.46),(.21,.17,.46),.014,p['steel'])
    pin('Static crossbrace centre',(0,-.20,.385),p['dark'],'Y',.015)
    return ('city-manual-wheelchair','手動車椅子の静的プロップ','Manual wheelchair static prop',
        '公共施設の入口、待合室や街路シーンに配置する汎用手動車椅子。大きなスポーク車輪と外側ハンドリム、前部キャスター、左右独立のフットレスト、肘掛け、張り地付き座面と背、後方グリップ、座面下の交差支えを造形しています。人、介助者や別体クッションは含みません。固定姿勢の外観用モデルで、走行・折り畳み・ブレーキ・移動支援の機能はなく、医療用途、荷重定格や安全認証を示しません。製品設計や操作指示ではありません。',
        'A generic manual wheelchair appearance prop for public-building entrances, waiting areas and street scenes. Large spoked wheels have outboard handrims, with small front casters, individual footplates, armrests, upholstered seat and back, rear push grips and crossed under-seat supports. No person, attendant or separate cushion is included. Fixed static geometry has no rolling, folding, braking or mobility-assistance function and claims no clinical suitability, load rating or safety certification. It is not a product design or operating guidance.',
        ['public-space','wheelchair','mobility-prop','車椅子'])


def stroller():
    p=palette()
    for s in [-1,1]:
        # Long diagonal handle-to-front-wheel rails and shorter rear-leg rails.
        path('Stroller main side rail',[(s*.22,-.40,.185),(s*.228,-.27,.41),(s*.235,.105,.66),(s*.248,.355,1.015)],.015,p['dark'])
        path('Rear folding leg',[(s*.27,.31,.115),(s*.265,.255,.32),(s*.235,.105,.66)],.016,p['steel'])
        rod('Diagonal lower basket support',(s*.256,.28,.23),(s*.219,-.31,.27),.012,p['steel'])
        wheel('Stroller rear fixed wheel',s*.27,.31,.10,.045,p,hubmat=p['dark'])
        wheel('Stroller front swivel wheel',s*.22,-.40,.079,.035,p,.183,yaw=s*.16,hubmat=p['dark'])
        cyl('Round folding hinge',(s*.251,.105,.66),.040,.026,p['dark'],'X',32,.003)
        pin('Hinge centre fastener',(s*.269,.105,.66),p['steel'],radius=.014)
        box('Folding release tab',(s*.254,.126,.706),(.027,.044,.016),p['amber'],.003)
        rod('Seat side support',(s*.193,-.21,.54),(s*.193,.19,.79),.013,p['dark'])
        path('Open front bumper bar',[(s*.205,.07,.65),(s*.22,-.225,.665),(s*.18,-.30,.665)],.014,p['dark'])
    rod('Stroller rear axle',(-.28,.31,.10),(.28,.31,.10),.013,p['steel'])
    rod('Rear foot-brake appearance bar',(-.21,.33,.17),(.21,.33,.17),.011,p['dark'])
    for s in [-1,1]:rod('Rear brake-bar side link',(s*.21,.33,.17),(s*.269,.31,.12),.011,p['dark'])
    box('Rear brake pedal',(0,.351,.183),(.095,.055,.019),p['dark'],.005)
    path('Continuous upper push handle',[(-.248,.355,1.015),(-.225,.402,1.042),(.225,.402,1.042),(.248,.355,1.015)],.018,p['rubber'])
    rod('Lower seat crossbeam',(-.205,-.20,.51),(.205,-.20,.51),.014,p['steel'])
    cushion('Stroller textile seat',(0,-.075,.556),(.378,.31,.040),p['teal'],.034)
    panel_between('Reclined textile seat back',(0,.061,.57),(0,.226,.867),.38,.043,p['teal'])
    panel_between('Angled padded calf panel',(0,-.22,.55),(0,-.342,.395),.33,.028,p['teal'])
    box('Foot ledge',(0,-.352,.389),(.34,.075,.025),p['dark'],.009)
    rod('Bumper front padded crosspiece',(-.18,-.30,.665),(.18,-.30,.665),.020,p['rubber'],24)
    # Closed-volume textile straps sit forward of the seat, not separate props.
    for s in [-1,1]:
        beam('Shoulder harness webbing',(s*.101,.178,.802),(s*.045,.045,.608),.028,.006,p['seam'],.001)
        beam('Waist harness webbing',(s*.169,-.02,.598),(s*.03,-.04,.595),.027,.006,p['seam'],.001)
    box('Five-point harness centre buckle',(0,-.045,.608),(.055,.024,.047),p['dark'],.007)
    beam('Harness crotch strap',(0,-.15,.580),(0,-.047,.602),.027,.006,p['seam'],.001)
    basket('Lower stroller storage basket',(0,.005,.215),(.33,.43),(.42,.52),.18,p['seam'],p['dark'])
    for s in [-1,1]:
        for y in [-.15,.18]:beam('Basket hanging textile loop',(s*.20,y,.37),(s*(.231 if y<0 else .258),y,.49),.022,.008,p['seam'],.001)
    # Open canopy: a thick arch loft with visible inside and no front/back wall.
    # The shell is closed around its perimeter; the large front aperture is real.
    nx=25;nt=9;vs=[]
    for shell in [0,1]:
        for k in range(nt):
            t=k/(nt-1);y=.25-.48*t;base=.857+.048*t
            for i in range(nx):
                a=math.pi*i/(nx-1);r=.232-shell*.006;h=.228-.025*t-shell*.006
                vs.append((r*math.cos(a),y,base+h*math.sin(a)))
    count=nx*nt;fs=[]
    for k in range(nt-1):
        for i in range(nx-1):
            a=k*nx+i;b=a+1;c=a+nx+1;d=a+nx
            fs += [(a,b,c,d),(count+d,count+c,count+b,count+a)]
    perimeter=list(range(nx))+[k*nx+nx-1 for k in range(1,nt)]+list(range((nt-1)*nx+nx-2,(nt-1)*nx-1,-1))+[k*nx for k in range(nt-2,0,-1)]
    for j,a in enumerate(perimeter):
        b=perimeter[(j+1)%len(perimeter)];fs.append((a,count+a,count+b,b))
    o=mesh('Extended open textile sun canopy',vs,fs,p['teal'])
    for f in o.data.polygons:f.use_smooth=True
    for t in [0,.50,1]:
        points=[]
        for i in range(nx):
            a=math.pi*i/(nx-1)
            points.append((.233*math.cos(a),.25-.48*t,.857+.048*t+(.229-.025*t)*math.sin(a)))
        path('Canopy bow and bound seam',points,.005,p['seam'])
    for s in [-1,1]:
        path('Canopy lower side hem',[(s*.232,.25,.857),(s*.232,-.23,.905)],.005,p['seam'])
        rod('Canopy side hinge support',(s*.224,.19,.79),(s*.232,.25,.857),.009,p['dark'])
        pin('Canopy hinge',(s*.239,.20,.824),p['steel'],radius=.013)
    return ('city-open-baby-stroller','幌を広げたベビーカーの静的プロップ','Open-canopy baby stroller static prop',
        '公園、歩道や公共施設の待合スペースに配置する、幌を広げた汎用ベビーカー。実際に開いた幌と内側、布地の座面と斜めの背、ハーネス、折り畳み部の丸い継手、下部収納バスケット、前方旋回キャスター、後輪と押し手を造形しています。子供、人、荷物や玩具は含みません。固定の外観用モデルで、折り畳み・走行・ブレーキ・拘束や子供の使用を支える機能はなく、荷重定格や安全認証はありません。育児用品の設計や操作指示ではありません。',
        'A generic stroller with extended open canopy for park, sidewalk and public waiting-area scenes. Features a genuinely open canopy with visible inside, textile seat and reclined back, harness, round folding joints, lower storage basket, front swivel casters, rear wheels and push handle. No child, person, luggage or toys are included. Fixed appearance geometry has no folding, rolling, braking, restraint or child-use function, load rating or safety certification. It is not a childcare product design or operating guidance.',
        ['public-space','stroller','open-canopy','ベビーカー'])


def rollator():
    p=palette()
    for s in [-1,1]:
        wheel('Rollator front swivel wheel',s*.251,-.265,.092,.037,p,.205,yaw=s*.12,hubmat=p['dark'])
        wheel('Rollator rear fixed wheel',s*.278,.275,.092,.040,p,hubmat=p['dark'])
        path('Rollator swept main tube',[(s*.251,-.245,.211),(s*.246,-.19,.365),(s*.245,-.055,.605),(s*.245,.13,.842)],.017,p['red'])
        path('Rollator rear leg',[(s*.278,.275,.092),(s*.267,.235,.27),(s*.248,-.040,.584)],.016,p['red'])
        rod('Rear axle short stud',(s*.253,.275,.092),(s*.300,.275,.092),.011,p['steel'])
        cyl('Frame folding joint',(s*.264,-.037,.588),.035,.023,p['dark'],'X',28,.003)
        pin('Folding joint cap',(s*.28,-.037,.588),p['steel'],radius=.012)
        rod('Handle height sleeve',(s*.245,.106,.805),(s*.245,.16,.887),.021,p['dark'],24)
        path('Ergonomic rear handgrip',[(s*.245,.155,.874),(s*.245,.236,.905),(s*.245,.307,.899)],.021,p['rubber'])
        path('Open squeeze brake lever',[(s*.245,.172,.868),(s*.245,.204,.846),(s*.245,.278,.842),(s*.245,.298,.875)],.006,p['dark'])
        path('Brake cable loop',[(s*.249,.171,.852),(s*.270,.135,.72),(s*.285,.065,.615),(s*.292,.12,.43),(s*.288,.24,.22),(s*.285,.274,.147)],.0035,p['rubber'])
        box('Rear tire brake shoe',(s*.278,.273,.187),(.041,.055,.018),p['dark'],.003)
        rod('Seat frame side rail',(s*.218,-.17,.537),(s*.218,.17,.537),.012,p['steel'])
        rod('Backrest upright',(s*.245,-.084,.57),(s*.245,-.16,.710),.012,p['red'])
        box('Rear wheel side bracket',(s*.252,.265,.13),(.012,.062,.084),p['dark'],.003)
    # Fold brace spans the underside without filling the rear walking opening.
    beam('Under-seat crossed stay A',(-.218,-.14,.530),(.218,.14,.530),.015,.021,p['steel'])
    beam('Under-seat crossed stay B',(.218,-.14,.514),(-.218,.14,.514),.015,.021,p['steel'])
    pin('Under-seat brace visual pivot',(0,0,.501),p['dark'],'Z',.012)
    cushion('Rollator rest seat',(0,.005,.559),(.425,.315,.040),p['vinyl'],.037)
    for y in [-.14,.15]:rod('Seat underside cross tube',(-.225,y,.534),(.225,y,.534),.012,p['steel'])
    path('Curved forward backrest rail',[(-.245,-.16,.710),(-.185,-.22,.727),(0,-.248,.732),(.185,-.22,.727),(.245,-.16,.710)],.022,p['rubber'])
    basket('Rollator under-seat storage bag',(0,-.025,.285),(.29,.22),(.385,.29),.228,p['seam'],p['dark'])
    for s in [-1,1]:
        beam('Storage bag hanging strap',(s*.172,-.16,.495),(s*.172,-.16,.55),.025,.008,p['vinyl'],.001)
        box('Storage bag side tab',(s*.202,-.03,.482),(.012,.055,.035),p['vinyl'],.003)
    box('Storage bag front pocket',(0,-.177,.405),(.245,.015,.108),p['teal'],.005)
    rod('Front pocket top binding',(-.115,-.189,.456),(.115,-.189,.456),.0035,p['dark'],12)
    return ('city-four-wheel-rollator','四輪歩行器の静的プロップ','Four-wheel rollator static prop',
        '公共施設の休憩所、玄関や歩道シーンに配置する汎用四輪ロレータ。後方が開いた歩行フレーム、前方キャスターと後輪、左右の握りと開口した手ブレーキ、ケーブル、休憩用座面、湾曲した前方背当てと座面下バッグを造形しています。車椅子や買い物カートではありません。人、荷物や追加の移動補助具は含みません。静的な外観用モデルで、移動支援・支持・ブレーキ・着座の実機能、医療用途、荷重定格や安全認証はなく、製品設計や操作指示ではありません。',
        'A generic four-wheel rollator for public rest areas, entrances and sidewalk scenes. Its rear-open walking frame has front casters, rear wheels, paired grips with open handbrake levers and cables, rest seat, curved forward backrest and under-seat storage bag. This is not a wheelchair or shopping trolley. No person, load or additional mobility aid is included. Static appearance geometry provides no mobility-assistance, support, braking or seating function, clinical suitability, load rating or safety certification, and is not a product design or operating guidance.',
        ['public-space','rollator','walking-frame','歩行器'])


def stretcher():
    p=palette()
    for x in [-.275,.275]:
        for y in [-.74,.74]:
            wheel('Transfer trolley caster',x,y,.095,.047,p,.221,yaw=(.17 if x*y>0 else -.10))
            box('Caster mounting plate',(x,y+.02,.236),(.095,.086,.019),p['grey'],.004)
            box('Caster brake pedal',(x,y-.045,.194),(.067,.082,.016),p['dark'],.004)
        beam('Low chassis side beam',(x,-.79,.266),(x,.79,.266),.054,.052,p['grey'],.005)
    for y in [-.68,.68]:beam('Lower chassis crossmember',(-.29,y,.267),(.29,y,.267),.052,.052,p['grey'],.004)
    for y in [-.59,-.43,.59]:beam('Lower support attachment crossmember',(-.275,y,.279),(.275,y,.279),.045,.048,p['grey'],.004)
    # Two offset scissor pairs are distinct from the low mechanic's creeper.
    for s in [-1,1]:
        beam('Tall outer support strut',(s*.215,-.59,.285),(s*.215,.59,.726),.041,.056,p['grey'],.004)
        beam('Tall inner crossing strut',(s*.170,.59,.285),(s*.170,-.59,.726),.041,.056,p['steel'],.004)
        cyl('Large support crossing pivot',(s*.215,0,.505),.045,.100,p['dark'],'X',32,.002)
        pin('Support pivot cap',(s*.271,0,.505),p['steel'],radius=.024)
        for yy,zz in [(-.59,.285),(.59,.285),(-.59,.726),(.59,.726)]:
            pin('Scissor end pivot',(s*.243,yy,zz),p['dark'],radius=.024)
        beam('Upper mattress support rail',(s*.291,-.93,.743),(s*.291,.93,.743),.045,.048,p['grey'],.005)
        # Side rail has real open bays and rounded top corners.
        path('Raised open side rail',[(s*.35,-.64,.76),(s*.35,-.64,1.035),(s*.35,-.60,1.073),(s*.35,.60,1.073),(s*.35,.64,1.035),(s*.35,.64,.76)],.014,p['steel'])
        rod('Side rail lower horizontal',(s*.35,-.64,.861),(s*.35,.64,.861),.011,p['steel'])
        for yy in [-.37,0,.37]:rod('Side rail vertical',(s*.35,yy,.861),(s*.35,yy,1.073),.010,p['steel'])
        for yy in [-.64,.64]:
            box('Side rail lower joint',(s*.35,yy,.785),(.048,.065,.055),p['dark'],.005)
            pin('Rail hinge cap',(s*.379,yy,.785),p['steel'],radius=.016)
            rod('Rail-to-deck outrigger',(s*.292,yy,.768),(s*.35,yy,.768),.013,p['steel'])
        box('Rail release tab',(s*.371,-.58,.809),(.014,.036,.024),p['amber'],.003)
    for y in [-.84,-.59,-.20,.36,.59,.84]:beam('Mattress platform transverse support',(-.29,y,.739),(.29,y,.739),.037,.040,p['grey'],.003)
    box('Mattress platform pan',(0,-.22,.778),(.586,1.43,.021),p['grey'],.008)
    cushion('Long stretcher mattress',(0,-.24,.827),(.60,1.39,.077),p['teal'],.054)
    # Short head section is fixed at a shallow raised angle with clear hinge seam.
    start=Vector((0,.47,.80));end=Vector((0,.927,.923));d=end-start
    head=box('Fixed raised head deck',(start+end)/2,(.586,.024,d.length),p['grey'],.006)
    head.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    pad=box('Fixed raised head mattress',(start+end)/2+Vector((0,-.010,.052)),(.60,.075,d.length),p['teal'],.018)
    pad.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    rod('Head segment visual hinge',(-.305,.47,.797),(.305,.47,.797),.017,p['steel'],24)
    for x in [-.215,.215]:
        rod('Fixed head tilt stay',(x,.68,.745),(x,.84,.89),.012,p['steel'])
        pin('Head tilt stay fixing',(x,.68,.752),p['dark'],radius=.011)
    # Distinct central cylinder, underside links and fixed foot control detail.
    rod('Support lift cylinder',(0,-.43,.288),(0,.10,.515),.038,p['dark'],32)
    rod('Lift piston visual extension',(0,.07,.502),(0,.405,.648),.021,p['chrome'],24)
    rod('Cylinder upper eye crossbar',(-.235,.405,.648),(.235,.405,.648),.017,p['steel'],24)
    box('Central lower cylinder bracket',(0,-.43,.282),(.17,.10,.056),p['grey'],.006)
    path('Side foot control lever',[(.08,-.43,.286),(.19,-.48,.261),(.38,-.48,.247)],.012,p['steel'])
    box('Fixed pedal pad',(.391,-.48,.25),(.115,.082,.023),p['rubber'],.006)
    for y in [-1.01,1.01]:
        s=1 if y>0 else -1
        path('End pushing handle',[(-.27,s*.91,.755),(-.27,y,.90),(-.23,s*1.05,.925),(.23,s*1.05,.925),(.27,y,.90),(.27,s*.91,.755)],.017,p['steel'])
        rod('End pushing grip',(-.19,s*1.05,.925),(.19,s*1.05,.925),.022,p['rubber'],24)
        for x in [-.315,.315]:
            cyl('Deck corner protective roller',(x,s*.925,.777),.047,.041,p['rubber'],verts=32,bevel=.004)
    return ('city-transfer-stretcher-trolley','搬送ストレッチャーの静的プロップ','Transfer stretcher trolley static prop',
        '公共施設の救護室や医療施設の廊下を可視化するための、背の高い搬送ストレッチャー。長いマットレスと少し起きた頭部、開口のある左右の側柵、上下の台枠、交差した高さ支持材、シリンダーの外観、四輪キャスターと両端の押し手を造形しています。低い整備用クリーパーとは異なる高床の搬送機器シルエットです。人、患者、寝具、医療器具や別体の移乗補助具は含みません。全て固定された外観用モデルで、医療・搬送・昇降・拘束・ブレーキの機能、荷重定格や安全認証はなく、治療・製品設計・操作の指示ではありません。',
        'A tall transfer-stretcher appearance prop for visualizing public first-aid rooms and healthcare corridors. Features a long mattress with slightly raised head section, open side rails, separate upper and lower chassis, crossed height-support struts, visual cylinder, four casters and pushing handles at both ends. Its high transfer-equipment silhouette is distinct from a low garage creeper. No person, patient, bedding, medical instruments or separate transfer aid is included. All parts are fixed, without clinical, transfer, lifting, restraint or braking function, load rating or safety certification. It provides no treatment, product-design or operating guidance.',
        ['public-space','stretcher','transfer-trolley','ストレッチャー'])


BUILDERS=[wheelchair,stroller,rollator,stretcher]
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-015/assets');parser.add_argument('--only',default='')
    a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    for fn in BUILDERS:
        reset();spec=fn()
        if a.only and spec[0]!=a.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/public_mobility.py',azimuth=-53,elevation=26)
        render(out/'_qa'/f'{spec[0]}-underside.png',azimuth=127,elevation=-26,size=800)
