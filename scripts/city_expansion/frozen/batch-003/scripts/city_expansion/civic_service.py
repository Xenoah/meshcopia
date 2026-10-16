"""Four original city service assets for Xenoah / Meshcopia, CC BY 4.0.
Original procedural geometry and constant-color materials only. No outside assets.
Blender Z-up metres; common exporter emits GLB and equivalent STL in Y-up metres.
Usage: CITY_RENDER_SAMPLES=48 blender -b --threads 4 --python scripts/city_expansion/civic_service.py -- --out batches/batch-003/assets [--only ID]
"""
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *


def colors():
    return dict(steel=mat('Satin stainless steel',(.43,.49,.51),.8,.29),zinc=mat('Dull galvanized hardware',(.37,.41,.41),.72,.46),dark=mat('Graphite cast metal',(.035,.045,.045),.3,.57),rubber=mat('Charcoal elastomer',(.012,.019,.020),0,.78),green=mat('Deep green enamel',(.055,.16,.13),.3,.35),brass=mat('Antique brass accent',(.46,.30,.10),.75,.35),lens=mat('Opaque optical blue coating',(.025,.13,.18),.72,.13),orange=mat('Safety ochre powder coating',(.69,.35,.055),.2,.45),wood=mat('Replaceable composite brush block',(.28,.17,.075),0,.72),bristle=mat('Stiff tan brush fibers',(.43,.32,.17),0,.92),teal=mat('Molded teal tank polymer',(.045,.29,.28),0,.55),cream=mat('Molded basin ivory',(.64,.70,.66),0,.40),soap=mat('Opaque soap dispenser body',(.66,.72,.74),0,.42),black=mat('Unpainted charcoal steel',(.06,.065,.065),.68,.65))


def cyl(n,p,r,d,m,axis='Z',verts=40,bev=.002,r2=None):
    if r2 is None:o=cylinder(n,p,r,d,m,verts,bevel=bev)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=p)
        o=finish(bpy.context.object,n,m,bev,True)
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    if axis=='X':o.rotation_euler[1]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def rod(n,a,b,r,m,verts=20,bev=.0008):
    a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,verts=verts,bev=min(bev,r*.15));o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def beam(n,a,b,w,d,m):
    a,b=Vector(a),Vector(b);o=box(n,(a+b)/2,(w,d,(b-a).length),m,.003);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def ring(n,center,outer,inner,depth,m,axis='Z',segments=48):
    vs=[]
    for r,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:
        vs.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for i in range(segments))
    fs=[]
    for k in range(4):
        for i in range(segments):
            j=(i+1)%segments;fs.append((k*segments+i,k*segments+j,((k+1)%4)*segments+j,((k+1)%4)*segments+i))
    o=mesh(n,vs,fs,m,0,True);o.location=center
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    if axis=='X':o.rotation_euler[1]=math.pi/2
    # Annular end caps stay planar.
    for i,f in enumerate(o.data.polygons):f.use_smooth=(i//segments)%2==0
    return o


def screw(n,p,m,axis='Z',r=.007):
    cyl(n+' washer',p,r*1.55,r*.33,m,axis,24,.00035)
    q=list(p);q['XYZ'.index(axis)]+=(-1 if axis=='Y' else 1)*r*.4
    cyl(n+' hex bolt',q,r,r*.85,m,axis,6,.0004)


def lathe(n,profile,m,segments=64):
    vs=[];rings=[]
    for r,z in profile:
        if r==0:rings.append([len(vs)]);vs.append((0,0,z))
        else:rings.append(list(range(len(vs),len(vs)+segments)));vs.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for i in range(segments))
    fs=[]
    for a,b in zip(rings,rings[1:]+rings[:1]):
        if len(a)==1 and len(b)==1:continue
        for i in range(segments):
            j=(i+1)%segments
            if len(a)==1:fs.append((a[0],b[i],b[j]))
            elif len(b)==1:fs.append((a[i],b[0],a[j]))
            else:fs.append((a[i],b[i],b[j],a[j]))
    return mesh(n,vs,fs,m,0,True)


def slab_x(n,x0,x1,profile,m,bevel=.004):
    vs=[(x,y,z) for x in [x0,x1] for y,z in profile];l=len(profile)
    fs=[tuple(range(l-1,-1,-1)),tuple(range(l,2*l))]
    for i in range(l):j=(i+1)%l;fs.append((i,j,l+j,l+i))
    return mesh(n,vs,fs,m,bevel)


def rounded_path(xhalf,y0,zbase,ztop,r,depth=0):
    # Upright U rail, quarter-circle shoulders in the XZ plane.
    pts=[(-xhalf,y0,zbase),(-xhalf,y0,ztop-r)]
    for i in range(1,9):
        a=math.pi-math.pi/2*i/8;pts.append((-xhalf+r+r*math.cos(a),y0,ztop-r+r*math.sin(a)))
    pts.append((xhalf-r,y0,ztop))
    for i in range(1,9):
        a=math.pi/2-math.pi/2*i/8;pts.append((xhalf-r+r*math.cos(a),y0,ztop-r+r*math.sin(a)))
    pts.append((xhalf,y0,zbase));return pts


def binocular_viewer():
    p=colors()
    lathe('Stepped cast pedestal base',[(0,0),(.225,0),(.235,.018),(.235,.036),(.218,.055),(.168,.079),(.115,.11),(.076,.14),(.065,.17),(0,.17)],p['green'])
    for x in [-.145,.145]:
        for y in [-.145,.145]:screw('Foundation anchor',(x,y,.063),p['zinc'],r=.010)
    cyl('Tapered pedestal column',(0,0,.675),.065,1.06,p['green'],verts=64,bev=.008,r2=.051)
    ring('Base collar',(0,0,.161),.078,.059,.04,p['brass'],segments=64)
    cyl('Azimuth rotation bearing',(0,0,1.226),.081,.078,p['dark'],verts=64,bev=.007)
    ring('Azimuth bearing steel lip',(0,0,1.264),.085,.069,.012,p['steel'],segments=64)
    box('Coin housing',(0,-.024,1.098),(.215,.166,.244),p['green'],.023)
    box('Removable payment service panel',(0,-.112,1.102),(.179,.014,.195),p['steel'],.012)
    box('Unbranded blank instruction plate',(0,-.122,1.141),(.128,.004,.062),p['dark'],.005)
    box('Coin slot bezel',(0,-.125,1.075),(.059,.008,.030),p['brass'],.006)
    box('Recessed coin slot',(0,-.130,1.075),(.036,.002,.005),p['rubber'],.001)
    for x in [-.071,.071]:
        for z in [1.024,1.18]:screw('Service panel screw',(x,-.123,z),p['zinc'],'Y',.004)
    cyl('Coin vault key plug',(.061,-.126,1.054),.009,.009,p['dark'],'Y',24,.0008)
    box('Rear service cap',(0,.061,1.097),(.136,.018,.14),p['green'],.010)
    box('Yoke bridge',(0,0,1.306),(.57,.10,.075),p['green'],.018)
    for x in [-.276,.276]:
        slab_x('Tilt yoke cheek',x-.018,x+.018,[(-.054,1.288),(.052,1.288),(.058,1.451),(.038,1.486),(-.036,1.486),(-.059,1.448)],p['green'],.009)
        cyl('Tilt pivot hub',(x,0,1.444),.045,.060,p['brass'],'X',48,.004)
        screw('Tilt locking bolt',(x+(.035 if x>0 else -.035),0,1.444),p['zinc'],'X',.014)
    before=set(bpy.context.scene.objects)
    box('Rounded optical bridge',(0,-.006,0),(.391,.245,.174),p['green'],.043)
    for x in [-.108,.108]:
        # Optical channel aligns from ocular at negative Y to objective at positive Y.
        cyl('Twin tapered objective body',(x,.104,0),.084,.244,p['green'],'Y',64,.007,r2=.070)
        ring('Objective flared rim',(x,.241,0),.096,.075,.047,p['green'],'Y',64)
        ring('Objective inner retaining ring',(x,.243,0),.078,.069,.014,p['brass'],'Y',64)
        cyl('Recessed objective lens',(x,.232,0),.069,.006,p['lens'],'Y',64,.0007)
        cyl('Ocular extension',(x,-.164,0),.050,.12,p['green'],'Y',48,.004)
        ring('Ocular ribbed rubber cup',(x,-.231,0),.050,.028,.035,p['rubber'],'Y',48)
        ring('Ocular metal retaining lip',(x,-.237,0),.031,.025,.010,p['steel'],'Y',48)
        cyl('Recessed ocular lens',(x,-.231,0),.025,.004,p['lens'],'Y',48,.0002)
        for yy in [-.222,-.229,-.236]:ring('Eyecup molded grip ring',(x,yy,0),.052,.047,.003,p['rubber'],'Y',48)
    for x in [-.226,.226]:
        # Fixed grab handles join the instrument body at two visible shoulders.
        tube('Bent viewer grip',[(x,-.08,-.035),(x*1.22,-.09,-.055),(x*1.25,-.078,-.105),(x*1.25,.075,-.105),(x*1.20,.10,-.055),(x,.10,-.035)],.014,p['green'],2)
        rod('Rubber hand grip',(x*1.25,-.063,-.105),(x*1.25,.061,-.105),.018,p['rubber'],28)
    box('Top optical service cover',(0,-.015,.093),(.186,.165,.012),p['green'],.012)
    for x in [-.072,.072]:
        for yy in [-.071,.04]:screw('Optical cover fastener',(x,yy,.103),p['zinc'],r=.004)
    rotation=Matrix.Rotation(math.radians(10),4,'X');shift=Matrix.Translation((0,0,1.445))
    for o in set(bpy.context.scene.objects)-before:o.matrix_world=shift@rotation@o.matrix_world
    return ('city-scenic-binocular-viewer','展望台用の固定双眼望遠鏡','Pedestal scenic binocular viewer','展望台や遊歩道の眺望ポイントに置く固定式双眼望遠鏡の静的モデル。実形状の二つの対物鏡筒・接眼部、上向きの本体、傾斜軸ヨーク、握り、基部固定金具、硬貨スロットと無地の点検パネルを備えます。レンズは不透明な単色表現で、拡大・光学・課金・可動機能はありません。','A static fixed binocular viewer for an observation terrace or scenic promenade. Includes two distinct objective barrels and eyepieces, an upward-tilted head, tilt-pivot yoke, grips, base anchors, coin slot and blank service panel. Lenses use an opaque constant-color representation; no magnification, optical, payment or articulation functionality is supplied.',['binoculars','scenic','observation','展望台'])


def bristle_mesh(n,roots,direction,length,m):
    # Three nonidentical, physically separate six-sided strands per visible tuft.
    vs=[];fs=[];d=Vector(direction).normalized();a=d.cross(Vector((0,1,0)))
    if a.length<.1:a=d.cross(Vector((1,0,0)))
    a.normalize();b=d.cross(a).normalized();segments=6
    for index,root in enumerate(roots):
        for j in range(3):
            angle=j*math.tau/3+index*.37;offset=a*math.cos(angle)*.0028+b*math.sin(angle)*.0028
            start=Vector(root)+offset;tip=start+d*(length*(.94+.05*math.sin(index*2.3+j)))+offset*.55
            base=len(vs);r=.0026
            for c,rr in [(start,r),(tip,r*.78)]:
                vs.extend(tuple(c+a*math.cos(i*math.tau/segments)*rr+b*math.sin(i*math.tau/segments)*rr) for i in range(segments))
            fs.append(tuple(base+i for i in range(segments-1,-1,-1)));fs.append(tuple(base+segments+i for i in range(segments)))
            for i in range(segments):k=(i+1)%segments;fs.append((base+i,base+k,base+segments+k,base+segments+i))
    return mesh(n,vs,fs,m,0,False)


def boot_cleaner():
    p=colors()
    for x in [-.302,.302]:
        box('Longitudinal ground rail',(x,0,.032),(.048,.66,.064),p['dark'],.008)
        for y in [-.29,.29]:
            box('Ground anchor foot',(x,y,.011),(.125,.108,.022),p['zinc'],.009)
            screw('Ground anchor',(x+(.032 if x>0 else -.032),y,.025),p['zinc'],r=.008)
    for y in [-.235,.235]:box('Crossmember',(0,y,.055),(.622,.036,.040),p['dark'],.006)
    # Slatted removable dirt tray has true apertures under the replaceable brush.
    for i in range(8):box('Open dirt tray slat',(-.245+i*.070,0,.056),(.045,.44,.008),p['zinc'],.002)
    box('Sole brush replaceable block',(0,-.025,.088),(.303,.38,.042),p['wood'],.006)
    for x in [-.12,.12]:
        for y in [-.187,.137]:screw('Sole brush block fixing',(x,y,.111),p['zinc'],r=.005)
    roots=[(-.115+i*.023,-.160+j*.027,.11) for i in range(11) for j in range(11)]
    bristle_mesh('Individual upward sole-brush tuft strands',roots,(0,0,1),.054,p['bristle'])
    for sign in [-1,1]:
        x=sign*.225
        box('Side brush replaceable block',(x,-.025,.173),(.035,.38,.155),p['wood'],.006)
        box('Side brush steel backing plate',(x+sign*.025,-.025,.176),(.014,.404,.176),p['orange'],.005)
        for y in [-.186,.136]:
            beam('Side brush mounting strut',(x+sign*.02,y,.058),(x+sign*.02,y,.188),.024,.026,p['dark'])
            screw('Side brush block clamp',(x+sign*.038,y,.173),p['zinc'],'X',.006)
        roots=[(sign*.206,-.174+j*.027,.130+k*.027) for j in range(12) for k in range(4)]
        bristle_mesh('Individual side-brush tuft strands',roots,(-sign,0,0),.052,p['bristle'])
    # Scraper is raised in front of the bristles and supported at both ends.
    for x in [-.226,.226]:box('Scraper support tab',(x,-.284,.098),(.027,.034,.095),p['dark'],.004)
    box('Replaceable boot scraper blade',(0,-.285,.143),(.479,.013,.043),p['steel'],.002)
    for x in [-.224,.224]:screw('Scraper retaining bolt',(x,-.296,.142),p['zinc'],'Y',.006)
    tube('Continuous upright steadying rail',rounded_path(.302,.29,.062,1.045,.074),.019,p['orange'],3)
    rod('Top textured grip',(-.195,.29,1.045),(.195,.29,1.045),.024,p['rubber'],40)
    for x in [-.302,.302]:
        ring('Rail fixing socket',(x,.29,.118),.027,.018,.12,p['dark'],segments=36)
        screw('Rail pinch screw',(x,.26,.111),p['zinc'],'Y',.005)
    return ('city-boot-cleaning-station','ブラシと泥落とし刃付きの靴清掃台','Boot brush and scraper station','公園・作業区画の入口で長靴の泥落としを表現する据置式ステーション。足裏用と左右側面用の交換ブラシブロック、独立した毛束、前面の泥落とし刃、透かし底受け、固定脚と握りレールを備えます。靴・泥は含みません。清掃性能・衛生性能・転倒防止などの安全性は検証していません。','A fixed boot-cleaning prop for park or worksite entrances, with replaceable sole and twin side brush blocks, separate bristle tufts, a front scraper blade, open slatted debris tray, anchor feet and steadying grip rail. No boots or dirt included. Cleaning efficacy, hygiene performance and safety including fall prevention have not been validated.',['boots','brush','scraper','entrance','泥落とし'])


def barbecue():
    p=colors()
    box('Anchored steel ground plate',(0,0,.014),(.37,.37,.028),p['black'],.012)
    for x in [-.135,.135]:
        for y in [-.135,.135]:screw('Pedestal anchor',(x,y,.030),p['zinc'],r=.010)
    box('Square pedestal',(0,0,.376),(.125,.125,.72),p['black'],.009)
    box('Under-basin mounting plate',(0,0,.721),(.45,.32,.018),p['black'],.006)
    for x in [-.17,.17]:beam('Basin underside gusset',(x,0,.725),(x*.27,0,.58),.025,.14,p['black'])
    # Fully modeled empty charcoal basin: floor, thick sloping sides, lowered front.
    box('Charcoal basin floor',(0,0,.75),(.64,.47,.032),p['black'],.008)
    for sign in [-1,1]:
        slab_x('Tapered grill windguard side',sign*.337-.012,sign*.337+.012,[(-.25,.746),(.268,.746),(.268,1.065),(.16,1.065),(-.25,.939)],p['black'],.005)
        beam('Side windguard top rim',(sign*.338,-.25,.939),(sign*.338,.16,1.065),.023,.018,p['black'])
    box('Rear grill windguard',(0,.257,.901),(.681,.025,.327),p['black'],.005)
    box('Rear folded top lip',(0,.257,1.065),(.704,.042,.019),p['black'],.005)
    box('Low front charcoal retaining wall',(0,-.244,.802),(.655,.024,.113),p['black'],.006)
    # Air inlets sit in a separate shallow front intake manifold, with actual gaps.
    for x in [-.25,.25]:box('Air intake end return',(x,-.262,.79),(.024,.025,.061),p['black'],.003)
    for z in [.765,.788,.811]:box('Separated intake louver',(0,-.272,z),(.494,.022,.011),p['dark'],.002)
    box('Ash service drawer front',(0,-.249,.727),(.43,.020,.055),p['dark'],.004)
    for x in [-.115,.115]:box('Ash pull mount',(x,-.267,.727),(.022,.023,.023),p['zinc'],.003)
    rod('Ash drawer pull',(-.115,-.281,.727),(.115,-.281,.727),.008,p['zinc'],20)
    # Three real support levels on each side; current grate rests on the middle ledge.
    for sign in [-1,1]:
        for y in [-.19,.19]:
            box('Vertical grate height rack',(sign*.318,y,.922),(.025,.033,.219),p['dark'],.003)
            for z in [.842,.903,.964]:box('Grate height support tooth',(sign*.301,y,z),(.052,.037,.016),p['steel'],.003)
        box('Grate side frame',(sign*.286,0,.923),(.022,.456,.025),p['steel'],.004)
    for y in [-.224,.224]:box('Grate end frame',(0,y,.923),(.594,.022,.025),p['steel'],.004)
    for i in range(18):rod('Separated cooking grate rod',(-.266+i*.0313,-.218,.929),(-.266+i*.0313,.218,.929),.0055,p['steel'],16,.0005)
    # Twin cool-touch-style springs are purely visual, not a safety claim.
    for x in [-.21,.21]:
        tube('Grate lifting handle bracket',[(x,-.213,.923),(x,-.329,.923),(x,-.35,.91),(x,-.35,.873),(x,-.32,.861)],.007,p['steel'],2)
        pts=[]
        for i in range(201):
            t=i/200;aa=t*math.tau*10;pts.append((x+.015*math.cos(aa),-.332+.087*t,.878+.015*math.sin(aa)))
        tube('Helical lifting grip spring',pts,.003,p['steel'],1)
        rod('Spring grip core rod',(x,-.337,.878),(x,-.239,.878),.006,p['steel'],20)
        rod('Return support for spring grip',(x,-.239,.878),(x,-.213,.923),.006,p['steel'],20)
        for yy in [-.337,-.239]:cyl('Spring grip retaining collar',(x,yy,.878),.020,.009,p['steel'],'Y',24,.001)
    for x in [-.26,.26]:screw('Rear basin fixing',(x,.274,.804),p['zinc'],'Y',.007)
    return ('city-public-barbecue-grill','公園用の支柱式炭火グリル','Public park pedestal charcoal grill','公園やピクニック場に置く支柱式炭火グリルの静的モデル。空の炭受け、側面・背面の風よけ、実際に隙間のある焼き網、三段の網支持金具、持ち手、吸気部と灰受けの引手を造形。食材・炭・炎は含みません。調理・耐熱・火災安全性は未検証で、動作や燃焼表現もありません。','A static pedestal charcoal grill for parks and picnic areas, with an empty charcoal basin, side and rear windguards, genuinely open cooking grate, three-level grate support brackets, lifting handles, intake details and ash-drawer pull. No food, charcoal or flame is included. Cooking function, heat resistance and fire safety are not validated; no mechanical or combustion behavior is supplied.',['barbecue','charcoal','grill','park','炭火グリル'])


def roundrect(w,d,r,z,segments=12):
    pts=[]
    for cx,cy,start in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
        for i in range(segments):
            a=math.radians(start+i*90/segments);pts.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
    return pts


def basin(n,m):
    # Continuous thick shell with real recessed bowl and through drain, no flat dark decal.
    seg=48
    profiles=[roundrect(.085,.085,.0425,.787),roundrect(.375,.255,.09,.795),roundrect(.61,.455,.13,.928),roundrect(.64,.485,.14,.948),roundrect(.575,.42,.112,.949),roundrect(.36,.24,.09,.825),roundrect(.085,.085,.0425,.811)]
    # Round-rectangle all-arc drain ring retains 48 distinct vertices.
    vs=[v for profile in profiles for v in profile];fs=[]
    for k in range(len(profiles)):
        nxt=(k+1)%len(profiles)
        for i in range(seg):j=(i+1)%seg;fs.append((k*seg+i,k*seg+j,nxt*seg+j,nxt*seg+i))
    return mesh(n,vs,fs,m,0,True)


def handwash():
    p=colors()
    box('Wide stabilized molded base',(0,0,.049),(.69,.62,.098),p['dark'],.038)
    for x in [-.269,.269]:box('Tank ground skid',(x,0,.023),(.10,.54,.046),p['rubber'],.018)
    box('Portable water tank body',(0,.014,.429),(.616,.51,.718),p['teal'],.070)
    for x in [-.245,.245]:
        box('Molded front corner reinforcement',(x,-.222,.43),(.054,.026,.57),p['teal'],.014)
        box('Molded rear corner reinforcement',(x,.252,.43),(.054,.027,.57),p['teal'],.014)
    # Actual hand basin is centered slightly forward above the tank shoulder.
    b=basin('Thick molded recessed hand basin',p['cream']);b.location.y=-.044
    ring('Drain flange',(0,-.044,.819),.043,.026,.012,p['steel'],segments=48)
    for offset in [-.018,0,.018]:rod('Drain strainer crossbar',(-math.sqrt(.026**2-offset**2),-.044+offset,.825),(math.sqrt(.026**2-offset**2),-.044+offset,.825),.0027,p['steel'],12,.0002)
    # Back shelf joins the basin lip, bearing a faucet and exactly two separate dispensers.
    box('Rear accessory mounting shelf',(0,.211,.936),(.592,.116,.034),p['cream'],.016)
    cyl('Faucet mounting escutcheon',(0,.205,.966),.038,.025,p['steel'],verts=48,bev=.004)
    pts=[(0,.205,.969),(0,.205,1.086)]
    for i in range(1,13):
        a=math.pi*i/12;pts.append((0,.135+.070*math.cos(a),1.086+.070*math.sin(a)))
    pts.extend([(0,.065,1.064),(0,.065,1.048)])
    tube('Gooseneck handwash faucet',pts,.012,p['steel'],3)
    cyl('Faucet aerator tip',(0,.065,1.044),.016,.022,p['steel'],verts=32,bev=.002)
    ring('Open faucet outlet',(0,.065,1.031),.013,.009,.007,p['dark'],segments=32)
    for x in [-.204,.204]:
        box('Soap bottle mounting shoe',(x,.209,.974),(.107,.103,.038),p['dark'],.011)
        box('Separate soap dispenser bottle',(x,.209,1.062),(.096,.081,.151),p['soap'],.020)
        box('Unbranded soap indicator panel',(x,.166,1.062),(.052,.004,.074),p['teal'],.007)
        cyl('Soap bottle neck',(x,.209,1.148),.024,.025,p['soap'],verts=32,bev=.003)
        cyl('Dispenser pump stem',(x,.209,1.173),.009,.031,p['steel'],verts=24,bev=.001)
        box('Soap pump head',(x,.191,1.192),(.039,.078,.018),p['dark'],.007)
        box('Soap outlet nozzle',(x,.144,1.184),(.020,.032,.011),p['dark'],.003)
    # Foot-operated diaphragm pump and positive attachment details.
    box('Foot-pump recessed surround',(0,-.264,.154),(.231,.035,.161),p['dark'],.021)
    cyl('Pump diaphragm housing',(0,-.297,.135),.070,.037,p['rubber'],'Y',48,.005)
    for x in [-.074,.074]:box('Pedal pivot lug',(x,-.30,.12),(.019,.075,.038),p['zinc'],.004)
    cyl('Pedal pivot pin',(0,-.317,.121),.009,.177,p['steel'],'X',24,.0008)
    box('Foot pump pedal',(0,-.365,.112),(.19,.158,.025),p['dark'],.012,rot=(math.radians(8),0,0))
    for i in range(5):box('Pedal grip ridge',(0,-.414+i*.023,.128+(i*.023)*math.tan(math.radians(8))),(.153,.008,.006),p['rubber'],.002)
    rod('Visible foot pump linkage',(0,-.304,.139),(0,-.353,.135),.012,p['zinc'],24)
    # Distinct rear servicing: gasketed hatch, hinges, latches and two capped couplings.
    box('Rear service hatch gasket',(0,.274,.458),(.443,.015,.438),p['rubber'],.031)
    box('Rear removable service hatch',(0,.284,.458),(.419,.022,.412),p['teal'],.028)
    for x in [-.16,.16]:
        cyl('Service quarter turn latch',(x,.301,.565),.014,.008,p['dark'],'Y',24,.001)
        box('Service latch key slot',(x,.306,.565),(.015,.002,.003),p['steel'],0)
    for z in [.321,.504]:cyl('Service hatch hinge',(-.212,.296,z),.010,.07,p['zinc'],verts=24,bev=.001)
    for x,z in [(-.114,.749),(.114,.165)]:
        cyl('Rear capped tank service port',(x,.283,z),.033,.044,p['dark'],'Y',40,.004)
        cyl('Tank port cap',(x,.310,z),.039,.018,p['cream'],'Y',40,.003)
        for a in range(6):
            aa=a*math.tau/6;box('Service cap grip rib',(x+.035*math.cos(aa),.322,z+.035*math.sin(aa)),(.010,.012,.010),p['cream'],.002)
    for x in [-.323,.323]:
        for y in [.09,.196]:box('Side carrying handle mounting boss',(x,y,.676),(.029,.034,.044),p['teal'],.009)
        tube('Side tank carrying grip',[(x,.09,.677),(x*1.07,.104,.677),(x*1.07,.183,.677),(x,.196,.677)],.013,p['dark'],2)
    return ('city-portable-handwash-station','足踏みポンプ式の屋外手洗いステーション','Portable foot-pump handwash station','屋外イベントや公園作業場所に置く可搬型手洗い設備の静的モデル。成形タンク、実形状のくぼんだ洗面鉢と排水口、曲がり蛇口、独立した二つの石けんディスペンサー、足踏みペダル、運搬握り、背面の点検蓋・給排水キャップを備えます。トイレや飲水器ではなく、水・石けんの内容物は含みません。給排水動作・衛生性能・飲用適合性は検証していません。','A static portable handwash unit for outdoor events and park worksites, with a molded tank, genuinely recessed basin and drain, gooseneck faucet, two separate soap dispensers, foot pedal, carrying grips, rear access hatch and capped service ports. This is not a toilet or drinking fountain; water and soap contents are not included. Pumping, drainage, hygiene performance and potable-water suitability have not been validated.',['handwash','basin','foot-pump','outdoor','手洗い'])


BUILDERS=[binocular_viewer,boot_cleaner,barbecue,handwash]
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-003/assets');ap.add_argument('--only',default='');a=ap.parse_args(args)
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    for fn in BUILDERS:
        reset();spec=fn()
        if a.only and spec[0]!=a.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/civic_service.py',azimuth=55 if fn==binocular_viewer else -55,elevation=27 if fn in [barbecue,handwash] else 24)
