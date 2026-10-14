"""Original unbranded commuter bicycle. CC BY 4.0. Static visualization assembly."""
import bpy, math, sys, argparse, json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import common
import civic as g


def materials():
 g.materials()
 for n,c,m,r in [('cycle-teal',(.045,.22,.24,1),.45,.34),('chrome',(.57,.62,.65,1),.85,.24),('tire',(.018,.023,.026,1),0,.85),('saddle',(.035,.045,.047,1),0,.76),('chain-steel',(.30,.32,.29,1),.8,.35),('lens',(.79,.84,.72,1),.15,.18),('reflector-red',(.65,.035,.018,1),.2,.28)]:
  mat=bpy.data.materials.new(n);mat.use_nodes=True;mat.diffuse_color=c;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=c;p.inputs['Metallic'].default_value=m;p.inputs['Roughness'].default_value=r;g.M[n]=mat


def rod(n,a,b,r,mat='chrome',vertices=16):
 a=Vector(a);b=Vector(b);small=r<.0035;o=g.cyl(n,(a+b)/2,r,(b-a).length,mat,b-a,vertices,b=0 if small else min(r*.15,.0015))
 if small:
  for face in o.data.polygons:face.use_smooth=abs(face.normal.z)<.5
 return o


def wire(n,points,r=.0025,mat='graphite'):
 return g.tube(n,points,r,mat)


def ring(n,center,r,t,mat='chrome',segments=64):
 return common.torus(n,center,r,t,g.M[mat],rotation=(math.pi/2,0,0),segments=segments)


def wheel(n,cx):
 cz=.356
 ring(n+' inflated commuter tire',(cx,0,cz),.329,.027,'tire',72)
 for y in [-.014,.014]:ring(n+' rim lip',(cx,y,cz),.308,.009,'chrome',64)
 ring(n+' rim channel',(cx,0,cz),.305,.010,'graphite',64)
 g.cyl(n+' hub body',(cx,0,cz),.022,.105,'chrome',(0,1,0),24,.003)
 for y in [-.042,.042]:g.cyl(n+' spoke flange',(cx,y,cz),.036,.007,'chrome',(0,1,0),32,.001)
 # Cross-laced spokes, alternating flange side and tangent direction.
 for i in range(32):
  a=i*math.tau/32;side=-1 if i%2 else 1;ha=a+(0.22 if (i//2)%2 else -.22)
  inner=(cx+.033*math.cos(ha),side*.042,cz+.033*math.sin(ha))
  outer=(cx+.303*math.cos(a),side*.009,cz+.303*math.sin(a))
  rod(n+' stainless spoke',inner,outer,.00145,'chrome',10)
  direction=Vector(outer)-Vector(inner);nip=g.cyl(n+' spoke nipple',outer,.0025,.012,'steel',direction,10,0)
  for face in nip.data.polygons:face.use_smooth=abs(face.normal.z)<.5
 for side in [-1,1]:
  g.cyl(n+' axle end',(cx,side*.064,cz),.009,.025,'steel',(0,1,0),12,.001)
  g.bolt(n+' axle nut',(cx,side*.078,cz),(0,side,0),.008)
 # A valve belongs to the rim, offset from the spoke pattern.
 a=.42;rod(n+' valve stem',(cx+.287*math.cos(a),0,cz+.287*math.sin(a)),(cx+.307*math.cos(a),0,cz+.307*math.sin(a)),.003,'steel',12)


def fender(n,cx,start,end):
 count=48;angles=[math.radians(start+(end-start)*i/count) for i in range(count+1)]
 verts=[]
 for radius in [.367,.373]:
  for y in [-.036,.036]:verts.extend([(cx+radius*math.cos(a),y,.356+radius*math.sin(a)) for a in angles])
 k=len(angles);faces=[]
 for i in range(k-1):
  faces.extend([(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),(i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)])
 faces.extend([(0,k,3*k,2*k),(k-1,3*k-1,4*k-1,2*k-1)])
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);g.finish(o,n,'graphite',.001)
 # Stay wires attach outside the tire and end on the fender edges.
 for side in [-1,1]:
  for a in [math.radians(35),math.radians(145)]:rod(n+' support stay',(cx,side*.055,.356),(cx+.37*math.cos(a),side*.037,.356+.37*math.sin(a)),.0026,'chrome',12)


def brake(n,cx,cz):
 for side in [-1,1]:
  g.box(n+' brake pad',(cx,side*.031,cz),(.045,.012,.018),'rubber',.004)
  rod(n+' pad fixing pin',(cx,side*.035,cz),(cx,side*.063,cz),.004,'steel',12)
  rod(n+' cantilever arm',(cx,side*.062,cz-.023),(cx-.012,side*.095,cz+.067),.006,'chrome',14)
  g.bolt(n+' pivot screw',(cx,side*.07,cz-.023),(0,side,0),.005)
 rod(n+' cable straddle',(cx-.012,-.095,cz+.067),(cx-.012,.095,cz+.067),.002,'steel',10)


def chain():
 rear=Vector((-.50,.356));front=Vector((-.10,.34));r0=.052;r1=.105;delta=front-rear
 phi=math.atan2(delta.y,delta.x);theta=math.acos((r0-r1)/delta.length);top=phi+theta;bottom=phi-theta
 points=[rear+Vector((math.cos(top),math.sin(top)))*r0,front+Vector((math.cos(top),math.sin(top)))*r1]
 points +=[front+Vector((math.cos(top+(bottom-top)*i/32),math.sin(top+(bottom-top)*i/32)))*r1 for i in range(1,33)]
 points +=[rear+Vector((math.cos(bottom),math.sin(bottom)))*r0]
 points +=[rear+Vector((math.cos(bottom+(top-math.tau-bottom)*i/28),math.sin(bottom+(top-math.tau-bottom)*i/28)))*r0 for i in range(1,29)]
 points.append(points[0]);lengths=[0]
 for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+(b-a).length)
 count=88;samples=[];j=0
 for i in range(count):
  distance=lengths[-1]*i/count
  while j<len(lengths)-2 and lengths[j+1]<distance:j+=1
  t=(distance-lengths[j])/max(lengths[j+1]-lengths[j],1e-8);samples.append(points[j].lerp(points[j+1],t))
 for i,a in enumerate(samples):
  b=samples[(i+1)%count];mid=(a+b)/2;angle=-math.atan2(b.y-a.y,b.x-a.x)
  roller=g.cyl('Chain roller',(a.x,-.097,a.y),.0032,.017,'chain-steel',(0,1,0),10,0)
  for face in roller.data.polygons:face.use_smooth=abs(face.normal.z)<.5
  for side in [-1,1]:
   plate=g.box('Individual chain link plate',(mid.x,-.097+side*.009,mid.y),((b-a).length+.004,.0022,.0065),'chain-steel',0);plate.rotation_euler[1]=angle


def bicycle():
 wheel('Rear wheel',-.50);wheel('Front wheel',.58)
 bb=(-.10,0,.34);seat=(-.23,0,.88);htop=(.40,0,.90);hbottom=(.44,0,.73)
 rod('Seat tube',bb,seat,.021,'cycle-teal',28)
 rod('Down tube',bb,hbottom,.024,'cycle-teal',28)
 rod('Top tube',(-.232,0,.865),(.405,0,.885),.019,'cycle-teal',28)
 rod('Head tube',hbottom,htop,.027,'cycle-teal',28)
 g.cyl('Bottom bracket shell',bb,.032,.15,'cycle-teal',(0,1,0),32,.004)
 for side in [-1,1]:
  wire('Chain stay',[(-.10,side*.045,.34),(-.29,side*.067,.325),(-.50,side*.060,.356)],.012,'cycle-teal')
  rod('Seat stay',(-.235,side*.025,.84),(-.50,side*.060,.356),.010,'cycle-teal',20)
  wire('Swept front fork',[(.44,side*.035,.73),(.48,side*.052,.56),(.56,side*.060,.39),(.58,side*.060,.356)],.012,'cycle-teal')
  for x in [-.50,.58]:g.box('Axle dropout',(x,side*.058,.356),(.06,.012,.045),'steel',.006)
 g.box('Fork crown',(.442,0,.735),(.065,.135,.035),'cycle-teal',.010)
 # Headset, quill, stem and one-piece swept handlebar.
 for x,z in [(.438,.74),(.401,.897)]:g.cyl('Headset bearing',(x,0,z),.031,.023,'chrome',(-.23,0,1),28,.003)
 rod('Quill stem',(.40,0,.89),(.378,0,.985),.015,'chrome',24)
 rod('Handlebar stem',(.378,0,.982),(.47,0,1.022),.016,'chrome',24)
 g.cyl('Stem clamp bolt',(.445,0,1.021),.007,.018,'steel',verts=12,b=.001)
 wire('Swept commuter handlebar',[(.49,-.30,1.01),(.455,-.20,1.03),(.47,0,1.03),(.455,.20,1.03),(.49,.30,1.01)],.012,'chrome')
 for side in [-1,1]:
  rod('Textured rubber hand grip',(.481,side*.235,1.016),(.495,side*.315,1.005),.018,'rubber',24)
  g.cyl('Handlebar grip plug',(.496,side*.319,1.004),.0185,.009,'graphite',(0,1,0),20,.002)
  g.box('Brake lever clamp',(.465,side*.198,1.014),(.036,.024,.035),'graphite',.006)
  wire('Hand brake lever',[(.475,side*.196,1.007),(.523,side*.192,.975),(.532,side*.245,.965)],.0055,'chrome')
 # Seatpost and a rounded, narrow-nosed saddle with supporting rails.
 rod('Seatpost',(-.23,0,.86),(-.26,0,1.015),.014,'chrome',24)
 g.cyl('Seatpost collar',(-.235,0,.91),.025,.024,'graphite',(-.19,0,1),24,.003)
 g.bolt('Seatpost clamp screw',(-.235,-.03,.91),(0,-1,0),.005)
 outline=[(-.385,-.066),(-.32,-.087),(-.225,-.074),(-.11,-.027),(-.105,.027),(-.225,.074),(-.32,.087),(-.385,.066)]
 n=len(outline);v=[(x,y,z) for z in [1.015,1.065] for x,y in outline];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new('Commuter saddle');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Commuter saddle',me);bpy.context.collection.objects.link(o);g.finish(o,o.name,'saddle',.014)
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 sub=o.modifiers.new('Rounded saddle padding','SUBSURF');sub.levels=2;sub.render_levels=2
 for y in [-.032,.032]:wire('Saddle support rail',[(-.35,y,1.02),(-.30,y,.99),(-.20,y,.99),(-.145,y,1.02)],.004,'chrome')
 # Detailed single-speed drive, deliberately aligned to one coherent chain plane.
 ring('Chainring machined rim',(-.10,-.097,.34),.088,.008,'chrome',48)
 g.cyl('Chainring center boss',(-.10,-.097,.34),.025,.022,'steel',(0,1,0),24,.002)
 for a in [i*math.tau/5 for i in range(5)]:rod('Chainring spider',(-.10,-.097,.34),(-.10+.085*math.cos(a),-.097,.34+.085*math.sin(a)),.006,'chrome',12)
 for a in [i*math.tau/36 for i in range(36)]:
  o=g.box('Chainring tooth',(-.10+.100*math.cos(a),-.097,.34+.100*math.sin(a)),(.012,.006,.007),'steel',.001);o.rotation_euler[1]=-a
 for y,r in [(-.065,.041),(-.078,.046),(-.091,.052)]:
  g.cyl('Rear sprocket cluster',(-.50,y,.356),r,.008,'steel',(0,1,0),32,.001)
 chain()
 for side in [-1,1]:
  end=Vector((.057,-.128,.307)) if side==-1 else Vector((-.257,.128,.373))
  start=Vector((-.10,side*.128,.34));rod('Crank arm',start,end,.012,'chrome',20)
  g.cyl('Crank bolt',start,.010,.015,'graphite',(0,1,0),12,.001)
  pedal_center=end+Vector((0,side*.048,0))
  rod('Pedal spindle',end,pedal_center,.006,'steel',12)
  x,y,z=pedal_center
  for xx in [x-.047,x+.047]:g.box('Pedal side rail',(xx,y,z),(.014,.075,.022),'graphite',.003)
  for yy in [y-.033,y+.033]:g.box('Pedal end rail',(x,yy,z),(.09,.012,.022),'graphite',.003)
  for xx in [x-.026,x,x+.026]:g.box('Pedal traction rib',(xx,y,z+.006),(.006,.065,.016),'rubber',.001)
  g.box('Pedal amber reflector',(x,y+side*.042,z),(.05,.006,.013),'yellow',.002)
 # Rim brakes and two separate cable runs, not a decorative disconnected loop.
 brake('Front rim brake',.44,.624);brake('Rear rim brake',-.41,.647)
 wire('Front brake cable',[(.49,-.195,.994),(.54,-.14,.91),(.46,-.08,.80),(.428,-.095,.691)],.0025,'graphite')
 wire('Rear brake cable',[(.49,.195,.994),(.34,.11,.98),(.27,-.026,.91),(-.19,-.027,.887),(-.33,-.08,.78),(-.422,-.095,.714)],.0025,'graphite')
 fender('Front metal mudguard',.58,-28,204);fender('Rear metal mudguard',-.50,-17,222)
 # Functional-looking rear rack joins both rear dropouts and seat area.
 poly=[(-.76,-.075,.782),(-.23,-.075,.782),(-.23,.075,.782),(-.76,.075,.782),(-.76,-.075,.782)]
 common.tube('Rear rack perimeter',poly,.006,g.M['graphite'],resolution=3)
 for side in [-1,1]:
  rod('Rear rack leg',(-.50,side*.065,.356),(-.72,side*.075,.782),.005,'chrome',12)
  rod('Rear rack forward brace',(-.23,side*.075,.782),(-.225,side*.025,.855),.005,'chrome',12)
 for x in [-.68,-.58,-.48,-.38,-.28]:rod('Rack cross slat',(x,-.075,.782),(x,.075,.782),.005,'graphite',12)
 g.box('Rear reflector bracket',(-.774,0,.763),(.016,.10,.055),'graphite',.004)
 g.box('Rear red reflector',(-.785,0,.763),(.01,.078,.035),'reflector-red',.004)
 rod('Headlight bracket',(.445,0,.92),(.49,0,.94),.006,'steel',12)
 g.cyl('Compact headlight body',(.505,0,.946),.027,.048,'graphite',(1,0,.12),28,.005)
 g.cyl('Headlight lens',(.531,0,.949),.022,.007,'lens',(1,0,.12),28,.002)
 # Kickstand in its static deployed pose, kept clear of crank and rear wheel.
 wire('Deployed kickstand',[(-.135,.045,.335),(-.17,.12,.24),(-.255,.18,.012)],.007,'steel')
 g.box('Kickstand rubber foot',(-.255,.18,.012),(.035,.024,.021),'rubber',.005)


if __name__=='__main__':
 argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
 p=argparse.ArgumentParser();p.add_argument('--output','--out',dest='output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox');p.add_argument('--only',choices=['city-commuter-bicycle']);a=p.parse_args(argv)
 slug='city-commuter-bicycle'
 if (a.output/slug).exists():p.error('Refusing to overwrite existing asset directory')
 common.reset();materials();bicycle()
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 common.publish_asset(slug,'シティコミューターバイク','City commuter bicycle','ダイヤモンドフレーム、スポーク車輪、連続したリンクチェーン、クランク、ブレーキ、泥よけと荷台を備えた街乗り自転車。','Unbranded commuter bicycle with diamond frame, cross-laced spokes, linked chain drive, cranks, pedals, rim brakes and cables, fenders, rear rack and lights. Static visualization assembly, not a rideable or engineering-validated design.',['bicycle','commuter','transport','自転車'],str(a.output),'scripts/city/civic_bicycle.py',azimuth=-72,elevation=18)
 f=a.output/slug/'asset.json';data=json.loads(f.read_text());data['usages'][0]['sourcePaths'].append('scripts/city/civic.py');f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
