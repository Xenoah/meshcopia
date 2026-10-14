"""Original Meshcopia civic street fixtures. No third-party assets.
Recovered procedural source; regenerate and QA before publication.
"""
import bpy, bmesh, math, sys
from mathutils import Vector
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import common
M={}

def materials():
 global M
 M={}
 specs={'graphite':((.075,.105,.12,1),.65,.34),'paint':((.16,.24,.22,1),.45,.38),'steel':((.47,.53,.55,1),.8,.27),'dark':((.018,.025,.03,1),.15,.6),'blue':((.035,.25,.36,1),.45,.34),'yellow':((.85,.52,.08,1),.35,.36),'green':((.16,.38,.23,1),.4,.38),'cream':((.72,.75,.71,1),.35,.4),'red':((.55,.075,.045,1),.55,.36),'rubber':((.025,.027,.028,1),0,.82),'screen':((.09,.23,.27,1),.2,.22),'light':((.61,.78,.72,1),.2,.35)}
 for n,(c,m,r) in specs.items():
  mat=bpy.data.materials.new(n);mat.diffuse_color=c;mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=c;p.inputs['Metallic'].default_value=m;p.inputs['Roughness'].default_value=r;M[n]=mat

def finish(o,n,mat,bevel=0):
 o.name=n;o.data.materials.append(M[mat]);bpy.context.view_layer.objects.active=o
 if bevel:
  m=o.modifiers.new('Manufactured edge radii','BEVEL');m.width=min(bevel,min(o.dimensions)*.2);m.segments=3
  bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for p in o.data.polygons:p.use_smooth=True
 m=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=30
 return o

def box(n,loc,size,mat='graphite',b=.006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,mat,b)

def cyl(n,loc,r,h,mat='steel',axis=(0,0,1),verts=32,b=.002):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=h,location=loc);o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,mat,b)

def torus(n,loc,r,t,mat='steel',axis=(0,0,1),segments=40):
 bpy.ops.mesh.primitive_torus_add(major_segments=segments,minor_segments=8,location=loc,major_radius=r,minor_radius=t);o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();return finish(o,n,mat)

def lathe(n,profile,loc=(0,0,0),mat='steel',segments=48):
 v=[(loc[0]+r*math.cos(i*math.tau/segments),loc[1]+r*math.sin(i*math.tau/segments),loc[2]+z) for r,z in profile for i in range(segments)];f=[]
 for j in range(len(profile)-1):
  for i in range(segments):
   a=j*segments+i;d=j*segments+(i+1)%segments;f.append((a,d,d+segments,a+segments))
 mesh=bpy.data.meshes.new(n);mesh.from_pydata(v,[],f);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(n,mesh);bpy.context.collection.objects.link(o);return finish(o,n,mat)

def tube(n,points,r,mat='steel'):
 bpy.ops.object.select_all(action='DESELECT');c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=r;c.bevel_resolution=3;c.use_fill_caps=True;s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for p,v in zip(s.bezier_points,points):p.co=v;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return finish(o,n,mat)

def bolt(n,loc,axis=(0,0,1),r=.008):
 cyl(n+' washer',loc,r*1.45,.003,'steel',axis,24,.0007);cyl(n+' hex head',Vector(loc)+Vector(axis)*.004,r,.008,'steel',axis,6,.0008)

def lock(n,x,y,z):
 cyl(n+' bezel',(x,y,z),.017,.009,'steel',(0,1,0));cyl(n+' plug',(x,y-.006,z),.012,.006,'graphite',(0,1,0));box(n+' keyway',(x,y-.010,z),(.002,.002,.012),'dark',.0005)

def feet(w,d):
 for x in [-w/2+.06,w/2-.06]:
  for y in [-d/2+.06,d/2-.06]:box('Ground anchor foot',(x,y,.025),(.09,.09,.05),'graphite');bolt('Anchor bolt',(x,y,.052),r=.009)

def door(n,x,y,z,w,h,mat):
 box(n+' inset seal',(x,y+.008,z),(w+.009,.016,h+.009),'rubber',.009);box(n+' folded metal panel',(x,y-.003,z),(w,.022,h),mat,.009)
 for zz in [z-h*.32,z+h*.32]:cyl(n+' hinge barrel',(x-w/2+.008,y-.012,zz),.009,.07,'steel')
 lock(n+' keyed latch',x+w*.35,y-.019,z)

def litter():
 feet(.58,.52);box('Base plinth',(0,0,.095),(.58,.52,.10),'graphite',.018)
 box('Rear enclosure',(0,.237,.55),(.56,.035,.86),'paint',.012)
 for x in [-.265,.265]:box('Side folded enclosure',(x,0,.55),(.035,.49,.86),'paint',.012)
 door('Front maintenance door',0,-.253,.49,.49,.64,'paint')
 box('Opening inner back',(0,.188,.88),(.48,.025,.21),'dark');box('Opening liner floor',(0,0,.77),(.48,.43,.025),'dark')
 for x in [-.246,.246]:box('Opening side reveal',(x,-.08,.885),(.022,.32,.20),'steel',.003)
 box('Rolled opening lower lip',(0,-.257,.785),(.51,.038,.035),'steel',.008)
 box('Overhanging rain hood',(0,-.008,1.025),(.63,.57,.075),'graphite',.022)
 box('Hood drip edge',(0,-.285,.992),(.61,.025,.022),'steel',.005)
 for x in [-.17,-.085,0,.085,.17]:box('Lower ventilation inset',(x,-.267,.225),(.025,.004,.08),'dark',.008)
 for y in [-.12,.03,.18]:box('Rear reinforcement',(0,y,.135),(.48,.025,.018),'steel',.002)
 for x in [-.25,.25]:bolt('Hood retention',(x,.18,1.065),r=.006)

def recycling():
 feet(1.27,.54);box('Shared raised plinth',(0,0,.105),(1.27,.54,.11),'graphite',.018)
 for i,(x,mat) in enumerate([(-.41,'blue'),(0,'yellow'),(.41,'green')]):
  box('Stream %d inner dark liner'%i,(x,.02,.58),(.375,.455,.85),'dark',.01)
  box('Stream %d rear cabinet'%i,(x,.235,.61),(.397,.035,.92),'cream',.008)
  for xx in [x-.195,x+.195]:box('Compartment vertical return',(xx,0,.61),(.016,.49,.92),'cream',.005)
  door('Stream %d service door'%i,x,-.257,.49,.369,.66,'cream')
  box('Stream color strip',(x,-.274,.765),(.33,.012,.047),mat,.004)
  box('Opening left cheek',(x-.151,-.249,.935),(.065,.04,.24),mat,.009);box('Opening right cheek',(x+.151,-.249,.935),(.065,.04,.24),mat,.009)
  box('Opening top rail',(x,-.249,1.045),(.36,.04,.04),mat,.008);box('Opening bottom lip',(x,-.266,.827),(.36,.065,.04),'steel',.008)
  box('Rain cap',(x,0,1.095),(.416,.58,.063),'graphite',.015)
  if i==0:
   for xx in [x-.065,x+.065]:cyl('Bottle aperture separator',(xx,-.255,.938),.009,.17,'steel')
  elif i==1:box('Paper flap',(x,-.235,.984),(.23,.018,.065),'steel',.007)
  else:box('General waste opening brow',(x,-.267,1.016),(.23,.035,.025),'steel')
  for xx in [x-.14,x+.14]:bolt('Cap fixing',(xx,.18,1.128),r=.005)

def fountain():
 # Latest unvalidated refinement: flat annular footplate and exposed anchors.
 lathe('Pedestal base',[(0,0),(.205,0),(.205,.035),(.19,.05),(.135,.05),(.12,.10),(.12,.17),(.115,.18)],mat='graphite')
 cyl('Pedestal column',(0,0,.52),.12,.70,'paint',verts=48,b=.01)
 for a in [0,math.pi/2,math.pi,math.pi*1.5]:bolt('Footplate anchor',(.16*math.cos(a),.16*math.sin(a),.054))
 box('Service hatch seal',(0,-.117,.42),(.13,.016,.29),'rubber',.015);box('Service hatch',(0,-.13,.42),(.117,.016,.275),'paint',.012);lock('Hatch latch',0,-.141,.50)
 for x,z in [(-.30,.76),(.25,.98)]:
  tube('Cast supporting arm',[(0,0,z-.20),(x*.65,0,z-.13),(x,0,z-.055)],.055,'paint')
  lathe('Drinking bowl',[(.024,-.065),(.10,-.06),(.15,-.035),(.181,0),(.18,.016),(.17,.021),(.155,-.004),(.12,-.028),(.025,-.041)],(x,0,z),'steel')
  torus('Rolled bowl rim',(x,0,z+.014),.174,.007)
  cyl('Drain dark throat',(x,0,z-.048),.027,.014,'dark')
  for yy in [-.014,0,.014]:box('Drain grate rib',(x,yy,z-.039),(.04,.004,.004),'steel',.001)
  cyl('Bubbler mounting boss',(x,.107,z+.023),.033,.04,'steel')
  tube('Bubbler swan neck',[(x,.107,z+.03),(x,.105,z+.09),(x,.075,z+.115),(x,.045,z+.096)],.013,'steel')
  cyl('Bubbler outlet dark bore',(x,.043,z+.094),.008,.003,'dark',(0,-.6,-.8),16,.0005)
  cyl('Push button ring',(x,-.149,z-.006),.026,.015,'graphite',(0,-.8,.6));cyl('Push button',(x,-.157,z),.018,.01,'steel',(0,-.8,.6))

def parcel():
 feet(1.55,.51);box('Recessed kick plinth',(0,0,.10),(1.48,.48,.15),'graphite',.018)
 box('Locker rear shell',(0,.232,.98),(1.53,.04,1.69),'graphite',.01)
 for x in [-.75,.75]:box('Side armor',(x,0,.98),(.04,.49,1.69),'graphite',.012)
 for col,x in enumerate([-.50,0,.50]):
  heights=[.27,.27,.40,.63] if col!=1 else [.37,.32,.28,.60]
  z=.155
  for j,h in enumerate(heights):
   center=z+h/2;box('Locker %d-%d gasket'%(col,j),(x,-.254,center),(.476,.026,h-.009),'rubber',.004)
   box('Locker %d-%d door'%(col,j),(x,-.272,center),(.461,.025,h-.022),'cream' if col!=1 else 'paint',.008)
   box('Recessed finger pull',(x+.155,-.288,center),(.046,.008,.083),'dark',.012)
   box('Steel pull lip',(x+.165,-.295,center),(.011,.012,.066),'steel',.004)
   for zz in [center-h*.30,center+h*.30]:box('Concealed hinge end',(x-.221,-.287,zz),(.016,.012,.028),'steel',.003)
   box('Blank compartment tag',(x-.144,-.288,center+h*.28),(.064,.004,.021),'steel',.002)
   z+=h
 box('Upper fascia infill',(0,-.254,1.782),(1.46,.035,.10),'graphite',.006)
 box('Weather cap',(0,0,1.872),(1.62,.60,.085),'graphite',.02)
 box('Front drip rail',(0,-.299,1.839),(1.58,.02,.023),'steel',.004)
 box('Terminal rear housing',(.843,-.15,1.20),(.18,.17,.43),'graphite',.02)
 box('Terminal glass',(.843,-.243,1.26),(.135,.018,.19),'dark',.009)
 box('Terminal active display',(.843,-.254,1.278),(.11,.004,.12),'screen',.003)
 for z in [1.29,1.265]:box('Display status bar',(.843,-.257,z),(.071,.002,.006),'light',.0008)
 box('Reader pad',(.843,-.25,1.105),(.11,.016,.067),'rubber',.008)
 for y in [-.12,.02,.16]:box('Rear cooling slot',(0,.256,.32+y),(.30,.004,.012),'dark',.005)

def meter():
 cyl('Meter anchor flange',(0,0,.026),.145,.052,'graphite',verts=48,b=.007)
 for a in [math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]:bolt('Pavement anchor',(.107*math.cos(a),.107*math.sin(a),.055),r=.009)
 cyl('Lower tube pedestal',(0,0,.53),.068,.98,'steel',verts=48,b=.004)
 cyl('Anti tamper lower collar',(0,0,.105),.082,.06,'graphite',b=.005)
 cyl('Upper collar',(0,0,1.016),.083,.075,'graphite',b=.006)
 box('Lower meter body',(0,0,1.17),(.275,.23,.32),'graphite',.045)
 box('Meter rounded upper casing',(0,0,1.462),(.36,.25,.40),'paint',.055)
 box('Face weather gasket',(0,-.125,1.435),(.294,.018,.363),'rubber',.027)
 box('Face bezel',(0,-.139,1.433),(.278,.02,.347),'steel',.023)
 box('Display bezel',(0,-.153,1.516),(.226,.018,.128),'dark',.013)
 box('Display glass',(0,-.165,1.522),(.197,.005,.094),'screen',.008)
 for x in [-.065,-.02,.025]:
  for z in [1.5,1.523,1.546]:box('LCD horizontal segment',(x,-.169,z),(.025,.002,.004),'light',.0008)
 box('Coin slot surround',(.073,-.159,1.389),(.064,.018,.041),'graphite',.008)
 box('Coin slot',(.073,-.17,1.389),(.042,.003,.005),'dark',.001)
 for x in [-.09,-.043]:
  for z in [1.401,1.363]:cyl('Selection button',(x,-.164,z),.014,.013,'graphite',(0,1,0),24,.003)
 box('Contactless reader',(0,-.159,1.296),(.11,.018,.055),'dark',.007)
 for x in [-.021,0,.021]:box('Reader raised marker',(x,-.171,1.296),(.005,.002,.022),'steel',.001)
 box('Payment return pocket',(0,-.12,1.14),(.17,.015,.055),'dark',.008)
 box('Return tray lower rim',(0,-.134,1.119),(.18,.04,.015),'steel',.004)
 box('Rear battery access seam',(0,.127,1.40),(.245,.014,.31),'rubber',.018)
 box('Rear battery access door',(0,.138,1.40),(.225,.018,.29),'paint',.015)
 for x in [-.09,.09]:
  for z in [1.28,1.52]:bolt('Rear security screw',(x,.15,z),(0,1,0),.005)
 lock('Cash box lock',.095,-.119,1.182)
 panel=box('Canopy solar glass',(0,-.006,1.677),(.29,.21,.014),'dark',.007);panel.rotation_euler[0]=.10
 for x in [-.105,-.035,.035,.105]:
  for y in [-.060,0,.060]:
   o=box('Photovoltaic cell',(x,y,1.687+y*.10),(.062,.05,.003),'screen',.002);o.rotation_euler[0]=.10

def hydrant():
 # Latest unvalidated refinement: flat annular flange under visible anchors.
 lathe('Cast hydrant barrel',[(0,0),(.19,0),(.19,.035),(.18,.05),(.135,.05),(.114,.10),(.108,.16),(.108,.52),(.135,.55),(.14,.59),(.14,.615),(.118,.63),(.115,.71),(.095,.77),(.045,.79),(0,.79)],mat='red')
 for a in [i*math.tau/6 for i in range(6)]:bolt('Base foundation bolt',(.157*math.cos(a),.157*math.sin(a),.054),r=.011)
 for a in [i*math.tau/6 for i in range(6)]:bolt('Bonnet joint bolt',(.121*math.cos(a),.121*math.sin(a),.621),r=.008)
 torus('Bonnet flange seam',(0,0,.592),.139,.005,'graphite')
 cyl('Top operating nut',(0,0,.804),.033,.037,'steel',verts=5,b=.003)
 for s in [-1,1]:
  cyl('Outlet cast neck',(s*.138,0,.445),.067,.12,'red',(1,0,0),48,.008)
  cyl('Outlet flange',(s*.209,0,.445),.087,.043,'red',(1,0,0),48,.005)
  cyl('Outlet gasket',(s*.233,0,.445),.077,.008,'rubber',(1,0,0),48,.001)
  cyl('Outlet cap',(s*.252,0,.445),.078,.033,'red',(1,0,0),48,.008)
  cyl('Outlet cap square wrench nut',(s*.277,0,.445),.023,.023,'steel',(1,0,0),4,.003)
  torus('Cap tether loop',(s*.243,-.07,.43),.013,.004,'steel',(0,1,0))
  for j in range(21):
   t=j/20;x=s*(.238-.12*t);y=-.074-.037*math.sin(math.pi*t);z=.421-.13*math.sin(math.pi*t)-.04*t
   torus('Retaining chain link',(x,y,z),.014,.003,'steel',(0,1,0) if j%2==0 else (1,0,0),segments=24)
  torus('Barrel tether anchor',(s*.113,-.07,.38),.012,.004,'steel',(1,0,0))
 box('Blank cast inspection plate',(0,-.109,.26),(.103,.013,.085),'red',.01)
 for x in [-.033,.033]:bolt('Inspection plate fastener',(x,-.119,.26),(0,-1,0),.004)

ASSETS=[
 ('city-litter-bin','街路ごみ箱','Street litter bin','雨よけフード、投入口、施錠式扉、独立した脚と通気スリットを備えた街路用ごみ箱。','Outdoor litter cabinet with a rain hood, real deposit opening, keyed service door, individual feet and vent details.',litter,['bin','waste','street','ごみ箱']),
 ('city-recycling-station','3分別リサイクルステーション','Three-stream recycling station','色分けされた投入口と独立した回収扉を備えたコンパクトな3分別ごみ箱。','Compact three-stream recycling station with color-coded openings, individual collection doors, weather caps and an anchored plinth.',recycling,['recycling','waste','street','分別']),
 ('city-drinking-fountain','二段式街路飲水台','Dual-height drinking fountain','高さの異なる2つのボウル、押しボタン、排水グリル、点検扉を持つ公共空間向け飲水台。','Public-space fountain with two bowl heights, push buttons, drain grilles, curved bubblers and a service hatch. Visual prop, not certified accessibility hardware.',fountain,['fountain','water','street','飲水台']),
 ('city-parcel-locker','屋外宅配ロッカー','Outdoor parcel locker bank','大小12個の扉と側面端末、雨よけ屋根を備えた屋外宅配ロッカー。','Outdoor parcel locker bank with twelve differently sized doors, gasket seams, flush pulls, a side terminal and a drip canopy.',parcel,['parcel','locker','street','宅配']),
 ('city-parking-meter','街路パーキングメーター','Street parking payment meter','ソーラーパネル、表示部、投入スロット、操作ボタンを備えた独立型パーキングメーター。','Standalone parking payment meter with solar canopy, segmented display, coin slot, selection buttons, reader pad and rear service access.',meter,['parking','meter','street','駐車']),
 ('city-fire-hydrant','二口消火栓','Two-outlet fire hydrant','フランジ、六角ボルト、キャップ、保持チェーンを個別に造形した汎用消火栓。','Generic two-outlet hydrant with cast barrel profile, bolted flanges, removable-looking caps, wrench nuts and individually modeled retaining-chain links.',hydrant,['hydrant','fire','street','消火栓'])
]

if __name__=='__main__':
 import argparse
 argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
 p=argparse.ArgumentParser()
 p.add_argument('--output','--out',dest='output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
 p.add_argument('--only',choices=[row[0] for row in ASSETS])
 a=p.parse_args(argv)
 selected=[row for row in ASSETS if not a.only or row[0]==a.only]
 conflicts=[str(a.output/row[0]) for row in selected if (a.output/row[0]).exists()]
 if conflicts:p.error('Refusing to overwrite existing asset directories: '+', '.join(conflicts))
 for slug,ja,en,dj,de,fn,tags in selected:
  common.reset();materials();fn()
  common.publish_asset(slug,ja,en,dj,de,tags,str(a.output),'scripts/city/civic.py')
