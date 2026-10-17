"""Original static workshop machines for Xenoah / Meshcopia, CC BY 4.0.
Portable Blender 4.3.2 recipe; no third-party meshes, images, fonts or brands.
Not electrical, mechanical, pressure or load validated; no operating instructions.
"""
import argparse,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import *

def palette():
 return dict(teal=mat('Petrol workshop enamel',(.035,.225,.238),.3,.38),ochre=mat('Ochre grinder enamel',(.54,.295,.055),.3,.38),red=mat('Oxide red enamel',(.43,.055,.033),.3,.42),dark=mat('Graphite painted frame',(.035,.047,.053),.3,.48),iron=mat('Grey cast iron',(.15,.17,.18),.65,.55),steel=mat('Satin steel',(.48,.54,.56),.85,.29),bright=mat('Polished quill',(.66,.71,.73),.92,.22),rubber=mat('Black cable and rubber',(.016,.020,.024),0,.79),stone=mat('Coarse abrasive stone',(.24,.26,.25),0,.9),fine=mat('Fine abrasive stone',(.47,.46,.43),0,.9),face=mat('Unlit opaque display',(.055,.105,.112),.1,.35),green=mat('Sage cylinder enamel',(.215,.30,.235),.4,.43),brass=mat('Dull connector brass',(.48,.31,.095),.77,.37))

def cyl(name,loc,r,depth,material,axis='Z',verts=40,bevel=.002):
 verts=min(verts,16 if r<.008 else 24 if r<.035 else 48);o=cylinder(name,loc,r,depth,material,verts,bevel=bevel)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for m in o.modifiers:
  if m.type=='BEVEL':m.segments=1
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(name,a,b,r,material,verts=20):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,material,verts=verts,bevel=min(.001,r*.14));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def beam(name,a,b,w,d,material,bevel=.003):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,d,(b-a).length),material,bevel);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def ball(name,loc,r,material):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=r,location=loc);return finish(bpy.context.object,name,material,0,True)

def fastener(name,loc,material,axis='Z',r=.007,sign=1):
 cyl(name+' washer',loc,r*1.48,r*.32,material,axis,16,0);pt=list(loc);pt['XYZ'.index(axis)]+=sign*r*.45;cyl(name+' hex head',pt,r,r*.85,material,axis,6,.0005)

def profile(name,center,depth,points,material,axis='Y',bevel=.002):
 n=len(points)
 vs=[(x,c,z) if axis=='Y' else (c,x,z) for c in [center-depth/2,center+depth/2] for x,z in points]
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,vs,fs,material,bevel)
 if 'wheel housing' in name or 'wheel cover' in name:
  for f in list(o.data.polygons)[2:]:f.use_smooth=True
 return o

def cut(o,cutter):
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 m=o.modifiers.new('Genuine opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 for f in o.data.polygons:f.use_smooth=False
 o.data.update();return o

def outline(cx,cz,w,h,r):
 pts=[]
 for x,z,a in [(cx+w/2-r,cz+h/2-r,0),(cx-w/2+r,cz+h/2-r,90),(cx-w/2+r,cz-h/2+r,180),(cx+w/2-r,cz-h/2+r,270)]:
  for i in range(9):
   th=math.radians(a+90*i/8);pts.append((x+r*math.cos(th),z+r*math.sin(th)))
 return pts

def annular_x(name,x,y,z,r0,r1,depth,start,end,material,steps=48):
 vs=[]
 for xx in [x-depth/2,x+depth/2]:
  for r in [r0,r1]:
   for i in range(steps+1):
    a=math.radians(start+(end-start)*i/steps);vs.append((xx,y+r*math.cos(a),z+r*math.sin(a)))
 n=steps+1;fs=[]
 for i in range(steps):fs += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
 fs += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
 o=mesh(name,vs,fs,material,0)
 for i,f in enumerate(o.data.polygons):
  if i<steps*4 and i%4>=2:f.use_smooth=True
 return o

def cable(name,points,r,material):
 p=[Vector(v) for v in points];q=[p[0],*p,p[-1]];out=[]
 for j in range(1,len(q)-2):
  a,b,c,d=q[j-1:j+3]
  for k in range(8):
   t=k/8;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 out.append(p[-1]);return tube(name,out,r,material,2)

def drill_press():
 p=palette();base=box('Cast floor mounting base',(0,.045,.055),(.49,.68,.110),p['iron'],.028)
 for x in [-.174,.174]:
  for y in [-.192,.272]:cut(base,cyl('Mounting aperture cutter',(x,y,.055),.017,.19,None,verts=24,bevel=0))
 box('Base central rib',(0,.16,.123),(.23,.34,.055),p['teal'],.012);cyl('Column flange',(0,.225,.15),.107,.058,p['teal'],verts=48,bevel=.006)
 for x in [-.069,.069]:fastener('Flange bolt',(x,.225,.185),p['steel'],r=.010)
 cyl('Polished upright column',(0,.225,.804),.049,1.29,p['steel'],verts=48)
 cyl('Head collar',(0,.225,1.39),.069,.15,p['teal'],verts=48,bevel=.004)
 cyl('Sliding table collar',(0,.225,.777),.075,.13,p['teal'],verts=48,bevel=.005)
 beam('Table bracket arm',(0,.225,.795),(0,-.121,.795),.095,.083,p['teal'],.008)
 profile('Table bracket brace',0,.055,[(.217,.72),(.217,.80),(-.178,.80)],p['teal'],'X',.004)
 cyl('Table tilt trunnion',(0,-.121,.797),.052,.14,p['iron'],'X',40,.004);fastener('Table tilt lock',(.079,-.121,.797),p['steel'],'X',.017)
 table=box('Slotted cast working table',(0,-.168,.854),(.414,.405,.033),p['iron'],.012)
 cut(table,cyl('Central table clearance cutter',(0,-.168,.854),.025,.12,None,verts=32,bevel=0))
 for x in [-.117,.117]:cut(table,box('Long table slot cutter',(x,-.168,.854),(.018,.266,.11),None,0))
 for y in [-.297,-.039]:cut(table,box('Cross table slot cutter',(0,y,.854),(.142,.018,.11),None,0))
 cyl('Table clamp boss',(.08,.226,.78),.021,.046,p['steel'],'X',24);rod('Table clamp lever',(.092,.226,.78),(.184,.226,.751),.008,p['dark']);ball('Table clamp grip',(.189,.226,.75),.017,p['rubber'])
 cyl('Table crank spindle',(-.087,.226,.78),.016,.061,p['steel'],'X',24);rod('Table crank arm',(-.122,.226,.78),(-.122,.226,.696),.009,p['iron']);cyl('Crank grip',(-.155,.226,.696),.016,.07,p['rubber'],'X',24,.004)
 box('Long cast head',(0,.024,1.444),(.222,.51,.19),p['teal'],.042);box('Closed belt cover',(0,.045,1.581),(.273,.625,.107),p['dark'],.035);box('Belt cover seam',(0,.045,1.536),(.274,.626,.017),p['iron'],.007)
 cyl('Rear motor barrel',(0,.337,1.421),.083,.242,p['dark'],verts=48,bevel=.012)
 for z in [1.303,1.543]:cyl('Rear motor cap',(0,.337,z),.086,.028,p['iron'],verts=48,bevel=.005)
 for x in [-.070,.070]:box('Motor attachment saddle',(x,.279,1.414),(.025,.11,.115),p['teal'],.003)
 for a in range(0,360,45):
  th=math.radians(a);box('Motor cooling fin',(.084*math.cos(th),.337+.084*math.sin(th),1.422),(.010,.010,.175),p['iron'],.001)
 cyl('Spindle housing',(0,-.168,1.365),.062,.150,p['teal'],verts=48,bevel=.005);cyl('Stationary polished quill',(0,-.168,1.275),.031,.13,p['bright'],verts=40)
 cyl('Chuck upper sleeve',(0,-.168,1.215),.040,.047,p['iron'],verts=40,bevel=.003);cyl('Chuck body',(0,-.168,1.175),.041,.044,p['steel'],verts=32,bevel=.005);cyl('Empty chuck nose',(0,-.168,1.142),.024,.033,p['iron'],verts=32,bevel=.004)
 for i in range(16):
  a=math.tau*i/16;rod('Chuck grip ridge',(.040*math.cos(a),-.168+.040*math.sin(a),1.163),(.040*math.cos(a),-.168+.040*math.sin(a),1.189),.0017,p['iron'],12)
 cyl('Feed shaft side boss',(.128,-.112,1.443),.037,.058,p['iron'],'X',32,.003);cyl('Feed handle hub',(.168,-.112,1.443),.030,.048,p['steel'],'X',32,.003)
 for deg in [15,135,255]:
  a=math.radians(deg);end=(.18,-.112+.168*math.cos(a),1.443+.168*math.sin(a));rod('Feed lever spoke',(.18,-.112,1.443),end,.007,p['steel']);ball('Feed lever grip',end,.022,p['rubber'])
 box('Operator switch bezel',(0,-.243,1.449),(.094,.026,.095),p['dark'],.006);box('Stop paddle',(0,-.261,1.434),(.060,.014,.043),p['red'],.004);box('Power key',(0,-.261,1.476),(.026,.014,.020),p['rubber'],.002)
 for x in [-.084,.084]:fastener('Head screw',(x,-.229,1.502),p['steel'],'Y',.005,-1)
 cable('Parked electrical lead',[(.055,.342,1.315),(.10,.42,1.20),(.11,.43,.92),(.12,.43,.67),(.10,.40,.61),(.075,.37,.70)],.006,p['rubber']);box('Unused cable end',(.075,.37,.714),(.024,.022,.040),p['rubber'],.004)
 return ('city-floor-drill-press','床置きボール盤','Floor-standing drill press','街の整備工房やメーカースペースに置く床置きボール盤。取付穴付き鋳物ベース、丸支柱、調整用カラーとクランク、実際に抜けたスロットと中心穴を持つ作業台、ベルトカバー、後部モーター外装、クイルと空のチャック、三本の送りハンドル、正面スイッチを備えます。ドリル刃、材料、加工動作は含みません。電気・機械・荷重支持・安全性は未検証の静的な外観モデルで、操作・製作の指示は付属しません。','A floor-standing drill press for municipal maintenance workshops and makerspaces, with an apertured cast base, round column, adjustable-table collar and crank, genuine table slots and central clearance hole, closed belt cover, rear motor exterior, quill and empty chuck, three-spoke feed handle and front switches. No drill bit, stock or cutting action is included. Static appearance geometry with no electrical, mechanical, load-bearing or safety validation and no operation or fabrication instructions.',['workshop','drill-press','maintenance','makerspace','ボール盤'])

def band_saw():
 p=palette()
 for x in [-.234,.234]:
  for y in [-.182,.182]:cyl('Stationary rubber foot',(x,y,.029),.033,.058,p['rubber'],verts=24,bevel=.004)
 box('Cabinet base flange',(0,0,.074),(.59,.47,.045),p['dark'],.008);box('Stand cabinet',(0,.014,.226),(.52,.41,.292),p['teal'],.016);box('Stand front access door',(0,-.197,.231),(.424,.015,.217),p['dark'],.006)
 for x in [-.181,.181]:
  for z in [.148,.31]:fastener('Stand access screw',(x,-.210,z),p['steel'],'Y',.005,-1)
 profile('Lower closed wheel housing',.015,.288,outline(-.025,.576,.59,.553,.155),p['teal'],bevel=.006)
 profile('Upper closed wheel housing',.015,.288,outline(-.025,1.371,.59,.565,.196),p['teal'],bevel=.006)
 profile('Connecting left backbone',.048,.274,[(-.337,.56),(-.196,.56),(-.196,1.41),(-.337,1.41)],p['teal'],bevel=.007)
 for name,cz,w,h,r in [('Lower wheel cover',.576,.548,.512,.135),('Upper wheel cover',1.371,.548,.524,.177)]:
  profile(name,-.139,.018,outline(-.025,cz,w,h,r),p['dark'],bevel=.004);profile(name+' inset',-.151,.008,outline(-.025,cz,w-.024,h-.024,r-.012),p['teal'])
  cyl(name+' latch',(.17,-.165,cz),.019,.012,p['iron'],'Y',24);box(name+' latch slot',(.17,-.173,cz),(.017,.003,.004),p['steel'],.0005)
  for z in [cz-.15,cz+.15]:box(name+' hinge',(-.275,-.154,z),(.023,.035,.070),p['steel'],.003)
 table=box('Slotted cast saw table',(.095,-.058,.898),(.704,.60,.037),p['iron'],.008)
 cut(table,cyl('Blade clearance cutter',(.229,-.035,.898),.020,.13,None,verts=32,bevel=0));cut(table,box('Blade insertion slit cutter',(.229,-.207,.898),(.010,.358,.13),None,0))
 cyl('Table tilt bearing',(-.057,.030,.854),.056,.26,p['dark'],'X',40,.004)
 for x in [-.205,.052]:beam('Table support',(x,.032,.77),(x,.032,.885),.067,.12,p['teal'],.004)
 fastener('Table tilt lock',(.083,.03,.854),p['steel'],'X',.016)
 box('Front fence rail',(.095,-.369,.878),(.70,.027,.036),p['steel'],.004);box('Short straight fence',(-.142,-.062,.949),(.027,.56,.065),p['steel'],.004);box('Fence locking block',(-.142,-.370,.905),(.064,.055,.066),p['dark'],.005);cyl('Fence lock grip',(-.142,-.413,.90),.019,.058,p['rubber'],'Y',24,.003)
 box('Stationary visible blade',(.229,-.035,1.007),(.013,.0024,.203),p['steel'],0);box('Upper blade guard',(.229,-.011,1.115),(.042,.034,.101),p['dark'],.003)
 cyl('Guide adjustment post',(.229,.028,1.17),.014,.25,p['steel'],verts=24);box('Upper blade guide',(.229,-.016,1.067),(.065,.060,.027),p['iron'],.003)
 for x in [.209,.249]:cyl('Blade guide roller',(x,-.042,1.054),.011,.017,p['steel'],'Y',20,.001)
 cyl('Guide locking hub',(.278,.031,1.193),.018,.032,p['iron'],'X',24);rod('Guide locking lever',(.296,.031,1.193),(.348,.031,1.228),.006,p['steel']);ball('Guide lock grip',(.350,.031,1.230),.014,p['rubber'])
 cyl('Top tension spindle',(-.025,.025,1.675),.013,.070,p['steel'],verts=24);cyl('Top tension wheel',(-.025,.025,1.707),.057,.023,p['dark'],verts=40,bevel=.004);cyl('Tension wheel center',(-.025,.025,1.722),.014,.008,p['steel'],verts=24)
 box('Operator switch box',(-.266,-.166,1.013),(.080,.046,.111),p['dark'],.006);box('Stop paddle',(-.266,-.193,.998),(.057,.016,.050),p['red'],.004);box('Start switch',(-.266,-.193,1.041),(.026,.016,.021),p['rubber'],.002)
 cyl('Rear drive motor',(-.075,.237,.582),.102,.19,p['iron'],'Y',48,.008);cyl('Rear motor cap',(-.075,.341,.582),.097,.028,p['dark'],'Y',48,.006)
 for x in [-.139,-.011]:box('Motor attachment bracket',(x,.176,.50),(.038,.17,.041),p['dark'],.003)
 for i in range(5):box('Motor cap cooling rib',(-.075,.359,.526+i*.028),(.121,.008,.007),p['iron'],.001)
 cyl('Dust port flange',(.146,.170,.400),.057,.035,p['dark'],'Y',40,.003);outlet=cyl('Hollow dust outlet',(.146,.225,.400),.045,.102,p['iron'],'Y',40,.001);cut(outlet,cyl('Dust bore cutter',(.146,.225,.400),.035,.14,None,'Y',40,0))
 cable('Parked saw power lead',[(-.16,.25,.57),(-.24,.32,.53),(-.28,.33,.28),(-.26,.33,.19),(-.18,.32,.18),(-.15,.30,.30)],.006,p['rubber']);box('Unused lead end',(-.15,.30,.317),(.024,.022,.042),p['rubber'],.004)
 return ('city-vertical-band-saw','縦型バンドソー','Vertical workshop band saw','地域の整備工房やメーカースペース用の縦型バンドソー。上下の車輪ハウジングを左の背骨フレームでつなぎ、開いた喉部、差し込みスリットと刃の穴を持つ作業台、定規フェンス、短く見える静止帯刃、ガイド、上部調整輪、正面スイッチ、後部モーター外装と中空の集じん口を造形しています。材料、切断動作、内部の駆動輪や配線は含みません。電気・機械・荷重支持・安全性は未検証の静的な外観モデルで、操作・製作の指示は付属しません。','A vertical band saw for municipal workshops and makerspaces. Separate upper and lower wheel housings connect through a left backbone around an open throat. Includes a slotted work table with real blade aperture, straight fence, short stationary visible band, guides, top adjustment wheel, front switches, rear motor exterior and hollow dust outlet. No stock, cutting action, internal drive wheels or wiring is included. Static appearance geometry with no electrical, mechanical, load-bearing or safety validation and no operation or fabrication instructions.',['workshop','band-saw','maintenance','makerspace','バンドソー'])

def bench_grinder():
 p=palette()
 for x in [-.115,.115]:
  for y in [-.09,.09]:cyl('Rubber isolation foot',(x,y,.018),.022,.036,p['rubber'],verts=24,bevel=.003)
 base=box('Bench mounting base',(0,0,.054),(.315,.272,.050),p['iron'],.017)
 for x in [-.125,.125]:
  for y in [-.094,.094]:cut(base,cyl('Mount bore cutter',(x,y,.054),.008,.12,None,verts=20,bevel=0))
 profile('Motor pedestal',0,.183,[(-.105,.068),(.105,.068),(.081,.232),(-.081,.232)],p['ochre'],bevel=.008)
 cyl('Central motor body',(0,.015,.270),.105,.282,p['ochre'],'X',48,.012)
 for x in [-.145,.145]:cyl('Motor end plate',(x,.015,.270),.099,.027,p['iron'],'X',48,.004)
 for a in [40,80,100,140,220,260,280,320]:
  t=math.radians(a);rod('Motor cooling fin',(-.117,.015+.105*math.cos(t),.270+.105*math.sin(t)),(.117,.015+.105*math.cos(t),.270+.105*math.sin(t)),.004,p['iron'])
 cyl('Stationary axle',(0,.015,.270),.023,.62,p['steel'],'X',32,.001)
 for side in [-1,1]:
  x=side*.257;cyl('Abrasive wheel',(x,.015,.270),.139,.055,p['stone'] if side<0 else p['fine'],'X',48)
  annular_x('Partial curved wheel guard',x,.015,.270,.150,.163,.082,-138,138,p['ochre'],56)
  annular_x('Partial outer side guard',x+side*.043,.015,.270,.039,.162,.008,-138,138,p['ochre'],56)
  annular_x('Partial inner side guard',x-side*.043,.015,.270,.039,.162,.008,-138,138,p['ochre'],56)
  cyl('Wheel retaining flange',(x+side*.033,.015,.270),.044,.013,p['steel'],'X',32);fastener('Arbor nut',(x+side*.044,.015,.270),p['iron'],'X',.015,side)
  box('Tool rest mounting lug',(x,-.086,.153),(.070,.055,.035),p['ochre'],.004);beam('Tool rest bracket',(x,-.087,.153),(x,-.172,.191),.031,.028,p['iron']);box('Operator tool rest',(x,-.176,.204),(.107,.092,.012),p['steel'],.002)
  for yy in [-.087,-.134]:fastener('Tool rest fastener',(x+side*.023,yy,.167),p['steel'],'X',.006,side)
  box('Guard mouth upper lip',(x,-.109,.374),(.100,.034,.018),p['iron'],.002,rot=(math.radians(-15),0,0));rod('Screen support',(x+side*.043,-.077,.396),(x+side*.043,-.151,.442),.005,p['steel'])
  cyl('Screen hinge',(x,-.153,.444),.008,.112,p['steel'],'X',20,.001);box('Opaque static screen',(x,-.179,.430),(.111,.058,.005),p['face'],.001,rot=(math.radians(20),0,0))
  for yy,zz in [(.11,.35),(.11,.19)]:fastener('Guard screw',(x+side*.050,yy,zz),p['steel'],'X',.005,side)
 box('Operator switch housing',(0,-.105,.124),(.108,.052,.080),p['dark'],.007);box('Switch rocker',(0,-.138,.127),(.048,.018,.046),p['rubber'],.004);box('Red off key',(0,-.149,.116),(.036,.006,.018),p['red'],.002);box('Plain motor label',(0,-.096,.285),(.10,.006,.035),p['iron'],.003)
 cable('Parked grinder cord',[(.05,.110,.192),(.07,.20,.145),(.16,.24,.08),(.07,.29,.057),(-.08,.28,.063),(-.13,.20,.084)],.006,p['rubber']);box('Unused cord plug',(-.140,.194,.087),(.042,.026,.025),p['rubber'],.004)
 return ('city-double-wheel-bench-grinder','両頭ベンチグラインダー','Double-wheel bench grinder','整備工房の作業台上に置く両頭グラインダー。中央モーター外装、左右の砥石、正面が実際に開いた部分カバーと側板、独立した工具受けと支持金具、上部リップ、支持された不透明な小型スクリーン、正面スイッチ、取付穴付きベースとゴム足を備えます。作業台、材料、回転・研削・火花は含みません。スクリーンは透過せず保護性能を示しません。電気・機械・荷重支持・安全性は未検証の静的な外観モデルで、操作・製作の指示は付属しません。','A double-wheel grinder for maintenance workshop benches, with central motor exterior, two abrasive wheels, genuinely open-front partial guards and side plates, separate bracketed tool rests, upper lips, supported opaque small screens, front switch, apertured base and rubber feet. No workbench, workpiece, rotation, grinding or sparks is included. The opaque screens are visual details, not evidence of protective performance. Static appearance geometry with no electrical, mechanical, load-bearing or safety validation and no operation or fabrication instructions.',['workshop','bench-grinder','maintenance','abrasive','グラインダー'])

def caster(x,y,p):
 cyl('Caster swivel',(x,y,.148),.024,.031,p['steel'],verts=24);box('Caster pad',(x,y,.174),(.081,.071,.018),p['dark'],.003)
 for xx in [x-.032,x+.032]:profile('Caster fork',xx,.010,[(y-.024,.143),(y+.031,.143),(y+.041,.059),(y-.017,.059)],p['steel'],'X')
 cyl('Caster rubber wheel',(x,y+.012,.060),.060,.047,p['rubber'],'X',32,.004);cyl('Caster hub',(x,y+.012,.060),.022,.052,p['iron'],'X',24);cyl('Caster axle',(x,y+.012,.060),.008,.084,p['steel'],'X',20,.001)

def welder_cart():
 p=palette()
 for x in [-.263,.263]:
  cyl('Rear transport tire',(x,.333,.116),.116,.058,p['rubber'],'X',40,.006);cyl('Rear wheel hub',(x,.333,.116),.060,.064,p['iron'],'X',32,.003);fastener('Rear axle nut',(x+(1 if x>0 else -1)*.038,.333,.116),p['steel'],'X',.011,1 if x>0 else -1)
 rod('Rear axle',(-.31,.333,.116),(.31,.333,.116),.013,p['steel'],24)
 for x in [-.217,.217]:box('Rear axle bearing bracket',(x,.333,.147),(.045,.065,.065),p['dark'],.004)
 for x in [-.215,.215]:caster(x,-.327,p)
 box('Lower tray floor',(0,.006,.192),(.50,.865,.026),p['dark'],.004)
 for x in [-.249,.249]:box('Lower tray side lip',(x,.006,.222),(.020,.865,.071),p['dark'],.003)
 for y in [-.418,.430]:box('Lower tray end lip',(0,y,.222),(.482,.018,.071),p['dark'],.003)
 for x in [-.217,.217]:
  beam('Cart underframe',(x,-.383,.172),(x,.397,.172),.038,.045,p['dark']);beam('Front shelf upright',(x,-.325,.20),(x,-.325,.585),.032,.032,p['dark']);beam('Rear handle upright',(x,.221,.19),(x,.221,1.097),.032,.032,p['dark']);beam('Shelf diagonal brace',(x,-.325,.253),(x,.208,.542),.025,.025,p['dark'])
 rod('Push handle',(-.221,.221,1.094),(.221,.221,1.094),.017,p['dark'],24);rod('Push handle grip',(-.14,.221,1.094),(.14,.221,1.094),.022,p['rubber'],24)
 box('Raised power unit shelf',(0,-.085,.555),(.502,.625,.027),p['dark'],.004)
 for x in [-.249,.249]:box('Upper shelf side lip',(x,-.085,.577),(.018,.625,.055),p['dark'],.003)
 for y in [-.389,.217]:box('Upper shelf end lip',(0,y,.578),(.48,.018,.055),p['dark'],.003)
 for x in [-.163,.163]:
  for y in [-.297,.128]:box('Power unit rubber foot',(x,y,.588),(.056,.065,.037),p['rubber'],.005)
 box('Power unit bottom panel',(0,-.086,.612),(.416,.548,.025),p['red'],.005);box('Power unit top panel',(0,-.086,.918),(.419,.551,.025),p['red'],.008)
 for x in [-.203,.203]:
  box('Side upper shell strip',(x,-.086,.875),(.020,.532,.064),p['red'],.003);box('Side lower shell strip',(x,-.086,.655),(.020,.532,.065),p['red'],.003)
  for y in [-.335,.165]:box('Side end frame',(x,y,.765),(.020,.044,.203),p['red'],.003)
  box('Recessed vent baffle',(x*.86,-.086,.765),(.014,.470,.155),p['dark'],.003)
  for i in range(7):box('Open side louver blade',(x,-.086,.692+i*.023),(.031,.468,.009),p['iron'],.001,rot=(0,math.radians(18),0))
 box('Front instrument panel',(0,-.358,.765),(.392,.023,.287),p['dark'],.007);box('Display bezel',(-.065,-.375,.839),(.165,.018,.068),p['iron'],.004);box('Blank opaque display',(-.065,-.387,.839),(.139,.009,.042),p['face'],.002)
 cyl('Front adjustment dial',(.112,-.388,.826),.031,.036,p['rubber'],'Y',32,.004);box('Dial marker',(.112,-.410,.846),(.004,.003,.009),p['steel'],.0004);box('Front rocker switch',(.112,-.376,.737),(.037,.020,.045),p['rubber'],.003)
 for x in [-.113,.093]:cyl('Lead connector bezel',(x,-.383,.677),.027,.033,p['iron'],'Y',32,.003);cyl('Connected lead plug',(x,-.414,.677),.018,.045,p['rubber'],'Y',24,.003)
 for x in [-.17,.17]:box('Rear grille upright',(x,.188,.765),(.049,.022,.284),p['dark'],.003)
 for z in [.633,.897]:box('Rear grille cross edge',(0,.188,z),(.294,.022,.022),p['dark'],.002)
 for i in range(8):box('Open rear ventilation louver',(0,.192,.661+i*.029),(.292,.032,.010),p['iron'],.001,rot=(math.radians(-20),0,0))
 box('Recessed electronics shield',(0,.145,.765),(.335,.016,.247),p['dark'],.003)
 for x in [-.176,.176]:
  for z in [.65,.882]:fastener('Front cover screw',(x,-.376,z),p['steel'],'Y',.004,-1)
 for x in [-.105,.105]:box('Carry handle mounting block',(x,-.086,.947),(.050,.067,.044),p['dark'],.006)
 rod('Power unit carry handle',(-.108,-.086,.974),(.108,-.086,.974),.018,p['rubber'],24)
 cyl('Cylinder support foot ring',(0,.329,.243),.109,.042,p['iron'],verts=40,bevel=.006);cyl('Closed cylinder body',(0,.329,.640),.096,.770,p['green'],verts=48,bevel=.031);cyl('Cylinder shoulder',(0,.329,1.018),.087,.082,p['green'],verts=48,bevel=.030);cyl('Cylinder capped neck',(0,.329,1.067),.041,.058,p['iron'],verts=32,bevel=.006)
 cap=cyl('Protective cylinder cap',(0,.329,1.123),.052,.113,p['green'],verts=40,bevel=.018)
 for x in [-.051,.051]:cut(cap,box('Cap side window cutter',(x,.329,1.125),(.045,.056,.039),None,.007))
 for z in [.440,.885]:
  torus('Cylinder retaining band',(0,.329,z),.101,.009,p['dark'],segments=40)
  for x in [-.103,.103]:beam('Strap mounting ear',(x,.329,z),(x,.218,z),.024,.018,p['dark'],.002)
  box('Retention cross rail',(0,.221,z),(.424,.028,.034),p['dark'],.003);fastener('Strap clasp',(.103,.321,z),p['steel'],'X',.006)
 for x in [-.352,.352]:rod('Cable hook peg',(x*.6165,-.158,.610),(x,-.158,.610),.009,p['steel']);rod('Cable hook upturn',(x,-.158,.610),(x,-.158,.652),.009,p['steel'])
 cable('Welding torch lead',[(-.113,-.441,.677),(-.18,-.47,.65),(-.31,-.41,.55),(-.326,-.29,.34),(-.326,-.09,.325),(-.326,-.035,.50),(-.326,-.16,.619),(-.326,-.27,.55),(-.326,-.27,.40),(-.326,-.10,.405),(-.326,-.065,.61),(-.326,-.078,.75)],.010,p['rubber'])
 box('Torch parking bracket',(-.262,-.08,.759),(.116,.054,.026),p['dark'],.003);rod('Torch grip',(-.326,-.078,.733),(-.326,-.078,.853),.021,p['rubber'],28);box('Torch trigger',(-.347,-.078,.799),(.009,.030,.043),p['red'],.002);rod('Torch neck',(-.326,-.078,.852),(-.326,-.055,.887),.010,p['steel']);rod('Torch angled tip',(-.326,-.055,.887),(-.326,.001,.907),.010,p['steel']);rod('Inactive nozzle',(-.326,-.005,.905),(-.326,.034,.918),.016,p['brass'],24)
 cable('Ground clamp lead',[(.093,-.441,.677),(.18,-.46,.60),(.315,-.37,.48),(.325,-.21,.305),(.325,-.065,.33),(.325,-.048,.52),(.325,-.158,.617),(.325,-.23,.49),(.325,-.13,.403),(.325,-.015,.53),(.325,.004,.72)],.008,p['rubber'])
 box('Clamp parking tab',(.267,.006,.774),(.118,.039,.023),p['dark'],.003);profile('Clamp lower jaw',.325,.023,[(-.009,.705),(.008,.705),(.034,.778),(.030,.823),(.006,.813),(.011,.772)],p['steel'],'X');profile('Clamp upper jaw',.325,.023,[(.014,.716),(.034,.711),(.047,.774),(.029,.822),(.010,.817),(.025,.772)],p['iron'],'X');cyl('Clamp hinge',(.325,.026,.774),.011,.043,p['steel'],'X',20,.001);box('Clamp insulated handle',(.325,.004,.737),(.029,.021,.067),p['rubber'],.005,rot=(math.radians(12),0,0))
 return ('city-welding-machine-cart','溶接機とケーブルの専用カート','Welding machine and cable cart','街の整備工房に置く移動式溶接機の一式。無表示画面・ダイヤル・接続端子、実際に隙間のある側面・後面ルーバーを持つ電源装置外装を、二段トレーと斜材、後部大径車輪、前部キャスター、押し手付きの専用台車に載せています。フックに掛けたケーブル、静止トーチとアースクランプ、後部の保護キャップ付き密閉ボンベ外装と二本の保持バンドを含み、一式で一モデルです。火花・熱・溶接動作・内部回路・ボンベ内容物はありません。電気・機械・圧力・荷重支持・安全性は未検証の静的な外観モデルで、操作・製作の指示は付属しません。','A mobile welding setup for municipal workshops. An exterior-only power unit with blank screen, dial, lead connectors and real open side/rear louvers sits on a purpose-built two-level trolley with diagonal braces, large rear wheels, front casters and push handle. Includes hooked cable loops, parked inactive torch and ground clamp, and a rear closed cylinder exterior with protective cap and two retaining bands. The whole assembly is one model. No sparks, heat, welding action, internal circuitry or cylinder contents are included. Static appearance geometry with no electrical, mechanical, pressure, load-bearing or safety validation and no operation or fabrication instructions.',['workshop','welder','trolley','maintenance','溶接機'])

BUILDERS=[drill_press,band_saw,bench_grinder,welder_cart]
IDS=['city-floor-drill-press','city-vertical-band-saw','city-double-wheel-bench-grinder','city-welding-machine-cart']
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-027/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if args.geometry_only:common.render=lambda *args,**kwargs:None
 out=Path(args.out);out=out if out.is_absolute() else ROOT/out
 for fn,id in zip(BUILDERS,IDS):
  if args.only and args.only!=id:continue
  reset();spec=fn();publish_asset(*spec,out,'scripts/city_expansion/workshop_machines.py',azimuth=-55,elevation=24)
