"""Four original indoor climate-control appearance props. Xenoah, CC BY 4.0.
No external models, image textures or brands. Static scene geometry only: no
heat, humidity, refrigerant, airflow, electrical or mechanical operation.
Author Z-up metres; immutable common.py exports metre-valued Y-up GLB/STL.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(white=mat('Warm ivory appliance enamel',(.78,.80,.76),.06,.36),
        pale=mat('Pale molded trim',(.64,.69,.68),.03,.43),
        teal=mat('Muted teal removable reservoir',(.16,.34,.37),.03,.45),
        steel=mat('Satin galvanized mounting metal',(.40,.47,.49),.68,.42),
        silver=mat('Satin pipe and shaft metal',(.61,.66,.67),.76,.33),
        brass=mat('Unbranded warm metal valve fittings',(.47,.32,.12),.65,.40),
        dark=mat('Dark interior mechanical material',(.08,.10,.105),.12,.60),
        rubber=mat('Graphite rubber and seals',(.028,.034,.038),0,.77),
        screen=mat('Inactive blue grey control panel',(.07,.16,.19),.06,.33),
        indicator=mat('Unlit muted green indicator',(.18,.36,.25),.02,.50))


def cyl(name,pos,radius,depth,material,axis='Z',n=32,bevel=.001):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name,a,b,radius,material,n=24):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,radius,(b-a).length,material,n=n,bevel=min(.001,radius*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def ring(name,pos,major,minor,material,axis='Z',n=48,m=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,major_radius=major,minor_radius=minor,location=pos)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,name,material,smooth=True)


def sleeve(name,pos,outer,inner,length,material,axis='Z',n=40):
    # Four cyclic rings form an annular wall with two genuinely open ends.
    vs=[]
    for r,z in [(outer,-length/2),(outer,length/2),(inner,length/2),(inner,-length/2)]:
        vs += [(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n)]
    fs=[]
    for k in range(4):
        for i in range(n):fs.append((k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i))
    o=mesh(name,vs,fs,material);o.location=pos
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=(f.index//n in [0,2])
    return o


def prism_x(name,profile,x,width,material,bevel=.003):
    n=len(profile);vs=[(xx,y,z) for xx in [x-width/2,x+width/2] for y,z in profile]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def rect_frame_xy(name,center,w,d,t,h,material,bevel=.002):
    # One closed annular mesh avoids exact coincident edges between butt-jointed bars.
    vs=[]
    for ww,dd,z in [(w,d,-h/2),(w,d,h/2),(w-2*t,d-2*t,h/2),(w-2*t,d-2*t,-h/2)]:
        vs.extend([(-ww/2,-dd/2,z),(ww/2,-dd/2,z),(ww/2,dd/2,z),(-ww/2,dd/2,z)])
    fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)]
    o=mesh(name,vs,fs,material,min(bevel,t*.2,h*.2));o.location=center
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def slotted_mount(name,x,y,z,w=.055,h=.12,depth=.010,material=None):
    # A single manifold plate surrounding a true vertical fixing slot.
    holew=w*.28;holeh=h*.42;vs=[]
    for ww,hh,yy in [(w,h,-depth/2),(w,h,depth/2),(holew,holeh,depth/2),(holew,holeh,-depth/2)]:
        vs.extend([(-ww/2,yy,-hh/2),(ww/2,yy,-hh/2),(ww/2,yy,hh/2),(-ww/2,yy,hh/2)])
    fs=[(k*4+i,k*4+(i+1)%4,((k+1)%4)*4+(i+1)%4,((k+1)%4)*4+i) for k in range(4) for i in range(4)]
    o=mesh(name,vs,fs,material,.002);o.location=(x,y,z)
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def radiator():
    p=palette()
    # Distinct pressed panel sections, not a cast-iron column radiator or a solid decal.
    for y in [-.041,.041]:
        for i in range(14):
            x=(i-6.5)*.068
            box('Pressed vertical radiator panel section',(x,y,.338),(.064,.024,.514),p['white'],.010)
        for z in [.095,.579]:cyl('Horizontal radiator water manifold',(0,y,z),.022,.976,p['white'],'X',40,.002)
    # Sparse broad internal convector strips, separated by real air space.
    for i in range(14):
        x=(i-6.5)*.068
        box('Interior broad convector strip',(x,0,.338),(.014,.063,.420),p['steel'],.002)
    for x in [-.497,.497]:box('Radiator side cover',(x,0,.338),(.018,.112,.548),p['white'],.006)
    for y in [-.053,.053]:box('Top grille longitudinal edge',(0,y,.620),(1.006,.013,.018),p['white'],.004)
    for i in range(29):
        box('Open top grille cross slat',((i-14)*.0338,0,.620),(.012,.095,.014),p['white'],.003)
    # Rear wall fixing plates and hooked stand-offs remain part of this wall unit.
    for x in [-.315,.315]:
        slotted_mount('Rear wall bracket upper slot',x,.143,.448,w=.062,h=.160,depth=.012,material=p['steel'])
        slotted_mount('Rear wall bracket lower slot',x,.143,.206,w=.062,h=.126,depth=.012,material=p['steel'])
        for z in [.208,.476]:
            box('Wall bracket stand-off arm',(x,.097,z),(.040,.105,.016),p['steel'],.003)
            box('Radiator hooked retaining tab',(x,.061,z+.017),(.048,.014,.050),p['steel'],.003)
        box('Vertical rear bracket spine',(x,.136,.332),(.030,.011,.176),p['steel'],.002)
    # Upper-right static thermostat valve with a substantial ribbed hand control.
    cyl('Upper inlet threaded collar',(.525,-.041,.579),.026,.060,p['brass'],'X',32,.002)
    cyl('Upper hex valve union',(.560,-.041,.579),.032,.031,p['silver'],'X',6,.002)
    cyl('Static valve body',(.590,-.041,.579),.027,.052,p['brass'],'X',32,.002)
    cyl('Thermostat collar',(.622,-.041,.579),.031,.018,p['pale'],'X',32,.002)
    cyl('Unmarked thermostat hand knob',(.661,-.041,.579),.037,.069,p['white'],'X',40,.004)
    for i in range(12):
        a=i*math.tau/12
        box('Thermostat grip rib',(.661,-.041+.035*math.cos(a),.579+.035*math.sin(a)),(.052,.008,.008),p['pale'],.002,rot=(a,0,0))
    cyl('Thermostat end cap',(.699,-.041,.579),.030,.009,p['pale'],'X',32,.001)
    rod('Upper valve downward pipe',(.590,-.041,.560),(.590,-.041,.473),.014,p['silver'])
    cyl('Upper pipe end collar',(.590,-.041,.470),.019,.022,p['brass'],n=24)
    # Low return connection with a downward tail and a small nonfunctional cap.
    cyl('Lower return union',(.534,-.041,.095),.026,.065,p['silver'],'X',6,.002)
    cyl('Lower return block',(.575,-.041,.095),.024,.041,p['brass'],'X',28,.002)
    rod('Lower return descending tail',(.575,-.041,.094),(.575,-.041,.018),.013,p['silver'])
    cyl('Return tail union',(.575,-.041,.017),.018,.025,p['brass'],n=6,bevel=.001)
    cyl('Upper left bleed fitting',(-.522,-.041,.579),.018,.035,p['silver'],'X',24,.001)
    cyl('Bleed fitting square plug',(-.544,-.041,.579),.009,.012,p['brass'],'X',4,.0008)
    cyl('Lower left blanking cap',(-.523,-.041,.095),.023,.032,p['white'],'X',24,.002)
    return ('city-panel-radiator','壁掛け室内パネルラジエーター','Wall-mounted indoor panel radiator',
        '住宅・宿泊施設・事務室の壁際に配置する室内暖房器具の外観模型。二列の縦長パネル区画、上部の実開口グリル、少数の内部対流板、左右の配管継手、無目盛りの固定サーモスタットつまみ、放気栓と実スロット付き背面壁金具を造形。屋外の冷媒用室外機やテラス用ヒーターとは用途・構造が異なります。床基準原点から壁面への取付高さと離隔を調整してください。暖房・通水・温度制御・操作機構はなく、耐圧・耐熱・取付安全性や認証を示しません。',
        'An indoor room-heating appearance prop for walls in homes, accommodation and offices. Two rows of pressed vertical panel sections, genuinely open top grille, sparse interior convector strips, side pipe unions, fixed unmarked thermostat knob, bleed fitting and slotted rear wall brackets are modeled. Its indoor room-heating purpose and panel form differ from an outdoor refrigerant condenser or patio heater. Adjust wall installation height and stand-off from the base-centered origin. Heating, plumbing, temperature control and working mechanisms are absent; pressure, heat resistance, mounting safety and certification are not claimed.',
        ['interior','radiator','wall-mounted','heating-prop','ラジエーター'])


def air_curtain():
    p=palette()
    profile=[(-.139,.068),(-.139,.258),(-.115,.286),(.103,.286),(.130,.264),(.130,.061),(.095,.045),(-.112,.045)]
    for x in [-.574,.574]:prism_x('Air curtain rounded end enclosure',profile,x,.042,p['white'],.009)
    box('Air curtain upper cover',(0,-.003,.280),(1.110,.252,.027),p['white'],.010)
    box('Air curtain rear service panel',(0,.121,.170),(1.110,.016,.220),p['pale'],.006)
    # Three-sided front surround and a separate grille define an actual inlet recess.
    box('Air curtain inlet upper brow',(0,-.136,.254),(1.110,.025,.028),p['white'],.006)
    box('Air curtain lower front nose',(0,-.130,.079),(1.110,.040,.058),p['white'],.011)
    for x in [-.531,.531]:box('Air curtain inlet vertical surround',(x,-.137,.172),(.031,.023,.142),p['white'],.005)
    for i in range(31):
        box('Separated inlet grille vertical bar',((i-15)*.033,-.145,.172),(.009,.016,.133),p['pale'],.0025)
    for z in [.140,.204]:box('Intake grille rear cross support',(0,-.127,z),(1.043,.009,.007),p['steel'],.0015)
    # The inlet is not backed by a sealed black decal: an actual rotor occupies the cavity.
    cyl('Fixed crossflow rotor shaft',(0,.017,.177),.013,1.044,p['silver'],'X',24,.001)
    for x in [-.500,0,.500]:cyl('Crossflow rotor end and center disk',(x,.017,.177),.061,.009,p['dark'],'X',40,.001)
    for i in range(12):
        a=i*math.tau/12
        box('Crossflow rotor broad blade',(0,.017+.052*math.cos(a),.177+.052*math.sin(a)),(1.010,.016,.009),p['steel'],.0017,rot=(a+.35,0,0))
    # Bottom discharge is a recessed opening between the front and rear rails.
    box('Bottom discharge rear lip',(0,.101,.056),(1.106,.028,.023),p['white'],.005)
    for x in [-.532,.532]:box('Bottom discharge end cheek',(x,-.011,.056),(.029,.190,.023),p['white'],.004)
    for y in [-.066,-.013,.040]:
        box('Fixed directional discharge vane',(0,y,.050),(1.030,.036,.008),p['pale'],.002,rot=(math.radians(-24),0,0))
    for x in [-.33,.33]:box('Outlet vane support pivot bar',(x,-.011,.068),(.012,.170,.012),p['steel'],.002)
    # Rear brackets have actual open fixing slots and broad supporting flanges.
    for x in [-.37,.37]:
        slotted_mount('Air curtain wall mounting slot',x,.165,.182,w=.080,h=.176,depth=.016,material=p['steel'])
        box('Rear bracket stand-off',(x,.140,.110),(.074,.066,.018),p['steel'],.003)
        box('Rear bracket upper locating hook',(x,.143,.246),(.074,.058,.014),p['steel'],.003)
    for x in [-.48,.48]:
        for z in [.090,.250]:cyl('Rear cover recessed fastening',(x,.133,z),.006,.005,p['dark'],'Y',12,.0005)
    box('Air curtain inactive status insert',(.514,-.155,.091),(.040,.007,.018),p['screen'],.003)
    cyl('Unlit status dot',(.513,-.160,.092),.003,.003,p['indicator'],'Y',16,.0003)
    return ('city-overdoor-air-curtain','出入口上部用エアカーテン','Overdoor indoor air curtain',
        '店舗や公共施設の室内出入口上部に置く、幅広いエアカーテン外観。丸みのある端部、前面の実開口吸込みグリル、奥の固定横流ローター、下側の開いた吹出口と三枚の方向板、背面点検板・壁取付スロットを造形。屋外室外機、受動的な壁換気口、可搬送風機、ダクト単体とは異なる出入口上部の一体備品です。原点は最下面中央で、扉上の高さと壁オフセットは利用側で設定します。空気流・送風・加熱・電装・可動部は実装せず、換気性能・電気安全性・認証は未検証。',
        'A wide air-curtain appearance unit for the indoor side above shop and civic-building doorways. Rounded end enclosures surround a genuinely open front intake grille, recessed fixed crossflow rotor, open lower discharge throat with three direction vanes, rear service panel and slotted wall mounts. This complete overdoor appliance is distinct from an outdoor condenser, passive wall vent, portable blower or standalone duct module. The origin is bottom-centered; set doorway installation height and wall offset in the scene. No airflow, fan drive, heating, electrical or moving functions are implemented, and ventilation performance, electrical safety and certification are unvalidated.',
        ['interior','doorway','air-curtain','climate-control-prop','エアカーテン'])


def dehumidifier():
    p=palette()
    # Four small rolling contacts and their yokes provide honest under-base structure.
    for x in [-.121,.121]:
        for y in [-.095,.095]:
            cyl('Caster wheel',(x,y,.025),.025,.024,p['rubber'],'X',32,.002)
            cyl('Caster wheel hub',(x+.014,y,.025),.010,.005,p['steel'],'X',20,.0008)
            for xx in [-.018,.018]:box('Caster fork cheek',(x+xx,y,.040),(.006,.039,.042),p['steel'],.002)
            cyl('Caster swivel stem',(x,y,.064),.010,.035,p['steel'],n=20,bevel=.001)
    box('Dehumidifier base chassis',(0,0,.084),(.310,.267,.043),p['dark'],.012)
    box('Base underside inspection cover',(0,0,.064),(.222,.177,.012),p['steel'],.005)
    # Separate shell walls leave real intake/outlet volumes rather than a solid box body.
    for x in [-.161,.161]:box('Tall molded side shell',(x,0,.343),(.018,.286,.500),p['white'],.008)
    box('Front upper appliance shell',(0,-.137,.420),(.310,.020,.346),p['white'],.010)
    box('Rear lower service shell',(0,.137,.204),(.308,.018,.238),p['pale'],.006)
    for x in [-.151,.151]:box('Rear intake side surround',(x,.142,.447),(.020,.021,.235),p['white'],.005)
    for z in [.335,.559]:box('Rear intake horizontal surround',(0,.142,z),(.291,.021,.023),p['white'],.005)
    for i in range(9):
        box('Rear intake separated louver',(0,.147,.352+i*.023),(.285,.023,.010),p['pale'],.003,rot=(math.radians(17),0,0))
    for x in [-.095,0,.095]:box('Rear inlet internal grille support',(x,.127,.446),(.008,.010,.198),p['steel'],.0015)
    # Coil-like structure is visible in the cavity, not a black rectangle flush with the grille.
    for x in [-.10,-.05,0,.05,.10]:box('Sparse internal exchanger plate',(x,.073,.444),(.008,.055,.181),p['steel'],.0015)
    for z in [.369,.440,.512]:rod('Internal exchanger cross tube',(-.116,.062,z),(.116,.062,z),.007,p['silver'],20)
    # Front water tank is fixed slightly withdrawn. Its open basin and pull are separate geometry.
    ty=-.039
    box('Tank basin floor',(0,ty,.117),(.277,.235,.020),p['teal'],.008)
    for x in [-.136,.136]:box('Tank basin side wall',(x,ty,.182),(.014,.235,.139),p['teal'],.005)
    box('Tank basin rear wall',(0,ty+.112,.182),(.262,.014,.139),p['teal'],.005)
    box('Removable tank front fascia',(0,ty-.120,.182),(.304,.025,.153),p['teal'],.010)
    # Recessed pull formed by an open surrounding ledge with a set-back inner wall.
    box('Tank handle rear recess',(0,ty-.137,.211),(.110,.008,.033),p['dark'],.004)
    for x in [-.061,.061]:box('Tank pull end support',(x,ty-.155,.209),(.014,.036,.020),p['teal'],.004)
    box('Tank projecting pull bridge',(0,ty-.169,.209),(.121,.014,.020),p['teal'],.004)
    box('Tank top front lip',(0,ty-.126,.256),(.286,.022,.013),p['pale'],.004)
    # Tank top remains actually open, revealing the empty interior and slight pull-out gap.
    for x in [-.128,.128]:box('Tank sliding guide rail',(x,.003,.106),(.012,.232,.015),p['pale'],.003)
    # Top discharge frame and angled vanes reveal a 60 mm deep recess.
    box('Top front control shelf',(0,-.101,.585),(.323,.079,.027),p['white'],.008)
    box('Top rear discharge rim',(0,.132,.585),(.323,.026,.027),p['white'],.006)
    for x in [-.151,.151]:box('Top discharge side rim',(x,.030,.585),(.024,.182,.027),p['white'],.006)
    for y in [-.044,-.014,.016,.046,.076,.106]:
        box('Top outlet fixed direction louver',(0,y,.583),(.276,.020,.008),p['pale'],.002,rot=(math.radians(-28),0,0))
    box('Top discharge recessed guide',(0,-.052,.541),(.281,.012,.065),p['dark'],.003)
    box('Inactive humidity control display',(-.038,-.107,.602),(.108,.043,.006),p['screen'],.004)
    for x in [.048,.090,.128]:cyl('Unmarked top control button',(x,-.108,.603),.010,.005,p['pale'],n=24,bevel=.001)
    # Raised rigid carry handle has a real hand opening, fixed in its lifted pose.
    for x in [-.145,.145]:
        cyl('Handle side pivot',(x,0,.554),.017,.022,p['steel'],'X',24,.001)
        box('Carry handle upright',(x,0,.620),(.020,.025,.132),p['pale'],.006)
    box('Raised carry grip',(0,0,.686),(.302,.030,.027),p['dark'],.009)
    # Open rear drain outlet, visibly separate from the lower service shell.
    sleeve('Rear drain outlet open bore',(.105,.171,.224),.014,.008,.057,p['pale'],'Y',32)
    ring('Drain outlet collar',(.105,.153,.224),.015,.003,p['steel'],'Y',32,8)
    cyl('Rear cable gland',(-.095,.152,.132),.013,.024,p['rubber'],'Y',24,.001)
    # Compact parked cable, not loose floor clutter or separately counted accessory.
    tube('Parked power cable',[(-.095,.163,.132),(-.116,.191,.169),(-.112,.195,.263),(-.056,.195,.283),(-.036,.195,.249),(-.046,.190,.204)],.004,p['rubber'],1)
    box('Parked cable plug',(-.045,.188,.195),(.022,.018,.031),p['dark'],.004)
    box('Rear cord retaining clip',(-.114,.166,.243),(.040,.031,.024),p['pale'],.004)
    return ('city-portable-dehumidifier','水タンク付き室内用移動式除湿機','Portable indoor dehumidifier with water tank',
        '住宅・管理室・収納室の床に配置する室内用除湿機の外観。背面吸込みルーバーと上面吹出口の実際の隙間、奥の簡略化した交換器板、少し引き出した固定姿勢の空の水タンクと取手、開いた排水口、持運びハンドル、四個のキャスター、背面収納コードを造形。屋外室外機や単体の送風機ではなく、タンク回収式の室内備品として区別します。除湿・通水・冷媒・電装・移動・タンク操作は実装していません。能力・防水性・電気安全性・認証は未検証。',
        'An indoor moisture-removal appearance prop for floors in homes, facility rooms and storage interiors. Genuine gaps in the rear intake and top outlet reveal recessed simplified exchanger plates. An empty removable-looking water tank is fixed slightly withdrawn, with a real pull handle, open drain outlet, raised carry handle, four casters and parked rear cord. The tank-collection indoor appliance is distinct from an outdoor condenser or standalone blower. Dehumidification, plumbing, refrigerant, electrical operation, rolling and tank movement are not implemented. Capacity, water resistance, electrical safety and certification are unvalidated.',
        ['interior','dehumidifier','appliance','water-tank','除湿機'])


def cassette():
    p=palette()
    # Low white square room-facing trim. The lowest face is the ceiling-facing appliance underside.
    rect_frame_xy('Outer ceiling cassette fascia',(0,0,.050),.842,.842,.038,.048,p['white'],.009)
    # Four corner blocks separate the four genuine discharge margins.
    for x in [-.322,.322]:
        for y in [-.322,.322]:box('Cassette fascia corner',(x,y,.048),(.159,.159,.043),p['white'],.010)
    rect_frame_xy('Return grille perimeter',(0,0,.041),.474,.474,.024,.034,p['white'],.006)
    # Central square grille with open spaces into the recessed return plenum.
    for i in range(11):box('Central return grille slat',(0,(i-5)*.040,.036),(.427,.010,.018),p['pale'],.0025)
    for x in [-.145,0,.145]:box('Central grille rear support',(x,0,.051),(.010,.428,.012),p['pale'],.002)
    rect_frame_xy('Recessed return plenum walls',(0,0,.113),.462,.462,.015,.116,p['dark'],.002)
    # Actual circular inlet fan representation above grille, not a sealed dark face.
    cyl('Return impeller center hub',(0,0,.183),.041,.042,p['dark'],n=40,bevel=.003)
    ring('Return impeller outer ring',(0,0,.170),.158,.008,p['steel'],n=64,m=8)
    for i in range(8):
        a=i*math.tau/8
        box('Fixed return impeller broad vane',(.094*math.cos(a),.094*math.sin(a),.169),(.124,.028,.016),p['steel'],.004,rot=(0,math.radians(15),a+.22))
    # Four perimeter discharge recesses and broad fixed directional vanes.
    for side in [-1,1]:
        box('Discharge outer guide X',(side*.374,0,.099),(.014,.441,.098),p['dark'],.003)
        box('Discharge outer guide Y',(0,side*.374,.099),(.441,.014,.098),p['dark'],.003)
        for offset in [-.017,.017]:
            box('Long X-margin discharge vane',(side*.311+offset,0,.041),(.026,.437,.010),p['pale'],.0025,rot=(0,math.radians(side*24),0))
            box('Long Y-margin discharge vane',(0,side*.311+offset,.041),(.437,.026,.010),p['pale'],.0025,rot=(math.radians(-side*24),0,0))
        for d in [-.161,.161]:
            box('X-margin vane end support',(side*.311,d,.065),(.113,.012,.014),p['steel'],.002)
            box('Y-margin vane end support',(d,side*.311,.065),(.012,.113,.014),p['steel'],.002)
    # Upper service housing is a real box enclosure behind the ceiling trim.
    for x in [-.319,.319]:box('Upper cassette metal side wall',(x,0,.238),(.014,.638,.226),p['steel'],.005)
    for y in [-.319,.319]:box('Upper cassette metal end wall',(0,y,.238),(.613,.014,.226),p['steel'],.005)
    box('Upper cassette removable service lid',(0,0,.351),(.650,.650,.018),p['steel'],.006)
    for x in [-.243,.243]:box('Service lid broad stiffening rib',(x,0,.365),(.023,.530,.016),p['steel'],.004)
    # Four broad mounting ears with actual central slots, each tied into a side wall.
    for x in [-.354,.354]:
        for y in [-.230,.230]:
            rect_frame_xy('Open suspension mounting ear',(x,y,.278),.098,.075,.019,.014,p['silver'],.0025)
            box('Suspension ear upstand',(x*.906,y,.301),(.014,.075,.059),p['silver'],.003)
    # Rear-side connection collars, control-box cover and restrained screw count.
    box('Upper electrical service box',(0,.352,.224),(.241,.064,.117),p['pale'],.007)
    for x in [-.093,.093]:cyl('Electrical cover fastening',(x,.388,.224),.006,.005,p['dark'],'Y',12,.0005)
    for x,r in [(-.204,.014),(-.252,.011)]:
        cyl('Capped refrigerant connection collar',(x,.346,.196),r,.050,p['brass'],'Y',28,.001)
        cyl('Connection protective blank cap',(x,.374,.196),r*.86,.009,p['dark'],'Y',24,.001)
    sleeve('Cassette condensate drain socket',(.235,.347,.152),.018,.011,.055,p['pale'],'Y',32)
    # Small inactive sensor panel lies on one solid corner, not over an airflow opening.
    box('Inactive corner status insert',(.318,-.320,.022),(.084,.035,.006),p['screen'],.004)
    for x in [.296,.322,.345]:cyl('Unlit cassette status dot',(x,-.321,.0175),.0035,.003,p['indicator'],n=16,bevel=.0003)
    return ('city-ceiling-cassette-air-conditioner','四方向吹出し天井カセット型室内機','Four-way ceiling-cassette indoor air conditioner',
        '事務室・店舗・公共施設の天井へ配置する角形カセット室内機の外観。中央の実開口吸込み格子、奥の固定インペラー表現、四辺に独立した吹出し空間と固定方向板、上部点検筐体、実スロット付き吊金具、閉じた接続キャップと開いた排水ソケットを造形。室内天井側の一体機器で、既存の屋外冷媒凝縮器や受動換気口・ダクトとは異なります。最下面Y=0の原点から天井高さへ移動し、上部筐体は天井裏へ納める想定です。冷暖房・冷媒・通水・電装・空気流・可動部は実装せず、機器性能・吊下げ安全性・認証は未検証。',
        'A square indoor cassette appearance unit for office, shop and civic-building ceilings. It models a genuinely open central return grille with recessed fixed impeller representation, four separate perimeter discharge spaces and fixed direction vanes, upper service housing, slotted suspension brackets, capped connection fittings and open condensate socket. The complete room-side ceiling appliance is distinct from the existing outdoor refrigerant condenser, passive vents and duct modules. Move the lowest-face Y=0 origin to the ceiling height, with the upper housing above the ceiling plane. Heating/cooling, refrigerant, plumbing, electrical operation, airflow and moving parts are absent; equipment performance, suspension safety and certification are unvalidated.',
        ['interior','ceiling','air-conditioner','cassette','天井カセット'])


BUILDERS=[radiator,air_curtain,dehumidifier,cassette]
if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-033/assets');ap.add_argument('--only',default='');ap.add_argument('--geometry-only',action='store_true');a=ap.parse_args(argv)
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    if a.geometry_only:common.render=lambda *args,**kwargs:None
    for fn in BUILDERS:
        reset();spec=fn()
        if a.only and spec[0]!=a.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/indoor_climate_fixtures.py',azimuth=-55,elevation=(-28 if spec[0]=='city-ceiling-cassette-air-conditioner' else 25))
