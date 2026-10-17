"""Original community-room game furnishings for Xenoah. CC BY 4.0.
No third-party models, brands, logos, game artwork or textures.
Static whole assemblies; neither game mechanics nor real equipment certification.
"""
import math,sys,argparse,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def palette():
 return dict(wood=mat('Warm plain laminated wood color',(.38,.22,.11),0,.55),edge=mat('Pale wood edge color',(.61,.43,.25),0,.48),darkwood=mat('Dark sealed wood color',(.12,.073,.045),0,.52),steel=mat('Satin equipment steel',(.38,.43,.46),.72,.39),dark=mat('Graphite fittings',(.026,.033,.037),.2,.55),white=mat('Ivory playing surfaces',(.77,.77,.68),0,.55),black=mat('Charcoal playing surfaces',(.06,.075,.07),0,.58),green=mat('Muted green playing surface',(.07,.27,.19),0,.68),red=mat('Muted red game details',(.49,.075,.048),0,.48),blue=mat('Muted blue game details',(.055,.23,.39),0,.45),glass=mat('Inactive display glass appearance',(.025,.065,.074),.16,.22),rubber=mat('Black rubber',(.014,.018,.021),0,.78))
def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
 o=cylinder(n,p,r,d,m,v,bevel=b)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def rod(n,a,b,r,m,v=24):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bar(n,a,b,w,t,m,bev=.003):
 a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def sideplate(n,points,x,t,m,b=.003):
 k=len(points);vs=[(xx,y,z) for xx in [x-t/2,x+t/2] for y,z in points];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(n,vs,fs,m,b)
def ring(n,p,major,minor,m,axis='Z',v=40):
 bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=major,minor_radius=minor,location=p);o=bpy.context.object
 if axis=='X':o.rotation_euler[1]=math.pi/2
 elif axis=='Y':o.rotation_euler[0]=math.pi/2
 return finish(o,n,m,smooth=True)

def chess_table():
 p=palette()
 box('Chess table single slab',(0,0,.735),(.900,.900,.075),p['wood'],.018)
 box('Board raised perimeter',(0,0,.777),(.696,.696,.014),p['darkwood'],.006)
 for i in range(8):
  for j in range(8):box('Individual alternating chessboard square',((i-3.5)*.080,(j-3.5)*.080,.787),(.0794,.0794,.012),p['white'] if (i+j)%2==0 else p['black'],.0008)
 # One connected pedestal assembly carries the table and its two fixed seats.
 cyl('Table broad pedestal',(0,0,.380),.095,.668,p['steel'],v=40,b=.004)
 cyl('Under-table mounting plate',(0,0,.681),.185,.023,p['dark'],v=32,b=.003)
 box('Table ground beam',(0,0,.061),(1.600,.160,.090),p['steel'],.010)
 for x in [-.700,.700]:
  box('Seat support foot',(x,0,.037),(.360,.420,.056),p['steel'],.008)
  cyl('Seat pedestal',(x,0,.246),.051,.407,p['steel'],v=32,b=.003)
  box('Seat underside bearer',(x,0,.448),(.358,.330,.036),p['dark'],.006)
  for j in [-1,0,1]:box('Fixed seating wood slat',(x,j*.116,.480),(.418,.105,.044),p['edge'],.008)
  for y in [-.145,.145]:
   for xx in [-.140,.140]:cyl('Seat foot anchor head',(x+xx,y,.069),.012,.008,p['dark'],v=6,b=.001)
 for x in [-.12,.12]:
  for y in [-.12,.12]:cyl('Table plate fastening',(x,y,.665),.012,.009,p['steel'],v=6,b=.001)
 return ('city-fixed-chess-table','対面座席付きチェステーブル','Fixed chess table with facing seats','公園の交流スペースや集会室へ置く、二人用の対面座席と盤を一体化したテーブル。実形状の64マス、厚い天板、中央支柱、連結した脚梁、二座の木色スラットと取付金具を造形。盤・座席を含む一式を1点と数えます。駒・ルール処理・座席調整は含みません。実用品の耐荷重・安全性は未検証です。','A two-person chess-table assembly for park social areas and community rooms. The 64 individually modeled squares sit on a thick tabletop above a center pedestal and connected foot beam, with two opposing slatted seats and visible mountings. Board and seats belong to one counted assembly. Pieces, game logic and seat adjustment are absent. Real load capacity and safety are unvalidated.',['community','chess','table','チェス'])

def table_football():
 p=palette()
 # Four splayed legs carry a recessed playing box.
 for x in [-.31,.31]:
  for y in [-.52,.52]:
   bar('Splayed table football leg',(x*1.12,y*1.08,.045),(x,y,.675),.094,.094,p['darkwood'],.008)
   cyl('Leg leveling pad',(x*1.12,y*1.08,.028),.059,.040,p['rubber'],v=24,b=.004)
   for zz in [.572,.620]:cyl('Leg upper fastening',(x+(.053 if x>0 else -.053),y,zz),.012,.008,p['steel'],'X',v=6)
 for y in [-.40,.40]:box('Under-box cross bearer',(0,y,.630),(.708,.065,.065),p['darkwood'],.006)
 box('Playing field backing',(0,0,.697),(.640,1.188,.053),p['wood'],.008)
 box('Recessed flat playing field',(0,0,.726),(.630,1.180,.012),p['green'],.004)
 # Thin original field markings are actual raised strips, not external artwork.
 for x in [-.285,.285]:box('Field side line',(x,0,.733),(.004,1.120,.001),p['white'],.0001)
 for y in [-.555,0,.555]:box('Field cross line',(0,y,.733),(.570,.004,.001),p['white'],.0001)
 ring('Center field circle',(0,0,.734),.095,.002,p['white'],v=40)
 ys=[-.490,-.350,-.180,-.060,.060,.180,.350,.490]
 # Side walls have open rectangular shaft passages underneath round sleeves.
 for x in [-.347,.347]:
  for z in [.757,.849]:box('Long side wall continuous rail',(x,0,z),(.065,1.284,.036),p['wood'],.006)
  edges=[-.642]+ys+[.642]
  for j in range(len(edges)-1):
   lo=edges[j]+(.026 if j else 0);hi=edges[j+1]-(.026 if j<len(ys) else 0)
   box('Side wall segment between shaft holes',(x,(lo+hi)/2,.802),(.065,hi-lo,.058),p['wood'],.004)
  for y in ys:ring('Rod passage sleeve',(x,y,.803),.018,.005,p['dark'],'X',24)
 for y in [-.623,.623]:
  for x in [-.244,.244]:box('Goal end side panel',(x,y,.791),(.191,.058,.153),p['wood'],.007)
  box('Goal opening upper rail',(0,y,.855),(.300,.058,.027),p['edge'],.004)
  box('Goal rear catcher tray',(0,y*1.14,.709),(.298,.201,.034),p['dark'],.006)
  box('Goal catcher rear wall',(0,y*1.29,.763),(.298,.026,.120),p['darkwood'],.005)
  for x in [-.146,.146]:box('Goal catcher side cheek',(x,y*1.16,.763),(.025,.166,.120),p['darkwood'],.005)
  # A simple five-bead score counter is fixed, not a scoring mechanism.
  rod('Score bead spindle',(-.120,y,.899),(.120,y,.899),.004,p['steel'],16)
  for x in [-.134,.134]:box('Score spindle support',(x,y,.884),(.019,.022,.037),p['dark'],.003)
  for i in range(5):cyl('Fixed score bead',(-.075+i*.029,y,.899),.016,.019,p['red'] if y<0 else p['blue'],'X',v=20,b=.002)
 counts=[1,2,5,3,3,5,2,1]
 for j,y in enumerate(ys):
  team=p['red'] if j in [0,1,3,5] else p['blue'];sign=-1 if j in [0,1,3,5] else 1
  rod('Steel player rod',(-.515,y,.803),(.515,y,.803),.007,p['steel'])
  cyl('Rod hand grip',(sign*.546,y,.803),.019,.100,p['dark'],'X',v=28,b=.003)
  cyl('Rod far stop cap',(-sign*.526,y,.803),.013,.019,p['rubber'],'X',v=20)
  for x in [-.287,.287]:cyl('Rod bumper',(x,y,.803),.015,.038,p['rubber'],'X',v=20)
  count=counts[j]
  for i in range(count):
   x=(i-(count-1)/2)*(.100 if count==5 else .148)
   box('Fixed miniature player torso',(x,y,.804),(.042,.034,.055),team,.006)
   sphere('Miniature player head',(x,y,.849),(.018,.018,.020),p['edge'],segments=16,rings=8)
   box('Miniature player striking foot',(x,y-.004,.759),(.039,.031,.037),team,.003)
 sphere('Single parked table football ball',(.104,.093,.749),(.014,.014,.014),p['white'],segments=20,rings=10)
 return ('city-table-football','テーブルサッカー台','Table football game','交流室・宿泊施設の遊戯コーナー向けのテーブルサッカー台。凹んだ競技面と立体ライン、八本のロッド、固定した22人の選手、両端の実開口ゴールと受け皿、スコア用ビーズ、傾斜脚と調整足の外観を造形。選手・ボール・操作棒は台に含む一式で1点です。回転・スライド・得点処理・物理動作は未実装で、競技規格・実用品安全性は未検証です。','A table-football prop for community rooms and hospitality recreation corners. It includes a recessed field with modeled lines, eight rods, 22 fixed player figures, genuinely open end goals and catch trays, score beads, splayed legs and leveling-foot exteriors. Figures, ball and rods form one table assembly. Rotation, sliding, scoring and ball physics are not implemented; competitive specifications and real equipment safety are unvalidated.',['community','table-football','game','テーブルサッカー'])

def arcade_cabinet():
 p=palette()
 profile=[(-.410,.050),(.390,.050),(.390,1.840),(.205,1.880),(-.225,1.880),(-.305,1.790),(-.215,1.130),(-.400,1.015),(-.410,.900)]
 for x in [-.345,.345]:sideplate('Original arcade cabinet side profile',profile,x,.036,p['blue'],.010)
 box('Arcade base plinth',(0,-.010,.071),(.675,.775,.092),p['dark'],.009)
 for x in [-.279,.279]:
  for y in [-.310,.310]:cyl('Cabinet leveling foot',(x,y,.027),.033,.040,p['rubber'],v=24,b=.003)
 box('Rear service cabinet wall',(0,.376,.947),(.662,.026,1.710),p['darkwood'],.005)
 box('Front lower kick panel',(0,-.388,.380),(.663,.025,.590),p['blue'],.005)
 box('Front coin-service panel',(0,-.389,.755),(.661,.027,.155),p['dark'],.004)
 for x in [-.091,.091]:
  box('Coin slot surround',(x,-.412,.774),(.075,.025,.091),p['steel'],.005)
  box('Dark coin slit',(x,-.427,.787),(.006,.006,.043),p['dark'],.001)
  box('Coin return recess',(x,-.428,.742),(.047,.007,.021),p['black'],.001)
 # Screen is tilted and recessed inside a substantial bezel, with no game artwork.
 angle=math.radians(-8)
 for x in [-.290,.290]:box('Display vertical bezel',(x,-.202,1.411),(.072,.051,.628),p['dark'],.007,rot=(angle,0,0))
 for z in [1.120,1.702]:
  yy=-.202-math.sin(angle)*(z-1.411)
  box('Display horizontal bezel',(0,yy,z),(.560,.050,.059),p['dark'],.007,rot=(angle,0,0))
 box('Inactive blank arcade display',(0,-.181,1.411),(.512,.025,.520),p['glass'],.006,rot=(angle,0,0))
 box('Upper plain header front',(0,-.251,1.796),(.658,.031,.124),p['edge'],.007)
 box('Cabinet roof',(0,.014,1.858),(.666,.742,.033),p['blue'],.008)
 box('Control deck front apron',(0,-.392,.950),(.658,.035,.099),p['dark'],.006)
 box('Sloped control deck',(0,-.294,1.018),(.665,.274,.040),p['dark'],.007,rot=(math.radians(-8),0,0))
 cyl('Joystick mounting plate',(-.190,-.299,1.044),.043,.008,p['steel'],v=28,b=.001)
 rod('Static joystick shaft',(-.190,-.299,1.045),(-.190,-.299,1.120),.009,p['steel'],20)
 sphere('Joystick ball grip',(-.190,-.299,1.136),(.027,.027,.027),p['red'],segments=24,rings=12)
 for x,y,m in [(0,-.320,p['red']),(.066,-.320,p['red']),(.132,-.320,p['red']),(.032,-.248,p['blue']),(.098,-.248,p['blue']),(.164,-.248,p['blue'])]:
  cyl('Pushbutton outer collar',(x,y,1.048),.022,.008,p['steel'],v=28)
  cyl('Fixed arcade pushbutton',(x,y,1.056),.017,.014,m,v=28,b=.002)
 box('Rear removable access panel',(0,.397,.688),(.540,.018,.932),p['darkwood'],.006)
 for x in [-.246,.246]:
  for z in [.260,1.115]:cyl('Back service cover fastener',(x,.410,z),.007,.005,p['steel'],'Y',v=12,b=.0005)
 for z in [1.348+i*.042 for i in range(8)]:box('Rear ventilation louver',(0,.401,z),(.494,.018,.013),p['dark'],.002,rot=(math.radians(-20),0,0))
 box('Rear power inlet housing',(.205,.411,.163),(.083,.027,.056),p['dark'],.004)
 box('Recessed nonfunctional power socket',(.205,.428,.164),(.041,.007,.029),p['black'],.002)
 return ('city-upright-arcade-cabinet','汎用直立アーケード筐体','Generic upright arcade cabinet','遊戯施設や交流ラウンジ用に自作した汎用の直立ゲーム筐体。傾いた無表示画面と厚い枠、段付き操作面、固定ジョイスティックとボタン、硬貨口風の前面金具、背面サービス扉・通気部・電源口を造形。既存ゲームの画面・キャラクター・ロゴ・ブランドは使用していません。画面表示、入力、遊戯ソフト、電装・課金機能は含まず、実機性能や安全性は未検証です。','An originally designed upright arcade-cabinet prop for recreation venues and community lounges. It has a tilted blank display with thick bezel, stepped control deck, fixed joystick and buttons, coin-slot-like front fittings, rear service door, vents and power-inlet exterior. No existing game screens, characters, logos or brands are used. Display output, inputs, game software, electrical and payment functions are absent; real-device performance and safety are unvalidated.',['community','arcade','cabinet','ゲーム筐体'])

def dartboard_cabinet():
 p=palette()
 # Wall cabinet is presented open, with a raised back frame and hinged wings.
 box('Dart cabinet rear panel',(0,.065,.420),(.620,.026,.810),p['darkwood'],.008)
 for x in [-.301,.301]:box('Dart cabinet side rail',(x,0,.420),(.030,.145,.810),p['wood'],.006)
 for z in [.031,.809]:box('Dart cabinet top and bottom rail',(0,0,z),(.583,.145,.032),p['wood'],.006)
 cyl('Dartboard solid backing',(0,-.010,.461),.225,.043,p['dark'],'Y',v=80,b=.002)
 # Radial closed wedges create an original generic target with actual recessed gaps.
 def sector(name,r0,r1,a0,a1,material):
  steps=4;points=[(r1*math.cos(a0+(a1-a0)*i/steps),.461+r1*math.sin(a0+(a1-a0)*i/steps)) for i in range(steps+1)]+[(r0*math.cos(a0+(a1-a0)*i/steps),.461+r0*math.sin(a0+(a1-a0)*i/steps)) for i in range(steps,-1,-1)];k=len(points);vs=[(x,y,z) for y in [-.043,-.035] for x,z in points];fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)];return mesh(name,vs,fs,material)
 for i in range(20):
  a=i*math.tau/20;gap=.006
  for k,(lo,hi) in enumerate([(.018,.106),(.108,.119),(.121,.194),(.196,.208)]):sector('Individual target scoring wedge',lo,hi,a+gap,a+math.tau/20-gap,(p['red'] if i%2==0 else p['green']) if k%2 else (p['white'] if i%2==0 else p['black']))
 for r in [.017,.107,.120,.195,.209]:ring('Round target divider wire',(0,-.046,.461),r,.0011,p['steel'],'Y',80)
 for i in range(20):
  a=i*math.tau/20;rod('Radial target divider wire',(.018*math.cos(a),-.046,.461+.018*math.sin(a)),(.208*math.cos(a),-.046,.461+.208*math.sin(a)),.001,p['steel'],8)
 cyl('Target central bull ring',(0,-.044,.461),.016,.011,p['green'],'Y',v=32,b=0)
 cyl('Target central bull',(0,-.051,.461),.007,.006,p['red'],'Y',v=24,b=0)
 for side in [-1,1]:
  # Open cabinet doors rotate away from the front, preserving visible hinges.
  hinge=Vector((side*.315,-.058,.420));ang=math.radians(-side*60);direction=Vector((side*math.cos(ang),math.sin(ang)*side,0))
  center=hinge+direction*.148
  door=box('Fixed open dart cabinet door',center,(.296,.022,.785),p['wood'],.006,rot=(0,0,ang))
  inset=box('Plain door scoring inset',center+Vector((math.sin(ang)*.014,-math.cos(ang)*.014,0)),(.238,.009,.634),p['black'],.004,rot=(0,0,ang))
  for z in [.170,.680]:
   cyl('Cabinet door hinge barrel',(side*.314,-.057,z),.008,.089,p['steel'],v=20,b=.001)
   box('Hinge fixed leaf',(side*.294,-.067,z),(.035,.007,.063),p['steel'],.001)
  rod('Rear wall mounting crossbar',(side*.230,.094,.660),(side*.230,.094,.735),.009,p['steel'],20)
  cyl('Rear mounting head',(side*.230,.107,.710),.017,.012,p['steel'],'Y',v=6,b=.001)
 box('Dart storage shelf',(0,-.034,.112),(.510,.110,.025),p['edge'],.004)
 for x in [-.085,0,.085]:
  rod('Parked dart thin tip',(x,-.054,.125),(x,-.054,.162),.0014,p['steel'],12)
  cyl('Parked dart barrel',(x,-.054,.186),.005,.048,p['steel'],v=20,b=.0005)
  rod('Parked dart shaft',(x,-.054,.208),(x,-.054,.240),.0022,p['dark'],12)
  for angle in [0,math.pi/2]:box('Parked dart fixed flight',(x,-.054,.245),(.027,.0018,.030),p['red'],.0003,rot=(0,0,angle))
 return ('city-open-dartboard-cabinet','開いたダーツ収納キャビネット','Open dartboard cabinet','交流施設やラウンジの壁へ掛ける、開いたダーツ盤収納キャビネット。放射状の色分けターゲット、実形状の細い区切り線、固定した両開き扉と無地の記録面、蝶番、収納棚と三本の固定ダーツ、背面壁取付部を造形。点数数字・ブランド・得点処理はありません。盤とダーツを含む一式で1点です。壁の設置高さは利用側で調整します。投擲・判定・扉操作や実用品安全性は未検証です。','An open wall-mounted dartboard cabinet for community facilities and lounges. It includes a radially segmented color target, modeled fine divider wires, fixed open doors with blank scoring surfaces, hinges, storage shelf, three parked darts and rear wall fittings. Score numerals, brands and scoring logic are absent. Board and darts count as one cabinet assembly. Set wall placement height in the scene. Throwing, hit detection, door motion and real equipment safety are unvalidated.',['community','darts','wall-cabinet','ダーツ'])
BUILDERS=[chess_table,table_football,arcade_cabinet,dartboard_cabinet]
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-034/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
 if a.geometry_only:
  import common
  common.render=lambda *args,**kwargs:None
 for fn in BUILDERS:
  reset();s=fn()
  if a.only and s[0]!=a.only:continue
  publish_asset(*s,out,'scripts/city_expansion/community_game_furnishings.py',azimuth=-55,elevation=30)
