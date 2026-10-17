"""Original clinical-room scene props. Xenoah, CC BY 4.0.
Static assemblies; clinical functions and medical safety certification are absent.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(white=mat('Warm clinical shell',(.72,.75,.74),.03,.43),paint=mat('Muted blue upholstery',(.045,.25,.34),0,.66),steel=mat('Brushed support metal',(.46,.53,.57),.73,.34),bright=mat('Small bright hardware',(.65,.70,.74),.82,.27),dark=mat('Dark service trim',(.035,.047,.058),.12,.54),rubber=mat('Caster and cable rubber',(.016,.023,.028),0,.76),screen=mat('Opaque inactive instrument face',(.021,.066,.084),.08,.28),lens=mat('Opaque unlit lens face',(.40,.62,.67),.08,.30),linen=mat('Plain mattress fabric',(.69,.73,.72),0,.85))
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

def ward_bed():
 p=pal()
 for x in [-.420,.420]:
  for y in [-.880,.880]:caster('Bed',x,y,.071,p)
 for x in [-.420,.420]:box('Bed lower chassis side',(x,0,.201),(.068,1.842,.070),p['white'],.007)
 for y in [-.800,.800]:box('Bed lower chassis crossbar',(0,y,.201),(.904,.065,.070),p['steel'],.005)
 # Fixed lift-link pairs remain visibly attached to lower and upper frames.
 for x in [-.343,.343]:
  bar('Bed diagonal lift link',(x,-.70,.225),(x,.64,.546),.052,.032,p['steel'],.004)
  bar('Bed opposing lift link',(x,.70,.225),(x,-.64,.546),.052,.032,p['steel'],.004)
  cyl('Bed lift-link center pin',(x,0,.385),.030,.052,p['bright'],'X',v=24,b=.002)
 box('Bed fixed actuator housing',(0,.130,.302),(.140,.470,.103),p['white'],.010)
 rod('Bed actuator rod',(0,-.091,.315),(0,-.505,.510),.020,p['steel'],24)
 for x in [-.443,.443]:box('Bed upper platform rail',(x,0,.566),(.064,2.016,.068),p['white'],.007)
 box('Bed horizontal deck',(0,.374,.594),(.903,1.238,.055),p['steel'],.004)
 box('Plain bed lower mattress',(0,.380,.684),(.914,1.224,.134),p['linen'],.034)
 angle=-math.atan2(.440,.720);center=Vector((0,-.580,.814));normal=Vector((0,-math.sin(angle),math.cos(angle)))
 box('Raised bed back deck',center,(.905,.844,.045),p['steel'],.004,rot=(angle,0,0))
 box('Plain raised back mattress',center+normal*.084,(.914,.822,.129),p['linen'],.030,rot=(angle,0,0))
 for x in [-.250,.250]:rod('Fixed raised-back support strut',(x,-.800,.598),(x,-.700,.870),.014,p['steel'],24)
 for x in [-.461,.461]:
  for y in [-1.015,1.015]:bar('Bed endboard mounting post',(x,y,.576),(x,y,1.112 if y<0 else .948),.036,.040,p['steel'],.004)
 for y,z,h in [(-1.049,1.026,.367),(1.049,.880,.317)]:
  box('Bed head or foot board',(0,y,z),(.995,.071,h),p['white'],.026)
  box('Bed endboard inset',(0,y+(-.040 if y<0 else .040),z),(.739,.013,h*.54),p['paint'],.016)
 for side in [-1,1]:
  x=side*.530
  for y in [-.480,.380]:
   for yy in [y-.229,y+.229]:rod('Bed side-rail upright',(x,yy,.604),(x,yy,.995),.014,p['white'],24)
   for z in [.720,.944,.995]:rod('Bed side-rail horizontal',(x,y-.229,z),(x,y+.229,z),.014,p['white'],24)
   for yy in [y-.229,y+.229]:rod('Bed side-rail mounting stem',(side*.444,yy,.588),(x,yy,.621),.017,p['steel'],20)
   cyl('Rail fixed hinge hub',(x,y-.229,.623),.032,.031,p['dark'],'X',v=24,b=.002)
 box('Bed blank side control block',(.556,.360,.878),(.024,.117,.069),p['dark'],.005)
 for y in [.332,.362,.392]:box('Unlabeled bed control key',(.572,y,.879),(.009,.019,.025),p['white'],.002)
 return ('city-adjustable-ward-bed','背上げ状態の病室ベッド','Adjustable-style ward bed','診療施設の病室背景に置く背上げ状態のベッド。分割マットレスと上体側の傾斜面、ヘッド・フット板、左右の短い側柵、固定された昇降リンクと駆動部外形、四つの車輪・ブレーキ外形、無表示の側面操作部を造形。搬送ストレッチャーとは異なる病室用設備として一式1点です。患者・寝具の装飾は含まず、昇降・電動・荷重・医療安全性能は実装・検証していません。','A bed with raised back section for clinic and hospital room backgrounds. It has divided plain mattresses, inclined upper-body support, head/foot boards, short side rails, fixed lift links/actuator exterior, four casters with brake exteriors and an unlabelled side control block. It is a ward-room assembly rather than a transfer stretcher and counts as one model. Patient and decorative bedding are absent; adjustment, electrical, load and medical-safety performance are not implemented or validated.',['clinical','bed','interior','病室ベッド'])

def dental_chair():
 p=pal()
 cyl('Dental chair broad pedestal base',(0,.110,.058),.423,.106,p['white'],v=48,b=.011)
 box('Dental chair lift pedestal',(0,.075,.290),(.283,.366,.411),p['white'],.039)
 box('Dental chair pedestal rear cover',(0,.246,.303),(.229,.034,.239),p['dark'],.008)
 box('Dental chair seat support',(0,.103,.522),(.476,.531,.089),p['steel'],.012)
 box('Dental chair seat cushion',(0,.133,.607),(.559,.618,.127),p['paint'],.049)
 a=-math.atan2(.493,.553);c=Vector((0,-.429,.843));n=Vector((0,-math.sin(a),math.cos(a)))
 box('Dental chair reclined back shell',c,(.544,.768,.058),p['white'],.025,rot=(a,0,0))
 box('Dental chair back cushion',c+n*.068,(.493,.739,.112),p['paint'],.037,rot=(a,0,0))
 rod('Dental chair headrest support',(0,-.704,1.084),(0,-.825,1.238),.025,p['steel'],28)
 box('Dental chair rounded headrest',(0,-.824,1.266),(.272,.193,.122),p['paint'],.043,rot=(a,0,0))
 aa=-math.atan2(.270,.570)
 box('Dental chair sloped lower leg shell',(0,.625,.437),(.505,.632,.056),p['white'],.019,rot=(aa,0,0))
 box('Dental chair lower leg cushion',(0,.625,.487),(.477,.610,.091),p['paint'],.031,rot=(aa,0,0))
 box('Dental foot support',(0,.944,.274),(.493,.204,.047),p['dark'],.013)
 for side in [-1,1]:
  rod('Dental armrest upright',(side*.300,.090,.557),(side*.350,.086,.795),.024,p['steel'],24)
  box('Dental padded armrest',(side*.354,.068,.811),(.091,.369,.065),p['paint'],.023)
  cyl('Dental backrest fixed pivot',(side*.279,-.151,.589),.050,.039,p['white'],'X',v=32,b=.004)
 # Side service unit is connected to the chair pedestal by a low support arm.
 box('Dental service-unit foot',(.680,-.102,.065),(.303,.389,.091),p['white'],.021)
 bar('Connected dental unit support',(0,.091,.197),(.683,-.102,.197),.073,.092,p['steel'],.008)
 box('Dental side cabinet',(.680,-.102,.479),(.252,.314,.701),p['white'],.029)
 for z in [.330,.390,.450]:box('Dental service cabinet rear vent',(.680,.060,z),(.173,.012,.014),p['dark'],.002)
 # A thick bowl section leaves the interior and central drain opening visible.
 profile=[(.185,.929),(.171,.948),(.150,.925),(.115,.873),(.035,.848),(.021,.848),(.021,.835),(.060,.834),(.145,.875),(.186,.914)];N=48;vs=[(.680+r*math.cos(i*math.tau/N),-.118+r*math.sin(i*math.tau/N),z) for r,z in profile for i in range(N)];fs=[(k*N+i,k*N+(i+1)%N,((k+1)%len(profile))*N+(i+1)%N,((k+1)%len(profile))*N+i) for k in range(len(profile)) for i in range(N)];mesh('Dental rinse bowl with visible drain',vs,fs,p['white'],smooth=True)
 sleeve('Dental bowl drain trim',(.680,-.118,.849),.032,.020,.009,p['steel'],v=32)
 sleeve('Rinse bowl support and drain neck',(.680,-.118,.832),.057,.024,.014,p['white'],v=32)
 cyl('Dark recessed dental drain interior',(.680,-.118,.835),.019,.006,p['dark'],v=28,b=.0005)
 smooth_cable('Dental rinse faucet',[(.798,-.208,.824),(.798,-.208,1.021),(.763,-.178,1.070),(.716,-.129,1.055)],.011,p['steel'])
 cyl('Dental faucet dark outlet',(.715,-.128,1.049),.009,.011,p['dark'],v=24,b=.0005)
 bar('Dental tray articulated support',(.680,.003,.735),(.680,.228,.939),.036,.046,p['steel'],.004)
 box('Dental instrument tray',(.680,.249,.998),(.474,.297,.057),p['white'],.013)
 box('Dental tray shallow inset',(.680,.239,1.030),(.411,.230,.013),p['dark'],.005)
 for x in [.527,.680,.833]:
  cyl('Fixed dental instrument handle',(x,.403,.943),.015,.156,p['steel'],v=24,b=.002)
  ring('Dental instrument holster',(x,.403,.967),.019,.005,p['white'],v=24)
  bar('Holster attachment tab',(x,.390,.970),(x,.361,.982),.024,.020,p['white'],.002)
  smooth_cable('Curved fixed dental instrument hose',[(x,.403,.867),(x,.456,.691),(x+.018,.443,.471),(x+.026,.246,.431),(x+.009,.078,.700)],.006,p['dark'])
 for obj in bpy.context.scene.objects:
  if obj.type=='MESH' and obj.data.materials and obj.data.materials[0]==p['paint']:
   for mod in obj.modifiers:
    if mod.type=='BEVEL':mod.segments=4
 return ('city-dental-treatment-chair','側方ユニット付き歯科診療椅子','Dental treatment chair with side unit','歯科診療室の背景に置く椅子と側方ユニット一式。傾斜した背・脚クッション、頭当て・肘掛け、昇降台外形、支持アームで接続したキャビネット、実際に凹んだすすぎ鉢と排水口、水栓、器具トレーと三本の固定ハンドピース・曲線ホースを造形。一式1点で、患者や医療画面を含みません。診療・給排水・作動や医療安全適合を表す設計ではありません。','A chair and connected side-unit assembly for dental-room backgrounds. It has inclined back/leg cushions, headrest/armrests, lift-base exterior, support-linked cabinet, genuinely recessed rinse bowl and drain, faucet, instrument tray and three fixed handpiece exteriors with curved hoses. It counts as one assembly and contains no patient or medical imagery. It is not a design demonstrating clinical, plumbing, operational or medical-safety performance.',['clinical','dental','chair','歯科診療椅子'])

def ultrasound_cart():
 p=pal()
 for x in [-.236,.236]:
  for y in [-.230,.230]:caster('Ultrasound cart',x,y,.052,p)
 box('Ultrasound cart base',(0,0,.160),(.583,.591,.075),p['white'],.023)
 box('Ultrasound cart lower cabinet',(0,.035,.537),(.447,.416,.733),p['white'],.032)
 box('Ultrasound cart rear service panel',(0,.252,.579),(.351,.022,.501),p['dark'],.012)
 for z in [.414,.457,.500,.543]:box('Cart rear service louver',(0,.267,z),(.264,.011,.017),p['steel'],.002)
 box('Ultrasound console support',(0,-.018,.933),(.453,.453,.092),p['white'],.018)
 box('Ultrasound keyboard console',(0,-.200,1.006),(.635,.403,.060),p['white'],.021,rot=(math.radians(5),0,0))
 for row in range(3):
  for col in range(11):box('Unlettered console keyboard key',(-.229+col*.043,-.305+row*.041,1.045),(.034,.029,.009),p['dark'],.002)
 for x in [-.205,-.132,-.059,.014]:cyl('Fixed console control knob',(x,-.105,1.052),.018,.025,p['steel'],v=24,b=.002)
 sphere('Console fixed trackball',(.186,-.118,1.058),(.038,.038,.025),p['dark'],segments=24,rings=12)
 rod('Monitor articulated support',(0,.145,.962),(0,.114,1.311),.034,p['steel'],28)
 angle=math.radians(-12);center=Vector((0,.073,1.432));normal=Vector((0,-math.cos(angle),-math.sin(angle)))
 box('Ultrasound monitor rear enclosure',center,(.588,.060,.424),p['white'],.016,rot=(angle,0,0))
 box('Blank inactive ultrasound screen',center+normal*.035,(.520,.012,.352),p['screen'],.006,rot=(angle,0,0))
 for x in [-.201,0,.201]:box('Rear monitor small grille',(x,.112,1.416),(.131,.013,.086),p['dark'],.003,rot=(angle,0,0))
 for y in [-.021,.133]:
  sleeve('Probe holding collar',(.310,y,.904),.027,.018,.041,p['white'],v=28)
  rod('Probe holder connecting arm',(.209,y,.898),(.310,y,.898),.012,p['white'],20)
  cyl('Parked probe narrow handle',(.310,y,.953),.017,.146,p['white'],v=28,b=.003)
  box('Opaque parked probe head',(.310,y,1.038),(.067,.041,.033),p['white'],.011)
  box('Probe unlit dark contact face',(.310,y,1.057),(.053,.033,.008),p['screen'],.003)
  smooth_cable('Connected probe cable',[(.310,y,.881),(.350,y-.020,.757),(.362,y+.022,.466),(.326,y+.120,.375),(.257,y+.142,.510),(.230,y+.110,.718)],.006,p['rubber'])
  cyl('Probe side connection cap',(.229,y+.110,.718),.018,.024,p['dark'],'X',v=24,b=.002)
 rod('Cart rear push handle',(-.200,.294,.934),(.200,.294,.934),.020,p['dark'],28)
 for x in [-.190,.190]:rod('Push-handle bracket',(x,.221,.893),(x,.294,.934),.014,p['steel'],20)
 return ('city-ultrasound-equipment-cart','無表示の超音波装置カート','Ultrasound equipment cart with blank screen','診療施設の室内背景に置く移動式超音波装置外装。四輪台車・背面サービス部、文字のないキー/固定つまみ/トラックボール、角度を付けた無表示モニター、二本の保持プローブと曲線ケーブル、後部押し手を造形。画面は不透明PBRで画像・患者情報を含みません。画像取得、診断、音波・電気動作や医療機器安全性能は実装・検証していません。','A mobile ultrasound-system exterior for clinical interior backgrounds. It has a four-caster base/rear service area, unlettered keys/fixed controls/trackball, angled blank monitor, two parked probe exteriors with curved cables and rear push handle. The screen is opaque PBR and contains no imaging or patient data. Image capture, diagnosis, acoustic/electrical behavior and medical-device safety are not implemented or validated.',['clinical','ultrasound','equipment','超音波装置'])

def surgical_light():
 p=pal()
 for i in range(5):
  a=i*math.tau/5+.3;u=Vector((math.cos(a),math.sin(a),0));x,y=u.x*.406,u.y*.406;caster('Lamp base',x,y,.046,p)
  bar('Five-spoke mobile light base',u*.040+Vector((0,0,.163)),u*.406+Vector((0,0,.146)),.057,.048,p['white'],.008)
 cyl('Lamp base mast socket',(0,0,.213),.076,.152,p['white'],v=36,b=.009)
 cyl('Lamp lower vertical mast',(0,0,.877),.034,1.315,p['white'],v=32,b=.003)
 cyl('Lamp mast height collar',(0,0,1.494),.045,.104,p['dark'],v=32,b=.004)
 cyl('Lamp short upper mast',(0,0,1.640),.025,.220,p['steel'],v=28,b=.002)
 joints=[Vector((0,0,1.753)),Vector((0,-.414,2.077)),Vector((0,-.862,1.952))]
 for a,b in zip(joints,joints[1:]):
  for x in [-.039,.039]:bar('Parallel articulated light arm',a+Vector((x,0,0)),b+Vector((x,0,0)),.024,.041,p['white'],.005)
 for q in joints:cyl('Fixed lamp arm pivot',q,.051,.124,p['white'],'X',v=32,b=.004)
 center=Vector((0,-1.020,1.744));axis=Vector((0,-.400,-.9165)).normalized();u=Vector((1,0,0));v=axis.cross(u).normalized()
 rod('Light head supporting neck',joints[-1],center-axis*.088,.028,p['steel'],28)
 o=cyl('Mobile surgical light head shell',center,.318,.086,p['white'],v=48,b=.010);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 o=ring('Light head outer face seal',center+axis*.049,.297,.009,p['dark'],v=48);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 locs=[center]
 for i in range(6):
  a=i*math.tau/6;locs.append(center+.195*(u*math.cos(a)+v*math.sin(a)))
 for q in locs:
  o=cyl('Individual light lens surround',q+axis*.051,.078,.016,p['steel'],v=32,b=.003);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
  o=cyl('Opaque inactive light lens',q+axis*.061,.066,.008,p['lens'],v=32,b=.002);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 for side in [-1,1]:
  a=center+u*side*.310;b=center+u*side*.359+axis*.046;rod('Light head side handle bracket',a,b,.013,p['steel'],20)
  rod('Light head padded side handle',b-v*.073,b+v*.073,.018,p['white'],24)
 smooth_cable('Fixed mobile light supply cord',[(0,.031,.280),(.071,.097,.170),(.138,.217,.019),(.290,.305,.010),(.399,.258,.010),(.339,.158,.010),(.212,.177,.010),(.183,.282,.010),(.310,.391,.010)],.005,p['rubber'])
 box('Light supply plug',(.325,.409,.015),(.051,.033,.026),p['dark'],.004,rot=(0,0,.85))
 return ('city-mobile-surgical-light','移動式多灯手術灯外装','Mobile multi-lens surgical light exterior','診療・処置室の背景に置く移動式多灯照明外装。五本脚と車輪、伸縮支柱外形、平行リンク式の固定腕と軸、七つの個別レンズ面を持つ円形ヘッド、左右の把持部、曲線状の固定電源線を造形。レンズは不透明・非発光PBRで、スポット追尾灯とは異なる医療照明風の外観です。照度・電装・調整・医療安全性能を実装または検証した器具ではありません。','A mobile multi-lens light exterior for clinical treatment-room backgrounds. It has a five-spoke caster base, telescoping-style mast, fixed parallel-link arms/pivots, round head with seven individual lens faces, side handles and curved fixed power cord. Lenses are opaque non-emissive PBR surfaces; the medical-lighting exterior differs from a followspot. Illumination, electrical behavior, adjustment and medical-safety performance are not implemented or validated.',['clinical','lighting','equipment','手術灯'])

BUILDERS=[ward_bed,dental_chair,ultrasound_cart,surgical_light]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-049/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/clinical_room_equipment.py',azimuth=-55,elevation=27)
