"""Original Meshcopia wheelbarrow and outdoor telephone visual props, CC BY 4.0."""
import argparse,math,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import common as C
from mathutils import Vector

def materials():
 return {k:C.mat(k,c,m,r) for k,c,m,r in [('paint',(.045,.15,.105),.45,.38),('steel',(.39,.44,.46),.78,.32),('rubber',(.025,.032,.035),0,.72),('cream',(.65,.67,.62),.22,.4),('dark',(.045,.06,.065),.3,.45),('yellow',(.68,.46,.055),.35,.4),('glass',(.045,.12,.13),.4,.2)]}
def box(name,loc,size,mat,bevel=.005):return C.box(name,loc,size,mat,bevel)
def cyl(name,loc,r,d,mat,axis='Z',vertices=32):return C.cylinder(name,loc,r,d,mat,vertices,{'X':(0,math.pi/2,0),'Y':(math.pi/2,0,0),'Z':None}[axis],min(.002,r/8,d/8))
def rod(name,a,b,r,mat):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,mat);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def loop(w,l,z,cy=0,roundness=.06):
 p=[]
 for cx,yy,start in [(w/2-roundness,l/2-roundness,0),(-w/2+roundness,l/2-roundness,90),(-w/2+roundness,-l/2+roundness,180),(w/2-roundness,-l/2+roundness,270)]:
  for n in range(5):
   a=math.radians(start+n*90/4);p.append((cx+roundness*math.cos(a),cy+yy+roundness*math.sin(a),z))
 return p

def wheelbarrow(M):
 # Closed thin shell, not a solid opaque block hiding the open interior.
 rings=[loop(.38,.54,.43,-.10,.06),loop(.69,.94,.78,-.10,.085),loop(.665,.915,.775,-.10,.08),loop(.355,.515,.448,-.10,.055)]
 verts=sum(rings,[]);n=len(rings[0]);faces=[]
 for k in range(3):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 faces += [tuple(reversed(range(n))),tuple(3*n+j for j in range(n))]
 C.mesh('Pressed open load tub with inner shell',verts,faces,M['paint'],.003)
 rim=rings[1];C.tube('Continuous rolled tub rim',rim+[rim[0]],.012,M['paint'],2)
 for x in [-.18,.18]:
  C.tube('Single continuous support and handle rail',[(x,-.59,.24),(x,-.35,.35),(x,.23,.43),(x,.57,.62),(x,.97,.80)],.021,M['steel'],2)
  rod('Replaceable rubber handle grip',(x,.78,.715),(x,.99,.81),.028,M['rubber'])
  C.tube('Bent parking leg with ground return',[(x,.30,.469),(x,.47,.019),(x,.65,.019),(x,.54,.603)],.019,M['steel'],2)
  rod('Leg diagonal reinforcing strut',(x,.58,.08),(x,.19,.40),.012,M['steel'])
  box('Tub underside longitudinal saddle',(x,-.05,.425),(.055,.46,.028),M['paint'],.006)
 for y,z in [(.45,.06),(.23,.43),(-.38,.36)]:rod('Transverse support brace',(-.20,y,z),(.20,y,z),.015,M['steel'])
 C.torus('Rounded single pneumatic tire',(0,-.59,.25),.19,.06,M['rubber'],rotation=(0,math.pi/2,0),segments=48)
 cyl('Stamped wheel rim',(0,-.59,.25),.163,.085,M['cream'],'X',48)
 for sign in [-1,1]:
  cyl('Inset dished wheel center',(sign*.046,-.59,.25),.115,.008,M['steel'],'X',32)
  cyl('Wheel hub cap',(sign*.062,-.59,.25),.047,.026,M['cream'],'X',24)
  for j in range(6):
   a=j*math.tau/6;cyl('Recessed hub ventilation detail',(sign*.051,-.59+.082*math.sin(a),.25+.082*math.cos(a)),.017,.005,M['dark'],'X',12)
 rod('Through wheel axle',(-.23,-.59,.25),(.23,-.59,.25),.016,M['steel'])
 for x in [-.215,.215]:cyl('Axle retention hex head',(x,-.59,.25),.024,.014,M['steel'],'X',6)
 # Broad pressed side channels follow the sloped bowl walls.
 for sign in [-1,1]:
  for y in [-.28,.12]:rod('Pressed tub side stiffening bead',(sign*.20,y,.47),(sign*.31,y,.71),.006,M['paint'])


def key_glyph(cx,cz,label,material):
 # Original line-built numerals, not a bundled or external font.
 w,h=.0065,.0085
 segments={'a':(-w,h,w,h),'b':(w,h,w,0),'c':(w,0,w,-h),'d':(-w,-h,w,-h),'e':(-w,0,-w,-h),'f':(-w,h,-w,0),'g':(-w,0,w,0)}
 patterns={'0':'abcdef','1':'bc','2':'abged','3':'abgcd','4':'fgbc','5':'afgcd','6':'afgecd','7':'abc','8':'abcdefg','9':'abfgcd'}
 lines=[segments[k] for k in patterns[label]] if label in patterns else [(-w,0,w,0),(-w,-h,w,h),(-w,h,w,-h)] if label=='*' else [(-w,-.003,w,-.003),(-w,.003,w,.003),(-.003,-h,-.003,h),(.003,-h,.003,h)]
 vertices=[];faces=[]
 for x1,z1,x2,z2 in lines:
  dx,dz=x2-x1,z2-z1;l=math.hypot(dx,dz);px,pz=-dz/l*.0008,dx/l*.0008;n=len(vertices)
  vertices += [(cx+x1-px,-.1645,cz+z1-pz),(cx+x2-px,-.1645,cz+z2-pz),(cx+x2+px,-.1645,cz+z2+pz),(cx+x1+px,-.1645,cz+z1+pz)];faces.append((n,n+1,n+2,n+3))
 C.mesh('Original keypad numeral '+label,vertices,faces,material)

def telephone(M):
 box('Ground anchor footplate',(0,0,.025),(.36,.29,.05),M['steel'],.012)
 box('Hollow service pedestal',(0,.025,.47),(.17,.14,.87),M['paint'],.012)
 box('Pedestal access panel',(0,.101,.43),(.125,.006,.40),M['dark'],.004)
 for x in [-.135,.135]:
  for y in [-.095,.095]:cyl('Foundation anchor hex',(x,y,.058),.014,.017,M['steel'],vertices=6)
 box('Telephone weatherproof cabinet',(0,0,1.16),(.37,.23,.52),M['paint'],.022)
 box('Front gasket seam',(0,-.121,1.16),(.335,.009,.475),M['dark'],.014)
 box('Inset brushed metal face',(0,-.13,1.16),(.322,.012,.46),M['steel'],.012)
 # Folded rain hood has genuine thickness and open front.
 box('Rain hood roof',(0,-.06,1.447),(.43,.36,.025),M['paint'],.012)
 for x in [-.207,.207]:box('Protective rain hood side',(x,-.085,1.25),(.022,.31,.38),M['paint'],.009)
 box('Header display bezel',(.05,-.145,1.329),(.158,.018,.072),M['dark'],.008)
 box('Blank nonfunctional information display',(.05,-.157,1.329),(.137,.006,.052),M['glass'],.004)
 for row in range(4):
  for col in range(3):
   x=.005+col*.045;z=1.252-row*.045
   box('Keypad recessed key socket',(x,-.143,z),(.035,.012,.034),M['dark'],.004)
   box('Raised tactile keypad key',(x,-.156,z),(.026,.016,.025),M['cream'],.004)
   key_glyph(x,z,'123456789*0#'[row*3+col],M['dark'])
 cyl('Keypad center tactile pip',(.05,-.166,1.207),.003,.003,M['dark'],'Y',12)
 box('Narrow card entry bezel',(.048,-.15,1.018),(.125,.018,.028),M['dark'],.004)
 box('Card entry recess',(.048,-.162,1.018),(.096,.006,.006),M['rubber'],.001)
 # Handset sits visibly in separate upper and lower cradle hooks.
 for z in [1.29,1.085]:box('Handset cradle hook',(-.116,-.158,z),(.069,.048,.025),M['dark'],.006)
 C.tube('Curved telephone handset spine',[(-.113,-.192,1.31),(-.123,-.217,1.27),(-.123,-.221,1.14),(-.113,-.192,1.09)],.024,M['rubber'],3)
 for z in [1.31,1.09]:
  C.sphere('Handset receiver cup',(-.113,-.194,z),(.043,.028,.034),M['rubber'],24,12)
  for j in range(5):cyl('Receiver perforation',(-.139+j*.013,-.222,z),.0025,.002,M['dark'],'Y',8)
 pts=[(-.106,-.20,1.066)]
 for j in range(121):
  t=j/120;pts.append((-.105+.009*math.cos(t*math.tau*18),-.19+.009*math.sin(t*math.tau*18),1.055-.30*t))
 for j in range(17):
  t=j/16;angle=math.pi+t*math.pi;pts.append((-.065+.04*math.cos(angle),-.19+.055*t,.755+.04*math.sin(angle)))
 pts += [(-.025,-.135,.79),(-.025,-.132,.91)]
 C.tube('Continuous coiled handset cable',pts,.0032,M['rubber'],1)
 for z in [1.00,1.30]:cyl('Rear service hinge knuckle',(.18,.085,z),.009,.07,M['steel'],vertices=16)
 box('Rear cabinet service door',(0,.119,1.16),(.31,.008,.43),M['paint'],.009)
 for x in [-.12,.12]:
  for z in [.99,1.33]:cyl('Rear access screw',(x,.127,z),.006,.006,M['steel'],'Y',12)
 for x in [-.16,.16]:
  for z in [.956,1.364]:cyl('Faceplate tamper-resistant fastener',(x,-.142,z),.006,.006,M['steel'],'Y',12)

ASSETS=[('city-construction-wheelbarrow','建設用一輪手押し車','Construction wheelbarrow','深い開放荷台、一本の車輪、支持脚と長い取っ手を備えた土砂・園芸資材用の一輪車。買物カートやパレット運搬車とは異なる用途の静的モデル。','Open deep-tray single-wheel barrow for loose soil and landscaping material, with folded support legs and long handles. Distinct from basket shopping trolleys and pallet jacks; static visual model with no load rating.',wheelbarrow,['wheelbarrow','construction','landscaping','一輪車']),('city-public-telephone','屋外公衆電話ポスト','Outdoor public telephone pedestal','雨よけ、受話器、連続したコイルコード、操作キーと点検扉を持つ汎用屋外電話。通話や決済機能のない静的モデル。','Unbranded weatherproof telephone on a service pedestal, with open rain hood, cradled handset, continuous coiled cord, tactile keypad and rear service door. Static visual prop without calling or payment functionality.',telephone,['telephone','communication','street','公衆電話'])]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--only',choices=[a[0] for a in ASSETS]);args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
 for slug,ja,en,dj,de,fn,tags in ASSETS:
  if args.only and args.only!=slug:continue
  if (args.output/slug).exists():p.error('Refusing to overwrite '+slug)
  C.reset();fn(materials());C.publish_asset(slug,ja,en,dj,de,tags,args.output,'scripts/city/compact_utilities.py',azimuth=-55,elevation=25 if 'telephone' in slug else 30)
