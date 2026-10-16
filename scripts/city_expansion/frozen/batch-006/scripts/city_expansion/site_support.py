"""Four original site-support props for Xenoah Meshcopia, CC BY 4.0.
Deterministic static visualization geometry, Blender 4.3.2. No external assets.
"""
import bpy, sys, math, argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

TAU=math.tau
_base_box=box

def box(n,p,size,m=None,bevel=.008,rot=None):
 # Single-segment chamfers on small details avoid gratuitous triangle inflation.
 o=_base_box(n,p,size,m,bevel,rot)
 if min(size)<=.030:
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.segments=1
 return o

def palette():
 return dict(steel=mat('Brushed galvanized hardware',(.43,.49,.52),.78,.34),dark=mat('Graphite painted structure',(.032,.046,.051),.32,.49),rubber=mat('Molded charcoal rubber',(.012,.018,.021),0,.84),orange=mat('Warm industrial orange enamel',(.72,.19,.035),.26,.38),blue=mat('Deep blue equipment enamel',(.035,.19,.29),.26,.4),red=mat('Red control detail',(.52,.045,.025),.2,.43),white=mat('Frosted off-white lamp face',(.75,.79,.72),.12,.35),black=mat('Matte black recess',(.006,.009,.012),.04,.77),brass=mat('Warm brass connection',(.45,.31,.12),.72,.36),alloy=mat('Cast aluminium surface',(.32,.37,.39),.72,.53),duct=mat('Flexible yellow duct fabric',(.69,.43,.047),0,.72))

def cyl(n,p,r,d,m,axis='Z',v=32,b=.002):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 if r<=.04:
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.segments=1
 return o

def rod(n,a,b,r,m,v=16):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.13));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def beam(n,a,b,w,d,m,bevel=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bevel);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bolt_at(n,p,m,axis='Z',r=.008):
 cyl(n+' washer',p,r*1.5,r*.26,m,axis,16,0)
 q=list(p);q['XYZ'.index(axis)]+=r*.4
 return cyl(n+' hex head',q,r,r*.65,m,axis,6,.0005)

def hollow_ring(n,c,outer,inner,depth,m,axis='Z',steps=48):
 vs=[]
 def cv(x,y,z):
  if axis=='X':return(c[0]+z,c[1]+x,c[2]+y)
  if axis=='Y':return(c[0]+x,c[1]+z,c[2]+y)
  return(c[0]+x,c[1]+y,c[2]+z)
 for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
  vs += [cv(r*math.cos(TAU*i/steps),r*math.sin(TAU*i/steps),z) for i in range(steps)]
 fs=[]
 for i in range(steps):
  j=(i+1)%steps;fs += [(i,j,steps+j,steps+i),(2*steps+i,3*steps+i,3*steps+j,2*steps+j),(i,2*steps+i,2*steps+j,j),(steps+i,steps+j,3*steps+j,3*steps+i)]
 ob=mesh(n,vs,fs,m)
 for i,f in enumerate(ob.data.polygons):f.use_smooth=i%4<2
 return ob

def loop(n,points,r,m,res=2):
 # Closed curve without duplicate endpoint or coincident closing caps.
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=res;cu.use_fill_caps=False
 s=cu.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 s.use_cyclic_u=True;o=bpy.data.objects.new(n,cu);bpy.context.collection.objects.link(o);cu.materials.append(m);return o

def ellipse(n,c,rx,rz,r,m,axis='Y',segments=32):
 pts=[]
 for i in range(segments):
  t=TAU*i/segments;a,b=rx*math.cos(t),rz*math.sin(t)
  pts.append((c[0]+a,c[1],c[2]+b) if axis=='Y' else (c[0],c[1]+a,c[2]+b))
 return loop(n,pts,r,m,1)

def profile_x(n,poly,width,m,bevel=.002):
 k=len(poly);vs=[(x,y,z) for x in [-width/2,width/2] for y,z in poly]
 fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
 return mesh(n,vs,fs,m,bevel)

def annular_sector_x(n,c,outer,inner,width,a0,a1,m,steps=48):
 vs=[]
 for x,r in [(-width/2,outer),(width/2,outer),(-width/2,inner),(width/2,inner)]:
  vs += [(c[0]+x,c[1]+r*math.cos(a0+(a1-a0)*i/steps),c[2]+r*math.sin(a0+(a1-a0)*i/steps)) for i in range(steps+1)]
 k=steps+1;fs=[]
 for i in range(steps):
  j=i+1;fs += [(i,j,k+j,k+i),(2*k+i,3*k+i,3*k+j,2*k+j),(i,2*k+i,2*k+j,j),(k+i,k+j,3*k+j,3*k+i)]
 fs += [(0,k,3*k,2*k),(steps,2*k+steps,3*k+steps,k+steps)]
 return mesh(n,vs,fs,m)

def trailer():
 p=palette()
 # Deep chassis rails, crossmembers and single-axle suspension.
 for x in [-.40,.40]:box('Trailer longitudinal chassis',(x,.04,.37),(.075,1.40,.11),p['dark'],.009)
 for y in [-.59,.0,.65]:box('Chassis crossmember',(0,y,.36),(.90,.08,.09),p['dark'],.006)
 rod('Solid trailer axle',(-.65,.19,.255),(.65,.19,.255),.035,p['steel'],24)
 for x in [-.40,.40]:
  for j in range(3):
   tube('Layered leaf spring',[(x,-.16,.32-j*.009),(x,.18,.29-j*.009),(x,.50,.32-j*.009)],.011-j*.001,p['dark'],1)
  for y in [-.16,.50]:box('Spring hanger',(x,y,.33),(.065,.06,.13),p['steel'],.004)
 for x in [-.61,.61]:
  cyl('Pneumatic trailer tire',(x,.19,.255),.255,.145,p['rubber'],'X',64,.018)
  for s in [-1,1]:
   xx=x+s*.074;hollow_ring('Tire shoulder bead',(xx,.19,.255),.216,.185,.008,p['black'],'X',48)
  xx=x+math.copysign(.078,x)
  cyl('Wheel pressed rim',(xx,.19,.255),.148,.014,p['steel'],'X',48,.004)
  hollow_ring('Wheel rim lip',(xx+math.copysign(.010,x),.19,.255),.149,.131,.009,p['alloy'],'X',48)
  cyl('Hub dust cap',(xx+math.copysign(.018,x),.19,.255),.052,.044,p['dark'],'X',32,.004)
  for i in range(5):
   t=TAU*i/5;bolt_at('Wheel lug',(xx,.19+.092*math.cos(t),.255+.092*math.sin(t)),p['steel'],'X',.009)
  for i in range(24):
   t=TAU*i/24
   o=box('Tire tread shoulder',(x,.19+.252*math.cos(t),.255+.252*math.sin(t)),(.13,.029,.012),p['rubber'],.002);o.rotation_euler[0]=t-math.pi/2
  # Folded fender is a solid extruded section, open beneath wheel.
  poly=[(-.16,.37),(-.10,.56),(.49,.56),(.57,.38),(.54,.37),(.46,.525),(-.075,.525),(-.13,.36)]
  o=profile_x('Folded trailer wheel fender',poly,.22,p['orange'],.005);o.location.x=x
  for yy in [-.08,.47]:beam('Fender support',(math.copysign(.42,x),yy,.40),(x,yy,.51),.03,.03,p['dark'])
 # Tow A-frame, coupling shell and static crank jack.
 for x in [-.37,.37]:beam('A-frame drawbar',(x,-.56,.36),(0,-1.42,.36),.075,.09,p['steel'],.006)
 box('Coupling mounting block',(0,-1.45,.36),(.14,.29,.085),p['steel'],.008)
 box('Tow coupling outer housing',(0,-1.63,.365),(.15,.22,.105),p['alloy'],.025)
 box('Coupler underside dark cavity',(0,-1.70,.32),(.095,.12,.018),p['black'],.008)
 beam('Coupler latch lever',(0,-1.62,.425),(0,-1.48,.47),.045,.027,p['steel'])
 for y in [-1.43,-1.55]:bolt_at('Coupler fixing',(0,y,.414),p['dark'],r=.013)
 for x in [-.07,.07]:
  pts=[(x,-1.32,.31),(x*1.6,-1.49,.22),(x*.7,-1.63,.26)]
  tube('Retaining loop cable',pts,.008,p['steel'],2)
 box('Drawbar jack bracket',(.16,-1.18,.36),(.22,.13,.065),p['dark'],.006)
 cyl('Drawbar jack sleeve',(.20,-1.18,.30),.035,.42,p['steel'],v=32)
 cyl('Drawbar jack ram',(.20,-1.18,.13),.023,.23,p['alloy'],v=24)
 box('Drawbar jack foot',(.20,-1.18,.025),(.20,.15,.025),p['dark'],.005)
 rod('Jack winding handle',(.20,-1.18,.52),(.34,-1.18,.52),.012,p['steel'])
 cyl('Jack grip',(.34,-1.18,.49),.018,.07,p['rubber'],v=24)
 # Low equipment enclosure, open vents and controls are static decorative geometry.
 box('Sealed equipment deck',(0,.02,.45),(.91,1.36,.06),p['orange'],.018)
 box('Power enclosure',(0,.08,.72),(.81,1.16,.50),p['orange'],.035)
 box('Lift-off top lid',(0,.08,.982),(.84,1.19,.052),p['orange'],.018)
 for x in [-.412,.412]:
  box('Dark panel gasket',(x,.09,.72),(.008,.90,.36),p['black'],.009)
  box('Service access panel',(x*1.012,.09,.72),(.010,.87,.33),p['orange'],.009)
  for y in [-.26,.35]:bolt_at('Access panel screw',(x*1.033,y,.83),p['steel'],'X',.007)
  for i in range(7):
   box('Panel louver opening',(x*1.038,.09,.61+i*.030),(.007,.48,.012),p['black'],.003)
  box('Service panel pull',(x*1.085,-.26,.72),(.035,.10,.022),p['dark'],.005)
 box('Rear control recess',(0,.672,.75),(.43,.014,.24),p['dark'],.012)
 box('Controller glass',(0,.685,.80),(.20,.013,.075),p['black'],.006)
 for x in [-.10,.10]:cyl('Control selector',(x,.692,.70),.024,.018,p['red'] if x>0 else p['steel'],'Y',24,.003)
 for x in [-.31,.31]:box('Rear unlit reflector',(x,.681,.54),(.11,.022,.065),p['red'],.007)
 # Four deployed outriggers, sleeves, screw feet and visible crank tips.
 for x in [-1,1]:
  for y in [-.48,.58]:
   box('Outrigger guide sleeve',(x*.49,y,.39),(.31,.092,.085),p['dark'],.005)
   box('Deployed stabilizer beam',(x*.75,y,.38),(.56,.065,.06),p['steel'],.005)
   bolt_at('Outrigger lock bolt',(x*.50,y,.442),p['steel'],r=.012)
   cyl('Stabilizer jack sleeve',(x*.99,y,.25),.030,.30,p['orange'],v=24)
   cyl('Stabilizer screw',(x*.99,y,.12),.019,.24,p['steel'],v=24)
   box('Stabilizer foot plate',(x*.99,y,.015),(.20,.19,.030),p['dark'],.006)
   rod('Stabilizer crank',(x*.99,y,.425),(x*.99,y+.11,.425),.008,p['steel'])
   cyl('Crank grip',(x*.99,y+.11,.40),.013,.05,p['rubber'],v=20)
 # Telescopic mast, lower pivot cheeks, winch drum and original cable route.
 for x in [-.12,.12]:box('Mast pivot cheek',(x,.46,1.06),(.055,.19,.32),p['dark'],.008)
 rod('Mast base pivot',(-.17,.46,1.04),(.17,.46,1.04),.027,p['steel'],24)
 box('Lower mast section',(0,.46,1.75),(.15,.15,1.55),p['dark'],.006)
 box('Middle mast section',(0,.46,2.61),(.118,.118,1.58),p['steel'],.005)
 box('Upper mast section',(0,.46,3.25),(.087,.087,1.18),p['alloy'],.004)
 for z in [2.47,3.35]:box('Mast telescoping collar',(0,.46,z),(.177 if z<3 else .145,.177 if z<3 else .145,.065),p['dark'],.006)
 box('Winch bracket',(.14,.46,1.31),(.19,.22,.045),p['steel'],.004)
 cyl('Winch cable drum',(.15,.46,1.40),.074,.15,p['dark'],'X',32,.003)
 for xx in [.065,.235]:cyl('Winch spool flange',(xx,.46,1.40),.087,.012,p['steel'],'X',32,.002)
 for i in range(9):hollow_ring('Coiled winch cable',(.09+i*.014,.46,1.40),.070,.065,.009,p['black'],'X',32)
 beam('Winch handle arm',(.26,.46,1.40),(.26,.36,1.51),.025,.016,p['steel'])
 rod('Winch hand grip',(.26,.36,1.51),(.36,.36,1.51),.017,p['rubber'],24)
 tube('Mast lifting cable',[(.13,.39,1.43),(.095,.39,2.48),(.095,.51,2.53),(.02,.54,3.65)],.004,p['black'],1)
 # Four unlit floodlights on individual tilting yokes. No emissive material.
 box('Lamp crossarm',(0,.46,3.81),(1.65,.10,.095),p['dark'],.008)
 for i,x in enumerate([-.61,-.205,.205,.61]):
  box('Floodlight stem',(x,.46,3.91),(.045,.045,.18),p['steel'],.004)
  for s in [-1,1]:box('Lamp yoke side',(x+s*.158,.46,3.98),(.025,.07,.17),p['dark'],.004)
  box('Lamp yoke base',(x,.46,3.91),(.34,.07,.025),p['dark'],.004)
  box('Floodlight rear heat sink',(x,.46,4.045),(.285,.14,.25),p['dark'],.016)
  box('Floodlight perimeter housing',(x,.367,4.045),(.32,.060,.28),p['alloy'],.014)
  box('Floodlight dark lens seal',(x,.331,4.045),(.286,.014,.246),p['black'],.009)
  box('Unlit frosted lamp face',(x,.321,4.045),(.264,.013,.224),p['white'],.008)
  for j in range(6):box('Floodlight cooling fin',(x-.12+j*.048,.548,4.045),(.014,.038,.218),p['dark'],.002)
  for sx in [-1,1]:bolt_at('Yoke pivot',(x+sx*.18,.46,4.025),p['steel'],'X',.011)
  tube('Lamp strain-relieved cable',[(x,.55,4.02),(x,.58,3.87),(x*.5,.54,3.80),(0,.53,3.72)],.005,p['black'],1)
 return('city-roadwork-light-trailer','工事用伸縮照明トレーラー','Roadwork telescopic light trailer','小型の牽引式照明設備。4基の非発光灯具、伸長状態の角形マスト、手動巻上げ部、板ばね付き車軸、牽引金具と4本の接地アウトリガーを造形。牽引車、可動部、発電・照明・牽引機能は含みません。安全認証や積載性能を表すものではありません。','A compact towable lighting prop with four unlit lamp housings, a statically raised telescopic mast, hand winch, leaf-sprung axle, coupling and four deployed stabilizers. No towing vehicle, moving parts, power generation, illumination or towing function is included. It makes no safety-certification or load-capacity claim.',['construction','lighting','trailer','工事照明'])

def blower():
 p=palette();z=.36
 # Hollow drum, substantial rolled intake rim and visible six-blade rotor.
 hollow_ring('Open blower drum',(0,0,z),.265,.239,.43,p['orange'],'Y',64)
 for y in [-.22,.22]:hollow_ring('Rolled shroud rim',(0,y,z),.281,.237,.035,p['dark'],'Y',64)
 cyl('Fan motor casing',(0,.08,z),.074,.21,p['alloy'],'Y',40,.005)
 cyl('Fan center hub',(0,-.075,z),.070,.07,p['dark'],'Y',40,.006)
 cyl('Fan hub cap',(0,-.118,z),.044,.02,p['steel'],'Y',32,.004)
 for j in range(6):
  a=TAU*j/6
  # Swept, closed thickness blade with mild pitch between root and tip.
  poly=[(.055,-.013),(.106,-.025),(.215,.030),(.221,.077),(.171,.082),(.086,.025)]
  vs=[]
  for dy in [-.006,.006]:
   for rr,tt in poly:
    vs.append((rr*math.cos(a)-tt*math.sin(a),-.07+dy+.14*tt,z+rr*math.sin(a)+tt*math.cos(a)))
  k=len(poly);faces=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
  mesh('Swept stationary impeller blade',vs,faces,p['steel'],.0015)
 # Concentric front guard and four rear motor braces, all actual open spacing.
 for r in [.075,.12,.165,.21,.249]:ellipse('Intake concentric wire guard',(0,-.255,z),r,r,.0035,p['steel'],segments=64)
 for j in range(12):
  a=TAU*j/12;rod('Intake radial guard wire',(.047*math.cos(a),-.258,z+.047*math.sin(a)),(.255*math.cos(a),-.258,z+.255*math.sin(a)),.0032,p['steel'],12)
 for j in range(4):
  a=TAU*(j+.125)/4;rod('Rear motor suspension brace',(.06*math.cos(a),.17,z+.06*math.sin(a)),(.241*math.cos(a),.17,z+.241*math.sin(a)),.011,p['dark'],16)
 # Protective bent-tube side frames and isolation feet.
 for x in [-.23,.23]:
  pts=[(x,-.31,.044),(x,-.36,.105),(x,-.34,.24),(x,-.27,.27),(x,.26,.27),(x,.34,.21),(x,.34,.06)]
  tube('Tubular carry stand side',pts,.018,p['dark'],2)
  for y in [-.29,.28]:box('Vibration isolation foot',(x,y,.020),(.09,.13,.04),p['rubber'],.009)
  rod('Shroud side pivot',(x*.98,0,z),(math.copysign(.31,x),0,z),.022,p['steel'],24)
  bolt_at('Side trunnion head',(math.copysign(.315,x),0,z),p['dark'],'X',.021)
 for y in [-.30,.29]:rod('Carry stand transverse brace',(-.23,y,.07),(.23,y,.07),.018,p['dark'])
 tube('Top protective handle',[(-.20,-.03,.53),(-.20,-.03,.69),(-.14,-.03,.74),(.14,-.03,.74),(.20,-.03,.69),(.20,-.03,.53)],.017,p['dark'],2)
 rod('Top handle rubber grip',(-.12,-.03,.74),(.12,-.03,.74),.023,p['rubber'],24)
 box('Switch enclosure',(.273,.09,.48),(.058,.13,.11),p['dark'],.009)
 box('Recessed switch plate',(.307,.09,.48),(.013,.085,.07),p['black'],.003)
 box('Unmarked red rocker',(.318,.09,.48),(.012,.036,.037),p['red'],.004)
 # Short intact flexible connector with visible hollow wall and reinforcing hoops.
 n=64;ys=[.245+i*.033 for i in range(15)];verts=[]
 for inside in [False,True]:
  for j,y in enumerate(ys):
   rr=.237+(.006 if j%2 else -.002)-( .009 if inside else 0)
   cz=z-.048*((y-.245)/.462)**2
   verts += [(rr*math.cos(TAU*i/n),y,cz+rr*math.sin(TAU*i/n)) for i in range(n)]
 rows=len(ys);stride=rows*n;faces=[]
 for inside in [0,1]:
  for j in range(rows-1):
   for i in range(n):
    a=inside*stride+j*n+i;b=inside*stride+j*n+(i+1)%n;c=inside*stride+(j+1)*n+(i+1)%n;d=inside*stride+(j+1)*n+i;faces.append((a,b,c,d))
 for j in [0,rows-1]:
  for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,a+stride,b+stride,b))
 mesh('Short flexible open ventilation duct',verts,faces,p['duct'],smooth=True)
 for j,y in enumerate(ys):
  cz=z-.048*((y-.245)/.462)**2
  ellipse('Duct external reinforcing hoop',(0,y,cz),.243,.243,.0045,p['dark'],segments=48)
 for y in [.252,.704]:
  cz=z-.048*((y-.245)/.462)**2;hollow_ring('Duct clamp band',(0,y,cz),.250,.244,.022,p['steel'],'Y',48)
  box('Duct band latch',(.25,y,cz),(.035,.038,.046),p['steel'],.004)
 # Short coiled attached lead, no supply outlet or companion extension included.
 tube('Attached power lead',[(.28,.13,.44),(.32,.18,.30),(.32,.04,.13),(.28,-.12,.12),(.12,-.16,.11),(.02,-.08,.11),(.08,.06,.11),(.24,.08,.11),(.29,-.04,.11)],.005,p['black'],2)
 return('city-confined-space-blower','短いダクト付き可搬換気送風機','Portable ventilation blower with short duct','可搬式ドラム型送風機の静的モデル。中空シュラウド、同心円状グリル、6枚の固定羽根、持ち手付き防振フレームと短い中空フレキシブルダクトを備えます。長いダクト、電源、送風・換気動作は付属しません。閉鎖空間での使用適合性や安全性能を保証しません。','A static portable drum ventilation blower with hollow shroud, concentric open grille, six fixed fan blades, isolated carry frame and a short hollow flexible duct. Long duct runs, power supply, airflow and ventilation behavior are absent. It does not claim confined-space suitability or validated safety performance.',['blower','ventilation','construction','送風機'])

def vise():
 p=palette()
 # Three genuinely splayed tubular legs, independent folding hinges and wide feet.
 angles=[math.radians(210),math.radians(330),math.radians(90)]
 for j,a in enumerate(angles):
  top=(.12*math.cos(a),.12*math.sin(a),.87);bottom=(.405*math.cos(a),.405*math.sin(a),.035)
  rod('Folding tubular leg',bottom,top,.028,p['dark'],28)
  mid=(.37*math.cos(a),.37*math.sin(a),.135)
  rod('Lower leg reinforced sleeve',bottom,mid,.033,p['steel'],28)
  o=box('Broad non-slip foot',bottom,(.12,.10,.037),p['rubber'],.009);o.rotation_euler[2]=a
  o=box('Hinged top leg clevis',top,(.10,.095,.105),p['orange'],.008);o.rotation_euler[2]=a
  tang=Vector((-math.sin(a),math.cos(a),0));aa=Vector(top)+tang*.068;bb=Vector(top)-tang*.068
  rod('Leg pivot bolt',aa,bb,.015,p['steel'],20)
  # Three radial spreader struts meet at a low central folding collar.
  low=(.29*math.cos(a),.29*math.sin(a),.38)
  beam('Folding spreader strut',(0,0,.38),low,.024,.018,p['steel'])
  cyl('Spreader joint pin',low,.011,.035,p['dark'],v=16,b=.001)
 cyl('Spreader center collar',(0,0,.38),.045,.050,p['orange'],v=32,b=.003)
 # Triangular under-table tool tray, side lips and genuine open top.
 tri=[(.255*math.cos(a),.255*math.sin(a)) for a in angles];vs=[(x,y,z) for z in [.395,.414] for x,y in tri];faces=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
 mesh('Triangular tool shelf floor',vs,faces,p['orange'],.003)
 for j in range(3):
  a,b=tri[j],tri[(j+1)%3];beam('Raised tool shelf rim',(a[0],a[1],.434),(b[0],b[1],.434),.012,.049,p['orange'])
 # Split worktop with open edge slots rather than dark painted holes.
 box('Main vise worktop',(0,.005,.925),(.48,.32,.046),p['orange'],.012)
 for x in [-.24,.24]:
  for yy in [-.14,.005,.15]:box('Worktop projecting lug',(x+math.copysign(.027,x),yy,.923),(.07,.060,.05),p['orange'],.006)
 for x in [-.16,.16]:
  for y in [-.105,.105]:bolt_at('Worktop attachment',(x,y,.952),p['steel'],r=.012)
 # Longitudinal pipe cradle uses two V jaws, the space between them remains empty.
 for y in [-.08,.08]:
  for s in [-1,1]:
   beam('V jaw cast support',(s*.11,y,.96),(s*.035,y,1.015),.048,.070,p['alloy'],.004)
   o=box('Serrated jaw insert',(s*.062,y,1.021),(.093,.077,.018),p['steel'],.002);o.rotation_euler[1]=s*math.radians(34)
   for j in range(5):
    # Individual raised jaw teeth do not fill the V recess.
    x=s*(.036+j*.012);zz=1.04-(abs(x)-.036)*.66
    o=box('V jaw gripping tooth',(x,y,zz),(.005,.072,.006),p['dark'],.0006);o.rotation_euler[1]=s*math.radians(34)
 # The chain hangs slack across the empty jaws, not unsupported in an arch.
 points=[]
 for i in range(17):
  t=i/16;points.append((-.145+.29*t,-.025,1.035-.049*math.sin(math.pi*t)))
 for i,pt in enumerate(points):
  if i%2:ellipse('Alternating clamp chain link',pt,.011,.018,.0032,p['steel'],axis='X',segments=20)
  else:ellipse('Alternating clamp chain link',pt,.013,.018,.0032,p['steel'],axis='Y',segments=20)
 box('Chain anchor clevis',(-.15,-.025,.988),(.058,.065,.075),p['dark'],.006)
 cyl('Chain anchor cross pin',(-.15,-.025,1.015),.012,.091,p['steel'],'Y',20,.001)
 box('Chain takeup housing',(.165,-.025,.993),(.076,.090,.088),p['alloy'],.008)
 cyl('Chain tension screw',(.165,-.025,1.087),.016,.15,p['steel'],v=28,b=.001)
 for i in range(10):hollow_ring('Tension screw thread',(.165,-.025,1.033+i*.010),.019,.015,.004,p['steel'],steps=24)
 cyl('Handle central barrel',(.165,-.025,1.175),.026,.045,p['dark'],v=28,b=.003)
 rod('Sliding tommy bar',(.055,-.025,1.175),(.315,-.025,1.175),.009,p['steel'],20)
 for x in [.055,.315]:cyl('Tommy bar end stop',(x,-.025,1.175),.014,.017,p['dark'],'X',20,.002)
 # Underbody gussets and folded-form carry hook, useful from reverse angle.
 for x in [-.14,.14]:beam('Under-table gusset',(x,-.10,.90),(x,.10,.83),.025,.035,p['dark'])
 tube('Frame carry loop',[(-.09,.145,.89),(-.09,.22,.80),(.09,.22,.80),(.09,.145,.89)],.012,p['steel'],2)
 return('city-tripod-pipe-vise','三脚式チェーンパイプバイス','Tripod chain pipe vise','3本の開いた脚と三角形工具棚を備える可搬パイプバイス。折畳みヒンジ、V字の歯付き受け、交互向きの鎖リンク、締付ねじと横ハンドルを造形。パイプ、工具、締付・折畳み動作は含みません。荷重・締付性能や作業安全性は未検証です。','A portable pipe vise on three splayed folding legs with a triangular tool tray. Includes hinge clevises, serrated V jaws, alternating chain links, tension screw and sliding handle. Pipe, tools, clamping and folding motion are not supplied. Load capacity, clamping performance and working safety are not validated.',['vise','workstand','pipe','パイプバイス'])

def tile_saw():
 p=palette()
 # Open reservoir pan with wall thickness, molded feet and bottom stiffeners.
 box('Water reservoir floor',(0,0,.065),(.86,.66,.055),p['dark'],.016)
 for x in [-.415,.415]:box('Reservoir side wall',(x,0,.13),(.035,.66,.15),p['dark'],.010)
 for y in [-.313,.313]:box('Reservoir end wall',(0,y,.13),(.80,.034,.15),p['dark'],.009)
 for x in [-.32,.32]:
  for y in [-.24,.24]:box('Rubber table foot',(x,y,.025),(.12,.10,.05),p['rubber'],.012)
 for x in [-.27,0,.27]:box('Underside strengthening rib',(x,0,.038),(.035,.49,.030),p['alloy'],.005)
 cyl('Water pan drain plug',(.431,-.21,.095),.024,.022,p['orange'],'X',28,.003)
 box('Pan recessed drain boss',(.42,-.21,.095),(.035,.075,.065),p['dark'],.010)
 # Two exposed guide rails, their saddles and distinct sliding table rollers.
 for x in [-.31,.31]:
  for y in [-.26,.26]:box('Rail pedestal',(x,y,.21),(.085,.075,.13),p['orange'],.008)
  rod('Precision sliding bed rail',(x,-.365,.266),(x,.365,.266),.014,p['steel'],32)
  for y in [-.363,.363]:cyl('Rail end stop',(x,y,.266),.025,.025,p['dark'],'Y',24,.002)
  for y in [-.19,.15]:
   box('Bed guide saddle',(x,y,.280),(.075,.065,.038),p['dark'],.006)
   cyl('Small guide roller',(x,y,.26),.024,.040,p['alloy'],'X',24,.002)
 # Segmented aluminium bed gives real drainage gaps and an open central kerf.
 for side in [-1,1]:
  for j in range(4):
   x=side*(.041+j*.074);box('Slotted aluminium workbed plank',(x,-.045,.316),(.066,.44,.026),p['steel'],.003)
 box('Workbed front tie bar',(0,-.28,.303),(.65,.035,.032),p['alloy'],.004)
 box('Workbed rear tie bar',(0,.194,.303),(.65,.035,.032),p['alloy'],.004)
 box('Tile end fence',(0,-.238,.344),(.65,.026,.070),p['alloy'],.004)
 for x in [-.26,.26]:bolt_at('Fence adjustment bolt',(x,-.238,.383),p['dark'],r=.009)
 # Static angle stop on the left half, not a supplied tile.
 box('Adjustable fence stop',(-.18,-.17,.349),(.05,.11,.025),p['orange'],.004)
 cyl('Fence stop thumbscrew',(-.18,-.17,.377),.024,.028,p['dark'],v=24,b=.003)
 for x in [-.24,.24]:tube('Sliding bed pull loop',[(x,-.275,.315),(x,-.34,.315),(x+(.10 if x<0 else -.10),-.34,.315),(x+(.10 if x<0 else -.10),-.275,.315)],.010,p['dark'],2)
 # Cantilever support joins the chassis, raising motor and blade above table.
 box('Saw column mounting foot',(-.36,.24,.22),(.14,.15,.10),p['orange'],.010)
 for x in [-.40,-.32]:bolt_at('Column mount bolt',(x,.24,.278),p['steel'],r=.010)
 beam('Rigid upright saw column',(-.36,.24,.23),(-.36,.24,.60),.095,.11,p['orange'],.012)
 box('Saw head horizontal bridge',(-.19,.24,.595),(.43,.11,.10),p['orange'],.012)
 beam('Column triangular support',(-.36,.24,.44),(-.13,.24,.59),.040,.07,p['alloy'])
 cyl('Head tilt pivot',(-.31,.24,.59),.043,.15,p['dark'],'X',32,.003)
 cyl('Head tilt locking knob',(-.415,.24,.59),.035,.044,p['dark'],'X',28,.004)
 # Closed guard section and stationary blade, no functional sharpness claim.
 center=(.015,.08,.482)
 cyl('Stationary saw blade',center,.145,.004,p['steel'],'X',80,.0004)
 for j in range(24):
  a=TAU*j/24
  annular_sector_x('Blade rim segment',center,.146,.137,.006,a+.015,a+TAU/24-.015,p['alloy'],steps=3)
 cyl('Blade spindle boss',(.035,.08,.482),.035,.045,p['dark'],'X',32,.002)
 bolt_at('Blade arbor bolt',(.064,.08,.482),p['steel'],'X',.016)
 annular_sector_x('Upper blade wraparound guard',center,.172,.156,.080,math.radians(-12),math.radians(192),p['orange'],steps=50)
 # Side guard cheek is a semicircular solid sector, no coplanar duplicated faces.
 poly=[(center[1]+.168*math.cos(math.radians(-8)+math.radians(196)*i/40),center[2]+.168*math.sin(math.radians(-8)+math.radians(196)*i/40)) for i in range(41)]
 poly += [(center[1]-.13,center[2]+.012),(center[1]+.13,center[2]+.012)]
 for xx in [-.030,.059]:
  o=profile_x('Blade guard side cheek',poly,.009,p['orange'],.001);o.location.x=xx
 for yy in [-.015,.17]:bolt_at('Blade guard side screw',(.067,yy,.55),p['steel'],'X',.007)
 # Motor on the opposite side of the blade, explicit finned body and vents.
 cyl('Saw motor barrel',(-.125,.08,.482),.077,.23,p['alloy'],'X',40,.004)
 for i in range(7):hollow_ring('Motor cooling ridge',(-.22+i*.026,.08,.482),.084,.076,.008,p['dark'],'X',40)
 cyl('Motor end cap',(-.256,.08,.482),.086,.040,p['dark'],'X',40,.005)
 for j in range(8):
  a=TAU*j/8;o=box('Motor rear vent recess',(-.279,.08+.053*math.cos(a),.482+.053*math.sin(a)),(.006,.010,.028),p['black'],.002);o.rotation_euler[0]=a
 box('Power switch housing',(-.18,-.01,.56),(.13,.075,.08),p['dark'],.009)
 box('Unmarked power switch',(-.18,-.052,.568),(.045,.012,.029),p['red'],.003)
 tube('Head carry handle',[(-.23,.08,.55),(-.23,.08,.69),(-.17,.08,.72),(-.04,.08,.72),(.01,.08,.67),(.01,.08,.63)],.013,p['dark'],2)
 rod('Carry handle soft grip',(-.17,.08,.72),(-.05,.08,.72),.019,p['rubber'],24)
 # Unfilled water tray, static pump and two short routed hoses.
 box('Reservoir pump casing',(.27,.24,.135),(.09,.08,.09),p['blue'],.009)
 for i in range(4):box('Pump intake recess',(.27,.197,.109+i*.014),(.061,.006,.005),p['black'],.001)
 tube('Blade water feed hose',[(.27,.24,.18),(.29,.27,.29),(.24,.28,.44),(.15,.25,.58),(.05,.15,.63),(.04,.12,.59)],.006,p['blue'],2)
 cyl('Guard water fitting',(.04,.12,.60),.012,.030,p['brass'],v=24,b=.001)
 tube('Motor cable into rear tray',[(-.18,.14,.55),(-.26,.23,.50),(-.28,.27,.32),(-.22,.27,.18),(-.10,.26,.13)],.005,p['black'],2)
 return('city-wet-tile-saw','卓上湿式タイル切断機','Tabletop wet tile saw','水受けトレーと2本のレール上のスライドベッドを備える小型タイル切断機。片持ち支柱、放熱フィン付きモーター、固定刃と上部ガード、定規、ポンプ筐体、給水ホースを造形。タイル、水、架台、切断・回転・給水動作は付属しません。作業用機械や安全規格適合品ではありません。','A compact tabletop wet tile saw with open reservoir, twin guide rails and sliding-bed geometry. Models a cantilever column, finned motor, fixed blade and upper guard, fence, pump casing and water hose. No tile, water, separate stand, cutting, rotation or water-flow behavior is supplied. It is not a working machine or safety-standard-certified product.',['tile-saw','construction','cutting','タイル切断機'])

BUILDERS=[trailer,blower,vise,tile_saw]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-006/assets');parser.add_argument('--only',default='');a=parser.parse_args(args)
 out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  if a.only and 'city-'+{'trailer':'roadwork-light-trailer','blower':'confined-space-blower','vise':'tripod-pipe-vise','tile_saw':'wet-tile-saw'}[fn.__name__]!=a.only:continue
  reset();data=fn();publish_asset(*data,out,'scripts/city_expansion/site_support.py',azimuth=-58,elevation=23 if fn==trailer else 27)
