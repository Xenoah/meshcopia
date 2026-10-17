"""Original construction-support appearance props for Xenoah. CC BY 4.0.
Generic forms for scenes only, not real equipment or construction instructions.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Galvanized-looking support steel',(.41,.47,.48),.78,.40),dark=mat('Dark coated structure',(.055,.068,.075),.4,.55),yellow=mat('Ochre site enamel',(.61,.33,.045),.25,.48),blue=mat('Blue formwork frame',(.065,.20,.30),.30,.45),wood=mat('Plain sealed form-facing plywood',(.32,.20,.11),0,.72),black=mat('Dark recess and rubber',(.014,.020,.023),0,.80),red=mat('Red latch accents',(.42,.045,.026),.2,.45))
def cyl(n,p,r,d,m,axis='Z',v=28,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,d,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def hexbolt(n,p,m,axis='Z',r=.008):
 cyl(n+' washer',p,r*1.6,.0025,m,axis,16,0);q=list(p);q['XYZ'.index(axis)]+=.004;cyl(n+' head',q,r,.007,m,axis,6,.0004)
def ring(n,p,r,t,m,axis='Z',segments=36):return torus(n,p,r,t,m,rotation=(0,math.pi/2,0) if axis=='X' else ((math.pi/2,0,0) if axis=='Y' else None),segments=segments)
def loft(n,profile,m,segments=48):
 vs=[];rings=[]
 for radius,z in profile:
  if radius==0:rings.append([len(vs)]);vs.append((0,0,z))
  else:rings.append(list(range(len(vs),len(vs)+segments)));vs.extend((radius*math.cos(i*math.tau/segments),radius*math.sin(i*math.tau/segments),z) for i in range(segments))
 fs=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  if len(a)==1 and len(b)==1:continue
  for i in range(segments):
   j=(i+1)%segments
   if len(a)==1:fs.append((a[0],b[i],b[j]))
   elif len(b)==1:fs.append((a[i],b[0],a[j]))
   else:fs.append((a[i],b[i],b[j],a[j]))
 o=mesh(n,vs,fs,m,0,True);mod=o.modifiers.new('Hard profile transitions','EDGE_SPLIT');mod.use_edge_angle=True;mod.use_edge_sharp=False;mod.split_angle=math.radians(25);return o
def chain_ring(n,p,r,t,m,axis):
 bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=6,major_radius=r,minor_radius=t,location=p);o=bpy.context.object;o.rotation_euler=(0,math.pi/2,0) if axis=='X' else (math.pi/2,0,0);return finish(o,n,m,0,True)
def geometric_normals(o):
 old=o.data;fresh=bpy.data.meshes.new(old.name+' outward faceted bores');fresh.from_pydata([tuple(v.co) for v in old.vertices],[],[tuple(f.vertices) for f in old.polygons]);fresh.update()
 for m in old.materials:fresh.materials.append(m)
 o.data=fresh
def subtract(target,cutter):
 bpy.context.view_layer.objects.active=target
 for modifier in list(target.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
 mod=target.modifiers.new('Actual open hole','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
def prop():
 p=palette()
 bottom=box('Prop bottom plate',(0,0,.012),(.23,.23,.024),p['steel'],.004)
 top=box('Prop top plate',(0,0,2.23),(.23,.23,.024),p['steel'],.004)
 # Plate bolt openings are real holes, not colored discs.
 for plate,z in [(bottom,.012),(top,2.23)]:
  for x in [-.077,.077]:
   for y in [-.077,.077]:subtract(plate,cyl('temporary plate bore',(x,y,z),.012,.07,None,v=20,b=0))
 lower=cyl('Outer prop tube',(0,0,.675),.045,1.30,p['yellow'],v=40,b=.002)
 upper=cyl('Upper perforated prop tube',(0,0,1.62),.034,1.198,p['steel'],v=40,b=.0015)
 for z in [1.40,1.52,1.64,1.76,1.88,2.00,2.12]:subtract(upper,cyl('temporary height pin bore',(0,0,z),.009,.11,None,'Y',20,0))
 for o in [bottom,top,upper]:geometric_normals(o)
 # Fine helical collar appearance is explicit geometry, not a working thread.
 pts=[]
 for i in range(141):
  t=i/140;a=t*math.tau*5;pts.append((.047*math.cos(a),.047*math.sin(a),1.175+.15*t))
 tube('Visible adjustment thread',pts,.004,p['steel'],1)
 cyl('Adjustment collar',(0,0,1.23),.064,.058,p['dark'],v=32,b=.004)
 rod('Collar turning handle',(-.145,0,1.23),(.145,0,1.23),.011,p['steel'],20)
 for x in [-.145,.145]:cyl('Handle grip cap',(x,0,1.23),.018,.025,p['black'],'X',20,.002)
 rod('Height locking pin',(0,-.075,1.40),(0,.075,1.40),.008,p['dark'],20)
 ring('Pin retaining loop',(0,-.093,1.40),.025,.004,p['dark'],'Y',28)
 for i in range(7):
  z=1.36-i*.021;chain_ring('Short captive pin chain',(.045,-.055,z),.011,.0022,p['steel'],'X' if i%2 else 'Y')
 box('Chain collar anchor',(.038,-.043,1.21),(.02,.025,.02),p['steel'],.002)
 for x in [-.055,.055]:bar('Lower plate gusset',(x,0,.025),(x*.6,0,.13),.04,.012,p['yellow'])
 return ('city-adjustable-steel-prop','伸縮式の鋼製サポート支柱','Adjustable steel support prop','工事中の建物や資材置場の背景に配置する伸縮式支柱。実際に開いた高さピン穴と上下板の穴、外筒・内筒、ねじ状の調整部、回転ハンドル、固定ピンと短い脱落防止鎖を造形。床・上部荷重・支保工全体、伸縮・回転は含みません。荷重・座屈・固定や施工条件を検証した実用品設計ではありません。','A telescopic support-prop exterior for construction interiors and storage yards, with real height-pin and plate openings, inner/outer tubes, thread-like adjustment detail, turning handle, locking pin and short captive chain. Floor, supported load, complete shoring system and motion are absent. This is not a real design validated for loading, buckling, anchorage or construction conditions.',['construction','prop','shoring','支柱'])
def formwork():
 p=palette();w=.90;h=1.80
 box('Unmarked sealed plywood form face',(0,-.020,h/2),(w-.065,.027,h-.065),p['wood'],.003)
 for x in [-w/2+.020,w/2-.020]:box('Formwork vertical perimeter',(x,.023,h/2),(.040,.095,h),p['blue'],.004)
 for z in [.020,h-.020]:box('Formwork horizontal perimeter',(0,.023,z),(w-.078,.090,.039),p['blue'],.004)
 for z in [.30,.70,1.10,1.50]:
  box('Rear horizontal stiffener',(0,.054,z),(w-.070,.055,.060),p['blue'],.004)
  for x in [-.36,.36]:hexbolt('Stiffener frame fastening',(x,.085,z),p['steel'],'Y',.006)
 for x in [-.21,.21]:box('Rear vertical stiffener',(x,.045,.90),(.035,.045,h-.08),p['blue'],.003)
 # Exposed edge tie brackets with true open eyes, made as thick annuli.
 for x in [-.485,.485]:
  for z in [.42,1.38]:
   bar('Tie bracket web',(x*.89,.026,z),(x,.026,z),.032,.055,p['steel'])
   ring('Open tie attachment eye',(x,.026,z),.025,.008,p['steel'],'X',28)
 for x in [-.20,.20]:
  box('Handle backing crosspiece',(x,.031,.88),(.21,.077,.045),p['blue'],.003)
  tube('Rear lifting handgrip',[(x-.075,.08,.88),(x-.075,.145,.88),(x+.075,.145,.88),(x+.075,.08,.88)],.012,p['steel'],2)
  for xx in [x-.075,x+.075]:box('Handle mounting saddle',(xx,.075,.88),(.032,.025,.055),p['steel'],.003)
 for x in [-.35,0,.35]:
  for z in [.09,1.71]:cyl('Recessed front fastener',(x,-.035,z),.006,.004,p['steel'],'Y',12,0)
 return ('city-framed-wall-formwork-panel','枠付きの壁型枠パネル','Framed wall-formwork panel','建設現場や資材置場向けの一枚型枠パネル。無地の合板調表面、金属の外枠、背面の縦横補強、持ち手、開口した連結金具と留め具を造形。壁・コンクリート・支柱・対向パネルや完成した型枠系統は含みません。単体の立て置き用原点で、支持と配置はシーン側で調整してください。耐圧・緊結・施工安全は未検証。','A single framed formwork panel for construction and storage-yard scenes, with plain plywood-like facing, metal perimeter, rear grid stiffeners, handgrips, open connection eyes and fasteners. Wall, concrete, braces, opposing panel and a complete formwork system are absent. Its base origin supports upright scene placement; supply visual supports in the host scene. Pressure resistance, fastening and construction safety are unvalidated.',['construction','formwork','panel','型枠'])
def debris_chute():
 p=palette()
 # Three overlapping flared shells form one complete short chute assembly.
 for i in range(3):
  z=i*.56
  loft('Open tapered debris chute shell',[(.225,z),(.235,z),(.305,z+.61),(.292,z+.61)],p['yellow'],48)
  ring('Chute segment rim',(0,0,z+.605),.298,.012,p['dark'],segments=48)
  for side in [-1,1]:
   box('Segment suspension tab',(side*.285,0,z+.49),(.055,.060,.080),p['steel'],.006)
   ring('Suspension eye',(side*.310,0,z+.49),.022,.005,p['steel'],'Y',24)
 # Wide top hopper is open and unbranded; throat aligns with chute, no sealed disc.
 loft('Receiving hopper shell',[(.290,1.67),(.307,1.67),(.48,1.99),(.48,2.12),(.463,2.12),(.463,1.995)],p['yellow'],56)
 ring('Hopper rolled edge',(0,0,2.115),.472,.014,p['dark'],segments=56)
 # Two suspension runs of linked geometry, modest density.
 for side in [-1,1]:
  for i in range(31):
   z=.50+i*.054;chain_ring('Suspension chain link',(side*.335,0,z),.030,.004,p['steel'],'X' if i%2 else 'Y')
  bar('Upper mounting crossbeam',(side*.335,-.06,2.18),(side*.335,.40,2.18),.055,.055,p['dark'])
  box('Wall mounting plate',(side*.335,.42,2.18),(.12,.03,.25),p['steel'],.005)
  for z in [2.10,2.26]:hexbolt('Mounting plate bolt',(side*.335,.438,z),p['dark'],'Y',.009)
  rod('Diagonal mounting brace',(side*.335,.40,2.07),(side*.335,-.03,2.18),.015,p['steel'],20)
 return ('city-suspended-rubble-chute','吊下げ式の瓦礫シュート','Suspended rubble chute assembly','改修工事の外壁に配置する短い瓦礫排出シュート。三段の重なり合う中空筒、開いた上部ホッパー、吊り金具と実形状の鎖、壁側取付フレームをまとめた一組です。建物・受け容器・瓦礫や落下動作は含まず、取付高さ・壁離れをシーンで調整してください。耐荷重・粉じん・落下物や施工安全を検証した実用品ではありません。','A short debris-chute assembly for renovation facades, combining three overlapping hollow tapered sections, an open receiving hopper, suspension eyes, modeled chain links and wall-side support frame. Building, receiving bin, debris and falling behavior are absent; adjust installation height and wall offset in the scene. This is not real equipment validated for loads, dust, falling objects or construction safety.',['construction','chute','renovation','瓦礫シュート'])
def concrete_skip():
 p=palette()
 # Thick open hopper slopes toward the outlet, supported by a real cage.
 loft('Concrete skip hopper',[(.105,.30),(.125,.30),(.46,.91),(.46,1.23),(.443,1.23),(.443,.918),(.105,.325)],p['blue'],56)
 ring('Hopper rim',(0,0,1.225),.452,.014,p['steel'],segments=56)
 for x in [-.32,.32]:
  for y in [-.32,.32]:
   bar('Skip cage leg',(x,y,.03),(x,y,.87),.040,.040,p['dark'])
   box('Skip base shoe',(x,y,.015),(.14,.14,.03),p['steel'],.004)
  bar('Skip lower rail',(x,-.32,.19),(x,.32,.19),.035,.035,p['dark'])
 for y in [-.32,.32]:bar('Skip lower crossbar',(-.32,y,.19),(.32,y,.19),.035,.035,p['dark'])
 for side in [-1,1]:
  bar('Lifting bail upright',(side*.43,0,.84),(side*.43,0,1.58),.045,.040,p['steel'])
  cyl('Bail pivot',(side*.45,0,.85),.055,.050,p['steel'],'X',28,.003)
  bar('Cage diagonal brace',(side*.32,-.32,.20),(side*.32,.32,.83),.025,.025,p['dark'])
  hexbolt('Bail pivot bolt',(side*.485,0,.85),p['dark'],'X',.016)
 bar('Lifting bail upper bridge',(-.43,0,1.58),(.43,0,1.58),.045,.040,p['steel'])
 ring('Lifting eye',(0,0,1.64),.065,.014,p['steel'],'Y',36)
 # Outlet with a closed slide gate, visible tracks and an operating-link exterior.
 box('Outlet rectangular collar',(0,0,.285),(.245,.235,.085),p['steel'],.005)
 box('Closed discharge gate',(0,-.03,.238),(.27,.30,.014),p['dark'],.003)
 for x in [-.145,.145]:box('Discharge gate guide',(x,-.035,.247),(.025,.32,.038),p['steel'],.003)
 rod('Gate actuator link',(0,-.17,.24),(0,-.40,.49),.012,p['steel'],20)
 cyl('Gate lever pivot',(0,-.40,.49),.026,.11,p['dark'],'X',24,.002)
 rod('Gate operating lever',(0,-.40,.49),(0,-.51,.92),.016,p['steel'],24)
 rod('Lever handgrip',(-.09,-.51,.92),(.09,-.51,.92),.023,p['black'],24)
 bar('Lever pivot support',(-.055,-.32,.49),(-.055,-.40,.49),.027,.028,p['dark'])
 box('Lever latch tab',(0,-.46,.73),(.05,.06,.035),p['red'],.004)
 return ('city-concrete-pouring-skip','コンクリート打設用ホッパー','Concrete pouring skip hopper','建設現場の荷役場面に置く打設用ホッパー外観。厚みのある開いた受け槽、脚付き支持枠、持上げ枠と吊り環、閉じた排出ゲート・ガイド・レバーを造形。ミキサーではなく、材料を受けて排出する容器の静的プロップです。コンクリート・クレーン・吊り索や排出動作はなく、揚重・耐荷重・打設性能や施工安全は未検証。','A pouring-skip exterior for construction lifting scenes, with a thick open hopper, footed support cage, lifting bail/eye, closed discharge gate, guides and lever. Unlike a mixer, this static prop represents a receiving and dispensing container. Concrete, crane, lifting sling and discharge behavior are absent; lifting, load, pouring performance and construction safety are unvalidated.',['construction','hopper','skip','concrete','打設ホッパー'])
BUILDERS=[prop,formwork,debris_chute,concrete_skip]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-023/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/construction_support.py',azimuth=-55,elevation=24)
