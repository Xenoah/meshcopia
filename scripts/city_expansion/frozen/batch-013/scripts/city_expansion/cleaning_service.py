"""Four original cleaning and maintenance props for Xenoah, CC BY 4.0.
Independent procedural construction, no third-party assets, marks or textures.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Brushed stainless fittings',(.36,.42,.44),.80,.36),black=mat('Dark powder coated steel',(.035,.045,.05),.35,.52),rubber=mat('Charcoal flexible rubber',(.014,.020,.021),0,.86),blue=mat('Deep blue molded polymer',(.035,.18,.30),.05,.43),white=mat('Ivory polymer',(.70,.73,.68),0,.48),red=mat('Red machine enamel',(.48,.045,.025),.25,.42),yellow=mat('Amber control insert',(.64,.35,.035),.1,.4),brass=mat('Brass couplings',(.44,.29,.09),.8,.4))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.002):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,d,m):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,.003);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def fastener(n,p,m,axis='Z',r=.006):
 cyl(n+' washer',p,r*1.5,r*.28,m,axis,20,.0003);q=list(p);q['XYZ'.index(axis)]+=(-1 if axis=='Y' else 1)*r*.4;cyl(n+' hex head',q,r,r*.70,m,axis,6,.0003)
def extrusion(n,profile,x,w,m,bevel=.004):
 vs=[(xx,y,z) for xx in [x-w/2,x+w/2] for y,z in profile];k=len(profile);fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,bevel)
def wheel(n,x,y,z,r,w,p,tread=False):
 cyl(n+' rubber',(x,y,z),r,w,p['rubber'],'X',40,.008)
 for s in [-1,1]:
  cyl(n+' hub',(x+s*w*.52,y,z),r*.48,.018,p['steel'],'X',28,.003)
  cyl(n+' axle cap',(x+s*w*.66,y,z),r*.18,.014,p['black'],'X',20,.002)
 if tread:
  for i in range(18):
   a=i*math.tau/18;o=box(n+' diagonal tread',(x,y+(r-.004)*math.sin(a),z+(r-.004)*math.cos(a)),(w*.92,.033,.023),p['rubber'],.004);o.rotation_euler[0]=-a

def hose_rings(n,points,r,m,rings=12):
 # Decorative corrugation is geometry; hose is fixed, closed and not deformable.
 tube(n,points,r,m,2)
 for i in range(1,len(points)-1):
  c=Vector(points[i]);t=Vector(points[i+1])-Vector(points[i-1]);o=torus(n+' corrugated ring',c,r*1.03,.004,m,segments=16);o.rotation_euler=t.to_track_quat('Z','Y').to_euler()

def floor_scrubber():
 p=palette()
 box('Machine underframe',(0,.0,.18),(.54,.77,.12),p['black'],.025)
 for x in [-.288,.288]:wheel('Traction wheel',x,.17,.15,.15,.07,p)
 cyl('Front disc brush carrier',(0,-.32,.092),.27,.09,p['black'],v=64,b=.012)
 cyl('Circular replaceable brush',(0,-.32,.042),.25,.046,p['rubber'],v=64,b=.003)
 for i in range(40):
  a=i*math.tau/40;rod('Brush perimeter tuft',(.246*math.cos(a),-.32+.246*math.sin(a),.020),(.25*math.cos(a),-.32+.25*math.sin(a),.055),.006,p['black'],10)
 extrusion('Molded solution tank',[(-.42,.29),(-.45,.60),(-.32,.84),(-.15,.94),(.25,.91),(.35,.73),(.30,.29)],0,.49,p['blue'],.035)
 extrusion('Recovery tank top lid',[(-.18,.941),(-.13,.985),(.22,.956),(.274,.914)],0,.47,p['white'],.012)
 cyl('Solution filling cap',(-.13,-.28,.875),.050,.025,p['black'],v=32,b=.004)
 for a in range(8):
  ang=a*math.tau/8;box('Fill cap grip',(-.13+.044*math.cos(ang),-.28+.044*math.sin(ang),.886),(.014,.015,.017),p['black'],.002)
 # Open handle frame, control console and rear waste-water hose.
 for x in [-.21,.21]:
  tube('Operator handle upright',[(x,.25,.55),(x,.49,.89),(x,.55,1.04)],.020,p['black'],3)
  rod('Handle grip',(x,.55,1.04),(x,.59,1.115),.028,p['rubber'],24)
 box('Control console',(0,.48,.96),(.35,.115,.08),p['black'],.014,rot=(math.radians(-25),0,0))
 box('Inert status screen',(-.07,.424,.985),(.105,.008,.044),p['blue'],.005)
 for x in [.05,.12]:cyl('Operator switch',(x,.42,.985),.018,.013,p['yellow'] if x>.1 else p['red'],'Y',24,.002)
 tube('Waste drain hose',[(.23,.30,.65),(.27,.39,.49),(.26,.43,.27),(.13,.46,.21)],.027,p['rubber'],3)
 cyl('Drain hose end cap',(.13,.46,.21),.034,.050,p['black'],'X',24,.003)
 # Curved rear squeegee follows the floor, not a rigid box blade.
 pts=[(.37*math.sin(a),.54+.10*math.cos(a),.047) for a in [(-1+i/16*2)*math.pi/2 for i in range(17)]]
 tube('Squeegee upper spine',[(x,y,z+.045) for x,y,z in pts],.020,p['steel'],2)
 for a,b in zip(pts,pts[1:]):bar('Segmented rubber squeegee lip',a,b,.014,.078,p['rubber'])
 for x in [-.25,.25]:
  bar('Squeegee arm',(x,.25,.18),(x,.60,.10),.025,.024,p['black']);cyl('Squeegee adjustment knob',(x,.61,.13),.025,.025,p['yellow'],v=24,b=.003)
 tube('Suction transfer hose',[(0,.63,.08),(0,.55,.20),(.08,.36,.45)],.030,p['rubber'],3)
 for x in [-.247,.247]:
  box('Tank latch',(x,.10,.84),(.016,.065,.09),p['black'],.004)
  for y in [-.21,.23]:fastener('Chassis fastener',(x,y,.27),p['steel'],'X')
 return ('city-walk-behind-floor-scrubber','歩行型の床洗浄機','Walk-behind floor scrubber','公共施設や店舗の床清掃シーン向けの歩行型洗浄機。円形ブラシ、成形タンク、操作ハンドル、実形状の湾曲スクイージー、排水・吸引ホースを備えます。液体、内部ポンプ、洗浄・吸引・走行はなく、衛生・電気安全や床適合性は未検証。','A walk-behind scrubber for public-building and retail floor-cleaning scenes, with a disc brush, molded tanks, operator handle, curved squeegee and fixed drain/suction hoses. No liquid, internal pump, scrubbing, suction or driving behavior is included; hygiene, electrical safety and floor compatibility are unvalidated.',['floor','scrubber','cleaning','洗浄機'])

def auger_ribbon(n,x0,x1,sign,p):
 vs=[];steps=44
 for i in range(steps+1):
  x=x0+(x1-x0)*i/steps;a=sign*i/steps*math.tau*1.25
  for r,d in [(.052,-.006),(.178,-.006),(.178,.006),(.052,.006)]:vs.append((x+d,-.10+r*math.cos(a),.246+r*math.sin(a)))
 fs=[(3,2,1,0),tuple(range(steps*4,steps*4+4))]
 for i in range(steps):
  for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
 return mesh(n,vs,fs,p['red'],0)

def snow_blower():
 p=palette()
 # Wide open-front auger bucket with curved rear wall and replaceable cutting edge.
 for x in [-.35,.35]:
  profile=[(-.31,.046),(.08,.046),(.20,.12),(.23,.25),(.18,.43),(.06,.49),(-.31,.49)]
  extrusion('Auger housing side cheek',profile,x,.025,p['red'],.007)
  box('Adjustable side skid',(x*1.07,-.15,.04),(.048,.32,.032),p['black'],.012)
  for y in [-.24,-.05]:fastener('Skid fastening',(x*1.08,y,.08),p['steel'],'X',.008)
 # Rear half-cylinder skin with true front opening.
 vs=[];fs=[];steps=24
 for x in [-.34,.34]:
  for radius in [.23,.246]:
   for i in range(steps+1):
    a=-math.pi/2+i/steps*math.pi;vs.append((x,-.10+radius*math.cos(a),.246+radius*math.sin(a)))
 k=steps+1
 for j in range(steps):
  fs.extend([(j,j+1,2*k+j+1,2*k+j),(k+j,3*k+j,3*k+j+1,k+j+1),(j,k+j,k+j+1,j+1),(2*k+j,2*k+j+1,3*k+j+1,3*k+j)])
 for j in [0,steps]:fs.append((j,2*k+j,3*k+j,k+j))
 mesh('Curved back of auger housing',vs,fs,p['red'])
 box('Replaceable scraper edge',(0,-.30,.046),(.715,.035,.023),p['steel'],.004)
 rod('Auger cross shaft',(-.38,-.10,.246),(.38,-.10,.246),.026,p['steel'],32)
 auger_ribbon('Left helical auger',-.31,-.035,1,p);auger_ribbon('Right helical auger',.31,.035,-1,p)
 for x in [-.35,.35]:cyl('Auger bearing cap',(x,-.10,.246),.052,.040,p['black'],'X',28,.003)
 box('Impeller drive gearbox',(0,.16,.255),(.16,.18,.18),p['black'],.017)
 box('Drive chassis',(0,.36,.22),(.49,.49,.13),p['black'],.015)
 for x in [-.30,.30]:wheel('Drive tire',x,.49,.195,.195,.105,p,True)
 # Compact engine envelope and controls; no working internals.
 box('Engine crankcase',(0,.35,.41),(.30,.32,.24),p['black'],.026)
 box('Fuel tank',(0,.36,.585),(.33,.29,.13),p['white'],.018)
 cyl('Fuel cap',(.08,.34,.67),.038,.030,p['black'],v=28,b=.003)
 cyl('Recoil starter housing',(.17,.34,.435),.11,.046,p['black'],'X',40,.008)
 for i in range(10):
  a=i*math.tau/10;rod('Starter vent spoke',(.198,.34+.058*math.sin(a),.435+.058*math.cos(a)),(.198,.34+.092*math.sin(a),.435+.092*math.cos(a)),.004,p['steel'],10)
 box('Muffler guard',(-.20,.40,.49),(.09,.18,.14),p['steel'],.008)
 for z in [.445,.475,.505,.535]:box('Muffler vent stripe',(-.249,.40,z),(.004,.13,.007),p['black'],.001)
 # Open rectangular discharge chute with a bent hood and a real empty mouth.
 cyl('Chute rotating collar',(0,.02,.49),.12,.065,p['black'],v=40,b=.004)
 for x in [-.093,.093]:extrusion('Chute sidewall',[(.10,.51),(.10,.83),(-.05,.98),(-.25,.98),(-.25,.85),(-.08,.79),(-.08,.51)],x,.015,p['red'],.004)
 box('Chute rear vertical',(0,.10,.68),(.19,.017,.34),p['red'],.004)
 box('Chute lower front wall',(0,-.08,.65),(.18,.017,.28),p['red'],.004)
 bar('Chute inner deflector floor',(0,-.08,.79),(0,-.25,.85),.18,.017,p['red'])
 bar('Chute curved hood',(0,.10,.83),(0,-.05,.98),.20,.016,p['red'])
 box('Chute top deflector',(0,-.15,.98),(.20,.21,.018),p['red'],.004)
 for x in [-.115,.115]:cyl('Chute deflector pivot',(x,-.065,.90),.025,.023,p['black'],'X',24,.003)
 for x in [-.235,.235]:
  tube('Operator handle',[(x,.48,.32),(x,.78,.83),(x,.89,1.04),(x,.99,1.04)],.018,p['black'],3)
  rod('Handle insulated grip',(x,.89,1.04),(x,1.0,1.04),.025,p['rubber'],24)
  rod('Control engagement lever',(x,.90,1.075),(x,.99,1.075),.008,p['red'],16)
 box('Operator control bridge',(0,.80,.90),(.47,.16,.05),p['black'],.008)
 rod('Chute direction crank',(.20,.75,.90),(.20,.16,.64),.007,p['steel'],16)
 tube('Clutch cable',[(-.20,.90,1.055),(-.18,.68,.78),(-.15,.52,.35)],.004,p['rubber'],1)
 return('city-two-stage-snow-blower','二段式の歩行型除雪機','Walk-behind two-stage snow blower','歩道や駐車場の保守シーン用の除雪機。前開きの曲面ハウジング、左右の螺旋オーガ、空洞の排雪筒、駆動輪、操作部を造形。雪、内部インペラ、燃料・エンジン内部、除雪・走行・可動は含まず、実機安全や性能を保証しません。','A snow-clearing prop for sidewalks and parking-area maintenance scenes. The open-front curved bucket exposes two helical augers, with an empty discharge chute, treaded drive wheels and operator controls. Snow, internal impeller, fuel and engine internals, snow-clearing, driving and articulation are absent; no real equipment safety or performance is warranted.',['snow','blower','winter','maintenance','除雪'])

def pressure_washer():
 p=palette()
 for x in [-.22,.22]:wheel('Transport wheel',x,.16,.125,.125,.060,p)
 rod('Continuous trolley wheel axle',(-.235,.16,.125),(.235,.16,.125),.012,p['steel'],24)
 for x in [-.15,.15]:box('Axle bearing support',(x,.16,.155),(.032,.060,.080),p['black'],.005)
 for x in [-.18,.18]:
  tube('Washer trolley side frame',[(x,-.20,.045),(x,-.25,.10),(x,-.23,.44),(x,.05,.82),(x,.14,.91)],.017,p['black'],3)
  cyl('Front rubber foot',(x,-.20,.025),.035,.045,p['rubber'],v=24,b=.004)
 rod('Top trolley handle',(-.18,.14,.91),(.18,.14,.91),.020,p['black'],24)
 rod('Top rubber grip',(-.10,.14,.91),(.10,.14,.91),.026,p['rubber'],24)
 box('Motor mounting deck',(0,-.005,.20),(.38,.42,.035),p['steel'],.009)
 cyl('Electric motor housing',(0,.01,.36),.105,.31,p['blue'],'Y',40,.008)
 for i in range(12):
  a=i*math.tau/12;bar('Motor cooling fin',(.107*math.cos(a),-.12,.36+.107*math.sin(a)),(.107*math.cos(a),.13,.36+.107*math.sin(a)),.012,.014,p['blue'])
 cyl('Motor fan cover',(0,.18,.36),.11,.045,p['black'],'Y',40,.005)
 for x in [-.06,-.03,0,.03,.06]:rod('Fan cover grille',(x,.205,.29),(x,.205,.43),.004,p['steel'],12)
 box('Pump manifold',(0,-.19,.33),(.23,.10,.13),p['brass'],.012)
 for x in [-.073,0,.073]:cyl('Pump chamber cap',(x,-.245,.33),.026,.018,p['brass'],'Y',6,.002)
 for x in [-.135,.135]:cyl('Water connector',(x,-.19,.33),.025,.065,p['brass'],'X',24,.002)
 box('Motor electrical switch',(0,.02,.482),(.11,.14,.047),p['black'],.008)
 box('On-off rocker',(0,-.02,.512),(.043,.040,.014),p['red'],.003)
 # Side holster holds the distinctive trigger gun and long lance.
 box('Trigger gun holster',(.19,-.045,.60),(.060,.085,.095),p['black'],.005)
 bar('Spray gun grip',(.22,-.04,.62),(.22,-.01,.77),.035,.060,p['black'])
 tube('Trigger guard',[(.22,-.075,.64),(.22,-.11,.66),(.22,-.11,.735),(.22,-.055,.76)],.008,p['black'],2)
 rod('Inert trigger',(.22,-.075,.68),(.22,-.08,.735),.006,p['yellow'],16)
 rod('Long spray lance',(.22,-.005,.77),(.22,.12,1.16),.009,p['steel'],20)
 rod('Lance nozzle sleeve',(.22,.105,1.115),(.22,.13,1.19),.018,p['black'],24)
 # Original fixed hose coil above the pump, not an alternate hose-reel asset.
 pts=[]
 for i in range(145):
  a=i/144*math.tau*3;pts.append((.145*math.cos(a),.02+i/144*.08,.62+.145*math.sin(a)))
 tube('Pressure hose three-turn coil',pts,.011,p['rubber'],2)
 rod('Coil support crossbar',(-.17,-.01,.72),(.17,-.01,.72),.012,p['black'],20)
 for x in [-.12,.12]:tube('Coil retention hook',[(x,-.01,.72),(x,.08,.72),(x,.12,.75),(x,.12,.78)],.008,p['black'],2)
 tube('Pressure hose pump lead',[pts[0],(.18,-.06,.50),(.16,-.17,.33)],.011,p['rubber'],2)
 tube('Pressure hose gun lead',[pts[-1],(.20,.14,.57),(.22,-.02,.64)],.011,p['rubber'],2)
 for x in [-.15,.15]:fastener('Deck fixing',(x,-.13,.221),p['black'])
 return('city-electric-pressure-washer','電動式の高圧洗浄機','Electric pressure washer trolley','公共施設の外壁や舗装清掃シーン向けの小型洗浄機。車輪付き管フレーム、フィン付き電動機、ポンプ外装、固定ホース巻き、トリガーガンと長いランスを備えます。給水・電源・噴流、内部機構、実際の圧力・洗浄・走行はなく、安全性は未検証。','A small pressure-washer trolley for public-building wall and paving cleaning scenes, with tubular frame, finned electric motor, pump exterior, fixed hose coil, trigger gun and long lance. Supply water, mains power, spray, working internals, pressure, cleaning and rolling behavior are absent; real equipment safety is unvalidated.',['pressure','washer','cleaning','maintenance','高圧洗浄'])

def wet_dry_vacuum():
 p=palette()
 for x in [-.17,.17]:
  for y in [-.17,.17]:
   cyl('Caster swivel',(x,y,.090),.022,.036,p['steel'],v=20,b=.002)
   for xx in [x-.022,x+.022]:box('Caster fork',(xx,y,.05),(.008,.047,.055),p['black'],.003)
   cyl('Caster tire',(x,y,.039),.039,.033,p['rubber'],'X',24,.002)
 box('Caster base platform',(0,0,.113),(.47,.47,.055),p['black'],.035)
 cyl('Stainless collection drum',(0,0,.34),.20,.40,p['steel'],v=64,b=.009)
 for z in [.152,.51]:torus('Rolled drum rim',(0,0,z),.20,.011,p['steel'],segments=48)
 cyl('Lid seal ring',(0,0,.548),.214,.036,p['black'],v=64,b=.006)
 cyl('Motor head',(0,0,.62),.181,.13,p['blue'],v=48,b=.023)
 cyl('Motor top cover',(0,0,.696),.151,.034,p['black'],v=48,b=.011)
 for x in [-.083,.083]:bar('Carrying handle stanchion',(x,0,.71),(x,0,.777),.020,.035,p['black'])
 rod('Carrying handle',(-.083,0,.777),(.083,0,.777),.020,p['black'],24)
 for x in [-.213,.213]:
  box('Drum toggle latch',(x,0,.50),(.025,.052,.13),p['black'],.005)
  cyl('Latch hinge',(x,0,.54),.009,.069,p['steel'],'Y',20,.001)
  rod('Latch catch',(x,-.016,.45),(x,-.016,.50),.004,p['steel'],12)
 cyl('Front hose inlet',(0,-.20,.44),.043,.057,p['black'],'Y',32,.004)
 cyl('Drain cap',(0,-.202,.20),.026,.027,p['black'],'Y',24,.003)
 for i in range(12):
  a=i*math.tau/12;box('Motor exhaust slot',(.1815*math.cos(a),.1815*math.sin(a),.625),(.004,.027,.037),p['black'],.001,rot=(0,0,a))
 box('Top power switch',(.08,-.09,.72),(.036,.047,.012),p['red'],.003)
 # Curved suction hose and parked wand create an unmistakable vacuum silhouette.
 pts=[]
 controls=[(0,-.235,.44),(-.10,-.35,.43),(-.30,-.36,.38),(-.40,-.25,.25),(-.39,.02,.18),(-.31,.24,.30),(-.27,.25,.62)]
 for i in range(len(controls)-1):
  a,b,c,d=[Vector(controls[max(0,min(len(controls)-1,k))]) for k in [i-1,i,i+1,i+2]]
  for j in range(5):
   t=j/5;pts.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
 pts.append(controls[-1]);hose_rings('Fixed corrugated suction hose',pts,.025,p['rubber'])
 rod('Steel cleaning wand',(-.27,.25,.62),(-.27,.42,.11),.017,p['steel'],28)
 rod('Wand hand grip',(-.27,.25,.62),(-.27,.28,.53),.026,p['black'],28)
 cyl('Wand floor-head coupling',(-.27,.42,.095),.022,.055,p['black'],v=24,b=.003)
 box('Floor suction head',(-.27,.44,.055),(.30,.105,.065),p['black'],.012)
 box('Floor nozzle lower lip',(-.27,.42,.023),(.276,.075,.019),p['rubber'],.004)
 # Rear winding hooks and fixed power cable are included without a connected supply.
 for z in [.31,.48]:box('Cable winding hook',(0,.21,z),(.10,.05,.035),p['black'],.007)
 for i in range(3):
  y=.239+i*.009;tube('Parked power cable',[(-.07,y,.30),(-.09,y,.32),(-.09,y,.48),(-.07,y,.50),(.07,y,.50),(.09,y,.48),(.09,y,.32),(.07,y,.30)],.004,p['rubber'],1)
 box('Generic disconnected plug',(.11,.24,.37),(.032,.035,.06),p['black'],.005)
 return('city-wet-dry-vacuum','湿乾両用の業務用掃除機','Commercial wet/dry vacuum','建物や作業場の清掃シーン向けの湿乾両用集じん機。金属タンク、キャスター、蓋留め、上部モーター外装、蛇腹ホース、金属パイプ、床用ノズルと背面コードを造形。液体や粉じん、フィルター・電動機内部、吸引・通電・走行はなく、集じん性能や安全認証は未検証。','A wet/dry vacuum prop for building and workshop cleaning scenes, with metal drum, casters, lid latches, motor-head exterior, corrugated hose, steel wand, floor nozzle and rear cable. Liquids, dust, filters and motor internals, suction, powered and rolling behavior are absent; collection performance and safety certification are unvalidated.',['vacuum','cleaning','wet-dry','maintenance','掃除機'])

BUILDERS=[floor_scrubber,snow_blower,pressure_washer,wet_dry_vacuum]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-013/assets');p.add_argument('--only',default='');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/cleaning_service.py',azimuth=-55,elevation=24)
