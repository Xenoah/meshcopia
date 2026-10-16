"""Four original architectural / retail city assemblies, CC BY 4.0, Xenoah.
No third-party geometry, images, fonts or trademarks. Static visual assets only.
Authoring: Blender Z-up metres. Export: self-contained GLB / matching STL, Y-up m.
Rebuild: CITY_RENDER_SAMPLES=48 blender -b --factory-startup --threads 4 \\
 --python scripts/city_expansion/architectural_entry.py -- --out batches/batch-005/assets
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(
        alu=mat('Brushed natural aluminium',(.48,.55,.58),.78,.30),
        steel=mat('Satin stainless fasteners',(.48,.51,.53),.82,.24),
        zinc=mat('Galvanized rear mounting hardware',(.27,.33,.35),.73,.46),
        dark=mat('Graphite anodized metal',(.035,.052,.062),.58,.36),
        rubber=mat('Black EPDM seals',(.014,.020,.022),0,.80),
        glass=mat('Opaque blue-tinted glazing substitute',(.15,.36,.43),.22,.16),
        dome=mat('Opaque smoke-blue rooflight surface',(.24,.43,.49),.15,.15),
        ivory=mat('Warm ivory molded antenna enclosure',(.78,.80,.75),.04,.35),
        coil=mat('Dark gray antenna loop covers',(.20,.26,.27),.15,.48),
        lens=mat('Opaque dark status-light lens',(.02,.10,.12),.1,.16),
        canvas=mat('Black coated dock-shelter fabric',(.034,.044,.048),0,.88),
        seam=mat('Reinforced charcoal fabric seams',(.065,.08,.085),0,.76),
        yellow=mat('Muted yellow alignment stripes',(.83,.57,.09),0,.64),
        curb=mat('Warm gray insulated curb outer sheet',(.62,.66,.64),.25,.45),
        liner=mat('Light gray inner curb liner',(.44,.49,.48),.45,.54))


def cyl(n,p,r,d,m,axis='Z',verts=32,bev=.002):
    o=cylinder(n,p,r,d,m,vertices=verts,bevel=bev)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def rod(n,a,b,r,m,verts=20,bev=.001):
    a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=min(bev,r*.15))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def beam(n,a,b,w,d,m,bev=.005):
    a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,bev)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def screw(n,p,m,axis='Z',r=.008):
    cyl(n+' washer',p,r*1.5,r*.32,m,axis,20,.0003)
    q=list(p);q['XYZ'.index(axis)]+=r*.48
    cyl(n+' hex head',q,r,r*.82,m,axis,6,.0004)


def roundrect(w,h,r,steps=8):
    """Counterclockwise rounded rectangle in a local 2D plane, no duplicate seams."""
    pts=[]
    for cx,cy,a0 in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(steps+1):
            a=math.radians(a0+j*90/steps);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts


def loop_frame(n,w,h,r,band,depth,center,m,plane='XY',steps=8):
    outer=roundrect(w,h,r,steps);inner=roundrect(w-2*band,h-2*band,max(r-band,.001),steps)
    vs=[];count=len(outer)
    for path,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:
        for a,b in path:
            if plane=='YZ':v=(z,a,b)
            else:v=(a,b,z)
            vs.append(tuple(center[k]+v[k] for k in range(3)))
    fs=[]
    for k in range(4):
        for i in range(count):j=(i+1)%count;fs.append((k*count+i,k*count+j,((k+1)%4)*count+j,((k+1)%4)*count+i))
    o=mesh(n,vs,fs,m,0,False)
    # Curved corner side bands are smooth, broad planar faces stay planar.
    for i,f in enumerate(o.data.polygons):f.use_smooth=(i//count)%2==0
    return o


def annular_sector(n,outer,inner,z0,z1,a0,a1,m,steps=64):
    full=abs(a1-a0-360)<1e-6;count=steps if full else steps+1
    vs=[]
    for r,z in [(outer,z0),(outer,z1),(inner,z1),(inner,z0)]:
        for i in range(count):a=math.radians(a0+(a1-a0)*i/steps);vs.append((r*math.cos(a),r*math.sin(a),z))
    fs=[]
    for k in range(4):
        for i in range(steps):j=(i+1)%count;fs.append((k*count+i,k*count+j,((k+1)%4)*count+j,((k+1)%4)*count+i))
    if not full:fs.extend([(0,count,2*count,3*count),(count-1,4*count-1,3*count-1,2*count-1)])
    o=mesh(n,vs,fs,m,0,False)
    for i,f in enumerate(o.data.polygons):f.use_smooth=i<4*steps and (i//steps)%2==0
    return o


def radial_box(n,r,a,z,size,m,bev=.004,tangent_offset=0):
    a=math.radians(a);return box(n,(r*math.cos(a)-tangent_offset*math.sin(a),r*math.sin(a)+tangent_offset*math.cos(a),z),size,m,bev,(0,0,a))


def profile_y(n,outline,y0,y1,m,bevel=.003):
    vs=[(x,y,z) for y in [y0,y1] for x,z in outline];nn=len(outline)
    fs=[tuple(range(nn-1,-1,-1)),tuple(range(nn,nn*2))]
    fs.extend((i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn))
    return mesh(n,vs,fs,m,bevel)


def revolving_door():
    p=palette()
    # Two partial side drums leave genuine opposing front / rear entrances.
    for ai in [-40,140]:
        annular_sector('Curved stationary opaque glazing',1.305,1.289,.095,2.365,ai,ai+80,p['glass'],40)
        for z0,z1 in [(.035,.105),(2.34,2.40)]:annular_sector('Drum sill or head rail',1.335,1.268,z0,z1,ai,ai+80,p['alu'],40)
        for a in [ai,ai+40,ai+80]:
            radial_box('Stationary drum vertical mullion',1.307,a,1.226,(.052,.052,2.29),p['alu'],.007)
            for z in [.115,2.32]:
                radial_box('Mullion base or head clamp',1.31,a,z,(.078,.088,.07),p['dark'],.006)
            # Vertical rubber edge strip on the inner side of each access edge.
            if a!=ai+40:radial_box('Stationary entrance brush seal',1.267,a,1.22,(.018,.025,2.20),p['rubber'],.003)
    # Full structural head ring, open centre, layered service fascia.
    annular_sector('Continuous main header annulus',1.39,1.21,2.385,2.610,0,360,p['alu'],96)
    annular_sector('Header lower shadow trim',1.405,1.19,2.37,2.398,0,360,p['dark'],96)
    annular_sector('Header upper rain cap',1.413,1.19,2.605,2.635,0,360,p['alu'],96)
    for a in range(0,360,30):
        rad=math.radians(a)
        screw('Header top cover screw',(1.32*math.cos(rad),1.32*math.sin(rad),2.638),p['steel'],r=.007)
    for a in [20,140,260]:
        # Actual radial bearings/support webs, not a floating central drum.
        ar=math.radians(a)
        beam('Upper radial bearing support',(.08*math.cos(ar),.08*math.sin(ar),2.49),(1.245*math.cos(ar),1.245*math.sin(ar),2.49),.070,.075,p['dark'],.005)
    cyl('Top bearing housing',(0,0,2.47),.18,.22,p['dark'],verts=64,bev=.009)
    cyl('Motor access cover',(0,0,2.596),.205,.028,p['alu'],verts=64,bev=.004)
    for a in range(0,360,60):
        ar=math.radians(a);screw('Motor-cover screw',(.155*math.cos(ar),.155*math.sin(ar),2.615),p['steel'],r=.006)
    cyl('Fixed floor bearing plate',(0,0,.018),.145,.036,p['alu'],verts=64,bev=.005)
    for a in range(0,360,90):
        ar=math.radians(a);screw('Floor-bearing fixing',(.108*math.cos(ar),.108*math.sin(ar),.039),p['steel'],r=.007)
    cyl('Central rotating-looking spindle',(0,0,1.225),.072,2.39,p['alu'],verts=48,bev=.006)
    for z in [.102,2.338]:cyl('Wing hub collar',(0,0,z),.104,.082,p['dark'],verts=48,bev=.005)
    # Three genuine radial leaf assemblies, fixed at 120 degree spacing.
    for a in [20,140,260]:
        radial_box('Radial leaf opaque blue pane',.675,a,1.225,(1.09,.016,2.11),p['glass'],.002)
        for r in [.107,1.245]:radial_box('Radial leaf vertical stile',r,a,1.225,(.045,.054,2.25),p['alu'],.006)
        for z in [.126,2.324]:radial_box('Radial leaf top or bottom rail',.673,a,z,(1.135,.060,.070),p['alu'],.008)
        radial_box('Leaf waist safety rail',.675,a,1.025,(1.105,.041,.047),p['alu'],.006)
        radial_box('Outer vertical brush seal',1.275,a,1.223,(.014,.055,2.23),p['rubber'],.002)
        radial_box('Lower door sweep',.675,a,.073,(1.13,.026,.024),p['rubber'],.003)
        # Handle rails bridge true two-point mounts on both faces.
        ar=math.radians(a)
        for side in [-1,1]:
            def point(r,t,z):return (r*math.cos(ar)-t*math.sin(ar),r*math.sin(ar)+t*math.cos(ar),z)
            for r in [.59,.98]:rod('Push rail standoff',point(r,side*.024,1.04),point(r,side*.105,1.04),.012,p['steel'],20)
            rod('Radial leaf push rail',point(.57,side*.105,1.04),point(1.0,side*.105,1.04),.018,p['steel'],24,.002)
            for r in [.16,1.19]:
                for z in [.15,2.30]:radial_box('Leaf corner connection cover',r,a,z,(.042,.007,.038),p['dark'],.003,tangent_offset=side*.033)
    # Inset downlight bodies, solid opaque lenses, no emission/runtime behavior.
    for a in [80,200,320]:
        ar=math.radians(a);cyl('Header underside bezel',(1.28*math.cos(ar),1.28*math.sin(ar),2.365),.041,.016,p['dark'],verts=32,bev=.002)
        cyl('Opaque downlight diffuser',(1.28*math.cos(ar),1.28*math.sin(ar),2.353),.031,.007,p['ivory'],verts=32,bev=.001)
    return ('city-revolving-entry-door','三翼回転式エントランスドア','Three-wing revolving entry door','三枚の放射状ドア、対向する二つの開口を持つ曲面ドラム、環状ヘッダー、上部軸受支持、床軸受、両面押し棒、ブラシシールを備えた入口アセンブリ。青い面は不透明な単色PBRで、透過ガラスではありません。建物や床は含みません。静的な固定姿勢で、回転動作・自動制御・挟み込み保護や安全規格への適合は未実装・未検証です。接地配置原点と回転機構用の支点は別で、独立した可動ピボットはありません。','Entrance assembly with three radial door wings, two opposing access openings in a segmented curved drum, annular header, supported upper bearing, floor bearing, two-sided push rails and brush seals. Blue surfaces are opaque constant-color PBR glazing substitutes, not transparent glass. No building or floor is included. Fixed static pose with no rotation, automatic controls or entrapment protection, and no safety-compliance validation. The ground placement origin is not a supplied articulation pivot; moving parts are not separately rigged.',['architecture','entry','revolving-door','retail','回転ドア'])


def retail_pedestals():
    p=palette()
    # Paired pedestal planes follow YZ, with a 1.08 m nominal passage along Y.
    for x in [-.63,.63]:
        box('Molded plinth lower shell',(x,0,.065),(.184,.59,.13),p['ivory'],.028)
        box('Exposed steel mounting plate',(x,0,.018),(.23,.65,.036),p['zinc'],.015)
        box('Rubber floor isolation pad',(x,0,.0045),(.212,.628,.009),p['rubber'],.004)
        for dx in [-.078,.078]:
            for y in [-.256,.256]:screw('Floor mount anchor',(x+dx,y,.045),p['steel'],r=.009)
        loop_frame('Rounded antenna outer enclosure',.48,1.49,.14,.063,.074,(x,0,.835),p['ivory'],'YZ',10)
        loop_frame('Outer cover dark gasket seam',.463,1.47,.134,.012,.079,(x,0,.835),p['rubber'],'YZ',10)
        # Face cover overlays the narrow dark seam while leaving a real central aperture.
        for sx in [-1,1]:loop_frame('Perimeter antenna face cap',.464,1.472,.134,.050,.010,(x+sx*.043,0,.835),p['ivory'],'YZ',10)
        # Two closed, inset antenna-loop covers bridge center supports, not empty floating loops.
        loop_frame('Inner oval antenna loop cover',.308,1.285,.111,.021,.024,(x,0,.842),p['coil'],'YZ',12)
        for y in [-.153,.153]:
            for z in [.45,1.15]:box('Antenna loop enclosure bridge',(x,y,z),(.032,.082,.029),p['coil'],.007)
        for z in [.25,.84,1.43]:box('Central antenna loop crossbrace',(x,0,z),(.026,.31,.023),p['coil'],.005)
        # Opaque upper status lens fits into a shallow bezel and has no emissive claim.
        for side in [-1,1]:
            box('Upper lens bezel',(x+side*.045,0,1.525),(.016,.176,.048),p['dark'],.010)
            box('Opaque unlit status lens',(x+side*.054,0,1.527),(.010,.137,.028),p['lens'],.008)
        # Each pedestal has an outward-facing separate rear service hatch and screw heads.
        side=-1 if x<0 else 1
        box('Cable service access gasket',(x+side*.095,0,.089),(.008,.34,.079),p['rubber'],.012)
        box('Cable service access cover',(x+side*.102,0,.091),(.008,.316,.065),p['ivory'],.010)
        for y in [-.133,.133]:
            o=cyl('Service cover captive screw',(x+side*.109,y,.092),.005,.004,p['steel'],'X',16,.0005)
        # Hollow rear-facing cable gland; no cable or concealed electronics is asserted.
        gland=annular_sector('Cable-entry threaded collar',.018,.010,0,.028,0,360,p['dark'],32)
        gland.rotation_euler[0]=math.pi/2;gland.location=(x,.298,.076)
        ann=annular_sector('Cable-entry ferrule opening',.013,.0085,0,.010,0,360,p['zinc'],32)
        ann.rotation_euler[0]=math.pi/2;ann.location=(x,.312,.076)
        for y in [-.205,.205]:
            for z in [.19,1.44]:cyl('Side enclosure assembly screw',(x+side*.049,y,z),.0055,.006,p['steel'],'X',16,.0005)
    return ('city-retail-security-pedestals','店舗用アンテナゲート一対','Paired retail antenna pedestals','店舗入口に配置する二本一組のアンテナゲート外観。丸角の開口フレーム、内側ループカバー、支持橋、非発光の表示レンズ、ケーブル用サービス蓋、開口したケーブルグランド、床取付板と固定ボルトを造形。店舗、配線、商品タグや内部電子回路は含みません。検出、警報、防犯、通信や通行制御機能のない静的表示モデルで、設置基準・安全性・検出性能は未検証です。配置原点は一対全体の中心で、各固定穴の施工基準点ではありません。','A paired retail entrance antenna-gate appearance assembly with rounded open frames, inset loop covers, support bridges, unlit opaque status lenses, cable service lids, open cable glands, ground plates and mounting bolts. No shop, wiring, product tags or internal electronics is included. Static visualization with no detection, alarm, theft prevention, communications or access-control functionality; installation, safety and detection performance are unvalidated. The placement origin is centered on the complete pair, not an installation datum for individual mounting holes.',['retail','antenna-gate','security-pedestal','entrance','店舗'])


def loading_shelter():
    p=palette()
    # Rear U mounting frame and matching front header; all fabric is fixed geometry.
    for x in [-1.52,1.52]:
        box('Rear vertical wall channel',(x,.35,1.73),(.12,.10,3.38),p['zinc'],.010)
        box('Forward vertical shelter rail',(x,-.36,1.73),(.075,.065,3.28),p['dark'],.008)
        for z in [.24,1.23,2.23,3.22]:
            box('Rear wall mounting tab',(x,.412,z),(.25,.025,.17),p['zinc'],.008)
            for xx in [x-.086,x+.086]:
                cyl('Wall anchor washer',(xx,.434,z),.022,.009,p['steel'],'Y',24,.001)
                cyl('Wall anchor hex head',(xx,.445,z),.014,.018,p['steel'],'Y',6,.001)
        for z in [.35,3.12]:
            beam('Depth stand-off frame',(x,.36,z),(x,-.38,z),.06,.06,p['zinc'],.006)
            beam('Triangular frame stay',(x,.35,z+.22 if z<1 else z-.22),(x,-.31,z),.039,.039,p['zinc'],.004)
        # Closed accordion side textile shell: zig-zag front/back fold section extruded in Z.
        yz=[]
        for i in range(9):
            y=.31-i*.08125;xx=x+(1 if x>0 else -1)*(.045 if i%2 else 0);yz.append((xx,y))
        thickness=.014;vs=[]
        for z in [.16,3.28]:
            for offset in [0,thickness*(1 if x>0 else -1)]:
                vs.extend((xx+offset,y,z) for xx,y in yz)
        k=len(yz);fs=[]
        for j in range(k-1):
            fs.extend([(j,j+1,2*k+j+1,2*k+j),(k+j,3*k+j,3*k+j+1,k+j+1),(j,k+j,k+j+1,j+1),(2*k+j,2*k+j+1,3*k+j+1,3*k+j)])
        fs.extend([(0,2*k,3*k,k),(k-1,2*k-1,4*k-1,3*k-1)])
        mesh('Pleated shelter side wall',vs,fs,p['canvas'],.0015)
        # Flexible front side curtain has tapered inner corner and a visible rolled seam.
        s=1 if x>0 else -1
        outline=[(s*1.56,.16),(s*1.56,3.32),(s*1.10,3.32),(s*1.10,.36),(s*1.22,.16)]
        profile_y('Reinforced hanging side curtain',outline,-.435,-.412,p['canvas'],.008)
        box('Vertical curtain outer reinforced hem',(s*1.526,-.45,1.74),(.046,.028,3.13),p['seam'],.009)
        box('Vertical alignment guide stripe',(s*1.262,-.451,1.68),(.052,.008,2.37),p['yellow'],.004)
        for z in [.32,.68,1.04,1.40,1.76,2.12,2.48,2.84,3.20]:
            cyl('Curtain edge rivet',(s*1.526,-.468,z),.008,.006,p['steel'],'Y',16,.0005)
        # Lower molded impact / fold-stop blocks are attached to the front rails.
        box('Lower shelter corner pad',(s*1.49,-.385,.12),(.20,.17,.24),p['rubber'],.025)
        box('Lower pad fastening strip',(s*1.49,-.484,.12),(.17,.014,.07),p['zinc'],.006)
        for xx in [s*1.49-.06,s*1.49+.06]:cyl('Lower-pad screw',(xx,-.495,.12),.009,.012,p['steel'],'Y',6,.001)
    box('Rear top crossmember',(0,.35,3.37),(3.18,.10,.12),p['zinc'],.010)
    box('Front canopy crossmember',(0,-.36,3.36),(3.19,.075,.085),p['dark'],.010)
    # Sloping canopy closed folded sheet above the open truck bay.
    vs=[(-1.65,-.49,3.405),(1.65,-.49,3.405),(1.65,.46,3.48),(-1.65,.46,3.48),(-1.65,-.49,3.43),(1.65,-.49,3.43),(1.65,.46,3.505),(-1.65,.46,3.505)]
    mesh('Sloping galvanized canopy',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],p['zinc'],.006)
    for x in [-1.625,1.625]:beam('Canopy turned-down side edge',(x,-.49,3.39),(x,.46,3.465),.028,.074,p['zinc'],.004)
    # True shallow front gutter, open at the top, with closed end pieces.
    box('Canopy front gutter bed',(0,-.506,3.365),(3.30,.10,.022),p['zinc'],.004)
    box('Canopy gutter outer upstand',(0,-.556,3.395),(3.30,.018,.078),p['zinc'],.004)
    for x in [-1.64,1.64]:box('Canopy gutter end',(x,-.512,3.395),(.022,.091,.078),p['zinc'],.004)
    # Broad hanging head curtain, reinforced segmented lower hems.
    profile_y('Hanging head curtain',[(-1.54,3.36),(1.54,3.36),(1.50,2.76),(.66,2.73),(0,2.76),(-.66,2.73),(-1.50,2.76)],-.453,-.424,p['canvas'],.008)
    box('Head curtain attachment clamp',(0,-.473,3.32),(3.07,.026,.06),p['zinc'],.006)
    for x in [-1.40,-1.12,-.84,-.56,-.28,0,.28,.56,.84,1.12,1.40]:cyl('Head-clamp fixing',(x,-.492,3.32),.008,.012,p['steel'],'Y',6,.001)
    for x in [-1.0,-.50,0,.50,1.0]:box('Head curtain stitched reinforcement',(x,-.474,3.025),(.018,.011,.49),p['seam'],.004)
    beam('Head curtain left weighted hem',(-1.50,-.476,2.765),(0,-.476,2.765),.022,.028,p['seam'],.004)
    beam('Head curtain right weighted hem',(0,-.476,2.765),(1.50,-.476,2.765),.022,.028,p['seam'],.004)
    # Rear corner gussets under the canopy are explicitly visible from behind.
    for x in [-1.48,1.48]:
        beam('Rear canopy diagonal stay',(x,.34,3.03),(x,-.28,3.36),.045,.045,p['zinc'],.004)
        for y in [-.22,.22]:screw('Canopy upper bolt',(x,y,3.475 if y>.0 else 3.44),p['steel'],r=.009)
    return ('city-loading-dock-shelter','荷捌き口用ドックシェルター','Loading dock curtain shelter','倉庫の荷捌き開口に取り付ける三辺型ドックシェルター。プリーツ状の側面生地、厚みのある側幕と上幕、誘導帯、補強縁、前後フレーム、壁付け金具、斜材、傾斜ひさしと開口した雨樋を造形。トラック、倉庫壁、シャッター、ドック床や荷役機械は含みません。幕は固定メッシュで、変形・衝突・水密性・耐候性・安全性の検証や実装はありません。底面中央原点は施工の壁面基準や取付高さではなく、配置時に壁面位置と高さを合わせてください。','Three-sided warehouse loading-bay curtain shelter with pleated side fabric, thick side and head curtains, alignment strips, reinforced hems, front and rear frames, wall brackets, diagonal stays, sloped canopy and genuinely open gutter. No truck, warehouse wall, shutter, dock floor or loading equipment is included. Curtains are fixed meshes with no deformation or collision behavior, and no weather-sealing, structural or safety validation. The bottom-centered placement origin is not a wall-mount or installation-height datum; align the mounting plane and height in the target scene.',['warehouse','loading-dock','shelter','architecture','荷捌き'])


def roof_dome(n,a,b,h,zbase,m,segments=96,rings=18,thickness=.009):
    """Closed thin rectangular-domed shell, with one vertex at each apex.
    Superellipse exponent 4 gives thermoformed rounded rectangular plan rings.
    """
    vs=[];paths=[]
    for inner in [False,True]:
        aa=a-(thickness if inner else 0);bb=b-(thickness if inner else 0);hh=h-(thickness if inner else 0)
        paths.append([[len(vs)]]);vs.append((0,0,zbase+hh))
        for k in range(1,rings+1):
            theta=math.pi/2*k/rings;rr=math.sin(theta);z=zbase+hh*math.cos(theta);inds=[]
            for j in range(segments):
                ph=math.tau*j/segments;c=math.cos(ph);s=math.sin(ph)
                x=aa*rr*math.copysign(math.sqrt(abs(c)),c);y=bb*rr*math.copysign(math.sqrt(abs(s)),s)
                inds.append(len(vs));vs.append((x,y,z))
            paths[-1].append(inds)
    fs=[]
    for ip,pa in enumerate(paths):
        for k in range(rings):
            prev,nex=pa[k],pa[k+1]
            for j in range(segments):
                jj=(j+1)%segments
                face=(prev[0],nex[j],nex[jj]) if len(prev)==1 else (prev[j],nex[j],nex[jj],prev[jj])
                fs.append(tuple(reversed(face)) if ip else face)
    for j in range(segments):jj=(j+1)%segments;fs.append((paths[0][-1][j],paths[1][-1][j],paths[1][-1][jj],paths[0][-1][jj]))
    return mesh(n,vs,fs,m,0,True)


def dome_flange(m,segments=96):
    """A closed flat glazing flange bridges the domed plan to the curb corners."""
    vs=[]
    for aa,bb,power,z in [(.786,.586,.125,.334),(.786,.586,.125,.347),(.735,.535,.5,.347),(.735,.535,.5,.334)]:
        for j in range(segments):
            a=math.tau*j/segments;c=math.cos(a);s=math.sin(a)
            vs.append((aa*math.copysign(abs(c)**power,c),bb*math.copysign(abs(s)**power,s),z))
    fs=[]
    for k in range(4):
        for j in range(segments):
            jj=(j+1)%segments;fs.append((k*segments+j,k*segments+jj,((k+1)%4)*segments+jj,((k+1)%4)*segments+j))
    return mesh('Continuous flat glazing flange',vs,fs,m,0,False)


def domed_skylight():
    p=palette()
    # Hollow curb and flashed base retain an actual opening visible from below.
    loop_frame('Wide roof-weather flashing flange',1.84,1.44,.065,.145,.018,(0,0,.009),p['zinc'],steps=8)
    loop_frame('Insulated raised curb shell',1.57,1.17,.038,.070,.300,(0,0,.168),p['curb'],steps=8)
    loop_frame('Internal curb liner return',1.435,1.035,.025,.018,.285,(0,0,.165),p['liner'],steps=8)
    loop_frame('Curb lower drip apron',1.61,1.21,.045,.040,.040,(0,0,.043),p['zinc'],steps=8)
    loop_frame('Continuous rooflight seating gasket',1.585,1.185,.08,.070,.020,(0,0,.325),p['rubber'],steps=12)
    # Lip and separate smoothly crowned shell are deliberately opaque, not transmission glass.
    dome_flange(p['dome'])
    roof_dome('Closed domed glazing substitute',.754,.554,.295,.346,p['dome'])
    # Four separate top clamps leave deliberate drainage gaps near corners.
    for y in [-.579,.579]:box('Long glazing retainer',(0,y,.355),(1.38,.046,.029),p['alu'],.009)
    for x in [-.779,.779]:box('Short glazing retainer',(x,0,.355),(.046,.946,.029),p['alu'],.009)
    for y in [-.580,.580]:
        for x in [-.62,-.31,0,.31,.62]:screw('Long retainer screw',(x,y,.373),p['steel'],r=.007)
    for x in [-.780,.780]:
        for y in [-.39,0,.39]:screw('Short retainer screw',(x,y,.373),p['steel'],r=.007)
    # Discrete outer skirt overlap strips, visible fixing hardware and corner gussets.
    for x in [-.792,.792]:
        box('Curb vertical corner seam',(x,0,.174),(.010,.029,.278),p['zinc'],.003)
        for y in [-.46,0,.46]:
            for z in [.085,.265]:cyl('Curb side fastening',(x+(.008 if x>0 else -.008),y,z),.006,.009,p['steel'],'X',16,.0005)
    for y in [-.591,.591]:
        for x in [-.60,0,.60]:
            for z in [.085,.265]:cyl('Curb end fastening',(x,y,z),.006,.009,p['steel'],'Y',16,.0005)
    for x in [-.85,.85]:
        for y in [-.63,0,.63]:screw('Flashing roof fixing',(x,y,.023),p['steel'],r=.007)
    for y in [-.65,.65]:
        for x in [-.42,0,.42]:screw('Flashing long-edge fixing',(x,y,.023),p['steel'],r=.007)
    for sx in [-1,1]:
        for sy in [-1,1]:
            # Four triangular sheet gussets support liner corners from the underside.
            vs=[(sx*.694,sy*.494,.045),(sx*.594,sy*.494,.045),(sx*.694,sy*.394,.045),(sx*.694,sy*.494,.060),(sx*.594,sy*.494,.060),(sx*.694,sy*.394,.060)]
            mesh('Internal curb corner gusset',vs,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],p['zinc'],.002)
    return ('city-domed-roof-skylight','立上り枠付きドーム型天窓','Domed roof skylight with raised curb','屋根に配置する固定式ドーム天窓。丸角長方形の厚み付きドーム、開口を持つ立上り枠と内張り、止水フランジ、連続ガスケット、分割押縁、留めねじ、内側隅補強を造形。ドームは不透明な青灰色の単色PBRで、透過・採光の再現ではありません。屋根本体、開閉機構や通気機能は含みません。水密性・断熱性・荷重・防火・施工・安全基準は未検証です。底面中央の配置原点は実際の屋根勾配・取付面基準とは別で、配置先に合わせて調整してください。','Fixed rooflight with a thick rounded-rectangular domed shell, genuinely hollow raised curb and liner, weather-flashing flange, continuous gasket, separate retainer bars, fastening screws and internal corner gussets. The dome is an opaque blue-gray constant-color PBR surface, not transparent glazing or a daylight simulation. No roof, opening mechanism or ventilation function is included. Weather sealing, insulation, loading, fire performance, installation and safety standards are unvalidated. The bottom-centered placement origin is separate from the actual roof slope or mounting datum and must be positioned for the target scene.',['roof','skylight','dome','architecture','天窓'])


BUILDERS=[revolving_door,retail_pedestals,loading_shelter,domed_skylight]
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-005/assets');ap.add_argument('--only',default='');a=ap.parse_args(args)
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    for fn in BUILDERS:
        reset();spec=fn()
        if a.only and spec[0]!=a.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/architectural_entry.py',azimuth=-58,elevation=25 if spec[0]!='city-domed-roof-skylight' else 29)
