"""Four original outdoor recreation props, CC BY 4.0, Xenoah.
No third-party geometry, images, fonts, brands or animal character designs.
All are static scene props, not structural or playground safety designs.
Usage: CITY_RENDER_SAMPLES=48 blender -b --factory-startup --threads 4 \
  --python scripts/city_expansion/recreation.py -- --out batches/batch-002/assets [--only ID]
"""
import sys, math, argparse
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(
        steel=mat('Satin stainless hardware', (.46,.51,.53), .78,.32),
        zinc=mat('Galvanized mounting steel', (.31,.37,.39), .72,.48),
        dark=mat('Charcoal rubber and recesses', (.018,.025,.030), 0,.74),
        navy=mat('Deep blue outdoor powder coat', (.032,.105,.15), .25,.42),
        blue=mat('Blue matte playing surface', (.035,.24,.36), .05,.72),
        white=mat('Warm white markings and board', (.84,.87,.83), .02,.48),
        rope=mat('Cream woven nylon net', (.72,.76,.70), 0,.82),
        orange=mat('Warm orange coated metal', (.80,.205,.038), .14,.45),
        yellow=mat('Golden yellow playground polymer', (.92,.57,.065), 0,.56),
        teal=mat('Teal molded playground polymer', (.025,.38,.37), 0,.56),
        concrete=mat('Warm precast mineral support', (.43,.45,.40), 0,.88))


def cyl(n,p,r,d,m,axis='Z',verts=32,bev=.002):
    o=cylinder(n,p,r,d,m,vertices=verts,bevel=bev)
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    if axis=='X': o.rotation_euler[1]=math.pi/2
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return o


def rod(n,a,b,r,m,verts=16,bev=.0006):
    a,b=Vector(a),Vector(b)
    o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=min(bev,r*.15))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def bar(n,a,b,w,d,m,bev=.004):
    a,b=Vector(a),Vector(b)
    o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def screw(n,p,m,axis='Z',r=.009):
    cyl(n+' washer',p,r*1.65,r*.28,m,axis,20,.0004)
    q=list(p);q['XYZ'.index(axis)]+=r*.47
    cyl(n+' hex head',q,r,r*.8,m,axis,6,.0005)


def sweep(n,points,r,m,sides=8):
    """Closed round-section tube, flat caps and outward smooth side normals."""
    pp=[Vector(p) for p in points];vs=[];fs=[];previous_tangent=None;u=None
    for i,p in enumerate(pp):
        tangent=(pp[min(i+1,len(pp)-1)]-pp[max(0,i-1)]).normalized()
        if previous_tangent is None:
            helper=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
            u=tangent.cross(helper).normalized()
        else:
            u=previous_tangent.rotation_difference(tangent)@u
            u=(u-tangent*u.dot(tangent)).normalized()
        v=tangent.cross(u).normalized();previous_tangent=tangent
        for j in range(sides):
            vv=p+r*(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides));vs.append(tuple(vv))
    for i in range(len(pp)-1):
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    fs.extend([tuple(reversed(range(sides))),tuple(range((len(pp)-1)*sides,len(pp)*sides))])
    o=mesh(n,vs,fs,m,0,True)
    for f in o.data.polygons:
        if len(f.vertices)!=4:f.use_smooth=False
    return o


def profile(n,outline,width,m,bevel=.01):
    # XZ silhouette extruded across Y. Concave cap tessellation happens at export.
    vs=[(x,y,z) for y in [-width/2,width/2] for x,z in outline];nn=len(outline)
    fs=[tuple(range(nn-1,-1,-1)),tuple(range(nn,nn*2))]
    fs.extend((i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn))
    return mesh(n,vs,fs,m,bevel)


def outdoor_table_tennis():
    p=palette()
    # Regulation-sized nominal 2.74 m x 1.525 m play slab, 0.76 m top height.
    for x in [-.687,.687]:
        box('Durable split playing slab',(x,0,.7375),(1.368,1.525,.045),p['blue'],.009)
    for y in [-.7525,.7525]:box('Long perimeter paint stripe',(0,y,.7607),(2.70,.020,.0015),p['white'],.0003)
    for x in [-1.3575,1.3575]:box('End perimeter paint stripe',(x,0,.7607),(.020,1.50,.0015),p['white'],.0003)
    box('Doubles center paint stripe',(0,0,.7607),(2.70,.006,.0015),p['white'],.0002)
    for y in [-.672,.672]:box('Recessed galvanized long apron',(0,y,.686),(2.57,.045,.065),p['navy'],.006)
    for x in [-1.267,1.267]:box('Galvanized end apron',(x,0,.686),(.045,1.37,.065),p['navy'],.006)
    for x in [-.87,.87]:
        box('Precast stable foot',(x,0,.045),(.48,1.04,.09),p['concrete'],.030)
        # Symmetric taper gives a proper pedestal, not a thin free-floating support.
        outline=[(x-.155,.084),(x+.155,.084),(x+.115,.637),(x-.115,.637)]
        profile('Tapered mineral pier',outline,.36,p['concrete'],.018)
        box('Pier head load spreader',(x,0,.641),(.37,1.26,.075),p['concrete'],.018)
        box('Under-top transverse steel bearer',(x,0,.697),(.105,1.38,.044),p['zinc'],.005)
        for y in [-.47,.47]:
            box('Base anchor shoe',(x,y,.101),(.16,.10,.018),p['zinc'],.004)
            for xx in [x-.052,x+.052]:screw('Foot anchoring bolt',(xx,y,.114),p['steel'],r=.008)
        for y in [-.49,.49]:
            bar('Under-top diagonal brace',(x,0,.38),(x,y,.680),.035,.035,p['navy'],.003)
            screw('Transverse bearer bolt',(x,y,.720),p['steel'],r=.007)
    box('Under-table longitudinal tie',(0,0,.365),(1.84,.085,.085),p['navy'],.008)
    # Fixed metal wire net, 152.5 mm above play surface, tensioned in a steel frame.
    for y in [-.87,.87]:
        cyl('Fixed net upright',(0,y,.840),.014,.190,p['steel'],verts=24,bev=.0015)
        box('Net clamp saddle',(0,y,.738),(.12,.084,.042),p['zinc'],.006)
        bar('Net clamp return',(0,math.copysign(.715,y),.707),(0,y,.707),.032,.032,p['zinc'],.003)
        screw('Net clamp screw',(0,y,.763),p['steel'],r=.007)
        cyl('Net post end cap',(0,y,.939),.016,.010,p['navy'],verts=24,bev=.002)
    for z in [.770,.913]:rod('Net horizontal frame',(0,-.87,z),(0,.87,z),.006,p['steel'],12)
    # All grid strands are closed-volume rods. No alpha image masquerading as mesh.
    for i in range(86):
        y=-.85+i*1.70/85
        rod('Net vertical wire %02d'%i,(0,y,.771),(0,y,.912),.0016,p['steel'],8,0)
    for j in range(1,7):
        z=.771+j*.020
        rod('Net horizontal wire %02d'%j,(0,-.855,z),(0,.855,z),.0016,p['steel'],8,0)
    return ('city-outdoor-table-tennis','固定ネット付き屋外卓球台','Outdoor table tennis table with fixed net',
        '公園や屋外広場向けの単体卓球台。公称2.74×1.525 m・天板高さ0.76 mの青い天板、白線、固定式金属ワイヤーネット、テーパー付き鉱物系支柱、横梁・斜材・接地固定金具を造形。ラケット、球、競技場や利用者は含みません。静的装飾モデルで、競技規格認定や屋外構造安全性の検証は行っていません。',
        'One outdoor table tennis table for parks and plazas: a nominal 2.74 × 1.525 m blue top at 0.76 m, painted boundaries and doubles line, fixed metal-wire net, tapered mineral piers, cross bearers, braces and anchor hardware. No bats, ball, court or people. Static decorative geometry, without sporting-standard certification or outdoor structural-safety validation.',
        ['recreation','table-tennis','park','sport','卓球'])


def basketball_goal():
    p=palette()
    # Single fixed ground-anchored freestanding goal. Board front points toward -Y.
    box('Ground anchor base plate',(0,1.03,.025),(.64,.58,.05),p['zinc'],.015)
    for x in [-.245,.245]:
        for y in [.825,1.235]:
            screw('Ground anchor nut',(x,y,.055),p['steel'],r=.019)
            cyl('Anchor thread end',(x,y,.078),.010,.014,p['steel'],verts=16,bev=.001)
    box('Square steel support post',(0,1.03,1.52),(.18,.18,2.97),p['navy'],.014)
    box('Post weather cap',(0,1.03,3.01),(.199,.199,.028),p['navy'],.009)
    # Visible real joints, gussets and an inclined reach arm, not a floating backboard.
    bar('Upper cantilever reach arm',(0,1.03,2.95),(0,.12,3.50),.16,.16,p['navy'],.010)
    bar('Lower diagonal brace',(0,1.03,2.43),(0,.12,3.38),.09,.09,p['navy'],.006)
    for x in [-.095,.095]:
        o=profile('Post foot triangular gusset',[(-.23,.048),(.23,.048),(0,.43)],.016,p['navy'],.003)
        o.rotation_euler[2]=math.pi/2;o.location.x=x;o.location.y=1.03
    box('Rear board central mounting rail',(0,.105,3.46),(.15,.10,.76),p['zinc'],.007)
    for z in [3.10,3.78]:
        box('Rear board horizontal frame',(0,.074,z),(1.65,.064,.055),p['zinc'],.005)
        for x in [-.70,.70]:screw('Rear board fixing bolt',(x,.118,z),p['steel'],'Y',.010)
    for x in [-.785,.785]:box('Rear board upright frame',(x,.074,3.44),(.055,.064,.74),p['zinc'],.005)
    for x in [-.70,.70]:bar('Rear wing stiffener',(0,.12,3.48),(x,.10,3.10),.040,.035,p['zinc'],.003)
    box('Opaque rectangular backboard',(0,0,3.475),(1.80,.055,1.05),p['white'],.018)
    for x in [-.882,.882]:box('Backboard side edge trim',(x,-.033,3.475),(.034,.018,1.038),p['navy'],.006)
    box('Backboard top edge trim',(0,-.033,3.983),(1.78,.018,.034),p['navy'],.006)
    box('Lower backboard protective pad',(0,-.014,2.964),(1.81,.105,.095),p['navy'],.023)
    # Conventional target square is original simple geometry, not a logo.
    for x in [-.295,.295]:box('Target square vertical paint',(x,-.0306,3.2825),(.025,.002,.455),p['orange'],.0003)
    for z in [3.0675,3.4975]:box('Target square horizontal paint',(0,-.0306,z),(.615,.002,.025),p['orange'],.0003)
    box('Rim mounting face plate',(0,-.059,3.08),(.20,.045,.22),p['orange'],.008)
    for x in [-.071,.071]:
        for z in [3.014,3.147]:screw('Rim mounting bolt',(x,-.085,z),p['steel'],'Y',.008)
    box('Rim connection neck',(0,-.137,3.035),(.14,.145,.052),p['orange'],.006)
    for x in [-.063,.063]:
        # A sloped rod and side cheek both join the underside of the projecting ring.
        rod('Rim underside gusset',(x,-.086,2.989),(x,-.277,3.031),.015,p['orange'],16)
    torus('Basketball hoop ring',(0,-.397,3.05),.225,.018,p['orange'],segments=64)
    # Twelve paired zigzag nylon cords create a visibly open tapered diamond net.
    levels=[(3.028,.213),(2.916,.202),(2.808,.183),(2.701,.163),(2.615,.145)]
    for i in range(12):
        for direction in [-1,1]:
            points=[]
            for j,(z,r) in enumerate(levels):
                a=math.tau*i/12+direction*(j%2)*math.pi/12
                points.append((r*math.cos(a),-.397+r*math.sin(a),z))
            sweep('Diamond nylon net cord %02d %s'%(i,direction),points,.0032,p['rope'],8)
        a=math.tau*i/12
        torus('Rim net attachment loop',(math.cos(a)*.216,-.397+math.sin(a)*.216,3.029),.009,.0025,p['orange'],rotation=(math.pi/2,0,a),segments=12)
    torus('Net open lower hem',(0,-.397,2.615),.145,.0035,p['rope'],segments=48)
    for z in [.14,.28]:
        for x in [-.073,.073]:screw('Post base connection bolt',(x,.931,z),p['steel'],'Y',.009)
    return ('city-basketball-goal','独立支柱式バスケットボールゴール','Freestanding basketball goal',
        '屋外コートの片側に置く単体バスケットボールゴール。公称リング高さ3.05 m、1.80×1.05 mの不透明バックボード、開口したリングとダイヤ状ネット、背面フレーム、斜め支持腕、支柱・補強板・アンカーを備えます。ボール、コートや相手側ゴールは含みません。静的装飾用で、競技規格認定、荷重計算、転倒防止・遊具安全性の検証は行っていません。',
        'One freestanding ground-anchored goal for an outdoor basketball court, with a nominal 3.05 m ring height, 1.80 × 1.05 m opaque backboard, open hoop and diamond net, rear frame, cantilever arms, post, gussets and anchors. No ball, court or opposite goal. Static decorative geometry with no sporting-standard certification, load calculations, tip-over or playground-safety validation.',
        ['recreation','basketball','goal','sport','バスケットボール'])


def playground_seesaw():
    p=palette();pivot=Vector((0,0,.63))
    # Fixed foundation assembly first. Two separated A-frames support the pivot.
    for y in [-.20,.20]:
        box('Foundation shoe',(0,y,.021),(.65,.12,.042),p['zinc'],.010)
        for x in [-.255,.255]:screw('Seesaw foundation anchor',(x,y,.046),p['steel'],r=.013)
        for x in [-.24,.24]:bar('A-frame pivot support',(x,y,.060),(0,y,.63),.085,.075,p['navy'],.008)
        cyl('Pivot bearing housing',(0,y,.63),.102,.085,p['navy'],'Y',40,.005)
        cyl('Covered pivot bearing',(0,y+math.copysign(.052,y),.63),.073,.022,p['orange'],'Y',40,.006)
        cyl('Axle hex nut',(0,y+math.copysign(.069,y),.63),.025,.018,p['steel'],'Y',6,.001)
    cyl('Pivot axle',(0,0,.63),.035,.54,p['steel'],'Y',32,.002)
    # Paired ground stops are shaped elastomer bumps on low connected mounts.
    for x in [-1.17,1.17]:
        box('Stop ground mounting plate',(x,0,.012),(.28,.34,.024),p['zinc'],.015)
        cyl('Rubber travel stop',(x,0,.115),.102,.195,p['dark'],verts=40,bev=.020)
        sphere('Rounded travel stop head',(x,0,.202),(.102,.102,.045),p['dark'],24,12)
        for y in [-.133,.133]:screw('Stop plate bolt',(x,y,.029),p['steel'],r=.008)
    before=set(bpy.context.scene.objects)
    box('Single balanced rocker beam',(0,0,.665),(2.78,.15,.145),p['teal'],.016)
    for y in [-.083,.083]:
        box('Center pivot reinforcement cheek',(0,y,.665),(.44,.016,.19),p['zinc'],.012)
        for x in [-.165,.165]:screw('Beam cheek bolt',(x,y+math.copysign(.014,y),.665),p['steel'],'Y',.011)
    for sign in [-1,1]:
        x=sign*1.16
        box('Contoured end saddle seat',(x,0,.766),(.44,.37,.065),p['orange'],.027)
        box('Seat mounting subplate',(x,0,.724),(.32,.25,.025),p['zinc'],.008)
        for xx in [x-.13,x+.13]:
            for y in [-.12,.12]:screw('Seat recessed attachment',(xx,y,.800),p['steel'],r=.006)
        hx=sign*.88
        # A continuous rounded U handle is affixed to two through-beam feet.
        pts=[(hx,-.135,.73),(hx,-.135,.915)]
        for j in range(1,13):
            a=math.pi-j*math.pi/12;pts.append((hx,.135*math.cos(a),.915+.135*math.sin(a)))
        pts.append((hx,.135,.73))
        sweep('Continuous grab handle',pts,.017,p['navy'],12)
        rod('Handle horizontal rubber grip',(hx,-.070,1.043),(hx,.070,1.043),.022,p['dark'],20)
        for y in [-.135,.135]:
            box('Handle foot bracket',(hx,y,.727),(.080,.063,.034),p['zinc'],.005)
            screw('Handle foot fixing',(hx+sign*.021,y,.747),p['steel'],r=.007)
        rod('Footrest throughbar',(sign*.73,-.29,.535),(sign*.73,.29,.535),.019,p['zinc'],24)
        for y in [-.235,.235]:
            cyl('Nonslip footrest grip',(sign*.73,y,.535),.029,.118,p['dark'],'Y',24,.004)
            bar('Footrest joining strap',(sign*.73,y/2,.535),(sign*.73,y/2,.651),.038,.035,p['teal'],.004)
        box('Beam rounded end cap',(sign*1.393,0,.665),(.017,.154,.146),p['navy'],.009)
    # Model has a small static rest angle. No rig or hinge-centered node is promised.
    transform=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(5),4,'Y')@Matrix.Translation(-pivot)
    for o in set(bpy.context.scene.objects)-before:o.matrix_world=transform@o.matrix_world
    return ('city-playground-seesaw','2席の公園シーソー','Two-seat playground seesaw',
        '小公園向けの2席シーソーをわずかに傾けた静止姿勢で造形。座席、手すり、足掛け、1本梁、両側A型支柱、覆い付き軸受、地面側のゴムストッパーと固定金具を備えます。子供、地面や落下保護舗装は含みません。装飾用の静的メッシュで、動作・荷重・挟み込み・遊具安全規格は未検証です。',
        'A two-seat playground seesaw shown at a slight static rest angle, with seats, grab handles, footrests, one rocker beam, paired A-frame supports, covered pivot bearings, ground bump stops and anchor hardware. No children, ground surface or impact-absorbing surfacing. Decorative static meshes only; motion, loading, entrapment and playground safety standards are not validated.',
        ['recreation','playground','seesaw','park','シーソー'])


def spring_play_rider():
    p=palette()
    box('Foundation anchor plate',(0,0,.018),(.42,.40,.036),p['zinc'],.018)
    for x in [-.158,.158]:
        for y in [-.148,.148]:screw('Spring rider ground anchor',(x,y,.043),p['steel'],r=.012)
    cyl('Spring bottom load spreader',(0,0,.071),.145,.045,p['navy'],verts=48,bev=.009)
    # Closed end turns sit in the flange. Central turns rise uniformly.
    turns=5.5;steps=220;points=[]
    for i in range(steps+1):
        t=i/steps;rise=max(0,min(1,(t-.09)/.82));a=math.tau*turns*t
        points.append((.105*math.cos(a),.105*math.sin(a),.098+.359*rise))
    sweep('Original helical support spring',points,.018,p['navy'],10)
    cyl('Spring top load spreader',(0,0,.485),.145,.043,p['navy'],verts=48,bev=.008)
    box('Upper saddle mounting plate',(0,0,.515),(.32,.21,.025),p['zinc'],.008)
    for x in [-.116,.116]:
        for y in [-.075,.075]:screw('Upper mount fastener',(x,y,.533),p['steel'],r=.008)
    # A unique abstract smooth swoosh and open oval hand loop. No animal features.
    outline=[(-.43,.58),(-.46,.615),(-.44,.658),(-.37,.696),(-.23,.703),(-.06,.674),(.12,.648),(.31,.686),(.40,.668),(.43,.626),(.40,.579),(.24,.542),(.06,.531),(-.18,.543)]
    profile('Abstract swoosh main body',outline,.15,p['teal'],.012)
    box('Single rounded saddle seat',(-.22,0,.723),(.36,.35,.068),p['yellow'],.028)
    box('Saddle underside mounting pad',(-.22,0,.682),(.24,.23,.028),p['navy'],.010)
    for y in [-.083,.083]:
        for x in [-.32,-.12]:screw('Seat underside fastener',(x,y,.674),p['steel'],r=.006)
    # Ring lies in the XZ plane and intersects the structural body at its lower arc.
    loop=torus('Abstract open oval upper loop',(.21,0,.845),.205,.047,p['yellow'],rotation=(math.pi/2,0,0),segments=64)
    loop.scale=(.82,1.15,1)
    bpy.context.view_layer.objects.active=loop;loop.select_set(True)
    # Local torus Y becomes world Z after rotation: elliptical rise, uniform thickness depth.
    rod('Handle throughbar',(.21,-.265,1.037),(.21,.265,1.037),.017,p['steel'],24)
    for y in [-.205,.205]:
        cyl('Rounded hand grip',(.21,y,1.037),.027,.126,p['dark'],'Y',32,.007)
        cyl('Hand grip end flange',(.21,math.copysign(.272,y),1.037),.032,.015,p['dark'],'Y',32,.004)
    # Main body and footrest actually overlap around a central load-bearing sleeve.
    rod('Footrest crossbar',(.15,-.29,.559),(.15,.29,.559),.019,p['steel'],24)
    for y in [-.225,.225]:
        cyl('Footrest rubber pad',(.15,y,.559),.032,.14,p['dark'],'Y',24,.006)
        for yy in [y-.035,y,y+.035]:cyl('Raised footrest tread ring',(.15,yy,.559),.035,.009,p['dark'],'Y',24,.001)
    for y in [-.082,.082]:
        cyl('Decorative structural side boss',(.02,y,.609),.038,.018,p['navy'],'Y',32,.004)
        screw('Main body fixing',(.02,y+math.copysign(.012,y),.609),p['steel'],'Y',.009)
    return ('city-spring-play-rider','抽象ループ型のスプリング遊具','Abstract loop spring play rider',
        '公園や遊び場に置く1人用スプリング遊具のオリジナル抽象デザイン。動物や既存キャラクターを模していない流線形本体、開いた楕円ループ、座席、両側グリップ・足掛け、コイルばね、上下フランジと接地固定板を造形。子供、地面や落下保護舗装は含みません。装飾用の静的モデルで、ばね挙動・耐荷重・挟み込み・遊具安全規格は未検証です。',
        'An original single-seat spring rider for park and playground scenes: an abstract swoosh body and open oval loop, not an animal or an existing character, with a saddle, paired grips and footrests, helical spring, mounting flanges and ground anchor plate. No child, ground or impact-absorbing surfacing. Decorative static geometry; spring behavior, load capacity, entrapment and playground safety standards are not validated.',
        ['recreation','playground','spring-rider','abstract','スプリング遊具'])


BUILDERS=[outdoor_table_tennis,basketball_goal,playground_seesaw,spring_play_rider]
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-002/assets');ap.add_argument('--only',default='');a=ap.parse_args(args)
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    mapping={'outdoor_table_tennis':'city-outdoor-table-tennis','basketball_goal':'city-basketball-goal','playground_seesaw':'city-playground-seesaw','spring_play_rider':'city-spring-play-rider'}
    for fn in BUILDERS:
        if a.only and mapping[fn.__name__]!=a.only:continue
        reset();spec=fn()
        # Bake common world coordinates before material grouping. This avoids
        # sub-micrometre split-vertex discrepancies from a rotated active object.
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH')
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        publish_asset(*spec,out,'scripts/city_expansion/recreation.py',azimuth=-55 if fn!=basketball_goal else -65,elevation=24 if fn!=basketball_goal else 14)
