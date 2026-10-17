"""Four original active-park equipment assemblies, Xenoah, CC BY 4.0.
Procedural geometry and plain PBR materials only. No brands or external assets.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(teal=mat('Muted petrol powder coating',(.035,.255,.29),.20,.44),amber=mat('Ochre yellow powder coating',(.79,.39,.045),.12,.43),steel=mat('Satin galvanized small fittings',(.43,.48,.50),.75,.36),dark=mat('Dark graphite coated frame',(.045,.063,.072),.22,.49),rubber=mat('Dark molded rubber feet',(.023,.030,.032),0,.79),deck=mat('Warm grey nonslip deck appearance',(.31,.35,.33),0,.82),white=mat('Warm ivory woven tape appearance',(.84,.82,.72),0,.77),net=mat('Dark olive net cord',(.035,.052,.038),0,.74),slab=mat('Warm sand climbing panel',(.48,.35,.23),0,.78),edge=mat('Dark ochre panel edges',(.24,.15,.08),0,.65),orange=mat('Terracotta climbing holds',(.64,.15,.052),0,.66),blue=mat('Blue green climbing holds',(.023,.30,.36),0,.63),yellow=mat('Mustard climbing holds',(.77,.49,.055),0,.66),purple=mat('Muted plum climbing holds',(.28,.095,.22),0,.67))

def cyl(n,p,r,h,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,h,m,vertices=v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(n,a,b,r,m,v=16,bev=.0006):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(bev,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bar(n,a,b,w,t,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def ring(n,p,r,t,m,axis='Z',v=48,mv=8):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=mv,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)

def sleeve(n,p,ro,ri,h,m,v=64):
 vs=[]
 for r,z in [(ro,-h/2),(ro,h/2),(ri,h/2),(ri,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)];o=mesh(n,vs,fs,m);o.location=p
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o

def sector(n,r0,r1,a0,a1,z,h,m,steps=20):
 vs=[(r*math.cos(a0+(a1-a0)*i/steps),r*math.sin(a0+(a1-a0)*i/steps),zz) for zz in [z-h/2,z+h/2] for r in [r0,r1] for i in range(steps+1)];s=steps+1;fs=[]
 for i in range(steps):fs.extend([(i,i+1,s+i+1,s+i),(2*s+i,3*s+i,3*s+i+1,2*s+i+1),(i,2*s+i,2*s+i+1,i+1),(s+i,s+i+1,3*s+i+1,3*s+i)])
 fs.extend([(0,s,3*s,2*s),(steps,2*s+steps,3*s+steps,s+steps)])
 return mesh(n,vs,fs,m,.006)

def xy(r,a,z):return (r*math.cos(a),r*math.sin(a),z)

def roundabout():
 p=palette()
 cyl('Ground bearing anchor plate',(0,0,.023),.325,.046,p['dark'],v=64,b=.007)
 cyl('Central fixed pedestal',(0,0,.139),.105,.232,p['steel'],v=40,b=.004)
 cyl('Lower rotating hub housing',(0,0,.222),.195,.130,p['teal'],v=48,b=.006)
 for i in range(8):
  a=i*math.tau/8
  cyl('Anchor plate hex bolt',xy(.255,a,.053),.017,.016,p['steel'],v=6)
  bar('Deck underside radial stiffener',xy(.14,a,.255),xy(.96,a,.255),.052,.061,p['dark'],.004)
 sleeve('Deep circular deck rim',(0,0,.292),1.065,1.014,.090,p['teal'],v=96)
 cyl('Continuous circular standing deck',(0,0,.305),1.032,.064,p['deck'],v=96,b=.007)
 # Non-slip raised radial strips are attached, not a texture or safety claim.
 for i in range(24):
  a=i*math.tau/24
  bar('Raised deck grip strip',xy(.34,a,.336),xy(.985,a,.336),.010,.004,p['dark'],.001)
 cyl('Raised central hub cap',(0,0,.383),.155,.140,p['teal'],v=48,b=.008)
 cyl('Center handrail mast',(0,0,.641),.040,.534,p['teal'],v=32,b=.003)
 cyl('Center mast domed-looking cap',(0,0,.917),.045,.032,p['teal'],v=32,b=.008)
 ring('Shared central circular hand grip',(0,0,.910),.225,.022,p['amber'],v=64,mv=12)
 for i in range(3):
  a=i*math.tau/3+.18
  rod('Central grip radial attachment',xy(.025,a,.910),xy(.225,a,.910),.022,p['amber'],v=20)
  # Three radial bent-looking rails terminate in deck sockets.
  pts=[xy(.90,a,.330),xy(.90,a,.825),xy(.865,a,.890),xy(.79,a,.924),xy(.23,a,.924)]
  tube('Connected outer handrail',pts,.023,p['amber'],resolution=2)
  cyl('Handrail deck socket',xy(.90,a,.360),.046,.058,p['steel'],v=24,b=.003)
  sector('Curved fixed bench seat',.675,.930,a+.34,a+1.05,.594,.058,p['amber'])
  # A real curved bearer beneath every seat reaches its pair of mounting arms.
  sector('Seat underside curved bearer',.760,.835,a+.30,a+1.08,.550,.044,p['teal'])
  for aa in [a+.40,a+.98]:
   rod('Bench diagonal support arm',xy(.80,a+.60,.456),xy(.80,aa,.552),.023,p['teal'],v=20)
   cyl('Seat top fastening',xy(.805,aa,.626),.011,.009,p['steel'],v=6)
 # All three seats have direct floor posts beneath their actual arcs.
 for i in range(3):
  a=i*math.tau/3+.18
  for aa in [a+.42,a+.98]:
   cyl('Curved bench direct support',xy(.80,aa,.449),.029,.239,p['teal'],v=24,b=.002)
   cyl('Bench post deck flange',xy(.80,aa,.347),.052,.024,p['steel'],v=24,b=.002)
 return ('city-playground-roundabout','ベンチと手すり付き公園回転遊具','Playground roundabout with seats and rails','公園の遊び場に配置する、円形デッキと固定ベンチを備えた回転遊具の静的モデル。縁枠と滑り止め風の桟、三つの湾曲座面、中央の環状グリップと外側手すり、足元金具、下面の放射状補強、軸受風ハブと接地プレートを造形。全体で1点です。回転・衝突判定はなく、実用品の安全性・耐荷重・規格適合は未検証です。','A static roundabout assembly for playground scenes, with a circular deck and three fixed curved benches. It has a rim, raised grip-looking strips, central ring grip and outer rails, foot sockets, radial underside stiffeners, bearing-looking hub and grounded anchor plate. The whole assembly counts as one model. Rotation and collision behavior are absent; real-equipment safety, load capacity and standards compliance are unvalidated.',['playground','roundabout','round-deck','回転遊具'])

def elliptical_link(n,center,direction,normal,m):
 # Closed oval torus. Alternating link planes and overlapping oval spans thread
 # through adjacent link openings rather than creating floating dashed rods.
 d=Vector(direction).normalized();normal=Vector(normal).normalized();u=d.cross(normal).normalized();vs=[];N=20;K=8
 for i in range(N):
  a=i*math.tau/N;v=u*(.015*math.cos(a))+d*(.028*math.sin(a));rad=(u*(math.cos(a)/.015)+d*(math.sin(a)/.028)).normalized()
  for j in range(K):
   b=j*math.tau/K;vs.append(Vector(center)+v+.0032*(rad*math.cos(b)+normal*math.sin(b)))
 fs=[(i*K+j,((i+1)%N)*K+j,((i+1)%N)*K+(j+1)%K,i*K+(j+1)%K) for i in range(N) for j in range(K)]
 return mesh(n,vs,fs,m,smooth=True)

def chain_course(n,a,b,m):
 a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.1:u=Vector((1,0,0))
 u.normalize();v=d.cross(u).normalized();count=max(2,round((b-a).length/.044))
 for j in range(count+1):elliptical_link(n,a+(b-a)*(j/count),d,u if j%2==0 else v,m)

def disc_target():
 p=palette()
 cyl('Disc target grounded mounting plate',(0,0,.022),.245,.044,p['dark'],v=64,b=.006)
 cyl('Target lower pole mounting collar',(0,0,.127),.080,.220,p['steel'],v=40,b=.003)
 cyl('Disc target central pole',(0,0,.896),.032,1.748,p['steel'],v=32,b=.002)
 for i in range(6):cyl('Target mounting hex anchor',xy(.185,i*math.tau/6,.052),.015,.017,p['steel'],v=6)
 cyl('Basket supporting pole collar',(0,0,.687),.065,.092,p['teal'],v=40,b=.003)
 ring('Open basket lower circular rail',(0,0,.740),.240,.009,p['steel'],v=64)
 ring('Open basket upper circular rim',(0,0,.972),.365,.011,p['steel'],v=72)
 ring('Basket middle wire course',(0,0,.850),.298,.0055,p['steel'],v=64)
 for i in range(20):
  a=i*math.tau/20
  rod('Basket open radial floor wire',xy(.040,a,.732),xy(.241,a,.740),.0055,p['steel'],v=12)
  rod('Basket outward rising wire',xy(.241,a,.740),xy(.366,a,.972),.0055,p['steel'],v=12)
 for i in range(8):rod('Basket load-bearing radial arm',(0,0,.695),xy(.240,i*math.tau/8,.740),.011,p['teal'],v=16)
 ring('Lower chain gathering ring',(0,0,1.010),.084,.008,p['steel'],v=48)
 for i in range(4):rod('Gathering ring radial spoke',xy(.030,i*math.tau/4,1.010),xy(.084,i*math.tau/4,1.010),.006,p['steel'],v=12)
 # Open top crown: center cap, radial spokes, colored outer band and inner chain rail.
 cyl('Top crown pole collar',(0,0,1.705),.054,.110,p['teal'],v=32,b=.003)
 sleeve('Top crown open annular colored band',(0,0,1.720),.306,.292,.080,p['amber'],v=72)
 ring('Upper chain suspension rail',(0,0,1.683),.267,.009,p['steel'],v=64)
 for i in range(8):
  a=i*math.tau/8
  rod('Crown radial support spoke',xy(.035,a,1.715),xy(.300,a,1.715),.008,p['teal'],v=16)
  rod('Suspension rail small tab',xy(.267,a,1.683),xy(.267,a,1.719),.006,p['steel'],v=12)
 for i in range(14):
  a=i*math.tau/14+.10
  # Endpoint link openings engage the two horizontal metal support rings.
  chain_course('Alternating oval disc-catcher chain',xy(.267,a,1.667),xy(.084,a,1.026),p['steel'])
 cyl('Target upper closed cap',(0,0,1.773),.044,.030,p['teal'],v=32,b=.007)
 return ('city-disc-golf-target','開放ワイヤーバスケット付きディスクゴルフ的','Disc-golf target with open wire basket','公園のディスクゴルフ区画に配置する、中心ポール式ターゲットの一式。開放したワイヤーバスケット、上下の円環、交互に向きを変えた楕円リンクのチェーン列、透けた上部クラウン、支えスポーク、ポール固定カラーとボルト付き接地板を造形。ディスクは含まず、全体で1点です。チェーンの揺れ・捕球判定はなく、競技規格や実用品の安全性は未検証です。','A center-pole disc-golf target assembly for park course scenes. It has an open wire basket, upper/lower rings, courses of alternating oval chain links, an open top crown, support spokes, pole collars and a bolted grounded plate. No disc is included; the whole target counts as one model. Chain movement and catching behavior are absent; competition specifications and real-equipment safety are unvalidated.',['sports','disc-golf','wire-basket','ディスクゴルフ'])

def tape(n,xs,zs,height,depth,m):
 # Closed volume following the net sag, including front/back and both end caps.
 vs=[]
 for x,z in zip(xs,zs):vs.extend([(x,-depth/2,z-height/2),(x,depth/2,z-height/2),(x,depth/2,z+height/2),(x,-depth/2,z+height/2)])
 fs=[]
 for i in range(len(xs)-1):
  for j in range(4):fs.append((i*4+j,(i+1)*4+j,(i+1)*4+(j+1)%4,i*4+(j+1)%4))
 fs.extend([(3,2,1,0),tuple(range(len(vs)-4,len(vs)))])
 return mesh(n,vs,fs,m)

def tennis_set():
 p=palette();half=6.35
 for x in [-6.43,6.43]:
  cyl('Tennis post grounded plate',(x,0,.020),.175,.040,p['dark'],v=48,b=.005)
  cyl('Tennis net main post',(x,0,.572),.047,1.100,p['teal'],v=32,b=.003)
  cyl('Post lower thick collar',(x,0,.109),.071,.154,p['dark'],v=32,b=.003)
  cyl('Post closed crown cap',(x,0,1.130),.054,.041,p['teal'],v=32,b=.008)
  for i in range(4):cyl('Post base anchor bolt',(x+.125*math.cos(i*math.tau/4),.125*math.sin(i*math.tau/4),.048),.012,.016,p['steel'],v=6)
  inward=-1 if x>0 else 1
  for z in [.16,.57,1.065]:
   rod('Post net lashing eye stem',(x,0,z),(x+inward*.068,0,z),.009,p['steel'],v=16)
   ring('Post net lashing closed eye',(x+inward*.071,0,z),.016,.004,p['steel'],'X',24)
  # Fixed post-side collar and cable routing remain visible from the rear.
  cyl('Post top cable guide axle',(x,0,1.076),.016,.133,p['steel'],'Y',v=24)
  ring('Cable guide outer wheel',(x,-.067,1.076),.030,.006,p['steel'],'Y',32)
 # Continuous lightly sagged net, made of closed individual cords rather than a sheet.
 N=158;xs=[-half+2*half*i/N for i in range(N+1)]
 top=lambda x:.925+.145*(abs(x)/half)**2
 bot=lambda x:.110+.025*(abs(x)/half)**2
 for i,x in enumerate(xs):rod('Closed vertical tennis net cord',(x,0,bot(x)),(x,0,top(x)),.0027,p['net'],v=8,bev=0)
 for row in range(12):
  f=row/11
  pts=[(x,0,bot(x)+(top(x)-bot(x))*f) for x in xs[::2]]
  if pts[-1][0]!=xs[-1]:pts.append((xs[-1],0,bot(xs[-1])+(top(xs[-1])-bot(xs[-1]))*f))
  tube('Closed horizontal sagged net cord',pts,.0025,p['net'],resolution=0)
 tape('Continuous ivory upper net tape',xs,[top(x) for x in xs],.054,.014,p['white'])
 tape('Continuous dark bottom net binding',xs,[bot(x) for x in xs],.019,.010,p['net'])
 for x in [-half,half]:box('Net vertical side binding',(x,0,(top(x)+bot(x))/2),(.042,.015,top(x)-bot(x)+.035),p['white'],.002)
 # Fixed tension cable follows the top edge and passes into the post fittings.
 tube('Top net tension cable',[(-6.43,-.065,1.075),(-6.35,0,1.070)]+[(x,0,top(x)) for x in xs[1:-1]]+[(6.35,0,1.070),(6.43,-.065,1.075)],.0034,p['steel'],resolution=1)
 box('Center retaining strap',(0,-.014,.473),(.041,.010,.946),p['white'],.002)
 box('Center strap rear return',(0,.014,.473),(.041,.010,.946),p['white'],.002)
 box('Center strap top fold',(0,0,.944),(.041,.036,.014),p['white'],.002)
 box('Center strap ground anchor plate',(0,0,.012),(.130,.110,.024),p['dark'],.004)
 for x in [-.041,.041]:cyl('Center strap anchor fastener',(x,0,.029),.009,.012,p['steel'],v=6)
 # Right-side external crank gearbox, drum, lever, and connected cable.
 x=6.43
 box('Crank gearbox attached housing',(x+.080,0,.817),(.154,.129,.144),p['teal'],.012)
 cyl('Crank horizontal drive shaft',(x+.186,0,.817),.016,.108,p['steel'],'X',v=24)
 bar('Tennis net crank arm',(x+.242,0,.817),(x+.242,0,.678),.024,.019,p['steel'],.003)
 cyl('Crank hand grip spindle',(x+.274,0,.678),.012,.078,p['steel'],'X',v=20)
 cyl('Crank rubber hand grip',(x+.311,0,.678),.023,.084,p['rubber'],'X',v=24,b=.005)
 cyl('Cable fixed winding drum',(x+.082,-.085,.817),.045,.065,p['dark'],'Y',v=32,b=.003)
 tube('Right post exposed tension cable',[(x,-.065,1.075),(x+.081,-.112,.942),(x+.081,-.112,.848)],.0034,p['steel'],resolution=1)
 for z in [.768,.869]:cyl('Gearbox cover fastening',(x+.159,-.045,z),.008,.008,p['steel'],'X',v=6)
 # The opposing dead-end cable uses a small turnbuckle, not a second crank.
 rod('Left post cable anchor bracket',(-6.43,0,.855),(-6.50,-.054,.855),.012,p['steel'],v=16)
 cyl('Left fixed cable anchor barrel',(-6.50,-.054,.917),.012,.130,p['steel'],v=20)
 tube('Left post exposed anchored cable',[(-6.43,-.065,1.075),(-6.50,-.054,.978)],.0034,p['steel'],resolution=1)
 return ('city-tennis-net-set','支柱と巻取ハンドル付きテニスネット','Tennis net set with posts and crank','テニスコート場面へ据える、ネット・二本の支柱・張力金具の一式。実体のある縦横コード、中央へ下がる上端テープ、側端と下端の縁取り、中央押さえ帯、巻取箱とハンドル、反対側の固定金具、接地アンカーを造形。床・ライン・コート・ラケットは含まず、全体で1点です。網目は表示用に簡略化され、張力調整・競技規格・実用品の安全性は未検証です。','A net, two-post and tension-fitting assembly for tennis-court scenes. It has solid vertical/horizontal cords, sagged upper tape, side/bottom bindings, center retaining strap, crank housing and handle, opposite fixed cable anchor and grounded plates. Court flooring, lines and rackets are absent; the whole set counts as one model. The mesh spacing is simplified for visualization; tension adjustment, competition specifications and real-equipment safety are unvalidated.',['sports','tennis','net','テニスネット'])

def hold(n,x,z,w,h,d,seed,m,steel):
 # Irregular convex faceted handhold; thick front volume and inset-looking bolt.
 # Fixed deterministic angular patterns make each hold original without spheres.
 N=7;vs=[]
 for layer,y,scale in [(0,-.127,1.0),(1,-.127-d*.72,.91),(2,-.127-d,.42)]:
  for i in range(N):
   a=i*math.tau/N+.19*seed;rr=1+.11*math.sin(i*2.3+seed*.8)
   vs.append((x+math.cos(a)*w*.5*rr*scale+(d*.10 if layer==2 else 0),y,z+math.sin(a)*h*.5*rr*scale))
 fs=[tuple(reversed(range(N)))];fs.extend((k*N+i,k*N+(i+1)%N,(k+1)*N+(i+1)%N,(k+1)*N+i) for k in range(2) for i in range(N));fs.append(tuple(range(2*N,3*N)))
 mesh(n,vs,fs,m,.004)
 cyl('Hold central dark bolt recess',(x,-.129-d,z),.013,.006,palette_ref['dark'],'Y',v=20,b=.0006)
 cyl('Hold exposed hex fixing',(x,-.135-d,z),.007,.008,steel,'Y',v=6,b=.0005)

palette_ref={}
def climbing_wall():
 global palette_ref
 p=palette();palette_ref=p
 # Thick freestanding slab is carried by its frame; no invented invisible ground.
 for x in [-1.07,1.07]:
  box('Wall long grounded base runner',(x,.510,.065),(.150,1.770,.090),p['dark'],.008)
  for y in [-.287,1.307]:box('Wall ground runner rubber pad',(x,y,.024),(.180,.176,.048),p['rubber'],.006)
  box('Wall main upright frame',(x,.038,1.600),(.100,.100,3.070),p['teal'],.007)
  box('Wall mast lower mounting shoe',(x,.038,.155),(.186,.192,.150),p['steel'],.006)
  bar('Rear long structural diagonal',(x,1.245,.118),(x,.079,2.570),.075,.075,p['teal'],.005)
  box('Rear brace bottom bolted shoe',(x,1.245,.133),(.156,.188,.067),p['steel'],.006)
  for y in [-.250,1.247]:cyl('Base runner anchor bolt',(x,y,.172 if y>0 else .114),.014,.018,p['steel'],v=6)
  for z in [.190,2.560,3.070]:cyl('Frame side fastening',(x+(.056 if x>0 else -.056),.038,z),.015,.016,p['steel'],'X',v=6)
 for z in [.260,1.015,1.875,2.685,3.075]:box('Rear slab cross bearer',(0,.040,z),(2.170,.090,.090),p['teal'],.006)
 box('Rear floor tie',(0,1.245,.068),(2.196,.080,.080),p['dark'],.006)
 bar('Back frame racking diagonal',(-1.022,.102,.315),(1.022,.102,2.996),.043,.032,p['steel'],.003)
 # Three joined panels with restrained visible construction seams.
 for i,z in enumerate([.745,1.685,2.625]):
  box('Thick climbing slab panel',(0,-.062,z),(2.090,.140,.932),p['slab'],.008)
  for x in [-.971,.971]:
   for zz in [z-.376,z+.376]:cyl('Climbing slab frame screw',(x,-.137,zz),.012,.012,p['steel'],'Y',v=6)
 for x in [-1.054,1.054]:box('Climbing panel perimeter edge trim',(x,-.062,1.685),(.032,.156,2.837),p['edge'],.005)
 for z in [.270,3.100]:box('Climbing slab top bottom edge trim',(0,-.062,z),(2.145,.156,.031),p['edge'],.005)
 # Original routes, varying orientation/proportions, bolted to the slab face.
 holds=[(-.69,.51,.21,.12,.07,0,'orange'),(-.19,.39,.17,.10,.065,1,'yellow'),(.40,.53,.20,.13,.08,2,'blue'),(.76,.82,.16,.17,.075,3,'purple'),(-.42,.91,.24,.12,.085,4,'blue'),(.03,1.06,.15,.19,.09,5,'orange'),(-.81,1.31,.17,.21,.075,6,'yellow'),(.47,1.32,.25,.12,.09,7,'yellow'),(.80,1.65,.15,.17,.075,8,'orange'),(-.29,1.63,.21,.15,.105,9,'purple'),(-.68,1.94,.21,.13,.09,10,'orange'),(.18,1.97,.24,.14,.09,11,'blue'),(.61,2.23,.19,.17,.10,12,'purple'),(-.11,2.34,.17,.20,.08,13,'yellow'),(-.77,2.58,.23,.13,.10,14,'blue'),(.30,2.70,.23,.13,.085,15,'orange'),(.80,2.88,.16,.15,.09,16,'yellow'),(-.32,2.91,.19,.12,.07,17,'purple')]
 for x,z,w,h,d,s,c in holds:hold('Original faceted climbing hold',x,z,w,h,d,s,p[c],p['steel'])
 # Spare dark capped insert sockets are attached face disks, not perforation claims.
 for x,z in [(-.79,.73),(.19,.71),(-.54,1.15),(.73,1.14),(.15,1.48),(-.70,1.72),(.52,1.91),(-.48,2.20),(.28,2.43),(-.61,2.80)]:
  cyl('Unused capped hold fixing socket',(x,-.134,z),.010,.009,p['dark'],'Y',v=16,b=.001)
 return ('city-freestanding-climbing-wall','斜材付き自立クライミングウォール','Freestanding climbing wall with rear braces','公園や屋内運動施設の背景へ置く、自立式クライミングパネルの一式。厚みのある三段パネル、大小の不規則なオリジナルホールドと固定ボルト、周囲縁材、背面の横桟と筋交い、長い後方斜材、連結接地レールとゴム足を造形。マット・人・ロープは含まず、全体で1点です。登攀動作・荷重計算・落下保護・実用品の安全性は未検証です。','A freestanding climbing-panel assembly for park and indoor exercise-facility backdrops. It has three thick panels, varied irregular original holds with fixing bolts, perimeter trim, rear bearers and cross brace, long rear diagonals, connected base rails and rubber feet. Mats, people and ropes are absent; the whole wall counts as one model. Climbing behavior, load calculations, fall protection and real-equipment safety are unvalidated.',['sports','climbing','climbing-wall','クライミング'])

BUILDERS=[roundabout,disc_target,tennis_set,climbing_wall]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-054/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/active_park_equipment.py',azimuth=-73 if s[0]=='city-tennis-net-set' else -55,elevation=20 if s[0]=='city-tennis-net-set' else 25)
