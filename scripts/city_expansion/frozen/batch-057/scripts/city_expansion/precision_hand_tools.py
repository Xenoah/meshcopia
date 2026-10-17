"""Original workshop measurement and clamping tools. Xenoah, CC BY 4.0.
Closed analytic static assemblies. No borrowed models, brands, graphics or fonts.
"""
import math, sys, argparse, bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Brushed tool steel',(.39,.45,.49),.82,.32),bright=mat('Machined bright edges',(.65,.71,.73),.86,.25),dark=mat('Blackened hardware',(.025,.032,.038),.30,.42),rubber=mat('Dark molded grips',(.012,.018,.024),0,.74),blue=mat('Deep blue impact housing',(.025,.13,.26),.13,.41),red=mat('Red grip coating',(.48,.025,.012),.04,.58),yellow=mat('Yellow level coating',(.78,.47,.025),.12,.42),screen=mat('Blank inactive LCD',(.12,.19,.18),.10,.29),mark=mat('Unnumbered dark reference marks',(.017,.024,.029),.06,.57),bubble=mat('Fixed pale bubble indicator',(.80,.91,.66),0,.24))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.0007):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=24,bev=.0005):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.001):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(n,p,r,t,m,axis='Z',v=40):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)
def sleeve(n,p,ro,ri,h,m,axis='Z',v=48):
 vs=[]
 for r,z in [(ro,-h/2),(ro,h/2),(ri,h/2),(ri,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)]
 o=mesh(n,vs,fs,m);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o
def plate_xy(n,poly,z,t,m,bev=.0006):
 N=len(poly);vs=[(x,y,zz) for zz in [z-t/2,z+t/2] for x,y in poly];fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)]
 return mesh(n,vs,fs,m,bev)
def plate_xz(n,poly,y,t,m,bev=.001):
 N=len(poly);vs=[(x,yy,z) for yy in [y-t/2,y+t/2] for x,z in poly];fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)]
 return mesh(n,vs,fs,m,bev)
def bolt_head(n,p,r,m,axis='Z'):
 return cyl(n,p,r,r*.52,m,axis,v=6,b=r*.07)
def knurled(n,p,r,d,m,axis='Z',ribs=24):
 o=cyl(n,p,r,d,m,axis,v=48,b=.0004)
 for i in range(ribs):
  a=i*math.tau/ribs;v=Vector((r*math.cos(a),r*math.sin(a),0))
  if axis=='X':v=Vector((0,v.y,-v.x))
  if axis=='Y':v=Vector((v.x,0,v.y))
  q=Vector(p)+v;rod(n+' raised grip ridge',q-Vector((d*.39 if axis=='X' else 0,d*.39 if axis=='Y' else 0,d*.39 if axis=='Z' else 0)),q+Vector((d*.39 if axis=='X' else 0,d*.39 if axis=='Y' else 0,d*.39 if axis=='Z' else 0)),.0003,m,8,.00005)
 return o

def digital_caliper():
 p=palette()
 # The stainless beam continues through the slider; a separate slender depth rod projects at the end.
 box('Caliper rectangular measuring beam',(.012,0,.009),(.268,.016,.0046),p['steel'],.0007)
 box('Caliper polished beam top',(.014,0,.0115),(.264,.013,.0007),p['bright'],.00015)
 box('Depth rod guide groove exterior',(.109,.0071,.0089),(.070,.0023,.0024),p['dark'],.0002)
 box('Projected fixed depth-measuring rod',(.150,.0048,.0088),(.055,.0029,.0023),p['steel'],.0002)
 # Large outside jaws and smaller inside jaws have opposing parallel measuring faces.
 fixed=[(-.122,.011),(-.110,.011),(-.110,-.035),(-.103,-.046),(-.103,-.068),(-.110,-.068),(-.126,-.037),(-.128,-.009)]
 moving=[(-.065,.011),(-.053,.011),(-.047,-.009),(-.048,-.037),(-.065,-.068),(-.073,-.068),(-.073,-.046),(-.065,-.035)]
 plate_xy('Fixed exterior measuring jaw',fixed,.009,.008,p['steel'],.0007)
 plate_xy('Moving exterior measuring jaw',moving,.009,.008,p['steel'],.0007)
 box('Fixed flat outer measuring contact',(-.1028,-.057,.009),(.0016,.022,.007),p['bright'],.0002)
 box('Moving flat outer measuring contact',(-.0732,-.057,.009),(.0016,.022,.007),p['bright'],.0002)
 plate_xy('Fixed inside-measuring jaw',[(-.123,.006),(-.111,.006),(-.112,.025),(-.118,.039),(-.122,.039)],.009,.006,p['bright'],.0005)
 plate_xy('Moving inside-measuring jaw',[(-.063,.006),(-.052,.006),(-.053,.039),(-.057,.039),(-.063,.025)],.009,.006,p['bright'],.0005)
 box('Caliper slider lower saddle',(-.048,0,.0085),(.055,.027,.012),p['steel'],.0015)
 box('Caliper blue digital readout housing',(-.044,-.003,.018),(.056,.035,.014),p['blue'],.003)
 box('LCD dark raised bezel',(-.044,.001,.025),(.044,.022,.003),p['dark'],.0012)
 box('Blank inactive LCD panel',(-.044,.001,.0266),(.038,.016,.0009),p['screen'],.0008)
 for i,x in enumerate([-.059,-.044,-.029]):cyl('Unmarked fixed caliper control',(x,-.0167,.025),.003,.0024,p['red'] if i==0 else p['rubber'],v=24,b=.0004)
 for y in [-.010,.010]:
  for x in [-.069,-.023]:cyl('Slider underside screw',(x,y,.0019),.0018,.0013,p['dark'],v=12,b=.0002)
 # Lock screw stands on the top edge; the thumb wheel protrudes below the beam.
 cyl('Slider lock screw neck',(-.045,.019,.012),.0025,.010,p['steel'],'Y',v=20,b=.0003)
 knurled('Slider lock screw head',(-.045,.025,.012),.005,.0045,p['bright'],'Y',20)
 box('Thumbwheel support bridge',(-.032,-.024,.012),(.017,.009,.005),p['steel'],.001)
 knurled('Caliper thumb adjustment wheel',(-.032,-.026,.013),.007,.005,p['bright'],'Z',28)
 for i in range(61):
  x=-.107+i*.004
  if -.076<x<-.012:continue
  long=i%5==0
  box('Unnumbered beam graduation',(x,.003 if long else .0044,.01205),(.00032,.007 if long else .0042,.00035),p['mark'],.00005)
 return ('city-digital-slide-caliper','無表示デジタルノギス','Blank-display digital slide caliper','整備工場や工作室の机上に置くデジタルノギス。対向する外側/内側測定ジョウ、金属ビーム、固定位置のスライダー、無表示LCDと三つのボタン、上端ロックねじ、ローレット状の送り輪、突出したデプスバー、無番号の参考目盛と裏ねじを造形。開いたジョウは固定で測定/表示/スライド機能はなく、目盛は校正されていません。一式1点、机上配置用の静的小物です。','A digital slide caliper for workshop and maintenance benches. Opposed outside/inside measuring jaws, steel beam, fixed slider, blank LCD and three buttons, top locking screw, knurled thumbwheel, projecting depth rod, unnumbered reference graduations and underside screws are modeled. Jaws remain open in a fixed pose: measurement, display and sliding are not implemented and marks are not calibrated. The complete assembly counts as one static tabletop prop.',['workshop','digital-caliper','measurement','ノギス'])

def clear_vial_material():
 m=mat('Transparent green-tinted vial shell',(.51,.79,.16),0,.12)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.46
 return m

def spirit_level():
 p=palette();p['glass']=clear_vial_material()
 # Three true through openings are left by these connected structural rail/web pieces.
 for z in [.008,.060]:box('Level full length aluminum reference rail',(0,0,z),(.610,.037,.009),p['bright'],.001)
 for z in [.016,.052]:box('Level yellow continuous frame rail',(0,0,z),(.598,.032,.011),p['yellow'],.0015)
 for x,w in [(-.284,.031),(-.147,.156),(.147,.156),(.284,.031)]:
  box('Level solid reinforced web',(x,0,.034),(w,.032,.029),p['yellow'],.0013)
 # Spaces: left [-.269,-.225], center [-.069,.069], right [.225,.269].
 for x in [-.312,.312]:
  box('Shock absorbing level end cap',(x,0,.034),(.022,.044,.068),p['rubber'],.004)
  for z in [.014,.026,.038,.050]:box('End cap molded transverse rib',(x,0,z),(.023,.046,.0025),p['dark'],.0007)
 for y in [-.0165,.0165]:
  for x in [-.147,.147]:
   box('Level side raised reinforcement',(x,y,.034),(.131,.003,.017),p['yellow'],.002)
   for j in range(4):box('Level molded hand grip rib',(x+(.024*j-.036),y*1.06,.034),(.003,.003,.015),p['dark'],.0006)
 def vial(n,center,direction,length):
  d=Vector(direction).normalized();c=Vector(center)
  # Glass annular shell and closed transparent end disks are real mesh, not a painted mark.
  shell=sleeve(n+' transparent tube',c,.0102,.0086,length,p['glass'],'Z',48);shell.rotation_euler=d.to_track_quat('Z','Y').to_euler()
  for sign in [-1,1]:
   q=c+d*sign*(length/2-.0004)
   o=cyl(n+' sealed transparent end',q,.0097,.0014,p['glass'],v=40,b=.00025);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
   q=c+d*sign*(length/2+.003)
   o=cyl(n+' black cradle collar',q,.0125,.009,p['dark'],v=40,b=.001);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
   q=c+d*sign*min(.0135,length*.24)
   o=ring(n+' dark reference line',q,.0104,.0006,p['mark'],v=48);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
  o=sphere(n+' fixed enclosed pale bubble',c,(min(.0063,length*.15),min(.0063,length*.15),min(.011,length*.22)),p['bubble'],32,16);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 vial('Horizontal center vial',(0,0,.034),(1,0,0),.116)
 vial('Vertical end vial',(-.247,0,.034),(0,0,1),.029)
 vial('Angled end vial',(.247,0,.034),(.60,0,.80),.029)
 # Tiny side fasteners at the solid webs, not floating on the open windows.
 for x in [-.280,-.082,.082,.280]:
  for y in [-.017,.017]:cyl('Level side retaining fastener',(x,y,.034),.0025,.002,p['dark'],'Y',v=12,b=.0003)
 return ('city-three-vial-spirit-level','三気泡管の水平器','Three-vial spirit level','施工現場や工具棚に置く横長の水平器。上下の金属基準面、黄色い補強フレーム、実際に貫通した三つの観察窓、水平/垂直/斜めの透明な密閉気泡管、黒い基準線、固定した淡色の内部気泡表示、保護端キャップと側面握りを造形。透明管は形状と透過材質を持ち、気泡表示は固定の不透明楕円体で液体/気泡物理を再現しません。斜め管は参考角度で校正されておらず水平測定不可。一式1点の静的小物です。','A long spirit level for construction scenes or tool shelving. Upper/lower metal reference rails, yellow reinforced frame, three actual through-view windows, horizontal/vertical/angled transparent sealed vials, black reference rings, fixed pale internal bubble indicators, protective end caps and side grips are modeled. Vials use real closed geometry and transmissive materials; bubble indicators are fixed opaque ellipsoids, not simulated liquid or air physics. The angled vial is illustrative, not calibrated, and the prop cannot measure level. One complete static assembly.',['workshop','spirit-level','measurement','水平器'])

def helical_ridge(n,x,y,z0,z1,root,outer,pitch,m):
 turns=(z1-z0)/pitch;N=int(math.ceil(turns*36));vs=[]
 for i in range(N+1):
  a=math.tau*turns*i/N;z=z0+(z1-z0)*i/N
  for r,dz in [(root,-pitch*.30),(outer,-pitch*.10),(outer,pitch*.10),(root,pitch*.30)]:vs.append((x+r*math.cos(a),y+r*math.sin(a),z+dz))
 fs=[(3,2,1,0),(4*N,4*N+1,4*N+2,4*N+3)]
 fs += [(4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j) for i in range(N) for j in range(4)]
 o=mesh(n,vs,fs,m)
 for f in o.data.polygons:f.use_smooth=f.index>1 and (f.index-2)%4==1
 return o

def c_screw_clamp():
 p=palette()
 # Single analytic concave C-profile, thick at the spine and threaded boss.
 poly=[(.062,.181),(-.036,.181),(-.075,.169),(-.092,.146),(-.100,.111),(-.098,.064),(-.086,.028),(-.062,.009),(.063,.009),(.063,.043),(-.042,.043),(-.058,.056),(-.064,.082),(-.065,.120),(-.054,.145),(-.037,.153),(.062,.153)]
 plate_xz('Cast C-clamp main frame',poly,0,.027,p['blue'],.004)
 rib=[(.041,.175),(-.034,.175),(-.069,.162),(-.084,.143),(-.092,.111),(-.090,.066),(-.080,.035),(-.058,.018),(.036,.018),(.036,.026),(-.053,.027),(-.071,.041),(-.081,.069),(-.084,.111),(-.077,.138),(-.064,.154),(-.031,.166),(.041,.166)]
 for y in [-.014,.014]:plate_xz('C-frame raised cast reinforcement',rib,y,.004,p['blue'],.0012)
 box('Fixed clamp anvil body',(.046,0,.158),(.040,.035,.019),p['blue'],.003)
 box('Fixed machined anvil face',(.046,0,.147),(.033,.031,.005),p['steel'],.0007)
 cyl('Threaded lower cast boss',(.042,0,.025),.021,.045,p['blue'],v=40,b=.002)
 cyl('Boss upper machined ring',(.042,0,.048),.013,.003,p['steel'],v=40,b=.0004)
 cyl('Clamp screw root shaft',(.042,0,.032),.0064,.160,p['steel'],v=40,b=.0003)
 helical_ridge('Continuous capped helical screw thread',.042,0,-.044,.105,.0061,.0082,.004,p['bright'])
 cyl('Swivel pad neck',(.042,0,.109),.0048,.016,p['steel'],v=32,b=.0004)
 o=sphere('Swivel pad spherical seat',(.042,0,.116),(.0065,.0065,.0065),p['steel'],24,12)
 # This small mechanical ball seat uses deterministic planar facets.
 for f in o.data.polygons:f.use_smooth=False
 cyl('Round floating swivel contact pad',(.042,0,.123),.019,.008,p['steel'],v=48,b=.0015)
 cyl('Flat swivel contact surface',(.042,0,.1272),.0175,.0018,p['bright'],v=48,b=.0003)
 cyl('Sliding T-handle hub',(.042,0,-.056),.010,.022,p['dark'],v=40,b=.0014)
 rod('Sliding tommy-bar handle',(-.011,0,-.058),(.095,0,-.058),.0038,p['steel'],32)
 for x in [-.014,.098]:sphere('Tommy-bar captive end stop',(x,0,-.058),(.006,.006,.006),p['bright'],24,12)
 return ('city-c-frame-screw-clamp','C型ねじクランプ','C-frame screw clamp','木工室や金属加工台に置くC型ねじクランプ。厚い一体C形フレーム、表裏の鋳造風補強、固定の機械加工アンビル、下側ボスを通る実形状の連続らせんねじ、球面座と丸い首振りパッド、端止め付きスライドTハンドルを造形。パッドと上ジョウ間の小さい隙間は意図した固定姿勢です。ねじ回転/締付/首振りはなく、ボス内部の雌ねじや荷重性能は再現しません。一式1点の静的な工具小物です。','A C-frame screw clamp for woodworking or metalworking benches. A thick one-piece C-profile frame, front/back cast-style ribs, fixed machined anvil, geometric continuous helical screw through the lower boss, spherical seat/round swivel pad, and captive sliding T-handle are modeled. The small gap between pad and upper jaw is an intentional fixed pose. Screw rotation, clamping and pad articulation are absent; internal female threads and load performance are not modeled. One complete static tool prop.',['workshop','c-clamp','screw-clamp','クランプ'])

def bolt_cutters():
 p=palette()
 # Thick opposing straight-cutting jaws, not curved bypass blades.
 jaw=[(-.003,.230),(-.003,.182),(-.017,.154),(-.027,.117),(-.045,.085),(-.065,.095),(-.064,.139),(-.051,.189),(-.027,.226)]
 for s in [-1,1]:
  pts=[(s*x,y) for x,y in jaw]
  plate_xy('Forged straight-cut jaw',pts,.020,.024,p['steel'],.002)
  # A real wedge insert tapers in thickness towards its straight center cutting edge.
  x0=s*-.0027;x1=s*-.014
  vs=[(x0,.181,.019),(x0,.228,.019),(x1,.225,.008),(x1,.185,.008),(x0,.181,.021),(x0,.228,.021),(x1,.225,.032),(x1,.185,.032)]
  mesh('Straight beveled jaw cutting land',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],p['bright'],.0004)
 # Front and back bridge plates retain two distinct jaw pivots.
 for z in [.003,.037]:
  plate_xy('Twin-pivot head bridge',[(-.059,.142),(-.056,.116),(.056,.116),(.059,.142),(.041,.154),(-.041,.154)],z,.007,p['dark'],.002)
 for x in [-.043,.043]:
  cyl('Jaw pivot pin',(x,.132,.020),.0085,.050,p['steel'],v=32,b=.0007)
  bolt_head('Front hexagonal jaw pivot',(x,.132,.046),.011,p['bright'])
  cyl('Rear jaw pivot washer',(x,.132,-.005),.012,.003,p['steel'],v=32,b=.0004)
  bolt_head('Rear hexagonal jaw pivot',(x,.132,-.008),.009,p['dark'])
 # Long handles terminate in thick forged tangs and offset compound links.
 for s in [-1,1]:
  top=Vector((s*.028,.055,.020));end=Vector((s*.143,-.340,.020));axis=(end-top).normalized()
  rod('Long tubular cutter handle',top,end,.0105,p['red'],32,.001)
  gripstart=top+(end-top)*.61
  rod('Thick molded handle grip',gripstart,end+axis*.004,.0155,p['rubber'],40,.002)
  for j in range(12):
   q=gripstart+(end+axis*.003-gripstart)*(j/12)
   o=ring('Handle grip raised traction ring',q,.0152,.001,p['dark'],v=32);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
  rod('Handle grip closed butt',end,end+axis*.007,.016,p['red'],32,.001)
  plate_xy('Forged handle upper tang',[(s*.015,.078),(s*.043,.079),(s*.057,.033),(s*.038,.009),(s*.022,.020)],.020,.020,p['steel'],.0016)
  cyl('Lower compound handle pivot',(s*.029,.062,.020),.007,.033,p['bright'],v=32,b=.0006)
  for z in [.002,.038]:bolt_head('Compound pivot retaining bolt',(s*.029,.062,z),.008,p['dark'])
  # Offset short links connect the heel of each jaw to the opposite handle tang.
  for z in ([.008,.032] if s<0 else [.000,.040]):
   aa=Vector((s*.046,.098,z));bb=Vector((-s*.029,.062,z));d=bb-aa
   box('Layered compound leverage plate',(aa+bb)/2,(d.length+.016,.016,.006),p['steel'],.0012,rot=(0,0,math.atan2(d.y,d.x)))
  cyl('Jaw heel compound-link pin',(s*.046,.098,.020),.006,.044,p['bright'],v=32,b=.0006)
  bolt_head('Jaw heel adjustment nut',(s*.046,.098,.043),.008,p['dark'])
 # Stop hardware bridges the handle tangs and explains the fixed handle spread.
 box('Compound mechanism central stop',(0,.049,.020),(.022,.015,.020),p['dark'],.0015)
 rod('Adjuster stop screw',(-.022,.049,.020),(.022,.049,.020),.004,p['bright'],24,.0004)
 for x in [-.021,.021]:bolt_head('Stop screw locknut',(x,.049,.020),.006,p['steel'],'X')
 return ('city-compound-bolt-cutters','複合リンク式ボルトクリッパー','Compound-link bolt cutters','工場や建設作業場の工具棚/作業台に置く大型ボルトクリッパー。直線の対向切断刃と厚い鍛造風ジョウ、二軸の表裏ブリッジ、交差する短い複合リンク、調整ナットとストップねじ、長い二本の金属ハンドル、閉じた端と滑り止めの黒い握りを造形。剪定ばさみとは異なる直線の対向刃を少し開いた固定姿勢です。刃/リンク/ハンドルの動作、実際の切断、刃硬度や安全性能は再現していません。全部品を含む一式1点。','Large bolt cutters for factory or construction workshop shelving and benches. Straight opposing cutting edges and thick forged-style jaws, front/rear twin-pivot bridge plates, short crossed compound links, adjustment nuts/stop screw, long twin metal handles, closed grip ends and ribbed black grips are modeled. Unlike bypass pruning shears, the straight opposing jaws have a narrow fixed opening. Jaw, linkage and handle motion, actual cutting, edge hardness and safety performance are not implemented. All components form one complete static prop.',['workshop','bolt-cutters','compound-linkage','ボルトクリッパー'])

BUILDERS=[digital_caliper,spirit_level,c_screw_clamp,bolt_cutters]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-057/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/precision_hand_tools.py',azimuth=-55,elevation=55)
