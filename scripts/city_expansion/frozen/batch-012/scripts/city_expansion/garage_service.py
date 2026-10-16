"""Four original static garage scene props for Xenoah / Meshcopia, CC BY 4.0.

Original geometry and constant-color PBR design, no imported assets or fonts.
Not load-rated equipment, engineering drawings, operational instructions or safety
certification. Blender 4.3.2. Shared common.py is intentionally read-only.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(
        red=mat('Workshop vermilion powder coat', (.49, .064, .032), .32, .37),
        blue=mat('Tire machine petrol blue enamel', (.035, .20, .265), .3, .38),
        dark=mat('Graphite frame enamel', (.035, .048, .055), .35, .48),
        steel=mat('Satin zinc plated steel', (.48, .53, .55), .82, .31),
        chrome=mat('Polished hydraulic rod', (.64, .69, .71), .92, .21),
        iron=mat('Dark cast iron', (.105, .12, .13), .65, .62),
        rubber=mat('Black moulded rubber', (.014, .020, .024), 0, .83),
        vinyl=mat('Black upholstery vinyl', (.032, .038, .044), 0, .56),
        thread=mat('Grey upholstery welt', (.14, .16, .17), 0, .67),
        brass=mat('Brass hose connections', (.43, .28, .085), .8, .36),
        face=mat('Unmarked warm gauge face', (.76, .77, .69), .05, .46),
    )


def cyl(name, pos, radius, depth, material, axis='Z', verts=40, bevel=.002):
    # Small hardware retains round silhouettes without oversized radial meshes.
    verts=min(verts,16 if radius < .007 else 24 if radius < .03 else 48)
    o = cylinder(name, pos, radius, depth, material, verts, bevel=bevel)
    for modifier in o.modifiers:
        if modifier.type=='BEVEL': modifier.segments=1
    if axis == 'X': o.rotation_euler[1] = math.pi / 2
    if axis == 'Y': o.rotation_euler[0] = math.pi / 2
    for f in o.data.polygons: f.use_smooth = len(f.vertices) == 4
    return o


def rod(name, start, end, radius, material, verts=28):
    a, b = Vector(start), Vector(end)
    o = cyl(name, (a+b)/2, radius, (b-a).length, material, verts=verts, bevel=min(.0015, radius*.15))
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return o


def beam(name, start, end, width, depth, material, bevel=.004):
    a, b = Vector(start), Vector(end)
    o = box(name, (a+b)/2, (width, depth, (b-a).length), material, bevel)
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return o


def hollow_beam(name, start, end, width, depth, wall, material):
    """Closed wall shell with genuine open rectangular ends, not black decals."""
    a, b = Vector(start), Vector(end)
    length = (b-a).length
    outer = [(-width/2, -depth/2), (width/2, -depth/2), (width/2, depth/2), (-width/2, depth/2)]
    inner = [(-width/2+wall, -depth/2+wall), (width/2-wall, -depth/2+wall), (width/2-wall, depth/2-wall), (-width/2+wall, depth/2-wall)]
    vs = [(x, y, z) for z in [-length/2, length/2] for ring in [outer, inner] for x, y in ring]
    faces = []
    for i in range(4):
        j = (i+1) % 4
        faces += [(i, j, j+8, i+8), (i+4, i+12, j+12, j+4), (i, i+4, j+4, j), (i+8, j+8, j+12, i+12)]
    o = mesh(name, vs, faces, material, .0015)
    o.location = (a+b)/2
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return o


def profile_x(name, x, width, yz, material, bevel=.003):
    n = len(yz)
    vs = [(xx, y, z) for xx in [x-width/2, x+width/2] for y, z in yz]
    fs = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    fs += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    return mesh(name, vs, fs, material, bevel)


def fastener(name, pos, material, axis='Z', radius=.008, sign=1):
    idx = 'XYZ'.index(axis)
    cyl(name+' washer', pos, radius*1.55, radius*.28, material, axis, 16, 0)
    p = list(pos); p[idx] += sign*radius*.4
    cyl(name+' hexagonal head', p, radius, radius*.72, material, axis, 6, .0007)


def ring_rect_xy(name, x, y, z, width, length, corner, thickness, material):
    pts = []
    for cx, cy, angle in [(width/2-corner, length/2-corner, 0), (-width/2+corner, length/2-corner, 90), (-width/2+corner, -length/2+corner, 180), (width/2-corner, -length/2+corner, 270)]:
        for i in range(9):
            a = math.radians(angle+i*90/8)
            pts.append((x+cx+corner*math.cos(a), y+cy+corner*math.sin(a), z))
    # Cyclic curve avoids a duplicate cap seam in the rounded closed rail.
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions='3D'; c.bevel_depth=thickness; c.bevel_resolution=3
    s=c.splines.new('POLY'); s.points.add(len(pts)-1); s.use_cyclic_u=True
    for p, co in zip(s.points, pts): p.co=(*co, 1)
    o=bpy.data.objects.new(name, c); bpy.context.collection.objects.link(o); c.materials.append(material)
    return o


def cushion(name, pos, width, length, thickness, material, corner=.065):
    x, y, z = pos
    vs=[]
    # Soft-sided closed loft; top face remains a restrained broad cushion.
    levels=[(-thickness/2, .011), (-thickness/2+.006, .003), (thickness/2-.010, 0), (thickness/2, .009)]
    for zz, inset in levels:
        for cx, cy, a0 in [(width/2-corner, length/2-corner, 0), (-width/2+corner, length/2-corner, 90), (-width/2+corner, -length/2+corner, 180), (width/2-corner, -length/2+corner, 270)]:
            for k in range(9):
                angle=math.radians(a0+k*90/8)
                vs.append((x+cx+(corner-inset)*math.cos(angle), y+cy+(corner-inset)*math.sin(angle), z+zz))
    n=36; fs=[tuple(reversed(range(n)))]
    for j in range(3):
        for i in range(n): fs.append((j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i))
    fs.append(tuple(range(3*n,4*n)))
    o=mesh(name,vs,fs,material)
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    mod=o.modifiers.new('Upholstery weighted normals','WEIGHTED_NORMAL'); mod.keep_sharp=True
    return o


def caster(name, x, y, radius, width, top, p, yaw=0, color=None):
    """A distinct wheel, axle, paired fork cheeks, swivel and mounting plate."""
    color = color or p['dark']
    start=set(bpy.context.scene.objects)
    z=radius
    cyl(name+' rubber wheel',(x,y,z),radius,width,p['rubber'],'X',40,.002)
    for sign in [-1,1]:
        cyl(name+' recessed wheel hub',(x+sign*(width/2+.001),y,z),radius*.49,.006,p['steel'],'X',32,.001)
        # Fork is offset in Y from the swivel, leaving the wheel silhouette clear.
        profile_x(name+' formed fork cheek',x+sign*(width/2+.008),.008,[(y-.020,z+.005),(y-.020,top-.012),(y+.014,top-.012),(y+.022,z+.015),(y+.011,z-.009),(y-.011,z-.009)],color,.0015)
        fastener(name+' axle end',(x+sign*(width/2+.014),y,z),p['steel'],'X',.006,sign)
    box(name+' fork crown',(x,y-.002,top-.017),(width+.025,.041,.010),color,.002)
    cyl(name+' swivel race',(x,y-.004,top-.004),.026,.016,p['steel'],verts=32,bevel=.001)
    box(name+' mounting plate',(x,y-.004,top+.008),(.066,.061,.009),color,.003)
    for xx in [-.023,.023]:
        for yy in [-.020,.020]:fastener(name+' mount screw',(x+xx,y-.004+yy,top+.014),p['steel'],radius=.0035)
    if yaw:
        from mathutils import Matrix
        R=Matrix.Rotation(yaw,4,'Z');T=Matrix.Translation((x,y,0))
        for o in set(bpy.context.scene.objects)-start: o.matrix_world=T@R@T.inverted()@o.matrix_world


def jack():
    p=palette()
    # Long low side rails with a genuine open center, not a pallet-jack fork.
    rail=[(-.455,.061),(-.455,.109),(-.31,.132),(.21,.191),(.35,.167),(.385,.103),(.385,.064)]
    for x in [-.142,.142]:
        profile_x('Swept low jack chassis rail',x,.025,rail,p['red'],.005)
        for y,z in [(-.36,.092),(.24,.128)]:fastener('Chassis side pin',(x+(.018 if x>0 else -.018),y,z),p['steel'],'X',.011,1 if x>0 else -1)
    box('Rear pump bed',(0,.255,.090),(.265,.24,.022),p['dark'],.003)
    box('Chassis front bridge',(0,-.36,.085),(.27,.052,.035),p['red'],.003)
    rod('Front continuous wheel axle',(-.214,-.38,.058),(.214,-.38,.058),.012,p['steel'])
    for x in [-.184,.184]:
        cyl('Large fixed front steel roller',(x,-.38,.058),.058,.052,p['iron'],'X',48,.004)
        cyl('Front roller hub',(x+(.03 if x>0 else -.03),-.38,.058),.030,.009,p['steel'],'X',32,.001)
        fastener('Front wheel axle',(x+(.037 if x>0 else -.037),-.38,.058),p['steel'],'X',.009,1 if x>0 else -1)
    for x in [-.192,.192]:
        box('Rear caster outrigger',(x*.78,.30,.112),(.11,.083,.021),p['red'],.004)
        caster('Rear jack swivel caster',x,.30,.038,.027,.091,p,yaw=.20 if x<0 else -.22)
    # Paired rising lift plates and separate thin parallel-motion links.
    arm=[(.255,.105),(.272,.148),(-.227,.272),(-.31,.251),(-.32,.212),(-.21,.205)]
    for x in [-.090,.090]:
        profile_x('Raised lift arm plate',x,.028,arm,p['red'],.004)
        rod('Saddle leveling link',(x*1.36,.20,.153),(x*1.36,-.275,.227),.009,p['steel'],24)
        for y,z in [(.255,.132),(-.276,.234)]:fastener('Lift arm pivot',(x+(.021 if x>0 else -.021),y,z),p['steel'],'X',.014,1 if x>0 else -1)
    rod('Main lift-arm cross pin',(-.144,.255,.132),(.144,.255,.132),.016,p['steel'],32)
    box('Lift-arm connecting saddle bridge',(0,-.265,.249),(.21,.07,.033),p['red'],.005)
    cyl('Saddle swivel stem',(0,-.275,.278),.026,.047,p['steel'],verts=40)
    cyl('Circular load saddle',(0,-.275,.302),.073,.022,p['iron'],verts=64,bevel=.003)
    cyl('Saddle rubber contact inset',(0,-.275,.316),.061,.011,p['rubber'],verts=56,bevel=.002)
    for i in range(4):
        a=math.tau*i/4
        o=box('Raised saddle retaining lip',(.066*math.cos(a),-.275+.066*math.sin(a),.323),(.031,.012,.020),p['iron'],.002)
        o.rotation_euler[2]=a+math.pi/2
    rod('Hydraulic barrel',(0,.294,.132),(0,-.068,.174),.032,p['iron'],48)
    rod('Polished ram extension',(0,-.061,.175),(0,-.204,.205),.017,p['chrome'],40)
    rod('Ram collar',(0,-.054,.172),(0,-.086,.178),.036,p['steel'],40)
    box('Hydraulic pump block',(0,.285,.133),(.102,.104,.071),p['iron'],.005)
    cyl('Pump plunger',(.047,.296,.184),.014,.072,p['chrome'],verts=32)
    cyl('Release screw',(-.043,.325,.184),.013,.022,p['steel'],verts=24)
    # Pump return spring has separated coils, outside the chassis near the rear.
    points=[]
    for i in range(121):
        t=i/120; a=t*math.tau*8
        points.append((.057+.011*math.cos(a),.205+.089*t,.147+.011*math.sin(a)))
    tube('Pump linkage return spring',points,.0021,p['steel'],1)
    for x in [-.032,.032]:profile_x('Pump handle clevis cheek',x,.012,[(.312,.12),(.397,.16),(.423,.25),(.387,.264),(.335,.192)],p['red'],.002)
    rod('Handle fork pivot',(-.055,.366,.184),(.055,.366,.184),.011,p['steel'])
    for x in [-.059,.059]:fastener('Handle pivot nut',(x,.366,.184),p['steel'],'X',.010,1 if x>0 else -1)
    rod('Angled handle socket',(0,.378,.202),(0,.470,.335),.024,p['iron'],40)
    rod('Long removable pump handle',(0,.452,.309),(0,.936,1.019),.017,p['steel'],40)
    rod('Upper rubber handle grip',(0,.829,.862),(0,.940,1.025),.024,p['rubber'],40)
    rod('Handle grip lower collar',(0,.824,.855),(0,.837,.874),.026,p['iron'],32)
    fastener('Socket retaining screw',(.026,.445,.298),p['steel'],'X',.007)
    # Open carry loop and underside fasteners expose the layered construction.
    tube('Chassis carrying loop',[(-.14,.055,.18),(-.205,.055,.20),(-.22,-.065,.20),(-.14,-.065,.18)],.009,p['dark'],2)
    for x in [-.105,.105]:
        for y in [.18,.32]:fastener('Pump tray underside fastener',(x,y,.076),p['steel'],radius=.006,sign=-1)
    return ('city-hydraulic-floor-jack','低床油圧フロアジャッキ','Low-profile hydraulic floor jack',
        '自動車整備ガレージの床に置く、低い車輪付きフロアジャッキ。開いた左右シャーシ、固定前輪と後部旋回キャスター、持ち上げアームと水平リンク、丸いゴム付きサドル、油圧シリンダー、ポンプ機構と斜めの長いハンドルを個別造形しています。車両、ジャッキスタンド、荷物は含みません。外観用の静的プロップであり、揚重能力・安全性・実動作を示さず、設計・操作・安全指示や認証ではありません。',
        'A low wheeled floor jack for automotive service-garage scenes, with an open paired chassis, fixed front rollers, rear swivel casters, raised lifting arm and leveling links, rubber-inset round saddle, hydraulic barrel, pump details and a long inclined handle. Vehicle, axle stands and load are not included. This is a static appearance prop, not load-rated, safe or functioning equipment; it provides no engineering, operation or safety instructions and no certification.',
        ['garage','floor-jack','hydraulic','maintenance','ジャッキ'])


def crane():
    p=palette()
    # Wide open H footprint. Each long leg has its own folding knuckle and pin.
    hollow_beam('Rear hoist cross tube',(-.48,.39,.145),(.48,.39,.145),.11,.11,.009,p['red'])
    for x in [-.37,.37]:
        hollow_beam('Long forward folding outrigger',(x,.28,.145),(x,-.90,.145),.092,.11,.008,p['red'])
        box('Front leg end cover',(x,-.909,.145),(.086,.012,.098),p['dark'],.003)
        box('Leg hinge bed',(x,.26,.192),(.15,.18,.026),p['iron'],.004)
        for sign in [-1,1]:
            profile_x('Folding leg hinge ear',x+sign*.065,.014,[(.18,.14),(.18,.27),(.30,.29),(.35,.22),(.35,.14)],p['red'],.004)
            fastener('Folding leg transverse pin',(x+sign*.078,.25,.227),p['steel'],'X',.016,sign)
        for y in [-.78,.41]:
            caster('Hoist outrigger caster',x,y,.053,.039,.119,p,yaw=(.1 if x<0 else -.16),color=p['iron'])
        # Small rear wheels extend the rear leg ends, not duplicate another prop.
    for x in [-.41,.41]:
        box('Rear stabilizer foot',(x,.57,.14),(.105,.30,.083),p['red'],.005)
        caster('Rear hoist stabilizer caster',x,.64,.050,.038,.11,p,yaw=math.pi/2,color=p['iron'])
    box('Mast base saddle',(0,.37,.221),(.29,.27,.083),p['red'],.006)
    hollow_beam('Upright rectangular crane mast',(0,.36,.24),(0,.36,1.48),.14,.14,.010,p['red'])
    for x in [-.27,.27]:
        beam('Rear diagonal mast brace',(x,.39,.205),(0,.36,.86),.047,.042,p['red'])
        for yy,zz in [(.39,.23)]:fastener('Brace foot fixing',(x,yy,zz),p['steel'],radius=.010)
    # Distinct rear handle, service caps and fixed boom hinge.
    tube('Rear push handle',[(-.08,.44,.91),(-.20,.53,.91),(-.20,.57,1.08),(.20,.57,1.08),(.20,.53,.91),(.08,.44,.91)],.016,p['dark'],2)
    rod('Rear handle grip',(-.15,.57,1.08),(.15,.57,1.08),.022,p['rubber'],32)
    for x in [-.105,.105]:
        profile_x('Boom hinge side plate',x,.024,[(.21,1.40),(.21,1.58),(.35,1.65),(.46,1.59),(.46,1.40)],p['red'],.004)
        fastener('Large boom hinge bolt',(x+(.020 if x>0 else -.020),.34,1.55),p['steel'],'X',.022,1 if x>0 else -1)
    # Outer square sleeve and narrower visible telescopic extension.
    a=Vector((0,.34,1.55)); b=Vector((0,-.52,1.78)); c=Vector((0,-.90,1.882))
    hollow_beam('Hoist outer boom sleeve',a,b,.12,.12,.010,p['red'])
    hollow_beam('Hoist telescopic inner boom',(0,-.38,1.743),c,.088,.088,.007,p['dark'])
    # Pin bosses around the fixed extension give real layered depth, not printed text.
    for y in [-.12,-.29,-.43]:
        z=1.55+(.34-y)*(.23/.86)
        for x in [-.064,.064]:
            cyl('Boom extension pin boss',(x,y,z),.016,.008,p['iron'],'X',28,.001)
            cyl('Boom pin recessed centre',(x+(.005 if x>0 else -.005),y,z),.008,.004,p['dark'],'X',24,.0005)
    rod('Boom locking pin',(-.088,-.29,1.719),(.088,-.29,1.719),.010,p['steel'],28)
    fastener('Boom retaining pin end',(.094,-.29,1.719),p['steel'],'X',.013)
    # Static ram is separate from the mast and boom, with visible eye joints.
    lower=(0,.19,.40); upper=(0,-.325,1.698)
    delta=Vector(upper)-Vector(lower)
    barrel_end=Vector(lower)+delta*.63
    rod('Hoist hydraulic ram barrel',lower,barrel_end,.047,p['iron'],48)
    rod('Hoist polished ram piston',barrel_end,upper,.026,p['chrome'],40)
    rod('Ram barrel gland',barrel_end-delta.normalized()*.018,barrel_end+delta.normalized()*.018,.052,p['steel'],40)
    for yy,zz in [(.19,.40),(-.325,1.698)]:
        cyl('Hydraulic eye cross-pin',(0,yy,zz),.027,.13,p['steel'],'X',32,.002)
        for x in [-.073,.073]:fastener('Ram eye nut',(x,yy,zz),p['steel'],'X',.015,1 if x>0 else -1)
    box('Ram lower clevis bed',(0,.19,.345),(.19,.17,.05),p['red'],.004)
    for x in [-.067,.067]:box('Lower hydraulic clevis plate',(x,.19,.40),(.018,.12,.13),p['red'],.004)
    # Lever at the hydraulic pump, on the operator side.
    box('Ram pump housing',(.073,.18,.46),(.074,.085,.12),p['iron'],.006)
    rod('Pump operating lever',(.093,.20,.48),(.15,.49,.88),.012,p['steel'],28)
    rod('Pump lever grip',(.139,.435,.805),(.152,.503,.90),.019,p['rubber'],32)
    cyl('Pump release valve',(.116,.17,.44),.013,.024,p['steel'],'X',24,.001)
    # A short unloaded hanging chain. Alternating links are individual closed tori.
    cyl('Boom chain anchor pin',(0,-.88,1.862),.012,.118,p['steel'],'X',28,.001)
    for i in range(5):
        o=torus('Unloaded hoist chain link %02d'%i,(0,-.90,1.817-i*.042),.022,.0045,p['steel'],segments=32)
        o.rotation_euler=(math.pi/2,0,0) if i%2==0 else (0,math.pi/2,0)
        # In local XY, elongate the vertical direction after rotation.
        o.scale=(1,1.42,1) if i%2==0 else (1.42,1,1)
    cyl('Hook swivel neck',(0,-.90,1.603),.013,.070,p['steel'],verts=28,bevel=.001)
    # Open C hook in YZ, intentionally unmistakably unloaded.
    pts=[]
    for i in range(31):
        ang=math.radians(85+285*i/30)
        pts.append((0,-.90+.045*math.cos(ang),1.516+.050*math.sin(ang)))
    tube('Open forged lifting hook',pts,.012,p['iron'],3)
    beam('Hook latch visual insert',(0,-.86,1.526),(0,-.905,1.555),.008,.010,p['steel'],.001)
    return ('city-folding-engine-crane','折りたたみ脚のエンジンクレーン','Folding-leg workshop engine crane',
        '自動車工場用の独立した車輪付きエンジンクレーン。開いたH形の脚、折りたたみ部のヒンジとピン、斜め補強を持つマスト、伸長した角形ブーム、油圧ラム、ポンプレバー、短い鎖と空のフックを造形。脚やブームは固定配置で可動しません。エンジン、車両、吊り荷、吊り具一式は含みません。外観用の静的プロップで、荷重定格・実動作・安全認証を持たず、製作・揚重・操作・安全の指示を提供しません。',
        'A standalone wheeled engine crane for automotive workshops. Its open H-frame has folding-leg hinge plates and pins, a braced mast, extended square boom, hydraulic ram, pump lever, short chain and empty hook. Legs and boom are fixed in the shown pose with no articulation. No engine, vehicle, suspended load or complete rigging kit is included. This static appearance prop has no load rating, functioning mechanism or safety certification and supplies no engineering, lifting, operation or safety instructions.',
        ['garage','engine-crane','hoist','workshop','クレーン'])


def creeper():
    p=palette()
    # Broad low deck with a tall separate headrest and narrow open frame perimeter.
    box('Mechanics board steel underside',(0,0,.110),(.429,.975,.021),p['dark'],.006)
    ring_rect_xy('Tubular creeper perimeter frame',0,0,.114,.478,1.043,.072,.016,p['red'])
    for y in [-.34,0,.34]:
        box('Underside caster cross member',(0,y,.091),(.50,.049,.032),p['red'],.004)
        for x in [-.17,.17]:fastener('Cross-member underside fixing',(x,y,.072),p['steel'],radius=.005,sign=-1)
    for x in [-.23,.23]:
        for j,y in enumerate([-.36,0,.36]):
            caster('Creeper caster %s %d'%('L' if x<0 else 'R',j+1),x,y,.035,.025,.078,p,yaw=(.20 if j==0 else -.20 if j==2 else 0)*(1 if x<0 else -1),color=p['iron'])
    cushion('Long upholstered body pad',(0,-.112,.148),.395,.697,.050,p['vinyl'],.047)
    ring_rect_xy('Body cushion edge welt',0,-.112,.160,.385,.687,.044,.0029,p['thread'])
    cushion('Raised upholstered headrest',(0,.351,.172),.395,.204,.094,p['vinyl'],.043)
    ring_rect_xy('Headrest edge welt',0,.351,.199,.384,.193,.039,.003,p['thread'])
    # Two shallow transverse seam bands distinguish body upholstery from a slab.
    for y in [-.25,.055]:
        box('Upholstery recessed seam',(0,y,.173),(.338,.003,.002),p['thread'],.0005)
    # A hollow carry handle is formed at the foot; no tools or person included.
    ring_rect_xy('Creeper foot carry loop',0,-.536,.119,.18,.08,.027,.010,p['dark'])
    for x in [-.145,.145]:
        for y in [-.38,.18,.37]:
            cyl('Upholstery mounting boss',(x,y,.090),.015,.018,p['iron'],verts=24,bevel=.001)
            fastener('Upholstery underside screw',(x,y,.077),p['steel'],radius=.005,sign=-1)
    box('Headrest underside reinforcement',(0,.35,.087),(.335,.108,.024),p['dark'],.004)
    return ('city-mechanic-creeper','六輪のパッド付きメカニッククリーパー','Six-caster padded mechanics creeper',
        '整備ガレージで車体の下に寝て移動する姿を表す低床クリーパー。丸い鋼管フレーム、長いクッション、独立した高いヘッドレスト、縁取りと縫い目表現、持ち手、裏面の横梁と取付部、六つの旋回キャスターを備えます。人物、車両、工具は含みません。静的な外観素材で、走行・荷重支持・安全性を検証した製品ではなく、製作・使用・安全の指示や認証を提供しません。',
        'A low rolling mechanics board for under-vehicle workshop scenes, with a rounded tubular frame, long padded cushion, separate raised headrest, welt and seam details, carry handle, underside crossmembers and mount hardware, and six complete swivel-caster assemblies. Person, vehicle and tools are not included. This is static appearance geometry, not a tested rolling, load-bearing or safety-rated product; no engineering, operation or safety instructions or certification are supplied.',
        ['garage','creeper','mechanic','padded','クリーパー'])


def annular_sector(name, radius0, radius1, start, end, z, depth, material):
    steps=18;vs=[]
    for zz in [z-depth/2,z+depth/2]:
        for r in [radius0,radius1]:
            for i in range(steps+1):
                a=start+(end-start)*i/steps;vs.append((r*math.cos(a),-.055+r*math.sin(a),zz))
    n=steps+1;fs=[]
    for i in range(steps):
        fs += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
               (i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
    fs += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    return mesh(name,vs,fs,material,.0015)


def tire_machine():
    p=palette()
    # Cabinet shell built from walls, with a genuine hollow rear ventilation bay.
    box('Machine heavy base pan',(0,0,.096),(.68,.66,.070),p['dark'],.012)
    for x in [-.265,.265]:
        for y in [-.24,.24]:
            cyl('Fixed rubber isolation foot',(x,y,.032),.041,.064,p['rubber'],verts=40,bevel=.004)
            cyl('Foot threaded support',(x,y,.068),.014,.027,p['steel'],verts=24)
    box('Front cabinet wall',(0,-.302,.408),(.625,.025,.57),p['blue'],.008)
    for x in [-.30,.30]:box('Side cabinet wall',(x,0,.408),(.025,.59,.57),p['blue'],.006)
    box('Upper cabinet deck',(0,0,.700),(.65,.635,.046),p['blue'],.009)
    box('Rear upper panel',(0,.302,.602),(.625,.022,.17),p['blue'],.005)
    box('Rear lower service panel',(0,.302,.211),(.625,.022,.18),p['blue'],.005)
    for x in [-.265,.265]:box('Rear vent perimeter upright',(x,.302,.405),(.095,.022,.214),p['blue'],.003)
    for z in [.305,.505]:box('Rear vent horizontal rim',(0,.307,z),(.44,.028,.018),p['dark'],.003)
    for j in range(7):
        o=box('Rear open ventilation louver',(0,.309,.326+j*.025),(.427,.034,.010),p['dark'],.0015)
        o.rotation_euler[0]=math.radians(-22)
    # A simple shield visible through the real gaps, not an exposed internal motor.
    box('Recessed interior dust shield',(0,.15,.405),(.45,.015,.26),p['iron'],.004)
    for x in [-.264,.264]:
        for z in [.17,.65]:fastener('Rear access screw',(x,.317,z),p['steel'],'Y',.005)
    for x in [-.277,.277]:
        for z in [.19,.64]:fastener('Front cabinet screw',(x,-.320,z),p['steel'],'Y',.005,-1)
    # Blank replaceable front plate and three actual pedal hinges.
    box('Blank front service inset',(0,-.320,.467),(.43,.012,.24),p['dark'],.006)
    box('Plain unbranded enamel insert',(0,-.328,.48),(.35,.006,.15),p['blue'],.005)
    for x in [-.187,.187]:
        for z in [.376,.559]:fastener('Front insert fastening',(x,-.331,z),p['steel'],'Y',.004,-1)
    box('Pedal box',(0,-.347,.184),(.51,.13,.125),p['dark'],.008)
    for j,x in enumerate([-.17,0,.17]):
        cyl('Foot pedal pivot',(x,-.402,.174),.013,.115,p['steel'],'X',24,.001)
        o=box('Foot pedal tread',(x,-.447,.155),(.115,.124,.023),p['iron'],.004)
        o.rotation_euler[0]=math.radians(-12)
        for y in [-.478,-.452,-.426]:box('Raised pedal grip rib',(x,y,.17+(y+.45)*.21),(.100,.008,.006),p['rubber'],.001)
        fastener('Pedal mounting screw',(x,-.39,.218),p['steel'],radius=.005)
    # Four quarter sectors leave real radial slider slots between them.
    cyl('Turntable gearbox neck',(0,-.055,.754),.115,.085,p['iron'],verts=48,bevel=.005)
    cyl('Turntable lower carrier',(0,-.055,.792),.257,.028,p['dark'],verts=64,bevel=.003)
    for j in range(4):
        a=math.tau*j/4
        annular_sector('Segmented clamp turntable',.057,.287,a+.043,a+math.pi/2-.043,.816,.026,p['steel'])
        # Steel slider seated in each open radial slot with raised gripping jaw.
        s=set(bpy.context.scene.objects)
        box('Radial jaw guide',(0,-.055+.175,.825),(.028,.145,.025),p['iron'],.002)
        box('Sliding jaw carriage',(0,-.055+.233,.849),(.064,.085,.033),p['dark'],.003)
        profile_x('Stepped steel clamping jaw',0,.062,[(.151,.858),(.151,.886),(.177,.886),(.177,.928),(.197,.928),(.219,.872),(.236,.862)],p['steel'],.002)
        for xx in [-.019,.019]:fastener('Jaw top fastening',(xx,.178,.870),p['iron'],radius=.004)
        from mathutils import Matrix
        T=Matrix.Translation((0,-.055,0));R=Matrix.Rotation(a,4,'Z')
        for o in set(bpy.context.scene.objects)-s:o.matrix_world=T@R@T.inverted()@o.matrix_world
    cyl('Table center circular boss',(0,-.055,.819),.047,.030,p['steel'],verts=40,bevel=.002)
    cyl('Center recess',(0,-.055,.837),.025,.005,p['iron'],verts=32,bevel=.001)
    # Independent rear column with swivel bearing and cantilever demount head.
    box('Rear column mounting plinth',(.19,.235,.748),(.24,.25,.065),p['dark'],.007)
    for x in [.105,.275]:
        for y in [.15,.32]:fastener('Column plinth anchoring',(x,y,.787),p['steel'],radius=.009)
    hollow_beam('Square tire-machine upright',(.19,.275,.77),(.19,.275,1.493),.125,.14,.009,p['blue'])
    box('Upright top cap',(.19,.275,1.50),(.133,.148,.025),p['dark'],.006)
    cyl('Swing arm vertical hinge',(.19,.275,1.505),.048,.145,p['steel'],verts=40,bevel=.003)
    beam('Upper lateral swing arm',(.19,.275,1.538),(.018,-.115,1.538),.080,.080,p['blue'])
    cyl('Demount shaft sleeve',(.018,-.115,1.478),.037,.19,p['dark'],verts=40,bevel=.004)
    cyl('Vertical demount adjustment shaft',(.018,-.115,1.312),.022,.45,p['chrome'],verts=40,bevel=.002)
    cyl('Top shaft grip',(.018,-.115,1.594),.034,.047,p['rubber'],verts=40,bevel=.004)
    cyl('Shaft lock boss',(.057,-.115,1.477),.020,.045,p['steel'],'X',32,.002)
    rod('Shaft lock handle',(.075,-.115,1.477),(.154,-.115,1.505),.009,p['dark'],24)
    # Triangular icosphere avoids a UV-sphere pole normal changing between runs.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=.018,location=(.158,-.115,1.507))
    finish(bpy.context.object,'Lock-handle ball',p['rubber'],0,True)
    # Distinct curved shoe at the empty table, not a tire or wheel assembly.
    box('Demount shaft foot',(.018,-.115,1.074),(.061,.068,.040),p['iron'],.008)
    shoe=profile_x('Curved demount duckhead',.038,.085,[(-.175,1.065),(-.172,1.091),(-.13,1.10),(-.071,1.081),(-.048,1.046),(-.073,1.037),(-.101,1.064),(-.14,1.068)],p['steel'],.005)
    cyl('Demount shoe guide roller',(-.027,-.149,1.057),.022,.027,p['dark'],'X',32,.002)
    # Bead breaker: side support pad, swinging lever, pneumatic cylinder and paddle.
    box('Side bead breaker rubber support',(.327,-.035,.352),(.035,.225,.235),p['rubber'],.008)
    for y in [-.113,-.072,-.031,.010,.051]:box('Bead pad vertical rib',(.348,y,.352),(.009,.010,.200),p['iron'],.0015)
    cyl('Bead arm rear hinge',(.365,.23,.315),.034,.14,p['steel'],verts=40,bevel=.002)
    beam('Bead breaker swing lever',(.37,.23,.315),(.55,-.13,.315),.055,.061,p['blue'])
    rod('Bead breaker air barrel',(.357,.12,.475),(.52,-.04,.399),.033,p['iron'],40)
    rod('Bead breaker polished piston',(.52,-.04,.399),(.565,-.145,.347),.015,p['chrome'],32)
    cyl('Paddle mounting pivot',(.56,-.145,.32),.021,.105,p['steel'],'Y',32,.001)
    # Broad curved sheet paddle faces the cabinet pad and has a rolled outer edge.
    vs=[]
    for z in [.217,.425]:
        for thickness in [0,.009]:
            for i in range(13):
                y=-.145-.112+.224*i/12
                x=.555+.048*((i-6)/6)**2+thickness
                vs.append((x,y,z))
    n=13;fs=[]
    for i in range(12):fs += [(i,i+1,2*n+i+1,2*n+i),(n+i,3*n+i,3*n+i+1,n+i+1),(i,n+i,n+i+1,i+1),(2*n+i,2*n+i+1,3*n+i+1,3*n+i)]
    fs += [(0,2*n,3*n,n),(n-1,2*n-1,4*n-1,3*n-1)]
    mesh('Curved side bead-breaking paddle',vs,fs,p['steel'],.002)
    rod('Paddle upper handle',(.59,-.09,.42),(.66,-.09,.53),.011,p['steel'],24)
    rod('Paddle hand grip',(.65,-.09,.515),(.68,-.09,.565),.018,p['rubber'],28)
    # Rear air preparation and a short parked hose loop, without a supply cable.
    box('Rear filter bracket',(-.21,.343,.646),(.12,.06,.026),p['dark'],.003)
    cyl('Air regulator body',(-.21,.36,.607),.031,.072,p['iron'],verts=32)
    cyl('Air-filter bowl',(-.21,.36,.537),.026,.080,p['steel'],verts=32,bevel=.005)
    cyl('Regulator adjustment knob',(-.21,.36,.667),.028,.045,p['rubber'],verts=32,bevel=.003)
    cyl('Pressure gauge rim',(-.21,.40,.615),.033,.021,p['steel'],'Y',40,.002)
    cyl('Blank pressure dial',(-.21,.413,.615),.028,.006,p['face'],'Y',40,.001)
    beam('Gauge needle',(-.21,.417,.615),(-.224,.417,.633),.002,.002,p['dark'],.0004)
    rod('Air coupling',(-.25,.36,.606),(-.29,.36,.606),.011,p['brass'],24)
    tube('Parked service hose',[(-.29,.36,.606),(-.37,.40,.57),(-.40,.40,.30),(-.36,.41,.20),(-.27,.41,.19),(-.22,.41,.26),(-.25,.41,.36),(-.31,.41,.40)],.008,p['rubber'],2)
    cyl('Hose parked tip',(-.31,.41,.407),.012,.043,p['brass'],verts=24,bevel=.001)
    for x in [-.22,.22]:
        for y in [-.19,.19]:fastener('Machine underside fixing',(x,y,.057),p['steel'],radius=.007,sign=-1)
    return ('city-tire-changing-machine','固定式タイヤチェンジャー','Fixed workshop tire-changing machine',
        '自動車整備店用の汎用タイヤ交換機。中空の固定キャビネット、隙間を持つ四分割ターンテーブルと四つのクランプ爪、後部支柱と旋回アーム、縦軸と脱着ヘッド、三つのフットペダル、側面のビードブレーカーの湾曲パドル、裏面ルーバーと空気調整器を造形。タイヤ、ホイール、車両、外部の圧縮空気源と電源ケーブルは含みません。外観用の静的モデルで、回転・空圧・電気・脱着機能や安全認証はなく、製作・整備・操作・安全の指示を提供しません。',
        'A generic fixed tire-changing machine for automotive workshops. Features a hollow cabinet, four-sector turntable with open slider gaps and four clamping jaws, rear upright and swing arm, vertical shaft and demount head, three foot pedals, side bead-breaking lever with curved paddle, rear louvers and air regulator. Tire, wheel, vehicle, external compressed-air supply and mains cable are not included. This is static appearance geometry with no rotation, pneumatic, electrical or demounting function or safety certification, and no engineering, maintenance, operation or safety instructions.',
        ['garage','tire-changer','workshop','automotive','タイヤチェンジャー'])


BUILDERS=[jack,crane,creeper,tire_machine]
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='batches/batch-012/assets')
    parser.add_argument('--only',default='')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=Path(args.out); out=out if out.is_absolute() else ROOT/out
    for fn in BUILDERS:
        reset(); spec=fn()
        if args.only and spec[0]!=args.only: continue
        # Front and back are actual renders reimported from the exact final GLB.
        publish_asset(*spec,out,'scripts/city_expansion/garage_service.py',azimuth=-52,elevation=26 if fn!=creeper else 34)
        render(out/'_qa'/f'{spec[0]}-underside.png',azimuth=128,elevation=-26,size=800)
