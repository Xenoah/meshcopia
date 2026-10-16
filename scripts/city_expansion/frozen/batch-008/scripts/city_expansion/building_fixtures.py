"""Original static public-building fixtures for Xenoah / Meshcopia, CC BY 4.0.
Decorative geometry only: no functional, medical, hygiene, child-use or fire-safety
certification; no instructions for operating physical equipment.
Run with Blender 4.3.2; only this source and frozen common.py are required.
"""
import sys, math, argparse
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

GENERATOR='scripts/city_expansion/building_fixtures.py'

def palette():
 return dict(steel=mat('Satin stainless steel',(.49,.56,.59),.82,.29), alloy=mat('Brushed aluminium hardware',(.44,.49,.51),.72,.37), dark=mat('Graphite recessed surfaces',(.019,.025,.029),.10,.6), rubber=mat('Matte black flexible polymer',(.012,.017,.019),0,.77), ivory=mat('Warm ivory molded polymer',(.80,.78,.69),0,.36), white=mat('Warm white enamel',(.82,.85,.82),.18,.29), green=mat('Deep green pipe enamel',(.055,.28,.16),.27,.36), yellow=mat('Yellow valve marker',(.89,.57,.055),.12,.42), red=mat('Red cylinder enamel',(.62,.035,.025),.22,.31), brass=mat('Valve brass',(.58,.39,.12),.76,.28), paper=mat('Blank unprinted label',(.86,.85,.76),0,.76), blue=mat('Sensor blue inset',(.025,.11,.16),.35,.25))

def cyl(n,p,r,d,m,axis='Z',verts=48,bev=.001):
 o=cylinder(n,p,r,d,m,verts,bevel=bev)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(n,a,b,r,m,verts=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def beam(n,a,b,w,d,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def screw(n,p,m,axis='Z',r=.006):
 cyl(n+' washer',p,r*1.65,r*.28,m,axis,24,.0004)
 q=list(p);q['XYZ'.index(axis)]+= (-1 if axis=='Y' else 1)*r*.5
 cyl(n+' hex head',q,r,r*.8,m,axis,6,.0004)

def round_box(n,p,s,m,bevel=.025,segments=5):
 o=box(n,p,s,m,0);b=o.modifiers.new('Rounded molded corners','BEVEL');b.width=min(bevel,min(s)*.45);b.segments=segments
 b=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');b.keep_sharp=True
 return o

def lathe(n,profile,m,segments=72,center=(0,0,0)):
 vs=[];rings=[]
 for r,z in profile:
  if r==0:rings.append([len(vs)]);vs.append((center[0],center[1],z+center[2]))
  else:
   rings.append(list(range(len(vs),len(vs)+segments)))
   vs.extend((center[0]+r*math.cos(i*math.tau/segments),center[1]+r*math.sin(i*math.tau/segments),z+center[2]) for i in range(segments))
 fs=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  if len(a)==1 and len(b)==1:continue
  for i in range(segments):
   j=(i+1)%segments
   if len(a)==1:fs.append((a[0],b[i],b[j]))
   elif len(b)==1:fs.append((a[i],b[0],a[j]))
   else:fs.append((a[i],b[i],b[j],a[j]))
 return mesh(n,vs,fs,m,0,True)

def rr_loop(w,d,r,n=16,cx=0,cy=0,z=0):
 vs=[]
 for x,y,start in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
  for i in range(n):
   a=math.radians(start+90*i/n);vs.append((cx+x+r*math.cos(a),cy+y+r*math.sin(a),z))
 return vs

def rr_profiles(n,profiles,m,segments=16,cap=False):
 # Each profile is (width, depth, corner radius, z, y offset).
 vs=[]
 for w,d,r,z,y in profiles:vs.extend(rr_loop(w,d,r,segments,cy=y,z=z))
 count=4*segments;fs=[]
 pairs=list(zip(range(len(profiles)-1),range(1,len(profiles))))
 if not cap:pairs.append((len(profiles)-1,0))
 for a,b in pairs:
  for i in range(count):j=(i+1)%count;fs.append((a*count+i,a*count+j,b*count+j,b*count+i))
 if cap:fs.extend([tuple(reversed(range(count))),tuple((len(profiles)-1)*count+i for i in range(count))])
 return mesh(n,vs,fs,m,0,True)

def bezier_tube(n,points,r,m,steps=8,res=2):
 # Interpolating Catmull-Rom centerline, endpoints included; deterministic.
 pp=[Vector(x) for x in points];out=[]
 for i in range(len(pp)-1):
  a=pp[max(i-1,0)];b=pp[i];c=pp[i+1];d=pp[min(i+2,len(pp)-1)]
  for j in range(steps):
   t=j/steps;v=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);out.append(v)
 out.append(pp[-1]);return tube(n,out,r,m,res)

def closed_tube(n,points,r,m,res=3):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=res;c.use_fill_caps=False
 sp=c.splines.new('POLY');sp.points.add(len(points)-1);sp.use_cyclic_u=True
 for v,co in zip(sp.points,points):v.co=(*co,1)
 o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);c.materials.append(m);return o

def underside_render(path):
 # Extra low fill reveals real undersides without modifying exported geometry.
 obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
 bounds=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
 lo=Vector([min(v[i] for v in bounds) for i in range(3)]);hi=Vector([max(v[i] for v in bounds) for i in range(3)])
 center=(lo+hi)/2;span=max(hi-lo)
 bpy.ops.object.light_add(type='AREA',location=center+Vector((.4,-1.1,-1.3))*span)
 fill=bpy.context.object;fill.data.energy=260*span*span;fill.data.shape='DISK';fill.data.size=1.1*span;look_at(fill,center)
 render(path,azimuth=-55,elevation=-26,size=800)
 bpy.data.objects.remove(fill,do_unlink=True)

def tube_ring(n,p,outer,inner,length,m,axis='Z',segments=64):
 o=lathe(n,[(inner,-length/2),(outer,-length/2),(outer,length/2),(inner,length/2)],m,segments)
 o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return o

def hand_dryer():
 p=palette()
 # Continuous exterior/inner shell; the underside is genuinely open, not a black decal.
 rr_profiles('Rounded enamel dryer shell',[(.252,.142,.032,.065,-.003),(.270,.158,.036,.092,-.003),(.270,.157,.038,.290,.005),(.254,.141,.037,.327,.012),(.225,.115,.029,.336,.014),(.218,.108,.027,.328,.014),(.235,.124,.028,.307,.010),(.248,.135,.027,.105,.000),(.232,.120,.024,.065,-.003)],p['white'])
 round_box('Solid top crown',(0,.010,.329),(.217,.107,.016),p['white'],.014,5)
 # Lower rectangular nozzle has a real passage and rounded lip.
 rr_profiles('Downward outlet passage',[(.133,.062,.014,.035,-.030),(.139,.068,.016,.040,-.030),(.139,.068,.016,.071,-.030),(.121,.050,.011,.071,-.030),(.121,.050,.011,.039,-.030)],p['steel'],16)
 round_box('Recessed internal air baffle',(0,-.025,.109),(.171,.076,.010),p['dark'],.012)
 for x in [-.042,-.014,.014,.042]:box('Outlet flow divider',(x,-.030,.061),(.003,.047,.023),p['alloy'],.001)
 # Rear intake vent has separated slats and open gaps.
 for i in range(12):box('Open intake grille slat %02d'%i,(-.101+i*.0184,.044,.067),(.008,.033,.010),p['alloy'],.0015)
 for y in [.023,.064]:box('Intake grille rim',(0,y,.070),(.224,.006,.015),p['alloy'],.002)
 for x in [-.111,.111]:box('Intake grille end return',(x,.043,.070),(.006,.039,.015),p['alloy'],.0015)
 round_box('Front sensor bezel',(0,-.082,.117),(.050,.008,.021),p['dark'],.008,5)
 round_box('Optical sensor inset',(0,-.087,.117),(.032,.004,.011),p['blue'],.004,5)
 round_box('Blank unprinted product badge',(0,-.074,.267),(.078,.004,.021),p['alloy'],.005,4)
 # Rear backplate, lifted mounting cleats and cable inlet are visible from the back.
 round_box('Rear removable backplate',(0,.087,.191),(.228,.024,.272),p['alloy'],.018,5)
 for x in [-.078,.078]:
  box('Raised rear fixing rail',(x,.108,.192),(.028,.025,.230),p['dark'],.005)
  for z in [.098,.286]:
   tube_ring('Rear mounting socket',(x,.123,z),.010,.005,.008,p['alloy'],'Y',32)
   screw('Rear backplate fastener',(x,.103,z),p['steel'],'Y',.004)
 box('Back horizontal mounting hook',(0,.125,.280),(.185,.018,.025),p['steel'],.004)
 for x in [-.108,.108]:
  for z in [.115,.268]:screw('Side cover fastener',(x,.071,z),p['steel'],'Y',.0035)
 tube_ring('Rear cable inlet grommet',(0,.108,.139),.016,.008,.009,p['rubber'],'Y',48)
 for z in [.185,.212]:box('Rear horizontal strengthening bead',(0,.102,z),(.117,.006,.008),p['alloy'],.002)
 return ('city-wall-hand-dryer','下向きノズルの壁掛けハンドドライヤー','Wall-mounted downward-nozzle hand dryer','公共トイレの壁面向けの静的なハンドドライヤー。丸みのある外殻、実際に開いた下面ノズルと吸気格子、センサー風部品、背面固定板と配線入口を造形。壁や電源配線は含みません。送風・加熱・衛生効果はなく、衛生・電気・安全認証はありません。配置時は壁面からの距離と取付高さを調整してください。','A static wall hand-dryer prop for public washroom scenes, with a rounded shell, genuinely open downward outlet, separated intake slats, sensor-like insert, rear mount and cable inlet. Wall and power wiring are absent. It provides no airflow, heat or hygiene effect and has no hygiene, electrical or safety certification. Adjust wall offset and installation height in the target scene.',['washroom','hand-dryer','wall-fixture','ハンドドライヤー'])

def baby_station():
 p=palette()
 # Wide shallow tray with a raised rounded perimeter and a recessed integral bed.
 rr_profiles('Open molded changing tray',[(.834,.540,.072,.221,-.071),(.883,.586,.083,.236,-.071),(.900,.608,.087,.285,-.071),(.896,.603,.086,.308,-.071),(.852,.559,.073,.308,-.071),(.805,.512,.063,.278,-.071),(.771,.478,.057,.270,-.071)],p['ivory'],20,cap=True)
 # The cap closes the lowered bed only; the sides and recessed lip remain visible.
 rr_profiles('Rounded tray upper lip',[(.895,.602,.086,.299,-.071),(.900,.607,.088,.305,-.071),(.895,.602,.086,.313,-.071),(.856,.563,.075,.313,-.071),(.850,.557,.073,.305,-.071)],p['white'],20)
 round_box('Wall-mounted rear enclosure',(0,.263,.440),(.837,.098,.563),p['ivory'],.043,8)
 round_box('Enclosure front inset',(0,.209,.473),(.740,.016,.397),p['white'],.007,5)
 round_box('Blank front information plaque',(0,.197,.543),(.250,.010,.115),p['paper'],.004,4)
 # Molded nesting groove, modeled as an original raised perimeter without text.
 for x in [-.351,.351]:box('Back enclosure inner side bead',(x,.195,.465),(.014,.012,.332),p['ivory'],.005)
 box('Back enclosure upper bead',(0,.195,.634),(.705,.012,.014),p['ivory'],.005)
 # Hinge barrels alternate visibly along the wall edge, with continuous axle.
 cyl('Hinge axle',(0,.195,.254),.012,.780,p['steel'],'X',48,.001)
 for i in range(9):
  x=-.350+i*.0875;cyl('Static molded hinge barrel %02d'%i,(x,.195,.254),.027,.068,p['ivory'] if i%2==0 else p['alloy'],'X',40,.002)
 for x in [-.397,.397]:
  cyl('Hinge end cap',(x,.195,.254),.019,.018,p['alloy'],'X',32,.0015)
  box('Hinge fixing plate',(x,.219,.273),(.047,.022,.112),p['alloy'],.006)
 # Two underside diagonal supports and supporting molded ribs.
 for x in [-.320,.320]:
  beam('Fixed underside support arm',(x,.230,.122),(x,-.274,.235),.025,.028,p['alloy'],.004)
  cyl('Support wall hinge',(x,.223,.135),.017,.046,p['steel'],'X',32,.001)
  cyl('Support tray hinge',(x,-.258,.231),.016,.047,p['steel'],'X',32,.001)
  box('Wall support saddle',(x,.241,.142),(.059,.034,.101),p['alloy'],.005)
 for x in [-.260,-.130,0,.130,.260]:box('Tray underside molded rib',(x,-.067,.220),(.017,.426,.031),p['ivory'],.005)
 box('Tray underside cross rib',(0,-.240,.214),(.698,.017,.034),p['ivory'],.005)
 # Static belt follows the bed and lip. It is decorative, not a tested restraint.
 for sign in [-1,1]:
  x0=sign*.027;x1=sign*.360
  pts=[(x0,-.090,.282),(sign*.185,-.090,.284),(x1,-.090,.290),(sign*.411,-.090,.314)]
  vs=[]
  for x,y,z in pts:vs.extend([(x,y-.025,z),(x,y+.025,z),(x,y+.025,z+.003),(x,y-.025,z+.003)])
  fs=[]
  for i in range(len(pts)-1):
   for j in range(4):k=(j+1)%4;fs.append((i*4+j,i*4+k,(i+1)*4+k,(i+1)*4+j))
  fs.extend([(3,2,1,0),tuple((len(pts)-1)*4+i for i in range(4))]);mesh('Static decorative retaining strap',vs,fs,p['dark'],.0007)
 round_box('Belt buckle body',(0,-.090,.289),(.075,.065,.016),p['dark'],.005,4)
 round_box('Buckle latch insert',(0,-.093,.300),(.032,.033,.006),p['alloy'],.003,3)
 for x in [-.412,.412]:
  box('Strap anchor tab',(x,-.09,.308),(.018,.066,.010),p['alloy'],.003)
  screw('Strap anchor screw',(x,-.09,.315),p['steel'],r=.004)
 # Rear mounting geometry stays intentionally exposed in the supplied model.
 for x in [-.286,.286]:
  box('Rear mounting cleat',(x,.321,.443),(.062,.026,.430),p['alloy'],.008)
  for z in [.267,.624]:tube_ring('Rear wall fixing hole',(x,.337,z),.015,.007,.012,p['steel'],'Y',32)
 for z in [.300,.585]:box('Rear enclosure reinforcing ridge',(0,.317,z),(.660,.013,.016),p['ivory'],.005)
 return ('city-folding-baby-changing-station','開いた状態の壁掛けおむつ交換台','Open wall-mounted baby-changing station','公共施設のトイレを演出する、開いた状態で固定した壁掛けおむつ交換台。浅い成形トレー、壁面ケース、蝶番、下面の支持材と補強リブ、静止ベルトを備えます。壁や乳児は含みません。折り畳み動作や耐荷重・拘束・衛生機能はなく、乳幼児用製品としての安全認証もありません。実用品の設計や安全な使用方法を示すものではありません。壁面位置と設置高さは利用先で調整してください。','A decorative wall-mounted baby-changing station held in its open pose for public washroom scenes. Includes a recessed molded tray, wall enclosure, hinge barrels, underside braces and ribs, and a static belt. No wall or child is included. There is no folding behavior, rated support, restraint or hygiene function and no child-use safety certification. It is not a physical product design or safe-use guidance. Adjust wall offset and installation height in the target scene.',['washroom','changing-station','wall-fixture','おむつ交換台'])

def eyewash_shower():
 p=palette()
 # Anchored column and shut-off fittings are generic decorative shapes.
 lathe('Pipe pedestal floor flange',[(0,.010),(.115,.010),(.122,.017),(.122,.032),(.108,.040),(.040,.040),(.035,.061),(0,.061)],p['green'],80,center=(0,.115,0))
 for a in [math.pi/4+i*math.pi/2 for i in range(4)]:screw('Floor flange anchor',(.090*math.cos(a),.115+.090*math.sin(a),.038),p['steel'],r=.011)
 cyl('Main upright supply column',(0,.115,1.109),.026,2.110,p['green'],verts=64,bev=.001)
 for z in [.144,.850,1.292,2.030]:cyl('Pipe union coupling',(0,.115,z),.035,.058,p['green'],verts=48,bev=.003)
 cyl('Lower drain inspection sleeve',(0,.115,.175),.036,.077,p['alloy'],verts=48,bev=.002)
 # Smooth curved upper arm, not a square disconnected elbow.
 bezier_tube('Bent overhead shower arm',[(0,.115,2.084),(0,.115,2.186),(0,.089,2.230),(0,.025,2.253),(0,-.233,2.253),(0,-.349,2.230),(0,-.381,2.170)],.026,p['green'],steps=8,res=3)
 cyl('Overhead valve body',(0,-.098,2.253),.043,.104,p['brass'],'Y',48,.002)
 for y in [-.150,-.047]:cyl('Overhead union hex',(0,y,2.253),.044,.023,p['green'],'Y',6,.002)
 # Thin-walled bell with true open underside; rings and radial bars create real gaps.
 lathe('Open drench shower bell',[(.025,2.180),(.035,2.180),(.048,2.149),(.081,2.122),(.125,2.102),(.163,2.090),(.169,2.082),(.166,2.069),(.155,2.065),(.150,2.077),(.119,2.091),(.073,2.111),(.040,2.139),(.025,2.153)],p['green'],80,center=(0,-.381,0))
 for r in [.045,.085,.125,.151]:tube_ring('Open shower distributor ring',(0,-.381,2.076),r+.003,r-.003,.007,p['alloy'],segments=64)
 for i in range(16):
  a=math.tau*i/16;rod('Distributor spoke',(.013*math.cos(a),-.381+.013*math.sin(a),2.076),(.151*math.cos(a),-.381+.151*math.sin(a),2.076),.0028,p['alloy'],12)
 cyl('Shower distributor central boss',(0,-.381,2.076),.017,.018,p['alloy'],verts=32,bev=.001)
 # Eye bowl with actual recessed basin, curled lip, drain and two curved outlets.
 bezier_tube('Eyewash branch pipe',[(0,.115,.942),(0,-.026,.942),(0,-.165,.942),(0,-.200,.970)],.022,p['green'],steps=6,res=3)
 cyl('Eyewash branch valve',(0,-.022,.942),.037,.090,p['brass'],'Y',40,.002)
 lathe('Open stainless eyewash basin',[(0,.965),(.060,.965),(.095,.985),(.153,1.025),(.202,1.066),(.215,1.074),(.216,1.083),(.208,1.089),(.199,1.083),(.146,1.040),(.091,1.005),(.045,.988),(0,.988)],p['steel'],96,center=(0,-.205,0))
 cyl('Basin underside drain collar',(0,-.205,.955),.040,.044,p['alloy'],verts=48,bev=.002)
 tube_ring('Recessed drain rim',(0,-.205,.991),.027,.020,.008,p['dark'],segments=48)
 for x in [-.013,0,.013]:box('Drain grille cross bar',(x,-.205,.995),(.004,.039,.006),p['alloy'],.001)
 for sign in [-1,1]:
  bezier_tube('Curved eye nozzle riser',[(sign*.068,-.130,1.031),(sign*.094,-.137,1.083),(sign*.091,-.159,1.142),(sign*.069,-.192,1.154)],.011,p['alloy'],steps=7,res=3)
  sphere('Eye nozzle swivel',(sign*.068,-.192,1.154),(.019,.020,.017),p['alloy'],24,12)
  tube_ring('Open eye nozzle rim',(sign*.068,-.203,1.169),.022,.012,.015,p['green'],segments=48)
  # Dust cap rests to the side, connected by a short static loop.
  cyl('Parked nozzle dust cap',(sign*.117,-.181,1.140),.021,.010,p['green'],verts=40,bev=.002)
  bezier_tube('Dust cap tether',[(sign*.083,-.193,1.159),(sign*.115,-.222,1.135),(sign*.132,-.203,1.126),(sign*.118,-.181,1.140)],.0025,p['rubber'],steps=6,res=2)
 # Decorative side handwheel and upper pull rod, without instructional symbols.
 rod('Eyewash valve spindle',(.0,-.022,.942),(.123,-.022,.942),.012,p['brass'],24)
 torus('Eyewash valve handwheel',(.137,-.022,.942),.067,.008,p['green'],rotation=(0,math.pi/2,0),segments=64)
 cyl('Eyewash wheel hub',(.137,-.022,.942),.022,.021,p['green'],'X',32,.002)
 for i in range(5):
  a=i*math.tau/5;rod('Handwheel spoke',(.137,-.022,.942),(.137,-.022+.059*math.cos(a),.942+.059*math.sin(a)),.005,p['green'],16)
 rod('Upper valve actuator spindle',(.0,-.098,2.253),(.087,-.098,2.253),.010,p['brass'],24)
 beam('Valve actuator crank',(.087,-.098,2.253),(.087,-.179,2.236),.018,.012,p['alloy'],.002)
 rod('Hanging shower pull rod',(.087,-.179,2.236),(.087,-.179,1.488),.0045,p['alloy'],20)
 pts=[(.087,-.179,1.488),(-.010,-.179,1.385),(.184,-.179,1.385),(.087,-.179,1.488)]
 closed_tube('Triangular pull handle',pts[:-1],.008,p['yellow'],3)
 # Rear connection is a visibly hollow socket, not hidden behind a solid cap.
 rod('Rear feed stub',(0,.115,.374),(0,.226,.374),.026,p['green'],40)
 tube_ring('Open rear supply coupling',(0,.245,.374),.039,.022,.059,p['brass'],'Y',64)
 cyl('Feed union hex',(0,.218,.374),.044,.030,p['green'],'Y',6,.002)
 return ('city-emergency-eyewash-shower','洗眼ボウル付きの緊急シャワー設備模型','Combination eyewash and drench shower prop','工場や公共施設の管理区域を演出する洗眼・シャワー複合設備の静的模型。開いた洗眼ボウル、二つのノズル、実際に隙間を持つ上部散水口、曲がり配管、手回し弁、引き棒と固定フランジを備えます。給排水設備や水は含みません。給水・洗眼・救急・衛生機能はなく、安全・医療・性能認証はありません。実用品の設計や操作手順ではありません。','A static combination eyewash and drench-shower prop for industrial or public-building service scenes. Features an open basin, two eye nozzles, open overhead distributor geometry, curved plumbing, valve handwheel, pull rod and floor flange. Supply infrastructure and water are absent. It has no water-delivery, eye-treatment, emergency or hygiene function and no safety, medical or performance certification. This is not a physical equipment design or operating guide.',['eyewash','shower','industrial','static-prop','洗眼設備'])

def extinguisher():
 p=palette()
 lathe('Rounded pressure-cylinder visual shell',[(0,.028),(.064,.028),(.080,.037),(.087,.055),(.089,.083),(.089,.395),(.087,.425),(.079,.448),(.061,.470),(.041,.486),(.025,.496),(.024,.522),(0,.522)],p['red'],96)
 lathe('Protective bottom foot',[(.072,0),(.085,0),(.092,.012),(.092,.039),(.087,.051),(.081,.052),(.078,.038),(.072,.030)],p['dark'],96)
 # Four shallow feet integrated into the lower support collar.
 for a in [i*math.pi/2 for i in range(4)]:
  o=box('Foot standing pad',(.063*math.cos(a),.063*math.sin(a),.007),(.041,.026,.014),p['rubber'],.004);o.rotation_euler[2]=a
 cyl('Neck collar',(0,0,.515),.031,.026,p['brass'],verts=48,bev=.002)
 cyl('Valve threaded base',(0,0,.534),.028,.027,p['brass'],verts=6,bev=.0015)
 round_box('Valve body',(0,0,.555),(.061,.046,.043),p['brass'],.007,4)
 cyl('Valve stem',(0,0,.582),.010,.031,p['steel'],verts=32,bev=.001)
 # Gauge faces the front; ring, tick marks and pointer are decorative and uncalibrated.
 rod('Gauge stem',(0,-.012,.558),(0,-.047,.569),.011,p['brass'],32)
 tube_ring('Gauge protective bezel',(0,-.057,.573),.027,.022,.018,p['steel'],'Y',64)
 cyl('Blank gauge dial',(0,-.065,.573),.022,.003,p['paper'],'Y',64,.0005)
 for i in range(9):
  a=math.radians(-145+i*36.25);x=.0175*math.cos(a);z=.573+.0175*math.sin(a)
  beam('Unnumbered decorative gauge tick',(x,-.067,z),(x*.82,-.067,.573+(z-.573)*.82),.0012,.0012,p['dark'],.0002)
 rod('Fixed decorative gauge pointer',(0,-.069,.573),(.010,-.069,.584),.0012,p['red'],12)
 cyl('Dial pointer hub',(0,-.070,.573),.003,.003,p['dark'],'Y',24,.0005)
 # Separated lower carrying loop and upper squeeze lever, all frozen in one pose.
 lower=[(-.020,.003,.589),(.021,.003,.604),(.122,.003,.604),(.141,.003,.589),(.132,.003,.574),(.045,.003,.574),(.022,.003,.582)]
 closed_tube('Open carrying-handle loop',lower,.009,p['dark'],3)
 beam('Upper squeeze lever',(-.018,.005,.610),(.134,.005,.632),.022,.012,p['dark'],.003)
 cyl('Lever pivot',(-.012,.004,.599),.009,.043,p['steel'],'Y',32,.001)
 cyl('Pull-pin stem',(-.020,.002,.589),.0033,.071,p['steel'],'Y',24,.0004)
 torus('Pull-pin ring',(-.020,-.043,.589),.016,.0028,p['steel'],rotation=(math.pi/2,0,0),segments=48)
 # Side hose follows a gentle loop; the held nozzle has a real open mouth.
 rod('Hose outlet fitting',(-.024,.004,.551),(-.064,.004,.551),.011,p['brass'],32)
 cyl('Hose fitting hex',(-.057,.004,.551),.014,.025,p['brass'],'X',6,.001)
 bezier_tube('Curved discharge hose',[(-.070,.004,.551),(-.108,.002,.537),(-.130,-.004,.474),(-.133,-.014,.364),(-.129,-.023,.265),(-.119,-.031,.237)],.009,p['rubber'],steps=9,res=3)
 lathe('Hollow discharge nozzle',[(.008,.150),(.018,.150),(.021,.158),(.019,.198),(.014,.229),(.014,.245),(.008,.245)],p['dark'],64,center=(-.119,-.031,0))
 tube_ring('Nozzle open rim',(-.119,-.031,.154),.021,.013,.009,p['dark'],segments=64)
 box('Nozzle retaining bracket',(-.099,-.031,.221),(.040,.034,.021),p['steel'],.004)
 cyl('Retaining bracket bolt',(-.089,-.031,.221),.006,.039,p['steel'],'X',6,.001)
 # Blank label follows the cylinder curvature, with no brand or operating text.
 vs=[];steps=40
 for r,z in [(.0895,.149),(.0895,.369),(.0902,.149),(.0902,.369)]:
  for i in range(steps+1):
   a=math.radians(225+90*i/steps);vs.append((r*math.cos(a),r*math.sin(a),z))
 N=steps+1;fs=[]
 for i in range(steps):
  j=i+1;fs.extend([(i,j,N+j,N+i),(2*N+j,2*N+i,3*N+i,3*N+j),(i,2*N+i,2*N+j,j),(N+j,3*N+j,3*N+i,N+i)])
 fs.extend([(0,N,3*N,2*N),(steps,2*N+steps,3*N+steps,N+steps)])
 mesh('Blank curved non-instructional label',vs,fs,p['paper'],0,False)
 # Rear seam and unobtrusive carry-bracket hardware add useful back-view detail.
 box('Rear short retaining saddle',(0,.088,.404),(.045,.014,.042),p['dark'],.006)
 for x in [-.014,.014]:screw('Rear saddle fixing',(x,.099,.404),p['steel'],'Y',.003)
 return ('city-portable-fire-extinguisher','無銘の携帯消火器模型','Generic portable fire-extinguisher prop','建物内や工場の背景向けの無銘の消火器模型。丸い圧力容器風の本体、弁、目盛数字のない飾り圧力計、開口した取っ手、固定レバー、ピン、曲線ホース、中空ノズル、脚と無印ラベルを備えます。消火剤はなく、圧力表示・消火・安全機能はありません。消防・安全認証や性能保証はなく、操作手順も含みません。','An unbranded portable fire-extinguisher prop for building interiors and industrial scenes. Includes a rounded cylinder, valve, unnumbered decorative gauge, open carry handle, fixed lever, pin, curved hose, hollow nozzle, foot and blank label. There is no extinguishing agent, pressure indication, firefighting or safety function. No firefighting or safety certification, performance guarantee or operating instructions are supplied.',['fire-extinguisher','building','industrial','static-prop','消火器模型'])

BUILDERS=[hand_dryer,baby_station,eyewash_shower,extinguisher]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-008/assets');ap.add_argument('--only',default='');a=ap.parse_args(args)
 out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();spec=fn()
  if a.only and spec[0]!=a.only:continue
  publish_asset(*spec,out,GENERATOR,azimuth=-58,elevation=22)
  underside_render(out/'_qa'/f'{spec[0]}-underside.png')
