"""Original garage service equipment scene props. Xenoah, CC BY 4.0.
Static unrigged assemblies, not working or certified equipment designs.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(white=mat('Powder-coated light service metal',(.48,.54,.54),.12,.44),paint=mat('Deep blue service paint',(.035,.17,.29),.18,.42),steel=mat('Brushed exposed steel',(.40,.47,.51),.76,.34),bright=mat('Bright small hardware',(.59,.65,.68),.81,.28),dark=mat('Dark mechanism trim',(.034,.043,.053),.16,.53),rubber=mat('Rubber feet and hoses',(.014,.019,.024),0,.77),screen=mat('Blank inactive control face',(.020,.049,.065),.10,.30),red=mat('Red control details',(.48,.025,.015),.05,.49),amber=mat('Amber fixed control details',(.62,.29,.025),.03,.47))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
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
def frame(n,w,h,t,d,p,m,bev=.002):
 vs=[]
 for ww,hh,y in [(w,h,-d/2),(w,h,d/2),(w-2*t,h-2*t,d/2),(w-2*t,h-2*t,-d/2)]:vs.extend([(-ww/2,y,-hh/2),(ww/2,y,-hh/2),(ww/2,y,hh/2),(-ww/2,y,hh/2)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)];o=mesh(n,vs,fs,m,bev);o.location=p
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 return o

def smooth_cable(name,points,r,m):
 pts=[Vector(x) for x in points];out=[]
 for i in range(len(pts)-1):
  p0=pts[max(0,i-1)];p1=pts[i];p2=pts[i+1];p3=pts[min(len(pts)-1,i+2)]
  for j in range(9):
   t=j/9;out.append(tuple(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)))
 out.append(tuple(pts[-1]));return tube(name,out,r,m,1)
def caster(n,x,y,r,p):
 cyl(n+' rubber wheel',(x,y,r),r,.039,p['rubber'],'X',v=28,b=.004)
 cyl(n+' steel hub',(x,y,r),r*.45,.047,p['steel'],'X',v=24,b=.001)
 for side in [-1,1]:box(n+' caster fork',(x+side*.029,y,r*1.35),(.010,r*.93,r*.95),p['steel'],.002)
 box(n+' fork bridge',(x,y,r*1.82),(.071,r*.93,.016),p['steel'],.002)
 cyl(n+' swivel stem',(x,y,r*2.05),.020,r*.45,p['steel'],v=24,b=.001)
 box(n+' fixed brake pedal',(x,y-r*.63,r*1.57),(.040,r*.60,.016),p['dark'],.002)

def bolt(n,p,r,m,axis='Z'):
 return cyl(n,p,r,r*.60,m,axis,v=6,b=min(.001,r*.08))
def profile_body(n,profile,m,N=48):
 vs=[(r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),z) for r,z in profile for i in range(N)];fs=[]
 for j in range(len(profile)):
  for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,((j+1)%len(profile))*N+(i+1)%N,((j+1)%len(profile))*N+i))
 o=mesh(n,vs,fs,m)
 for f in o.data.polygons:f.use_smooth=f.index//N not in [0,len(profile)-1]
 return o

def two_post_lift():
 p=pal()
 for side in [-1,1]:
  x=side*1.425
  box('Lift column anchored foot',(x,0,.040),(.520,.635,.080),p['steel'],.011)
  for dx in [-.188,.188]:
   for y in [-.241,.241]:bolt('Column anchor head',(x+dx,y,.086),.026,p['bright'])
  box('Two-post lift vertical column',(x,.020,1.488),(.257,.312,2.848),p['paint'],.019)
  box('Column rear service cover',(x,.186,1.462),(.191,.022,2.466),p['dark'],.005)
  for z in [.293,.793,1.293,1.793,2.293,2.643]:
   for dx in [-.077,.077]:bolt('Column service cover fastener',(x+dx,.199,z),.009,p['steel'],'Y')
  for yy in [-.108,.108]:rod('Visible carriage guide rod',(x-side*.151,yy,.165),(x-side*.151,yy,2.732),.018,p['steel'],24)
  box('Fixed lift carriage',(x-side*.175,.015,.575),(.161,.358,.494),p['white'],.014)
  for yy in [-.132,.132]:
   cyl('Swing arm hinge hub',(x-side*.175,yy,.379),.069,.170,p['steel'],v=32,b=.005)
   a=Vector((x-side*.175,yy,.367));b=Vector((side*.690,math.copysign(.590,yy),.367));c=Vector((side*.472,math.copysign(.923,yy),.367))
   bar('Outer rectangular lift arm',a,b,.110,.084,p['paint'],.010)
   bar('Visible telescoping inner lift arm',b,c,.075,.060,p['steel'],.006)
   cyl('Lift pad threaded stem',c+Vector((0,0,.053)),.023,.131,p['steel'],v=28,b=.002)
   cyl('Circular rubber lift pad',c+Vector((0,0,.127)),.086,.033,p['rubber'],v=32,b=.004)
   for j in range(5):ring('Pad adjustment thread',c+Vector((0,0,.026+j*.014)),.024,.003,p['steel'],v=24)
  box('Column lower cable junction',(x,.210,.222),(.138,.074,.182),p['dark'],.009)
 box('Overhead lift cross-member',(0,.020,2.851),(3.082,.236,.178),p['paint'],.015)
 rod('Overhead lower limit-bar exterior',(-1.270,-.116,2.679),(1.270,-.116,2.679),.017,p['dark'],24)
 for x in [-1.258,1.258]:bar('Limit-bar connected bracket',(x,-.116,2.679),(x,-.075,2.794),.025,.024,p['steel'],.003)
 # One external motor/reservoir/control assembly is attached to the right column.
 box('Lift motor mounting bracket',(1.608,.076,1.187),(.172,.229,.255),p['steel'],.006)
 cyl('Lift pump motor exterior',(1.708,.076,1.287),.083,.282,p['dark'],v=32,b=.005)
 for z in [1.191,1.225,1.259,1.293,1.327,1.361]:ring('Pump motor cooling ring',(1.708,.076,z),.085,.006,p['steel'],v=32)
 box('Lift fluid reservoir exterior',(1.708,.076,.950),(.190,.192,.308),p['white'],.018)
 cyl('Reservoir filler cap',(1.743,.076,1.116),.026,.025,p['dark'],v=24,b=.002)
 box('Lift control mounting bracket',(1.535,-.152,1.468),(.141,.100,.181),p['steel'],.005)
 box('Lift blank control enclosure',(1.591,-.215,1.468),(.192,.095,.220),p['white'],.012)
 cyl('Lift fixed red control',(1.591,-.271,1.500),.027,.021,p['red'],'Y',v=24,b=.003)
 box('Lift unlabelled control button',(1.591,-.268,1.426),(.039,.015,.030),p['dark'],.004)
 smooth_cable('Fixed external hydraulic-looking line',[(1.708,.124,1.154),(1.831,.158,1.110),(1.837,.226,.685),(1.655,.228,.296),(1.450,.230,.249)],.009,p['rubber'])
 return ('city-two-post-vehicle-lift','4支持腕付き2柱車両リフト','Two-post vehicle lift with four support arms','整備工場のサービス区画に置く2柱式車両リフト。底板とアンカー外形、背面カバー・案内棒、固定キャリッジ、四本の伸縮風支持腕とゴム受け、上部梁・下側バー、片側ポンプ/タンク/操作箱の外形と曲線配管を造形。車両は含まず一式1点。床面中央原点で柱間の配置寸法は実測バウンディング値を参照してください。昇降・油圧・衝突・荷重や安全規格適合を実装・検証した実用品設計ではありません。','A two-post lift for vehicle-service workshop backgrounds. It has anchored-looking base plates, rear column covers/guide rods, fixed carriages, four telescoping-style arms and rubber pads, overhead beam/lower bar, and one side-mounted pump/reservoir/control exterior with curved fixed line. The complete assembly counts once and includes no vehicle. Place using its ground-centered origin and measured bounding dimensions. Lifting, hydraulics, collisions, load capacity and safety compliance are neither implemented nor validated.',['garage','vehicle-lift','workshop','車両リフト'])

def wheel_balancer():
 p=pal()
 box('Wheel balancer plinth',(-.140,0,.073),(.736,.614,.113),p['dark'],.021)
 for x in [-.421,.141]:
  for y in [-.225,.225]:cyl('Balancer rubber foot',(x,y,.025),.040,.050,p['rubber'],v=24,b=.004)
 box('Wheel balancer main cabinet',(-.140,0,.475),(.671,.551,.715),p['paint'],.029)
 box('Balancer rear service panel',(-.140,.286,.484),(.521,.023,.531),p['white'],.010)
 for z in [.306,.350,.394,.438]:box('Balancer rear grille',(-.140,.302,z),(.351,.012,.016),p['dark'],.002)
 for x in [-.369,.089]:
  for z in [.242,.727]:bolt('Balancer panel screw',(x,.300,z),.011,p['steel'],'Y')
 # Ten shallow empty weight compartments, built with a floor and dividers.
 box('Wheel weight tray floor',(-.140,-.014,.854),(.724,.622,.035),p['dark'],.010)
 for x in [-.487,.207]:box('Weight tray outside wall',(x,-.014,.885),(.024,.622,.067),p['white'],.004)
 for y in [-.313,-.014,.285]:box('Weight tray transverse wall',(-.140,y,.885),(.694,.022,.067),p['white'],.004)
 for x in [-.350,-.210,-.070,.070]:box('Weight tray compartment divider',(x,-.014,.879),(.014,.576,.055),p['dark'],.002)
 cyl('Balancer spindle bearing mount',(.221,0,.696),.112,.139,p['white'],'X',v=40,b=.006)
 cyl('Exposed horizontal balancing spindle',(.523,0,.696),.029,.512,p['steel'],'X',v=32,b=.002)
 # A simple locating cone is parked on the spindle; no wheel or measurement is supplied.
 N=32;vs=[]
 for x,r in [(.411,.083),(.529,.038)]:vs.extend((x,r*math.cos(i*math.tau/N),.696+r*math.sin(i*math.tau/N)) for i in range(N))
 fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)];mesh('Balancer wheel-centering cone',vs,fs,p['steel'])
 cyl('Fixed spindle locking nut',(.720,0,.696),.052,.052,p['dark'],'X',v=6,b=.003)
 for i in range(3):
  a=i*math.tau/3;rod('Spindle nut handle',(.720,.036*math.cos(a),.696+.036*math.sin(a)),(.720,.093*math.cos(a),.696+.093*math.sin(a)),.010,p['dark'],16)
 # Closed thick half-cylinder guard; pivoted upright behind the empty spindle.
 N=32;vs=[]
 for x,r in [(-.164,.352),(.164,.352),(.164,.327),(-.164,.327)]:
  for i in range(N+1):a=i*math.pi/N;vs.append((x,r*math.cos(a),r*math.sin(a)))
 fs=[]
 for k in range(4):
  for i in range(N):fs.append((k*(N+1)+i,k*(N+1)+i+1,((k+1)%4)*(N+1)+i+1,((k+1)%4)*(N+1)+i))
 fs.extend([(0,N+1,2*(N+1),3*(N+1)),(N,4*N+3,3*N+2,2*N+1)])
 guard=mesh('Raised curved wheel guard',vs,fs,p['dark']);guard.location=(.537,.270,1.085);guard.rotation_euler[0]=math.radians(48)
 for f in guard.data.polygons:f.use_smooth=f.index<4*N and f.index//N in [0,2]
 rod('Guard hinge shaft',(.120,.270,1.085),(.714,.270,1.085),.029,p['steel'],28)
 for xx in [.390,.684]:bar('Curved guard connected hinge arm',(xx,.270,1.085),(xx,.270+.338*math.cos(math.radians(48)),1.085+.338*math.sin(math.radians(48))),.033,.027,p['dark'],.003)
 bar('Cabinet guard pivot support',(.128,.247,.831),(.128,.270,1.085),.065,.052,p['paint'],.005)
 cyl('Guard fixed pivot cap',(.105,.270,1.085),.049,.032,p['white'],'X',v=28,b=.003)
 rod('Control mast',(-.350,.219,.895),(-.350,.223,1.197),.025,p['steel'],24)
 box('Balancer control head',(-.350,.197,1.246),(.358,.113,.233),p['white'],.017,rot=(math.radians(-12),0,0))
 box('Blank balance readout',(-.350,.132,1.272),(.273,.014,.090),p['screen'],.005,rot=(math.radians(-12),0,0))
 for x in [-.450,-.385,-.320,-.255]:box('Unlabelled balance control key',(x,.124,1.199),(.039,.017,.027),p['dark'],.003)
 return ('city-wheel-balancing-machine','保護フードを開いた車輪バランサー','Wheel balancing machine with raised guard','整備工場のタイヤ作業背景に置く車輪バランサー。主軸と固定位置決め円すい・締付具、上げた厚みのある半円ガードと支点、十区画の空の重りトレー、無表示の操作ヘッド、背面サービス板と通気部を造形。タイヤを外す交換機とは用途が異なり、車輪は付属しません。一式1点で、回転・計測・校正・電装・安全性能は未実装・未検証です。','A wheel-balancer exterior for tyre-service workshop scenes. It has an exposed spindle with fixed locating cone/locking handle, raised thick curved guard and pivot, ten empty weight-tray compartments, blank control head, rear service panel and vents. Its balancing purpose differs from a tyre-removal machine; no wheel is included. The complete assembly counts once. Rotation, measurement, calibration, electrical behavior and safety performance are unimplemented and untested.',['garage','wheel-balancer','workshop','車輪バランサー'])

def parts_washer():
 p=pal()
 for x in [-.359,.359]:
  for y in [-.224,.224]:
   box('Washer connected support leg',(x,y,.414),(.049,.049,.730),p['paint'],.005)
   box('Washer rubber foot',(x,y,.036),(.079,.079,.072),p['rubber'],.007)
 box('Parts washer lower shelf',(0,0,.264),(.766,.487,.033),p['white'],.006)
 for x in [-.377,.377]:box('Shelf raised edge',(x,0,.284),(.017,.487,.040),p['paint'],.003)
 box('Parts washer basin floor',(0,0,.798),(.884,.592,.047),p['steel'],.008)
 for x in [-.432,.432]:box('Parts washer side wall',(x,0,.897),(.037,.592,.226),p['paint'],.008)
 for y in [-.281,.281]:box('Parts washer end wall',(0,y,.897),(.850,.037,.226),p['paint'],.008)
 for x in [-.437,.437]:box('Basin bright side rim',(x,0,1.014),(.048,.622,.025),p['steel'],.005)
 for y in [-.294,.294]:box('Basin bright end rim',(0,y,1.014),(.892,.042,.025),p['steel'],.005)
 # Elevated removable-looking perforated rack leaves real gaps and visible basin floor.
 for x in [-.345,-.230,-.115,0,.115,.230,.345]:box('Wash rack longitudinal bar',(x,0,.851),(.014,.433,.018),p['steel'],.002)
 for y in [-.201,-.100,0,.100,.201]:box('Wash rack crossbar',(0,y,.862),(.721,.014,.018),p['steel'],.002)
 for x in [-.348,.348]:
  for y in [-.201,.201]:rod('Wash rack short foot',(x,y,.819),(x,y,.842),.008,p['steel'],16)
 # Hinged open lid, connected by actual hinge barrels and a fixed support stay.
 for x in [-.281,.281]:cyl('Washer lid hinge',(x,.304,1.011),.022,.117,p['steel'],'X',v=24,b=.002)
 angle=math.radians(-19);lidcenter=Vector((0,.399,1.286))
 box('Open parts washer lid',lidcenter,(.921,.039,.581),p['paint'],.015,rot=(angle,0,0))
 normal=Vector((0,-math.cos(angle),-math.sin(angle)))
 box('Lid inner recessed-looking panel',lidcenter+normal*.025,(.793,.014,.457),p['white'],.009,rot=(angle,0,0))
 for side in [-1,1]:
  bar('Lid connected support stay',(side*.380,.262,.963),(side*.380,.393,1.263),.016,.021,p['steel'],.002)
 rod('Lid top carry handle',(-.123,.489,1.567),(.123,.489,1.567),.013,p['dark'],24)
 for x in [-.113,.113]:rod('Lid handle mounting stem',(x,.489,1.567),(x,.483,1.537),.009,p['steel'],20)
 box('Parts washer pump exterior',(.318,.197,.924),(.100,.108,.169),p['dark'],.009)
 smooth_cable('Fixed wash-fluid nozzle',[(.318,.197,1.003),(.305,.182,1.178),(.189,.116,1.199),(.082,.030,1.120)],.012,p['steel'])
 rod('Washer dark nozzle opening',(.082,.030,1.119),(.077,.026,1.110),.009,p['dark'],20)
 smooth_cable('Fixed washer brush hose',[(.332,.171,.951),(.336,-.024,.910),(.215,-.142,.912),(.098,-.154,.936)],.008,p['rubber'])
 rod('Wash brush handle',(.098,-.154,.936),(-.069,-.148,.936),.016,p['dark'],24)
 box('Brush bristle block',(-.092,-.148,.926),(.071,.047,.037),p['rubber'],.004)
 box('Washer exterior switch box',(.454,-.100,.937),(.035,.109,.104),p['dark'],.006)
 box('Fixed washer power key',(.477,-.100,.937),(.015,.052,.044),p['red'],.004)
 sleeve('Basin lower drain neck',(0,.176,.765),.027,.017,.073,p['steel'],v=28)
 bolt('Closed drain cap',(0,.176,.724),.026,p['dark'])
 return ('city-open-parts-washer','蓋を開いた部品洗浄槽','Open-lid workshop parts washer','工場・自動車整備室の作業背景に置く部品洗浄槽。深さのある空槽と金属縁、すき間のある洗浄ラック、開いた蓋・蝶番・支持棒、四脚と下棚、ポンプ外形・固定ノズル・ブラシホース、下部排水栓外形を造形。洗面台とは異なる部品洗浄設備として一式1点。液体・洗剤・部品は含まず、洗浄・給排水・電装・安全性能を実装または検証した機器ではありません。','An open-lid parts washer for industrial and vehicle-service workshop backgrounds. It has a genuinely recessed empty basin/metal rim, open-bar washing rack, hinged lid/support stays, four legs/lower shelf, pump exterior/fixed nozzle/brush hose and closed lower drain exterior. It is one parts-cleaning assembly rather than a washbasin. Fluid, chemicals and workpieces are absent; cleaning, plumbing, electrical and safety performance are not implemented or validated.',['garage','parts-washer','workshop','部品洗浄槽'])

def waste_oil_collector():
 p=pal()
 for x in [-.235,.235]:
  for y in [-.202,.202]:caster('Oil collector',x,y,.057,p)
 box('Oil receiver caster platform',(0,0,.156),(.571,.520,.055),p['dark'],.014)
 cyl('Waste oil tank body',(0,0,.459),.230,.568,p['paint'],v=48,b=.018)
 for z in [.205,.706]:ring('Oil tank rolled seam',(0,0,z),.225,.012,p['steel'],v=48)
 cyl('Oil tank upper domed-looking shoulder',(0,0,.751),.197,.051,p['paint'],v=48,b=.009)
 cyl('Collector column mount',(0,0,.815),.064,.102,p['white'],v=32,b=.006)
 sleeve('Open telescoping-style collector riser',(0,0,1.155),.029,.020,.630,p['steel'],v=32)
 cyl('Riser fixed height collar',(0,0,.893),.043,.063,p['dark'],v=28,b=.003)
 rod('Height collar locking screw',(.031,0,.895),(.091,0,.895),.009,p['steel'],20)
 cyl('Height collar knob',(.104,0,.895),.022,.029,p['dark'],'X',v=20,b=.003)
 # Thick conical receiver with an open central drain and a closed rolled rim.
 profile=[(.031,1.425),(.031,1.459),(.260,1.614),(.279,1.630),(.286,1.620),(.274,1.598),(.045,1.443),(.045,1.425)]
 profile_body('Open oil receiving funnel',profile,p['white'],48)
 ring('Collector funnel rounded rim',(0,0,1.625),.279,.009,p['steel'],v=48)
 sleeve('Funnel drain neck',(0,0,1.425),.039,.024,.073,p['steel'],v=32)
 # A removable-looking coarse screen spans the bowl, not an opaque fill.
 for off in [-.120,-.060,0,.060,.120]:
  half=math.sqrt(.199**2-off**2)
  rod('Funnel screen cross wire',(-half,off,1.571),(half,off,1.571),.0025,p['steel'],16)
  rod('Funnel screen longitudinal wire',(off,-half,1.576),(off,half,1.576),.0025,p['steel'],16)
 for x in [-.145,.145]:rod('Oil receiver push-handle upright',(x,.218,.443),(x,.269,.930),.016,p['dark'],24)
 rod('Oil receiver push handle',(-.145,.269,.930),(.145,.269,.930),.021,p['dark'],28)
 cyl('Oil tank small filler cap',(-.126,-.026,.779),.030,.025,p['dark'],v=24,b=.003)
 box('Blank oil tank level-indicator backing',(.223,-.017,.477),(.022,.063,.274),p['white'],.005)
 box('Opaque level-indicator face',(.236,-.017,.477),(.010,.023,.224),p['screen'],.002)
 for z in [.398,.438,.478,.518,.558]:box('Unnumbered level tick',(.242,-.030,z),(.006,.014,.004),p['dark'],.001)
 cyl('Oil drain valve side neck',(-.241,0,.290),.025,.068,p['steel'],'X',v=24,b=.002)
 cyl('Oil drain valve body',(-.290,0,.290),.036,.060,p['steel'],'X',v=28,b=.003)
 bar('Fixed drain lever',(-.289,0,.320),(-.289,.090,.320),.017,.012,p['red'],.002)
 smooth_cable('Fixed tank service hose',[(-.318,0,.290),(-.370,-.110,.310),(-.350,-.218,.610),(-.284,-.195,.822),(-.256,-.093,.725)],.011,p['rubber'])
 cyl('Parked hose connection',(-.252,-.090,.722),.021,.046,p['steel'],v=24,b=.002)
 return ('city-wheeled-waste-oil-collector','大型受け皿付き廃油回収タンク','Wheeled waste-oil collector with funnel','車両整備の背景に置く車輪付き廃油回収装置。丸い貯留槽と巻き縁、四輪台、押し手、伸縮風の固定支柱・締付つまみ、実際に凹んだ大きな受け皿と粗いワイヤー網・中央口、外部弁と曲線ホース、無数値の不透明レベル表示外形を造形。液体・車両は含まず一式1点。回収・圧力・排出・荷重・安全性能を実装・検証した容器ではありません。','A wheeled waste-oil receiver for vehicle-service backgrounds. It has a cylindrical tank/rolled seams, four-caster platform, push handle, fixed telescoping-style riser/locking knob, genuinely recessed large funnel with coarse wire screen/central opening, external valve/curved hose and opaque unnumbered level-indicator exterior. It counts as one assembly and includes no fluid or vehicle. Collection, pressure, discharge, load capacity and safety performance are not implemented or validated.',['garage','oil-collector','workshop','廃油回収'])

BUILDERS=[two_post_lift,wheel_balancer,parts_washer,waste_oil_collector]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-051/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/garage_service_equipment.py',azimuth=-55,elevation=27)
