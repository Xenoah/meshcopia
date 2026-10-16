"""Original generic site measuring, marking and inspection props. Xenoah, CC BY 4.0.
No real product, brand or third-party geometry. Static scene equipment only.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Satin metal fittings',(.40,.47,.50),.80,.34),black=mat('Dark powder coated structure',(.035,.045,.05),.28,.55),rubber=mat('Matte dark grip rubber',(.013,.019,.022),0,.80),yellow=mat('Warm safety yellow polymer',(.66,.38,.045),.1,.40),green=mat('Muted instrument green',(.10,.29,.21),.12,.40),white=mat('Ivory casing and scale marks',(.70,.74,.70),.05,.43),glass=mat('Opaque blue optical and display face',(.018,.072,.105),.42,.20),red=mat('Red control accent',(.47,.045,.025),.1,.45))
def cyl(n,p,r,d,m,axis='Z',v=28,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,d,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def screw(n,p,m,axis='Z',r=.005):
 cyl(n+' washer',p,r*1.5,.002,m,axis,12,0);q=list(p);q['XYZ'.index(axis)]+=.0025;cyl(n+' hex',q,r,.004,m,axis,6,0)
def wheel(n,x,y,z,r,w,p):
 cyl(n+' rubber tire',(x,y,z),r,w,p['rubber'],'X',32,.005)
 for s in [-1,1]:
  cyl(n+' inset hub',(x+s*w*.51,y,z),r*.65,.012,p['steel'],'X',24,.002)
  cyl(n+' central cap',(x+s*w*.65,y,z),r*.22,.014,p['black'],'X',16,.001)
def ring(n,loc,r,minor,m,axis='Z',segments=40):
 return torus(n,loc,r,minor,m,rotation=(0,math.pi/2,0) if axis=='X' else ((math.pi/2,0,0) if axis=='Y' else None),segments=segments)
def instrument():
 p=palette()
 # Each adjustable tripod leg has two upper rails, one lower slide, a real clamp and a spike.
 for i in range(3):
  a=i*math.tau/3+math.pi/6;rad=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0))
  top=rad*.105+Vector((0,0,1.18));middle=rad*.33+Vector((0,0,.47));foot=rad*.49+Vector((0,0,.035))
  for s in [-1,1]:bar('Tripod upper twin rail',top+side*.023*s,middle+side*.023*s,.023,.029,p['yellow'])
  bar('Tripod telescoping lower leg',middle,foot,.032,.028,p['steel'])
  box('Tripod lower clamp',middle,(.075,.052,.055),p['black'],.006,rot=(0,0,a))
  lever=middle+rad*.043;bar('Clamp toggle lever',lever,lever+Vector((0,0,.066)),.014,.017,p['red'])
  rod('Ground spike',foot,rad*.495+Vector((0,0,0)),.012,p['steel'],16)
  box('Foot pressure tab',rad*.48+Vector((0,0,.075)),(.084,.043,.016),p['black'],.002,rot=(0,0,a))
  rod('Tripod top pivot',top-side*.045,top+side*.045,.017,p['steel'],20)
  rod('Tripod spread limiter',rad*.18+Vector((0,0,.96)),(0,0,.88),.009,p['black'],16)
 cyl('Tripod head plate',(0,0,1.20),.148,.045,p['steel'],v=40,b=.004)
 cyl('Instrument leveling base',(0,0,1.245),.106,.055,p['black'],v=40,b=.003)
 for i in range(3):
  a=i*math.tau/3;cyl('Leveling screw',(math.cos(a)*.087,math.sin(a)*.087,1.28),.024,.027,p['rubber'],v=20,b=.002)
 cyl('Azimuth bearing base',(0,0,1.313),.116,.047,p['green'],v=40,b=.006)
 box('Instrument lower bridge',(0,0,1.364),(.255,.17,.075),p['green'],.018)
 for x in [-.103,.103]:
  box('Instrument telescope trunnion tower',(x,.012,1.496),(.071,.15,.23),p['green'],.015)
  cyl('Telescope pivot',(x*1.34,0,1.534),.042,.035,p['black'],'X',28,.003)
  cyl('Fine aiming knob',(x*1.54,-.018,1.478),.023,.027,p['rubber'],'X',20,.002)
 cyl('Telescope barrel',(0,-.015,1.542),.066,.245,p['white'],'Y',40,.005)
 cyl('Objective outer barrel',(0,-.15,1.542),.073,.052,p['black'],'Y',40,.003)
 ring('Objective protective rim',(0,-.18,1.542),.057,.009,p['black'],'Y',40)
 cyl('Recessed objective lens',(0,-.178,1.542),.052,.004,p['glass'],'Y',36,0)
 cyl('Rear eyepiece barrel',(0,.129,1.542),.036,.055,p['black'],'Y',28,.002)
 cyl('Eyepiece rubber cup',(0,.165,1.542),.042,.022,p['rubber'],'Y',28,.003)
 cyl('Eyepiece dark face',(0,.178,1.542),.027,.003,p['glass'],'Y',24,0)
 box('Front control housing',(0,-.112,1.397),(.193,.036,.091),p['black'],.008)
 box('Blank instrument display',(-.025,-.133,1.408),(.105,.004,.046),p['glass'],.002)
 for x in [.047,.070]:
  for z in [1.378,1.398,1.418]:box('Control key',(x,-.135,z),(.013,.006,.012),p['white'],.001)
 for x in [-.11,.11]:bar('Carrying handle upright',(x,.014,1.615),(x,.014,1.695),.026,.029,p['black'])
 bar('Open carrying handle bridge',(-.11,.014,1.695),(.11,.014,1.695),.029,.033,p['black'])
 return ('city-tripod-survey-instrument','三脚付き測量器','Tripod-mounted survey instrument','建設現場や道路測量のシーン向けの据置測量器。伸縮脚のレールと固定レバー、整準ねじ、左右の支持塔、望遠鏡外装、対物・接眼面、操作面と開いた持ち手を造形。光学面と表示面は不透明材質で、測距・測角・水平調整や可動機構は実装していません。測量精度や現場機器としての適合は未検証。','A stationary survey-instrument prop for construction and street-survey scenes, with sliding tripod rails and clamps, leveling screws, twin trunnion towers, telescope housing, objective/eyepiece faces, controls and open carrying handle. Optical and display faces are opaque materials; distance/angle measurement, leveling and articulation are not implemented. Survey accuracy and real equipment compliance are unvalidated.',['survey','tripod','measurement','測量器'])
def measuring_wheel():
 p=palette();r=.255;z=.263
 # Open spoke wheel, not a filled cylinder. Rim is a real closed toroidal tire.
 ring('Measuring wheel tire',(0,0,z),r-.018,.026,p['rubber'],'X',56)
 ring('Wheel metal rim',(0,0,z),r-.042,.014,p['yellow'],'X',48)
 cyl('Wheel hub',(0,0,z),.050,.10,p['black'],'X',32,.003)
 for i in range(6):
  a=i*math.tau/6;bar('Measuring wheel radial spoke',(0,math.sin(a)*.035,z+math.cos(a)*.035),(0,math.sin(a)*.214,z+math.cos(a)*.214),.022,.020,p['yellow'])
 rod('Wheel axle',(-.09,0,z),(.09,0,z),.016,p['steel'],24)
 for x in [-.070,.070]:bar('Wheel fork blade',(x,0,z),(x,.025,.54),.022,.035,p['black'])
 rod('Fork bridge',(-.070,.025,.54),(.070,.025,.54),.019,p['black'],24)
 rod('Lower handle shaft',(0,.025,.54),(0,.18,.92),.018,p['steel'],24)
 rod('Upper handle shaft',(0,.18,.92),(0,.25,1.145),.016,p['steel'],24)
 cyl('Shaft folding lock',(0,.178,.91),.032,.057,p['black'],'X',24,.003)
 box('Fold lock release',(0,.157,.94),(.045,.028,.035),p['red'],.004)
 tube('Handle dogleg',[(0,.25,1.145),(0,.265,1.19),(0,.33,1.208),(0,.40,1.205)],.018,p['black'],2)
 rod('Operator grip',(0,.335,1.208),(0,.435,1.205),.026,p['rubber'],24)
 box('Mechanical counter housing',(-.083,.015,.382),(.056,.128,.076),p['black'],.009)
 box('Blank counter window',(-.083,-.052,.39),(.043,.006,.030),p['glass'],.003)
 for x in [-.097,-.084,-.071]:box('Unnumbered counter drum divider',(x,-.056,.39),(.002,.003,.027),p['white'],0)
 cyl('Counter reset knob',(-.124,.012,.39),.018,.022,p['red'],'X',20,.002)
 rod('Counter drive link',(-.084,.018,.30),(-.084,.018,.36),.009,p['steel'],16)
 tube('Parking stand',[(.06,.035,.48),(.075,.24,.06),(.075,.31,.018),(-.075,.31,.018),(-.075,.24,.06),(-.06,.035,.48)],.012,p['black'],2)
 for x in [-.075,.075]:box('Stand rubber shoe',(x,.30,.017),(.032,.067,.028),p['rubber'],.004)
 return ('city-measuring-wheel','距離測定用の歩行輪','Walking distance measuring wheel','歩道・外構の距離測定場面に置く手押し測定輪。開いたスポーク、ゴム輪、フォーク、折り畳みロック風の継手、計数器外装、グリップと自立スタンドを造形。数字・距離スケール、回転・折り畳み・計測機能はなく、校正値や測定精度を示すものではありません。','A push-along measuring-wheel prop for sidewalk and landscape layout scenes, with open spokes, rubber tire, fork, folding-lock exterior, counter housing, grip and parking stand. No digits, distance scale, wheel rotation, folding or measuring behavior is included; this does not represent calibrated measurement accuracy.',['measurement','wheel','survey','測定輪'])
def line_marker():
 p=palette()
 # A compact aerosol striping trolley, not an engine-powered pump cart.
 for x in [-.17,.17]:
  bar('Marker side chassis',(x,-.24,.11),(x,.25,.11),.028,.030,p['yellow'])
  for y in [-.21,.23]:wheel('Striping trolley wheel',x*1.18,y,.104,.104,.047,p)
 for y in [-.21,.23]:rod('Trolley axle',(-.22,y,.104),(.22,y,.104),.011,p['steel'],20)
 for y in [-.15,.16]:bar('Trolley cross brace',(-.17,y,.12),(.17,y,.12),.028,.024,p['black'])
 for x in [-.115,.115]:
  bar('Can holder upright',(x,-.03,.14),(x,-.03,.48),.024,.025,p['yellow'])
  box('Holder lateral clasp',(x*.74,-.03,.30),(.057,.072,.023),p['black'],.004)
 # Inverted unbranded can in an open holder, valve near the ground.
 cyl('Aerosol can body',(0,-.03,.335),.060,.235,p['white'],v=40,b=.008)
 cyl('Can upper rolled seam',(0,-.03,.457),.060,.009,p['steel'],v=36,b=.001)
 cyl('Can lower shoulder',(0,-.03,.207),.046,.024,p['steel'],v=32,b=.006)
 cyl('Downward nozzle',(0,-.03,.185),.010,.024,p['red'],v=20,b=.002)
 ring('Can securing collar',(0,-.03,.374),.064,.007,p['black'],segments=40)
 bar('Top can retainer',(-.112,-.03,.48),(.112,-.03,.48),.025,.028,p['yellow'])
 rod('Can clamp screw',(0,-.03,.49),(0,-.03,.462),.006,p['steel'],16)
 cyl('Can clamp thumbwheel',(0,-.03,.507),.023,.014,p['black'],v=20,b=.002)
 # Adjustable front masking blades leave a real central spray gap.
 for x in [-.055,.055]:
  box('Striping width mask',(x,-.028,.074),(.014,.195,.100),p['steel'],.003)
  box('Mask sliding bracket',(x,.05,.14),(.067,.028,.018),p['black'],.002)
  screw('Mask adjuster',(x,.05,.153),p['steel'],r=.006)
 for x in [-.13,.13]:tube('Operator handle side',[(x,.20,.14),(x,.36,.60),(x,.53,.94)],.016,p['black'],2)
 rod('Handle transverse grip',(-.17,.53,.94),(.17,.53,.94),.024,p['rubber'],24)
 rod('Spray trigger lever',(-.095,.488,.91),(.095,.488,.91),.010,p['red'],20)
 tube('Fixed trigger cable',[(.09,.49,.91),(.145,.37,.65),(.15,.20,.36),(.065,.02,.22),(.02,-.03,.193)],.0035,p['black'],1)
 box('Trigger actuator bracket',(.032,-.03,.193),(.047,.025,.015),p['black'],.002)
 return ('city-aerosol-line-marking-trolley','スプレー式ライン引き台車','Aerosol line-marking trolley','駐車区画や園路のライン施工場面向けの小型台車。倒立スプレー缶の外装、開いた保持枠、下向きノズル、幅調整用マスク板、四輪の車台、トリガーと固定ケーブルを造形。缶は無地で、中身・塗膜・噴霧・可動はありません。実際の施工寸法や薬剤使用、安全性能を定める設計ではありません。','A compact trolley for parking-bay and park-path striping scenes, with an inverted unbranded aerosol-can exterior, open holder, downward nozzle, adjustable-mask exteriors, four-wheel frame, trigger and fixed cable. Contents, painted lines, spraying and movement are absent. This is not a design specifying real application dimensions, chemical use or safety performance.',['line-marking','trolley','maintenance','ライン引き'])
def pipe_camera():
 p=palette()
 # Open support cage and coiled inspection push cable, distinct from a water hose reel.
 for x in [-.18,.18]:
  tube('Reel support foot',[(x,-.23,.025),(x,.20,.025),(x,.23,.10),(x,.20,.34),(x,.05,.51)],.014,p['black'],2)
  rod('Reel upright',(x,-.19,.025),(x,.02,.31),.016,p['black'],20)
 for y in [-.20,.18]:rod('Reel foot crossbar',(-.18,y,.025),(.18,y,.025),.014,p['black'],20)
 for x in [-.18,.18]:box('Reel rubber foot',(x,-.19,.018),(.048,.074,.032),p['rubber'],.005)
 center=(0,0,.298)
 rod('Reel central axle',(-.205,0,.298),(.205,0,.298),.018,p['steel'],24)
 cyl('Cable drum core',center,.164,.24,p['green'],'X',36,.004)
 for x in [-.147,.147]:
  ring('Open reel guard rim',(x,0,.298),.245,.010,p['steel'],'X',48)
  cyl('Reel hub plate',(x,0,.298),.055,.018,p['black'],'X',24,.002)
  for i in range(6):
   a=i*math.tau/6;rod('Reel guard spoke',(x,math.sin(a)*.049,.298+math.cos(a)*.049),(x,math.sin(a)*.235,.298+math.cos(a)*.235),.006,p['steel'],12)
 # One continuous helical cable is explicit geometry, not a texture or many counted assets.
 points=[]
 for i in range(321):
  t=i/320;ang=t*math.tau*8;points.append((-.106+.212*t,.174*math.sin(ang),.298+.174*math.cos(ang)))
 tube('Fixed coiled inspection push cable',points,.011,p['yellow'],2)
 rod('Reel carry handle',(-.18,.05,.51),(.18,.05,.51),.022,p['rubber'],24)
 # Hinged monitor held above rear support. Screen is explicitly opaque/inactive.
 for x in [-.13,.13]:bar('Display support',(x,.20,.34),(x,.15,.60),.025,.024,p['black'])
 box('Monitor outer enclosure',(0,.145,.65),(.335,.062,.236),p['black'],.013)
 box('Inactive inspection screen',(0,.111,.675),(.278,.007,.145),p['glass'],.005)
 for x in [-.10,-.05,0,.05,.10]:box('Monitor control key',(x,.107,.562),(.021,.008,.015),p['white'],.002)
 for x in [-.14,.14]:cyl('Monitor hinge',(x,.145,.526),.023,.045,p['steel'],'X',20,.002)
 box('Monitor battery cover',(0,.180,.65),(.19,.015,.13),p['green'],.006)
 for x in [-.125,.125]:
  for z in [.57,.73]:screw('Monitor rear screw',(x,.183,z),p['steel'],'Y',.004)
 tube('Monitor fixed signal lead',[(.14,.17,.56),(.19,.19,.47),(.21,.06,.31),(.205,0,.298)],.006,p['black'],2)
 # Exposed cable end and a lens-bearing inspection probe parked on the front rail.
 lead=[]
 for controls in [[(.106,0,.472),(.16,-.08,.47),(.15,-.20,.38),(.13,-.24,.26)],[(.13,-.24,.26),(.11,-.27,.15),(.0,-.23,.12),(-.10,-.23,.12)]]:
  a,b,c,d=[Vector(v) for v in controls]
  for i in range(21):
   if lead and i==0:continue
   t=i/20;lead.append(tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d))
 tube('Parked probe lead',lead,.009,p['yellow'],2)
 rod('Probe rear strain relief',(-.10,-.23,.12),(-.15,-.23,.12),.014,p['rubber'],20)
 cyl('Metal inspection probe',(-.19,-.23,.12),.025,.085,p['steel'],'X',32,.003)
 cyl('Probe lens face',(-.236,-.23,.12),.015,.004,p['glass'],'X',24,0)
 for i in range(6):
  a=i*math.tau/6;cyl('Unlit probe LED',(-.237,-.23+.019*math.sin(a),.12+.019*math.cos(a)),.0035,.004,p['white'],'X',10,0)
 box('Probe parking clip',(-.19,-.217,.09),(.05,.035,.035),p['black'],.004)
 return ('city-pipe-inspection-camera-reel','管内点検カメラリール','Pipe inspection camera reel','配管点検や施設保守のシーン用の携帯カメラリール。開いた巻枠、連続した固定ケーブル、持ち手、背面バッテリー外装付き表示器、信号線とレンズ面のある保管状態のプローブを造形。画面とレンズは不透明・非発光で、映像・照明・ケーブル展開や防水性能は含みません。現物の点検装置設計ではありません。','A portable inspection-camera reel for pipe-survey and facility-maintenance scenes, with an open cage, continuous fixed coil, carrying handle, monitor with rear battery exterior, signal lead and parked lens-bearing probe. Display and optics are opaque and nonemissive; video, lighting, cable deployment and waterproof performance are not included. This is not a real inspection-device design.',['inspection','camera','reel','pipe','点検カメラ'])
BUILDERS=[instrument,measuring_wheel,line_marker,pipe_camera]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-020/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/site_survey_tools.py',azimuth=-55,elevation=24)
