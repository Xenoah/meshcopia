"""Original commercial kitchen scene fixtures. Xenoah, CC BY 4.0.
Static appearance props, no brands, real heating, washing or fluid simulation.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def pal():
 return dict(steel=mat('Satin stainless kitchen metal',(.49,.54,.55),.76,.36),bright=mat('Bright fittings',(.67,.71,.71),.82,.28),dark=mat('Dark service recess',(.055,.069,.072),.28,.55),rubber=mat('Graphite seals and feet',(.018,.025,.027),0,.73),blue=mat('Muted blue rack polymer',(.055,.27,.36),.02,.52),glass=mat('Opaque dark oven window substitute',(.04,.09,.105),.14,.22),screen=mat('Inactive control display',(.035,.09,.095),.04,.34),red=mat('Unlit red control accent',(.44,.065,.045),.02,.48))
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
def feet(p,w,d,z=.037):
 for x in [-w/2,w/2]:
  for y in [-d/2,d/2]:
   cyl('Adjustable equipment foot',(x,y,z),.028,.050,p['rubber'],v=24,b=.003)
   cyl('Foot threaded-looking stem',(x,y,z+.040),.013,.052,p['steel'],v=20,b=.001)

def double_sink():
 p=pal()
 def rr(w,d,r):
  pts=[]
  for cx,cy,a0 in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
   for j in range(8):a=math.radians(a0+j*90/8);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
  return pts
 def bowl(cx):
  loops=[(rr(.530,.510,.060),.930),(rr(.460,.440,.055),.930),(rr(.440,.420,.065),.880),(rr(.320,.300,.085),.700),([(.026*math.cos(i*math.tau/32),.026*math.sin(i*math.tau/32)) for i in range(32)],.686),([(.030*math.cos(i*math.tau/32),.030*math.sin(i*math.tau/32)) for i in range(32)],.675),(rr(.332,.312,.088),.682),(rr(.490,.470,.065),.913)];vs=[(cx+x,y,z) for pts,z in loops for x,y in pts];n=32;fs=[(k*n+i,k*n+(i+1)%n,((k+1)%len(loops))*n+(i+1)%n,((k+1)%len(loops))*n+i) for k in range(len(loops)) for i in range(n)];o=mesh('Deep sink bowl with real drain opening',vs,fs,p['steel'])
  for f in o.data.polygons:f.use_smooth=f.index//n in [1,2,3,5,6,7]
  sleeve('Visible open drain fitting',(cx,0,.677),.031,.020,.028,p['bright'])
  sleeve('Drain downpipe',(cx,0,.592),.023,.018,.145,p['steel'])
  tube('Visible U-shaped waste trap',[(cx,0,.529),(cx,0,.440),(cx,.090,.412),(cx,.173,.440),(cx,.173,.515)],.022,p['steel'],2)
  sleeve('Open rear waste connection',(cx,.207,.515),.023,.018,.080,p['steel'],'Y')
  for z in [.553,.515]:cyl('Waste pipe union collar',(cx,0,z),.029,.018,p['dark'],v=24,b=.001)
 for x in [-.310,.310]:bowl(x)
 # One continuous counter deck with genuine rounded bowl cutouts avoids open corner gaps.
 deck=box('Continuous double-sink countertop',(0,0,.916),(1.310,.716,.022),p['steel'],0)
 for cx in [-.310,.310]:
  contour=rr(.494,.474,.058);n=len(contour)
  vs=[(cx+x,y,z) for z in [.880,.955] for x,y in contour]
  fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  cutter=mesh('Temporary countertop opening cutter',vs,fs,p['steel'])
  mod=deck.modifiers.new('Actual rounded bowl cutout','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
  bpy.context.view_layer.objects.active=deck;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 mod=deck.modifiers.new('Soft counter edges','BEVEL');mod.width=.0015;mod.segments=1

 for x in [-.560,.560]:
  for y in [-.244,.244]:
   cyl('Tubular sink leg',(x,y,.478),.025,.844,p['steel'],v=28,b=.002)
   cyl('Sink leveling foot',(x,y,.040),.033,.062,p['rubber'],v=24,b=.003)
  rod('Sink side lower brace',(x,-.244,.212),(x,.244,.212),.015,p['steel'])
 rod('Sink lower rear brace',(-.560,.244,.212),(.560,.244,.212),.015,p['steel'])
 box('Raised sink backsplash',(0,.357,1.057),(1.300,.024,.282),p['steel'],.006)
 for x in [-.310,.310]:
  cyl('Faucet mounting foot',(x,.282,.941),.032,.028,p['bright'],v=32,b=.002)
  cyl('Faucet upright',(x,.282,1.020),.016,.140,p['bright'],v=28,b=.001)
  tube('Arched faucet spout',[(x,.282,1.087),(x,.274,1.211),(x,.207,1.270),(x,.073,1.270),(x,-.004,1.205)],.013,p['bright'],2)
  sleeve('Visible open faucet aerator',(x,-.004,1.191),.017,.011,.029,p['bright'])
  for side in [-1,1]:
   cyl('Faucet control base',(x+side*.067,.282,.945),.021,.025,p['bright'],v=24,b=.002)
   rod('Fixed faucet lever',(x+side*.067,.282,.962),(x+side*.110,.262,.987),.006,p['bright'],16)
 return ('city-commercial-double-sink','脚付き業務用二槽流し台','Freestanding commercial double sink','食堂・厨房の洗浄区画へ置く脚付き二槽流し台。深い二つの鉢と実開口の排水口、アーチ水栓と開いた吐水端、背立て、四脚と下部補強、下の排水管・U字トラップを造形。壁・給排水設備は付属せず、現場の位置へ配置する一式1点です。水流や弁操作は実装していません。','A freestanding double sink for cafeteria and commercial-kitchen wash areas, with two deep bowls and actual drain openings, arched faucets with open outlets, backsplash, four legs/lower bracing, drain pipes and visible U traps. Wall and building plumbing are not included; place the whole single assembly as needed. Water flow and valve operation are not implemented.',['kitchen','sink','plumbing','二槽シンク'])

def range_hood():
 p=pal()
 # Eight rings form a thick open canopy, not a closed pyramidal box.
 loops=[(1.200,.640,0,.190),(1.200,.640,0,.220),(.390,.310,.110,.620),(.390,.310,.110,.650),(.352,.272,.110,.650),(.352,.272,.110,.620),(1.160,.600,0,.220),(1.160,.600,0,.190)];vs=[]
 for w,d,cy,z in loops:vs.extend([(-w/2,cy-d/2,z),(w/2,cy-d/2,z),(w/2,cy+d/2,z),(-w/2,cy+d/2,z)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%len(loops))*4+(i+1)%4,((k+1)%len(loops))*4+i) for k in range(len(loops)) for i in range(4)];o=mesh('Open flared extraction canopy',vs,fs,p['steel'],.002)
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 # The rectangular chimney is a hollow annular extrusion with an open upper connection.
 vs=[]
 for w,d,z in [(.380,.300,.632),(.380,.300,1.060),(.350,.270,1.060),(.350,.270,.632)]:vs.extend([(-w/2,.110-d/2,z),(w/2,.110-d/2,z),(w/2,.110+d/2,z),(-w/2,.110+d/2,z)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)];mesh('Open rectangular hood chimney',vs,fs,p['steel'])
 for x in [-.277,.277]:
  frame('Removable-style filter frame',.512,.475,.024,.015,(x,-.005,.204),p['dark'],'XY')
  for i in range(14):box('Separated grease-filter baffle',(x+(i-6.5)*.034,-.005,.209),(.018,.423,.015),p['bright'],.002,rot=(0,math.radians(26),0))
  for y in [-.172,.172]:rod('Filter rear supporting rail',(x-.222,y,.221),(x+.222,y,.221),.004,p['steel'],12)
  box('Filter pull tab',(x,-.226,.194),(.065,.025,.017),p['dark'],.003)
 for x in [-.460,.460]:
  box('Hood underside light recess',(x,-.280,.191),(.144,.026,.012),p['dark'],.003)
  box('Unlit underside light diffuser',(x,-.286,.184),(.115,.019,.008),p['ivory'] if 'ivory' in p else p['bright'],.002)
 for x in [-.360,.360]:frame('Rear slotted wall mounting plate',.088,.188,.029,.015,(x,.321,.294),p['steel'],'XZ')
 box('Front control strip',(-.350,-.324,.216),(.294,.013,.034),p['dark'],.004)
 for i in range(4):cyl('Fixed hood pushbutton',(-.442+i*.055,-.334,.216),.009,.006,p['bright'],'Y',v=20,b=.001)
 box('Rear grease collection cup',(0,.253,.163),(.135,.105,.058),p['steel'],.007)
 return ('city-commercial-range-hood','壁付業務用レンジフード','Wall-mounted commercial range hood','厨房の加熱器具上に配置する壁付排気フード。内側が開いた斜面キャノピーと角形煙道、二枚の実隙間付きバッフルフィルター、引手、下面照明の外形、前面ボタン、背面取付スロットと小さな回収カップを造形。床基準原点から設置高さを調整し、建物ダクトは別途配置します。送風・照明・捕集機能は実装していません。','A wall-mounted extraction hood for placement above cooking equipment, with hollow sloped canopy and rectangular chimney, two genuinely gapped baffle filters, pulls, underside-light exteriors, front buttons, rear mounting slots and a small collection cup. Adjust installation height from the base origin; building ductwork is separate. Air movement, lighting and capture functions are not implemented.',['kitchen','range-hood','ventilation','レンジフード'])

def convection_oven():
 p=pal();feet(p,.724,.590)
 # Side, rear and top sheets surround a genuinely open cooking chamber.
 for x in [-.429,.429]:box('Oven outer side sheet',(x,0,.485),(.025,.746,.768),p['steel'],.006)
 box('Oven rear outer service sheet',(0,.367,.485),(.842,.024,.768),p['steel'],.005)
 box('Oven top cover',(0,0,.876),(.884,.780,.027),p['steel'],.006)
 box('Oven lower base',(0,0,.125),(.842,.743,.048),p['dark'],.005)
 for x in [-.321,.257]:box('Cooking chamber inner side',(x,-.016,.493),(.018,.634,.590),p['steel'],.004)
 box('Cooking chamber rear liner',(-.032,.290,.493),(.570,.018,.590),p['dark'],.003)
 for z in [.202,.784]:box('Cooking chamber upper lower liner',(-.032,-.016,z),(.580,.632,.018),p['steel'],.003)
 frame('Oven door gasket surround',.640,.635,.030,.016,(-.032,-.347,.493),p['rubber'],'XZ')
 for z in [.345,.559]:
  for x in [-.292,.228]:rod('Oven shelf side guide',(x,-.295,z),(x,.253,z),.006,p['steel'])
  for y in [-.293,.247]:rod('Wire shelf front back edge',(-.281,y,z+.009),(.217,y,z+.009),.005,p['bright'],16)
  for i in range(13):x=-.276+i*.040;rod('Individual rack shelf wire',(x,-.293,z+.009),(x,.247,z+.009),.003,p['bright'],12)
 cyl('Rear fixed convection fan hub',(-.032,.270,.552),.035,.030,p['steel'],'Y',v=28,b=.002)
 for i in range(8):
  a=i*math.tau/8;box('Rear fixed convection fan blade',(-.032+.074*math.cos(a),.272,.552+.074*math.sin(a)),(.104,.016,.037),p['steel'],.004,rot=(0,-a,0))
 ring('Fan guard outer hoop',(-.032,.248,.552),.128,.004,p['bright'],'Y',48)
 for a in [0,math.pi/4,math.pi/2,3*math.pi/4]:rod('Fan protective guard wire',(-.032+.124*math.cos(a),.242,.552+.124*math.sin(a)),(-.032-.124*math.cos(a),.242,.552-.124*math.sin(a)),.0025,p['bright'],12)
 box('Oven front control column',(.348,-.358,.495),(.123,.042,.724),p['steel'],.005)
 box('Inactive oven digital display',(.349,-.383,.727),(.087,.009,.047),p['screen'],.003)
 for z in [.592,.450,.308]:
  cyl('Fixed oven control knob',(.348,-.389,z),.031,.035,p['rubber'],'Y',v=32,b=.003)
  box('Knob position rib',(.348,-.410,z+.014),(.005,.004,.018),p['bright'],.0007)
 # Door is fixed swung open. The blue pane is deliberately opaque, not glass transmission.
 before=set(bpy.context.scene.objects);hinge=Vector((-.356,-.368,.493))
 frame('Open oven door perimeter',.650,.648,.057,.044,(.325,0,0),p['steel'],'XZ',.004)
 box('Opaque oven viewing pane',(.325,0,0),(.523,.019,.517),p['glass'],.006)
 for z in [-.190,.190]:box('Door handle mounting post',(.586,-.044,z),(.028,.060,.032),p['steel'],.004)
 rod('Open oven door pull',(.586,-.079,-.205),(.586,-.079,.205),.013,p['dark'],24)
 rot=Matrix.Rotation(math.radians(-106),4,'Z');trans=Matrix.Translation(hinge)
 for o in set(bpy.context.scene.objects)-before:o.matrix_world=trans@rot@o.matrix_world
 for z in [.260,.728]:cyl('Oven door fixed hinge',(-.356,-.367,z),.014,.104,p['steel'],v=24,b=.001)
 for x in [-.337,.337]:
  for z in [.218,.747]:cyl('Rear cover screw',(x,.383,z),.007,.006,p['dark'],'Y',v=12,b=.0006)
 for z in [.635+i*.027 for i in range(5)]:box('Rear service vent exterior',(0,.383,z),(.392,.011,.010),p['dark'],.002)
 cyl('Rear service connection cap',(.287,.395,.234),.021,.032,p['dark'],'Y',v=24,b=.002)
 return ('city-commercial-convection-oven','業務用コンベクションオーブン','Commercial convection oven','食堂やベーカリー厨房の作業位置へ置く対流式オーブン外観。開いた加熱室、二段の実ワイヤー棚、奥の固定ファンとガード、横に開いた扉と引手、つまみ・無表示パネル、裏点検部と調整足を造形。扉の青灰色窓は不透明な単色PBR表現です。台・食品・トレーは含まず、加熱・送風・開閉操作は実装していません。','A convection-oven appearance prop for cafeteria and bakery work areas. An open chamber contains two real wire shelves and a fixed rear fan/guard, with swung-open door/pull, knobs, inactive display, rear service features and leveling feet. The blue-gray door window is an opaque constant-color PBR substitute. Counter, food and trays are absent; heating, airflow and door operation are not implemented.',['kitchen','oven','bakery','オーブン'])

def dishwasher():
 p=pal();feet(p,.490,.490)
 for x in [-.296,.296]:box('Dishwasher side enclosure',(x,0,.462),(.022,.624,.690),p['steel'],.005)
 box('Dishwasher rear service enclosure',(0,.304,.462),(.572,.022,.690),p['steel'],.005)
 box('Dishwasher top cover',(0,0,.819),(.616,.650,.028),p['steel'],.005)
 box('Dishwasher lower base',(0,0,.131),(.572,.602,.037),p['dark'],.005)
 # The front is open. Liner sheets enclose the deep empty wash chamber.
 for x in [-.260,.260]:box('Dishwasher chamber side liner',(x,-.001,.493),(.015,.566,.521),p['steel'],.003)
 box('Dishwasher chamber back liner',(0,.274,.493),(.514,.015,.521),p['steel'],.003)
 for z in [.238,.748]:
  panel=box('Dishwasher chamber floor roof',(0,-.001,z),(.518,.566,.015),p['steel'],0)
  if z==.238:
   cutter=cylinder('Temporary through-drain cutter',(0,.186,z),.017,.060,p['steel'],32,bevel=0)
   mod=panel.modifiers.new('Real through-drain opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
   bpy.context.view_layer.objects.active=panel;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
  mod=panel.modifiers.new('Small liner edge bevel','BEVEL');mod.width=.001;mod.segments=1

 frame('Wash chamber front gasket',.554,.553,.019,.016,(0,-.292,.493),p['rubber'],'XZ')
 box('Front upper control strip',(0,-.316,.789),(.567,.030,.053),p['dark'],.004)
 box('Inactive dishwasher display',(-.114,-.335,.789),(.133,.008,.027),p['screen'],.002)
 for x in [.085,.143,.201]:cyl('Dishwasher fixed pushbutton',(x,-.336,.789),.013,.008,p['bright'],'Y',v=20,b=.001)
 # Door is horizontal and fixed open, with a visible interior and small dispenser.
 box('Open dishwasher door outer skin',(0,-.580,.212),(.570,.574,.034),p['steel'],.006)
 box('Open door inner panel',(0,-.580,.233),(.524,.528,.014),p['steel'],.004)
 for x in [-.270,.270]:cyl('Dishwasher door hinge barrel',(x,-.295,.218),.014,.044,p['steel'],'X',v=20,b=.001)
 box('Door soap dispenser exterior',(.145,-.734,.248),(.142,.084,.019),p['dark'],.004)
 box('Fixed dispenser cover',(.145,-.735,.261),(.122,.066,.009),p['steel'],.003)
 box('Door external pull lip',(0,-.866,.213),(.380,.027,.031),p['dark'],.004)
 # A single basket is fixed partly withdrawn, supported by actual rollers and rails.
 for x in [-.222,.222]:
  rod('Basket guide rail',(x,-.779,.248),(x,.215,.248),.007,p['steel'],16)
  for y in [-.596,-.273]:cyl('Basket roller',(x,y,.271),.021,.018,p['rubber'],'X',v=24,b=.001)
 frame('Partly withdrawn basket bottom perimeter',.476,.480,.013,.014,(0,-.424,.296),p['blue'],'XY')
 for x in [-.234,.234]:
  for z in [.315,.428]:rod('Basket side top rail',(x,-.658,z),(x,-.190,z),.005,p['blue'],16)
 for y in [-.658,-.190]:
  for z in [.315,.428]:rod('Basket end rail',(-.234,y,z),(.234,y,z),.005,p['blue'],16)
 for i in range(9):
  x=(i-4)*.054;rod('Basket floor grid length',(x,-.650,.300),(x,-.198,.300),.003,p['blue'],12)
  y=-.640+i*.054;rod('Basket floor grid width',(-.226,y,.300),(.226,y,.300),.003,p['blue'],12)
  for xx in [-.234,.234]:rod('Basket vertical side upright',(xx,y,.300),(xx,y,.429),.004,p['blue'],12)
 for y in [-.570,-.440,-.310]:
  for x in [-.162,-.108,-.054,0,.054,.108,.162]:rod('Fixed dish rack support tine',(x,y,.300),(x,y-.020,.399),.003,p['blue'],12)
 rod('Fixed interior lower spray arm',(-.197,.065,.262),(.197,.065,.262),.009,p['steel'],20)
 for x in [-.155,-.075,.075,.155]:cyl('Spray arm nozzle appearance',(x,.065,.273),.004,.004,p['dark'],v=12,b=.0003)
 sleeve('Interior open drain fitting',(0,.186,.247),.023,.014,.018,p['bright'])
 for x in [-.210,.210]:
  cyl('Rear water hose connection',(x,.329,.258),.018,.038,p['steel'],'Y',v=24,b=.001)
  tube('Parked rear supply or drain hose',[(x,.347,.260),(x,.382,.205),(x*.64,.390,.194),(x*.61,.385,.354),(x*.75,.366,.397)],.010 if x<0 else .014,p['rubber'],1)
 box('Rear electrical service cover',(0,.327,.622),(.271,.023,.162),p['dark'],.005)
 for x in [-.111,.111]:cyl('Rear service cover screw',(x,.342,.622),.006,.004,p['steel'],'Y',v=12,b=.0005)
 return ('city-undercounter-dishwasher','開いたアンダーカウンター食器洗浄機','Open undercounter dishwasher','食堂や小さな厨房のカウンター下へ置く食器洗浄機外観。実際に開いた洗浄室、水平に開いた扉と洗剤入れ、少し引き出したワイヤー状ラックと支持ローラー、内部噴射アーム、排水口、裏の接続口・収納ホースを造形。カウンター・食器は含まず、扉とラックは固定姿勢です。洗浄・通水・電装機能は実装していません。','An undercounter-dishwasher appearance prop for cafeterias and small kitchens. It has a genuinely open chamber, horizontal open door/dispenser, partly withdrawn wire-like rack on support rollers, interior spray arm, drain opening, rear connections and parked hoses. Counter and dishes are absent; door and rack remain in one fixed pose. Washing, plumbing and electrical functions are not implemented.',['kitchen','dishwasher','cleaning','食器洗浄機'])
BUILDERS=[double_sink,range_hood,convection_oven,dishwasher]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-038/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/commercial_kitchen_fixtures.py',azimuth=-55,elevation=30)
