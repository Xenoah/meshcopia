"""Original static compact construction equipment for Xenoah, CC BY 4.0.
No third-party design, logos, textures or fonts. Blender 4.3.2.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def pal():return dict(steel=mat('Zinc plated steel',(.36,.40,.42),.8,.36),iron=mat('Rough cast iron',(.08,.095,.10),.55,.67),black=mat('Graphite machine powder coat',(.025,.033,.035),.3,.48),rubber=mat('Non-marking rubber',(.012,.017,.02),0,.86),ochre=mat('Industrial ochre enamel',(.58,.28,.045),.25,.40),blue=mat('Service blue enamel',(.065,.19,.26),.28,.38),white=mat('Blank enamel indicator',(.78,.79,.71),.12,.38),red=mat('Safety control red',(.45,.055,.035),.15,.42),brass=mat('Brass couplings',(.48,.32,.11),.75,.4))
def cyl(n,p,r,d,m,axis='Z',verts=32,b=.002,r2=None):
 if r2 is None:o=cylinder(n,p,r,d,m,verts,bevel=b)
 else:
  bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=p);o=finish(bpy.context.object,n,m,b,True)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,verts=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,b=min(.001,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,d,m):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,.003);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def screw(n,p,m,axis='Z',r=.006):
 cyl(n+' washer',p,r*1.5,r*.25,m,axis,20,.0002);q=list(p);q['XYZ'.index(axis)]+=(-1 if axis=='Y' else 1)*r*.4;cyl(n+' head',q,r,r*.7,m,axis,6,.0003)
def extrusion(n,profile,w,m,b=.004):
 vs=[(x,y,z) for x in [-w/2,w/2] for y,z in profile];k=len(profile);fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,b)
def rounded_frame(n,center,w,h,r,t,m,y=0):
 # Closed tubular rounded rectangle in XZ plane, deterministic circular bends.
 pts=[]
 for cx,cz,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(9):
   an=math.radians(a+i*90/8);pts.append((center[0]+cx+r*math.cos(an),y,center[2]+cz+r*math.sin(an)))
 pts.append(pts[0]);return tube(n,pts,t,m,2)
def engine(n,c,p,scale=1):
 x,y,z=c;s=scale
 def P(a,b,c):return(x+a*s,y+b*s,z+c*s)
 def S(a,b,c):return(a*s,b*s,c*s)
 box(n+' crankcase',P(0,0,.04),S(.19,.21,.17),p['iron'],.018*s)
 # Exposed horizontal cylinder cooling fins and rectangular rocker cover.
 for i in range(7):box(n+' cooling fin %02d'%i,P(0,.052,.149+i*.012),S(.18,.16,.007),p['iron'],.0015*s)
 box(n+' rocker cover',P(0,.052,.237),S(.18,.15,.045),p['steel'],.009*s)
 for xx in [-.063,.063]:screw(n+' rocker fastener',P(xx,.052,.261),p['black'],r=.006*s)
 cyl(n+' recoil starter',P(0,-.132,.08),.087*s,.055*s,p['ochre'],'Y',40,.005*s)
 cyl(n+' recoil center',P(0,-.164,.08),.026*s,.013*s,p['black'],'Y',32,.002*s)
 for i in range(10):
  a=math.tau*i/10;xx=.059*math.sin(a);zz=.08+.059*math.cos(a)
  o=box(n+' starter ventilation recess',P(xx,-.163,zz),S(.009,.005,.024),p['black'],.003*s);o.rotation_euler[1]=a
 tube(n+' starter cord',[P(.044,-.15,.16),P(.087,-.165,.187),P(.11,-.16,.195)],.003*s,p['black'],1)
 box(n+' pull grip',P(.115,-.16,.201),S(.069,.028,.020),p['rubber'],.007*s)
 box(n+' air-filter housing',P(.135,.045,.14),S(.08,.13,.15),p['black'],.012*s)
 for i in range(5):box(n+' air-filter grille',P(.178,.045,.09+i*.024),S(.005,.10,.006),p['iron'],.001*s)
 # A simple exhaust elbow and closed muffler with perforated external shield.
 tube(n+' exhaust pipe',[P(-.07,.10,.19),P(-.13,.14,.18),P(-.15,.14,.12)],.012*s,p['steel'],2)
 box(n+' muffler body',P(-.15,.10,.08),S(.095,.12,.09),p['black'],.009*s)
 for i in range(6):box(n+' muffler heat-shield rib',P(-.205,.10,.04+i*.016),S(.006,.14,.007),p['steel'],.001*s)
 box(n+' upper shield bridge',P(-.205,.10,.13),S(.012,.155,.013),p['steel'],.002*s)
 return

def compactor():
 p=pal()
 extrusion('Formed compaction base plate',[(-.39,.045),(-.32,0),(.31,0),(.39,.037),(.39,.073),(.30,.04),(-.31,.04),(-.39,.078)],.52,p['iron'],.008)
 for x in [-.18,.18]:bar('Plate reinforcement runner',(x,-.27,.062),(x,.27,.062),.034,.045,p['iron'])
 cyl('Front exciter bearing housing',(0,-.17,.145),.077,.34,p['ochre'],'X',40,.005)
 for x in [-.17,.17]:
  cyl('Exciter end cover',(x,-.17,.145),.082,.018,p['steel'],'X',40,.002)
  for y in [-.21,-.13]:screw('Exciter fixing',(x,y,.211),p['steel'],r=.006)
 for x in [-.16,.16]:
  for y in [.02,.24]:cyl('Elastomer engine isolation mount',(x,y,.117),.028,.06,p['rubber'],verts=24,b=.003)
 box('Floating engine platform',(0,.13,.157),(.40,.32,.026),p['ochre'],.005)
 engine('Air-cooled compactor engine',(0,.11,.20),p,.88)
 box('Fuel tank',(0,-.015,.493),(.30,.21,.13),p['ochre'],.026)
 cyl('Fuel cap',(.07,-.025,.566),.029,.021,p['black'],verts=32,b=.004)
 # Visible belt safety guard and independent carrying lifting eye.
 extrusion('External drive-belt guard',[(-.24,.125),(-.24,.27),(.03,.41),(.18,.38),(.18,.18),(.12,.11)],.065,p['ochre'],.012).location.x=-.245
 for y,z in [(-.18,.21),(.07,.30)]:screw('Belt guard fixing',(-.282,y,z),p['steel'],'X',r=.007)
 for x in [-.21,.21]:
  cyl('Handle pivot',(x,.30,.24),.030,.045,p['steel'],'X',24,.003)
  tube('Isolated folding handle upright',[(x,.30,.24),(x,.44,.35),(x,.66,.79),(x,.68,.94)],.018,p['black'],2)
 rod('Handle top bar',(-.21,.68,.94),(.21,.68,.94),.019,p['black'])
 rod('Vibration-damping handle grip',(-.16,.68,.94),(.16,.68,.94),.027,p['rubber'],32)
 box('Throttle lever mount',(.14,.68,.94),(.047,.055,.045),p['black'],.006)
 bar('Throttle lever',(.14,.68,.96),(.14,.64,1.01),.012,.014,p['red'])
 tube('Throttle cable',[(.14,.67,.93),(.14,.60,.71),(.16,.38,.42),(.12,.19,.37)],.003,p['black'],1)
 return('city-plate-compactor','小型プレートコンパクター','Compact vibratory plate compactor','舗装補修や小規模な路盤工事に配置する振動転圧機。反り上がった底板、起振部、エンジンの冷却フィン、防振支持、ベルトカバーと操作ハンドルを造形。転圧・燃焼・振動機能はありません。','A compact plate compactor for road repairs and small sub-base works. Includes a formed compaction shoe, exciter housing, finned engine, isolated platform, belt guard and control handle. No compaction, combustion or vibration behavior is supplied.',['compactor','construction','roadwork','転圧'])

def rammer():
 p=pal()
 box('Cast rammer shoe',(0,0,.038),(.31,.36,.076),p['iron'],.015)
 box('Replaceable shoe sole',(0,0,.009),(.306,.355,.018),p['rubber'],.005)
 for x in [-.11,.11]:box('Shoe top rib',(x,0,.09),(.027,.29,.045),p['iron'],.005)
 for x in [-.09,.09]:
  for y in [-.12,.12]:screw('Sole anchor',(x,y,.119),p['steel'],r=.007)
 cyl('Telescopic lower leg',(0,0,.24),.065,.27,p['steel'],verts=40,b=.003)
 # Separate thin toroidal folds resemble an intact protective bellows.
 cyl('Bellows central sheath',(0,0,.38),.089,.32,p['rubber'],verts=40,b=.002)
 for i in range(11):torus('Protective bellows fold %02d'%i,(0,0,.235+i*.029),.088,.012,p['rubber'],segments=40)
 cyl('Lower bellows clamp',(0,0,.218),.095,.018,p['steel'],verts=40,b=.002)
 cyl('Upper bellows clamp',(0,0,.543),.099,.026,p['steel'],verts=40,b=.002)
 box('Ramming drive gearbox',(0,0,.635),(.25,.26,.19),p['ochre'],.026)
 for x in [-.132,.132]:
  cyl('Gearcase round access cover',(x,0,.64),.078,.015,p['iron'],'X',32,.003)
  for i in range(4):
   a=math.tau*i/4;screw('Gearcase screw',(x,.056*math.cos(a),.64+.056*math.sin(a)),p['steel'],'X',r=.005)
 engine('Rammer power unit',(0,.005,.723),p,.80)
 box('Upper fuel tank',(0,-.01,1.007),(.33,.27,.14),p['ochre'],.025)
 cyl('Raised fuel filler',(.06,-.015,1.087),.030,.022,p['black'],verts=32,b=.004)
 # Continuous protected handle frame and isolation pads.
 for x in [-.205,.205]:
  tube('Suspended handle side rail',[(x,.03,.65),(x,.18,.77),(x,.18,1.05),(x,.13,1.15),(x,-.17,1.15),(x,-.25,1.08),(x,-.25,.80)],.021,p['black'],2)
  cyl('Handle isolation block',(x,.015,.67),.033,.05,p['rubber'],'X',24,.003)
 rod('Rear operator handle',(-.205,.18,1.05),(.205,.18,1.05),.024,p['rubber'],24)
 rod('Front carry crossbar',(-.205,-.25,.80),(.205,-.25,.80),.021,p['black'],24)
 rod('Tank protection upper crossbar',(-.205,-.17,1.15),(.205,-.17,1.15),.021,p['black'],24)
 box('Throttle housing',(.14,.18,1.05),(.047,.058,.051),p['black'],.007)
 bar('Rammer throttle',(.14,.18,1.075),(.14,.15,1.12),.013,.014,p['red'])
 return('city-tamping-rammer','小型の振動タンピングランマー','Compact tamping rammer','狭い溝や道路補修現場の転圧作業を表す縦型ランマー。矩形の足、伸縮脚、蛇腹カバー、駆動ケース、エンジンと防振ハンドルを備えます。プレート転圧機とは異なる狭所用機器の静的形状です。','A vertical tamping rammer for narrow trench and road-repair scenes, with a rectangular shoe, telescopic leg, protective bellows, gearbox, engine and isolated handle. This is a narrow-area tamping machine, functionally distinct from a plate compactor; no operational motion is included.',['rammer','tamping','construction','ランマー'])

def generator():
 p=pal()
 for y in [-.235,.235]:rounded_frame('Tubular generator roll cage',(0,0,.31),.72,.56,.075,.020,p['black'],y)
 for x in [-.30,.30]:
  for z in [.06,.56]:rod('Cage cross member',(x,-.235,z),(x,.235,z),.020,p['black'])
  for y in [-.19,.19]:box('Rubber vibration foot',(x,y,.024),(.10,.083,.048),p['rubber'],.013)
 box('Lower skid tray',(0,0,.085),(.61,.40,.026),p['steel'],.008)
 engine('Generator petrol engine',(-.13,.01,.13),p,.83)
 # Alternator axis along X, with cooling bands and a rear vented end cap.
 cyl('Alternator body',(.15,.018,.26),.134,.29,p['iron'],'X',48,.007)
 for x in [.07,.11,.15,.19,.23]:cyl('Alternator casing fin',(x,.018,.26),.141,.010,p['steel'],'X',48,.001)
 cyl('Alternator rear cooling cowl',(.303,.018,.26),.137,.023,p['black'],'X',48,.003)
 for i in range(12):
  an=i*math.tau/12;yy=.018+.089*math.cos(an);zz=.26+.089*math.sin(an)
  o=box('Alternator vent impression',(.318,yy,zz),(.004,.014,.050),p['iron'],.003);o.rotation_euler[0]=an
 box('Wide generator fuel tank',(0,.015,.485),(.56,.35,.12),p['blue'],.028)
 cyl('Fuel filler cap',(.16,.025,.553),.036,.020,p['black'],verts=40,b=.005)
 box('Recessed fuel gauge',(-.16,.025,.549),(.08,.025,.009),p['black'],.004)
 box('Gauge indicator',(-.17,.025,.555),(.022,.016,.003),p['white'],.001)
 # Externally visible control panel, unbranded and with blank meter.
 box('Control panel housing',(.15,-.245,.326),(.315,.040,.235),p['blue'],.010)
 box('Control panel face',(.15,-.269,.326),(.285,.010,.205),p['black'],.007)
 for x in [.08,.22]:
  cyl('Covered outlet rim',(x,-.279,.30),.039,.013,p['steel'],'Y',32,.0015)
  cyl('Outlet recessed face',(x,-.288,.30),.032,.012,p['rubber'],'Y',32,.002)
  for xx,zz in [(x-.010,.305),(x+.010,.305)]:box('Socket opening',(xx,-.296,zz),(.005,.002,.013),p['iron'],.001)
  cyl('Socket earth opening',(x,-.296,.286),.0035,.003,p['iron'],'Y',12,.0002)
 box('Voltage gauge blank lens',(.07,-.282,.38),(.075,.008,.037),p['white'],.004)
 cyl('Engine cut-off switch',(.23,-.284,.382),.016,.013,p['red'],'Y',24,.002)
 for x in [.017,.283]:
  for z in [.237,.415]:screw('Control panel screw',(x,-.283,z),p['steel'],'Y',.0035)
 return('city-portable-generator','可搬式オープンフレーム発電機','Portable open-frame generator','工事区画や屋外作業場に置く汎用の小型発電機。保護フレーム、防振脚、燃料タンク、フィン付き原動機、発電部とコンセント付き操作面を造形。ケーブル、電力供給、燃料・排気の動作は含みません。','A generic compact generator for construction compounds and outdoor work areas. Models the roll cage, anti-vibration feet, fuel tank, finned engine, alternator and outlet control panel. Cables, power supply, fuel and exhaust simulation are not included.',['generator','power','construction','発電機'])

def compressor():
 p=pal()
 # Horizontal pressure receiver; tank shell, welded-looking rings and domed ends.
 cyl('Air receiver barrel',(0,0,.285),.18,.62,p['blue'],'X',64,.005)
 for x in [-.31,.31]:sphere('Domed receiver end',(x,0,.285),(.095,.18,.18),p['blue'],40,20)
 for x in [-.29,.29]:torus('Receiver weld seam',(x,0,.285),.179,.004,p['steel'],rotation=(0,math.pi/2,0),segments=48)
 for x in [.23]:
  rod('Wheel axle',(x,-.265,.12),(x,.265,.12),.018,p['steel'])
  for y in [-.248,.248]:
   cyl('Transport wheel',(x,y,.12),.12,.048,p['rubber'],'Y',40,.004)
   cyl('Wheel hub',(x,y*1.11,.12),.050,.012,p['iron'],'Y',32,.0015)
   cyl('Wheel axle cap',(x,y*1.14,.12),.016,.014,p['steel'],'Y',24,.001)
 for y in [-.11,.11]:
  box('Front ground leg',(-.27,y,.115),(.055,.055,.17),p['iron'],.006)
  box('Leg rubber pad',(-.27,y,.035),(.085,.075,.05),p['rubber'],.009)
 box('Motor pump platform',(0,0,.475),(.43,.24,.026),p['iron'],.007)
 # Electric motor and paired compressor cylinders are separate, exposed components.
 cyl('Electric motor barrel',(.12,0,.59),.095,.25,p['iron'],'X',40,.004)
 for x in [.03,.07,.11,.15,.19]:cyl('Motor cooling fin',(x,0,.59),.103,.008,p['steel'],'X',40,.001)
 cyl('Fan-end housing',(.26,0,.59),.106,.032,p['black'],'X',40,.003)
 for i in range(8):
  an=i*math.tau/8;o=box('Fan cover slot',(.279,.065*math.sin(an),.59+.065*math.cos(an)),(.003,.011,.033),p['iron'],.002);o.rotation_euler[0]=an
 box('Compressor crankcase',(-.13,0,.56),(.16,.18,.14),p['iron'],.018)
 for y in [-.063,.063]:
  for i in range(5):box('Pump cylinder cooling fin',(-.13,y,.65+i*.014),(.15,.105,.007),p['steel'],.0015)
  box('Pump cylinder head',(-.13,y,.725),(.15,.11,.034),p['black'],.004)
  for x in [-.185,-.075]:screw('Head screw',(x,y,.745),p['steel'],r=.004)
 tube('Receiver copper feed',[(-.18,.04,.74),(-.23,.12,.74),(-.28,.13,.68),(-.28,.13,.45)],.009,p['brass'],2)
 box('Pressure switch housing',(-.31,-.045,.54),(.10,.105,.09),p['black'],.009)
 cyl('Red power rocker',(-.31,-.045,.592),.017,.016,p['red'],verts=24,b=.003)
 rod('Air outlet manifold',(-.34,-.11,.53),(-.34,-.23,.53),.014,p['brass'],24)
 cyl('Pressure gauge rim',(-.34,-.17,.60),.034,.019,p['steel'],'Y',32,.0015)
 cyl('Pressure gauge blank face',(-.34,-.182,.60),.028,.005,p['white'],'Y',32,.001)
 bar('Gauge needle',(-.34,-.186,.60),(-.351,-.186,.616),.002,.002,p['black'])
 cyl('Air pressure regulator',(-.34,-.23,.56),.022,.046,p['black'],verts=24,b=.003)
 cyl('Quick outlet coupling',(-.34,-.254,.53),.018,.036,p['brass'],'Y',24,.0015)
 # Upward pull handle at the wheeled end, joined to two tank mounting ears.
 for y in [-.15,.15]:
  box('Handle tank ear',(.24,y,.40),(.065,.025,.10),p['iron'],.004)
  tube('Transport handle upright',[(.25,y,.40),(.38,y,.55),(.43,y,.78)],.017,p['black'],2)
 rod('Transport handle crossbar',(.43,-.15,.78),(.43,.15,.78),.020,p['rubber'],28)
 cyl('Drain valve',(-.03,0,.094),.012,.04,p['brass'],verts=20,b=.001)
 return('city-portable-air-compressor','タンク付き可搬式空気圧縮機','Portable receiver-tank air compressor','屋外の補修作業や管理庫向けの車輪付き空気圧縮機。横置き受気タンク、電動機、放熱フィン付き圧縮部、圧力計、調圧器、排水弁と運搬ハンドルを造形。ホース、圧縮空気、可動・電気機能はありません。','A wheeled air compressor for outdoor maintenance and service sheds. Includes a horizontal receiver tank, motor, finned pump, gauge, regulator, drain valve and transport handle. No hose, compressed air, electrical operation or moving mechanism is supplied.',['compressor','air','maintenance','圧縮機'])

BUILDERS=[compactor,rammer,generator,compressor]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-004/assets');p.add_argument('--only',default='');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/construction_machines.py',azimuth=-55,elevation=24)
