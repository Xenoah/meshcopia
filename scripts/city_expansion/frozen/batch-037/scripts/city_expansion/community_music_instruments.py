"""Original static music-room assemblies for Xenoah. CC BY 4.0.
No external meshes, scores, brand marks or audio. Complete assemblies count once.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def pal():
 return dict(wood=mat('Warm plain wooden case',(.29,.13,.055),0,.42),pale=mat('Pale untextured soundboard wood',(.62,.40,.18),0,.52),darkwood=mat('Dark wooden bridge and board',(.075,.039,.023),0,.46),black=mat('Black instrument finish',(.022,.026,.030),.05,.30),rubber=mat('Dark rubber pads',(.015,.019,.021),0,.76),ivory=mat('Warm ivory keys and trim',(.78,.78,.69),0,.42),steel=mat('Satin plated fittings',(.48,.53,.55),.78,.31),gold=mat('Warm brushed cymbal metal',(.54,.35,.10),.74,.34),red=mat('Muted red drum shell',(.36,.045,.032),.13,.35),head=mat('Plain opaque drum heads',(.65,.67,.65),.02,.63))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=20):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.1));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(n,p,r,t,m,axis='Z',v=48):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)
def prism(n,contour,y,depth,m):
 k=len(contour);vs=[(x,yy,z) for yy in [y-depth/2,y+depth/2] for x,z in contour];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];o=mesh(n,vs,fs,m)
 for f in o.data.polygons:f.use_smooth=f.index>=2
 return o

def upright_piano():
 p=pal()
 box('Upright piano main case',(0,.065,.662),(1.440,.422,1.062),p['wood'],.018)
 box('Piano top lid',(0,.048,1.202),(1.475,.478,.034),p['darkwood'],.010)
 for x in [-.695,.695]:
  box('Piano front side stile',(x,-.189,.602),(.052,.126,1.040),p['wood'],.010)
  box('Piano broad foot',(x,-.063,.067),(.108,.556,.097),p['darkwood'],.010)
  for y in [-.238,.171]:cyl('Small piano foot glide',(x,y,.016),.027,.026,p['rubber'],v=24,b=.002)
 box('Keyboard supporting keybed',(0,-.255,.721),(1.374,.347,.057),p['darkwood'],.009)
 box('Keyboard front lip',(0,-.425,.748),(1.374,.023,.038),p['wood'],.006)
 white=[n for n in range(21,109) if n%12 in [0,2,4,5,7,9,11]];wi=0
 for n in range(21,109):
  if n in white:
   x=(wi-25.5)*.024;box('Individual white piano key',(x,-.322,.762),(.023,.184,.022),p['ivory'],.0015);wi+=1
  else:
   x=(wi-26)*.024;box('Individual raised black piano key',(x,-.263,.785),(.014,.111,.024),p['black'],.0015)
 for x in [-.654,.654]:box('Keyboard end cheek',(x,-.321,.780),(.055,.209,.067),p['wood'],.006)
 box('Raised fixed fallboard',(0,-.158,.857),(1.326,.031,.143),p['wood'],.007)
 box('Upper front music panel',(0,-.164,1.030),(1.327,.023,.184),p['wood'],.006)
 # Plain folding-style music rest is fixed open, with no sheet music or lettering.
 box('Piano music rest panel',(0,-.208,1.015),(.560,.016,.190),p['darkwood'],.006,rot=(math.radians(-13),0,0))
 box('Music rest lower ledge',(0,-.233,.915),(.578,.055,.017),p['darkwood'],.004)
 for x in [-.210,.210]:rod('Music rest small supporting arm',(x,-.171,.954),(x,-.208,.972),.007,p['steel'],16)
 box('Lower front removable panel',(0,-.154,.431),(1.310,.025,.497),p['wood'],.008)
 box('Three-pedal lower mounting block',(0,-.186,.137),(.293,.109,.097),p['darkwood'],.006)
 for x in [-.078,0,.078]:
  bar('Fixed piano pedal stem',(x,-.202,.136),(x,-.330,.092),.019,.014,p['gold'],.002)
  box('Piano pedal toe',(x,-.354,.086),(.045,.074,.013),p['gold'],.004)
 # Rear structure is not a blank box: soundboard-colored panel and structural braces.
 box('Rear soundboard appearance panel',(0,.285,.661),(1.322,.020,.974),p['pale'],.004)
 for x in [-.570,-.285,0,.285,.570]:box('Rear piano support post',(x,.310,.660),(.064,.056,.984),p['darkwood'],.005)
 for z in [.203,1.118]:box('Rear cross brace',(0,.326,z),(1.341,.033,.069),p['darkwood'],.005)
 for x in [-.44,-.15,.15,.44]:cyl('Rear support screw head',(x,.347,1.118),.009,.005,p['steel'],'Y',v=12,b=.0005)
 return ('city-upright-piano','アップライトピアノ','Upright piano','交流室・学校の音楽室・小規模舞台に置く無銘のアップライトピアノ。52個の白鍵と36個の黒鍵、厚い鍵盤台、固定開放した鍵盤蓋と譜面台、三本のペダル、側脚、裏の響板色パネルと補強柱を造形。椅子・楽譜は付属せず、鍵やペダルは本体に含む一式1点です。音声、鍵盤アクション、調律や実楽器の性能は実装・検証していません。','An unbranded upright-piano prop for community rooms, school music rooms and small stages. It includes 52 white and 36 black keys, thick keybed, fixed raised fallboard/music rest, three pedals, side feet, rear soundboard-colored panel and braces. Stool and sheet music are absent; keys and pedals belong to one piano assembly. Audio, key action, tuning and real-instrument performance are not implemented or validated.',['music','piano','community','ピアノ'])

def guitar_stand():
 p=pal();n=96;outer=[]
 for i in range(n):
  a=i*math.tau/n;c=math.cos(a);w=.145-.035*c-.052*math.exp(-((c-.12)/.36)**2);outer.append((math.sin(a)*w,.422+.248*c))
 prism('Guitar curved wooden back',outer,.050,.008,p['wood'])
 # Closed thin body side wall, genuinely hollow between the front and back.
 vs=[]
 for scale,y in [(1,-.053),(1,.051),(.955,.051),(.955,-.053)]:vs.extend((x*scale,y,.422+(z-.422)*scale) for x,z in outer)
 fs=[(k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i) for k in range(4) for i in range(n)];o=mesh('Guitar hollow body side wall',vs,fs,p['wood'])
 for f in o.data.polygons:f.use_smooth=f.index//n in [0,2]
 hole=[(.051*math.sin(i*math.tau/n),.465+.051*math.cos(i*math.tau/n)) for i in range(n)];vs=[]
 for contour,y in [(outer,-.061),(outer,-.054),(hole,-.054),(hole,-.061)]:vs.extend((x,y,z) for x,z in contour)
 fs=[(k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i) for k in range(4) for i in range(n)];mesh('Guitar top with actual open sound hole',vs,fs,p['pale'])
 for r in [.053,.058]:ring('Plain sound-hole rosette ring',(0,-.063,.465),r,.0014,p['darkwood'],'Y',64)
 # Neck joins the upper bout; the six strings and frets are actual geometry.
 box('Guitar neck back',(0,-.010,.802),(.051,.045,.368),p['wood'],.010)
 box('Guitar fingerboard',(0,-.046,.805),(.054,.016,.385),p['darkwood'],.003)
 box('Neck heel block',(0,.005,.649),(.065,.077,.111),p['wood'],.010)
 head=[(-.032,.983),(-.037,1.099),(-.028,1.129),(.028,1.129),(.037,1.099),(.032,.983)]
 prism('Guitar headstock',head,-.012,.029,p['wood'])
 box('String nut',(0,-.058,.987),(.055,.009,.007),p['ivory'],.001)
 box('Guitar bridge',(0,-.070,.290),(.124,.022,.029),p['darkwood'],.004)
 box('Guitar bridge saddle',(0,-.083,.300),(.061,.008,.005),p['ivory'],.0007)
 for i in range(6):
  x=(i-2.5)*.0075;rod('Fixed guitar string',(x,-.086,.291),(x,-.060,.991),.00032,p['steel'],8)
  sphere('Bridge pin',(x,-.086,.283),(.0025,.0025,.0035),p['ivory'],segments=12,rings=6)
 for i in range(1,17):
  z=.987-.696*(1-2**(-i/12));rod('Individual fret wire',(-.025,-.056,z),(.025,-.056,z),.0009,p['steel'],8)
 for side in [-1,1]:
  for i in range(3):
   z=1.018+i*.037;cyl('Tuning machine post',(side*.025,-.034,z),.006,.016,p['steel'],'Y',v=16,b=.0005)
   rod('Tuning key shaft',(side*.034,-.010,z),(side*.052,-.010,z),.003,p['steel'],12)
   box('Fixed tuning key',(side*.059,-.010,z),(.016,.011,.022),p['ivory'],.004)
   rod('Headstock string return',(side*.025,-.043,z),(side*(.00375+i*.0075),-.060,.991),.00032,p['steel'],8)
 # Separate three-foot stand is part of the single assembly.
 for a in [math.radians(25),math.radians(155),math.radians(270)]:
  end=(.245*math.cos(a),.065+.245*math.sin(a),.021);rod('Guitar stand tripod leg',(0,.085,.150),end,.012,p['black']);cyl('Stand rubber end pad',end,.018,.031,p['rubber'],v=20,b=.003)
 rod('Guitar stand back upright',(0,.085,.075),(0,.085,.827),.013,p['black'])
 for x in [-.091,.091]:
  tube('Lower padded cradle support',[(0,.085,.201),(x,.063,.184),(x,-.012,.184),(x,-.041,.206)],.011,p['black'],1)
  rod('Cradle soft pad',(x,.015,.185),(x,-.030,.200),.014,p['rubber'],20)
 for x in [-.038,.038]:rod('Neck stand fork',(0,.085,.822),(x,.003,.822),.010,p['black']);cyl('Neck support rubber pad',(x,-.007,.822),.014,.029,p['rubber'],'Y',v=20,b=.003)
 return ('city-acoustic-guitar-stand','スタンド付きアコースティックギター','Acoustic guitar with stand','交流室・路上演奏の待機場所・音楽室向けの、三脚スタンドで保持した無銘の六弦ギター。曲線の中空胴と実開口のサウンドホール、ネックとヘッド、16本のフレット線、六本の固定弦、ペグ、ブリッジ、下部受けとネック支えを造形。ギターとスタンドで一式1点です。演奏者・ケース・楽譜は付属せず、弦振動・音声・調律・実楽器の音響性能は未検証です。','An unbranded six-string acoustic guitar held on a tripod stand for community rooms, busking rest areas and music rooms. A curved hollow body and actual sound-hole opening accompany neck/headstock, 16 fret wires, six fixed strings, tuning keys, bridge, lower cradle and neck support. Guitar and stand count as one assembly. Player, case and sheet music are absent; string motion, audio, tuning and real acoustic performance are unvalidated.',['music','guitar','stand','ギター'])

def drum_set():
 p=pal()
 def drum(name,x,y,z,r,h,axis='Z'):
  cyl(name+' colored shell',(x,y,z),r,h,p['red'],axis,v=48,b=.003)
  for side in [-1,1]:
   pos=(x,y+side*h/2,z) if axis=='Y' else (x,y,z+side*h/2)
   cyl(name+' plain closed head',pos,r*.96,.006,p['head'],axis,v=48,b=.001)
   ring(name+' metal head hoop',pos,r,.007,p['steel'],axis,48)
  for i in range(8):
   a=i*math.tau/8
   if axis=='Y':a1=(x+(r+.010)*math.cos(a),y-h*.38,z+(r+.010)*math.sin(a));b1=(a1[0],y+h*.38,a1[2])
   else:a1=(x+(r+.010)*math.cos(a),y+(r+.010)*math.sin(a),z-h*.38);b1=(a1[0],a1[1],z+h*.38)
   rod(name+' tension lug',a1,b1,.005,p['steel'],12)
 drum('Bass drum',0,-.015,.313,.300,.400,'Y')
 for x in [-.247,.247]:
  rod('Bass drum side spur',(x,-.095,.204),(x*1.30,-.205,.033),.010,p['steel']);cyl('Bass spur rubber foot',(x*1.30,-.205,.021),.017,.027,p['rubber'],v=20,b=.002)
 drum('Left rack tom',-.160,.052,.718,.128,.179)
 drum('Right rack tom',.161,.068,.719,.145,.190)
 rod('Rack tom central stand',(0,.093,.450),(0,.093,.692),.014,p['steel'])
 for x in [-.160,.161]:rod('Rack tom supporting arm',(0,.093,.650),(x,.066,.650),.010,p['steel'])
 drum('Floor tom',.491,.252,.447,.184,.295)
 for a in [0,2*math.pi/3,4*math.pi/3]:
  x=.491+.165*math.cos(a);y=.252+.165*math.sin(a);rod('Floor tom leg',(x,y,.424),(x+.025*math.cos(a),y+.025*math.sin(a),.025),.009,p['steel']);cyl('Floor tom rubber foot',(x+.025*math.cos(a),y+.025*math.sin(a),.017),.014,.027,p['rubber'],v=16,b=.002)
 drum('Snare drum',-.412,.297,.529,.155,.135)
 def stand(name,x,y,z,r=.190):
  rod(name+' main pole',(x,y,.060),(x,y,z),.011,p['steel'])
  for a in [0,2*math.pi/3,4*math.pi/3]:
   end=(x+r*math.cos(a),y+r*math.sin(a),.019);rod(name+' tripod leg',(x,y,.220),end,.008,p['steel']);cyl(name+' foot',end,.013,.025,p['rubber'],v=16,b=.002)
  cyl(name+' adjustment collar',(x,y,z*.60),.017,.045,p['black'],v=24,b=.002)
  rod(name+' lock wing',(x-.026,y,z*.60),(x+.026,y,z*.60),.004,p['steel'],12)
 stand('Snare stand',-.412,.297,.463,.160)
 for a in [0,2*math.pi/3,4*math.pi/3]:rod('Snare basket arm',(-.412,.297,.441),(-.412+.145*math.cos(a),.297+.145*math.sin(a),.466),.006,p['steel'],16)
 def cymbal(name,x,y,z,r):
  profile=[(.007,.020),(.036,.027),(.060,.010),(r,.000),(r,-.003),(.060,.006),(.036,.023),(.007,.016)];n=64;vs=[(x+rr*math.cos(i*math.tau/n),y+rr*math.sin(i*math.tau/n),z+zz) for rr,zz in profile for i in range(n)];fs=[(j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i) for j in range(len(profile)) for i in range(n)];mesh(name,vs,fs,p['gold'],smooth=True)
  cyl(name+' center clamp',(x,y,z+.032),.012,.018,p['black'],v=20,b=.001)
 for name,x,y,z,r in [('Crash cymbal',-.613,-.083,.961,.220),('Ride cymbal',.589,-.112,.987,.240)]:stand(name,x,y,z+.046,.210);cymbal(name,x,y,z,r)
 stand('Hi hat stand',-.618,.417,.828,.160);cymbal('Hi hat upper cymbal',-.618,.417,.828,.170);cymbal('Hi hat lower cymbal',-.618,.417,.799,.170)
 for x,y in [(0,.302),(-.618,.518)]:
  box('Fixed pedal base',(x,y,.024),(.080,.179,.021),p['black'],.004)
  box('Fixed foot pedal',(x,y,.040),(.061,.141,.014),p['steel'],.003,rot=(math.radians(8),0,0))
 rod('Hi hat pedal visible linkage',(-.618,.417,.060),(-.618,.465,.047),.005,p['steel'],16)
 rod('Bass drum beater rod',(0,.226,.082),(0,.215,.268),.005,p['steel'],16);sphere('Bass drum fixed beater head',(0,.204,.281),(.022,.018,.029),p['ivory'],segments=20,rings=10)
 stand('Drummer stool',0,.657,.438,.205);cyl('Drum stool padded seat',(0,.657,.468),.159,.065,p['black'],v=40,b=.010)
 for x in [-.460,-.395]:rod('Parked wooden drumstick',(x,.214,.605),(x+.047,.395,.605),.003,p['pale'],12)
 return ('city-compact-drum-set','コンパクトなドラムセット','Compact drum set','交流ラウンジや小規模舞台向けの五胴ドラムセット。バスドラム、二つのラックタム、フロアタム、スネア、三か所のシンバル台（ハイハットは上下二枚）、ペダル、椅子と置いた二本のスティックを一式で造形。各ヘッド、金属輪、張力金具、支柱・三脚・ゴム足に実形状を持たせています。全部を1点と数え、演奏者・音声・振動・ペダル動作・調律は含まず、演奏性能は未検証です。','A five-drum set for community lounges and small stages: bass drum, two rack toms, floor tom and snare, with three cymbal-stand positions (two cymbals at the hi-hat), pedals, stool and two parked sticks. Heads, metal hoops, tension fittings, poles, tripods and rubber feet are modeled. The complete set counts once. Player, audio, vibration, pedal behavior and tuning are absent; performance as a real instrument is unvalidated.',['music','drums','stage','ドラムセット'])

def framed_xylophone():
 p=pal();width=1.100
 for x in [-.480,.480]:
  for y in [-.195,.195]:
   cyl('Xylophone caster wheel',(x,y,.038),.032,.026,p['rubber'],'X',v=24,b=.002)
   box('Caster fork',(x,y,.065),(.049,.038,.051),p['steel'],.004)
   rod('Frame upright',(x,y,.075),(x,y,.835),.017,p['black'])
  rod('Side base cross rail',(x,-.195,.127),(x,.195,.127),.019,p['black'])
 for y in [-.195,.195]:rod('Lower longitudinal frame rail',(-.480,y,.273),(.480,y,.273),.015,p['black'])
 for y in [-.163,.163]:box('Bar supporting longitudinal frame',(0,y,.839),(1.105,.033,.038),p['darkwood'],.006)
 for x in [-.538,.538]:box('Xylophone end frame',(x,0,.839),(.035,.562,.038),p['darkwood'],.006)
 for y in [-.100,.100]:rod('Continuous bar support cord',(-.512,y,.862),(.512,y,.862),.003,p['rubber'],12)
 # Twenty graduated bars, not a claim of a particular musical range or tuned pitch.
 for i in range(20):
  x=(i-9.5)*.051;length=.540-i*.013
  box('Graduated wooden sounding bar',(x,0,.882),(.045,length,.027),p['pale'],.004)
  for y in [-.100,.100]:
   cyl('Bar retaining button',(x,y,.900),.004,.005,p['black'],v=12,b=.0005)
  # A genuinely open resonator tube is visible from below.
  r=.017;ri=.014;h=.430-i*.010;n=24;vs=[]
  for rr,z in [(r,.842-h),(r,.842),(ri,.842),(ri,.842-h)]:vs.extend((x+rr*math.cos(j*math.tau/n),rr*math.sin(j*math.tau/n),z) for j in range(n))
  fs=[(k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j) for k in range(4) for j in range(n)];o=mesh('Open hanging resonator tube',vs,fs,p['steel'])
  for f in o.data.polygons:f.use_smooth=f.index//n in [0,2]
 for z in [.500,.780]:rod('Resonator tube support rail',(-.500,.026,z),(.500,.026,z),.007,p['steel'],16)
 for x in [-.480,.480]:rod('Resonator rail hanger',(x,.026,.500),(x,.026,.833),.008,p['steel'],16)
 for y in [-.130,.130]:bar('Mallet tray diagonal support',(.480,y,.830),(.690,y,.777),.018,.018,p['black'],.003)
 box('Side mallet storage tray',(.633,0,.790),(.153,.401,.019),p['darkwood'],.004)
 for y in [-.130,.130]:
  rod('Parked xylophone mallet',(.596,y-.065,.810),(.653,y+.085,.810),.003,p['wood'],12)
  sphere('Mallet rubber head',(.653,y+.085,.810),(.016,.016,.016),p['rubber'],segments=20,rings=10)
 return ('city-framed-xylophone','架台付き教育用木琴','Framed educational xylophone','学校の音楽室や交流施設向けの架台付き木琴。長さを変えた20枚の木色バー、保持ボタンと支持コード、下側が開いた20本の共鳴管、台枠・支柱・四個の車輪、横のマレット置場と二本のばちを造形。バー・管・ばちを含む一式1点で、音域・調律された周波数を示す設計ではありません。音声、振動、可動機構や実楽器の音響性能は未検証です。','An educational xylophone prop on a wheeled frame for school music rooms and community facilities. It has 20 graduated wood-colored bars, retaining buttons/support cords, 20 bottom-open resonator tubes, frame/uprights/four wheels and a side tray with two mallets. Bars, tubes and mallets count within one assembly. No particular musical range or tuned frequencies are represented as an engineering claim. Audio, vibration, moving mechanisms and real acoustic performance are unvalidated.',['music','xylophone','school','木琴'])
BUILDERS=[upright_piano,guitar_stand,drum_set,framed_xylophone]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-037/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/community_music_instruments.py',azimuth=-55,elevation=24)
