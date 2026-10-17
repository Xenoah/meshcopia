"""Original community art-room equipment. Xenoah, CC BY 4.0.
No external artwork, drawings, brands, powered mechanisms or functional certification.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(wood=mat('Warm plain easel wood',(.43,.26,.12),0,.50),darkwood=mat('Dark wooden stiffeners',(.20,.11,.052),0,.55),ivory=mat('Unmarked warm canvas or board',(.75,.75,.68),0,.69),steel=mat('Satin workshop fittings',(.47,.52,.55),.72,.35),bright=mat('Polished small hardware',(.65,.69,.71),.80,.28),paint=mat('Muted sage machine enamel',(.13,.29,.24),.13,.43),dark=mat('Dark metal fixtures',(.045,.062,.066),.32,.48),rubber=mat('Dark pads and cable rubber',(.018,.023,.026),0,.74),tray=mat('Warm neutral ceramic splash pan',(.58,.58,.50),.03,.43),red=mat('Unlit small power-control accent',(.39,.040,.028),0,.45))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(n,p,r,t,m,axis='Z',v=40):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)
def sleeve(n,p,ro,ri,h,m,axis='Z',v=32):
 vs=[]
 for r,z in [(ro,-h/2),(ro,h/2),(ri,h/2),(ri,-h/2)]:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%4)*v+(i+1)%v,((k+1)%4)*v+i) for k in range(4) for i in range(v)];o=mesh(n,vs,fs,m);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,2]
 return o
def frame(n,w,h,t,d,p,m,plane='XZ',bev=.002):
 vs=[]
 for ww,hh,z in [(w,h,-d/2),(w,h,d/2),(w-2*t,h-2*t,d/2),(w-2*t,h-2*t,-d/2)]:vs.extend([(-ww/2,-hh/2,z),(ww/2,-hh/2,z),(ww/2,hh/2,z),(-ww/2,hh/2,z)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)];o=mesh(n,vs,fs,m,bev);o.location=p
 if plane=='XZ':o.rotation_euler[0]=math.pi/2
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 return o
def floor_easel():
 p=pal()
 for side in [-1,1]:
  bar('Splayed easel front wooden leg',(side*.418,-.145,.041),(side*.063,-.020,1.814),.049,.048,p['wood'],.004)
  box('Easel front leg floor pad',(side*.418,-.145,.024),(.069,.069,.034),p['rubber'],.004)
 bar('Easel rear folding wooden leg',(0,.609,.040),(0,.012,1.546),.048,.050,p['wood'],.004)
 box('Rear easel floor pad',(0,.609,.023),(.070,.074,.032),p['rubber'],.004)
 box('Easel center adjustable mast',(0,-.038,1.147),(.059,.041,1.444),p['wood'],.004)
 bar('Easel upper wooden cross brace',(-.104,-.014,1.621),(.104,-.014,1.621),.050,.046,p['wood'],.003)
 bar('Easel lower wooden cross brace',(-.305,-.106,.595),(.305,-.106,.595),.049,.047,p['wood'],.003)
 # A blank stretched canvas belongs to this easel assembly, not an artwork.
 box('Unpainted plain canvas face',(0,-.133,1.194),(.802,.020,.718),p['ivory'],.003)
 for x in [-.365,.365]:box('Rear canvas wooden stretcher',(x,-.104,1.194),(.058,.043,.706),p['darkwood'],.003)
 for z in [.863,1.525]:box('Rear canvas horizontal stretcher',(0,-.104,z),(.727,.043,.053),p['darkwood'],.003)
 bar('Rear canvas diagonal support',(-.335,-.082,.884),(.335,-.082,1.505),.025,.018,p['wood'],.002)
 box('Easel adjustable lower tray',(0,-.140,.810),(.928,.158,.047),p['wood'],.005)
 box('Easel tray front retaining lip',(0,-.220,.838),(.934,.023,.049),p['darkwood'],.004)
 for x in [-.300,.300]:box('Lower tray rear support cleat',(x,-.081,.796),(.074,.083,.093),p['darkwood'],.005)
 box('Easel lower tray sliding clamp',(0,-.047,.765),(.116,.074,.130),p['wood'],.005)
 cyl('Easel tray fixed tightening knob',(0,-.094,.763),.035,.038,p['dark'],'Y',v=28,b=.004)
 box('Easel upper canvas holding clamp',(0,-.098,1.581),(.203,.153,.051),p['wood'],.004)
 box('Upper clamp rear sliding block',(0,-.039,1.611),(.098,.073,.104),p['wood'],.004)
 cyl('Upper clamp fixed knob',(0,-.086,1.629),.026,.026,p['dark'],'Y',v=28,b=.003)
 cyl('Easel rear leg upper hinge',(0,.013,1.545),.021,.122,p['steel'],'X',v=24,b=.002)
 # Folding spreaders connect each front side to the rear leg at its actual position.
 for side in [-1,1]:
  a=(side*.288,-.094,.692);b=(side*.095,.183,.672);c=(0,.351,.692)
  bar('Easel spreader front link',a,b,.014,.009,p['steel'],.0015)
  bar('Easel spreader rear link',b,c,.014,.009,p['steel'],.0015)
  cyl('Easel spreader folding pin',b,.013,.016,p['dark'],'X',v=20,b=.001)
 return ('city-tripod-floor-easel','三脚式フロアイーゼル','Tripod floor easel','交流施設の美術室・制作室に置く木製三脚イーゼル。開いた前二脚と折り畳み式の後脚、中央マスト、上下の固定クランプ、下受け皿と落下止め、金属の開き止め、無地キャンバスと裏の木枠を造形。キャンバスは一式に含まれ、絵画・作者名・図柄はありません。調整や折り畳み動作、構造安全の検証はありません。','A wooden tripod easel for community art rooms and studios. It includes splayed front legs, rear folding-style leg, center mast, fixed upper/lower clamps, lower tray/retaining lip, metal spreaders and a blank canvas with rear stretcher frame. The canvas belongs to this one assembly; no painting, artist name or artwork is included. Adjustment, folding motion and structural-safety validation are not supplied.',['art','easel','workshop','イーゼル'])

def pottery_wheel():
 p=pal()
 for x in [-.215,.215]:
  for y in [-.188,.188]:
   box('Pottery wheel square leg',(x,y,.228),(.051,.051,.381),p['steel'],.004)
   box('Pottery wheel foot pad',(x,y,.029),(.072,.074,.040),p['rubber'],.005)
 box('Pottery wheel main drive enclosure',(0,.011,.480),(.529,.474,.293),p['paint'],.020)
 box('Pottery wheel upper support deck',(0,.012,.638),(.557,.505,.036),p['dark'],.007)
 cyl('Wheel spindle housing',(0,0,.680),.102,.115,p['steel'],v=40,b=.005)
 for i in range(3):
  a=i*math.tau/3;cyl('Splash basin deck support pad',(.235*math.cos(a),.235*math.sin(a),.672),.029,.038,p['rubber'],v=24,b=.002)
 # Eight profile rings give a real open splash basin and central opening.
 v=64;profile=[(.327,.680),(.343,.779),(.335,.797),(.312,.797),(.299,.710),(.109,.710),(.109,.688),(.305,.688)];vs=[]
 for r,z in profile:vs.extend((r*math.cos(i*math.tau/v),r*math.sin(i*math.tau/v),z) for i in range(v))
 fs=[(k*v+i,k*v+(i+1)%v,((k+1)%len(profile))*v+(i+1)%v,((k+1)%len(profile))*v+i) for k in range(len(profile)) for i in range(v)];o=mesh('Open pottery splash basin',vs,fs,p['tray'])
 for f in o.data.polygons:f.use_smooth=f.index//v in [0,1,3,4,6,7]
 cyl('Pottery wheel throwing head',(0,0,.743),.202,.029,p['steel'],v=64,b=.003)
 for r in [.066,.129,.183]:ring('Wheelhead shallow concentric guide',(0,0,.759),r,.0014,p['bright'],v=64)
 for y in [-.237,.237]:
  box('Wheel drive enclosure service seam',(0,y,.479),(.434,.016,.195),p['paint'],.006)
  for x in [-.170,.170]:cyl('Drive service-panel screw',(x,y*1.04,.480),.007,.006,p['dark'],'Y',v=12,b=.0005)
 box('Pottery wheel power control bezel',(.153,-.252,.526),(.098,.022,.060),p['dark'],.005)
 cyl('Fixed pottery power control',(.153,-.266,.526),.018,.014,p['red'],'Y',v=24,b=.002)
 for z in [.421+i*.028 for i in range(5)]:box('Rear motor cooling vent',(0,.255,z),(.241,.010,.010),p['dark'],.002)
 # Included wired foot controller is parked in front, joined by a fixed cable.
 box('Pottery foot controller lower base',(.319,-.459,.035),(.142,.233,.047),p['dark'],.007)
 box('Fixed tilted pottery foot pedal',(.319,-.459,.079),(.133,.212,.032),p['rubber'],.006,rot=(math.radians(-12),0,0))
 for y in [-.518,-.480,-.442,-.404]:box('Foot pedal traction rib',(.319,y,.099+(y+.459)*math.sin(math.radians(-12))),(.114,.010,.008),p['dark'],.001)
 cyl('Foot pedal hinge axle',(.319,-.363,.057),.014,.161,p['steel'],'X',v=24,b=.001)
 tube('Fixed pedal cable',[(.262,-.359,.049),(.171,-.337,.034),(.041,-.346,.038),(-.069,-.283,.145),(-.103,-.235,.381)],.007,p['rubber'],1)
 return ('city-electric-pottery-wheel','足踏み操作器付き電動ろくろ','Electric pottery wheel with pedal','陶芸教室・交流施設の制作室に置く電動ろくろ外観。回転円盤と細い同心ガイド、内側が実際に開いた飛沫受け鉢、主軸外装、駆動筐体と通気表現、四脚、ケーブルで繋がる足踏み操作器を造形。粘土・器・椅子は含まず、ペダルは本体と合わせて一式1点です。回転・速度制御・電装や実用品性能は実装・検証していません。','An electric pottery-wheel appearance prop for ceramics classes and community studios. It has a throwing disk with fine concentric guides, genuinely open splash basin, spindle exterior, drive enclosure/vent details, four legs and a cable-connected foot controller. Clay, pottery and stool are absent; the included pedal is part of one assembly. Rotation, speed control, electrical operation and real-equipment performance are not implemented or validated.',['art','pottery','workshop','ろくろ'])

def printmaking_press():
 p=pal()
 for x in [-.485,.485]:
  for y in [-.307,.307]:
   box('Printmaking press stand leg',(x,y,.411),(.058,.058,.744),p['paint'],.005)
   box('Press stand floor pad',(x,y,.028),(.088,.088,.038),p['rubber'],.005)
  bar('Press stand width brace',(x,-.307,.249),(x,.307,.249),.033,.033,p['steel'],.003)
 for y in [-.307,.307]:
  bar('Press upper stand beam',(-.619,y,.774),(.619,y,.774),.071,.067,p['paint'],.005)
  bar('Press stand long diagonal',(-.472,y,.278),(.472,y,.693),.025,.024,p['steel'],.002)
 for y in [-.361,.361]:
  frame('Press cast-style side frame',.472,.534,.068,.072,(0,y,1.024),p['paint'],'XZ',.007)
  for x in [-.180,.180]:box('Press side-frame mounting foot',(x,y,.786),(.102,.114,.067),p['dark'],.004)
 for z in [.823,1.045]:
  cyl('Printmaking main pressure roller',(0,0,z),.100,.626,p['bright'],'Y',v=48,b=.004)
  cyl('Main pressure roller through shaft',(0,0,z),.028,.877,p['steel'],'Y',v=28,b=.002)
  for y in [-.410,.410]:cyl('Main roller bearing cap',(0,y,z),.061,.038,p['dark'],'Y',v=32,b=.003)
 for y in [-.361,.361]:
  box('Upper roller sliding bearing carrier',(0,y,1.045),(.350,.084,.132),p['dark'],.004)
  cyl('Upper roller adjustment screw',(0,y,1.247),.016,.302,p['bright'],v=24,b=.001)
  cyl('Adjustment threaded collar',(0,y,1.280),.035,.044,p['dark'],v=28,b=.002)
  rod('Upper adjustment T handle',(-.085,y,1.400),(.085,y,1.400),.011,p['steel'],20)
  for x in [-.085,.085]:sphere('Adjustment handle round end',(x,y,1.400),(.018,.018,.018),p['dark'],segments=16,rings=8)
 # Long sliding bed lies in the gap between the fixed rollers, with supporting idlers.
 box('Press sliding metal bed',(0,0,.931),(1.570,.594,.022),p['steel'],.004)
 box('Plain printmaking bed blanket',(0,0,.947),(1.403,.544,.011),p['darkwood'],.002)
 for x in [-.535,.535]:
  cyl('Press bed supporting idler',(x,0,.873),.045,.584,p['dark'],'Y',v=32,b=.002)
  for y in [-.309,.309]:box('Bed idler supporting bracket',(x,y,.827),(.067,.043,.126),p['paint'],.004)
 # Handwheel attaches to the lower roller shaft, with three real spokes and crank grip.
 ring('Press feed handwheel',(0,-.486,.823),.220,.014,p['steel'],'Y',64)
 cyl('Feed handwheel center hub',(0,-.483,.823),.048,.079,p['dark'],'Y',v=28,b=.003)
 for i in range(3):
  a=i*math.tau/3;rod('Feed handwheel spoke',(0,-.483,.823),(.211*math.cos(a),-.483,.823+.211*math.sin(a)),.010,p['steel'],20)
 rod('Feed handwheel crank pin',(.211,-.483,.823),(.211,-.625,.823),.010,p['steel'],20)
 cyl('Feed crank hand grip',(.211,-.620,.823),.021,.104,p['rubber'],'Y',v=28,b=.004)
 return ('city-compact-printmaking-press','スタンド付き小型版画プレス','Compact printmaking press on stand','美術室・地域工房に置く手回し版画プレス。上下二本の太いローラーと両側フレーム、上部の調整ねじ・Tハンドル、長い送り盤と無地マット、支持ローラー、三本スポークの手回し輪とグリップ、補強した四脚スタンドを造形。紙・版・インク・作品は含みません。ローラー・送り盤・調整機構は静止し、印刷や圧力性能の検証はありません。','A hand-cranked printmaking press for art rooms and community workshops. It has two thick pressure rollers with side frames, upper adjustment screws/T handles, long sliding bed and plain mat, support idlers, a three-spoke feed handwheel with crank grip, and a braced four-leg stand. Paper, plates, ink and artworks are absent. Rollers, bed and adjustments are fixed; printing and pressure performance are not validated.',['art','printmaking','press','版画プレス'])

def drafting_table():
 p=pal()
 for x in [-.438,.438]:
  box('Drafting-table T-foot',(x,0,.048),(.092,.858,.066),p['paint'],.010)
  for y in [-.363,.363]:box('Drafting table rubber foot pad',(x,y,.019),(.106,.115,.027),p['rubber'],.005)
  box('Drafting-table vertical pedestal',(x,.030,.509),(.067,.084,.884),p['paint'],.007)
  box('Drafting pedestal height collar',(x,.030,.704),(.094,.112,.102),p['dark'],.006)
  cyl('Fixed height-lock knob',(x+(.063 if x>0 else -.063),.030,.704),.031,.043,p['dark'],'X',v=28,b=.003)
 bar('Drafting lower frame crossmember',(-.438,.044,.294),(.438,.044,.294),.047,.049,p['steel'],.004)
 bar('Drafting upper pivot crossmember',(-.438,.015,.967),(.438,.015,.967),.045,.049,p['steel'],.004)
 # A complete unmarked drawing board is fixed at thirty degrees, with true rear bracing.
 before=set(bpy.context.scene.objects)
 box('Drafting board wooden core',(0,0,0),(1.231,.851,.034),p['wood'],.006)
 box('Unmarked drafting surface',(0,0,.023),(1.199,.819,.012),p['ivory'],.003)
 for x in [-.433,.433]:box('Drafting board underside stiffener',(x,0,-.041),(.052,.734,.045),p['darkwood'],.004)
 for y in [-.318,.318]:box('Drafting board underside cross brace',(0,y,-.065),(.919,.047,.035),p['steel'],.003)
 box('Front pencil retaining ledge',(0,-.417,.051),(1.185,.039,.049),p['wood'],.005)
 box('Parallel drafting ruler',(0,-.125,.045),(1.141,.055,.016),p['steel'],.003)
 for x in [-.510,.510]:
  box('Ruler sliding handle',(x,-.125,.065),(.076,.080,.028),p['dark'],.004)
  for y in [-.350,.350]:cyl('Parallel-rule cable pulley',(x,y,.043),.013,.013,p['dark'],v=24,b=.001)
  rod('Parallel-rule guide cable',(x,-.350,.044),(x,.350,.044),.0018,p['dark'],12)
 for y in [-.350,.350]:rod('Parallel-rule cable cross run',(-.510,y,.044),(.510,y,.044),.0018,p['dark'],12)
 bpy.context.view_layer.update()
 transform=Matrix.Translation((0,0,1.071))@Matrix.Rotation(math.radians(30),4,'X')
 for o in set(bpy.context.scene.objects)-before:o.matrix_world=transform@o.matrix_world
 for x in [-.438,.438]:
  cyl('Drafting board tilt pivot',(x,0,1.002),.053,.094,p['dark'],'X',v=32,b=.003)
  # Paired fixed adjustment struts visibly connect the post to rear board cross-brace.
  a=(x,.030,.667);b=(x,.279,1.202)
  rod('Drafting tilt adjustment outer sleeve',a,Vector(a).lerp(Vector(b),.58),.018,p['steel'],24)
  rod('Drafting tilt adjustment inner rod',Vector(a).lerp(Vector(b),.45),b,.011,p['bright'],20)
  for q in [a,b]:cyl('Tilt support end pivot',q,.022,.076,p['dark'],'X',v=24,b=.001)
  cyl('Drafting board fixed tilt knob',(x+(.073 if x>0 else -.073),0,1.002),.036,.043,p['dark'],'X',v=28,b=.004)
 return ('city-tilting-drafting-table','平行定規付き傾斜製図台','Tilting drafting table with parallel rule','設計教室・交流施設の制作室に置く傾斜製図台。30度に固定した無地の板面、裏補強、前の鉛筆受け、平行定規と小さな滑車・実ケーブル、二本の支柱とT字脚、回転支点・傾斜支持材・固定ノブを造形。紙・図面・筆記具・椅子は含まず、板と定規は一台に含まれます。高さ・傾斜・定規の可動機能と精度検証はありません。','A tilting drafting table for design classrooms and community studios. It has a blank board fixed at thirty degrees, rear stiffeners, front pencil ledge, parallel rule with small pulleys and real cable geometry, twin pedestals/T feet, tilt pivots, supporting struts and fixed knobs. Paper, drawings, writing tools and chair are absent; board and ruler belong to one table assembly. Height, tilt and rule movement and accuracy validation are not provided.',['art','drafting','table','製図台'])

BUILDERS=[floor_easel,pottery_wheel,printmaking_press,drafting_table]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-042/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/community_art_workshop.py',azimuth=-55,elevation=27)
