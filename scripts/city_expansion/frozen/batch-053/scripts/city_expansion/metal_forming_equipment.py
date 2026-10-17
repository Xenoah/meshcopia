"""Original workshop metal-forming equipment scene props. Xenoah, CC BY 4.0.
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
 for f in o.data.polygons:
  j=f.index//N;f.use_smooth=abs(profile[j][1]-profile[(j+1)%len(profile)][1])>1e-8
 return o

def spring(n,x,y,z0,z1,r,wire,m,turns=7):
 pts=[(x+r*math.cos(i*math.tau*turns/112),y+r*math.sin(i*math.tau*turns/112),z0+(z1-z0)*i/112) for i in range(113)];return tube(n,pts,wire,m,1)
def extrude_x(n,xc,w,yz,m,bev=.002):
 N=len(yz);vs=[(x,y,z) for x in [xc-w/2,xc+w/2] for y,z in yz];fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)];return mesh(n,vs,fs,m,bev)
def floor_stand(p,width,depth,height,name):
 for x in [-width/2,width/2]:
  for y in [-depth/2,depth/2]:
   box(name+' support leg',(x,y,height/2+.030),(.055,.055,height),p['paint'],.005)
   box(name+' rubber foot',(x,y,.034),(.084,.084,.068),p['rubber'],.006)
 for y in [-depth/2,depth/2]:box(name+' low crossbar',(0,y,.257),(width+.050,.038,.045),p['steel'],.004)
 for x in [-width/2,width/2]:box(name+' low side brace',(x,0,.257),(.038,depth+.050,.045),p['steel'],.004)

def shop_press():
 p=pal()
 for x in [-.420,.420]:
  box('Press floor skid',(x,0,.050),(.155,.754,.100),p['steel'],.009)
  box('Press upright column',(x,0,.922),(.110,.172,1.744),p['paint'],.009)
  for y in [-.171,.171]:bar('Press triangular-looking foot brace',(x,y,.101),(x,0,.398),.030,.036,p['steel'],.003)
  box('Press front column slot exterior',(x,-.092,.823),(.029,.014,.918),p['dark'],.003)
  for z in [.412,.522,.632,.742,.852,.962,1.072,1.182]:cyl('Unnumbered table-height hole inset',(x,-.102,z),.016,.008,p['dark'],'Y',v=20,b=0)
 box('Press top load cross-member',(0,0,1.747),(.958,.254,.177),p['paint'],.012)
 box('Press lower stabilizing beam',(0,.024,.265),(.902,.112,.085),p['steel'],.006)
 for x in [-.422,.422]:
  cyl('Fixed press table support pin',(x,0,.717),.025,.256,p['steel'],'Y',v=28,b=.002)
  cyl('Table support pin end collar',(x,-.141,.717),.035,.022,p['dark'],'Y',v=24,b=.002)
 for y in [-.104,.104]:box('Open press work-bed beam',(0,y,.779),(.938,.085,.119),p['steel'],.007)
 for x in [-.420,.420]:box('Press bed connected side tie',(x,0,.779),(.094,.270,.119),p['white'],.007)
 for x in [-.157,.157]:
  # V-notched closed block, extruded across the front-to-back bearing width.
  yz=[(-.095,.837),(.095,.837),(.095,.912),(.025,.912),(0,.882),(-.025,.912),(-.095,.912)]
  o=extrude_x('Fixed V-shaped press block',x,.160,yz,p['dark'],.002)
 cyl('Press hydraulic cylinder body',(0,0,1.541),.077,.346,p['white'],v=40,b=.006)
 cyl('Press cylinder upper mounting flange',(0,0,1.711),.109,.045,p['steel'],v=36,b=.003)
 cyl('Fixed exposed press ram',(0,0,1.285),.036,.255,p['steel'],v=32,b=.002)
 box('Press moving-head exterior',(0,0,1.185),(.357,.142,.079),p['paint'],.007)
 cyl('Press ram contact shoe',(0,0,1.112),.066,.077,p['steel'],v=32,b=.004)
 for x in [-.148,.148]:
  rod('Return spring upper anchor',(x,0,1.652),(x,-.048,1.652),.012,p['steel'],20)
  spring('Continuous press return spring',x,-.048,1.225,1.652,.025,.005,p['steel'])
  for zz in [1.225,1.652]:rod('Connected return spring end hook',(x+.025,-.048,zz),(x,-.048,zz),.005,p['steel'],16)
  rod('Return spring lower bracket',(x,-.048,1.225),(x,0,1.185),.011,p['steel'],20)
 box('Side pump mounting bracket',(.521,.026,.949),(.168,.134,.187),p['steel'],.006)
 box('Manual press pump body',(.602,.026,.954),(.105,.157,.230),p['white'],.011)
 rod('Pump handle pivot',(.602,-.025,1.030),(.602,-.109,1.144),.018,p['steel'],24)
 rod('Raised manual pump handle',(.602,-.109,1.144),(.602,-.319,1.428),.014,p['steel'],24)
 rod('Pump rubber hand grip',(.602,-.271,1.363),(.602,-.331,1.444),.022,p['rubber'],24)
 smooth_cable('Fixed press hydraulic-looking hose',[(.626,.093,1.020),(.678,.177,1.201),(.544,.205,1.527),(.222,.163,1.609),(.065,.015,1.609)],.010,p['rubber'])
 rod('Gauge casing support neck',(0,-.065,1.617),(0,-.106,1.617),.021,p['steel'],24)
 cyl('Blank press gauge casing',(0,-.113,1.617),.073,.041,p['steel'],'Y',v=36,b=.003)
 cyl('Opaque blank press gauge face',(0,-.137,1.617),.061,.009,p['white'],'Y',v=36,b=.001)
 for i in range(9):
  a=math.radians(35+i*28);bar('Unnumbered gauge tick',(.049*math.cos(a),-.143,1.617+.049*math.sin(a)),(.055*math.cos(a),-.143,1.617+.055*math.sin(a)),.003,.003,p['dark'],.0005)
 rod('Fixed gauge pointer',(0,-.143,1.617),(.025,-.143,1.646),.0025,p['red'],12)
 return ('city-hydraulic-shop-press','H形フレームの油圧ショッププレス','H-frame hydraulic shop press','金属加工・車両整備工場の背景に置くH形ショッププレス。二本柱と床スキッド、固定高さの開いた作業台と二つのV溝ブロック、ラム外形、連続した二本の戻しばね、手動ポンプ/握り/曲線ホース、数値のない固定計器を造形。一式1点で加工材は含みません。荷重・油圧・復帰・計測や安全性を実装/検証した製造用設計ではありません。','An H-frame shop-press exterior for metalworking and vehicle-service backgrounds. It has twin uprights/floor skids, a fixed-height open work bed and two V-notched blocks, ram exterior, two continuous return springs, manual pump/handle/curved hose and a fixed unnumbered gauge. The complete assembly counts once and contains no workpiece. Load, hydraulic, return, measuring and safety performance are not implemented or validated.',['workshop','shop-press','metal-forming','ショッププレス'])

def sheet_metal_brake():
 p=pal();floor_stand(p,1.290,.460,.817,'Folding brake')
 box('Brake stand top beam',(0,0,.852),(1.456,.583,.110),p['paint'],.009)
 box('Brake lower flat working bed',(0,-.004,.934),(1.540,.427,.068),p['steel'],.007)
 for x in [-.677,.677]:box('Brake clamping end tower',(x,.120,1.050),(.126,.188,.250),p['paint'],.009)
 box('Brake upper finger support bar',(0,.135,1.144),(1.432,.101,.094),p['paint'],.006)
 for i in range(12):
  x=-.605+i*.110
  extrude_x('Individual fixed brake clamp finger',x,.106,[(-.203,.979),(.166,.979),(.166,1.134),(-.075,1.134)],p['white'],.003)
 hinge=Vector((0,-.238,.955));a=math.radians(-25);center=hinge+Vector((0,math.sin(a)*.130,-math.cos(a)*.130))
 box('Fixed angled brake folding apron',center,(1.506,.047,.260),p['paint'],.008,rot=(a,0,0))
 box('Apron lower reinforcing beam',center+Vector((0,-.024,-.087)),(1.458,.073,.047),p['steel'],.004,rot=(a,0,0))
 for x in [-.781,.781]:cyl('Brake apron hinge',(x,-.238,.955),.052,.074,p['steel'],'X',v=32,b=.004)
 for x in [-.688,.688]:
  bar('Apron operating lever',(x,-.289,.841),(x,-.531,.474),.034,.040,p['steel'],.004)
  rod('Apron lower hand grip',(x,-.511,.504),(x,-.566,.421),.023,p['rubber'],24)
  rod('Upper clamp lever pivot',(x,.144,1.169),(x,.093,1.287),.017,p['steel'],24)
  rod('Upper clamp lever grip',(x,.093,1.287),(x,-.009,1.354),.022,p['rubber'],24)
 for x in [-.559,.559]:
  rod('Clamp screw visible stem',(x,.134,1.157),(x,.134,1.258),.013,p['steel'],24)
  cyl('Clamp screw broad knob',(x,.134,1.270),.035,.031,p['dark'],v=28,b=.003)
 box('Brake blank rear identification plate',(0,.296,.853),(.226,.014,.069),p['white'],.004)
 for x in [-.088,.088]:bolt('Rear plate screw',(x,.304,.853),.006,p['steel'],'Y')
 return ('city-manual-sheet-metal-brake','手動フィンガー式板金折曲機','Manual finger-style sheet-metal brake','板金作業場の背景に置く手動折曲機。補強付き四脚台、平らな作業ベッド、十二個の固定クランプフィンガー、前側の角度付き折曲エプロンと両端蝶番、左右の長い操作レバー/握り、上部の締付レバー・調整つまみ、裏面銘板を造形。フィンガーやレバーは一式の部品で、モデルは1点です。板材は付属せず、可動・加工精度・荷重・安全性能は未実装・未検証です。','A manual folding brake for sheet-metal workshop backgrounds. It has a braced four-leg stand, flat working bed, twelve fixed clamping fingers, angled front folding apron with end hinges, two long operating levers/grips, upper clamp levers/adjustment knobs and a rear blank plate. All fingers and levers belong to one model. No sheet is included; motion, forming accuracy, load and safety performance are unimplemented and untested.',['workshop','sheet-metal-brake','metal-forming','板金折曲'])

def toothed_wheel(n,x,y,z,r,d,m):
 N=48;vs=[]
 for xx in [x-d/2,x+d/2]:
  for i in range(N):
   rr=r*(1.10 if i%4 in [1,2] else .94);a=i*math.tau/N;vs.append((xx,y+rr*math.cos(a),z+rr*math.sin(a)))
 fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)];return mesh(n,vs,fs,m)

def three_roll_roller():
 p=pal();floor_stand(p,1.030,.438,.825,'Slip roller')
 box('Roller stand mounting deck',(0,0,.875),(1.197,.546,.070),p['paint'],.009)
 for x in [-.559,.559]:
  extrude_x('Three-roll machine side bearing frame',x,.092,[(-.250,.900),(.250,.900),(.214,1.218),(.117,1.286),(-.117,1.286),(-.214,1.218)],p['paint'],.006)
  for y,z in [(-.115,1.013),(.115,1.013),(0,1.170)]:cyl('Roller connected bearing cap',(x+(.060 if x>0 else -.060),y,z),.061,.049,p['white'],'X',v=32,b=.004)
 for y,z in [(-.115,1.013),(.115,1.013),(0,1.170)]:
  cyl('Exposed smooth forming roller',(0,y,z),.076,1.074,p['steel'],'X',v=48,b=.004)
  cyl('Forming roller shaft',(0,y,z),.025,1.303,p['steel'],'X',v=28,b=.002)
 for y in [-.115,.115]:toothed_wheel('Visible lower roll drive gear',-.663,y,1.013,.099,.036,p['dark'])
 toothed_wheel('Visible intermediate drive gear',-.663,0,1.105,.054,.036,p['steel'])
 cyl('Roller crank hub',(.685,-.115,1.013),.037,.100,p['steel'],'X',v=28,b=.003)
 ring('Roller three-spoke handwheel rim',(.719,-.115,1.013),.180,.014,p['dark'],'X',v=36)
 for i in range(3):
  a=i*math.tau/3;rod('Roller handwheel spoke',(.719,-.115,1.013),(.719,-.115+.177*math.cos(a),1.013+.177*math.sin(a)),.011,p['dark'],20)
 rod('Roller turning hand grip',(.719,-.115,1.193),(.827,-.115,1.193),.019,p['rubber'],24)
 for x in [-.559,.559]:
  box('Upper roll screw bridge',(x,0,1.298),(.137,.174,.053),p['white'],.005)
  cyl('Upper roll adjustment screw',(x,0,1.346),.014,.137,p['steel'],v=24,b=.001)
  cyl('Upper roll adjustment hand knob',(x,0,1.418),.047,.034,p['dark'],v=28,b=.004)
  rod('Adjustment knob cross handle',(x-.070,0,1.418),(x+.070,0,1.418),.009,p['steel'],20)
 box('Upper roller fixed release latch',(.657,.047,1.192),(.033,.103,.026),p['steel'],.003,rot=(0,0,.4))
 box('Roller rear cross stabilizer',(0,.224,1.070),(1.106,.037,.044),p['steel'],.004)
 return ('city-three-roll-slip-roller','3本ロール式板材曲げ機','Three-roll sheet-metal slip roller','金属加工場の背景に置く手動3本ロール曲げ機。四脚と補強、左右の軸受フレーム、三本の離れたローラー/主軸、片側の歯車外形、反対側の三本スポーク手回し輪と握り、二つの上側調整ねじ/つまみ、固定解除ラッチ外形を造形。板材や加工結果は付属せず一式1点。ローラー回転・歯車伝達・曲げ精度・荷重や安全性能は実装/検証していません。','A manual three-roll machine for metalworking backgrounds. It has a braced four-leg stand, side bearing frames, three separated rollers/shafts, visible gear exteriors on one side, a three-spoke handwheel/grip on the other, two upper adjustment screws/knobs and a fixed release-latch exterior. The whole assembly counts once; no stock or finished sheet is supplied. Roller/gear motion, forming accuracy, load and safety performance are unimplemented and untested.',['workshop','slip-roller','metal-forming','ロール曲げ'])

def hollow_bent_pipe(n,points,ro,ri,m,N=20):
 pts=[Vector(p) for p in points];vs=[];norms=[]
 for j,p in enumerate(pts):
  t=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized();u=Vector((0,0,1));v=t.cross(u).normalized();norms.append((u,v))
 for r in [ro,ri]:
  for p,(u,v) in zip(pts,norms):
   vs.extend(tuple(p+r*(math.cos(i*math.tau/N)*u+math.sin(i*math.tau/N)*v)) for i in range(N))
 L=len(pts);fs=[]
 for j in range(L-1):
  for i in range(N):
   k=(i+1)%N;fs.append((j*N+i,j*N+k,(j+1)*N+k,(j+1)*N+i));b=L*N;fs.append((b+j*N+k,b+j*N+i,b+(j+1)*N+i,b+(j+1)*N+k))
 for i in range(N):
  k=(i+1)%N;fs.append((k,i,L*N+i,L*N+k));a=(L-1)*N;b=(2*L-1)*N;fs.append((a+i,a+k,b+k,b+i))
 return mesh(n,vs,fs,m,smooth=True)

def pedestal_tube_bender():
 p=pal()
 box('Tube bender anchored base',(0,0,.036),(.559,.513,.072),p['steel'],.011)
 for x in [-.209,.209]:
  for y in [-.186,.186]:bolt('Pedestal floor anchor head',(x,y,.077),.017,p['bright'])
 box('Tube bender square pedestal',(0,0,.475),(.126,.126,.883),p['paint'],.009)
 for side in [-1,1]:bar('Tube bender base gusset',(side*.189,0,.070),(0,0,.338),.031,.054,p['steel'],.003)
 box('Bender working mounting plate',(0,0,.930),(.548,.444,.075),p['paint'],.009)
 profile_body('Grooved horizontal tube former',[(.185,.978),(.185,1.005),(.173,1.025),(.185,1.045),(.185,1.068),(.030,1.068),(.030,.978)],p['steel'],48)
 sleeve('Former lower support collar',(0,0,.973),.101,.024,.027,p['steel'],v=32)
 cyl('Former central pivot shaft',(0,0,1.047),.026,.231,p['steel'],v=28,b=.002)
 cyl('Former top locking washer',(0,0,1.076),.051,.021,p['dark'],v=28,b=.002)
 bolt('Former central hex fastener',(0,0,1.153),.033,p['white'])
 cyl('Opposed pressure roller',(.253,-.040,1.025),.047,.083,p['white'],v=32,b=.004)
 cyl('Pressure roller spindle',(.253,-.040,1.014),.012,.156,p['steel'],v=24,b=.001)
 box('Pressure roller connected bracket',(.226,-.040,.961),(.128,.119,.031),p['steel'],.004)
 box('Feed clamp connected mounting foot',(.235,-.160,.972),(.088,.079,.026),p['steel'],.003)
 box('Fixed feed-end clamp block',(.235,-.160,1.021),(.077,.071,.090),p['dark'],.006)
 # A short stationary bent hollow tube demonstrates the forming path, not mechanics.
 R=.191;pts=[(R,-.250,1.026),(R,-.125,1.026),(R,0,1.026)]
 pts.extend((R*math.cos(i*math.radians(110)/28),R*math.sin(i*math.radians(110)/28),1.026) for i in range(1,29))
 end=Vector(pts[-1]);t=Vector((-math.sin(math.radians(110)),math.cos(math.radians(110)),0));pts.extend([tuple(end+t*.120),tuple(end+t*.240)])
 hollow_bent_pipe('Fixed hollow demonstration tube',pts,.018,.012,p['white'],20)
 bar('Long fixed tube-bender lever',(0,0,1.110),(.794,-.243,1.110),.038,.042,p['steel'],.004)
 rod('Tube bender rubber hand grip',(.780,-.239,1.110),(.986,-.302,1.110),.025,p['rubber'],28)
 box('Blank pedestal identification plate',(0,-.068,.590),(.087,.012,.119),p['white'],.004)
 for z in [.551,.629]:bolt('Pedestal plate screw',(0,-.075,z),.005,p['steel'],'Y')
 return ('city-pedestal-tube-bender','台座式手動パイプ曲げ機','Pedestal-mounted manual tube bender','金属加工場の背景に置く台座式パイプ曲げ機。アンカー外形付き底板と補強、支柱/作業板、溝付きの丸い型と中心軸、押さえローラー/送り側クランプ、長い固定レバーと握り、両端が開いた短い曲がり管を造形。例示管も一式の部品で、モデル数は1点です。可動・加工経路・管材強度・精度・荷重や安全性能は未実装・未検証です。','A pedestal tube-bending machine for metalworking backgrounds. It has an anchored-looking base/bracing, column/working plate, grooved circular former/central pivot, pressure roller/feed clamp, long fixed lever/grip and a short bent example tube with both ends open. The example tube belongs to the single assembly and is not counted separately. Motion, forming path, stock strength, accuracy, load and safety behavior are unimplemented and untested.',['workshop','tube-bender','metal-forming','パイプ曲げ'])

BUILDERS=[shop_press,sheet_metal_brake,three_roll_roller,pedestal_tube_bender]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-053/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/metal_forming_equipment.py',azimuth=-55,elevation=27)
