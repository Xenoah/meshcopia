"""Original stationary workshop processing machines. Xenoah, CC BY 4.0.
One complete assembly per asset. Static exterior props, not working equipment.
No third-party geometry, brands, fonts, logos, measurements or certifications.
"""
import math, sys, argparse, bpy, bmesh
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(paint=mat('Deep petrol workshop enamel',(.055,.20,.22),.18,.39),light=mat('Pale gray machine enamel',(.56,.60,.59),.12,.42),steel=mat('Satin machined steel',(.40,.46,.49),.78,.30),bright=mat('Polished guide steel',(.60,.66,.69),.84,.25),dark=mat('Charcoal cast machine metal',(.048,.061,.066),.32,.48),rubber=mat('Black rubber grips and tires',(.018,.024,.026),0,.73),abrasive=mat('Umber abrasive belt and disc',(.24,.12,.046),0,.91),filter=mat('Warm pale pleated filter',(.65,.61,.49),0,.89),red=mat('Unlit stop control',(.48,.046,.029),0,.45),green=mat('Unlit start control',(.048,.30,.15),0,.48))

def cyl(n,p,r,d,m,axis='Z',v=40,b=.002):
 o=cylinder(n,p,r,d,m,vertices=v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(n,a,b,r,m,v=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.0015,r*.14));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bar(n,a,b,w,t,m,bv=.004):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bv);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def ring(n,p,r,t,m,axis='Z',v=48):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)

def sleeve(n,p,ro,ri,h,m,axis='Z',v=48):
 vs=[]
 for r,z in [(ro,-h/2),(ro,h/2),(ri,h/2),(ri,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)]
 o=mesh(n,vs,fs,m);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o

def cone_shell(n,p,rlo,rhi,t,h,m,v=64):
 vs=[]
 for r,z in [(rlo,-h/2),(rhi,h/2),(rhi-t,h/2),(rlo-t,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)]
 o=mesh(n,vs,fs,m);o.location=p
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o

def handwheel(n,p,r,m,axis='Y',grip=True):
 p=Vector(p);ring(n+' open rim',p,r,.010 if r>.07 else .007,m,axis,40)
 if axis=='Y':u,v=Vector((1,0,0)),Vector((0,0,1));normal=Vector((0,-1,0))
 elif axis=='X':u,v=Vector((0,1,0)),Vector((0,0,1));normal=Vector((1,0,0))
 else:u,v=Vector((1,0,0)),Vector((0,1,0));normal=Vector((0,0,1))
 cyl(n+' axle hub',p,r*.23,.033,m,axis,v=28,b=.002)
 for i in range(3):
  a=i*math.tau/3+.30;rod(n+' spoke',p,p+(u*math.cos(a)+v*math.sin(a))*r,.007,m,20)
 if grip:
  q=p+u*r;rod(n+' crank pin',q,q+normal*.055,.008,m,20);rod(n+' fixed grip',q+normal*.025,q+normal*.080,.014,bpy.data.materials.get('Black rubber grips and tires'),24)

def hexbolt(n,p,m,axis='Z',r=.009,d=.008):return cyl(n,p,r,d,m,axis,v=6,b=.0007)

def foot(n,x,y,z,p):
 box(n+' plate',(x,y,z+.012),(.110,.095,.024),p['dark'],.005);cyl(n+' pad',(x,y,z-.003),.035,.018,p['rubber'],v=28,b=.002)

def lathe():
 p=palette()
 # Two substantial cabinets and a rear cross bridge form one lathe stand.
 for x in [-.495,.495]:
  box('Lathe cabinet plinth',(x,0,.075),(.330,.490,.110),p['dark'],.013)
  box('Lathe stand cabinet',(x,.010,.410),(.315,.455,.600),p['paint'],.014)
  box('Lathe inset cabinet door',(x,-.225,.405),(.271,.023,.505),p['light'],.007)
  box('Cabinet vertical recessed pull',(x+.088,-.243,.492),(.024,.015,.116),p['dark'],.004)
  for z in [.230,.580]:cyl('Cabinet door hinge',(x-.131,-.238,z),.009,.040,p['steel'],v=20,b=.001)
  for xx in [x-.109,x+.109]:
   for yy in [-.17,.17]:cyl('Lathe leveling pad',(xx,yy,.020),.032,.039,p['rubber'],v=28,b=.003)
 box('Lathe stand rear connecting rail',(0,.185,.620),(1.130,.065,.120),p['paint'],.006)
 box('Lathe chip tray bottom',(0,0,.748),(1.420,.560,.045),p['light'],.008)
 for y in [-.270,.270]:box('Chip tray raised long rim',(0,y,.783),(1.420,.027,.060),p['light'],.005)
 for x in [-.696,.696]:box('Chip tray raised end rim',(x,0,.783),(.028,.520,.060),p['light'],.005)
 box('Lathe bed cast base',(.020,.015,.858),(1.205,.285,.139),p['paint'],.011)
 for y in [-.091,.096]:box('Lathe continuous precision bed guide',(.032,y,.942),(1.178,.060,.037),p['bright'],.004)
 for x in [-.370,-.070,.230,.530]:box('Lathe bed lower web',(x,.014,.830),(.058,.277,.084),p['dark'],.006)
 box('Headstock lower mounting foot',(-.500,0,.969),(.300,.330,.060),p['dark'],.006)
 box('Lathe headstock enclosure',(-.514,.015,1.108),(.304,.329,.280),p['paint'],.022)
 box('Headstock front control panel',(-.516,-.156,1.119),(.250,.018,.169),p['light'],.007)
 for x in [-.590,-.504]:cyl('Fixed spindle selector knob',(x,-.177,1.150),.022,.028,p['dark'],'Y',v=28,b=.003)
 cyl('Lathe unlit stop control',(-.424,-.180,1.073),.023,.033,p['red'],'Y',v=28,b=.003)
 box('Headstock removable side cover',(-.673,.013,1.110),(.022,.260,.223),p['paint'],.011)
 for y in [-.100,.116]:
  for z in [1.025,1.197]:hexbolt('Headstock cover fastener',(-.687,y,z),p['steel'],'X')
 # The chuck is a real thick ring with a central opening and three stepped jaws.
 sleeve('Lathe spindle nose',(-.342,.015,1.119),.061,.026,.084,p['dark'],'X',48)
 sleeve('Three-jaw chuck main body',(-.281,.015,1.119),.103,.029,.091,p['steel'],'X',64)
 sleeve('Chuck face annulus',(-.231,.015,1.119),.098,.032,.014,p['bright'],'X',64)
 for i in range(3):
  a=i*math.tau/3+.25;y=.015+math.sin(a)*.073;z=1.119+math.cos(a)*.073
  box('Chuck radial jaw slide',(-.214,y,z),(.028,.030,.067),p['dark'],.002,rot=(-a,0,0))
  y2=.015+math.sin(a)*.052;z2=1.119+math.cos(a)*.052
  box('Chuck stepped gripping jaw',(-.193,y2,z2),(.035,.025,.034),p['bright'],.002,rot=(-a,0,0))
  q=Vector((-.277,.015+math.sin(a)*.101,1.119+math.cos(a)*.101));axis=Vector((0,math.sin(a),math.cos(a)));o=sleeve('Chuck key recess',q,.011,.005,.012,p['dark'],v=24);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 # Separate saddle, cross slide and tool post clearly sit on the two bed guides.
 box('Lathe carriage saddle',(.028,.003,.983),(.248,.316,.064),p['steel'],.005)
 box('Carriage front apron',(.028,-.187,.927),(.255,.083,.153),p['paint'],.009)
 box('Lathe cross slide',(.025,-.024,1.034),(.166,.265,.049),p['dark'],.004)
 box('Lathe compound slide',(.022,-.026,1.077),(.139,.158,.037),p['steel'],.004,rot=(0,0,-.15))
 cyl('Toolpost swivel plinth',(.011,-.004,1.106),.049,.029,p['dark'],v=40,b=.002)
 box('Lathe square toolpost',(.011,-.004,1.146),(.086,.086,.066),p['steel'],.004)
 box('Lathe fixed short cutting tool',(-.054,.005,1.137),(.117,.018,.018),p['dark'],.001)
 for x in [-.013,.034]:
  for y in [-.027,.020]:hexbolt('Toolpost clamping screw',(x,y,1.185),p['dark'],r=.008,d=.016)
 rod('Toolpost fixed locking lever',(.011,-.004,1.194),(.086,.025,1.194),.006,p['bright'],20)
 cyl('Cross-slide control shaft',(.029,-.203,1.032),.011,.115,p['steel'],'Y',v=24,b=.001)
 handwheel('Cross-slide handwheel',(.029,-.266,1.032),.044,p['bright'],'Y')
 cyl('Carriage wheel shaft',(-.031,-.258,.929),.013,.083,p['steel'],'Y',v=24,b=.001)
 handwheel('Carriage feed handwheel',(-.031,-.299,.929),.068,p['dark'],'Y')
 rod('Lathe fixed apron engagement lever',(.113,-.245,.909),(.151,-.264,.855),.007,p['steel'],20)
 sphere('Apron lever knob',(.151,-.264,.855),(.016,.016,.016),p['rubber'],20,10)
 rod('Lathe long exposed lead screw',(-.556,-.190,.852),(.598,-.190,.852),.012,p['steel'],28)
 pts=[]
 for i in range(841):
  a=i*math.tau/20;pts.append((-.543+1.125*i/840,-.190+.013*math.cos(a),.852+.013*math.sin(a)))
 tube('Visible exterior lead-screw helix',pts,.0021,p['bright'],1)
 for x in [-.571,.610]:box('Lead-screw end bearing',(x,-.189,.853),(.039,.064,.063),p['paint'],.005)
 box('Tailstock bed saddle',(.431,.010,.987),(.228,.270,.058),p['dark'],.006)
 box('Tailstock sloping-looking body',(.441,.019,1.062),(.173,.170,.128),p['paint'],.016)
 cyl('Tailstock quill housing',(.434,.017,1.118),.060,.219,p['paint'],'X',v=40,b=.005)
 cyl('Extended tailstock quill',(.292,.017,1.118),.025,.113,p['bright'],'X',v=32,b=.002)
 bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=.001,radius2=.025,depth=.046,location=(.217,.017,1.118),rotation=(0,math.pi/2,0));finish(bpy.context.object,'Tailstock center point',p['steel'])
 cyl('Tailstock handwheel shaft',(.573,.017,1.118),.012,.087,p['steel'],'X',v=24,b=.001)
 handwheel('Tailstock handwheel',(.621,.017,1.118),.063,p['dark'],'X')
 rod('Tailstock quill-lock lever',(.443,.017,1.176),(.480,-.023,1.232),.007,p['bright'],20)
 sphere('Tailstock lever grip',(.480,-.023,1.232),(.015,.015,.022),p['rubber'],20,10)
 return ('city-metalworking-lathe','キャビネット台付き小型金工旋盤','Cabinet-mounted metalworking lathe','公共工房・学校の金属加工室に据える小型旋盤。二連キャビネット台と切粉皿、主軸台、中心が実開口の三爪チャック、二本のベッド案内面、往復台・横送り台・角形刃物台、心押台とセンター、手輪と外装送りねじを造形。台を含む一式1点で、加工物は付属しません。回転・切削・送り・荷重などの機械動作や安全性能は実装・検証していません。','A compact lathe for floor placement in public workshops and school metalworking rooms. It includes twin stand cabinets and chip tray, headstock, genuinely open three-jaw chuck, two bed guides, carriage/cross slide/square toolpost, tailstock with center, handwheels and exterior lead screw. The stand and machine count as one assembly; no workpiece is supplied. Rotation, machining, feeds, loads and safety performance are neither implemented nor validated.',['workshop','lathe','metalworking','旋盤'])

def planer():
 p=palette()
 # Open four-leg stand, not a solid box underneath the planer.
 for x in [-.264,.264]:
  for y in [-.220,.220]:
   bar('Planer stand splayed leg',(x*1.14,y*1.12,.041),(x,y,.739),.046,.046,p['dark'],.004)
   box('Planer rubber stand foot',(x*1.14,y*1.12,.025),(.080,.073,.050),p['rubber'],.006)
 for y in [-.235,.235]:box('Planer low stand cross rail',(0,y,.250),(.570,.037,.051),p['paint'],.004)
 for x in [-.281,.281]:box('Planer low stand side rail',(x,0,.250),(.039,.482,.051),p['paint'],.004)
 box('Planer stand upper mounting deck',(0,0,.746),(.636,.534,.046),p['dark'],.006)
 for x in [-.246,.246]:
  for y in [-.191,.191]:hexbolt('Planer deck mounting bolt',(x,y,.777),p['steel'],r=.010)
 box('Planer bottom cast chassis',(0,0,.806),(.615,.452,.092),p['paint'],.013)
 box('Planer continuous central bed',(0,0,.864),(.474,.438,.030),p['bright'],.004)
 # Actual front-to-back stock passage is air beneath the cutter head.
 for x in [-.274,.274]:
  box('Planer side lower casting',(x,0,.926),(.072,.359,.209),p['paint'],.013)
  for y in [-.146,.146]:
   cyl('Planer polished height post',(x,y,1.069),.016,.356,p['bright'],v=28,b=.0015)
   cyl('Height post lower boot',(x,y,.934),.024,.084,p['dark'],v=28,b=.003)
 box('Planer distinct raised cutter housing',(0,0,1.188),(.578,.367,.200),p['paint'],.021)
 box('Planer head front service face',(0,-.194,1.189),(.493,.025,.132),p['light'],.008)
 box('Planer head upper cover',(0,0,1.296),(.560,.351,.027),p['light'],.007)
 for x in [-.215,.215]:
  for z in [1.151,1.230]:hexbolt('Cutter cover captive screw',(x,-.210,z),p['steel'],'Y',r=.007,d=.007)
 for y in [-.128,.128]:
  cyl('Planer exposed infeed and outfeed roller',(0,y,1.081),.027,.461,p['dark'],'X',v=40,b=.002)
  for x in [-.228,.228]:cyl('Planer roller end collar',(x,y,1.081),.032,.019,p['steel'],'X',v=28,b=.001)
 for s in [-1,1]:
  box('Planer extended stock support table',(0,s*.420,.863),(.468,.383,.026),p['steel'],.005)
  box('Planer extension outer folded lip',(0,s*.608,.848),(.462,.020,.050),p['steel'],.003)
  cyl('Planer table hinge',(0,s*.230,.849),.014,.470,p['dark'],'X',v=24,b=.0015)
  for x in [-.171,.171]:bar('Planer extension underside bracket',(x,s*.182,.794),(x,s*.522,.849),.024,.025,p['dark'],.002)
  for x in [-.214,.214]:hexbolt('Planer extension corner fastener',(x,s*.556,.880),p['dark'],r=.006,d=.006)
 cyl('Planer height-adjustment spindle',(.273,.146,1.327),.014,.121,p['bright'],v=28,b=.002)
 handwheel('Planer height handwheel',(.273,.146,1.387),.078,p['dark'],'Z')
 box('Planer fixed depth index backing',(.318,-.006,1.051),(.013,.062,.255),p['light'],.002)
 for z in [0.955,0.980,1.005,1.030,1.055,1.080,1.105,1.130,1.155]:box('Unnumbered depth scale notch',(.327,-.010,z),(.005,.030,.003),p['dark'],.0006)
 box('Planer depth fixed pointer',(.329,-.016,1.138),(.011,.048,.010),p['red'],.001)
 cyl('Planer front unlit stop switch',(-.169,-.218,1.190),.022,.025,p['red'],'Y',v=28,b=.003)
 cyl('Planer front unlit start switch',(-.104,-.218,1.190),.015,.024,p['green'],'Y',v=24,b=.002)
 # Chip hood bridges into a visibly open round rear connection.
 box('Planer rear chip collection hood',(0,.225,1.222),(.403,.153,.124),p['dark'],.014)
 sleeve('Open planer chip-extraction connection',(0,.354,1.225),.062,.051,.154,p['dark'],'Y',v=48)
 ring('Planer duct retaining lip',(0,.433,1.225),.057,.006,p['steel'],'Y',48)
 for x in [-.161,.161]:hexbolt('Chip hood fastening screw',(x,.306,1.224),p['steel'],'Y',r=.007,d=.008)
 return ('city-thickness-planer','延長テーブルと架台付き自動かんな盤','Stand-mounted thickness planer','木工教室・共同工房の床に置く厚み仕上げ用の自動かんな盤。四脚架台、前後に実際に通り抜ける材料通路、主テーブルと延長テーブル、独立した刃胴カバー、送りローラー外装、四本の高さ支柱、上部手輪と後方の開口集塵口を造形。架台を含む一式1点で、木材や集塵ホースは含みません。切削・送り・高さ調整・排塵の動作や加工精度は実装・検証していません。','A thickness-finishing planer for floor placement in woodworking classrooms and shared workshops. It has a four-leg stand, truly open front-to-back stock passage, main bed and extension tables, distinct cutter-head cover, feed-roller exteriors, four height posts, top handwheel and open rear chip-extraction connection. Stand and machine are one assembly; lumber and extraction hose are absent. Cutting, feed, height adjustment, chip removal and machining accuracy are neither implemented nor validated.',['workshop','woodworking','planer','かんな盤'])

def belt_loop(n,x,y,zlo,zhi,r,w,t,m,steps=28):
 # Four corresponding contours make a closed thick endless belt, open at each side.
 contours=[]
 for rr,xx in [(r,x-w/2),(r,x+w/2),(r-t,x+w/2),(r-t,x-w/2)]:
  pts=[]
  for i in range(steps+1):
   a=i*math.pi/steps;pts.append((xx,y+rr*math.cos(a),zhi+rr*math.sin(a)))
  for i in range(steps+1):
   a=math.pi+i*math.pi/steps;pts.append((xx,y+rr*math.cos(a),zlo+rr*math.sin(a)))
  contours.append(pts)
 v=sum(contours,[]);k=len(contours[0]);f=[(j*k+i,j*k+(i+1)%k,((j+1)%4)*k+(i+1)%k,((j+1)%4)*k+i) for j in range(4) for i in range(k)]
 return mesh(n,v,f,m)

def sander():
 p=palette()
 box('Sander cabinet plinth',(0,.030,.076),(.635,.495,.112),p['dark'],.014)
 for x in [-.237,.237]:
  for y in [-.144,.204]:cyl('Sander leveling pad',(x,y,.020),.035,.039,p['rubber'],v=28,b=.003)
 box('Single combination-sander cabinet',(0,.030,.430),(.582,.451,.616),p['paint'],.016)
 box('Sander cabinet front door',(0,-.202,.427),(.504,.022,.520),p['light'],.008)
 box('Sander door recessed pull',(.185,-.221,.546),(.024,.018,.128),p['dark'],.004)
 for z in [.248,.606]:cyl('Sander door hinge',(-.244,-.215,z),.010,.048,p['steel'],v=20,b=.001)
 for x in [-.171,-.128,-.085,-.042,.001,.044,.087,.130,.173]:box('Sander lower cabinet vent',(x,-.217,.252),(.015,.010,.075),p['dark'],.0015)
 box('Sander mounting top plate',(0,.030,.756),(.663,.533,.050),p['steel'],.006)
 box('Combined machine cast base',(0,.032,.826),(.573,.389,.105),p['paint'],.014)
 box('Central shared drive housing',(.010,.067,.956),(.470,.245,.175),p['paint'],.022)
 cyl('Rear drive motor exterior',(.048,.211,.952),.094,.196,p['dark'],'Y',v=48,b=.005)
 for y in [.165,.196,.227,.258,.289]:ring('Motor housing cooling rib',(.048,y,.952),.094,.005,p['steel'],'Y',40)
 cyl('Motor rear cap',(.048,.316,.952),.089,.030,p['dark'],'Y',v=40,b=.004)
 for x in [-.242,.242]:
  for y in [-.116,.174]:hexbolt('Sander base anchor bolt',(x,y,.890),p['steel'],r=.010,d=.009)
 # Wide endless belt travels vertically around two real cylindrical rollers.
 x=-.220;y=.010;lo=1.040;hi=1.447;r=.073
 belt_loop('Continuous thick abrasive belt',x,y,lo,hi,r,.166,.006,p['abrasive'])
 for z in [lo,hi]:
  cyl('Belt sanding roller',(x,y,z),.0675,.178,p['dark'],'X',v=48,b=.002)
  cyl('Belt roller visible end hub',(x-.101,y,z),.025,.026,p['steel'],'X',v=28,b=.002)
  hexbolt('Roller fixed axle fastener',(x-.115,y,z),p['dark'],'X',r=.010,d=.009)
 box('Belt back structural spine',(x,.069,1.243),(.088,.043,.455),p['paint'],.007)
 box('Belt working-platen backing',(x,-.041,1.241),(.154,.025,.338),p['steel'],.003)
 bar('Belt assembly lower mount',(x,.064,.891),(x,.064,1.103),.111,.101,p['paint'],.006)
 for z in [1.075,1.424]:box('Belt right roller-bearing block',(x+.107,.015,z),(.045,.105,.087),p['paint'],.008)
 box('Belt rear safety cover',(x,.104,1.248),(.201,.041,.395),p['paint'],.009)
 cyl('Belt tracking adjustment knob',(x+.145,.021,1.449),.023,.036,p['rubber'],'X',v=28,b=.003)
 box('Belt work-rest mounting cross bracket',(x,-.013,.975),(.235,.084,.040),p['paint'],.004)
 box('Belt flat-stock work rest',(x,-.164,1.100),(.235,.194,.022),p['steel'],.004)
 for xx in [x-.071,x+.071]:bar('Belt rest underside support',(xx,-.141,1.083),(xx,-.016,.961),.023,.024,p['dark'],.002)
 cyl('Belt rest tilt-lock knob',(x+.139,-.112,1.051),.021,.029,p['dark'],'X',v=28,b=.002)
 # Separate disc station on the same drive and stand, not two grinding wheels.
 cx=.195;cz=1.118
 cyl('Disc rear circular guard',(cx,.036,cz),.203,.078,p['paint'],'Y',v=64,b=.006)
 sleeve('Disc raised guard rim',(cx,-.008,cz),.205,.190,.026,p['dark'],'Y',v=64)
 cyl('Sanding disc rigid backing',(cx,-.036,cz),.183,.025,p['steel'],'Y',v=64,b=.003)
 cyl('Flat abrasive sanding disc face',(cx,-.051,cz),.178,.008,p['abrasive'],'Y',v=64,b=.001)
 cyl('Disc center fixed arbor cap',(cx,-.058,cz),.018,.012,p['dark'],'Y',v=28,b=.001)
 box('Disc work table',(cx,-.209,1.009),(.410,.287,.027),p['steel'],.004)
 box('Disc table fixed miter guide groove',(cx,-.232,1.024),(.365,.008,.0025),p['dark'],.0004)
 for xx in [cx-.145,cx+.145]:bar('Disc table connected support',(xx,-.173,.989),(xx,.032,.900),.028,.028,p['dark'],.003)
 cyl('Disc table fixed tilt pivot',(.402,-.111,.960),.026,.037,p['steel'],'X',v=28,b=.002)
 cyl('Disc work-table lock knob',(.427,-.111,.960),.023,.030,p['dark'],'X',v=28,b=.003)
 box('Disc lower extraction hood joining guard and outlet',(.327,.088,.932),(.160,.132,.115),p['dark'],.009)
 sleeve('Open disc dust outlet',(.362,.173,.923),.040,.032,.125,p['dark'],'Y',v=40)
 ring('Disc dust outlet collar',(.362,.237,.923),.036,.004,p['steel'],'Y',40)
 sleeve('Open belt dust outlet',(-.220,.187,.918),.035,.027,.117,p['dark'],'Y',v=40)
 box('Sander front switch box',(-.054,-.189,.841),(.126,.040,.072),p['dark'],.006)
 cyl('Sander stop control',(-.085,-.216,.844),.018,.022,p['red'],'Y',v=24,b=.002)
 cyl('Sander start control',(-.027,-.216,.844),.013,.021,p['green'],'Y',v=24,b=.002)
 return ('city-belt-disc-sander','架台付きベルト・ディスクサンダー','Combined belt and disc sander','木工・模型工房で平材の面や端部を研磨する一体型据置機。共通のキャビネット台・駆動部に、上下ローラーを巡る厚みのある連続ベルト、支持プレート、円形の平面研磨ディスク、別々の材料受け、ガード、調整つまみと二つの開口集塵口を組み合わせています。刃物研ぎ用の両頭グラインダーではなく、一式を1点として数えます。材料は付属せず、回転・研磨・集塵・安全性能は実装・検証していません。','One stationary assembly for finishing flat-stock surfaces and edges in woodworking and model-making workshops. A shared cabinet and drive carry a thick continuous belt around upper/lower rollers, backing platen, flat abrasive disc, separate work rests, guards, fixed adjustment knobs and two open dust outlets. It is a stock-finishing belt/disc machine, not a double-wheel sharpening grinder, and counts as one assembly. Stock is absent; rotation, sanding, extraction and safety performance are neither implemented nor validated.',['workshop','woodworking','sander','研磨機'])

def caster(n,x,y,p):
 cyl(n+' rubber wheel',(x,y,.055),.055,.038,p['rubber'],'X',v=32,b=.005)
 for xx in [x-.024,x+.024]:
  cyl(n+' metal wheel hub',(xx,y,.055),.022,.012,p['steel'],'X',v=24,b=.0015)
  box(n+' connected fork',(xx,y,.092),(.010,.048,.072),p['steel'],.003)
 box(n+' fork bridge',(x,y,.128),(.067,.051,.014),p['steel'],.003)
 cyl(n+' swivel',(x,y,.142),.027,.028,p['dark'],v=28,b=.002)

def dust_extractor():
 p=palette()
 # Wheeled rectangular support carries a cyclone/bin on the left and filter on the right.
 for x in [-.473,.473]:
  for y in [-.245,.245]:caster('Dust extractor caster',x,y,p)
 for y in [-.254,.254]:box('Extractor base long rail',(0,y,.167),(1.053,.046,.052),p['dark'],.005)
 for x in [-.500,.500]:box('Extractor base end rail',(x,0,.167),(.046,.519,.052),p['dark'],.005)
 box('Extractor bin bottom platform',(-.228,0,.193),(.462,.466,.032),p['steel'],.005)
 for x in [-.501,.501]:
  for y in [-.230,.230]:box('Extractor vertical support post',(x,y,.857),(.040,.040,1.386),p['paint'],.005)
 box('Extractor upper rear cross member',(0,.230,1.527),(1.035,.047,.055),p['paint'],.005)
 box('Extractor filter lower shelf',(.266,0,.528),(.435,.445,.039),p['dark'],.005)
 for x in [.087,.470]:bar('Filter shelf diagonal support',(x,.220,.326),(x,-.198,.519),.026,.027,p['paint'],.003)
 cx=-.229
 cyl('Dust collection bin body',(cx,0,.432),.196,.446,p['light'],v=64,b=.008)
 cyl('Collection bin rolled lower rim',(cx,0,.219),.202,.021,p['dark'],v=64,b=.003)
 cyl('Collection bin removable lid',(cx,0,.661),.211,.036,p['dark'],v=64,b=.004)
 for side in [-1,1]:
  # Side handles and latches intersect their mounting pads, not floating details.
  x=cx+side*.191
  box('Collection bin handle mounting pad',(x,0,.476),(.025,.097,.071),p['steel'],.004)
  rod('Collection bin handle lower pin',(x, -.034,.471),(x+side*.039,-.034,.471),.007,p['dark'],20)
  rod('Collection bin handle upper pin',(x, .034,.471),(x+side*.039,.034,.471),.007,p['dark'],20)
  rod('Collection bin side grip',(x+side*.039,-.034,.471),(x+side*.039,.034,.471),.010,p['dark'],24)
 for a in [-math.pi/2,.5,math.pi-.5]:
  x=cx+.198*math.cos(a);y=.198*math.sin(a)
  o=box('Collection lid toggle latch',(x,y,.637),(.026,.019,.066),p['steel'],.003);o.rotation_euler[2]=a+math.pi/2
 sleeve('Cyclone discharge neck',(cx,0,.724),.075,.064,.107,p['dark'],v=48)
 ring('Discharge neck lower clamp',(cx,0,.687),.076,.005,p['steel'],v=48)
 cone_shell('Hollow cyclone taper',(cx,0,.917),.075,.210,.008,.312,p['paint'],64)
 body=sleeve('Hollow cylindrical cyclone chamber',(cx,0,1.256),.210,.202,.366,p['paint'],v=64)
 # A genuine opening through the front shell joins the open duct sleeve.
 cut=cyl('Temporary cyclone inlet wall cutter',(cx,-.204,1.284),.066,.190,p['dark'],'Y',v=48,b=0)
 mod=body.modifiers.new('True inlet through cyclone shell','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.dissolve_degenerate(bm,dist=0.000002,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
 for f in body.data.polygons:f.use_smooth=False
 sleeve('Open workshop dust inlet',(cx,-.301,1.284),.077,.066,.243,p['dark'],'Y',v=48)
 ring('Dust inlet cuff retaining lip',(cx,-.424,1.284),.073,.006,p['steel'],'Y',48)
 ring('Cyclone chamber lower rolled seam',(cx,0,1.079),.209,.006,p['steel'],v=64)
 cyl('Cyclone upper blower housing',(cx,0,1.480),.224,.123,p['paint'],v=64,b=.010)
 cyl('Blower top service lid',(cx,0,1.551),.211,.027,p['light'],v=64,b=.003)
 for i in range(8):
  a=i*math.tau/8;hexbolt('Blower cover perimeter bolt',(cx+.184*math.cos(a),.184*math.sin(a),1.571),p['steel'],r=.009,d=.009)
 cyl('Extractor motor mounting flange',(cx,0,1.574),.119,.033,p['steel'],v=48,b=.003)
 for i in range(4):
  a=i*math.tau/4+.45;hexbolt('Motor flange anchor screw',(cx+.104*math.cos(a),.104*math.sin(a),1.595),p['dark'],r=.007,d=.012)
 cyl('Extractor vertical fan motor',(cx,0,1.690),.099,.235,p['dark'],v=48,b=.006)
 for z in [1.599,1.625,1.651,1.677,1.703,1.729,1.755]:ring('Extractor motor cooling rib',(cx,0,z),.101,.004,p['steel'],v=40)
 cyl('Extractor motor top end cap',(cx,0,1.816),.105,.026,p['dark'],v=48,b=.004)
 box('Motor side electrical enclosure',(cx+.100,.010,1.687),(.077,.088,.113),p['dark'],.007)
 tube('Connected motor-to-control cable',[(cx+.134,.020,1.676),(-.049,.070,1.610),(.045,.266,1.531),(.501,.266,1.531),(.529,.230,1.310),(.529,-.220,1.269),(.501,-.238,1.269)],.007,p['rubber'],1)
 for x in [.140,.390]:
  box('Cable rear-rail clamp mounting tab',(x,.255,1.531),(.025,.024,.028),p['steel'],.002)
  ring('Cable retaining clamp',(x,.266,1.531),.009,.002,p['steel'],'X',24)
 # The broad outlet bridge visibly connects fan housing and the filter top.
 box('Blower-to-filter enclosed outlet bridge',(.052,.015,1.477),(.453,.164,.113),p['paint'],.009)
 fx=.270
 cyl('Filter upper manifold cap',(fx,0,1.438),.195,.072,p['light'],v=64,b=.006)
 # 48 deep exterior pleats are real closed corrugated geometry, no texture.
 n=96;verts=[]
 for z in [.625,1.405]:
  for i in range(n):
   a=i*math.tau/n;r=.180 if i%2==0 else .160;verts.append((fx+r*math.cos(a),r*math.sin(a),z))
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh('Pleated cartridge filter exterior',verts,faces,p['filter'])
 for z in [.638,1.390]:sleeve('Filter cartridge retaining band',(fx,0,z),.186,.178,.031,p['steel'],v=64)
 cyl('Filter lower collection bowl',(fx,0,.588),.187,.085,p['paint'],v=64,b=.008)
 cyl('Filter lower drain cap',(fx,0,.539),.045,.022,p['dark'],v=32,b=.003)
 for a in [0,math.pi]:
  x=fx+.188*math.cos(a);y=.188*math.sin(a);box('Filter lower bowl latch',(x,y,.600),(.018,.040,.065),p['steel'],.003)
 # Head brackets tie both tall assemblies into the frame.
 for x,y in [(-.501,.230),(-.501,-.230),(.501,.230),(.501,-.230)]:
  targetx=cx if x<0 else fx
  bar('Extractor upper assembly support',(x,y,1.481),(targetx,y*.45,1.481),.044,.035,p['dark'],.003)
 box('Extractor front control enclosure',(.501,-.243,1.269),(.095,.054,.153),p['light'],.007)
 cyl('Extractor unlit stop control',(.501,-.283,1.298),.022,.027,p['red'],'Y',v=28,b=.003)
 cyl('Extractor unlit start control',(.501,-.283,1.238),.014,.025,p['green'],'Y',v=24,b=.002)
 return ('city-cyclone-dust-extractor','車輪付きサイクロン式工房集塵機','Wheeled cyclone workshop dust extractor','木工室・共同工房に据えるサイクロン式集塵機の外観模型。車輪付き支持枠、上部ファン・縦置きモーター、内部を空洞にした円筒と円錐の分離器、実開口の吸込接続口、蓋・取手・留具付き回収容器、接続ダクトと深いひだのフィルター外形を造形。回収容器やフィルターを含む一式1点で、作業機や延長ホースは含みません。送風・分離・ろ過・粉塵対策・荷重や安全性能は実装・検証していません。','A cyclone-extractor appearance prop for woodworking rooms and shared workshops. It includes a wheeled support frame, upper fan and vertical motor, hollow cylindrical/conical separator, genuinely open inlet connection, lidded collection bin with handles/latches, connecting outlet duct and deeply pleated filter exterior. Bin and filter are part of one complete assembly; processing machines and extension hoses are absent. Airflow, separation, filtration, dust protection, loads and safety performance are neither implemented nor validated.',['workshop','dust-extraction','cyclone','集塵機'])

BUILDERS=[lathe,planer,sander,dust_extractor]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-046/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/workshop_processing_machines.py',azimuth=-55,elevation=25)
