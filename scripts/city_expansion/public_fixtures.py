"""Four functionally distinct original public-space props, CC BY 4.0, Xenoah.
No third-party meshes, textures, brand identities or font dependencies.
Usage: blender -b --factory-startup --python scripts/city_expansion/public_fixtures.py -- --out batches/batch-001/assets [--only ID]
"""
import sys,math,argparse
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Brushed stainless steel',(.39,.44,.47),.82,.32),zinc=mat('Galvanized hardware',(.36,.40,.40),.75,.48),rubber=mat('Soft charcoal rubber',(.015,.022,.025),0,.79),dark=mat('Recess shadow metal',(.025,.031,.034),.25,.65),blue=mat('Dusty blue powder coat',(.075,.19,.26),.25,.39),sand=mat('Molded warm ochre polyethylene',(.52,.35,.095),0,.64),green=mat('Garden green hose polymer',(.11,.22,.12),0,.58),brass=mat('Hose coupling brass',(.53,.34,.11),.74,.38))

def cyl(n,p,r,d,m,axis='Z',verts=32,bev=.002,r2=None):
 if r2 is None:o=cylinder(n,p,r,d,m,verts,bevel=bev)
 else:
  bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=p);o=finish(bpy.context.object,n,m,bev,True)
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 if axis=='X':o.rotation_euler[1]=math.pi/2
 # Keep end disks flat rather than shading through the cap.
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(n,a,b,r,m,verts=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=min(.001,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bar(n,a,b,w,d,m):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,.002);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def screw(n,p,m,axis='Z',r=.006):
 cyl(n+' washer',p,r*1.5,r*.25,m,axis,20,.0003)
 q=list(p);q['XYZ'.index(axis)]+= -r*.4 if axis=='Y' else r*.4
 cyl(n+' hex head',q,r,r*.75,m,axis,6,.0003)

def lathe(n,profile,m,segments=64):
 vs=[];rings=[]
 for r,z in profile:
  if r==0:rings.append([len(vs)]);vs.append((0,0,z))
  else:rings.append(list(range(len(vs),len(vs)+segments)));vs.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for i in range(segments))
 fs=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  if len(a)==1 and len(b)==1:continue
  for i in range(segments):
   j=(i+1)%segments
   if len(a)==1:fs.append((a[0],b[i],b[j]))
   elif len(b)==1:fs.append((a[i],b[0],a[j]))
   else:fs.append((a[i],b[i],b[j],a[j]))
 return mesh(n,vs,fs,m,0,True)

def tapered_shell(n,lower,upper,z0,z1,t,m):
 # Closed-volume four-wall shell; cavity and rim are real geometry.
 vs=[]
 for w,d,z in [(lower[0],lower[1],z0),(upper[0],upper[1],z1),(lower[0]-2*t,lower[1]-2*t,z0+t),(upper[0]-2*t,upper[1]-2*t,z1)]:
  vs.extend([(-w/2,-d/2,z),(w/2,-d/2,z),(w/2,d/2,z),(-w/2,d/2,z)])
 fs=[]
 for i in range(4):
  j=(i+1)%4;fs.extend([(i,j,4+j,4+i),(8+j,8+i,12+i,12+j),(4+i,4+j,12+j,12+i)])
 fs.extend([(3,2,1,0),(8,9,10,11)])
 return mesh(n,vs,fs,m,.004)

def stanchion():
 p=palette()
 lathe('Weighted bell base',[(0,.018),(.172,.018),(.185,.024),(.185,.035),(.17,.045),(.125,.061),(.065,.071),(.038,.086),(.029,.096),(.029,.102),(0,.102)],p['steel'])
 lathe('Non-marking underside foot',[(0,0),(.177,0),(.181,.007),(.177,.019),(0,.019)],p['rubber'])
 cyl('Stainless post',(0,0,.49),.028,.82,p['steel'],verts=48)
 cyl('Base post collar',(0,0,.107),.035,.045,p['steel'],verts=48)
 cyl('Upper belt cartridge housing',(0,0,.916),.053,.122,p['dark'],verts=48,bev=.003)
 cyl('Cartridge satin lower rim',(0,0,.86),.056,.015,p['steel'],verts=48,bev=.002)
 cyl('Cartridge metal top cap',(0,0,.982),.055,.017,p['steel'],verts=48,bev=.003)
 cyl('Central cap fastener',(0,0,.993),.007,.005,p['steel'],verts=24,bev=.0005)
 box('Fastener slot',(0,0,.996),(.009,.0015,.0008),p['dark'],0)
 # A short retracted belt tongue and locking hook, rather than a floating full belt.
 box('Retracted woven belt tongue',(0,-.064,.925),(.042,.041,.064),p['blue'],.001)
 box('Belt safety latch',(0,-.088,.925),(.051,.013,.075),p['dark'],.003)
 for x in [-.024,.024]:box('Latch guide rim',(x,-.096,.925),(.005,.005,.063),p['steel'],.001)
 for angle in [0,math.pi/2,math.pi]:
  x,y=.052*math.cos(angle),.052*math.sin(angle)
  o=box('Receiving belt clip',(x,y,.921),(.012,.023,.078),p['dark'],.002);o.rotation_euler[2]=angle
  o=box('Receiving clip guide',(x*1.08,y*1.08,.921),(.010,.012,.057),p['steel'],.001);o.rotation_euler[2]=angle
 return ('city-queue-belt-stanchion','巻取ベルト式の列整理ポール','Retractable-belt queue stanchion','施設入口や窓口の列整理に使う単体ポール。重り入り台座、滑り止め、ベルト収納頭部、短く収納された連結端と3方向の受け金具を造形。相手側ポールと伸ばしたベルトは含みません。','One queue-control post for building entrances and service counters, with a weighted bell base, non-marking foot, belt cassette, short retracted connector and three receiving clips. No second post or extended barrier belt is included.',['queue','stanchion','entrance','列整理'])

def cigarette_pedestal():
 p=palette()
 box('Ground anchor plate',(0,0,.012),(.24,.22,.024),p['steel'],.012)
 for x in [-.087,.087]:
  for y in [-.075,.075]:screw('Anchor bolt',(x,y,.025),p['zinc'],r=.006)
 box('Slim pedestal',(0,.015,.45),(.09,.075,.87),p['blue'],.007)
 box('Back body panel',(0,.072,.932),(.222,.022,.312),p['blue'],.007)
 for x in [-.105,.105]:box('Bin side wall',(x,-.008,.932),(.015,.16,.312),p['blue'],.006)
 box('Lower front return',(0,-.081,.855),(.215,.018,.151),p['blue'],.005)
 box('Inner removable steel ash container',(0,-.005,.868),(.181,.127,.155),p['steel'],.009)
 box('Container dark top',(0,-.008,.946),(.158,.108,.004),p['dark'],.001)
 # Eight actual separated crushing bars above the receptacle.
 for i in range(8):box('Cigarette crushing grate bar %02d'%i,(-.079+i*.0226,-.015,.969),(.009,.117,.008),p['steel'],.002)
 box('Grate front rim',(0,-.074,.968),(.187,.012,.013),p['steel'],.002)
 box('Rain canopy',(0,-.016,1.101),(.246,.196,.029),p['blue'],.009,rot=(math.radians(-5),0,0))
 box('Canopy front drip lip',(0,-.111,1.081),(.242,.011,.029),p['blue'],.003)
 for x in [-.1,.1]:box('Canopy support return',(x,.0,1.051),(.013,.153,.092),p['blue'],.003)
 # Honest front opening remains between grate and canopy.
 box('Back service door',(0,.087,.941),(.181,.011,.245),p['steel'],.006)
 cyl('Back quarter-turn latch',(.06,.096,.947),.012,.006,p['dark'],'Y',24,.001)
 box('Latch screwdriver slot',(.06,.100,.947),(.014,.001,.002),p['steel'],0)
 for z in [.864,1.023]:cyl('Rear access hinge',(-.088,.094,z),.007,.041,p['steel'],'Z',20,.0006)
 box('Blank maintenance label',(0,.096,.995),(.083,.002,.031),p['dark'],.001)
 return ('city-cigarette-disposal-pedestal','吸い殻専用の屋外処理スタンド','Outdoor cigarette-disposal pedestal','建物外の喫煙場所向けの吸い殻専用スタンド。雨除け、開いた投入口、消火用格子、内箱、背面の点検扉と固定板を備えます。一般ごみ箱や消防設備ではありません。','A dedicated cigarette-waste pedestal for outdoor smoking areas, with a rain hood, open deposit mouth, crushing grate, inner receptacle, rear service door and anchor plate. It is not a general litter bin or fire-safety device.',['cigarette','ash','smoking-area','吸い殻'])

def grit_bin():
 p=palette();body=p['sand']
 for x in [-.40,.40]:box('Ground skid',(x,0,.036),(.14,.59,.072),p['dark'],.022)
 tapered_shell('Tapered grit storage body',(1.03,.57),(1.19,.72),.055,.722,.026,body)
 # Raised external reinforcement ribs are slanted to follow the taper.
 for x in [-.39,0,.39]:
  for sign in [-1,1]:bar('Molded body reinforcement',(x,sign*.290,.12),(x,sign*.355,.66),.027,.018,body)
 for x in [-.585,.585]:box('Upper body side flange',(x,0,.718),(.040,.733,.035),body,.007)
 for y in [-.35,.35]:box('Upper body front rear flange',(0,y,.718),(1.19,.042,.035),body,.007)
 # Closed sloping lid is a fabricated six-face shell profile, not an unshaped cube.
 w=.625;d=.39;vs=[(-w,-d,.738),(w,-d,.738),(w,d,.738),(-w,d,.738),(-w,-d,.810),(w,-d,.810),(w,d,.858),(-w,d,.858)]
 mesh('Weather shedding closed lid',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],body,.012)
 box('Lid seam shadow',(0,-.37,.736),(1.16,.009,.010),p['dark'],.002)
 for x in [-.43,.43]:
  cyl('Rear lid hinge pin',(x,.39,.769),.018,.15,p['zinc'],'X',24,.0015)
  for xx in [x-.056,x+.056]:box('Hinge mounting lug',(xx,.375,.741),(.024,.045,.071),body,.004)
 # Recessed black grab pocket with separate load-bearing handle.
 box('Front handle recess',(0,-.395,.778),(.28,.008,.036),p['dark'],.010)
 bar('Grip handle',(-.12,-.411,.789),(.12,-.411,.789),.017,.021,body)
 for x in [-.14,.14]:box('Grip mounting block',(x,-.400,.786),(.034,.031,.04),body,.005)
 box('Front label recess',(0,-.336,.524),(.44,.015,.14),p['dark'],.014)
 box('Blank replaceable grit label',(0,-.347,.524),(.39,.010,.10),p['steel'],.009)
 # Three pictographic grains: original geometry, no typeface or trademark.
 for x,z in [(-.08,.512),(.0,.542),(.08,.512)]:sphere('Sand grain marker',(x,-.355,z),(.012,.002,.009),body,12,6)
 for x in [-.60,.60]:
  for y in [-.14,.14]:box('Side lifting handhold',(x,y,.62),(.018,.16,.034),p['dark'],.009)
 return ('city-grit-storage-bin','路面凍結防止砂の貯蔵箱','Roadside grit storage bin','坂道や歩道脇で散布用の砂・融雪材を保管する閉蓋状態の箱。テーパー付き中空本体、補強リブ、斜め蓋、蝶番、取っ手と接地スキッドを備えます。砂・散布器具は付属しません。','A closed-lid storage bin for grit or de-icing material beside sloping streets and sidewalks. Includes a tapered hollow body, reinforcement ribs, weather-shedding lid, hinges, handles and ground skids. Loose grit and spreading tools are not included.',['grit','winter','maintenance','storage','融雪'])

def hose_reel():
 p=palette();center=Vector((0,0,.42))
 # Wall bracket lies toward +Y. Model origin is still base-centered, not wall pivot.
 for x in [-.19,.19]:
  box('Wall fixing rail',(x,.25,.42),(.045,.025,.47),p['blue'],.006)
  for z in [.22,.62]:screw('Wall bolt',(x,.232,z),p['zinc'],'Y',.007)
  bar('Triangular reel support',(x,.23,.23),(x,-.015,.42),.028,.028,p['blue'])
  bar('Upper reel arm',(x,.23,.47),(x,-.015,.47),.029,.026,p['blue'])
 cyl('Reel spindle',(0,-.015,.45),.025,.46,p['zinc'],'X',32,.0015)
 cyl('Hose winding drum',(0,-.015,.45),.105,.29,p['blue'],'X',48,.002)
 for x in [-.163,.163]:
  torus('Open reel outer hoop',(x,-.015,.45),.227,.013,p['blue'],rotation=(0,math.pi/2,0),segments=64)
  cyl('Reel bearing boss',(x,-.015,.45),.041,.035,p['steel'],'X',32,.002)
  for i in range(6):
   a=math.tau*i/6
   bar('Open reel spoke',(x,-.015+.043*math.cos(a),.45+.043*math.sin(a)),(x,-.015+.216*math.cos(a),.45+.216*math.sin(a)),.018,.017,p['blue'])
 # Three layers of a continuous deterministic helical hose; visible hollow spaces remain.
 points=[]
 turns=15
 for i in range(turns*32+1):
  t=i/(turns*32);layer=int(min(2,t*3));local=(t*3)-layer
  x=(-.125+.25*local) if layer%2==0 else (.125-.25*local)
  r=.12+layer*.024;a=2*math.pi*turns*t
  points.append((x,-.015+r*math.cos(a),.45+r*math.sin(a)))
 tube('Wound irrigation hose',points,.010,p['green'],2)
 # The free end descends from the outer coil in a smooth polyline arc.
 pts=[points[-1],(-.13,-.015,.625),(-.19,-.07,.61),(-.21,-.145,.54),(-.22,-.18,.41),(-.24,-.185,.28),(-.28,-.17,.23)]
 tube('Free hose tail',pts,.010,p['green'],2)
 a,b=Vector(pts[-2]),Vector(pts[-1]);direction=(b-a).normalized();end=b+direction*.07
 rod('Brass quick connector',b,end,.016,p['brass'],24)
 rod('Nozzle rubber grip',end,end+direction*.08,.020,p['rubber'],24)
 rod('Adjustable nozzle barrel',end+direction*.08,end+direction*.12,.012,p['brass'],24)
 # Side water feed and independent manual crank.
 rod('Inlet swivel',(.19,-.015,.45),(.25,-.015,.45),.018,p['brass'],24)
 rod('Crank axle',(-.205,-.015,.45),(-.255,-.015,.45),.012,p['steel'])
 bar('Offset crank arm',(-.255,-.015,.45),(-.255,-.12,.35),.018,.018,p['steel'])
 cyl('Crank hand grip',(-.295,-.12,.35),.021,.095,p['rubber'],'X',24,.003)
 return ('city-wall-irrigation-hose-reel','散水用の壁掛けホースリール','Wall-mounted irrigation hose reel','公園管理庫や店舗裏の壁面に取り付ける手回し散水ホースリール。透かしスポーク、巻きホース、給水継手、ノズル、クランクと壁面ブラケットを造形。壁、水栓、給水配管や動くホースは含みません。配置原点は取付面の基準点ではないため、利用先で壁面位置と取付高さを調整してください。','A hand-cranked irrigation hose reel for park service buildings or shop service walls. Features open spokes, wound hose, inlet coupling, nozzle, crank and mounting brackets. No wall, tap, supply plumbing or simulated flexible hose is included. The placement origin is not a mounting datum: adjust the wall offset and installation height in the target scene.',['hose','irrigation','reel','maintenance','散水'])

BUILDERS=[stanchion,cigarette_pedestal,grit_bin,hose_reel]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-001/assets');ap.add_argument('--only',default='');a=ap.parse_args(args)
 out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();spec=fn()
  if a.only and spec[0]!=a.only:continue
  publish_asset(*spec,out,'scripts/city_expansion/public_fixtures.py',azimuth=-55,elevation=23)
