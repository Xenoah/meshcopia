"""Original manual food-preparation equipment scene props. Xenoah, CC BY 4.0.
Static unrigged assemblies, not working or certified equipment designs.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(white=mat('Powder-coated light service metal',(.48,.54,.54),.12,.44),paint=mat('Deep blue service paint',(.035,.17,.29),.18,.42),steel=mat('Brushed exposed steel',(.40,.47,.51),.76,.34),bright=mat('Bright small hardware',(.59,.65,.68),.81,.28),dark=mat('Dark mechanism trim',(.034,.043,.053),.16,.53),rubber=mat('Rubber feet and hoses',(.014,.019,.024),0,.77),screen=mat('Blank inactive control face',(.020,.049,.065),.10,.30),red=mat('Red control details',(.48,.025,.015),.05,.49),amber=mat('Amber fixed control details',(.62,.29,.025),.03,.47))
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

def smooth_cable(name,points,r,m):
 pts=[Vector(x) for x in points];out=[]
 for i in range(len(pts)-1):
  p0=pts[max(0,i-1)];p1=pts[i];p2=pts[i+1];p3=pts[min(len(pts)-1,i+2)]
  for j in range(9):
   t=j/9;out.append(tuple(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)))
 out.append(tuple(pts[-1]));return tube(name,out,r,m,1)
def caster(n,x,y,r,p):
 cyl(n+' rubber wheel',(x,y,r),r,.039,p['rubber'],'X',v=28,b=.004)
 cyl(n+' steel hub',(x,y,r),r*.45,.047,p['steel'],'X',v=24,b=.001)
 for side in [-1,1]:box(n+' caster fork',(x+side*.029,y,r*1.35),(.010,r*.93,r*.95),p['steel'],.002)
 box(n+' fork bridge',(x,y,r*1.82),(.071,r*.93,.016),p['steel'],.002)
 cyl(n+' swivel stem',(x,y,r*2.05),.020,r*.45,p['steel'],v=24,b=.001)
 box(n+' fixed brake pedal',(x,y-r*.63,r*1.57),(.040,r*.60,.016),p['dark'],.002)

def bolt(n,p,r,m,axis='Z'):
 return cyl(n,p,r,r*.60,m,axis,v=6,b=min(.001,r*.08))
def profile_body(n,profile,m,N=48):
 vs=[(r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),z) for r,z in profile for i in range(N)];fs=[]
 for j in range(len(profile)):
  for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,((j+1)%len(profile))*N+(i+1)%N,((j+1)%len(profile))*N+i))
 o=mesh(n,vs,fs,m)
 for f in o.data.polygons:
  j=f.index//N;f.use_smooth=abs(profile[j][1]-profile[(j+1)%len(profile)][1])>1e-8
 return o

def snack_palette():
 p=pal();p['paint']=mat('Green enamel machine body',(.045,.24,.16),.12,.36);p['cream']=mat('Warm cream enamel',(.72,.68,.53),.10,.39)
 g=mat('Light transparent snack cabinet pane',(.61,.76,.78,.08),.02,.18);g.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.08;g.surface_render_method='DITHERED';g.use_transparency_overlap=False;p['glass']=g
 return p

def feet(p,x,y,z=.023,r=.027):
 for xx in [-x,x]:
  for yy in [-y,y]:cyl('Countertop rubber foot',(xx,yy,z),r,z*2,p['rubber'],v=24,b=.003)
def control_knob(n,x,y,z,r,p):
 cyl(n+' collar',(x,y,z),r*1.18,.012,p['steel'],'Y',v=24,b=.001)
 cyl(n+' fixed knob',(x,y-.014,z),r,.023,p['dark'],'Y',v=28,b=.003)
 box(n+' unnumbered indicator',(x,y-.027,z+r*.42),(.003,.004,r*.65),p['cream'],.0005)
def power_inlet(n,x,y,z,p):
 box(n+' rear power inlet',(x,y,z),(.041,.019,.031),p['dark'],.003)
 for dx in [-.011,0,.011]:box(n+' modeled socket recess',(x+dx,y+.011,z),(.004,.004,.011),p['steel'],.0005)

def citrus_press():
 p=snack_palette();feet(p,.086,.112,z=.014,r=.022)
 box('Heavy citrus press base',(0,0,.040),(.238,.300,.050),p['paint'],.014)
 cyl('Rear column foot',(0,.104,.081),.043,.061,p['paint'],v=36,b=.004)
 cyl('Tall press support column',(0,.104,.299),.024,.451,p['steel'],v=36,b=.002)
 box('Bowl support sliding collar',(0,.104,.246),(.078,.067,.086),p['paint'],.009)
 bar('Bowl horizontal support arm',(0,.104,.241),(0,-.032,.241),.043,.035,p['paint'],.005)
 profile_body('Open juice collection bowl',[(.036,.241),(.069,.248),(.105,.290),(.108,.309),(.100,.309),(.097,.292),(.064,.257),(.032,.252)],p['steel'],48).location.y=-.032
 # Closed reamer body has a real raised conical exterior, not a flat printed shape.
 cyl('Reamer base support',(0,-.032,.258),.041,.019,p['steel'],v=36,b=.002)
 profile_body('Citrus reamer tapered hollow cone',[(.037,.262),(.031,.294),(.008,.328),(.005,.328),(.007,.322),(.028,.290),(.030,.267)],p['steel'],40).location.y=-.032
 cyl('Reamer small closed tip',(0,-.032,.328),.008,.003,p['steel'],v=28,b=.0006)
 for i in range(12):
  a=math.tau*i/12
  points=[(rad*math.cos(a),-.032+rad*math.sin(a),z) for rad,z in [(.0372625,.267),(.0322,.294),(.0146118,.320)]]
  tube('Reamer visible profile-following rib',points,.0025,p['steel'],1)
 sleeve('Visible juice outlet stub',(0,-.133,.266),.012,.008,.055,p['steel'],'Y',v=28)
 box('Upper lever pivot housing',(0,.104,.516),(.085,.075,.073),p['paint'],.010)
 cyl('Press lever transverse pivot',(0,.104,.526),.018,.106,p['steel'],'X',v=28,b=.002)
 for x in [-.056,.056]:bolt('Lever pivot nut',(x,.104,.526),.014,p['dark'],'X')
 rod('Raised citrus lever',(0,.104,.526),(0,-.203,.644),.014,p['steel'],28)
 rod('Citrus lever grip',(0,-.172,.633),(0,-.269,.669),.022,p['rubber'],32)
 bar('Fixed pressure link',(0,.023,.556),(0,-.032,.457),.026,.023,p['steel'],.003)
 cyl('Press bell neck',(0,-.032,.443),.019,.059,p['steel'],v=28,b=.002)
 profile_body('Raised hollow pressing bell',[(.018,.438),(.043,.422),(.089,.369),(.096,.360),(.089,.354),(.082,.366),(.036,.412),(.013,.427)],p['steel'],48).location.y=-.032
 cyl('Support collar locking stem',(.044,.104,.244),.008,.030,p['steel'],'X',v=20,b=.001)
 cyl('Support collar fixed knob',(.063,.104,.244),.017,.020,p['dark'],'X',v=24,b=.002)
 return ('city-lever-citrus-press','レバーを上げた手動シトラスプレス','Raised-lever manual citrus press','カフェやジュース店の台上に置く手動柑橘プレス。重い台座と柱、固定された高いレバーとリンク、内側が開いた押し鐘、リブ付き円錐リーマー、深さのある受け皿と吐出口外形を造形しています。果物や受けグラスは含まず、台の高さに合わせて配置します。レバー・搾汁・液体経路は動作せず、食品接触や圧搾性能を検証した実用品設計ではない静的小物です。','A manual citrus press for cafe and juice-counter scenes. A weighted base and column support the raised fixed lever/link, hollow pressing bell, ribbed conical reamer, recessed collecting bowl and outlet exterior. Fruit and a receiving glass are omitted; place at counter height. Lever movement, juicing and liquid flow are not implemented. This static prop is not a validated food-contact or pressing-equipment design.',['cafe','citrus-press','food-preparation','シトラスプレス'])

def potato_cutter():
 p=snack_palette()
 for x in [-.101,.101]:
  for y in [-.143,.194]:
   cyl('Cutter suction foot',(x,y,.016),.029,.032,p['rubber'],v=28,b=.003)
   cyl('Foot attachment stem',(x,y,.044),.012,.038,p['steel'],v=24,b=.001)
 box('Grid cutter base',(0,.023,.060),(.253,.428,.034),p['paint'],.007)
 for x in [-.106,.106]:bar('Cutter guide rail',(x,-.157,.098),(x,.193,.098),.018,.020,p['steel'],.002)
 box('Cutter feed trough floor',(0,.041,.106),(.188,.302,.013),p['steel'],.003)
 for x in [-.096,.096]:box('Low feed trough side',(x,.045,.128),(.013,.305,.052),p['steel'],.003)
 frame('Open square blade cartridge',.216,.216,.016,.031,(0,-.135,.213),p['steel'],.002)
 for i in range(1,9):
  x=-.092+i*.184/9;z=.121+i*.184/9
  box('Fixed vertical cutting-grid blade',(x,-.135,.213),(.0024,.022,.184),p['bright'],.0004)
  box('Fixed horizontal cutting-grid blade',(0,-.133,z),(.184,.022,.0024),p['bright'],.0004)
 for x in [-.099,.099]:
  for z in [.114,.312]:bolt('Blade frame captive bolt',(x,-.1515,z),.006,p['dark'],'Y')
 box('Retracted grid pusher backing',(0,.157,.204),(.177,.023,.169),p['steel'],.004)
 for i in range(9):
  for j in range(9):box('Fixed square pusher finger',(-.081+i*.02025,.137,.124+j*.02025),(.015,.026,.015),p['cream'],.001)
 for x in [-.105,.105]:
  box('Handle rear pivot bracket',(x,.191,.146),(.028,.049,.143),p['paint'],.004)
  cyl('Raised handle pivot',(x,.191,.209),.015,.042,p['steel'],'X',v=24,b=.001)
  bar('Raised cutter lever side',(x,.191,.209),(x,.036,.530),.022,.023,p['steel'],.003)
 rod('Cutter handle crossbar',(-.109,.036,.530),(.109,.036,.530),.015,p['steel'],24)
 rod('Cutter hand grip',(-.089,.036,.530),(.089,.036,.530),.022,p['rubber'],28)
 for x in [-.067,.067]:bar('Fixed pusher linkage',(x,.142,.311),(x,.166,.220),.018,.017,p['steel'],.002)
 rod('Linkage transverse anchor',(-.108,.142,.311),(.108,.142,.311),.009,p['steel'],24)
 return ('city-grid-potato-cutter','格子刃と上げたハンドル付きポテトカッター','Raised-handle grid potato cutter','食堂や軽食厨房の台に置く格子刃式手動ポテトカッター。81個の開口がある9×9刃格子、後退した81個の押し子、ガイド付き受け台、上げた二股ハンドルとリンク、吸着脚を一式にしています。食材は含まず、台の高さに合わせて設置します。刃や押し子は実形状ですが固定され、切断・吸着動作や食品用の安全性は実装・検証していません。','A manual grid potato cutter for canteen and snack-kitchen counters. One assembly includes a 9-by-9 cutting grid with 81 openings, 81 retracted pusher fingers, guided feed tray, raised forked handle/linkage and suction feet. No food is included; position at counter height. Blades and fingers are actual fixed geometry, with no cutting, suction or validated food-equipment safety behavior.',['kitchen','potato-cutter','food-preparation','ポテトカッター'])

def vacuum_sealer():
 p=snack_palette();feet(p,.183,.174,z=.019,r=.026)
 box('Sealer lower cabinet',(0,0,.096),(.470,.469,.135),p['steel'],.012)
 box('Sealer chamber floor',(0,0,.174),(.433,.426,.025),p['steel'],.004)
 for x in [-.224,.224]:box('Sealer chamber side wall',(x,0,.237),(.020,.454,.132),p['steel'],.003)
 for y in [-.218,.218]:box('Sealer chamber end wall',(0,y,.237),(.433,.020,.132),p['steel'],.003)
 fr=frame('Chamber upper sealing rim',.480,.471,.022,.012,(0,0,.307),p['steel'],.002);fr.rotation_euler.x=math.pi/2
 for x in [-.178,.178]:box('Seal-bar support block',(x,-.157,.190),(.035,.039,.035),p['dark'],.003)
 box('Fixed chamber seal bar',(0,-.157,.215),(.390,.035,.023),p['cream'],.003)
 box('Fixed seal-bar strip',(0,-.157,.228),(.373,.019,.005),p['dark'],.001)
 # Raised metal lid is transformed as an assembly about the rear hinge axis.
 angle=math.radians(-110);pivot=Vector((0,.228,.313))
 def lidbox(n,loc,size,m,bev=.004):
  o=box(n,loc,size,m,bev);o.location=pivot+Vector((loc[0],loc[1]*math.cos(angle)-loc[2]*math.sin(angle),loc[1]*math.sin(angle)+loc[2]*math.cos(angle)));o.rotation_euler.x=angle;return o
 lidbox('Raised solid metal chamber lid',(0,-.225,.010),(.492,.471,.028),p['paint'],.011)
 for x in [-.223,.223]:lidbox('Lid long rubber gasket',(x,-.225,-.007),(.015,.423,.012),p['rubber'],.002)
 for y in [-.429,-.021]:lidbox('Lid short rubber gasket',(0,y,-.007),(.447,.015,.012),p['rubber'],.002)
 lidbox('Lid inner liner',(0,-.225,-.008),(.415,.390,.008),p['steel'],.004)
 for x in [-.117,.117]:lidbox('Lid handle mount',(x,-.452,.039),(.028,.032,.051),p['dark'],.003)
 lidbox('Lid lifting handle',(0,-.452,.067),(.266,.033,.026),p['rubber'],.006)
 for x in [-.160,.160]:
  box('Rear lid hinge base',(x,.232,.283),(.069,.035,.052),p['steel'],.004)
  cyl('Lid hinge barrel',(x,.232,.314),.019,.078,p['steel'],'X',v=28,b=.002)
 # Static side stay meets the actual raised lid edge.
 top=pivot+Vector((.237,-.135*math.cos(angle),-.135*math.sin(angle)))
 rod('Fixed lid support stay',(.237,.145,.253),top,.008,p['steel'],24)
 box('Sealer front control fascia',(0,-.239,.108),(.413,.022,.080),p['dark'],.005)
 box('Blank sealer display',(-.075,-.252,.112),(.144,.007,.041),p['screen'],.004)
 for x in [.044,.083,.122,.161]:cyl('Unmarked fixed sealer button',(x,-.253,.113),.010,.009,p['cream'],'Y',v=20,b=.001)
 for x in [-.14,-.10,-.06,-.02,.02,.06,.10,.14]:box('Sealer rear vent',(x,.239,.107),(.018,.013,.050),p['dark'],.002)
 power_inlet('Sealer',.174,.239,.095,p)
 return ('city-open-chamber-vacuum-sealer','金属蓋を開いた卓上チャンバー真空包装機','Open-metal-lid chamber vacuum sealer','食品売場や厨房の作業台に置くチャンバー式真空包装機の外観。深さのある空の槽と前方シールバー、上げた金属蓋の内張り/ガスケット、ヒンジと固定ステー、無表示操作面、背面通気と接続部を備えています。袋や食品は含まず、蓋は不透明な金属表現です。台の高さに合わせて配置する静的モデルで、減圧・加熱シール・蓋の動作や圧力容器の性能は実装・検証していません。','A chamber vacuum-packaging machine exterior for food-shop and kitchen worktops. It has a genuinely recessed empty chamber, front seal bar, raised metal lid with inner liner/gasket, hinges and fixed stay, blank controls, rear vents and connection exterior. Bags and food are omitted; the lid is opaque metal. Position at worktop height. Vacuum, heat sealing, lid movement and pressure-vessel performance are neither implemented nor validated.',['kitchen','vacuum-sealer','food-preparation','真空包装機'])

def shaved_ice_machine():
 p=snack_palette();feet(p,.128,.109,z=.014,r=.025)
 box('Shaved ice machine plinth',(0,0,.042),(.325,.290,.059),p['paint'],.014)
 box('Open serving area inset',(0,-.023,.075),(.234,.199,.011),p['steel'],.004)
 for x in [-.126,.126]:
  box('Cast side pedestal foot',(x,.055,.101),(.062,.113,.088),p['paint'],.007)
  box('Tall machine arch post',(x,.066,.331),(.047,.067,.464),p['paint'],.006)
  box('Upper arch corner',(x,.050,.575),(.068,.098,.073),p['paint'],.008)
 box('Cast arch cross head',(0,.052,.601),(.293,.087,.047),p['paint'],.007)
 for x in [-.126,.126]:bolt('Arch cap bolt',(x,.052,.626),.010,p['steel'])
 # Open block chamber and lower blade carrier, no ice or serving vessel included.
 sleeve('Open cylindrical ice chamber',(0,.017,.384),.110,.102,.153,p['steel'],v=48)
 sleeve('Lower ice chamber support rim',(0,.017,.302),.117,.087,.020,p['paint'],v=48)
 for x in [-.121,.121]:bar('Blade carrier support',(x,.065,.301),(x*.77,.017,.301),.034,.028,p['paint'],.003)
 cyl('Blade carrier center hub',(0,.017,.300),.019,.018,p['steel'],v=28,b=.001)
 for i in range(4):
  a=math.tau*i/4;rod('Fixed blade carrier spoke',(0,.017,.300),(.093*math.cos(a),.017+.093*math.sin(a),.300),.008,p['steel'],20)
 box('Fixed shaved-ice blade',(0,-.016,.307),(.177,.020,.006),p['bright'],.001)
 cyl('Fixed ice pressure plate',(0,.017,.438),.095,.017,p['steel'],v=40,b=.002)
 cyl('Vertical pressure screw core',(0,.017,.558),.011,.242,p['steel'],v=28,b=.001)
 pts=[(.013*math.cos(t*math.tau),.017+.013*math.sin(t*math.tau),.454+t*.011) for t in [i/16 for i in range(16*19+1)]]
 tube('Modeled fixed pressure screw helix',pts,.0017,p['steel'],1)
 cyl('Pressure screw guide collar',(0,.017,.603),.022,.041,p['dark'],v=28,b=.002)
 cyl('Upper pressure screw handle hub',(0,.017,.685),.022,.023,p['steel'],v=28,b=.002)
 rod('Pressure screw cross handle',(-.072,.017,.689),(.072,.017,.689),.009,p['dark'],24)
 cyl('Side drive shaft',(.099,.066,.466),.014,.225,p['steel'],'X',v=28,b=.001)
 cyl('Side gear enclosure',(.148,.066,.466),.060,.033,p['paint'],'X',v=40,b=.006)
 ring('Hand crank rim',(.197,.066,.466),.093,.009,p['steel'],'X',v=48)
 cyl('Crank center hub',(.197,.066,.466),.021,.026,p['steel'],'X',v=28,b=.002)
 for i in range(4):
  a=math.tau*i/4;rod('Crank wheel spoke',(.197,.066,.466),(.197,.066+.091*math.cos(a),.466+.091*math.sin(a)),.007,p['steel'],20)
 rod('Crank outward grip spindle',(.197,-.026,.466),(.260,-.026,.466),.009,p['steel'],24)
 cyl('Fixed crank hand grip',(.258,-.026,.466),.016,.070,p['rubber'],'X',v=28,b=.003)
 for x in [-.126,.126]:
  for z in [.212,.421]:bolt('Arch external fastener',(x,.031,z),.009,p['steel'],'Y')
 return ('city-hand-cranked-shaved-ice-machine','手回し輪付きブロック氷削り機','Hand-cranked block-ice shaving machine','祭りや軽食店の台上に置く手回し式かき氷機。鋳物風アーチ、開放円筒室と固定押し板、実形状のねじ山、側面の輪形ハンドル/握り、下部の刃支持部と空の受け空間を造形しています。氷や器は含まず、机の高さに合わせて配置します。刃・輪・ねじは固定で、切削・伝動・食品機器の安全性能は実装・検証していない静的な外観モデルです。','A hand-cranked shaved-ice machine for festival and snack-counter scenes. A cast-style arch carries an open cylindrical block chamber, fixed pressure plate, geometric screw thread, side crank wheel/grip, lower blade carrier and empty receiving space. Ice and serving bowls are omitted; place at counter height. Blade, wheel and screw are fixed, with no cutting, transmission or validated food-equipment safety performance.',['festival','shaved-ice-machine','food-preparation','かき氷機'])

BUILDERS=[citrus_press,potato_cutter,vacuum_sealer,shaved_ice_machine]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-058/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/food_preparation_equipment.py',azimuth=-55,elevation=27)
