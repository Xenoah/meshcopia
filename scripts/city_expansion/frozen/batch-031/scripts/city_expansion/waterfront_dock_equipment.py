"""Four original waterfront dock appearance assemblies, Xenoah / CC BY 4.0.
No third-party geometry, brands, photographs, texture maps or font assets.
Static visualization only, not marine engineering, load-bearing or safety design.
Blender Z-up construction; immutable common exports actual Y-up metre-valued GLB/STL.
"""
import argparse, math, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(aluminum=mat('Satin marine aluminum appearance',(.45,.52,.55),.76,.40),
                steel=mat('Satin stainless hardware',(.61,.67,.69),.82,.34),
                dark=mat('Graphite structural finish',(.055,.072,.076),.38,.49),
                float=mat('Charcoal molded sealed-float appearance',(.036,.050,.055),0,.76),
                rubber=mat('Black polymer rollers and fenders',(.022,.028,.030),0,.83),
                wood=mat('Warm sealed timber plank appearance',(.38,.22,.105),0,.65),
                wood2=mat('Lighter sealed timber plank appearance',(.43,.27,.14),0,.65),
                blue=mat('Desaturated marine blue machinery enamel',(.075,.255,.31),.25,.42),
                brass=mat('Dull bronze bearing detail',(.41,.28,.12),.76,.44),
                face=mat('Unlit opaque control screen',(.036,.082,.088),.15,.38),
                red=mat('Inactive red stop-button appearance',(.57,.046,.027),0,.40),
                green=mat('Inactive green button appearance',(.056,.26,.12),0,.43))


def cyl(name,pos,radius,depth,material,axis='Z',n=32,bevel=.0015):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name,a,b,r,material,n=24):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,r,(b-a).length,material,n=n,bevel=min(.001,r*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def beam(name,a,b,w,d,material,bevel=.004):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(w,d,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def fastener(name,pos,material,axis='Z',r=.009,sign=1):
    cyl(name+' washer',pos,r*1.5,r*.30,material,axis,n=20,bevel=0)
    v=list(pos);v['XYZ'.index(axis)]+=sign*r*.5
    cyl(name+' hex head',v,r,r*.85,material,axis,n=6,bevel=.0006)


def profile(name,points,center,depth,material,axis='X',bevel=.003):
    n=len(points)
    vs=[(s,a,b) if axis=='X' else (a,s,b) for s in [center-depth/2,center+depth/2] for a,b in points]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def cut(obj,cutter):
    bpy.context.view_layer.objects.active=obj
    for m in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
    mod=obj.modifiers.new('Genuine through aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    if obj.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for f in obj.data.polygons:f.use_smooth=False
    obj.data.update()
    return obj


def lathe(name,profile,pos,material,n=80,axis='Z',scale=(1,1,1)):
    """Continuous closed radial shell. Axis ends use unique vertices, never zero rings."""
    vs=[];rings=[]
    for r,z in profile:
        if abs(r)<1e-10:rings.append([len(vs)]);vs.append((0,0,z))
        else:
            row=[]
            for j in range(n):
                row.append(len(vs));a=j*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),z))
            rings.append(row)
    fs=[]
    for a,b in zip(rings,rings[1:]+rings[:1]):
        if len(a)==len(b)==1:continue
        for j in range(n):
            if len(a)==1:fs.append((a[0],b[(j+1)%n],b[j]))
            elif len(b)==1:fs.append((a[j],a[(j+1)%n],b[0]))
            else:fs.append((a[j],a[(j+1)%n],b[(j+1)%n],b[j]))
    o=mesh(name,vs,fs,material);o.location=pos;o.scale=scale
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:
        zz=[o.data.vertices[i].co.z for i in f.vertices];f.use_smooth=max(zz)-min(zz)>1e-7
    return o


def rounded_horns(material):
    # One continuous cast crossbar with upward-curved, tapered horns and rounded poles.
    p=[(-.387,.285,0,0),(-.381,.285,.013,.012),(-.368,.284,.022,.020),(-.347,.280,.029,.026),(-.314,.272,.035,.032),(-.270,.262,.043,.039),(-.218,.251,.052,.045),(-.160,.243,.061,.049),(-.090,.239,.067,.051),(0,.238,.070,.052),(.090,.239,.067,.051),(.160,.243,.061,.049),(.218,.251,.052,.045),(.270,.262,.043,.039),(.314,.272,.035,.032),(.347,.280,.029,.026),(.368,.284,.022,.020),(.381,.285,.013,.012),(.387,.285,0,0)]
    vs=[];rows=[];n=48
    for x,z,ry,rz in p:
        if ry==0:rows.append([len(vs)]);vs.append((x,0,z))
        else:
            row=[]
            for j in range(n):
                a=j*math.tau/n;row.append(len(vs));vs.append((x,ry*math.cos(a),z+rz*math.sin(a)))
            rows.append(row)
    fs=[]
    for a,b in zip(rows,rows[1:]):
        for j in range(n):
            if len(a)==1:fs.append((a[0],b[j],b[(j+1)%n]))
            elif len(b)==1:fs.append((a[j],b[0],a[(j+1)%n]))
            else:fs.append((a[j],b[j],b[(j+1)%n],a[(j+1)%n]))
    return mesh('Continuous swept double-horn cast crown',vs,fs,material,smooth=True)


def floating_dock():
    p=palette()
    # Four individually sealed float modules, not a single black foundation block.
    for x in [-.60,.60]:
        for y in [-.79,.79]:
            box('Individual sealed molded float',(x,y,.265),(.80,1.40,.46),p['float'],.095)
            box('Float molded upper shoulder',(x,y,.475),(.84,1.43,.085),p['float'],.034)
            for yy in [y-.48,y,y+.48]:
                box('Float lower longitudinal molded rib',(x,yy,.071),(.64,.095,.064),p['float'],.025)
            for xx in [x-.37,x+.37]:
                box('Float side molded reinforcement',(xx,y,.253),(.065,1.12,.075),p['float'],.023)
            for yy in [y-.48,y+.48]:
                box('Float retention cross strap',(x,yy,.523),(.94,.055,.022),p['steel'],.006)
                for xx in [x-.43,x+.43]:
                    box('Float retention strap drop',(xx,yy,.473),(.026,.055,.105),p['steel'],.005)
                    fastener('Float strap fastener',(xx,yy,.539),p['dark'],r=.010)
    for x in [-1.015,1.015]:
        box('Continuous perimeter side frame',(x,0,.611),(.13,3.22,.17),p['aluminum'],.009)
        box('Long protective rub strip',(x*1.071,0,.646),(.049,3.17,.113),p['rubber'],.015)
    for y in [-1.545,1.545]:box('Perimeter end frame',(0,y,.611),(1.95,.13,.17),p['aluminum'],.009)
    for y in [-1.05,-.525,0,.525,1.05]:box('Under-deck cross joist',(0,y,.622),(1.96,.076,.135),p['aluminum'],.005)
    for x in [-.52,.52]:box('Longitudinal float support stringer',(x,0,.566),(.075,3.08,.095),p['aluminum'],.005)
    # Thin diagonal underframe braces remain visible in the underside review.
    for y in [-.78,.78]:
        beam('Underside diagonal frame brace',(-.91,y-.65,.527),(.91,y+.65,.527),.035,.021,p['steel'],.003)
    for i in range(20):
        y=-1.52+i*.160
        box('Individual sealed deck plank',(0,y,.727),(2.12,.148,.055),p['wood'] if i%4 else p['wood2'],.006)
        for x in [-.97,-.52,.52,.97]:cyl('Flush deck plank fixing',(x,y,.756),.006,.004,p['dark'],n=12,bevel=.0004)
    # Corner brackets are genuine small aperture plates, with no adjacent dock included.
    for x in [-.83,.83]:
        for y in [-1.66,1.66]:
            o=box('Projecting dock connection lug',(x,y,.600),(.17,.29,.045),p['aluminum'],.013)
            cut(o,cyl('Connection pin aperture cutter',(x,y+(1 if y>0 else -1)*.065,.600),.028,.11,None,n=40,bevel=0))
            fastener('Connection bracket inner fixing',(x,y-(1 if y>0 else -1)*.065,.629),p['steel'],r=.012)
            box('Connection lug support web',(x,y*.945,.559),(.038,.145,.095),p['aluminum'],.005)
    for x in [-1.022,1.022]:
        for y in [-1.40,0,1.40]:fastener('Side frame assembly bolt',(x+(1 if x>0 else -1)*.071,y,.605),p['steel'],'X',.012,1 if x>0 else -1)
    return ('city-floating-dock-section','分割フロート式浮桟橋ユニット','Floating dock section','運河沿いや小規模マリーナの水際に配置する浮桟橋の外観ユニット。隙間を設けた個別デッキ板、外周フレームと横桁・縦桁・下面斜材、四つの独立した密閉フロート外形、保持金具、側面緩衝帯、実際に穴の開いた端部連結金具を備えます。水面、岸、係留索、船や隣接ユニットは含みません。浮力、波追従、連結動作、耐荷重、耐食性や安全性は検証していない静的な外観モデルです。','A floating-dock appearance section for canal edges and small marina scenes. It has individual gapped deck planks, perimeter framing, transverse joists, longitudinal stringers and underside diagonal braces, four separate sealed-float exteriors, retaining hardware, side rub strips and genuinely apertured end connection lugs. No water, shore, mooring line, boat or adjoining section is included. Buoyancy, wave response, connection movement, loading, corrosion resistance and safety have not been validated; this is a static appearance model.',['waterfront','floating-dock','marina','桟橋'])


def gangway():
    p=palette();z=lambda y:.555-.22*y
    for x in [-.53,.53]:
        beam('Sloping side structural stringer',(x,-1.57,z(-1.57)-.074),(x,1.57,z(1.57)-.074),.09,.14,p['aluminum'],.006)
        beam('Raised sloping toe edge',(x,-1.56,z(-1.56)+.045),(x,1.56,z(1.56)+.045),.025,.105,p['aluminum'],.003)
    for y in [-1.45,-.75,0,.75,1.45]:
        beam('Under-deck transverse bearer',(-.53,y,z(y)-.07),(.53,y,z(y)-.07),.06,.065,p['aluminum'],.004)
    for i in range(34):
        y=-1.518+i*.092
        box('Individual aluminum walking slat',(0,y,z(y)),(1.015,.080,.035),p['aluminum'],.003,rot=(math.atan(-.22),0,0))
        # Fine non-abrasive longitudinal ridges represent extrusion texture with real geometry.
        for yy in [-.021,.021]:box('Raised slat traction rib',(0,y+yy,z(y+yy)+.020),(.96,.005,.004),p['steel'],.001,rot=(math.atan(-.22),0,0))
    for x in [-.55,.55]:
        for y in [-1.43,-.71,.01,.73,1.45]:
            rod('Gangway rail upright',(x,y,z(y)-.035),(x,y,z(y)+.972),.023,p['aluminum'])
            box('Rail post mounting shoe',(x,y,z(y)+.026),(.074,.10,.12),p['dark'],.005)
            for dz in [-.006,.060]:fastener('Upright shoe bolt',(x+(1 if x>0 else -1)*.042,y,z(y)+dz),p['steel'],'X',.007,1 if x>0 else -1)
        rod('Continuous sloped upper handrail',(x,-1.49,z(-1.49)+.974),(x,1.49,z(1.49)+.974),.028,p['aluminum'],32)
        rod('Continuous sloped intermediate rail',(x,-1.43,z(-1.43)+.505),(x,1.45,z(1.45)+.505),.019,p['aluminum'],24)
        for y in [-1.49,1.49]:cyl('Rounded handrail end closure',(x,y,z(y)+.974),.029,.014,p['dark'],'Y',n=28,bevel=.004)
        # Closed thin triangular braces reinforce the sloped access structure.
        for y in [-1.12,-.40,.32,1.04]:
            profile('Triangular post-to-stringer brace',[(y-.18,z(y-.18)-.13),(y+.18,z(y+.18)-.13),(y+.18,z(y+.18)+.12)],x*.92,.018,p['aluminum'],'X',.002)
    # Shore hinge has bolted mounting plate, interleaved knuckles and one axle.
    shore=box('Shore hinge mounting plate',(0,-1.715,.868),(1.25,.24,.055),p['dark'],.012)
    for x in [-.51,.51]:
        cut(shore,cyl('Shore anchor through-hole',(x,-1.765,.868),.018,.14,None,n=32,bevel=0))
        box('Hinge plate standing ear',(x,-1.660,.930),(.061,.13,.14),p['dark'],.008)
    for x in [-.40,-.20,0,.20,.40]:
        cyl('Alternating shore hinge knuckle',(x,-1.620,.906),.048,.165,p['aluminum'] if int((x+.41)*10)%2 else p['dark'],'X',n=40,bevel=.002)
    rod('Continuous shore hinge pin',(-.65,-1.620,.906),(.65,-1.620,.906),.018,p['steel'],32)
    for x in [-.66,.66]:fastener('Hinge pin retaining head',(x,-1.620,.906),p['steel'],'X',.026,1 if x>0 else -1)
    # Polymer landing rollers are held in paired brackets beneath the low end.
    for x in [-.35,.35]:
        for xx in [x-.085,x+.085]:
            profile('Landing roller support cheek',[(1.36,.24),(1.70,.205),(1.72,.105),(1.45,.105)],xx,.023,p['aluminum'],'X',.005)
        cyl('Landing polymer roller',(x,1.585,.118),.118,.130,p['rubber'],'X',n=48,bevel=.012)
        cyl('Landing roller bearing hub',(x,1.585,.118),.043,.144,p['steel'],'X',n=32,bevel=.003)
        rod('Landing roller axle',(x-.108,1.585,.118),(x+.108,1.585,.118),.014,p['steel'])
        for xx in [x-.114,x+.114]:fastener('Landing roller axle head',(xx,1.585,.118),p['steel'],'X',.019,1 if xx>x else -1)
    beam('Landing threshold lip',(-.51,1.58,z(1.58)),(.51,1.58,z(1.58)),.075,.025,p['steel'],.002)
    return ('city-hinged-dock-gangway','ヒンジ付き桟橋渡り通路','Hinged dock gangway','岸から浮桟橋への渡り通路を固定した傾斜姿勢で表現した一式。実際に隙間のある細幅の床板、傾斜側桁と横桁、つま先縁、二段の手すりと支持金具、穴付き岸側取付板と分割ヒンジ筒・通しピン、下端の一対の支持ローラーを備えます。岸や桟橋は含みません。ヒンジ・ローラー・潮位追従は動かず、実際の通行、荷重支持、アクセシビリティ適合性や海洋環境での安全性は検証していません。','A shore-to-floating-dock access span in one fixed sloping pose. The assembly includes genuinely gapped narrow walking slats, sloping side stringers and transverse bearers, toe edges, two-level side rails and brackets, an apertured shore attachment plate with segmented hinge knuckles and through pin, and a pair of landing rollers beneath the low end. No shore or dock is included. The hinge, rollers and tide response do not operate. Passage, loading, accessibility compliance and marine safety are unvalidated.',['waterfront','gangway','dock-access','渡り通路'])


def cleat():
    p=palette()
    base=box('Rounded substantial cleat mounting base',(0,0,.031),(.535,.292,.062),p['dark'],.026)
    for x in [-.204,.204]:
        for y in [-.091,.091]:
            cut(base,cyl('Actual cleat base mounting-hole cutter',(x,y,.031),.021,.16,None,n=48,bevel=0))
    for x in [-.118,.118]:
        lathe('Flared cast cleat support',[(0,.050),(.079,.050),(.081,.061),(.075,.077),(.063,.103),(.055,.147),(.060,.191),(.070,.217),(0,.217)],(x,0,0),p['dark'],n=64,scale=(1,.82,1))
    rounded_horns(p['dark'])
    # Broad raised seats and a slim center rib give cast geometry depth without filling holes.
    box('Central cast foot rib',(0,0,.068),(.285,.111,.038),p['dark'],.018)
    return ('city-dock-mooring-cleat','桟橋用両角係船クリート','Dock mooring cleat','浮桟橋や運河の縁に配置する低い両角型係船クリート。先端へ細くなり緩く反り上がる一体の二本角、二つの広がった鋳物風支持部、中央補強部、丸めた厚いベースと四つの実際の貫通取付穴を備えます。道路用ボラードとは異なる低い係船金具の外観で、索や取付ボルトは含みません。係留動作、荷重支持、材料強度、耐食性や安全性は検証していない静的表示用です。','A low double-horn mooring cleat for dock edges and canal-side scenes. A continuous crown has two gently upswept tapering horns above flared cast-style supports, a central reinforcing seat, rounded substantial base and four genuine through mounting holes. This is low-profile mooring hardware rather than a road bollard. No line or mounting bolts are included. Static appearance only; mooring operation, loading, material strength, corrosion resistance and safety are unvalidated.',['waterfront','mooring-cleat','dock','係船クリート'])


def capstan():
    p=palette()
    base=box('Capstan equipment mounting sole',(0,.15,.090),(.88,1.17,.080),p['dark'],.028)
    for x in [-.345,.345]:
        for y in [-.32,.62]:
            cut(base,cyl('Sole anchor aperture',(x,y,.055),.021,.24,None,n=32,bevel=0))
    for x in [-.26,.26]:box('Underside support runner',(x,.15,.025),(.092,1.02,.050),p['dark'],.010)
    cyl('Cast reduction gearbox barrel',(0,-.11,.227),.278,.250,p['blue'],n=64,bevel=.022)
    cyl('Gearbox upper joint flange',(0,-.11,.350),.302,.048,p['blue'],n=64,bevel=.008)
    for j in range(8):
        a=(j+.5)*math.tau/8
        fastener('Gearbox perimeter bolt',(.266*math.cos(a),-.11+.266*math.sin(a),.380),p['steel'],r=.012)
    for x in [-.23,.23]:
        box('Gearbox mounting foot',(x,-.11,.124),(.15,.38,.057),p['blue'],.012)
        for y in [-.235,.015]:fastener('Gearbox foot bolt',(x,y,.158),p['steel'],r=.012)
    # Continuous shaped drum with top/bottom flanges and a concave hauling waist.
    lathe('Vertical waisted capstan rope drum',[(0,.387),(.237,.387),(.282,.397),(.294,.414),(.296,.440),(.285,.459),(.248,.475),(.222,.514),(.203,.565),(.195,.625),(.195,.687),(.202,.737),(.220,.783),(.251,.813),(.289,.824),(.299,.838),(.299,.866),(.287,.883),(.241,.890),(0,.890)],(0,-.11,0),p['steel'],n=96)
    cyl('Drum upper recessed end cover',(0,-.11,.896),.198,.020,p['dark'],n=64,bevel=.004)
    cyl('Drum top center bearing cap',(0,-.11,.914),.076,.031,p['brass'],n=48,bevel=.008)
    for j in range(6):
        a=j*math.tau/6
        fastener('Upper cover fastening',(.155*math.cos(a),-.11+.155*math.sin(a),.910),p['steel'],r=.008)
    # Enclosed motor and coupling belong to the same capstan assembly, not a second asset.
    cyl('Gearbox rear motor coupling',(0,.230,.254),.111,.165,p['blue'],'Y',n=48,bevel=.010)
    cyl('Horizontal electric motor exterior',(0,.461,.254),.136,.350,p['blue'],'Y',n=48,bevel=.010)
    for j in range(14):
        a=j*math.tau/14
        o=box('Motor exterior cooling fin',(.140*math.cos(a),.463,.254+.140*math.sin(a)),(.027,.295,.014),p['blue'],.003)
        o.rotation_euler[1]=math.pi/2-a
    cyl('Motor rear fan cover',(0,.658,.254),.143,.061,p['dark'],'Y',n=48,bevel=.012)
    # Raised radial ribs are closed decorative cover geometry, not open ventilation claims.
    for j in range(10):
        a=j*math.tau/10
        rod('Rear fan cover radial rib',(.042*math.cos(a),.691,.254+.042*math.sin(a)),(.116*math.cos(a),.691,.254+.116*math.sin(a)),.006,p['blue'],16)
    cyl('Rear fan cover center cap',(0,.696,.254),.037,.012,p['blue'],'Y',n=32,bevel=.003)
    for x in [-.115,.115]:
        box('Motor mounting foot',(x,.462,.123),(.086,.31,.044),p['blue'],.007)
        for y in [.36,.56]:fastener('Motor foot fastening',(x,y,.152),p['steel'],r=.009)
    box('Motor terminal box',(0,.460,.424),(.17,.18,.093),p['blue'],.011)
    box('Motor terminal box lid',(0,.460,.475),(.181,.191,.018),p['dark'],.005)
    for x in [-.069,.069]:
        for y in [.389,.531]:fastener('Terminal box lid screw',(x,y,.487),p['steel'],r=.0045)
    # Bracketed control enclosure has inactive buttons, not labels or a working system.
    box('Control enclosure support upright',(.346,.275,.347),(.048,.055,.49),p['dark'],.005)
    box('Control enclosure mounting foot',(.346,.275,.123),(.16,.16,.030),p['dark'],.006)
    for y in [.225,.325]:fastener('Control support anchor',(.346,y,.146),p['steel'],r=.008)
    box('Control enclosure',(.346,.252,.651),(.215,.162,.302),p['blue'],.018)
    box('Control enclosure door gasket',(.346,.163,.651),(.192,.016,.274),p['rubber'],.010)
    box('Control enclosure front door',(.346,.151,.651),(.183,.014,.264),p['dark'],.008)
    box('Inactive blank indicator',(.346,.140,.719),(.116,.008,.043),p['face'],.004)
    for x,ma in [(.303,p['green']),(.391,p['red'])]:
        cyl('Control button bezel',(x,.137,.629),.025,.012,p['steel'],'Y',n=32,bevel=.002)
        cyl('Inactive push button',(x,.124,.629),.019,.020,ma,'Y',n=32,bevel=.004)
    cyl('Control door latch',(.413,.135,.564),.009,.014,p['steel'],'Y',n=20,bevel=.002)
    for z0 in [.557,.745]:box('Control door hinge',(.251,.159,z0),(.021,.031,.037),p['steel'],.004)
    for y in [.237,.287]:cyl('Control enclosure sealed gland',(.346,y,.489),.012,.032,p['rubber'],n=24,bevel=.003)
    # Fixed closed cable jacket connects enclosure to terminal box.
    tube('Fixed enclosed motor control cable',[(.346,.287,.486),(.346,.330,.401),(.260,.403,.367),(.155,.432,.375),(.089,.461,.423)],.011,p['rubber'],2)
    return ('city-mooring-capstan','縦ドラム式係船キャプスタン','Mooring capstan','運河の船着場やマリーナの設備として配置する縦ドラム式キャプスタンの外観一式。上下フランジとくびれを持つ連続した金属ドラム、上蓋、減速機外装、後方のフィン付きモーターと端子箱、配線外形、支持柱付き無表示操作箱、実取付穴のある共通ベースと固定金具を備えます。索や船は含まず、ドラム回転・巻取り・電装・制御は動作しません。係留能力、荷重、巻込み防止、耐食性や安全性を検証していない静的外観モデルです。','A vertical-drum capstan appearance assembly for canal landing stages and marina equipment areas. It has a continuous metal drum with upper/lower flanges and a concave waist, upper cover, reduction-gear housing, rear finned motor and terminal box, cable exterior, bracketed inactive control enclosure, and a shared base with genuine anchor apertures and mounting hardware. No line or vessel is included. Drum rotation, hauling, electrics and controls are nonfunctional. Mooring capacity, loading, entanglement protection, corrosion resistance and safety are unvalidated; this is static appearance geometry.',['waterfront','capstan','mooring','係船機'])


BUILDERS=[floating_dock,gangway,cleat,capstan]
IDS=['city-floating-dock-section','city-hinged-dock-gangway','city-dock-mooring-cleat','city-mooring-capstan']
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-031/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.geometry_only:common.render=lambda *args,**kwargs:None
    out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    for fn,slug in zip(BUILDERS,IDS):
        if args.only and args.only!=slug:continue
        reset();spec=fn();publish_asset(*spec,out,'scripts/city_expansion/waterfront_dock_equipment.py',azimuth=125 if slug=='city-hinged-dock-gangway' else -55,elevation=24)
