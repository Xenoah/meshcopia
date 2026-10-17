"""Four original static event presentation props. Xenoah, CC BY 4.0.
No third-party geometry, textures, fonts, brands or logos.
Production: CITY_RENDER_SAMPLES=48 blender -b -noaudio --factory-startup --threads 4 \
 --python scripts/city_expansion/event_presentation.py -- --out batches/batch-019/assets
Portable reproduction may add --geometry-only, which skips raster rendering only.
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(black=mat('Graphite satin equipment enamel',(.036,.045,.055),.34,.40),
        dark=mat('Charcoal matte recessed interiors',(.009,.014,.019),.06,.78),
        steel=mat('Brushed stainless hardware',(.43,.49,.53),.76,.31),
        aluminum=mat('Satin anodized aluminum',(.57,.62,.64),.70,.32),
        ivory=mat('Warm ivory equipment polymer',(.78,.78,.71),.05,.45),
        screen=mat('Blank opaque off-white projection surface',(.88,.89,.86),0,.87),
        rubber=mat('Dark rubber pads grips and screen border',(.017,.021,.025),0,.80),
        timber=mat('Warm walnut-color solid lectern finish',(.28,.115,.048),.02,.48),
        lens=mat('Opaque dark blue optical placeholder, no transparency or emission',(.025,.075,.10),.25,.22),
        blue=mat('Muted blue equipment control',(.075,.21,.30),.18,.49),
        red=mat('Opaque red control cap, unlit',(.55,.035,.023),.02,.5))


def cyl(n,p,r,d,m,axis='Z',verts=32,bev=.0015):
    o=cylinder(n,p,r,d,m,vertices=verts,bevel=bev)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def rod(n,a,b,r,m,verts=20,bev=.001):
    a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def beam(n,a,b,w,d,m,bev=.003):
    a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def fixing(n,p,m,axis='Z',r=.008):
    cyl(n+' washer',p,r*1.5,.003,m,axis,20,.0005)
    q=list(p);q['XYZ'.index(axis)]+=.0045
    cyl(n+' hex head',q,r,.009,m,axis,6,.0005)


def ring(n,p,outer,inner,depth,m,axis='Z',sides=48):
    """Closed annular mesh: actual central aperture and no coincident seam vertices."""
    v=[];f=[]
    for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
        for i in range(sides):
            a=math.tau*i/sides;v.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(sides):
        j=(i+1)%sides
        f.extend([(i,j,sides+j,sides+i),(2*sides+i,3*sides+i,3*sides+j,2*sides+j),
                  (i,2*sides+i,2*sides+j,j),(sides+i,sides+j,3*sides+j,3*sides+i)])
    o=mesh(n,v,f,m);o.location=p
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    for i,face in enumerate(o.data.polygons):face.use_smooth=i%4<2
    return o


def annular_arc(n,p,r0,r1,depth,a0,a1,m,axis='X',steps=40):
    """Closed curved section of a thick shell; omitted arc is a true open slot."""
    v=[];f=[];k=steps+1
    for z,r in [(-depth/2,r0),(-depth/2,r1),(depth/2,r1),(depth/2,r0)]:
        for i in range(k):
            a=math.radians(a0+(a1-a0)*i/steps);v.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(4):
        for i in range(steps):f.append((j*k+i,j*k+i+1,((j+1)%4)*k+i+1,((j+1)%4)*k+i))
    f.extend([(0,k,2*k,3*k),(k-1,4*k-1,3*k-1,2*k-1)])
    o=mesh(n,v,f,m);o.location=p
    if axis=='X':o.rotation_euler=(math.pi/2,0,math.pi/2)
    elif axis=='Y':o.rotation_euler=(math.pi/2,0,0)
    for i,face in enumerate(o.data.polygons):face.use_smooth=(steps<=i<2*steps or 3*steps<=i<4*steps)
    return o


def sweep(n,points,r,m,sides=12,frame='X'):
    pts=[Vector(p) for p in points];v=[];f=[]
    for i,p in enumerate(pts):
        t=((pts[1]-p) if i==0 else ((p-pts[i-1]) if i==len(pts)-1 else (pts[i+1]-pts[i-1]))).normalized()
        ref=Vector((1,0,0) if frame=='X' else (0,0,1));u=(ref-t*ref.dot(t)).normalized();w=t.cross(u).normalized()
        for j in range(sides):
            a=math.tau*j/sides;v.append(tuple(p+r*(u*math.cos(a)+w*math.sin(a))))
    for i in range(len(pts)-1):
        for j in range(sides):
            nj=(j+1)%sides;f.append((i*sides+j,(i+1)*sides+j,(i+1)*sides+nj,i*sides+nj))
    f.extend([tuple(range(sides-1,-1,-1)),tuple((len(pts)-1)*sides+j for j in range(sides))])
    o=mesh(n,v,f,m)
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def cut_hole(obj,n,p,r,depth,axis='Z',verts=48):
    cutter=cyl(n,p,r,depth,None,axis,verts,0)
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Actual through aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    return obj


def profile_x(n,points,x0,x1,m,bev=.005):
    v=[(x,y,z) for x in (x0,x1) for y,z in points];k=len(points)
    f=[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]
    f.extend((i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k))
    return mesh(n,v,f,m,bev)


def lectern():
    p=palette()
    # A reading desk, not a counter: sloping surface, manuscript lip and open rear shelf.
    box('Weighted lectern plinth',(0,0,.044),(.62,.50,.064),p['black'],.025)
    for x in [-.24,.24]:
        for y in [-.17,.17]:cyl('Non-slip underside pad',(x,y,.014),.041,.028,p['rubber'],verts=28,bev=.004)
    box('Pedestal foot saddle',(0,-.035,.090),(.34,.27,.05),p['steel'],.010)
    profile_x('Tapered central pedestal',[(-.15,.105),(.07,.105),(.11,.91),(-.18,1.045)],-.13,.13,p['black'],.012)
    # Distinct shaped audience-facing timber shield; there is no bar storage or countertop.
    v=[(-.245,-.186,.36),(.245,-.186,.36),(.285,-.214,1.065),(-.285,-.214,1.065),
       (-.245,-.164,.36),(.245,-.164,.36),(.285,-.192,1.065),(-.285,-.192,1.065)]
    mesh('Tapered warm timber audience shield',v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],p['timber'],.008)
    for x in [-.23,.23]:
        rod('Shield lower stand-off',(x,-.17,.39),(x*.50,-.11,.39),.010,p['steel'])
        beam('Hidden-top shield bracket',(x,-.19,.95),(x*.46,-.06,.92),.026,.025,p['steel'])
        fixing('Front shield screw',(x,-.194,.405),p['black'],'Y',.005)
    box('Rear accessible shelf',(0,.135,.59),(.43,.30,.028),p['timber'],.008)
    for x in [-.18,.18]:
        beam('Shelf underside brace',(x*.60,.01,.44),(x,.25,.573),.026,.026,p['steel'])
        box('Shelf side retaining lip',(x*1.16,.135,.611),(.012,.30,.034),p['black'],.003)
    # Deck is built flat with a genuine cable pass, then inclined as an assembly.
    before=set(bpy.data.objects)
    deck=box('Angled reading deck',(0,0,0),(.66,.48,.034),p['timber'],.010)
    cut_hole(deck,'Cable pass cutter',(-.249,-.122,0),.023,.15)
    ring('Cable pass grommet',(-.249,-.122,.019),.028,.022,.012,p['rubber'],sides=40)
    box('Opaque non-slip reading inset',(.025,.009,.019),(.48,.345,.006),p['black'],.008)
    box('Manuscript retaining lip',(0,.224,.039),(.61,.025,.050),p['black'],.007)
    box('Lip lower metal edge',(0,.239,.024),(.61,.009,.019),p['steel'],.003)
    for x in [-.235,.235]:box('Reading-deck underside stiffener',(x,0,-.028),(.028,.40,.027),p['steel'],.003)
    # Surface falls towards the speaker at +Y.
    R=Matrix.Rotation(math.radians(-14),4,'X');T=Matrix.Translation((0,.005,1.075))
    for o in set(bpy.data.objects)-before:o.matrix_world=T@R@o.matrix_world
    for x in [-.12,.12]:
        beam('Desk saddle riser',(x,-.03,.89),(x,-.05,1.088),.036,.08,p['steel'])
        fixing('Desk saddle fastener',(x,.074,.99),p['steel'],'Y',.008)
    # Low-profile microphone socket and fixed bent neck, connected to the deck.
    cyl('Microphone deck socket',(.243,-.117,1.132),.030,.028,p['black'],verts=40,bev=.004)
    pts=[(.243,-.117,1.142),(.243,-.117,1.22),(.243,-.107,1.285),(.243,-.073,1.34),(.243,-.015,1.381),(.243,.056,1.402),(.243,.13,1.397)]
    sweep('Fixed gooseneck microphone stalk',pts,.0075,p['black'])
    for z in [1.176,1.197,1.218,1.239]:ring('Gooseneck collar',(.243,-.117,z),.009,.007,.006,p['steel'],sides=20)
    a=Vector((.243,.13,1.397));b=Vector((.243,.203,1.385))
    rod('Opaque microphone capsule',a,b,.015,p['dark'],28,.003)
    rod('Microphone capsule base',a,a+(b-a)*.23,.017,p['steel'],28,.001)
    # The rear cable exits the pass-through, stops inside the pedestal, and is not a loose accessory.
    sweep('Short fixed microphone cable',[(-.249,-.111,1.124),(-.249,-.09,1.01),(-.205,.03,.94),(-.135,.087,.884)],.0045,p['rubber'],10)
    ring('Pedestal rear cable entry',(-.130,.087,.884),.015,.007,.012,p['steel'],'X',28)
    return ('city-conference-lectern','会議用マイク付き演台','Conference lectern with fixed microphone',
        '傾斜した読み台、原稿止め、滑り止め面、実際に開いた配線孔、背面棚、先細りの前板、台座と固定グースネックマイクを備えた会議・講演用の演台。天板と前板は木目画像を使わない単色の木材調仕上げです。マイク・配線・収納部は静的な外観で、音声処理や可動機構はありません。人、原稿、会場、外部音響機器を含みません。内部配線、電子回路、細かなねじ山は省略。機器安全性、構造、電気・音響性能は未検証。',
        'A purpose-built conference lectern with an inclined reading deck, manuscript lip, non-slip inset, genuine cable-pass aperture, rear shelf, tapered audience shield, weighted-looking plinth and fixed gooseneck microphone. Deck and shield use constant walnut-like color, not a wood image texture. Microphone, wiring and storage are static appearance only, with no audio processing or movable mechanism. No person, manuscript, venue or external audio equipment is included. Internal wiring, circuits and fine screw threads are omitted. Equipment safety, structure and electrical/acoustic performance are unvalidated.',
        ['conference','lectern','presentation','演台'])


def ceiling_projector():
    p=palette()
    # The casing has discrete solid shells and actual open side ventilation slots.
    box('Upper projector shell',(0,0,.145),(.445,.345,.023),p['ivory'],.018)
    box('Lower projector shell',(0,0,.025),(.445,.345,.027),p['ivory'],.018)
    box('Recessed dark inner enclosure',(0,.018,.085),(.365,.274,.075),p['dark'],.015)
    front=box('Projector front fascia',(0,-.169,.085),(.433,.018,.104),p['ivory'],.007)
    cut_hole(front,'Front lens opening',(-.107,-.17,.087),.061,.09,'Y')
    box('Rear connection fascia',(0,.170,.085),(.433,.018,.104),p['ivory'],.007)
    for x in [-.217,.217]:
        for y in [-.142,.142]:box('Side vent end post',(x,y,.085),(.013,.035,.105),p['ivory'],.003)
        for i in range(10):
            y=-.122+i*.027
            # Each blade leaves a real gap through to the dark recessed inner enclosure.
            box('Actual separated side ventilation blade',(x,y,.086),(.014,.011,.088),p['black'],.002,rot=(.0,.0,math.radians(-20 if x<0 else 20)))
    ring('Deep lens barrel',(-.107,-.211,.087),.064,.050,.089,p['black'],'Y',64)
    ring('Raised lens focus ring',(-.107,-.244,.087),.070,.051,.027,p['rubber'],'Y',64)
    ring('Brushed lens trim',(-.107,-.260,.087),.064,.052,.008,p['aluminum'],'Y',64)
    cyl('Opaque non-projecting lens placeholder',(-.107,-.242,.087),.050,.009,p['lens'],'Y',64,.001)
    for i in range(36):
        a=math.tau*i/36
        o=box('Focus ring grip rib',(-.107+.068*math.cos(a),-.246,.087+.068*math.sin(a)),(.004,.021,.004),p['black'],.001)
        o.rotation_euler[1]=-a
    # Front intake grille occupies a separate opening-like frame, not a painted vent texture.
    box('Front grille recessed backing',(.105,-.182,.085),(.145,.006,.066),p['dark'],.003)
    for z in [.061,.079,.097,.115]:box('Front grille raised louver',(.105,-.190,z),(.146,.012,.006),p['black'],.001,rot=(math.radians(18),0,0))
    cyl('Unlit front status indicator',(.194,-.181,.119),.006,.004,p['blue'],'Y',24,.0005)
    # Visible underside controls suit an upside-down ceiling installation.
    box('Underside control recess',(.090,-.012,.009),(.13,.11,.008),p['dark'],.010)
    cyl('Power button',(.059,-.026,.003),.013,.006,p['ivory'],verts=28,bev=.001)
    for x,y in [(.102,-.028),(.128,-.028),(.102,.004),(.128,.004)]:cyl('Blank control button',(x,y,.003),.007,.006,p['steel'],verts=24,bev=.001)
    for x in [-.17,.17]:
        for y in [-.12,.12]:fixing('Lower shell captive screw',(x,y,.010),p['steel'],'Z',.005)
    # Rear ports are shallow geometric sockets with actual frames and opaque interiors.
    for x,w,h,z in [(-.132,.043,.022,.096),(-.063,.038,.018,.096),(.003,.052,.028,.095)]:
        box('Rear port dark inset',(x,.181,z),(w,.007,h),p['dark'],.002)
        for dx in [-w/2,w/2]:box('Rear socket side wall',(x+dx,.186,z),(.003,.014,h+.004),p['steel'],.0005)
        for dz in [-h/2,h/2]:box('Rear socket horizontal rim',(x,.186,z+dz),(w,.014,.003),p['steel'],.0005)
    ring('Round service connector rim',(.072,.187,.094),.015,.010,.014,p['steel'],'Y',32)
    cyl('Opaque service connector back',(.072,.181,.094),.0095,.005,p['dark'],'Y',28,.0005)
    box('Power socket dark recess',(.151,.183,.084),(.039,.009,.035),p['dark'],.005)
    for x in [.141,.159]:box('Generic socket contact block',(x,.19,.084),(.004,.006,.013),p['steel'],.0005)
    # Connected mount arms, tilt joint, telescoping-looking stem and perforated ceiling plate.
    for x in [-.15,.15]:
        for y in [-.103,.103]:
            cyl('Casing mount stand-off',(x,y,.173),.014,.042,p['steel'],verts=24)
            beam('Angled projector mounting arm',(x,y,.185),(x*.20,y*.18,.240),.025,.018,p['black'])
            fixing('Mount arm end screw',(x,y,.196),p['steel'],r=.006)
    cyl('Mount arm central boss',(0,0,.240),.047,.036,p['black'],verts=40)
    cyl('Lower mount stem',(0,0,.314),.023,.13,p['steel'],verts=32)
    cyl('Static tilt joint barrel',(0,0,.382),.033,.105,p['black'],'X',40)
    for x in [-.056,.056]:
        box('Tilt joint cheek',(x,0,.407),(.013,.066,.094),p['black'],.009)
        cyl('Tilt joint tension washer',(x*1.14,0,.382),.027,.012,p['steel'],'X',32)
    cyl('Tilt clamp knob',(.081,0,.382),.032,.024,p['rubber'],'X',12,.003)
    box('Upper joint bridge',(0,0,.450),(.13,.065,.02),p['black'],.005)
    cyl('Ceiling drop stem',(0,0,.532),.026,.158,p['steel'],verts=40)
    ring('Stem clamp collar',(0,0,.490),.033,.026,.029,p['black'],sides=40)
    cyl('Stem clamp screw',(.039,0,.49),.014,.029,p['rubber'],'X',12,.002)
    plate=box('Ceiling attachment plate',(0,0,.623),(.20,.16,.021),p['black'],.008)
    for x in [-.068,.068]:
        for y in [-.050,.050]:cut_hole(plate,'Ceiling fixing hole',(x,y,.623),.008,.08,verts=24)
    cyl('Stem-to-plate socket',(0,0,.603),.043,.033,p['black'],verts=40)
    return ('city-ceiling-projector','天吊りプロジェクター','Ceiling-mounted projector',
        '段付きレンズ枠、独立した通気ルーバー、下面操作ボタン、背面の端子形状、取付アーム、固定傾斜ジョイント、支柱と穴あき天井取付板を備えた天吊りプロジェクター。レンズは不透明な青黒い代替面で、透過・発光・映像投影は行いません。取付部は固定形状で可動しません。天井、壁、スクリーン、外部ケーブルは含みません。内部光学系・電源・回路・冷却機構は省略。取付安全性、構造、電気・光学性能は未検証。天井への位置・高さ調整は別途必要です。',
        'A ceiling-mounted projector with stepped lens rings, separated ventilation louvers, underside controls, rear socket shapes, mounting arms, fixed tilt joint, drop stem and a perforated ceiling plate. Its lens is an opaque blue-black placeholder, with no transmission, emission or image projection. All mount joints are static. No ceiling, wall, screen or external cable is included. Internal optics, power supply, circuits and cooling mechanism are omitted. Mounting safety, structure and electrical/optical performance are unvalidated. Installation height and ceiling alignment must be positioned separately.',
        ['projector','ceiling-mount','conference','プロジェクター'])


def tripod_base(p,center_y,radius,hub_z,pole_top,heavy=False):
    r=.027 if heavy else .020
    cyl('Central vertical pedestal',(0,center_y,(pole_top+.13)/2),r,pole_top-.13,p['steel'],verts=40)
    cyl('Tripod lower sliding collar',(0,center_y,.19),r*1.9,.075,p['black'],verts=32)
    cyl('Tripod leg pivot hub',(0,center_y,hub_z),r*2.6,.10,p['black'],verts=32)
    for k,a in enumerate([90,210,330]):
        a=math.radians(a);d=Vector((math.cos(a),math.sin(a),0))
        a0=Vector((0,center_y,hub_z))+d*.043
        b=Vector((0,center_y,.031))+d*radius
        rod('Splayed tubular tripod leg '+str(k),a0,b,.025 if heavy else .018,p['black'],24,.002)
        mid=a0.lerp(b,.62)
        rod('Folding-looking leg support stay '+str(k),(0,center_y,.19),mid,.009 if heavy else .007,p['steel'],16,.001)
        box('Tripod rubber foot '+str(k),b-Vector((0,0,.012)),(.083 if heavy else .065,.10 if heavy else .080,.038),p['rubber'],.012,rot=(0,0,a-math.pi/2))
        # Hinge faces join the legs to the hub; no operational articulation is claimed.
        perp=Vector((-d.y,d.x,0));q=a0+perp*.023
        rod('Tripod hinge axle '+str(k),q-perp*.043,q+perp*.010,.009,p['steel'],20,.001)
    cyl('Pedestal height collar',(0,center_y,hub_z+.105),r*1.6,.055,p['black'],verts=32)
    cyl('Pedestal height clamp',(r*1.9,center_y,hub_z+.105),r*.65,r*1.4,p['rubber'],'X',12,.002)


def projection_screen():
    p=palette();tripod_base(p,.095,.56,.405,2.33)
    # One opaque screen, with a dark rear and blank neutral display side.
    box('Single extended black-backed screen',(0,0,1.601),(1.86,.012,1.286),p['rubber'],.003)
    box('Blank opaque projection face',(0,-.008,1.601),(1.755,.006,1.183),p['screen'],.001)
    # Rolled housing is a thick shell with a true continuous slot at its top.
    annular_arc('Cassette shell with actual screen slot',(0,0,.919),.038,.047,1.972,103,437,p['aluminum'],'X',60)
    for x in [-.997,.997]:cyl('Cassette end cap',(x,0,.919),.049,.028,p['black'],'X',40,.004)
    cyl('Upper screen suspension bar',(0,0,2.249),.018,1.925,p['black'],'X',40,.001)
    for x in [-.974,.974]:cyl('Upper bar protective cap',(x,0,2.249),.021,.026,p['rubber'],'X',24,.002)
    # Center pole is behind the surface, with a real hooked bridge to the top bar.
    cyl('Upper pole collar',(0,.095,1.29),.029,.070,p['black'],verts=32)
    cyl('Upper pole clamp knob',(.039,.095,1.29),.018,.027,p['rubber'],'X',12,.002)
    box('Top pole hook bridge',(0,.054,2.325),(.051,.13,.027),p['black'],.005)
    box('Top suspension catch',(0,.006,2.286),(.051,.026,.070),p['black'],.005)
    # Actual closed-section diagonal stays support opposite upper corners from the rear pole.
    for x in [-.80,.80]:
        rod('Rear diagonal screen stay',(0,.105,1.19),(x,.012,2.244),.0055,p['steel'],12,.0006)
        ring('Rear stay upper eye',(x,.019,2.240),.013,.006,.012,p['steel'],'Y',24)
    box('Cassette-to-pole saddle',(0,.065,.914),(.10,.12,.090),p['black'],.008)
    cyl('Cassette saddle clamp',(0,.095,.914),.036,.10,p['black'],verts=32)
    cyl('Cassette saddle knob',(.058,.095,.914),.022,.027,p['rubber'],'X',12,.003)
    # The small handle is permanently fixed to the cassette, not a separate accessory.
    for x in [.17,.33]:rod('Cassette handle stand-off',(x,.035,.906),(x,.093,.865),.009,p['black'],20,.002)
    rod('Cassette carrying grip',(.17,.093,.865),(.33,.093,.865),.013,p['rubber'],24,.003)
    return ('city-tripod-projection-screen','三脚式ポータブル投影スクリーン','Tripod portable projection screen',
        '無地の不透明な投影面を一枚だけ展開した可搬式スクリーン。黒縁と黒い背面、上端バー、実際に開いたスリット付き収納筒、中央支柱、背面の斜めステー、三脚と折畳み風の補強リンクを備えます。白面は単色材質で、画像テクスチャ・透過・発光・映像表示はありません。巻取り・伸縮・脚は固定状態です。投影機、会場、床、人は含みません。巻取りばね、内部機構、細かなねじ山は省略。転倒安全性、構造、光学・投影性能は未検証。',
        'A portable screen with exactly one extended blank opaque projection surface, black border and rear, top suspension bar, genuinely slotted cassette housing, center pole, rear diagonal stays, tripod feet and folding-looking brace links. The off-white face is a constant-color material, with no image texture, transparency, emission or displayed picture. Retraction, telescoping and legs are fixed. No projector, venue, floor or person is included. Roll-up spring, internal mechanisms and fine screw threads are omitted. Tip resistance, structural safety and optical/projection performance are unvalidated.',
        ['projection-screen','tripod','conference','投影スクリーン'])


def followspot():
    p=palette();tripod_base(p,0,.54,.44,1.14,True)
    cyl('Pan pedestal bearing',(0,0,1.14),.060,.075,p['black'],verts=40)
    ring('Pan bearing trim',(0,0,1.146),.064,.047,.020,p['steel'],sides=40)
    box('Yoke bottom bridge',(0,0,1.205),(.48,.105,.043),p['black'],.010)
    for x in [-.224,.224]:
        box('Vertical yoke arm',(x,0,1.365),(.041,.105,.34),p['black'],.014)
        cyl('Yoke trunnion bearing',(x,0,1.505),.052,.049,p['steel'],'X',40,.003)
        cyl('Tilt tension grip',(x*1.16,0,1.505),.043,.036,p['rubber'],'X',12,.004)
        rod('Side trunnion axle',(x*.61,0,1.505),(x,0,1.505),.021,p['steel'],28,.002)
    z=1.505
    # Main cylindrical barrel, front tube and hollow hood surround a recessed opaque lens.
    ring('Main followspot barrel',(0,-.033,z),.158,.143,.333,p['black'],'Y',64)
    ring('Front barrel collar',(0,-.202,z),.163,.121,.034,p['steel'],'Y',64)
    ring('Optical tube exterior',(0,-.315,z),.125,.109,.212,p['black'],'Y',64)
    ring('Front focusing collar',(0,-.411,z),.133,.109,.042,p['rubber'],'Y',64)
    ring('Hollow lens hood',(0,-.475,z),.135,.120,.092,p['black'],'Y',64)
    ring('Lens edge retaining ring',(0,-.439,z),.121,.106,.013,p['steel'],'Y',64)
    cyl('Recessed opaque non-emitting lens',(0,-.427,z),.105,.009,p['lens'],'Y',64,.001)
    for i in range(32):
        a=math.tau*i/32
        o=box('Focus collar grip rib',(.132*math.cos(a),-.411,z+.132*math.sin(a)),(.005,.028,.005),p['black'],.001);o.rotation_euler[1]=-a
    # True ventilation openings surround a short rear cage, with a recessed opaque core.
    ring('Rear ventilation forward rim',(0,.144,z),.158,.140,.021,p['black'],'Y',64)
    ring('Rear ventilation end rim',(0,.284,z),.158,.139,.026,p['black'],'Y',64)
    for i in range(18):annular_arc('Separated rear ventilation shell rib',(0,.214,z),.144,.156,.122,i*20+3,i*20+15,p['black'],'Y',3)
    cyl('Recessed static rear equipment core',(0,.19,z),.112,.16,p['dark'],'Y',48,.004)
    # The rear grille contains physical bars and a shallow opaque fan appearance behind them.
    ring('Rear grille outer ring',(0,.306,z),.145,.099,.023,p['black'],'Y',56)
    cyl('Unlit rear fan-shaped interior',(0,.287,z),.098,.012,p['dark'],'Y',48,.002)
    for xx in [-.075,-.050,-.025,0,.025,.050,.075]:
        half=math.sqrt(.098**2-xx**2);rod('Rear grille vertical bar',(xx,.320,z-half),(xx,.320,z+half),.0038,p['steel'],12,.0004)
    cyl('Rear grille center boss',(0,.325,z),.018,.011,p['black'],'Y',28,.001)
    # Fixed operators handle and recognisable external controls, not an operating mechanism.
    sweep('Fixed rear operator handle',[(-.104,.283,z+.065),(-.104,.396,z+.103),(-.081,.425,z+.125),(.081,.425,z+.125),(.104,.396,z+.103),(.104,.283,z+.065)],.012,p['rubber'],12,'Z')
    for x in [-.10,.10]:cyl('Operator handle attachment collar',(x,.286,z+.067),.018,.026,p['steel'],'Y',24,.002)
    box('Top iris control rail',(-.050,-.024,z+.157),(.023,.23,.017),p['steel'],.003)
    box('Fixed iris slider',(-.050,.015,z+.174),(.045,.038,.025),p['black'],.005)
    rod('Iris control lever',(-.050,.015,z+.182),(-.050,.075,z+.241),.007,p['steel'],20,.001)
    cyl('Iris lever knob',(-.050,.079,z+.245),.018,.029,p['rubber'],'X',20,.003)
    box('Side focus guide rail',(.124,-.300,z),(.016,.20,.020),p['steel'],.003)
    cyl('Focus lock knob',(.155,-.305,z),.028,.039,p['rubber'],'X',12,.003)
    box('Rear control pod',(.151,.199,z-.025),(.031,.115,.072),p['black'],.006)
    for yy in [.176,.215]:cyl('Opaque side control knob',(.176,yy,z-.022),.012,.019,p['blue'],'X',20,.002)
    box('Unlit rear power recess',(.051,.314,z-.117),(.044,.008,.024),p['dark'],.002)
    box('Static red toggle cap',(.053,.321,z-.116),(.016,.008,.013),p['red'],.002)
    for x in [-.105,.105]:
        fixing('Rear case captive bolt',(x,.319,z+.074),p['steel'],'Y',.006)
    return ('city-theatrical-followspot','舞台用フォロースポットライト','Theatrical followspot on tripod',
        '長い鏡筒、奥まったレンズ代替面、実際に中空のフード、後部通気スロットと格子、操作ハンドル、アイリス風レバー、焦点調整風ノブ、ヨークと左右支点を備えた三脚式の舞台用フォロースポット外観。レンズは不透明な青黒い材質で、光源・光束・投影・透過はありません。照準・支点・脚・操作部は固定です。舞台、天井、人物、電源ケーブルは含みません。内部光学系、ランプ、電気回路、冷却機構と細かなねじ山は省略。機器安全性、構造、電気・光学性能は未検証。',
        'A theatrical followspot appearance assembly on a tripod pedestal, with elongated barrel, recessed lens placeholder, genuinely hollow hood, rear ventilation slots and grille, operator handle, iris-like lever, focus-like knob, yoke and paired trunnions. The lens is opaque blue-black material with no light source, beam, projection or transmission. Aiming, pivots, legs and controls are static. No stage, ceiling, person or power cable is included. Internal optics, lamp, circuits, cooling mechanism and fine screw threads are omitted. Equipment safety, structure and electrical/optical performance are unvalidated.',
        ['followspot','theatrical-equipment','tripod','フォロースポット'])


def underside_render(path,azimuth):
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    vv=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lo=Vector([min(v[i] for v in vv) for i in range(3)]);hi=Vector([max(v[i] for v in vv) for i in range(3)]);span=max(hi-lo);center=(lo+hi)/2
    lights=[]
    for pos,power in [((-.4,-1.2,-1.4),250),((1.2,.8,-.9),150)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*span);o=bpy.context.object;o.data.energy=power*span*span;o.data.shape='DISK';o.data.size=1.2*span;look_at(o,center);lights.append(o)
    common.render(path,azimuth,-28)
    for o in lights:bpy.data.objects.remove(o,do_unlink=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-019/assets');ap.add_argument('--geometry-only',action='store_true');ap.add_argument('--only',default='');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if a.geometry_only:common.render=lambda *args,**kwargs:None
    builders=[(lectern,-60,23),(ceiling_projector,-54,22),(projection_screen,-68,17),(followspot,-57,22)]
    reports=[]
    for build,az,el in builders:
        if a.only and a.only!=build.__name__:continue
        reset();data=build();report=publish_asset(*data,a.out,'scripts/city_expansion/event_presentation.py',azimuth=az,elevation=el);reports.append(report)
        if not a.geometry_only:underside_render(Path(a.out)/'_qa'/f'{data[0]}-underside.png',az+25)
    print('BATCH_019_COMPLETE '+json.dumps(reports),flush=True)

if __name__=='__main__':main()
