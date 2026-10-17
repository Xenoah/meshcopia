"""Original countertop snack-service equipment scene props. Xenoah, CC BY 4.0.
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
 p=pal();p['paint']=mat('Deep red enamel cabinet',(.44,.025,.026),.12,.36);p['cream']=mat('Warm cream enamel',(.72,.68,.53),.10,.39)
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

def cotton_candy_machine():
 p=snack_palette();feet(p,.151,.113)
 box('Cotton candy machine base',(0,0,.122),(.421,.344,.171),p['paint'],.022)
 box('Spinner base upper metal tray',(0,0,.213),(.435,.358,.026),p['steel'],.009)
 profile_body('Open flared cotton candy bowl',[(.215,.224),(.255,.252),(.320,.393),(.335,.430),(.335,.445),(.326,.445),(.326,.431),(.312,.399),(.245,.262),(.208,.239),(.030,.239),(.030,.224)],p['steel'],64)
 cyl('Cotton bowl closed floor',(0,0,.232),.212,.018,p['steel'],v=48,b=.002)
 cyl('Fixed center spinner support',(0,0,.260),.034,.065,p['dark'],v=28,b=.002)
 cyl('Fixed cotton spinner drum',(0,0,.303),.073,.062,p['steel'],v=40,b=.004)
 sleeve('Spinner upper open sugar collar',(0,0,.342),.059,.042,.025,p['steel'],v=36)
 cyl('Visible sugar cavity dark floor',(0,0,.330),.043,.006,p['dark'],v=32,b=0)
 for i in range(20):
  a=i*math.tau/20;box('Spinner side rib',(.074*math.cos(a),.074*math.sin(a),.304),(.004,.009,.034),p['dark'],.001,rot=(0,0,a))
 control_knob('Spinner control',.099,-.178,.130,.025,p)
 for x in [-.117,-.060]:box('Fixed unmarked rocker switch',(x,-.178,.134),(.027,.018,.037),p['dark'],.004)
 for x in [-.211,.211]:
  for y in [-.080,.080]:box('Bowl retaining catch',(x,y,.213),(.030,.025,.036),p['dark'],.003)
 for x in [-.12,-.08,-.04,0,.04,.08,.12]:box('Rear motor ventilation inset',(x,.176,.120),(.018,.012,.052),p['dark'],.002)
 power_inlet('Spinner',.135,.180,.077,p)
 return ('city-cotton-candy-machine','開放ボウル付き綿菓子機','Open-bowl cotton candy machine','公園売店や催事カウンターに配置する綿菓子機。厚みを持つ広がった金属ボウルと実際の凹んだ内側、中央の固定スピナーヘッド/砂糖口、赤い基台、操作つまみ/スイッチ、四脚ゴム足、裏側吸排気外形と電源口を造形しています。綿菓子・砂糖・棒は付属しません。台上配置用に高さを調整してください。加熱・回転・食品処理を実装した機器設計ではない、静的な一式1点です。','A cotton-candy machine for park concessions and event counters. It has a thick flared metal bowl with genuinely recessed interior, fixed central spinner head and sugar opening, red base, knobs/switches, four rubber feet, rear ventilation exteriors and power inlet. No candy, sugar or sticks are included. Adjust its installation height for a counter. This is one static assembly, not a functioning heating, spinning or food-processing design.',['concession','cotton-candy','countertop','綿菓子機'])

def popcorn_machine():
 p=snack_palette();feet(p,.252,.193,.022,.026)
 box('Popcorn cabinet base',(0,0,.110),(.622,.492,.146),p['paint'],.014)
 box('Cabinet interior collecting floor',(0,0,.190),(.578,.446,.028),p['steel'],.005)
 for x in [-.298,.298]:
  for y in [-.233,.233]:box('Popcorn cabinet connected corner post',(x,y,.527),(.031,.031,.692),p['paint'],.005)
 for x in [-.291,.291]:box('Actual transparent side pane',(x,0,.526),(.007,.438,.641),p['glass'],.001)
 box('Actual transparent front pane',(0,-.233,.526),(.566,.007,.641),p['glass'],.001)
 for x in [-.142,.142]:
  box('Closed transparent rear service door',(x,.233,.526),(.276,.007,.641),p['glass'],.001)
  box('Rear service door lower rail',(x,.235,.211),(.278,.019,.020),p['steel'],.002)
  for z in [.330,.716]:cyl('Rear service door hinge',(-.287 if x<0 else .287,.247,z),.012,.055,p['steel'],v=20,b=.001)
  xx=-.025 if x<0 else .025
  for z in [.485,.545]:rod('Door handle mounting stem',(xx,.235,z),(xx,.265,z),.006,p['steel'],16)
  rod('Rear door vertical handle',(xx,.265,.485),(xx,.265,.545),.008,p['dark'],20)
 box('Popcorn cabinet top fascia',(0,0,.904),(.680,.550,.103),p['paint'],.013)
 box('Raised canopy cap',(0,0,.973),(.615,.492,.044),p['cream'],.010)
 box('Blank front canopy panel',(0,-.281,.906),(.482,.014,.066),p['cream'],.008)
 cyl('Kettle motor and hanging shaft',(0,.025,.800),.030,.140,p['steel'],v=28,b=.003)
 rod('Connected fixed kettle agitator spindle',(0,.025,.746),(0,.025,.625),.009,p['steel'],24)
 box('Kettle support crossbar',(0,0,.834),(.428,.038,.035),p['steel'],.004)
 for x in [-.193,.193]:rod('Kettle hanging bracket',(x,0,.836),(x,0,.663),.010,p['steel'],20)
 profile_body('Open popcorn kettle',[(.112,.586),(.137,.604),(.148,.665),(.148,.694),(.140,.694),(.140,.667),(.129,.614),(.106,.600),(.025,.600),(.025,.586)],p['steel'],48)
 cyl('Kettle floor',(0,0,.594),.113,.018,p['steel'],v=36,b=.002)
 cyl('Kettle transverse pivot',(0,0,.665),.012,.409,p['steel'],'X',v=24,b=.001)
 rod('Kettle tilt handle',(.200,0,.665),(.249,-.062,.665),.012,p['dark'],24)
 box('Kettle fixed split lid',(0,.072,.700),(.231,.131,.015),p['steel'],.004)
 for x in [-.155,-.102]:box('Canopy fixed rocker',(x,.282,.907),(.030,.016,.034),p['dark'],.003)
 box('Front crumb drawer face',(0,-.251,.115),(.486,.014,.067),p['cream'],.005)
 for x in [-.082,.082]:rod('Drawer handle post',(x,-.255,.115),(x,-.282,.115),.006,p['steel'],16)
 rod('Drawer pull grip',(-.082,-.282,.115),(.082,-.282,.115),.009,p['dark'],24)
 power_inlet('Popcorn cabinet',.191,.253,.089,p)
 return ('city-countertop-popcorn-machine','透明筐体の卓上ポップコーン機','Glazed countertop popcorn machine','売店や映画館のカウンターに配置するポップコーン機。四隅の支柱と天蓋、実際に透過する側面/前面/閉じた後扉、内側の吊り下げ釜と軸・ブラケット・半蓋、底の受け面、引出し取手、後扉の蝶番/握り、裏面電源口を一式に造形しています。GLBのガラスは淡いアルファ透過で屈折表現ではありません。ポップコーン、発光、加熱/撹拌/扉動作は付属しません。台の高さに合わせて配置する静的小物で、食品機器としての機能や適合を示しません。','A popcorn machine for concession or cinema counters. It includes corner posts/canopy, genuinely transparent side/front panes and closed rear doors, a suspended kettle with shaft, brackets and half lid, collection floor, drawer pull, rear hinges/handles and power inlet. GLB glazing uses light alpha blending rather than refraction. No popcorn, illumination, heating/stirring or door motion is included. Adjust placement to counter height; this static prop is not a functioning or certified food appliance.',['concession','popcorn','transparent-cabinet','ポップコーン機'])

def vertical_rotisserie():
 p=snack_palette();feet(p,.175,.163,.022,.025)
 box('Rotisserie countertop base',(0,0,.076),(.438,.428,.083),p['steel'],.012)
 # Open drip tray assembled from a real floor and connected raised perimeter.
 box('Rotisserie drip tray floor',(0,-.046,.123),(.408,.493,.020),p['steel'],.005)
 for x in [-.198,.198]:box('Raised drip tray side',(x,-.046,.145),(.015,.493,.047),p['steel'],.004)
 for y in [-.285,.193]:box('Raised drip tray end',(0,y,.145),(.408,.015,.047),p['steel'],.004)
 box('Vertical rear heater plenum',(0,.146,.494),(.357,.135,.706),p['steel'],.012)
 for z in [.278,.470,.662]:
  box('Unlit rectangular heater surround',(0,.072,z),(.302,.028,.164),p['dark'],.006)
  box('Opaque ceramic heater tile',(0,.053,z),(.276,.018,.140),p['cream'],.005)
  for x in [-.104,-.052,0,.052,.104]:
   rod('Fixed unlit heater element',(x,.041,z-.052),(x,.041,z+.052),.0035,p['steel'],12)
 box('Top drive motor exterior',(0,.055,.879),(.172,.293,.087),p['white'],.011)
 rod('Stationary vertical food spit',(0,-.059,.157),(0,-.059,.886),.008,p['steel'],24)
 cyl('Lower spit support bearing',(0,-.059,.153),.029,.051,p['dark'],v=28,b=.003)
 cyl('Spit empty support disc',(0,-.059,.231),.092,.013,p['steel'],v=36,b=.002)
 for z in [.247,.739]:
  cyl('Fixed spit fork clamp',(0,-.059,z),.016,.030,p['steel'],v=24,b=.001)
  rod('Continuous spit fork cross-arm',(-.038,-.059,z),(.038,-.059,z),.0045,p['steel'],16)
  for x in [-.038,.038]:
   rod('Spit fork prong',(x,-.059,z),(x,-.059,z+(.072 if z<.4 else -.072)),.0035,p['steel'],16)
 for z in [.343,.548,.752]:control_knob('Rotisserie heat control',.183,.142,z,.022,p)
 # Knobs face sideways; create each control as X-axis parts instead of fake front projections.
 for o in list(bpy.context.scene.objects):
  if o.name.startswith('Rotisserie heat control'):
   # Rotate the assembled front-oriented control about its cabinet-side center.
   pivot=Vector((.183,.142,float(o.location.z)))
   delta=o.location-pivot;o.location=pivot+Vector((-delta.y,delta.x,delta.z));o.rotation_euler.z+=math.pi/2
 for i in range(8):box('Rear heater ventilation inset',(-.122+i*.035,.218,.736),(.017,.012,.086),p['dark'],.002)
 power_inlet('Rotisserie',.112,.220,.212,p)
 return ('city-vertical-rotisserie-spit','縦型回転焼き機の外観','Vertical rotisserie spit appliance','飲食店の調理台に配置する縦型回転焼き機の外観です。空の縦串と固定フォーク/受け皿、上側駆動部外装、三段の非発光ヒーター面、側面つまみ、実際に凹んだ周縁付き油受け、ゴム脚と背面通気/電源口を造形。肉や食品は含まず、一式1点です。台上設置高さはシーン側で調整してください。回転・加熱・排煙や食品機器の安全性能は未実装・未検証です。','A vertical rotisserie exterior for restaurant counters. It has an empty vertical spit with fixed forks/support disc, upper drive housing, three unlit heater faces, side controls, a genuinely recessed rimmed drip tray, rubber feet and rear vent/power details. No meat or food is supplied; all parts count as one model. Adjust counter placement height. Rotation, heating, ventilation and food-appliance safety performance are unimplemented and untested.',['kitchen','vertical-rotisserie','spit','縦型焼き機'])

def conveyor_toaster():
 p=snack_palette();feet(p,.185,.160,.027,.024)
 box('Toaster lower service base',(0,.026,.105),(.468,.470,.123),p['steel'],.013)
 for x in [-.221,.221]:box('Toaster deep side housing',(x,.026,.274),(.042,.470,.330),p['steel'],.010)
 box('Toaster upper insulated roof',(0,.026,.445),(.468,.470,.045),p['steel'],.011)
 box('Toaster rear upper body',(0,.245,.329),(.429,.032,.219),p['steel'],.008)
 # A genuine horizontal front loading opening above an open wire belt.
 for y in [-.257+i*.020 for i in range(26)]:rod('Fixed conveyor cross-wire',(-.195,y,.232),(.195,y,.232),.003,p['steel'],12)
 for x in [-.195,.195]:rod('Conveyor side link bar',(x,-.267,.232),(x,.253,.232),.005,p['dark'],16)
 for y in [-.247,.230]:cyl('Conveyor end roller',(0,y,.224),.022,.398,p['steel'],'X',v=28,b=.002)
 box('Front loading ledge',(0,-.274,.208),(.414,.068,.022),p['steel'],.004)
 for x in [-.196,.196]:box('Loading guide rail',(x,-.289,.245),(.018,.147,.021),p['steel'],.003)
 # Downward sloped discharge chute below the belt, open in front.
 box('Sloped toast return chute',(0,-.247,.142),(.396,.258,.017),p['steel'],.004,rot=(math.radians(15),0,0))
 for x in [-.195,.195]:box('Chute raised guide',(x,-.247,.157),(.014,.258,.034),p['steel'],.003,rot=(math.radians(15),0,0))
 box('Upper front control strip',(0,-.217,.371),(.419,.026,.082),p['white'],.006)
 for x in [-.124,0,.124]:control_knob('Toaster unnumbered fixed dial',x,-.235,.372,.025,p)
 for x in [-.145,-.104,-.063,-.022,.019,.060,.101,.142]:box('Roof ventilation dark inset',(x,.044,.471),(.017,.175,.009),p['dark'],.002)
 for x in [-.110,.110]:bolt('Rear housing screw',(x,.262,.340),.008,p['bright'],'Y')
 power_inlet('Toaster',.130,.267,.107,p)
 return ('city-conveyor-belt-toaster','コンベア式卓上トースター','Countertop conveyor-belt toaster','ホテル朝食会場や食堂の調理台に置くコンベア式トースター。上部の装填開口と固定ワイヤーベルト、端のローラー/ガイド、下側の傾斜した返却シュート、三つの無目盛ダイヤル、天面通気外形、裏面の留め具/電源口と四脚を造形しています。ワイヤーは実ジオメトリで、ベルトや食品は動きません。パンは含まず一式1点。カウンターの高さに合わせて配置し、加熱・搬送・食品安全の機能を持たない静的小物として使用してください。','A conveyor toaster for hotel breakfast counters and cafeterias. It has an upper loading opening with a fixed geometric wire belt, end rollers/guides, a lower sloped return chute, three unnumbered dials, top ventilation exteriors, rear fasteners/power inlet and four feet. The wires are real geometry; belt and food motion are absent. No bread is supplied and the assembly counts once. Adjust counter placement height and use as a static prop without heating, transport or food-safety functionality.',['kitchen','conveyor-toaster','countertop','トースター'])

BUILDERS=[cotton_candy_machine,popcorn_machine,vertical_rotisserie,conveyor_toaster]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-055/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/snack_service_equipment.py',azimuth=-55,elevation=27)
