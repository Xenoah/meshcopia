"""Four original static urban-ecology props for Xenoah / Meshcopia, CC BY 4.0.
Blender 4.3.2. Geometry/materials only; no brands, scans, fonts or image assets.
This is visual scene dressing, not animal-habitat or meteorological design advice.
"""
import bpy, math, sys, argparse, json, hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(wood=mat('Warm unfinished timber',(.38,.20,.085),0,.78),light=mat('Pale timber endgrain',(.62,.41,.21),0,.83),darkwood=mat('Dark timber braces',(.20,.105,.052),0,.82),bamboo=mat('Golden hollow reed',(.62,.47,.23),0,.78),reed=mat('Muted reed variation',(.44,.32,.14),0,.83),steel=mat('Satin galvanized hardware',(.44,.49,.50),.72,.36),dark=mat('Charcoal hardware',(.037,.048,.046),.35,.59),roof=mat('Patinated roof green',(.08,.18,.13),.32,.53),white=mat('Warm white instrument polymer',(.76,.78,.72),0,.47),blue=mat('Muted blue painted hive timber',(.12,.28,.34),0,.69),cream=mat('Cream painted hive timber',(.67,.59,.36),0,.73))

def cyl(name,loc,radius,depth,material,axis='Z',vertices=32,bevel=.002):
 o=cylinder(name,loc,radius,depth,material,vertices,bevel=bevel)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def rod(name,a,b,radius,material,vertices=16,bevel=.001):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,radius,(b-a).length,material,vertices=vertices,bevel=bevel);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def bar(name,a,b,width,depth,material,bevel=.003):
 a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def screw(name,p,material,axis='Y',r=.007):
 return cyl(name,p,r,.006,material,axis,6,.0005)

def lathe(name,profile,material,segments=32,loc=(0,0,0),axis=(0,0,1)):
 """Closed revolved section. Exact single pole vertices avoid degenerate faces."""
 vs=[];rings=[]
 for radius,z in profile:
  if abs(radius)<1e-12:rings.append([len(vs)]);vs.append((0,0,z))
  else:
   rings.append(list(range(len(vs),len(vs)+segments)))
   vs.extend((radius*math.cos(i*math.tau/segments),radius*math.sin(i*math.tau/segments),z) for i in range(segments))
 fs=[]
 for i in range(len(rings)):
  a,b=rings[i],rings[(i+1)%len(rings)]
  if len(a)==len(b)==1:continue
  for j in range(segments):
   k=(j+1)%segments
   if len(a)==1:fs.append((a[0],b[j],b[k]))
   elif len(b)==1:fs.append((a[j],b[0],a[k]))
   else:fs.append((a[j],b[j],b[k],a[k]))
 o=mesh(name,vs,fs,material,0,False);o.location=loc;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();return o

def hollow(name,loc,ro,ri,depth,material,axis=(0,1,0),segments=24):
 return lathe(name,[(ro,-depth/2),(ro,depth/2),(ri,depth/2),(ri,-depth/2)],material,segments,loc,axis)

def plank_gable(name,xhalf,yhalf,eave,rise,thick,material):
 slope=math.atan2(rise,xhalf);length=math.hypot(xhalf,rise)
 for side in [-1,1]:
  box(name+' roof slope',(side*xhalf/2,0,eave+rise/2),(length+thick*.5,yhalf*2,thick),material,.004,rot=(0,side*slope,0))

def insect_hotel():
 p=palette()
 # A planted-looking pair of feet and structural posts; no terrain supplied.
 for x in [-.35,.35]:
  box('Galvanized foot shoe',(x,0,.075),(.15,.26,.15),p['steel'],.009)
  box('Timber support post',(x,0,.39),(.095,.11,.67),p['darkwood'],.005)
  for y in [-.06,.06]:screw('Foot shoe hex bolt',(x,y,.115),p['dark'],r=.009)
 box('Lower stand stretcher',(0,.025,.25),(.69,.062,.065),p['wood'],.004)
 for x in [-.35,.35]:bar('Stand diagonal knee',(x,0,.36),(x*.53,0,.65),.045,.065,p['wood'])
 # Cabinet is a closed-backed open-front timber lattice, not a nest box.
 for x in [-.46,.46]:box('Outer cabinet stile',(x,0,1.09),(.055,.35,1.02),p['wood'],.005)
 for z in [.60,1.08,1.58]:box('Compartment horizontal shelf',(0,0,z),(.90,.35,.045),p['wood'],.004)
 box('Compartment center mullion',(0,0,1.09),(.042,.35,.95),p['wood'],.003)
 for i in range(7):box('Full cabinet rear plank',(-.408+i*.136,.164,1.09),(.133,.025,.96),p['darkwood'],.0025)
 # Left upper chamber: staggered thick-walled reeds with genuinely empty bores.
 for row in range(5):
  for col in range(5):
   x=-.398+col*.078+(row%2)*.012;z=1.15+row*.080;r=.0325 if (row+col)%3 else .028
   hollow('Upper chamber hollow reed',(x,-.010,z),r,r-.006,.295,p['bamboo'] if (row+col)%2 else p['reed'],segments=20)
 # Lower right chamber: larger hollow branch sleeves, each with visible rim.
 for row in range(3):
  for col in range(4):
   x=.075+col*.10;z=.692+row*.135
   hollow('Lower chamber timber bore',(x,-.006,z),.045,.032,.287,p['light'] if (row+col)%2 else p['wood'],segments=24)
 # Two different slatted compartments with real openings, not black painted slots.
 for i in range(6):box('Horizontal refuge slat',(.231,-.004,1.145+i*.074),(.395,.29,.027),p['light'],.003)
 for i in range(6):box('Vertical refuge slat',(-.235+(i-2.5)*.061,-.015,.839),(.022,.285,.40),p['light'],.0025)
 for x in [-.39,-.08]:box('Lower chamber front retaining batten',(x,-.169,.842),(.021,.021,.39),p['darkwood'],.002)
 # Gabled canopy, honest end grain and fascia, sealed back gable.
 plank_gable('Timber canopy',.56,.235,1.59,.24,.035,p['roof'])
 mesh('Rear gable infill',[(-.45,.165,1.60),(.45,.165,1.60),(0,.165,1.80),(-.45,.19,1.60),(.45,.19,1.60),(0,.19,1.80)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],p['wood'],.002)
 for y in [-.228,.228]:
  for side in [-1,1]:bar('Pitched canopy fascia',(0,y,1.835),(side*.563,y,1.59),.033,.038,p['wood'])
 bar('Canopy ridge cap',(0,-.247,1.837),(0,.247,1.837),.032,.032,p['darkwood'])
 box('Gable cross tie',(0,-.166,1.605),(.89,.032,.035),p['light'],.002)
 for x in [-.445,.445]:
  for z in [.62,1.08,1.56]:screw('Front cabinet fastener',(x,-.180,z),p['dark'],r=.006)
 return('city-insect-hotel','木枠のインセクトホテル','Timber insect hotel','公園や公共菜園の展示シーンに置く、支柱付きの木枠インセクトホテル。背板と切妻屋根、4区画の棚、実際に中空の葦管と木管、横・縦の隙間を持つ板組を造形しています。昆虫・植栽・地面は含まず、生息環境の適性、防虫、保全効果を保証しない静的な外観模型です。','A freestanding timber insect hotel for park and community-garden scenes, with a boarded back, gabled canopy, four shelf compartments, genuinely hollow reed and timber sleeves, and horizontal/vertical slatted refuges. No insects, planting or ground are included. This static appearance prop makes no habitat suitability, pest-control or conservation-performance claim.',['garden','insect-hotel','ecology','インセクトホテル'])

def bird_feeder():
 p=palette()
 # Cruciform foot, raised central post and four diagonal load-path cues.
 for ax in range(2):box('Crossed pedestal ground beam',(0,0,.042+ax*.033),(.67,.085,.084) if not ax else (.084,.61,.084),p['darkwood'],.006)
 box('Square pedestal post',(0,0,.54),(.105,.105,1.03),p['wood'],.005)
 for a in range(4):
  ang=a*math.pi/2;v=Vector((math.cos(ang),math.sin(ang),0))
  bar('Pedestal diagonal brace',(v.x*.27,v.y*.27,.09),(v.x*.05,v.y*.05,.45),.047,.045,p['light'])
 for x in [-.23,.23]:bar('Tray underside knee',(0,0,.79),(x,0,1.025),.035,.046,p['light'])
 for y in [-.18,.18]:bar('Tray underside cross knee',(0,0,.82),(0,y,1.025),.035,.043,p['light'])
 for x in [-.24,.24]:box('Tray cross bearer',(x,0,1.025),(.055,.53,.045),p['darkwood'],.003)
 # Slatted tray floor has real narrow drainage gaps and an open upper volume.
 for i in range(8):box('Feed tray floor board',(-.287+i*.082,0,1.062),(.078,.52,.030),p['light'],.0025)
 for x in [-.335,.335]:box('Feed tray side lip',(x,0,1.103),(.032,.58,.076),p['wood'],.003)
 for y in [-.275,.275]:box('Feed tray end lip',(0,y,1.103),(.64,.030,.076),p['wood'],.003)
 # Four posts keep all four feeding sides open; this is explicitly not a nest box.
 for x in [-.271,.271]:
  for y in [-.213,.213]:
   box('Open canopy support',(x,y,1.305),(.038,.038,.46),p['wood'],.003)
   bar('Canopy knee',(x,y,1.38),(x*.63,y,1.535),.026,.030,p['light'])
 for y in [-.222,.222]:box('Canopy tie beam',(0,y,1.54),(.64,.043,.043),p['darkwood'],.0025)
 # Planks are individually modeled; ridge and end fascia cover their joints.
 slope=math.atan2(.20,.43);length=math.hypot(.43,.20)
 for side in [-1,1]:
  for i in range(7):box('Roof plank',(side*.215,-.321+i*.107,1.63),(length+.012,.105,.028),p['roof'],.003,rot=(0,side*slope,0))
  for y in [-.38,.38]:bar('Sloping roof fascia',(0,y,1.737),(side*.43,y,1.537),.031,.038,p['light'])
 bar('Raised ridge flashing',(0,-.392,1.75),(0,.392,1.75),.043,.043,p['darkwood'])
 for x in [-.335,.335]:
  for y in [-.205,.205]:screw('Tray lip screw',(x,y,1.108),p['steel'],'X',.005)
 return('city-roofed-bird-feeder','屋根付きの野鳥給餌台','Roofed bird feeder on pedestal','住宅の庭や公園の景観に使う、四方が開いた屋根付き給餌台。排水用の実際の隙間を持つ板張りトレー、低い縁、4本の屋根支柱、切妻の板屋根、筋交い付きの台座を備えます。巣箱ではありません。鳥・餌・水・地面は含まず、給餌の適否や衛生・動物の健康、安全性を保証しません。','An open-sided roofed feeding tray for residential-garden and park scenery, with a slatted tray containing actual drainage gaps, low rims, four canopy posts, a gabled plank roof and a braced pedestal. It is not a nest box. Birds, food, water and ground are omitted; no feeding suitability, hygiene, animal-health or safety performance is claimed.',['bird-feeder','garden','pedestal','給餌台'])

def beehive():
 p=palette()
 # Four-foot timber stand, cross rails and low diagonals.
 for x in [-.23,.23]:
  for y in [-.235,.235]:box('Hive stand leg',(x,y,.145),(.075,.075,.29),p['darkwood'],.005)
 for x in [-.23,.23]:box('Hive stand runner',(x,0,.27),(.085,.63,.067),p['wood'],.004)
 for y in [-.235,.235]:box('Hive stand cross rail',(0,y,.19),(.46,.048,.062),p['wood'],.003)
 bar('Rear stand diagonal',(-.23,.242,.055),(.23,.242,.23),.035,.036,p['light'])
 box('Hive bottom board',(0,0,.315),(.56,.61,.045),p['wood'],.004)
 # Entrance rim is genuinely interrupted rather than a painted dark rectangle.
 box('Entrance rear spacer',(0,.269,.355),(.52,.036,.042),p['darkwood'],.002)
 for x in [-.246,.246]:box('Entrance side spacer',(x,-.004,.355),(.035,.52,.042),p['darkwood'],.002)
 for x in [-.192,.192]:box('Front entrance reducer',(x,-.27,.355),(.137,.036,.042),p['wood'],.002)
 box('Landing board',(0,-.421,.318),(.40,.27,.031),p['light'],.003,rot=(math.radians(7),0,0))
 for x in [-.16,.16]:bar('Landing-board underside cleat',(x,-.27,.296),(x,-.53,.280),.035,.027,p['darkwood'])
 # Three hollow, externally closed-by-lid box courses. No hidden frames or comb.
 for k,h in enumerate([.225,.225,.19]):
  z0=.376+sum([.225,.225,.19][:k]);z=z0+h/2;m=p['cream'] if k!=1 else p['blue']
  for x in [-.247,.247]:box('Hive body side wall',(x,0,z),(.036,.536,h-.006),m,.003)
  for y in [-.25,.25]:box('Hive body end wall',(0,y,z),(.46,.036,h-.006),m,.003)
  # Small original contrasting finger-joint end-grain patches, not branding.
  for x in [-.246,.246]:
   for y in [-.272,.272]:
    for j in range(3):box('Corner joint exposed endgrain',(x,y,z0+.035+j*(h-.055)/3),(.033,.009,.026),p['wood'],.0008)
  # Front and rear handles are closed rectangular strap pieces with a real grip gap.
  for y in [-.279,.279]:
   for x in [-.074,.074]:box('Lift-handle mounting block',(x,y,z+.004),(.021,.022,.065),p['dark'],.003)
   yy=y+(-.035 if y<0 else .035)
   for x in [-.074,.074]:box('Lift-handle standoff',(x,(y+yy)/2,z+.018),(.018,abs(yy-y)+.014,.020),p['steel'],.003)
   box('Lift handle grip',(0,yy,z+.018),(.16,.018,.026),p['steel'],.004)
  box('Rear hive identification plate blank',(.12,.272,z+.045),(.093,.007,.045),p['light'],.002)
 top=.376+.225+.225+.19
 box('Insulated lid core',(0,0,top+.034),(.575,.60,.066),p['wood'],.006)
 box('Overhanging metal lid',(0,0,top+.075),(.605,.63,.022),p['steel'],.006)
 for x in [-.293,.293]:box('Folded lid side skirt',(x,0,top+.043),(.018,.624,.065),p['steel'],.0025)
 for y in [-.305,.305]:box('Folded lid end skirt',(0,y,top+.043),(.57,.018,.065),p['steel'],.0025)
 # Closed hold-down latch, front and rear, assembled from mounting and hinge parts.
 for y in [-.289,.289]:
  box('Lid latch backplate',(.192,y,top-.015),(.026,.014,.10),p['dark'],.002)
  box('Lid latch lever',(.192,y*1.035,top-.018),(.018,.016,.064),p['steel'],.003)
  screw('Lid latch pivot',(.192,y*1.071,top+.006),p['dark'],r=.006)
 return('city-urban-apiary-beehive','架台付きの都市養蜂箱','Urban apiary beehive on stand','公共菜園や屋上養蜂エリアの情景用に作成した、架台付きの積層式養蜂箱。3段の木箱、角の継ぎ目、前後の持ち手、張り出した金属蓋、巣門の実際の隙間、着地板と脚部を造形しています。蜂・蜂蜜・巣脾・内部の巣枠・養蜂道具は含みません。養蜂手順や生態・動物の健康、耐候性の保証を示すものではありません。','A stand-mounted stacked hive for community-garden and rooftop-apiary scenery, with three timber box courses, corner-joint details, front/rear lifting handles, an overhanging metal lid, a genuinely open entrance gap, a landing board and braced legs. Bees, honey, comb, internal frames and beekeeping tools are omitted. It is not beekeeping guidance and makes no ecological, animal-health or weather-resistance claim.',['beehive','apiary','garden','養蜂箱'])

def weather_station():
 p=palette()
 # Mast foot and compact three-legged support base. No separate installation site.
 cyl('Central mast foot',(0,0,.055),.10,.11,p['dark'],vertices=32,bevel=.005)
 cyl('Weather mast',(0,0,1.11),.028,2.12,p['steel'],vertices=32,bevel=.001)
 for i in range(3):
  a=math.radians(-90)+i*math.tau/3;x,y=.34*math.cos(a),.34*math.sin(a)
  box('Tripod ground shoe',(x,y,.018),(.13,.13,.036),p['dark'],.005)
  bar('Tripod tubular brace',(x,y,.043),(0,0,.52),.032,.032,p['steel'])
  for dx in [-.04,.04]:screw('Ground-shoe anchor',(x+dx,y,.040),p['steel'],'Z',.007)
 cyl('Tripod mast collar',(0,0,.51),.045,.085,p['dark'],vertices=24,bevel=.003)
 # A lateral instrumentation boom supports separately readable sensor silhouettes.
 rod('Instrument cross arm',(-.40,0,1.47),(.40,0,1.47),.019,p['steel'],24)
 for z in [1.44,1.50]:cyl('Cross-arm clamp',(0,0,z),.044,.024,p['dark'],vertices=24,bevel=.002)
 # Six real annular louver plates surround an unmarked central sensor capsule.
 sx=.34;sy=0
 cyl('Radiation shield sensor core',(sx,sy,1.55),.031,.235,p['dark'],vertices=24,bevel=.003)
 for i in range(6):
  z=1.46+i*.036
  lathe('Radiation-shield louver',[(.034,-.006),(.097,-.006),(.103,0),(.089,.014),(.034,.014)],p['white'],32,(sx,sy,z))
 lathe('Radiation-shield top cap',[(0,0),(.102,0),(.106,.008),(.074,.034),(0,.042)],p['white'],32,(sx,sy,1.68))
 for a in [0,math.tau/3,2*math.tau/3]:rod('Louver spacer rod',(sx+.052*math.cos(a),.052*math.sin(a),1.445),(sx+.052*math.cos(a),.052*math.sin(a),1.69),.0035,p['steel'],10,.0002)
 # Rain collector is a thick open funnel with a narrow, actual inner throat.
 rx=-.34
 cyl('Rain collector support stem',(rx,0,1.53),.024,.18,p['dark'],vertices=24,bevel=.002)
 lathe('Rain collector bowl',[(.037,-.12),(.092,-.045),(.105,.036),(.105,.060),(.096,.060),(.096,.035),(.083,-.039),(.022,-.105),(.022,-.12)],p['white'],40,(rx,0,1.71))
 hollow('Rain collector upper rolled lip',(rx,0,1.771),.110,.095,.010,p['steel'],axis=(0,0,1),segments=40)
 # Wind vane below the top rotor. One solid arrow, not a compass or live reading.
 cyl('Wind vane bearing',(0,0,1.905),.042,.105,p['dark'],vertices=24,bevel=.003)
 rod('Wind vane balance shaft',(-.305,0,1.94),(.30,0,1.94),.008,p['steel'],16)
 # Tail fin in a vertical XZ plane, with finite thickness and beveled perimeter.
 verts=[(x,y,z) for y in [-.007,.007] for x,z in [(-.31,1.94),(-.19,1.865),(-.19,2.015)]]
 mesh('Vane tail fin',verts,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],p['roof'],.002)
 verts=[(x,y,z) for z in [1.932,1.948] for x,y in [(.34,0),(.24,-.047),(.24,.047)]]
 mesh('Vane arrowhead',verts,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],p['dark'],.001)
 # Three hollow hemispherical anemometer cups, all facing tangent to rotation.
 cyl('Anemometer upper bearing',(0,0,2.14),.040,.11,p['dark'],vertices=24,bevel=.003)
 cyl('Anemometer rotor cap',(0,0,2.204),.046,.024,p['white'],vertices=24,bevel=.005)
 for i in range(3):
  a=math.radians(20)+i*math.tau/3;radial=Vector((math.cos(a),math.sin(a),0));tangent=Vector((-math.sin(a),math.cos(a),0));center=radial*.215+Vector((0,0,2.18))
  rod('Anemometer radial arm',(radial.x*.024,radial.y*.024,2.18),tuple(center),.008,p['steel'],16)
  ro=.071;ri=.063;profile=[(0,-ro)]
  for j in range(1,9):theta=j*math.pi/16;profile.append((ro*math.sin(theta),-ro*math.cos(theta)))
  for j in range(8,0,-1):theta=j*math.pi/16;profile.append((ri*math.sin(theta),-ri*math.cos(theta)))
  profile.append((0,-ri));lathe('Hollow anemometer cup',profile,p['dark'],24,tuple(center),tuple(tangent))
 # Blank receiver enclosure and short cable routing, no data display or logo.
 box('Instrument junction housing',(0,-.071,1.08),(.17,.104,.22),p['white'],.014)
 box('Closed junction cover',(0,-.130,1.08),(.146,.019,.195),p['dark'],.006)
 for x in [-.052,.052]:
  for z in [1.013,1.147]:screw('Junction-cover screw',(x,-.143,z),p['steel'],r=.005)
 tube('Instrument cable',[(.34,0,1.44),(.19,.025,1.40),(.045,.025,1.40),(.038,.025,1.02),(.025,-.043,.98)],.0045,p['dark'],1)
 for z in [.78,1.29]:hollow('Mast cable-retaining band',(0,0,z),.032,.027,.014,p['dark'],axis=(0,0,1),segments=24)
 return('city-weather-instrument-station','小型の気象観測マスト','Compact weather instrument station','公園・公共菜園・屋上の風景に配置する小型気象観測装置の静的な外観模型。3脚で支えたマスト、実際に中空の3杯式風杯、矢羽根、隙間のある放射シールド、開いた雨量収集漏斗、無表示の接続箱と短い配線を備えます。気象データ・校正・測定機能・可動機構・電源・外部ネットワークは含まず、気候測定の精度や機器の安全性・認証は主張しません。','A static compact weather-instrument appearance prop for park, community-garden and rooftop scenery, with a tripod-supported mast, three genuinely hollow anemometer cups, a directional vane, a gapped radiation shield, an open rain-collector funnel, a blank junction box and short cable routing. No weather data, calibration, measurement functions, moving mechanism, power supply or external networking are supplied; no climate-measurement accuracy, equipment-safety or certification claim is made.',['weather-station','anemometer','garden','気象観測'])

BUILDERS=[insect_hotel,bird_feeder,beehive,weather_station]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-014/assets');parser.add_argument('--only',default='');args=parser.parse_args(args)
 out=Path(args.out);out=out if out.is_absolute() else ROOT/out
 for fn in BUILDERS:
  reset();spec=fn()
  if args.only and spec[0]!=args.only:continue
  report=publish_asset(*spec,out,'scripts/city_expansion/urban_ecology.py',azimuth=-60,elevation=24)
  # Underside review uses the exact reimported GLB plus a QA-only fill light.
  meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
  bounds=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
  lo=Vector([min(v[i] for v in bounds) for i in range(3)]);hi=Vector([max(v[i] for v in bounds) for i in range(3)])
  span=max(hi-lo);center=(lo+hi)/2
  bpy.ops.object.light_add(type='AREA',location=center+Vector((.2,-.6,-1.8))*span)
  fill=bpy.context.object;fill.name='QA underside fill';fill.data.energy=120*span*span;fill.data.size=span*1.6;look_at(fill,center)
  render(out/'_qa'/f'{spec[0]}-underside.png',azimuth=-60,elevation=-24)
  bpy.data.objects.remove(fill,do_unlink=True)
