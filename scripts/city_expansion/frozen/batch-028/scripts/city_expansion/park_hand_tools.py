"""Original hand-held landscape maintenance props. Xenoah, CC BY 4.0.
Generic scene geometry, not a real tool specification or operating instruction.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Satin tool steel',(.42,.48,.49),.72,.40),edge=mat('Bright exposed edge',(.61,.66,.66),.78,.31),dark=mat('Dark coated steel',(.065,.085,.09),.38,.54),wood=mat('Plain wooden shaft color',(.44,.27,.12),0,.67),green=mat('Muted green enamel',(.07,.25,.17),.30,.44),rubber=mat('Dark matte grip',(.025,.035,.030),0,.80),orange=mat('Warm orange grip accent',(.66,.22,.035),.06,.48))
def cyl(n,p,r,d,m,axis='Z',v=28,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.1));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def plate_xy(n,outline,z,t,m,bev=.0006):
 if 'blade' in n.lower():
  rounded=[]
  for i,b in enumerate(outline):
   a=outline[i-1];c=outline[(i+1)%len(outline)];start=(.16*a[0]+.84*b[0],.16*a[1]+.84*b[1]);end=(.84*b[0]+.16*c[0],.84*b[1]+.16*c[1])
   for j in range(5):
    u=j/4;rounded.append(((1-u)**2*start[0]+2*(1-u)*u*b[0]+u*u*end[0],(1-u)**2*start[1]+2*(1-u)*u*b[1]+u*u*end[1]))
  outline=rounded;bev=0
 k=len(outline);vs=[(x,y,zz) for zz in [z-t/2,z+t/2] for x,y in outline];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,bev)
def strip(n,points,w,t,m):
 # Closed spring-metal ribbon with real width and thickness, not a one-sided curve.
 vs=[]
 for x,y,z in points:vs.extend([(x-w/2,y-t/2,z),(x+w/2,y-t/2,z),(x+w/2,y+t/2,z),(x-w/2,y+t/2,z)])
 fs=[(3,2,1,0),tuple(range(len(vs)-4,len(vs)))]
 for j in range(len(points)-1):
  for i in range(4):fs.append((j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i))
 return mesh(n,vs,fs,m,.0004)
def shaped_blade(p):
 rows=[(.003,.010),(.020,.072),(.060,.105),(.220,.102),(.282,.075)];n=10;vs=[]
 for back in [False,True]:
  for z,w in rows:
   for j in range(n+1):
    x=w*(2*j/n-1);y=.019*(w/.105)*(1-(x/w)**2)+.009*z/.282;vs.append((x,y+(.0035 if back else 0),z))
 h=len(rows);k=h*(n+1);fs=[]
 for l in range(2):
  for i in range(h-1):
   for j in range(n):
    a=l*k+i*(n+1)+j;fs.append((a,a+1,a+n+2,a+n+1) if l==0 else (a+n+1,a+n+2,a+1,a))
 border=list(range(n+1))+[i*(n+1)+n for i in range(1,h)]+list(range((h-1)*(n+1)+n-1,(h-1)*(n+1)-1,-1))+[i*(n+1) for i in range(h-2,0,-1)]
 for a,b in zip(border,border[1:]+border[:1]):fs.append((a,b,b+k,a+k))
 o=mesh('Shallow dished digging blade',vs,fs,p['steel'],0,True);mod=o.modifiers.new('Separate thin blade perimeter normals','EDGE_SPLIT');mod.split_angle=math.radians(35);mod.use_edge_angle=True;mod.use_edge_sharp=False;return o
def spade():
 p=palette();shaped_blade(p)
 cyl('Blade socket',(0,.016,.319),.024,.14,p['dark'],v=32,b=.002)
 cyl('Wooden main shaft',(0,.016,.609),.018,.56,p['wood'],v=32,b=.002)
 cyl('Upper ferrule',(0,.016,.884),.022,.069,p['dark'],v=28,b=.002)
 # Split fork and transverse grip leave an open D-shaped hand opening.
 for side in [-1,1]:tube('D handle fork',[(0,.016,.88),(side*.045,.016,.93),(side*.067,.016,1.025)],.015,p['dark'],2)
 rod('D handle upper grip',(-.067,.016,1.025),(.067,.016,1.025),.021,p['rubber'],28)
 for z in [.28,.35,.89]:cyl('Socket and grip rivet',(0,-.010,z),.0055,.007,p['steel'],'Y',16,.0004)
 for x in [-.071,.071]:
  box('Folded foot tread',(x,.022,.273),(.075,.048,.017),p['dark'],.003)
  for xx in [-.02,0,.02]:box('Foot tread ridge',(x+xx,.022,.283),(.006,.036,.004),p['steel'],.0008)
 return ('city-garden-digging-spade','公園管理用のスコップ','Garden digging spade','花壇・公園管理小屋に置く手作業用スコップ。浅く湾曲した厚みのある刃、足掛けの折返しとリブ、金属ソケット、木色の柄、開いたD字握りを造形。刃先を下にした展示姿勢で、壁や道具掛けへの配置は利用者側で調整してください。土や掘削動作は含みません。','A hand spade for flower-bed and park-maintenance scenes, with a shallow dished solid blade, folded foot treads and ribs, metal socket, plain wood-colored shaft and open D grip. Presented blade-down; adjust support and placement against a wall or tool rack in the host scene. Soil and digging behavior are absent.',['garden','tool','spade','公園管理'])
def rake():
 p=palette()
 cyl('Rake wooden handle',(0,.012,.928),.016,.99,p['wood'],v=32,b=.002)
 cyl('Rake handle socket',(0,.012,.443),.022,.12,p['dark'],v=28,b=.002)
 cyl('Rake upper grip',(0,.012,1.394),.019,.11,p['rubber'],v=28,b=.003)
 for i in range(17):
  f=(i-8)/8;x=.285*f
  strip('Individual fanned spring tine',[(.034*f,.012,.443),(.11*f,.008,.310),(x*.84,.006,.169),(x,-.006,.050),(x,-.040,.019),(x,-.067,.015)],.008,.0025,p['steel'])
 # A curved transverse retaining strip stabilizes the spreading tines.
 curve=[(.25*f,.007,.205+.010*(1-f*f)) for f in [i/12 for i in range(-12,13)]]
 tube('Tine retaining crosswire',curve,.0035,p['dark'],1)
 plate_xy('Tine clamp plate',[(-.047,-.002),(.047,-.002),(.038,.035),(-.038,.035)],.430,.014,p['dark'],.001)
 for x in [-.026,.026]:cyl('Tine clamp rivet',(x,-.008,.426),.006,.010,p['steel'],'Y',16,.0005)
 return ('city-fan-leaf-rake','扇形の落葉レーキ','Fan leaf rake','公園や庭園の落葉清掃場面向けの扇形レーキ。17本の厚み付きばね鋼風の爪と曲げ先端、横方向の保持線、クランプ、木色の長柄と握りを造形。爪は実ジオメトリで、画像テクスチャではありません。立て置き表示用で、道具掛けなどの支持はシーン側で追加してください。弾性変形や掃き集め動作はありません。','A fan rake for leaf-clearing scenes in parks and gardens, with 17 solid spring-steel-like tines and bent tips, transverse retainer, clamp, long wood-colored shaft and grip. The tines are modeled geometry, not a texture. Presented upright; add a rack or other support in the host scene. Elastic bending and raking behavior are absent.',['garden','rake','tool','落葉レーキ'])
def shears():
 p=palette()
 # Two overlapping thick curved blade outlines, held in one fixed open pose.
 plate_xy('Curved bypass cutting blade',[(-.012,-.012),(.012,-.006),(.020,.018),(.024,.045),(.018,.068),(.004,.083),(-.009,.087),(.002,.068),(.006,.049),(.003,.030),(-.010,.014)],.013,.004,p['steel'])
 plate_xy('Bypass hooked counterblade',[(-.016,-.008),(.003,.002),(-.012,.023),(-.020,.042),(-.019,.061),(-.010,.078),(-.025,.068),(-.032,.047),(-.029,.026)],.007,.005,p['dark'])
 plate_xy('Exposed curved blade bevel',[(.004,.083),(.018,.068),(.024,.045),(.020,.018),(.014,.019),(.018,.043),(.013,.066)],.0152,.0006,p['edge'],0)
 for side in [-1,1]:
  points=[(side*.007,-.006,.010),(side*.026,-.043,.010),(side*.043,-.082,.010),(side*.048,-.127,.010)]
  tube('Shear metal handle tang',points,.007,p['steel'],2)
  tube('Shaped shear grip',points[1:],.011,p['orange'] if side==1 else p['rubber'],3)
  end=Vector(points[-1]);direction=(end-Vector(points[-2])).normalized();rod('Handle heel plug',end-direction*.004,end+direction*.004,.0113,p['dark'],24)
 cyl('Main shear pivot',(0,0,.012),.012,.019,p['steel'],v=28,b=.001)
 cyl('Pivot hex fastener',(0,0,.023),.007,.004,p['dark'],v=6,b=.0005)
 # Coil axis across the handles; spring is fixed geometry, not a simulation.
 pts=[]
 for i in range(73):
  t=i/72;a=t*math.tau*6;pts.append((-.023+.046*t,-.049+.006*math.cos(a),.010+.006*math.sin(a)))
 tube('Fixed return spring coil',pts,.0015,p['steel'],1)
 for side in [-1,1]:rod('Return spring seat',(side*.021,-.049,.010),(side*.029,-.049,.010),.004,p['dark'],16)
 plate_xy('Fixed locking tab',[(.024,-.030),(.042,-.029),(.043,-.017),(.027,-.017)],.024,.004,p['dark'],.001)
 cyl('Lock tab pivot',(.029,-.024,.027),.003,.004,p['steel'],v=12,b=.0003)
 return ('city-bypass-pruning-shears','バイパス式の剪定ばさみ','Bypass pruning shears','公園管理や園芸作業台に置く小型剪定ばさみ。重なり合う曲刃と受刃、刃先の面取り、主軸、左右の握り、実形状の戻しばねと固定ロック片を造形。机上に平置きする開いた一姿勢の静的プロップです。刃の動作・切断・ばね変形は含まず、実用品の切削性能や安全設計を検証したものではありません。','Small pruning shears for park-maintenance and gardening workbench scenes, with overlapping curved cutting and hooked counterblades, an exposed edge bevel, main pivot, paired grips, modeled return spring and fixed latch tab. A static open pose lies flat for tabletop placement. Blade motion, cutting and spring deformation are absent; this is not a tool design validated for cutting performance or safety.',['garden','shears','tool','剪定ばさみ'])
def loft(n,profile,m,segments=48,yscale=1):
 vs=[];rings=[]
 for r,z in profile:
  if r==0:rings.append([len(vs)]);vs.append((0,0,z))
  else:rings.append(list(range(len(vs),len(vs)+segments)));vs.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments)*yscale,z) for i in range(segments))
 fs=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  if len(a)==1 and len(b)==1:continue
  for i in range(segments):
   j=(i+1)%segments
   if len(a)==1:fs.append((a[0],b[i],b[j]))
   elif len(b)==1:fs.append((a[i],b[0],a[j]))
   else:fs.append((a[i],b[i],b[j],a[j]))
 o=mesh(n,vs,fs,m,0,True);mod=o.modifiers.new('Crisp profile bends','EDGE_SPLIT');mod.split_angle=math.radians(28);mod.use_edge_angle=True;mod.use_edge_sharp=False
 if n=='Hollow oval watering can body':
  group=o.vertex_groups.new(name='Watering body circumferential normals');group.add(list(range(len(vs))),1.0,'REPLACE')
 return o

def watering_can():
 p=palette()
 loft('Hollow oval watering can body',[(0,0),(.135,0),(.145,.018),(.15,.25),(.125,.29),(.070,.30),(.070,.292),(.119,.282),(.143,.247),(.138,.020),(0,.012)],p['green'],56,.78)
 # Fill lip is an open annulus, retaining an unobstructed view into the bowl.
 lip=torus('Open filling lip',(0,0,.298),.071,.005,p['steel'],segments=40);lip.scale.y=.78
 base=torus('Lower rolled seam',(0,0,.019),.142,.004,p['dark'],segments=48);base.scale.y=.78
 a=Vector((0,-.09,.075));b=Vector((0,-.365,.34));length=(b-a).length
 spout=loft('Hollow rising spout',[(.025,0),(.018,length),(.013,length),(.019,0)],p['green'],36);spout.location=a;spout.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
 # Rose face has true through-openings cut into its solid shallow cap.
 disk=cyl('Perforated watering rose',(0,0,0),.045,.009,p['steel'],v=48,b=.001)
 for modifier in list(disk.modifiers):bpy.context.view_layer.objects.active=disk;bpy.ops.object.modifier_apply(modifier=modifier.name)
 holes=[(0,0)]+[(r*math.cos(i*math.tau/count),r*math.sin(i*math.tau/count)) for r,count in [(.016,6),(.032,12)] for i in range(count)]
 for x,y in holes:
  cut=cyl('Temporary rose bore',(x,y,0),.0028,.04,None,v=12,b=0);bpy.context.view_layer.objects.active=disk;mod=disk.modifiers.new('Open rose perforation','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 old=disk.data;fresh=bpy.data.meshes.new('Rose with geometric normals');fresh.from_pydata([tuple(v.co) for v in old.vertices],[],[tuple(f.vertices) for f in old.polygons]);fresh.materials.append(p['steel']);fresh.update();bm=bmesh.new();bm.from_mesh(fresh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(fresh);bm.free();disk.data=fresh
 direction=(b-a).normalized();q=(b-a).to_track_quat('Z','Y');disk.location=b+direction*.023;disk.rotation_euler=q.to_euler()
 rose=loft('Rose expanding collar',[(.018,0),(.046,.020),(.040,.020),(.013,0)],p['dark'],40);rose.location=b;rose.rotation_euler=q.to_euler()
 pts=[(0,.157*math.cos(i*math.pi/32),.269+.20*math.sin(i*math.pi/32)) for i in range(33)]
 tube('High arched carrying handle',pts,.010,p['dark'],2)
 for side in [-1,1]:
  rod('Carrying handle mount',(0,side*.112,.264),(0,side*.157,.269),.012,p['steel'],24)
  cyl('Handle mount rivet',(.013,side*.143,.268),.005,.007,p['steel'],'X',16,.0005)
 tube('Rear pouring handle',[(0,.105,.246),(0,.199,.245),(0,.231,.184),(0,.216,.096),(0,.108,.068)],.012,p['green'],3)
 return ('city-garden-watering-can','園芸用のじょうろ','Garden watering can','花壇・温室・公園管理小屋向けのじょうろ。空洞のある楕円の胴と開いた給水口、上の弓形持ち手、後ろの傾け用持ち手、中空の注ぎ口、19個の貫通穴を持つ散水口を造形。水や流れ、可動機構はなく、内部の流体経路や散水性能は未検証です。','A watering can for flower beds, greenhouses and park-maintenance sheds, with a hollow oval vessel and open fill port, high arched carrying handle, rear pouring handle, hollow spout and rose with 19 actual through-holes. Water, flow and articulation are absent; internal fluid routing and watering performance are unvalidated.',['garden','watering','can','じょうろ'])
# Preserve the original prepared positions, UV layout and profile split topology.
# Only the body corner normals are made uniform around each elliptical profile band.
import common as _common
_original_prepare=_common._prepare
def _prepare_with_uniform_body_normals():
 obs,dims=_original_prepare()
 for ob in obs:
  group=ob.vertex_groups.get('Watering body circumferential normals')
  if group is None:continue
  me=ob.data;members={v.index for v in me.vertices if any(g.group==group.index and g.weight>.5 for g in v.groups)}
  normals=[tuple(n.vector) for n in me.corner_normals];sums={};keys={}
  for face in me.polygons:
   if not all(v in members for v in face.vertices):continue
   band=(round(min(me.vertices[v].co.z for v in face.vertices),6),round(max(me.vertices[v].co.z for v in face.vertices),6))
   for loop_index in face.loop_indices:
    pos=tuple(me.vertices[me.loops[loop_index].vertex_index].co);key=(pos,band);keys[loop_index]=key;sums[key]=sums.get(key,Vector())+face.normal
  for loop_index,key in keys.items():normals[loop_index]=tuple(sums[key].normalized())
  me.normals_split_custom_set(normals)
 return obs,dims
_common._prepare=_prepare_with_uniform_body_normals
BUILDERS=[spade,rake,shears,watering_can]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-028/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/park_hand_tools.py',azimuth=-65 if fn==watering_can else -55,elevation=53 if fn==shears else (32 if fn==watering_can else 24))
