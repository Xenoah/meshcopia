"""Original retail and hospitality exterior props for Xenoah, CC BY 4.0.
No third-party design, logos, textures or fonts. Blender 4.3.2.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
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

def patio_heater():
 p=pal()
 lathe('Weighted base plate',[(0,0),(.26,0),(.28,.018),(.28,.035),(.26,.05),(0,.05)],p['black'])
 cyl('Patio heater tank enclosure',(0,0,.39),.192,.68,p['steel'],verts=64,b=.009)
 cyl('Tank enclosure lower rim',(0,0,.059),.20,.025,p['black'],verts=64,b=.004)
 lathe('Sloping enclosure top',[(0,.73),(.195,.73),(.195,.745),(.13,.81),(.055,.82),(0,.82)],p['steel'])
 cyl('Central riser',(0,0,1.22),.033,.85,p['steel'],verts=48,b=.002)
 for z in [.83,1.61]:cyl('Riser collar',(0,0,z),.047,.035,p['iron'],verts=40,b=.002)
 # Burner housing is enclosed by a guard, not a light emitter or real burner.
 cyl('Burner lower cup',(0,0,1.67),.135,.095,p['iron'],verts=48,b=.005)
 cyl('Inert burner core',(0,0,1.805),.091,.22,p['black'],verts=48,b=.003)
 for i in range(24):
  an=math.tau*i/24;rod('Vertical burner guard',(math.cos(an)*.128,math.sin(an)*.128,1.685),(math.cos(an)*.128,math.sin(an)*.128,1.928),.004,p['steel'],12)
 for z in [1.70,1.81,1.92]:torus('Burner guard band',(0,0,z),.128,.006,p['steel'],segments=48)
 cyl('Burner upper ring',(0,0,1.938),.143,.026,p['steel'],verts=48,b=.003)
 lathe('Open underside mushroom reflector',[(.46,1.97),(.47,1.981),(.445,1.996),(.30,2.04),(.14,2.068),(.0,2.072),(.0,2.061),(.14,2.057),(.30,2.029),(.445,1.985),(.459,1.978)],p['steel'],80)
 cyl('Reflector center cap',(0,0,2.075),.021,.018,p['iron'],verts=32,b=.002)
 for i in range(3):
  an=i*math.tau/3;rod('Reflector mounting stay',(.07*math.cos(an),.07*math.sin(an),1.93),(.13*math.cos(an),.13*math.sin(an),2.058),.004,p['iron'],16)
 box('Control-panel mount',(0,-.125,1.652),(.12,.045,.078),p['black'],.009)
 cyl('Control dial',(0,-.154,1.66),.020,.015,p['black'],'Y',28,.003)
 box('Blank control indicator',(0,-.165,1.675),(.004,.002,.010),p['white'],.001)
 # Rear service door with upright seam and two visible small hinges.
 for x in [-.10,.10]:rod('Tank service seam',(x,.166,.13),(x,.166,.64),.002,p['iron'],12)
 box('Tank service latch',(0,.195,.47),(.045,.015,.09),p['black'],.005)
 for z in [.20,.59]:cyl('Service door hinge',(.11,.164,z),.009,.04,p['iron'],verts=20,b=.001)
 for x in [-.17,.17]:
  cyl('Rear tilt transport wheel',(x,.22,.075),.058,.034,p['rubber'],'X',32,.004)
  cyl('Tilt wheel hub',(x*1.12,.22,.075),.020,.009,p['steel'],'X',20,.001)
 return('city-patio-heater','屋外テラス用のパティオヒーター','Outdoor patio heater','飲食店のテラスや屋外待合場所に置くマッシュルーム形の暖房器具。筒形収納部、支柱、ガード付き上部、実際に凹んだ反射傘、操作部と背面点検部を造形。燃料容器の中身・燃焼・熱・発光はなく、火災安全や使用条件を検証していません。','A mushroom-style heater for restaurant patios or outdoor waiting areas, with a cylindrical enclosure, riser, guarded upper assembly, genuinely concave reflector, controls and rear access. No fuel contents, combustion, heat or light emission is supplied; fire safety and operating conditions are not validated.',['patio','heater','terrace','ヒーター'])

def market_stall():
 p=pal();cloth=mat('Warm ivory canopy fabric',(.70,.70,.60),0,.82);trim=mat('Moss green canopy valance',(.08,.21,.13),0,.79);wood=mat('Counter warm wood solid color',(.32,.19,.09),0,.66)
 for x in [-.94,.94]:
  for y in [-.94,.94]:
   box('Tent ground foot',(x,y,.014),(.13,.13,.028),p['steel'],.008)
   box('Telescopic lower leg',(x,y,.66),(.034,.034,1.30),p['steel'],.004)
   box('Upper telescoping leg',(x,y,1.65),(.043,.043,1.05),p['steel'],.004)
   box('Sliding scissor hub',(x,y,1.75),(.068,.065,.09),p['black'],.006)
   cyl('Leg height locking pin',(x,y-.024,1.13),.005,.020,p['black'],'Y',16,.0006)
 # Crossed upper perimeter bars and ridge struts are separate fabrication geometry.
 for y in [-.94,.94]:
  for side in [-1,1]:
   bar('Scissor side A',(side*.94,y,1.77),(0,y,2.15),.018,.016,p['steel'])
   bar('Scissor side B',(side*.94,y,2.15),(0,y,1.77),.018,.016,p['steel'])
  rod('Scissor middle pivot',(0,y-.022,1.96),(0,y+.022,1.96),.009,p['black'],20)
 for x in [-.94,.94]:
  for side in [-1,1]:
   bar('Scissor end A',(x,side*.94,1.77),(x,0,2.15),.018,.016,p['steel'])
   bar('Scissor end B',(x,side*.94,2.15),(x,0,1.77),.018,.016,p['steel'])
  rod('Scissor end pivot',(x-.022,0,1.96),(x+.022,0,1.96),.009,p['black'],20)
 for x in [-.94,.94]:
  for y in [-.94,.94]:bar('Hip canopy support',(x,y,2.15),(0,0,2.73),.022,.022,p['steel'])
 cyl('Canopy peak connector',(0,0,2.69),.055,.10,p['black'],verts=24,b=.004)
 # Four closed-volume cloth faces with a modest thickness, not alpha cards.
 corners=[(-1.02,-1.02,2.18),(1.02,-1.02,2.18),(1.02,1.02,2.18),(-1.02,1.02,2.18)]
 # One continuous closed fabric shell avoids coincident internal seam faces.
 verts=[*corners,(0,0,2.79),*[(x,y,z+.008) for x,y,z in corners],(0,0,2.798)]
 faces=[]
 for i in range(4):
  j=(i+1)%4;faces.extend([(i,4,j),(5+i,5+j,9),(i,j,5+j,5+i)])
 mesh('Continuous four-panel fabric roof',verts,faces,cloth)
 for y in [-1.02,1.02]:box('Canopy front back valance',(0,y,2.115),(2.05,.012,.14),trim,.003)
 for x in [-1.02,1.02]:box('Canopy side valance',(x,0,2.115),(.012,2.05,.14),trim,.003)
 # Independent practical stall counter within the shelter, counted in this assembly only.
 box('Stall counter top',(0,-.63,.91),(1.82,.58,.055),wood,.014)
 for x in [-.79,.79]:
  for y in [-.84,-.42]:box('Counter folding leg',(x,y,.46),(.038,.038,.88),p['black'],.005)
  bar('Counter leg diagonal',(x,-.84,.14),(x,-.42,.80),.018,.018,p['steel'])
 box('Counter lower shelf',(0,-.63,.25),(1.60,.43,.027),wood,.007)
 box('Counter front modesty board',(0,-.91,.64),(1.69,.018,.43),trim,.005)
 for x in [-.83,.83]:
  for z in [.46,.81]:screw('Modesty board fixing',(x,-.923,z),p['steel'],'Y',r=.0035)
 return('city-folding-market-stall','開設状態の折畳み式マーケット屋台','Open folding market stall','広場の市やイベント物販に使う2 m級の仮設屋台。四脚の伸縮支柱、交差支え、4面の布屋根と垂れ、独立したカウンターと棚をひとつの静止セットにまとめました。商品、看板、地面、実際の開閉・耐風性能は含みません。','A roughly two-metre temporary market stall for plazas and event sales, with four telescopic legs, scissor braces, four fabric roof panels and valances, plus an independent counter and shelf in one static assembly. No goods, signs, ground, folding behavior or wind-resistance performance is supplied.',['market','stall','canopy','retail','屋台'])

def display_fridge():
 p=pal();enamel=mat('Warm white refrigerator enamel',(.67,.72,.71),.12,.40);dark=mat('Refrigerator interior gray',(.30,.38,.39),.18,.54)
 for x in [-.48,.48]:
  for y in [-.24,.24]:cyl('Adjustable refrigerator foot',(x,y,.044),.033,.088,p['black'],verts=24,b=.004)
 box('Refrigeration base enclosure',(0,0,.225),(1.20,.72,.30),enamel,.018)
 box('Bottom ventilation recess',(0,-.365,.22),(1.04,.018,.19),p['black'],.006)
 for i in range(19):box('Bottom intake grille blade',(-.47+i*.052,-.38,.22),(.013,.018,.174),p['steel'],.002)
 box('Cabinet back insulated panel',(0,.34,1.10),(1.20,.065,1.78),enamel,.012)
 for x in [-.58,.58]:box('Cabinet side insulated panel',(x,0,1.10),(.04,.71,1.78),enamel,.010)
 box('Cabinet inner backing',(0,.296,1.17),(1.10,.013,1.55),dark,.005)
 box('Upper refrigeration hood',(0,0,1.955),(1.21,.74,.14),enamel,.016)
 box('Upper return air dark slot',(0,-.372,1.925),(1.07,.015,.045),p['black'],.004)
 for i in range(24):box('Upper air grille divider',(-.52+i*.045,-.384,1.926),(.006,.013,.039),p['steel'],.001)
 # Three adjustable shelves plus lower merchandising deck; genuine open front.
 for level,z in enumerate([.42,.78,1.13,1.48]):
  box('Merchandising shelf',(0,-.015,z),(1.10,.58,.030),enamel,.006)
  box('Shelf front price strip',(0,-.314,z+.018),(1.11,.025,.046),p['black'],.004)
  box('Blank price insert',(0,-.330,z+.019),(1.065,.006,.025),p['white'],.001)
  for x in [-.52,.52]:
   bar('Shelf support bracket',(x,.28,z-.11),(x,-.20,z-.025),.019,.017,p['steel'])
 for x in [-.535,.535]:
  box('Shelf adjustment rail',(x,.28,1.13),(.023,.017,1.47),p['steel'],.003)
  for z in [.51,.68,.85,1.02,1.19,1.36,1.53,1.70]:box('Rail slot appearance',(x,.268,z),(.010,.004,.024),p['black'],.001)
 box('Upper inert display light strip',(0,.0,1.873),(.92,.045,.014),p['white'],.003)
 # Rear maintenance components and drain/control points, not operating internals.
 box('Rear compressor service lid',(0,.38,.33),(.83,.022,.31),p['steel'],.009)
 for x in [-.36,.36]:
  for z in [.22,.44]:screw('Service lid screw',(x,.394,z),p['black'],'Y',r=.004)
 for i in range(8):box('Rear ventilation slot',(0,.395,.23+i*.026),(.66,.004,.007),p['black'],.001)
 box('Rear mains junction cover',(.44,.39,.48),(.10,.033,.14),p['black'],.007)
 box('Front temperature display',(0,-.377,.354),(.17,.012,.036),p['black'],.005)
 box('Blank temperature readout',(-.025,-.386,.354),(.095,.004,.019),p['blue'],.002)
 cyl('Temperature adjustment button',(.058,-.387,.354),.008,.004,p['black'],'Y',16,.001)
 return('city-refrigerated-display-case','開放型の冷蔵陳列ケース','Open-front refrigerated display case','店舗や駅売店向けの空の冷蔵陳列ケース。4段の棚、価格差し、断熱側板、上部・下部の通風部、背面点検板と接地脚を造形。商品、冷却・排水・照明・温度表示の動作はなく、食品衛生や電気安全の基準適合を検証していません。','An empty open-front refrigerated display for shops and station kiosks, with four shelves, blank price strips, insulated sides, upper/lower ventilation details, rear access and adjustable feet. No goods, cooling, drainage, powered lights or active temperature display is supplied; food hygiene and electrical-safety compliance are not validated.',['refrigerator','display','retail','shop','冷蔵'])

def luggage_cart():
 p=pal();brass=mat('Brushed warm brass cart frame',(.48,.31,.105),.82,.30);carpet=mat('Burgundy platform carpet solid color',(.20,.025,.035),0,.94)
 box('Rounded platform frame',(0,0,.213),(.76,1.12,.085),p['black'],.025)
 box('Inset luggage platform',(0,0,.263),(.69,1.045,.025),carpet,.016)
 for x in [-.295,.295]:
  for y in [-.445,.445]:
   cyl('Caster swivel bearing',(x,y,.165),.036,.035,p['steel'],verts=24,b=.002)
   for xx in [x-.035,x+.035]:box('Caster fork plate',(xx,y,.107),(.011,.074,.104),p['steel'],.005)
   cyl('Caster wheel',(x,y,.07),.070,.052,p['rubber'],'X',32,.003)
   for xx in [x-.030,x+.030]:cyl('Caster axle cap',(xx,y,.07),.019,.012,p['steel'],'X',20,.0015)
 # Two tall continuous rounded arches, joined by a luggage hanger bar.
 for y in [-.43,.43]:
  pts=[(-.32,y,.27),(-.32,y,1.65)]
  for i in range(1,25):
   an=math.pi-i*math.pi/24;pts.append((.32*math.cos(an),y,1.65+.32*math.sin(an)))
  pts.append((.32,y,.27));tube('Bellhop arch frame',pts,.026,brass,3)
  for x in [-.32,.32]:
   cyl('Upright fixing collar',(x,y,.30),.038,.075,brass,verts=28,b=.004)
   screw('Upright fixing bolt',(x,y-.030,.30),p['steel'],'Y',r=.005)
  rod('Lower luggage retaining crossbar',(-.30,y,.40),(.30,y,.40),.018,brass,24)
 rod('Upper garment hanging rail',(0,-.43,1.91),(0,.43,1.91),.022,brass,32)
 for x in [-.32,.32]:
  rod('Side pushing rail',(x,-.43,.98),(x,.43,.98),.021,brass,28)
  rod('Side grip sleeve',(x,-.19,.98),(x,.19,.98),.027,p['rubber'],28)
 # Soft impact pads at deck ends; no luggage or hangers packaged as extra models.
 for y in [-.568,.568]:box('Platform end bumper',(0,y,.214),(.63,.033,.049),p['rubber'],.013)
 return('city-hotel-luggage-cart','ホテル用のベルボーイカート','Hotel bellhop luggage cart','ホテル玄関やロビーで使う荷物運搬カート。四つの旋回キャスター、縁付きのカーペット台、真鍮色の連続アーチ、押し手と上部ハンガーバーを備えます。荷物、ハンガー、走行・旋回・荷重や転倒安全の検証は含みません。','A bellhop cart for hotel entrances and lobbies, with four swivel-caster assemblies, an edged carpet platform, continuous brass-colored arches, push grips and overhead hanging rail. No luggage or hangers, rolling/swiveling behavior, load testing or tip-over safety validation is included.',['luggage','cart','hotel','hospitality','荷物'])

BUILDERS=[patio_heater,market_stall,display_fridge,luggage_cart]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-010/assets');p.add_argument('--only',default='');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/retail_hospitality.py',azimuth=-55,elevation=24)
