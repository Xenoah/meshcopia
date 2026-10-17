"""Four original retail and warehouse fixture assemblies. Xenoah, CC BY 4.0.
Authoring coordinates are metres, Z-up; common.py exports ground-centered Y-up.
No external meshes, images, lettering or trademarks. Static unrigged props only.
"""
import math, sys, argparse, bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(cream=mat('Warm pale powder coating',(.66,.69,.66),.14,.48),
                steel=mat('Brushed plain metal',(.48,.53,.56),.72,.34),
                dark=mat('Opaque inactive display and rubber',(.022,.029,.034),0,.61),
                blue=mat('Deep petrol powder coating',(.045,.16,.22),.22,.42),
                white=mat('Blank opaque label inserts',(.84,.83,.76),0,.60),
                orange=mat('Rack safety-orange coating',(.72,.19,.042),.14,.47),
                wood=mat('Plain warm pallet timber',(.43,.29,.15),0,.82),
                curtain=mat('Opaque ochre curtain',(.42,.28,.095),0,.91))


def cyl(n,p,r,d,m,axis='Z',v=32,b=.001):
    o=cylinder(n,p,r,d,m,v,bevel=b)
    if axis=='X': o.rotation_euler[1]=math.pi/2
    elif axis=='Y': o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return o


def rod(n,a,b,r,m,v=20):
    a,b=Vector(a),Vector(b)
    o=cyl(n,(a+b)/2,r,(b-a).length,m,v=v,b=min(.001,r*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def bar(n,a,b,w,t,m,bev=.002):
    a,b=Vector(a),Vector(b)
    o=box(n,(a+b)/2,(w,t,(b-a).length),m,bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def ring(n,p,r,t,m,axis='Z',v=36):
    bpy.ops.mesh.primitive_torus_add(major_segments=v,minor_segments=8,major_radius=r,minor_radius=t,location=p)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,n,m,smooth=True)


def panel(n,w,h,d,p,m,holes=()):
    """Single closed XZ plate with exact rectangular apertures, no Boolean ops.
    A conforming cell grid prevents T-junctions. Aperture walls are solid thickness.
    """
    xs=sorted(set([-w/2,w/2]+[v for x0,x1,z0,z1 in holes for v in (x0,x1)]))
    zs=sorted(set([-h/2,h/2]+[v for x0,x1,z0,z1 in holes for v in (z0,z1)]))
    occupied={}
    for i in range(len(xs)-1):
        for j in range(len(zs)-1):
            x,z=(xs[i]+xs[i+1])/2,(zs[j]+zs[j+1])/2
            occupied[i,j]=not any(x0<x<x1 and z0<z<z1 for x0,x1,z0,z1 in holes)
    vs=[];fs=[];index={}
    def vert(x,y,z):
        q=(x,y,z)
        if q not in index:index[q]=len(vs);vs.append(q)
        return index[q]
    def face(points):fs.append(tuple(vert(*q) for q in points))
    for (i,j),solid in occupied.items():
        if not solid:continue
        a,b=xs[i],xs[i+1];c,e=zs[j],zs[j+1];f,g=-d/2,d/2
        face([(a,f,c),(b,f,c),(b,f,e),(a,f,e)])
        face([(a,g,e),(b,g,e),(b,g,c),(a,g,c)])
        if not occupied.get((i-1,j),False):face([(a,f,c),(a,f,e),(a,g,e),(a,g,c)])
        if not occupied.get((i+1,j),False):face([(b,f,e),(b,f,c),(b,g,c),(b,g,e)])
        if not occupied.get((i,j-1),False):face([(b,f,c),(a,f,c),(a,g,c),(b,g,c)])
        if not occupied.get((i,j+1),False):face([(a,f,e),(b,f,e),(b,g,e),(a,g,e)])
    o=mesh(n,vs,fs,m);o.location=p
    return o


def triangle_bracket(n,x,sign,z,m):
    # A closed triangular plate intersects its upright and the underside of its shelf.
    cross=[(sign*.028,z-.155),(sign*.028,z+.002),(sign*.470,z+.002)]
    vs=[(xx,y,zz) for xx in [x-.009,x+.009] for y,zz in cross]
    return mesh(n,vs,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],m,.001)


def belt_loop(n,left,right,z,r,thick,width,m):
    loops=[];N=16
    for radius in [r,r-thick]:
        loop=[]
        for i in range(N+1):
            a=-math.pi/2+i*math.pi/N;loop.append((right+radius*math.cos(a),z+radius*math.sin(a)))
        for i in range(N+1):
            a=math.pi/2+i*math.pi/N;loop.append((left+radius*math.cos(a),z+radius*math.sin(a)))
        loops.append(loop)
    count=len(loops[0]);vs=[]
    for k,y in [(0,-width/2),(0,width/2),(1,width/2),(1,-width/2)]:vs.extend((x,y,zz) for x,zz in loops[k])
    fs=[(k*count+i,k*count+(i+1)%count,((k+1)%4)*count+(i+1)%count,((k+1)%4)*count+i) for k in range(4) for i in range(count)]
    o=mesh(n,vs,fs,m)
    # Smooth only the actual curved belt surfaces; straight runs retain planar normals.
    for f in o.data.polygons:
        i=f.index%count
        f.use_smooth=f.index//count in (0,2) and i not in (N,count-1)
    return o


def checkout_station():
    p=palette()
    # Stable asymmetrical furniture carcass with a distinct staff-side knee recess.
    box('Checkout customer toe plinth',(0,-.315,.075),(2.79,.31,.15),p['dark'],.012)
    box('Conveyor supporting cabinet',(-.75,-.015,.440),(1.59,.65,.730),p['blue'],.016)
    box('Conveyor front service panel',(-.75,-.350,.448),(1.43,.024,.603),p['cream'],.008)
    for x in [-1.33,-.17]:
        for z in [.19,.70]:cyl('Conveyor service panel screw',(x,-.367,z),.008,.006,p['steel'],'Y',v=16,b=.0005)
    box('Scanner cabinet front body',(.405,-.175,.470),(.665,.420,.790),p['blue'],.014)
    box('Cashier drawer casing',(.405,.204,.770),(.628,.360,.194),p['cream'],.008)
    box('Cashier drawer front',(.405,.392,.770),(.571,.019,.137),p['steel'],.004)
    box('Cash drawer recessed pull',(.405,.410,.782),(.177,.022,.025),p['dark'],.004)
    box('Bagging pedestal',(.999,-.182,.427),(.621,.420,.704),p['blue'],.013)
    box('Bagging pedestal rear access',(.999,.039,.427),(.529,.018,.571),p['cream'],.007)
    box('Cashier footrest longitudinal rail',(.451,.298,.171),(.741,.038,.040),p['steel'],.006)
    for x in [.104,.798]:bar('Cashier footrest support',(x,.298,.171),(x,-.014,.147),.031,.031,p['steel'])
    # Complete conveyor loop, visible rollers and inset side rails.
    belt_loop('Continuous closed conveyor belt',-1.344,-.228,.846,.092,.014,.586,p['dark'])
    for x in [-1.344,-.228]:
        cyl('Conveyor end drum',(x,0,.846),.077,.578,p['steel'],'Y',v=40,b=.002)
        rod('Conveyor end roller axle',(x,-.355,.846),(x,.355,.846),.012,p['steel'])
    for y in [-.328,.328]:
        box('Conveyor retaining rim',(-.786,y,.920),(1.374,.055,.089),p['steel'],.007)
        for x in [-1.344,-.228]:cyl('Conveyor axle end cap',(x,y*1.09,.846),.021,.017,p['steel'],'Y',v=24,b=.001)
    box('Conveyor leading end guard',(-1.449,0,.842),(.036,.711,.116),p['steel'],.006)
    box('Flat scan counter',(.365,0,.913),(.881,.738,.057),p['steel'],.009)
    box('Horizontal scanner opaque window',(.295,-.020,.947),(.318,.333,.012),p['dark'],.006)
    box('Scanner upright housing',(.295,-.262,1.078),(.365,.127,.280),p['dark'],.012)
    box('Scanner upright opaque window',(.295,-.190,1.081),(.281,.014,.185),p['blue'],.004)
    box('Bagging landing surface',(1.051,0,.844),(.713,.871,.059),p['steel'],.010)
    for y in [-.435,.435]:box('Bagging surface raised side lip',(1.051,y,.874),(.717,.026,.070),p['steel'],.004)
    box('Bagging end retaining lip',(1.404,0,.875),(.025,.869,.071),p['steel'],.004)
    # The terminal faces the cashier at +Y; opaque non-emissive screens only.
    box('Terminal weighted mounting base',(.680,.198,.959),(.220,.213,.034),p['dark'],.008)
    cyl('Terminal mounting pole',(.680,.198,1.112),.024,.290,p['steel'],v=28,b=.002)
    box('Terminal upper tilt hinge',(.680,.198,1.265),(.207,.055,.047),p['dark'],.005)
    tilt=-.16
    box('Cashier terminal back housing',(.680,.205,1.363),(.361,.077,.278),p['dark'],.012,rot=(tilt,0,0))
    box('Cashier terminal opaque blank display',(.680,.250,1.365),(.316,.012,.229),p['blue'],.004,rot=(tilt,0,0))
    box('Cashier keypad base',(.187,.274,.970),(.275,.177,.038),p['dark'],.006)
    for i in range(4):
        for j in range(3):box('Unmarked cashier key',(.095+i*.059,.229+j*.044,.993),(.044,.030,.011),p['cream'],.002)
    tube('Terminal fixed cable',[(.680,.170,1.235),(.722,.173,1.143),(.734,.163,1.032),(.701,.159,.950)],.006,p['dark'],2)
    return ('city-retail-checkout-station','ベルト式小売店レジ台','Retail belt checkout station',
        'スーパーや小売店の会計レーンに置く、コンベヤ一体型の無銘レジ台。閉じたベルトと端部ドラム、二面のスキャナー外装、店員側を向いた端末と無刻印キー、引出し・足掛け・膝元の空き、荷物をまとめる低い袋詰め面を造形。画面と読取面は不透明・非発光の固定材質で、ベルト移動、読取、会計、引出し操作は未実装。',
        'An unbranded belt checkout for supermarket and retail payment lanes. It includes a closed conveyor loop and end drums, two-plane scanner exterior, cashier-facing terminal and unmarked keys, drawer, footrest, staff knee clearance, and a lower bagging landing. Display and scan faces are opaque, non-emissive static materials. Belt motion, scanning, payment and drawer operation are not implemented.',
        ['retail','checkout','conveyor','レジ台'])


def gondola_shelving():
    p=palette()
    box('Gondola recessed toe plinth',(0,0,.083),(1.242,.930,.166),p['blue'],.010)
    box('Gondola broad base deck',(0,0,.195),(1.286,1.068,.066),p['cream'],.007)
    for x in [-.585,.585]:
        slots=[(-.010,.010,-.760+i*.095,-.717+i*.095) for i in range(17)]
        panel('Perforated adjustable gondola upright',.076,1.737,.063,(x,0,1.078),p['steel'],slots)
        box('Gondola upright top cap',(x,0,1.956),(.081,.071,.024),p['cream'],.003)
    box('Gondola central back panel',(0,0,1.060),(1.100,.029,1.651),p['cream'],.003)
    # Four genuinely supported shelf decks on each face, including the base level.
    for side in [-1,1]:
        for z in [.259,.720,1.181,1.642]:
            box('Double-sided shop shelf deck',(0,side*.285,z),(1.135,.461,.027),p['cream'],.003)
            for x in [-.548,.548]:
                triangle_bracket('Shelf triangular cantilever bracket',x,side,z-.015,p['steel'])
                box('Shelf hooked upright attachment',(x,side*.041,z-.068),(.027,.047,.139),p['steel'],.001)
            box('Shelf front folded fascia',(0,side*.522,z-.001),(1.159,.026,.056),p['blue'],.003)
            box('Blank price-strip insert',(0,side*.537,z+.001),(1.102,.008,.029),p['white'],.001)
            for x in [-.564,.564]:box('Shelf end retaining edge',(x,side*.287,z+.019),(.019,.455,.040),p['cream'],.002)
    box('Gondola top spine trim',(0,0,1.905),(1.140,.065,.048),p['cream'],.004)
    return ('city-retail-gondola-shelving','両面式小売店ゴンドラ棚','Double-sided retail gondola shelving',
        'コンビニや小売店の売場通路に並べる、自立した両面ゴンドラ棚。左右の支柱には実際に貫通する取付長穴があり、中央背板、引き込まれた蹴込み台、片面四段ずつ計八枚の棚板、三角支持金具と取付爪風部品、無記載のプライス帯を備えます。商品や値札文字は含みません。高さ調整・荷重・実用上の安全性は再現または検証していません。',
        'A freestanding double-sided gondola for convenience-store and retail aisles. Two uprights have actual through mounting slots, with a central backing panel, recessed toe plinth, eight shelf decks arranged four per face, triangular support brackets, hook-form attachments and blank price strips. No goods or price lettering are included. Height adjustment, load behavior and operational safety are not implemented or validated.',
        ['retail','shelving','gondola','陳列棚'])


def folded_curtain(n,p,m):
    # Thick, closed folded cloth strip; not a single-sided alpha plane.
    width=.225;height=1.715;N=48;vs=[]
    for z in [-height/2,height/2]:
        for depth in [-.005,.005]:
            vs.extend((-width/2+width*i/N,.032*math.sin(i*math.tau/8)+depth,z) for i in range(N+1))
    R=N+1;fs=[]
    for i in range(N):
        fs.extend([(i,i+1,2*R+i+1,2*R+i),(R+i,3*R+i,3*R+i+1,R+i+1),
                   (i,R+i,R+i+1,i+1),(2*R+i,2*R+i+1,3*R+i+1,3*R+i)])
    fs.extend([(0,2*R,3*R,R),(N,R+N,3*R+N,2*R+N)])
    o=mesh(n,vs,fs,m);o.location=p
    for f in o.data.polygons:f.use_smooth=f.index<4*N and f.index%4 in (0,1)
    return o


def photo_booth():
    p=palette()
    box('Booth raised floor base',(0,0,.060),(1.800,1.284,.120),p['blue'],.015)
    box('Booth interior floor',(0,.008,.128),(1.681,1.157,.025),p['dark'],.004)
    box('Booth left external wall',(-.866,0,1.090),(.067,1.250,1.990),p['cream'],.009)
    box('Booth right external wall',(.866,0,1.090),(.067,1.250,1.990),p['cream'],.009)
    # Rear ventilation slots genuinely penetrate the rear service wall.
    holes=[(-.759,-.441,-.10+i*.076,-.071+i*.076) for i in range(8)]
    panel('Booth rear wall with true service vents',1.674,1.988,.059,(0,.596,1.090),p['cream'],holes)
    box('Booth overhanging roof',(0,0,2.121),(1.839,1.321,.107),p['blue'],.012)
    box('Booth front blank header',(0,-.594,1.998),(1.714,.091,.213),p['cream'],.008)
    box('Booth service compartment partition',(-.380,.010,1.084),(.049,1.156,1.915),p['cream'],.006)
    # Front service cabinet includes a true output mouth and blank controls.
    panel('Booth front service fascia',.464,1.779,.058,(-.620,-.596,1.012),p['blue'],[(-.154,.154,-.320,-.283)])
    box('Booth recessed empty output back',(-.620,-.530,.712),(.311,.020,.047),p['dark'],.002)
    box('Booth output collection ledge',(-.620,-.632,.689),(.338,.106,.023),p['steel'],.003)
    box('External blank service-control bezel',(-.620,-.633,1.448),(.309,.041,.287),p['dark'],.009)
    box('External inactive opaque control face',(-.620,-.657,1.448),(.257,.011,.234),p['blue'],.004)
    box('Unmarked service reader plate',(-.620,-.635,1.156),(.244,.031,.134),p['steel'],.005)
    box('Unmarked service button',(-.620,-.657,1.156),(.080,.014,.046),p['dark'],.004)
    # Interior camera/display assembly faces +X toward the stool on the opposite wall.
    box('Internal photographic equipment fascia',(-.341,.086,1.348),(.031,.682,1.008),p['blue'],.009)
    box('Interior inactive display bezel',(-.313,.079,1.240),(.034,.428,.308),p['dark'],.007)
    box('Interior opaque blank display',(-.291,.079,1.240),(.011,.372,.257),p['blue'],.004)
    cyl('Internal fixed camera lens barrel',(-.286,.080,1.617),.050,.093,p['dark'],'X',v=40,b=.002)
    ring('Camera exterior lens rim',(-.236,.080,1.617),.041,.006,p['steel'],'X',v=40)
    cyl('Camera opaque lens face',(-.233,.080,1.617),.034,.009,p['dark'],'X',v=40,b=.001)
    box('Inactive photographic light diffuser',(-.310,.080,1.787),(.035,.477,.105),p['white'],.007)
    box('Interior blank operation button plate',(-.302,-.222,.972),(.029,.118,.081),p['steel'],.004)
    cyl('Fixed unmarked camera start button',(-.278,-.222,.972),.022,.018,p['dark'],'X',v=24,b=.001)
    # A supported seat with a back cushion, no floating seat slab.
    box('Seat anchoring foot',(.603,.077,.159),(.338,.439,.054),p['steel'],.007)
    cyl('Photo seat support pedestal',(.603,.077,.327),.063,.310,p['steel'],v=32,b=.003)
    box('Photo booth seat base',(.545,.077,.493),(.500,.581,.056),p['dark'],.012)
    box('Photo booth seat cushion',(.545,.077,.536),(.515,.592,.064),p['blue'],.018)
    box('Photo booth wall-backed seat cushion',(.814,.077,.798),(.041,.605,.398),p['blue'],.014)
    # Partial curtain gathers only at the right side; the entrance remains open.
    rod('Curtain overhead support rod',(-.367,-.547,1.865),(.848,-.547,1.865),.014,p['steel'],24)
    folded_curtain('Gathered opaque folded privacy curtain',(.721,-.556,.9875),p['curtain'])
    for i in range(7):
        x=.6085+i*.0375
        ring('Curtain hanging loop',(x,-.547,1.862),.020,.004,p['steel'],'X',v=20)
    box('Curtain tie-back band',(.728,-.592,.906),(.205,.018,.057),p['blue'],.003)
    box('Open entrance threshold edge',(.173,-.624,.119),(1.162,.041,.029),p['steel'],.004)
    for x in [-.827,.827]:
        for z in [.186,1.906]:cyl('Rear maintenance panel screw',(x,.631,z),.009,.008,p['steel'],'Y',v=16,b=.0005)
    return ('city-photo-booth','開いた入口付き写真ブース','Photo booth with open entrance',
        '駅や商業施設の通路に置く、自立型の無銘写真ブース。前面には入室できる空いた開口と片側に寄せた厚みのあるカーテンがあり、内部に台座付き座席・背当て、向かい合う固定カメラと不透明な画面、外側に無記載の操作面と空の出力口、背面に貫通換気スリットを造形。画面・レンズ・照明面は不透明かつ非発光です。撮影、印刷、支払、カーテン操作は未実装。',
        'A freestanding unbranded photo booth for station and shopping-center corridors. Its front has a genuinely open entrance and thick gathered curtain at one side, with a pedestal seat/backrest, opposing fixed camera and opaque display inside, blank exterior controls, an empty output mouth, and through ventilation slots at the rear. Display, lens and lighting faces are opaque and non-emissive. Photography, printing, payment and curtain motion are not implemented.',
        ['retail','photo-booth','interior','写真ブース'])


def pallet(n,x,y,z,p):
    # One empty block pallet: three runners, nine blocks, three bearers, five top boards.
    for xx in [-.440,0,.440]:
        box(n+' bottom runner',(x+xx,y,z+.013),(.145,1.010,.026),p['wood'],.002)
        for yy in [-.410,0,.410]:box(n+' spacer block',(x+xx,y+yy,z+.060),(.143,.146,.070),p['wood'],.002)
    for yy in [-.410,0,.410]:box(n+' transverse bearer',(x,y+yy,z+.104),(1.108,.145,.025),p['wood'],.002)
    for xx in [-.448,-.224,0,.224,.448]:
        box(n+' upper deck board',(x+xx,y,z+.131),(.188,1.010,.029),p['wood'],.002)
        for yy in [-.410,.410]:cyl(n+' visible flush nail head',(x+xx,y+yy,z+.146),.0038,.0014,p['steel'],v=12,b=0)


def pallet_racking():
    p=palette()
    for x in [-1.326,1.326]:
        for y in [-.503,.503]:
            box('Rack upright anchored baseplate',(x,y,.017),(.208,.198,.034),p['steel'],.004)
            holes=[(-.013,.013,-1.330+i*.100,-1.277+i*.100) for i in range(27)]
            panel('Rack upright with true connector slots',.100,2.938,.075,(x,y,1.503),p['blue'],holes)
            box('Rack upright top cap',(x,y,2.984),(.104,.079,.027),p['blue'],.002)
            for dx in [-.074,.074]:cyl('Rack anchor bolt',(x+dx,y,.043),.013,.017,p['steel'],v=6,b=.001)
        # Bracing is carried by the two side frames, not floating behind the bay.
        for z in [.185,1.073,1.961,2.851]:bar('Rack side-frame horizontal tie',(x,-.502,z),(x,.502,z),.041,.042,p['blue'])
        for z in [.185,1.073,1.961]:
            bar('Rack side-frame diagonal brace',(x,-.489,z),(x,.489,z+.888),.037,.032,p['steel'])
        for y in [-.503,.503]:
            for z in [.185,1.073,1.961,2.851]:cyl('Rack side brace joint fastener',(x+.057,y,z),.013,.018,p['steel'],'X',v=6,b=.001)
    for z in [.400,1.400,2.400]:
        for y in [-.503,.503]:
            box('Rack connected load crossbeam',(0,y,z),(2.586,.091,.132),p['orange'],.006)
            for x in [-1.278,1.278]:
                box('Rack crossbeam end connector plate',(x,y,z+.014),(.065,.108,.228),p['orange'],.003)
                for dz in [-.049,.067]:cyl('Rack connector locking pin',(x,y-.061,z+dz),.009,.014,p['steel'],'Y',v=20,b=.001)
        for x in [-.674,.674]:bar('Rack depthwise pallet support rail',(x,-.503,z+.035),(x,.503,z+.035),.061,.061,p['steel'])
    pallet('Lower left empty pallet',-.644,0,.466,p)
    pallet('Middle left empty pallet',-.644,0,1.466,p)
    pallet('Middle right empty pallet',.644,0,1.466,p)
    box('Blank rack end identification plate',(-1.384,-.503,1.810),(.020,.160,.168),p['white'],.003)
    for z in [1.750,1.870]:cyl('Rack blank plate side mounting screw',(-1.399,-.503,z),.008,.010,p['steel'],'X',v=16,b=.0006)
    return ('city-pallet-racking-bay','空パレット付き倉庫ラック一区画','Warehouse pallet-racking bay',
        '倉庫・物流施設に置く一連のパレットラック一区画。四本の貫通スロット付き支柱、接地用足板、左右の水平材と斜材、三段の前後クロスビームと接続金具、奥行方向のパレット受け、原作の空の木製ブロックパレット三枚を備えます。パレットは下段左に一枚、中段に二枚で、上段は空です。収納物やロゴはなく、全体で一モデルです。荷重計算、固定工事、構造安全性・搬送動作は未検証。',
        'One complete pallet-racking bay for warehouse and distribution scenes. It has four through-slotted uprights and footplates, horizontal/diagonal side-frame bracing, three pairs of connected front/rear crossbeams, depthwise pallet supports, and three original empty timber block pallets. One pallet is on the lower left, two are on the middle level, and the upper level is empty. There are no goods or logos; the entire bay counts as one model. Load ratings, anchoring works, structural safety and handling behavior are not validated.',
        ['warehouse','pallet-racking','storage','倉庫ラック'])


BUILDERS=[checkout_station,gondola_shelving,photo_booth,pallet_racking]
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-050/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true');a=parser.parse_args(args)
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    if a.geometry_only:
        import common
        common.render=lambda *args,**kwargs:None
    for builder in BUILDERS:
        reset();spec=builder()
        if a.only and spec[0]!=a.only:continue
        bpy.context.view_layer.update()
        publish_asset(*spec,out,'scripts/city_expansion/retail_storage_fixtures.py',azimuth=-55,elevation=25)
