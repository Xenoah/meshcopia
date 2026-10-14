"""Original civic mobility and service equipment. CC BY 4.0; no external assets."""
import bpy, bmesh, math, sys, json, argparse
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).parent))
import common
import civic as g


def materials():
 g.materials()
 for n,c,m,r in [('orange',(.63,.18,.035,1),.3,.38),('machine-yellow',(.74,.43,.035,1),.4,.36),('mirror',(.72,.78,.80,1),1,.065),('chrome',(.55,.61,.64,1),.85,.22),('tire',(.024,.029,.032,1),0,.85),('frame-green',(.075,.19,.15,1),.5,.4),('reflector',(.77,.10,.05,1),.15,.30)]:
  a=bpy.data.materials.new(n);a.use_nodes=True;a.diffuse_color=c;p=a.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=c;p.inputs['Metallic'].default_value=m;p.inputs['Roughness'].default_value=r;g.M[n]=a


def rod(n,a,b,r,mat='steel',vertices=20):
 a=Vector(a);b=Vector(b);return g.cyl(n,(a+b)/2,r,(b-a).length,mat,b-a,vertices,b=min(.002,r*.2))


def poly_tube(n,points,r,mat='steel',res=2):return common.tube(n,points,r,g.M[mat],resolution=res)


def wheel(n,x,y,z,r,w,mat='tire'):
 g.cyl(n+' rubber wheel',(x,y,z),r,w,mat,(0,1,0),32,.008)
 g.cyl(n+' rim',(x,y-w*.51,z),r*.58,.012,'steel',(0,1,0),24,.003)
 g.cyl(n+' opposite rim',(x,y+w*.51,z),r*.58,.012,'steel',(0,1,0),24,.003)
 g.cyl(n+' axle',(x,y,z),r*.15,w+.025,'graphite',(0,1,0),16,.002)
 for side in [-1,1]:g.bolt(n+' axle bolt',(x,y+side*(w/2+.018),z),(0,side,0),r*.14)


def transform_set(objects,matrix):
 for o in objects:o.matrix_world=matrix@o.matrix_world


def mirror():
 g.cyl('Mirror ground footplate',(0,.12,.02),.14,.04,'steel',verts=40,b=.004)
 for a in [i*math.tau/4+math.pi/4 for i in range(4)]:g.bolt('Mirror foundation anchor',(.105*math.cos(a),.12+.105*math.sin(a),.045),r=.008)
 g.cyl('Mirror tubular post',(0,.12,.88),.042,1.72,'graphite',verts=32,b=.005)
 g.cyl('Post foot collar',(0,.12,.09),.055,.10,'steel',b=.004)
 center=Vector((0,0,1.80));before=set(bpy.context.scene.objects)
 shell=g.lathe('Convex mirror backing',[(0,-.07),(.15,-.065),(.31,-.04),(.40,0),(.426,.02),(.425,.052),(.40,.062),(.388,.048)],mat='orange',segments=64)
 # Reflective surface is physically convex, with a 70 mm sag across 780 mm diameter.
 R=.39;sag=.07;sphere_radius=(R*R+sag*sag)/(2*sag)
 profile=[]
 for i in range(25):
  r=R*i/24;depth=.048+sag-(sphere_radius-math.sqrt(sphere_radius*sphere_radius-r*r));profile.append((r,depth))
 face=g.lathe('Convex reflective face',profile,mat='mirror',segments=64)
 for mod in list(face.modifiers):face.modifiers.remove(mod)
 bm=bmesh.new();bm.from_mesh(face.data);bm.normal_update()
 if sum(f.normal.z for f in bm.faces)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(face.data);bm.free()
 g.torus('Mirror retaining gasket',(0,0,.050),.393,.008,'rubber',segments=64)
 g.torus('Rolled orange rim',(0,0,.052),.415,.014,'orange',segments=64)
 rotate=Matrix.Translation(center)@Matrix.Rotation(math.pi/2,4,'X')
 transform_set(set(bpy.context.scene.objects)-before,rotate)
 # Protective visor follows only upper half, projecting beyond the rim.
 angles=[math.radians(10+i*160/32) for i in range(33)];verts=[]
 for y in [.035,-.13]:
  for r in [.422,.449]:verts.extend([(r*math.cos(a),y,1.80+r*math.sin(a)) for a in angles])
 n=len(angles);faces=[]
 for i in range(n-1):
  faces.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
 faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
 me=bpy.data.meshes.new('Mirror weather visor');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Mirror weather visor',me);bpy.context.collection.objects.link(o);g.finish(o,o.name,'orange',.002)
 for a in [i*math.tau/8 for i in range(8)]:
  g.tube('Backing radial stiffening rib',[(.10*math.cos(a),.079,1.80+.10*math.sin(a)),(.21*math.cos(a),.066,1.80+.21*math.sin(a)),(.33*math.cos(a),.046,1.80+.33*math.sin(a))],.009,'orange')
 for z in [1.62,1.88]:
  g.box('Post clamp bracket',(0,.12,z),(.15,.13,.045),'steel',.005)
  for x in [-.052,.052]:g.bolt('Mirror adjustable clamp bolt',(x,.19,z),(0,1,0),.006)
 g.box('Rear ball mounting bracket',(0,.075,1.80),(.15,.065,.22),'graphite',.008)
 g.cyl('Rear tilt pivot',(0,.10,1.80),.055,.19,'steel',(1,0,0),24,.004)
 for x in [-.10,.10]:g.bolt('Tilt adjustment bolt',(x,.10,1.80),(1 if x>0 else -1,0,0),.009)


def boom_gate():
 g.box('Gate anchored base',(0,0,.035),(.48,.47,.07),'graphite',.012)
 for x in [-.17,.17]:
  for y in [-.16,.16]:g.bolt('Gate foundation anchor',(x,y,.076),r=.010)
 g.box('Gate motor cabinet',(0,0,.59),(.37,.38,1.08),'machine-yellow',.030)
 g.box('Motor cabinet weather cap',(0,0,1.148),(.41,.43,.065),'graphite',.018)
 g.door('Gate service access',0,-.198,.56,.29,.79,'machine-yellow')
 for z in [.30,.35,.40]:g.box('Gate lower cooling slot',(0,.194,z),(.20,.006,.012),'dark',.003)
 g.cyl('Main pivot housing',(0,-.245,1.045),.128,.11,'graphite',(0,1,0),48,.006)
 g.cyl('Pivot mounting disc',(0,-.31,1.045),.103,.028,'steel',(0,1,0),40,.003)
 for a in [i*math.tau/6 for i in range(6)]:g.bolt('Hub face bolt',(.077*math.cos(a),-.33,1.045+.077*math.sin(a)),(0,-1,0),.006)
 # Arm extends from a short balanced tail through its hinge to a receiving cradle.
 g.box('Rectangular barrier boom',(1.38,-.35,1.045),(3.42,.08,.105),'cream',.012)
 for x in [.32,.86,1.40,1.94,2.48,2.97]:g.box('Reflective boom band',(x,-.395,1.045),(.23,.008,.086),'reflector',.003)
 for x in [.32,.86,1.40,1.94,2.48,2.97]:g.box('Rear boom band',(x,-.305,1.045),(.23,.008,.086),'reflector',.003)
 g.box('Boom tip cap',(3.11,-.35,1.045),(.05,.095,.12),'rubber',.008)
 g.box('Balanced arm tail',(-.39,-.35,1.005),(.20,.16,.20),'graphite',.018)
 for x in [-.44,-.34]:g.bolt('Counterweight retainer',(x,-.437,1.005),(0,-1,0),.008)
 g.box('Arm pivot saddle',(0,-.35,1.045),(.24,.13,.14),'steel',.008)
 for x in [-.08,.08]:g.bolt('Arm clamp',(x,-.422,1.045),(0,-1,0),.007)
 # Static lowered operating pose; separate receiving stand makes the long span credible.
 g.box('Receiving stand foot',(3.02,-.35,.02),(.22,.22,.04),'steel',.008)
 for x in [2.95,3.09]:g.bolt('Receiver anchor',(x,-.35,.045),r=.008)
 g.box('Receiving stand',(3.02,-.35,.495),(.06,.06,.95),'graphite',.007)
 g.box('Rubber boom rest',(3.02,-.35,.987),(.15,.12,.025),'rubber',.006)
 for y in [-.425,-.275]:g.box('Receiving cradle cheek',(3.02,y,1.027),(.15,.025,.105),'steel',.005)


def pallet_jack():
 # Forks taper at their tips and leave a real center opening.
 for y in [-.25,.25]:
  pts=[(-.42,.135),(.73,.135),(.80,.11),(.80,.08),(-.42,.08)]
  n=len(pts);v=[(x,y+dy,z) for dy in [-.09,.09] for x,z in pts];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  me=bpy.data.meshes.new('Tapered pallet fork');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Tapered pallet fork',me);bpy.context.collection.objects.link(o);g.finish(o,o.name,'machine-yellow',.005)
  for x in [.60,.70]:wheel('Tandem load roller',x,y,.049,.049,.095,'rubber')
  g.box('Fork roller carrier',(.65,y,.094),(.22,.12,.025),'graphite',.005)
  rod('Fork actuating pushrod',(-.47,y,.12),(.55,y,.10),.012,'steel',16)
 g.box('Fork bridging crossmember',(-.47,0,.17),(.27,.68,.20),'machine-yellow',.016)
 for y in [-.25,.25]:g.box('Fork heel reinforcement',(-.40,y,.21),(.17,.19,.15),'machine-yellow',.012)
 # Steering axle, paired wheels and a visible hydraulic pump/piston.
 for y in [-.105,.105]:wheel('Rear steering wheel',-.63,y,.09,.09,.065)
 g.cyl('Steering kingpin',(-.63,0,.20),.055,.19,'steel',verts=28,b=.006)
 g.box('Steering bogie crown',(-.63,0,.205),(.19,.32,.035),'graphite',.007)
 for yy in [-.15,-.06,.06,.15]:g.box('Steering wheel fork cheek',(-.63,yy,.15),(.08,.012,.14),'steel',.004)
 g.cyl('Hydraulic ram body',(-.56,0,.30),.058,.22,'graphite',verts=32,b=.008)
 g.cyl('Polished hydraulic piston',(-.56,0,.445),.029,.13,'chrome',verts=24,b=.003)
 g.cyl('Ram upper pivot',(-.54,0,.50),.026,.18,'steel',(0,1,0),24,.003)
 for y in [-.12,.12]:rod('Lifting linkage',(-.55,y,.47),(-.39,y,.26),.018,'machine-yellow',20)
 g.cyl('Handle lower pivot',(-.70,0,.29),.034,.21,'steel',(0,1,0),24,.004)
 rod('Pull handle stem',(-.70,0,.30),(-.91,0,1.03),.026,'graphite',24)
 g.tube('Loop pull handle',[(-.91,0,1.01),(-.94,-.14,1.04),(-.97,-.17,1.20),(-.98,0,1.25),(-.97,.17,1.20),(-.94,.14,1.04),(-.91,0,1.01)],.021,'graphite')
 rod('Rubber handle grip',(-.98,-.135,1.235),(-.98,.135,1.235),.026,'rubber',24)
 rod('Release control lever',(-.975,-.07,1.19),(-.975,.07,1.19),.009,'steel',16)
 g.tube('Hydraulic release cable',[(-.98,0,1.19),(-.89,.03,.94),(-.73,.04,.36),(-.58,.02,.24)],.003,'rubber')
 g.cyl('Pump service cap',(-.56,0,.42),.067,.025,'steel',verts=24,b=.003)


def caster(n,x,y):
 # A fork bracket around each freely rolling wheel, with an upright swivel bearing.
 wheel(n,x+.018,y,.063,.063,.034)
 g.cyl(n+' swivel bearing',(x,y,.153),.025,.045,'steel',verts=24,b=.003)
 g.box(n+' fork crown',(x+.006,y,.128),(.075,.072,.018),'chrome',.004)
 for yy in [y-.03,y+.03]:g.box(n+' fork cheek',(x+.017,yy,.099),(.059,.013,.07),'steel',.004)


def trolley():
 for x in [-.36,.36]:
  for y in [-.22,.22]:caster('Shopping trolley caster',x,y)
 poly_tube('Lower chassis perimeter',[(-.43,-.23,.19),(.44,-.23,.19),(.44,.23,.19),(-.43,.23,.19),(-.43,-.23,.19)],.016,'chrome',3)
 for y in [-.22,.22]:
  g.tube('Basket support frame',[(-.42,y,.19),(-.46,y,.35),(-.40,y,.80),(-.47,y,.94),(-.54,y,1.02)],.014,'chrome')
  rod('Front basket support',(.37,y,.19),(.34,y,.43),.013,'chrome',20)
 # Basket widens upward. Each wire is real round geometry, with no filled faces.
 def cross(z):
  t=(z-.39)/.51;return (-.30-.12*t,.34+.10*t,.20+.09*t)
 for z in [.39,.49,.59,.69,.79,.90]:
  rear,front,half=cross(z);poly_tube('Basket horizontal wire',[(rear,-half,z),(front,-half,z),(front,half,z),(rear,half,z)],.004 if z<.90 else .010,'chrome',2)
 for ysign in [-1,1]:
  for i in range(14):
   t=i/13;rod('Basket side upright wire',(-.30+.64*t,ysign*.20,.39),(-.42+.86*t,ysign*.29,.90),.0038,'chrome',12)
 for i in range(12):
  t=-1+2*i/11;rod('Basket front upright wire',(.34,.20*t,.39),(.44,.29*t,.90),.0038,'chrome',12)
 for i in range(12):
  x=-.30+.64*i/11;rod('Basket floor longitudinal wire',(x,-.20,.39),(x,.20,.39),.0038,'chrome',12)
 for y in [-.16,-.08,0,.08,.16]:rod('Basket floor cross wire',(-.30,y,.39),(.34,y,.39),.0038,'chrome',12)
 # Hinged rear nesting gate follows the same tapered opening and has open wire infill.
 for z in [.42,.54,.66,.78,.88]:
  rear,front,half=cross(z);rod('Nesting gate horizontal wire',(rear,-half,z),(rear,half,z),.004,'chrome',12)
 for i in range(9):
  t=-1+2*i/8;rod('Nesting gate upright wire',(-.307,.207*t,.42),(-.415,.285*t,.88),.0038,'chrome',12)
 rod('Rear gate upper hinge bar',(-.42,-.29,.90),(-.42,.29,.90),.008,'chrome',20)
 for y in [-.28,.28]:g.cyl('Rear gate hinge barrel',(-.42,y,.90),.014,.05,'steel',(0,1,0),20,.002)
 for y in [-.29,.29]:g.tube('Handle support',[(-.42,y,.90),(-.51,y,.98),(-.54,y,1.02)],.014,'chrome')
 rod('Original blank trolley handle',(-.54,-.30,1.02),(-.54,.30,1.02),.022,'red',28)
 for y in [-.31,.31]:g.cyl('Handle end plug',(-.54,y,1.02),.024,.025,'graphite',(0,1,0),24,.003)
 poly_tube('Lower tray rim',[(-.33,-.20,.21),(.37,-.20,.21),(.37,.20,.21),(-.33,.20,.21),(-.33,-.20,.21)],.006,'chrome',2)
 for x in [-.33,.37]:
  for side in [-1,1]:rod('Tray support weld',(x,side*.20,.21),(x,side*.23,.19),.006,'chrome',12)
 # Lower tray is also open wire, useful for bulky goods without hiding chassis.
 for x in [-.28,-.16,-.04,.08,.20,.32]:rod('Lower tray wire',(x,-.20,.21),(x,.20,.21),.004,'chrome',12)
 for y in [-.15,0,.15]:rod('Lower tray crossbar',(-.33,y,.21),(.37,y,.21),.005,'chrome',12)


def mixer():
 # Triangulated wheeled frame with a separate fixed support foot.
 for y in [-.36,.36]:wheel('Mixer transport wheel',-.30,y,.15,.15,.065)
 rod('Transport wheel axle',(-.30,-.41,.15),(-.30,.41,.15),.021,'steel',24)
 for y in [-.28,.28]:
  rod('Lower chassis rail',(-.32,y,.22),(.41,y,.20),.025,'frame-green',24)
  rod('Yoke support leg',(-.30,y,.20),(-.02,y,.76),.026,'frame-green',24)
  rod('Front tripod leg',(.42,y,.06),(-.02,y,.76),.024,'frame-green',24)
  g.box('Mixer fixed front foot',(.42,y,.025),(.16,.09,.05),'rubber',.012)
 rod('Frame rear crossbar',(-.30,-.30,.23),(-.30,.30,.23),.023,'frame-green',24)
 rod('Frame front crossbar',(.37,-.29,.20),(.37,.29,.20),.023,'frame-green',24)
 # Yoke and tilt bearings outside the drum leave its internal volume clear.
 for y in [-.34,.34]:
  g.box('Tilting yoke upright',(-.015,y,.82),(.07,.055,.40),'frame-green',.012)
  g.cyl('Yoke bearing',(-.015,y,.98),.068,.07,'steel',(0,1,0),32,.004)
 g.box('Yoke lower crossbar',(-.015,0,.63),(.075,.70,.055),'frame-green',.010)
 before=set(bpy.context.scene.objects)
 drum=g.lathe('Hollow concrete mixing drum',[(0,-.27),(.12,-.27),(.25,-.15),(.29,.08),(.25,.27),(.21,.38),(.215,.40),(.19,.40),(.185,.37),(.225,.25),(.265,.08),(.225,-.12),(.11,-.23),(0,-.23)],mat='orange',segments=64)
 for mod in list(drum.modifiers):drum.modifiers.remove(mod)
 g.torus('Reinforced drum mouth',(0,0,.395),.204,.012,'steel',segments=64)
 g.torus('External drum stiffening rib',(0,0,.075),.292,.010,'orange',segments=64)
 g.torus('Drum ring gear backing',(0,0,-.025),.280,.015,'steel',segments=64)
 for a in [i*math.tau/40 for i in range(40)]:
  tooth=g.box('Cast ring gear tooth',(.293*math.cos(a),.293*math.sin(a),-.025),(.032,.022,.028),'steel',.002);tooth.rotation_euler[2]=a
 g.cyl('Drum rear spindle',(0,0,-.30),.055,.12,'steel',verts=32,b=.004)
 for a in [0,math.tau/3,2*math.tau/3]:
  o=g.box('Internal mixing paddle',(.213*math.cos(a),.213*math.sin(a),.035),(.055,.022,.30),'steel',.005);o.rotation_euler[2]=a;o.rotation_euler[1]=-.12
 rot=Vector((.60,0,.80)).to_track_quat('Z','Y').to_matrix().to_4x4()
 transform_set(set(bpy.context.scene.objects)-before,Matrix.Translation((.02,0,1.0))@rot)
 g.box('Rear motor housing',(-.33,0,.84),(.24,.31,.21),'frame-green',.022)
 for y in [-.105,-.052,0,.052,.105]:g.box('Motor cooling fin',(-.46,y,.84),(.014,.015,.15),'steel',.002)
 g.box('Motor switch',(-.345,-.164,.85),(.072,.022,.057),'graphite',.007)
 g.box('Motor stop button',(-.345,-.18,.85),(.035,.012,.027),'red',.004)
 g.cyl('Tilt wheel spindle',(-.015,-.43,.98),.023,.18,'steel',(0,1,0),24,.003)
 g.torus('Tilt handwheel',(-.015,-.505,.98),.16,.013,'graphite',(0,1,0),segments=48)
 for a in [0,math.tau/3,2*math.tau/3]:rod('Tilt handwheel spoke',(-.015,-.505,.98),(-.015+.15*math.cos(a),-.505,.98+.15*math.sin(a)),.009,'steel',16)
 g.cyl('Tilt index plate',(-.015,-.37,.98),.105,.015,'steel',(0,1,0),40,.003)
 for a in [i*math.tau/8 for i in range(8)]:g.cyl('Tilt index recess',(-.015+.078*math.cos(a),-.38,.98+.078*math.sin(a)),.008,.003,'dark',(0,1,0),12,.0005)
 g.tube('Tilt locking lever',[(-.01,-.43,.85),(.12,-.43,.75),(.24,-.43,.74)],.009,'steel')


ASSETS=[
 ('city-convex-mirror','街路凸面ミラー','Street convex safety mirror','実際に凸状に湾曲した鏡面、ひさし、背面金具と固定支柱を備えた汎用ミラー。','Unbranded convex mirror with physically curved reflective surface, weather visor, adjustable rear brackets and anchored tubular post. Reflections depend on your renderer and lighting.',mirror,['mirror','safety','street','ミラー']),
 ('city-parking-boom-gate','駐車場遮断バー','Parking boom gate','回転軸、釣合いおもり、モーター収納箱と受け支柱を備えた下がった状態の遮断バー。','Lowered parking boom with pivot hub, arm clamp, counterweight, service cabinet and receiving cradle. Static visual assembly, not an operational access-control system.',boom_gate,['parking','gate','barrier','遮断機']),
 ('city-pallet-jack','ハンドパレットトラック','Manual pallet jack','テーパーフォーク、荷重ローラー、操舵車輪、油圧シリンダーと操作ハンドルを個別に造形したパレットジャック。','Manual pallet jack with tapered forks, tandem load rollers, paired steering wheels, hydraulic ram, lifting linkage and loop handle.',pallet_jack,['pallet','jack','warehouse','運搬']),
 ('city-shopping-trolley','ワイヤー買い物カート','Wire shopping trolley','実際に隙間のあるワイヤーバスケット、可動式に見える後部ゲート、下段トレーと4つのキャスターを備えたカート。','Shopping trolley with genuinely open tapered wire basket, rear nesting gate, lower wire tray, tubular chassis and four detailed swivel casters.',trolley,['shopping','trolley','cart','買い物']),
 ('city-concrete-mixer','小型コンクリートミキサー','Compact concrete mixer','内部の羽根が見える中空ドラム、支持ヨーク、傾斜ハンドルと運搬車輪を備えた小型ミキサー。','Compact mixer with hollow tilted drum, internal mixing paddles, support yoke, tilt handwheel, motor housing and transport wheels. Static visualization prop.',mixer,['mixer','construction','machine','ミキサー'])]

if __name__=='__main__':
 argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
 p=argparse.ArgumentParser();p.add_argument('--output','--out',dest='output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox');p.add_argument('--only',choices=[r[0] for r in ASSETS]);a=p.parse_args(argv)
 selected=[r for r in ASSETS if not a.only or r[0]==a.only];conflicts=[str(a.output/r[0]) for r in selected if (a.output/r[0]).exists()]
 if conflicts:p.error('Refusing to overwrite: '+', '.join(conflicts))
 for slug,ja,en,dj,de,fn,tags in selected:
  common.reset();materials();fn()
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
  common.publish_asset(slug,ja,en,dj,de,tags,str(a.output),'scripts/city/civic_mobility.py')
  f=a.output/slug/'asset.json';data=json.loads(f.read_text());data['usages'][0]['sourcePaths'].append('scripts/city/civic.py');f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  if slug=='city-convex-mirror':
   bpy.ops.object.light_add(type='AREA',location=(-1.2,-3,1.1));softbox=bpy.context.object;softbox.name='Preview reflection softbox';softbox.data.energy=90;softbox.data.shape='RECTANGLE';softbox.data.size=1.2;softbox.data.size_y=2.8;common.look_at(softbox,(0,-.10,1.8))
   common.render(a.output/slug/'preview.png');common.render(a.output/'_qa'/f'{slug}-back.png',azimuth=125);bpy.data.objects.remove(softbox,do_unlink=True)
