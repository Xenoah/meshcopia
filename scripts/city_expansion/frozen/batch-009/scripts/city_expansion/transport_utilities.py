"""Four original static transport/utility city assemblies for Xenoah, CC BY 4.0.
No external meshes, textures, logos, diagrams or standards-derived designs.
Blender 4.3.2; metre authoring in Z-up converted to Y-up by the frozen helper.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(steel=mat('Satin galvanized steel',(.43,.48,.51),.80,.35),dark=mat('Cast structural iron',(.055,.068,.076),.68,.55),rubber=mat('Graphite elastomer',(.018,.025,.028),0,.84),green=mat('Utility sage enamel',(.16,.29,.21),.35,.43),blue=mat('Marine blue powder coat',(.045,.15,.24),.32,.42),orange=mat('Clamp ochre enamel',(.69,.28,.045),.27,.40),red=mat('Muted vermilion enamel',(.52,.055,.025),.30,.43),white=mat('Warm reflective-looking solid enamel',(.78,.79,.71),.20,.38),ceramic=mat('Glazed taupe ceramic',(.52,.39,.25),0,.26),brass=mat('Terminal brass',(.45,.31,.105),.80,.31),wood=mat('Dark pressure-treated sleeper timber',(.17,.12,.074),0,.85),concrete=mat('Neutral cast concrete',(.37,.39,.36),0,.94))

def cyl(n,p,r,d,m,axis='Z',verts=32,b=.002,r2=None):
 if r2 is None:o=cylinder(n,p,r,d,m,verts,bevel=b)
 else:
  bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=p);o=finish(bpy.context.object,n,m,b,True)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=1  # A single machined chamfer, not unnecessary rounded microgeometry.
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(n,a,b,r,m,verts=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,b=min(.0015,r*.14));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bar(n,a,b,w,d,m,bev=.004):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def screw(n,p,m,axis='Z',r=.014,sign=1):
 cyl(n+' washer',p,r*1.55,r*.26,m,axis,24,.0008);q=list(p);q['XYZ'.index(axis)]+=sign*r*.43;cyl(n+' hex head',q,r,r*.80,m,axis,6,.001)

def prism(n,poly,z0,z1,m,bevel=.003):
 k=len(poly);v=[(x,y,z) for z in [z0,z1] for x,y in poly];f=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,v,f,m,bevel)

def extrude_x(n,profile,x0,x1,m,bevel=.003):
 k=len(profile);v=[(x,y,z) for x in [x0,x1] for y,z in profile];f=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,v,f,m,bevel)

def extrude_y(n,profile,y0,y1,m,bevel=.003):
 k=len(profile);v=[(x,y,z) for y in [y0,y1] for x,z in profile];f=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,v,f,m,bevel)

def annulus(n,p,outer,inner,depth,m,axis='Z',segments=32):
 v=[]
 for r,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:v.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for i in range(segments))
 f=[]
 for k in range(4):
  for i in range(segments):j=(i+1)%segments;f.append((k*segments+i,k*segments+j,((k+1)%4)*segments+j,((k+1)%4)*segments+i))
 o=mesh(n,v,f,m,0,True);o.location=p
 if axis=='X':o.rotation_euler[1]=math.pi/2
 if axis=='Y':o.rotation_euler[0]=math.pi/2
 for i,face in enumerate(o.data.polygons):face.use_smooth=(i//segments)%2==0
 return o

def handwheel(n,p,r,m):
 x,y,z=p;annulus(n+' open ring',p,r,r-.010,.016,m,'Y',40)
 for i in range(3):
  a=i*math.tau/3;rod(n+' spoke',(x,y,z),(x+(r-.006)*math.cos(a),y,z+(r-.006)*math.sin(a)),.005,m,16)
 cyl(n+' hub',p,.017,.033,m,'Y',24,.002)


def bridge_joint():
 p=palette();steel=mat('Worn satin joint steel',(.32,.36,.38),.86,.46)
 # Continuous closed comb plates, with real gaps rather than dark strips.
 # The second comb is offset by half a pitch, giving clearance around every finger.
 pitch=.145;centers=[-1.0875+i*pitch for i in range(16)];half=.029
 for side in [-1,1]:
  cc=centers if side==1 else [x+.0725 for x in centers[:-1]]
  poly=[(-1.20,.44),(1.20,.44),(1.20,.155)]
  for x in reversed(cc):poly.extend([(x+half,.155),(x+half,-.123),(x-half,-.123),(x-half,.155)])
  poly.append((-1.20,.155))
  if side==-1:poly=[(x,-y) for x,y in poly]
  prism('Interdigitated steel finger plate '+str(side),poly,.355,.405,steel,.003)
  y=side*.325
  # Recessed structural angle beneath each comb root.
  box('Longitudinal underside support flange',(0,y,.325),(2.39,.235,.040),p['dark'],.004)
  box('Support vertical web',(0,side*.415,.235),(2.37,.035,.19),p['dark'],.004)
  box('Support anchor return foot',(0,side*.443,.150),(2.38,.10,.035),p['dark'],.003)
  for x in [-1.10,-.73,-.365,0,.365,.73,1.10]:
   screw('Recessed root fixing',(x,y,.407),p['steel'],r=.018)
   cyl('Anchor bolt beneath plate',(x,y,.215),.013,.26,p['steel'],verts=24,b=.001)
   cyl('Anchor spread washer',(x,y,.098),.033,.010,p['steel'],verts=24,b=.001)
   screw('Anchor retaining nut',(x,y,.084),p['steel'],r=.021,sign=-1)
   # Triangular support gusset connects the anchor return to the plate support.
   profile=[(side*.402,.17),(side*.402,.315),(side*.258,.315)]
   extrude_x('Support angle stiffening gusset',profile,x-.012,x+.012,p['dark'],.002)
 # Hollow elastomer collection trough, not a storm drain. Open ended intentionally.
 prof=[(-.26,.29),(-.225,.14),(-.13,.105),(.13,.105),(.225,.14),(.26,.29),(.242,.29),(.210,.153),(.125,.122),(-.125,.122),(-.210,.153),(-.242,.29)]
 extrude_x('Open underside movement trough',prof,-1.195,1.195,p['rubber'],.002)
 for x in [-1.18,1.18]:
  for y in [-.262,.262]:box('Trough clamping tab',(x,y,.283),(.040,.060,.025),p['steel'],.003)
 # Actual perpendicular mounting lugs and short embedded-anchor visual tails.
 for x in [-.93,-.31,.31,.93]:
  for side in [-1,1]:
   box('Outboard embed anchor block',(x,side*.476,.227),(.072,.095,.070),p['dark'],.005)
   rod('Angled embed anchor',(x,side*.495,.23),(x,side*.63,.065),.014,p['steel'])
   rod('Bent anchor tail',(x,side*.63,.065),(x+.075,side*.63,.065),.014,p['steel'])
 return('city-bridge-expansion-joint','橋梁床版用フィンガー伸縮継手','Bridge deck finger expansion joint','橋梁道路の継ぎ目に埋め込む静的なフィンガー型伸縮継手。互い違いの厚鋼板には実際の隙間があり、下面の支持アングル、補剛板、締結ボルト、埋込みアンカーと開いたゴム製受け樋を備えます。排水格子やケーブル保護スロープではありません。床版・舗装・車両は付属せず、設置時は上面を道路面に合わせて下部を沈めてください。移動・排水の機能、荷重や道路規格の適合性は未検証。','A static embedded finger expansion joint for bridge-road deck seams. Interleaved thick steel comb plates have actual clearance gaps, with underside support angles, gussets, fastening bolts, embed anchors and an open elastomer trough. This is not a storm-drain grate or cable ramp. Road deck, pavement and vehicles are omitted; lower the assembly into its host surface until the finger plate top aligns with the road plane. No movement, drainage function, traffic load rating or road-standard compliance is supplied.',['bridge','expansion-joint','infrastructure','伸縮継手'])


def transformer():
 p=palette();darkgreen=mat('Deep utility green enamel',(.07,.15,.105),.30,.52)
 box('Chamfered concrete installation pad',(0,0,.10),(1.86,1.67,.20),p['concrete'],.045)
 for x in [-.54,.54]:
  box('Skid ground rail',(x,.07,.255),(.12,1.16,.11),p['dark'],.008)
  for y in [-.40,.51]:
   box('Tank mounting foot',(x,y,.310),(.19,.18,.055),darkgreen,.006)
   screw('Mounting anchor',(x+.045,y,.345),p['steel'],r=.018)
 box('Oil tank main body',(0,.165,.895),(1.15,.86,1.12),p['green'],.065)
 box('Tank lower rolled seam',(0,.165,.375),(1.18,.885,.07),darkgreen,.022)
 box('Tank lid seal',(0,.165,1.465),(1.20,.91,.022),p['rubber'],.010)
 box('Removable tank top cover',(0,.165,1.49),(1.235,.945,.050),p['green'],.025)
 for x in [-.55,0,.55]:
  for y in [-.255,.585]:screw('Tank cover fastener',(x,y,1.520),p['steel'],r=.012)
 # A side radiator is an array of thin sealed flat panels with real air gaps.
 for side in [-1,1]:
  for y in [-.17,.535]:rod('Cooling header tank connection',(side*.535,y,1.22),(side*.728,y,1.22),.033,darkgreen)
  for z in [.48,1.22]:rod('Radiator horizontal header',(side*.724,-.195,z),(side*.724,.56,z),.031,darkgreen)
  for i in range(10):
   yy=-.175+i*.079
   box('Sealed vertical radiator cooling plate',(side*.728,yy,.85),(.26,.027,.75),p['green'],.010)
   for xx in [side*.655,side*.80]:box('Radiator plate pressed ridge',(xx,yy-.014,.85),(.015,.012,.64),darkgreen,.004)
  box('Radiator lower guard',(side*.733,.18,.44),(.31,.84,.034),p['dark'],.007)
 # Additional rear exterior fins and real service interfaces, without wires.
 for x in [-.46,-.34,-.22,-.10,.02,.14,.26,.38,.50]:box('Rear corrugated cooling rib',(x,.635,.89),(.038,.12,.82),p['green'],.011)
 # Protected service cabinet shares tank brackets, with closed but recessed doors.
 box('Front cabinet rear support',(0,-.345,.86),(1.13,.17,.99),darkgreen,.018)
 box('Service cabinet sill',(0,-.595,.400),(1.19,.41,.10),darkgreen,.015)
 for x in [-.565,.565]:box('Service cabinet side wall',(x,-.58,.90),(.060,.43,1.0),p['green'],.012)
 box('Service cabinet weather hood',(0,-.585,1.420),(1.24,.48,.085),p['green'],.018)
 box('Recess behind two cabinet doors',(0,-.800,.905),(1.10,.030,.925),p['rubber'],.007)
 for side in [-1,1]:
  xx=side*.279
  box('Closed recessed service door',(xx,-.822,.905),(.540,.042,.905),p['green'],.012)
  box('Service door inward pressed panel',(xx,-.848,.925),(.43,.018,.71),darkgreen,.012)
  for z in [.58,1.22]:
   cyl('Cabinet hinge barrel',(side*.533,-.853,z),.016,.105,p['steel'],verts=24,b=.002)
   box('Cabinet hinge strap',(side*.493,-.851,z),(.080,.013,.057),p['steel'],.003)
  rod('Door handle standoff',(side*.065,-.862,.88),(side*.065,-.899,.88),.010,p['steel'])
  rod('Door handle standoff',(side*.065,-.862,1.03),(side*.065,-.899,1.03),.010,p['steel'])
  rod('Door pull handle',(side*.065,-.899,.88),(side*.065,-.899,1.03),.013,p['steel'])
 box('Blank equipment plaque',(-.27,-.864,1.13),(.24,.012,.090),p['steel'],.003)
 box('Recessed door lock socket',(.065,-.870,.79),(.037,.018,.052),p['dark'],.004)
 cyl('Nonfunctional lock cylinder',(.065,-.886,.79),.011,.012,p['steel'],'Y',24,.001)
 # Top bushings have stepped glazed skirts, solid bodies and a restrained terminal cap.
 for x in [-.38,0,.38]:
  cyl('Terminal bolted mounting flange',(x,.18,1.53),.092,.034,p['steel'],verts=40,b=.003)
  for a in [0,math.pi/2,math.pi,math.pi*1.5]:screw('Bushing flange bolt',(x+.065*math.cos(a),.18+.065*math.sin(a),1.553),p['dark'],r=.008)
  cyl('Bushing ceramic core',(x,.18,1.73),.034,.37,p['ceramic'],verts=40,b=.002)
  for j in range(6):cyl('Glazed insulator weather skirt',(x,.18,1.60+j*.048),.071-.004*j,.025,p['ceramic'],verts=40,b=.002,r2=.039)
  cyl('Terminal metal ferrule',(x,.18,1.931),.038,.044,p['brass'],verts=32,b=.003)
  box('Blank terminal lug',(x,.18,1.97),(.065,.027,.052),p['brass'],.005)
  cyl('Terminal clamping bolt',(x,.18,1.98),.010,.055,p['steel'],'Y',6,.001)
 # Lid fill cap, upper handling lugs and low capped service valve.
 cyl('Closed oil fill neck',(.42,.50,1.56),.042,.075,darkgreen,verts=32,b=.003)
 cyl('Closed fill cap',(.42,.50,1.605),.053,.022,p['dark'],verts=32,b=.003)
 for x in [-.50,.50]:
  annulus('Top lifting eye',(x,.38,1.59),.053,.029,.028,p['green'],'Y',32)
  box('Lifting eye weld foot',(x,.38,1.535),(.12,.075,.035),p['green'],.005)
 cyl('Capped rear drain neck',(.42,.725,.45),.027,.095,p['brass'],'Y',28,.002)
 cyl('Rear drain cap',(.42,.777,.45),.033,.024,p['dark'],'Y',8,.002)
 return('city-pad-mounted-transformer','基礎パッド付き地上変圧器','Pad-mounted utility transformer','公共設備や工業地区向けの無銘・静的な油入変圧器の外観。基礎パッド、据付脚、油槽、通風隙間のある側面冷却フィン、背面リブ、上面の碍子端子、閉じた保護サービスキャビネットを造形しています。端子・キャップは外観のみで、接続配線・内部油・巻線・図面はありません。実機の設計、通電機能、定格、感電・防火安全性、設置基準の適合性は一切示しません。','An unbranded static exterior of a utility oil-filled transformer for public-service and industrial scenes. Includes a concrete pad, mounting skids, tank, side cooling banks with actual air gaps, rear ribs, top insulated terminals and a closed protected service cabinet. Terminals and caps are visual only; connected wiring, internal oil, windings and electrical diagrams are omitted. This supplies no operational electrical function, equipment design, rating, shock/fire safety claim or installation-standard compliance.',['transformer','utility','electrical-prop','変圧器'])


def railway_buffer():
 p=palette();rail=mat('Railhead polished steel',(.39,.41,.40),.90,.31)
 # Short paired rail bed only, enough to show the stop anchoring, not a track kit.
 for y in [-1.02,-.53,-.04,.45,.94]:
  box('Dark timber cross sleeper',(0,y,.09),(2.08,.23,.18),p['wood'],.018)
  for x in [-.715,.715]:
   box('Rail fastening baseplate',(x,y,.196),(.31,.21,.032),p['dark'],.004)
   for dx in [-.118,.118]:
    box('Rail foot retaining clip',(x+dx,y,.237),(.070,.085,.033),p['dark'],.006)
    screw('Track fixing bolt',(x+dx,y,.260),p['steel'],r=.015)
 # Distinct rail cross-section, with a broad foot, narrow web and rounded head.
 profile=[(-.075,.214),(.075,.214),(.075,.238),(.024,.250),(.018,.327),(.045,.339),(.045,.377),(-.045,.377),(-.045,.339),(-.018,.327),(-.024,.250),(-.075,.238)]
 for x in [-.715,.715]:
  extrude_y('Rail length with actual profile',[(x+xx,z) for xx,z in profile],-1.18,1.18,rail,.003)
  # A-frame with rail-connected front leg, compression brace and ties.
  box('Front stop clamp base',(x,-.42,.410),(.27,.32,.095),p['dark'],.008)
  box('Rear stop clamp base',(x,.98,.410),(.29,.32,.095),p['dark'],.008)
  for y in [-.42,.98]:
   for dx in [-.109,.109]:screw('Stop base anchor',(x+dx,y,.462),p['steel'],r=.018)
  bar('Forward rising buffer support',(x,-.44,.44),(x,-.22,1.21),.145,.145,p['dark'],.007)
  bar('Long diagonal buffer compression strut',(x,1.03,.44),(x,-.20,1.18),.16,.15,p['dark'],.007)
  bar('Horizontal lower A-frame tie',(x,-.42,.46),(x,.99,.46),.105,.085,p['dark'],.004)
  # Two cheek gussets on each apex. The real triangular recess is left open below.
  poly=[(-.40,.94),(-.30,1.25),(.16,.97)]
  for dx in [-.092,.092]:
   extrude_x('Triangular apex cheek gusset',poly,x+dx-.014,x+dx+.014,p['steel'],.003)
   for y,z in [(-.29,1.15),(-.25,1.03),(.035,1.01)]:screw('Cheek throughbolt',(x+dx*1.18,y,z),p['dark'],'X',.018,sign=1 if dx>0 else -1)
  for y in [-.48,.98]:
   for side in [-1,1]:box('Rail clamp side jaw',(x+side*.099,y,.348),(.052,.21,.14),p['dark'],.004)
 # Lateral bracing arrests the supported frame sideways.
 for y,z in [(.89,.52),(-.28,1.10)]:bar('Transverse stop-frame brace',(-.715,y,z),(.715,y,z),.09,.09,p['dark'])
 bar('Rear diagonal cross brace',(-.65,.90,.51),(.65,.19,1.0),.055,.045,p['steel'])
 bar('Rear diagonal cross brace',(.65,.90,.51),(-.65,.19,1.0),.055,.045,p['steel'])
 # Beam is a welded hollow-looking fabricated assembly with end caps.
 box('Wide buffer impact beam',(0,-.31,1.205),(2.04,.24,.31),p['red'],.014)
 box('Buffer top steel flange',(0,-.31,1.366),(2.11,.28,.032),p['dark'],.005)
 box('Buffer lower steel flange',(0,-.31,1.046),(2.11,.28,.032),p['dark'],.005)
 for x in [-1.035,1.035]:box('Buffer end closing plate',(x,-.31,1.205),(.025,.255,.315),p['dark'],.006)
 for x in [-.715,.715]:
  box('Impact pad carrier',(x,-.451,1.205),(.43,.045,.29),p['steel'],.010)
  box('Black elastomer buffer contact',(x,-.494,1.205),(.35,.075,.235),p['rubber'],.024)
  for dx in [-.185,.185]:
   for dz in [-.105,.105]:screw('Impact pad attachment',(x+dx,-.481,1.205+dz),p['dark'],'Y',.010,sign=-1)
 for x in [-.28,.28]:
  box('Original blank visibility plate',(x,-.439,1.205),(.19,.012,.19),p['white'],.006)
  for dx in [-.070,.070]:screw('Visibility plate fixings',(x+dx,-.449,1.205),p['steel'],'Y',.007,sign=-1)
 return('city-railway-buffer-stop','短いレール床付き車止め','Railway buffer stop with short rail bed','線路終端を表現する静的な車止め。短い一対の断面付きレール、枕木、レール締結部、三角形の補強フレーム、斜材と横補強、幅広の緩衝梁とゴム接触面を備えます。列車、連続線路、バラスト・地盤は含まず、耐衝突性能や軌道規格の適合を示しません。レール区間は本車止めの一体的な設置表現であり、独立した追加素材ではありません。','A static railway end-stop assembly with a short pair of profiled rails, timber sleepers, rail fasteners, reinforced triangular frames, diagonal and lateral braces, a wide buffer beam and elastomer contact faces. No train, continuous track, ballast or terrain is supplied, and no collision performance or railway-standard compliance is implied. The short rail bed is integral installation context for this one asset, not an independently counted track asset.',['railway','buffer-stop','transport','車止め'])


def flood_gate():
 p=palette();panel=mat('Satin anodized flood panel',(.43,.51,.55),.76,.40)
 # A real rectangular open frame sits behind the closed metal flood panel.
 for x in [-.91,.91]:
  box('Wall-opening side mounting flange',(x,.11,.81),(.18,.075,1.62),p['blue'],.006)
  box('Structural frame side channel',(x*.94,.015,.81),(.10,.20,1.49),p['blue'],.007)
 for z in [.075,1.545]:
  box('Wall-opening horizontal mounting flange',(0,.11,z),(1.83,.079,.15),p['blue'],.006)
  box('Structural frame horizontal channel',(0,.011,z),(1.73,.204,.09),p['blue'],.007)
 # Raised continuous sealing seat and visible elastomer compression gasket.
 for x in [-.793,.793]:
  box('Vertical gasket seat',(x,-.075,.81),(.055,.045,1.40),p['dark'],.003)
  box('Compressed vertical seal',(x,-.101,.81),(.038,.018,1.37),p['rubber'],.004)
 for z in [.133,1.487]:
  box('Horizontal gasket seat',(0,-.078,z),(1.62,.045,.055),p['dark'],.003)
  box('Compressed horizontal seal',(0,-.103,z),(1.58,.018,.038),p['rubber'],.004)
 # Solid sealed plate, backed by continuous structural stiffeners, no glass.
 box('Closed sealed flood barrier leaf',(0,-.137,.81),(1.625,.061,1.395),panel,.009)
 for x in [-.745,.745]:box('Panel vertical perimeter reinforcement',(x,-.186,.81),(.075,.06,1.30),p['blue'],.006)
 for z in [.191,1.429]:box('Panel horizontal perimeter reinforcement',(0,-.187,z),(1.54,.06,.075),p['blue'],.006)
 for z in [.52,1.10]:
  box('Front continuous stiffening rib',(0,-.197,z),(1.50,.07,.062),p['blue'],.006)
  box('Rear continuous stiffening rib',(0,-.081,z),(1.48,.07,.072),p['blue'],.006)
 for x in [-.46,0,.46]:box('Rear vertical stiffener',(x,-.037,.81),(.065,.09,1.26),p['blue'],.005)
 # Rear corner brackets reinforce the leaf without filling the wall opening.
 for sx in [-1,1]:
  for sz in [-1,1]:
   poly=[(sx*.68,.81+sz*.55),(sx*.68,.81+sz*.33),(sx*.47,.81+sz*.55)]
   extrude_y('Rear triangular corner gusset',poly,-.005,.020,p['steel'],.002)
 # Left hand exposed heavy hinge barrels, static closed pose only.
 for z in [.34,.81,1.28]:
  box('Frame hinge strap',(-.913,-.12,z),(.15,.10,.13),p['blue'],.005)
  box('Leaf hinge strap',(-.745,-.216,z),(.17,.035,.10),p['blue'],.005)
  for zz in [z-.049,z+.049]:cyl('Outer hinge knuckle',(-.826,-.223,zz),.033,.041,p['steel'],verts=32,b=.003)
  cyl('Central hinge knuckle',(-.826,-.223,z),.033,.048,p['blue'],verts=32,b=.003)
  cyl('Hinge pin',(-.826,-.223,z),.013,.164,p['steel'],verts=24,b=.001)
  cyl('Hinge top cap',(-.826,-.223,z+.087),.020,.013,p['dark'],verts=24,b=.001)
 # Five clamp dogs distinguish this from an entry door. All visual/static.
 for x,z,angle in [(.84,.33,0),(.84,.81,0),(.84,1.29,0),(-.36,1.48,math.pi/2),(.36,1.48,math.pi/2)]:
  box('Clamp frame mounting block',(x,-.125,z),(.105,.13,.14),p['blue'],.008)
  o=box('Static compression clamp dog',(x-.072 if angle==0 else x,-.240,z if angle==0 else z-.067),(.23,.045,.067),p['orange'],.007)
  o.rotation_euler[1]=angle
  cyl('Clamp screw visible spindle',(x,-.278,z),.012,.22,p['steel'],'Y',24,.001)
  cyl('Clamp threaded-looking collar',(x,-.235,z),.028,.041,p['dark'],'Y',24,.003)
  for j in range(5):cyl('Clamp spindle thread ridge',(x,-.255-j*.012,z),.015,.004,p['steel'],'Y',20,.0005)
  handwheel('Clamp handwheel',(x,-.392,z),.063,p['orange'])
 # Main wall mount holes read as actual ring sleeves with bolt shanks.
 for x in [-.936,.936]:
  for z in [.16,.56,1.06,1.46]:
   annulus('Wall anchor countersunk sleeve',(x,.062,z),.025,.013,.020,p['steel'],'Y',24)
   cyl('Wall anchor shank',(x,.112,z),.010,.13,p['steel'],'Y',20,.001)
   screw('Wall anchor head',(x,.045,z),p['steel'],'Y',.017,sign=-1)
 for x in [-.57,0,.57]:
  for z in [.062,1.558]:screw('Horizontal frame anchor',(x,.060,z),p['steel'],'Y',.014,sign=-1)
 # Compact lifting grips on the front leaf, not door latch handles.
 for x in [-.35,.35]:
  for xx in [x-.065,x+.065]:rod('Leaf lifting grip stand-off',(xx,-.177,.79),(xx,-.259,.79),.010,p['steel'])
  rod('Leaf lifting grip',(x-.065,-.259,.79),(x+.065,-.259,.79),.013,p['steel'])
 return('city-flood-barrier-gate','壁開口用の止水ゲート','Wall-opening flood barrier gate','壁の開口部に固定する閉鎖状態の止水ゲート外観。中空の四周枠、密閉金属パネル、圧縮シール、前後の補強材、三つのヒンジ、手輪付き締付け金具と取付けフランジを造形。通常の出入口ドアではなく、洪水対策設備を表現する静的小道具です。壁・水・周囲建物は含みません。床面中央の原点は取付面ではないため、設置時は背面フランジの平面を壁面に合わせ、開口寸法と高さを別途調整してください。止水性能、圧力耐力、安全性、施工適合性は未認証・未検証。','A closed wall-opening flood barrier exterior with a real open perimeter frame, sealed metal leaf, compression gasket, front/rear stiffeners, three hinges, handwheel clamp dogs and mounting flanges. This is a static flood-equipment prop, not an ordinary entry door. No wall, water or building is included. Its base-centered origin is not a mounting datum: align the rear flange faces to the host wall and adjust opening clearance and installation height separately. It has no certified or verified flood sealing, pressure resistance, safety or construction suitability.',['flood-barrier','gate','infrastructure','止水ゲート'])

BUILDERS=[bridge_joint,transformer,railway_buffer,flood_gate]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-009/assets');parser.add_argument('--only',default='');a=parser.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  az,el=(-55,30) if fn==bridge_joint else (-55,24)
  publish_asset(*s,out,'scripts/city_expansion/transport_utilities.py',azimuth=az,elevation=el)
  # Extra lower-side QA fill makes attachment/underside details inspectable.
  verts=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices]
  lo=Vector([min(v[i] for v in verts) for i in range(3)]);hi=Vector([max(v[i] for v in verts) for i in range(3)]);center=(lo+hi)/2;span=max(hi-lo)
  bpy.ops.object.light_add(type='AREA',location=center+Vector((-.2,1.1,-1.6))*span);lamp=bpy.context.object;lamp.name='Underside QA fill';lamp.data.energy=200*span*span;lamp.data.size=span*1.5;look_at(lamp,center)
  render(out/'_qa'/f'{s[0]}-underside.png',az+135,-27,800)
  bpy.data.objects.remove(lamp,do_unlink=True)
