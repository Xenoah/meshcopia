"""Original generic urban road vehicles for Xenoah / Meshcopia. CC BY 4.0.
Authoring: metres, Z-up, forward -Y. Immutable common.py exports metres/Y-up.
Original geometry only; no manufacturer references, logos, lettering or image textures.
Glazing is deliberately alpha-blended, not simulated refractive automotive glass.
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import reset, mat, mesh, tube, torus, publish_asset, ROOT

def box(name,loc,size,m=None,bevel=.012,rot=None):
    o=common.box(name,loc,size,m,bevel,rot)
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=2
    return o

def cyl(name,loc,r,d,m,axis='Z',n=32,bevel=.003):
    o=common.cylinder(name,loc,r,d,m,n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o

def rod(name,a,b,r,m,n=20):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,m,n=n,bevel=min(.002,r*.1));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def beam(name,a,b,w,d,m,bevel=.006):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,d,(b-a).length),m,bevel);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def prof(name,center,depth,pts,m,axis='X',bevel=.005):
    n=len(pts);vs=[(c,u,v) if axis=='X' else (u,c,v) for c in (center-depth/2,center+depth/2) for u,v in pts]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,m,bevel)

def curve(name,points,r,m):
    ps=[Vector(p) for p in points];q=[ps[0],*ps,ps[-1]];out=[]
    for j in range(1,len(q)-2):
        a,b,c,d=q[j-1:j+3]
        for k in range(9):
            t=k/9;out.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(ps[-1]);return tube(name,out,r,m,2)

def palette():
    p=dict(cream=mat('Warm ivory body paint',(.71,.76,.71),.25,.34),teal=mat('Deep muted teal paint',(.025,.27,.29),.28,.33),redpaint=mat('Brick red service vehicle paint',(.58,.045,.028),.26,.34),green=mat('Sage green municipal body paint',(.22,.39,.25),.24,.4),van=mat('Cool off white panel van paint',(.70,.76,.80),.24,.33),dark=mat('Graphite chassis and trim',(.029,.038,.043),.48,.44),rubber=mat('Charcoal tire and seal rubber',(.016,.020,.023),0,.82),steel=mat('Satin aluminium and plated steel',(.46,.53,.56),.8,.28),bright=mat('Polished metal detail',(.66,.71,.73),.88,.20),seat=mat('Blue grey seat upholstery',(.10,.18,.22),0,.80),floor=mat('Non slip dark interior floor',(.10,.12,.13),0,.88),inside=mat('Light warm interior lining',(.58,.62,.60),.06,.65),yellow=mat('Warm yellow handrail coating',(.86,.57,.055),.18,.45),lamp=mat('Opaque inactive white lamp lenses',(.82,.87,.85),.1,.28),red=mat('Opaque inactive red lenses',(.60,.026,.018),.1,.34),amber=mat('Opaque inactive amber lenses',(.92,.37,.03),.08,.34),blue=mat('Opaque inactive blue beacon lenses',(.05,.24,.62),.15,.3),hose=mat('Muted linen hose covering',(.65,.57,.38),0,.88),dial=mat('Blank pale gauge faces',(.73,.78,.74),.05,.6))
    g=mat('Lightly tinted alpha blended glazing',(.41,.66,.70,.07),.05,.18)
    g.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.07
    g.surface_render_method='DITHERED';g.use_transparency_overlap=False;p['glass']=g
    return p

def bolt(name,pt,p,axis='X',r=.018,sgn=1):
    cyl(name+' washer',pt,r*1.4,.008,p['steel'],axis,20,.001)
    pos=list(pt);pos['XYZ'.index(axis)]+=sgn*.009
    cyl(name+' hex head',pos,r,.019,p['bright'],axis,6,.001)

def wheel(name,x,y,r,w,p,lugs=8):
    # Closed annular contour with broad sidewall, shoulder and flat rolling crown.
    z=r;N=48;sections=[(-w*.50,r*.46),(-w*.50,r*.77),(-w*.43,r*.94),(-w*.28,r),(w*.28,r),(w*.43,r*.94),(w*.50,r*.77),(w*.50,r*.46)]
    vs=[(x+xx,y+rr*math.cos(math.tau*i/N),z+rr*math.sin(math.tau*i/N)) for xx,rr in sections for i in range(N)];fs=[]
    for k in range(len(sections)):
        for i in range(N):fs.append((k*N+i,k*N+(i+1)%N,((k+1)%len(sections))*N+(i+1)%N,((k+1)%len(sections))*N+i))
    mesh(name+' closed tire',vs,fs,p['rubber'],0,True)
    cyl(name+' wheel rim barrel',(x,y,z),r*.47,w*.96,p['steel'],'X',40,.006)
    for s in [-1,1]:
        xx=x+s*w*.505
        cyl(name+' recessed rim dish',(xx,y,z),r*.38,.021,p['dark'],'X',36,.004)
        cyl(name+' wheel center',(xx+s*.014,y,z),r*.28,.026,p['steel'],'X',36,.004)
        torus(name+' rolled rim lip',(xx,y,z),r*.435,.012,p['bright'],rotation=(0,math.pi/2,0),segments=40)
        cyl(name+' hub',(xx+s*.035,y,z),r*.15,.070,p['dark'],'X',32,.008)
        for k in range(lugs):
            a=math.tau*k/lugs;bolt(name+' lug',(xx+s*.032,y+r*.215*math.cos(a),z+r*.215*math.sin(a)),p,'X',r*.025,s)
        for k in range(8):
            a=math.tau*(k+.5)/8;cyl(name+' dark rim ventilation inset',(xx+s*.014,y+r*.335*math.cos(a),z+r*.335*math.sin(a)),r*.038,.012,p['rubber'],'X',16,0)
    # The closed contour provides the tire's visible shoulder and flat crown.

def running_gear(p,axles,track,r,w,start,end,railz,dual=False):
    for x in [-track*.31,track*.31]:box('Longitudinal chassis rail',(x,(start+end)/2,railz),(.13,end-start,.22),p['dark'],.012)
    for y in [start+.25,(start+end)/2,end-.25]:box('Chassis transverse member',(0,y,railz),(track*.78,.13,.18),p['dark'],.010)
    for j,y in enumerate(axles):
        for s in [-1,1]:
            xx=s*track/2;wheel('Road wheel',xx,y,r,w,p,6 if r<.4 else 8)
            if dual and j>0:wheel('Inner rear twin tire',xx-s*w*1.03,y,r,w,p)
            cyl('Brake drum',(xx-s*w*.47,y,r),r*.32,.16,p['dark'],'X',32)
            for k in range(3):box('Layered leaf spring',(s*track*.31,y,railz-.11-k*.023),(.09,.75-k*.12,.018),p['steel'],.004)
            rod('Suspension shock',(s*track*.34,y-.18,r*.9),(s*track*.31,y-.34,railz+.09),.036,p['dark'])
        rod('Solid axle beam',(-track*.48,y,r),(track*.48,y,r),.075,p['dark'],32)
        common.sphere('Differential housing',(0,y,r),(.18,.21,.15),p['dark'],24,12)
        rod('Axle torque link',(0,y,r),(0,y-.45,railz),.052,p['steel'])
    box('Underside gearbox',(0,(start+end)*.3,railz),(.40,.65,.23),p['dark'],.045)
    rod('Longitudinal propeller shaft',(0,axles[0]+.25,railz-.05),(0,axles[-1]-.2,railz-.05),.049,p['steel'])

def arched_panel(name,x,depth,y0,y1,bottom,top,arches,m):
    # A single closed solid panel whose lower outline rises around each tire.
    pts=[(y0,bottom)]
    for cy,r,zc in sorted(arches):
        if not(y0<cy-r and cy+r<y1):continue
        pts.append((cy-r,bottom));pts.append((cy-r,zc))
        for i in range(1,25):
            a=math.pi-math.pi*i/24;pts.append((cy+r*math.cos(a),zc+r*math.sin(a)))
        pts.append((cy+r,bottom))
    pts += [(y1,bottom),(y1,top),(y0,top)]
    return prof(name,x,depth,pts,m,bevel=.007)

def arch_trim(name,x,y,z,r,p,m=None,width=.035):
    pts=[(x,y+r*math.cos(math.pi-i*math.pi/32),z+r*math.sin(math.pi-i*math.pi/32)) for i in range(33)]
    tube(name,pts,width,m or p['rubber'],2)

def seat(name,x,y,z,p,w=.45,head=False):
    box(name+' floor pedestal',(x,y,z-.28),(w*.62,.33,.50),p['dark'],.016)
    box(name+' lower shell',(x,y,z-.025),(w,.43,.08),p['inside'],.035)
    box(name+' cushion',(x,y-.035,z+.03),(w*.94,.41,.10),p['seat'],.040)
    box(name+' back shell',(x,y+.185,z+.33),(w,.095,.63 if head else .55),p['inside'],.035,rot=(math.radians(-7),0,0))
    box(name+' padded back',(x,y+.12,z+.32),(w*.9,.07,.49 if head else .43),p['seat'],.035,rot=(math.radians(-7),0,0))
    if head:
        for dx in [-.11,.11]:rod(name+' headrest post',(x+dx,y+.20,z+.57),(x+dx,y+.20,z+.73),.012,p['steel'])
        box(name+' headrest',(x,y+.2,z+.75),(w*.72,.13,.19),p['seat'],.045)

def steering(x,y,z,p):
    rod('Steering column',(x,y-.18,z-.40),(x,y,z),.032,p['dark'],24)
    torus('Steering wheel',(x,y,z),.18,.021,p['rubber'],rotation=(math.radians(25),0,0),segments=40)
    for a in [30,150,270]:
        t=math.radians(a);rod('Steering spoke',(x,y,z),(x+.172*math.cos(t),y+.172*math.sin(t)*math.cos(math.radians(25)),z+.172*math.sin(t)*math.sin(math.radians(25))),.016,p['dark'])
    box('Steering hub',(x,y,z),(.105,.10,.05),p['dark'],.02,rot=(math.radians(25),0,0))

def driver_area(p,x,y,floor,dashw=.68):
    seat('Driver seat',x,y+.43,floor+.49,p,w=.49,head=True)
    box('Dashboard lower console',(x,y-.26,floor+.51),(dashw,.37,.39),p['dark'],.05)
    box('Instrument cluster hood',(x,y-.1,floor+.76),(.41,.15,.17),p['dark'],.02)
    for dx in [-.10,.10]:
        cyl('Blank instrument dial',(x+dx,y-.015,floor+.77),.057,.012,p['dial'],'Y',24,.002)
        rod('Static instrument needle',(x+dx,y-.024,floor+.77),(x+dx+.022,y-.024,floor+.793),.003,p['dark'],12)
    steering(x,y+.10,floor+.95,p)
    for dx in [-.1,.1]:box('Driver floor pedal',(x+dx,y-.08,floor+.07),(.10,.16,.035),p['rubber'],.005,rot=(.2,0,0))
    rod('Parking control lever',(x+.27,y+.25,floor+.37),(x+.27,y+.17,floor+.62),.013,p['dark'])
    grip=common.sphere('Control lever knob',(x+.27,y+.17,floor+.62),(.025,.025,.032),p['rubber'],20,10)
    # Tiny grips use intentional faceted normals: smooth accumulation can vary in independent exports.
    for face in grip.data.polygons:face.use_smooth=False

def handle(name,loc,p,axis='X',length=.22):
    x,y,z=loc
    if axis=='X':
        s=1 if x>0 else -1
        for yy in [y-length/2,y+length/2]:rod(name+' stand off',(x-s*.025,yy,z),(x,yy,z),.018,p['dark'])
        rod(name+' grip',(x,y-length/2,z),(x,y+length/2,z),.021,p['dark'])
    else:
        for zz in [z-length/2,z+length/2]:rod(name+' stand off',(x,y-.03,zz),(x,y,zz),.018,p['dark'])
        rod(name+' grip',(x,y,z-length/2),(x,y,z+length/2),.021,p['dark'])

def lights(name,y,width,z,p,rear=False):
    s=1 if rear else -1
    for x in [-width*.36,width*.36]:
        box(name+' lamp housing',(x,y,z),(.33,.08,.18),p['dark'],.025)
        for j,key in enumerate(['red' if rear else 'lamp','amber']):box(name+' inactive lens',(x+(-.075 if j==0 else .095),y+s*.046,z),(.15 if j==0 else .105,.012,.12),p[key],.012)

def mirror(p,s,x,y,z):
    curve('Mirror support',[(s*x,y+.04,z-.14),(s*(x+.11),y-.11,z-.05),(s*(x+.26),y-.13,z+.05)],.022,p['dark'])
    box('Mirror housing',(s*(x+.27),y-.13,z+.09),(.17,.10,.30),p['dark'],.035)
    box('Opaque mirror reflective face',(s*(x+.27),y-.071,z+.09),(.133,.012,.25),p['steel'],.020)

def wipers(p,front_y,z,width=1.65,slope=.0):
    for x in [-width*.26,width*.26]:
        rod('Wiper arm',(x,front_y,z),(x+.20,front_y+slope*.35,z+.35),.013,p['dark'])
        rod('Wiper blade',(x+.03,front_y+slope*.22-.012,z+.23),(x+.39,front_y+slope*.48-.012,z+.49),.018,p['rubber'])

def grille(p,y,z,w,h,paint,rows=5):
    box('Radiator grille recessed baffle',(0,y,z),(w,.03,h),p['dark'],.014)
    for j in range(rows):box('Grille horizontal blade',(0,y-.024,z-h*.4+j*h*.8/(rows-1)),(w*.92,.025,h*.07),paint,.004)

def entry_step(p,x,y,z,w=.20,d=.62):
    box('Entry step support',(x,y,z),(.16,d,.09),p['dark'],.008)
    box('Entry tread',(x,y,z+.05),(w,d,.027),p['steel'],.004)
    for k in range(5):box('Entry anti slip rib',(x,y-d*.35+k*d*.175,z+.068),(w*.83,.013,.01),p['rubber'],.002)

def bus():
    p=palette();W=2.45;y0=-5.35;y1=5.35;ax=[-3.5,3.10];r=.49
    running_gear(p,ax,2.12,r,.28,-4.95,5.0,.49,dual=True)
    box('Low floor passenger deck',(0,-1.05,.66),(2.28,8.25,.10),p['floor'],.012)
    box('Raised rear passenger floor',(0,3.77,.95),(2.28,2.97,.12),p['floor'],.012)
    box('Rear floor first step',(0,2.32,.76),(1.05,.30,.18),p['floor'],.01)
    box('Rear floor upper step',(0,2.55,.89),(1.05,.28,.10),p['floor'],.01)
    for s in [-1,1]:
        arched_panel('Lower side body with wheel cutouts',s*1.19,.105,-5.18,5.17,.54,1.39,[(a,.58,.49) for a in ax],p['teal'])
        box('Upper window sill',(s*1.19,0,1.43),(.11,10.35,.12),p['cream'],.016)
        box('Roof edge rail',(s*1.19,.01,2.77),(.105,10.35,.12),p['cream'],.02)
        for a in ax:
            arch_trim('Tire clearance arch',s*1.25,a,.49,.586,p,width=.025)
            box('Interior wheel box',(s*.91,a,1.04),(.55,1.30,.47),p['inside'],.06)
        for yy in [-4.97,-3.94,-2.78,-1.62,-.46,.70,1.86,3.02,4.18,5.17]:
            box('Window vertical pillar',(s*1.19,yy,2.10),(.12,.075,1.26),p['cream'],.012)
        for k in range(9):
            a=[-4.97,-3.94,-2.78,-1.62,-.46,.70,1.86,3.02,4.18][k];b=[-3.94,-2.78,-1.62,-.46,.70,1.86,3.02,4.18,5.17][k]
            # Right front and center door zones receive full height glazed door leaves instead.
            if s==1 and k in [0,4]:continue
            box('Transparent passenger side window',(s*1.195,(a+b)/2,2.10),(.014,b-a-.10,1.23),p['glass'],.003)
            box('Upper window vent divider',(s*1.208,(a+b)/2,2.48),(.025,b-a-.09,.026),p['dark'],.003)
        box('Lower exterior rub rail',(s*1.253,0,1.29),(.028,10.12,.035),p['dark'],.006)
        for yy in [-4.5,-.1,4.6]:
            box('Side marker mounting plinth',(s*1.250,yy,1.08),(.030,.14,.08),p['dark'],.007)
            box('Side inactive marker',(s*1.263,yy,1.08),(.015,.12,.06),p['amber'],.006)
    # Two full height closed paired passenger doors, with distinct low thresholds.
    for a,b in [(-4.97,-3.94),(-.46,.70)]:
        cy=(a+b)/2
        box('Passenger door lower dark inset',(1.253,cy,1.03),(.025,b-a-.075,.73),p['dark'],.008)
        for yy in [a+.035,cy,b-.035]:box('Passenger door upright',(1.27,yy,1.68),(.055,.045,2.05),p['dark'],.007)
        for yy in [(a+cy)/2,(cy+b)/2]:
            box('Transparent passenger door upper glass',(1.274,yy,2.11),(.015,(b-a)/2-.07,1.17),p['glass'],.002)
            box('Passenger door lower glazed panel',(1.279,yy,1.04),(.012,(b-a)/2-.08,.60),p['glass'],.002)
        box('Door lower edge',(1.275,cy,.65),(.07,b-a-.03,.09),p['steel'],.006)
        box('Door top edge',(1.275,cy,2.73),(.065,b-a-.02,.06),p['dark'],.006)
        for yy in [a+.10,b-.10]:rod('Passenger entry grab',(1.06,yy,.70),(1.06,yy,2.36),.018,p['yellow'])
    # Front face inclines gently above the large low windscreen sill.
    box('Front lower fascia',(0,-5.22,.99),(2.37,.17,.73),p['cream'],.06)
    prof('Front windshield alpha glass',0,2.22,[(-5.303,1.42),(-5.092,2.68),(-5.075,2.677),(-5.286,1.417)],p['glass'],bevel=.002)
    for x in [-1.16,0,1.16]:beam('Front windshield frame',(x,-5.31,1.41),(x,-5.09,2.71),.055,.055,p['dark'],.006)
    box('Front roof brow',(0,-5.04,2.77),(2.39,.30,.18),p['cream'],.045)
    box('Blank destination recess',(0,-5.193,2.75),(1.63,.025,.16),p['dark'],.012)
    box('Front bumper',(0,-5.34,.64),(2.36,.19,.16),p['dark'],.045)
    lights('Bus front',-5.321,2.35,.98,p);grille(p,-5.321,.77,.86,.18,p['cream'],4);wipers(p,-5.338,1.47,2.0,.17)
    for s in [-1,1]:mirror(p,s,1.20,-4.94,2.28)
    driver_area(p,-.68,-4.54,.72,.74)
    box('Front passenger dash shelf',(.62,-4.99,1.42),(1.03,.38,.13),p['inside'],.04)
    box('Driver partition lower',(-.69,-3.59,1.23),(.89,.06,.99),p['inside'],.018)
    box('Driver partition transparent upper',(-.69,-3.59,2.04),(.89,.014,.62),p['glass'],.003)
    # 18 passenger seats plus one driver: bilateral seats leave a continuous aisle.
    for yy in [-2.72,-1.84,-.96,-.08,.80,1.68,3.24,4.13]:
        for x in [-.83,.83]:
            if x>0 and yy in [-.08]:continue
            seat('Passenger seat',x,yy,(1.40 if yy>3 else 1.20),p,w=.43)
    for x in [-.78,0,.78]:seat('Rear bench individual place',x,4.88,1.40,p,w=.62)
    for x in [-.40,.40]:
        rod('Interior overhead grab rail',(x,-3.5,2.53),(x,4.55,2.53),.019,p['yellow'])
        for yy in [-3.35,-1.5,.9,2.65,4.5]:
            rod('Interior grab vertical',(x,yy,.76 if yy<2.6 else 1.0),(x,yy,2.53),.019,p['yellow'])
            rod('Grab roof attachment',(x,yy,2.53),(x,yy,2.75),.017,p['yellow'])
        for yy in [-2.6,-.7,1.3,3.6]:
            rod('Hanging strap stem',(x,yy,2.52),(x,yy,2.33),.010,p['dark'])
            torus('Passenger hanging grip',(x,yy,2.265),.064,.010,p['yellow'],rotation=(math.pi/2,0,0),segments=24)
    box('Long gently beveled roof',(0,.04,2.86),(2.43,10.42,.18),p['cream'],.075)
    box('Roof HVAC shallow enclosure',(0,1.05,3.04),(1.58,3.58,.23),p['inside'],.09)
    for x in [-.48,.48]:
        cyl('Roof ventilation fan recess',(x,.91,3.163),.34,.018,p['dark'],n=40)
        for k in range(5):box('Roof fan protective bar',(x-.24+k*.12,.91,3.178),(.023,.49,.016),p['steel'],.003)
    box('Rear lower service body',(0,5.22,1.20),(2.38,.16,1.19),p['teal'],.04)
    box('Rear window glass',(0,5.259,2.15),(2.11,.014,.98),p['glass'],.003)
    for x in [-1.16,1.16]:box('Rear corner pillar',(x,5.20,2.13),(.13,.18,1.27),p['cream'],.02)
    box('Rear lower window crossbar',(0,5.25,1.65),(2.36,.06,.07),p['cream'],.01)
    box('Rear engine grille recessed panel',(0,5.316,1.13),(1.56,.021,.56),p['dark'],.02)
    for z in [.92,1.02,1.12,1.22,1.32]:box('Rear service ventilation slat',(0,5.333,z),(1.45,.025,.035),p['teal'],.004)
    for x in [-.84,.84]:handle('Rear service latch',(x,5.34,1.42),p,'Y',.13)
    box('Rear bumper',(0,5.35,.63),(2.35,.19,.17),p['dark'],.035);lights('Bus rear',5.321,2.48,1.48,p,True)
    box('Underside rear service casing',(0,4.13,.65),(1.31,1.66,.40),p['dark'],.06)
    box('Underfloor equipment enclosure',(-.69,.02,.45),(.57,1.91,.28),p['dark'],.035)
    return ('city-urban-transit-bus','低床型都市路線バス','Urban transit bus','停留所や都市道路に配置する、二軸の低床型路線バスです。長い車体、二か所の閉じた乗客扉、広い窓、段差付きの後部床、座席、手すりと吊り手、運転席・操舵輪・計器、車軸と底部フレーム、後部サービスグリル、屋根上の空調外装を一式に造形しています。淡いアルファ透過ガラスをGLBに収録し、側窓と前面窓から実際の座席と車内が見えます。扉下部の暗色パネル・ミラー・灯火・行先表示欄は不透明です。屈折ガラス、内部エンジン、文字、人物、扉開閉・走行・操舵・空調動作は含みません。部品全体で一モデルです。','A two-axle low-floor-style transit bus for stops and urban road scenes. Its long body includes two closed passenger doorways, broad windows, a stepped rear floor, modeled passenger seats, handrails and hanging grips, driver seat with steering wheel and blank instruments, axles and underframe, rear service grille and rooftop HVAC exterior. Lightly tinted alpha-blended glazing is exported in the GLB, allowing genuine views of the included seats and cabin. Lower dark door panels, mirrors, lamps and the blank destination panel are opaque. No refractive-glass simulation, internal engine, lettering, people, door, driving, steering or HVAC behavior is included. All components form one complete model.',['road-vehicle','transit-bus','passenger-interior','bus','バス'])


def van():
    p=palette();r=.345;ax=[-1.63,1.63]
    running_gear(p,ax,1.68,r,.22,-2.48,2.48,.39)
    box('Cargo floor undertray',(0,.61,.57),(1.78,3.82,.13),p['dark'],.025)
    box('Cab footwell',(0,-1.30,.60),(1.77,1.69,.12),p['floor'],.025)
    # Cargo hull is a visibly distinct sealed load body, not a glass cabin.
    for s in [-1,1]:
        arched_panel('Van lower rocker panel',s*.92,.10,-2.47,2.47,.43,1.14,[(a,.408,.345) for a in ax],p['van'])
        prof('Solid cargo side panel',s*.922,.085,[(-.48,1.12),(2.43,1.12),(2.43,2.13),(2.27,2.30),(-.37,2.30),(-.48,2.18)],p['van'],bevel=.035)
        box('Side rubbing strip',(s*.981,.55,1.04),(.035,3.73,.085),p['dark'],.016)
        for y in ax:arch_trim('Van wheel arch rubber lip',s*.984,y,r,.414,p,width=.026)
        # Front-door shell and genuine upper window opening with raked front edge.
        prof('Cab door lower pressed panel',s*.919,.072,[(-2.12,1.10),(-2.00,1.36),(-.51,1.36),(-.51,.72),(-1.18,.72),(-1.20,1.10)],p['van'],bevel=.025)
        prof('Cab side glazing',s*.929,.014,[(-2.01,1.40),(-1.47,2.05),(-.57,2.10),(-.55,1.40)],p['glass'],bevel=.002)
        beam('Raked front door pillar',(s*.925,-2.08,1.34),(s*.925,-1.49,2.11),.065,.065,p['dark'])
        box('Rear cab door pillar',(s*.924,-.51,1.72),(.075,.075,.81),p['dark'],.01)
        beam('Cab window upper frame',(s*.924,-1.49,2.12),(s*.924,-.50,2.14),.065,.065,p['van'])
        box('Cab window lower seal',(s*.943,-1.27,1.38),(.035,1.49,.035),p['dark'],.006)
        box('Door vertical shut seam',(s*.968,-.478,1.25),(.012,.018,.87),p['dark'],.002)
        handle('Cab door handle',(s*.981,-.70,1.25),p,length=.19)
        mirror(p,s,.94,-1.95,1.47)
    # Passenger-side sliding cargo access: bounded panel, tracks and distinct handle.
    box('Sliding cargo door upper gap',(.970,.50,2.21),(.012,1.71,.018),p['dark'],.002)
    for y in [-.38,1.39]:box('Sliding cargo door vertical gap',(.972,y,1.52),(.012,.018,1.39),p['dark'],.002)
    box('Sliding cargo door lower gap',(.973,.50,.825),(.012,1.77,.018),p['dark'],.002)
    box('Sliding cargo door exterior track',(.989,1.48,1.73),(.04,1.61,.05),p['dark'],.007)
    box('Sliding cargo door track insert',(1.011,1.48,1.73),(.012,1.48,.018),p['steel'],.003)
    handle('Side loading door handle',(1.007,-.19,1.38),p,length=.22)
    box('High cargo roof',(0,.94,2.29),(1.88,3.02,.14),p['van'],.065)
    box('Cab roof',(0,-1.00,2.15),(1.87,1.10,.15),p['van'],.055)
    prof('Rising roof transition',0,1.88,[(-.54,2.08),(-.54,2.24),(-.30,2.35),(-.10,2.35),(-.10,2.22),(-.36,2.08)],p['van'],bevel=.025)
    # Short tapered hood/front nose gives the van a passenger-car-like stance.
    prof('Short sloped bonnet',0,1.83,[(-2.59,.94),(-2.59,1.16),(-2.04,1.35),(-1.97,1.23),(-2.27,.94)],p['van'],bevel=.04)
    prof('Windshield glazing',0,1.72,[(-2.056,1.37),(-1.487,2.06),(-1.475,2.048),(-2.044,1.358)],p['glass'],bevel=.002)
    for x in [-.88,.88]:beam('Front windshield side frame',(x,-2.08,1.35),(x,-1.49,2.11),.07,.07,p['van'])
    box('Van front face',(0,-2.54,.83),(1.84,.16,.35),p['van'],.04)
    box('Van front bumper',(0,-2.64,.55),(1.86,.20,.24),p['dark'],.045)
    grille(p,-2.632,.83,.86,.22,p['steel'],4);lights('Van front',-2.634,1.88,1.04,p);wipers(p,-2.08,1.39,1.6,.82)
    box('Full dashboard',(0,-1.85,1.31),(1.64,.35,.18),p['dark'],.045)
    driver_area(p,-.48,-1.66,.65,.66);seat('Passenger seat',.48,-1.20,1.14,p,.49,True)
    box('Opaque cargo/cab partition',(0,-.42,1.44),(1.74,.06,1.59),p['inside'],.02)
    # Separate rear split doors with actual outer frame, four hinge sets and latches.
    box('Rear door frame',(0,2.465,1.41),(1.86,.10,1.86),p['dark'],.05)
    for s in [-1,1]:
        box('Separate rear cargo door',(s*.454,2.526,1.44),(.878,.06,1.73),p['van'],.045)
        for z in [.89,1.94]:
            box('Rear door hinge leaf',(s*.84,2.566,z),(.14,.025,.10),p['steel'],.006)
            cyl('Rear door hinge barrel',(s*.90,2.582,z),.027,.16,p['steel'],n=24)
        handle('Rear vertical door handle',(s*.09,2.575,1.35),p,'Y',.24)
        box('Rear pillar lamp recess',(s*.875,2.585,.98),(.092,.045,.38),p['dark'],.012)
        for k,key in enumerate(['red','amber','lamp']):box('Rear inactive stacked lens',(s*.876,2.612,.85+k*.12),(.063,.012,.089),p[key],.006)
    box('Rear loading threshold',(0,2.58,.51),(1.86,.22,.14),p['dark'],.025)
    box('Rear bumper tread',(0,2.62,.596),(1.37,.15,.018),p['rubber'],.006)
    box('Underfloor fuel tank',(-.52,.05,.38),(.58,.85,.22),p['dark'],.035)
    cyl('Exhaust muffler',(.50,.80,.36),.10,.70,p['steel'],'Y',32,.02)
    curve('Rear exhaust pipe',[(.50,1.1,.36),(.5,1.75,.35),(.65,2.18,.33),(.76,2.43,.32)],.033,p['dark'])
    box('Fuel filler outline',(-.98,1.03,1.27),(.015,.24,.22),p['dark'],.022)
    box('Fuel filler flap',(-.991,1.03,1.27),(.015,.205,.185),p['van'],.02)
    return ('city-delivery-panel-van','配送用パネルバン','Delivery panel van','市街地の配送拠点や店舗の荷さばき場に配置する小型配送バンです。短いボンネットと傾斜した前面窓、独立した運転席、左右の座席・操舵輪・計器、背の高い密閉荷室、側面スライド扉の輪郭とレール、観音開きの後扉とヒンジ・取手、車輪アーチ、車軸と底部外装を造形しています。運転室の窓はGLB内の淡いアルファ透過材質で、実際に含まれる内装が見えます。荷室・仕切壁・ミラー・灯火は不透明で、荷室内部と積荷は省略しています。屈折ガラス、扉開閉、走行・操舵機構、文字や人物は含みません。部品全体で一モデルです。','A compact delivery van for city depots and shop loading areas. A short bonnet and raked windshield distinguish its cab from the tall enclosed cargo body. Included features are two modeled front seats, steering wheel and blank instruments, side sliding-door seams and track, separate split rear doors with hinges and handles, shaped wheel arches, axles and underside exterior detail. Cab windows use lightly tinted alpha-blended GLB material and reveal the included interior. Cargo shell, partition, mirrors and lamps are opaque; cargo internals and goods are omitted. No refractive-glass simulation, door motion, driving or steering mechanism, lettering or people is included. All components form one complete model.',['road-vehicle','delivery-van','cargo-access','panel-van','配送車'])


def fire_truck():
    p=palette();r=.51;ax=[-2.32,2.03]
    running_gear(p,ax,2.10,r,.29,-3.43,3.56,.62,dual=True)
    box('Crew cab floor',(0,-2.04,.86),(2.23,2.91,.13),p['floor'],.025)
    for s in [-1,1]:
        arched_panel('Crew cab lower side',s*1.15,.10,-3.49,-.58,.62,1.57,[(-2.32,.60,.51)],p['redpaint'])
        box('Cab door sill trim',(s*1.215,-1.28,.71),(.04,.95,.12),p['steel'],.012)
        for y in [-3.37,-1.95,-.66]:box('Crew cab window pillar',(s*1.15,y,2.23),(.11,.085,1.24),p['redpaint'],.015)
        for a,b in [(-3.37,-1.95),(-1.95,-.66)]:
            box('Crew cab side transparent window',(s*1.156,(a+b)/2,2.24),(.014,b-a-.12,1.04),p['glass'],.003)
            box('Cab lower window frame',(s*1.178,(a+b)/2,1.69),(.045,b-a-.08,.06),p['dark'],.007)
            box('Cab door rear seam',(s*1.209,b-.01,1.26),(.012,.018,.78),p['dark'],.002)
            handle('Crew cab door handle',(s*1.232,b-.23,1.43),p,length=.23)
        arch_trim('Front fender metal lip',s*1.22,-2.32,r,.607,p,p['dark'],.034)
        for y in [-3.08,-1.16]:entry_step(p,s*1.18,y,.50,.25,.49)
        mirror(p,s,1.18,-3.16,2.19)
    box('Crew cab roof',(0,-2.03,2.94),(2.37,2.99,.18),p['redpaint'],.075)
    box('Crew cab rear wall',(0,-.59,1.98),(2.28,.10,1.93),p['redpaint'],.03)
    box('Front red fascia',(0,-3.46,1.19),(2.30,.18,.86),p['redpaint'],.055)
    box('Broad transparent windshield',(0,-3.532,2.23),(2.17,.014,1.09),p['glass'],.003)
    for x in [-1.13,0,1.13]:box('Front windshield pillar',(x,-3.54,2.24),(.06,.07,1.21),p['dark'],.008)
    box('Front windshield lower seal',(0,-3.548,1.665),(2.30,.055,.055),p['dark'],.008)
    box('Front windshield upper frame',(0,-3.50,2.82),(2.31,.10,.09),p['redpaint'],.02)
    box('Fire truck front bumper',(0,-3.61,.69),(2.39,.26,.21),p['steel'],.04)
    lights('Pumper front',-3.568,2.4,1.17,p);grille(p,-3.562,.93,1.10,.23,p['steel'],5);wipers(p,-3.56,1.72,2.0)
    driver_area(p,-.67,-2.98,.94,.76);seat('Front crew seat',.67,-2.56,1.44,p,.50,True)
    for x in [-.68,0,.68]:seat('Rear crew seat',x,-1.16,1.43,p,.52,True)
    box('Full front dash shelf',(0,-3.27,1.67),(2.05,.35,.16),p['dark'],.04)
    # Roof lightbar: unlit opaque lenses, mounting feet physically meet the roof.
    for x in [-.74,.74]:box('Lightbar mounting foot',(x,-2.90,3.071),(.15,.25,.13),p['dark'],.015)
    box('Emergency lightbar base',(0,-2.90,3.145),(1.99,.30,.06),p['steel'],.025)
    for x in [-.76,.76]:box('Opaque inactive blue lightbar lens',(x,-2.90,3.24),(.42,.28,.14),p['blue'],.045)
    box('Lightbar middle housing',(0,-2.90,3.22),(1.03,.27,.10),p['inside'],.025)
    # Lower equipment body sits on crossbearers, while side bays remain visibly distinct.
    for y in [-.27,1.32,3.20]:box('Equipment body crossbearer',(0,y,.83),(2.25,.16,.18),p['dark'],.015)
    box('Equipment deck',(0,1.48,.97),(2.30,4.05,.12),p['steel'],.015)
    box('Equipment body central opaque core',(0,1.48,1.76),(1.87,3.99,1.48),p['redpaint'],.035)
    for s in [-1,1]:
        arched_panel('Rear body sill with axle arch',s*1.15,.10,-.46,3.47,.69,1.40,[(2.03,.60,.51)],p['redpaint'])
        arch_trim('Rear fender black lip',s*1.22,2.03,r,.607,p,width=.034)
        # Three recessed roll-up bay shutters per side, with the pump replacing the forward left bay.
        for a,b in [(-.37,.78),(.88,1.73),(2.32,3.37)]:
            if s==-1 and a<0:continue
            cy=(a+b)/2;lo=1.46 if a>0 else 1.05;hi=2.42
            box('Equipment bay dark surround',(s*1.18,cy,(lo+hi)/2),(.08,b-a,hi-lo),p['dark'],.014)
            box('Equipment roll shutter',(s*1.226,cy,(lo+hi)/2),(.025,b-a-.09,hi-lo-.08),p['steel'],.008)
            n=int((hi-lo)/.085)
            for k in range(n):box('Shutter horizontal groove',(s*1.242,cy,lo+.07+k*.083),(.012,b-a-.10,.012),p['dark'],.002)
            handle('Equipment bay latch',(s*1.267,cy,lo+.13),p,length=.27)
        box('Upper body edge cap',(s*1.16,1.50,2.48),(.14,4.06,.10),p['redpaint'],.02)
    # Exposed left pump panel, not a hidden set of labels painted on a body.
    box('Pump control recessed backing',(-1.183,.20,1.71),(.07,1.10,1.36),p['dark'],.02)
    box('Pump satin control face',(-1.227,.20,1.73),(.035,1.01,1.23),p['steel'],.015)
    for j,yy in enumerate([-.12,.22,.55]):
        cyl('Pump outlet shoulder',(-1.28,yy,1.39),.116,.10,p['dark'],'X',32,.008)
        cyl('Pump outlet capped coupling',(-1.37,yy,1.39),.095,.10,p['bright'],'X',12,.005)
        cyl('Pump outlet cap',(-1.425,yy,1.39),.078,.016,p['dark'],'X',32,.003)
        rod('Valve control stem',(-1.25,yy,1.72),(-1.38,yy,1.72),.025,p['dark'])
        torus('Valve handwheel',(-1.40,yy,1.72),.082,.012,p['redpaint'],rotation=(0,math.pi/2,0),segments=28)
        for a in [0,120,240]:
            t=math.radians(a);rod('Valve wheel spoke',(-1.4,yy,1.72),(-1.4,yy+.075*math.cos(t),1.72+.075*math.sin(t)),.009,p['redpaint'])
    for yy in [-.07,.43]:
        cyl('Pump gauge outer rim',(-1.28,yy,2.13),.106,.035,p['dark'],'X',32,.004)
        cyl('Pump blank gauge face',(-1.301,yy,2.13),.084,.010,p['dial'],'X',32,.001)
        rod('Pump gauge fixed needle',(-1.31,yy,2.13),(-1.31,yy+.043,2.168),.005,p['dark'],12)
    box('Pump panel floor step',(-1.28,.20,1.03),(.30,1.10,.07),p['steel'],.014)
    curve('Pump short curved hose',[(-1.32,-.12,1.34),(-1.38,-.30,1.12),(-1.34,-.40,.96),(-1.10,-.37,.94),(-1.02,-.14,1.05)],.027,p['rubber'])
    # Top hose tray and a complete stowed straight ladder carried on three supports.
    box('Top hose storage tray',(0,1.54,2.56),(1.29,3.65,.09),p['dark'],.018)
    for x in [-.61,.61]:box('Hose tray lip',(x,1.54,2.68),(.05,3.63,.19),p['steel'],.009)
    for x in [-.34,0,.34]:
        for z in [2.65,2.72]:box('Folded hose stack',(x,1.55,z),(.27,3.36,.075),p['hose'],.033)
        for yy in [.30,2.75]:box('Hose retaining strap',(x,yy,2.765),(.28,.05,.025),p['dark'],.005)
    for y in [-.05,1.53,3.05]:box('Ladder saddle bracket',(.97,y,2.62),(.50,.16,.29),p['dark'],.012)
    for x in [.76,1.15]:box('Stowed ladder rail',(x,1.49,2.82),(.055,3.92,.11),p['steel'],.009)
    for j in range(14):cyl('Stowed ladder rung',(.955,-.28+j*.27,2.82),.024,.39,p['steel'],'X',20,.003)
    # Rear reel is bracketed to the equipment deck and reads as a separate mechanism.
    box('Rear equipment wall',(0,3.50,1.79),(2.28,.10,1.43),p['redpaint'],.025)
    for x in [-.47,.47]:beam('Rear reel triangular support',(x,3.52,1.09),(x,3.65,1.91),.085,.085,p['steel'])
    rod('Reel axle',(-.55,3.65,1.91),(.55,3.65,1.91),.055,p['steel'])
    for x in [-.47,.47]:cyl('Reel flange',(x,3.65,1.91),.37,.044,p['redpaint'],'X',40,.01)
    cyl('Reel central drum',(0,3.65,1.91),.24,.88,p['dark'],'X',40,.012)
    for x in [-.35,-.25,-.15,-.05,.05,.15,.25,.35]:torus('Wound rear hose',(x,3.65,1.91),.275,.041,p['rubber'],rotation=(0,math.pi/2,0),segments=40)
    curve('Reel outlet hose',[(.39,3.69,1.66),(.62,3.78,1.43),(.72,3.80,1.23),(.61,3.82,1.13)],.034,p['rubber'])
    rod('Hose nozzle',(.61,3.82,1.13),(.39,3.82,1.13),.048,p['steel'])
    box('Rear tread bumper',(0,3.68,.74),(2.40,.38,.17),p['steel'],.025);lights('Pumper rear',3.573,2.51,1.22,p,True)
    for s in [-1,1]:
        rod('Rear access grab',(s*1.02,3.59,1.42),(s*1.02,3.59,2.21),.019,p['steel'])
        for z in [1.45,2.18]:rod('Rear grab return',(s*1.02,3.50,z),(s*1.02,3.59,z),.019,p['steel'])
    box('Underbody water tank exterior',(0,1.04,.86),(1.38,2.37,.29),p['dark'],.04)
    return ('city-fire-pumper-truck','消防ポンプ車','Fire pumper truck','消防署の車庫前や都市の緊急車両シーンに配置する、文字のない二軸ポンプ車です。乗員用の長いキャブ、前後二列の座席、操舵輪と計器、側面機材シャッター、露出したポンプ操作盤・固定指針の計器・弁ハンドルと接続口、屋根上の折り畳みホース束と積載はしご、後部ホースリール、ステップと底部フレームを一式に造形しています。キャブ窓はGLBの淡いアルファ透過材質で、実際の内装を見通せます。灯火とミラーは不透明で消灯状態、機材室とタンクの内部は省略しています。屈折ガラス、文字、人物、放水・油圧・扉開閉・走行・操舵動作、実車の性能や安全性の検証は含みません。全体で一モデルです。','An unlettered two-axle pumper truck for station forecourts and urban emergency-vehicle scenes. A long crew cab with two seat rows, steering and blank instruments is paired with equipment shutters, an exposed pump panel with fixed-needle gauges, valve handwheels and capped couplings, top folded hose stacks and a stowed ladder, rear hose reel, steps and underframe. Lightly tinted alpha-blended cab glazing reveals actual included interior geometry. Lamps and mirrors are opaque and inactive; equipment-bay and tank internals are omitted. No refractive-glass simulation, lettering, people, water, hydraulic, door, driving or steering behavior, real-vehicle performance or safety validation is included. All components form one complete model.',['road-vehicle','fire-pumper','crew-cab','hose-reel','消防車'])


def refuse_truck():
    p=palette();r=.50;ax=[-2.60,1.63,2.81]
    running_gear(p,ax,2.12,r,.28,-3.46,3.88,.62,dual=True)
    box('Refuse cab floor',(0,-2.65,.86),(2.20,1.99,.13),p['floor'],.025)
    for s in [-1,1]:
        arched_panel('Compact cab lower side',s*1.13,.11,-3.62,-1.64,.63,1.53,[(-2.60,.59,.50)],p['cream'])
        prof('Compact cab side alpha glazing',s*1.137,.014,[(-3.47,1.62),(-3.30,2.62),(-1.78,2.62),(-1.75,1.62)],p['glass'],bevel=.002)
        beam('Compact raked front pillar',(s*1.13,-3.52,1.55),(s*1.13,-3.32,2.70),.075,.075,p['cream'])
        box('Compact rear door pillar',(s*1.13,-1.70,2.12),(.10,.10,1.19),p['cream'],.015)
        box('Cab lower window trim',(s*1.166,-2.61,1.58),(.04,1.76,.06),p['dark'],.006)
        box('Cab door seam',(s*1.195,-1.68,1.26),(.012,.015,.57),p['dark'],.001)
        handle('Refuse cab door handle',(s*1.22,-1.94,1.39),p,length=.23)
        arch_trim('Cab tire arch trim',s*1.20,-2.60,r,.597,p,width=.032)
        entry_step(p,s*1.17,-1.95,.50,.24,.49)
        mirror(p,s,1.16,-3.38,2.16)
    box('Compact cab roof',(0,-2.59,2.73),(2.32,2.04,.18),p['cream'],.065)
    box('Cab rear wall',(0,-1.65,1.87),(2.23,.10,1.83),p['cream'],.03)
    box('Refuse truck front fascia',(0,-3.56,1.18),(2.27,.19,.75),p['cream'],.045)
    prof('Cab front alpha windshield',0,2.13,[(-3.64,1.59),(-3.44,2.62),(-3.425,2.617),(-3.625,1.587)],p['glass'],bevel=.002)
    for x in [-1.10,0,1.10]:beam('Refuse front windshield frame',(x,-3.65,1.57),(x,-3.44,2.65),.057,.057,p['dark'])
    box('Cab windshield lower lip',(0,-3.63,1.55),(2.29,.11,.08),p['cream'],.012)
    box('Refuse front bumper',(0,-3.72,.70),(2.38,.24,.20),p['dark'],.04)
    grille(p,-3.666,.96,1.04,.26,p['steel'],5);lights('Refuse front',-3.671,2.31,1.23,p);wipers(p,-3.66,1.64,1.9,.195)
    driver_area(p,-.65,-3.12,.93,.73);seat('Refuse crew seat',.65,-2.68,1.43,p,.51,True)
    box('Refuse full dash',(0,-3.32,1.60),(2.08,.28,.17),p['dark'],.035)
    for x in [-.85,.85]:
        cyl('Amber beacon mounting foot',(x,-2.58,2.84),.095,.06,p['dark'],n=28)
        cyl('Opaque inactive amber beacon',(x,-2.58,2.95),.079,.16,p['amber'],n=32,bevel=.025)
    # The wide compactor body has a faceted, rounded-shoulder cross section.
    section=[(-1.12,1.04),(1.12,1.04),(1.23,1.21),(1.23,2.79),(1.01,3.13),(.78,3.26),(-.78,3.26),(-1.01,3.13),(-1.23,2.79),(-1.23,1.21)]
    prof('Opaque compactor body',.88,4.70,section,p['green'],axis='Y',bevel=.05)
    for y in [-1.22,.12,1.47,2.82]:
        box('Compactor chassis crossbearer',(0,y,.94),(2.19,.18,.20),p['dark'],.014)
        for s in [-1,1]:
            box('Body external vertical stiffener',(s*1.266,y,2.01),(.065,.12,1.49),p['green'],.016)
            beam('Upper shoulder reinforcement',(s*1.26,y,2.78),(s*.92,y,3.22),.065,.12,p['green'])
    for s in [-1,1]:
        box('Lower longitudinal body rib',(s*1.27,.83,1.19),(.075,4.65,.11),p['dark'],.012)
        # The tandem tires remain visible below continuous side protection, not buried in a box.
        for yy in [1.63,2.81]:
            arch_trim('Rear tandem half fender',s*1.22,yy,r,.587,p,p['dark'],.056)
            box('Rear wheel mudflap',(s*1.17,yy+.56,.43),(.33,.035,.62),p['rubber'],.006)
        box('Side protection rail',(s*1.19,-.44,.59),(.11,1.61,.12),p['steel'],.012)
        for yy in [-1.02,.10]:beam('Side rail chassis hanger',(s*.94,yy,.91),(s*1.19,yy,.61),.065,.065,p['dark'])
        box('Side small service hatch',(s*1.265,-.64,1.88),(.090,.66,.65),p['dark'],.020)
        box('Side service hatch cover',(s*1.314,-.64,1.88),(.018,.60,.59),p['green'],.017)
        handle('Service hatch latch',(s*1.348,-.64,1.68),p,length=.15)
    # Rear-loading hopper: a real open mouth with side cheeks, sloped bowl and recessed blade.
    for s in [-1,1]:
        prof('Tailgate side cheek',s*1.18,.16,[(3.15,.97),(4.19,.91),(4.36,1.13),(4.16,2.57),(3.60,3.17),(3.10,3.17)],p['green'],bevel=.035)
        prof('Tailgate dark outer reinforcement',s*1.29,.075,[(3.24,1.24),(3.64,1.28),(4.13,2.55),(3.80,2.87),(3.49,2.19)],p['dark'],bevel=.016)
    # Ramp is a closed sloping plate. No fake flat dark panel at the hopper opening.
    prof('Visible hopper basin floor',0,2.22,[(3.20,1.45),(4.23,.96),(4.28,1.06),(3.23,1.57)],p['steel'],bevel=.012)
    box('Rear hopper loading lip',(0,4.28,1.04),(2.31,.15,.16),p['dark'],.025)
    box('Deep inner hopper wall',(0,3.24,2.07),(2.10,.08,1.05),p['dark'],.016)
    prof('Static visible compactor blade',0,2.04,[(3.31,1.70),(3.49,1.70),(3.67,2.30),(3.56,2.46),(3.38,2.37)],p['steel'],bevel=.018)
    prof('Tailgate upper canopy',0,2.28,[(3.16,2.77),(3.66,2.73),(4.15,2.54),(4.14,2.74),(3.68,3.21),(3.16,3.25)],p['green'],bevel=.04)
    box('Rear upper safety colour band',(0,4.12,2.64),(2.26,.042,.12),p['amber'],.01)
    for s in [-1,1]:
        # Outer supports/pins terminate in the body and tailgate, not suspended in space.
        for yy,zz in [(3.11,2.94),(3.90,1.55)]:
            cyl('Tailgate exterior hinge pin',(s*1.33,yy,zz),.11,.13,p['steel'],'X',32,.01)
            bolt('Tailgate hinge retainer',(s*1.41,yy,zz),p,'X',.035,s)
        a=Vector((s*1.34,2.90,2.39));b=Vector((s*1.34,3.91,1.60));v=b-a
        rod('Tailgate support cylinder barrel',a,a+v*.64,.083,p['dark'],32)
        rod('Tailgate support static bright rod',a+v*.59,b,.041,p['bright'],24)
        rod('Support cylinder gland',a+v*.59,a+v*.67,.093,p['steel'],28)
        for pt in [a,b]:
            box('Cylinder attachment clevis',(s*1.27,pt.y,pt.z),(.22,.19,.16),p['green'],.015)
        curve('Tailgate curved service hose',[(s*1.28,2.71,2.23),(s*1.41,2.87,2.50),(s*1.44,3.17,2.60),(s*1.40,3.34,2.31)],.022,p['rubber'])
        box('Rear worker step bracket',(s*.91,4.15,.72),(.12,.45,.21),p['dark'],.012)
        box('Rear stationary riding step',(s*.91,4.39,.73),(.48,.48,.07),p['steel'],.012)
        for k in range(5):box('Rear step grip',(s*.91,4.22+k*.08,.770),(.40,.013,.015),p['rubber'],.002)
        rod('Rear handhold',(s*1.12,4.31,1.19),(s*1.12,4.31,2.22),.024,p['yellow'])
        for z in [1.22,2.18]:rod('Rear handhold mounting return',(s*1.12,4.08,z),(s*1.12,4.31,z),.024,p['yellow'])
        box('Rear lamp cluster',(s*1.01,4.265,1.33),(.23,.06,.19),p['dark'],.012)
        box('Rear inactive stop lens',(s*1.01,4.304,1.34),(.17,.012,.12),p['red'],.008)
        box('Rear side control box',(s*1.34,3.90,1.29),(.10,.30,.24),p['dark'],.014)
        for yy,key in [(3.83,'red'),(3.96,'yellow')]:cyl('Inactive rear control button',(s*1.397,yy,1.29),.028,.016,p[key],'X',20,.003)
    box('Rear lower protective beam',(0,4.00,.51),(2.13,.13,.15),p['dark'],.02)
    box('Underbody hydraulic tank exterior',(-.68,-.47,.66),(.59,1.25,.41),p['dark'],.035)
    cyl('Tank filler cap',(-.68,-.68,.886),.065,.045,p['steel'],n=24)
    return ('city-rear-loading-refuse-truck','後部投入式ごみ収集車','Rear-loading refuse truck','住宅街や清掃拠点のシーンに配置する三軸の後部投入式ごみ収集車です。短い乗員キャブ、三本の車軸と後部の複輪、上肩を面取りした大きな圧縮室外装、側面補強材と点検蓋、実際に開口した後部ホッパー、斜面のある受け皿と奥の固定ブレード、外側の支持アーム・ピン・シリンダー外装と曲線ホース、後部ステップと手すりを備えます。キャブは淡いアルファ透過窓から造形済みの二席・操舵輪・計器を見通せます。圧縮室内部、廃棄物、機関内部は省略し、灯火とミラーは不透明・非作動です。屈折ガラス、走行・操舵・圧縮・油圧・扉開閉動作や実機性能・安全性の検証は含みません。全体で一モデルです。','A three-axle rear-loading refuse truck for residential streets and municipal depots. Its compact crew cab, three axles with rear twin tires, large chamfered-shoulder compactor exterior, side ribs and service hatches are distinct from the other vehicles. The rear hopper is genuinely open, with a sloping bowl, recessed fixed blade, exterior support arms, pins, cylinder exteriors and curved service hoses, plus rear steps and handholds. Lightly tinted alpha-blended cab windows reveal two modeled seats, steering wheel and blank instruments. Internal compactor chamber, refuse and engine internals are omitted; lamps and mirrors are opaque and inactive. No refractive-glass simulation, driving, steering, compaction, hydraulic or door behavior, real-machine performance or safety validation is included. All components form one complete model.',['road-vehicle','refuse-truck','rear-loading-hopper','three-axle','ごみ収集車'])

BUILDERS=[bus,van,fire_truck,refuse_truck]
IDS=['city-urban-transit-bus','city-delivery-panel-van','city-fire-pumper-truck','city-rear-loading-refuse-truck']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-048/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if a.geometry_only:common.render=lambda *args,**kwargs:None
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    for fn,id in zip(BUILDERS,IDS):
        if a.only and a.only!=id:continue
        reset();spec=fn();publish_asset(*spec,out,'scripts/city_expansion/urban_transport_vehicles.py',azimuth=-55,elevation=23)
