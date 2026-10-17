"""Original community studio equipment. Xenoah, CC BY 4.0.
Static assemblies; recording, lighting, audio and support-load functions are absent.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def pal():
 return dict(paint=mat('Dark slate equipment housing',(.070,.095,.115),.18,.44),steel=mat('Satin support metal',(.43,.49,.53),.75,.33),bright=mat('Bright small fittings',(.64,.69,.72),.82,.28),dark=mat('Graphite cloth and trim',(.027,.034,.041),0,.69),rubber=mat('Soft black grip and cable',(.012,.017,.021),0,.78),white=mat('Plain softbox diffuser cloth',(.81,.82,.79),0,.89),screen=mat('Opaque inactive lens and screen',(.025,.063,.079),.10,.24),red=mat('Unlit dark red button',(.38,.032,.023),0,.43),wood=mat('Warm stand cradle',(.39,.25,.13),0,.52))
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

def video_camera():
 p=pal()
 # Three spread telescopic twin-tube legs, braced to a central spider.
 for i in range(3):
  a=i*math.tau/3+math.pi/6;u=Vector((math.cos(a),math.sin(a),0));v=Vector((-math.sin(a),math.cos(a),0));top=u*.075+Vector((0,0,1.225));end=u*.54+Vector((0,0,.035))
  for side in [-1,1]:
   shift=v*.021*side;rod('Tripod paired upper leg tube',top+shift,top.lerp(end,.66)+shift,.012,p['paint'],20);rod('Tripod exposed lower tube',top.lerp(end,.56)+shift,end+shift,.009,p['steel'],20)
  box('Tripod lower leg clamp',tuple(top.lerp(end,.65)),(.067,.051,.045),p['dark'],.004,rot=(0,0,a+math.pi/2))
  sphere('Tripod rubber foot',tuple(end),(.041,.039,.035),p['rubber'],segments=20,rings=10)
  rod('Tripod spreader brace',u*.025+Vector((0,0,.34)),top.lerp(end,.78),.009,p['steel'],16)
  cyl('Tripod upper hinge',tuple(top),.029,.066,p['dark'],'X',v=24,b=.002)
 cyl('Tripod spreader center',(0,0,.34),.044,.029,p['dark'],v=28,b=.003)
 cyl('Tripod central bowl',(0,0,1.225),.097,.075,p['paint'],v=40,b=.005)
 cyl('Fixed camera pan head',(0,0,1.300),.070,.091,p['dark'],v=36,b=.004)
 box('Tilt head support',(0,0,1.371),(.142,.148,.071),p['paint'],.006)
 cyl('Tilt axis knob',(.090,0,1.377),.034,.044,p['rubber'],'X',v=28,b=.003)
 rod('Pan control arm',(.070,.053,1.366),(.195,.338,1.200),.009,p['steel'],24)
 rod('Pan control rubber grip',(.165,.272,1.238),(.211,.371,1.181),.017,p['rubber'],24)
 box('Camera quick-release plate',(0,-.025,1.418),(.129,.249,.024),p['steel'],.003)
 box('Original video camera body',(0,-.017,1.520),(.170,.294,.185),p['paint'],.011)
 box('Camera rear battery',(0,.168,1.517),(.130,.086,.159),p['dark'],.009)
 box('Camera upper accessory rail',(0,-.003,1.631),(.049,.207,.022),p['steel'],.003)
 for y in [-.073,.080]:bar('Camera top handle upright',(0,y,1.630),(0,y,1.700),.027,.029,p['paint'],.004)
 box('Camera raised top carry handle',(0,.003,1.704),(.041,.191,.034),p['rubber'],.006)
 cyl('Video lens main barrel',(0,-.212,1.530),.068,.140,p['dark'],'Y',v=48,b=.004)
 for y in [-.174,-.222,-.263]:ring('Lens focus or zoom collar',(0,y,1.530),.067,.006,p['rubber'],'Y',v=40)
 sleeve('Actual open video lens hood',(0,-.308,1.530),.080,.067,.069,p['paint'],'Y',v=48)
 cyl('Recessed opaque video lens face',(0,-.280,1.530),.061,.005,p['screen'],'Y',v=48,b=.0005)
 frame('Camera front rectangular shade',.224,.177,.015,.035,(0,-.350,1.530),p['dark'])
 box('Right camera hand grip',(.105,.017,1.511),(.057,.177,.122),p['rubber'],.013)
 cyl('Camera fixed record button',(.138,-.020,1.553),.012,.008,p['red'],'X',v=24,b=.001)
 # Side screen is a plain inactive face with visible hinge and rear shell.
 rod('Camera screen hinge',(-.091,-.064,1.474),(-.091,-.064,1.586),.012,p['steel'],24)
 box('Opened camera display shell',(-.183,-.063,1.532),(.172,.022,.109),p['paint'],.005)
 box('Blank side display face',(-.183,-.077,1.532),(.146,.006,.084),p['screen'],.002)
 for z in [1.479,1.505,1.531]:box('Camera back service grille',(0,.215,z),(.095,.008,.009),p['steel'],.001)
 cyl('Camera rear connection cap',(.061,.215,1.569),.013,.009,p['dark'],'Y',v=24,b=.001)
 return ('city-tripod-video-camera','三脚付きビデオカメラ','Tripod-mounted video camera','公共スタジオ・催事会場で据えて使う無銘のビデオカメラ一式。二本管の三脚と伸縮部外形、開脚補強、固定パン/チルトヘッドと操作棒、レンズの実開口フードと角形遮光枠、無表示の開いた側面画面、上部取手・後部バッテリーを造形。監視用壁付カメラとは異なる撮影機材です。レンズ面は不透明PBRで、録画・光学・画面表示・首振り機能や支持荷重は検証していません。','An unbranded camera assembly for public studios and event venues. It has a twin-tube tripod with telescoping exteriors and spreaders, fixed pan/tilt head and control arm, truly open lens hood and rectangular shade, open blank side screen, top handle and rear battery. It is filming equipment rather than a wall-mounted security camera. The lens is an opaque PBR face; recording, optics, display, movement and support-load performance are not implemented or validated.',['studio','video','camera','ビデオカメラ'])

def boom_microphone():
 p=pal()
 for i in range(3):
  a=i*math.tau/3+.2;u=Vector((math.cos(a),math.sin(a),0));rod('Microphone stand spread leg',u*.025+Vector((0,0,.180)),u*.43+Vector((0,0,.030)),.016,p['paint'],24)
  rod('Microphone leg rubber end',u*.371+Vector((0,0,.053)),u*.45+Vector((0,0,.024)),.021,p['rubber'],24)
 cyl('Microphone tripod collar',(0,0,.172),.046,.111,p['dark'],v=28,b=.004)
 cyl('Microphone lower mast',(0,0,.630),.019,.920,p['paint'],v=28,b=.002)
 cyl('Microphone height collar',(0,0,1.075),.028,.072,p['rubber'],v=32,b=.003)
 cyl('Microphone exposed upper mast',(0,0,1.255),.014,.371,p['steel'],v=28,b=.001)
 cyl('Boom pivot body',(0,0,1.441),.043,.080,p['paint'],'X',v=28,b=.003)
 cyl('Boom tilt locking knob',(.055,0,1.441),.034,.030,p['rubber'],'X',v=28,b=.003)
 a=Vector((0,.310,1.374));b=Vector((0,-.755,1.608));axis=(b-a).normalized()
 rod('Long microphone boom',a,b,.012,p['steel'],24)
 rod('Boom rear counterweight grip',(0,.238,1.390),(0,.352,1.365),.025,p['dark'],28)
 # A fixed clip connects the microphone body directly to the boom tip.
 rod('Microphone holder short adapter',b,(0,-.769,1.646),.011,p['paint'],20)
 micaxis=Vector((0,-.94,.342));center=Vector((0,-.775,1.658));start=center-micaxis*.075;end=center+micaxis*.085
 rod('Microphone tapered-looking body',start,end,.022,p['paint'],32)
 q=center-micaxis*.013;o=sleeve('Microphone retaining clip',q,.028,.021,.048,p['rubber'],v=28);o.rotation_euler=micaxis.to_track_quat('Z','Y').to_euler()
 g=center+micaxis*.120;rod('Grille dark inner capsule',g-micaxis*.040,g+micaxis*.040,.027,p['dark'],32)
 u=Vector((1,0,0));v=micaxis.cross(u).normalized()
 for i in range(8):
  q=g+micaxis*(-.039+i*.011);o=ring('Microphone transverse grille wire',q,.028,.0013,p['steel'],v=32);o.rotation_euler=micaxis.to_track_quat('Z','Y').to_euler()
 for i in range(16):
  a=i*math.tau/16;off=.028*(u*math.cos(a)+v*math.sin(a));rod('Microphone longitudinal grille wire',g-micaxis*.040+off,g+micaxis*.040+off,.0012,p['steel'],12)
 o=cyl('Microphone grille end cap',g+micaxis*.043,.028,.005,p['steel'],v=32,b=.001);o.rotation_euler=micaxis.to_track_quat('Z','Y').to_euler()
 tube('Microphone connected cable',[tuple(start),(.016,-.629,1.575),(.021,-.260,1.500),(.028,.020,1.434),(.030,.037,1.068),(.026,.038,.33),(.074,.083,.020),(.23,.12,.009),(.30,.24,.009),(.19,.34,.009),(.05,.26,.009),(.13,.16,.009),(.27,.21,.009),(.35,.34,.009)],.005,p['rubber'],1)
 rod('Cable connector metal barrel',(.35,.34,.009),(.392,.374,.009),.008,p['steel'],24)
 return ('city-boom-microphone-stand','ブーム付きマイクスタンド','Boom microphone stand','地域スタジオ・会議・舞台の音声収録風景に置くマイク一式。開いた三脚、二段支柱と高さカラー、長いブームと後部重り外形、保持クリップ、金属線グリル付きマイク、支柱沿いから床へつながる固定ケーブルを造形。マイク・台・線は一式1点です。音声収録、通電、長さ調整、ケーブル変形や転倒安全性能は実装・検証していません。','A microphone assembly for community studio, meeting and stage recording scenes. It has a spread tripod, two-stage mast and height collar, long boom with rear weight exterior, retaining clip, wire-grille microphone and a connected fixed cable following the stand onto the floor. Microphone, stand and cable count as one model. Audio capture, electrical behavior, adjustment, cable deformation and stability performance are not implemented or validated.',['studio','audio','microphone','マイク'])

def softbox():
 p=pal()
 for i in range(3):
  a=i*math.tau/3+.3;u=Vector((math.cos(a),math.sin(a),0));rod('Softbox tripod leg',u*.020+Vector((0,0,.31)),u*.58+Vector((0,0,.025)),.016,p['paint'],24)
  rod('Softbox leg end sleeve',u*.515+Vector((0,0,.058)),u*.60+Vector((0,0,.016)),.021,p['rubber'],24)
  rod('Softbox leg spreader',u*.025+Vector((0,0,.11)),u*.30+Vector((0,0,.17)),.009,p['steel'],16)
 cyl('Softbox stand lower mast',(0,0,.64),.025,1.10,p['paint'],v=28,b=.002)
 for z in [.31,1.16]:cyl('Softbox stand locking collar',(0,0,z),.034,.060,p['dark'],v=28,b=.003)
 cyl('Softbox stand upper section',(0,0,1.35),.019,.40,p['steel'],v=28,b=.001)
 box('Softbox tilt mount pedestal',(0,.010,1.570),(.090,.095,.090),p['paint'],.007)
 cyl('Softbox side tilt knob',(.063,.010,1.584),.035,.037,p['rubber'],'X',v=28,b=.003)
 # Eight closed fabric wall panels make a true depth volume, not a textured card.
 zc=1.91;front=-.405;back=.070;rf=.490;rb=.140;n=8
 vs=[]
 for r,y in [(rf,front),(rb,back),(rb,back+.007),(rf,front+.007)]:
  vs.extend((r*math.cos((i+.5)*math.tau/n),y,zc+r*math.sin((i+.5)*math.tau/n)) for i in range(n))
 fs=[(k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i) for k in range(4) for i in range(n)]
 mesh('Continuous eight-panel closed softbox cloth shell',vs,fs,p['dark'])
 for i in range(n):
  a=(i+.5)*math.tau/n
  rod('Softbox outer radial seam',(rf*math.cos(a),front,zc+rf*math.sin(a)),(rb*math.cos(a),back,zc+rb*math.sin(a)),.004,p['paint'],16)
 # Thin front diffuser is solid, opaque cloth; it is not an emitting surface.
 o=cyl('Octagonal front diffuser',(0,front-.003,zc),rf*.978,.009,p['white'],'Y',v=8,b=0);o.rotation_euler[1]=math.pi/8
 for i in range(n):
  a=(i+.5)*math.tau/n;b=(i+1.5)*math.tau/n
  rod('Softbox front perimeter binding',(rf*math.cos(a),front,zc+rf*math.sin(a)),(rf*math.cos(b),front,zc+rf*math.sin(b)),.008,p['paint'],16)
 cyl('Softbox rear light housing',(0,.141,zc),.117,.221,p['paint'],'Y',v=40,b=.005)
 cyl('Softbox rear control disk',(0,.259,zc),.104,.026,p['dark'],'Y',v=36,b=.003)
 for z in [1.870,1.905,1.940]:box('Rear lamp cooling louver',(0,.278,z),(.134,.014,.011),p['steel'],.002)
 cyl('Rear fixed light adjustment knob',(.067,.285,1.956),.017,.020,p['rubber'],'Y',v=24,b=.002)
 for x in [-.127,.127]:bar('Light yoke side', (x,.112,1.588),(x,.112,1.918),.025,.031,p['paint'],.004)
 box('Light yoke bottom bridge',(0,.112,1.597),(.280,.040,.026),p['paint'],.004)
 bar('Tilt pedestal to yoke connection',(0,.010,1.594),(0,.112,1.594),.045,.040,p['paint'],.003)
 for x in [-.130,.130]:cyl('Lamp yoke pivot screw',(x,.112,zc),.024,.029,p['dark'],'X',v=24,b=.002)
 tube('Fixed softbox power cable',[(.053,.277,1.864),(.065,.300,1.750),(.055,.190,1.370),(.040,.071,.700),(.049,.067,.100),(.116,.130,.010),(.252,.170,.010),(.330,.100,.010)],.005,p['rubber'],1)
 box('Softbox cord unbranded end plug',(.346,.085,.013),(.046,.029,.024),p['dark'],.004,rot=(0,0,-.45))
 return ('city-octagonal-studio-softbox','八角形スタジオソフトボックス','Octagonal studio softbox','公共スタジオ・ポートレート撮影室向けの拡散照明外装。八枚の厚み付き布パネル、無地の前面拡散布、縁の綴じと放射状継ぎ目、後部灯体・グリル、傾斜ヨーク、伸縮式外形の三脚支柱と固定電源線を造形。追尾スポットとは異なる広い拡散面の機材です。布とレンズ類は不透明PBRで発光せず、照明・通電・調整動作やスタンド安全性は未検証です。','A diffused-lighting exterior for public studios and portrait rooms. It has eight thick fabric wall panels, plain front diffusion cloth, bound perimeter and radial seams, rear lamp housing/grille, tilt yoke, telescoping-style tripod stand and fixed power cable. Its broad diffuser is distinct from a followspot. Cloth and optical surfaces use opaque non-emissive PBR materials; lighting, electrical operation, adjustment and stand safety are not validated.',['studio','lighting','softbox','ソフトボックス'])

def headphones():
 p=pal()
 cyl('Headphone stand weighted-looking foot',(0,.019,.018),.107,.030,p['paint'],v=48,b=.004)
 ring('Stand foot underside rubber ring',(0,.019,.006),.086,.006,p['rubber'],v=40)
 bar('Headphone stand central post',(0,.036,.030),(0,.036,.483),.027,.034,p['steel'],.004)
 # Curved wooden cradle follows the inner arch rather than cutting through it.
 count=16;xs=[-.055+.110*i/count for i in range(count+1)];vs=[]
 for y in [-.031,.059]:
  vs.extend((x,y,.310+.190*math.sqrt(1-(x/.111)**2)+.001) for x in xs)
  vs.extend((x,y,.454) for x in xs)
 row=count+1;fs=[]
 for i in range(count):
  fs.extend([(i,i+1,2*row+i+1,2*row+i),(row+i,3*row+i,3*row+i+1,row+i+1),(i,row+i,row+i+1,i+1),(2*row+i,2*row+i+1,3*row+i+1,3*row+i)])
 fs.extend([(0,2*row,3*row,row),(count,row+count,3*row+count,2*row+count)])
 mesh('Curved headphone stand cradle',vs,fs,p['wood'],.001)
 # Closed-section arch band: height follows an ellipse above the two cups.
 n=40;vs=[]
 for i in range(n+1):
  a=i*math.pi/n
  for dr,y in [(0,-.024),(0,.024),(.009,.024),(.009,-.024)]:vs.append(((.111+dr)*math.cos(a),y,.310+(.190+dr)*math.sin(a)))
 fs=[(4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j) for i in range(n) for j in range(4)]+[(3,2,1,0),(4*n,4*n+1,4*n+2,4*n+3)]
 mesh('Continuous padded headphone headband',vs,fs,p['rubber'])
 for side in [-1,1]:
  x=side*.112
  bar('Headphone adjustment arm',(x,0,.316),(side*.111,0,.272),.013,.019,p['steel'],.002)
  # Closed ear shell and thick annular cushions, elliptical in their face plane.
  o=cyl('Closed-back headphone ear shell',(side*.119,0,.252),.065,.039,p['paint'],'X',v=40,b=.004);o.scale.y=.78;o.scale.z=1.10
  o=sleeve('Open-centered headphone ear cushion',(side*.091,0,.252),.061,.039,.023,p['rubber'],'X',v=40);o.scale.y=.80;o.scale.z=1.10
  o=cyl('Recessed opaque ear interior',(side*.098,0,.252),.039,.004,p['dark'],'X',v=32,b=0);o.scale.y=.80;o.scale.z=1.10
  cyl('Headphone yoke hinge',(side*.119,0,.324),.012,.043,p['steel'],'X',v=24,b=.001)
  o=ring('Outer ear shell trim',(side*.142,0,.252),.048,.002,p['steel'],'X',v=36);o.scale.y=.78;o.scale.z=1.10
 tube('Connected headphone cable',[(-.125,-.015,.190),(-.143,-.024,.132),(-.130,-.030,.034),(-.170,-.100,.008),(-.080,-.154,.008),(.032,-.125,.008),(.013,-.073,.008),(-.067,-.077,.008),(-.090,-.121,.008),(.022,-.160,.008),(.110,-.122,.008)],.0033,p['rubber'],1)
 rod('Headphone cable plug sleeve',(.109,-.122,.008),(.146,-.098,.008),.006,p['dark'],20)
 rod('Headphone cable metal plug',(.143,-.100,.008),(.169,-.083,.008),.003,p['bright'],20)
 return ('city-headphones-on-stand','台付きモニターヘッドホン','Monitor headphones on stand','地域スタジオや音声編集机に置くヘッドホン一式。左右の閉鎖型イヤーカップ、開口付き楕円クッションと奥の暗い面、連続したアーチ状ヘッドバンド、調整アーム・金具、木色の受けと金属支柱の卓上台、床面に置いたケーブルとプラグを造形。台・線を含め一式1点で、机や音響装置は含みません。再生音、電装、頭部追従・装着変形はありません。','A headphone assembly for community studios and audio-editing desks. It has two closed-back ear cups, open-centered elliptical cushions with recessed dark interiors, a continuous arched headband, adjustment arms and fittings, a desk stand with wooden-colored cradle/metal post, and a resting cable with plug. Stand and cable are included in one model; desk and audio equipment are absent. Audio playback, electrical operation, head tracking and wearing deformation are not supplied.',['studio','audio','headphones','ヘッドホン'])

BUILDERS=[video_camera,boom_microphone,softbox,headphones]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-045/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/community_studio_equipment.py',azimuth=-55,elevation=27)
