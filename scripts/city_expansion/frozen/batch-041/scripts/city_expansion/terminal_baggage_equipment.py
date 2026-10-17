"""Original transport-terminal scene equipment. Xenoah, CC BY 4.0.
No brand markings, inspection simulation, sensing, towing or functional certification.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(steel=mat('Satin terminal fixture metal',(.47,.53,.57),.72,.36),bright=mat('Brushed fitting metal',(.64,.69,.71),.80,.30),paint=mat('Muted teal equipment finish',(.045,.22,.28),.12,.45),white=mat('Warm light arch enclosure',(.69,.71,.70),.05,.48),dark=mat('Dark service trim',(.049,.065,.078),.25,.50),rubber=mat('Dark belt curtain and tire rubber',(.018,.023,.028),0,.73),blue=mat('Inactive blue status lenses',(.045,.25,.40),.04,.30),red=mat('Inactive red status lens',(.41,.038,.028),0,.38),screen=mat('Blank opaque display panel',(.026,.072,.085),.07,.30),wood=mat('Plain untextured trailer decking',(.38,.25,.12),0,.62),amber=mat('Unlit amber reflector',(.67,.29,.038),.03,.36))
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
def capsule_points(half,r,n=32):
 return [(half+r*math.cos(-math.pi/2+i*math.pi/n),r*math.sin(-math.pi/2+i*math.pi/n)) for i in range(n+1)]+[(-half+r*math.cos(math.pi/2+i*math.pi/n),r*math.sin(math.pi/2+i*math.pi/n)) for i in range(n+1)]
def capsule_solid(n,half,r,z0,z1,m):
 pts=capsule_points(half,r);k=len(pts);vs=[(x,y,z) for z in [z0,z1] for x,y in pts];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];o=mesh(n,vs,fs,m)
 for f in o.data.polygons:f.use_smooth=f.index>=2
 return o

def baggage_carousel():
 p=pal();h=.900;outer=1.220;inner=.738
 capsule_solid('Continuous oval carousel lower plinth',h,1.229,.095,.176,p['dark'])
 # Thin external skirt is a complete rounded ring, not solid filled belt geometry.
 rings=[(1.235,.146),(1.235,.544),(1.202,.544),(1.202,.146)];vs=[]
 for r,z in rings:vs.extend((x,y,z) for x,y in capsule_points(h,r))
 n=len(capsule_points(h,1));fs=[(k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i) for k in range(4) for i in range(n)];o=mesh('Rounded carousel outer service skirt',vs,fs,p['steel'])
 for f in o.data.polygons:f.use_smooth=f.index//n in [0,2]
 capsule_solid('Raised central carousel island',h,.716,.154,.735,p['paint'])
 capsule_solid('Central island top cap',h,.724,.727,.749,p['steel'])
 # Seventy-two independent thick slats follow straight runs and semicircular ends.
 def slat(name,a,b):
  # a,b contain outer and inner boundary points, paired across one narrow travel interval.
  oo0,ii0=a;oo1,ii1=b;top=[(*oo0,.562),(*oo1,.562),(*ii1,.679),(*ii0,.679)];vs=[(x,y,z-.025) for x,y,z in top]+top;fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];o=mesh(name,vs,fs,p['dark'],.002)
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.segments=1
 for side in [-1,1]:
  for i in range(14):
   x0=-h+2*h*(i+.020)/14;x1=-h+2*h*(i+.980)/14
   slat('Straight-run individual baggage slat',((x0,side*outer),(x0,side*inner)),((x1,side*outer),(x1,side*inner)))
  for i in range(22):
   a0=-math.pi/2+math.pi*(i+.020)/22;a1=-math.pi/2+math.pi*(i+.980)/22
   if side<0:a0+=math.pi;a1+=math.pi
   cx=side*h
   slat('Curved-run individual baggage slat',((cx+outer*math.cos(a0),outer*math.sin(a0)),(cx+inner*math.cos(a0),inner*math.sin(a0))),((cx+outer*math.cos(a1),outer*math.sin(a1)),(cx+inner*math.cos(a1),inner*math.sin(a1))))
 pts=capsule_points(h,1.238,48);tube('Continuous outer rubber bumper',[(x,y,.515) for x,y in pts+[pts[0]]],.021,p['rubber'],2)
 for x in [-1.420,0,1.420]:
  for y in [-.710,.710]:cyl('Carousel floor support foot',(x,y,.064),.092,.120,p['rubber'],v=24,b=.005)
 for side in [-1,1]:
  box('Skirt service access panel',(0,side*1.239,.337),(.571,.018,.265),p['steel'],.006)
  cyl('Skirt access quarter-turn latch',(.210,side*1.252,.337),.018,.009,p['dark'],'Y',v=24,b=.001)
  for x in [-.241,.241]:
   for z in [.236,.437]:cyl('Service panel screw',(x,side*1.253,z),.006,.006,p['dark'],'Y',v=12,b=.0005)
 return ('city-baggage-reclaim-carousel','楕円型手荷物受取コンベヤ','Oval baggage reclaim carousel','空港や旅客ターミナルの受取エリアに置く楕円型手荷物コンベヤ。二つの直線区間と半円端を回る72枚の独立した厚い傾斜スラット、中央島、丸い外周カバーとバンパー、床支持足、前後の点検蓋を造形。荷物、搬入口、建物側の裏コンベヤは含まず、一周した受取台のみの一式1点です。ベルト搬送や設備制御は実装していません。','An oval baggage carousel for airport and passenger-terminal reclaim areas. Seventy-two separate thick inclined slats follow two straight runs and rounded ends around a central island, with a curved outer skirt/bumper, support feet and front/rear access panels. Luggage, feed opening and behind-wall conveyor are absent; this is one complete closed-loop reclaim unit. Belt transport and equipment controls are not implemented.',['terminal','baggage','carousel','手荷物受取'])

def baggage_inspection():
 p=pal()
 # Longitudinal direction is X. The tunnel is genuinely open at both ends.
 box('Inspection equipment lower cabinet',(0,0,.565),(1.220,.960,.460),p['paint'],.018)
 for x in [-.465,.465]:
  for y in [-.351,.351]:
   box('Inspection main cabinet leg',(x,y,.198),(.061,.061,.314),p['steel'],.005)
   cyl('Inspection cabinet leveling foot',(x,y,.038),.045,.060,p['rubber'],v=24,b=.004)
 for y in [-.423,.423]:box('Inspection tunnel thick side wall',(0,y,1.115),(1.190,.106,.682),p['paint'],.014)
 box('Inspection tunnel top beam',(0,0,1.479),(1.218,.952,.119),p['paint'],.014)
 for y in [-.360,.360]:box('Inner tunnel side lining',(0,y,1.122),(1.150,.018,.599),p['dark'],.004)
 box('Inner tunnel roof lining',(0,0,1.414),(1.149,.710,.020),p['dark'],.003)
 box('Fixed inspection conveyor belt',(0,0,.820),(2.408,.702,.054),p['rubber'],.020)
 for x in [-1.188,1.188]:cyl('Belt nose roller',(x,0,.820),.028,.703,p['dark'],'Y',v=28,b=.001)
 for y in [-.386,.386]:box('Conveyor side frame',(0,y,.785),(2.520,.051,.087),p['steel'],.006)
 for x in [-1.064,1.064]:
  for y in [-.345,.345]:
   box('Outer conveyor support leg',(x,y,.406),(.044,.044,.724),p['steel'],.004)
   cyl('Outer conveyor floor foot',(x,y,.037),.039,.058,p['rubber'],v=24,b=.003)
  rod('Conveyor support cross brace',(x,-.345,.285),(x,.345,.285),.014,p['steel'],20)
 # Static thick curtains have separated strips; a few are folded slightly aside.
 for side in [-1,1]:
  x=side*.604
  box('Tunnel curtain header',(x,0,1.399),(.033,.736,.044),p['dark'],.004)
  for i in range(9):
   y=(i-4)*.077;drop=.444 if i not in [3,4] else .330
   points=[(x,y,1.388),(x,y,1.194),(x+side*(.031 if i%3==0 else .008),y,1.388-drop)]
   # Closed folded ribbon with finite thickness, not single-sided cloth planes.
   vs=[]
   for dx in [-.006,.006]:
    for xx,yy,zz in points:vs.extend([(xx+dx,yy-.033,zz),(xx+dx,yy+.033,zz)])
   fs=[(0,2,3,1),(2,4,5,3),(6,7,9,8),(8,9,11,10),(0,1,7,6),(4,10,11,5),(0,6,8,2),(2,8,10,4),(1,3,9,7),(3,5,11,9)];mesh('Individual static tunnel curtain strip',vs,fs,p['rubber'],.001)
  for y in [-.411,.411]:
   box('Tunnel mouth corner trim',(x,y,1.113),(.045,.046,.646),p['steel'],.005)
 for x in [-.470,.470]:
  box('Inspection front cabinet service panel',(x*.62,-.489,.571),(.516,.018,.280),p['paint'],.006)
  cyl('Cabinet service key latch',(x*.62+.175,-.502,.581),.014,.008,p['dark'],'Y',v=20,b=.001)
 # Side operator screen and keyboard remain blank/original, with a real support arm.
 box('Console lower support bracket',(-.235,-.601,.843),(.174,.328,.084),p['steel'],.008)
 rod('Console monitor upright',(-.235,-.687,.869),(-.235,-.687,1.259),.022,p['dark'],24)
 box('Inspection operator monitor',(-.235,-.688,1.312),(.453,.070,.283),p['dark'],.012)
 box('Blank inspection monitor face',(-.235,-.727,1.312),(.404,.012,.228),p['screen'],.003)
 box('Operator keyboard shelf',(-.235,-.749,.916),(.447,.284,.034),p['steel'],.006)
 box('Generic keyboard base',(-.266,-.755,.945),(.302,.132,.026),p['dark'],.005)
 for row in range(3):
  for col in range(9):box('Unlabeled keyboard key',(-.386+col*.030,-.795+row*.036,.962),(.024,.025,.009),p['steel'],.001)
 cyl('Operator fixed control button',(-.054,-.752,.951),.019,.014,p['red'],v=24,b=.002)
 tube('Console cable to cabinet',[(-.235,-.656,1.235),(-.258,-.634,1.067),(-.258,-.543,.892),(-.258,-.476,.741)],.007,p['rubber'],1)
 for x in [-.404,.404]:
  box('Rear cooling grille inset',(x*.65,.490,.583),(.352,.013,.178),p['dark'],.004)
  for z in [.523+i*.027 for i in range(5)]:box('Rear grille horizontal louver',(x*.65,.500,z),(.316,.013,.010),p['steel'],.001)
 cyl('Rear cabinet service connector',(.431,.497,.419),.018,.020,p['dark'],'Y',v=24,b=.001)
 return ('city-baggage-inspection-tunnel','手荷物検査トンネル装置','Baggage inspection tunnel machine','旅客ターミナルや公共施設入口の手荷物検査区画を示す無銘の筐体。両端が開いたトンネルと厚い分割カーテン、長い固定搬送ベルト・支持脚、点検扉、裏グリル、支持アーム付き無表示モニターと汎用キーを造形。手荷物・検査画像・標章は含みません。外観用の静的モデルで、撮影、放射線、検出・警報や搬送機能は実装していません。','An unbranded enclosure marking a baggage-inspection area at passenger terminals or public-building entrances. It has a tunnel open at both ends with thick separated curtains, a long fixed belt on support legs, service doors, rear grilles and a bracket-mounted blank monitor with generic keys. Luggage, inspection imagery and certification marks are absent. This static exterior prop implements no imaging, radiation, detection, alarms or transport functions.',['terminal','inspection','conveyor','手荷物検査'])

def metal_detector():
 p=pal()
 for x in [-.520,.520]:
  box('Walk-through detector full-height side panel',(x,0,1.152),(.170,.420,2.180),p['white'],.019)
  box('Detector panel wide floor shoe',(x,0,.053),(.244,.581,.090),p['dark'],.012)
  for y in [-.220,.220]:cyl('Detector shoe fixing cap',(x,y,.103),.015,.010,p['steel'],v=6,b=.001)
  box('Front status column dark recess',(x,-.216,1.179),(.049,.015,1.576),p['dark'],.006)
  for i in range(12):box('Unlit status indicator lens',(x,-.226,.494+i*.125),(.027,.008,.051),p['blue'],.004)
  box('Detector rear access panel',(x,.216,1.159),(.126,.016,1.985),p['white'],.008)
  for z in [.245,2.067]:cyl('Rear access-panel screw',(x,.229,z),.007,.006,p['steel'],'Y',v=12,b=.0005)
  cyl('Rear panel cable-entry cap',(x,.231,.171),.018,.014,p['dark'],'Y',v=24,b=.001)
 box('Walk-through detector overhead bridge',(0,0,2.260),(1.219,.448,.192),p['white'],.018)
 box('Overhead front control inset',(0,-.231,2.270),(.493,.018,.116),p['dark'],.006)
 box('Blank detector header display',(-.072,-.243,2.277),(.258,.008,.069),p['screen'],.003)
 for x in [.132,.189]:cyl('Fixed detector header control',(x,-.244,2.272),.014,.009,p['steel'],'Y',v=24,b=.001)
 box('Header rear service seam',(0,.229,2.260),(.795,.013,.126),p['white'],.005)
 for x in [-.348,.348]:cyl('Header rear cover screw',(x,.240,2.260),.007,.005,p['steel'],'Y',v=12,b=.0006)
 return ('city-walkthrough-metal-detector','通過型金属探知ゲート','Walk-through metal detector gate','旅客施設や公共建築の入口で検査導線を示す通過型ゲート。二枚の全高側面パネルと上部橋、足元の取付台、左右各12個の無発光表示窓、無表示の上部操作面、裏点検面・接続口を造形。独立した小売店用盗難防止ペデスタルとは異なる一体型アーチです。人物・床・隣接柵は含まず、検出・警報・認証や安全機能はありません。','A walk-through gate marking a screening route at passenger facilities or public-building entrances. It includes two full-height side panels with overhead bridge, wide mounting feet, twelve unlit indicator windows per side, blank header control face and rear access/connection details. This continuous arch differs from separate retail antitheft pedestals. People, floor and adjacent barriers are absent; no detection, alarms, authentication or safety functions are supplied.',['terminal','security','gate','金属探知ゲート'])

def baggage_trailer():
 p=pal()
 for x in [-.732,.732]:
  cyl('Trailer transverse axle',(x,0,.184),.030,1.456,p['dark'],'Y',v=24,b=.003)
  for y in [-.677,.677]:
   cyl('Trailer rubber tire',(x,y,.184),.180,.124,p['rubber'],'Y',v=40,b=.016)
   for side in [-1,1]:
    cyl('Trailer wheel rim',(x,y+side*.064,.184),.112,.014,p['steel'],'Y',v=32,b=.003)
    cyl('Trailer wheel center hub',(x,y+side*.076,.184),.047,.033,p['dark'],'Y',v=28,b=.002)
    for i in range(6):
     a=i*math.tau/6;cyl('Trailer rim bolt',(x+.077*math.cos(a),y+side*.077,.184+.077*math.sin(a)),.007,.008,p['bright'],'Y',v=6,b=.0006)
 for y in [-.447,.447]:box('Trailer longitudinal chassis beam',(0,y,.402),(2.116,.081,.119),p['dark'],.008)
 for x in [-.795,0,.795]:box('Trailer under-deck crossmember',(x,0,.407),(.076,1.225,.105),p['steel'],.006)
 for x in [-.732,.732]:
  for y in [-.393,.393]:box('Axle suspension support block',(x,y,.294),(.146,.079,.163),p['dark'],.007)
 cyl('Front steering bolster turntable',(-.732,0,.319),.159,.077,p['steel'],v=40,b=.005)
 box('Trailer load bed lower frame',(0,0,.482),(2.150,1.282,.065),p['paint'],.010)
 for i in range(9):box('Individual plain deck board',(0,(i-4)*.134,.525),(2.065,.126,.033),p['wood'],.004)
 for y in [-.621,.621]:
  for x in [-.974,0,.974]:rod('Trailer side guard upright',(x,y,.515),(x,y,.883),.015,p['steel'],24)
  for z in [.683,.881]:rod('Trailer long side guard',( -.974,y,z),(.974,y,z),.014,p['steel'],24)
 # Rear gate is closed in a separate frame, with visible hinge pins and latches.
 for y in [-.582,.582]:rod('Rear end-gate upright',(.990,y,.548),(.990,y,.884),.012,p['steel'],24)
 for z in [.554,.879]:rod('Rear end-gate horizontal bar',(.990,-.582,z),(.990,.582,z),.012,p['steel'],24)
 for y in [-.390,0,.390]:rod('Rear end-gate grid upright',(.990,y,.556),(.990,y,.878),.007,p['steel'],16)
 for y in [-.513,.513]:
  cyl('Rear end-gate hinge barrel',(1.002,y,.548),.018,.086,p['dark'],'Y',v=24,b=.002)
  box('Gate upper latch catch',(.990,y,.856),(.050,.078,.037),p['dark'],.003)
 # Front guard has a lower opening and the fixed drawbar connects to its steering bolster.
 for z in [.650,.880]:rod('Front baggage headboard rail',(-.993,-.606,z),(-.993,.606,z),.016,p['steel'],24)
 for y in [-.420,-.140,.140,.420]:rod('Front headboard short upright',(-.993,y,.544),(-.993,y,.880),.008,p['steel'],16)
 bar('Drawbar steering bolster crossbar',(-.732,-.300,.319),(-.732,.300,.319),.055,.048,p['dark'],.004)
 for y in [-.247,.247]:bar('Trailer drawbar A-frame arm',(-.732,y,.319),(-1.633,0,.321),.052,.041,p['dark'],.004)
 bar('Fixed trailer tow stem',(-1.594,0,.321),(-1.894,0,.321),.048,.050,p['dark'],.004)
 ring('Open trailer towing eye',(-1.949,0,.321),.063,.016,p['steel'],v=40)
 for y in [-.247,.247]:cyl('Drawbar bolster pivot pin',(-.741,y,.319),.018,.097,p['steel'],'Y',v=24,b=.002)
 for y in [-.523,.523]:
  box('Rear unlit reflector mount',(1.090,y,.463),(.025,.118,.064),p['dark'],.005)
  box('Rear unlit red reflector',(1.106,y,.463),(.012,.091,.042),p['red'],.004)
 for x in [-.764,.764]:
  for y in [-.650,.650]:box('Side unlit amber reflector',(x,y,.480),(.096,.016,.035),p['amber'],.003)
 return ('city-baggage-tow-trailer','牽引式手荷物トレーラー','Baggage tow trailer','旅客ターミナルの搬送ヤードに置く低床の牽引式手荷物トレーラー。四輪・車軸と下部フレーム、木材色の個別床板、側部ガードと前立て、閉じた後扉・蝶番・掛け金、前輪側ボルスターに繋がるA字ドローバーと実開口の牽引環を造形。牽引車・荷物は付属せず、全体で一台です。車輪、操舵、扉、連結は静止し、牽引・荷重や道路適合性の検証はありません。','A low baggage tow trailer for passenger-terminal handling yards. It has four wheels and axles, underframe, individual wood-colored deck boards, side guards/front headboard, closed rear gate with hinges/latches, and an A-frame drawbar connected to the front steering bolster with an actual open towing eye. Tug and luggage are absent; the entire trailer is one model. Wheels, steering, gate and coupling are static; towing, load and road compliance are not validated.',['terminal','baggage','trailer','手荷物トレーラー'])

BUILDERS=[baggage_carousel,baggage_inspection,metal_detector,baggage_trailer]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-041/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/terminal_baggage_equipment.py',azimuth=-55,elevation=27)
