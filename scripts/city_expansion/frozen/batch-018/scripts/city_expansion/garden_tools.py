"""Four original public-garden maintenance props for Xenoah / Meshcopia.
CC BY 4.0. No external models, images, fonts or brand references. Blender 4.3.2.
Static exterior visualization, not operating or fabrication documentation.
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(steel=mat('Satin zinc steel',(.38,.43,.46),.78,.34),dark=mat('Graphite painted metal',(.028,.042,.044),.33,.45),rubber=mat('Textured charcoal rubber',(.014,.021,.022),0,.85),green=mat('Garden green polymer',(.095,.28,.15),0,.48),orange=mat('Warm orange polymer',(.68,.21,.036),0,.43),black=mat('Dark molded polymer',(.035,.045,.047),0,.58),red=mat('Control red polymer',(.55,.065,.035),0,.48),silver=mat('Bright cutter steel',(.53,.58,.61),.85,.31),line=mat('Pale fixed nylon line',(.72,.75,.57),0,.57))


def cyl(name,center,radius,depth,material,axis='Z',segments=32,bevel=.002,radius2=None):
    if radius2 is None:o=cylinder(name,center,radius,depth,material,segments,bevel=bevel)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=segments,radius1=radius,radius2=radius2,depth=depth,location=center)
        o=finish(bpy.context.object,name,material,bevel,False)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
    return o


def rod(name,start,end,radius,material,segments=20):
    a,b=Vector(start),Vector(end);o=cyl(name,(a+b)*.5,radius,(b-a).length,material,segments=segments,bevel=min(.001,radius*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def strut(name,start,end,width,depth,material):
    a,b=Vector(start),Vector(end);o=box(name,(a+b)*.5,(width,depth,(b-a).length),material,.003)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def screw(name,center,material,axis='Z',radius=.006):
    cyl(name+' washer',center,radius*1.45,radius*.35,material,axis,20,.0003)
    p=list(center);p['XYZ'.index(axis)]+=radius*.45
    cyl(name+' hex head',p,radius,radius*.8,material,axis,6,.0003)


def annulus(name,center,outer,inner,depth,material,axis='Z',segments=36):
    vs=[]
    for r,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:
        vs.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for i in range(segments))
    fs=[]
    for k in range(4):
        for i in range(segments):
            j=(i+1)%segments;fs.append((k*segments+i,k*segments+j,((k+1)%4)*segments+j,((k+1)%4)*segments+i))
    o=mesh(name,vs,fs,material);o.location=center
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for i,f in enumerate(o.data.polygons):f.use_smooth=(i//segments)%2==0
    return o


def profile(name,points,thickness,material,axis='Z',bevel=.002):
    # Extrude a planar polygon with explicit closed end faces.
    n=len(points);vs=[]
    for d in [-thickness/2,thickness/2]:
        for a,b in points:vs.append((a,b,d) if axis=='Z' else ((d,a,b) if axis=='X' else (a,d,b)))
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def loop(name,points,radius,material):
    # A cyclic tube with no coincident cap faces. Cross sections are parallel transported.
    pts=[Vector(p) for p in points];vs=[];n=len(pts);sides=12
    ref=(pts[1]-pts[0]).cross(pts[2]-pts[1]).normalized()
    assert ref.length>.9
    for i,p in enumerate(pts):
        tangent=(pts[(i+1)%n]-pts[(i-1)%n]).normalized()
        u=tangent.cross(ref).normalized();v=tangent.cross(u).normalized()
        vs.extend(tuple(p+radius*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*v)) for j in range(sides))
    fs=[(i*sides+j,i*sides+(j+1)%sides,((i+1)%n)*sides+(j+1)%sides,((i+1)%n)*sides+j) for i in range(n) for j in range(sides)]
    return mesh(name,vs,fs,material,0,True)


def hopper_shell(name,material):
    # Four connected tapered wall faces, rim and open lower throat; no fill geometry.
    levels=[(.29,.235,.78),(.066,.055,.47),(.053,.042,.47),(.278,.223,.78)]
    vs=[]
    for x,y,z in levels:vs.extend([(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)])
    fs=[]
    for k in range(4):
        for i in range(4):j=(i+1)%4;fs.append((4*k+i,4*k+j,4*((k+1)%4)+j,4*((k+1)%4)+i))
    return mesh(name,vs,fs,material,.002)


def wheel(name,x,y,z,p):
    r=.145;w=.064
    cyl(name+' rubber tire',(x,y,z),r,w,p['rubber'],'X',40,.007)
    for side in [-1,1]:
        xx=x+side*w*.51
        cyl(name+' inset hub disk',(xx,y,z),.105,.009,p['green'],'X',32,.002)
        annulus(name+' hub ring',(xx+side*.006,y,z),.076,.048,.007,p['dark'],'X',32)
        cyl(name+' axle cap',(xx+side*.013,y,z),.025,.025,p['steel'],'X',24,.002)
    for i in range(18):
        a=i*math.tau/18
        o=box(name+' raised tread',(x,y+math.sin(a)*.143,z+math.cos(a)*.143),(w*.82,.024,.008),p['rubber'],.002);o.rotation_euler[0]=-a


def spreader():
    p=palette();hopper_shell('Empty tapered hopper with open throat',p['green'])
    # Rounded continuous lip stays outside the real cavity.
    lip=[(-.29,-.235,.781),(.29,-.235,.781),(.29,.235,.781),(-.29,.235,.781)]
    loop('Rolled hopper rim',lip,.011,p['dark'])
    for x in [-.19,.19]:
        tube('Hopper frame rail',[(x,-.17,.67),(x,-.19,.26),(x,.27,.26),(x,.40,.045)],.014,p['dark'],2)
        box('Rear ground shoe',(x,.397,.032),(.072,.10,.064),p['rubber'],.009)
        strut('Hopper diagonal brace',(x,-.18,.29),(x,.19,.66),.018,.018,p['steel'])
        for y in [-.16,.16]:screw('Hopper frame fastener',(x,y,.66),p['steel'],'X')
    rod('Continuous wheel axle',(-.36,0,.15),(.36,0,.15),.014,p['steel'],28)
    for x in [-.325,.325]:wheel('Spreader wheel',x,0,.15,p)
    for x in [-.22,.22]:
        tube('Long push handle',[(x,.191,.71),(x,.28,.75),(x,.69,1.015),(x,.77,1.04)],.016,p['dark'],2)
        screw('Handle attachment',(x,.198,.71),p['steel'],'X',.008)
    rod('Foam push grip',(-.22,.77,1.04),(.22,.77,1.04),.024,p['rubber'],28)
    # Open metering throat, partial slide and exposed drive enclosure.
    for x in [-.060,.060]:box('Metering throat side',(x,0,.431),(.012,.108,.079),p['dark'],.001)
    for y in [-.049,.049]:box('Metering throat end',(0,y,.431),(.108,.010,.079),p['dark'],.001)
    box('Partly recessed metering slide',(.038,.0,.397),(.093,.080,.005),p['steel'],.001)
    box('Metering slide tab',(.103,.0,.397),(.037,.024,.009),p['red'],.002)
    rod('Slide lever link',(.108,.0,.407),(.11,.24,.60),.004,p['steel'],16)
    rod('Control linkage',(.11,.24,.60),(.12,.715,1.038),.004,p['steel'],16)
    box('Metering hand lever',(.12,.72,1.048),(.035,.10,.015),p['red'],.004,rot=(.15,0,0))
    # Rotor is exposed below the chute, with broad visible throwing vanes.
    cyl('Spreader rotor disk',(0,0,.335),.145,.011,p['black'],segments=40,bevel=.0015)
    cyl('Rotor spindle',(0,0,.281),.014,.115,p['steel'],segments=24)
    for i in range(4):
        a=i*math.tau/4
        o=box('Radial rotor vane',(.075*math.cos(a),.075*math.sin(a),.354),(.12,.007,.033),p['green'],.0015);o.rotation_euler[2]=a
    box('Axle drive enclosure',(0,.013,.18),(.095,.082,.092),p['black'],.013)
    cyl('Drive spindle collar',(0,0,.239),.028,.036,p['steel'],segments=28)
    for x in [-.035,.035]:screw('Drive cover bolt',(x,-.032,.18),p['steel'],'Y',.004)
    return ('city-broadcast-spreader','手押し式の散布機','Walk-behind broadcast spreader','公園や庭園の管理場面に置く手押し散布機。空の開口ホッパー、下部の計量口とスライド、露出した散布円盤と羽根、車軸、二輪、押し手と操作リンクを造形しています。粒材、内部歯車、散布・回転動作は含まず、容量・散布性能・安全認証は示しません。','A walk-behind spreader for park and garden maintenance scenes, with an empty open hopper, metering throat and slide, exposed rotor disk and vanes, axle, two wheels, push handle and control linkage. No granules, internal gears, dispensing or rotation behavior; no capacity, spreading-performance or safety certification is claimed.',['garden','maintenance','spreader','散布機'])


def hedge_trimmer():
    p=palette()
    # Distinct paired opposed-tooth blade strips, not a solid rectangular blade.
    for z,offset in [(.038,0),(.045,.010)]:
        box('Cutter bar spine',(-.35,0,z),(.68,.026,.005),p['silver'],.0007)
        for i in range(15):
            x=-.657+i*.042+offset
            for side in [-1,1]:
                pts=[(x-.014,side*.008),(x+.014,side*.008),(x+.011,side*.053),(x+.004,side*.061),(x-.008,side*.058)]
                o=profile('Opposed trapezoid cutter tooth',pts,.004,p['silver'],'Z',.0006);o.location.z=z
    box('Upper blade stiffener',(-.35,0,.053),(.65,.016,.011),p['dark'],.002)
    for x in [-.60,-.45,-.30,-.15]:screw('Blade retention bolt',(x,0,.062),p['steel'],radius=.004)
    # Wide blade-end shoe preserves visible tooth spacing.
    o=profile('Tip protector',[(-.709,-.028),(-.690,-.041),(-.671,-.030),(-.671,.030),(-.690,.041),(-.709,.028)],.016,p['orange'],'Z',.003);o.location.z=.043
    # Body is a tapered closed polygon with layered split-case seam.
    body=[(-.005,.040),(.19,.042),(.265,.071),(.251,.137),(.19,.180),(.07,.178),(.003,.125)]
    profile('Motor lower shell',body,.132,p['orange'],'Y',.012)
    profile('Split-case center seam',body,.008,p['dark'],'Y',.002)
    box('Blade drive neck',(-.025,0,.058),(.078,.082,.042),p['dark'],.008)
    # Genuine handle opening in front D-shaped loop.
    loop('Front wraparound handle',[(.055,-.087,.085),(.055,-.114,.142),(.055,-.106,.230),(.055,-.070,.259),(.055,.070,.259),(.055,.106,.230),(.055,.114,.142),(.055,.087,.085)],.014,p['black'])
    rod('Front handle upper padded grip',(.055,-.068,.259),(.055,.068,.259),.019,p['rubber'],24)
    # Guard shield is a separate transverse solid shell with shaped corners.
    guard=[(-.105,.056),(-.118,.071),(-.108,.172),(-.078,.203),(.078,.203),(.108,.172),(.118,.071),(.105,.056)]
    o=profile('Transverse hand guard',guard,.009,p['black'],'X',.003);o.location.x=-.010
    for y in [-.062,.062]:screw('Guard bracket screw',(-.018,y,.086),p['steel'],'X',.004)
    # Rear handle is a long open loop with integral upper grip and visible trigger.
    loop('Rear handle open frame',[(.206,0,.151),(.277,0,.173),(.423,0,.172),(.460,0,.141),(.454,0,.075),(.419,0,.055),(.270,0,.058),(.228,0,.080)],.018,p['orange'])
    rod('Rear control grip',(.286,0,.172),(.412,0,.172),.024,p['rubber'],28)
    box('Fixed trigger',(.342,0,.137),(.086,.017,.014),p['red'],.004,rot=(0,.06,0))
    box('Rear battery interface cap',(.253,0,.066),(.053,.094,.059),p['black'],.006)
    # Louvered side vent: separate rails over inset backing, rather than painted lines.
    for side in [-1,1]:
        y=side*.069
        box('Motor vent backing',(.152,y,.119),(.080,.006,.057),p['black'],.004)
        for i in range(5):box('Motor ventilation louver',(.118+i*.017,y+side*.005,.119),(.008,.008,.049),p['dark'],.001,rot=(0,-.14,0))
        for x,z in [(.028,.089),(.206,.077),(.202,.156)]:screw('Motor shell fastener',(x,side*.071,z),p['steel'],'Y',.0035)
    return ('city-electric-hedge-trimmer','電動ヘッジトリマー','Electric hedge trimmer','庭園や生垣の管理場面に使う横置きのヘッジトリマー。重ねた対向刃と保持バー、先端保護部、手元ガード、前後二つの開口ハンドル、トリガー、通気ルーバー付きの無銘モーター外装を備えます。電池・電源コード・植物・内部駆動部は付属せず、刈込み動作・性能・安全認証はありません。','A horizontally resting hedge trimmer for garden and hedge-maintenance scenes, with layered opposed toothed cutters and retaining bar, tip protector, hand guard, two open handles, trigger and an unbranded louvered motor housing. Battery, power cord, plants and working internals are omitted; no cutting behavior, performance or safety certification is supplied.',['garden','maintenance','hedge-trimmer','ヘッジトリマー'])


def sector(name,center,inner,outer,zlo,zhi,start,end,material,steps=30):
    cx,cy,cz=center;vs=[]
    for r,z in [(inner,zlo),(outer,zlo),(outer,zhi),(inner,zhi)]:
        for i in range(steps+1):
            a=start+(end-start)*i/steps;vs.append((cx+r*math.cos(a),cy+r*math.sin(a),cz+z))
    n=steps+1;fs=[]
    for k in range(4):
        for i in range(steps):fs.append((k*n+i,k*n+i+1,((k+1)%4)*n+i+1,((k+1)%4)*n+i))
    fs.extend([(0,n,2*n,3*n),(steps,3*n+steps,2*n+steps,n+steps)])
    return mesh(name,vs,fs,material,.001)


def grass_trimmer():
    p=palette();shaftA=Vector((-.47,0,.152));shaftB=Vector((.40,0,1.36));d=(shaftB-shaftA).normalized()
    cyl('Fixed line spool',(-.5,0,.046),.057,.071,p['black'],segments=40,bevel=.006)
    cyl('Spool lower bump cap',(-.5,0,.011),.030,.022,p['dark'],segments=32,bevel=.003)
    annulus('Spool cover seam',(-.5,0,.071),.058,.051,.009,p['orange'],segments=32)
    for side in [-1,1]:rod('Short fixed nylon line end',(-.5,side*.051,.045),(-.5+side*.017,side*.151,.045),.0025,p['line'],12)
    # Partial shield leaves a genuine open front and no full disk filling the opening.
    sector('Curved spool guard roof',(-.5,0,0),.058,.222,.104,.117,math.radians(-96),math.radians(96),p['green'],28)
    sector('Downturned guard skirt',(-.5,0,0),.210,.223,.053,.114,math.radians(-96),math.radians(96),p['black'],28)
    box('Guard mount rib',(-.392,0,.124),(.18,.027,.031),p['green'],.005)
    for x in [-.441,-.355]:screw('Guard mounting screw',(x,0,.143),p['steel'],radius=.005)
    cyl('Lower bevel gear housing',(-.5,0,.127),.043,.069,p['steel'],segments=32,bevel=.006,radius2=.030)
    rod('Angled shaft boot',(-.491,0,.144),(-.409,0,.239),.029,p['black'],28)
    rod('Long aluminum drive shaft',shaftA,shaftB,.014,p['steel'],32)
    mid=shaftA+(shaftB-shaftA)*.49
    rod('Shaft split coupling',mid-d*.035,mid+d*.035,.022,p['black'],28)
    screw('Coupling pinch screw',(mid.x, -.023,mid.z),p['steel'],'Y',.005)
    # Loop control handle stands off the shaft, with a real central void.
    c=shaftA+(shaftB-shaftA)*.66;side=Vector((-d.z,0,d.x));pts=[]
    for u,v in [(-.035,-.045),(-.10,-.13),(-.16,-.13),(-.19,-.09),(-.19,.09),(-.16,.13),(-.10,.13),(-.035,.045)]:pts.append(tuple(c+side*(-u)+Vector((0,v,0))))
    loop('Wide loop auxiliary handle',pts,.015,p['black'])
    rod('Loop handle shaft clamp',c-d*.03,c+d*.03,.026,p['black'],28)
    screw('Loop clamp fastener',(c.x,-.032,c.z),p['steel'],'Y',.006)
    gripA=shaftA+(shaftB-shaftA)*.82;gripB=shaftA+(shaftB-shaftA)*.96
    rod('Upper shaft cushioned control grip',gripA,gripB,.025,p['rubber'],28)
    t=(gripA+gripB)/2
    box('Fixed thumb control',(t.x,-.027,t.z),(.035,.017,.065),p['red'],.005,rot=(0,math.atan2(d.x,d.z),0))
    # Distinct compact inline electric power head, without backpack or combustion-engine parts.
    motor=Vector((.455,0,1.432));o=box('Inline motor upper shell',motor,(.145,.161,.228),p['green'],.028);o.rotation_euler[1]=math.atan2(d.x,d.z)
    cap=motor+d*.112;o=box('Motor rear interface cap',cap,(.145,.165,.043),p['black'],.009);o.rotation_euler[1]=math.atan2(d.x,d.z)
    for sideSign in [-1,1]:
        box('Motor side inset',(motor.x,sideSign*.081,motor.z),(.085,.007,.104),p['black'],.004,rot=(0,math.atan2(d.x,d.z),0))
        for i in range(5):
            pos=motor+d*((i-2)*.018)
            o=box('Motor air louver',(pos.x,sideSign*.088,pos.z),(.071,.010,.007),p['green'],.001);o.rotation_euler[1]=math.atan2(d.x,d.z)
        screw('Motor casing screw',(motor.x+.042,sideSign*.085,motor.z+.045),p['steel'],'Y',.004)
    # Short control cable clipped to the shaft; no detachable companion.
    tube('Control cable',[(t.x+.019,.018,t.z-.009),(.36,.018,1.27),(.43,.018,1.38)],.0025,p['black'],1)
    return ('city-string-grass-trimmer','ループハンドル付きの草刈りトリマー','Loop-handle string grass trimmer','公園の縁や庭の草刈り場面に使う長軸トリマー。斜めの金属シャフト、分割継手、開口ループハンドル、上部グリップとモーター外装、曲面ガード、スプールと短い固定ナイロン線を備えます。電池・電源コード・草・内部駆動部は付属せず、回転・切断動作・性能・安全認証はありません。','A long-shaft string trimmer for park edges and garden-care scenes, with an angled metal shaft, coupling, open loop handle, upper grip and motor exterior, curved guard, spool and short fixed nylon-line ends. Battery, power cord, grass and working internals are omitted; no spinning, cutting behavior, performance or safety certification is supplied.',['garden','maintenance','grass-trimmer','草刈り'])


def helical_flight(name,inner,outer,zstart,rise,turns,thickness,material):
    # A single continuous thick helical strip, closed at both ends.
    steps=96;vs=[]
    for i in range(steps+1):
        a=i/steps*turns*math.tau;z=zstart+rise*i/steps
        for r,h in [(inner,-thickness/2),(outer,-thickness/2),(outer,thickness/2),(inner,thickness/2)]:vs.append((r*math.cos(a),r*math.sin(a),z+h))
    fs=[]
    for i in range(steps):
        for k in range(4):fs.append((i*4+k,i*4+(k+1)%4,(i+1)*4+(k+1)%4,(i+1)*4+k))
    fs.extend([(3,2,1,0),(steps*4,steps*4+1,steps*4+2,steps*4+3)])
    return mesh(name,vs,fs,material)


def earth_auger():
    p=palette()
    cyl('Pointed pilot tip',(0,0,.055),0,.11,p['steel'],segments=24,bevel=0,radius2=.020)
    cyl('Auger central shaft',(0,0,.433),.019,.81,p['dark'],segments=32,bevel=.001)
    helical_flight('Single continuous ground-auger helix',.017,.127,.12,.615,3.0,.006,p['steel'])
    # A modest terminal shoe joins the first turn rather than duplicating a bit.
    shoe=profile('Lower flight terminal shoe',[(.016,-.024),(.137,-.024),(.143,.018),(.022,.024)],.009,p['dark'],'Z',.0015);shoe.location.z=.116
    cyl('Upper bit coupling sleeve',(0,0,.807),.034,.10,p['steel'],segments=32,bevel=.003)
    rod('Coupling cross pin',(-.046,0,.809),(.046,0,.809),.007,p['dark'],20)
    screw('Coupling retaining head',(.048,0,.809),p['steel'],'X',.010)
    cyl('Lower gearbox neck',(0,0,.88),.061,.088,p['black'],segments=32,bevel=.005)
    cyl('Round drive gearbox',(0,0,.938),.104,.084,p['dark'],segments=40,bevel=.009)
    for i in range(6):
        a=i*math.tau/6;screw('Gearbox perimeter bolt',(.082*math.cos(a),.082*math.sin(a),.985),p['steel'],radius=.006)
    # Wide two-handed frame, with two separately open gripped sides.
    for side in [-1,1]:
        pts=[(side*.070,-.065,.976),(side*.295,-.150,.983),(side*.383,-.127,1.004),(side*.402,-.077,1.015),(side*.402,.077,1.015),(side*.383,.127,1.004),(side*.295,.15,.983),(side*.070,.065,.976)]
        loop('Two-handed side handle frame',pts,.018,p['dark'])
        rod('Rubber outer hand grip',(side*.402,-.074,1.015),(side*.402,.074,1.015),.026,p['rubber'],28)
        box('Handle attachment plate',(side*.092,0,.987),(.055,.17,.026),p['steel'],.004)
        for y in [-.058,.058]:screw('Handle plate bolt',(side*.092,y,1.004),p['dark'],radius=.006)
    box('Fixed right hand trigger',(.372,-.005,.984),(.018,.089,.014),p['red'],.004)
    tube('Handle control cable',[(.379,-.08,1.011),(.27,-.14,.992),(.10,-.08,1.06)],.003,p['black'],1)
    # Taller asymmetric drive shell distinguishes it from the long-shaft trimmer.
    box('Drive motor casing',(0,0,1.075),(.223,.211,.19),p['orange'],.030)
    box('Recessed upper cover seam',(0,0,1.17),(.206,.195,.018),p['black'],.006)
    box('Motor top cover',(0,0,1.189),(.213,.202,.035),p['orange'],.012)
    box('Rear power interface enclosure',(0,.137,1.077),(.178,.091,.139),p['black'],.018)
    box('Power interface closed cap',(0,.186,1.077),(.161,.014,.118),p['dark'],.006)
    for side in [-1,1]:
        box('Drive side vent recess',(side*.114,0,1.088),(.008,.126,.080),p['black'],.005)
        for i in range(5):box('Drive side vent louver',(side*.120,-.050+i*.025,1.088),(.008,.010,.068),p['orange'],.0015)
        for y,z in [(-.074,1.023),(.071,1.144)]:screw('Drive shell screw',(side*.116,y,z),p['steel'],'X',.004)
    box('Blank control button',(0,-.109,1.113),(.035,.012,.027),p['red'],.004)
    return ('city-two-handle-earth-auger','両手ハンドル付きの穴掘りオーガー','Two-handle earth auger','公園の植栽や庭園整備の場面に置く直立姿勢の穴掘り機。左右の開口ハンドル、駆動ヘッド外装と丸い減速部、固定ピン付き継手、一本の連続らせん刃と先端を造形しています。地面・土・電池・内部駆動部は含まず、掘削・回転動作・荷重性能・安全認証はありません。','An upright earth-auger prop for planting and garden-maintenance scenes, with open left/right handles, drive-head exterior and round gearbox, pinned coupling, one continuous helical ground bit and pilot tip. Ground, soil, battery and working internals are omitted; no drilling, rotation behavior, load performance or safety certification is supplied.',['garden','maintenance','earth-auger','穴掘り'])


BUILDERS=[spreader,hedge_trimmer,grass_trimmer,earth_auger]


def underside(path):
    # Additional low area lights make actual underside geometry legible.
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];coords=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
    lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);center=(lo+hi)/2;span=max(hi-lo);lights=[]
    for p in [(-.7,-1.0,-1.1),(1.1,.8,-.65)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(p)*span);o=bpy.context.object;o.data.energy=250*span*span;o.data.size=1.2*span;look_at(o,center);lights.append(o)
    common.render(path,-55,-32,800)
    for o in lights:bpy.data.objects.remove(o,do_unlink=True)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-018/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true',help='Reproduce GLB/STL/metadata without rendering presentation images.')
    args=parser.parse_args(args);out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    if args.geometry_only:common.render=lambda *a,**k:None
    for builder in BUILDERS:
        reset();spec=builder()
        if args.only and spec[0]!=args.only:continue
        common.publish_asset(*spec,out,'scripts/city_expansion/garden_tools.py',azimuth=-55,elevation=24)
        if not args.geometry_only:underside(out/'_qa'/f'{spec[0]}-underside.png')
