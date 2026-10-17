"""Original portable workshop power-tool props. Xenoah, CC BY 4.0.
Static visualization; no brands, operating behavior or manufacturing dimensions.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def pal():
 return dict(teal=mat('Muted teal molded tool body',(.045,.26,.27),.06,.43),dark=mat('Graphite tool overmold',(.025,.035,.040),0,.65),rubber=mat('Soft black grip rubber',(.014,.019,.021),0,.78),steel=mat('Satin tool steel',(.42,.47,.48),.78,.35),bright=mat('Bright cutting metal appearance',(.66,.70,.70),.82,.28),orange=mat('Unbranded orange controls',(.71,.21,.035),.03,.45),black=mat('Dark recess and fasteners',(.025,.030,.035),.35,.55),disc=mat('Plain abrasive wheel',(.10,.12,.125),.05,.84))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.002):
 a,bp=Vector(a),Vector(b);o=box(n,(a+bp)/2,(w,t,(bp-a).length),m,bev);o.rotation_euler=(bp-a).to_track_quat('Z','Y').to_euler();return o
def sideplate(n,pts,x,t,m,bev=.001):
 k=len(pts);vs=[(xx,y,z) for xx in [x-t/2,x+t/2] for y,z in pts];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,bev)
def ring(n,p,r,t,m,axis='Z',v=40):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)
def battery(p,center,w=.075,d=.102,h=.043):
 x,y,z=center;box('Shared generic slide-in battery housing',center,(w,d,h),p['dark'],.006)
 box('Battery base impact rail',(x,y,z-h*.43),(w+.004,d+.003,.010),p['rubber'],.003)
 for xx in [-1,1]:box('Battery release latch',(x+xx*(w/2+.001),y-.018,z+.007),(.009,.032,.015),p['orange'],.002)
 for i in range(3):box('Recessed battery charge bar',(x-.020+i*.020,y-d/2-.001,z+.005),(.012,.002,.005),p['black'],.0005)
 for xx in [-w*.32,w*.32]:box('Battery sliding top rail',(x+xx,y,z+h/2+.003),(.010,d*.72,.010),p['teal'],.002)

def cordless_drill():
 p=pal();battery(p,(0,.038,.029))
 bar('Slanted drill handle',(0,.053,.061),(0,.014,.214),.049,.052,p['teal'],.009)
 bar('Rear handle rubber overmold',(0,.074,.075),(0,.036,.191),.042,.018,p['rubber'],.006)
 for z in [.092,.116,.140,.164]:box('Handle transverse grip rib',(0,.063-(z-.092)*.25,z),(.043,.008,.006),p['dark'],.0015)
 cyl('Drill motor main shell',(0,.016,.240),.045,.160,p['teal'],'Y',v=40,b=.004)
 cyl('Drill rear motor cap',(0,.104,.240),.044,.024,p['dark'],'Y',v=40,b=.003)
 for i in range(7):box('Rear motor vent slot',((i-3)*.010,.118,.240),(.004,.005,.041),p['black'],.0008)
 cyl('Gear collar',(0,-.075,.240),.040,.032,p['dark'],'Y',v=40,b=.002)
 for i in range(12):
  a=i*math.tau/12;box('Clutch collar grip tooth',(.039*math.cos(a),-.075,.240+.039*math.sin(a)),(.008,.023,.007),p['teal'],.0015,rot=(0,a,0))
 cyl('Keyless chuck sleeve',(0,-.110,.240),.027,.044,p['black'],'Y',v=40,b=.002)
 cyl('Chuck metal nose',(0,-.138,.240),.021,.014,p['steel'],'Y',v=32,b=.001)
 for i in range(3):
  a=i*math.tau/3;box('Three fixed chuck jaws',(.009*math.cos(a),-.148,.240+.009*math.sin(a)),(.006,.017,.006),p['bright'],.0008,rot=(0,a,0))
 cyl('Fixed drill-bit core',(0,-.190,.240),.0033,.095,p['steel'],'Y',v=20,b=0)
 for phase in [0,math.pi]:
  pts=[]
  for i in range(81):t=i/80;a=t*math.tau*3+phase;pts.append((.0038*math.cos(a),-.158-.070*t,.240+.0038*math.sin(a)))
  tube('Static helical drill-bit ridge',pts,.001,p['bright'],0)
 # Small taper at the end is appearance geometry, not a working cutting specification.
 bpy.ops.mesh.primitive_cone_add(vertices=20,radius1=.0033,radius2=0,depth=.006,location=(0,-.240,.240),rotation=(math.pi/2,0,0));finish(bpy.context.object,'Drill-bit pointed end',p['bright'],smooth=True)
 box('Fixed drill trigger',(0,-.012,.196),(.031,.021,.035),p['orange'],.004)
 box('Forward reverse switch',(0,.000,.218),(.063,.019,.013),p['dark'],.003)
 box('Top speed selector',(0,.019,.286),(.026,.035,.007),p['orange'],.002)
 for x in [-.045,.045]:
  for y in [-.018,.065]:cyl('Motor casing fastener',(x,y,.240),.004,.004,p['steel'],'X',v=12,b=.0005)
 sideplate('Belt hook',[(-.003,.063),(-.003,.034),(.027,.034),(.027,.040),(.004,.040),(.004,.063)],.048,.005,p['steel'],.001)
 return ('city-cordless-drill','コードレスドリル','Cordless drill','施設保守や内装作業台向けの携帯ドリル。傾斜した握り、着脱式風の固定バッテリー、前後の操作部、通気部、チャックと三つの固定爪、細いねじれ形状のビット、ベルトフックを造形。バッテリー上で立つ姿勢です。据置ボール盤とは異なる手持ち工具で、ビット・バッテリーを含め一式1点です。回転・穴あけ・電池・調整動作や実用品安全性は未検証です。','A portable drill for facility-maintenance and interior-work benches, with slanted grip, fixed slide-in-style battery, controls, vents, chuck with three static jaws, narrow helical bit and belt hook. Presented standing on the battery. Unlike a floor drill press, it is a handheld assembly; bit and battery count within one model. Rotation, drilling, battery operation, adjustment and real tool safety are unvalidated.',['tool','drill','maintenance','ドリル'])

def angle_grinder():
 p=pal()
 cyl('Grinder main motor shell',(0,.080,.069),.040,.187,p['teal'],'Y',v=40,b=.004)
 cyl('Grinder rear hand grip',(0,.225,.069),.031,.130,p['rubber'],'Y',v=36,b=.003)
 cyl('Rear tool end cap',(0,.295,.069),.029,.018,p['dark'],'Y',v=32,b=.002)
 box('Rear parked support rib',(0,.260,.025),(.052,.054,.022),p['dark'],.003)
 for i in range(6):box('Motor side vent slit',(.039,.036+i*.018,.070),(.004,.010,.019),p['black'],.001)
 box('Fixed sliding power switch',(0,.088,.112),(.022,.043,.009),p['orange'],.003)
 box('Angled metal gear head',(0,-.047,.071),(.081,.071,.068),p['steel'],.010)
 cyl('Disc axle hub',(.050,-.067,.069),.020,.041,p['steel'],'X',v=32,b=.002)
 cyl('Abrasive grinding disc',(.075,-.067,.069),.063,.006,p['disc'],'X',v=64,b=.0004)
 cyl('Disc clamping flange',(.082,-.067,.069),.016,.010,p['steel'],'X',v=32,b=.001)
 for a in [0,math.pi]:cyl('Flange pin recess',(.088,-.067+.009*math.cos(a),.069+.009*math.sin(a)),.002,.002,p['black'],'X',v=12,b=0)
 # Curved protective shroud wraps the rear half of the wheel, with an open working half.
 n=28;vs=[]
 for x,r in [(.063,.070),(.084,.070),(.084,.066),(.063,.066)]:
  vs.extend((x,-.067+r*math.cos(-.15+i*(math.pi+.30)/n),.069+r*math.sin(-.15+i*(math.pi+.30)/n)) for i in range(n+1))
 fs=[]
 for k in range(4):
  for i in range(n):fs.append((k*(n+1)+i,k*(n+1)+i+1,((k+1)%4)*(n+1)+i+1,((k+1)%4)*(n+1)+i))
 fs.extend([(0,n+1,2*(n+1),3*(n+1)),(n,4*n+3,3*n+2,2*n+1)]);guard=mesh('Partial grinder wheel safety-guard exterior',vs,fs,p['dark'])
 for face in guard.data.polygons:
  face.use_smooth=face.index<n or 2*n<=face.index<3*n
 ring('Guard neck clamp',(.042,-.067,.069),.027,.004,p['dark'],'X',40)
 cyl('Auxiliary grip threaded-looking collar',(-.057,-.038,.078),.014,.033,p['steel'],'X',v=24,b=.001)
 cyl('Side auxiliary hand grip',(-.115,-.038,.078),.023,.092,p['rubber'],'X',v=32,b=.004)
 cyl('Auxiliary grip end stop',(-.165,-.038,.078),.025,.012,p['dark'],'X',v=28,b=.002)
 for x in [-.139,-.118,-.097]:ring('Auxiliary handle grip rib',(x,-.038,.078),.023,.002,p['dark'],'X',24)
 for x in [-.033,.033]:cyl('Gear head cover fastening',(x,-.067,.106),.004,.006,p['black'],v=12,b=.0006)
 return ('city-handheld-angle-grinder','手持ちアングルグラインダー','Handheld angle grinder','金属保守作業台に横置きする携帯研削工具。長いモーター胴、後方握り、横の補助ハンドル、直角ギア部、固定研削円盤と締付フランジ、作業側を開けた半周ガード、通気部とスイッチを造形。据置両頭グラインダーとは異なる手持ち姿勢です。円盤・補助握りを含む一式1点で、回転・研削・電装・ガード調整は実装せず、保護性能や実用品安全性は未検証です。','A portable grinding-tool prop resting on a maintenance bench, with long motor body, rear grip, side auxiliary handle, right-angle gear head, fixed abrasive wheel and clamping flange, half-wrap guard exposing the working side, vents and switch. It differs from a stationary double-wheel bench grinder. Disc and auxiliary grip belong to one assembly. Rotation, grinding, electrical operation and guard adjustment are absent; protective performance and real tool safety are unvalidated.',['tool','grinder','maintenance','グラインダー'])

def circular_saw():
 p=pal()
 # One closed annular shoe prevents coplanar crossing plates at its corners.
 vs=[]
 for w,d,z,cx,cy in [(.216,.348,.0065,.006,-.011),(.216,.348,.0155,.006,-.011),(.018,.220,.0155,.031,-.025),(.018,.220,.0065,.031,-.025)]:
  vs.extend([(cx-w/2,cy-d/2,z),(cx+w/2,cy-d/2,z),(cx+w/2,cy+d/2,z),(cx-w/2,cy+d/2,z)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)]
 shoe=mesh('One-piece shoe with actual blade slot',vs,fs,p['steel'],.001)
 for mod in shoe.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 # A static shallow blade pose is set within the shoe; teeth are actual outline geometry.
 pts=[]
 for i in range(48):
  a=i*math.tau/48
  for da,r in [(0,.087),(.038,.091),(.070,.087)]:pts.append((-.025+r*math.cos(a+da),.105+r*math.sin(a+da)))
 sideplate('Fixed toothed circular saw blade',pts,.031,.0025,p['bright'],0)
 cyl('Circular saw arbor',(.037,-.025,.105),.017,.015,p['steel'],'X',v=32,b=.001)
 cyl('Arbor retaining nut',(.047,-.025,.105),.010,.006,p['black'],'X',v=6,b=.0006)
 # Broad upper guard is an annular extruded half shell; lower retracting guard is fixed.
 def guard(name,a0,a1,r0,r1,x,t,material):
  n=36;prof=[(-.025+r1*math.cos(a0+(a1-a0)*i/n),.105+r1*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)]+[(-.025+r0*math.cos(a0+(a1-a0)*i/n),.105+r0*math.sin(a0+(a1-a0)*i/n)) for i in range(n,-1,-1)];o=sideplate(name,prof,x,t,material,.0007)
  for face in o.data.polygons:
   if 2<=face.index<2+n or 3+n<=face.index<3+2*n:face.use_smooth=True
  return o
 guard('Upper circular saw blade guard',0,math.pi,.093,.103,.022,.035,p['teal'])
 guard('Fixed lower retracting blade guard',math.pi,math.tau,.091,.097,.027,.021,p['steel'])
 box('Guard upper stiffening ridge',(.022,-.025,.207),(.033,.100,.014),p['teal'],.004)
 cyl('Saw transverse motor body',(-.052,-.020,.119),.047,.145,p['teal'],'X',v=40,b=.005)
 cyl('Saw motor outer vent cap',(-.128,-.020,.119),.046,.018,p['dark'],'X',v=36,b=.003)
 for z in [.092,.106,.120,.134,.148]:box('Motor cap recessed vent',(-.139,-.020,z),(.004,.052,.005),p['black'],.0008)
 box('Main handle supporting rear motor housing',(-.052,.070,.126),(.100,.100,.060),p['teal'],.010)
 tube('Saw main handle loop',[(-.056,.025,.162),(-.056,.049,.256),(-.056,.148,.265),(-.056,.166,.212),(-.056,.128,.154)],.019,p['dark'],2)
 tube('Raised main grip overmold',[(-.056,.059,.258),(-.056,.136,.265)],.021,p['rubber'],2)
 box('Fixed saw trigger',(-.056,.104,.239),(.023,.047,.013),p['orange'],.003)
 cyl('Forward saw stabilizing knob',(-.048,-.120,.188),.026,.041,p['rubber'],v=32,b=.004)
 bar('Front stabilizing knob support bracket',(-.048,-.050,.145),(-.048,-.120,.158),.025,.028,p['teal'],.004)
 rod('Front knob support',(-.048,-.120,.151),(-.048,-.120,.178),.012,p['steel'])
 for y in [-.132,.116]:
  bar('Shoe height support bracket',(-.016,y,.018),(-.016,y,.085),.035,.018,p['steel'],.002)
  cyl('Shoe bevel pivot',(.003,y,.042),.011,.035,p['black'],'X',v=24,b=.001)
 box('Fixed depth lever',(-.037,.143,.087),(.065,.017,.012),p['orange'],.003,rot=(0,math.radians(-20),0))
 box('Lower guard parked lever',(.058,.044,.088),(.018,.057,.012),p['orange'],.003,rot=(math.radians(-20),0,0))
 return ('city-handheld-circular-saw','手持ち丸のこ','Handheld circular saw','建築保守・木工作業台向けの携帯丸のこ。実スロット付きの靴板、固定した歯付き円形刃、上部・下部ガード、横向きモーター、開いた主ハンドルと前方つまみ、支持金具と固定調整レバーを造形。刃は浅い固定姿勢で、材料や切粉はありません。既存据置タイルソーと異なる木工作業用の手持ち外形で、一式1点です。切断・回転・ガード退避・調整や実用品安全性は未検証です。','A portable circular-saw prop for building-maintenance and woodworking benches, with genuinely slotted shoe, fixed toothed circular blade, upper/lower guard exteriors, transverse motor, open main handle and front knob, supports and static adjustment levers. The blade is in one shallow fixed pose; no workpiece or chips are included. Its handheld woodworking form differs from the existing stationary tile saw; the complete tool counts once. Cutting, rotation, guard retraction, adjustment and real equipment safety are unvalidated.',['tool','circular-saw','maintenance','丸のこ'])

def reciprocating_saw():
 p=pal();battery(p,(0,.267,.030),.083,.100,.047)
 cyl('Reciprocating saw motor shell',(0,.036,.118),.041,.227,p['teal'],'Y',v=40,b=.005)
 cyl('Front grip rubber bellows',(0,-.105,.118),.035,.085,p['rubber'],'Y',v=32,b=.003)
 for y in [-.137,-.119,-.101,-.083]:ring('Bellows molded ridge',(0,y,.118),.035,.0028,p['dark'],'Y',32)
 # Open D handle joins the motor and battery heel; no detached floating trigger.
 tube('Open reciprocating saw rear handle',[(0,.126,.142),(0,.202,.189),(0,.283,.164),(0,.287,.080),(0,.204,.063),(0,.119,.096)],.021,p['dark'],2)
 bar('Rear handle rubber grip',(0,.280,.084),(0,.280,.160),.045,.043,p['rubber'],.009)
 box('Fixed trigger inside handle',(0,.246,.122),(.030,.022,.045),p['orange'],.004)
 box('Handle lock button',(.025,.267,.161),(.013,.027,.013),p['orange'],.003)
 for x in [-.041,.041]:
  for y in [.012,.039,.066,.093]:box('Motor side vent recess',(x,y,.119),(.004,.014,.032),p['black'],.001)
 cyl('Front blade clamp collar',(0,-.155,.118),.021,.027,p['steel'],'Y',v=32,b=.002)
 box('Fixed blade release lever',(.029,-.155,.120),(.020,.028,.009),p['orange'],.002)
 # Shoe is a real thick rectangular ring; central slot remains open around the blade.
 for x in [-.029,.029]:box('Saw shoe side cheek',(x,-.183,.116),(.010,.014,.085),p['steel'],.002)
 for z in [.076,.156]:box('Saw shoe cross edge',(0,-.183,z),(.053,.014,.010),p['steel'],.002)
 for x in [-.018,.018]:rod('Shoe supporting slide rod',(x,-.139,.150),(x,-.179,.150),.005,p['steel'],16)
 # Thin reciprocating blade, with a toothed lower edge and rounded-looking tip profile.
 pts=[(-.161,.126),(-.333,.126),(-.351,.116),(-.351,.098)]
 for i in range(25):y=-.351+i*.0076;pts.extend([(y+.0038,.093),(y+.0076,.099)])
 sideplate('Fixed toothed reciprocating blade',pts,0,.0025,p['bright'],0)
 for x in [-.039,.039]:cyl('Front casing screw',(x,-.060,.118),.004,.004,p['steel'],'X',v=12,b=.0005)
 box('Parked nose support pad',(0,-.079,.069),(.039,.037,.022),p['dark'],.003)
 return ('city-reciprocating-saw','バッテリー式レシプロソー','Battery reciprocating saw','建物保守や改修作業台向けの携帯往復のこ。長いモーター胴、前方のゴム状握り、実際に開いたD型ハンドル、固定トリガーとバッテリー、クランプ、実スロット付き靴板、実形状の歯を持つ薄い直線刃を造形。丸刃の機械とは切断部と保持構造が異なり、刃と電池を含む一式1点です。往復・切断・靴板調整・電池動作は未実装で、刃性能や実用品安全性は未検証です。','A portable reciprocating-saw prop for building-maintenance and refurbishment benches. It has a long motor housing, front rubber-like grip, genuinely open D handle, fixed trigger and battery, clamp, slotted shoe and thin straight blade with modeled teeth. Cutting and holding structures differ from a circular-blade tool; blade and battery are part of one assembly. Reciprocation, cutting, shoe adjustment and battery behavior are absent; blade performance and real equipment safety are unvalidated.',['tool','reciprocating-saw','maintenance','レシプロソー'])
BUILDERS=[cordless_drill,angle_grinder,circular_saw,reciprocating_saw]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-036/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/portable_power_tools.py',azimuth=-55,elevation=28)
