"""Original educational bench instruments. Xenoah, CC BY 4.0.
Static props with no measurements, heating, optics, electronics or gripping behavior.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(white=mat('Warm light instrument enclosure',(.68,.70,.69),.04,.45),paint=mat('Muted blue instrument finish',(.055,.20,.29),.12,.44),steel=mat('Satin instrument metal',(.46,.52,.55),.74,.34),bright=mat('Bright connector metal',(.64,.69,.72),.82,.27),dark=mat('Dark instrument trim',(.038,.051,.060),.22,.48),rubber=mat('Dark cable and grip rubber',(.016,.021,.025),0,.75),screen=mat('Opaque inactive screen or lens',(.025,.075,.093),.12,.27),yellow=mat('Plain yellow sponge block',(.58,.43,.095),0,.86),red=mat('Unlit small red button',(.40,.041,.029),0,.43))
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
def microscope():
 p=pal()
 box('Microscope broad weighted-looking base',(0,.020,.040),(.220,.292,.061),p['white'],.018)
 for x in [-.078,.078]:
  for y in [-.089,.124]:cyl('Microscope rubber foot',(x,y,.010),.019,.018,p['rubber'],v=20,b=.002)
 # Concave C-arm profile extruded in X leaves the viewing and specimen space open.
 profile=[(-.020,.060),(.118,.060),(.143,.089),(.137,.323),(.101,.402),(.039,.414),(-.012,.376),(.025,.344),(.068,.350),(.085,.316),(.081,.111),(.038,.084),(-.020,.084)];k=len(profile);vs=[(x,y,z) for x in [-.034,.034] for y,z in profile];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];mesh('Microscope curved-profile C support',vs,fs,p['white'],.004)
 box('Stage rear mounting bridge',(0,.075,.225),(.109,.040,.038),p['dark'],.004)
 stage=box('Specimen stage with true aperture',(0,-.009,.239),(.163,.157,.018),p['dark'],0)
 cutter=cylinder('Temporary stage aperture cutter',(0,-.027,.239),.018,.070,p['dark'],32,bevel=0);mod=stage.modifiers.new('Open specimen optical aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.context.view_layer.objects.active=stage;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 bevel=stage.modifiers.new('Soft stage edge','BEVEL');bevel.width=.0015;bevel.segments=1
 for x in [-.050,.050]:
  box('Fixed specimen spring clip',(x,-.017,.253),(.009,.095,.004),p['bright'],.001)
  cyl('Specimen clip screw',(x,.024,.255),.008,.006,p['steel'],v=16,b=.0005)
 cyl('Microscope condenser exterior',(0,-.027,.202),.029,.060,p['dark'],v=32,b=.002)
 cyl('Condenser lower opaque lens',(0,-.027,.171),.022,.008,p['screen'],v=32,b=.001)
 cyl('Base illuminator surround',(0,-.027,.077),.036,.019,p['steel'],v=32,b=.002)
 cyl('Unlit opaque illuminator face',(0,-.027,.088),.027,.006,p['screen'],v=32,b=.0007)
 cyl('Objective-turret supporting neck',(0,-.028,.355),.023,.046,p['white'],v=28,b=.002)
 cyl('Focus controls connecting axle',(0,.065,.282),.013,.145,p['steel'],'X',v=24,b=.001)
 cyl('Fixed objective turret',(0,-.028,.336),.043,.019,p['dark'],v=36,b=.002)
 for i in range(3):
  a=i*math.tau/3;x=.027*math.cos(a);y=-.028+.027*math.sin(a);h=[.040,.050,.058][i]
  cyl('Individual objective barrel',(x,y,.321-h/2),.011,h,p['steel'],v=24,b=.001)
  cyl('Objective dark end face',(x,y,.320-h),.008,.004,p['screen'],v=24,b=.0004)
 box('Microscope binocular head housing',(0,-.007,.401),(.095,.071,.064),p['white'],.011,rot=(math.radians(20),0,0))
 rod('Optical head supporting neck',(0,.055,.389),(0,-.010,.405),.031,p['white'],32)
 for side in [-1,1]:
  a=Vector((side*.025,-.023,.425));b=Vector((side*.030,-.082,.486));v=(b-a).normalized()
  rod('Inclined eyepiece tube',a,b,.013,p['dark'],28)
  o=sleeve('Open eyepiece rubber cup',b+v*.006,.017,.010,.022,p['rubber'],v=32);o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
  o=cyl('Opaque inset eyepiece lens',b-v*.004,.009,.003,p['screen'],v=28,b=.0005);o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
  cyl('Coarse microscope focus knob',(side*.064,.065,.282),.030,.044,p['dark'],'X',v=32,b=.003)
  cyl('Fine microscope focus knob',(side*.091,.065,.282),.016,.019,p['steel'],'X',v=28,b=.002)
 cyl('Stage traverse fixed knob',(.091,.023,.215),.015,.024,p['dark'],'X',v=24,b=.002)
 cyl('Base fixed illumination control',(.092,-.052,.047),.012,.023,p['dark'],'X',v=24,b=.001)
 box('Rear microscope service cover',(0,.146,.166),(.054,.011,.103),p['white'],.004)
 cyl('Rear instrument connection cap',(0,.153,.130),.010,.010,p['dark'],'Y',v=24,b=.001)
 return ('city-binocular-lab-microscope','双眼式実習用顕微鏡','Binocular laboratory microscope','学校・公共施設の実習室で机上に配置する双眼式顕微鏡。C字支持アーム、実開口のあるステージと標本クリップ、三本の対物レンズ外装、斜めの接眼部、粗微動ノブ、コンデンサー・照明部外形、背面接続口を造形。標本やスライドは含まず、レンズは不透明な色付きPBR面です。拡大光学、照明、焦点調整や検査機能は実装していません。','A binocular microscope for desk placement in school and public-facility teaching labs. It includes a C-shaped support, stage with a real opening and specimen clips, three objective exteriors, inclined eyepieces, coarse/fine focus knobs, condenser/illuminator exteriors and rear connection detail. Specimen and slides are absent; lenses are opaque colored PBR surfaces. Optical magnification, illumination, focusing and inspection functions are not implemented.',['education','microscope','laboratory','顕微鏡'])

def solder_station():
 p=pal()
 box('Soldering controller enclosure',(-.167,.017,.072),(.194,.187,.119),p['paint'],.014)
 for x in [-.237,-.097]:
  for y in [-.046,.081]:box('Controller rubber floor pad',(x,y,.009),(.029,.034,.016),p['rubber'],.003)
 box('Soldering controller front panel',(-.167,-.082,.075),(.169,.015,.094),p['dark'],.006)
 box('Blank temperature display',(-.183,-.092,.097),(.094,.007,.033),p['screen'],.002)
 cyl('Fixed temperature control knob',(-.126,-.099,.052),.023,.025,p['rubber'],'Y',v=28,b=.003)
 cyl('Controller cable connector collar',(-.220,-.093,.048),.011,.014,p['bright'],'Y',v=24,b=.001)
 for y in [-.023,.009,.041,.073]:box('Controller upper vent slot',(-.169,y,.135),(.123,.012,.006),p['dark'],.001)
 box('Iron holder wide base',(.130,-.040,.023),(.166,.269,.036),p['dark'],.008)
 for x in [.069,.191]:
  for y in [-.144,.063]:box('Iron holder rubber pad',(x,y,.007),(.024,.029,.012),p['rubber'],.002)
 # The metal coil is actual thick helix geometry around the parked iron shaft.
 axis=Vector((0,.664,.747));center=Vector((.130,-.020,.086));u=Vector((1,0,0));v=axis.cross(u).normalized();pts=[]
 for i in range(121):
  a=i*math.tau/24;t=-.043+.086*i/120;q=center+axis*t+.022*(u*math.cos(a)+v*math.sin(a));pts.append(tuple(q))
 tube('Five-turn iron-holder coil',pts,.0027,p['bright'],1)
 for side in [-1,1]:rod('Iron coil holder support',(.130+side*.023,.010,.038),(.130+side*.023,.001,.102),.006,p['steel'],16)
 a=Vector((.130,-.064,.036));b=Vector((.130,.018,.129));rod('Parked soldering iron metal shaft',a,b,.006,p['steel'],24)
 rod('Soldering iron tapered-looking tip',(.130,-.078,.021),a,.003,p['bright'],20)
 rod('Soldering iron heat-resistant grip',(.130,.014,.124),(.130,.083,.202),.014,p['rubber'],28)
 for t in [.10,.32,.54]:
  q=Vector((.130,.014,.124)).lerp(Vector((.130,.083,.202)),t);o=ring('Iron grip collar',q,.014,.002,p['dark'],v=28);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 tube('Connected fixed iron cable',[(.130,.084,.203),(.133,.117,.222),(.071,.163,.177),(-.031,.169,.074),(-.093,.135,.054),(-.166,.111,.057)],.006,p['rubber'],1)
 box('Rear iron cable socket',(-.166,.115,.058),(.033,.023,.033),p['dark'],.004)
 frame('Open sponge tray rim',.139,.079,.010,.021,(.130,-.126,.044),p['steel'],'XY')
 box('Sponge tray bottom',(.130,-.126,.039),(.135,.075,.012),p['steel'],.002)
 box('Plain cleaning sponge block',(.130,-.126,.054),(.112,.051,.016),p['yellow'],.003)
 return ('city-soldering-workstation','こて台付きはんだ付けステーション','Soldering station with iron holder','公共工房・電子工作室の作業台に置く温調器付きこて一式。無表示パネルと固定つまみの制御箱、接続ケーブル、保持コイルに収めたこてと金属先端、広いこて台、実開口のあるスポンジ皿と無地スポンジを造形。制御器・こて・台は合わせて一式1点で、作業台や部品は含みません。加熱、温度制御、電装やはんだ付け動作はありません。','A temperature-controller and iron assembly for public workshops and electronics benches. It includes a controller with blank display/fixed knob, connected cable, parked iron and metal tip in a real retaining coil, wide holder base and open sponge tray with plain sponge. Controller, iron and holder count as one assembly; bench and electronic parts are absent. Heating, temperature control, electrical operation and soldering behavior are not supplied.',['electronics','soldering','workshop','はんだごて'])

def oscilloscope():
 p=pal()
 box('Oscilloscope main enclosure',(0,.008,.112),(.354,.188,.193),p['white'],.015)
 box('Oscilloscope front bezel',(0,-.095,.112),(.342,.020,.181),p['dark'],.008)
 for x in [-.135,.135]:
  for y in [-.062,.080]:box('Oscilloscope foot pad',(x,y,.012),(.055,.045,.021),p['rubber'],.005)
 box('Blank oscilloscope screen',(-.073,-.108,.139),(.160,.008,.106),p['screen'],.003)
 for z in [.091,.120,.149,.178]:box('Unlabeled screen-side soft key',(.021,-.115,z),(.015,.016,.012),p['white'],.002)
 for x,z,r in [(.073,.167,.019),(.128,.167,.014),(.073,.107,.012),(.128,.107,.012),(.065,.058,.010),(.117,.058,.010)]:
  cyl('Fixed oscilloscope adjustment knob',(x,-.117,z),r,.025,p['white'],'Y',v=28,b=.002)
  box('Knob top position rib',(x,-.131,z+r*.57),(.003,.004,r*.60),p['dark'],.0005)
 for x in [-.126,-.081,-.036,.009]:
  sleeve('Open oscilloscope input socket',(x,-.116,.048),.010,.006,.021,p['bright'],'Y',v=28)
  cyl('Input socket recessed dark center',(x,-.106,.048),.005,.003,p['rubber'],'Y',v=20,b=.0003)
 for x in [-.187,.187]:
  cyl('Carry-handle side pivot',(x,.010,.135),.025,.026,p['dark'],'X',v=28,b=.002)
  bar('Raised fixed handle side arm',(x,.010,.135),(x,.010,.268),.019,.028,p['paint'],.004)
 box('Raised carrying handle crossbar',(0,.010,.268),(.390,.031,.028),p['paint'],.008)
 box('Handle soft central grip',(0,.010,.268),(.207,.037,.035),p['rubber'],.007)
 box('Rear fan grille backing',(-.078,.110,.119),(.139,.013,.119),p['dark'],.004)
 for i in range(6):box('Rear cooling grille louver',(-.078,.119,.074+i*.018),(.114,.012,.007),p['steel'],.001)
 box('Rear power-entry recess',(.102,.111,.083),(.071,.015,.051),p['dark'],.004)
 for x in [.084,.102,.120]:box('Power-entry metal pin exterior',(x,.124,.083),(.005,.012,.012),p['steel'],.0007)
 for x in [-.144,.144]:
  for z in [.056,.179]:cyl('Oscilloscope rear service screw',(x,.110,z),.005,.006,p['steel'],'Y',v=12,b=.0005)
 return ('city-bench-oscilloscope','卓上オシロスコープ','Benchtop oscilloscope','電子工作室・学校の実習机に置く無銘の卓上測定器。無表示の画面、固定ノブとソフトキー、四つの実開口付き入力ソケット、上げた取手と側面支点、脚、背面の冷却グリル・電源入口外形を造形。波形、数値、プローブ、外部装置は含みません。静的な外観モデルで、信号取得・表示・電気測定や校正性能はありません。','An unbranded benchtop instrument for electronics rooms and teaching desks. It includes a blank screen, fixed knobs/soft keys, four input sockets with real openings, raised handle and side pivots, feet, rear cooling grille and power-entry exterior. Waveforms, readings, probes and external equipment are absent. This static appearance model has no signal capture, display behavior, electrical measurement or calibrated performance.',['electronics','oscilloscope','education','オシロスコープ'])

def bench_vise():
 p=pal()
 cyl('Vise circular swivel foot',(0,0,.030),.103,.043,p['paint'],v=48,b=.005)
 cyl('Vise upper swivel bearing',(0,0,.061),.080,.024,p['dark'],v=40,b=.002)
 for i in range(3):
  a=i*math.tau/3+math.pi/2;x=.100*math.cos(a);y=.100*math.sin(a);sleeve('Real open vise mounting ear',(x,y,.026),.026,.011,.030,p['paint'],v=28)
 box('Vise slide guide housing',(.025,0,.112),(.180,.102,.091),p['paint'],.011)
 box('Vise fixed jaw upright',(.080,0,.169),(.054,.123,.107),p['paint'],.008)
 box('Vise fixed hardened jaw',(.049,0,.200),(.015,.148,.054),p['steel'],.003)
 box('Vise moving jaw upright',(-.119,0,.168),(.052,.123,.108),p['paint'],.008)
 box('Vise moving hardened jaw',(-.087,0,.200),(.015,.148,.054),p['steel'],.003)
 for x in [.040,-.078]:
  for z in [.184,.194,.204,.214]:box('Jaw-face horizontal gripping ridge',(x,0,z),(.004,.136,.003),p['bright'],.0005)
 box('Vise moving square slide',(-.042,0,.112),(.256,.055,.051),p['steel'],.004)
 rod('Vise main lead-screw exterior',(-.257,0,.111),(.126,0,.111),.011,p['dark'],24)
 # Visible helical detail on the exposed front screw, not an animated mechanism.
 pts=[]
 for i in range(161):
  a=i*math.tau/16;x=-.238+.090*i/160;pts.append((x,.012*math.cos(a),.111+.012*math.sin(a)))
 tube('Vise exposed lead-screw thread',pts,.0016,p['bright'],1)
 cyl('Vise screw handle hub',(-.266,0,.111),.023,.040,p['paint'],'X',v=28,b=.003)
 rod('Sliding vise T handle',(-.285,-.110,.111),(-.285,.110,.111),.007,p['steel'],20)
 for y in [-.114,.114]:sphere('Vise handle end stop',(-.285,y,.111),(.013,.013,.013),p['dark'],segments=16,rings=8)
 box('Small rear anvil extension',(.161,0,.129),(.109,.100,.056),p['paint'],.007)
 box('Small rear anvil metal face',(.161,0,.160),(.101,.097,.014),p['steel'],.003)
 for side in [-1,1]:
  cyl('Fixed swivel-lock screw',(side*.071,side*.043,.079),.012,.030,p['dark'],v=24,b=.002)
  rod('Swivel-lock short lever',(side*.071,side*.043,.093),(side*.109,side*.072,.093),.006,p['steel'],16)
 return ('city-swivel-bench-vise','旋回台付き平口バイス','Swivel-base bench vise','工房・学校の作業台に取り付ける平口バイス。開いた平行口金と細い把持溝、固定側と移動側の鋳物風胴体、角形スライド、露出した送りねじとT字ハンドル、小さな後部金敷、旋回台と実開口の取付耳・固定レバーを造形。丸管用三脚バイスとは異なる机上固定の平口工具です。台・取付ボルト・加工物は含まず、締付動作や保持力の検証はありません。','A flat-jaw vise for mounting on workshop or school benches. It has open parallel jaws with fine gripping ridges, cast-style fixed/moving bodies, square slide, exposed lead screw/T handle, small rear anvil, swivel base and genuinely open mounting ears with locking levers. This bench-mounted flat-jaw tool differs from a tripod pipe vise. Bench, mounting bolts and workpiece are absent; clamping motion and holding force are not validated.',['workshop','vise','tool','バイス'])

BUILDERS=[microscope,solder_station,oscilloscope,bench_vise]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-043/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/educational_bench_instruments.py',azimuth=-55,elevation=27)
