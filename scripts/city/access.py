"""Original street-access props. Blender 4.3; no external assets. CC BY 4.0."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))

# Modeling uses Z up and meters. Export and inspection are delegated to common.
def mat(name,color,metal=0,rough=.45):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m

def finish(o,name,m,bevel=0):
 o.name=name
 if m:o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Manufactured edge radii','BEVEL');mod.width=bevel;mod.segments=3
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
  mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=40
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o

def box(name,loc,scale,m,b=.008):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,m,min(b,min(scale)*.3))
def cyl(name,loc,r,d,m,n=32,b=.003,axis=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=d,location=loc);o=bpy.context.object
 if axis:o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
 return finish(o,name,m,min(b,d*.2,r*.2))
def torus(name,loc,r,t,m,rot=None):
 bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=10,location=loc,major_radius=r,minor_radius=t);o=bpy.context.object
 if rot:o.rotation_euler=rot
 return finish(o,name,m)
def tube(name,pts,r,m):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=r;curve.bevel_resolution=5;curve.use_fill_caps=True
 sp=curve.splines.new('POLY');sp.points.add(len(pts)-1)
 for v,p in zip(sp.points,pts):v.co=(*p,1)
 o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return finish(o,name,m)
def mesh(name,verts,faces,m,b=.003):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
 return finish(o,name,m,b)
def extrude_x(name,profile,length,m,b=.005):
 n=len(profile);v=[(x,y,z) for x in (-length/2,length/2) for y,z in profile];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];return mesh(name,v,f,m,b)
def bolts(x,y,z,steel,spacing=.062):
 for a in (-1,1):
  for b in (-1,1):
   cyl('Anchor washer',(x+a*spacing,y+b*spacing,z),.014,.003,steel)
   cyl('Hexagonal anchor head',(x+a*spacing,y+b*spacing,z+.006),.009,.009,steel,n=6,b=.0008)
def palette():
 return dict(steel=mat('Satin stainless steel',(.48,.54,.57),.85,.27),dark=mat('Graphite powder coat',(.038,.053,.061),.55,.33),rubber=mat('Recycled charcoal rubber',(.035,.042,.043),0,.88),yellow=mat('Warm safety yellow',(.95,.61,.025),0,.48),red=mat('Red reflective polymer',(.78,.045,.025),.15,.22),white=mat('Ivory reflective strip',(.86,.88,.84),.08,.25),orange=mat('Safety orange molded polyethylene',(.96,.19,.025),0,.42),black=mat('Recess and gasket',(.018,.023,.026),0,.72))

def bollard(p):
 s,d=p['steel'],p['dark']
 cyl('Ground receiver flange',(0,0,.015),.125,.03,d,n=48)
 for a in range(4):
  t=a*math.pi/2;cyl('Receiver anchor washer',(.095*math.cos(t),.095*math.sin(t),.033),.012,.005,s);cyl('Receiver anchor bolt',(.095*math.cos(t),.095*math.sin(t),.038),.008,.008,s,n=6)
 cyl('Socket collar',(0,0,.064),.085,.075,s,n=48)
 torus('Socket sealing ring',(0,0,.102),.070,.004,p['black'])
 cyl('Removable steel post',(0,0,.527),.064,.85,d,n=48,b=.007)
 cyl('Upper reflector band',(0,0,.832),.065,.080,p['white'],n=48,b=.001)
 cyl('Lower red reflector band',(0,0,.757),.065,.026,p['red'],n=48,b=.001)
 cyl('Brushed cap',(0,0,.959),.066,.034,s,n=48,b=.012)
 cyl('Front locking cylinder',(0,-.067,.183),.015,.008,s,n=32,b=.001,axis=(0,1,0))
 box('Lock keyway',(0,-.072,.183),(.003,.002,.015),p['black'],.0005)
 # Separate rounded grab loop, intentionally connected to the cap.
 pts=[(.026*math.cos(math.pi*i/20),0,.984+.026*math.sin(math.pi*i/20)) for i in range(21)]
 tube('Lift-out grab loop',pts,.005,s)

def cycle_rack(p):
 s=p['steel']
 for x in (-.39,.39):
  box('Base mounting shoe',(x,0,.013),(.18,.17,.026),s,.012);bolts(x,0,.028,s,.059)
  torus('Tube base weld',(x,0,.036),.026,.004,s)
 pts=[(-.39,0,.03),(-.39,0,.69)]
 for i in range(17):
  t=math.pi-(math.pi/2)*i/16;pts.append((-.25+.14*math.cos(t),0,.69+.14*math.sin(t)))
 pts.append((.25,0,.83))
 for i in range(1,17):
  t=math.pi/2-(math.pi/2)*i/16;pts.append((.25+.14*math.cos(t),0,.69+.14*math.sin(t)))
 pts.append((.39,0,.03));tube('Continuous bent stainless hoop',pts,.026,s)
 for x in (-.39,.39):cyl('Protective rubber contact sleeve',(x,0,.47),.030,.25,p['dark'],b=.005)

def railing(p):
 d,s=p['dark'],p['steel']
 for x in (-.88,.88):
  box('Foot plate',(x,0,.014),(.18,.16,.028),d,.01);bolts(x,0,.03,s,.057)
  box('Square structural post',(x,0,.56),(.06,.06,1.08),d,.006)
  box('Post end cap',(x,0,1.112),(.071,.071,.028),s,.008)
 for z in (.18,.98):box('Horizontal rail',(0,0,z),(1.76,.044,.05),d,.005)
 for i in range(11):box('Vertical safety picket',(-.75+i*.15,0,.58),(.026,.026,.78),d,.003)
 for x in (-.88,.88):
  for z in (.18,.98):
   cyl('Rail bracket rivet',(x,-.034,z),.009,.008,s,n=16,axis=(0,1,0))
 # Two joining lugs make the panel modular without including neighbors.
 for x in (-.929,.929):
  for z in (.32,.84):box('Panel join tab',(x,.005,z),(.037,.024,.057),s,.004)

def curb_ramp(p):
 # Broad wedge with closed sides, transverse traction ribs and bright side guides.
 prof=[(-.30,.008),(.30,.008),(.30,.155),(.235,.155),(-.30,.017)]
 extrude_x('Solid portable ramp body',prof,.90,p['rubber'],.0015)
 slope=(.155-.017)/(.235+.30)
 for i in range(11):
  y=-.245+i*.043;z=.017+slope*(y+.30)+.003
  o=box('Raised traction bar',(0,y,z),(.77,.012,.006),p['black'],.002);o.rotation_euler[0]=math.atan(slope)
 for x in (-.418,.418):
  o=box('Yellow sloped edge marker',(x,-.01,.017+slope*.29+.004),(.027,.49,.005),p['yellow'],.002);o.rotation_euler[0]=math.atan(slope)
 # Rear handhold recess represented as a dark inset with actual raised rim.
 box('Rear recessed carrying grip',(0,.301,.096),(.23,.004,.033),p['black'],.009)
 box('Grip upper lip',(0,.308,.117),(.26,.018,.011),p['rubber'],.005)
 for x in (-.31,.31):
  cyl('Rear fixing recess',(x,.265,.158),.016,.003,p['black']);cyl('Recessed stainless fixing',(x,.265,.160),.008,.003,p['steel'],n=6,b=.0004)

def speed_cushion(p):
 # Chamfered pad mesh: lower footprint to raised plateau with four sloping faces.
 v=[(-.9,-1,0),(.9,-1,0),(.9,1,0),(-.9,1,0),(-.9,-1,.015),(.9,-1,.015),(.9,1,.015),(-.9,1,.015),(-.67,-.71,.085),(.67,-.71,.085),(.67,.71,.085),(-.67,.71,.085)]
 f=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,9,8),(5,6,10,9),(6,7,11,10),(7,4,8,11),(8,9,10,11)]
 mesh('Beveled traffic calming pad',v,f,p['rubber'],.007)
 # Nine molded module joints and top traction ribs.
 for x in (-.3,.3):box('Longitudinal module seam',(x,0,.086),(.006,1.39,.002),p['black'],.0005)
 for y in (-.35,.35):box('Transverse module seam',(0,y,.086),(1.32,.005,.002),p['black'],.0005)
 for x in (-.52,0,.52):
  for y in (-.54,.54):cyl('Counterbored anchor socket',(x,y,.087),.022,.002,p['black']);cyl('Hex anchor in recess',(x,y,.089),.009,.003,p['steel'],n=6,b=.0005)
 for y in [-.62+i*.075 for i in range(18)]:
  for x in (-.47,.47):box('Fine molded tread',(x,y,.088),(.30,.007,.003),p['rubber'],.001)
 # Painted slope bars sit on the actual front/back planes.
 for side in (-1,1):
  for x in (-.55,-.275,0,.275,.55):
   y=side*.855;z=.0505
   o=box('High visibility approach stripe',(x,y,z),(.12,.28,.0025),p['yellow'],.001);o.rotation_euler[0]=-side*math.atan(.07/.29)

def road_barrier(p):
 o,r,w=p['orange'],p['red'],p['white']
 profile=[(-.25,.025),(.25,.025),(.25,.15),(.16,.27),(.13,.68),(.10,.75),(-.10,.75),(-.13,.68),(-.16,.27),(-.25,.15)]
 extrude_x('Hollow-form water-fill barrier shell',profile,1.48,o,.025)
 for x in (-.53,.53):box('Wide molded ground foot',(x,0,.025),(.26,.53,.05),o,.018)
 for side in (-1,1):
  # White reflectors backed by recessed darker panels.
  ob=box('Recessed reflective panel bed',(0,side*.145,.53),(1.27,.012,.19),r,.012);ob.rotation_euler[0]=side*.073
  for i in range(5):
   x=-.49+i*.245
   ob=box('White reflector tile',(x,side*.155,.53),(.16,.007,.145),w,.004);ob.rotation_euler[0]=side*.073
  for x in (-.56,-.28,0,.28,.56):
   ob=box('Lower molded stiffening rib',(x,side*.204,.205),(.045,.034,.16),o,.011);ob.rotation_euler[0]=-side*.33
 # Fill collar and removable fluted cap.
 cyl('Fill neck',(0,0,.759),.064,.023,o,n=40)
 cyl('Black screw fill cap',(0,0,.781),.068,.025,p['dark'],n=40,b=.005)
 for i in range(16):
  a=2*math.pi*i/16;ob=box('Cap grip knurl',(.067*math.cos(a),.067*math.sin(a),.782),(.008,.009,.017),p['dark'],.002);ob.rotation_euler[2]=a
 # Molded top handhold: open space below the bridge, not a painted hole.
 for x in (-.42,.42):
  for dx in (-.10,.10):box('Carry handle standoff',(x+dx,0,.779),(.035,.06,.09),o,.012)
  box('Carry handle bridge',(x,0,.817),(.23,.06,.03),o,.012)
 # Complementary male/female linking pieces.
 cyl('Male linking pin',(.81,0,.25),.035,.36,o,n=24,b=.008)
 for z in (.13,.37):box('Male pin support',(.758,0,z),(.15,.08,.06),o,.012)
 for z in (.15,.35):
  torus('Female interlock eye',(-.805,0,z),.05,.019,o)
  box('Eye root web',(-.755,0,z),(.10,.065,.038),o,.007)
 cyl('Drain plug flange',(.66,-.237,.115),.032,.012,p['dark'],axis=(0,1,0))
 cyl('Drain plug hex',(.66,-.248,.115),.019,.015,p['dark'],n=6,axis=(0,1,0))

ASSETS=[
 ('city-bollard','着脱式スチールボラード','Removable steel bollard',bollard,'A removable powder-coated steel bollard with socket collar, lift loop, lock and reflector bands.'),
 ('city-cycle-rack','逆U字型自転車ラック','Inverted-U cycle rack',cycle_rack,'A single anchored stainless-steel bicycle hoop with bent corners, protective sleeves and mounting hardware; no bicycle included.'),
 ('city-pedestrian-railing','歩道用ガードパネル','Pedestrian railing panel',railing,'A standalone powder-coated pedestrian guard panel with steel pickets, foot plates, anchor bolts and joining tabs.'),
 ('city-curb-ramp','可搬式段差スロープ','Portable curb ramp',curb_ramp,'A rubber curb transition wedge with raised traction ribs, bright edge markers, carrying recess and rear fixing points.'),
 ('city-speed-cushion','道路用減速クッション','Road speed cushion',speed_cushion,'A low rubber traffic-calming pad with tapered approaches, modular seams, fixing sockets, traction ribs and yellow approach stripes.'),
 ('city-road-barrier','注水式ロードバリア','Water-fill road barrier',road_barrier,'A molded orange work-zone barrier with wide feet, reflectors, carry handles, fill cap, drain plug and complementary interlocking ends.')]

if __name__=='__main__':
 import common
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
 parser.add_argument('--only',nargs='*',default=[])
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
 out=args.output
 wanted=args.only
 descriptions={
 'city-bollard':'反射帯、鍵穴、持ち上げループ、基礎ソケットを備える着脱式の車止め。',
 'city-cycle-rack':'曲げ加工されたステンレス製の単体自転車ラック。保護スリーブと固定ボルト付き。自転車は含みません。',
 'city-pedestrian-railing':'支柱、縦格子、固定金具、連結タブを備える歩行者用の独立した柵パネル。',
 'city-curb-ramp':'滑り止めリブ、黄色い端部表示、背面グリップ、固定ポイントを備えるゴム製段差スロープ。',
 'city-speed-cushion':'傾斜した進入面、モジュール継ぎ目、アンカー、滑り止め、黄色い表示を備える道路用減速パッド。',
 'city-road-barrier':'反射板、ハンドル、注水キャップ、排水プラグ、連結部を備える樹脂製工事バリア。'}
 for slug,title,en,builder,desc in ASSETS:
  if wanted and slug not in wanted:continue
  if (out/slug).exists():raise FileExistsError(f'Refusing to overwrite {out/slug}; move existing output before regenerating.')
  common.reset();builder(palette())
  common.publish_asset(slug,title,en,descriptions[slug],desc,['access','road-safety',slug.removeprefix('city-')],out,'scripts/city/access.py',elevation=30 if slug in ('city-curb-ramp','city-speed-cushion') else 22)
