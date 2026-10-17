"""Original document-service equipment scene props. Xenoah, CC BY 4.0.
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

def paper_palette():
 p=pal();p['paper']=mat('Blank warm paper',(.78,.75,.66),0,.78);p['glass']=mat('Opaque inactive optical surface',(.024,.065,.074),.12,.25);return p

def thick_strip_x(n,width,yz,thick,m):
 pts=[Vector((0,y,z)) for y,z in yz];path=[]
 for j in range(len(pts)-1):
  p0=pts[max(0,j-1)];p1=pts[j];p2=pts[j+1];p3=pts[min(j+2,len(pts)-1)]
  for i in range(6):
   t=i/6;path.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 path.append(pts[-1]);L=len(path);vs=[]
 for layer in [0,1]:
  for j,q in enumerate(path):
   tangent=(path[min(j+1,L-1)]-path[max(0,j-1)]).normalized();normal=Vector((0,-tangent.z,tangent.y));q=q+normal*thick*layer
   vs.extend([(-width/2,q.y,q.z),(width/2,q.y,q.z)])
 fs=[];off=2*L
 for j in range(L-1):
  k=2*j;fs.extend([(k,k+1,k+3,k+2),(off+k+2,off+k+3,off+k+1,off+k)])
 smooth_count=len(fs)
 for j in range(L-1):
  k=2*j;fs.extend([(k,k+2,off+k+2,off+k),(k+3,k+1,off+k+1,off+k+3)])
 fs.extend([(1,0,off,off+1),(2*L-2,2*L-1,4*L-1,4*L-2)])
 o=mesh(n,vs,fs,m)
 for f in o.data.polygons:f.use_smooth=f.index<smooth_count
 return o

def plate_frame(n,x,y,z,w,h,p):
 box(n+' backing',(x,y,z),(w,.024,h),p['dark'],.006)
 box(n+' inactive display',(x,y-.014,z),(w-.025,.008,h-.025),p['glass'],.004)
def feet4(p,x,y,z=.018):
 for xx in [-x,x]:
  for yy in [-y,y]:cyl('Rubber countertop foot',(xx,yy,z),.025,z*2,p['rubber'],v=24,b=.002)

def wide_format_plotter():
 p=paper_palette()
 for x in [-.534,.534]:
  box('Plotter long floor foot',(x,0,.061),(.089,.562,.065),p['dark'],.008)
  for y in [-.226,.226]:
   cyl('Plotter transport wheel',(x,y,.045),.045,.053,p['rubber'],'X',v=28,b=.005)
   cyl('Plotter wheel hub',(x,y,.045),.021,.062,p['steel'],'X',v=24,b=.001)
  box('Plotter upright stand',(x,.045,.476),(.069,.099,.796),p['paint'],.007)
 box('Plotter low stand crossbrace',(0,.045,.302),(1.122,.057,.071),p['steel'],.006)
 box('Plotter stand upper rail',(0,.045,.863),(1.203,.173,.070),p['steel'],.006)
 for x in [-.642,.642]:box('Plotter end cover',(x,0,1.006),(.104,.451,.251),p['white'],.018)
 box('Plotter rear housing',(0,.144,1.014),(1.215,.151,.235),p['white'],.014)
 box('Plotter upper paper-feed cover',(0,-.051,1.085),(1.215,.269,.095),p['white'],.013)
 box('Plotter lower front service fascia',(0,-.129,.932),(1.215,.169,.094),p['paint'],.011)
 box('Plotter deep feed throat',(0,.023,1.001),(1.196,.025,.077),p['dark'],.003)
 cyl('Visible plotter feed roller',(0,-.096,.992),.022,1.148,p['steel'],'X',v=32,b=.002)
 # The curved blank paper web is a single closed thin shell rather than a texture.
 yz=[(-.176,.993),(-.222,.973),(-.260,.926),(-.281,.862),(-.286,.791),(-.278,.720),(-.256,.651),(-.224,.596)]
 thick_strip_x('Static blank emerging paper web',.929,yz,.002,p['paper'])
 cyl('Rear paper roll',(0,.164,.658),.081,1.025,p['paper'],'X',v=48,b=.004)
 cyl('Paper roll spindle',(0,.164,.658),.023,1.175,p['steel'],'X',v=28,b=.002)
 for x in [-.550,.550]:bar('Rear roll support',(x,.045,.784),(x,.164,.658),.033,.040,p['steel'],.004)
 for x in [-.493,.493]:
  bar('Paper catching-basket support',(x,.031,.604),(x,-.390,.388),.022,.024,p['steel'],.003)
 rod('Catch basket front edge',(-.493,-.390,.388),(.493,-.390,.388),.014,p['steel'],24)
 thick_strip_x('Fixed fabric paper catching sling',.962,[(-.381,.392),(-.301,.352),(-.189,.337),(-.071,.368),(.025,.463)],.005,p['dark'])
 rod('Catch basket rear anchor',(-.493,.025,.463),(.493,.025,.463),.013,p['steel'],24)
 for x in [-.493,.493]:rod('Basket rear mount tie',(x,.025,.463),(x,.045,.507),.012,p['steel'],20)
 plate_frame('Plotter control display',.624,-.231,1.063,.106,.081,p)
 for x in [.605,.650]:cyl('Unmarked plotter button',(x,-.228,.987),.009,.008,p['dark'],'Y',v=20,b=.001)
 box('Rear plotter service panel',(0,.225,1.026),(.775,.016,.160),p['steel'],.006)
 for x in [-.350,.350]:
  for z in [.970,1.083]:bolt('Rear service fastener',(x,.234,z),.006,p['dark'],'Y')
 box('Rear plotter cable socket',(.485,.228,.968),(.057,.021,.035),p['dark'],.004)
 return ('city-wide-format-roll-plotter','ロール紙式大判プロッター','Wide-format roll-paper plotter','設計事務所や印刷サービス店に配置する脚付き大判プロッター。幅広い給紙筐体、実際に開いた排紙口とローラー、無地の薄い湾曲紙、後ろのロール紙/軸/支持、固定の受け布と棒、車輪付き二脚と補強、操作表示面/ボタン、背面サービス板を造形しています。紙と受け布は一式に含まれる固定形状で別点数ではありません。画面は不透明・無表示、印刷/給紙/布の変形・電気機能はありません。','A stand-mounted large-format plotter for design offices and print shops. It has a broad feed housing, actual output opening/roller, thin curved blank paper web, rear roll/spindle/supports, fixed fabric catcher and rods, wheeled twin legs/bracing, blank control display/buttons and rear service panel. Paper and catcher are fixed geometry within one model, not additional assets. The screen is opaque and blank; printing, feeding, fabric deformation and electrical functions are absent.',['office','wide-format-plotter','printing','大判プロッター'])

def overhead_book_scanner():
 p=paper_palette();feet4(p,.261,.184)
 box('Book scanner desktop base',(0,0,.061),(.634,.465,.064),p['white'],.014)
 box('Book scanner center cradle spine',(0,-.025,.111),(.058,.340,.050),p['dark'],.007)
 for x in [-.155,.155]:
  a=math.radians(18 if x<0 else -18)
  box('Angled empty book cradle wing',(x,-.025,.170),(.297,.343,.024),p['paint'],.006,rot=(0,a,0))
  # The rear hinge and two inclined support struts visibly support each wing.
  cyl('Cradle hinge',(math.copysign(.026,x),-.025,.123),.014,.328,p['steel'],'Y',v=24,b=.001)
  for y in [-.153,.104]:bar('Cradle wing support',(x*.35,y,.087),(x*1.55,y,.186),.023,.027,p['steel'],.003)
 box('Scanner rear column',(0,.190,.497),(.064,.068,.820),p['white'],.007)
 bar('Scanner upper forward boom',(0,.190,.890),(0,-.057,.890),.053,.058,p['white'],.007)
 box('Overhead camera mount',(0,-.062,.850),(.145,.105,.058),p['dark'],.008)
 cyl('Downward camera lens barrel',(0,-.062,.808),.033,.039,p['steel'],v=32,b=.003)
 cyl('Opaque downward lens face',(0,-.062,.786),.027,.009,p['glass'],v=32,b=.001)
 bar('Scanner lighting crossbar',(-.265,.120,.770),(.265,.120,.770),.032,.040,p['steel'],.004)
 for x in [-.245,.245]:
  bar('Scanner lamp bracket',(x,.120,.770),(x,-.013,.684),.022,.027,p['steel'],.003)
  box('Scanner fixed side light housing',(x,-.016,.674),(.094,.348,.035),p['dark'],.005,rot=(0,math.radians(-28 if x<0 else 28),0))
  box('Opaque unlit scanner diffuser',(x+(.008 if x<0 else -.008),-.016,.656),(.075,.327,.011),p['cream'] if 'cream' in p else p['white'],.004,rot=(0,math.radians(-28 if x<0 else 28),0))
 plate_frame('Scanner front control face',.167,-.240,.083,.127,.064,p)
 cyl('Scanner fixed capture button',(-.211,-.238,.078),.016,.014,p['paint'],'Y',v=28,b=.003)
 smooth_cable('Fixed scanner camera cable',[(.059,-.045,.842),(.084,.154,.850),(.049,.229,.749),(.052,.228,.368),(.090,.225,.095)],.006,p['rubber'])
 box('Scanner rear connection bank',(.130,.238,.072),(.076,.022,.037),p['dark'],.003)
 return ('city-overhead-book-scanner','上方カメラ式ブックスキャナー','Overhead-camera book scanner','図書館や資料デジタル化室の机上に置くブックスキャナー。空の左右傾斜ブッククレードル、下側支え/蝶番、後柱と前に張り出すカメラアーム、下向きレンズ外形、左右の固定照明バー、操作面と曲線ケーブルを造形しています。本・紙面画像は付属せず一式1点。レンズ/画面/拡散板は不透明で、照明発光・撮影・スキャン・クレードル調整は実装していません。台の高さに合わせて配置してください。','An overhead book scanner for library and digitization-room desks. It includes an empty pair of inclined cradle wings, underside braces/hinges, rear column/forward camera arm, downward lens exterior, fixed side light bars, controls and curved cable. No book or page image is included; the assembly counts once. Lens, screen and diffusers are opaque, with no illumination, capture, scanning or cradle adjustment implemented. Adjust placement to desk height.',['library','book-scanner','digitization','ブックスキャナー'])

def comb_binding_machine():
 p=paper_palette();feet4(p,.168,.110,.012)
 # Low sloped housing uses an explicit closed profile.
 yz=[(-.148,.023),(.149,.023),(.149,.139),(.020,.170),(-.148,.092)]
 N=len(yz);vs=[(x,y,z) for x in [-.219,.219] for y,z in yz];fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,N+(i+1)%N,N+i) for i in range(N)];mesh('Sloped binder body',vs,fs,p['paint'],.008)
 box('Binder front paper resting deck',(0,-.153,.065),(.432,.067,.025),p['steel'],.005)
 box('Binder paper insertion slot',(0,-.158,.103),(.373,.014,.012),p['dark'],.002)
 box('Comb opening rail',(0,.044,.172),(.398,.045,.027),p['steel'],.004)
 for i in range(21):
  x=-.182+i*.0182
  # Thick U-like fingers remain open at their forward tips, not closed rings.
  tube('Fixed comb opening hook',[(x,.034,.176),(x,.036,.202),(x,.012,.215),(x,-.008,.215)],.003,p['steel'],1)
 for x in [-.227,.227]:
  cyl('Binder handle pivot',(x,.103,.129),.026,.029,p['steel'],'X',v=28,b=.002)
  bar('Raised binder lever side',(x,.103,.129),(x,.037,.326),.024,.021,p['steel'],.003)
 rod('Binder wide rubber hand grip',(-.227,.037,.326),(.227,.037,.326),.018,p['rubber'],28)
 box('Paper width guide',(-.176,-.139,.090),(.019,.088,.038),p['dark'],.003)
 box('Binder closed waste tray rear',(0,.156,.063),(.365,.018,.054),p['white'],.004)
 box('Waste tray recessed-looking grip',(0,.168,.064),(.089,.012,.017),p['dark'],.003)
 for x in [-.169,.169]:bolt('Binder rear cover fastener',(x,.1495,.116),.005,p['steel'],'Y')
 return ('city-manual-comb-binding-machine','手動コンブ式製本機','Manual comb-binding machine','事務所や学校の印刷室に置く手動製本機。傾斜筐体、紙差込口外形と手前の受け台、幅ガイド、二十一個の固定開きフック、左右の支点/立ち上がったレバーと幅広握り、背面の閉じた屑受けを造形しています。紙・樹脂コンブは付属せず、各フックは一式の部品です。パンチ/開閉/製本は動作しない静的小物で、設置時は机の高さに合わせてください。','A manual binding machine for office and school print rooms. Its sloped housing includes a paper-slot exterior/rest, width guide, twenty-one fixed opening hooks, side pivots/raised operating lever with wide grip and a closed rear waste tray. No paper or plastic comb is included; all hooks belong to one assembly. Punching, opening and binding are not operational. Adjust this static prop to desk height.',['office','comb-binding','print-room','製本機'])

def microfilm_reader():
 p=paper_palette();feet4(p,.213,.179,.018)
 box('Microfilm reader plinth',(0,0,.078),(.512,.452,.102),p['dark'],.012)
 box('Microfilm mechanism cabinet',(0,.045,.211),(.476,.341,.183),p['white'],.013)
 # Screen head leans slightly back but keeps an opaque, entirely blank viewing face.
 box('Microfilm screen rear body',(0,.095,.544),(.494,.285,.499),p['white'],.018)
 plate_frame('Microfilm reading screen',0,-.056,.565,.439,.367,p)
 box('Microfilm lower viewing hood',(0,-.102,.360),(.488,.153,.037),p['dark'],.006)
 for x in [-.237,.237]:box('Microfilm screen side hood',(x,-.105,.565),(.025,.161,.400),p['dark'],.005)
 box('Microfilm top viewing hood',(0,-.105,.769),(.497,.161,.029),p['dark'],.006)
 box('Film transport recessed dark deck',(0,-.164,.205),(.440,.166,.028),p['dark'],.005)
 for x in [-.147,.147]:
  cyl('Film spool rim lower',(x,-.165,.224),.075,.010,p['steel'],v=40,b=.002)
  cyl('Film spool dark winding',(x,-.165,.241),.057,.026,p['dark'],v=36,b=.002)
  sleeve('Film spool open top ring',(x,-.165,.259),.075,.019,.009,p['steel'],v=40)
  cyl('Film spool center hub',(x,-.165,.260),.015,.016,p['steel'],v=24,b=.001)
 # Blank film strip and center gate are geometry, with no photographs or scanned text.
 box('Fixed blank film path',(0,-.165,.240),(.249,.020,.002),p['rubber'],.0003)
 for x in [-.030,.030]:
  for y in [-.182,-.148]:box('Film gate mounting standoff',(x,y,.232),(.010,.010,.030),p['steel'],.001)
 frame('Central film gate frame',.074,.050,.009,.014,(0,-.165,.250),p['steel'],.001).rotation_euler.x=math.pi/2
 for x in [-.049,.049]:cyl('Film guide roller',(x,-.165,.242),.009,.030,p['steel'],v=20,b=.001)
 for x in [-.181,.181]:
  cyl('Film winding control spindle',(x,-.239,.166),.018,.032,p['steel'],'Y',v=24,b=.001)
  cyl('Film winding hand knob',(x,-.258,.166),.032,.025,p['dark'],'Y',v=28,b=.003)
 cyl('Microfilm focus dial',(.250,.036,.409),.032,.028,p['dark'],'X',v=28,b=.003)
 for x in [-.168,-.120,-.072,-.024,.024,.072,.120,.168]:box('Reader rear ventilation inset',(x,.243,.587),(.023,.014,.128),p['dark'],.003)
 box('Reader rear connection bank',(.145,.224,.190),(.069,.027,.041),p['dark'],.004)
 return ('city-microfilm-reading-machine','無表示画面のマイクロフィルム閲覧機','Blank-screen microfilm reader','図書館や資料閲覧室の机上に置くマイクロフィルム閲覧機。フード付き大型表示面、下の二個のフィルムリールと無地フィルム経路/中央ゲート、巻取つまみ、側面ピントつまみ、背面通気/接続部と足を造形しています。画面は不透明な無表示面で、資料画像や文字、光学投影、巻取/ピント調節機能は含みません。リールと本体は一式1点。机の高さに合わせて配置する静的な室内小物です。','A microfilm reader for library and archive desks. It includes a large hooded screen, two film reels with a blank film path/central gate, winding knobs, side focus dial, rear ventilation/connections and feet. The screen is opaque and blank; no archive imagery, text, optical projection, winding or focusing behavior is supplied. Reels and cabinet form one model. Adjust placement to desk height as a static interior prop.',['library','microfilm-reader','archive','マイクロフィルム'])

BUILDERS=[wide_format_plotter,overhead_book_scanner,comb_binding_machine,microfilm_reader]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-056/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/document_service_equipment.py',azimuth=-55,elevation=27)
