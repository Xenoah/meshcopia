"""Original compact utility vehicles for Xenoah / Meshcopia, CC BY 4.0.
Blender 4.3.2 procedural source: no third-party geometry, images, brands or fonts.
Static exterior assemblies, not mechanical, hydraulic, drive or safety designs.
Forward is -Y while authoring in metres/Z-up; common exports metres/Y-up.
"""
import argparse, math, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import reset, mat, mesh, tube, torus, publish_asset, ROOT

def box(name, loc, size, material=None, bevel=.008, rot=None):
    o=common.box(name,loc,size,material,bevel,rot)
    for m in o.modifiers:
        if m.type=='BEVEL': m.segments=1
    return o

def cyl(name,loc,r,depth,material,axis='Z',verts=32,bevel=.002):
    o=common.cylinder(name,loc,r,depth,material,verts,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=1
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o

def rod(name,a,b,r,material,verts=20):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,r,(b-a).length,material,verts=verts,bevel=min(.001,r*.15))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def beam(name,a,b,w,d,material,bevel=.003):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,d,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def profile(name,center,depth,points,material,axis='X',bevel=.002):
    n=len(points);vs=[(c,y,z) if axis=='X' else (y,c,z) for c in [center-depth/2,center+depth/2] for y,z in points]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,vs,fs,material,bevel)
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=1
    return o

def link(name,x,a,b,width,depth,material):
    a,b=Vector(a),Vector(b);v=b-a;n=Vector((-v.y,v.x)).normalized()*width/2
    return profile(name,x,depth,[tuple(a+n),tuple(b+n),tuple(b-n),tuple(a-n)],material,bevel=.003)

def cable(name,points,r,material):
    p=[Vector(v) for v in points];q=[p[0],*p,p[-1]];out=[]
    for j in range(1,len(q)-2):
        a,b,c,d=q[j-1:j+3]
        for k in range(7):
            t=k/7;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(p[-1]);return tube(name,out,r,material,1)

def bolt(name,loc,p,axis='X',r=.012,sign=1):
    cyl(name+' washer',loc,r*1.45,r*.35,p['steel'],axis,20,0)
    q=list(loc);q['XYZ'.index(axis)]+=sign*r*.48
    cyl(name+' hex head',q,r,r*.82,p['steel'],axis,6,.001)

def palette():
    return dict(yellow=mat('Warm industrial ochre enamel',(.69,.37,.045),.3,.4),orange=mat('Muted orange enamel',(.71,.19,.035),.3,.4),blue=mat('Deep blue enamel',(.035,.18,.34),.3,.4),dark=mat('Graphite steel frame',(.035,.048,.060),.5,.42),steel=mat('Satin plated steel',(.43,.49,.52),.83,.3),chrome=mat('Polished hydraulic rod',(.65,.71,.75),.92,.2),rubber=mat('Charcoal rubber',(.018,.023,.029),0,.83),seat=mat('Dark upholstery',(.055,.065,.072),0,.76),light=mat('Opaque unlit worklamp lens',(.81,.84,.78),.15,.3),red=mat('Red unlit marker and stop',(.48,.035,.022),.1,.4),amber=mat('Amber unlit beacon',(.85,.32,.035),.1,.35),face=mat('Blank control face',(.08,.12,.14),.15,.45))

def pin(name,x,y,z,length,p,r=.035):
    cyl(name+' pivot shaft',(x,y,z),r,length,p['steel'],'X',24)
    for s in [-1,1]:
        cyl(name+' retaining washer',(x+s*(length/2+.004),y,z),r*1.32,.012,p['dark'],'X',24,.001)
        bolt(name+' retaining bolt',(x+s*(length/2+.011),y,z),p,'X',r*.45,s)

def hydraulic(name,a,b,p,r=.042,ratio=.60):
    a,b=Vector(a),Vector(b);v=b-a;u=v.normalized()
    rod(name+' cylinder barrel',a+u*.035,a+v*ratio,r,p['dark'],32)
    rod(name+' bright piston rod',a+v*(ratio-.05),b-u*.02,r*.48,p['chrome'],24)
    rod(name+' gland collar',a+v*(ratio-.025),a+v*(ratio+.018),r*1.11,p['steel'],24)
    rod(name+' lower end cap',a+u*.01,a+u*.07,r*1.07,p['dark'],24)
    for pt in [a,b]:pin(name+' clevis',pt.x,pt.y,pt.z,r*3.2,p,r*.58)

def wheel(name,x,y,z,r,w,p, tread=True):
    # Closed annular sidewall and crown. The axle/rim are separate closed parts.
    seg=48;sections=[(-w*.5,r*.48),(-w*.50,r*.83),(-w*.37,r*.96),(-w*.28,r*.99),(w*.28,r*.99),(w*.37,r*.96),(w*.50,r*.83),(w*.50,r*.48)]
    vs=[(x+xx,y+rr*math.cos(math.tau*i/seg),z+rr*math.sin(math.tau*i/seg)) for xx,rr in sections for i in range(seg)]
    fs=[]
    for k in range(len(sections)):
        j=(k+1)%len(sections)
        for i in range(seg):fs.append((k*seg+i,k*seg+(i+1)%seg,j*seg+(i+1)%seg,j*seg+i))
    o=mesh(name+' closed tire',vs,fs,p['rubber'],0,True)
    if tread:
        for i in range(32):
            a=math.tau*i/32
            box(name+' tread rib',(x,y+(r-.006)*math.cos(a),z+(r-.006)*math.sin(a)),(w*.70,r*.12,.014),p['rubber'],.002,rot=(a-math.pi/2,0,0))
    cyl(name+' rim barrel',(x,y,z),r*.49,w*.92,p['steel'],'X',40,.006)
    for sign in [-1,1]:
        xx=x+sign*w*.48
        cyl(name+' rim dish',(xx,y,z),r*.40,.021,p['dark'],'X',32,.003)
        cyl(name+' hub cap',(xx+sign*.013,y,z),r*.19,.045,p['steel'],'X',28,.004)
        for j in range(5):
            a=math.tau*j/5;bolt(name+' lug',(xx+sign*.011,y+r*.28*math.cos(a),z+r*.28*math.sin(a)),p,'X',r*.035,sign)

def seat(name,x,y,z,p,width=.44):
    # Front of every operator seat faces -Y.
    box(name+' suspension pedestal',(x,y,z-.14),(width*.65,.30,.23),p['dark'],.025)
    box(name+' cushion',(x,y-.035,z),(width,.40,.095),p['seat'],.037)
    box(name+' back shell',(x,y+.17,z+.22),(width,.085,.42),p['dark'],.025,rot=(math.radians(-8),0,0))
    box(name+' back upholstery',(x,y+.12,z+.23),(width*.9,.07,.35),p['seat'],.029,rot=(math.radians(-8),0,0))
    for s in [-1,1]:
        box(name+' armrest',(x+s*(width/2+.026),y+.015,z+.23),(.065,.32,.065),p['seat'],.016)
        beam(name+' armrest support',(x+s*width*.49,y+.11,z+.07),(x+s*width*.49,y+.11,z+.23),.025,.025,p['dark'])
    # An unfastened parked restraint is visible, with no safety certification.
    box(name+' belt latch',(x+width*.36,y-.02,z+.063),(.044,.049,.028),p['red'],.006)

def steering(name,x,y,z,p,r=.15):
    a=Vector((x,y-.13,z-.23));b=Vector((x,y,z));rod(name+' column',a,b,.029,p['dark'],24)
    tor=torus(name+' wheel',(x,y,z),r,.015,p['rubber'],rotation=(math.radians(22),0,0),segments=36)
    normal=Vector((0,-math.sin(math.radians(22)),math.cos(math.radians(22))))
    for ang in [30,150,270]:
        th=math.radians(ang);end=Vector((r*math.cos(th),r*math.sin(th)*math.cos(math.radians(22)),r*math.sin(th)*math.sin(math.radians(22))))+b;rod(name+' spoke',b,end,.010,p['steel'])
    rod(name+' wheel hub',b-normal*.018,b+normal*.025,.043,p['dark'],24)

def lever(name,a,b,p):
    rod(name+' stalk',a,b,.009,p['steel']);common.sphere(name+' grip',b,(.024,.024,.032),p['rubber'],20,12)

def lamp(name,loc,size,p,axis='Y',sign=-1):
    box(name+' housing',loc,size,p['dark'],.012)
    q=list(loc);q['XYZ'.index(axis)]+=sign*size['XYZ'.index(axis)]*.51
    dims=list(size);dims['XYZ'.index(axis)]=.008
    dims[(('XYZ'.index(axis))+1)%3]*=.77;dims[(('XYZ'.index(axis))+2)%3]*=.77
    box(name+' opaque inactive lens',q,dims,p['light'],.004)

def step(name,x,y,z,width,depth,p):
    box(name+' pan',(x,y,z),(width,depth,.035),p['dark'],.004)
    for k in range(5):box(name+' grip rib',(x,y-depth*.35+k*depth*.175,z+.021),(width*.85,.009,.009),p['steel'],.001)


def forklift():
    p=palette()
    # Unequal front drive and rear steering wheel sizes, with both tangency planes at zero.
    for x in [-.50,.50]:
        wheel('Front drive wheel',x,-.57,.341,.34,.24,p)
        wheel('Rear steering wheel',x,.79,.266,.265,.205,p)
    rod('Front axle',(-.54,-.57,.341),(.54,-.57,.341),.067,p['dark'],28)
    rod('Rear steering axle',(-.53,.79,.266),(.53,.79,.266),.053,p['dark'],28)
    box('Rear axle central chassis saddle',(0,.79,.34),(.20,.24,.21),p['dark'],.012)
    for x in [-.41,.41]:
        box('Chassis longitudinal rail',(x,.12,.43),(.12,1.73,.19),p['dark'],.009)
        box('Open side entry lower sill',(x,.10,.57),(.11,.83,.12),p['yellow'],.008)
        step('Operator side entry step',x*1.16,.03,.397,.22,.42,p)
    box('Front drive casing',(0,-.58,.47),(.76,.42,.27),p['dark'],.018)
    box('Rear body belly',(0,.71,.49),(.89,.64,.34),p['yellow'],.047)
    # Faceted cast counterweight with bumper and recessed tow socket.
    profile('Counterweight',0,.99,[(.43,.48),(1.12,.48),(1.19,.62),(1.13,1.02),(.91,1.15),(.44,1.10)],p['yellow'])
    box('Rear bumper',(0,1.16,.58),(.86,.085,.12),p['dark'],.022)
    box('Rear tow socket surround',(0,1.187,.63),(.18,.035,.12),p['steel'],.006)
    box('Tow socket dark recess',(0,1.209,.63),(.10,.014,.064),p['dark'],.004)
    cyl('Tow retaining vertical pin',(0,1.205,.69),.016,.13,p['steel'],verts=20)
    for x in [-.36,.36]:
        box('Rear unlit marker housing',(x,1.126,.91),(.15,.065,.085),p['dark'],.008)
        box('Rear unlit red marker',(x,1.164,.91),(.114,.012,.057),p['red'],.003)
    box('Engine top cover',(0,.72,1.065),(.91,.47,.09),p['yellow'],.024)
    box('Rear engine grille recessed baffle',(0,1.175,.80),(.64,.018,.17),p['dark'],.003,rot=(math.radians(8.53),0,0))
    for i in range(8):box('Rear engine grille slat',(-.28+i*.08,1.187,.80),(.026,.016,.149),p['yellow'],.002,rot=(math.radians(8.53),0,0))
    box('Operator floor',(0,-.01,.586),(.78,.87,.065),p['dark'],.008)
    box('Forward dash cowl',(0,-.415,.925),(.74,.22,.49),p['yellow'],.024)
    box('Blank dashboard',(0,-.333,1.117),(.46,.18,.035),p['face'],.007,rot=(math.radians(20),0,0))
    box('Seat floor mounting pedestal',(0,.24,.775),(.34,.32,.38),p['dark'],.015)
    seat('Operator seat',0,.24,1.035,p)
    steering('Operator steering',-.08,-.335,1.307,p,r=.16)
    for x in [-.19,.05]:box('Operator floor pedal',(x,-.22,.654),(.11,.14,.028),p['rubber'],.005,rot=(math.radians(18),0,0))
    box('Hydraulic lever console',(.31,-.07,1.03),(.16,.38,.13),p['dark'],.012)
    box('Hydraulic console floor support',(.31,.01,.79),(.10,.15,.36),p['dark'],.008)
    for i in range(3):lever('Hydraulic control',( .31,-.17+i*.09,1.03),(.31,-.21+i*.09,1.20),p)
    # Open canopy with side access and visible slatted overhead guard, not a filled cabin.
    for x in [-.43,.43]:
        beam('Front overhead-guard post',(x*.86,-.45,.72),(x,-.52,2.11),.062,.070,p['dark'],.005)
        beam('Rear overhead-guard post',(x,.71,1.00),(x,.70,2.11),.062,.070,p['dark'],.005)
        beam('Long overhead guard rail',(x,-.56,2.14),(x,.75,2.14),.075,.075,p['dark'],.006)
        rod('Entry grab lower return',(x*.92,-.485,1.03),(x*1.18,-.485,1.09),.016,p['steel'])
        rod('Entry grab handle',(x*1.18,-.485,1.09),(x*1.18,-.50,1.49),.016,p['steel'])
        rod('Entry grab upper return',(x*1.18,-.50,1.49),(x*.95,-.50,1.55),.016,p['steel'])
    for y in [-.54,.73]:box('Overhead cross frame',(0,y,2.14),(.92,.075,.075),p['dark'],.006)
    for x in [-.30,-.15,0,.15,.30]:box('Separated guard roof slat',(x,.10,2.155),(.052,1.22,.035),p['dark'],.003)
    for x in [-.37,.37]:lamp('Front worklight',(x,-.57,1.96),(.145,.10,.10),p)
    cyl('Beacon plinth',(.30,.62,2.195),.057,.060,p['dark'],verts=24)
    cyl('Unlit amber beacon',(.30,.62,2.265),.045,.10,p['amber'],verts=32,bevel=.013)
    # Two parallel open mast channels; separate inner running rails and lower carriage.
    for x in [-.31,.31]:
        box('Outer mast channel web',(x,-.815,1.22),(.095,.068,1.91),p['dark'],.005)
        for yy in [-.887,-.755]:box('Outer mast channel flange',(x,yy,1.22),(.128,.040,1.91),p['dark'],.004)
        box('Inner mast running rail',(x,-.932,1.28),(.072,.067,1.71),p['steel'],.003)
        for zz in [.58,1.88]:cyl('Mast guide roller',(x,-.887,zz),.049,.090,p['steel'],'X',24,.002)
        hydraulic('Mast tilt ram',(x,-.36,.46),(x,-.81,.73),p,r=.033)
    for zz in [.31,2.13]:box('Mast crossmember',(0,-.815,zz),(.73,.15,.09),p['dark'],.006)
    hydraulic('Mast lift cylinder',(0,-.815,.34),(0,-.815,1.97),p,r=.051,ratio=.75)
    box('Lift cylinder chain-sheave crosshead',(0,-.83,1.976),(.49,.105,.065),p['dark'],.006)
    for x in [-.17,.17]:
        # Repeated short linked plates convey stationary lift chains, not a textured strip.
        for j in range(27):
            zz=.73+j*.044;box('Static mast chain plate',(x,-.938,zz),(.020,.014,.032),p['steel'],.002)
            cyl('Static mast chain pin',(x,-.942,zz+.011),.005,.030,p['dark'],'X',12,0)
        cyl('Chain return sheave',(x,-.86,1.954),.057,.031,p['dark'],'X',24,.003)
    box('Fork carriage upper beam',(0,-1.012,.80),(.91,.11,.093),p['dark'],.006)
    box('Fork carriage lower beam',(0,-1.015,.38),(.86,.105,.071),p['dark'],.005)
    for x in [-.40,.40]:box('Carriage outer vertical',(x,-1.015,.60),(.069,.10,.43),p['dark'],.004)
    for x in [-.35,-.175,0,.175,.35]:box('Load backrest vertical',(x,-1.02,1.095),(.038,.045,.64),p['dark'],.003)
    for zz in [.81,1.41]:box('Load backrest crossbar',(0,-1.02,zz),(.89,.045,.047),p['dark'],.003)
    for x in [-.26,.26]:
        profile('Forged L-shaped fork',x,.115,[(-1.085,.84),(-1.15,.84),(-1.15,.222),(-2.27,.192),(-2.34,.159),(-1.085,.159)],p['steel'],bevel=.005)
        box('Fork upper mounting hook',(x,-1.068,.82),(.15,.11,.08),p['dark'],.004)
        bolt('Fork position lock',(x,-1.07,.8615),p,'Z',.012)
    box('Carriage hose junction',(.10,-.95,.862),(.07,.075,.11),p['dark'],.007)
    cable('Lift hose loop',[(.09,-.77,.53),(.12,-.72,1.0),(.13,-.73,1.76),(.13,-.82,1.94),(.10,-.94,1.76),(.10,-.95,.90)],.012,p['rubber'])
    return ('city-counterbalance-forklift','カウンターバランス式フォークリフト','Counterbalance forklift','物流倉庫や街の荷さばき場に配置する着座式フォークリフト。一式に前後で径の異なる四輪、車軸と底部フレーム、後部カウンターウェイト、両側乗降ステップ、座席・操舵輪・ペダルと操作レバー、隙間のある頭上ガードを造形しています。二本の開いたマスト溝、ガイドローラー、静止チェーン、昇降・傾斜シリンダー、荷受けバックレストと低位置の二本のL字フォークを備え、荷物は含みません。全体で一モデル。駆動・昇降・油圧動作、可動リグ、内部エンジン、実機性能・安全性の検証はありません。','A seated counterbalance forklift for warehouse yards and urban loading areas. Includes four differently sized front/rear wheels, axles and underside frame, rear counterweight, open entry steps on both sides, seat, steering wheel, pedals and control levers, and a slatted overhead guard. Twin open mast channels, guide rollers, stationary chain detail, lift and tilt cylinders, load backrest and two low-position L-shaped forks are modeled without cargo. The whole assembly counts as one model. No drive, lifting or hydraulic behavior, articulation rig, internal engine, real-machine performance or safety validation is included.',['utility-vehicle','forklift','warehouse','loading-yard','フォークリフト'])


def capsule_points(length,r,zc,steps=20):
    pts=[]
    for cy,start in [(length/2,-90),(-length/2,90)]:
        for i in range(steps+1):
            a=math.radians(start+180*i/steps);pts.append((cy+r*math.cos(a),zc+r*math.sin(a)))
    return pts

def track(name,x,p):
    outer=capsule_points(1.36,.30,.335);inner=capsule_points(1.36,.238,.335);n=len(outer);w=.30
    vs=[(xx,y,z) for xx in [x-w/2,x+w/2] for pts in [outer,inner] for y,z in pts];fs=[]
    for i in range(n):
        j=(i+1)%n;fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    mesh(name+' closed rubber belt',vs,fs,p['rubber'])
    # Straight runs and semicircle ends have the same shoe pitch, with a small visible gap.
    for z,sign in [(.02,-1),(.65,1)]:
        for i in range(13):box(name+' straight-run track shoe',(x,-.62+i*.10333,z),(.338,.083,.04),p['rubber'],.004)
    for cy,start in [(.68,-90),(-.68,90)]:
        for i in range(10):
            a=math.radians(start+9+18*i)
            box(name+' curved-end track shoe',(x,cy+.312*math.cos(a),.335+.312*math.sin(a)),(.338,.080,.04),p['rubber'],.004,rot=(a-math.pi/2,0,0))
    for y in [-.68,.68]:
        cyl(name+' end drive wheel',(x,y,.335),.223,.242,p['dark'],'X',36,.005)
        for s in [-1,1]:
            cyl(name+' end hub',(x+s*.126,y,.335),.102,.028,p['steel'],'X',28,.003)
            bolt(name+' end axle lock',(x+s*.144,y,.335),p,'X',.023,s)
    for y in [-.37,0,.37]:cyl(name+' lower carrier roller',(x,y,.234),.154,.234,p['dark'],'X',28,.004)
    box(name+' roller support beam',(x,0,.40),(.18,1.28,.16),p['dark'],.012)
    for y in [-.37,0,.37]:pin(name+' small roller axle',x,y,.234,.28,p,.025)

def excavator():
    p=palette()
    for x in [-.60,.60]:track('Crawler track',x,p)
    for y in [-.47,.43]:box('Crawler transverse frame',(0,y,.49),(1.19,.20,.18),p['dark'],.012)
    box('Central lower chassis',(0,.02,.53),(.75,1.40,.18),p['dark'],.025)
    cyl('Slewing lower bearing',(0,.07,.635),.44,.12,p['steel'],verts=48,bevel=.008)
    cyl('Slewing ring outer cover',(0,.07,.70),.49,.08,p['dark'],verts=48,bevel=.007)
    box('Upper rotating floor',(0,.02,.78),(1.22,1.57,.14),p['orange'],.024)
    for x in [-.52,.52]:
        box('Cab step attachment bracket',(x,.05,.765),(.08,.25,.08),p['dark'],.005)
        step('Cab access step',x,.05,.725,.23,.44,p)
    profile('Rear counterweight cover',0,1.22,[(.32,.82),(.90,.82),(.98,.98),(.91,1.31),(.70,1.42),(.32,1.39)],p['orange'],bevel=.025)
    box('Engine top lid',(.25,.53,1.403),(.58,.53,.055),p['dark'],.025)
    box('Rear grille recess',(0,.961,1.123),(.78,.016,.26),p['dark'],.005,rot=(math.radians(11.98),0,0))
    for i in range(8):box('Rear grille separate slat',(-.34+i*.097,.975,1.123),(.037,.020,.225),p['orange'],.003,rot=(math.radians(11.98),0,0))
    for x in [-.51,.51]:lamp('Rear inactive lamp',(x,.932,1.26),(.12,.08,.09),p,sign=1)
    box('Rear bumper',(0,.97,.92),(.95,.075,.09),p['dark'],.018)
    cyl('Closed filler cap',(.43,.53,1.448),.043,.035,p['dark'],verts=24)
    # Open left operator station, with forward pedal room and independent right boom mount.
    seat('Operator seat',-.30,.20,1.10,p,width=.40)
    box('Operator foot deck',(-.31,-.37,.88),(.59,.52,.035),p['dark'],.005)
    for x in [-.43,-.18]:box('Travel pedal',(x,-.46,.925),(.12,.17,.027),p['rubber'],.005,rot=(math.radians(14),0,0));lever('Travel control',(x,-.40,.93),(x,-.38,1.19),p)
    for x in [-.57,-.03]:
        box('Side console floor mounting stem',(x,.09,.935),(.07,.16,.20),p['dark'],.008)
        box('Side control console',(x,.02,1.105),(.12,.34,.20),p['dark'],.016)
        lever('Excavator joystick',(x,-.03,1.199),(x,-.04,1.34),p)
    for x in [-.61,.02]:
        for y in [-.45,.62]:beam('Open canopy pillar',(x,y,.83),(x,y,2.27),.047,.055,p['dark'],.004)
    box('Canopy roof',(-.295,.085,2.315),(.81,1.26,.095),p['dark'],.035)
    for y in [-.47,.64]:box('Canopy crossrail',(-.295,y,2.25),(.69,.055,.067),p['dark'],.004)
    rod('Left entry grab lower return',(-.61,-.45,1.08),(-.70,-.45,1.16),.018,p['steel'])
    rod('Left entrance grab handle',(-.70,-.45,1.16),(-.70,-.45,1.58),.018,p['steel'])
    rod('Left entry grab upper return',(-.70,-.45,1.58),(-.61,-.45,1.66),.018,p['steel'])
    box('Canopy worklight mounting tab',(-.29,-.535,2.258),(.06,.06,.065),p['dark'],.003)
    lamp('Canopy worklight',(-.29,-.57,2.21),(.17,.085,.10),p)
    # Front dozer blade stays above track contact plane, connected to chassis by two arms.
    for x in [-.46,.46]:
        beam('Blade push arm',(x,-.32,.46),(x,-1.15,.29),.10,.12,p['dark'],.006)
        pin('Blade arm hinge',x,-.32,.46,.18,p,.039)
    profile('Dozer blade',0,1.46,[(-1.17,.15),(-1.31,.20),(-1.33,.46),(-1.22,.53),(-1.19,.45)],p['orange'],bevel=.008)
    box('Dozer blade cutting edge',(0,-1.284,.167),(1.48,.072,.049),p['steel'],.004)
    for xx in [.005,.115]:profile('Blade cylinder clevis ear',xx,.028,[(-1.24,.29),(-1.24,.44),(-1.10,.42),(-1.10,.32)],p['orange'],bevel=.003)
    hydraulic('Blade raise ram',(.06,-.42,.62),(.06,-1.14,.37),p,r=.039)
    # Offset swing bracket and a curved/tapered boom. All joints have actual cross-pins.
    cyl('Boom swing pivot',(.29,-.67,.97),.11,.36,p['dark'],verts=32)
    for x in [.14,.44]:profile('Boom root cheek',x,.055,[(-.83,.86),(-.49,.86),(-.50,1.14),(-.73,1.18)],p['orange'],bevel=.007)
    profile('Main tapered boom',.29,.225,[(-.72,1.01),(-.89,1.35),(-1.05,1.98),(-1.23,2.23),(-1.37,2.21),(-1.28,1.91),(-1.10,1.26),(-.86,.94)],p['orange'],bevel=.012)
    pin('Boom foot',.29,-.73,1.04,.43,p,.052)
    pin('Boom upper articulation',.29,-1.28,2.18,.35,p,.047)
    profile('Tapered dipper stick',.29,.19,[(-1.19,2.18),(-1.36,2.23),(-1.72,1.39),(-2.10,.83),(-1.96,.74),(-1.55,1.32)],p['orange'],bevel=.009)
    pin('Bucket main hinge',.29,-2.025,.82,.34,p,.045)
    hydraulic('Boom lift ram',(.29,-.84,.97),(.29,-1.10,1.79),p,r=.057,ratio=.59)
    hydraulic('Dipper positioning ram',(.29,-1.02,1.75),(.29,-1.62,1.55),p,r=.047,ratio=.60)
    hydraulic('Bucket curl ram',(.29,-1.40,2.10),(.29,-1.91,1.12),p,r=.038,ratio=.62)
    # Twin curl bell cranks and a short link do not intersect the bucket mouth.
    for xx in [.15,.43]:
        link('Bucket bell crank',xx,(-1.91,1.12),(-1.95,.89),.065,.035,p['dark'])
        link('Bucket coupling link',xx,(-1.91,1.12),(-2.19,.87),.060,.035,p['dark'])
    pin('Curl linkage hinge',.29,-1.91,1.12,.39,p,.032)
    pin('Bucket rear lug hinge',.29,-2.19,.87,.39,p,.032)
    # Open scoop: thick belly strip, two closed cheek plates, lip and four teeth.
    curve=[(-2.00,.91),(-2.08,.48),(-2.29,.25),(-2.61,.22)]
    outer=[(-1.96,.91),(-2.04,.45),(-2.27,.20),(-2.63,.17)]
    profile('Bucket curved floor',.29,.52,curve+list(reversed(outer)),p['dark'],bevel=.003)
    cheek=[(-2.00,.91),(-2.08,.48),(-2.29,.25),(-2.61,.22),(-2.39,.62),(-2.16,.90)]
    for xx in [.015,.565]:profile('Bucket side cheek',xx,.035,cheek,p['dark'],bevel=.005)
    box('Bucket cutting lip',(.29,-2.60,.205),(.60,.09,.055),p['steel'],.004)
    for xx in [.065,.215,.365,.515]:profile('Bucket tooth',xx,.073,[(-2.58,.235),(-2.76,.195),(-2.78,.159),(-2.58,.178)],p['steel'],bevel=.003)
    for xx in [.17,.41]:profile('Bucket rear hinge lug',xx,.042,[(-2.25,.77),(-2.26,.91),(-2.11,.95),(-2.06,.82)],p['orange'],bevel=.004)
    box('Boom hose manifold exterior',(.29,-.50,.90),(.23,.13,.14),p['dark'],.008)
    for x in [.21,.37]:
        cable('Boom hydraulic hose',[(x,-.48,.95),(x,-.57,1.23),(x,-.85,1.54),(x,-1.01,1.99),(x,-1.25,2.30),(x,-1.42,2.09),(x,-1.67,1.43)],.010,p['rubber'])
    return ('city-tracked-mini-excavator','履帯式ミニショベル','Tracked mini excavator','街の小規模工事や整備ヤード向けの履帯式ミニショベル。左右の閉じたゴム履帯、個別の踏板、端部車輪と下部ローラー、横梁、旋回リング、後部カウンターウェイトを持つ上部車体を備えます。左の開放式運転席には乗降ステップ、座席、ペダル、操作レバーとキャノピーを設け、右寄りのブーム・アームをピン、油圧シリンダー外装、ホース、バケットリンクでつないでいます。内側が空いたバケットと四つの爪、前方の押土板を含む一体のモデル。土砂や人物、履帯駆動・旋回・掘削・油圧動作、内部機構、実機性能・安全性の検証は含みません。','A tracked mini excavator for small urban worksites and maintenance yards. Two closed rubber crawler belts carry individual shoes, end wheels and lower rollers around a crossmember chassis and slewing ring. The upper body has a rear counterweight and an open left operator station with entry steps, seat, pedals, joysticks and canopy. An offset boom and dipper are joined by visible pins, exterior hydraulic cylinders, hoses and bucket linkage. An open scoop with four teeth and a front dozer blade are included as one complete model. No soil, people, crawler drive, slewing, digging or hydraulic behavior, internal mechanism, real-machine performance or safety validation is included.',['utility-vehicle','mini-excavator','crawler','construction','ミニショベル'])


def roller():
    p=palette()
    # Two full-width smooth steel drums, with actual end faces and mounted axle centers.
    for y in [-.84,.84]:
        cyl('Smooth compaction drum',(0,y,.40),.40,1.02,p['steel'],'X',64,.013)
        for s in [-1,1]:
            cyl('Recessed drum end face',(s*.515,y,.40),.325,.026,p['dark'],'X',48,.005)
            cyl('Drum final-drive boss',(s*.538,y,.40),.127,.059,p['yellow'],'X',32,.005)
            cyl('Drum axle end',(s*.578,y,.40),.056,.045,p['steel'],'X',24,.003)
            for i in range(6):
                a=math.tau*i/6;bolt('Drum hub fastener',(s*.569,y+.092*math.cos(a),.40+.092*math.sin(a)),p,'X',.010,s)
            profile('Drum support cheek',s*.605,.059,[(y-.25,.37),(y+.25,.37),(y+.27,.69),(y+.13,.83),(y-.19,.80)],p['yellow'],bevel=.016)
            pin('Drum axle retention',s*.605,y,.40,.12,p,.039)
        box('Drum top support crossbeam',(0,y,.823),(1.24,.23,.11),p['yellow'],.012)
        for yy in [y-.35,y+.35]:
            box('Drum scraper blade',(0,yy,.606),(1.04,.032,.075),p['dark'],.004,rot=(math.radians(-25 if yy<y else 25),0,0))
            for xx in [-.40,.40]:beam('Scraper mounting arm',(xx,y,.82),(xx,yy,.64),.033,.034,p['dark'])
        rod('Drum spray bar',(-.48,y-.25,.763),(.48,y-.25,.763),.020,p['dark'],24)
        for xx in [-.42,.42]:beam('Spray bar mounting bracket',(xx,y,.84),(xx,y-.25,.763),.025,.025,p['dark'],.002)
        for x in [-.36,-.18,0,.18,.36]:cyl('Stationary spray nozzle',(x,y-.25,.736),.012,.029,p['steel'],verts=16)
    # Distinct articulated front power hood and rear driver half.
    for yy in [-.64,.64]:box('Half chassis belly',(0,yy,.69),(1.00,.91,.19),p['dark'],.025)
    cyl('Central vertical steering articulation',(0,0,.68),.105,.43,p['steel'],verts=32,bevel=.006)
    for z in [.52,.84]:box('Articulation clevis fork',(0,.01,z),(.37,.39,.055),p['yellow'],.009)
    rod('Central oscillation pin',(-.21,0,.68),(.21,0,.68),.066,p['dark'],28)
    hydraulic('Articulation steering ram',(-.32,.32,.68),(-.28,-.33,.68),p,r=.036)
    profile('Front tapered engine hood',0,.92,[(-1.19,.88),(-1.19,1.16),(-.97,1.31),(-.28,1.31),(-.20,1.16),(-.20,.88)],p['yellow'],bevel=.026)
    box('Front hood service-panel gasket',(0,-.70,1.315),(.76,.67,.016),p['dark'],.006)
    box('Front hood top service panel',(0,-.70,1.332),(.77,.68,.037),p['yellow'],.020)
    for x in [-.34,.34]:bolt('Engine lid bolt',(x,-.95,1.352),p,'Z',.011)
    for s in [-1,1]:
        box('Engine side recessed vent',(s*.469,-.69,1.112),(.018,.60,.18),p['dark'],.005)
        for i in range(6):box('Engine side separate vent louver',(s*.487,-.94+i*.10,1.111),(.023,.044,.155),p['yellow'],.003)
        lamp('Front unlit lamp',(s*.36,-1.208,1.105),(.16,.075,.105),p)
    box('Front lower bumper',(0,-1.205,.882),(.88,.087,.105),p['dark'],.015)
    box('Operator rear deck',(0,.67,.89),(1.04,.94,.075),p['dark'],.008)
    for x in [-.60,.60]:
        step('Operator side lower step',x,.45,.52,.24,.42,p)
        step('Operator side upper step',x*.87,.45,.725,.18,.39,p)
        beam('Entry step bracket',(x*.88,.45,.72),(x,.45,.51),.055,.075,p['yellow'],.004)
    box('Rear water tank',(0,.99,1.05),(1.00,.30,.31),p['yellow'],.031)
    cyl('Water filler cap',(.33,.99,1.225),.058,.047,p['dark'],verts=28,bevel=.005)
    box('Roller seat floor mounting plinth',(0,.70,.954),(.36,.34,.07),p['dark'],.008)
    seat('Roller operator seat',0,.70,1.23,p,width=.43)
    box('Steering pedestal',(0,.20,1.09),(.39,.27,.39),p['yellow'],.022)
    box('Blank roller console',(0,.165,1.309),(.37,.23,.037),p['face'],.008,rot=(math.radians(16),0,0))
    steering('Roller steering',0,.22,1.46,p,.145)
    box('Travel-selector mounting stem',(.37,.49,.997),(.07,.10,.14),p['dark'],.006)
    box('Travel-selector console',(.37,.49,1.115),(.15,.22,.12),p['dark'],.010)
    lever('Travel selector',(.37,.49,1.14),(.37,.43,1.39),p)
    box('Foot pedal',(0,.33,.954),(.15,.17,.028),p['rubber'],.006,rot=(math.radians(16),0,0))
    # Open rear protective hoop, not a modeled safety rating or occupied vehicle.
    for x in [-.47,.47]:
        beam('Rear open roll hoop upright',(x,.94,1.17),(x,.92,2.30),.075,.079,p['dark'],.007)
        box('Roll hoop foot mounting plate',(x,.94,1.187),(.16,.20,.035),p['steel'],.006)
        for yy in [.88,1.00]:bolt('Roll hoop mounting bolt',(x,yy,1.2065),p,'Z',.014)
        rod('Entry grab upright',(x,.23,.925),(x,.27,1.42),.019,p['steel'])
    box('Rear open roll hoop crossbar',(0,.92,2.32),(1.02,.079,.08),p['dark'],.007)
    cyl('Rear unlit beacon base',(.34,.92,2.38),.052,.050,p['dark'],verts=24)
    cyl('Rear unlit amber beacon',(.34,.92,2.45),.043,.09,p['amber'],verts=28,bevel=.010)
    for x in [-.39,.39]:box('Rear unlit red marker',(x,1.146,1.06),(.11,.021,.072),p['red'],.005)
    for x in [-.12,.12]:cable('Articulation hydraulic hose',[(x,.28,.775),(x,.13,.91),(x,-.12,.91),(x,-.28,.79)],.014,p['rubber'])
    cable('Front drum spray feed',[(.40,-.35,1.02),(.44,-.46,.90),(.44,-.69,.79),(.44,-1.09,.764)],.012,p['rubber'])
    cable('Rear drum spray feed',[(.43,1.00,1.06),(.45,.94,.88),(.45,.74,.79),(.45,.59,.764)],.012,p['rubber'])
    return ('city-tandem-road-roller','搭乗式タンデムロードローラー','Ride-on tandem road roller','街路舗装工事の景観に置く小型の搭乗式タンデムローラー。接地する二本の平滑鋼製ドラム、端面・駆動ボス・車軸支持板、スクレーパーと散水管を造形しています。前部エンジンフードと後部運転台は中央の屈折ピン、クレビス、操向シリンダー外装とホースでつながり、側面ステップ、座席、操舵輪、ペダル、後部水タンク、上部が開いたロールフープが見えます。全体で一モデル。運転者、走行・振動・散水・油圧動作、内部エンジン、実機性能や保護構造の安全性検証は含みません。','A compact ride-on tandem roller for urban street-paving scenes. Two grounded smooth steel drums include end faces, drive bosses, axle support cheeks, scraper blades and spray bars. The front engine hood and rear operator platform meet at a visible articulation pin, clevis, exterior steering cylinder and hose loops. Side entry steps, seat, steering wheel, pedal, rear water tank and open roll hoop remain legible. The whole assembly is one model. No driver, propulsion, vibration, water spraying or hydraulic behavior, internal engine, real-machine performance or protective-structure safety validation is included.',['utility-vehicle','road-roller','tandem','roadwork','ロードローラー'])


def scissor_lift():
    p=palette()
    for x in [-.385,.385]:
        for y in [-.65,.65]:wheel('Solid platform wheel',x,y,.192,.191,.143,p,tread=False)
    for y in [-.65,.65]:rod('Platform axle',(-.405,y,.192),(.405,y,.192),.037,p['dark'],24)
    box('Mobile chassis tray',(0,0,.32),(.69,1.70,.25),p['blue'],.025)
    box('Chassis top deck',(0,0,.463),(.72,1.69,.045),p['dark'],.006)
    for x in [-.357,.357]:
        box('Chassis service hatch',(x,0,.331),(.023,.91,.17),p['blue'],.007)
        for y in [-.39,.39]:bolt('Service hatch latch',(.370 if x>0 else -.370,y,.334),p,'X',.012,-1 if x<0 else 1)
        for j in range(6):box('Battery vent slot',(x*1.05,-.20+j*.08,.339),(.010,.039,.071),p['dark'],.001)
    box('Rear low control bezel',(.10,.865,.34),(.30,.025,.12),p['dark'],.008)
    cyl('Rear emergency stop',(.16,.89,.35),.025,.023,p['red'],'Y',24,.003)
    cyl('Closed charge connector',(-.03,.889,.33),.025,.021,p['face'],'Y',24,.002)
    # Scissor rails are geometrically open channels. One endpoint slides in each track.
    for x in [-.275,.275]:
        for z,direction in [(.51,1),(1.77,-1)]:
            box('Scissor sliding rail bottom',(x,0,z),(.105,1.51,.034),p['dark'],.004)
            for xx in [x-.046,x+.046]:box('Scissor sliding rail side',(xx,0,z+direction*.038),(.018,1.51,.067),p['dark'],.002)
    # Two linked stages, two lateral pairs; crossing links occupy different X planes.
    for side in [-1,1]:
        for stage in range(2):
            z0=.57+stage*.57;z1=z0+.57
            xa=side*.25;xb=side*.307
            link('Ascending scissor arm',xa,(-.66,z0),(.66,z1),.084,.038,p['blue'])
            link('Descending scissor arm',xb,(.66,z0),(-.66,z1),.084,.038,p['blue'])
            pin('Scissor center crossover',side*.278,0,(z0+z1)/2,.128,p,.031)
            for yy,zz in [(-.66,z0),(.66,z0),(-.66,z1),(.66,z1)]:
                # Stage junction hardware is emitted once to avoid duplicate coincident parts.
                if stage==1 and zz==z0:continue
                pin('Scissor endpoint hinge',side*.278,yy,zz,.135,p,.031)
        for zz in [.57,1.71]:cyl('Rail sliding roller',(side*.278,.66,zz),.043,.067,p['steel'],'X',24,.002)
    for y,z in [(-.66,.57),(-.66,1.14),(-.66,1.71),(.66,1.14)]:
        rod('Paired scissor cross axle',(-.30,y,z),(.30,y,z),.027,p['dark'],24)
    hydraulic('Main elevating cylinder',(0,.48,.51),(0,-.16,.925),p,r=.043,ratio=.60)
    box('Cylinder lower anchor',(0,.48,.492),(.15,.13,.09),p['dark'],.006)
    rod('Cylinder scissor pickup',(-.325,-.16,.925),(.325,-.16,.925),.035,p['dark'],24)
    cable('Elevating cylinder hose',[(.06,.55,.45),(.11,.33,.48),(.10,.15,.59),(.035,.18,.705)],.012,p['rubber'])
    # Fixed raised platform, short outrigging-free electric chassis, not a working lift.
    box('Platform underside frame',(0,0,1.785),(.83,1.89,.09),p['dark'],.009)
    box('Platform walking deck',(0,0,1.844),(.87,1.92,.047),p['steel'],.006)
    for x in [-.42,.42]:box('Platform side toe board',(x,0,1.932),(.025,1.92,.145),p['blue'],.003)
    box('Front toe board',(0,-.942,1.932),(.82,.025,.145),p['blue'],.003)
    # Rear toe board leaves the entry gate's threshold distinguishable.
    for x in [-.365,.365]:box('Rear fixed toe section',(x,.942,1.932),(.12,.025,.145),p['blue'],.003)
    for x in [-.42,.42]:
        for y in [-.94,0,.94]:rod('Platform guard post',(x,y,1.91),(x,y,2.88),.018,p['blue'])
        for z in [2.36,2.88]:rod('Side guard rail',(x,-.94,z),(x,.94,z),.018,p['blue'])
    for z in [2.36,2.88]:rod('Front guard rail',(-.42,-.94,z),(.42,-.94,z),.018,p['blue'])
    for x in [-.295,.295]:rod('Entry frame upright',(x,.94,1.91),(x,.94,2.88),.018,p['blue'])
    # A separately bounded closed rear gate with hinges, latch and a narrow genuine gap.
    for x in [-.269,.269]:rod('Closed access gate upright',(x,.949,2.01),(x,.949,2.855),.015,p['steel'])
    for z in [2.02,2.36,2.855]:rod('Closed access gate rail',(-.269,.949,z),(.269,.949,z),.015,p['steel'])
    for z in [2.10,2.70]:cyl('Access gate hinge',(.286,.949,z),.024,.083,p['dark'],verts=24)
    box('Access gate latch',(-.289,.969,2.51),(.078,.04,.034),p['dark'],.005)
    box('Gate toe board',(0,.949,1.947),(.538,.023,.117),p['blue'],.003)
    # Chassis-mounted access ladder stays below the elevated gate. It does not falsely
    # span the whole raised height as a rigid link that would prevent lowering.
    for x in [-.245,.245]:
        beam('Rear chassis ladder stile',(x,.91,.35),(x,.97,1.15),.038,.043,p['dark'],.004)
        beam('Rear ladder attachment',(x,.77,.42),(x,.925,.42),.042,.049,p['dark'],.004)
        gx=.295 if x>0 else -.295
        rod('Platform entry grab handle',(gx,1.01,1.89),(gx,1.01,2.33),.017,p['steel'])
        for zz in [2.03,2.30]:rod('Platform grab mounting return',(gx,.94,zz),(gx,1.01,zz),.017,p['steel'])
    for z in [.52,.81,1.10]:step('Rear chassis ladder rung',0,.91+(z-.35)*(.06/.80),z,.51,.13,p)
    box('Control box rail-drop bracket',(.42,-.73,2.755),(.035,.14,.25),p['dark'],.004)
    box('Platform control mount',(.28,-.73,2.64),(.26,.23,.077),p['dark'],.011)
    box('Blank platform control face',(.28,-.73,2.687),(.225,.20,.024),p['face'],.005)
    lever('Platform joystick',(.25,-.73,2.693),(.25,-.73,2.80),p)
    cyl('Platform stop button',(.35,-.74,2.710),.019,.028,p['red'],verts=20)
    cable('Platform control cable',[(.39,-.72,2.64),(.39,-.67,2.29),(.38,-.58,1.89),(.30,-.38,1.73),(.23,-.18,1.45),(.24,.12,1.18),(.21,-.12,.85),(.16,.20,.47)],.010,p['rubber'])
    return ('city-mobile-scissor-lift','移動式シザーリフト','Mobile scissor lift','屋内の天井設備保守や街の施設整備シーンに置く小型の移動式シザーリフト。四輪の低床車体、車軸、側面点検パネル、二段・左右一対の交差リンク、段間軸、中央ピン、スライドレールとローラー、斜めの昇降シリンダー外装を備えます。中間高さで固定した作業床にはつま先板、開放された手すり、後部の独立した閉扉ゲートとラッチ、乗降はしご、操作箱とケーブルを造形しています。上昇姿勢のため後部車体はしごとゲートの間には高さの差があります。建物固定式昇降機とは異なる移動車両の一式で一モデル。人物、走行・昇降・油圧動作、可動リグ、電気内部、荷重・実機性能・安全性の検証は含みません。','A compact mobile scissor lift for indoor overhead-maintenance and civic-facility scenes. The low four-wheel chassis includes axles and side service panels. Two stacked scissor stages on paired sides have separate crossing links, inter-stage shafts, center pins, sliding rails and rollers, and an angled exterior lifting cylinder. A platform fixed at an intermediate height includes toe boards, open guardrails, a distinct closed rear entry gate with latch, access ladder, control box and cable. The rear chassis ladder remains below the gate in this raised display pose. This is one complete mobile vehicle, distinct from a building-fixed lift. No people, driving, elevation or hydraulic behavior, articulation rig, internal electrics, load, real-machine performance or safety validation is included.',['utility-vehicle','scissor-lift','mobile-platform','maintenance','シザーリフト'])

BUILDERS=[forklift,excavator,roller,scissor_lift]
IDS=['city-counterbalance-forklift','city-tracked-mini-excavator','city-tandem-road-roller','city-mobile-scissor-lift']
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-035/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.geometry_only:common.render=lambda *args,**kwargs:None
    out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    for fn,id in zip(BUILDERS,IDS):
        if args.only and args.only!=id:continue
        reset();spec=fn();publish_asset(*spec,out,'scripts/city_expansion/compact_utility_vehicles.py',azimuth=-55,elevation=24)
