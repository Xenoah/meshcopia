"""Four original static ventilation components for Meshcopia, CC BY 4.0, Xenoah.
Portable geometry authored in Blender Z-up metres; common exports Y-up metres.
No borrowed meshes, textures or brand forms. Not functional engineering equipment.
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
    return dict(steel=mat('Satin galvanized appearance steel',(.48,.57,.61),.72,.32),
        light=mat('Light formed aluminum',(.68,.73,.74),.74,.28),
        blue=mat('Deep blue powder coat',(.035,.13,.21),.28,.39),
        dark=mat('Graphite mechanical fittings',(.035,.052,.062),.25,.47),
        rubber=mat('Dark isolation pads',(.020,.027,.031),0,.78),
        acoustic=mat('Charcoal acoustic splitter appearance',(.075,.091,.103),0,.92),
        amber=mat('Amber actuator cover',(.87,.38,.045),.05,.40))


def cyl(name,pos,radius,depth,material,axis='Z',n=32,bevel=.0015):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name,a,b,r,material,n=16):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,material,n=n,bevel=min(.0007,r*.09))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def ring(name,pos,major,minor,material,axis='Z',n=64,m=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,major_radius=major,minor_radius=minor,location=pos)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,name,material,smooth=True)


def screw(name,pos,material,axis='Z',r=.009):
    return cyl(name,pos,r,.006,material,axis,n=8,bevel=.0004)


def annular(name,profile,material,pos=(0,0,0),axis='Z',n=64,smooth=True):
    """Closed revolved radial/axial profile; profile is cyclic, without poles."""
    vs=[(r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z) for r,z in profile for j in range(n)]
    fs=[(k*n+j,k*n+(j+1)%n,((k+1)%len(profile))*n+(j+1)%n,((k+1)%len(profile))*n+j) for k in range(len(profile)) for j in range(n)]
    o=mesh(name,vs,fs,material,smooth=False);o.location=pos
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if smooth:
        for k in range(len(profile)):
            r1,z1=profile[k];r2,z2=profile[(k+1)%len(profile)]
            for j in range(n):o.data.polygons[k*n+j].use_smooth=abs(z2-z1)>1e-8
    return o


def closed_ribbon(name,grid,thickness,material,offset_axis=None):
    """Thick curved panel with explicit closed edge walls, no single-sided blades."""
    rows=len(grid);cols=len(grid[0]);top=[Vector(v) for row in grid for v in row];bottom=[]
    for i in range(rows):
        for j in range(cols):
            if offset_axis is not None:normal=Vector(offset_axis)
            else:
                du=Vector(grid[i][min(j+1,cols-1)])-Vector(grid[i][max(j-1,0)])
                dv=Vector(grid[min(i+1,rows-1)][j])-Vector(grid[max(i-1,0)][j])
                normal=du.cross(dv).normalized()
            bottom.append(top[i*cols+j]-normal*thickness)
    count=len(top);faces=[]
    for layer in range(2):
        for i in range(rows-1):
            for j in range(cols-1):
                q=(layer*count+i*cols+j,layer*count+i*cols+j+1,layer*count+(i+1)*cols+j+1,layer*count+(i+1)*cols+j)
                faces.append(q if layer==0 else tuple(reversed(q)))
    border=list(range(cols))+[i*cols+cols-1 for i in range(1,rows)]+[(rows-1)*cols+j for j in range(cols-2,-1,-1)]+[i*cols for i in range(rows-2,0,-1)]
    faces += [(a,b,b+count,a+count) for a,b in zip(border,border[1:]+border[:1])]
    o=mesh(name,top+bottom,faces,material)
    for f in o.data.polygons:f.use_smooth=f.index<2*(rows-1)*(cols-1)
    return o


def roof_turbine():
    p=palette();n=64;vs=[]
    # A square-to-round roof plate retains its real central opening.
    for z,inner in [(.018,False),(.034,False),(.034,True),(.018,True)]:
        for j in range(n):
            a=j*math.tau/n;r=.205 if inner else .34/max(abs(math.cos(a)),abs(math.sin(a)))
            vs.append((r*math.cos(a),r*math.sin(a),z))
    fs=[(k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j) for k in range(4) for j in range(n)]
    mesh('Square roof flashing with open throat',vs,fs,p['steel'])
    for x in [-.28,.28]:
        for y in [-.28,.28]:screw('Roof flashing fixing head',(x,y,.039),p['dark'],r=.011)
    annular('Hollow roof duct collar',[(.216,.028),(.216,.270),(.204,.270),(.204,.028)],p['steel'])
    annular('Collar crimp band',[(.223,.236),(.223,.268),(.215,.268),(.215,.236)],p['light'])
    for a in [0,math.tau/3,2*math.tau/3]:
        rod('Internal spindle support spoke',(.197*math.cos(a),.197*math.sin(a),.204),(0,0,.214),.009,p['dark'])
    cyl('Static central rotor spindle',(0,0,.485),.016,.56,p['dark'],n=24)
    annular('Lower rotating blade support rim',[(.226,.283),(.246,.299),(.247,.321),(.233,.333),(.224,.311)],p['light'])
    # Twenty separate thick swept vanes form an open cage, not a mushroom cap.
    for k in range(20):
        grid=[]
        for i in range(15):
            t=i/14;z=.310+.418*t;r=.238+.119*math.sin(math.pi*t)
            theta=k*math.tau/20+.55*t
            row=[]
            for j in range(5):
                u=(j/4-.5);a=theta+u*.205
                rr=r+.010*math.sin((u+.5)*math.pi)
                row.append((rr*math.cos(a),rr*math.sin(a),z))
            grid.append(row)
        closed_ribbon('Closed swept turbine vane',grid,.0055,p['light'])
    annular('Upper blade clamping rim',[(.239,.713),(.245,.727),(.238,.743),(.219,.743),(.219,.718)],p['steel'])
    # Low crown covers only the upper spindle; the side cage remains open.
    cyl('Upper rotor crown',(0,0,.741),.230,.026,p['steel'],n=64,bevel=.006)
    cyl('Upper spindle bearing cover',(0,0,.765),.055,.032,p['dark'],n=32,bevel=.004)
    cyl('Bearing cover top',(0,0,.783),.043,.009,p['light'],n=32,bevel=.002)
    return ('city-roof-turbine-vent','湾曲羽根ローター付きの屋根用タービン換気口','Roof turbine vent with curved open-blade rotor',
        '屋根面の通気立上り部に配置するタービン式換気口の静的プロップ。中央が開口した角形水切り板、中空カラー、内部支持スポークと主軸、上下の保持リング、厚みを持つ20枚の湾曲羽根で構成した開放ローター、頂部軸受カバーを造形しています。既存の傘型排気カウルではなく、回転部の羽根籠を表した構成です。屋根と接続ダクトは付属せず、回転、風力駆動、換気流量、雨仕舞、防火や建築基準への適合は実装・検証していません。',
        'A static turbine-vent prop for a roof ventilation riser, with a genuinely open square flashing throat, hollow collar, internal spindle supports, upper and lower retaining rings, twenty thick curved vanes forming an open rotor cage, and a top bearing cover. This depicts a rotating-blade assembly rather than a mushroom exhaust cowl. Roof and connecting duct are omitted. No rotation, wind drive, airflow, weather sealing, fire performance or building-code compliance is implemented or validated.',
        ['ventilation','roof-turbine','rotor','屋根換気'])


def prism_y(name,outline,y0,y1,material,bevel=0):
    vs=[(x,y,z) for y in [y0,y1] for x,z in outline];n=len(outline)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def centrifugal_fan():
    p=palette();p['impeller']=mat('Pale impeller alloy',(.65,.69,.70),.28,.38);cx=-.115;cz=.665;depth=.38
    pts=[]
    for i in range(97):
        t=i/96;a=math.pi/2+1.5*math.pi*t;r=.335+.175*t
        pts.append((cx+r*math.cos(a),cz+r*math.sin(a)))
    outline=pts+[(cx+.510,cz+.740),(cx+.235,cz+.740),(cx+.235,cz+.235)]
    # Closed side panels with a true front inlet cut all the way through.
    for front in [True,False]:
        y0,y1=(-.202,-.184) if front else (.184,.202)
        panel=prism_y('Volute inlet-side plate' if front else 'Volute motor-side plate',outline,y0,y1,p['blue'])
        if front:
            cutter=cyl('Temporary inlet cutter',(cx,-.193,cz),.264,.12,None,'Y',64,0)
            mod=panel.modifiers.new('Real inlet aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            bpy.context.view_layer.objects.active=panel;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
        mod=panel.modifiers.new('Side plate edge rounding','BEVEL');mod.width=.003;mod.segments=2
        mod=panel.modifiers.new('Side plate weighted normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    # The increasing-radius scroll skin is a closed sheet, capped at its two ends.
    outer=[];inner=[]
    for i,(x,z) in enumerate(pts):
        a=math.pi/2+1.5*math.pi*i/96
        outer.append([(x,-depth/2,z),(x,depth/2,z)])
    closed_ribbon('Thick spiral volute outer wall',outer,.015,p['blue'])
    box('Tangential outlet outer wall',(cx+.502,0,cz+.370),(.016,.38,.740),p['blue'],.003)
    box('Tangential outlet inner wall',(cx+.243,0,cz+.490),(.016,.38,.500),p['blue'],.003)
    cutwater=[[(cx-.003,-.190,cz+.336),(cx-.003,.190,cz+.336)],[(cx+.235,-.190,cz+.235),(cx+.235,.190,cz+.235)]]
    closed_ribbon('Volute tongue and outlet transition',cutwater,.014,p['blue'])
    # Open rectangular terminal flange at the upward tangential mouth.
    for x in [cx+.222,cx+.524]:box('Outlet flange side bar',(x,0,cz+.750),(.032,.46,.025),p['steel'],.003)
    for y in [-.217,.217]:box('Outlet flange end bar',(cx+.373,y,cz+.750),(.274,.026,.025),p['steel'],.003)
    for x in [cx+.222,cx+.524]:
        for y in [-.180,.180]:screw('Outlet flange fixing',(x,y,cz+.767),p['dark'],'Z',.008)
    annular('Flared circular inlet bellmouth',[(.264,-.183),(.288,-.224),(.299,-.294),(.285,-.307),(.274,-.235),(.252,-.192)],p['light'],(cx,0,cz),'Y',64)
    # Negative axial profile values point toward the front inlet (-Y).
    bell=bpy.context.scene.objects.get('Flared circular inlet bellmouth');bell.rotation_euler[0]=-math.pi/2
    cyl('Impeller rear disc',(cx,.102,cz),.238,.018,p['impeller'],'Y',64,.002)
    cyl('Impeller central hub',(cx,-.012,cz),.067,.220,p['dark'],'Y',40,.003)
    for k in range(12):
        grid=[]
        for i in range(9):
            t=i/8;r=.079+.151*t;a=k*math.tau/12-.52*t
            grid.append([(cx+r*math.cos(a),y,cz+r*math.sin(a)) for y in [-.101,.090]])
        closed_ribbon('Closed backward-curved impeller blade',grid,.006,p['impeller'])
    # Sparse guard leaves the true impeller and its inlet cavity visible.
    for r in [.102,.205,.286]:ring('Inlet protective concentric guard',(cx,-.320,cz),r,.0045,p['dark'],'Y',64,6)
    for k in range(8):
        a=k*math.tau/8;rod('Inlet protective radial guard',(cx+.066*math.cos(a),-.323,cz+.066*math.sin(a)),(cx+.286*math.cos(a),-.323,cz+.286*math.sin(a)),.0045,p['dark'],10)
    cyl('Inlet guard center badge',(cx,-.325,cz),.071,.012,p['steel'],'Y',32,.002)
    # Separate rear drive motor, shaft coupling and mounting pedestal.
    cyl('Rear shaft coupling',(cx,.255,cz),.060,.118,p['dark'],'Y',32,.003)
    cyl('Electric motor body',(cx,.485,cz),.146,.335,p['steel'],'Y',48,.006)
    for y in [.343,.373,.403,.433,.463,.493,.523,.553,.583]:
        annular('Motor circumferential cooling fin',[(.145,-.004),(.160,-.004),(.160,.004),(.145,.004)],p['steel'],(cx,y,cz),'Y',48)
    cyl('Motor rear end cover',(cx,.669,cz),.143,.039,p['dark'],'Y',48,.006)
    for x in [-.083,-.041,0,.041,.083]:
        length=2*math.sqrt(max(0,.107**2-x*x));box('Motor end cover raised ventilation rib',(cx+x,.692,cz),(.010,.008,length),p['steel'],.001)
    box('Motor terminal box',(cx,.492,cz+.162),(.160,.145,.091),p['blue'],.009)
    cyl('Motor cable gland',(cx+.098,.492,cz+.164),.022,.044,p['dark'],'X',24,.003)
    for x in [-.325,.265]:
        box('Long floor mounting skid',(x,.164,.030),(.105,1.11,.060),p['blue'],.007)
        for y in [-.335,.662]:screw('Skid mounting head',(x,y,.066),p['steel'],r=.014)
    for y in [-.113,.125]:
        box('Volute lower support crossbar',(-.030,y,.190),(.740,.072,.260),p['blue'],.007)
    box('Motor pedestal lower cross-support',(-.030,.502,.096),(.740,.316,.072),p['blue'],.006)
    for x in [cx-.103,cx+.103]:
        box('Motor foot pedestal',(x,.502,.331),(.075,.295,.540),p['blue'],.006)
        box('Motor foot shelf',(x,.502,.507),(.115,.316,.035),p['steel'],.004)
    for x,z in [(cx-.27,cz+.12),(cx-.24,cz-.24),(cx+.23,cz-.30),(cx+.34,cz+.10)]:
        for y in [-.209,.209]:screw('Volute side service fixing',(x,y,z),p['steel'],'Y',.010)
    return ('city-centrifugal-exhaust-fan','渦巻ケーシングと背面モーターの遠心排気ファン','Centrifugal exhaust fan with volute and rear motor',
        '機械室や換気設備架台に置く据置き遠心排気ファンの静的プロップ。渦巻状の厚いケーシング、貫通した円形吸込口と疎な保護ガード、奥に見える湾曲羽根インペラー、開いた接線方向吐出口、背面モーターと冷却フィン、軸継手、支持脚と固定スキッドを造形しています。軸流送風機や冷媒凝縮器とは異なる構成です。配線、接続ダクト、回転・通電・排気動作、圧力／流量曲線、騒音、熱・防火・保護等級や適合認証は含みません。',
        'A stationary centrifugal exhaust-fan prop for a plant room or ventilation equipment base, with a thick spiral volute, genuinely open circular inlet and sparse protective guard, visible curved-blade impeller, open tangential discharge, rear drive motor with cooling fins, coupling, supports and mounting skids. Its construction is distinct from an axial blower or refrigerant condenser. Wiring and connecting ducts are omitted, with no rotation, electrical operation, exhaust behavior, pressure/flow curve, noise, thermal/fire or ingress-protection performance, or compliance certification supplied.',
        ['ventilation','centrifugal-fan','plant-room','遠心ファン'])


def duct_frame(name,y,width,height,zcenter,material,rail=.045,depth=.024):
    for x in [-width/2+rail/2,width/2-rail/2]:box(name+' side',(x,y,zcenter),(rail,depth,height),material,.003)
    for z in [zcenter-height/2+rail/2,zcenter+height/2-rail/2]:box(name+' crossmember',(0,y,z),(width-2*rail+.004,depth,rail),material,.003)


def damper():
    p=palette();w=1.02;h=1.015;zc=.552
    for x in [-.498,.498]:box('Open damper casing side',(x,0,zc),(.024,.372,h),p['steel'],.004)
    for z in [.056,1.048]:box('Open damper casing cross sheet',(0,0,z),(.973,.372,.024),p['steel'],.003)
    for y in [-.202,.202]:
        duct_frame('Damper end connecting flange',y,1.105,1.105,zc,p['light'],.052,.028)
        for x in [-.524,.524]:
            for z in [.080,.552,1.024]:screw('Damper flange fixing head',(x,y+(.018 if y>0 else -.018),z),p['dark'],'Y',.010)
    angle=math.radians(34)
    for i,z in enumerate([.203,.436,.669,.902]):
        cyl('Through-blade pivot shaft',(.029,0,z),.014,1.163,p['dark'],'X',24,.001)
        blade=box('Thick partially open airflow damper blade',(0,0,z),(.955,.242,.025),p['steel'],.006,(angle,0,0))
        # Stiffening edge hems follow the same partially open pose.
        for sign in [-1,1]:
            yy=sign*.110*math.cos(angle);zz=z+sign*.110*math.sin(angle)
            box('Rolled damper blade edge hem',(0,yy,zz),(.936,.016,.029),p['light'],.004,(angle,0,0))
        for side in [-1,1]:cyl('Side-wall pivot bearing',(side*.519,0,z),.030,.028,p['blue'],'X',24,.003)
        # Each crank is physically connected to a shared vertical tie bar.
        end=(.600,.087,z+.059)
        rod('External blade crank arm',(.600,0,z),end,.013,p['blue'],16)
        cyl('Crank-to-link joint',(.622,.087,z+.059),.022,.034,p['steel'],'X',20,.002)
    box('Common vertical damper tie linkage',(.642,.087,.611),(.024,.027,.739),p['blue'],.004)
    box('Actuator mounting bracket',(.569,-.093,.480),(.120,.122,.221),p['steel'],.005)
    box('External control actuator lower housing',(.649,-.099,.481),(.112,.215,.186),p['dark'],.010)
    box('External control actuator amber cover',(.714,-.099,.481),(.042,.198,.168),p['amber'],.009)
    cyl('Actuator output coupling',(.642,0,.436),.038,.113,p['dark'],'X',28,.003)
    cyl('Actuator cable gland',(.650,-.233,.481),.018,.060,p['dark'],'Y',24,.002)
    box('Actuator blank cover inset',(.739,-.099,.492),(.007,.113,.061),p['dark'],.002)
    for y in [-.170,-.026]:
        for z in [.420,.542]:screw('Actuator cover captive screw',(.741,y,z),p['steel'],'X',.005)
    return ('city-multiblade-duct-damper','外部連結ロッドと駆動部付きの多翼ダクトダンパー','Multiblade duct damper with external linkage and actuator',
        '矩形換気ダクトの途中に組み込む流量調整ダンパーの静的プロップ。両端が開いた短いケーシングと接続フランジ、部分開度で固定した4枚の厚い羽根、各羽根の貫通軸と軸受、外側クランクと共通連結ロッド、琥珀色の外部アクチュエーターを造形しています。静止ルーバーとは異なり連動羽根機構の外形を持ちますが、可動リグ、角度制御、気密遮断、空気流量、電気制御、防火・防煙性能や認証は付属しません。接続ダクトと吊り架台は別途配置してください。',
        'A static airflow-control damper prop for installation within a rectangular ventilation duct, with an open-ended short casing and connecting flanges, four thick blades fixed partially open, through-shafts and bearings, exterior cranks and a common tie linkage, and an amber-covered external actuator. The linked-blade mechanism is structurally distinct from a static wall louver, but no movable rig, angle control, airtight shutoff, airflow, electrical control, fire/smoke performance or certification is supplied. Connecting ducts and suspension supports must be placed separately.',
        ['ventilation','duct-damper','actuator','ダンパー'])


def rounded_splitter(name,x,z0,z1,width,length,material):
    # Capsule section in X/Y gives genuine semicircular leading/trailing noses.
    r=width/2;d=length/2-r;outline=[]
    for i in range(17):
        a=math.pi*i/16;outline.append((x+r*math.cos(a),d+r*math.sin(a)))
    for i in range(17):
        a=math.pi+math.pi*i/16;outline.append((x+r*math.cos(a),-d+r*math.sin(a)))
    n=len(outline);vs=[(xx,yy,z) for z in [z0,z1] for xx,yy in outline]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,vs,fs,material)
    for f in o.data.polygons:f.use_smooth=f.index>=2 and (f.index-2 not in [16,33])
    return o


def silencer():
    p=palette()
    for x in [-.526,.526]:box('Silencer open casing side',(x,0,.486),(.028,1.46,.816),p['steel'],.005)
    for z in [.092,.880]:box('Silencer open casing upper or lower sheet',(0,0,z),(1.024,1.46,.028),p['steel'],.004)
    for y in [-.750,.750]:
        duct_frame('Open silencer end connecting flange',y,1.155,.927,.486,p['light'],.052,.029)
        for x in [-.548,.548]:
            for z in [.092,.486,.880]:screw('Silencer end flange fixing',(x,y+(.018 if y>0 else -.018),z),p['dark'],'Y',.011)
        for x in [-.28,.28]:
            for z in [.049,.923]:screw('Silencer upper lower flange fixing',(x,y+(.018 if y>0 else -.018),z),p['dark'],'Y',.009)
    # Three longitudinal splitters divide the open bore into four real passages.
    for x in [-.285,0,.285]:
        rounded_splitter('Full-height acoustic splitter with rounded noses',x,.106,.866,.132,1.326,p['light'])
        for side in [-1,1]:
            box('Inset acoustic splitter side panel',(x+side*.067,0,.486),(.009,1.120,.666),p['acoustic'],.004)
            for z in [.164,.808]:box('Splitter retaining edge strip',(x+side*.074,0,z),(.012,1.130,.021),p['steel'],.002)
            for y in [-.49,.49]:
                for z in [.177,.795]:screw('Splitter retaining screw',(x+side*.083,y,z),p['dark'],'X',.005)
    for side in [-1,1]:
        box('Inner side-wall acoustic liner',(side*.509,0,.486),(.012,1.31,.748),p['acoustic'],.003)
        for y in [-.473,.473]:box('External casing stiffening seam',(side*.547,y,.486),(.020,.031,.748),p['light'],.003)
    box('Silencer side access panel',(.552,0,.484),(.019,.622,.470),p['light'],.008)
    box('Silencer side access gasket',(.541,0,.484),(.009,.640,.488),p['dark'],.003)
    for y in [-.274,.274]:
        for z in [.286,.682]:screw('Access panel captive fixing',(.566,y,z),p['dark'],'X',.009)
    for y in [-.535,.535]:
        box('Silencer supporting mounting rail',(0,y,.043),(1.115,.094,.086),p['blue'],.005)
        for x in [-.50,.50]:screw('Mounting rail fixing',(x,y,.091),p['steel'],r=.011)
    for x in [-.37,.37]:
        for y in [-.470,.470]:box('Upper lifting-tab seat',(x,y,.905),(.100,.075,.028),p['steel'],.004)
    return ('city-duct-silencer-module','開口流路と3枚の吸音隔壁を持つダクト消音器','Open duct silencer with three acoustic splitters',
        '機械室や空調ダクトの直線区間に置く矩形消音器の静的プロップ。前後に貫通する開口筐体、接続フランジ、丸い前後端を持つ3枚の縦長吸音隔壁と4本の流路、濃色の側面パネルと内張り、外部補強継ぎ目、側面点検蓋、下面の支持レールを造形しています。空箱ではなく内部の隔壁を含む構成ですが、材質は不透明な単色外観用で、吸音材の微細孔や繊維は表現していません。接続ダクト、音響減衰、周波数特性、圧力損失、実際の空気流、断熱・防火性能や法規適合は含みません。',
        'A static rectangular duct-silencer prop for a straight ventilation run or plant room, with an open-through casing and connecting flanges, three full-height longitudinal acoustic splitters with rounded leading and trailing noses forming four passages, dark side panels and liners, external stiffening seams, a side access cover and lower mounting rails. It includes genuine internal splitter geometry rather than an empty box, but its opaque constant-color materials are appearance-only, with no microscopic pores or fibers modeled. Connecting ducts, acoustic attenuation, frequency response, pressure loss, actual airflow, insulation/fire performance and regulatory compliance are omitted.',
        ['ventilation','duct-silencer','acoustic-splitter','消音器'])


BUILDERS=[roof_turbine,centrifugal_fan,damper,silencer]


def underside(path):
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];coords=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
    lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)])
    center=(lo+hi)/2;span=max(hi-lo);lights=[]
    for pos in [(-.7,-1.0,-1.1),(1.1,.8,-.65)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*span);o=bpy.context.object;o.data.energy=250*span*span;o.data.size=1.2*span;look_at(o,center);lights.append(o)
    common.render(path,-55,-32,800)
    for o in lights:bpy.data.objects.remove(o,do_unlink=True)


if __name__=='__main__':
    arg=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-024/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true',help='Skip only rendering; core export and metadata stay identical.')
    args=parser.parse_args(arg);out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    if args.geometry_only:common.render=lambda *a,**k:None
    for builder in BUILDERS:
        reset();spec=builder()
        if args.only and spec[0]!=args.only:continue
        common.publish_asset(*spec,out,'scripts/city_expansion/ventilation_components.py',azimuth=-55,elevation=24)
        if not args.geometry_only:underside(out/'_qa'/f'{spec[0]}-underside.png')
