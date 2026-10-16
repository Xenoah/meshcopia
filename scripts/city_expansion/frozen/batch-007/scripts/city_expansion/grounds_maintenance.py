"""Original public garden and grounds-maintenance equipment for Xenoah, CC BY 4.0.
No third-party design, logos, textures or fonts. Blender 4.3.2.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector,Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def pal():return dict(steel=mat('Zinc plated steel',(.36,.40,.42),.8,.36),iron=mat('Rough cast iron',(.08,.095,.10),.55,.67),black=mat('Graphite machine powder coat',(.025,.033,.035),.3,.48),rubber=mat('Non-marking rubber',(.012,.017,.02),0,.86),ochre=mat('Industrial ochre enamel',(.58,.28,.045),.25,.40),blue=mat('Service blue enamel',(.065,.19,.26),.28,.38),white=mat('Blank enamel indicator',(.78,.79,.71),.12,.38),red=mat('Safety control red',(.45,.055,.035),.15,.42),brass=mat('Brass couplings',(.48,.32,.11),.75,.4))
def cyl(n,p,r,d,m,axis='Z',verts=32,b=.002,r2=None):
 if r2 is None:o=cylinder(n,p,r,d,m,verts,bevel=b)
 else:
  bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=p);o=finish(bpy.context.object,n,m,b,True)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,verts=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,b=min(.001,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,d,m):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,.003);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def screw(n,p,m,axis='Z',r=.006):
 cyl(n+' washer',p,r*1.5,r*.25,m,axis,20,.0002);q=list(p);q['XYZ'.index(axis)]+=(-1 if axis=='Y' else 1)*r*.4;cyl(n+' head',q,r,r*.7,m,axis,6,.0003)
def extrusion(n,profile,w,m,b=.004):
 vs=[(x,y,z) for x in [-w/2,w/2] for y,z in profile];k=len(profile);fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,b)
def rounded_frame(n,center,w,h,r,t,m,y=0):
 # Closed tubular rounded rectangle in XZ plane, deterministic circular bends.
 pts=[]
 for cx,cz,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(9):
   an=math.radians(a+i*90/8);pts.append((center[0]+cx+r*math.cos(an),y,center[2]+cz+r*math.sin(an)))
 pts.append(pts[0]);return tube(n,pts,t,m,2)

def wheel(n,p,r,w,m):
 x,y,z=p
 cyl(n+' tire',p,r,w,m['rubber'],'X',40,.005)
 for xx in [x-w*.52,x+w*.52]:
  cyl(n+' recessed wheel disk',(xx,y,z),r*.70,.008,m['iron'],'X',32,.002)
  cyl(n+' axle cap',(xx*1.005,y,z),r*.18,.016,m['steel'],'X',24,.001)
 for i in range(16):
  a=i*math.tau/16
  o=box(n+' tread bar',(x,y+math.sin(a)*(r-.002),z+math.cos(a)*(r-.002)),(w*.85,.018,.007),m['rubber'],.002);o.rotation_euler[0]=-a

def annulus(n,p,outer,inner,depth,m,axis='Z',nseg=40):
 vs=[]
 for rad,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:vs.extend((rad*math.cos(i*math.tau/nseg),rad*math.sin(i*math.tau/nseg),z) for i in range(nseg))
 fs=[]
 for k in range(4):
  for i in range(nseg):j=(i+1)%nseg;fs.append((k*nseg+i,k*nseg+j,((k+1)%4)*nseg+j,((k+1)%4)*nseg+i))
 o=mesh(n,vs,fs,m,0,True);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for i,f in enumerate(o.data.polygons):f.use_smooth=(i//nseg)%2==0
 return o

def webbing(n,points,width,thickness,m):
 pts=[Vector(v) for v in points];verts=[]
 for i,pt in enumerate(pts):
  tangent=(pts[min(len(pts)-1,i+1)]-pts[max(0,i-1)]).normalized();normal=Vector((0,-tangent.z,tangent.y)).normalized()
  for x,t in [(-width/2,-thickness/2),(width/2,-thickness/2),(width/2,thickness/2),(-width/2,thickness/2)]:verts.append(tuple(pt+Vector((x,0,0))+normal*t))
 faces=[]
 for i in range(len(pts)-1):
  for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
 faces.extend([(3,2,1,0),tuple(range((len(pts)-1)*4,len(pts)*4))]);return mesh(n,verts,faces,m,.0015)

def lawn_mower():
 p=pal();paint=mat('Muted garden green enamel',(.085,.22,.13),.22,.42);fabric=mat('Grass catcher woven-look solid color',(.035,.052,.043),0,.95)
 box('Rounded cutting deck',(0,0,.18),(.58,.68,.15),paint,.045)
 box('Deck lower rim',(0,0,.117),(.59,.69,.023),p['iron'],.010)
 for x in [-.31,.31]:
  for y in [-.24,.24]:
   wheel('Mower wheel',(x,y,.111),.111,.047,p)
   box('Wheel height adjuster',(x*.88,y,.165),(.019,.085,.055),p['steel'],.005)
 for x in [-.25,.25]:bar('Wheel carrier rail',(x,-.24,.111),(x,.24,.111),.021,.019,p['iron'])
 box('Engine crankcase',(0,-.065,.305),(.225,.22,.14),p['iron'],.022)
 for i in range(7):box('Air-cooled engine fin',(0,.01,.362+i*.010),(.22,.18,.005),p['steel'],.001)
 box('Engine pull-start cover',(0,-.05,.462),(.255,.25,.075),p['black'],.021)
 cyl('Pull-start ventilation recess',(0,-.053,.504),.079,.010,p['iron'],verts=40,b=.002)
 for i in range(10):
  a=i*math.tau/10;rod('Starter top ventilation spoke',(.027*math.cos(a),-.053+.027*math.sin(a),.511),(.068*math.cos(a),-.053+.068*math.sin(a),.511),.004,p['black'],12)
 cyl('Starter top badge blank',(0,-.053,.511),.025,.008,p['black'],verts=32,b=.002)
 box('Small fuel tank',(.15,-.075,.384),(.13,.21,.16),paint,.016)
 cyl('Fuel cap',(.15,-.08,.472),.026,.018,p['black'],verts=32,b=.003)
 box('Air filter',(-.153,.02,.375),(.095,.17,.11),p['black'],.009)
 box('Grass exit tunnel',(0,.352,.245),(.43,.08,.19),p['black'],.013)
 # Cloth bag with rigid top frame and sloping bottom; original closed mesh, not cloth simulation.
 vs=[(-.23,.36,.19),(.23,.36,.19),(.215,.78,.22),(-.215,.78,.22),(-.23,.36,.45),(.23,.36,.45),(.215,.78,.43),(-.215,.78,.43)]
 mesh('Rear grass catcher bag',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],fabric,.015)
 for x in [-.22,.22]:rod('Catcher upper frame',(x,.36,.455),(x,.77,.435),.009,p['black'])
 rod('Catcher rear frame',(-.22,.77,.435),(.22,.77,.435),.009,p['black'])
 box('Catcher lifting grip',(0,.58,.463),(.17,.045,.027),p['black'],.008)
 for x in [-.24,.24]:
  cyl('Handle deck pivot',(x,.26,.29),.033,.027,p['steel'],'X',24,.002)
  tube('Push handle upright',[(x,.27,.29),(x,.47,.48),(x,.87,.98),(x,.96,1.04)],.016,p['black'],2)
 rod('Operator cushioned handle',(-.24,.96,1.04),(.24,.96,1.04),.024,p['rubber'],32)
 tube('Engine stop bail',[(-.22,.94,1.02),(-.22,.90,1.075),(.22,.90,1.075),(.22,.94,1.02)],.006,p['steel'],2)
 tube('Stop-control cable',[(.22,.94,1.02),(.20,.79,.85),(.19,.45,.48),(.11,.13,.40)],.003,p['black'],1)
 return('city-push-lawn-mower','集草バッグ付き手押し芝刈り機','Push lawn mower with grass catcher','公園や住宅の庭の管理シーンに使う手押し芝刈り機。四輪、丸み付きデッキ、空冷エンジン、操作ハンドルと布製集草バッグを備えます。刈刃は密閉デッキ内として省略し、刈込み・燃焼・袋の変形などの動作はありません。','A push mower for park and residential garden maintenance scenes, with four wheels, rounded deck, air-cooled engine, operator handle and fabric grass catcher. A blade is not modeled inside the enclosed deck; no cutting, combustion or flexible-bag behavior is supplied.',['mower','garden','maintenance','芝刈り'])

def leaf_blower():
 p=pal();poly=mat('Warm orange blower polymer',(.66,.22,.035),0,.53)
 # Upright back frame, cushions and continuous shoulder straps.
 box('Backpack support frame',(0,.12,.32),(.36,.055,.57),p['black'],.022)
 for x in [-.115,.115]:box('Padded back cushion',(x,.165,.34),(.13,.045,.37),p['rubber'],.025)
 for x in [-.15,.15]:
  webbing('Padded shoulder webbing',[(x,.15,.55),(x,.25,.63),(x,.38,.59),(x,.43,.43),(x,.38,.20),(x,.25,.10),(x,.14,.14)],.055,.009,p['black'])
  box('Strap adjustment buckle',(x,.38,.23),(.055,.018,.064),p['iron'],.005)
 box('Backpack base tray',(0,-.005,.037),(.40,.31,.074),p['black'],.016)
 cyl('Fan volute main housing',(0,-.045,.285),.183,.20,poly,'Y',64,.018)
 cyl('Fan inlet recess',(0,-.155,.285),.137,.016,p['black'],'Y',48,.003)
 # Visible concentric front inlet guard rings and radial bars.
 for rr in [.045,.087,.126]:torus('Concentric intake guard',(0,-.169,.285),rr,.004,p['iron'],rotation=(math.pi/2,0,0),segments=40)
 for i in range(12):
  a=i*math.tau/12;rod('Intake radial guard',(0,-.173,.285),(.133*math.cos(a),-.173,.285+.133*math.sin(a)),.0035,p['iron'],12)
 cyl('Intake center cap',(0,-.179,.285),.024,.013,p['black'],'Y',24,.002)
 box('Blower engine cylinder',(0,-.045,.515),(.19,.15,.15),p['iron'],.016)
 for i in range(6):box('Engine fin',(0,-.045,.48+i*.017),(.22,.18,.007),p['steel'],.002)
 box('Engine top cover',(0,-.045,.606),(.22,.19,.048),poly,.013)
 box('Translucency-free fuel reservoir',(-.135,-.04,.12),(.11,.19,.12),p['white'],.018)
 cyl('Fuel reservoir cap',(-.15,-.04,.191),.023,.018,p['black'],verts=28,b=.003)
 box('Blower side exhaust',(-.158,-.055,.45),(.086,.11,.11),p['black'],.012)
 # Flexible hose exits at side then curves into a lower rigid blower tube.
 points=[(.14,-.01,.27),(.23,-.005,.26),(.29,-.04,.22),(.32,-.13,.16),(.33,-.27,.12),(.34,-.41,.10)]
 tube('Flexible air hose',points,.045,p['rubber'],3)
 for i in range(9):
  y=-.12-i*.031;torus('Flexible hose convolution',(.328+(i*.0015),y,.16-i*.0075),.045,.006,p['black'],rotation=(math.pi/2,0,0),segments=32)
 # Rigid nozzle retains a genuine hollow opening with shell walls.
 annulus('Rigid blower tube',(.34,-.72,.10),.047,.039,.61,p['black'],'Y',48)
 annulus('Nozzle flared ring',(.34,-1.025,.10),.050,.039,.035,poly,'Y',48)
 box('Blower handgrip base',(.34,-.44,.16),(.066,.09,.051),poly,.010)
 box('Blower hand grip',(.34,-.445,.235),(.042,.06,.13),p['black'],.012,rot=(math.radians(-10),0,0))
 box('Trigger',(.34,-.478,.24),(.018,.013,.043),p['red'],.004)
 tube('Throttle cable',[(.34,-.43,.24),(.31,-.22,.27),(.24,-.07,.36),(.12,.02,.48)],.0025,p['black'],1)
 return('city-backpack-leaf-blower','背負い式の落ち葉ブロワー','Backpack leaf blower','公園管理や歩道清掃に使う背負い式ブロワー。背面パッドと肩ベルト、ファンの吸気ガード、小型原動機、蛇腹ホース、操作グリップと中空ノズルを備えます。人、落ち葉、送風・騒音・燃焼・柔軟物の挙動は含みません。','A backpack blower for park care and sidewalk cleanup, with back pads and shoulder straps, a guarded fan intake, small power unit, flexible hose, control grip and hollow nozzle. No person, leaves, airflow, sound, combustion or flexible-body behavior is supplied.',['leaf-blower','garden','cleanup','ブロワー'])

def clothesline():
 p=pal();line=mat('Off-white polymer clothesline',(.62,.65,.58),0,.8)
 cyl('Ground socket',(0,0,.11),.047,.22,p['iron'],verts=40,b=.004)
 cyl('Central rotary mast',(0,0,1.02),.031,2.04,p['steel'],verts=48,b=.002)
 cyl('Rotating upper hub',(0,0,1.88),.071,.13,p['blue'],verts=40,b=.004)
 cyl('Lower sliding hub',(0,0,1.25),.063,.12,p['blue'],verts=40,b=.004)
 cyl('Mast cap',(0,0,2.055),.039,.03,p['black'],verts=40,b=.004)
 # Four telescoping radial arms and independent diagonal tensioning struts.
 for i in range(4):
  an=math.pi/4+i*math.tau/4;d=Vector((math.cos(an),math.sin(an),0));start=d*.06;end=d*1.34
  bar('Rotary drying arm',(start.x,start.y,1.89),(end.x,end.y,1.74),.031,.026,p['steel'])
  bar('Folding support stay',(d.x*.05,d.y*.05,1.25),(d.x*.72,d.y*.72,1.81),.018,.019,p['steel'])
  cyl('Arm hinge pin',(d.x*.07,d.y*.07,1.87),.011,.053,p['iron'],'X',20,.001)
  sphere('Arm protective endcap',(end.x,end.y,1.74),(.026,.026,.026),p['blue'],16,8)
 # Nested four-sided clotheslines around the arms, sag is intentionally slight/static.
 for ring in range(1,7):
  r=.24+ring*.17;pts=[]
  for i in range(4):
   a=math.pi/4+i*math.tau/4;b=a+math.pi/2;z=1.89-r/1.34*.15
   A=Vector((r*math.cos(a),r*math.sin(a),z));B=Vector((r*math.cos(b),r*math.sin(b),z));pts.extend([tuple(A),tuple((A+B)/2+Vector((0,0,-.018)))])
  pts.append(pts[0]);tube('Square clothesline circuit %02d'%ring,pts,.0026,line,1)
 box('Hub height-lock bracket',(.063,0,1.25),(.026,.042,.055),p['black'],.004)
 rod('Height-lock lever',(.07,0,1.26),(.13,0,1.31),.007,p['black'],16)
 tube('Opening pull loop',[(0,-.065,1.29),(0,-.10,1.09),(.045,-.12,1.05),(.07,-.10,1.09),(.02,-.065,1.29)],.004,p['black'],2)
 return('city-rotary-clothesline','回転式の屋外物干し','Rotary outdoor clothesline','共同住宅の中庭や住宅の庭に設置する開いた状態の回転物干し。支柱、可動を模した上下ハブ、4本の腕と支え、6周の実ジオメトリ物干し紐を造形。洗濯物、地面、回転・折畳み・紐のシミュレーションは含みません。','An open rotary clothesline for residential or shared courtyards, with a mast, upper/sliding hubs, four arms and support stays, and six actual geometry clothesline circuits. Laundry, ground, rotation, folding and line simulation are not included.',['clothesline','courtyard','laundry','物干し'])

def compost_tumbler():
 p=pal();poly=mat('Forest green compost polymer',(.045,.13,.075),0,.70)
 # Faceted rotating drum, closed volume with offset vent covers and hatch.
 o=cyl('Octagonal compost drum',(0,0,.78),.38,.82,poly,'X',8,.012);o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion((1,0,0),math.pi/8)@o.rotation_euler.to_quaternion()
 for x in [-.416,.416]:
  o=cyl('Octagonal drum end flange',(x,0,.78),.385,.026,p['black'],'X',8,.005);o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion((1,0,0),math.pi/8)@o.rotation_euler.to_quaternion()
  cyl('Drum axle boss',(x,0,.78),.095,.047,p['iron'],'X',32,.003)
 for x in [-.45,.45]:
  rod('Horizontal support axle',(x-.04,0,.78),(x+.04,0,.78),.025,p['steel'],28)
  for y in [-.31,.31]:
   bar('A-frame drum stand',(x,y,.045),(x,0,.78),.037,.037,p['black'])
   box('Stand ground foot',(x,y,.027),(.12,.12,.054),p['rubber'],.009)
  bar('Lower A-frame tie',(x,-.27,.15),(x,.27,.15),.031,.031,p['black'])
 for y in [-.29,.29]:bar('Cross-frame lower stretcher',(-.45,y,.11),(.45,y,.11),.030,.030,p['black'])
 # Recessed loading door flush on the vertical forward drum facet.
 box('Loading door surround',(0,-.355,.78),(.53,.026,.25),p['black'],.010)
 box('Closed loading hatch',(0,-.373,.78),(.47,.019,.198),poly,.007)
 rod('Loading hatch handle',(-.14,-.416,.81),(.14,-.416,.81),.014,p['black'],24)
 for x in [-.14,.14]:rod('Hatch handle mounting',(x,-.375,.81),(x,-.416,.81),.010,p['black'],20)
 for x in [-.30,.30]:
  for y in [-.085,.085]:box('Covered aeration vent',(x,y,1.135),(.055,.09,.018),p['black'],.005)
 for x in [-.245,.245]:
  for an in [math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]:
   y=.352*math.cos(an);z=.78+.352*math.sin(an);o=box('External panel stiffener',(x,y,z),(.035,.11,.027),poly,.004);o.rotation_euler[0]=an-math.pi/2
 bar('Turning crank arm',(.515,0,.78),(.515,-.15,.69),.020,.020,p['steel'])
 cyl('Turning crank grip',(.57,-.15,.69),.023,.11,p['rubber'],'X',28,.003)
 return('city-compost-tumbler','架台付きの回転コンポスター','Stand-mounted compost tumbler','公共菜園や住宅庭で使う密閉ドラム式コンポスターの外観モデル。八角形ドラム、架台、支持軸、閉じた投入扉、通気カバーと手回しクランクを備えます。中身・内部撹拌羽根・分解処理・回転動作は含みません。','An exterior model of a closed drum composter for community gardens and residential yards, with an octagonal drum, stand, axle supports, shut loading hatch, covered vents and hand crank. Contents, internal paddles, decomposition and rotation behavior are not included.',['compost','garden','recycling','コンポスター'])

BUILDERS=[lawn_mower,leaf_blower,clothesline,compost_tumbler]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-007/assets');p.add_argument('--only',default='');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/grounds_maintenance.py',azimuth=-55,elevation=24)
