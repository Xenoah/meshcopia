"""Four original static waterfront craft. Xenoah, CC BY 4.0.
Analytic thick shells, original proportions, no external geometry or textures.
No water, flotation, rescue certification, driving or hydrodynamic simulation.
"""
import math,sys,argparse,bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def pal():
 return dict(cream=mat('Warm ivory hull enamel',(.72,.73,.66),.05,.43),wood=mat('Oiled honey timber',(.33,.16,.055),0,.49),woodlight=mat('Timber end and seat faces',(.51,.29,.10),0,.48),wooddark=mat('Dark timber joinery',(.15,.061,.024),0,.54),steel=mat('Brushed marine hardware',(.43,.49,.51),.78,.30),dark=mat('Graphite mechanism',(.035,.043,.05),.08,.49),rubber=mat('Textured-looking rubber trim',(.018,.023,.027),0,.79),blue=mat('Pedal craft blue molding',(.035,.27,.42),.03,.39),aqua=mat('Pedal seat light molding',(.31,.62,.63),.02,.42),orange=mat('Unbranded safety-orange collar',(.74,.16,.026),0,.55),gray=mat('Rigid hull pale gray',(.49,.54,.55),.08,.44),red=mat('Rescue boat trim',(.44,.035,.022),0,.51),lime=mat('Personal craft lime deck',(.47,.62,.055),.02,.36),black=mat('Personal craft dark lower hull',(.026,.043,.052),.10,.40),seat=mat('Saddle and seat upholstery',(.065,.081,.085),0,.72))
def cyl(n,p,r,d,m,axis='Z',v=28,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.10));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(n,p,r,t,m,axis='Z',v=40):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)
def sleeve(n,p,ro,ri,h,m,axis='Z',v=32):
 vs=[]
 for r,z in [(ro,-h/2),(ro,h/2),(ri,h/2),(ri,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)];o=mesh(n,vs,fs,m);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o

def loft(n,sections,m,smooth=True):
 """Closed solid loft from equal-length X/Z section rings, including thick U rings."""
 N=len(sections[0][1]);vs=[(x,y,z) for y,ring in sections for x,z in ring];fs=[]
 for j in range(len(sections)-1):
  for k in range(N):fs.append((j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k))
 fs+=[tuple(range(N-1,-1,-1)),tuple((len(sections)-1)*N+k for k in range(N))]
 o=mesh(n,vs,fs,m)
 for f in o.data.polygons:f.use_smooth=smooth and f.index<(len(sections)-1)*N
 return o

def catmull(points,steps=5):
 pp=[Vector(p) for p in points];out=[]
 for i in range(len(pp)-1):
  a,b,c,d=pp[max(0,i-1)],pp[i],pp[i+1],pp[min(len(pp)-1,i+2)]
  for j in range(steps):
   t=j/steps;out.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
 return out+[tuple(pp[-1])]
def cable(n,points,r,m,steps=5):return tube(n,catmull(points,steps),r,m,1)

def row_profile(w,b,r,t=.032):
 outer=[(-w*math.cos(i*math.pi/16),b+(r-b)*(1-math.sin(i*math.pi/16)**.74)) for i in range(17)]
 inner=[(-(w-t)*math.cos(i*math.pi/16),b+t+(r-b-t)*(1-math.sin(i*math.pi/16)**.74)) for i in range(16,-1,-1)]
 return outer+inner
ROW=[(-1.90,.035,.49,.64),(-1.76,.22,.30,.61),(-1.53,.42,.18,.59),(-1.18,.59,.11,.575),(-.72,.70,.085,.565),(-.18,.75,.075,.56),(.38,.74,.08,.56),(.91,.68,.115,.565),(1.34,.57,.18,.58),(1.58,.45,.25,.60),(1.64,.43,.27,.61)]
def interp(sec,y):
 for i in range(len(sec)-1):
  if sec[i][0]<=y<=sec[i+1][0]:
   t=(y-sec[i][0])/(sec[i+1][0]-sec[i][0]);return tuple(sec[i][k]*(1-t)+sec[i+1][k]*t for k in range(1,len(sec[i])))
 return sec[0][1:] if y<sec[0][0] else sec[-1][1:]
def extruded_outline(n,points,z,th,m,bev=0):
 N=len(points);vs=[(x,y,z+dz) for dz in [-th/2,th/2] for x,y in points];fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)];return mesh(n,vs,fs,m,bev)

def rowboat():
 p=pal();loft('Thick open rounded rowing hull',[(y,row_profile(w,b,r,min(.032,w*.38))) for y,w,b,r in ROW],p['cream'])
 # Real solid end walls close the U-shell fore and aft, without filling the cockpit.
 w,b,r=ROW[-1][1:];cross=row_profile(w,b,r)[:17];loft('Solid curved stern transom',[(1.585,cross),(1.650,cross)],p['wood'],False)
 box('Narrow bow stem', (0,-1.881,.566),(.059,.075,.163),p['wood'],.012)
 box('Stern transom timber cap',(0,1.629,.615),(.86,.064,.034),p['wood'],.009)
 for side in [-1,1]:
  path=[(side*w,y,r+.008) for y,w,b,r in ROW];tube('Continuous timber gunwale',path,.026,p['wood'],2)
  for frac in [.43,.72]:
   pts=[]
   for y,w,b,r in ROW[1:]:
    th=math.acos(frac);pts.append((side*w*frac,y,b+(r-b)*(1-math.sin(th)**.74)))
   tube('Raised outside plank seam',pts,.007,p['woodlight'],1)
 # Several visible, closed curved ribs bear against the actual inside hull.
 for y in [-1.42,-1.05,-.64,-.20,.25,.68,1.08,1.40]:
  w,b,r=interp(ROW,y);t=.032;pts=[(-(w-t-.004)*math.cos(i*math.pi/14),y,b+t+.004+(r-b-t-.018)*(1-math.sin(i*math.pi/14)**.74)) for i in range(15)]
  tube('Hull inner curved rib',pts,.018,p['woodlight'],1)
 # Long low slatted sole with cross bearers, visibly distinct from the recessed hull.
 for y in [-.90,-.35,.25,.82]:
  beam=[]
  for yy in [y-.032,y+.032]:
   w,b,r=interp(ROW,yy);bottom=[(x,b+.032+(r-b-.032)*(1-max(0,1-(x/(w-.032))**2)**.37)-.002) for x in [-.36,-.24,-.12,0,.12,.24,.36]];beam.append((yy,bottom+[(.36,.240),(-.36,.240)]))
  loft('Hull-fitting floorboard cross bearer',beam,p['wooddark'],False)
 for x in [-.28,-.14,0,.14,.28]:box('Rowboat raised floorboard',(x,-.08,.2575),(.121,2.20,.035),p['wood'],.007)
 # Exactly two supported thwarts; cleats terminate into the sloping hull wall.
 for y in [-.55,.72]:
  w,b,r=interp(ROW,y);seat_z=.445;top_width=(w-.032)*math.sqrt(max(0,1-((r-seat_z)/(r-b-.032))**(2/.74)))
  box('Supported rowing thwart',(0,y,seat_z),(2*top_width+.015,.280,.057),p['woodlight'],.014)
  for side in [-1,1]:
   box('Thwart hull cleat',(side*(top_width-.065),y,seat_z-.043),(.090,.300,.055),p['wooddark'],.006)
   knee=[];cx=side*(top_width-.14)
   for yy in [y-.048,y+.048]:
    ww,bb,rr=interp(ROW,yy);xa,xb=cx-.035,cx+.035;za=bb+.032+(rr-bb-.032)*(1-max(0,1-(xa/(ww-.032))**2)**.37)-.003;zb=bb+.032+(rr-bb-.032)*(1-max(0,1-(xb/(ww-.032))**2)**.37)-.003;knee.append((yy,[(xa,za),(xb,zb),(xb,seat_z-.026),(xa,seat_z-.026)]))
   loft('Hull-fitting thwart support knee',knee,p['wood'],False)
   for yy in [y-.080,y+.080]:cyl('Thwart flush fixing',(side*(top_width-.053),yy,seat_z+.030),.011,.006,p['steel'],v=12,b=.0005)
 # Paired oars rest in fixed metal locks: shaft touches lock yoke bottom, not floating.
 for side in [-1,1]:
  y=-.14;w,b,r=interp(ROW,y);x=side*(w+.012)
  box('Oarlock gunwale mounting pad',(x,y,r+.018),(.115,.145,.038),p['wooddark'],.007)
  cyl('Oarlock socket',(x,y,r+.054),.025,.065,p['steel'],v=24,b=.002)
  cyl('Oarlock pivot stem',(x,y,r+.102),.014,.068,p['steel'],v=20,b=.001)
  # Outboard blade points aft, inboard handle points forward; same plane through lock.
  direction=Vector((side*.93,.50,.299)).normalized();center=Vector((x,y,r+.145));a=center-direction*.62;bpt=center+direction*1.12
  rod('Long timber oar shaft',a,bpt,.021,p['woodlight'],24)
  rod('Oar hand grip',a-direction*.14,a+direction*.06,.026,p['wood'],24)
  # Yoke U is oriented perpendicular to the shaft; bottom is at shaft underside.
  crossdir=Vector((-direction.y,direction.x,0));pts=[center+crossdir*-.036+Vector((0,0,.035)),center+crossdir*-.036+Vector((0,0,-.023)),center+crossdir*.036+Vector((0,0,-.023)),center+crossdir*.036+Vector((0,0,.035))];tube('Open oarlock U yoke',[tuple(v) for v in pts],.008,p['steel'],1)
  rod('Oar wear sleeve',center-direction*.070,center+direction*.070,.024,p['wooddark'],24)
  # Closed slightly spoon-shaped blade, tapered onto the shaft.
  blade_start=center+direction*.91;blade_end=center+direction*1.56;normal=crossdir
  verts=[]
  for d,half,raisez in [(0,.035,0),(.18,.115,-.010),(.57,.130,-.032),(.65,.087,-.040)]:
   mid=blade_start+direction*d+Vector((0,0,raisez));verts.extend([tuple(mid+normal*-half+Vector((0,0,-.009))),tuple(mid+normal*half+Vector((0,0,-.009))),tuple(mid+normal*half+Vector((0,0,.009))),tuple(mid+normal*-half+Vector((0,0,.009)))])
  fs=[(0,3,2,1),(12,13,14,15)]+[(4*j+k,4*j+(k+1)%4,4*(j+1)+(k+1)%4,4*(j+1)+k) for j in range(3) for k in range(4)];mesh('Shaped broad rowing blade',verts,fs,p['wood'],.006)
 # Keel strip visible from below and two small bow eye attachment pads.
 tube('Exterior longitudinal keel',[(0,y,b-.013) for y,w,b,r in ROW[1:]],.022,p['wooddark'],1)
 box('Bow eye backing plate',(0,-1.914,.535),(.053,.017,.082),p['steel'],.004);ring('Bow mooring eye',(0,-1.939,.535),.025,.007,p['steel'],'X',24)
 return meta('city-rowboat-with-oars','二本のオール付き木製ベンチ手漕ぎボート','Rowboat with two supported oars','水辺や貸しボート置場に配置する開放型手漕ぎボート。丸い厚肉船殻と本当に凹んだ船内、曲がった肋材、持上げた床板、支持材付き二枚の座板、船縁・船底キール、金属オール受けに接する二本の柄と幅広い水かき、船首環を造形。オールを含む一式で1点。','An open rowing boat for waterfront and rental-boathouse scenes. A rounded thick hull encloses a genuinely recessed interior, curved ribs, raised floorboards, two supported thwarts, timber gunwales and exterior keel. Two long oars with broad shaped blades rest in metal oarlocks; a small bow eye finishes the assembly. Both oars count within this one model.',['rowboat','oars','waterfront','手漕ぎボート'])

def pontoon(n,x,sections,m):
 return loft(n,[(y,[(x+w*math.cos(i*math.tau/24),z+h*math.sin(i*math.tau/24)) for i in range(24)]) for y,w,z,h in sections],m)
def pedalboat():
 p=pal();sec=[(-1.58,.035,.40,.055),(-1.49,.16,.33,.18),(-1.20,.28,.30,.26),(-.65,.30,.29,.27),(.20,.30,.29,.27),(.95,.28,.30,.26),(1.35,.24,.33,.23),(1.43,.18,.34,.19)]
 for side in [-1,1]:
  x=side*.69;pontoon('Separate rounded pedal-boat pontoon',x,sec,p['blue'])
  tube('Pontoon outer rub seam',[(x+side*w*.95,y,z+.035) for y,w,z,h in sec[1:]],.018,p['dark'],1)
 # Deck does not fill the rear drive opening. Foot wells are real voids above low floors.
 box('Twin hull front connecting bridge',(0,-1.04,.557),(1.50,.34,.115),p['aqua'],.030)
 box('Twin hull rear connecting bridge',(0,.79,.556),(1.50,.49,.115),p['aqua'],.034)
 box('Central drive tunnel',(0,-.05,.575),(.18,1.59,.18),p['blue'],.025)
 for side in [-1,1]:
  x=side*.40
  box('Recessed pedal footwell floor',(x,-.24,.444),(.58,1.30,.065),p['aqua'],.021)
  box('Footwell outside raised wall',(side*.696,-.20,.592),(.093,1.65,.234),p['blue'],.029)
  box('Footwell inner side wall',(side*.105,-.20,.535),(.040,1.63,.180),p['aqua'],.012)
  for yy in [-.65,-.48,-.31,-.14,.03]:box('Footwell grip rib',(x,yy,.480),(.43,.014,.009),p['dark'],.002)
  box('Seat supported molded plinth',(x,.60,.630),(.48,.55,.20),p['blue'],.037)
  box('Separate pedal boat seat cushion',(x,.50,.765),(.52,.53,.115),p['aqua'],.045)
  box('Curved-looking molded seat back',(x,.805,.941),(.53,.12,.40),p['aqua'],.045,rot=(math.radians(-12),0,0))
  for dx in [-.18,.18]:bar('Seat back base connection',(x+dx,.762,.721),(x+dx,.849,1.055),.052,.044,p['blue'],.010)
  # Supported crank shaft spans each well, with two opposite cranks and tread pedals.
  yy=-.45;zz=.635;rod('Pedal crank axle',(x-.245,yy,zz),(x+.245,yy,zz),.020,p['steel'],24)
  for s in [-1,1]:
   xx=x+s*.225;box('Crank bearing support',(xx,yy,.555),(.045,.090,.15),p['blue'],.008)
   cyl('Pedal shaft bearing',(xx,yy,zz),.036,.054,p['dark'],'X',v=24,b=.002)
   end=Vector((xx,yy+s*.095,zz+s*.055));bar('Fixed opposing pedal crank',(xx,yy,zz),end,.027,.020,p['steel'],.003)
   rod('Pedal spindle',end-Vector((.045,0,0)),end+Vector((.045,0,0)),.011,p['steel'],20)
   box('Pedal tread block',end,(.098,.080,.032),p['dark'],.006)
   for oy in [-.022,0,.022]:box('Pedal tread bar',end+Vector((0,oy,.019)),(.092,.006,.009),p['rubber'],.001)
 # Visible fixed paddlewheel occupies the actual open rear interval between pontoons.
 cy,cz=1.26,.407;rod('Paddlewheel through axle',(-.69,cy,cz),(.69,cy,cz),.034,p['steel'],28)
 for side in [-1,1]:
  cyl('Paddlewheel mounted bearing',(side*.45,cy,cz),.070,.095,p['dark'],'X',v=28,b=.005)
  box('Paddle bearing deck bracket',(side*.45,cy,.536),(.12,.19,.27),p['blue'],.016)
  ring('Paddlewheel side open rim',(side*.335,cy,cz),.265,.015,p['steel'],'X',40)
  cyl('Paddlewheel central hub',(side*.335,cy,cz),.060,.045,p['steel'],'X',v=28,b=.003)
  for i in range(8):
   an=i*math.tau/8;rod('Paddlewheel open radial spoke',(side*.335,cy,cz),(side*.335,cy+.265*math.cos(an),cz+.265*math.sin(an)),.011,p['steel'],16)
 for i in range(8):
  an=i*math.tau/8;box('Fixed paddle blade',(0,cy+.265*math.cos(an),cz+.265*math.sin(an)),(.69,.070,.180),p['blue'],.012,rot=(an-math.pi/2,0,0))
 box('Drive exterior shield',(0,.69,.645),(.225,.47,.22),p['dark'],.033)
 box('Rudder transom bracket',(0,.93,.649),(.19,.125,.13),p['steel'],.014)
 rod('Rear rudder vertical shaft',(0,.93,.86),(0,.93,.60),.023,p['steel'],24)
 # Rudder sits just behind drive, avoiding a blade intersection.
 bar('Rudder offset tiller arm',(0,.93,.84),(.0,1.82,.84),.041,.044,p['steel'],.005)
 rod('Rudder aft pivot',(0,1.82,.86),(0,1.82,.12),.024,p['steel'],24)
 box('Fixed external steering rudder',(0,1.845,.205),(.046,.31,.34),p['dark'],.018)
 bar('Hand steering lever',(0,.13,.66),(0,.31,.98),.028,.029,p['steel'],.005);cyl('Hand steering grip',(0,.31,1.01),.034,.12,p['dark'],v=24,b=.008)
 for side in [-1,1]:
  tube('Boarding side handhold',[(side*.79,.20,.65),(side*.86,.25,.78),(side*.86,.55,.78),(side*.79,.60,.65)],.020,p['steel'],2)
 return meta('city-two-seat-pedal-boat','二座席・双胴式ペダルボート','Two-seat twin-pontoon pedal boat','公園の池や貸しボート区画に配置する二座席ペダルボート。二つの別個の丸い浮体、連結デッキ、低い底と盛上がった縁を持つ二つの足元区画、支持された独立座席、固定ペダル・軸受、後部開口に見えるスポーク付き外輪と駆動覆い、外部舵と手動レバーを造形。一式1点。','A two-seat pedal boat for park-pond and rental waterfront scenes. Two separate rounded pontoons carry connecting deck bridges, genuinely recessed foot wells, independently supported seats, fixed pedals and bearings. The rear opening exposes a spoked paddlewheel and drive cover; an offset exterior rudder and hand lever distinguish the assembly from a rowing hull. One complete model.',['pedal-boat','paddlewheel','twin-pontoon','ペダルボート'])

def inflated_collar(n,points,radius,m):
 pts=[Vector(v) for v in catmull(points,6)];N=20;vs=[]
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();side=Vector((-tangent.y,tangent.x,0)).normalized();r=radius
  # Rounded-looking closed tips, with no UV-sphere normal instability.
  edge=min(i,len(pts)-1-i);r*= [.18,.65,.90,1.0][min(edge,3)]
  for j in range(N):
   a=j*math.tau/N;vs.append(tuple(p+side*(math.cos(a)*r)+Vector((0,0,math.sin(a)*r))))
 fs=[tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))]+[(i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j) for i in range(len(pts)-1) for j in range(N)]
 return mesh(n,vs,fs,m,smooth=True)
RIB=[(-2.13,.065,.40,.66),(-1.95,.34,.23,.60),(-1.65,.57,.10,.56),(-1.20,.74,.025,.53),(-.50,.80,0,.52),(.30,.80,0,.52),(1.10,.76,.025,.52),(1.65,.70,.075,.54),(1.80,.69,.09,.55)]
def rib_profile(w,b,r):
 # Hard chines intentionally remain hard; the rigid shell is not a rounded rowboat.
 outer=[(-w,r),(-w*.94,b+.22),(-w*.57,b+.065),(0,b),(w*.57,b+.065),(w*.94,b+.22),(w,r)]
 inner=[(w-.035,r),(w*.94-.035,b+.25),(w*.57-.028,b+.11),(0,b+.047),(-w*.57+.028,b+.11),(-w*.94+.035,b+.25),(-w+.035,r)]
 return outer+inner

def rescueboat():
 p=pal();loft('Rigid open hard-chine hull',[(y,rib_profile(w,b,r)) for y,w,b,r in RIB],p['gray'],False)
 bw,bb,br=RIB[0][1:];loft('Rigid bow stem closing wall',[(-2.155,rib_profile(bw,bb,br)[:7]),(-2.105,rib_profile(bw,bb,br)[:7])],p['gray'],False)
 w,b,r=RIB[-1][1:];cross=rib_profile(w,b,r)[:7];loft('Thick outboard transom',[(1.72,cross),(1.81,cross)],p['gray'],False)
 collar=[(-.79,1.91,.64),(-.91,1.65,.64),(-.99,.70,.64),(-.99,-.35,.65),(-.88,-1.22,.68),(-.63,-1.79,.74),(0,-2.15,.80),(.63,-1.79,.74),(.88,-1.22,.68),(.99,-.35,.65),(.99,.70,.64),(.91,1.65,.64),(.79,1.91,.64)]
 inflated_collar('Continuous shaped inflatable-style U collar',collar,.255,p['orange'])
 # A dark rubbing strake follows the outside midheight, with visible section joints.
 for side in [-1,1]:
  pts=[(side*1.18,1.62,.64),(side*1.245,.70,.64),(side*1.24,-.35,.65),(side*1.12,-1.22,.68),(side*.79,-1.92,.74),(side*.03,-2.405,.80)];cable('Collar outer abrasion strake',pts,.030,p['dark'],5)
  for y in [-1.15,-.35,.50,1.30]:
   # Top grab-rope saddles sit on collar; the sagging rope visibly threads through.
   x=side*(.99 if y>-.70 else .90);zz=.911 if y>-.70 else .938
   box('Collar rope attachment patch',(x,y,zz-.014),(.105,.155,.031),p['dark'],.013)
   ring('Grab rope raised attachment',(x,y,zz+.020),.029,.008,p['steel'],'X',24)
  pts=[]
  for j,y in enumerate([-1.15,-.75,-.35,.075,.50,.90,1.30]):
   x=side*(.99 if y>-.70 else .90);zz=(.956 if y<-.70 else .929)-(.055 if j%2 else 0);pts.append((x,y,zz))
  cable('Attached sagging grab rope',pts,.012,p['cream'],5)
  # Three visible closed collar band hoops follow the tube cross section.
  for y in [-.35,.70,1.35]:
   cx=side*(.99 if y<1 else .95);ring('Collar reinforcement band',(cx,y,.64),.255,.014,p['red'],'Y',32)
 # Low deck fitted within the shell; surrounding recesses remain visibly open.
 outline=[(-.53,-1.27),(-.63,-.80),(-.61,1.10),(-.56,1.57),(.56,1.57),(.61,1.10),(.63,-.80),(.53,-1.27),(0,-1.56)]
 extruded_outline('Rigid nonslip cockpit sole',outline,.320,.065,p['dark'],.012)
 for y in [-1.05,-.67,-.29,.10,.49,.88,1.27]:box('Cockpit sole transverse grip',(0,y,.357),(1.02,.017,.009),p['rubber'],.002)
 # Center console base, shaped body and blank unbranded steering facia.
 box('Console connected deck pedestal',(0,-.21,.335),(.48,.52,.10),p['gray'],.016)
 sections=[(-.46,[(-.225,.36),(.225,.36),(.190,.98),(-.190,.98)]),(.13,[(-.245,.36),(.245,.36),(.19,.86),(-.19,.86)])]
 loft('Tapered center steering console',sections,p['cream'],False)
 box('Angled blank instrument panel',(0,.166,.841),(.36,.039,.20),p['dark'],.012,rot=(math.radians(17),0,0))
 # Steering wheel lies behind console, connected by a visible inclined shaft.
 hub=Vector((0,.286,.919));axis=Vector((0,.90,.435)).normalized();rod('Console steering column',(0,.112,.835),hub,.025,p['steel'],24)
 steering=ring('Fixed three-spoke steering wheel',hub,.145,.016,p['dark'],'Y',36);steering.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 u=Vector((1,0,0));v=axis.cross(u)
 for j in range(3):
  a=j*math.tau/3;rod('Steering wheel spoke',hub,hub+(u*math.cos(a)+v*math.sin(a))*.139,.012,p['steel'],18)
 rod('Fixed throttle lever',(.238,-.04,.80),(.278,.02,.98),.013,p['steel'],20);cyl('Throttle grip',(.278,.02,1.002),.024,.065,p['dark'],v=24,b=.005)
 # One connected aft bench with actual feet and rear back support.
 box('Aft bench cushion',(0,.83,.622),(1.14,.40,.101),p['seat'],.036)
 box('Bench rigid substrate',(0,.83,.554),(1.13,.40,.048),p['gray'],.011)
 for x in [-.44,.44]:
  box('Bench floor-connected leg',(x,.83,.424),(.11,.28,.27),p['gray'],.016)
  bar('Bench back support',(x,1.00,.53),(x,1.075,.895),.042,.039,p['steel'],.005)
 box('Aft bench back cushion',(0,1.054,.799),(1.08,.102,.24),p['seat'],.033,rot=(math.radians(-9),0,0))
 # Entire original exterior outboard, deliberately unbranded and static.
 for x in [-.14,.14]:
  box('Outboard transom clamp plate',(x,1.822,.460),(.091,.14,.294),p['steel'],.012)
  box('Outboard upper transom saddle',(x,1.815,.567),(.105,.25,.058),p['dark'],.010)
  rod('Outboard clamp screw',(x,1.695,.460),(x,1.847,.460),.014,p['steel'],20)
  bar('Clamp screw T handle',(x-.045,1.675,.460),(x+.045,1.675,.460),.012,.014,p['dark'],.002)
 rod('Outboard tilt pivot',(-.22,1.92,.64),(.22,1.92,.64),.036,p['steel'],24)
 box('Outboard mounting spine',(0,2.00,.522),(.22,.24,.34),p['dark'],.025)
 box('Rounded original motor cowling',(0,2.12,.914),(.49,.59,.48),p['dark'],.085)
 box('Outboard cowling top cap',(0,2.12,1.157),(.41,.47,.037),p['gray'],.018)
 for side in [-1,1]:
  box('Outboard blank side inset',(side*.247,2.15,.942),(.018,.33,.14),p['gray'],.008)
  for yy in [2.04,2.10,2.16,2.22]:box('Cowling side intake fin',(side*.258,yy,1.058),(.014,.024,.043),p['black'],.002)
 box('Outboard lower leg',(0,2.125,.421),(.16,.23,.59),p['gray'],.028)
 box('Outboard anti-ventilation plate',(0,2.15,.215),(.44,.40,.033),p['dark'],.012)
 # Streamlined lower gearbox, skeg and three obvious pitched propeller blades.
 pontoon('Outboard lower gearbox',0,[(1.99,.040,.077,.043),(2.05,.082,.077,.080),(2.25,.071,.077,.070),(2.33,.039,.077,.037)],p['dark'])
 rod('Outboard propeller spindle',(0,2.22,.077),(0,2.47,.077),.027,p['steel'],24)
 cyl('Outboard propeller hub',(0,2.395,.077),.063,.12,p['steel'],'Y',v=28,b=.008)
 for i in range(3):
  an=i*math.tau/3
  # Broad curved-looking triangular outline, thick and slightly pitched around radial axis.
  coords=[(.040,-.025),(.13,-.075),(.205,-.027),(.185,.055),(.085,.060)]
  N=len(coords);vs=[]
  for dy in [-.012,.012]:
   for rr,ta in coords:vs.append((rr*math.cos(an)+ta*math.sin(an),2.395+dy+ta*.5,.077+rr*math.sin(an)-ta*math.cos(an)))
  fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(j,(j+1)%N,N+(j+1)%N,N+j) for j in range(N)];mesh('Three fixed outboard propeller blades',vs,fs,p['steel'],.006)
 # A thick nonrectangular skeg, not an unsupported flat card.
 poly=[(2.04,.08),(2.25,.07),(2.30,-.20),(2.18,-.22)];vs=[(x,y,z) for x in [-.018,.018] for y,z in poly];mesh('Outboard lower skeg',vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],p['dark'],.006)
 cable('Connected outboard service hose',[(.25,.13,.43),(.43,.46,.38),(.46,1.19,.38),(.31,1.70,.49),(.17,1.97,.63)],.018,p['rubber'],5)
 ring('Rigid hull bow towing eye',(0,-2.164,.406),.035,.009,p['steel'],'X',28)
 return meta('city-rigid-inflatable-rescue-boat','船外機付きリジッドインフレータブル救助艇外形','Rigid inflatable rescue boat exterior','港湾や救助艇置場の背景に置く、小型の無銘柄リジッドインフレータブル艇。硬いチャインを持つ開放船殻、連続した丸いU字カラーと擦れ止め・取付け済みロープ、低い床、支持された後部ベンチ、中央コンソールと舵輪、トランサムの固定具、独自形状の船外機外装・下部脚・スケグ・三枚の固定プロペラを造形。一式1点で、救助・浮力・航行・安全認証は一切主張しません。','A small unbranded rigid-inflatable craft exterior for harbour and rescue-station backgrounds. The hard-chine open hull has a continuous round U collar, abrasion strip and attached grab ropes, low sole, supported aft bench, center console and steering wheel. A clamped transom mount carries an original outboard cowling, lower leg, skeg and three fixed propeller blades. One assembly; no rescue, flotation, navigation or safety certification is claimed.',['rigid-inflatable','outboard','rescue-boat-exterior','救助艇外形'])

PWC=[(-1.48,.035,.29,.42),(-1.38,.20,.17,.53),(-1.17,.37,.09,.60),(-.83,.51,.035,.61),(-.35,.57,.015,.56),(.20,.58,.02,.52),(.72,.55,.055,.48),(1.15,.47,.12,.43),(1.37,.40,.18,.42)]
def personalcraft():
 p=pal()
 sections=[]
 for y,w,b,r in PWC:
  # Closed V-bottom hull, independent from its molded upper deck and foot channels.
  drop=min(.145,(r-b)*.50)
  sections.append((y,[(-w,r),(-w*.98,b+(r-b)*.43),(-w*.60,b+(r-b)*.14),(0,b),(w*.60,b+(r-b)*.14),(w*.98,b+(r-b)*.43),(w,r),(.78*w,r-drop),(-.78*w,r-drop)]))
 lower=loft('Personal watercraft V-bottom lower hull',sections,p['black'],True)
 for edge in lower.data.edges:
  if edge.vertices[0]%9==edge.vertices[1]%9:edge.use_edge_sharp=True
 deck=[]
 for y,w,b,r in PWC:
  cockpit=max(0,min(1,(y+.85)/.40))*max(0,min(1,(1.29-y)/.25));z=r+.018
  path=[(-w,z),(-.88*w,z+.025),(-.78*w,z-.10*cockpit),(-.39*w,z-.10*cockpit),(-.30*w,z+.12*cockpit),(0,z+.15*cockpit),(.30*w,z+.12*cockpit),(.39*w,z-.10*cockpit),(.78*w,z-.10*cockpit),(.88*w,z+.025),(w,z)]
  # Reverse lower skin creates a closed thick molded deck, with real recessed channels.
  deck.append((y,path+[(x,zz-.035) for x,zz in reversed(path)]))
 loft('Molded upper deck with actual foot channels',deck,p['lime'],False)
 for side in [-1,1]:
  tube('Continuous hull-deck rubbing seam',[(side*w,y,r+.003) for y,w,b,r in PWC],.018,p['dark'],1)
  # Sole grips follow the floor of each real molded side channel.
  for y in [-.28,-.10,.08,.26,.44,.62,.80,.98]:
   w,b,r=interp(PWC,y);box('Foot channel traction bar',(side*w*.585,y,r-.069),(.18,.026,.018),p['rubber'],.004)
 # Long rising saddle with variable widths/heights, on an actual molded center pedestal.
 seatsections=[(-.39,[(-.095,.76),(.095,.76),(.09,.88),(-.09,.88)]),(-.18,[(-.16,.73),(.16,.73),(.15,.90),(-.15,.90)]),(.23,[(-.19,.68),(.19,.68),(.18,.89),(-.18,.89)]),(.73,[(-.19,.65),(.19,.65),(.18,.91),(-.18,.91)]),(1.03,[(-.14,.63),(.14,.63),(.13,.81),(-.13,.81)])]
 # Saddle support fills only the center region, leaving both foot channels open.
 loft('Long saddle pedestal',[(.32+(y-.32)*.96,[(x*.92,z-.14) for x,z in cross]) for y,cross in seatsections],p['lime'],True)
 loft('Long sculpted upholstered saddle',seatsections,p['seat'],True)
 for y in [.14,.63]:box('Saddle transverse seam',(0,y,.899),(.326,.014,.008),p['dark'],.003)
 # Original handlebar cowling, visible steering stem and two fixed hand grips.
 extruded_outline('Raised steering cowling',[(-.20,-.78),(-.28,-.56),(-.19,-.33),(.19,-.33),(.28,-.56),(.20,-.78)],.731,.19,p['lime'],.025)
 rod('Connected steering stem',(0,-.57,.784),(0,-.43,1.035),.039,p['dark'],28)
 tube('Raised curved handlebars',[(-.40,-.39,1.023),(-.29,-.40,1.037),(-.20,-.44,1.058),(0,-.43,1.058),(.20,-.44,1.058),(.29,-.40,1.037),(.40,-.39,1.023)],.024,p['steel'],2)
 for side in [-1,1]:
  rod('Handlebar rubber grip',(side*.27,-.40,1.037),(side*.435,-.385,1.015),.032,p['rubber'],28)
  bar('Fixed handle squeeze lever',(side*.26,-.434,1.015),(side*.405,-.448,.998),.017,.013,p['dark'],.003)
  box('Handlebar control pod',(side*.24,-.402,1.041),(.055,.078,.066),p['dark'],.011)
 box('Blank unlit instrument face',(0,-.575,.843),(.17,.12,.016),p['black'],.015,rot=(math.radians(12),0,0))
 # A broad aft deck and attached fold-style boarding step, not part of a boat hull.
 # Each pad follows the actual piecewise-planar floor of the exported deck.
 # Interpolate the existing deck stations, not a continuous formula between them.
 floors=[(yy,rr+.018-.10*max(0,min(1,(yy+.85)/.40))*max(0,min(1,(1.29-yy)/.25))) for yy,ww,bb,rr in PWC]
 for side in [-1,1]:
  pad_sections=[]
  for yy in [1.03,1.10,1.15,1.22,1.29,1.32]:
   ww,bb,rr=interp(PWC,yy);zz=interp(floors,yy)[0];xa,xb=sorted([side*.46*ww,side*.72*ww]);pad_sections.append((yy,[(xa,zz-.002),(xb,zz-.002),(xb,zz+.012),(xa,zz+.012)]))
  pad=loft('Separate conforming aft deck grip pad',pad_sections,p['rubber'],False)
  finish(pad,pad.name,None,.0015,False)
 for side in [-1,1]:
  box('Boarding step hull mount',(side*.32,1.379,.333),(.10,.09,.13),p['steel'],.010)
  tube('Boarding step connected return',[(side*.32,1.385,.34),(side*.36,1.57,.16),(side*.32,1.65,.12)],.024,p['steel'],2)
 rod('Aft boarding step crossbar',(-.32,1.65,.12),(.32,1.65,.12),.034,p['rubber'],28)
 # Closed thick transom joins the depressed lower body to the upper aft deck.
 box('PWC connected solid stern transom',(0,1.358,.344),(.70,.036,.150),p['black'],.006)
 # Visible exterior jet nozzle has a real open ring and dark recessed inner face.
 sleeve('Open waterjet nozzle exterior',(0,1.447,.251),.105,.078,.20,p['steel'],'Y',32)
 cyl('Waterjet recessed dark inner face',(0,1.379,.251),.079,.012,p['black'],'Y',v=32,b=.001)
 ring('Waterjet outlet rim',(0,1.551,.251),.093,.012,p['dark'],'Y',32)
 for side in [-1,1]:box('Waterjet nozzle side pivot',(side*.112,1.454,.251),(.038,.06,.048),p['dark'],.007)
 box('Underside ride plate',(0,.97,.118),(.48,.53,.022),p['steel'],.008,rot=(math.radians(8),0,0))
 # Intake backing is shallow below the bottom; grille bars are visible, not a functional duct.
 box('Underside intake dark recess',(0,.32,.018),(.24,.46,.014),p['rubber'],.010)
 for x in [-.084,-.028,.028,.084]:box('Underside intake grille rail',(x,.32,.005),(.017,.43,.017),p['steel'],.003)
 ring('Front towing eye',(0,-1.491,.333),.023,.007,p['steel'],'X',24)
 return meta('city-personal-watercraft','細長いサドル付きパーソナルウォータークラフト','Personal watercraft with long saddle','都市の水辺・艇庫背景に配置する、独自の小型サドル式ウォータークラフト。V形の船底と成形デッキ、実際に低くなった左右の足元溝と滑り止め、長い成形サドルと支持部、立上がり舵軸・ハンドル、無表示の計器面、後部乗込みステップ、開口した噴射ノズル外形と船底グリルを造形。一式1点で、ボートの縮小版や色違いではありません。','A compact original saddle-style personal watercraft for urban waterfront and boathouse scenes. Its V-bottom body and molded deck form two genuinely lowered foot channels with grip strips. A long shaped saddle/support, raised steering stem and handlebars, blank instrument face, attached rear boarding step, open jet-nozzle exterior and underside grille complete the distinct assembly. It is one model, not a resized or recolored open boat.',['personal-watercraft','saddle','waterjet-exterior','ウォータークラフト'])

def meta(slug,ja,en,dja,den,tags):
 dja+=' 最下点をY=0とする水平中央原点です。水面の高さ・喫水位置は配置側で選んでください。水・人物・物理挙動・操縦・浮力・流体力学・救助機能は含まず、静的外形のみです。'
 den+=' The horizontally centered origin places the lowest geometry point at Y=0; choose the waterline and immersion height in your own scene. No water, people, physics, driving, flotation, hydrodynamics or rescue functionality is included: this is a static exterior assembly.'
 return slug,ja,en,dja,den,tags

BUILDERS=[rowboat,pedalboat,rescueboat,personalcraft]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-052/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true');a=parser.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  bpy.context.view_layer.update()
  publish_asset(*s,out,'scripts/city_expansion/urban_watercraft_models.py',azimuth=-55,elevation=32)
