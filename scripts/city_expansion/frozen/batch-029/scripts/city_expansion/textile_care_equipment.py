"""Four original textile-care facility props. Xenoah, CC BY 4.0.
Original procedural meshes and constant PBR materials only, without external assets.
Static appearance models, not working machinery, certified products or manufacturing plans.
Author Z-up metres; immutable common.py exports metre-valued Y-up GLB and STL.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(steel=mat('Satin structural steel', (.43,.49,.51), .72,.39),
                bright=mat('Satin stainless drum and hardware', (.64,.70,.72), .78,.32),
                enamel=mat('Warm white appliance enamel', (.78,.79,.73), .08,.34),
                blue=mat('Muted blue machine enamel', (.105,.235,.285), .22,.40),
                rubber=mat('Graphite rubber and grips', (.024,.029,.032), 0,.78),
                black=mat('Dark mechanical housings', (.055,.066,.068), .22,.47),
                window=mat('Opaque smoky door window representation', (.105,.17,.195), .30,.24),
                screen=mat('Inactive dark control display', (.035,.075,.085), .12,.34),
                cloth=mat('Blue grey linen canvas appearance', (.31,.43,.47), 0,.93),
                seam=mat('Folded fabric seam binding', (.21,.31,.35), 0,.92),
                pad=mat('Desaturated teal ironing cover', (.31,.49,.49), 0,.89),
                thread=mat('Warm neutral sewing thread', (.66,.55,.35), 0,.91),
                timber=mat('Pale solid laminate worktop', (.61,.49,.32), 0,.59),
                red=mat('Muted red inactive control accent', (.49,.055,.033), 0,.48))


def cyl(name, pos, radius, depth, material, axis='Z', n=32, bevel=.001):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name, a, b, radius, material, n=20, bevel=.0008):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,radius,(b-a).length,material,n=n,bevel=min(bevel,radius*.1))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def bar(name, a, b, width, depth, material, bevel=.003):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def path(name, points, radius, material, closed=False, resolution=2):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=radius;c.bevel_resolution=resolution;c.use_fill_caps=not closed
    s=c.splines.new('POLY');s.points.add(len(points)-1);s.use_cyclic_u=closed
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material)
    return o


def ring(name, pos, major, minor, material, axis='Z', n=64, m=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,major_radius=major,minor_radius=minor,location=pos)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,name,material,smooth=True)


def screw(name,pos,material,axis='Z',r=.005):
    return cyl(name,pos,r,.004,material,axis,n=8,bevel=.0003)


def lathe(name,profile,pos,material,n=64,axis='Z'):
    """Closed radial profile; unique axis poles avoid degenerate collapsed rings."""
    vs=[];rings=[]
    for r,z in profile:
        if abs(r)<1e-10:rings.append([len(vs)]);vs.append((0,0,z))
        else:
            ids=[]
            for j in range(n):ids.append(len(vs));vs.append((r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z))
            rings.append(ids)
    fs=[]
    for a,b in zip(rings,rings[1:]+rings[:1]):
        if len(a)==len(b)==1:continue
        for j in range(n):
            if len(a)==1:fs.append((a[0],b[(j+1)%n],b[j]))
            elif len(b)==1:fs.append((a[j],a[(j+1)%n],b[0]))
            else:fs.append((a[j],a[(j+1)%n],b[(j+1)%n],b[j]))
    o=mesh(name,vs,fs,material,smooth=True);o.location=pos
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:
        zz=[o.data.vertices[i].co.z for i in f.vertices]
        f.use_smooth=max(zz)-min(zz)>1e-7
    return o


def extrusion_xy(name,outline,z0,z1,material,bevel=.004):
    vs=[(x,y,z) for z in [z0,z1] for x,y in outline];n=len(outline)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def extrusion_xz(name,outline,y0,y1,material,bevel=.004):
    vs=[(x,y,z) for y in [y0,y1] for x,z in outline];n=len(outline)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def rounded_rect(w,d,r,n=8):
    pts=[]
    for cx,cy,start in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
        for i in range(n+1):
            a=math.radians(start+i*90/n);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts


def rect_aperture(name,half_width,zbottom,ztop,zc,rad,yfront,yback,material):
    """Closed rectangular face surround with an actual circular through-opening."""
    angles=[i*math.tau/64 for i in range(64)]
    angles += [math.atan2(z-zc,x)%math.tau for x in [-half_width,half_width] for z in [zbottom,ztop]]
    angles=sorted(set(round(a,12) for a in angles));vs=[]
    def outer(a):
        dx,dz=math.cos(a),math.sin(a)
        ts=[half_width/abs(dx) if abs(dx)>1e-10 else 1e10]
        ts += [(ztop-zc)/dz] if dz>1e-10 else ([(zbottom-zc)/dz] if dz< -1e-10 else [])
        t=min(ts);return (t*dx,zc+t*dz)
    for y,isouter in [(yfront,True),(yback,True),(yback,False),(yfront,False)]:
        for a in angles:
            x,z=outer(a) if isouter else (rad*math.cos(a),zc+rad*math.sin(a))
            vs.append((x,y,z))
    n=len(angles);fs=[]
    for k in range(4):
        for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j))
    return mesh(name,vs,fs,material)


def washer():
    p=palette()
    # 600 mm cabinet with separate structural panels, not a solid box behind the aperture.
    for x in [-.245,.245]:
        for y in [-.235,.235]:
            cyl('Washer elastomer contact foot',(x,y,.018),.034,.036,p['rubber'],n=28,bevel=.004)
            cyl('Washer leveling stem',(x,y,.046),.018,.034,p['steel'],n=20)
    box('Washer base tray',(0,0,.078),(.58,.57,.058),p['black'],.010)
    box('Washer underside service plate',(0,0,.050),(.48,.46,.012),p['steel'],.008)
    for x in [-.21,.21]:
        for y in [-.19,.19]:screw('Under-base fastening',(x,y,.041),p['black'])
    for x in [-.292,.292]:
        box('Enamel side wall',(x,0,.445),(.016,.584,.735),p['enamel'],.006)
        # Thin embossed reinforcement ribs are raised real geometry.
        for yy in [-.15,0,.15]:box('Side reinforcement bead',(x*1.027,yy,.43),(.008,.018,.48),p['enamel'],.004)
    box('Washer top cap',(0,0,.830),(.606,.606,.036),p['enamel'],.011)
    box('Upper control fascia',(0,-.292,.768),(.580,.030,.092),p['enamel'],.008)
    box('Rear removable cabinet panel',(0,.292,.449),(.574,.018,.730),p['steel'],.008)
    for x in [-.255,.255]:
        for z in [.14,.39,.69,.78]:screw('Rear cabinet screw',(x,.305,z),p['black'],'Y')
    # A deep, open drum sits behind the ring, with no dark disc filling the aperture.
    rect_aperture('Front cabinet with true circular aperture',.288,.114,.716,.426,.213,-.305,-.281,p['enamel'])
    lathe('Deep open stainless drum',[(0,-.205),(.182,-.205),(.197,-.185),(.197,.245),(.193,.262),(.184,.262),(.181,.246),(.181,-.173),(0,-.173)],(0,0,.426),p['bright'],n=80,axis='Y')
    # Rubber bellows is a thick annular shell, opening continuously into the drum.
    lathe('Recessed pleated rubber door gasket',[(.216,.308),(.219,.294),(.208,.282),(.210,.269),(.196,.254),(.184,.254),(.188,.270),(.196,.280),(.193,.295),(.198,.309)],(0,0,.426),p['rubber'],n=80,axis='Y')
    ring('Gasket rolled front sealing lip',(0,-.309,.426),.205,.008,p['rubber'],'Y',80)
    # Interior drum lifters, rear stamped rings and center boss are visible through the mouth.
    for a in [math.radians(30),math.radians(150),math.radians(270)]:
        x,z=.171*math.cos(a),.426+.171*math.sin(a)
        o=box('Raised interior drum lifter',(x,.012,z),(.025,.315,.020),p['bright'],.007)
        o.rotation_euler[1]=math.pi/2-a
    for r in [.065,.117,.157]:ring('Rear drum pressed concentric ridge',(0,.170,.426),r,.0035,p['bright'],'Y',64)
    cyl('Drum back central hub',(0,.166,.426),.035,.016,p['steel'],'Y',n=32,bevel=.003)
    # Front drawer, selector and inactive controls.
    box('Detergent drawer front',(-.173,-.313,.769),(.189,.024,.069),p['enamel'],.006)
    box('Detergent drawer recessed pull',(-.173,-.326,.756),(.124,.008,.013),p['black'],.003)
    cyl('Program selector bezel',(.002,-.315,.772),.032,.008,p['steel'],'Y',n=40)
    cyl('Program selector knob',(.002,-.329,.772),.026,.025,p['enamel'],'Y',n=36,bevel=.003)
    box('Selector index',(.002,-.343,.789),(.004,.003,.010),p['black'],.0005)
    box('Inactive wash display',(.143,-.311,.786),(.119,.008,.034),p['screen'],.003)
    for x in [.092,.132,.172,.212]:cyl('Small front function button',(x,-.319,.749),.008,.009,p['black'],'Y',n=20)
    box('Lower pump access fascia',(0,-.295,.106),(.57,.034,.045),p['enamel'],.005)
    cyl('Drain service access cover',(.211,-.316,.151),.032,.012,p['enamel'],'Y',n=32,bevel=.003)
    # Rear hose collars and deliberately parked, capped tails stay within this complete prop.
    for x,m in [(-.10,p['blue']),(.03,p['red'])]:
        cyl('Rear inlet socket',(x,.320,.737),.023,.039,p['steel'],'Y',n=24)
        ring('Colored inlet collar',(x,.343,.737),.018,.004,m,'Y',32)
        cyl('Inactive inlet cap',(x,.345,.737),.014,.007,p['black'],'Y',n=24)
    cyl('Drain hose cabinet gland',(.19,.315,.20),.027,.030,p['rubber'],'Y',n=28)
    hose=[(.19,.337,.20),(.22,.366,.28),(.22,.37,.57),(.18,.37,.65),(.12,.37,.66),(.09,.37,.62)]
    path('Parked fixed drain hose',hose,.015,p['rubber'])
    for z in [.32,.47,.60]:ring('Drain hose rib',(.22,.37,z),.015,.0025,p['black'],'Z',24,6)
    box('Rear hose retaining clip',(.22,.345,.56),(.060,.045,.027),p['steel'],.004)
    path('Fixed electrical cable',[(-.22,.308,.62),(-.22,.34,.48),(-.18,.35,.41),(-.11,.35,.42),(-.09,.35,.51),(-.14,.35,.57)],.006,p['rubber'],resolution=1)
    box('Parked electrical connector',(-.14,.350,.581),(.027,.020,.043),p['black'],.004)
    # Door is a separate closed assembly in a fixed open pose about the left hinge.
    before=set(bpy.context.scene.objects)
    ring('Open door thick outer molding',(0,-.345,.426),.221,.021,p['enamel'],'Y',80,10)
    ring('Open door inner trim',(0,-.350,.426),.193,.012,p['black'],'Y',80,8)
    lathe('Opaque dished door window insert',[(0,.363),(.095,.361),(.166,.347),(.179,.333),(.179,.325),(.165,.338),(.094,.352),(0,.354)],(0,0,.426),p['window'],n=64,axis='Y')
    path('Door pull handle',[(.184,-.364,.367),(.217,-.386,.386),(.225,-.391,.433),(.214,-.384,.474),(.188,-.364,.486)],.013,p['black'])
    for z in [.352,.500]:box('Door hinge leaf',(-.219,-.336,z),(.041,.027,.035),p['steel'],.003)
    angle=math.radians(-67);pivot=Vector((-.227,-.327,.426));R=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,'Z')@Matrix.Translation(-pivot)
    for o in set(bpy.context.scene.objects)-before:o.matrix_world=R@o.matrix_world
    for z in [.352,.500]:
        box('Cabinet door hinge bracket',(-.237,-.316,z),(.062,.024,.048),p['steel'],.004)
        cyl('Door hinge knuckle',(-.227,-.327,z),.012,.057,p['steel'],n=24)
    box('Door latch receiver',(.246,-.316,.426),(.023,.018,.047),p['black'],.004)
    return ('city-front-loading-washing-machine','前開きドラム式洗濯機','Front-loading washing machine','共同ランドリーや施設の洗濯室向けの洗濯機外観。前板の実開口、奥行きのある空のドラム、内側リフター、ゴム蛇腹、固定した開扉・不透明な窓表現、洗剤引出し、無表示操作部、背面接続口と収納状態のホース、底板と調整足を造形。洗浄・回転・通水・電装・扉動作は実装していません。性能、電気・水回りの安全性や製品適合性は未検証。','A washing-machine appearance prop for shared laundries and facility washrooms. It has a genuine front-panel aperture, deep empty drum and interior lifters, rubber bellows, fixed swung-open door with an opaque window representation, detergent drawer, inactive controls, rear connection collars and parked hoses, underside plate and leveling feet. Washing, rotation, plumbing, electrical operation and door motion are not implemented. Performance, electrical/plumbing safety and product compliance are unvalidated.',['laundry','washing-machine','appliance','洗濯機'])


def board_outline(scale=1):
    # Broad heel, gently tapering sides and a rounded narrow nose.
    pts=[(.45,-.188),(.50,-.16),(.51,-.12),(.51,.12),(.50,.16),(.45,.188),(-.28,.188),(-.44,.158),(-.56,.105),(-.625,.050),(-.642,0),(-.625,-.050),(-.56,-.105),(-.44,-.158),(-.28,-.188)]
    return [(x*scale,y*scale) for x,y in pts]


def ironing_board():
    p=palette()
    extrusion_xy('Ironing board perforation-free support deck',board_outline(.99),.847,.867,p['steel'],.008)
    extrusion_xy('Shaped padded ironing surface',board_outline(),.865,.892,p['pad'],.012)
    path('Continuous cover edge piping',[(x,y,.880) for x,y in board_outline()],.004,p['seam'],closed=True)
    # Paired crossed frames are physically separated at the pivot and joined with an axle.
    for side in [-1,1]:
        y=side*.105
        rod('First crossed leg',(-.40,y,.058),(.30,y,.843),.017,p['steel'],24)
        y=side*.151
        rod('Second crossed leg',(.40,y,.058),(-.30,y,.843),.017,p['steel'],24)
    for x in [-.40,.40]:
        rod('Wide floor stabilizer',(x,-.27,.045),(x,.27,.045),.021,p['steel'],24)
        for y in [-.27,.27]:
            cyl('Rubber stabilizer end cap',(x,y,.045),.028,.050,p['rubber'],'Y',n=28,bevel=.005)
    for x in [-.30,.30]:
        rod('Top folding cross axle',(x,-.171,.836),(x,.171,.836),.014,p['steel'],24)
        for y in [-.17,.17]:box('Under-board axle bracket',(x,y,.838),(.070,.033,.033),p['steel'],.003)
    rod('Crossed-leg central axle',(0,-.178,.5066),(0,.178,.5066),.012,p['steel'],24)
    for y in [-.18,.18]:
        cyl('Crossing pivot washer',(0,y,.5066),.026,.008,p['steel'],'Y',n=24)
        screw('Crossing pivot cap',(0,y*1.04,.5066),p['black'],'Y',.011)
    # Under-deck rack and fixed locking brace support the deployed pose.
    for y in [-.057,.057]:bar('Under-board locking track',(-.12,y,.823),(.32,y,.823),.020,.027,p['steel'])
    for x in [-.09,-.03,.03,.09,.15,.21,.27]:bar('Height rack rung',(x,-.07,.808),(x,.07,.808),.012,.014,p['steel'],.002)
    bar('Engaged diagonal lock brace',(-.185,0,.7141),(.15,0,.810),.023,.018,p['steel'],.003)
    rod('Lock-brace lower cross pin',(-.185,-.165,.7141),(-.185,.165,.7141),.008,p['steel'],20)
    box('Height locking pawl',(.15,0,.810),(.060,.050,.022),p['black'],.003)
    path('Fold release handle',[(.15,.04,.812),(.18,.08,.790),(.25,.08,.790)],.008,p['black'],resolution=1)
    # Real slatted iron cradle attaches to the board heel; it is not an independent counted prop.
    for y in [-.145,.145]:rod('Iron-rest cantilever',(.40,y,.850),(.78,y,.850),.010,p['steel'],20)
    rest=[(.52,-.16,.867),(.78,-.16,.867),(.80,-.14,.867),(.80,.14,.867),(.78,.16,.867),(.52,.16,.867)]
    path('Iron-rest perimeter',rest,.011,p['steel'],closed=True)
    for x in [.56,.61,.66,.71,.76]:rod('Iron-rest open crossbar',(x,-.155,.867),(x,.155,.867),.006,p['steel'],16)
    # Parked iron has a shaped sole, body, open hand grip, control dial and attached short cord.
    iron_before=set(bpy.context.scene.objects)
    ip=[(.535,-.080),(.720,-.073),(.770,-.035),(.790,0),(.770,.035),(.720,.073),(.535,.080),(.518,.057),(.518,-.057)]
    extrusion_xy('Parked iron soleplate',ip,.878,.888,p['bright'],.004)
    inner=[(.535+(x-.535)*.94,y*.91) for x,y in ip]
    extrusion_xy('Parked iron lower body',inner,.889,.949,p['enamel'],.012)
    extrusion_xz('Iron upper heel and nose',[(.531,.930),(.745,.930),(.716,.972),(.560,.988),(.530,.967)],-.060,.060,p['blue'],.010)
    path('Iron open loop handle',[(.552,-.002,.953),(.552,-.002,1.032),(.574,-.002,1.050),(.676,-.002,1.041),(.700,-.002,.974)],.018,p['black'],resolution=2)
    cyl('Iron temperature dial',(.616,-.041,.985),.021,.008,p['black'],n=28,bevel=.002)
    box('Unlit iron indicator',(.718,0,.977),(.023,.014,.006),p['red'],.002)
    path('Short parked iron cord',[(.534,.032,.970),(.495,.057,.975),(.477,.106,.940),(.509,.143,.924),(.555,.125,.925)],.005,p['rubber'],resolution=1)
    box('Iron cord resting plug',(.566,.123,.925),(.030,.022,.014),p['black'],.003)
    for o in set(bpy.context.scene.objects)-iron_before:o.location.z-=.005
    return ('city-folding-ironing-board','アイロン付き折畳み式アイロン台','Folding ironing board with parked iron','ランドリー、衣装室や補修室の内装向けの、展開状態のアイロン台一式。先細りのパッド面、縁取り、交差した管脚と回転軸、接地ゴム、裏面の高さラック・固定したロック支え、開いた格子のアイロン受けと置いたアイロンを造形。台とアイロンは一つの完成備品として数えます。折畳み、加熱、蒸気・温度制御はありません。耐荷重・耐熱性や機器安全性は未検証。','A deployed ironing-board assembly for laundry, costume and repair-room interiors. It includes a shaped padded surface and binding, crossed tubular legs and pivot, rubber contacts, underside height rack and engaged fixed brace, open-bar iron cradle and parked iron. The board and iron count as one complete prop. Folding, heating, steam and temperature control are absent. Load capacity, heat resistance and equipment safety are unvalidated.',['laundry','ironing-board','iron','アイロン台'])


def canvas_bag(p):
    # Closed shell enclosing a genuinely open top and empty interior. Small authored folds
    # are geometry, not image texture; inner and outer surfaces meet around the top rim.
    profiles=[(.555,.385,.050,.228),(.58,.407,.060,.27),(.647,.450,.073,.55),(.676,.479,.081,.805),(.680,.483,.082,.850),(.658,.461,.074,.850),(.654,.457,.073,.805),(.625,.428,.064,.55),(.558,.385,.052,.258),(.536,.365,.045,.246)]
    vs=[];n=0
    for k,(w,d,r,z) in enumerate(profiles):
        pts=rounded_rect(w,d,r,n=9);n=len(pts)
        for j,(x,y) in enumerate(pts):
            strength=(.004 if k in [0,4,5,9] else .010)
            off=strength*math.sin(j*math.tau/n*7+.5)
            xx=x+off*(1 if x>0 else -1);yy=y+off*.6*(1 if y>0 else -1)
            vs.append((xx,yy,z))
    fs=[]
    for k in range(len(profiles)-1):
        for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    fs += [tuple(reversed(range(n))),tuple(range((len(profiles)-1)*n,len(profiles)*n))]
    o=mesh('Open empty fabric collection bag',vs,fs,p['cloth'])
    for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
    # Sewn corner binding follows the outward fabric contour.
    for sx in [-1,1]:
        for sy in [-1,1]:path('Vertical sewn fabric corner',[(sx*.246,sy*.166,.245),(sx*.267,sy*.181,.28),(sx*.298,sy*.201,.55),(sx*.312,sy*.216,.805),(sx*.314,sy*.217,.85)],.003,p['seam'],resolution=1)
    path('Bag top folded binding',[(x,y,.851) for x,y in rounded_rect(.680,.483,.082,n=9)],.005,p['seam'],closed=True)


def hamper_trolley():
    p=palette()
    for x in [-.30,.30]:
        for y in [-.208,.208]:
            # Each caster has an axle, two fork cheeks, swivel collar and frame mounting plate.
            wheel_y=y-.015
            cyl('Hamper caster tire',(x,wheel_y,.055),.055,.034,p['rubber'],'X',n=32,bevel=.004)
            for s in [-1,1]:
                cyl('Caster recessed wheel hub',(x+s*.019,wheel_y,.055),.027,.005,p['steel'],'X',n=24)
                box('Caster fork cheek',(x+s*.026,y-.004,.091),(.012,.054,.078),p['steel'],.006)
            rod('Caster axle',(x-.035,wheel_y,.055),(x+.035,wheel_y,.055),.008,p['steel'],16)
            cyl('Caster swivel race',(x,y,.137),.034,.018,p['steel'],n=32,bevel=.003)
            box('Caster frame mounting plate',(x,y,.154),(.077,.077,.016),p['steel'],.004)
            if y<0:box('Fixed caster brake tab',(x,y+.024,.117),(.040,.065,.012),p['black'],.004,rot=(math.radians(-18),0,0))
    path('Lower trolley perimeter frame',[(x,y,.186) for x,y in rounded_rect(.665,.47,.055)],.015,p['steel'],closed=True)
    for x in [-.22,0,.22]:rod('Bag bottom supporting crossbar',(x,-.227,.214),(x,.227,.214),.016,p['steel'],20)
    for x in [-.330,.330]:
        for y in [-.235,.235]:rod('Trolley corner frame upright',(x,y,.175),(x*1.09,y*1.12,.870),.013,p['steel'],24)
    path('Top tubular rim',[(x,y,.870) for x,y in rounded_rect(.75,.555,.085)],.014,p['steel'],closed=True)
    canvas_bag(p)
    # Four paired textile straps visibly hang the fabric rim from the steel rail.
    for x in [-.24,.24]:
        for sy in [-1,1]:
            y=sy*.258
            path('Closed fabric suspension loop',[(x,y-sy*.019,.825),(x,y-sy*.019,.885),(x,y+sy*.021,.887),(x,y+sy*.023,.842),(x,y-sy*.008,.825)],.008,p['seam'],closed=True,resolution=1)
    for sy in [-1,1]:
        y=sy*.275
        path('Raised end push handle',[(-.24,y,.871),(-.24,y,.965),(-.22,y,1.000),(.22,y,1.000),(.24,y,.965),(.24,y,.871)],.014,p['steel'])
        rod('Handle sleeve',(-.17,y,1.000),(.17,y,1.000),.019,p['rubber'],28)
    return ('city-linen-hamper-trolley','布袋式リネン回収ワゴン','Fabric-bin linen hamper trolley','ランドリーや公共施設のバックヤード向けのリネン回収ワゴン。空の上部開口を持つ厚み付き布袋、緩やかな折り目と縁・縫目、吊りループ、上枠・四支柱・底支持棒、両端の押し手、旋回金具と車輪・固定ブレーキ外形を造形。荷物棚型カートや図書ワゴンではありません。布の変形、旋回・転動や制動動作はなく、衛生性能・耐荷重・安全性は未検証。','A linen-collection trolley for laundry and public-facility back rooms, with a thick fabric bin and genuinely open empty top, gentle modeled folds and bound seams, hanging loops, upper rim, four uprights, bottom support bars, end push handles, swivel hardware, wheels and static brake outlines. It is not a luggage rack or library trolley. Cloth simulation, swiveling, rolling and braking behavior are absent; hygiene performance, load capacity and safety are unvalidated.',['laundry','linen','hamper','trolley','リネン回収'])


def sewing_machine():
    p=palette()
    # The worktable, machine and wired pedal are one supported complete sewing station.
    for x in [-.425,.425]:
        for y in [-.235,.235]:
            box('Table rubber contact pad',(x,y,.018),(.074,.082,.036),p['rubber'],.009)
        bar('Table full-depth foot',(x,-.255,.055),(x,.255,.055),.045,.048,p['steel'],.005)
        for y in [-.175,.175]:bar('Table upright',(x,y,.055),(x,y,.718),.038,.038,p['blue'],.005)
        bar('Table leg upper beam',(x,-.255,.714),(x,.255,.714),.040,.044,p['blue'],.005)
    bar('Rear table tie beam',(-.425,.175,.234),(.425,.175,.234),.035,.035,p['steel'],.004)
    bar('Rear table diagonal brace',(-.425,.175,.235),(.425,.175,.673),.021,.026,p['steel'],.003)
    box('Sewing table top',(0,0,.750),(1.06,.60,.052),p['timber'],.013)
    for x in [-.425,.425]:
        for y in [-.175,.175]:
            box('Under-top fastening bracket',(x,y,.712),(.085,.085,.015),p['steel'],.003)
            screw('Table underside screw',(x+.026,y,.700),p['black'],r=.005)
    # One cast C-form creates a genuine open throat above the machine bed.
    outline=[(-.290,.794),(.285,.794),(.285,1.081),(.246,1.133),(-.229,1.133),(-.274,1.095),(-.274,.969),(-.166,.969),(-.166,1.030),(.116,1.030),(.128,.848),(-.290,.848)]
    extrusion_xz('Sewing machine cast C body',outline,-.098,.098,p['enamel'],.012)
    box('Machine lower bed seam',(0,-.002,.793),(.580,.215,.015),p['black'],.006)
    for x in [-.228,.228]:
        for y in [-.075,.075]:cyl('Machine tabletop rubber foot',(x,y,.783),.021,.014,p['rubber'],n=20,bevel=.002)
    # Split steel needle plate with a real narrow slot and two raised feed-dog rows.
    xp,yp=-.221,-.022
    for x,w in [(xp-.037,.060),(xp+.037,.060)]:box('Needle plate side', (x,yp,.853),(w,.090,.006),p['bright'],.001)
    for y in [yp-.041,yp+.041]:box('Needle plate slot end',(xp,y,.853),(.016,.008,.006),p['bright'],.001)
    for x in [xp-.047,xp+.047]:screw('Needle plate screw',(x,yp+.028,.858),p['black'],r=.003)
    for xx in [xp-.017,xp+.017]:
        for i in range(5):box('Feed dog tooth',(xx,yp-.022+i*.011,.858),(.007,.006,.005),p['steel'],.0005)
    # Needle and presser foot are small but real meshes, with clear foot clearance.
    cyl('Needle bar',(xp,yp,.933),.006,.092,p['bright'],n=20,bevel=.0005)
    box('Needle clamp',(xp,yp,.892),(.019,.018,.018),p['steel'],.002)
    screw('Needle clamp screw',(xp+.012,yp,.892),p['black'],'X',r=.0035)
    rod('Fixed sewing needle',(xp,yp,.891),(xp,yp,.855),.0012,p['bright'],n=12,bevel=0)
    cyl('Presser bar',(xp+.031,yp+.025,.923),.005,.090,p['bright'],n=20,bevel=.0004)
    bar('Presser foot curved ankle',(xp+.031,yp+.025,.879),(xp,yp+.023,.864),.010,.009,p['steel'],.001)
    for x in [xp-.010,xp+.010]:box('Open presser foot toe',(x,yp-.003,.863),(.008,.043,.007),p['bright'],.002)
    box('Presser foot rear bridge',(xp,yp+.020,.864),(.028,.008,.009),p['bright'],.001)
    # Removable head cover, visible tension stack, take-up loop and stitch controls.
    box('Needle head front cover',(-.223,-.105,1.050),(.091,.015,.130),p['blue'],.012)
    for z in [.997,1.100]:screw('Head cover screw',(-.223,-.115,z),p['steel'],'Y',.004)
    for yy in [-.120,-.128]:cyl('Thread tension disc',(-.163,yy,1.025),.019,.005,p['steel'],'Y',n=28,bevel=.0005)
    cyl('Thread tension adjuster',(-.163,-.139,1.025),.013,.018,p['black'],'Y',n=28,bevel=.002)
    ring('Take-up thread eye',(-.203,-.118,1.091),.008,.002,p['bright'],'Y',n=24,m=6)
    ring('Needle thread guide',(-.222,-.034,.912),.005,.0014,p['bright'],'Y',n=20,m=6)
    cyl('Stitch selection bezel',(.201,-.111,1.012),.030,.012,p['steel'],'Y',n=36)
    cyl('Stitch selection knob',(.201,-.126,1.012),.024,.021,p['black'],'Y',n=32,bevel=.003)
    box('Stitch knob index',(.201,-.139,1.025),(.003,.002,.010),p['enamel'],.0005)
    box('Reverse lever mounting block',(.209,-.112,.920),(.045,.025,.031),p['blue'],.005)
    bar('Reverse stitch lever',(.209,-.13,.925),(.209,-.152,.895),.015,.012,p['black'],.002)
    # Exposed balance wheel with concentric rim, recessed hub and three structural spokes.
    cyl('Handwheel axle',(.305,0,1.056),.019,.066,p['steel'],'X',n=28,bevel=.002)
    ring('Handwheel outer rim',(.332,0,1.056),.079,.013,p['black'],'X',n=64,m=10)
    ring('Handwheel bright inner trim',(.349,0,1.056),.064,.0035,p['steel'],'X',n=48,m=6)
    cyl('Handwheel recessed hub',(.333,0,1.056),.027,.027,p['steel'],'X',n=32,bevel=.003)
    for a in [0,math.tau/3,math.tau*2/3]:
        rod('Handwheel supporting spoke',(.332,.024*math.cos(a),1.056+.024*math.sin(a)),(.332,.073*math.cos(a),1.056+.073*math.sin(a)),.008,p['black'],n=16)
    # On-machine spool, pin, winding collars and an explicit fixed thread route.
    cyl('Main spool pin',(.104,0,1.173),.004,.090,p['steel'],n=16,bevel=.0004)
    cyl('Spool lower flange',(.104,0,1.153),.029,.005,p['enamel'],n=32)
    cyl('Thread spool',(.104,0,1.179),.024,.047,p['thread'],n=40,bevel=.002)
    cyl('Spool top flange',(.104,0,1.205),.029,.005,p['enamel'],n=32)
    for z in [1.159,1.166,1.173,1.180,1.187,1.194,1.201]:ring('Spool wound-thread ridge',(.104,0,z),.024,.0008,p['thread'],n=40,m=6)
    rod('Upper thread-guide stand',(-.028,.010,1.129),(-.028,.010,1.171),.003,p['steel'],16)
    ring('Upper thread-guide eye',(-.028,.010,1.178),.007,.0017,p['bright'],'Y',n=20,m=6)
    thread_route=[(.091,-.016,1.197),(-.028,.010,1.178),(-.163,-.118,1.044),(-.179,-.135,1.023),(-.203,-.118,1.091),(-.222,-.034,.912),(xp,yp,.861)]
    for a,b in zip(thread_route,thread_route[1:]):rod('Fixed thread segment',a,b,.00075,p['thread'],n=10,bevel=0)
    for point in thread_route[1:-1]:sphere('Thread route joint',point,(.00075,.00075,.00075),p['thread'],segments=12,rings=6)
    cyl('Bobbin-winder pedestal',(.224,.025,1.146),.014,.021,p['steel'],n=24)
    cyl('Empty bobbin winder spindle',(.224,.025,1.169),.004,.031,p['steel'],n=16)
    # Rear motor cover and access detail, plus a supported cable to the floor pedal.
    box('Rear electric drive cover',(.195,.117,.979),(.146,.090,.130),p['blue'],.023)
    for x in [.155,.180,.205,.230]:box('Raised motor ventilation rib',(x,.165,.975),(.008,.008,.062),p['black'],.002)
    box('Rear machine access cover',(-.035,.106,1.083),(.235,.014,.063),p['enamel'],.006)
    for x in [-.12,.05]:screw('Rear access screw',(x,.117,1.083),p['steel'],'Y',.004)
    box('Pedal nonslip bottom',(.195,-.176,.014),(.145,.200,.028),p['rubber'],.010)
    extrusion_xz('Sloped static sewing foot pedal',[(.122,.028),(.268,.028),(.268,.065),(.122,.045)],-.276,-.076,p['black'],.008)
    for y in [-.245,-.210,-.175,-.140,-.105]:box('Pedal raised tread',(.195,y,.058),(.110,.009,.006),p['rubber'],.001,rot=(0,math.radians(-8),0))
    path('Pedal electrical cord',[(.195,-.076,.041),(.245,.025,.035),(.33,.24,.040),(.34,.31,.14),(.34,.31,.65),(.30,.31,.81),(.245,.19,.889),(.245,.16,.935)],.0045,p['rubber'],resolution=1)
    box('Rear pedal cable socket',(.245,.167,.932),(.026,.021,.026),p['black'],.004)
    box('Cable under-table retaining clip',(.322,.299,.718),(.031,.030,.027),p['steel'],.003)
    return ('city-bench-sewing-machine','作業台付き卓上ミシン','Benchtop sewing machine with worktable','衣装修繕室、地域の工作室やランドリー補修スペース向けの卓上ミシン一式。空いた懐を持つC形本体、針棒と針、二股押さえ、針板の実スロット・送り歯、張力部品・糸案内・固定した糸経路、糸巻き、スポーク付きはずみ車、背面カバー、脚付き作業台と配線された床ペダルを造形。台とペダルを含む一つの完成備品です。縫製・送り・回転・電気動作や布シミュレーションはなく、機器安全性・精度・性能は未検証。','A complete benchtop sewing station for costume-repair rooms, community workshops and laundry repair areas. It includes a C-shaped body with an open throat, needle bar and needle, forked presser foot, needle-plate slot and feed teeth, tension components, thread guides and a fixed thread path, spool, spoked handwheel, rear covers, legged worktable and wired floor pedal. The table and pedal belong to one complete prop. Stitching, fabric feed, rotation, electrical operation and cloth simulation are absent; equipment safety, accuracy and performance are unvalidated.',['textile','sewing','machine','worktable','ミシン'])


BUILDERS=[washer,ironing_board,hamper_trolley,sewing_machine]
if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-029/assets');ap.add_argument('--only',default='');ap.add_argument('--geometry-only',action='store_true');args=ap.parse_args(argv)
    out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    if args.geometry_only:common.render=lambda *a,**k:None
    for builder in BUILDERS:
        reset();spec=builder()
        if args.only and spec[0]!=args.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/textile_care_equipment.py',azimuth=-58,elevation=(27 if spec[0]=='city-linen-hamper-trolley' else 24))
