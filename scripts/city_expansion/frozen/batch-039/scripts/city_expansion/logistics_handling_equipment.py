"""Original logistics-area equipment. Xenoah, CC BY 4.0.
Static whole assemblies, no brands, controls, load ratings or weighing simulation.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(steel=mat('Satin galvanized support metal',(.48,.53,.56),.75,.34),bright=mat('Bright roller and hardware metal',(.64,.68,.70),.82,.29),paint=mat('Industrial muted blue finish',(.055,.19,.30),.18,.41),dark=mat('Dark steel fittings',(.055,.071,.085),.45,.48),rubber=mat('Dark wheel and foot rubber',(.019,.026,.030),0,.76),yellow=mat('Muted warm safety accent',(.69,.39,.055),.04,.49),film=mat('Opaque pale wound film appearance',(.70,.75,.71),0,.34),core=mat('Plain cardboard roll core',(.34,.23,.12),0,.70),screen=mat('Blank inactive indicator panel',(.033,.082,.087),.02,.36),red=mat('Unlit stop-button accent',(.43,.035,.026),0,.44))
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
def frame(n,w,h,t,d,p,m,plane='XZ',bev=.002):
 vs=[]
 for ww,hh,z in [(w,h,-d/2),(w,h,d/2),(w-2*t,h-2*t,d/2),(w-2*t,h-2*t,-d/2)]:vs.extend([(-ww/2,-hh/2,z),(ww/2,-hh/2,z),(ww/2,hh/2,z),(-ww/2,hh/2,z)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)];o=mesh(n,vs,fs,m,bev);o.location=p
 if plane=='XZ':o.rotation_euler[0]=math.pi/2
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 return o
def wheel_caster(p,x,y,r=.067):
 z=r+.004
 cyl('Caster tire',(x,y,z),r,.042,p['rubber'],'X',v=32,b=.004)
 for side in [-1,1]:
  cyl('Caster wheel hub',(x+side*.025,y,z),r*.54,.008,p['steel'],'X',v=24,b=.001)
  box('Caster fork cheek',(x+side*.031,y+.010,z+.029),(.012,.073,.075),p['steel'],.004)
  cyl('Caster axle end',(x+side*.040,y,z),.009,.010,p['dark'],'X',v=12,b=.001)
 box('Caster fork top bridge',(x,y+.014,z+.073),(.075,.074,.017),p['steel'],.003)
 cyl('Caster swivel bearing',(x,y+.015,z+.091),.037,.021,p['dark'],v=24,b=.001)
 box('Caster deck mounting plate',(x,y+.015,z+.109),(.091,.095,.014),p['steel'],.003)
 return z+.116

def gravity_conveyor():
 p=pal();slope=.028
 def z(x):return .771+x*slope
 # Slightly declining fixed bed, individual free-roller exteriors, no motor.
 for y in [-.313,.313]:
  bar('Long conveyor side channel',(-1.040,y,z(-1.040)-.034),(1.040,y,z(1.040)-.034),.088,.035,p['paint'],.004)
  bar('Upper channel edge lip',(-1.040,y,z(-1.040)+.012),(1.040,y,z(1.040)+.012),.014,.045,p['paint'],.002)
 for i in range(29):
  x=-.974+i*.0696
  cyl('Individual conveyor roller',(x,0,z(x)),.030,.575,p['bright'],'Y',v=28,b=.002)
  cyl('Through roller axle',(x,0,z(x)),.008,.666,p['dark'],'Y',v=16,b=.001)
  for y in [-.338,.338]:cyl('Roller axle retaining nut',(x,y,z(x)),.011,.008,p['steel'],'Y',v=6,b=.001)
 for x in [-.788,.788]:
  top=z(x)-.050
  for y in [-.279,.279]:
   box('Conveyor square support leg',(x,y,(top+.060)/2),(.044,.044,top-.060),p['paint'],.004)
   cyl('Conveyor foot adjuster',(x,y,.056),.013,.066,p['steel'],v=20,b=.001)
   cyl('Conveyor round floor foot',(x,y,.025),.041,.038,p['rubber'],v=24,b=.003)
   box('Leg upper fastening plate',(x,y,top-.016),(.103,.060,.052),p['dark'],.004)
  bar('Conveyor support crossbar',(x,-.279,.253),(x,.279,.253),.033,.034,p['paint'],.003)
 for y in [-.279,.279]:
  bar('Conveyor long diagonal brace',(-.778,y,.273),(.778,y,.665),.023,.022,p['steel'],.002)
 for x in [-1.019,1.019]:box('Conveyor end cross tie',(x,0,z(x)-.065),(.030,.606,.032),p['paint'],.003)
 # Low end has a fixed stop; raised high-end lips receive an optional next module.
 box('Fixed low-end parcel stop',(-1.040,0,z(-1.040)+.035),(.024,.634,.091),p['yellow'],.004)
 for y in [-.313,.313]:frame('High-end joining tab',.068,.080,.020,.013,(1.080,y,z(1.040)-.029),p['steel'],'XZ')
 return ('city-gravity-roller-conveyor','重力式ローラーコンベヤ','Gravity roller conveyor','荷さばき場・小さな倉庫で箱の搬送経路を示すローラーコンベヤ。少し傾いた固定ベッドに29本の個別ローラー、軸端、側部チャンネル、四脚・高さ調整足・斜め補強、低い側の荷止めと端部連結金具を造形。箱や隣接モジュールは含まず、一台として配置します。ローラー回転・荷物の移動や耐荷重検証はありません。','A gravity-roller conveyor for parcel routes in loading areas and small warehouses. A slightly inclined fixed bed carries 29 separate rollers and axle ends, side channels, four legs with adjustable-looking feet, diagonal bracing, low-end stop and joining tabs. Boxes and neighboring modules are absent; place it as one complete machine. Roller rotation, parcel movement and load-rating validation are not provided.',['warehouse','conveyor','logistics','ローラーコンベヤ'])

def pallet_wrapper():
 p=pal()
 box('Wrapper continuous base frame',(0,.145,.062),(1.590,2.045,.100),p['paint'],.017)
 for x in [-.664,.664]:
  for y in [-.706,.938]:box('Wrapper floor isolation pad',(x,y,.017),(.154,.154,.026),p['rubber'],.007)
 cyl('Turntable lower bearing housing',(0,-.225,.119),.664,.075,p['dark'],v=64,b=.008)
 cyl('Circular pallet turntable',(0,-.225,.168),.737,.044,p['steel'],v=80,b=.006)
 ring('Turntable outer protective edge',(0,-.225,.166),.734,.008,p['yellow'],v=80)
 cyl('Turntable central hub plate',(0,-.225,.195),.101,.010,p['dark'],v=32,b=.002)
 for i in range(6):
  a=i*math.tau/6;cyl('Turntable hub fixing bolt',(.070*math.cos(a),-.225+.070*math.sin(a),.203),.007,.006,p['steel'],v=6,b=.0007)
 box('Vertical film carriage mast',(0,1.013,1.250),(.294,.312,2.318),p['paint'],.012)
 box('Mast foot mounting shoe',(0,1.013,.154),(.464,.421,.120),p['dark'],.007)
 for x in [-.178,.178]:
  for y in [.867,1.159]:cyl('Mast shoe bolt',(x,y,.221),.016,.015,p['steel'],v=6,b=.001)
 for x in [-.106,.106]:rod('Mast carriage guide rail',(x,.840,.315),(x,.840,2.233),.012,p['bright'],24)
 box('Mast upper chain guard',(0,.832,2.274),(.240,.059,.128),p['dark'],.006)
 box('Film carriage backing',(0,.810,.994),(.312,.049,.684),p['dark'],.006)
 for z in [.673,1.315]:
  box('Film-roll spindle support',(0,.699,z),(.281,.247,.027),p['steel'],.004)
  for x in [-.105,.105]:cyl('Film carriage guide block',(x,.839,z),.028,.065,p['dark'],v=24,b=.002)
 sleeve('Open wound-film core',(0,.638,.994),.033,.020,.624,p['core'],v=32)
 sleeve('Opaque wound stretch-film roll',(0,.638,.994),.103,.034,.523,p['film'],v=48)
 for z in [.721,1.267]:cyl('Roll spindle support collar',(0,.638,z),.045,.021,p['bright'],v=28,b=.001)
 cyl('Film-roll top adjustment knob',(0,.638,1.348),.033,.042,p['rubber'],v=28,b=.003)
 for z in [.770,1.210]:rod('Film carriage small roller axle',(.155,.690,z),(.155,.550,z),.009,p['steel'],16)
 cyl('Film carriage guide roller',(.155,.620,.990),.022,.470,p['dark'],v=24,b=.001)
 box('Rear mast drive housing',(0,1.247,.340),(.355,.188,.330),p['dark'],.013)
 for z in [.240+i*.033 for i in range(6)]:box('Drive housing rear vent',(0,1.348,z),(.231,.009,.011),p['steel'],.002)
 # Small control box is bolted directly to the mast, not floating beside it.
 box('Control cabinet bracket',(.195,1.017,1.506),(.128,.118,.120),p['steel'],.004)
 box('Wrapper side control cabinet',(.304,.965,1.535),(.160,.218,.332),p['paint'],.010)
 box('Blank wrapper display',(.304,.850,1.601),(.113,.013,.080),p['screen'],.003)
 cyl('Fixed stop-button collar',(.304,.849,1.467),.029,.013,p['yellow'],'Y',v=24,b=.002)
 cyl('Fixed unlit stop button',(.304,.836,1.467),.021,.021,p['red'],'Y',v=24,b=.003)
 # A compact approach wedge joins the low circular platform; not a safety-rated ramp.
 vs=[(-.430,-1.267,.010),(.430,-1.267,.010),(.430,-.824,.010),(-.430,-.824,.010),(-.430,-1.267,.020),(.430,-1.267,.020),(.430,-.824,.174),(-.430,-.824,.174)];fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];mesh('Short fixed turntable approach wedge',vs,fs,p['steel'],.003)
 return ('city-pallet-stretch-wrapper','パレット用ストレッチ包装機','Pallet stretch wrapping machine','倉庫の出荷区画でパレット包装位置を示す回転台式包装機。円形ターンテーブルと短い進入くさび、連続した基台、縦マストと二本のガイド、固定フィルム台・中空芯付き巻きロール、操作箱、裏の駆動外装を造形。パレット・積荷・広げたフィルムは含みません。巻きフィルムは不透明単色の外観で、回転・昇降・包装や安全機能は未実装です。','A turntable-style stretch wrapper for warehouse dispatch scenes. It includes a circular platform and short approach wedge, continuous base, vertical mast with twin guides, fixed film carriage and wound roll with open core, control cabinet and rear drive exterior. Pallet, cargo and extended film are absent. The wound film uses an opaque constant-color appearance; rotation, carriage travel, wrapping and safety functions are not implemented.',['warehouse','pallet','wrapper','包装機'])

def roll_cage():
 p=pal()
 for x in [-.314,.314]:
  for y in [-.249,.249]:wheel_caster(p,x,y,.068)
 box('Roll cage thick load deck',(0,0,.220),(.832,.730,.050),p['paint'],.009)
 for x in [-.328,.328]:box('Deck underside load runner',(x,0,.190),(.059,.643,.044),p['steel'],.004)
 for x in [-.394,.394]:
  for y in [-.338,.338]:rod('Full-height cage corner post',(x,y,.242),(x,y,1.735),.014,p['steel'],24)
 for y in [-.338,.338]:rod('Upper cage width rail',(-.394,y,1.735),(.394,y,1.735),.014,p['steel'],24)
 for x in [-.394,.394]:rod('Upper cage side rail',(x,-.338,1.735),(x,.338,1.735),.014,p['steel'],24)
 for z in [.300,1.006,1.672]:
  rod('Rear cage horizontal grid rail',(-.391,.340,z),(.391,.340,z),.007,p['steel'],16)
  for x in [-.395,.395]:rod('Side cage horizontal grid rail',(x,-.326,z),(x,.326,z),.007,p['steel'],16)
 for i in range(10):
  x=-.354+i*.0787;rod('Rear cage vertical wire',(x,.340,.284),(x,.340,1.695),.0045,p['steel'],12)
 for x in [-.395,.395]:
  for i in range(9):y=-.300+i*.075;rod('Side cage vertical wire',(x,y,.284),(x,y,1.695),.0045,p['steel'],12)
 # Two half doors, one fixed swung forward. The enclosure remains visibly open.
 for side in [-1,1]:
  before=set(bpy.context.scene.objects);sg=-side;w=.373;h=1.365
  for xx in [0,sg*w]:rod('Half-door vertical edge',(xx,0,-h/2),(xx,0,h/2),.010,p['steel'],20)
  for zz in [-h/2,0,h/2]:rod('Half-door horizontal edge',(0,0,zz),(sg*w,0,zz),.010 if zz else .006,p['steel'],20)
  for i in range(1,5):xx=sg*w*i/5;rod('Half-door individual grid wire',(xx,0,-h/2+.010),(xx,0,h/2-.010),.0045,p['steel'],12)
  for zz in [-.46,.46]:cyl('Half-door hinge barrel',(0,0,zz),.017,.082,p['dark'],v=24,b=.002)
  box('Door latch backing',(sg*(w-.024),-.008,0),(.050,.035,.111),p['dark'],.004)
  rod('Door latch grip',(sg*(w-.024),-.035,-.034),(sg*(w-.024),-.035,.034),.007,p['bright'],16)
  angle=math.radians(-82) if side==-1 else 0;transform=Matrix.Translation((side*.384,-.344,.984))@Matrix.Rotation(angle,4,'Z')
  for o in set(bpy.context.scene.objects)-before:o.matrix_world=transform@o.matrix_world
 for z in [.524,1.444]:
  for x in [-.393,.393]:box('Cage door hinge attachment',(x,-.346,z),(.042,.044,.088),p['steel'],.003)
 for x in [-.406,.406]:
  box('Side handle mounting spine',(x,.173,1.339),(.018,.052,.687),p['steel'],.003)
  rod('Side pushing handle lower mount',(x,.173,1.200),(x+(-.030 if x<0 else .030),.173,1.200),.009,p['steel'],16)
  rod('Side pushing handle upper mount',(x,.173,1.398),(x+(-.030 if x<0 else .030),.173,1.398),.009,p['steel'],16)
  rod('Side pushing handle',(x+(-.030 if x<0 else .030),.173,1.200),(x+(-.030 if x<0 else .030),.173,1.398),.012,p['dark'],20)
 return ('city-roll-cage-trolley','観音扉付きロールボックス台車','Double-door roll cage trolley','店舗の搬入口・荷さばき場で荷物をまとめて運ぶ背の高いかご台車。厚い荷台と四キャスター、三面の実ワイヤー格子、左右の押し手、二枚扉のうち一枚を開いた固定姿勢、蝶番・掛け金を造形。買い物カートと異なる立方体状の搬送囲いで、荷物は含みません。扉・車輪は静止し、荷重や搬送安全の検証はありません。','A tall roll cage for grouped goods at shop loading entrances and dispatch areas. It has a thick load deck, four casters, three real wire-grid sides, pushing handles and two front doors with one fixed open, plus hinges and latches. Its cubic transport enclosure is distinct from a shopping basket trolley; cargo is absent. Doors and wheels are static, with no load or transport-safety validation.',['warehouse','trolley','roll-cage','ロールボックス'])

def platform_scale():
 p=pal()
 # Raised deck visibly rests on four load-cell-looking blocks above a braced base.
 for x in [-.365,.365]:
  for y in [-.310,.310]:
   cyl('Scale adjustable round foot',(x,y,.027),.035,.042,p['rubber'],v=24,b=.003)
   cyl('Scale foot threaded-looking stem',(x,y,.063),.013,.056,p['steel'],v=20,b=.001)
   box('Scale load-cell exterior block',(x,y,.102),(.108,.068,.040),p['dark'],.003)
 for x in [-.365,.365]:box('Scale underside longitudinal runner',(x,0,.077),(.058,.732,.034),p['paint'],.004)
 for y in [-.300,.300]:box('Scale underside cross runner',(0,y,.080),(.777,.052,.040),p['paint'],.004)
 box('Scale weighing deck',(0,0,.136),(.910,.820,.050),p['steel'],.008)
 for x in [-.446,.446]:box('Scale side protective edge',(x,0,.158),(.016,.805,.030),p['dark'],.003)
 for y in [-.427,.427]:
  # Shallow ramp plate, separate from the scale's underside mechanism.
  sy=1 if y>0 else -1;vs=[(-.415,y-sy*.030,.012),(.415,y-sy*.030,.012),(.415,y+sy*.150,.012),(-.415,y+sy*.150,.012),(-.415,y-sy*.030,.151),(.415,y-sy*.030,.151),(.415,y+sy*.150,.024),(-.415,y+sy*.150,.024)];fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];mesh('Scale approach ramp',vs,fs,p['steel'],.003)
 box('Scale indicator stand base',(.378,.525,.055),(.181,.245,.087),p['paint'],.007)
 bar('Indicator stand base connecting brace',(.378,.305,.072),(.378,.524,.072),.064,.042,p['paint'],.004)
 rod('Scale indicator vertical post',(.378,.530,.090),(.378,.530,1.072),.021,p['steel'],28)
 box('Indicator rear mounting bracket',(.378,.529,1.074),(.130,.072,.092),p['dark'],.004)
 box('Scale indicator housing',(.378,.491,1.136),(.312,.104,.152),p['paint'],.010,rot=(math.radians(12),0,0))
 box('Scale blank display face',(.378,.435,1.151),(.219,.012,.073),p['screen'],.003,rot=(math.radians(12),0,0))
 for x in [.302,.351,.400,.449]:cyl('Scale fixed front function button',(x,.428,1.100),.009,.008,p['dark'],'Y',v=20,b=.001)
 tube('Scale indicator signal cable',[(.378,.565,1.087),(.378,.588,.994),(.398,.590,.477),(.396,.550,.222),(.362,.455,.105),(.321,.333,.086)],.006,p['rubber'],1)
 for z in [.363,.789]:ring('Indicator post cable clip',(.378,.530,z),.022,.003,p['dark'],v=24)
 for x in [.276,.480]:cyl('Indicator rear service screw',(x,.556,1.147),.006,.006,p['steel'],'Y',v=12,b=.0005)
 return ('city-low-platform-scale','低床台はかり','Low platform weighing scale','荷さばき場・業務用室内で箱や台車の計量位置を示す低床台はかり。金属計量台、前後の短い進入板、下面の補強と四つの荷重検出部外形、調整足、接続された支柱式表示器と実ケーブルを造形。表示は無表示で、荷物・台車は含みません。質量計算、校正精度、耐荷重や機能認証は実装・検証していません。','A low platform scale marking a weighing position for parcels or carts in dispatch and service rooms. It has a metal deck, short front/rear approach plates, underside braces and four load-cell exteriors, adjusting-looking feet, attached post indicator and real cable geometry. The indicator is blank; cargo and carts are absent. Mass calculation, calibrated accuracy, load ratings and functional certification are not provided.',['warehouse','scale','weighing','台はかり'])

BUILDERS=[gravity_conveyor,pallet_wrapper,roll_cage,platform_scale]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-039/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/logistics_handling_equipment.py',azimuth=-55,elevation=27)
