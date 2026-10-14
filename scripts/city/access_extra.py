"""Original secondary street access props, CC BY 4.0. No third-party assets."""
import bpy, math, sys, argparse, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from access import box,cyl,torus,tube,mesh,extrude_x,palette,mat,finish


def split_surface(name,verts,faces,material,sharp_pairs,flat_faces=()):
 """Smooth curved bands with explicitly disconnected normals at sharp cap loops.
 Avoid weighted-cap normals leaking into tiny sloped surfaces.
 """
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
 obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
 obj.data.materials.append(material)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 for face in data.polygons:face.use_smooth=face.index not in flat_faces
 sharp={tuple(sorted(pair)) for pair in sharp_pairs}
 for edge in data.edges:edge.use_edge_sharp=tuple(sorted(edge.vertices)) in sharp
 mod=obj.modifiers.new('Separate sharp cap normals','EDGE_SPLIT');mod.use_edge_angle=False;mod.use_edge_sharp=True
 bpy.ops.object.modifier_apply(modifier=mod.name)
 return obj


def lathe(name,profile,material,n=32,location=(0,0,0),split_caps=False):
 """Closed radial profile with no duplicate poles; all radii must be positive."""
 verts=[(location[0]+r*math.cos(i*math.tau/n),location[1]+r*math.sin(i*math.tau/n),location[2]+z) for r,z in profile for i in range(n)]
 faces=[]
 for j in range(len(profile)):
  k=(j+1)%len(profile)
  faces.extend((j*n+i,j*n+(i+1)%n,k*n+(i+1)%n,k*n+i) for i in range(n))
 if split_caps:
  sharp=[]
  for j,point in enumerate(profile):
   prev=profile[j-1];nxt=profile[(j+1)%len(profile)]
   a=(point[0]-prev[0],point[1]-prev[1]);b=(nxt[0]-point[0],nxt[1]-point[1])
   cosine=(a[0]*b[0]+a[1]*b[1])/(math.hypot(*a)*math.hypot(*b))
   if cosine<math.cos(math.radians(30)):
    sharp.extend((j*n+i,j*n+(i+1)%n) for i in range(n))
  return split_surface(name,verts,faces,material,sharp)
 return mesh(name,verts,faces,material,0)

def bore(obj,loc,radius,depth):
 bpy.ops.object.select_all(action='DESELECT')
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=loc)
 cutter=bpy.context.object
 bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 mod=obj.modifiers.new('Through fixing bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 return obj

def traffic_cone(p):
 box('Heavy rubber base',(0,0,.027),(.39,.39,.054),p['rubber'],.024)
 box('Underside inset footprint',(0,0,.009),(.33,.33,.018),p['black'],.014)
 # A genuine hollow shell; alternating face bands share the same tapered surface.
 levels=[.054,.24,.34,.45,.52,.63]
 radius=lambda z:.145-(z-.054)*(.108/.576)
 profile=[(radius(z),z) for z in levels]+[(radius(z)-.007,z) for z in reversed(levels)]
 shell=lathe('Hollow tapered cone shell',profile,p['orange'],48,split_caps=True)
 shell.data.materials.append(p['white'])
 # Outer strips 1 and 3 are reflective; inner wall and mouth remain orange.
 for face in shell.data.polygons:
  if face.index//48 in (1,3):face.material_index=1
 torus('Rounded mouth rim',(0,0,.63),.0335,.0035,p['orange'])
 for side in (-1,1):
  for i in range(3):box('Base grip ridge',(side*.169,-.09+i*.09,.056),(.012,.055,.004),p['black'],.001)

def wheel_stop(p):
 concrete=mat('Precast warm concrete',(.36,.37,.34),0,.92)
 profile=[(-.15,0),(.15,0),(.15,.025),(.075,.13),(-.075,.13),(-.15,.025)]
 body=extrude_x('Chamfered concrete wheel stop',profile,1.65,concrete,.008)
 for x in (-.57,.57):
  bore(body,(x,0,.08),.025,.3)
  lathe('Recessed fixing socket',[(.026,.123),(.026,.128),(.020,.128),(.020,.123)],p['steel'],24,(x,0,0))
 # Inlaid-looking reflectors follow the sloping front and back surfaces.
 slope=math.atan2(.105,.075)
 for side in (-1,1):
  for x in (-.36,.36):
   ob=box('Yellow face reflector',(x,side*.112,.078),(.27,.004,.080),p['yellow'],.001)
   ob.rotation_euler[0]=side*(math.pi/2-slope)
 finish(body,body.name,None,0)

def cable_protector(p):
 box('Continuous lower cable bed',(0,0,.005),(.9,.48,.01),p['rubber'],.003)
 # Side wings and open-ended internal channels, not a solid curb wedge.
 for side in (-1,1):
  prof=[(side*.15,.01),(side*.24,.01),(side*.24,.016),(side*.15,.073)]
  extrude_x('Sloped rubber entry wing',prof,.9,p['rubber'],.0008)
  box('Outer channel wall',(0,side*.146,.039),(.9,.018,.058),p['rubber'],.002)
 for y in (-.05,.05):box('Internal channel divider',(0,y,.037),(.9,.015,.054),p['rubber'],.002)
 box('Hinged yellow bridge lid',(0,0,.078),(.89,.29,.014),p['yellow'],.004)
 for x in (-.34,-.17,0,.17,.34):
  cyl('Alternating hinge barrel',(x,.149,.075),.011,.092,p['dark'],n=16,b=.001,axis=(1,0,0))
 cyl('Continuous hinge pin',(0,.149,.075),.004,.88,p['steel'],n=12,b=.0005,axis=(1,0,0))
 for x in [-.39+i*.065 for i in range(13)]:
  for y in (-.065,.065):
   ob=box('Raised chevron grip',(x,y,.086),(.038,.065,.003),p['rubber'],.0008);ob.rotation_euler[2]=(-1 if y<0 else 1)*.45
 for x in (-.32,.32):box('Lid latch tab',(x,-.153,.071),(.045,.024,.025),p['dark'],.004)
 # End alignment tongues remain outside the three open cable passageways.
 for x in (-.467,.467):
  for y in (-.19,.19):box('Interlocking end tongue',(x,y,.023),(.045,.045,.018),p['rubber'],.004)

def tree_guard(p):
 green=mat('Deep green powder coating',(.035,.10,.063),.35,.48)
 for x in (-.43,.43):
  for y in (-.43,.43):
   box('Anchor foot',(x,y,.012),(.13,.13,.024),green,.007)
   box('Corner upright',(x,y,.72),(.035,.035,1.40),green,.003)
   box('Closed post cap',(x,y,1.425),(.043,.043,.016),p['dark'],.004)
   for dx,dy in ((-.04,-.04),(.04,.04)):
    cyl('Foot anchor washer',(x+dx,y+dy,.026),.012,.003,p['steel'],n=12,b=.0005)
    cyl('Foot anchor hex head',(x+dx,y+dy,.032),.008,.009,p['steel'],n=6,b=.0006)
 for z in (.22,1.29):
  for side in (-1,1):
   box('Side cage rail',(side*.43,0,z),(.028,.86,.033),green,.003)
   box('Front and rear cage rail',(0,side*.43,z),(.86,.028,.033),green,.003)
 for i in range(5):
  v=-.30+i*.15
  for side in (-1,1):
   box('Side vertical picket',(side*.43,v,.755),(.014,.014,1.07),green,.0015)
   box('Front and rear vertical picket',(v,side*.43,.755),(.014,.014,1.07),green,.0015)
 for y in (-.451,.451):
  for z in (.22,1.29):
   box('Bolted half-cage joining plate',(0,y,z),(.09,.009,.055),green,.003)
   for x in (-.029,.029):cyl('Cage joining bolt',(x,y+(.007 if y>0 else -.007),z),.007,.009,p['steel'],n=6,b=.0005,axis=(0,1,0))

def bicycle_repair_stand(p):
 blue=mat('Service station blue coating',(.035,.18,.30),.35,.42)
 box('Station ground plate',(0,0,.018),(.38,.33,.036),p['dark'],.012)
 for x in (-.14,.14):
  for y in (-.11,.11):cyl('Station anchor bolt',(x,y,.045),.012,.017,p['steel'],n=6,b=.001)
 box('Structural service column',(0,0,.62),(.14,.15,1.20),blue,.012)
 box('Column cap',(0,0,1.23),(.16,.17,.035),p['dark'],.009)
 cyl('Cradle structural crossmember',(0,.02,1.18),.018,.25,p['steel'],n=20,b=.002,axis=(1,0,0))
 for x in (-.105,.105):
  tube('Seat-support cradle arm',[(x,.02,1.18),(x,-.10,1.18),(x,-.34,1.18),(x,-.38,1.22)],.016,p['steel'])
  cyl('Protective cradle sleeve',(x,-.245,1.18),.022,.19,p['rubber'],n=20,b=.004,axis=(0,1,0))
 box('Tool tether mounting rail',(0,-.086,.98),(.24,.025,.05),p['dark'],.005)
 for i,x in enumerate((-.085,0,.085)):
  cyl('Tether ferrule',(x,-.106,.98),.008,.022,p['steel'],n=12,b=.001,axis=(0,1,0))
  endz=(.58,.50,.60)[i]
  pts=[(x+.025*math.sin(math.pi*t/14),-.115-.07*math.sin(math.pi*t/14),.96+(.70-.96)*t/14) for t in range(15)]
  tube('Flexible security tether',pts,.0025,p['dark'])
  if i==0:
   box('Spanner shaft',(x,-.115,.635),(.014,.008,.13),p['steel'],.002)
   torus('Spanner ring end',(x,-.115,.704),.014,.004,p['steel'],rot=(math.pi/2,0,0))
   for dx in (-.012,.012):box('Spanner open jaw',(x+dx,-.115,.563),(.009,.008,.033),p['steel'],.001)
   box('Spanner jaw root',(x,-.115,.575),(.029,.008,.012),p['steel'],.001)
  elif i==1:
   cyl('Screwdriver grip',(x,-.115,.66),.012,.082,p['rubber'],n=16,b=.004)
   cyl('Screwdriver shaft',(x,-.115,.56),.0035,.12,p['steel'],n=12,b=.0005)
   box('Screwdriver blade',(x,-.115,.498),(.008,.003,.014),p['steel'],.0005)
  else:
   tube('L-shaped hex key',[(x,-.115,.70),(x,-.115,.54),(x+.045,-.115,.54)],.004,p['steel'])
 # Mechanical floor pump alongside the service column, not an unrelated utility bank.
 px=.285
 box('Pump footplate',(px,.015,.013),(.18,.25,.026),p['dark'],.01)
 cyl('Pump barrel',(px,.035,.34),.033,.64,blue,n=32,b=.005)
 cyl('Pump lower collar',(px,.035,.065),.039,.046,p['steel'],n=32,b=.004)
 cyl('Pump upper guide',(px,.035,.673),.040,.035,p['dark'],n=32,b=.003)
 cyl('Extended piston rod',(px,.035,.768),.010,.17,p['steel'],n=16,b=.001)
 cyl('Pump T handle',(px,.035,.86),.020,.25,p['rubber'],n=20,b=.004,axis=(1,0,0))
 tube('Pump air hose',[(px+.03,.035,.10),(px+.13,.02,.14),(px+.17,-.06,.30),(px+.13,-.10,.50),(px+.07,-.10,.65),(px+.015,-.11,.69)],.007,p['black'])
 cyl('Hose valve head',(px+.015,-.11,.70),.012,.043,p['steel'],n=16,b=.002)
 box('Valve locking lever',(px+.015,-.11,.727),(.025,.014,.008),p['dark'],.002)
 cyl('Mechanical pressure gauge case',(px,-.015,.57),.036,.026,p['steel'],n=32,b=.003,axis=(0,1,0))
 cyl('Unbranded gauge face',(px,-.030,.57),.030,.003,p['white'],n=32,b=.0005,axis=(0,1,0))
 o=box('Gauge pointer',(px+.007,-.033,.578),(.003,.002,.028),p['red'],.0004);o.rotation_euler[1]=-.6


def tactile_paving(p):
 stone=mat('Ochre tactile concrete',(.54,.37,.095),0,.86)
 box('Tactile paving slab',(0,0,.0175),(.3,.3,.035),stone,.003)
 # 36 truncated domes at a useful coarse pitch, not an accessibility certification.
 for i in range(6):
  for j in range(6):
   x=-.1125+i*.045;y=-.1125+j*.045
   n=16;r0=.0125;r1=.0085;z0=.035;z1=.040
   v=[(x+r*math.cos(k*math.tau/n),y+r*math.sin(k*math.tau/n),z) for r,z in ((r0,z0),(r1,z1)) for k in range(n)]
   f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
   sharp=[(ring*n+k,ring*n+(k+1)%n) for ring in (0,1) for k in range(n)]
   split_surface('Truncated warning dome',v,f,stone,sharp,flat_faces=(0,1))

ASSETS=[
 ('city-traffic-cone','反射帯付き交通コーン','Reflective traffic cone',traffic_cone,'中空のテーパー形状、反射帯、重量のあるゴム基部を備える交通コーン。','A hollow tapered traffic cone with reflective bands, rounded mouth and weighted rubber base.',24),
 ('city-wheel-stop','コンクリート製輪止め','Precast wheel stop',wheel_stop,'固定用貫通穴と両側の黄色い反射板を備える面取りされたコンクリート製輪止め。','A chamfered precast parking wheel stop with real through-fixing bores and yellow reflectors on both slopes.',28),
 ('city-cable-protector','ヒンジ式ケーブル保護ブリッジ','Hinged cable protector',cable_protector,'3本の開放端ケーブル通路、黄色いヒンジ蓋、滑り止めを備えるケーブル保護ブリッジ。ケーブルは含みません。','A three-channel cable-crossing bridge with open ends, hinged yellow lid, latches and raised grips; cables not included.',28),
 ('city-tree-guard','街路樹用保護ケージ','Street tree guard',tree_guard,'開放された中央空間、4本の支柱、縦格子、固定金具を備える樹木保護ケージ。樹木や植木鉢は含みません。','An open four-post tree-protection cage with rails, pickets, anchor feet and bolted joints; no tree or planter included.',26),
 ('city-bicycle-repair-stand','街頭自転車修理スタンド','Public bicycle repair stand',bicycle_repair_stand,'支持アーム、ワイヤーでつながれた工具、手動空気入れとホースを備える修理スタンド。自転車は含みません。','A public bicycle service post with support cradle, tethered generic tools, hand pump, hose and mechanical gauge; no bicycle included.',22),
 ('city-tactile-paving','突起付き注意喚起舗装板','Tactile warning paving slab',tactile_paving,'36個の切頭突起を備える単体の注意喚起舗装板。アクセシビリティ規格への適合は未検証。','A single practical warning paving slab with 36 truncated tactile domes. Accessibility-standard compliance has not been validated.',40)]

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
 parser.add_argument('--only',nargs='*',default=[])
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
 for slug,title,en,builder,ja,desc,elevation in ASSETS:
  if args.only and slug not in args.only:continue
  if (args.output/slug).exists():raise FileExistsError(f'Refusing to overwrite {args.output/slug}')
  common.reset();builder(palette())
  common.publish_asset(slug,title,en,ja,desc,['access','street-furniture',slug.removeprefix('city-')],args.output,'scripts/city/access_extra.py',elevation=elevation)

  metadata_path=args.output/slug/'asset.json'
  metadata=json.loads(metadata_path.read_text())
  metadata['usages'][0]['sourcePaths'].append('scripts/city/access.py')
  metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
