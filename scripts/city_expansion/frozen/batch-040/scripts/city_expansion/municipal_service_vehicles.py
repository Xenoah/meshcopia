"""Four original municipal-service vehicles for Xenoah / Meshcopia, CC BY 4.0.
Self-contained recipe plus immutable common.py. No imported meshes or branding.
Authoring metres / Z-up, front -Y; exported metres / Y-up by common.
Static visual assemblies only, not engineered vehicles or safety-rated machinery.
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import reset, mat, mesh, torus, tube, publish_asset, ROOT


def box(name,loc,size,material,bevel=.008,rot=None):
    o=common.box(name,loc,size,material,bevel,rot)
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=1
    return o


def cyl(name,loc,r,depth,material,axis='Z',n=32,bevel=.002):
    o=common.cylinder(name,loc,r,depth,material,n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=1
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def rod(name,a,b,r,material,n=20):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,r,(b-a).length,material,n=n,bevel=min(.001,r*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def beam(name,a,b,w,d,material,bevel=.003):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,d,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def profile(name,x,depth,points,material,bevel=.003):
    n=len(points);vs=[(xx,y,z) for xx in [x-depth/2,x+depth/2] for y,z in points]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,vs,fs,material,bevel)
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=1
    return o


def pipe(name,points,r,material):
    # Rounded, densely sampled route with closed ends, distinct from a free-floating curve.
    ps=[Vector(v) for v in points];qs=[ps[0],*ps,ps[-1]];out=[]
    for j in range(1,len(qs)-2):
        a,b,c,d=qs[j-1:j+3]
        for k in range(6):
            t=k/6;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(ps[-1]);return tube(name,out,r,material,1)


def palette(body,label):
    return dict(body=mat(label,body,.28,.42),dark=mat('Graphite chassis steel',(.040,.052,.060),.52,.45),
                steel=mat('Satin zinc and machined hardware',(.49,.55,.57),.82,.33),
                chrome=mat('Polished piston rods',(.64,.70,.72),.90,.23),
                rubber=mat('Charcoal tire and flexible skirt',(.022,.028,.030),0,.81),
                seat=mat('Charcoal padded seat',(.061,.072,.078),0,.77),
                glass=mat('Opaque blue grey glazing appearance',(.080,.155,.190),.27,.26),
                light=mat('Inactive opaque ivory lamp lenses',(.80,.84,.78),.10,.30),
                red=mat('Inactive red rear lenses',(.56,.041,.025),.10,.37),
                amber=mat('Inactive amber markers',(.87,.34,.030),.12,.37),
                bristle=mat('Coarse dark brush filaments',(.095,.102,.085),0,.90),
                floor=mat('Dark anti-slip deck coating',(.085,.100,.101),0,.85))


def fastener(name,pos,p,axis='X',sign=1,r=.011):
    cyl(name+' washer',pos,r*1.45,r*.30,p['steel'],axis,n=16,bevel=0)
    q=list(pos);q['XYZ'.index(axis)]+=sign*r*.48
    cyl(name+' hex head',q,r,r*.80,p['steel'],axis,n=6,bevel=.0007)


def pin(name,x,y,z,width,p,r=.030):
    cyl(name+' transverse pin',(x,y,z),r,width,p['steel'],'X',24)
    for s in [-1,1]:
        q=(x+s*(width/2+.003),y,z);cyl(name+' retaining disc',q,r*1.40,.013,p['dark'],'X',24,.001)
        fastener(name+' retaining bolt',(q[0]+s*.006,y,z),p,'X',s,r*.44)


def ram(name,a,b,p,r=.035,ratio=.60):
    a,b=Vector(a),Vector(b);v=b-a;u=v.normalized()
    rod(name+' barrel',a+u*.025,a+v*ratio,r,p['dark'],28)
    rod(name+' piston rod',a+v*(ratio-.04),b-u*.020,r*.46,p['chrome'],24)
    rod(name+' gland',a+v*(ratio-.02),a+v*(ratio+.025),r*1.12,p['steel'],24)
    for q in [a,b]:pin(name+' end eye',q.x,q.y,q.z,r*3.6,p,r*.65)


def wheel(name,x,y,r,w,p,aggressive=False):
    # Closed annular carcass with explicit sidewalls, shoulders and tread crown.
    z=r;seg=48;sections=[(-w*.5,r*.46),(-w*.5,r*.81),(-w*.39,r*.96),(-w*.28,r*.985),(w*.28,r*.985),(w*.39,r*.96),(w*.5,r*.81),(w*.5,r*.46)]
    vs=[(x+xx,y+rr*math.cos(i*math.tau/seg),z+rr*math.sin(i*math.tau/seg)) for xx,rr in sections for i in range(seg)]
    fs=[]
    for k in range(len(sections)):
        for i in range(seg):fs.append((k*seg+i,k*seg+(i+1)%seg,((k+1)%len(sections))*seg+(i+1)%seg,((k+1)%len(sections))*seg+i))
    mesh(name+' tire',vs,fs,p['rubber'],smooth=True)
    for i in range(32):
        a=math.tau*i/32
        if aggressive:
            for side in [-1,1]:
                o=box(name+' chevron tread lug',(x+side*w*.20,y+(r-.004)*math.cos(a),z+(r-.004)*math.sin(a)),(w*.49,r*.12,.015),p['rubber'],.002)
                o.rotation_euler=(a-math.pi/2,0,side*.28)
        else:box(name+' tread rib',(x,y+(r-.004)*math.cos(a),z+(r-.004)*math.sin(a)),(w*.76,r*.075,.012),p['rubber'],.002,rot=(a-math.pi/2,0,0))
    cyl(name+' steel wheel',(x,y,z),r*.47,w*.93,p['steel'],'X',40,.004)
    for s in [-1,1]:
        xx=x+s*w*.48;cyl(name+' inset disc',(xx,y,z),r*.34,.025,p['body'],'X',32,.003)
        cyl(name+' axle hub',(xx+s*.012,y,z),r*.14,.046,p['steel'],'X',24,.003)
        for j in range(5):
            a=j*math.tau/5;fastener(name+' wheel nut',(xx+s*.012,y+r*.24*math.cos(a),z+r*.24*math.sin(a)),p,sign=s,r=r*.031)


def step(name,x,y,z,w,d,p):
    box(name+' tread pan',(x,y,z),(w,d,.040),p['dark'],.005)
    for j in range(5):box(name+' anti-slip rib',(x,y-d*.36+j*d*.18,z+.025),(w*.85,.009,.008),p['steel'],.001)


def lamp(name,pos,size,p,color='light',axis='Y',sign=-1):
    box(name+' housing',pos,size,p['dark'],.010);q=list(pos);k='XYZ'.index(axis);q[k]+=sign*(size[k]/2+.002)
    dims=[s*.76 for s in size];dims[k]=.010;box(name+' opaque unlit lens',q,dims,p[color],.003)


def seat(name,x,y,z,width,p):
    box(name+' seat mounting',(x,y,z-.14),(width*.55,.27,.24),p['dark'],.012)
    box(name+' cushion',(x,y-.035,z),(width,.40,.11),p['seat'],.035)
    box(name+' back plate',(x,y+.16,z+.235),(width,.08,.43),p['dark'],.024,rot=(-.10,0,0))
    box(name+' back pad',(x,y+.115,z+.235),(width*.93,.065,.36),p['seat'],.025,rot=(-.10,0,0))


def steering(name,x,y,z,p,r=.145):
    a=Vector((x,y-.16,z-.28));b=Vector((x,y,z));rod(name+' inclined column',a,b,.027,p['dark'],24)
    torus(name+' rim',b,r,.014,p['rubber'],rotation=(.35,0,0),segments=32)
    for j in range(3):
        a=j*math.tau/3;end=b+Vector((r*math.cos(a),r*math.sin(a)*math.cos(.35),r*math.sin(a)*math.sin(.35)));rod(name+' spoke',b,end,.008,p['steel'])
    rod(name+' hub',b-Vector((0,-math.sin(.35),math.cos(.35)))*.02,b+Vector((0,-math.sin(.35),math.cos(.35)))*.025,.035,p['dark'],24)


def lever(name,a,b,p):
    rod(name+' lever stalk',a,b,.009,p['steel'])
    o=common.sphere(name+' grip',b,(.025,.025,.033),p['rubber'],20,12)
    # Tiny ergonomic grips use intentional faceted shading for stable exports.
    for face in o.data.polygons:face.use_smooth=False


def grille(name,x,y,z,w,h,p,sign=1,count=9):
    box(name+' recessed dark field',(x,y,z),(w,.026,h),p['dark'],.004)
    for j in range(count):box(name+' separate slat',(x-w*.44+j*w*.88/(count-1),y+sign*.018,z),(.025,.018,h*.86),p['body'],.002)


def sweeper():
    p=palette((.12,.34,.31),'Municipal muted teal enamel')
    # Cab-over front wheel chassis, narrow road tires and lower service frame.
    for x in [-.53,.53]:
        for y in [-.79,.91]:wheel('Sweeper road wheel',x,y,.285,.19,p)
        box('Sweeper longitudinal chassis',(x*.72,.10,.36),(.095,2.30,.15),p['dark'],.009)
    for y in [-.79,.91]:
        rod('Sweeper axle',(-.56,y,.285),(.56,y,.285),.052,p['dark'],24)
        box('Sweeper axle suspension saddle',(0,y,.37),(.31,.20,.17),p['dark'],.010)
    box('Sweeper central belly cover',(0,.04,.405),(.79,1.96,.12),p['dark'],.013)
    # Solid-color opaque glazing is explicitly not transparent glass.
    profile('Cab lower forward nose',0,1.04,[(-1.16,.53),(-1.16,.89),(-1.02,1.04),(-.19,1.03),(-.19,.53)],p['body'],.022)
    profile('Cab opaque glazing volume',0,.99,[(-1.14,.99),(-.93,1.95),(-.23,1.95),(-.18,1.00)],p['glass'],.013)
    box('Cab chamfered rain roof',(0,-.59,2.012),(1.13,.97,.105),p['body'],.033)
    box('Front windscreen lower crossrail',(0,-1.137,1.023),(1.04,.055,.055),p['dark'],.005)
    box('Front windscreen upper crossrail',(0,-.935,1.941),(1.04,.055,.055),p['dark'],.005)
    for x in [-.514,.514]:
        beam('Cab windscreen pillar',(x,-1.145,1.015),(x,-.935,1.96),.048,.047,p['body'])
        beam('Cab rear pillar',(x,-.19,1.00),(x,-.23,1.965),.048,.047,p['body'])
        # Door border, rear hinges and pull distinguish the enclosed entry.
        beam('Door front lower frame',(x,-1.04,.57),(x,-1.03,1.03),.035,.037,p['dark'])
        beam('Door bottom frame',(x,-1.04,.57),(x,-.26,.57),.035,.037,p['dark'])
        beam('Door back edge',(x,-.26,.57),(x,-.26,1.91),.035,.037,p['dark'])
        box('Door waist strip',(x,-.64,1.023),(.029,.80,.042),p['body'],.003)
        for zz in [.75,1.53]:cyl('Door hinge',(x*1.045,-.25,zz),.018,.11,p['steel'],n=20)
        rod('Door handle mounting lower',(x,-.39,1.105),(x*1.11,-.39,1.105),.011,p['dark'])
        rod('Door pull',(x*1.11,-.39,1.105),(x*1.11,-.56,1.105),.014,p['dark'])
        rod('Door handle mounting upper',(x*1.11,-.56,1.105),(x,-.56,1.105),.011,p['dark'])
        step('Sweeper side entry',x*1.10,-.38,.455,.20,.46,p)
        box('Entry step chassis bracket',(x*.97,-.38,.472),(.11,.27,.08),p['dark'],.005)
        pipe('Mirror support',[(x,-.98,1.75),(x*1.28,-1.01,1.76),(x*1.31,-1.01,1.60)],.013,p['dark'])
        box('Mirror housing',(x*1.32,-1.01,1.61),(.10,.055,.18),p['dark'],.014)
        box('Opaque mirror face',(x*1.32,-.976,1.61),(.077,.008,.15),p['steel'],.004)
    beam('Windscreen wiper stem',(.24,-1.164,1.08),(-.02,-1.064,1.51),.017,.015,p['dark'])
    beam('Windscreen wiper blade',(-.19,-1.048,1.53),(.16,-1.048,1.53),.018,.025,p['rubber'])
    box('Sweeper front bumper',(0,-1.20,.56),(1.10,.12,.12),p['dark'],.021)
    for x in [-.37,.37]:lamp('Sweeper headlamp',(x,-1.166,.79),(.18,.075,.13),p)
    # Separate waste hopper sits on brackets rather than replacing the chassis.
    for x in [-.36,.36]:
        for y in [.25,.95]:box('Hopper mounting foot',(x,y,.515),(.14,.18,.18),p['dark'],.008)
    profile('Faceted waste hopper',0,1.13,[(.02,.57),(1.32,.57),(1.42,.89),(1.34,1.76),(.20,1.79),(.02,1.58)],p['body'],.025)
    box('Waste hopper roof lid',(0,.71,1.807),(1.11,1.10,.055),p['steel'],.018)
    box('Waste hatch rear gasket',(0,1.397,1.15),(.94,.033,.75),p['dark'],.014,rot=(.093,0,0))
    box('Waste hatch rear panel',(0,1.423,1.15),(.88,.037,.69),p['body'],.015,rot=(.093,0,0))
    for x in [-.39,.39]:
        cyl('Hopper hatch upper hinge',(x,1.376,1.55),.031,.15,p['steel'],'X',24)
        box('Hopper hatch lower latch',(x,1.455,.89),(.045,.031,.18),p['dark'],.005)
        fastener('Hopper latch pivot',(x,1.469,.93),p,'Y',1,.012)
        lamp('Sweeper rear lamp',(x,1.38,.65),(.17,.07,.105),p,'red',sign=1)
        box('Waste hopper side seam',(x*1.48,.69,1.20),(.016,1.08,.022),p['dark'],.002)
    grille('Rear hopper ventilation',0,1.445,1.18,.56,.25,p,count=8)
    box('Sweeper rear lower bumper',(0,1.424,.49),(.94,.13,.12),p['dark'],.018)
    for x in [-.31,.31]:beam('Sweeper rear bumper bracket',(x,1.15,.40),(x,1.43,.49),.065,.065,p['dark'])
    cyl('Water tank cap',(.40,.34,1.86),.053,.052,p['dark'],n=24,bevel=.004)
    # Two independently supported leading rotary brushes; dark real gaps between bristle bundles.
    for x in [-.58,.58]:
        beam('Brush lateral support',(x*.57,-.94,.44),(x,-1.31,.30),.052,.055,p['dark'])
        pin('Brush support pivot',x*.57,-.94,.44,.11,p,.025)
        cyl('Brush vertical spindle',(x,-1.31,.25),.037,.23,p['steel'],n=24)
        cyl('Brush drive housing',(x,-1.31,.32),.082,.11,p['dark'],n=28,bevel=.009)
        cyl('Brush backing disc',(x,-1.31,.159),.218,.035,p['steel'],n=48,bevel=.004)
        for j in range(38):
            a=j*math.tau/38
            beam('Individual brush bundle',(x+.185*math.cos(a),-1.31+.185*math.sin(a),.155),(x+.287*math.cos(a),-1.31+.287*math.sin(a),.043),.026,.032,p['bristle'],.001)
        pipe('Brush hydraulic hose',[(x*.56,-.84,.45),(x*.70,-1.02,.46),(x,-1.22,.39),(x,-1.31,.36)],.010,p['rubber'])
    box('Pickup suction nozzle',(0,-1.11,.205),(.73,.27,.12),p['dark'],.014)
    box('Pickup front flexible skirt',(0,-1.257,.151),(.69,.018,.12),p['rubber'],.004)
    for x in [-.34,.34]:box('Pickup skirt end',(x,-1.105,.151),(.022,.28,.12),p['rubber'],.003)
    for x in [-.24,.24]:beam('Pickup support',(x,-.90,.40),(x,-1.10,.23),.035,.035,p['steel'])
    pipe('Large suction conduit',[(0,-1.07,.235),(0,-.89,.35),(0,-.57,.37),(0,-.11,.42),(0,.19,.61)],.080,p['rubber'])
    for yy,zz in [(-.80,.36),(-.35,.39)]:cyl('Suction pipe band',(0,yy,zz),.087,.028,p['steel'],'Y',32)
    cyl('Amber beacon base',(.31,-.40,2.09),.060,.07,p['dark'],n=24)
    cyl('Amber beacon lens',(.31,-.40,2.175),.048,.12,p['amber'],n=32,bevel=.010)
    return ('city-compact-street-sweeper','小型道路清掃車','Compact street sweeper','歩道沿いや施設周辺の清掃シーンに置く小型道路清掃車。前方の二枚の円形ブラシと分離した毛束、支持腕、吸込ノズル・スカート・底部吸引管、密閉型前部キャブと左右の乗降段、独立した後部回収ホッパーを備えます。細い四輪、車軸、底部フレーム、後部ハッチとラッチ、鏡・ワイパー・非発光灯も造形。窓は不透明な青灰色の表現で、キャブ内装は省略。一式を1モデルと数えます。静止展示用で、走行・清掃・吸引・油圧動作、実機性能や安全性の検証はありません。','A compact street-sweeper prop for pavement edges and civic-facility maintenance scenes. Twin leading circular brushes have separated bristle bundles and support arms; the pickup nozzle, flexible skirts and underside suction conduit lead toward a separate rear waste hopper. A closed forward cab has side entry steps, opaque blue-grey glazing, mirrors and a wiper; its interior is omitted. Four narrow road wheels, axles, underside chassis, hopper hatch and latches, and inactive lamps complete one whole vehicle counted once. Static display only, without driving, sweeping, suction or hydraulic operation, real-machine performance or safety validation.',['municipal-service','street-sweeper','cleaning-vehicle','道路清掃車'])


def loader():
    p=palette((.73,.39,.055),'Warm loader ochre enamel')
    # Four large construction tires, open articulated waist and distinct front cradle.
    for x in [-.66,.66]:
        for y in [-.87,.99]:wheel('Loader traction wheel',x,y,.405,.30,p,True)
    for y in [-.87,.99]:
        rod('Loader axle',(-.69,y,.405),(.69,y,.405),.082,p['dark'],28)
        cyl('Differential cover',(0,y,.405),.15,.30,p['dark'],'X',32,.012)
    box('Loader rear chassis',(0,.80,.59),(1.00,1.41,.26),p['dark'],.030)
    box('Loader front chassis',(0,-.71,.55),(.86,1.03,.21),p['dark'],.018)
    for zz in [.49,.69]:box('Articulation clevis plate',(0,-.02,zz),(.39,.43,.065),p['body'],.009)
    cyl('Central vertical articulation pin',(0,-.035,.59),.075,.33,p['steel'],n=32,bevel=.004)
    ram('Exterior steering ram',(-.33,.27,.53),(-.33,-.40,.53),p,.027)
    for yy in [.27,-.40]:box('Steering ram chassis lug',(-.33,yy,.55),(.13,.14,.15),p['dark'],.005)
    # Rear hood and operator station are behind the lifting cradle.
    profile('Loader sloping engine hood',0,1.05,[(.70,.73),(1.56,.73),(1.58,.93),(1.42,1.24),(.81,1.30),(.66,1.18)],p['body'],.025)
    box('Loader rear bumper',(0,1.59,.69),(1.02,.14,.18),p['dark'],.023)
    grille('Loader rear grille',0,1.575,1.03,.71,.25,p,count=10)
    for x in [-.42,.42]:lamp('Loader rear lamp',(x,1.58,.82),(.14,.07,.09),p,'red',sign=1)
    box('Loader operator deck',(0,.28,.77),(.91,1.00,.075),p['dark'],.008)
    seat('Loader seat',0,.42,1.03,.45,p)
    box('Loader steering pedestal',(0,-.12,.945),(.50,.22,.33),p['body'],.020)
    box('Loader blank dash',(0,-.08,1.11),(.39,.20,.035),p['glass'],.007)
    steering('Loader steering',-.06,-.065,1.385,p,.15)
    for x in [-.16,.08]:box('Loader pedal',(x,.05,.84),(.11,.15,.03),p['rubber'],.005,rot=(.20,0,0))
    box('Loader right control support',(.32,.30,.91),(.12,.19,.25),p['dark'],.008)
    box('Loader joystick console',(.32,.23,1.10),(.17,.37,.13),p['dark'],.012)
    lever('Loader lift joystick',(.32,.13,1.16),(.32,.10,1.33),p)
    for x in [-.49,.49]:
        for y in [-.10,.76]:beam('Loader canopy pillar',(x,y,.76),(x,y,2.13),.055,.065,p['dark'],.005)
        beam('Loader canopy side rail',(x,-.20,2.13),(x,.86,2.13),.065,.065,p['dark'])
        box('Loader step support',(x,.18,.64),(.11,.42,.16),p['dark'],.006)
        step('Loader upper side step',x*1.15,.18,.66,.25,.42,p)
        step('Loader lower side step',x*1.24,.18,.43,.29,.42,p)
        for yy in [.02,.34]:beam('Loader step hanger',(x*1.18,yy,.44),(x*1.08,yy,.72),.033,.035,p['dark'])
        pipe('Loader entry handhold',[(x,-.10,1.07),(x*1.17,-.10,1.15),(x*1.17,-.10,1.64),(x,-.10,1.72)],.017,p['steel'])
    box('Loader canopy roof',(0,.33,2.19),(1.17,1.27,.10),p['body'],.035)
    for x in [-.42,.42]:lamp('Loader canopy worklamp',(x,-.23,2.08),(.15,.10,.11),p)
    cyl('Loader beacon mount',(.35,.70,2.28),.054,.075,p['dark'],n=24)
    cyl('Loader amber beacon',(.35,.70,2.36),.043,.105,p['amber'],n=28,bevel=.008)
    # Wheel fenders are separate short planks above the large tires.
    for x in [-.66,.66]:
        for y in [-.87,.99]:
            box('Loader wheel fender',(x,y,.866),(.39,.83,.045),p['body'],.013)
            for yy in [y-.24,y+.24]:beam('Loader fender bracket',(x*.68,yy,.60),(x,yy,.85),.035,.035,p['dark'])
    # Twin low lift arms form a loader, never an excavator boom/dipper.
    for x in [-.36,.36]:
        profile('Loader lift tower',x,.16,[(-.29,.58),(.11,.58),(.11,1.18),(-.09,1.24),(-.29,.98)],p['body'],.009)
        profile('Loader single lift arm',x,.15,[(.00,1.15),(-.31,1.23),(-.94,1.03),(-1.60,.62),(-1.61,.45),(-1.41,.46),(-.80,.83),(-.29,1.02),(.00,.98)],p['body'],.010)
        pin('Loader arm chassis pivot',x,-.005,1.075,.25,p,.050)
        pin('Loader arm bucket pivot',x,-1.53,.535,.25,p,.042)
        ram('Loader main lift ram',(x,-.36,.58),(x,-1.02,.91),p,.046)
        box('Loader lower ram clevis bracket',(x,-.36,.61),(.17,.20,.16),p['dark'],.005)
        pin('Loader ram arm pickup',x,-1.02,.91,.23,p,.032)
        pipe('Loader lift hose',[(x,.00,.75),(x,-.30,.74),(x,-.36,.62)],.012,p['rubber'])
    box('Loader arm transverse brace',(0,-.75,.94),(.83,.13,.12),p['body'],.007)
    # Central Z-bar tilt circuit, each pin backed by a cradle or connected link.
    box('Tilt ram rear anchor',(0,-.10,1.10),(.20,.19,.15),p['dark'],.008)
    ram('Loader bucket tilt ram',(0,-.10,1.15),(0,-.94,1.18),p,.044)
    beam('Tilt bellcrank',(0,-.94,1.18),(0,-1.17,.77),.10,.095,p['dark'],.005)
    pin('Tilt bellcrank fulcrum',0,-1.08,.93,.29,p,.037)
    box('Tilt bellcrank support',(0,-1.08,.91),(.51,.11,.10),p['body'],.006)
    beam('Bucket short tilt link',(0,-1.17,.77),(0,-1.55,.82),.075,.075,p['steel'],.004)
    for yy,zz in [(-1.17,.77),(-1.55,.82)]:pin('Bucket tilt link eye',0,yy,zz,.19,p,.029)
    # Broad open loading bucket: thick floor, curved-looking rear profile and cheeks.
    profile('Loader bucket curved back and floor',0,1.47,[(-1.51,.29),(-1.51,.79),(-1.58,.83),(-1.67,.74),(-1.72,.43),(-1.98,.24),(-2.36,.19),(-2.39,.13),(-1.94,.16),(-1.62,.24)],p['steel'],.006)
    for x in [-.735,.735]:profile('Loader bucket side cheek',x,.045,[(-1.52,.27),(-1.52,.80),(-1.64,.82),(-2.35,.20),(-2.36,.145),(-1.91,.17)],p['body'],.006)
    box('Loader bucket cutting edge',(0,-2.365,.173),(1.56,.11,.050),p['dark'],.006)
    for x in [-.52,-.26,0,.26,.52]:fastener('Bucket edge bolt',(x,-2.355,.205),p,'Z',1,.011)
    for x in [-.36,.36]:
        profile('Bucket lift attachment ear',x,.12,[(-1.57,.40),(-1.44,.40),(-1.41,.59),(-1.57,.67)],p['dark'],.005)
        box('Bucket rear vertical stiffener',(x,-1.487,.54),(.075,.065,.50),p['steel'],.005)
    profile('Bucket central tilt ear',0,.15,[(-1.59,.61),(-1.46,.62),(-1.46,.86),(-1.59,.86)],p['dark'],.005)
    return ('city-compact-wheel-loader','小型ホイールローダー','Compact wheel loader','建設区画や公園整備の資材置場に配置する小型ホイールローダー。太い四輪、前後分割車体と中央関節、オープンキャノピーの着座運転席、側面二段ステップを備えます。低い左右一対のリフトアーム、支持塔、昇降シリンダーと中央Zバー風チルトリンクが、空洞の幅広バケットと刃先へ接続。後部フード、グリル、車軸、フェンダー、底面部材も造形。掘削機のブームやフォークとは異なる一式1モデルです。荷物はなく、走行・関節・積込・油圧動作、荷重・実機性能・安全性は未検証。','A compact wheel-loader prop for construction compounds and park-maintenance material yards. Four large tires flank front and rear chassis halves with a central articulation joint. An open-canopy seated station has two-level side entry steps. Paired low lift arms, support towers, lift cylinders and a central Z-bar-style tilt linkage connect to a broad hollow bucket and cutting edge, distinct from an excavator boom or forks. Rear hood, grille, axles, fenders and underside members complete one whole assembly counted once. No cargo, driving, articulation, loading or hydraulic operation, load rating, real-machine performance or safety validation is supplied.',['municipal-service','wheel-loader','construction-vehicle','ホイールローダー'])


def capsule(length,r,zc,n=16):
    out=[]
    for cy,start in [(length/2,-math.pi/2),(-length/2,math.pi/2)]:
        for j in range(n+1):
            a=start+math.pi*j/n;out.append((cy+r*math.cos(a),zc+r*math.sin(a)))
    return out


def carrier_track(name,x,p):
    outer=capsule(1.10,.24,.263);inner=capsule(1.10,.19,.263);n=len(outer);w=.24
    vs=[(xx,y,z) for xx in [x-w/2,x+w/2] for pts in [outer,inner] for y,z in pts];fs=[]
    for i in range(n):
        j=(i+1)%n;fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    mesh(name+' continuous closed belt',vs,fs,p['rubber'])
    for z in [.018,.508]:
        for j in range(11):box(name+' straight tread shoe',(x,-.50+j*.1,z),(.27,.080,.036),p['rubber'],.003)
    for cy,start in [(.55,-math.pi/2),(-.55,math.pi/2)]:
        for j in range(9):
            a=start+(j+.5)*math.pi/9;box(name+' curved tread shoe',(x,cy+.245*math.cos(a),.263+.245*math.sin(a)),(.27,.078,.034),p['rubber'],.003,rot=(a-math.pi/2,0,0))
    for y in [-.55,.55]:
        cyl(name+' end drive idler',(x,y,.263),.18,.21,p['dark'],'X',32,.005)
        for s in [-1,1]:
            cyl(name+' end hub',(x+s*.115,y,.263),.080,.027,p['body'],'X',24,.003)
            fastener(name+' hub bolt',(x+s*.128,y,.263),p,sign=s,r=.020)
    for y in [-.30,0,.30]:
        cyl(name+' lower support roller',(x,y,.195),.128,.20,p['steel'],'X',24,.003)
        pin(name+' roller pin',x,y,.195,.25,p,.024)
    box(name+' suspension rail',(x,0,.34),(.15,1.09,.11),p['dark'],.008)


def tub(name,p):
    # Closed double-surface tapered tub, genuinely open above the continuous inner floor.
    # Four corner order: front-left, front-right, rear-right, rear-left.
    outer_bottom=[(-.35,-.82,.61),(.35,-.82,.61),(.35,.23,.61),(-.35,.23,.61)]
    outer_top=[(-.56,-1.15,1.17),(.56,-1.15,1.17),(.56,.48,1.17),(-.56,.48,1.17)]
    inner_top=[(-.516,-1.10,1.17),(.516,-1.10,1.17),(.516,.435,1.17),(-.516,.435,1.17)]
    inner_bottom=[(-.315,-.78,.66),(.315,-.78,.66),(.315,.195,.66),(-.315,.195,.66)]
    vs=outer_bottom+outer_top+inner_top+inner_bottom;fs=[(3,2,1,0),(12,13,14,15)]
    for i in range(4):
        j=(i+1)%4;fs += [(i,j,4+j,4+i),(4+i,4+j,8+j,8+i),(8+i,8+j,12+j,12+i)]
    o=mesh(name,vs,fs,p['body'],.006)
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=1
    for i in range(4):beam('Dumper rolled top rim',outer_top[i],outer_top[(i+1)%4],.045,.045,p['steel'],.005)
    for x in [-.43,.43]:
        for y in [-.66,.15]:beam('Dumper exterior side stiffener',(x*.81,y,.65),(x*1.26,y,1.13),.047,.040,p['body'])


def carrier():
    p=palette((.64,.19,.07),'Muted vermilion dumper enamel')
    for x in [-.43,.43]:carrier_track('Compact dumper track',x,p)
    for y in [-.48,.44]:box('Dumper track crossmember',(0,y,.39),(.91,.15,.14),p['dark'],.008)
    box('Dumper central chassis',(0,.02,.46),(.65,1.42,.16),p['dark'],.016)
    for x in [-.29,.29]:box('Dumper upper frame rail',(x,-.12,.55),(.075,1.58,.10),p['dark'],.005)
    tub('Open tapered tipping tub',p)
    # Static lowered tub: front hinge and underfloor ram stay visibly attached.
    for x in [-.27,.27]:
        profile('Dumper front hinge cradle',x,.11,[(-.92,.49),(-.70,.49),(-.75,.645),(-.88,.645)],p['dark'],.004)
        pin('Dumper tipping hinge',x,-.82,.60,.19,p,.029)
        box('Tub underside longitudinal rib',(x,-.29,.602),(.052,1.04,.055),p['steel'],.003)
    ram('Dumper underfloor tip ram',(0,.43,.48),(0,-.22,.615),p,.038)
    box('Dumper ram frame clevis',(0,.43,.49),(.19,.19,.16),p['dark'],.005)
    box('Dumper ram tub pickup',(0,-.22,.605),(.18,.15,.10),p['steel'],.005)
    # Rear engine module and rear standing access are unlike the seated loader.
    box('Dumper rear engine compartment',(0,.77,.73),(.74,.55,.55),p['body'],.035)
    box('Dumper rear service gasket',(0,1.055,.72),(.58,.020,.37),p['dark'],.006)
    box('Dumper service door',(0,1.073,.72),(.54,.021,.33),p['body'],.008)
    grille('Dumper rear cooling grille',0,1.092,.77,.40,.17,p,count=7)
    cyl('Dumper filler cap',(.22,.81,1.04),.042,.046,p['dark'],n=24)
    for x in [-.31,.31]:
        box('Rear standing platform cantilever',(x,.98,.43),(.075,.63,.08),p['dark'],.005)
        beam('Rear platform diagonal brace',(x,.70,.44),(x,1.23,.31),.037,.040,p['steel'])
    step('Rear standing operator platform',0,1.20,.345,.76,.39,p)
    for x in [-.34,.34]:
        beam('Operator station side upright',(x,.83,.92),(x,1.02,1.20),.034,.036,p['dark'])
        rod('Operator station side grip',(x,.99,1.18),(x,1.23,1.18),.019,p['rubber'])
    box('Dumper operator cross console',(0,1.005,1.175),(.72,.20,.11),p['dark'],.012)
    box('Dumper blank instrument field',(0,1.027,1.239),(.28,.13,.020),p['glass'],.004)
    for x in [-.23,.23]:lever('Dumper differential travel lever',(x,1.055,1.23),(x,1.13,1.40),p)
    lever('Dumper tipping lever',(.32,1.02,1.23),(.32,1.04,1.37),p)
    cyl('Dumper stop button',(-.02,1.08,1.26),.020,.034,p['red'],n=20)
    for x in [-.20,.20]:pipe('Dumper control conduit',[(x,1.02,1.17),(x,.91,1.06),(x,.90,.95)],.010,p['rubber'])
    for x in [-.26,.26]:lamp('Dumper front work lamp',(x,-.85,.48),(.12,.075,.085),p)
    for x in [-.30,.30]:lamp('Dumper rear inactive marker',(x,1.063,.55),(.10,.055,.065),p,'red',sign=1)
    return ('city-tracked-dump-carrier','クローラー式小型運搬車','Tracked dump carrier','狭い造園通路や補修工事の土砂運搬シーン向けクローラー式運搬車。二本の短い履帯に駆動輪・支持ローラー・靴板を備え、開口した厚肉の台形荷台には傾斜側壁、縁材、前部ダンプ軸と床下シリンダーを造形しています。後部原動機ケースに接続した立ち乗り足場、支持付き操作盤、走行・傾斜レバー、配管、冷却格子を備えた一式1モデル。荷台は下ろした固定姿勢で荷物は含みません。走行・ダンプ・油圧・積載動作、実機性能・荷重・安全性は未検証です。','A compact tracked dump-carrier prop for narrow landscaping paths and repair-work material scenes. Two short crawler belts include end wheels, carrier rollers and tread shoes. The genuinely open thick-walled tapered tub has sloped sides, rim rails, front tipping pivots and an underfloor cylinder. A rear engine case supports a rear standing platform, mounted control console, travel and tipping levers, conduits and cooling grille. The whole assembly counts once. Its tub is fixed in a lowered empty pose. Driving, dumping, hydraulic and load-handling operation, real-machine performance, load capacity and safety are unvalidated.',['municipal-service','tracked-dumper','landscaping','クローラー運搬車'])


def cart():
    p=palette((.26,.39,.20),'Muted olive utility-cart enamel')
    # Low narrow road chassis, open passenger bench and genuinely separate rear cargo box.
    for x in [-.57,.57]:
        for y in [-.91,1.02]:wheel('Utility cart road wheel',x,y,.265,.20,p)
        box('Cart longitudinal lower rail',(x*.72,.11,.34),(.075,2.51,.11),p['dark'],.007)
    for y in [-.91,1.02]:
        rod('Cart axle',(-.60,y,.265),(.60,y,.265),.044,p['dark'],24)
        for x in [-.39,.39]:
            box('Cart suspension block',(x,y,.34),(.12,.26,.13),p['dark'],.009)
            for k in range(3):box('Cart visible leaf spring',(x,y,.315+k*.012),(.043,.46-k*.05,.008),p['steel'],.001)
    cyl('Cart rear motor housing',(0,1.02,.29),.115,.35,p['dark'],'X',32,.005)
    box('Cart battery enclosure',(0,.10,.39),(.76,.80,.18),p['dark'],.018)
    box('Cart central foot floor',(0,-.38,.46),(1.02,1.16,.075),p['floor'],.014)
    for x in [-.56,.56]:
        step('Cart low open side sill',x,-.34,.431,.18,.76,p)
        box('Cart sill frame bracket',(x*.84,-.34,.43),(.15,.63,.08),p['dark'],.006)
    profile('Cart short sloping nose',0,1.03,[(-1.36,.49),(-1.36,.67),(-1.19,.86),(-.84,.86),(-.74,.53)],p['body'],.024)
    box('Cart front bumper',(0,-1.40,.45),(1.08,.13,.12),p['dark'],.025)
    for x in [-.37,.37]:lamp('Cart headlamp',(x,-1.345,.68),(.20,.07,.12),p)
    box('Cart front dark grille',(0,-1.382,.59),(.37,.018,.085),p['dark'],.006)
    for x in [-.15,-.075,0,.075,.15]:box('Cart grille vertical fin',(x,-1.397,.59),(.016,.012,.065),p['steel'],.001)
    # Seat and console are floor-supported; open side entries remain clear.
    box('Cart bench box base',(0,.20,.60),(.98,.51,.30),p['body'],.025)
    seat('Cart two-place bench',0,.20,.79,.96,p)
    for x in [-.52,.52]:
        rod('Cart bench arm rail',(x,.05,.99),(x,.42,.99),.022,p['dark'])
        for y in [.08,.38]:rod('Cart bench arm support',(x,y,.79),(x,y,.99),.017,p['dark'])
    box('Cart dashboard cowl',(0,-.73,.99),(.95,.19,.27),p['body'],.016)
    box('Cart blank dash insert',(-.22,-.621,1.045),(.37,.021,.13),p['glass'],.006)
    steering('Cart steering',-.24,-.51,1.16,p,.145)
    for x in [-.33,-.12]:box('Cart floor pedal',(x,-.59,.515),(.10,.14,.025),p['rubber'],.004,rot=(.18,0,0))
    lever('Cart parking lever',(.40,-.02,.64),(.40,-.08,.88),p)
    # Thin-pillared roof with an open front, not the sweeper's closed cab.
    for x in [-.50,.50]:
        beam('Cart front canopy post',(x,-.81,.83),(x,-.69,1.82),.036,.045,p['dark'])
        beam('Cart rear canopy post',(x,.47,.59),(x,.49,1.82),.043,.048,p['dark'])
        beam('Cart canopy upper side',(x,-.72,1.82),(x,.55,1.82),.043,.043,p['dark'])
        pipe('Cart passenger grab rail',[(x,-.78,1.09),(x*1.11,-.76,1.18),(x*1.11,-.74,1.50),(x,-.73,1.57)],.013,p['steel'])
    box('Cart light canopy roof',(0,-.08,1.871),(1.19,1.47,.085),p['body'],.030)
    # Lower wind deflector only, with open air above; opaque material declared.
    box('Cart low wind deflector',(0,-.795,1.15),(.92,.025,.22),p['glass'],.008,rot=(.12,0,0))
    for z in [1.045,1.255]:box('Cart deflector edge',(0,-.795,z),(.97,.038,.027),p['dark'],.003)
    # Cargo bed has a visible interior and ribbed floor, not a sealed solid.
    for x in [-.40,.40]:
        box('Cart cargo chassis riser',(x,1.02,.57),(.075,.96,.22),p['dark'],.008)
    box('Cart separate cargo bed floor',(0,1.01,.705),(1.16,1.18,.065),p['steel'],.008)
    for x in [-.57,.57]:
        box('Cart cargo side wall',(x,1.015,.89),(.035,1.19,.32),p['body'],.006)
        box('Cart cargo side top rail',(x,1.015,1.056),(.055,1.23,.041),p['steel'],.006)
        for y in [.50,.88,1.28,1.57]:box('Cart cargo side stake',(x*1.037,y,.89),(.034,.046,.32),p['dark'],.004)
    box('Cart cargo front bulkhead',(0,.43,.89),(1.13,.036,.32),p['body'],.006)
    box('Cart cargo front top rail',(0,.43,1.057),(1.17,.055,.041),p['steel'],.005)
    for x in [-.46,-.23,0,.23,.46]:box('Cart raised bed floor rib',(x,1.00,.743),(.029,1.07,.012),p['steel'],.002)
    box('Cart separate tailgate',(0,1.606,.89),(1.08,.032,.30),p['body'],.006)
    box('Cart tailgate upper rail',(0,1.606,1.052),(1.12,.05,.04),p['steel'],.005)
    for x in [-.34,.34]:
        cyl('Cart tailgate lower hinge',(x,1.629,.75),.025,.15,p['steel'],'X',24,.002)
        box('Cart tailgate vertical stiffener',(x,1.633,.90),(.044,.028,.26),p['body'],.004)
    for x in [-.51,.51]:
        box('Cart tailgate latch',(x,1.64,1.01),(.065,.033,.09),p['dark'],.004)
        fastener('Cart tailgate latch pivot',(x,1.656,1.015),p,'Y',1,.010)
        lamp('Cart rear red lamp',(x,1.598,.61),(.15,.07,.10),p,'red',sign=1)
    box('Cart rear lamp support fascia',(0,1.575,.651),(1.10,.09,.11),p['dark'],.008)
    box('Cart rear bumper',(0,1.66,.46),(1.05,.12,.11),p['dark'],.019)
    for x in [-.36,.36]:beam('Cart rear bumper chassis bracket',(x,1.30,.35),(x,1.66,.46),.060,.060,p['dark'])
    box('Cart tow receiver',(0,1.70,.40),(.14,.18,.08),p['dark'],.005)
    cyl('Cart tow pin',(0,1.75,.445),.013,.10,p['steel'],n=20)
    for x in [-.57,.57]:
        for y in [-.91,1.02]:
            box('Cart short wheel fender',(x,y,.58),(.27,.66,.04),p['body'],.010)
            beam('Cart fender mount',(x*.76,y,.40),(x,y,.56),.035,.035,p['dark'])
    return ('city-utility-cargo-cart','小型ユーティリティ運搬カート','Utility cargo cart','公園・キャンパス・施設構内の低速搬送シーンに置く汎用カート。低床四輪シャーシ、開いた両側乗降部、幅広ベンチ席、細い柱の屋根、操舵輪とペダル、座席後方の独立した開放荷台を備えます。荷台床リブ、側板、ヒンジ・ラッチ付き後部ゲート、車軸・板ばね表現・底部電動機ケース・灯火も造形。前の低い風除けは不透明な青灰色表現で、その上方と側面は開放。空荷の一式を1モデルと数え、走行・積載・開閉・電気動作、実機性能・荷重・安全性は未検証です。','A generic utility cargo cart for low-speed transport scenes in parks, campuses and facility grounds. A low four-wheel chassis has open side entries, a broad bench seat, thin-post canopy, steering wheel and pedals, and a separate open cargo bed behind the seat. The bed includes floor ribs, side boards and a distinct hinged/latching tailgate; axles, visible leaf-spring detail, underside motor casing and inactive lamps are modeled. The short front wind deflector is opaque blue-grey, with open air above and on both sides. This empty whole assembly counts once. Driving, load handling, gate movement, electrical function, real-machine performance, load capacity and safety are unvalidated.',['municipal-service','utility-cart','cargo-bed','構内運搬車'])


BUILDERS=[sweeper,loader,carrier,cart]
IDS=['city-compact-street-sweeper','city-compact-wheel-loader','city-tracked-dump-carrier','city-utility-cargo-cart']
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-040/assets');ap.add_argument('--only',default='');ap.add_argument('--geometry-only',action='store_true')
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if a.geometry_only:common.render=lambda *args,**kwargs:None
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    for fn,id in zip(BUILDERS,IDS):
        if a.only and a.only!=id:continue
        reset();spec=fn();publish_asset(*spec,out,'scripts/city_expansion/municipal_service_vehicles.py',azimuth=-55,elevation=25)
