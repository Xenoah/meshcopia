"""Original compact urban structures. CC BY 4.0; no imported assets or brands."""
import bpy, math, sys, argparse, json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from access import box,cyl,torus,tube,mesh,palette,mat
from access_extra import split_surface


def arc_profile(name,profile,start,end,segments,material,center=(0,0,0)):
 """Closed section swept around an arc, with split corner/end-cap normals."""
 n=segments+1;m=len(profile)
 verts=[(center[0]+r*math.cos(start+(end-start)*i/segments),center[1]+r*math.sin(start+(end-start)*i/segments),center[2]+z) for r,z in profile for i in range(n)]
 faces=[]
 for j in range(m):
  k=(j+1)%m
  faces.extend((j*n+i,j*n+i+1,k*n+i+1,k*n+i) for i in range(segments))
 faces.extend((tuple(j*n for j in reversed(range(m))),tuple(j*n+segments for j in range(m))))
 sharp=[(j*n+i,j*n+i+1) for j in range(m) for i in range(segments)]
 sharp += [(j*n+i,((j+1)%m)*n+i) for j in range(m) for i in (0,segments)]
 return split_surface(name,verts,faces,material,sharp,flat_faces=(len(faces)-2,len(faces)-1))

def rod(name,a,b,r,material,n=16):
 a,b=Vector(a),Vector(b);return cyl(name,(a+b)/2,r,(b-a).length,material,n=n,b=min(.002,r*.15),axis=b-a)

def curb_corner(p):
 concrete=mat('Curb precast concrete',(.40,.41,.38),0,.90)
 profile=[(.63,0),(.98,0),(.98,.035),(.84,.035),(.82,.17),(.79,.18),(.64,.18),(.63,.17)]
 arc_profile('Curved curb and integral gutter',profile,0,math.pi/2,28,concrete)
 # Slightly inset end joint pads give clean seams when assembling curb runs.
 for angle in (0,math.pi/2):
  radial=Vector((math.cos(angle),math.sin(angle),0));tangent=Vector((-math.sin(angle),math.cos(angle),0))
  for r,z,w,h in ((.73,.09,.14,.14),(.90,.015,.12,.02)):
   loc=radial*r+tangent*(.0015 if angle==0 else -.0015);loc.z=z
   o=box('Recessed end joint face',loc,(w,.002,h),concrete,.0005);o.rotation_euler[2]=angle

def roof_hatch(p):
 metal=mat('Coated galvanized hatch',(.36,.42,.43),.65,.40)
 for x in (-.475,.475):box('Insulated curb side',(x,0,.10),(.10,1.25,.20),metal,.006)
 for y in (-.575,.575):box('Insulated curb end',(0,y,.10),(.85,.10,.20),metal,.006)
 for x in (-.445,.445):box('Opening gasket side',(x,0,.204),(.018,1.10,.012),p['black'],.003)
 for y in (-.535,.535):box('Opening gasket end',(0,y,.204),(.89,.018,.012),p['black'],.003)
 angle=math.radians(-65);hinge=Vector((0,.555,.235))
 def at(x,y,z):
  # Local lid y=0 is the hinge, negative y extends toward its lifted front edge.
  return hinge+Vector((x,y*math.cos(angle)-z*math.sin(angle),y*math.sin(angle)+z*math.cos(angle)))
 lid=box('Raised insulated lid',at(0,-.54,0),(1.04,1.12,.055),metal,.012);lid.rotation_euler[0]=angle
 backing=box('Lid inner liner',at(0,-.54,-.030),(.92,1.00,.012),p['steel'],.004);backing.rotation_euler[0]=angle
 for x in (-.32,.32):
  o=box('Inner lid stiffener',at(x,-.54,-.045),(.035,.94,.028),metal,.004);o.rotation_euler[0]=angle
 for x in (-.36,.36):
  cyl('Heavy hinge barrel',(x,.555,.235),.028,.16,p['steel'],n=24,b=.003,axis=(1,0,0))
  box('Hinge mounting bracket',(x,.575,.202),(.19,.085,.025),metal,.005)
  a=Vector((math.copysign(.435,x),-.34,.145));b=at(x,-.75,-.055);mid=a+(b-a)*.57
  box('Lower stay mounting clevis',(math.copysign(.45,x),-.34,.145),(.09,.07,.055),metal,.004)
  rod('Gas stay outer barrel',a,mid,.018,p['dark']);rod('Gas stay piston',mid,b,.008,p['steel'],12)
  for loc in (a,b):cyl('Stay clevis pivot',loc,.022,.045,p['steel'],n=16,b=.002,axis=(1,0,0))
 pts=[at(-.12,-1.00,-.04),at(-.12,-1.00,-.09),at(.12,-1.00,-.09),at(.12,-1.00,-.04)]
 tube('Inner pull handle',pts,.012,p['dark'])
 box('Front latch receiver',(0,-.62,.145),(.12,.045,.075),p['dark'],.006)
 for x in (-.46,.46):
  for y in (-.47,.47):cyl('Curb flange fastener',(x,y,.203),.010,.009,p['steel'],n=6,b=.001)

def maintenance_ladder(p):
 steel=mat('Galvanized ladder steel',(.43,.49,.51),.8,.35)
 for x in (-.24,.24):
  box('Continuous ladder stile',(x,0,1.90),(.045,.055,3.80),steel,.004)
  box('Ladder ground shoe',(x,0,.015),(.12,.13,.03),steel,.006)
  for z in (.40,1.80,3.25):
   box('Wall stand-off arm',(x,.145,z),(.035,.29,.045),steel,.003)
   box('Wall attachment plate',(x,.292,z),(.14,.018,.18),steel,.004)
   for dz in (-.055,.055):cyl('Wall fixing hex head',(x,.305,z+dz),.010,.012,p['dark'],n=6,b=.001,axis=(0,1,0))
 for i in range(14):
  z=.24+i*.25
  rod('Round climbing rung',(-.24,-.005,z),(.24,-.005,z),.016,steel,20)
  box('Rung traction crest',(0,-.005,z+.015),(.40,.012,.004),p['dark'],.001)
 for z in (1.65,2.20,2.75,3.30,3.77):
  arc_profile('Protective cage hoop',[(.395,z-.023),(.405,z-.023),(.405,z+.023),(.395,z+.023)],-math.pi,0,32,steel,center=(0,-.10,0))
  for side in (-1,1):
   rod('Hoop-to-stile brace',(side*.40,-.10,z),(side*.24,0,z),.012,steel,12)
 for angle in (-math.pi*5/6,-math.pi/2,-math.pi/6):
  x=.40*math.cos(angle);y=-.10+.40*math.sin(angle)
  o=box('Vertical cage retaining strap',(x,y,2.71),(.038,.010,2.17),steel,.002);o.rotation_euler[2]=angle+math.pi/2

def tripod_turnstile(p):
 s=p['steel'];d=p['dark']
 box('Anchored pedestal foot',(-.35,0,.02),(.43,.40,.04),d,.015)
 box('Turnstile pedestal',(-.35,0,.48),(.29,.27,.92),s,.015)
 box('Horizontal mechanism cabinet',(-.18,0,.945),(.80,.36,.23),s,.025)
 box('Dark cabinet top inset',(-.18,0,1.065),(.72,.30,.015),d,.008)
 box('Pedestal service panel',(-.35,-.141,.49),(.22,.012,.66),d,.007)
 cyl('Service panel lock',(-.35,-.151,.74),.012,.007,s,n=16,b=.001,axis=(0,1,0))
 for x in (-.49,-.21):
  for y in (-.13,.13):cyl('Pedestal floor anchor',(x,y,.047),.012,.014,s,n=6,b=.001)
 box('Rotor support housing',(.17,0,.77),(.22,.30,.32),s,.025)
 center=Vector((.17,-.19,.73))
 cyl('Rotor mounting boss',center,.105,.10,d,n=32,b=.008,axis=(0,1,0))
 cyl('Three-arm rotor hub',center+Vector((0,-.064,0)),.080,.055,s,n=32,b=.007,axis=(0,1,0))
 for angle in (math.pi/6,5*math.pi/6,3*math.pi/2):
  v=Vector((math.cos(angle),0,math.sin(angle)))
  pts=[center+v*.065+Vector((0,-.065,0)),center+v*.13+Vector((0,-.14,0)),center+v*.22+Vector((0,-.28,0)),center+v*.42+Vector((0,-.43,0))]
  tube('Radial passage-control arm',pts,.023,s)
  rod('Arm end plug',pts[-2]*.05+pts[-1]*.95,pts[-1]+(pts[-1]-pts[-2]).normalized()*.006,.024,d,20)
 for x in (-.49,.12):
  for z in (.88,1.01):cyl('Cabinet cover screw',(x,-.184,z),.006,.005,d,n=12,b=.0005,axis=(0,1,0))

def tree_grate(p):
 iron=mat('Charcoal cast iron',(.045,.055,.050),.55,.72)
 # Two removable halves separated along x=0; no tree, soil or planter included.
 for side in (-1,1):
  box('Outer side frame',(side*.581,0,.025),(.038,1.20,.05),iron,.003)
  for y in (-.581,.581):box('Split top and bottom frame',(side*.283,y,.025),(.558,.038,.05),iron,.003)
  start,end=(-math.pi/2+.012,math.pi/2-.012) if side==1 else (math.pi/2+.012,3*math.pi/2-.012)
  for radius in (.205,.375,.548):
   arc_profile('Split concentric grate band',[(radius-.007,0),(radius+.007,0),(radius+.007,.05),(radius-.007,.05)],start,end,28,iron)
 for i in range(24):
  angle=math.tau*(i+.5)/24;u=Vector((math.cos(angle),math.sin(angle),0));outer=.581/max(abs(u.x),abs(u.y))
  length=outer-.205;center=u*(.205+length/2);center.z=.0235
  o=box('Radial cast grate rib',center,(length,.014,.047),iron,.002);o.rotation_euler[2]=angle
 for x in (-.555,.555):
  for y in (-.555,.555):
   cyl('Captive perimeter fixing',(x,y,.053),.012,.006,p['steel'],n=6,b=.0007)

def exterior_clock(p):
 cream=mat('Weatherproof clock dial',(.80,.80,.70),0,.53)
 center=Vector((0,0,.325))
 cyl('Weatherproof clock housing',center,.325,.08,p['dark'],n=64,b=.009,axis=(0,1,0))
 cyl('Inset dial face',(0,-.046,.325),.294,.008,cream,n=64,b=.001,axis=(0,1,0))
 bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=10,major_radius=.306,minor_radius=.013,location=(0,-.051,.325),rotation=(math.pi/2,0,0))
 bezel=bpy.context.object;bezel.name='Raised protective bezel';bezel.data.materials.append(p['steel'])
 for face in bezel.data.polygons:face.use_smooth=True
 for i in range(60):
  a=i*math.tau/60;major=i%5==0;r=.254 if major else .263
  o=box('Hour index' if major else 'Minute tick',(r*math.sin(a),-.052,.325+r*math.cos(a)),(.012 if major else .004,.003,.040 if major else .014),p['dark'],.0005);o.rotation_euler[1]=a
 for name,angle,length,width,y in [('Hour hand',-55,.155,.017,-.060),('Minute hand',60,.225,.012,-.067)]:
  a=math.radians(angle);o=box(name,(math.sin(a)*length/2,y,.325+math.cos(a)*length/2),(width,.005,length),p['dark'],.002);o.rotation_euler[1]=a
 box('Static red second hand',(0,-.074,.237),(.003,.003,.210),p['red'],.0005)
 cyl('Hand spindle cap',(0,-.079,.325),.017,.009,p['steel'],n=24,b=.002,axis=(0,1,0))
 box('Rear wall mount',(0,.052,.325),(.18,.028,.40),p['dark'],.008)
 for z in (.19,.46):cyl('Wall mounting boss',(0,.071,z),.024,.018,p['steel'],n=20,b=.002,axis=(0,1,0))

ASSETS=[
 ('city-curb-corner','曲線縁石と側溝','Curved curb corner',curb_corner,'恒久的な道路縁石と浅い側溝を一体化した90度コーナー部材。','A permanent 90-degree precast curb corner with integral shallow gutter; not a portable access ramp.',30),
 ('city-roof-access-hatch','開放状態の屋上出入口','Open roof access hatch',roof_hatch,'開いた断熱蓋、中空の立ち上がり枠、ヒンジ、支持ステー、ハンドルを備える人用屋上ハッチ。','An open personnel roof hatch with hollow coaming, insulated lid, hinges, gas stays and pull handle.',26),
 ('city-maintenance-ladder','保護ケージ付き保守はしご','Caged maintenance ladder',maintenance_ladder,'壁面取付金具、横桟、保護フープと縦帯を備える垂直保守はしご。規格適合は未検証。','A vertical maintenance ladder with wall brackets, rungs, protective hoops and cage straps. Safety-standard compliance has not been validated.',18),
 ('city-tripod-turnstile','三腕式回転ゲート','Tripod turnstile',tripod_turnstile,'台座、機構ケース、接続された3本の回転腕を備える物理的な通行ゲート。','An unbranded mechanical tripod turnstile with anchored pedestal, mechanism cabinet and three connected radial arms.',24),
 ('city-tree-grate','二分割の街路樹グレーチング','Two-piece tree grate',tree_grate,'中央の樹幹開口、放射状スリット、同心円補強帯を備える二分割鋳鉄グレーチング。樹木は含みません。','A two-piece cast-iron tree grate with central trunk opening, radial slots and concentric reinforcement; no tree included.',38),
 ('city-exterior-clock','屋外用壁掛け時計','Exterior wall clock',exterior_clock,'保護リム、目盛、固定された針、背面取付金具を備える無銘の静的壁掛け時計。','A static unbranded exterior wall clock with protective bezel, tick marks, fixed hands and rear mounting hardware.',16)]

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
 parser.add_argument('--only',nargs='*',default=[])
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
 for slug,title,en,builder,ja,desc,elevation in ASSETS:
  if args.only and slug not in args.only:continue
  if (args.output/slug).exists():raise FileExistsError(f'Refusing to overwrite {args.output/slug}')
  common.reset();builder(palette())
  # Bake rotations so shared AABB-based bounds equal actual world mesh extents.
  bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type in ('MESH','CURVE'))
  bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
  common.publish_asset(slug,title,en,ja,desc,['urban-structure','access',slug.removeprefix('city-')],args.output,'scripts/city/access_structures.py',elevation=elevation)
  f=args.output/slug/'asset.json';metadata=json.loads(f.read_text())
  metadata['usages'][0]['sourcePaths']+=['scripts/city/access.py','scripts/city/access_extra.py']
  f.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
