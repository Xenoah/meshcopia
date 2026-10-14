"""Original recreation and small public-service props. CC BY 4.0.
Static visualization geometry only; no safety, accessibility or medical certification.
"""
import bpy,math,sys,json,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from access import box,cyl,tube,mesh,extrude_x,palette,mat
from access_extra import split_surface
from access_structures import rod


def ring(name,loc,major,minor,material,major_segments=48,minor_segments=10,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=major_segments,minor_segments=minor_segments,major_radius=major,minor_radius=minor,location=loc,rotation=rotation)
 obj=bpy.context.object;obj.name=name;obj.data.materials.append(material)
 for f in obj.data.polygons:f.use_smooth=True
 return obj

def closed_rope(name,points,radius,material):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=2;curve.use_fill_caps=False
 spline=curve.splines.new('POLY');spline.points.add(len(points)-1);spline.use_cyclic_u=True
 for v,point in zip(spline.points,points):v.co=(*point,1)
 obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);curve.materials.append(material)
 return obj


def ellipse_link(name,center,material,alternate=False):
 n=12;k=6;a=.012;b=.030;r=.0035;v=[]
 for i in range(n):
  t=i*math.tau/n;out=Vector((math.cos(t)/a,0,math.sin(t)/b)).normalized();c=Vector((a*math.cos(t),0,b*math.sin(t)))
  for j in range(k):
   q=c+out*(r*math.cos(j*math.tau/k))+Vector((0,r*math.sin(j*math.tau/k),0))
   if alternate:q.x,q.y=q.y,q.x
   v.append(Vector(center)+q)
 faces=[(i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k) for i in range(n) for j in range(k)]
 return split_surface(name,v,faces,material,[])

def playground_swing(p):
 blue=mat('Play frame blue coating',(.035,.17,.25),.35,.45)
 for x in (-1.45,1.45):
  for y in (-.95,.95):
   box('Ground anchoring shoe',(x,y,.014),(.18,.18,.028),p['dark'],.008)
   rod('A-frame structural leg',(x,y,.035),(x,0,2.32),.045,blue,24)
   for dx in (-.055,.055):cyl('Foot anchoring bolt',(x+dx,y,.036),.012,.014,p['steel'],n=6,b=.001)
  rod('A-frame spreader brace',(x,-.62,.80),(x,.62,.80),.028,blue,20)
  box('Apex reinforcing saddle',(x,0,2.305),(.14,.15,.16),blue,.018)
  cyl('Apex through bolt',(x,-.083,2.30),.022,.026,p['steel'],n=6,b=.002,axis=(0,1,0))
 rod('Continuous top beam',(-1.60,0,2.32),(1.60,0,2.32),.055,blue,32)
 for x in (-.215,.215):
  box('Hanger clamp',(x,0,2.315),(.09,.14,.11),p['steel'],.014)
  ring('Suspension shackle',(x,0,2.255),.018,.006,p['steel'],24,8,rotation=(math.pi/2,0,0))
  links=[ellipse_link('Alternating welded chain link',(x,0,.606+i*.052),p['steel'],bool(i%2)) for i in range(32)]
  bpy.ops.object.select_all(action='DESELECT')
  for link in links:link.select_set(True)
  bpy.context.view_layer.objects.active=links[0];bpy.ops.object.join()
  bpy.context.object.name='Left suspension chain' if x<0 else 'Right suspension chain'
  box('Seat chain fixing tab',(x,0,.568),(.028,.07,.060),p['steel'],.004)
  ring('Seat attachment eye',(x,0,.590),.012,.004,p['steel'],20,6,rotation=(math.pi/2,0,0))
 box('Rubber swing seat',(0,0,.540),(.50,.22,.055),p['rubber'],.018)
 box('Seat steel reinforcement',(0,0,.514),(.45,.17,.012),p['dark'],.004)
 for y in (-.070,0,.070):box('Molded seat grip rib',(0,y,.569),(.40,.008,.004),p['black'],.001)

def catmull(points,subdiv=6):
 pts=[Vector(p) for p in points];result=[]
 for i in range(len(pts)-1):
  a=pts[max(i-1,0)];b=pts[i];c=pts[i+1];d=pts[min(i+2,len(pts)-1)]
  for j in range(subdiv):
   t=j/subdiv;result.append((2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)*.5)
 result.append(pts[-1]);return result

def playground_slide(p):
 blue=mat('Slide frame blue coating',(.025,.15,.22),.35,.47)
 orange=mat('Molded slide chute',(.80,.20,.035),0,.44)
 path=catmull([(.65,1.65),(.35,1.60),(.08,1.40),(-.30,1.02),(-.70,.64),(-1.08,.30),(-1.40,.13),(-1.70,.12)])
 section=[(-.36,0),(-.36,.16),(-.33,.16),(-.29,.025),(.29,.025),(.33,.16),(.36,.16),(.36,0)]
 n=len(path);v=[]
 for x,offset in section:
  for i,point in enumerate(path):
   tangent=path[min(i+1,n-1)]-path[max(i-1,0)];normal=Vector((tangent.y,-tangent.x)).normalized()
   yz=point+normal*offset;v.append((x,yz.x,yz.y))
 faces=[]
 for j in range(len(section)):
  k=(j+1)%len(section);faces.extend((j*n+i,j*n+i+1,k*n+i+1,k*n+i) for i in range(n-1))
 faces.extend((tuple(j*n for j in reversed(range(len(section)))),tuple(j*n+n-1 for j in range(len(section)))))
 sharp=[(j*n+i,j*n+i+1) for j in range(len(section)) for i in range(n-1)]
 sharp += [(j*n+i,((j+1)%len(section))*n+i) for j in range(len(section)) for i in (0,n-1)]
 split_surface('Continuous curved chute and raised sides',v,faces,orange,sharp,flat_faces=(len(faces)-2,len(faces)-1))
 box('Upper platform deck',(0,.925,1.645),(1.0,.59,.06),p['dark'],.009)
 for x in (-.49,.49):
  for y in (.72,1.18):
   box('Support foot',(x,y,.015),(.16,.16,.03),p['dark'],.007)
   rod('Platform structural upright',(x,y,.03),(x,y,2.075),.032,blue,20)
   cyl('Ground fastener',(x,y,.039),.012,.016,p['steel'],n=6,b=.001)
  rod('Side handrail',(x,.64,2.075),(x,1.20,2.075),.028,blue,20)
  rod('Side mid rail',(x,.72,1.83),(x,1.18,1.83),.016,blue,16)
  for y in (.86,1.04):rod('Platform guard picket',(x,y,1.675),(x,y,2.075),.011,blue,12)
  rod('Platform lower brace',(x,.72,.80),(x,1.18,.80),.022,blue,16)
 # Rear inclined ladder, with each rung meeting both rails.
 for x in (-.33,.33):
  box('Ladder anchoring foot',(x,1.40,.010),(.12,.12,.020),p['dark'],.005)
  rod('Rear ladder stile',(x,1.40,.018),(x,1.18,1.68),.027,blue,20)
  tube('Ladder entry handhold',[(x,1.18,1.66),(x,1.18,2.06),(x,1.04,2.075)],.022,blue)
 for i in range(6):
  z=.24+i*.25;y=1.40-(z-.018)*(.22/1.662)
  rod('Ladder climbing rung',(-.33,y,z),(.33,y,z),.020,p['steel'],20)
 # Compute the underside at the support station so no brace crosses the sliding surface.
 support_y=-.45
 for a,b in zip(path,path[1:]):
  if a.x>=support_y>=b.x:
   support_z=a.y+(b.y-a.y)*(support_y-a.x)/(b.x-a.x)-.024
   break
 for x in (-.27,.27):
  rod('Mid-chute ground support',(x,support_y,.025),(x,support_y,support_z),.025,blue,16)
  box('Mid-support foot',(x,-.45,.0125),(.12,.15,.025),p['dark'],.005)
 rod('Under-chute cross support',(-.30,support_y,support_z),(.30,support_y,support_z),.026,blue,16)
 box('Chute exit support',(0,-1.54,.060),(.62,.18,.12),p['dark'],.010)


def lifebuoy_station(p):
 steel=p['steel'];rope=mat('Natural throwline cord',(.58,.52,.33),0,.90)
 box('Rescue station foot',(0,.06,.018),(.25,.24,.036),p['dark'],.009)
 box('Station support post',(0,.06,.75),(.06,.06,1.50),steel,.005)
 box('Post weather cap',(0,.06,1.505),(.075,.075,.025),p['dark'],.005)
 for x in (-.08,.08):cyl('Post anchor',(x,.06,.043),.012,.015,steel,n=6,b=.001)
 center=Vector((0,-.08,1.12))
 buoy=ring('Thick rescue ring',center,.25,.075,p['orange'],64,16,rotation=(math.pi/2,0,0));buoy.data.materials.append(p['white']);buoy.data.update()
 for face in buoy.data.polygons:
  angle=math.atan2(face.center.y,face.center.x);nearest=round(angle/(math.pi/2))*(math.pi/2)
  if abs(angle-nearest)<.15:face.material_index=1
 points=[]
 for i in range(65):
  a=i*math.tau/64;r=.342+.018*math.sin(2*a)**2;points.append((r*math.cos(a),-.12,1.12+r*math.sin(a)))
 closed_rope('Perimeter grab rope',points[:-1],.007,rope)
 for a in (0,math.pi/2,math.pi,3*math.pi/2):
  tube('Grab rope attachment',[(.292*math.cos(a),-.12,1.12+.292*math.sin(a)),(.342*math.cos(a),-.12,1.12+.342*math.sin(a))],.006,rope)
 for x in (-.12,.12):
  tube('Lower ring cradle hook',[(0,.06,.83),(x,.06,.83),(x,-.07,.83),(x,-.10,.88)],.012,steel)
  rod('Upper ring backing brace',(0,.06,1.32),(x,-.025,1.36),.012,steel,12)
 # A simple throwline spool on the same post; no instructional sign or emblem.
 cyl('Throwline reel rear flange',(0,.020,.50),.095,.018,p['orange'],n=32,b=.004,axis=(0,1,0))
 cyl('Throwline cord spool',(0,-.025,.50),.073,.070,rope,n=32,b=.005,axis=(0,1,0))
 cyl('Throwline reel front flange',(0,-.070,.50),.095,.018,p['orange'],n=32,b=.004,axis=(0,1,0))
 cyl('Reel axle',(0,-.083,.50),.020,.025,steel,n=20,b=.002,axis=(0,1,0))
 for y in (-.048,-.025,-.002):ring('Cord coil', (0,y,.50),.073,.003,rope,32,6,rotation=(math.pi/2,0,0))
 tube('Throwline loose tail',catmull([(.04,-.06,.44),(.10,-.08,.37),(.10,-.09,.30),(.03,-.09,.28),(-.01,-.08,.33)],4),.005,rope)
 box('Reel mounting stand-off',(0,.045,.50),(.06,.08,.08),steel,.005)


def glyph_aed(origin,p):
 # Original line-built letterforms, not a font or protected medical emblem.
 ox,oy,oz=origin
 for c,x in zip('AED',(-.065,0,.065)):
  if c=='A':
   for side in (-1,1):
    rod('A diagonal',(ox+x+side*.022,oy,oz-.025),(ox+x,oy,oz+.025),.003,p['dark'],8)
   box('A crossbar',(ox+x,oy,oz-.006),(.028,.006,.005),p['dark'],.0005)
  elif c=='E':
   box('E upright',(ox+x-.020,oy,oz),(.006,.006,.05),p['dark'],.0005)
   for z in (-.025,0,.025):box('E bar',(ox+x,oy,oz+z),(.04,.006,.005),p['dark'],.0005)
  else:
   box('D upright',(ox+x-.020,oy,oz),(.006,.006,.05),p['dark'],.0005)
   pts=[(ox+x-.020,oy,oz+.025),(ox+x+.010,oy,oz+.025),(ox+x+.024,oy,oz+.012),(ox+x+.024,oy,oz-.012),(ox+x+.010,oy,oz-.025),(ox+x-.020,oy,oz-.025)]
   tube('D curved stroke',pts,.003,p['dark'])

def aed_cabinet(p):
 white=mat('Cabinet light enamel',(.72,.77,.75),.20,.42);green=mat('Unbranded device green polymer',(.12,.34,.17),0,.50)
 box('Cabinet rear wall',(0,.10,.31),(.46,.02,.58),white,.006)
 for x in (-.22,.22):box('Cabinet side wall',(x,-.01,.31),(.02,.20,.58),white,.005)
 for z in (.01,.61):box('Cabinet upper and lower wall',(0,0,z),(.46,.22,.02),white,.005)
 for x in (-.214,.214):box('Door upright frame',(x,-.115,.31),(.032,.025,.60),green,.005)
 for z in (.03,.585):box('Door horizontal frame',(0,-.115,z),(.396,.025,.05),green,.005)
 # Transparent glazing is an actual exported alpha material, not an opaque proxy.
 glass=mat('Clear cabinet glazing',(.40,.54,.51),0,.14)
 shader=glass.node_tree.nodes.get('Principled BSDF');shader.inputs['Alpha'].default_value=.08;glass.diffuse_color=(.40,.54,.51,.08);glass.surface_render_method='DITHERED'
 box('Glazed door panel',(0,-.112,.307),(.39,.004,.50),glass,.001)
 for z in (.13,.46):cyl('Door hinge barrel',(-.230,-.11,z),.008,.07,p['steel'],n=16,b=.001)
 box('Door pull latch',(.227,-.137,.31),(.022,.025,.085),p['dark'],.005)
 cyl('Door latch lock',(.228,-.153,.31),.007,.005,p['steel'],n=12,b=.0006,axis=(0,1,0))
 # Portable handled device sits on the shelf; no functional medical claim.
 box('Device support shelf',(0,0,.1025),(.44,.18,.015),white,.003)
 box('Portable device case',(-.025,0,.235),(.30,.13,.25),white,.024)
 box('Device front face',(-.025,-.070,.235),(.265,.012,.205),green,.014)
 tube('Carrying handle',[(-.13,0,.355),(-.13,0,.405),(.08,0,.405),(.08,0,.355)],.013,p['dark'])
 box('Inset device display',(-.057,-.079,.280),(.12,.006,.060),p['dark'],.004)
 box('Inactive display highlight',(-.057,-.083,.280),(.095,.002,.038),mat('Inactive screen gray',(.13,.23,.24),.1,.3),.002)
 cyl('Unlabelled round device button',(-.080,-.084,.184),.018,.008,p['orange'],n=20,b=.001,axis=(0,1,0))
 box('Sealed pads pouch',(.070,-.084,.207),(.075,.012,.115),p['white'],.006)
 box('Pouch folded seal',(.070,-.093,.266),(.070,.009,.011),p['dark'],.002)
 tube('Stored pad connector lead',[(.10,-.03,.30),(.15,-.03,.31),(.16,-.04,.23),(.13,-.06,.16),(.09,-.08,.17)],.0035,p['dark'])
 box('Upper AED label plate',(0,-.130,.585),(.23,.008,.067),p['white'],.003);glyph_aed((0,-.138,.585),p)
 for x in (-.16,.16):
  for z in (.10,.52):
   box('Rear mounting tab',(x,.118,z),(.07,.024,.075),p['steel'],.004)
   cyl('Mounting bolt',(x,.135,z),.009,.010,p['dark'],n=6,b=.001,axis=(0,1,0))


def pet_bag_dispenser(p):
 green=mat('Dispenser forest green coating',(.035,.12,.075),.35,.50);bag=mat('Folded pale green bag',(.37,.48,.29),0,.80)
 box('Dispenser rear panel',(0,.074,.235),(.244,.022,.43),green,.006)
 for x in (-.131,.131):box('Side housing wall',(x,0,.235),(.018,.17,.43),green,.005)
 box('Bottom housing ledge',(0,0,.010),(.28,.17,.020),green,.004)
 # Front opening remains a genuine hole into the housing, with separate surrounding panels.
 box('Refill access door',(0,-.087,.293),(.26,.018,.314),green,.006)
 box('Lower aperture sill',(0,-.087,.043),(.26,.018,.066),green,.004)
 for x in (-.108,.108):box('Pull aperture side',(x,-.087,.106),(.044,.018,.060),green,.003)
 lid=box('Overhanging rain lid',(0,-.006,.456),(.304,.20,.028),p['dark'],.009);lid.rotation_euler[0]=math.radians(-5)
 for z in (.21,.37):cyl('Refill door hinge',(-.140,-.085,z),.007,.065,p['steel'],n=12,b=.001)
 cyl('Refill key cylinder',(.085,-.100,.405),.010,.007,p['steel'],n=16,b=.001,axis=(0,1,0))
 box('Keyway',(.085,-.105,.405),(.0025,.002,.011),p['black'],.0004)
 box('Visible bag stack',(0,-.055,.139),(.17,.045,.065),bag,.004)
 extrude_x('Folded bag pull edge',[(-.065,.122),(-.115,.120),(-.145,.100),(-.144,.098),(-.114,.118),(-.065,.120)],.095,bag,.0003)
 for x in (-.025,.025):
  o=box('Bag fold crease',(x,-.124,.111),(.001,.032,.0015),p['dark'],.0002);o.rotation_euler[0]=math.radians(34)
 for z in (.08,.38):box('Rear mounting flange',(0,.092,z),(.20,.025,.065),p['steel'],.004)
 for z in (.08,.38):
  for x in (-.065,.065):cyl('Mounting screw',(x,.108,z),.007,.009,p['dark'],n=6,b=.0007,axis=(0,1,0))

ASSETS=[
 ('city-lifebuoy-station','救命浮環ステーション','Lifebuoy station',lifebuoy_station,'厚みのある浮環、4本の帯、つかみ綱、投てき索リール、支持金具を備える静的な設備モデル。','A static station with thick ring, four bands, grab rope, throwline reel and support brackets; no safety certification is claimed.',22),
 ('city-aed-cabinet','AED収納キャビネット','AED storage cabinet',aed_cabinet,'ガラス扉、ラッチ、取付金具と、持ち手・画面・パッド袋を持つ無銘の機器を備える静的な収納モデル。医療機器として機能しません。','A glazed storage cabinet with latch, mounts and an unbranded handled device, display and pads pouch. Static visualization only, not a functioning or certified medical device.',20),
 ('city-pet-bag-dispenser','ペット用袋ディスペンサー','Pet bag dispenser',pet_bag_dispenser,'雨よけ蓋、補充扉、鍵、実際に開いた引出口、折り畳まれた袋の端を備える壁付けディスペンサー。ごみ箱は含みません。','A wall-mounted pet bag dispenser with rain lid, refill hinge, key cylinder, real pull aperture and folded bag edge; no waste bin included.',22),
 ('city-playground-swing','公園用ブランコ','Playground swing',playground_swing,'A型フレーム、接合金具、シャックル、交互のチェーンリンクと座席を備える静的なブランコ。安全規格適合は未検証。','A static playground swing with connected A-frame, spreaders, shackles, alternating chain links and rubber seat. Safety-standard compliance has not been validated.',19),
 ('city-playground-slide','公園用滑り台','Playground slide',playground_slide,'連続した曲面の滑走部、立ち上がった側面、踊り場、はしご、手すり、支持脚を備える静的な滑り台。安全規格適合は未検証。','A static slide with continuous curved chute, raised sides, platform, ladder, handrails and connected supports. Safety-standard compliance has not been validated.',21)]

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox');parser.add_argument('--only',nargs='*',default=[])
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
 for slug,title,en,builder,ja,desc,elevation in ASSETS:
  if args.only and slug not in args.only:continue
  if (args.output/slug).exists():raise FileExistsError(f'Refusing to overwrite {args.output/slug}')
  common.reset();builder(palette())
  bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type in ('MESH','CURVE'));bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
  common.publish_asset(slug,title,en,ja,desc,['street-furniture',slug.removeprefix('city-')],args.output,'scripts/city/access_recreation.py',elevation=elevation)
  f=args.output/slug/'asset.json';d=json.loads(f.read_text());d['usages'][0]['sourcePaths']+=['scripts/city/access.py','scripts/city/access_extra.py','scripts/city/access_structures.py'];f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
