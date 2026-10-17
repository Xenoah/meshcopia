"""Original four public sports-room prop assemblies. Xenoah, CC BY 4.0.
Procedural geometry and plain materials only; no external art, brands or models.
All straps, weights, targets, bars and mats are fixed parts, not separate assets.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(frame=mat('Powder-coated graphite steel',(.065,.085,.095),.30,.45),steel=mat('Satin small metal fittings',(.44,.49,.53),.72,.34),white=mat('Warm light frame coating',(.72,.75,.72),.18,.43),rubber=mat('Dark rubber foot pads',(.018,.023,.027),0,.74),red=mat('Muted oxblood upholstered bag',(.40,.055,.038),0,.56),seam=mat('Dark stitched edge piping',(.075,.038,.030),0,.65),tan=mat('Plain warm ring wood',(.52,.32,.14),0,.49),web=mat('Dark woven strap appearance',(.075,.082,.067),0,.81),wood=mat('Plain golden frame wood',(.38,.245,.12),0,.58),target=mat('Warm target backing fiber color',(.55,.43,.27),0,.84),ivory=mat('Target cream outer face',(.80,.78,.64),0,.76),blue=mat('Target blue green annulus',(.028,.29,.33),0,.71),orange=mat('Target burnt orange annulus',(.65,.17,.048),0,.73),yellow=mat('Target warm amber center',(.86,.59,.11),0,.68),matbase=mat('Landing mat dark blue sides',(.032,.10,.19),0,.74),mattop=mat('Landing mat muted azure top',(.075,.29,.43),0,.69),matseam=mat('Landing mat light blue piping',(.18,.39,.48),0,.71))

def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(n,a,b,r,m,v=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bar(n,a,b,w,t,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def ring(n,p,r,t,m,axis='Z',v=40,minor_v=10):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=minor_v,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)

def sleeve(n,p,ro,ri,h,m,axis='Z',v=48):
 vs=[]
 for r,z in [(ro,-h/2),(ro,h/2),(ri,h/2),(ri,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)];o=mesh(n,vs,fs,m);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o

def rect_loop(n,p,w,h,t,d,m,plane='XZ'):
 vs=[]
 for ww,hh,z in [(w,h,-d/2),(w,h,d/2),(w-2*t,h-2*t,d/2),(w-2*t,h-2*t,-d/2)]:vs.extend([(-ww/2,-hh/2,z),(ww/2,-hh/2,z),(ww/2,hh/2,z),(-ww/2,hh/2,z)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)];o=mesh(n,vs,fs,m,.0015);o.location=p
 if plane=='XZ':o.rotation_euler[0]=math.pi/2
 elif plane=='YZ':o.rotation_euler[1]=math.pi/2
 return o

def lathe(n,profile,p,m,v=64):
 # Profile starts/ends on the axis; caps use a single vertex, without degeneracy.
 vs=[];levels=[]
 for r,z in profile:
  if r==0:levels.append([len(vs)]);vs.append((0,0,z))
  else:levels.append(list(range(len(vs),len(vs)+v)));vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[]
 for a,b in zip(levels,levels[1:]):
  if len(a)==1:fs.extend((a[0],b[(i+1)%v],b[i]) for i in range(v))
  elif len(b)==1:fs.extend((a[i],a[(i+1)%v],b[0]) for i in range(v))
  else:fs.extend((a[i],a[(i+1)%v],b[(i+1)%v],b[i]) for i in range(v))
 o=mesh(n,vs,fs,m,smooth=True);o.location=p;return o

def chain_run(n,a,b,m):
 a,b=Vector(a),Vector(b);d=b-a;length=d.length;count=max(4,round(length/.028));direction=d.normalized();perp=direction.cross(Vector((0,1,0))).normalized()
 if perp.length<.01:perp=Vector((1,0,0))
 for i in range(count+1):
  o=ring(n,a+d*(i/count),.017,.0037,m,v=20,minor_v=8)
  normal=perp if i%2==0 else direction.cross(perp).normalized();o.rotation_euler=normal.to_track_quat('Z','Y').to_euler()

def boxing_stand():
 p=palette()
 # Wide connected U footprint, rear mast and diagonals, with clearly stacked ballast.
 for x in [-.61,.61]:
  box('Heavy-bag stand floor rail',(x,-.05,.075),(.104,1.42,.105),p['frame'],.009)
  for y in [-.690,.590]:box('Stand floor rail rubber pad',(x,y,.025),(.136,.151,.050),p['rubber'],.006)
 box('Stand rear connecting beam',(0,.570,.080),(1.275,.108,.110),p['frame'],.009)
 box('Stand rear main mast',(0,.570,1.325),(.117,.117,2.490),p['frame'],.009)
 box('Mast foot collar',(0,.570,.145),(.210,.210,.120),p['steel'],.006)
 for x in [-.61,.61]:
  bar('Mast angled lower stabilizer',(x,.530,.139),(0,.570,1.020),.058,.058,p['frame'],.005)
  for z in [.145,.195,.245]:cyl('Fixed stacked ballast plate',(x,.458,z),.180,.046,p['rubber'],v=40,b=.005)
  cyl('Ballast retaining post',(x,.458,.290),.022,.220,p['steel'],v=24,b=.002)
  cyl('Ballast peg top cap',(x,.458,.405),.029,.018,p['rubber'],v=24,b=.002)
  for y in [-.656,.555]:cyl('Floor rail fastening',(x,y,.132),.014,.012,p['steel'],v=6,b=.001)
 box('Heavy-bag upper cantilever arm',(0,.135,2.540),(.120,1.010,.116),p['frame'],.010)
 bar('Cantilever diagonal rear brace',(0,.570,1.930),(0,-.225,2.484),.053,.053,p['steel'],.004)
 box('Cantilever end cap',(0,-.378,2.540),(.128,.021,.123),p['rubber'],.003)
 for z in [2.485,2.575]:cyl('Cantilever side bolt',(0.066,.515,z),.015,.010,p['steel'],'X',v=6)
 # The metal eye, linked suspension and bag loops are visibly attached.
 cyl('Suspension threaded eye shaft',(0,-.315,2.453),.012,.092,p['steel'],v=24,b=.001)
 ring('Upper suspension closed eye',(0,-.315,2.399),.026,.006,p['steel'],'Y',32)
 ring('Suspension swivel lower eye',(0,-.315,2.357),.024,.005,p['steel'],'X',32)
 chain_run('Central interlocking suspension chain',(0,-.315,2.339),(0,-.315,2.215),p['steel'])
 ring('Four-chain gathering ring',(0,-.315,2.191),.027,.006,p['steel'],'Y',32)
 # Upholstered cylinder has rounded ends and two edge bands, no image textures.
 lathe('Continuous rounded heavy bag',[(0,-.548),(.148,-.548),(.190,-.535),(.215,-.500),(.223,-.452),(.223,.453),(.214,.505),(.185,.538),(.142,.548),(0,.548)],(0,-.315,1.315),p['red'])
 for z in [.800,1.827]:
  ring('Heavy-bag rolled end seam',(0,-.315,z),.200,.0055,p['seam'],v=64,minor_v=8)
 for x in [-.220,.220]:bar('Bag vertical seam piping',(x,-.315,.877),(x,-.315,1.756),.004,.004,p['seam'],.0008)
 cyl('Bag top closure pad',(0,-.315,1.863),.125,.013,p['seam'],v=40,b=.002)
 for i in range(4):
  a=i*math.tau/4+.15;xx=.170*math.cos(a);yy=-.315+.170*math.sin(a)
  box('Bag reinforced suspension tab',(xx,yy,1.835),(.044,.023,.126),p['seam'],.004,rot=(0,0,a-math.pi/2))
  o=ring('Bag closed suspension lug',(xx,yy,1.902),.018,.004,p['steel'],'Y',28);o.rotation_euler[2]=a-math.pi/2
  chain_run('Four angled interlocking bag chains',(xx,yy,1.918),(0,-.315,2.174),p['steel'])
 return ('city-boxing-heavy-bag-stand','自立フレーム付きサンドバッグ','Freestanding boxing heavy-bag stand','トレーニング室のボクシング区画へ置く、自立スタンドと吊り下げ式サンドバッグの一式。丸めた袋本体と縫い目、四方向の金属チェーン、上部アイ金具、張り出しアームと補強材、連結した接地レール、重り風の積層プレートを造形。袋と重りはこの1点の部品です。揺動・打撃判定・調整はなく、運動器具としての荷重・安定性・安全性は未検証です。','A freestanding heavy-bag assembly for a boxing area in a training room. It has a rounded upholstered bag with seams, four linked suspension chains, upper eye fittings, cantilever arm/braces, connected floor rails and stacked ballast-looking plates. The bag and plates belong to one counted assembly. Swinging, hit detection and adjustment are absent; load capacity, stability and exercise-equipment safety are unvalidated.',['sports','boxing','heavy-bag','サンドバッグ'])

def gymnastics_frame():
 p=palette()
 for x in [-1.080,1.080]:
  box('Gymnastic frame long floor runner',(x,0,.083),(.140,1.850,.105),p['white'],.009)
  for y in [-.841,.841]:box('Gymnastic runner floor pad',(x,y,.027),(.176,.180,.054),p['rubber'],.007)
  box('Gymnastic main upright',(x,0,1.607),(.106,.106,3.048),p['white'],.007)
  box('Upright lower attachment collar',(x,0,.170),(.170,.174,.160),p['frame'],.007)
  for y in [-.790,.790]:
   bar('Long side diagonal support',(x,y,.140),(x,0,2.230),.055,.055,p['frame'],.004)
   box('Diagonal base shoe',(x,y,.152),(.101,.127,.060),p['steel'],.004)
   cyl('Diagonal shoe fastening',(x,y,.190),.014,.018,p['steel'],v=6,b=.001)
  for z in [.205,2.228,3.090]:cyl('Upright side through-bolt',(x+(.064 if x>0 else -.064),0,z),.016,.013,p['steel'],'X',v=6,b=.001)
 # A rear ground tie belongs to the frame, away from the ring position.
 box('Rear floor frame tie',(0,.800,.086),(2.198,.058,.060),p['white'],.004)
 cyl('Gymnastic top suspension crossbar',(0,0,3.112),.059,2.360,p['steel'],'X',v=40,b=.003)
 for x in [-1.193,1.193]:cyl('Crossbar closed protective cap',(x,0,3.112),.065,.032,p['rubber'],'X',v=32,b=.003)
 for x in [-.335,.335]:
  # One continuous flat strap, looped around the bar and around each ring crown.
  # Y/Z outline is an elongated capsule with thick closed ribbon section.
  top=3.112;bottom=1.834;radius=.066;thick=.005;width=.044;N=18
  outer=[(radius*math.cos(math.pi*i/N),top+radius*math.sin(math.pi*i/N)) for i in range(N+1)]+[(radius*math.cos(math.pi+math.pi*i/N),bottom+radius*math.sin(math.pi+math.pi*i/N)) for i in range(N+1)]
  inner=[((radius-thick)*math.cos(math.pi*i/N),top+(radius-thick)*math.sin(math.pi*i/N)) for i in range(N+1)]+[((radius-thick)*math.cos(math.pi+math.pi*i/N),bottom+(radius-thick)*math.sin(math.pi+math.pi*i/N)) for i in range(N+1)]
  k=len(outer);vs=[(xx,y,z) for xx in [x-width/2,x+width/2] for y,z in outer+inner];fs=[]
  for j in range(k):
   q=(j+1)%k;fs.extend([(j,q,k+q,k+j),(2*k+j,3*k+j,3*k+q,2*k+q),(j,2*k+j,2*k+q,q),(k+j,k+q,3*k+q,3*k+j)])
  mesh('Continuous closed flat gymnastic strap',vs,fs,p['web'])
  ring('Wooden gymnastic ring',(x,0,1.650),.133,.017,p['tan'],'Y',64,12)
  # Crown meets the lower strap loop; small joining belt wraps around the ring.
  box('Ring crown strap saddle',(x,0,1.796),(.045,.136,.027),p['web'],.003)
  rect_loop('Fixed metal strap buckle',(x,-.074,2.562),.066,.106,.008,.014,p['steel'])
  bar('Buckle transverse pin',(x-.027,-.077,2.562),(x+.027,-.077,2.562),.007,.007,p['steel'],.001)
  box('Flat folded strap tail',(x,-.074,2.425),(.039,.008,.245),p['web'],.0015)
  for z in [2.354,2.388]:box('Strap sewn keeper band',(x,-.083,z),(.049,.010,.015),p['seam'],.001)
 return ('city-gymnastic-ring-frame','固定ベルト付き吊り輪フレーム','Gymnastic rings support frame','体育室・地域トレーニング室に置く、二つの吊り輪と自立支持フレームの一式。木色の環、上梁から環へ繋がる閉じた平ベルト、固定バックルと折り返し、金属横棒、二本の支柱、前後の斜材、長い接地脚と後部連結材を造形。輪・ベルト・架台を合わせて1点です。吊り輪の揺動・長さ調整・体操動作はなく、耐荷重や運動安全性は未検証です。','A two-ring support-frame assembly for gymnasiums and community training rooms. It has wooden-colored rings, continuous flat straps linking the top beam to ring crowns, fixed buckles and tails, metal crossbar, twin uprights, front/rear diagonal braces, long floor runners and a rear tie. Rings, straps and frame count as one model. Ring swing, strap adjustment and gymnastic behavior are absent; load capacity and exercise safety are unvalidated.',['sports','gymnastics','rings','吊り輪'])

def archery_target():
 p=palette()
 # Splayed wooden A-frames support a thick round target, with true rear bracing.
 for x in [-.395,.395]:
  bar('Target front wooden leg',(x,-.230,.049),(x,.095,1.890),.064,.065,p['wood'],.005)
  bar('Target rear wooden leg',(x,.835,.047),(x,.110,1.701),.061,.061,p['wood'],.005)
  for y in [-.230,.835]:box('Target stand ground shoe',(x,y,.025),(.092,.104,.050),p['rubber'],.005)
  cyl('Target rear-leg hinge',(x,.111,1.695),.025,.101,p['steel'],'X',v=24,b=.002)
  # The paired spreading links reach actual points on both legs.
  bar('Target side spreader',(x,-.121,.677),(x,.546,.706),.018,.013,p['steel'],.0015)
  cyl('Spreader rear pin',(x+.036,.546,.706),.013,.013,p['steel'],'X',v=20,b=.001)
 for z in [1.145,1.622]:box('Target rear horizontal bearer',(0,.115,z),(1.045,.072,.072),p['wood'],.005)
 bar('Rear target frame diagonal',(-.395,.158,1.145),(.395,.158,1.622),.039,.029,p['wood'],.003)
 box('Target lower resting ledge',(0,-.018,.821),(1.041,.247,.059),p['wood'],.006)
 for x in [-.47,.47]:box('Resting ledge front stop',(x,-.151,.856),(.061,.026,.092),p['wood'],.003)
 cyl('Deep circular target backing',(0,-.015,1.430),.598,.176,p['target'],'Y',v=96,b=.009)
 # Concentric face is original plain geometry, without text or regulation claims.
 for r,y,m in [(.578,-.108,p['ivory']),(.461,-.115,p['frame']),(.344,-.122,p['blue']),(.228,-.129,p['orange']),(.112,-.136,p['yellow'])]:cyl('Layered generic target face',(0,y,1.430),r,.015,m,'Y',v=96,b=.001)
 for r in [.176,.290,.405,.521]:ring('Fine raised face division',(0,-.147+(r*.06),1.430),r,.0014,p['seam'],'Y',96,8)
 # Back-face bands and retaining fasteners make the reverse a designed surface.
 for r in [.200,.390,.561]:ring('Target backing concentric binding',(0,.075,1.430),r,.0035,p['wood'],'Y',80,8)
 for x in [-.395,.395]:
  for z in [1.145,1.622]:cyl('Rear target bearer fastener',(x,.159,z),.012,.014,p['steel'],'Y',v=6,b=.001)
 for x in [-.560,.560]:box('Target side retaining strap',(x,-.010,1.430),(.026,.202,.197),p['web'],.003)
 return ('city-archery-target-stand','A型木脚付きアーチェリー的','Freestanding archery target stand','練習場の背景や体育施設の用具区画へ置く、自立式の円形アーチェリー的。厚い繊維色の円盤、段差のある独自配色の同心円面、外周押さえ、木製A型脚、下受け、背面の横桟と斜材、開き止め金具を造形。弓・矢・番号・競技用表示は含みません。的と架台は一式1点で、射撃判定・貫通挙動・競技規格・実用品安全性は未検証です。','A freestanding circular archery target for practice-area backdrops and sports-facility equipment scenes. It has a thick fiber-colored disk, stepped concentric face in an original plain color arrangement, side retainers, wooden A-frame legs, lower ledge, rear bearers/diagonal and metal spreaders. Bows, arrows, numbers and competition markings are absent. Target and stand form one assembly; hit detection, penetration behavior, competitive specifications and real-equipment safety are unvalidated.',['sports','archery','target','アーチェリー'])

def high_jump():
 p=palette()
 # One landing system: layered three-section block and top cover with edge piping.
 box('Landing mat continuous dark underside',(0,.620,.045),(4.060,2.880,.090),p['rubber'],.032)
 for x in [-1.350,0,1.350]:
  box('Landing mat layered base section',(x,.620,.312),(1.343,2.844,.494),p['matbase'],.038)
  box('Landing mat rounded upper cushion',(x,.620,.584),(1.343,2.844,.118),p['mattop'],.029)
 # Separate top seam strips are genuine geometry, not texture lines.
 for x in [-2.000,-.675,.675,2.000]:box('Mat top longitudinal seam',(x,.620,.642),(.010,2.782,.007),p['matseam'],.002)
 for y in [-.780,2.020]:box('Mat top end piping',(0,y,.639),(4.005,.010,.008),p['matseam'],.002)
 for y in [-.811,2.051]:
  for x in [-1.350,0,1.350]:
   for xx in [x-.180,x+.180]:box('Mat carrying handle sewn pad',(xx,y,.304),(.075,.018,.113),p['mattop'],.006)
   # Closed strap handhold remains attached at both pads, leaving a visible opening.
   yy=y+(-.055 if y<0 else .055)
   bar('Mat carrying handle left attachment',(x-.180,y,.304),(x-.180,yy,.304),.029,.012,p['web'],.002)
   bar('Mat carrying handle right attachment',(x+.180,y,.304),(x+.180,yy,.304),.029,.012,p['web'],.002)
   bar('Mat fixed carrying handhold',(x-.180,yy,.304),(x+.180,yy,.304),.029,.012,p['web'],.002)
 for x in [-2.195,2.195]:
  box('High-jump upright T-foot',(x,-.950,.063),(.121,1.124,.082),p['white'],.008)
  box('High-jump upright cross foot',(x,-.950,.063),(.510,.120,.082),p['white'],.008)
  for y in [-1.452,-.448]:box('Upright floor foot pad',(x,y,.022),(.151,.139,.044),p['rubber'],.006)
  box('Lower height-adjustment upright',(x,-.950,.666),(.086,.086,1.202),p['white'],.005)
  box('Telescoping upper upright',(x,-.950,1.615),(.053,.053,1.084),p['steel'],.003)
  box('Fixed height-lock collar',(x,-.950,1.223),(.113,.112,.116),p['frame'],.006)
  cyl('Fixed upright height-lock knob',(x,-1.030,1.223),.029,.060,p['rubber'],'Y',v=28,b=.003)
  box('Upright closed upper cap',(x,-.950,2.163),(.064,.064,.028),p['rubber'],.004)
  box('Crossbar carrier clamp',(x,-.950,1.620),(.080,.087,.106),p['frame'],.004)
  sign=-1 if x>0 else 1
  box('Crossbar inward support shelf',(x+sign*.055,-.950,1.610),(.117,.084,.018),p['white'],.002)
  cyl('Carrier locking screw',(x,-1.008,1.620),.018,.034,p['rubber'],'Y',v=24,b=.002)
  for z in [1.310+i*.055 for i in range(15)]:box('Unnumbered upright height tick',(x,-.979,z),(.027 if round(z*1000)%2 else .019,.003,.004),p['frame'],.0005)
  for xx in [-.175,.175]:cyl('Foot attachment fastening',(x+xx,-.950,.108),.012,.010,p['steel'],v=6,b=.001)
 cyl('Single fixed high-jump crossbar',(0,-.950,1.641),.019,4.410,p['orange'],'X',v=32,b=.002)
 for x in [-2.151,2.151]:cyl('Crossbar end sleeve',(x,-.950,1.641),.022,.148,p['yellow'],'X',v=32,b=.002)
 return ('city-high-jump-set','支柱と着地マット付き走高跳セット','High-jump bar and landing mat assembly','陸上練習施設・体育室の走高跳区画を表す、横バー・二本の支柱・着地マットの一式。伸縮式に見える角形支柱、固定ノブと無番号目盛り、バー受けと両端キャップ、接地するT字脚、三分割の厚い積層マット、上面継ぎ目と側面取手を造形。全部を合わせて1点で、選手・競技場床は含みません。高さ調整・落下・反発などの動作はなく、競技規格・衝撃吸収・実用品安全性は未検証です。','A high-jump bar, twin-upright and landing-mat assembly for athletics practice facilities and gymnasium scenes. It has telescoping-looking square uprights, fixed knobs and unnumbered ticks, crossbar shelves/end sleeves, grounded T-feet, thick three-section layered mat, top seams and side handles. All parts count as one model; athletes and venue flooring are absent. Height adjustment, bar dropping and rebound behavior are absent; competitive specifications, impact absorption and real-equipment safety are unvalidated.',['sports','athletics','high-jump','走高跳'])

BUILDERS=[boxing_stand,gymnastics_frame,archery_target,high_jump]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-044/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/public_gym_equipment.py',azimuth=-55,elevation=27)
