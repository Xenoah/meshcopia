"""Four original public-facility fitness appearance props. Xenoah, CC BY 4.0.
Static scene assets, not exercise guidance or real certified equipment designs.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Satin tubular steel',(.36,.43,.46),.72,.38),blue=mat('Muted blue enamel',(.055,.18,.26),.25,.45),black=mat('Dark molded body',(.025,.035,.04),.1,.60),rubber=mat('Matte rubber and pads',(.012,.018,.022),0,.85),grey=mat('Grey belt and textured-look pad',(.12,.15,.17),0,.76),glass=mat('Opaque inactive display',(.015,.065,.085),.3,.25),red=mat('Red control accents',(.48,.035,.020),.1,.48),white=mat('Neutral control keys',(.67,.72,.72),.1,.45))
def cyl(n,p,r,d,m,axis='Z',v=28,b=.0015):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.0015,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,d,m,bev=.004):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(n,p,r,t,m,axis='Z',seg=32):return torus(n,p,r,t,m,rotation=(0,math.pi/2,0) if axis=='X' else ((math.pi/2,0,0) if axis=='Y' else None),segments=seg)
def screw(n,p,m,axis='Z',r=.006):
 cyl(n+' washer',p,r*1.5,.0025,m,axis,12,0);q=list(p);q['XYZ'.index(axis)]+=.003;cyl(n+' head',q,r,.006,m,axis,6,0)
def extrusion(n,outline,x,width,m,bev=.008):
 vs=[(xx,y,z) for xx in [x-width/2,x+width/2] for y,z in outline];k=len(outline);fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,bev)
def foot(n,x,y,p,w=.15):box(n,(x,y,.027),(w,.12,.054),p['rubber'],.012)
def screen(n,loc,size,p,rot=(math.radians(18),0,0)):
 box(n+' enclosure',loc,size,p['black'],.018,rot=rot)
 # Face is a shallow raised blank panel, no branding or fictional performance data.
 x,y,z=loc;box(n+' inactive face',(x,y+.046,z+.012),(size[0]*.62,.012,size[2]*.55),p['glass'],.006,rot=rot)

def stationary_bike():
 p=palette()
 for y in [-.43,.45]:
  rod('Bike stabilizer footbar',(-.30,y,.09),(.30,y,.09),.035,p['steel'],28)
  for x in [-.30,.30]:foot('Bike leveling foot',x,y,p)
 bar('Stationary bike main base',(0,-.47,.12),(0,.46,.12),.095,.10,p['blue'],.015)
 bar('Bike diagonal main tube',(0,.28,.15),(0,-.14,.60),.080,.075,p['blue'],.012)
 bar('Seat mast lower',(0,.27,.15),(0,.16,.69),.068,.068,p['blue'],.010)
 bar('Seat height post',(0,.16,.61),(0,.12,.92),.045,.045,p['steel'],.005)
 box('Seat clamp sleeve',(0,.145,.74),(.082,.085,.065),p['black'],.008)
 cyl('Seat height knob',(.062,.145,.74),.029,.032,p['red'],'X',24,.003)
 box('Saddle adjustment carriage',(0,.10,.930),(.13,.22,.050),p['steel'],.004)
 extrusion('Padded exercise saddle',[(-.08,.95),(-.10,.986),(-.02,1.005),(.19,1.005),(.25,.980),(.23,.950)],0,.265,p['rubber'],.023)
 # Front flywheel sits inside a narrow circular guard, not a rolling vehicle wheel.
 cyl('Flywheel outer housing',(0,-.22,.36),.244,.115,p['blue'],'X',48,.012)
 for s in [-1,1]:
  cyl('Flywheel side inset',(s*.060,-.22,.36),.198,.010,p['black'],'X',40,.003)
  ring('Flywheel trim ring',(s*.068,-.22,.36),.198,.006,p['steel'],'X',40)
  for yy,zz in [(-.22,.36),(-.22,.49)]:screw('Housing fastening',(s*.077,yy,zz),p['steel'],'X')
 cyl('Pedal crank axle',(0,.045,.36),.035,.21,p['steel'],'X',28,.003)
 for side,dy,dz in [(-1,-.12,-.09),(1,.12,.09)]:
  x=side*.112;bar('Pedal crank arm',(x,.045,.36),(x,.045+dy,.36+dz),.024,.032,p['steel'],.003)
  box('Exercise pedal',(side*.18,.045+dy,.36+dz),(.16,.10,.028),p['black'],.006)
  tube('Fixed pedal foot strap',[(side*.13,.005+dy,.37+dz),(side*.13,.005+dy,.42+dz),(side*.23,.005+dy,.42+dz),(side*.23,.005+dy,.37+dz)],.007,p['rubber'],1)
 bar('Front control mast',(0,-.38,.13),(0,-.42,1.08),.055,.055,p['steel'],.007)
 tube('Continuous exercise bike handlebar',[(-.17,-.22,1.27),(-.17,-.37,1.23),(-.17,-.42,1.08),(.17,-.42,1.08),(.17,-.37,1.23),(.17,-.22,1.27)],.020,p['black'],2)
 for x in [-.17,.17]:rod('Handlebar grip',(x,-.32,1.245),(x,-.19,1.28),.025,p['rubber'],24)
 screen('Bike console',(0,-.43,1.20),(.21,.09,.15),p)
 for x in [-.06,0,.06]:box('Bike console key',(x,-.367,1.151),(.026,.009,.014),p['red'] if x==0 else p['white'],.002)
 return ('city-stationary-exercise-bike','据置式エクササイズバイク','Stationary exercise bicycle','公共スポーツ施設やホテルジム向けの据置自転車型運動器具。固定足、フレーム、円形フライホイール外装、左右クランク・ペダルと固定ストラップ、座面調整外装、ハンドル・無表示コンソールを造形。移動用自転車とは異なる固定器具です。車輪走行、ペダル回転、負荷制御・運動計測はなく、安全・身体適合性や実機性能は未検証。','A stationary bicycle-form exercise prop for civic sports facilities and hotel gyms, with stabilizer feet, frame, circular flywheel housing, opposed cranks/pedals and fixed straps, saddle-adjustment exterior, handlebars and inactive console. It is fixed exercise equipment rather than a commuter bicycle. Rolling, pedaling, resistance control and exercise measurement are absent; safety, body fit and equipment performance are unvalidated.',['fitness','bike','gym','エクササイズバイク'])

def rowing_machine():
 p=palette()
 # Long seat rail and a fixed sliding-seat carriage make the rowing mechanism distinct.
 box('Rowing seat rail',(0,.35,.31),(.12,1.86,.095),p['steel'],.008)
 for y in [-.60,1.14]:
  rod('Rowing transverse foot',(-.31,y,.075),(.31,y,.075),.030,p['blue'],24)
  for x in [-.31,.31]:foot('Rowing contact shoe',x,y,p)
  bar('Seat rail support',(0,y,.09),(0,y,.29),.075,.065,p['blue'],.006)
 box('Seat roller carriage',(0,.54,.375),(.24,.23,.048),p['black'],.007)
 for x in [-.073,.073]:
  for y in [.47,.61]:cyl('Seat guide roller',(x,y,.35),.029,.028,p['rubber'],'X',20,.002)
 box('Rowing seat pad',(0,.54,.422),(.34,.25,.064),p['rubber'],.027)
 # Fan housing with a real open ring grille and central axle.
 cyl('Rowing fan body',(0,-.71,.40),.285,.17,p['blue'],'X',48,.009)
 for s in [-1,1]:
  cyl('Fan recessed side',(s*.088,-.71,.40),.240,.010,p['black'],'X',40,.002)
  for rad in [.08,.145,.212,.266]:ring('Fan grille concentric ring',(s*.102,-.71,.40),rad,.004,p['steel'],'X',40)
  for i in range(12):
   a=i*math.tau/12;rod('Fan grille radial spoke',(s*.102,-.71+.04*math.sin(a),.40+.04*math.cos(a)),(s*.102,-.71+.263*math.sin(a),.40+.263*math.cos(a)),.003,p['steel'],10)
  cyl('Fan central hub',(s*.11,-.71,.40),.042,.020,p['steel'],'X',24,.002)
 # Angled foot cradles with heel stops and fixed retaining straps.
 for side in [-1,1]:
  x=side*.19;o=box('Rowing foot plate',(x,-.29,.32),(.16,.31,.030),p['black'],.008,rot=(math.radians(45),0,0))
  box('Heel cup bottom',(x,-.181,.23),(.18,.065,.045),p['rubber'],.008,rot=(math.radians(45),0,0))
  rod('Foot plate support',(side*.065,-.33,.30),(x,-.33,.30),.021,p['steel'],20)
  tube('Fixed rowing foot strap',[(x-.085,-.30,.37),(x-.085,-.335,.425),(x+.085,-.335,.425),(x+.085,-.30,.37)],.009,p['rubber'],1)
 rod('Handle parking crossbar',(-.27,-.44,.58),(.27,-.44,.58),.022,p['black'],24)
 for x in [-.20,.20]:bar('Handle storage support',(x,-.42,.29),(x,-.44,.58),.025,.025,p['blue'])
 for x in [-.20,.20]:rod('Rowing handle grip',(x-.055,-.44,.58),(x+.055,-.44,.58),.027,p['rubber'],24)
 tube('Fixed rowing pull cord',[(0,-.51,.58),(0,-.60,.58),(0,-.73,.50)],.006,p['black'],1)
 rod('Monitor stem',(0,-.74,.66),(0,-.63,1.02),.018,p['steel'],24)
 screen('Rowing monitor',(0,-.62,1.06),(.19,.07,.14),p,rot=(math.radians(12),0,0))
 return ('city-rowing-ergometer','ローイングエルゴメーター','Rowing ergometer','体育施設やジムの内装向けのローイング器具。長いシートレールと固定したローラー台、ファン形の外装・開いた格子、角度付き足台と固定ストラップ、保管位置の引き棒・コード、無表示モニターを造形。ファン内部の駆動、座面移動、引き動作や負荷・運動計測は含みません。安全・身体適合性や実機性能は未検証。','A rowing-machine prop for sports-center and gym interiors, with long seat rail and fixed roller carriage, fan-shaped housing and open grille, angled foot cradles with fixed straps, parked pull handle/cord and inactive monitor. Internal fan drive, seat travel, rowing motion, resistance and exercise measurement are absent. Safety, body fit and equipment performance are unvalidated.',['fitness','rowing','ergometer','gym','ローイング'])

def treadmill():
 p=palette()
 box('Treadmill lower frame',(0,0,.12),(.82,1.93,.18),p['black'],.035)
 for x in [-.34,.34]:
  for y in [-.70,.72]:foot('Treadmill floor pad',x,y,p,.17)
 box('Static treadmill belt',(0,.03,.222),(.57,1.63,.025),p['rubber'],.010)
 for x in [-.345,.345]:
  box('Treadmill side step rail',(x,.03,.235),(.112,1.69,.070),p['blue'],.012)
  for y in [-.56,-.35,-.14,.07,.28,.49,.70]:box('Side rail traction strip',(x,y,.273),(.080,.018,.005),p['grey'],.001)
 cyl('Rear belt roller',(0,.87,.208),.052,.66,p['steel'],'X',36,.003)
 for x in [-.36,.36]:
  box('Rear roller cap',(x,.87,.21),(.11,.14,.11),p['black'],.017)
  screw('Belt tension adjuster',(x,.947,.21),p['steel'],'Y',.010)
 box('Front motor cover',(0,-.79,.31),(.70,.36,.17),p['blue'],.030)
 for i in range(9):box('Motor cover raised vent slat',(-.24+i*.06,-.78,.401),(.025,.16,.010),p['black'],.003)
 for x in [-.35,.35]:
  bar('Treadmill console upright',(x,-.60,.20),(x,-.61,1.25),.062,.068,p['steel'],.009)
  tube('Treadmill handrail',[(x,-.60,1.10),(x,-.28,1.09),(x,.20,1.02)],.028,p['black'],2)
  rod('Treadmill grip zone',(x,-.18,1.075),(x,.18,1.025),.032,p['rubber'],24)
 box('Treadmill full console',(0,-.60,1.28),(.84,.21,.20),p['black'],.025,rot=(math.radians(24),0,0))
 box('Treadmill opaque display',(0,-.488,1.316),(.30,.014,.115),p['glass'],.006,rot=(math.radians(24),0,0))
 for x in [-.28,.28]:
  cyl('Recessed-looking bottle well',(x,-.62,1.39),.052,.010,p['rubber'],v=28,b=.002)
  ring('Bottle holder rim',(x,-.62,1.405),.052,.008,p['black'],seg=28)
 for x in [-.10,-.05,0,.05,.10]:box('Treadmill console button',(x,-.455,1.234),(.025,.012,.016),p['red'] if x==0 else p['white'],.003)
 box('Emergency key exterior',(0,-.445,1.20),(.044,.025,.024),p['red'],.004)
 tube('Short fixed key tether',[(0,-.438,1.19),(.06,-.42,1.10),(.10,-.44,1.16)],.003,p['black'],1)
 box('Rear console access panel',(0,-.714,1.28),(.34,.015,.11),p['blue'],.005)
 for x in [-.14,.14]:screw('Console panel screw',(x,-.725,1.28),p['steel'],'Y',.005)
 return ('city-fitness-treadmill','フィットネス用ランニングマシン','Fitness treadmill','体育施設・ホテルジム向けのランニングマシン外観。固定した走行ベルト、側部ステップと滑り止め条、後ローラーと調整ねじ、モーターカバー、手すり、無表示コンソール・キー外装を造形。ベルト移動・走行・傾斜制御・緊急停止や運動計測は実装していません。安全・身体適合性や実機性能は未検証。','A treadmill exterior for civic fitness facilities and hotel gyms, with static belt, side steps and traction strips, rear roller/adjusters, motor cover, handrails, inactive console and key exterior. Belt travel, running, incline control, emergency-stop behavior and exercise measurement are not implemented. Safety, body fit and equipment performance are unvalidated.',['fitness','treadmill','gym','ランニングマシン'])

def lat_station():
 p=palette()
 # Freestanding weight-stack station with real guide rods and a fixed cable path.
 for x in [-.39,.39]:
  bar('Weight machine base rail',(x,-.56,.075),(x,.48,.075),.075,.065,p['blue'],.010)
  for y in [-.56,.48]:foot('Weight machine floor pad',x,y,p,.18)
 for y in [-.45,.39]:bar('Machine base crossmember',(-.39,y,.11),(.39,y,.11),.065,.070,p['steel'],.007)
 bar('Machine central seat spine',(0,-.45,.11),(0,.39,.11),.065,.070,p['steel'],.007)
 for x in [-.29,.29]:bar('Tall stack frame',(x,.35,.12),(x,.35,2.15),.065,.065,p['blue'],.009)
 bar('Top overhead crossframe',(-.29,.35,2.15),(.29,.35,2.15),.065,.075,p['blue'],.008)
 bar('Guide rod upper brace',(-.29,.35,1.96),(.29,.35,1.96),.040,.050,p['steel'],.005)
 box('Weight stack plinth',(0,.35,.175),(.43,.27,.070),p['blue'],.008)
 for x in [-.12,.12]:cyl('Stack rest bumper',(x,.35,.213),.035,.025,p['rubber'],v=20,b=.002)
 for x in [-.12,.12]:rod('Weight stack guide rod',(x,.35,.12),(x,.35,1.94),.016,p['steel'],24)
 for i in range(13):box('Individual fixed weight plate',(0,.35,.24+i*.052),(.39,.25,.044),p['black'],.007)
 box('Weight stack selector spine',(0,.211,.54),(.035,.018,.66),p['steel'],.002)
 for i in range(12):cyl('Selector socket exterior',(0,.197,.25+i*.052),.006,.005,p['black'],'Y',12,0)
 rod('Fixed selector pin',(0,.195,.51),(0,.13,.51),.006,p['steel'],16)
 cyl('Selector pin grip',(0,.108,.51),.019,.034,p['red'],'Y',20,.003)
 box('Rear stack protective plate',(0,.505,1.05),(.53,.018,1.70),p['blue'],.008)
 for x in [-.29,.29]:
  for z in [.26,1.83]:bar('Rear guard stand-off',(x,.35,z),(x,.50,z),.025,.025,p['steel'])
 # Overhead beam projects forward to the pulldown handle.
 bar('Overhead forward beam',(0,.35,2.14),(0,-.48,2.14),.075,.065,p['blue'],.009)
 for y in [.31,-.43]:
  cyl('Cable pulley wheel',(0,y,2.13),.066,.030,p['black'],'X',32,.003)
  ring('Pulley visible groove',(0,y,2.13),.057,.004,p['steel'],'X',32)
  for x in [-.045,.045]:box('Pulley fork cheek',(x,y,2.13),(.015,.14,.15),p['steel'],.005)
  rod('Pulley axle',(-.063,y,2.13),(.063,y,2.13),.012,p['steel'],20)
 rod('Stack cable attachment stem',(0,.35,.886),(0,.376,.94),.012,p['steel'],20)
 cable=[(0,.376,.94),(0,.376,2.13)]
 for i in range(1,13):
  a=i/12*math.pi/2;cable.append((0,.31+.066*math.cos(a),2.13+.066*math.sin(a)))
 cable.append((0,-.43,2.196))
 for i in range(1,13):
  a=math.pi/2+i/12*math.pi/2;cable.append((0,-.43+.066*math.cos(a),2.13+.066*math.sin(a)))
 cable.append((0,-.496,1.823));tube('Fixed weight-stack cable',cable,.006,p['black'],1)
 ring('Lat handle connection',(0,-.496,1.80),.023,.005,p['steel'],'Y',24)
 tube('Curved pulldown bar',[(-.55,-.496,1.69),(-.40,-.496,1.76),(-.24,-.496,1.78),(0,-.496,1.78),(.24,-.496,1.78),(.40,-.496,1.76),(.55,-.496,1.69)],.017,p['steel'],2)
 for s in [-1,1]:rod('Lat bar rubber grip',(s*.40,-.496,1.76),(s*.56,-.496,1.685),.023,p['rubber'],24)
 bar('Seat support post',(0,-.24,.12),(0,-.24,.48),.065,.065,p['steel'],.007)
 box('Lat station seat',(0,-.27,.51),(.38,.39,.075),p['rubber'],.023)
 bar('Thigh pad support',(0,-.08,.14),(0,-.08,.70),.045,.045,p['steel'],.005)
 rod('Thigh pad axle',(-.23,-.08,.71),(.23,-.08,.71),.021,p['steel'],24)
 for x in [-.13,.13]:cyl('Thigh restraint pad',(x,-.08,.71),.072,.20,p['rubber'],'X',32,.013)
 return ('city-lat-pulldown-station','ラットプルダウン用ウェイト器具','Lat pulldown weight station','体育施設やジム内装向けの固定ウェイト器具。支柱・支持脚、十三枚の固定ウェイト板、ガイド棒、選択ピン外装、背面保護板、滑車と固定ケーブル、広い引き棒、座面・腿当てを造形。ウェイトやケーブルは動かず、実際の負荷や運動方法を示すものではありません。安全・身体適合性・耐荷重や実機性能は未検証。','A fixed-weight station prop for civic sports facilities and gyms, with frame/feet, thirteen static plates, guide rods, selector-pin exterior, rear guard, pulleys/fixed cable, wide pulldown bar, seat and thigh pads. Weights and cable do not move, and no actual resistance values or exercise instructions are supplied. Safety, body fit, load capacity and equipment performance are unvalidated.',['fitness','weights','pulldown','gym','ウェイト器具'])
BUILDERS=[stationary_bike,rowing_machine,treadmill,lat_station]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-026/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/fitness_equipment.py',azimuth=(125 if s[0]=='city-fitness-treadmill' else -55),elevation=24)
