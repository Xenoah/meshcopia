"""Original handheld facility-maintenance tools for Xenoah. CC BY 4.0.
Static scene geometry, not tool-making or operating specifications.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Satin forged tool steel',(.44,.49,.51),.76,.38),edge=mat('Bright machined surfaces',(.66,.70,.70),.82,.29),dark=mat('Dark steel and fittings',(.055,.069,.078),.45,.52),blue=mat('Muted blue enamel',(.055,.19,.29),.30,.45),wood=mat('Plain sealed wooden handle color',(.41,.25,.11),0,.65),rubber=mat('Matte rubber grip',(.018,.025,.028),0,.78),ivory=mat('Unbranded ivory cartridge',(.72,.73,.65),0,.48))
def cyl(n,p,r,d,m,axis='Z',v=28,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.002):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def plate(n,outline,z,t,m,bev=.001):
 k=len(outline);vs=[(x,y,zz) for zz in [z-t/2,z+t/2] for x,y in outline];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,bev)
def sideplate(n,outline,y,t,m,bev=.001):
 k=len(outline);vs=[(x,yy,z) for yy in [y-t/2,y+t/2] for x,z in outline];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,bev)
def bore(target,cutter):
 bpy.context.view_layer.objects.active=target
 for mod in list(target.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=target.modifiers.new('Actual through opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
def rebuild_normals(o):
 old=o.data;fresh=bpy.data.meshes.new(old.name+' triangulated geometric normals');fresh.from_pydata([tuple(v.co) for v in old.vertices],[],[tuple(f.vertices) for f in old.polygons]);fresh.update()
 for m in old.materials:fresh.materials.append(m)
 bm=bmesh.new();bm.from_mesh(fresh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(fresh);bm.free();o.data=fresh

def claw_hammer():
 p=palette()
 rows=[(-.180,.014,.011),(-.165,.019,.015),(-.130,.018,.015),(-.060,.014,.014),(.015,.012,.013),(.075,.012,.013),(.125,.010,.014)];n=24;vs=[(rx*math.cos(i*math.tau/n),y,.023+rz*math.sin(i*math.tau/n)) for y,rx,rz in rows for i in range(n)];fs=[tuple(reversed(range(n))),tuple(range((len(rows)-1)*n,len(rows)*n))]
 for j in range(len(rows)-1):
  for i in range(n):k=(i+1)%n;fs.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
 handle=mesh('Shaped wooden hammer handle',vs,fs,p['wood'],0,True)
 for face in handle.data.polygons[:2]:face.use_smooth=False
 box('Forged hammer head block',(0,.128,.027),(.065,.044,.045),p['steel'],.006)
 cyl('Hammer striking neck',(-.045,.128,.027),.016,.030,p['steel'],'X',32,.002)
 cyl('Circular striking face',(-.065,.128,.027),.025,.018,p['edge'],'X',40,.002)
 # Two thick, bent claws are separated by an actual central V gap.
 outline=[(.020,.046),(.043,.046),(.065,.039),(.084,.028),(.102,.010),(.107,.006),(.096,.008),(.076,.019),(.057,.025),(.020,.028)]
 for side in [-1,1]:sideplate('Split nail-pulling claw',outline,.128+side*.012,.015,p['steel'],.0015)
 box('Handle top end grain color',(0,.128,.051),(.020,.025,.004),p['wood'],.001)
 box('Handle retaining wedge',(0,.128,.054),(.003,.023,.003),p['dark'],.0004)
 return ('city-claw-hammer','釘抜き付きハンマー','Claw hammer','施設保守・大工作業台向けの片手ハンマー。木色の曲線柄、鍛造風ヘッド、円形の打撃面、実際に分かれた二股の曲がり爪、柄上端とくさびを造形。机上の平置き姿勢です。釘・材料・打撃や釘抜き動作は含まず、実用品の強度・性能・安全設計は未検証です。','A handheld hammer for facility-maintenance and carpentry workbenches, with shaped wood-colored handle, forged-looking head, circular striking face, genuinely split bent claw, handle end and retaining wedge. Presented in a tabletop resting pose. Nails, workpieces, striking and nail-pulling behavior are absent; real strength, performance and safety design are unvalidated.',['tool','hammer','maintenance','ハンマー'])

def adjustable_wrench():
 p=palette()
 body=plate('Adjustable wrench forged body',[(-.015,-.137),(-.019,-.120),(-.012,.035),(-.032,.061),(-.033,.095),(-.022,.115),(-.010,.113),(-.010,.078),(.018,.071),(.027,.045),(.010,.025),(.016,-.120),(.012,-.137)],.011,.019,p['steel'],.002)
 bore(body,box('Temporary real worm adjuster window',(.003,.052,.011),(.029,.022,.060),None,.001));bore(body,cyl('Temporary handle hanging bore',(0,-.119,.011),.007,.06,None,v=24,b=0));rebuild_normals(body)
 # Sliding jaw is parked open, with a real space between the flat gripping faces.
 plate('Movable wrench jaw',[(.009,.071),(.009,.108),(.020,.116),(.029,.109),(.029,.079),(.025,.067)],.011,.019,p['edge'],.0015)
 box('Fixed jaw gripping face',(-.009,.096,.011),(.003,.035,.018),p['edge'],.0005)
 box('Sliding jaw rack',(0,.065,.011),(.041,.009,.010),p['dark'],.0008)
 for i in range(9):box('Rack tooth',(-.016+i*.004,.060,.011),(.0025,.004,.010),p['edge'],.0003)
 cyl('Adjustment worm core',(.003,.052,.011),.008,.025,p['dark'],'X',28,.001)
 pts=[]
 for i in range(121):
  t=i/120;a=t*math.tau*6;pts.append((-.009+.024*t,.052+.0087*math.sin(a),.011+.0087*math.cos(a)))
 tube('Fixed worm adjustment thread',pts,.0015,p['edge'],1)
 for x in [-.013,.019]:cyl('Worm axle end',(x,.052,.011),.003,.005,p['steel'],'X',16,.0004)
 # A shallow raised forged rib is geometry, with no logo or calibrated scale.
 plate('Handle reinforcement rib',[(-.007,-.095),(.006,-.095),(.006,.020),(-.006,.024)],.022,.002,p['dark'],.0005)
 return ('city-adjustable-wrench','モンキーレンチ','Adjustable wrench','公共施設の保守工具棚や整備台に置く調整式レンチ。開いた固定顎と可動顎、ラック歯と固定したウォーム状調整ねじ、柄の補強面、実際に開いた吊下げ穴を造形。目盛や締結物はなく、一つの顎開度で固定されています。調整・締付け機能や実用品の強度・精度は未検証です。','An adjustable wrench for public-facility tool racks and maintenance benches, with separated fixed/sliding jaws, rack teeth, a fixed worm-like adjuster, raised handle rib and real hanging hole. No scale or fastener is included; the jaw remains at one opening. Adjustment, tightening, real strength and precision are unvalidated.',['tool','wrench','maintenance','レンチ'])

def hacksaw():
 p=palette()
 # Closed tubular arch with an open interior, not a filled silhouette.
 tube('Hacksaw bowed frame',[(-.18,0,.033),(-.19,.075,.033),(-.165,.115,.033),(.12,.115,.033),(.17,.085,.033),(.18,.015,.033)],.011,p['blue'],2)
 for x in [-.170,.170]:
  box('Blade end holder',(x,.006,.033),(.035,.033,.024),p['dark'],.003)
  cyl('Blade attachment pin',(x*.9705882353,-.005,.033),.004,.031,p['steel'],v=16,b=.0005)
 # Thin blade has a modeled sawtooth outline and two real mounting holes.
 tooth=[(-.170,.001),(.170,.001),(.170,-.013)]
 for i in range(55):
  x=.170-i*.0062;tooth.extend([(x-.0031,-.018),(x-.0062,-.013)])
 blade=plate('Static toothed hacksaw blade',tooth,.033,.0016,p['steel'],0)
 for x in [-.165,.165]:bore(blade,cyl('Temporary blade pin bore',(x,-.005,.033),.0024,.02,None,v=12,b=0))
 rebuild_normals(blade)
 # Separate pistol-like loop grip; the open loop is made from a continuous solid sweep.
 tube('Hacksaw rear handle loop',[(.174,.082,.033),(.224,.068,.033),(.246,.005,.033),(.220,-.063,.033),(.182,-.054,.033),(.179,.010,.033)],.015,p['rubber'],3)
 rod('Tension threaded shaft',(-.181,.006,.033),(-.223,.006,.033),.004,p['steel'],20)
 cyl('Tension nut',(-.225,.006,.033),.009,.010,p['dark'],'X',6,.0005)
 for side in [-1,1]:bar('Tension wing',(-.226,.006,.033),(-.226,.006+side*.024,.033),.007,.012,p['steel'],.001)
 for y in [-.029,-.012,.005,.022]:rod('Handle grip rib',(.235,y,.021),(.235,y,.045),.002,p['dark'],12)
 return ('city-frame-hacksaw','弓形の金切りのこ','Frame hacksaw','保守作業台や資材室向けの手動金切りのこ。開いた弓形フレーム、実形状の小さな歯を持つ薄い刃と取付穴、端の保持具、張力調整風のねじ・蝶形つまみ、開いた握りを造形。刃は固定され、切断物・切粉・切断動作はありません。実際の刃性能、張力や安全設計は未検証です。','A manual hacksaw for maintenance benches and stockrooms, with an open bowed frame, thin blade with modeled teeth and mounting holes, end holders, tension-adjuster exterior and wing grips, and open handle. The blade is fixed; workpieces, chips and cutting behavior are absent. Real blade performance, tension and safety design are unvalidated.',['tool','hacksaw','maintenance','金切りのこ'])

def caulking_gun():
 p=palette()
 # Tool lies on its side: cartridge axis runs along Y and trigger silhouette extends in X.
 c=(0,0,.034)
 cyl('Plain cartridge body',c,.025,.220,p['ivory'],'Y',40,.0015)
 for y in [-.111,.111]:cyl('Cartridge rolled end rim',(0,y,.034),.026,.005,p['steel'],'Y',32,.0007)
 for x in [-.030,.030]:bar('Open cartridge cradle rail',(x,-.120,.034),(x,.126,.034),.009,.012,p['blue'],.001)
 for y in [-.124,.128]:
  ring=torus('Open cradle end collar',(0,y,.034),.031,.005,p['blue'],rotation=(math.pi/2,0,0),segments=36)
 # Tapered hollow nozzle represented by an actual annular shell with a small open tip.
 seg=32;vs=[];rings=[]
 for r,y in [(.012,-.114),(.0035,-.185),(.0020,-.185),(.009,-.114)]:
  rings.append(list(range(len(vs),len(vs)+seg)));vs.extend((r*math.cos(i*math.tau/seg),y,.034+r*math.sin(i*math.tau/seg)) for i in range(seg))
 fs=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  for i in range(seg):j=(i+1)%seg;fs.append((a[i],b[i],b[j],a[j]))
 nozzle=mesh('Hollow tapered cartridge nozzle',vs,fs,p['ivory'],0,True);mod=nozzle.modifiers.new('Nozzle lip normals','EDGE_SPLIT');mod.split_angle=math.radians(30)
 box('Rear ratchet housing',(0,.143,.034),(.048,.032,.044),p['blue'],.004)
 rod('Plunger steel shaft',(0,.099,.034),(0,.254,.034),.004,p['steel'],20)
 tube('Plunger bent pull hook',[(0,.254,.034),(0,.279,.034),(.025,.285,.034),(.041,.269,.034)],.004,p['steel'],2)
 plate('Fixed caulking gun handle',[(.010,.164),(.022,.153),(.098,.233),(.098,.247),(.086,.252),(.078,.247)],.034,.022,p['blue'],.003)
 plate('Fixed squeeze trigger',[(.021,.124),(.033,.126),(.062,.173),(.061,.190),(.050,.190),(.037,.161)],.034,.015,p['steel'],.002)
 for x,y in [(.021,.141),(.026,.130)]:cyl('Trigger pivot fastening',(x,y,.048),.005,.005,p['dark'],v=16,b=.0005)
 plate('Ratchet release tab',[(-.018,.151),(-.035,.164),(-.031,.174),(-.011,.158)],.034,.010,p['dark'],.001)
 return ('city-cartridge-caulking-gun','カートリッジ式コーキングガン','Cartridge caulking gun','建物保守や内装工事の作業台向けの手動コーキングガン。無地カートリッジ、開いた保持枠、先端が開いた中空ノズル、押し棒と曲げた引手、固定した握り・トリガー・解放片を造形。横置きの一姿勢で、充填材、吐出、ラチェットやトリガー動作は含みません。実際の密封・施工性能は未検証です。','A manual caulking-gun prop for building-maintenance and interior-work benches, with unbranded cartridge, open cradle, hollow open-ended nozzle, plunger rod and bent pull hook, fixed grip, trigger and release tab. Presented on its side; sealant, dispensing, ratchet and trigger behavior are absent. Real sealing and application performance are unvalidated.',['tool','caulking','maintenance','コーキングガン'])
BUILDERS=[claw_hammer,adjustable_wrench,hacksaw,caulking_gun]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-032/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/workshop_hand_tools.py',azimuth=-55,elevation=55)
