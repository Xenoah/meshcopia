"""Original washroom interior fixtures for Xenoah, CC BY 4.0.
Generic static visualization models, not real plumbing or product designs.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():return dict(ceramic=mat('Warm white glazed ceramic',(.75,.78,.76),.05,.23),seat=mat('Ivory sanitary polymer',(.72,.75,.70),0,.35),steel=mat('Satin chrome fittings',(.48,.53,.55),.9,.24),black=mat('Dark gasket and recess',(.015,.024,.026),0,.65),waterless=mat('Empty drain interior',(.035,.045,.048),.15,.65),blue=mat('Blank blue sensor glass',(.025,.11,.16),.25,.25))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.002):
 o=cylinder(n,p,r,d,m,v,bevel=(0 if r<.005 else b))
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def oval_loft(n,profile,m,segments=64,smooth=True):
 # Profile: x-radius, y-radius, z, y-center. A closed path gives a true hollow shell.
 verts=[];rings=[]
 for rx,ry,z,cy in profile:
  if rx==0 and ry==0:rings.append([len(verts)]);verts.append((0,cy,z))
  else:rings.append(list(range(len(verts),len(verts)+segments)));verts.extend((rx*math.cos(i*math.tau/segments),cy+ry*math.sin(i*math.tau/segments),z) for i in range(segments))
 faces=[]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  if len(a)==1 and len(b)==1:continue
  for i in range(segments):
   j=(i+1)%segments
   if len(a)==1:faces.append((a[0],b[i],b[j]))
   elif len(b)==1:faces.append((a[i],b[0],a[j]))
   else:faces.append((a[i],b[i],b[j],a[j]))
 return mesh(n,verts,faces,m,0,smooth)
def oval_ring(n,rx,ry,z,cy,r,m):
 verts=[];faces=[];steps=64;cross=12
 for i in range(steps):
  a=i*math.tau/steps;normal=Vector((math.cos(a)/rx,math.sin(a)/ry,0)).normalized();center=Vector((rx*math.cos(a),cy+ry*math.sin(a),z))
  for j in range(cross):
   b=j*math.tau/cross;v=center+normal*(r*math.cos(b))+Vector((0,0,r*math.sin(b)));verts.append(tuple(v))
 for i in range(steps):
  for j in range(cross):faces.append((i*cross+j,((i+1)%steps)*cross+j,((i+1)%steps)*cross+(j+1)%cross,i*cross+(j+1)%cross))
 return mesh(n,verts,faces,m,0,True)
def screw(n,p,m,axis='Z'):
 cyl(n+' washer',p,.010,.003,m,axis,20,.0003);q=list(p);q['XYZ'.index(axis)]+=.003;cyl(n+' head',q,.006,.005,m,axis,6,.0003)
def drain(n,x,y,z,p,r=.032):
 cyl(n+' rim',(x,y,z),r,.009,p['steel'],v=40,b=.001)
 cyl(n+' empty inset',(x,y,z+.005),r*.80,.003,p['waterless'],v=32,b=.0002)
 for xx in [-.012,0,.012]:box(n+' strainer bar',(x+xx,y,z+.008),(.004,r*1.30,.004),p['steel'],.0006)

def toilet():
 p=palette()
 oval_loft('Toilet pedestal skirt',[(0,0,0,.08),(.135,.205,0,.08),(.14,.21,.025,.08),(.13,.19,.10,.075),(.11,.15,.19,.05),(.10,.14,.205,.03),(0,0,.205,.03)],p['ceramic'])
 oval_loft('Hollow ceramic toilet bowl',[(0,0,.18,.02),(.09,.13,.18,.02),(.15,.21,.28,-.01),(.205,.28,.39,-.075),(.219,.291,.435,-.08),(.21,.282,.45,-.08),(.18,.245,.45,-.08),(.162,.224,.405,-.08),(.13,.18,.33,-.065),(.075,.11,.278,-.02),(.05,.067,.273,-.01),(.041,.055,.258,-.006),(.038,.050,.224,.012),(0,0,.219,.012)],p['ceramic'])
 oval_loft('Recessed empty toilet outlet',[(0,0,.2205,.012),(.032,.043,.2205,.012),(.036,.048,.224,.012),(.034,.046,.227,.012),(0,0,.227,.012)],p['waterless'],48)
 # Thin oval seat rim with a genuine open center, plus open raised lid.
 oval_ring('Open-center toilet seat',.198,.263,.466,-.08,.019,p['seat'])
 lid=oval_loft('Raised oval lid',[(0,0,-.012,0),(.19,.245,-.012,0),(.218,.275,-.004,0),(.22,.277,.008,0),(.21,.266,.018,0),(0,0,.018,0)],p['seat']);lid.rotation_euler[0]=math.pi/2;lid.location=(0,.203,.736)
 for x in [-.11,.11]:
  cyl('Seat hinge barrel',(x,.19,.467),.021,.085,p['steel'],'X',28,.002)
  box('Seat hinge bracket',(x,.215,.438),(.044,.065,.035),p['steel'],.006)
 box('Bowl rear support bridge',(0,.235,.359),(.33,.23,.065),p['ceramic'],.018)
 box('Toilet cistern',(0,.34,.586),(.40,.205,.46),p['ceramic'],.035)
 box('Cistern removable lid',(0,.34,.826),(.425,.224,.038),p['ceramic'],.015)
 for x in [-.035,.035]:cyl('Unmarked dual flush button',(x,.335,.852),.027,.012,p['steel'],v=32,b=.002)
 cyl('Cistern supply fitting',(.154,.36,.32),.018,.08,p['steel'],v=28,b=.002)
 for x in [-.115,.115]:
  box('Floor fixing cover',(x,.06,.05),(.035,.064,.040),p['seat'],.009)
 cyl('Rear waste connector',(0,.265,.16),.050,.125,p['black'],'Y',40,.003)
 return('city-floor-flush-toilet','床置きタンク式洋便器','Floor-mounted cistern toilet','公共施設や店舗のトイレ内装用の洋便器。見える凹型排出口付きの中空の陶器鉢、開口のある便座、上げた蓋、ヒンジ、給水タンクと背面接続外装を造形。床・壁、水・汚物、内部のトラップ・配管、洗浄や蓋開閉はなく、衛生・給排水基準の適合は未検証。','A cistern toilet for public-building and retail washroom interiors, with a hollow ceramic bowl and visible recessed outlet, open-center seat, raised lid, hinges, cistern and rear fitting exteriors. Floor, wall, water, waste, internal trap/plumbing, flushing and lid movement are absent; hygiene and plumbing-standard compliance are unvalidated.',['toilet','cistern','washroom','ceramic','便器'])

def urinal():
 p=palette()
 # Back panel and basin are independent closed ceramic solids with an open cavity.
 box('Rounded urinal back body',(0,.065,.47),(.39,.14,.61),p['ceramic'],.050)
 oval_loft('Open urinal collection bowl',[(0,0,.09,-.045),(.075,.09,.09,-.045),(.14,.16,.14,-.075),(.199,.205,.25,-.08),(.203,.21,.30,-.08),(.188,.195,.317,-.08),(.168,.173,.312,-.08),(.145,.146,.25,-.08),(.087,.09,.175,-.06),(0,0,.166,-.05)],p['ceramic'])
 box('Inset glazed splash panel',(0,-.012,.48),(.295,.025,.39),p['ceramic'],.025)
 drain('Urinal drain',0,-.055,.179,p,.031)
 # Exposed top flush sensor/valve is a generic nonfunctional shape.
 cyl('Flush water riser',(0,.05,.822),.018,.10,p['steel'],v=28,b=.002)
 box('Flush sensor valve',(0,.04,.912),(.105,.094,.105),p['steel'],.016)
 box('Blank proximity sensor',(0,-.011,.922),(.056,.009,.035),p['blue'],.006)
 cyl('Wall water inlet',(0,.11,.913),.020,.08,p['steel'],'Y',28,.002)
 cyl('Water inlet escutcheon',(0,.153,.913),.044,.017,p['steel'],'Y',40,.003)
 # Rear mounting rails, brackets and short empty waste outlet, no wall supplied.
 for x in [-.13,.13]:
  box('Urinal rear fixing rail',(x,.153,.48),(.035,.040,.38),p['steel'],.005)
  for z in [.32,.64]:screw('Rear bracket fastening',(x,.177,z),p['black'],'Y')
 cyl('Urinal rear waste stub',(0,.095,.17),.041,.12,p['black'],'Y',36,.002)
 cyl('Waste stub flange',(0,.159,.17),.057,.013,p['steel'],'Y',36,.002)
 return('city-wall-hung-urinal','壁掛け式の小便器','Wall-hung urinal fixture','公共トイレの壁面に配置する小便器。開いた受鉢、釉薬調の背板、排水口、センサー風の給水部、背面固定金具と短い排水接続部を造形。壁・水・内部配管や洗浄・検知動作は含みません。取付高さと壁離れはシーンで調整し、衛生や給排水基準への適合は未検証。','A wall-hung urinal for public washrooms, with an open collection bowl, glazed-looking splash back, drain, sensor-like flush fitting, rear mounting rails and short waste connector. Wall, water, internal plumbing, flushing and sensing behavior are absent. Adjust installation height and wall offset in the scene; hygiene and plumbing-standard compliance are unvalidated.',['urinal','washroom','wall-mounted','ceramic','小便器'])

def pedestal_basin():
 p=palette()
 oval_loft('Tapered basin pedestal',[(0,0,0,.07),(.135,.14,0,.07),(.14,.145,.025,.07),(.12,.12,.09,.07),(.085,.087,.52,.075),(.105,.105,.67,.065),(.145,.13,.70,.045),(0,0,.70,.045)],p['ceramic'])
 oval_loft('Open ceramic washbasin',[(0,0,.655,-.02),(.13,.13,.655,-.02),(.22,.18,.72,-.035),(.295,.226,.83,-.04),(.304,.235,.855,-.04),(.294,.225,.875,-.04),(.269,.201,.875,-.04),(.245,.18,.83,-.04),(.17,.12,.75,-.04),(.06,.05,.713,-.04),(0,0,.710,-.04)],p['ceramic'])
 box('Faucet rear ledge',(0,.174,.852),(.43,.12,.050),p['ceramic'],.014)
 cyl('Faucet base escutcheon',(0,.175,.886),.037,.018,p['steel'],v=40,b=.003)
 cyl('Mixer tap body',(0,.175,.94),.026,.11,p['steel'],v=36,b=.005)
 tube('Curved mixer spout',[(0,.174,.976),(0,.165,1.005),(0,.14,1.025),(0,.09,1.03),(0,.035,1.01),(0,.025,.993)],.016,p['steel'],3)
 cyl('Tap aerator',(0,.025,.986),.018,.019,p['steel'],v=28,b=.002)
 cyl('Aerator dark outlet',(0,.025,.975),.0125,.002,p['waterless'],v=28,b=0)
 for x in [-.006,0,.006]:box('Aerator outlet strainer',(x,.025,.9735),(.0017,.018,.0015),p['steel'],.0002)
 tube('Single mixer lever',[(0,.18,1.003),(.045,.18,1.019),(.09,.18,1.019)],.010,p['steel'],2)
 drain('Basin waste drain',0,-.04,.723,p,.032)
 box('Unfilled overflow slot',(0,.148,.825),(.055,.006,.011),p['waterless'],.003)
 # The pedestal is closed; concealed plumbing and inspection access are omitted.
 cyl('Visible drain neck',(0,.10,.661),.026,.095,p['steel'],v=28,b=.002)
 for x in [-.19,.19]:box('Basin wall support',(x,.21,.78),(.055,.06,.07),p['steel'],.005)
 return('city-pedestal-washbasin','陶器製のペデスタル洗面台','Ceramic pedestal washbasin','建物の洗面室に置く据置きの陶器洗面台。曲面の脚と中空の鉢、吐水面付きのシングルレバー混合水栓、排水口、背面支持部を備えます。仮設手洗い装置とは別の固定内装器具です。水、完全な給排水系統、通水・温度調節はなく、衛生・施工基準への適合は未検証。','A fixed ceramic washbasin for building washrooms, with a curved pedestal, hollow basin, single-lever mixer-shaped faucet with outlet face, drain and rear supports. This is a fixed interior fixture rather than a portable handwash machine. Water, complete supply/waste plumbing, flow and temperature control are absent; hygiene and installation-standard compliance are unvalidated.',['basin','sink','washroom','pedestal','洗面台'])

def shower_set():
 p=palette()
 # Wall-mounted exposed shower set; geometry is modeled at plausible mounting heights,
 # then common places its lowest part at zero for scene placement.
 for x in [-.15,.15]:
  cyl('Wall mixing-valve escutcheon',(x,.12,.95),.045,.021,p['steel'],'Y',40,.003)
  cyl('Mixing valve wall elbow',(x,.065,.95),.021,.12,p['steel'],'Y',28,.002)
 cyl('Thermostatic-style mixing bar',(0,.0,.95),.035,.37,p['steel'],'X',40,.004)
 for x in [-.198,.198]:
  cyl('Mixing-bar end control',(x,0,.95),.040,.043,p['steel'],'X',32,.003)
  for a in range(8):
   an=a*math.tau/8;rod('Control grip groove',(x-.011,.038*math.sin(an),.95+.038*math.cos(an)),(x+.011,.038*math.sin(an),.95+.038*math.cos(an)),.002,p['black'],8)
 riser=[(0,.032,.975),(0,.032,1.85)]
 riser.extend((0,-.118+.15*math.cos(i*math.pi/24),1.85+.15*math.sin(i*math.pi/24)) for i in range(1,13))
 riser.append((0,-.25,2.0));riser.extend((0,-.25-.03*math.sin(i*math.pi/16),1.97+.03*math.cos(i*math.pi/16)) for i in range(1,9))
 tube('Overhead shower riser',riser,.014,p['steel'],2)
 for z in [1.20,1.75]:
  cyl('Riser wall stand-off',(0,.09,z),.019,.12,p['steel'],'Y',28,.002)
  cyl('Riser wall flange',(0,.157,z),.035,.016,p['steel'],'Y',36,.002)
 cyl('Rain head upper shell',(0,-.28,1.958),.12,.025,p['steel'],v=64,b=.006)
 cyl('Rain head lower insert',(0,-.28,1.940),.109,.012,p['black'],v=56,b=.002)
 for i in range(-4,5):
  for j in range(-4,5):
   x=i*.023;y=j*.023
   if x*x+y*y<.092**2:cyl('Rain head nozzle',(x,-.28+y,1.931),.0033,.008,p['seat'],v=10,b=.0004)
 # Slide rail and parked handheld shower with a fixed flexible hose.
 cyl('Hand shower slide rail',(.18,.035,1.40),.010,.63,p['steel'],v=28,b=.001)
 for z in [1.085,1.715]:
  box('Slide rail end bracket',(.18,.07,z),(.045,.10,.038),p['steel'],.007)
  cyl('Slide wall flange',(.18,.126,z),.030,.013,p['steel'],'Y',32,.002)
 cyl('Sliding shower holder',(.18,.02,1.46),.024,.06,p['steel'],v=28,b=.003)
 rod('Hand shower support peg',(.18,.02,1.46),(.18,-.055,1.46),.012,p['steel'],20)
 rod('Handheld shower handle',(.18,-.035,1.40),(.18,-.085,1.58),.019,p['steel'],28)
 head=cyl('Handheld shower head',(.18,-.094,1.625),.046,.028,p['steel'],'Y',40,.006)
 cyl('Handheld spray face',(.18,-.112,1.625),.039,.008,p['black'],'Y',32,.001)
 for i in range(8):
  a=i*math.tau/8;cyl('Hand shower nozzle',(.18+.026*math.cos(a),-.118,1.625+.026*math.sin(a)),.003,.006,p['seat'],'Y',10,.0003)
 hose=[(.09,0,.90),(.09,-.09,.50)]
 for i in range(1,25):
  t=i*math.pi/24;hose.append((-.025+.115*math.cos(t),-.09,.50-.115*math.sin(t)))
 hose.append((-.14,-.09,.95))
 a,b,c,d=[Vector(v) for v in [(-.14,-.09,.95),(-.14,-.09,1.15),(.10,-.05,1.20),(.18,-.05,1.405)]]
 for i in range(1,17):
  t=i/16;hose.append(tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d))
 tube('Fixed hanging shower hose',hose,.011,p['steel'],2)
 for i in range(1,len(hose)-1,3):
  tangent=Vector(hose[i+1])-Vector(hose[i-1]);o=torus('Hose helix ring',hose[i],.011,.002,p['black'],segments=16);o.rotation_euler=tangent.to_track_quat('Z','Y').to_euler()
 for pt in [hose[0],hose[-1]]:cyl('Hose end coupling',pt,.016,.034,p['steel'],v=24,b=.002)
 return('city-wall-shower-set','壁付けの露出型シャワーセット','Wall-mounted exposed shower set','公共浴室やプール更衣室に配置する露出配管型シャワー。混合栓風の操作バー、上部散水ヘッド、スライドレール、手持ちヘッドと固定ホースを造形。緊急洗眼シャワーとは用途・構造が異なる浴室器具です。壁・水・内部弁、温度・流量制御や可動はなく、安全・衛生基準への適合は未検証。最低点基準から取付高さと壁離れを調整してください。','An exposed shower set for public bathing rooms and pool changing facilities, with mixer-shaped control bar, overhead head, slide rail, handheld head and fixed hose. Its bathing purpose and construction differ from an emergency eyewash shower. Wall, water, internal valves, temperature/flow control and articulation are absent; safety and hygiene compliance are unvalidated. Adjust mounting height and wall offset from its lowest-point placement origin.',['shower','washroom','bathing','wall-mounted','シャワー'])

BUILDERS=[toilet,urinal,pedestal_basin,shower_set]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-016/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/washroom_fixtures.py',azimuth=-55,elevation=24)
