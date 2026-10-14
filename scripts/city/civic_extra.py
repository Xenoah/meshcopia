"""Original city service and transit props, CC BY 4.0. No third-party meshes/fonts."""
import bpy, math, sys, argparse, json
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).parent))
import common
import civic as g


def materials():
 g.materials()
 for name,color,metal,rough in [
  ('enamel-blue',(.035,.14,.23,1),.4,.34),('postal-red',(.45,.055,.035,1),.35,.4),
  ('safety-green',(.10,.58,.25,1),.15,.35),('hose',(.57,.40,.20,1),0,.82),
  ('brass',(.50,.32,.09,1),.75,.30),('can-silver',(.65,.69,.71,1),.8,.27),
  ('can-orange',(.72,.25,.045,1),.35,.38),('glass',(.42,.63,.66,.08),0,.12),
  ('screen-glass',(.10,.17,.18,.07),0,.10)]:
  m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=color
  p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=color[3]
  if color[3]<1:
   if hasattr(m,'surface_render_method'):m.surface_render_method='DITHERED'
   elif hasattr(m,'blend_method'):m.blend_method='BLEND'
   m.use_backface_culling=True
  g.M[name]=m
 m=bpy.data.materials.new('stock-led');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.8,.88,.85,1);p.inputs['Emission Color'].default_value=(.8,.88,.85,1);p.inputs['Emission Strength'].default_value=3;g.M['stock-led']=m


def prism(name,profile,depth,y,mat,bevel=.005):
 """Closed XZ outline extruded along Y; small bevels applied by civic helper."""
 n=len(profile);v=[(x,y+side*depth/2,z) for side in [-1,1] for x,z in profile]
 f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
 for i in range(n):j=(i+1)%n;f.append((i,j,j+n,i+n))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);return g.finish(o,name,mat,bevel)


def panel_frame(name,x,y,z,w,h,mat='graphite',rail=.028):
 for xx in [x-w/2,x+w/2]:g.box(name+' upright',(xx,y,z),(rail,.032,h+rail),mat,.003)
 for zz in [z-h/2,z+h/2]:g.box(name+' rail',(x,y,zz),(w,.032,rail),mat,.003)


def short_arc(name,cx,y,cz,r,start,end,mat='steel',thickness=.004):
 points=[(cx+r*math.cos(start+(end-start)*i/20),y,cz+r*math.sin(start+(end-start)*i/20)) for i in range(21)]
 return common.tube(name,points,thickness,g.M[mat],resolution=2)


def vending():
 g.feet(.99,.73)
 g.box('Recessed base plinth',(0,0,.095),(.99,.73,.12),'graphite',.025)
 g.box('Rear insulated cabinet',(0,.335,1.025),(.97,.055,1.78),'enamel-blue',.02)
 for x in [-.46,.46]:g.box('Folded cabinet side',(x,0,1.025),(.055,.70,1.78),'enamel-blue',.018)
 g.box('Top insulated cabinet',(0,0,1.90),(.99,.73,.075),'enamel-blue',.025)
 g.box('Base internal shelf',(0,0,.22),(.90,.66,.09),'graphite',.014)
 # Display compartment is actually open between frame and rear liner.
 g.box('Display dark back',(-.145,.24,1.18),(.60,.03,1.12),'dark',.006)
 for x in [-.444,.159]:g.box('Display return side',(x,-.03,1.18),(.022,.55,1.17),'graphite',.005)
 for row,z in enumerate([.70,.96,1.22,1.48]):
  g.box('Stock shelf',(-.145,-.015,z-.07),(.59,.47,.024),'steel',.004)
  g.box('Shelf price rail',(-.145,-.259,z-.056),(.59,.025,.034),'graphite',.003)
  for col,x in enumerate([-.35,-.215,-.08,.055]):
   # Cans with rolled rim and independent blank color sleeve.
   g.cyl('Stocked can body',(x,-.08,z+.035),.043,.16,'can-silver',verts=24,b=.004)
   g.cyl('Original color sleeve',(x,-.08,z+.030),.0438,.110,['blue','can-orange','green','cream'][col],verts=24,b=.001)
   g.torus('Can rolled rim',(x,-.08,z+.116),.039,.003,'steel',segments=24)
   g.box('Can pull tab',(x,-.08,z+.118),(.012,.022,.002),'graphite',.001)
   g.box('Blank shelf ticket',(x,-.275,z-.056),(.062,.003,.017),'cream',.001)
  g.box('Shelf stop bar',(-.145,-.205,z-.007),(.56,.012,.012),'steel',.002)
 for xx in [-.414,.124]:g.box('Internal stock lighting',(xx,-.23,1.18),(.008,.008,1.08),'stock-led',.001)
 g.box('Display glass',(-.145,-.305,1.18),(.596,.008,1.15),'screen-glass',.001)
 panel_frame('Display door seal',-.145,-.315,1.18,.615,1.18,'rubber',.025)
 panel_frame('Display door frame',-.145,-.33,1.18,.65,1.22,'steel',.035)
 for z in [.72,1.62]:g.cyl('Front door hinge',(-.468,-.315,z),.012,.12,'steel',b=.002)
 g.box('Payment fascia',(.325,-.337,1.175),(.252,.055,1.36),'enamel-blue',.022)
 g.box('Payment screen surround',(.325,-.373,1.56),(.18,.02,.17),'dark',.012)
 g.box('Payment display',(.325,-.385,1.57),(.145,.004,.12),'screen',.006)
 for z in [1.59,1.56]:g.box('Display status line',(.325,-.389,z),(.10,.002,.008),'light',.001)
 for row in range(3):
  for col in range(3):g.box('Selection keypad key',(.27+col*.055,-.379,1.35-row*.05),(.038,.014,.031),'steel',.005)
 g.box('Coin inlet bezel',(.325,-.38,1.13),(.12,.02,.04),'steel',.006)
 g.box('Coin inlet slot',(.325,-.392,1.13),(.075,.003,.006),'dark',.001)
 g.box('Card reader',(.325,-.38,.995),(.13,.02,.12),'dark',.012)
 for radius in [.015,.026,.037]:short_arc('Tap reader arc',.304,-.394,.995,radius,-.8,.8,'steel',.002)
 g.lock('Cash service lock',.40,-.38,.84)
 g.box('Lower delivery surround',(0,-.33,.36),(.87,.07,.26),'enamel-blue',.025)
 g.box('Collection pocket',(-.115,-.374,.365),(.56,.022,.16),'dark',.02)
 g.box('Collection tray',(-.115,-.408,.292),(.59,.09,.025),'steel',.008)
 g.box('Delivery flap',(-.115,-.39,.424),(.54,.018,.05),'steel',.007)
 for x in [.20,.245,.29,.335,.38]:g.box('Compressor vent',(x,-.37,.36),(.018,.006,.13),'dark',.003)
 g.box('Rear compressor panel',(0,.367,.41),(.72,.02,.43),'graphite',.015)
 for z in [.28,.33,.38,.43,.48]:g.box('Rear cooling louver',(0,.382,z),(.55,.025,.015),'steel',.003)
 for x in [-.32,.32]:
  for z in [.23,.59]:g.bolt('Rear access screw',(x,.38,z),(0,1,0),.005)


def postal():
 g.feet(.60,.49)
 g.box('Postal ground plinth',(0,0,.11),(.60,.49,.13),'graphite',.018)
 g.box('Mail storage body',(0,0,.64),(.55,.445,1.0),'postal-red',.025)
 # Separate arch canopy above a genuine deep slot, not a painted rectangle.
 profile=[(-.29,1.225),(.29,1.225)]
 profile +=[(.29*math.cos(a),1.225+.22*math.sin(a)) for a in [i*math.pi/20 for i in range(21)]]
 # Remove the duplicate first arc point for nonzero edges.
 profile=profile[:2]+profile[3:]
 roof=prism('Arched rain canopy',profile,.52,-.012,'postal-red',.008)
 for mod in list(roof.modifiers):roof.modifiers.remove(mod)
 for face in roof.data.polygons:face.use_smooth=abs(face.normal.y)<.1
 g.box('Mail inlet dark well',(0,.04,1.178),(.48,.32,.10),'dark',.006)
 for x in [-.258,.258]:g.box('Mail inlet side cheek',(x,0,1.183),(.04,.45,.11),'postal-red',.008)
 g.box('Mail inlet rear upstand',(0,.21,1.183),(.55,.03,.11),'postal-red',.006)
 g.box('Mail inlet lower sill',(0,-.244,1.129),(.53,.10,.025),'steel',.006)
 flap=g.box('Rain flap',(0,-.269,1.208),(.49,.025,.055),'steel',.007);flap.rotation_euler[0]=-.16
 g.door('Collection service door',0,-.231,.65,.47,.86,'postal-red')
 g.box('Collection notice frame',(0,-.263,.88),(.27,.016,.19),'graphite',.007)
 g.box('Blank collection notice',(0,-.274,.88),(.24,.005,.16),'cream',.003)
 for z in [.92,.89,.86]:g.box('Notice ruled line',(0,-.278,z),(.18,.002,.004),'graphite',.0005)
 # Original envelope pictogram made from bars, not a logo/font.
 g.box('Envelope blank plate',(0,-.260,.55),(.18,.009,.115),'cream',.005)
 for side in [-1,1]:
  ob=g.box('Envelope diagonal',(side*.041,-.267,.565),(.098,.003,.005),'postal-red',.001);ob.rotation_euler[1]=-side*.55
 for z in [.32,.39]:g.box('Lower drain slit',(0,.228,z),(.25,.004,.008),'dark',.002)


def shelter():
 # Four real columns with footplates, an open street-facing side, no seating.
 for x in [-1.43,1.43]:
  for y in [-.57,.57]:
   g.box('Anchored shelter footplate',(x,y,.018),(.20,.20,.036),'steel',.008)
   for dx in [-.065,.065]:
    for dy in [-.065,.065]:g.bolt('Shelter foundation bolt',(x+dx,y+dy,.039),r=.009)
   g.box('Structural square post',(x,y,1.19),(.075,.075,2.30),'graphite',.008)
   g.box('Post shoe',(x,y,.105),(.095,.095,.15),'steel',.008)
 # Rear glazing in three individually framed spans.
 for x in [-.94,0,.94]:
  g.box('Rear glass windscreen',(x,.573,1.20),(.87,.012,1.94),'glass',.002)
  panel_frame('Rear glazing frame',x,.58,1.20,.90,1.98,'steel',.026)
  for z in [.76,1.65]:
   for xx in [x-.435,x+.435]:g.box('Glass clamp',(xx,.555,z),(.035,.035,.05),'graphite',.003)
  for xx in [x-.24,x,x+.24]:g.box('Glass visibility marking',(xx,.561,1.37),(.11,.002,.018),'cream',.001)
 # One glazed end screen; opposite end is open.
 g.box('End glass windscreen',(-1.43,0,1.20),(.012,1.04,1.94),'glass',.002)
 for y in [-.535,.535]:g.box('End glazing upright',(-1.43,y,1.20),(.03,.026,1.99),'steel',.004)
 for z in [.21,2.19]:g.box('End glazing rail',(-1.43,0,z),(.03,1.07,.026),'steel',.004)
 for y in [-.32,0,.32]:g.box('End glass visibility marking',(-1.418,y,1.37),(.002,.13,.018),'cream',.001)
 for y in [-.57,.57]:g.box('Roof support longitudinal beam',(0,y,2.32),(3.06,.085,.12),'graphite',.012)
 for x in [-1.43,0,1.43]:g.box('Roof crossmember',(x,0,2.335),(.075,1.47,.09),'steel',.008)
 # Shallow curved aluminium roof, explicitly closed thickness at every end.
 n=20;ys=[-.80+1.60*i/n for i in range(n+1)]
 upper=[(y,2.48-.11*(y/.8)**2) for y in ys]
 profile=upper+[(y,z-.045) for y,z in reversed(upper)]
 verts=[(x,y,z) for x in [-1.61,1.61] for y,z in profile];k=len(profile)
 faces=[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]
 for i in range(k):j=(i+1)%k;faces.append((i,j,j+k,i+k))
 mesh=bpy.data.meshes.new('Curved shelter roof');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Curved shelter roof',mesh);bpy.context.collection.objects.link(o);g.finish(o,'Curved shelter roof','cream',.003)
 for x in [-1.58,1.58]:
  common.tube('Roof folded edge',[(x,y,z+.005) for y,z in upper],.018,g.M['steel'],resolution=2)
 g.box('Rear rain gutter',(0,.795,2.345),(3.24,.075,.065),'graphite',.009)
 g.tube('Rear rain downpipe',[(1.43,.80,2.35),(1.48,.79,2.22),(1.48,.68,2.10),(1.48,.68,.15),(1.53,.72,.09)],.022,'graphite')
 for z in [.55,1.55]:g.box('Downpipe fixing strap',(1.48,.67,z),(.065,.04,.025),'steel',.003)
 # Timetable is a blank original layout, no claimed actual route.
 g.box('Timetable rear housing',(.96,.525,1.52),(.34,.045,.57),'graphite',.012)
 g.box('Blank timetable sheet',(.96,.495,1.52),(.30,.008,.52),'cream',.003)
 g.box('Timetable header',(.96,.488,1.72),(.26,.002,.045),'blue',.002)
 for z in [1.64,1.58,1.52,1.46,1.40]:g.box('Timetable ruled line',(.96,.487,z),(.23,.002,.005),'graphite',.001)


def validator():
 g.box('Validator base plate',(0,0,.018),(.24,.22,.036),'steel',.008)
 for x in [-.083,.083]:
  for y in [-.075,.075]:g.bolt('Validator floor anchor',(x,y,.039),r=.007)
 g.box('Slim mounting column',(0,0,.54),(.075,.065,1.02),'steel',.012)
 g.box('Column service cover',(0,.036,.36),(.052,.009,.27),'graphite',.006)
 g.box('Upper bracket',(0,0,1.055),(.12,.10,.12),'graphite',.016)
 before=set(bpy.context.scene.objects)
 prism('Validator asymmetric housing',[(-.15,1.03),(.15,1.03),(.165,1.34),(.13,1.46),(-.13,1.46),(-.165,1.34)],.20,0,'yellow',.022)
 g.box('Validator face gasket',(0,-.105,1.245),(.27,.018,.37),'rubber',.020)
 g.box('Validator reader face',(0,-.119,1.235),(.25,.018,.35),'graphite',.018)
 g.box('Validation display',(0,-.133,1.35),(.18,.007,.084),'screen',.008)
 g.box('Status indicator bar',(0,-.14,1.412),(.15,.005,.012),'safety-green',.003)
 for z in [1.363,1.337]:g.box('Display status glyph',(0,-.138,z),(.11,.003,.007),'light',.001)
 g.box('Tap target',(0,-.135,1.20),(.18,.008,.13),'dark',.015)
 for r in [.022,.036,.05]:short_arc('Contactless target arc',-.022,-.142,1.20,r,-.85,.85,'cream',.0025)
 g.box('Ticket feed bezel',(0,-.135,1.085),(.20,.016,.045),'steel',.006)
 g.box('Ticket feed opening',(0,-.145,1.085),(.158,.003,.009),'dark',.002)
 g.box('Rear maintenance hatch',(0,.108,1.24),(.21,.014,.28),'graphite',.012)
 for x in [-.085,.085]:
  for z in [1.13,1.35]:g.bolt('Validator cover screw',(x,.12,z),(0,1,0),.004)
 # Entire head leans back; face components and rear access follow the same transform.
 pivot=Vector((0,0,1.10));rotation=Matrix.Rotation(math.radians(-12),4,'X')
 for o in set(bpy.context.scene.objects)-before:
  o.matrix_world=Matrix.Translation(pivot)@rotation@Matrix.Translation(-pivot)@o.matrix_world
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)


def charger():
 g.box('Charging post foundation',(0,0,.033),(.39,.34,.066),'graphite',.014)
 for x in [-.145,.145]:
  for y in [-.12,.12]:g.bolt('Charger anchor',(x,y,.07),r=.009)
 g.box('Charging pedestal body',(0,0,.83),(.32,.27,1.50),'cream',.038)
 g.box('Dark side impact strip',(-.161,0,.83),(.018,.235,1.35),'graphite',.008)
 g.box('Front dark fascia',(0,-.145,.99),(.255,.028,.95),'graphite',.022)
 g.box('Front display bezel',(0,-.165,1.28),(.205,.019,.19),'rubber',.014)
 g.box('Charging status display',(0,-.179,1.29),(.173,.005,.14),'screen',.008)
 for z in [1.32,1.28]:g.box('Charge status bar',(0,-.183,z),(.12,.002,.008),'light',.001)
 g.box('Upper status light',(0,-.146,1.51),(.19,.012,.018),'safety-green',.004)
 g.box('Contactless payment pad',(0,-.166,1.02),(.135,.018,.12),'dark',.012)
 for r in [.015,.028,.041]:short_arc('Charging reader arc',-.02,-.178,1.02,r,-.8,.8,'steel',.002)
 g.lock('Charger service key',.095,-.164,.67)
 # Cable is a real draped solid tube and terminates at strain relief and the holstered grip.
 g.cyl('Cable gland',(.176,0,1.17),.031,.042,'rubber',(1,0,0),24,.004)
 g.tube('Charging cable',[(.19,0,1.17),(.43,-.015,1.06),(.51,-.035,.50),(.45,-.075,.20),(.28,-.15,.22),(.25,-.19,.52),(.30,-.18,.82)],.018,'rubber')
 g.box('Connector holster bracket',(.194,-.10,.97),(.09,.12,.18),'graphite',.014)
 grip=g.box('Holstered connector grip',(.283,-.158,.90),(.075,.075,.20),'graphite',.022);grip.rotation_euler[1]=-.22
 g.cyl('Connector strain relief',(.30,-.18,.808),.025,.07,'rubber',(.2,0,1),24,.004)
 g.cyl('Connector head',(.255,-.145,1.016),.052,.12,'graphite',(-.5,0,1),32,.008)
 g.cyl('Connector collar',(.23,-.145,1.06),.046,.026,'steel',(-.5,0,1),32,.004)
 g.box('Connector release lever',(.30,-.20,.984),(.04,.015,.055),'blue',.005)
 g.box('Rear service gasket',(0,.14,.62),(.255,.014,.80),'rubber',.013)
 g.box('Rear service door',(0,.151,.62),(.235,.014,.78),'cream',.012)
 for z in [.32,.38,.44]:g.box('Rear cooling slot',(0,.161,z),(.15,.004,.012),'dark',.003)
 for x in [-.09,.09]:
  for z in [.27,.97]:g.bolt('Charger rear screw',(x,.164,z),(0,1,0),.004)


def hose_cabinet():
 # Wall-mount unit: included brackets, no fabricated wall or floor pedestal.
 for x in [-.32,.32]:
  for z in [.10,.88]:
   g.box('Wall mounting lug',(x,.145,z),(.09,.045,.10),'steel',.006)
   g.bolt('Wall mounting bolt',(x,.173,z),(0,1,0),.009)
 g.box('Cabinet rear pan',(0,.106,.49),(.78,.035,.98),'postal-red',.014)
 for x in [-.373,.373]:g.box('Cabinet folded side',(x,0,.49),(.035,.24,.98),'postal-red',.008)
 for z in [.017,.963]:g.box('Cabinet folded horizontal side',(0,0,z),(.75,.24,.035),'postal-red',.008)
 g.cyl('Reel bearing',(0,.055,.55),.075,.09,'steel',(0,1,0),32,.006)
 g.cyl('Reel rear disc',(0,.004,.55),.292,.018,'postal-red',(0,1,0),48,.004)
 # A continuous spiral hose with realistic pitch, not separate disconnected rings.
 points=[];turns=5.5
 for i in range(265):
  t=i/264;a=math.tau*turns*t;r=.06+.218*t
  points.append((r*math.cos(a),-.032,.55+r*math.sin(a)))
 common.tube('Continuous coiled fire hose',points,.018,g.M['hose'],resolution=3)
 g.cyl('Reel front hub',(0,-.071,.55),.055,.055,'steel',(0,1,0),32,.004)
 for a in [0,math.tau/3,2*math.tau/3]:
  o=g.box('Reel radial retaining strap',(.12*math.cos(a),-.069,.55+.12*math.sin(a)),(.26,.013,.017),'postal-red',.004);o.rotation_euler[1]=-a
 g.tube('Hose nozzle lead',[points[-1],(-.275,-.035,.35),(-.25,-.055,.19),(-.15,-.06,.13),(.10,-.06,.14),(.23,-.06,.22)],.018,'hose')
 g.cyl('Brass hose coupling',(.235,-.06,.24),.030,.075,'brass',(0,0,1),24,.004)
 g.cyl('Nozzle rubber grip',(.235,-.06,.32),.027,.105,'rubber',verts=24,b=.005)
 g.cyl('Nozzle barrel',(.235,-.06,.408),.021,.075,'brass',verts=24,b=.003)
 g.cyl('Nozzle dark opening',(.235,-.06,.448),.014,.006,'dark',verts=20,b=.001)
 for z in [.29,.33,.37]:g.torus('Nozzle grip rib',(.235,-.06,z),.027,.003,'rubber',segments=24)
 g.box('Glass door',(-.015,-.137,.49),(.67,.008,.85),'glass',.001)
 panel_frame('Front door gasket',0,-.139,.49,.733,.925,'rubber',.020)
 panel_frame('Front door frame',0,-.151,.49,.735,.93,'postal-red',.032)
 for z in [.23,.76]:g.cyl('Door hinge barrel',(-.383,-.12,z),.012,.11,'steel')
 g.lock('Cabinet key',.34,-.173,.50)
 g.box('Door pull',(.328,-.19,.61),(.026,.045,.115),'steel',.008)
 g.box('Blank emergency identification plate',(0,-.174,.91),(.25,.012,.08),'cream',.006)


ASSETS=[
 ('city-vending-machine','街路自動販売機','Street vending machine','独立した商品棚と缶、透明窓、操作部、受取口を備えた汎用自動販売機。','Generic stocked vending cabinet with transparent display, separate cans and shelves, keypad, payment hardware, delivery pocket and rear cooling louvers.',vending,['vending','retail','自動販売機']),
 ('city-postal-box','街路郵便ポスト','Street postal drop box','アーチ状の雨よけ、深い投函口、回収扉と無地の案内欄を持つブランドのない郵便ポスト。','Unbranded postal drop box with arched rain canopy, deep mail slot, hinged collection door and a blank ruled notice panel.',postal,['postal','mail','郵便']),
 ('city-bus-shelter','コンパクトバスシェルター','Compact bus shelter','曲面屋根、ガラス風防、固定金具、雨樋と無地の時刻表ケースを備えた座席なしのバス待合所。','Seat-free compact bus shelter with curved aluminium roof, framed glass windscreens, foundation anchors, rain gutter, downpipe and blank timetable case.',shelter,['bus','shelter','transit','待合所']),
 ('city-ticket-validator','交通チケット検札端末','Transit ticket validator','傾斜した読取ヘッド、表示部、タッチ領域、チケット投入口を備えた細身の交通端末。','Slim transit validator with inclined reader head, status display, contactless target, ticket feed and rear access hatch.',validator,['ticket','validator','transit','改札']),
 ('city-ev-charger','街路EV充電ポスト','Street EV charging post','表示部、カード読取部、ホルスター内コネクターとたるんだケーブルを備えた汎用充電ポスト。','Generic street EV post with display, reader, holstered connector, draped solid cable and service access. Visual prop; not an electrical specification or certified charger.',charger,['ev','charger','electric','充電']),
 ('city-fire-hose-cabinet','壁掛け消火ホース収納箱','Wall-mounted fire hose cabinet','透明扉越しに連続した巻きホース、リール、ノズルが見える壁掛け収納箱。','Wall-mounted cabinet with glazed framed door, continuous coiled hose, reel, brass nozzle and mounting lugs. Visual prop; not certified emergency equipment.',hose_cabinet,['fire','hose','cabinet','消火'])]

if __name__=='__main__':
 argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
 p=argparse.ArgumentParser();p.add_argument('--output','--out',dest='output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox');p.add_argument('--only',choices=[r[0] for r in ASSETS]);a=p.parse_args(argv)
 selected=[r for r in ASSETS if not a.only or r[0]==a.only]
 conflicts=[str(a.output/r[0]) for r in selected if (a.output/r[0]).exists()]
 if conflicts:p.error('Refusing to overwrite existing asset directories: '+', '.join(conflicts))
 for slug,ja,en,dj,de,fn,tags in selected:
  common.reset();materials();fn();common.publish_asset(slug,ja,en,dj,de,tags,str(a.output),'scripts/city/civic_extra.py')
  metadata=a.output/slug/'asset.json';data=json.loads(metadata.read_text())
  data['usages'][0]['sourcePaths'].append('scripts/city/civic.py')
  metadata.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
