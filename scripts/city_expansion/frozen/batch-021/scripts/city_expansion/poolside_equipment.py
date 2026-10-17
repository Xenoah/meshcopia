"""Four original generic poolside facility props, CC BY 4.0, Xenoah.
Closed static appearance geometry, not a product or competition/safety specification.
Portable Blender source. Shared common.py remains unmodified.
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
    return dict(
        steel=mat('Satin stainless steel',(.57,.64,.67),.80,.28),
        aluminum=mat('Soft anodized aluminum',(.48,.56,.60),.70,.37),
        dark=mat('Graphite mechanical fittings',(.054,.075,.085),.25,.46),
        rubber=mat('Charcoal rubber and traction strips',(.021,.033,.039),0,.80),
        blue=mat('Pool blue powder coat',(.025,.23,.36),.28,.39),
        white=mat('Warm white molded polymer',(.78,.80,.76),0,.46),
        red=mat('Warm coral molded polymer',(.65,.095,.055),0,.47),
        pale=mat('Pale blue walking surface',(.31,.57,.62),.05,.60),
    )


def cyl(name,pos,radius,depth,material,axis='Z',n=24,bevel=.0015):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name,a,b,radius,material,n=16):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,radius,(b-a).length,material,n=n,bevel=min(.001,radius*.10))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def beam(name,a,b,width,depth,material,bevel=.003):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def path(name,points,radius,material,closed=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1
    c.bevel_depth=radius;c.bevel_resolution=2;c.use_fill_caps=not closed
    s=c.splines.new('POLY');s.points.add(len(points)-1);s.use_cyclic_u=closed
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material)
    return o


def ring(name,pos,major,minor,material,axis='Z',n=64,m=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,major_radius=major,minor_radius=minor,location=pos)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,name,material,smooth=True)


def screw(name,pos,material,axis='Z',r=.008):
    return cyl(name,pos,r,.005,material,axis,n=8,bevel=.0005)


def yz_prism(name,profile,width,material,bevel=.003):
    """Closed extruded Y/Z silhouette with reliable outward cap normals."""
    vs=[(s*width/2,y,z) for s in [-1,1] for y,z in profile];n=len(profile)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def pool_ladder():
    p=palette()
    # The sockets sit at an authored deck datum 1.35 m above the lowest bumper.
    # Their height deliberately differs from the centered, grounded export origin.
    for side in [-1,1]:
        x=side*.304
        pts=[(x,.38,1.30),(x,.38,1.95)]
        pts += [(x,.06+.32*math.cos(i*math.pi/24),1.95+.32*math.sin(i*math.pi/24)) for i in range(1,25)]
        pts += [(x,-.26,.18),(x,-.248,.145),(x,-.218,.125),(x,-.11,.125)]
        path('Continuous curved deck grab rail and immersed leg',pts,.023,p['steel'])
        cyl('Deck socket gasket',(x,.38,1.337),.082,.012,p['rubber'],n=32)
        cyl('Deck socket mounting flange',(x,.38,1.349),.076,.018,p['steel'],n=40,bevel=.003)
        cyl('Socket collar around rail',(x,.38,1.394),.037,.082,p['steel'],n=32,bevel=.004)
        for d in [-1,1]:screw('Socket fixing screw',(x+d*.055,.38,1.362),p['dark'],r=.006)
        cyl('Pool wall standoff pad',(x,-.091,.125),.045,.035,p['rubber'],'Y',32,.004)
        for z in [.415,.735,1.055,1.375]:
            box('Tread end mounting shoe',(x,-.26,z-.021),(.056,.155,.052),p['steel'],.007)
            screw('Tread mounting end screw',(x+side*.030,-.26,z-.018),p['dark'],'X',r=.007)
    for i,z in enumerate([.415,.735,1.055,1.375]):
        box('Immersed ladder tread',(0,-.26,z),(.625,.168,.037),p['steel'],.009)
        box('Tread dark inset',(0,-.269,z+.022),(.515,.131,.010),p['rubber'],.003)
        for y in [-.315,-.286,-.257,-.228]:box('Tread raised transverse traction rib',(0,y,z+.029),(.478,.012,.006),p['dark'],.001)
    return ('city-pool-entry-ladder','プール縁用の曲線手すり付き入水はしご','Pool-entry ladder with curved deck grab rails',
        'プールの縁に取り付ける入水用はしごの静的プロップ。左右の連続した曲線手すり、深さ方向へ延びる四段の踏み板と滑り止め形状、デッキ固定ソケット、下部の壁当てパッドを造形しています。デッキ面は最下点から約1.27 m上に合わせて配置してください。水面・プール壁・床は付属せず、保守用ケージはしごとは別の構成です。昇降機能、耐荷重、滑り抵抗や安全認証を示すモデルではありません。',
        'A static pool-entry ladder for the edge of a swimming pool, with two continuous curved deck grab rails, four immersed-run treads with raised traction detail, deck sockets and lower wall-contact pads. Position the deck about 1.27 m above the lowest point of this grounded asset. Water, pool wall and deck are omitted; this is not a caged maintenance ladder. No climbing function, load rating, slip-resistance performance or safety certification is supplied.',
        ['pool','ladder','deck-equipment','プール'])


def start_block():
    p=palette()
    box('Broad mounting base',(0,.025,.036),(.60,.65,.072),p['steel'],.018)
    box('Mounting base isolation gasket',(0,.025,.011),(.574,.624,.022),p['rubber'],.008)
    for x in [-.238,.238]:
        for y in [-.235,.285]:screw('Base anchoring head',(x,y,.078),p['dark'],r=.012)
    # A closed tapered pedestal is visibly different from the top deck.
    yz_prism('Tapered starting platform pedestal',[(-.205,.072),(.245,.072),(.255,.615),(-.125,.595)],.35,p['blue'],.018)
    box('Pedestal rear inspection panel',(0,.256,.335),(.257,.018,.308),p['pale'],.012)
    for x in [-.105,.105]:
        for z in [.214,.457]:screw('Rear panel fixing',(x,.267,z),p['steel'],'Y',.006)
    # All upper details share the modest generic platform pitch, not a standard.
    pitch=.075;center=Vector((0,0,.655))
    def top_point(x,y,z):
        return center+Vector((x,y*math.cos(pitch)-z*math.sin(pitch),y*math.sin(pitch)+z*math.cos(pitch)))
    box('Raised platform lower shell',center,(.735,.845,.088),p['white'],.019,(pitch,0,0))
    box('Dark anti-slip top inset',top_point(0,0,.052),(.680,.783,.024),p['rubber'],.009,(pitch,0,0))
    for y in [-.34,-.28,-.22,-.16,-.10,-.04,.02,.08,.14,.20,.26,.32]:
        box('Top surface transverse traction bead',top_point(0,y,.067),(.622,.009,.005),p['dark'],.001,(pitch,0,0))
    # Distinct rear foot wedge and mounting tracks remain static.
    for x in [-.246,.246]:
        box('Rear wedge sliding rail',(x,.245,.746),(.035,.36,.025),p['steel'],.006,(pitch,0,0))
        for y in [.145,.245,.345]:screw('Wedge track locating head',(x,y,.755+y*.07),p['dark'],r=.005)
    yz_prism('Rear raised foot wedge',[(.135,.752),(.37,.770),(.37,.985),(.135,.785)],.465,p['blue'],.009)
    wedge_pitch=math.atan2(.20,.235)
    box('Rear wedge grip face',(0,.25,.889),(.437,.315,.018),p['rubber'],.006,(wedge_pitch,0,0))
    for yy in [-.105,-.035,.035,.105]:
        ridge_center=(0,.25+yy*math.cos(wedge_pitch)-.014*math.sin(wedge_pitch),.889+yy*math.sin(wedge_pitch)+.014*math.cos(wedge_pitch))
        box('Rear wedge transverse grip ridge',ridge_center,(.395,.010,.008),p['dark'],.002,(wedge_pitch,0,0))
    for side in [-1,1]:
        # Front/backstroke-type grab fitting is a static visual cue only.
        x=side*.245
        path('Under-platform front grab bracket',[(x,-.285,.612),(x,-.408,.564),(x,-.470,.485),(x,-.470,.445)],.016,p['steel'])
        cyl('Side grab fitting collar',(side*.186,-.285,.604),.033,.035,p['steel'],'X',24,.003)
    rod('Continuous front hand-grab bar',(-.262,-.470,.445),(.262,-.470,.445),.018,p['steel'],24)
    return ('city-swimming-start-block','後部フットウェッジ付きのプール用スタート台','Swimming start block with rear foot wedge',
        'プールのスタート側デッキに置く汎用スタート台。台座と傾斜支持部、縁を丸めた高床プラットフォーム、滑り止め形状、固定した後部フットウェッジとレール、前方グラブバー、背面の点検パネルを造形しています。デッキ・水面・競技レーン番号は付属しません。動作しない外観用モデルであり、公式寸法、競技規則への適合、荷重性能や安全認証は主張しません。',
        'A generic swimming start-block prop for a pool starting-end deck, with a mounting base and tapered support, raised bevel-edged platform, traction detail, fixed rear foot wedge and rails, front grab bar and rear inspection panel. Deck, water and lane numbers are omitted. This is static appearance geometry, with no official-dimension, competition-rule compliance, load-performance or safety-certification claim.',
        ['pool','starting-platform','sport-facility','プール'])


def lifeguard_chair():
    p=palette()
    # Four splayed tower legs support a separate foot platform and elevated seat.
    for sx in [-1,1]:
        for sy in [-1,1]:
            bottom=(sx*.505,sy*.425,.045);top=(sx*.394,sy*.322,1.27)
            box('Wide nonmarking tower foot',(bottom[0],bottom[1],.024),(.135,.15,.048),p['rubber'],.012)
            beam('Splayed observation tower leg',bottom,top,.054,.054,p['aluminum'],.006)
            screw('Visible tower assembly fixing',(sx*.426,sy*.325,1.194),p['dark'],'X',.010)
        beam('Lower side diagonal brace',(sx*.49,-.413,.175),(sx*.399,.325,1.16),.025,.031,p['steel'],.003)
        beam('Side platform bearer',(sx*.41,-.46,1.25),(sx*.41,.48,1.25),.065,.063,p['aluminum'],.005)
    beam('Rear lower cross brace',(-.47,.393,.30),(.47,.393,.30),.039,.039,p['aluminum'],.004)
    beam('Front upper cross brace',(-.41,-.332,1.15),(.41,-.332,1.15),.042,.042,p['aluminum'],.004)
    for i in range(7):
        box('Separated platform walking plank',(0,-.397+i*.132,1.297),(.91,.119,.047),p['pale'],.006)
        for x in [-.361,.361]:screw('Platform plank screw',(x,-.397+i*.132,1.323),p['dark'],r=.005)
    # Rear access stairs integrate with the tower; they are not a loose ladder.
    for side in [-1,1]:
        beam('Inclined stair stringer',(side*.34,1.50,.075),(side*.34,.44,1.26),.055,.068,p['aluminum'],.006)
        box('Stair base pad',(side*.34,1.49,.036),(.12,.17,.06),p['rubber'],.010)
        pts=[(side*.385,1.47,.58),(side*.385,1.44,.74),(side*.385,.59,1.76),(side*.385,.47,1.86),(side*.385,-.28,1.86),(side*.385,-.39,1.78),(side*.385,-.39,1.31)]
        path('Continuous stair and platform handrail',pts,.020,p['steel'])
        rod('Mid stair handrail supporting upright',(side*.385,1.075,.52),(side*.385,1.075,1.18),.017,p['steel'])
        rod('Upper stair rail mounting post',(side*.385,.50,1.29),(side*.385,.50,1.835),.017,p['steel'])
    for y,z in [(1.35,.27),(1.10,.55),(.85,.83),(.60,1.11)]:
        box('Access stair tread',(0,y,z),(.738,.245,.043),p['aluminum'],.008)
        box('Access stair traction inset',(0,y-.020,z+.025),(.645,.18,.012),p['rubber'],.003)
        for yy in [-.073,-.025,.023]:box('Access tread shallow raised strip',(0,y+yy,z+.033),(.60,.010,.005),p['dark'],.001)
    # Seat pedestal, individual seat slats, back slats and attached armrests.
    for x in [-.255,.255]:
        beam('Elevated seat support',(x,-.055,1.32),(x,-.055,1.72),.044,.052,p['aluminum'],.005)
        beam('Seat underside side bearer',(x,-.325,1.71),(x,.23,1.71),.045,.045,p['aluminum'],.004)
        beam('Backrest upright',(x,.22,1.71),(x,.30,2.17),.038,.038,p['aluminum'],.004)
        path('Seat armrest support',[(x,-.24,1.735),(x,-.24,1.96),(x,.21,1.96),(x,.25,1.76)],.014,p['steel'])
        box('Armrest cap',(x,-.023,1.98),(.064,.43,.035),p['white'],.010)
    for i in range(5):box('Separate observation seat slat',(0,-.262+i*.104,1.753),(.56,.093,.047),p['red'],.013)
    for z in [1.90,2.015,2.13]:
        y=.22+(z-1.71)*(.08/.46)
        box('Observation backrest horizontal slat',(0,y,z),(.58,.044,.095),p['red'],.014,(-.172,0,0))
    return ('city-lifeguard-observation-chair','階段と足場付きのプール監視用高座椅子','Elevated pool observation chair with access steps',
        'プールサイドの監視位置に置く高座椅子と架台の一体型プロップ。開放された四脚架台、補強材、足元プラットフォーム、背面アクセス階段と連続手すり、高いスラット座面・背もたれ・肘掛けを造形しています。人、傘、救命浮環や救助道具は含みません。固定状態の外観用モデルで、監視・救助機能、荷重定格、避難・安全基準への適合を保証しません。',
        'A complete elevated observation-chair prop for a poolside viewing position, combining an open four-legged tower, braces, foot platform, rear access stairs and continuous handrails with a raised slatted seat, backrest and armrests. People, umbrella, lifebuoy and rescue tools are omitted. All parts are static appearance geometry; no observation/rescue function, load rating or access/safety-standard compliance is guaranteed.',
        ['pool','observation-chair','elevated-seat','プール監視'])


def annular_float(name,pos,direction,material):
    # Six profile rings yield a truly bored, closed float. The rope can be seen
    # through the central bore and in the intentional gaps between float pieces.
    profile=[(-.034,.012),(-.034,.028),(-.024,.044),(.024,.044),(.034,.028),(.034,.012)]
    n=12;vs=[]
    for zz,r in profile:
        for j in range(n):
            a=j*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),zz))
    fs=[]
    for k in range(len(profile)):
        kk=(k+1)%len(profile)
        for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,kk*n+(j+1)%n,kk*n+j))
    o=mesh(name,vs,fs,material,smooth=True);o.location=pos;o.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler()
    # The end bevels and bore use smooth normals; geometry is intentionally modest.
    return o


def caster(x,y,p):
    cyl('Mobile reel caster tire',(x,y,.080),.080,.047,p['rubber'],'X',32,.004)
    for s in [-1,1]:
        cyl('Caster wheel hub',(x+s*.025,y,.080),.034,.008,p['steel'],'X',20,.001)
        box('Caster fork cheek',(x+s*.035,y,.130),(.015,.061,.095),p['aluminum'],.003)
    box('Caster fork bridge',(x,y,.173),(.094,.065,.020),p['aluminum'],.003)
    cyl('Caster swivel crown',(x,y,.196),.036,.026,p['steel'],n=24,bevel=.002)


def lane_reel():
    p=palette();height=.772
    for side in [-1,1]:
        x=side*.555
        for y in [-.33,.33]:caster(x,y,p)
        beam('Mobile reel side base member',(x,-.37,.225),(x,.37,.225),.048,.053,p['blue'],.006)
        for y in [-.31,.31]:beam('Inclined reel bearing support',(x,y,.24),(x,0,height),.044,.044,p['blue'],.005)
        box('Axle bearing housing',(x,0,height),(.092,.118,.124),p['dark'],.014)
        cyl('Axle bearing visible collar',(x+side*.053,0,height),.044,.022,p['steel'],'X',32,.002)
    for y in [-.33,.33]:beam('Lower cart cross member',(-.555,y,.23),(.555,y,.23),.043,.047,p['blue'],.005)
    rod('Reel axle',(-.647,0,height),(.681,0,height),.026,p['steel'],32)
    cyl('Rope winding drum core',(0,0,height),.253,.900,p['white'],'X',48,.008)
    for side in [-1,1]:
        x=side*.467
        # Open spoked flanges reveal the wound floats from either side.
        ring('Drum flange outer retaining hoop',(x,0,height),.396,.021,p['steel'],'X',64,8)
        cyl('Drum flange center hub',(x,0,height),.073,.052,p['blue'],'X',32,.004)
        for i in range(8):
            a=i*math.tau/8
            beam('Drum flange radial spoke',(x,.070*math.cos(a),height+.070*math.sin(a)),(x,.392*math.cos(a),height+.392*math.sin(a)),.028,.025,p['steel'],.003)
        cyl('Drum outer axle fastener',(x+side*.032,0,height),.038,.014,p['dark'],'X',8,.001)
    # One continuous helix, with separately bored float segments threaded on it.
    turns=3.75;start=-.395;extent=.790;r=.296;n=82
    def point(t):
        a=t*turns*math.tau+.25
        return Vector((start+extent*t,r*math.cos(a),height+r*math.sin(a)))
    pts=[point(i/300) for i in range(301)]
    path('Continuous lane rope through wound float bores',pts,.007,p['dark'])
    for i in range(n):
        t=(i+.5)/n;a=t*turns*math.tau+.25
        tangent=Vector((extent,-r*turns*math.tau*math.sin(a),r*turns*math.tau*math.cos(a)))
        material=p['red'] if i<8 or i>=74 else (p['white'] if (i//7)%2 else p['blue'])
        annular_float('Threaded lane-rope float segment',point(t),tangent,material)
    # Crank, stationary push handle and small rope terminal detail complete cart.
    rod('External hand crank arm',(.689,0,height),(.689,-.157,height-.14),.017,p['steel'],20)
    rod('Hand crank grip spindle',(.684,-.157,height-.14),(.799,-.157,height-.14),.011,p['steel'],20)
    cyl('Hand crank rotating grip',(.766,-.157,height-.14),.024,.108,p['rubber'],'X',28,.003)
    handle=[(-.555,.32,.24),(-.555,.42,1.145),(-.526,.42,1.195),(.526,.42,1.195),(.555,.42,1.145),(.555,.32,.24)]
    path('Cart push handle and rear uprights',handle,.023,p['blue'])
    rod('Cart push handle rubber sleeve',(-.34,.42,1.195),(.34,.42,1.195),.029,p['rubber'],32)
    for side in [-1,1]:
        box('Push handle foot bracket',(side*.555,.322,.267),(.073,.067,.063),p['steel'],.005)
        screw('Handle bracket fixing',(side*.595,.322,.270),p['dark'],'X',.008)
    end=point(1);tail=[end,end+Vector((.016,.025,.015)),end+Vector((.025,.055,-.025))]
    path('Short rope terminal beyond last float',tail,.007,p['dark'])
    ring('Lane rope terminal eye',tail[-1]+Vector((.016,0,-.01)),.020,.006,p['steel'],'Y',24,6)
    return ('city-pool-lane-rope-reel','浮子付きレーンロープを巻いた移動式リール','Mobile pool lane-rope reel with threaded floats',
        'プールのレーンロープ収納場所や用具庫に置く移動式リール一式。四つのキャスター付き架台、押し手、軸受、開口スポーク側板と巻胴、手回しクランク、一本の連続ロープに穴あき浮子を通して巻いた形状を造形しています。浮子はこの一式の構成部品であり、別モデルとして数えません。水面・プール壁は付属せず、巻取り、走行、浮力、張力保持、耐荷重や競技・安全認証の機能はありません。',
        'A complete mobile lane-rope storage reel for a pool equipment area or store room, with a four-caster frame, push handle, bearings, open spoked flanges and drum, hand crank, and bored float segments visibly threaded along one continuous wound rope. Floats are components of this single asset, not separately counted models. Water and pool walls are omitted; no winding, rolling, flotation, tension retention, load rating or competition/safety certification is supplied.',
        ['pool','lane-rope-reel','storage-equipment','プール用品'])


BUILDERS=[pool_ladder,start_block,lifeguard_chair,lane_reel]


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
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-021/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true',help='Reproduce GLB/STL/metadata without presentation images.')
    args=parser.parse_args(arg);out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    if args.geometry_only:common.render=lambda *a,**k:None
    for builder in BUILDERS:
        reset();spec=builder()
        if args.only and spec[0]!=args.only:continue
        common.publish_asset(*spec,out,'scripts/city_expansion/poolside_equipment.py',azimuth=-55,elevation=24)
        if not args.geometry_only:underside(out/'_qa'/f'{spec[0]}-underside.png')
