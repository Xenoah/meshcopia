"""Four original static vertical-access city structures. Xenoah, CC BY 4.0.
No third-party geometry, images, logos or fonts; not engineering specifications.
Authoring: metres, Z-up; distribution: metres, Y-up GLB and matching STL.
Production: CITY_RENDER_SAMPLES=48 blender -b -noaudio --factory-startup --threads 4 \
 --python scripts/city_expansion/vertical_access.py -- --out batches/batch-017/assets
Portable reproduction may add --geometry-only: only raster rendering is skipped.
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(steel=mat('Satin stainless structural metal',(.45,.51,.54),.78,.31),
        zinc=mat('Dark galvanized support steel',(.19,.25,.28),.70,.48),
        silver=mat('Brushed aluminum treads',(.55,.61,.63),.72,.37),
        graphite=mat('Graphite machinery paint',(.040,.060,.070),.28,.52),
        teal=mat('Opaque muted teal metal infill panels',(.09,.24,.27),.36,.36),
        rubber=mat('Charcoal rubber handrails and pads',(.018,.023,.025),0,.76),
        yellow=mat('Warm yellow edge markings',(.95,.59,.08),.02,.48),
        blue=mat('Industrial blue coated steel',(.075,.20,.31),.42,.42),
        dark=mat('Recessed unlit control surfaces',(.015,.026,.031),.1,.65),
        red=mat('Opaque red control cap',(.62,.035,.025),.03,.48),
        ivory=mat('Ivory control cap',(.80,.82,.76),.03,.5))


def cyl(n,p,r,d,m,axis='Z',verts=32,bev=.002):
    o=cylinder(n,p,r,d,m,vertices=verts,bevel=bev)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
    return o


def rod(n,a,b,r,m,verts=20,bev=.001):
    a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def beam(n,a,b,w,d,m,bev=.004):
    a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def fixing(n,p,m,axis='Z',r=.010):
    cyl(n+' washer',p,r*1.5,.004,m,axis,20,.0005)
    q=list(p);q['XYZ'.index(axis)]+=.006
    cyl(n+' hex head',q,r,.012,m,axis,6,.0005)


def small_stair_fixing(n,p,m,r=.006):
    """Readable closed washer and hex head; no subpixel repeated bevel rings."""
    cyl(n+' washer',p,r*1.5,.004,m,verts=12,bev=0)
    q=(p[0],p[1],p[2]+.006)
    cyl(n+' hex head',q,r,.012,m,verts=6,bev=0)


def extrude_profile(n,points,x0,x1,m,bev=0):
    v=[(x,y,z) for x in (x0,x1) for y,z in points];k=len(points)
    f=[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]
    f.extend((i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k))
    return mesh(n,v,f,m,bev)


def sweep(n,points,r,m,closed=False,sides=12,frame='Z',ellipse=None):
    """Actual closed mesh tube with welded seam, not alpha cards or curve overlap."""
    pts=[Vector(p) for p in points];v=[];f=[];k=len(pts)
    for i,p in enumerate(pts):
        if closed:t=(pts[(i+1)%k]-pts[(i-1)%k]).normalized()
        elif i==0:t=(pts[1]-p).normalized()
        elif i==k-1:t=(p-pts[i-1]).normalized()
        else:t=(pts[i+1]-pts[i-1]).normalized()
        ref=Vector((1,0,0) if frame=='X' else (0,0,1));u=(ref-t*ref.dot(t)).normalized();w=t.cross(u).normalized()
        for j in range(sides):
            a=math.tau*j/sides;v.append(tuple(p+u*math.cos(a)*r+w*math.sin(a)*(ellipse or r)))
    for i in range(k if closed else k-1):
        ni=(i+1)%k
        for j in range(sides):nj=(j+1)%sides;f.append((i*sides+j,ni*sides+j,ni*sides+nj,i*sides+nj))
    if not closed:f.extend([tuple(range(sides-1,-1,-1)),tuple((k-1)*sides+j for j in range(sides))])
    o=mesh(n,v,f,m)
    for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
    return o


def sector(n,r0,r1,z0,z1,a0,a1,m,steps=10):
    v=[];k=steps+1
    for r,z in [(r0,z0),(r1,z0),(r1,z1),(r0,z1)]:
        for i in range(k):a=math.radians(a0+(a1-a0)*i/steps);v.append((r*math.cos(a),r*math.sin(a),z))
    f=[]
    for q in range(4):
        for i in range(steps):f.append((q*k+i,q*k+i+1,((q+1)%4)*k+i+1,((q+1)%4)*k+i))
    f.extend([(0,k,2*k,3*k),(k-1,4*k-1,3*k-1,2*k-1)])
    return mesh(n,v,f,m)


def passenger_escalator():
    p=palette()
    # Short complete exterior assembly. The inclined visible steps do not imply a return chain.
    outline=[(-2.50,.03),(-1.53,.03),(1.55,1.76),(2.50,1.76),(2.50,2.035),(1.50,2.035),(-1.50,.235),(-2.50,.235)]
    extrude_profile('Continuous enclosed under-truss',outline,-.545,.545,p['graphite'],.012)
    for x in [-.59,.59]:
        extrude_profile('Stainless lower side skirt',[(y,z+.035) for y,z in outline],x-.04,x+.04,p['steel'],.008)
        # Balustrade is deliberately opaque metal infill, not false transparent glazing.
        panel=[(-2.16,.33),(-1.50,.33),(1.50,2.13),(2.16,2.13),(2.16,2.88),(1.50,2.88),(-1.50,1.08),(-2.16,1.08)]
        extrude_profile('Opaque teal balustrade infill',panel,x-.024,x+.024,p['teal'],.012)
        for y,z in [(-2.16,.34),(-1.5,.34),(-.5,.94),(.5,1.54),(1.5,2.14),(2.16,2.14)]:
            box('Balustrade panel clamp',(x,y,z+.34),(.068,.036,.69),p['steel'],.004)
            for zz in [z+.045,z+.63]:fixing('Panel clamp fastener',(x+.038,y,zz),p['steel'],'X',.006)
        # Top and concealed-return outlines meet via rounded end loops.
        pts=[(x,-2.15,1.13),(x,-1.5,1.13),(x,1.5,2.93),(x,2.15,2.93)]
        for i in range(1,21):
            a=math.pi/2-math.pi*i/20;pts.append((x,2.15+.22*math.cos(a),2.71+.22*math.sin(a)))
        pts.extend([(x,1.5,2.49),(x,-1.5,.69),(x,-2.15,.69)])
        for i in range(1,20):
            a=-math.pi/2-math.pi*i/20;pts.append((x,-2.15+.22*math.cos(a),.91+.22*math.sin(a)))
        sweep('Continuous rubber handrail loop',pts,.044,p['rubber'],True,16,'X',.032)
        # Actual rail support caps below the moving-looking top side only.
        sweep('Metal handrail guide',[(x,-2.13,1.085),(x,-1.5,1.085),(x,1.5,2.885),(x,2.13,2.885)],.020,p['steel'],False,12,'X',.016)
        for y,z in [(-2.30,.235),(2.30,2.035)]:
            box('Landing corner skirt cap',(x,y,z+.12),(.10,.30,.24),p['steel'],.022)
            box('Opaque entry sensor recess',(x-.053 if x>0 else x+.053,y-.05,z+.13),(.007,.10,.055),p['dark'],.010)
    # Real tread blocks, risers and separate shallow longitudinal ridges.
    steps=[(-1.65,.24)]+[(-1.35+i*.30,.42+i*.18) for i in range(10)]+[(1.65,2.04)]
    for j,(y,z) in enumerate(steps):
        box('Individual complete step '+str(j),(0,y,z-.09),(.91,.299,.18),p['silver'],.002)
        for x in [(-.42+k*.035) for k in range(25)]:
            box('Longitudinal tread rib',(x,y,z+.0025),(.013,.286,.005),p['steel'],0)
            if 0<j<11:box('Visible riser groove rib',(x,y-.150,z-.089),(.013,.004,.158),p['steel'],0)
        box('Yellow step front nosing',(0,y-.143,z+.006),(.90,.013,.009),p['yellow'],.001)
        for x in [-.447,.447]:box('Yellow tread side edge',(x,y,z+.006),(.012,.284,.009),p['yellow'],.001)
    # Landing service plates and genuine comb fingers at the moving-step junctions.
    for s,z in [(-1,.24),(1,2.04)]:
        y=s*2.23;box('Removable grooved landing plate',(0,y,z-.018),(.99,.53,.036),p['silver'],.006)
        for k in range(14):box('Landing traction rib',(0,y-.235+k*.036,z+.002),( .95,.011,.005),p['steel'],0)
        cy=s*1.925;box('Comb plate backing',(0,cy,z+.007),(.94,.084,.023),p['yellow'],.002)
        for k in range(26):box('Individual landing comb finger',(-.438+k*.035,cy-s*.058,z+.005),(.016,.070,.018),p['yellow'],.001)
        for x in [-.43,.43]:
            for yy in [y-.20,y+.20]:fixing('Landing plate captive screw',(x,yy,z+.006),p['steel'],r=.006)
    # Bottom-facing structural flanges, cross ties and real end attachment tabs.
    for y,z in [(-2.35,.03),(-1.7,.03),(-.8,.45),(0,.90),(.8,1.35),(1.7,1.76),(2.35,1.76)]:
        box('Underside truss cross tie',(0,y,z+.018),(1.07,.10,.036),p['zinc'],.004)
        for x in [-.43,.43]:fixing('Underside cross tie bolt',(x,y,z+.039),p['steel'],r=.009)
    for y,z in [(-2.44,.015),(2.44,1.75)]:
        for x in [-.48,.48]:box('Building-seat attachment shoe',(x,y,z),(.24,.14,.030),p['zinc'],.004)
    return ('city-passenger-escalator','短尺パッセンジャー・エスカレーター','Short passenger escalator',
        '上下の乗降板、実形状のコーム歯、段板と蹴上げ、踏面リブ、左右連続手すりループ、側板と下面梁を備えた短いエスカレーター外観。青緑の側面パネルは不透明な金属板で、透過ガラスではありません。上下床の高さと開口を別途合わせる配置用モデルで、建物・地面・人は含みません。隠れた駆動装置、戻り段列、チェーン、内部配線、細かなねじ山は省略。段・手すりは固定で動作や物理挙動はなく、輸送能力、機械安全、避難、アクセシビリティ、荷重や建築基準への適合は未検証。施工・操作案内ではありません。',
        'A short escalator appearance assembly with upper/lower landing plates, actual comb fingers, individual treads and risers, raised tread ribs, continuous handrail loops on both sides, side skirts and underside ties. Teal balustrade panels are opaque metal, not transparent glass. Align both landing heights and a host opening separately; no building, ground or person is included. Hidden drive, return-step train, chains, internal wiring and tiny screw threads are omitted. Steps and handrails are fixed with no operation or physics. Passenger capacity, machinery safety, evacuation, accessibility, loads and building-code compliance are unvalidated. This is not installation or operating guidance.',
        ['escalator','vertical-access','architecture','エスカレーター'])


def platform_lift():
    p=palette()
    # Freestanding display structure; platform is fixed above its lowest stop.
    for x in [-.51,.51]:
        box('Long base chassis rail',(x,.12,.067),(.16,1.95,.134),p['zinc'],.010)
        for y in [-.76,.94]:
            box('Base anchor shoe',(x,y,.018),(.25,.25,.036),p['steel'],.008)
            for dx in [-.075,.075]:fixing('Ground anchor head',(x+dx,y,.040),p['steel'],r=.012)
    for y in [-.61,.78]:box('Base cross tie',(0,y,.10),(1.18,.13,.13),p['zinc'],.010)
    # Rear mast with separate guide channels and a carriage visibly supporting the deck.
    box('Closed fixed lift mast',(0,.94,1.43),(.40,.25,2.80),p['blue'],.018)
    box('Mast head cap',(0,.94,2.845),(.45,.30,.052),p['steel'],.010)
    for x in [-.245,.245]:
        box('Exposed vertical guide rail',(x,.772,1.41),(.045,.052,2.69),p['steel'],.005)
        box('Guide rail backing web',(x,.822,1.41),(.075,.088,2.69),p['zinc'],.006)
        for z in [.24,.86,1.48,2.10,2.66]:fixing('Guide rail mount',(x,.755,z),p['steel'],'Y',.008)
    box('Carriage backplate',(0,.694,.83),(.65,.095,.80),p['zinc'],.012)
    for x in [-.247,.247]:
        for z in [.54,1.10]:
            box('Carriage guide shoe',(x,.744,z),(.15,.12,.19),p['graphite'],.012)
            cyl('Visible carriage roller',(x,.682,z),.062,.065,p['rubber'],'Y',32,.004)
            cyl('Carriage roller axle cap',(x,.640,z),.025,.018,p['steel'],'Y',20,.002)
    # Cantilever arms reach the underside of the entire deck, not floating brackets.
    for x in [-.40,.40]:
        box('Platform underframe cantilever',(x,-.03,.450),(.10,1.55,.14),p['zinc'],.007)
        beam('Carriage triangular support',(x,.65,.23),(x,-.23,.43),.072,.075,p['zinc'],.006)
        box('Carriage arm attachment gusset',(x,.61,.37),(.18,.12,.27),p['steel'],.006)
        for z in [.30,.46]:fixing('Cantilever mounting bolt',(x,.538,z),p['steel'],'Y',.012)
    box('Platform transverse support',(0,-.64,.45),(1.27,.09,.13),p['zinc'],.006)
    box('Raised access platform floor',(0,-.055,.55),(1.28,1.54,.07),p['silver'],.008)
    for x in [-.58+i*.083 for i in range(15)]:box('Deck anti-slip ridge',(x,-.06,.588),(.022,1.43,.006),p['steel'],.001)
    for x in [-.64,.64]:
        box('Platform edge toe plate',(x,-.045,.665),(.035,1.57,.18),p['blue'],.006)
        for y in [-.77,.68]:
            box('Side guard upright',(x,y,1.13),(.045,.045,1.12),p['steel'],.007)
            box('Guard foot socket',(x,y,.645),(.08,.08,.13),p['zinc'],.008)
            fixing('Guard socket fastener',(x+.043,y,.65),p['steel'],'X',.008)
        box('Side guard handrail',(x,-.045,1.68),(.052,1.50,.052),p['steel'],.010)
        box('Side guard middle rail',(x,-.045,1.18),(.035,1.50,.035),p['steel'],.006)
        for y in [-.44,-.08,.28]:box('Side guard baluster',(x,y,1.20),(.025,.025,.96),p['steel'],.004)
    # Rear guard prevents visual open drop beside the lifting mast.
    for z in [.72,1.18,1.68]:box('Rear guard cross rail',(0,.68,z),(1.28,.044,.044),p['steel'],.006)
    for x in [-.42,0,.42]:box('Rear guard vertical infill',(x,.68,1.20),(.028,.028,.92),p['steel'],.004)
    # Fixed closed front gate has attached barrel hinges, latch and a shallow toe plate.
    for x in [-.57,.57]:box('Front gate stile',(x,-.793,1.185),(.035,.035,.92),p['steel'],.006)
    for z in [.73,1.23,1.64]:box('Front gate rail',(0,-.793,z),(1.17,.035,.035),p['steel'],.006)
    box('Gate solid toe guard',(0,-.793,.688),(1.15,.026,.18),p['blue'],.004)
    for x in [-.29,0,.29]:box('Gate vertical bar',(x,-.793,1.18),(.025,.025,.88),p['steel'],.004)
    for z in [.88,1.47]:
        cyl('Gate hinge barrel',(-.612,-.79,z),.031,.135,p['steel'],verts=24,bev=.002)
        box('Gate hinge strap',(-.569,-.79,z),(.11,.040,.056),p['zinc'],.003)
    box('Closed gate latch housing',(.605,-.794,1.34),(.12,.065,.13),p['graphite'],.010)
    box('Gate latch handle',(.55,-.85,1.37),(.13,.032,.032),p['steel'],.006)
    box('Front threshold yellow edge',(0,-.817,.589),(1.22,.028,.010),p['yellow'],.002)
    # Unlit controls on an actual guard-mounted pod.
    box('Control pod bracket',(.66,.35,1.47),(.10,.12,.07),p['zinc'],.006)
    box('Guard-mounted control enclosure',(.73,.35,1.48),(.12,.16,.27),p['blue'],.016)
    for z,m in [(1.40,p['ivory']),(1.49,p['ivory']),(1.58,p['red'])]:cyl('Opaque nonfunctional control button',(.73,.257,z),.024,.021,m,'Y',24,.002)
    box('Rear mast service-cover gasket',(0,1.072,.76),(.31,.014,.72),p['rubber'],.012)
    box('Rear mast service cover',(0,1.083,.76),(.29,.018,.69),p['blue'],.012)
    for x in [-.12,.12]:
        for z in [.46,1.06]:fixing('Rear cover screw',(x,1.098,z),p['steel'],'Y',.007)
    return ('city-vertical-platform-lift','開放型垂直プラットフォームリフト','Open vertical platform access lift',
        '車椅子向け昇降設備を表現する、マスト付き開放型アクセスプラットフォームの静的外観。上昇位置の床、支持台枠、片持ち腕、斜材、ガイドと可視キャリッジ、側面・背面ガード、閉じた前扉、ヒンジ、ラッチと非作動ボタンを造形。床・壁・利用者・車椅子は含まず、下部フレームの基準と目的の床高さをシーン側で合わせる必要があります。内部駆動、配線、インターロック、油圧系統、細かなねじ山は省略。昇降・扉動作・安全機能はなく、アクセシビリティ、機械・荷重・人の利用・避難・建築基準の認証はありません。施工・操作案内ではありません。',
        'Static appearance of an open mast-mounted wheelchair-style access platform, with a raised deck, base chassis, cantilever arms and braces, exposed guides and visible carriage, side/rear guards, closed front gate, hinges, latch and nonfunctional buttons. No floor, wall, rider or wheelchair is included; align the lower chassis and intended floor levels in the host scene. Internal drive, wiring, interlocks, hydraulic circuit and tiny screw threads are omitted. No lift or gate motion, safety function, accessibility, machinery, load, human-use, evacuation or building-standard certification is supplied. This is not installation or operating guidance.',
        ['platform-lift','access-platform','vertical-access','昇降機'])


def loading_leveler():
    p=palette();ang=math.radians(12);cs=math.cos(ang);sn=math.sin(ang)
    def deck(x,y,z=0):return (x,y*cs,.70-y*sn+z)
    for x in [-1.04,1.04]:
        box('Recessed leveler side base channel',(x,0,.105),(.13,2.52,.19),p['zinc'],.008)
        for y in [-1.16,1.16]:
            box('Recess anchoring foot',(x,y,.02),(.23,.24,.04),p['steel'],.006)
            for yy in [y-.07,y+.07]:fixing('Base anchor bolt',(x,yy,.047),p['steel'],r=.012)
    for y in [-1.22,0,1.22]:box('Base channel crossmember',(0,y,.12),(2.15,.13,.17),p['zinc'],.007)
    for y in [.58,.80]:box('Pinned linkage foundation crossmember',(0,y,.14),(2.08,.10,.16),p['zinc'],.006)
    for x in [-.83,.83]:
        box('Rear hinge pedestal',(x,1.13,.305),(.14,.20,.42),p['blue'],.008)
        for dx in [-.035,.035]:fixing('Rear pedestal fixing',(x+dx,1.13,.527),p['steel'],r=.009)
    # Raised deck and welded underside stiffeners follow the same exact transform.
    box('Single raised steel deck',deck(0,0), (2.02,2.32,.065),p['blue'],.008,(-ang,0,0))
    for x in [-.83,-.42,0,.42,.83]:box('Longitudinal underside deck rib',deck(x,0,-.095),(.055,2.22,.15),p['zinc'],.004,(-ang,0,0))
    for y in [-.90,-.30,.30,.91]:box('Under-deck cross stiffener',deck(0,y,-.075),(1.96,.050,.13),p['zinc'],.004,(-ang,0,0))
    for x in [-.98,.98]:box('Yellow side deck edge',deck(x,0,.036),(.032,2.29,.009),p['yellow'],.001,(-ang,0,0))
    # Staggered compact lozenges are real raised tread geometry, not image textures.
    for j in range(14):
        y=-1.03+j*.157
        for i in range(11):
            x=-.87+i*.17+(.04 if j%2 else 0)
            o=box('Raised deck checker lozenge',deck(x,y,.036),(.071,.022,.007),p['steel'],.002)
            o.rotation_euler=(-ang,0,math.radians(32 if (i+j)%2 else -32))
    back=deck(0,1.16,-.014);cyl('Rear deck pivot shaft',back,.042,2.12,p['steel'],'X',32,.002)
    for x in [-.87,-.65,.65,.87]:cyl('Rear deck hinge sleeve',(x,back[1],back[2]),.068,.13,p['zinc'],'X',32,.002)
    front=deck(0,-1.16,-.01)
    # Short front hinged lip droops slightly from the raised deck.
    lipang=math.radians(5);ll=.44
    lipcenter=(0,front[1]-ll*.5*math.cos(lipang),front[2]-.5*ll*math.sin(lipang))
    box('Extended front lip plate',lipcenter,(2.0,ll,.038),p['steel'],.006,(lipang,0,0))
    box('Lip outer warning edge',(0,front[1]-ll*math.cos(lipang)+.018,front[2]-ll*math.sin(lipang)+.024),(2.0,.036,.010),p['yellow'],.001,(lipang,0,0))
    cyl('Front lip continuous hinge pin',front,.031,2.065,p['steel'],'X',32,.002)
    for i in range(13):cyl('Alternating lip hinge knuckle',(-.923+i*.154,front[1],front[2]),.052,.12,p['zinc'] if i%2 else p['blue'],'X',28,.002)
    for x in [-.73,-.30,.30,.73]:box('Lip underside reinforcing rib',(x,lipcenter[1],lipcenter[2]-.042),(.040,.34,.065),p['zinc'],.003,(lipang,0,0))
    # Readable pinned lift linkage plus hydraulic appearance barrel/rod in fixed pose.
    for x in [-.60,.60]:
        a=(x,.58,.22);b=deck(x,-.57,-.16)
        beam('Visible pinned lifting arm',a,b,.075,.090,p['blue'],.006)
        for yy,zz in [(a[1],a[2]),(b[1],b[2])]:
            cyl('Lift arm transverse pin',(x,yy,zz),.035,.17,p['steel'],'X',24,.002)
            for dx in [-.089,.089]:cyl('Lift arm pin retaining cap',(x+dx,yy,zz),.048,.015,p['steel'],'X',24,.002)
        for yy,zz in [(a[1],a[2]),(b[1],b[2])]:
            for dx in [-.06,.06]:box('Lift arm clevis cheek',(x+dx,yy,zz),(.025,.17,.15),p['zinc'],.006)
    b=deck(0,-.57,-.16);cyl('Lift-arm cross shaft',b,.042,1.34,p['steel'],'X',32,.002)
    a=Vector((0,.80,.20));b=Vector(b);v=b-a;u=v.normalized();joint=a+v*.64
    rod('Visible hydraulic appearance barrel',a,joint,.078,p['blue'],32,.005)
    rod('Exposed fixed piston rod',joint,b,.033,p['steel'],28,.002)
    rod('Cylinder gland ring',joint-u*.022,joint+u*.018,.090,p['zinc'],32,.002)
    for pp in [a,b]:
        cyl('Cylinder pin',pp,.034,.22,p['steel'],'X',24,.002)
        for x in [-.10,.10]:box('Cylinder mounting clevis',(x,pp.y,pp.z),(.025,.14,.16),p['zinc'],.005)
    # Folded side toe guards close the dangerous-looking deck/frame gaps visually.
    for x in [-1.005,1.005]:
        extrude_profile('Side triangular toe guard',[(-1.10,.27),(1.10,.27),(1.10,.45),(-1.10,.92)],x-.012,x+.012,p['blue'],.004)
        for y in [-.92,.86]:fixing('Side guard fixing',(x+.018,y,.40 if y>0 else .74),p['steel'],'X',.009)
    # Fixed lip link connects underside to hinge lever without implying operation.
    beam('Lip underside lever',deck(.30,-.90,-.13),(.30,front[1]-.11,front[2]-.07),.035,.040,p['zinc'],.003)
    return ('city-loading-dock-leveler','上昇姿勢の埋込型ドックレベラー','Raised recessed loading dock leveler',
        '倉庫荷捌き床に埋め込むデッキとリップの静的ユニット。上昇した縞鋼板風デッキ、前端リップと連続ピン・分割ヒンジ、下面の縦横補強、基礎フレーム、側面板、実形状の昇降リンクとシリンダー外観を造形。周囲ピット、床、建物、ドックシェルター、トラック、人や荷物は含みません。最下部フレームを基準に配置し、周囲床や車両高さは別途シーンで合わせる必要があります。隠れた油圧系統、動力源、内部機構、細かなねじ山は省略。固定姿勢のみで作動・衝突・荷重評価はなく、機械安全・人の利用・建築基準への適合は未検証。施工・操作案内ではありません。',
        'Static recessed warehouse dock deck-and-lip unit in a raised pose, with actual raised checker details, front lip, continuous pivot pins and segmented hinges, underside longitudinal/cross ribs, base frame, side toe guards, visible pinned lifting linkage and a cylinder appearance assembly. No surrounding pit, floor, building, dock shelter, truck, person or cargo is included. Place from the lowest support frame and align surrounding floor/vehicle heights separately. Hidden hydraulic circuit, power unit, internal mechanisms and tiny screw threads are omitted. Fixed pose only, without operation, collisions, load rating or machinery, human-use and building-standard validation. This is not installation or operating guidance.',
        ['dock-leveler','warehouse','loading-dock','access-structure','ドックレベラー'])


def spiral_stair():
    p=palette();r0=.11;r1=1.10;start=-100;da=22.5;n=14
    def polar(r,a,z):a=math.radians(a);return (r*math.cos(a),r*math.sin(a),z)
    cyl('Circular central column base plate',(0,0,.022),.285,.044,p['zinc'],verts=64,bev=.006)
    cyl('Continuous central structural column',(0,0,2.015),.115,4.00,p['steel'],verts=64,bev=.006)
    cyl('Column head weather cap',(0,0,4.027),.132,.035,p['steel'],verts=48,bev=.004)
    for a in range(0,360,60):fixing('Central column base anchor',polar(.223,a,.049),p['steel'],r=.014)
    for i in range(n):
        a0=start+i*da;a1=a0+da-.7;am=(a0+a1)/2;z=.20*(i+1)
        # Roots overlap genuine sleeves on the central column; radial underside arms carry plates.
        sector('Solid radial stair tread '+str(i+1),r0,r1,z-.043,z,a0,a1,p['silver'],12)
        cyl('Column tread sleeve',(0,0,z-.085),.171,.13,p['zinc'],verts=48,bev=.004)
        beam('Radial underside tread bracket',polar(.13,am,z-.077),polar(1.055,am,z-.077),.073,.07,p['zinc'],.005)
        beam('Diagonal tread root gusset',polar(.15,am,z-.14),polar(.53,am,z-.067),.050,.055,p['zinc'],.004)
        for rr in [.38,.61,.84,1.02]:sector('Raised annular tread traction strip',rr-.014,rr+.014,z+.001,z+.006,a0+1,a1-1,p['steel'],12)
        beam('Yellow radial leading tread edge',polar(.18,a0+.6,z+.008),polar(1.07,a0+.6,z+.008),.018,.009,p['yellow'],.001)
        # Handrail posts meet plates and explicit base shoes; paired infill bars follow the pitch.
        for a,rr,h in [(am,1.045,1.00),(a0+2.5,1.045,1.0 if i==0 else 1.0+(2.5-(da-.7)/2)*.20/da)]:
            pp=polar(rr,a,z);cyl('Outer guard post',polar(rr,a,z+h/2),.018,h,p['steel'],verts=20,bev=.001)
            box('Guard tread attachment shoe',(pp[0],pp[1],z+.018),(.075,.075,.036),p['zinc'],.005,(0,0,math.radians(a)))
            for dr in [-.022,.022]:small_stair_fixing('Guard shoe screw',polar(rr+dr,a,z+.038),p['steel'],r=.006)
        for rr in [.20,.94]:small_stair_fixing('Tread bracket bolt',polar(rr,am,z+.009),p['steel'],r=.008)
    # A wide wedge landing creates a real top destination, not just another thin tread.
    la=start+n*da;lz=3.0
    sector('Top landing radial deck',.11,1.29,lz-.065,lz,la,la+45,p['silver'],24)
    cyl('Top landing structural sleeve',(0,0,lz-.11),.195,.18,p['zinc'],verts=48,bev=.004)
    for a in [la+3,la+22.5,la+42]:
        beam('Top landing underside radial beam',polar(.14,a,lz-.12),polar(1.23,a,lz-.12),.09,.12,p['zinc'],.006)
        beam('Landing diagonal root support',polar(.16,a,lz-.30),polar(.74,a,lz-.105),.06,.06,p['zinc'],.004)
    for rr in [.35,.56,.77,.98,1.20]:sector('Landing raised traction strip',rr-.014,rr+.014,lz+.001,lz+.006,la+2,la+43,p['steel'],24)
    # Continuous outer helical handrail travels through every main post top.
    a_first=start+(da-.7)/2;a_last=start+(n-1)*da+(da-.7)/2
    points=[polar(1.045,start+1.5,1.20)]
    for i in range(14*10+1):
        t=i/(14*10);a=a_first+(a_last-a_first)*t;z=1.20+2.60*t;points.append(polar(1.045,a,z))
    # Smooth cubic transition keeps the swept cross section outward at the landing bend.
    p0=Vector(points[-1]);p3=Vector(polar(1.245,la+1,4.0))
    th=math.radians(a_last);ta=Vector((-1.045*math.sin(th),1.045*math.cos(th),.20/math.radians(da))).normalized()
    th=math.radians(la+1);tb=Vector((math.cos(th),math.sin(th),0))
    p1=p0+ta*.16;p2=p3-tb*.16
    for j in range(1,21):
        t=j/20;points.append(tuple(p0*(1-t)**3+p1*(3*t*(1-t)**2)+p2*(3*t*t*(1-t))+p3*t**3))
    sweep('Continuous outer helical handrail',points,.025,p['steel'],False,14)
    # Lower guard line connects infill bars, with its own pitched continuous route.
    mids=[]
    for j in range(141):
        t=j/140;mids.append(polar(1.045,a_first+(a_last-a_first)*t,.72+2.6*t))
    sweep('Continuous mid-height helical guard',mids,.014,p['steel'],False,12)
    for a in [la+1]:
        cyl('Top landing outer guard post',polar(1.245,a,3.50),.023,1.0,p['steel'],verts=24,bev=.002)
        pp=polar(1.245,a,3.02);box('Landing guard mounting shoe',pp,(.085,.085,.040),p['zinc'],.006,(0,0,math.radians(a)))
    # Radial side guard bounds the landing; the outer arc is a genuine open receiving-floor exit.
    for r in [.20,.55,.90,1.245]:cyl('Landing radial side guard post',polar(r,la+44,3.5),.018,1,p['steel'],verts=20,bev=.001)
    for z in [3.50,4.0]:rod('Landing radial side rail',polar(.14,la+44,z),polar(1.245,la+44,z),.025 if z==4 else .015,p['steel'],24,.001)
    # Terminal deck edge has readable yellow marking and a mounting plate for host-scene placement.
    sector('Open outer landing exit yellow edge',1.262,1.286,lz+.001,lz+.008,la+2,la+43,p['yellow'],24)
    for a in [la+12,la+33]:
        pp=polar(1.27,a,lz-.06);box('Landing host-connection tab',pp,(.12,.09,.04),p['zinc'],.004,(0,0,math.radians(a)))
    return ('city-exterior-spiral-stair','独立型屋外らせん階段','Freestanding exterior spiral stair',
        '中心柱と各段の接続スリーブ・下面放射梁を備えた、直階段とは異なるらせん経路の階段外観。十四枚の実厚段板、踏面リブ、縁帯、取付靴付き外側ガード、連続らせん手すりと中桟、補強した上部踊り場、ベース板とボルトを造形。柱と各段は実形状の部材で接続されています。上部の接続先床・建物・地面・人は含みません。踊り場の開放された接続辺と高さをシーン側で調整する配置用です。隠れた基礎アンカー、排水穴、溶接ビード、細かなねじ山は省略。歩行・避難・耐荷重・転落防止・アクセシビリティ・建築基準の認証はなく、施工・利用案内ではありません。',
        'A spiral-route stair appearance assembly materially different from a straight stair, with a continuous central column, fourteen thick radial treads connected through real sleeves and underside radial beams, raised tread strips, edge markings, shoe-mounted outer guards, continuous helical handrail/midrail and a reinforced top landing. Treads visibly connect to the column through modeled structural members. No receiving floor, building, ground or person is included; align the open landing connection edge and height in the host scene. Concealed foundation anchors, drainage holes, weld beads and tiny screw threads are omitted. No walking, evacuation, load, fall-protection, accessibility or building-standard certification is supplied. This is not installation or human-use guidance.',
        ['spiral-stair','exterior-stair','architecture','vertical-access','らせん階段'])


BUILDERS=[passenger_escalator,platform_lift,loading_leveler,spiral_stair]
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--geometry-only',action='store_true');ap.add_argument('--only',default='');a=ap.parse_args(args)
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    if a.geometry_only:common.render=lambda *args,**kwargs:None
    for builder in BUILDERS:
        if a.only and a.only!=builder.__name__:continue
        reset();info=builder()
        report=publish_asset(*info,out_dir=out,generator='scripts/city_expansion/vertical_access.py',azimuth=-55,elevation=25)
        if not a.geometry_only:
            meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
            lo=Vector([min(v[k] for v in coords) for k in range(3)]);hi=Vector([max(v[k] for v in coords) for k in range(3)]);center=(lo+hi)/2;span=max(hi-lo)
            bpy.ops.object.light_add(type='AREA',location=center+Vector((-.5,-.8,-1.5))*span);light=bpy.context.object;light.data.energy=300*span*span;light.data.size=span;look_at(light,center)
            common.render(out/'_qa'/f'{info[0]}-underside.png',-55,-28,800)
            bpy.data.objects.remove(light,do_unlink=True)
