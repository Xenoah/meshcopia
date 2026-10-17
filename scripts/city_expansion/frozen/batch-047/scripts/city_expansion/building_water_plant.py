"""Original building water-plant components. Xenoah, CC BY 4.0.
Static assemblies; flow, pressure, thermal and measurement functions are absent.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(paint=mat('Blue protective equipment finish',(.055,.23,.34),.20,.39),steel=mat('Satin machined steel',(.47,.53,.57),.78,.31),bright=mat('Bright fastener metal',(.65,.70,.73),.84,.27),dark=mat('Dark joint gasket',(.024,.033,.040),0,.73),brass=mat('Warm cast bronze',(.40,.26,.095),.73,.34),white=mat('Plain meter dial',(.79,.81,.77),0,.55),red=mat('Red vessel enamel',(.43,.055,.038),.18,.37))
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
def frame(n,w,h,t,d,p,m,bev=.002):
 vs=[]
 for ww,hh,y in [(w,h,-d/2),(w,h,d/2),(w-2*t,h-2*t,d/2),(w-2*t,h-2*t,-d/2)]:vs.extend([(-ww/2,y,-hh/2),(ww/2,y,-hh/2),(ww/2,y,hh/2),(-ww/2,y,hh/2)])
 fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)];o=mesh(n,vs,fs,m,bev);o.location=p
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 return o

def flange(n,p,ro,ri,d,m,axis='X',bolts=8):
 o=sleeve(n,p,ro,ri,d,m,axis,v=40)
 for i in range(bolts):
  a=i*math.tau/bolts+math.pi/bolts;r=(ro+ri)/2
  q=Vector(p)
  if axis=='X':q.y+=r*math.cos(a);q.z+=r*math.sin(a);q.x+=(1 if p[0]>=0 else -1)*d*.62
  elif axis=='Y':q.x+=r*math.cos(a);q.z+=r*math.sin(a);q.y-=d*.62
  else:q.x+=r*math.cos(a);q.y+=r*math.sin(a);q.z+=d*.62
  cyl(n+' separate fastener',q,.011,.012,m,axis,v=6,b=.001)
 return o

def bore_body(name,loc,scale,r,material):
 # Analytic closed outer bulb and circular bore avoid Boolean seam/order instability.
 sx,sy,sz=scale;limit=sx*math.sqrt(1-(r*1.10/min(sy,sz))**2);N=48;rows=24;vs=[]
 for j in range(rows+1):
  x=-limit+2*limit*j/rows;f=math.sqrt(1-(x/sx)**2)
  vs.extend((x,sy*f*math.cos(i*math.tau/N),sz*f*math.sin(i*math.tau/N)) for i in range(N))
 outer=(rows+1)*N
 for x in [-limit,limit]:vs.extend((x,r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N)) for i in range(N))
 fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(rows) for i in range(N)]
 fs.extend((outer+i,outer+N+i,outer+N+(i+1)%N,outer+(i+1)%N) for i in range(N))
 fs.extend((i,outer+i,outer+(i+1)%N,(i+1)%N) for i in range(N))
 fs.extend((rows*N+i,rows*N+(i+1)%N,outer+N+(i+1)%N,outer+N+i) for i in range(N))
 o=mesh(name,vs,fs,material);o.location=loc
 for face in o.data.polygons:face.use_smooth=face.index<(rows+1)*N
 return o

def gate_valve():
 p=pal();bore_body('Gate valve cast rounded chamber',(0,0,.278),(.139,.122,.159),.075,p['paint'])
 for side in [-1,1]:
  sleeve('Gate valve open pipe neck',(side*.156,0,.278),.096,.075,.119,p['paint'],'X',v=40)
  flange('Gate valve open bolted flange',(side*.221,0,.278),.153,.075,.033,p['paint'],'X')
  box('Valve support sole',(side*.068,0,.018),(.100,.145,.025),p['paint'],.006)
  bar('Valve cast support foot',(side*.068,0,.030),(side*.065,0,.150),.042,.064,p['paint'],.005)
 cyl('Gate valve rising bonnet neck',(0,0,.430),.062,.188,p['paint'],v=40,b=.005)
 flange('Gate valve bonnet flange',(0,0,.531),.096,.020,.037,p['paint'],'Z',bolts=6)
 for x in [-.069,.069]:bar('Open valve yoke upright',(x,0,.544),(x,0,.752),.032,.045,p['paint'],.003)
 box('Valve yoke upper bridge',(0,0,.755),(.181,.063,.036),p['paint'],.005)
 cyl('Valve visible rising stem',(0,0,.680),.016,.296,p['steel'],v=28,b=.001)
 pts=[]
 for i in range(145):
  a=i*math.tau/16;pts.append((.017*math.cos(a),.017*math.sin(a),.591+.111*i/144))
 tube('Valve stem exposed thread',pts,.0017,p['bright'],1)
 cyl('Handwheel center hub',(0,0,.817),.034,.043,p['paint'],v=28,b=.003)
 ring('Valve handwheel rim',(0,0,.827),.158,.012,p['paint'],v=48)
 for i in range(4):
  a=i*math.tau/4;rod('Valve handwheel spoke',(.021*math.cos(a),.021*math.sin(a),.819),(.153*math.cos(a),.153*math.sin(a),.827),.009,p['paint'],20)
 cyl('Handwheel center nut',(0,0,.844),.019,.013,p['bright'],v=6,b=.001)
 return ('city-flanged-gate-valve','フランジ付きハンドル式ゲート弁','Flanged handwheel gate valve','建物の機械室・配管展示に置く無銘のゲート弁。両端の実開口フランジ、丸い鋳物風胴体、ボンネットと開いたヨーク、外に見えるねじ付き弁棒、四本スポークの手輪、小さな支持脚を造形。外部配管は含まず、接続位置に合わせて配置してください。内部ゲート機構、開閉、流量・圧力性能や配管規格への適合は検証していません。','An unbranded gate-valve exterior for building plant rooms and pipework displays. It has genuinely open end flanges, rounded cast-style body, bonnet/open yoke, exposed threaded stem, four-spoke handwheel and small support feet. External piping is absent; position it to suit your scene connections. Internal gate mechanics, operation, flow/pressure performance and piping-standard compliance are not validated.',['utilities','valve','water','ゲート弁'])

def water_meter():
 p=pal();bore_body('Water meter bronze chamber',(0,0,.166),(.151,.104,.107),.054,p['brass'])
 for side in [-1,1]:
  sleeve('Meter open pipe tail',(side*.172,0,.166),.070,.054,.141,p['brass'],'X',v=40)
  flange('Meter visible end flange',(side*.252,0,.166),.107,.054,.026,p['brass'],'X',bolts=4)
  box('Meter little mounting foot',(side*.072,0,.017),(.073,.115,.027),p['brass'],.004)
  bar('Meter body foot web',(side*.072,0,.027),(side*.061,0,.091),.036,.045,p['brass'],.003)
 cyl('Meter register support neck',(0,0,.279),.052,.084,p['brass'],v=32,b=.003)
 cyl('Round meter register housing',(0,0,.325),.091,.050,p['paint'],v=40,b=.004)
 cyl('Plain opaque dial',(0,0,.353),.073,.007,p['white'],v=40,b=.001)
 ring('Meter raised register bezel',(0,0,.355),.079,.006,p['steel'],v=40)
 for i in range(24):
  a=i*math.tau/24;bar('Unnumbered static dial tick',(.058*math.cos(a),.058*math.sin(a),.358),(.066*math.cos(a),.066*math.sin(a),.358),.002,.002,p['dark'],.0003)
 rod('Single fixed decorative meter pointer',(0,0,.360),(.039,.026,.360),.002,p['dark'],16)
 cyl('Meter pointer center',(0,0,.362),.006,.005,p['steel'],v=20,b=.0005)
 # An open protective lid is a thick disk with an actual ring-shaped lip.
 rod('Meter cover hinge',(-.033,.080,.351),(.033,.080,.351),.007,p['steel'],20)
 center=Vector((0,.133,.416));axis=Vector((0,-.82,.57));o=cyl('Open meter register protective cover',center,.085,.013,p['paint'],v=40,b=.002);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 o=ring('Protective cover inner seal',center+axis*.008,.073,.003,p['dark'],v=40);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
 bar('Cover hinge connecting tab',(0,.081,.352),(0,.087,.373),.026,.014,p['paint'],.002)
 return ('city-flanged-water-meter','保護蓋付きフランジ水量計','Flanged water meter with cover','建物の給水設備や実習用配管展示に置く水量計外装。青銅色の胴体、両端の実開口接続、取付脚、丸い無数字の指示面と固定針、開いた保護蓋・蝶番を造形。24本の目盛は装飾で、読み値や校正を表しません。外部配管、測定機構、流れの再現や計量性能は含みません。','A water-meter exterior for building water services and teaching pipework displays. It has a bronze-colored chamber, genuinely open end connections, feet, round unnumbered face with fixed pointer, and open protective lid/hinge. Twenty-four tick marks are decorative rather than a reading or calibration. External piping, measurement mechanisms, simulated flow and metering performance are absent.',['utilities','meter','water','水量計'])

def heat_exchanger():
 p=pal()
 for x in [-.265,.265]:
  box('Heat exchanger foot rail',(x,0,.025),(.133,.690,.043),p['paint'],.006)
  for y in [-.244,.244]:cyl('Base rail mounting bolt',(x,y,.052),.017,.018,p['steel'],v=6,b=.001)
 for y in [-.229,.229]:
  box('Heavy exchanger pressure frame',(0,y,.600),(.650,.058,1.105),p['paint'],.011)
  for x in [-.270,.270]:box('Frame mounting leg',(x,y,.106),(.074,.079,.156),p['paint'],.005)
 # Eighteen individually closed thin plates, not a solid painted box.
 for i in range(18):
  y=-.185+i*.0217;box('Individual heat transfer plate',(0,y,.615),(.532,.009,.863),p['steel'],.003)
  # Narrow embossed-looking outer lip is actual geometry on both side edges.
  for x in [-.264,.264]:bar('Plate perimeter folded edge',(x,y,.207),(x,y,1.020),.005,.014,p['bright'],.001)
 for x in [-.305,.305]:
  for z in [.255,.605,.990]:
   rod('Long exchanger clamping tie rod',(x,-.292,z),(x,.292,z),.011,p['steel'],24)
   for y in [-.291,.291]:cyl('Exchanger tie-rod nut',(x,y,z),.023,.025,p['bright'],'Y',v=6,b=.001)
 for z in [.162,1.071]:rod('Plate pack horizontal guide',(0,-.290,z),(0,.312,z),.019,p['steel'],28)
 for x in [-.176,.176]:
  for z in [.354,.870]:
   sleeve('Open exchanger connector neck',(x,-.303,z),.063,.046,.117,p['steel'],'Y',v=36)
   flange('Open exchanger port flange',(x,-.371,z),.087,.046,.021,p['steel'],'Y',bolts=4)
   cyl('Recessed dark port interior',(x,-.255,z),.045,.006,p['dark'],'Y',v=32,b=0)
 for x in [-.233,.233]:
  for z in [.153,1.087]:cyl('Rear pressure frame fastener',(x,.265,z),.014,.017,p['bright'],'Y',v=6,b=.001)
 return ('city-plate-heat-exchanger','フレーム式プレート熱交換器','Framed plate heat exchanger','建物の機械室・地域エネルギー設備に置くプレート式熱交換器外装。18枚の個別プレートと縁、前後の厚い押さえ枠、六本の締付棒とナット、ガイド棒、前面四口の実開口フランジと奥の暗い面、据付脚を造形。配管接続の見える奥行きはありますが、内部流路やガスケット構成を再現した設計図ではありません。熱交換・流体・圧力機能は未実装です。','A plate-heat-exchanger exterior for building plant rooms and community energy scenes. It has eighteen individual plates with edges, heavy front/rear pressure frames, six clamping rods and nuts, guide bars, four genuinely open front flanges with recessed dark interiors, and mounting feet. Visible connector depth is modeled, but internal fluid passages and gasket construction are not an engineering design. Thermal exchange, fluid flow and pressure behavior are not implemented.',['utilities','heat-exchanger','plant-room','熱交換器'])

def expansion_vessel():
 p=pal();sphere('Closed expansion-vessel pressure shell',(0,0,.748),(.332,.332,.577),p['red'],segments=48,rings=32)
 ring('Vessel central shell seam',(0,0,.748),.332,.004,p['red'],v=48)
 for i in range(3):
  a=i*math.tau/3+.3;u=Vector((math.cos(a),math.sin(a),0));bar('Splayed vessel mounting leg',u*.235+Vector((0,0,.370)),u*.318+Vector((0,0,.041)),.047,.056,p['red'],.005)
  q=u*.318;box('Vessel broad support foot',(q.x,q.y,.023),(.143,.115,.034),p['red'],.005,rot=(0,0,a))
  cyl('Vessel foot bolt head',(q.x,q.y,.046),.016,.014,p['steel'],v=6,b=.001)
 cyl('Vessel lower service connection',(0,0,.168),.034,.112,p['steel'],v=32,b=.002)
 sleeve('Open bottom connection lip',(0,0,.107),.040,.026,.026,p['steel'],v=32)
 cyl('Upper charging-valve stem',(0,0,1.329),.014,.043,p['steel'],v=24,b=.001)
 cyl('Upper protective valve cap',(0,0,1.357),.023,.027,p['dark'],v=28,b=.002)
 sleeve('Visible side service nozzle',(.320,0,.440),.041,.028,.163,p['steel'],'X',v=32)
 flange('Small open service flange',(.414,0,.440),.064,.028,.022,p['steel'],'X',bolts=4)
 cyl('Nozzle recessed internal dark face',(.251,0,.440),.027,.005,p['dark'],'X',v=28,b=0)
 box('Blank vessel identification plate',(0,-.343,.733),(.152,.016,.106),p['steel'],.004)
 for x in [-.055,.055]:cyl('Identification plate stand-off',(x,-.331,.733),.008,.026,p['steel'],'Y',v=16,b=.001)
 for x in [-.061,.061]:
  for z in [.697,.769]:cyl('Blank plate corner screw',(x,-.355,z),.005,.005,p['bright'],'Y',v=12,b=.0004)
 return ('city-closed-expansion-vessel','脚付き密閉膨張タンク','Leg-mounted closed expansion vessel','建物の温水・空調機械室に配置する密閉膨張タンク外装。赤い丸胴と中央の継ぎ目、三本の広がった脚と足板、上部保護キャップ、底部接続外形、側面の実開口ノズル、無記載の銘板を造形。屋上の開放型貯水槽とは異なる機械室用の単体プロップです。内部隔膜・流体・圧力調整は省略し、耐圧や設備安全性を示す製造設計ではありません。','A closed expansion-vessel exterior for building hot-water and HVAC plant rooms. It has a red rounded shell and central seam, three splayed legs/feet, top protective cap, lower connection exterior, genuinely open side nozzle and blank identification plate. This plant-room prop is distinct from an elevated open water-storage installation. Internal diaphragm, fluid and pressure regulation are omitted; it is not a manufacturing design or evidence of pressure or equipment safety.',['utilities','tank','plant-room','膨張タンク'])

BUILDERS=[gate_valve,water_meter,heat_exchanger,expansion_vessel]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-047/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/building_water_plant.py',azimuth=-55,elevation=27)
