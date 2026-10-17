"""Four original generic food-service appliance props, CC BY 4.0, Xenoah.
Portable bpy geometry only. Static appearance, not working or certified equipment.
Author Z-up metres; unchanged common.py exports metre-valued Y-up GLB and STL.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(steel=mat('Satin stainless appearance',(.57,.64,.67),.78,.28),
        bright=mat('Bright turned metal',(.72,.78,.80),.88,.23),
        alloy=mat('Cast aluminum appearance',(.43,.50,.54),.67,.35),
        enamel=mat('Warm ivory enamel',(.72,.73,.66),.12,.35),
        dark=mat('Graphite mechanical fittings',(.038,.052,.061),.27,.46),
        rubber=mat('Dark molded grips and pads',(.018,.026,.030),0,.76),
        iron=mat('Dark cast griddle appearance',(.073,.088,.091),.56,.48),
        red=mat('Muted red control cap',(.59,.055,.035),0,.40),
        green=mat('Green unlit indicator lens',(.035,.24,.11),0,.31),
        amber=mat('Amber unlit indicator lens',(.67,.31,.035),0,.31))


def cyl(name,pos,radius,depth,material,axis='Z',n=32,bevel=.0015):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name,a,b,radius,material,n=16):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,radius,(b-a).length,material,n=n,bevel=min(.0007,radius*.09))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def path(name,points,radius,material,closed=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=radius;c.bevel_resolution=2;c.use_fill_caps=not closed
    s=c.splines.new('POLY');s.points.add(len(points)-1);s.use_cyclic_u=closed
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material);return o


def screw(name,pos,material,axis='Z',r=.006):
    return cyl(name,pos,r,.004,material,axis,n=8,bevel=.00035)


def ring(name,pos,major,minor,material,axis='Z',n=64,m=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,major_radius=major,minor_radius=minor,location=pos)
    o=bpy.context.object
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    return finish(o,name,material,smooth=True)


def lathe(name,profile,pos,material,n=64):
    """Closed radial section, supporting unique axis poles and a real bowl cavity."""
    vs=[];rings=[]
    for r,z in profile:
        if abs(r)<1e-10:rings.append([len(vs)]);vs.append((0,0,z))
        else:
            ids=[]
            for j in range(n):ids.append(len(vs));vs.append((r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z))
            rings.append(ids)
    fs=[]
    for a,b in zip(rings,rings[1:]+rings[:1]):
        if len(a)==len(b)==1:continue
        for j in range(n):
            if len(a)==1:fs.append((a[0],b[(j+1)%n],b[j]))
            elif len(b)==1:fs.append((a[j],a[(j+1)%n],b[0]))
            else:fs.append((a[j],a[(j+1)%n],b[(j+1)%n],b[j]))
    o=mesh(name,vs,fs,material,smooth=True);o.location=pos
    # Flat axial caps remain flat. Curved wall segments have smooth normals.
    for f in o.data.polygons:
        zz=[o.data.vertices[i].co.z for i in f.vertices]
        f.use_smooth=max(zz)-min(zz)>1e-7
    return o


def prism_x(name,profile,width,material,bevel=.004):
    vs=[(x,y,z) for x in [-width/2,width/2] for y,z in profile];n=len(profile)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def prism_y(name,profile,y0,y1,material,bevel=.003):
    vs=[(x,y,z) for y in [y0,y1] for x,z in profile];n=len(profile)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def arc_guard(name,cx,cy,cz,inner,outer,depth,start,end,material,n=56):
    """Closed thick partial annulus in the X/Z plane, with open central aperture."""
    vs=[]
    for r,y in [(inner,cy-depth/2),(outer,cy-depth/2),(outer,cy+depth/2),(inner,cy+depth/2)]:
        for j in range(n+1):
            a=start+(end-start)*j/n;vs.append((cx+r*math.cos(a),y,cz+r*math.sin(a)))
    m=n+1;fs=[]
    for k in range(4):
        for j in range(n):fs.append((k*m+j,k*m+j+1,((k+1)%4)*m+j+1,((k+1)%4)*m+j))
    fs += [(0,m,2*m,3*m),(n,3*m+n,2*m+n,m+n)]
    o=mesh(name,vs,fs,material,bevel=.0012)
    return o


def rounded_rect(width,depth,radius,n=6):
    pts=[]
    for cx,cy,angle in [(width/2-radius,depth/2-radius,0),(-width/2+radius,depth/2-radius,90),(-width/2+radius,-depth/2+radius,180),(width/2-radius,-depth/2+radius,270)]:
        for j in range(n+1):
            a=math.radians(angle+j*90/n);pts.append((cx+radius*math.cos(a),cy+radius*math.sin(a)))
    return pts


def vat(name,profiles,pos,material):
    """Outer floor, outer wall, rolled rim, inner wall and inner floor are one shell."""
    vs=[];n=0
    for w,d,r,z in profiles:
        pts=rounded_rect(w,d,r);n=len(pts);vs.extend((x,y,z) for x,y in pts)
    fs=[]
    for k in range(len(profiles)-1):
        fs.extend((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for j in range(n))
    fs += [tuple(reversed(range(n))),tuple(range((len(profiles)-1)*n,len(profiles)*n))]
    o=mesh(name,vs,fs,material);o.location=pos;return o


def griddle(name,material,pos,rotation=0,flip=False):
    """One closed plate with 25 recessed cells and a connected raised lattice."""
    q=[-.150,-.140,-.092,-.082,-.034,-.024,.024,.034,.082,.092,.140,.150]
    n=len(q);vs=[(x,y,z) for z in [.024,-.026] for y in q for x in q];fs=[]
    for j in range(n-1):
        for i in range(n-1):
            a=j*n+i;quad=(a,a+1,a+n+1,a+n)
            if i%2==1 and j%2==1:
                low=[]
                for v in quad:
                    low.append(len(vs));x,y,z=vs[v];vs.append((x,y,.002))
                fs.append(tuple(low))
                for k in range(4):fs.append((quad[k],quad[(k+1)%4],low[(k+1)%4],low[k]))
            else:fs.append(quad)
            fs.append(tuple(reversed([v+n*n for v in quad])))
    border=list(range(n))+[j*n+n-1 for j in range(1,n)]+[(n-1)*n+i for i in range(n-2,-1,-1)]+[j*n for j in range(n-2,0,-1)]
    fs.extend((a,a+n*n,b+n*n,b) for a,b in zip(border,border[1:]+border[:1]))
    if flip:vs=[(x,y,-z) for x,y,z in vs]
    o=mesh(name,vs,fs,material,bevel=.001);o.location=pos;o.rotation_euler[0]=rotation;return o


def controls_knob(name,pos,radius,p,axis='Y'):
    x,y,z=pos;cyl(name+' bright bezel',pos,radius+.006,.007,p['steel'],axis,n=40)
    dy=-.012 if axis=='Y' else 0
    cyl(name+' molded grip',(x,y+dy,z),radius,.025,p['rubber'],axis,n=32,bevel=.003)
    if axis=='Y':box(name+' index notch',(x,y-.026,z+radius*.58),(.004,.002,.014),p['enamel'],.0005)


def mixer():
    p=palette()
    for x in [-.174,.174]:
        for y in [-.256,.217]:cyl('Mixer contact foot',(x,y,.021),.038,.042,p['rubber'],n=32,bevel=.006)
    box('Broad rounded mixer plinth',(0,-.020,.078),(.460,.590,.084),p['enamel'],.027)
    box('Underside removable base plate',(0,-.020,.033),(.376,.493,.012),p['alloy'],.013)
    for x in [-.16,.16]:
        for y in [-.21,.17]:screw('Under-base assembly screw',(x,y,.025),p['dark'],r=.006)
    prism_x('Tapered rear mixer pedestal',[(.080,.108),(.265,.108),(.277,.647),(.235,.725),(.112,.725),(.073,.643)],.224,p['enamel'],.020)
    box('Overhanging drive arm',(0,.017,.710),(.256,.452,.132),p['enamel'],.035)
    box('Drive arm upper separation seam',(0,.028,.760),(.235,.394,.009),p['alloy'],.003)
    cyl('Planetary head lower housing',(0,-.106,.632),.102,.053,p['alloy'],n=64,bevel=.010)
    cyl('Static attachment drive collar',(0,-.106,.600),.032,.043,p['dark'],n=40,bevel=.004)
    cyl('Fixed beater attachment shaft',(0,-.106,.501),.012,.171,p['steel'],n=24)
    path('Flat beater closed outer loop',[(-.012,-.106,.490),(-.075,-.106,.459),(-.102,-.106,.382),(-.070,-.106,.319),(0,-.106,.297),(.070,-.106,.319),(.102,-.106,.382),(.075,-.106,.459),(.012,-.106,.490)],.009,p['steel'],closed=True)
    rod('Flat beater center web',(0,-.106,.470),(0,-.106,.307),.007,p['steel'])
    rod('Flat beater diagonal web',(-.075,-.106,.456),(.074,-.106,.324),.006,p['steel'])
    for side in [-1,1]:
        path('Bowl lifting cradle side arm',[(side*.092,.180,.324),(side*.182,.125,.324),(side*.218,-.105,.324)],.017,p['alloy'])
        cyl('Bowl cradle mounting lug',(side*.202,-.105,.341),.025,.027,p['steel'],'X',n=24)
    profile=[(0,.234),(.088,.234),(.132,.250),(.166,.290),(.192,.367),(.210,.479),(.214,.516),(.220,.522),(.220,.530),(.215,.536),(.207,.536),(.203,.527),(.202,.515),(.198,.478),(.181,.368),(.156,.298),(.124,.272),(.084,.262),(0,.262)]
    lathe('Thick rolled-rim open mixer bowl',profile,(0,-.105,0),p['bright'],n=72)
    for side in [-1,1]:
        path('Bowl lifting handle',[(side*.199,-.165,.464),(side*.255,-.165,.464),(side*.270,-.145,.464),(side*.270,-.065,.464),(side*.255,-.045,.464),(side*.199,-.045,.464)],.008,p['steel'])
        for y in [-.165,-.045]:box('Bowl handle root bracket',(side*.207,y,.464),(.020,.024,.025),p['steel'],.003)
    # A 270-degree open guard has a deliberate front-right access gap.
    for z in [.547,.652]:
        pts=[(.237*math.cos(math.radians(-5+i*270/72)),-.105+.237*math.sin(math.radians(-5+i*270/72)),z) for i in range(73)]
        path('Open partial bowl guard perimeter',pts,.0045,p['steel'])
    for i in range(10):
        a=math.radians(-5+i*30);x=.237*math.cos(a);y=-.105+.237*math.sin(a)
        rod('Open guard upright wire',(x,y,.549),(x,y,.650),.0034,p['steel'],n=12)
    box('Guard hinge mounting bracket',(-.162,.071,.637),(.050,.041,.059),p['alloy'],.005)
    cyl('Guard vertical hinge pin',(-.169,.065,.606),.010,.126,p['dark'],n=20)
    box('Side speed-control plate',(.119,.179,.536),(.011,.097,.157),p['dark'],.007)
    for z,mm in [(.575,p['green']),(.525,p['red'])]:cyl('Side control button',(.131,.179,z),.017,.018,mm,'X',n=24,bevel=.003)
    cyl('Bowl lift side pivot',(.130,.195,.375),.028,.026,p['steel'],'X',n=32)
    path('Fixed bowl lift lever',[(.148,.195,.375),(.177,.237,.417),(.181,.250,.480)],.010,p['alloy'])
    rod('Lift lever dark sleeve',(.181,.250,.453),(.181,.250,.503),.017,p['rubber'],n=24)
    box('Rear motor access panel',(0,.280,.465),(.172,.016,.250),p['alloy'],.010)
    for x in [-.065,.065]:
        for z in [.362,.570]:screw('Rear panel screw',(x,.290,z),p['dark'],'Y')
    for z in [.424,.445,.466,.487,.508]:box('Rear cooling grille dark slot',(0,.290,z),(.122,.005,.007),p['dark'],.001)
    box('Rear recessed power-entry surround',(0,.280,.221),(.064,.020,.046),p['dark'],.005)
    box('Rear unconnected power-entry face',(0,.292,.221),(.041,.006,.027),p['rubber'],.002)
    return ('city-planetary-food-mixer','開放ガードと深いボウル付きの業務用ミキサー','Planetary food mixer with open guard and deep bowl',
        'カフェやベーカリーの作業台に置く汎用ミキサーの静的プロップ。丸みのある台座と後部支柱、前方へ張り出す駆動部、内側まで厚みを持つ空のボウル、ボウル支持アーム、固定した平面ビーター、前右側が開いた部分ワイヤーガード、昇降レバー風の形状と操作部、背面点検パネルを造形しています。ボウル底と内壁は実際の空洞を囲み、食品や液体は含みません。ガード開口と固定された部品は外観表現であり、撹拌・昇降・電気機能、食品接触の適合性、機械安全を示すものではありません。',
        'A generic static mixer prop for a cafe or bakery work counter, with a rounded base and rear pedestal, overhanging drive head, empty thick-walled deep bowl, bowl-support cradle, fixed flat beater, partial wire guard open at the front right, lift-lever detail, controls and rear access panel. The bowl floor and inner wall surround a genuine cavity; no food or liquid is included. The guard opening and fixed parts are appearance cues only, with no mixing, lifting or electrical function, food-contact suitability or mechanical-safety claim.',
        ['food-service','mixer','counter-appliance','厨房'])


def slicer():
    p=palette()
    for x in [-.237,.237]:
        for y in [-.184,.203]:cyl('Slicer contact foot',(x,y,.021),.032,.042,p['rubber'],n=28,bevel=.005)
    box('Slicer rounded base casting',(0,.010,.075),(.585,.475,.080),p['alloy'],.021)
    box('Slicer underside closure plate',(0,.010,.032),(.490,.380,.014),p['dark'],.007)
    for x in [-.205,.205]:
        for y in [-.145,.165]:screw('Base plate underside screw',(x,y,.023),p['steel'],r=.006)
    prism_x('Raised blade motor pedestal',[(.022,.109),(.221,.109),(.213,.360),(.141,.452),(.052,.401)],.190,p['alloy'],.013)
    cyl('Rear motor enclosure',(-.077,.151,.382),.103,.196,p['alloy'],'Y',n=56,bevel=.011)
    cyl('Rear motor end panel',(-.077,.256,.382),.090,.016,p['dark'],'Y',n=48,bevel=.005)
    for x in [-.120,-.099,-.078,-.057,-.036]:box('Motor end grille rib',(x,.267,.382),(.009,.008,.098),p['alloy'],.002)
    cx=-.078;cz=.391
    cyl('Rear circular blade carrier',(cx,.047,cz),.183,.029,p['alloy'],'Y',n=72,bevel=.004)
    cyl('Circular slicer disc static blunt geometry',(cx,.026,cz),.177,.008,p['bright'],'Y',n=96,bevel=.001)
    cyl('Central circular blade cover',(cx,.018,cz),.143,.019,p['steel'],'Y',n=64,bevel=.006)
    ring('Raised central guard rim',(cx,.006,cz),.141,.004,p['bright'],'Y',n=64,m=8)
    cyl('Blade cover center fastener',(cx,.001,cz),.022,.014,p['dark'],'Y',n=32,bevel=.002)
    arc_guard('Upper partial circumference guard',cx,.022,cz,.180,.197,.039,math.radians(12),math.radians(244),p['steel'])
    # Parallel offset gauge face is an explicit closed polygon, not a painted disc.
    prism_y('Offset vertical thickness gauge plate',[(-.300,.236),(-.300,.537),(-.186,.555),(-.126,.514),(-.116,.247)],-.019,-.002,p['steel'],.005)
    box('Gauge back mounting spine',(-.238,.051,.345),(.045,.105,.202),p['alloy'],.007)
    rod('Thickness gauge adjustment stem',(-.250,-.142,.182),(-.250,.057,.182),.013,p['steel'],n=24)
    controls_knob('Thickness adjustment wheel',(-.250,-.163,.177),.037,p)
    for x in [-.242,.257]:
        box('Carriage rail support block',(x,-.175,.135),(.047,.068,.065),p['alloy'],.006)
        screw('Guide support top fixing',(x,-.175,.171),p['dark'],r=.006)
    rod('Exposed carriage slide rail',(-.262,-.175,.145),(.279,-.175,.145),.014,p['bright'],n=32)
    cyl('Carriage sliding sleeve',(.126,-.175,.145),.026,.141,p['dark'],'X',n=32,bevel=.003)
    box('Carriage upright foot',(.128,-.175,.205),(.071,.074,.112),p['alloy'],.006)
    pitch=-.15
    box('Angled empty carriage tray',(.119,-.116,.259),(.318,.292,.018),p['steel'],.006,(0,pitch,0))
    box('Carriage front raised lip',(.119,-.264,.263),(.318,.017,.039),p['steel'],.004,(0,pitch,0))
    box('Carriage far raised lip',(.119,.027,.263),(.318,.017,.039),p['steel'],.004,(0,pitch,0))
    for x in [.029,.075,.121,.167,.213]:box('Tray shallow guide bead',(x,-.119,.273+(x-.119)*.15),(.006,.241,.007),p['bright'],.001,(0,pitch,0))
    for x in [-.023,.275]:
        rod('Food pusher guide support',(x,-.112,.275),(x,-.112,.425),.009,p['steel'],n=20)
    rod('Food pusher slide bar',(-.034,-.112,.423),(.294,-.112,.423),.011,p['bright'],n=24)
    cyl('Food pusher sliding boss',(.224,-.112,.423),.023,.047,p['dark'],'X',n=28,bevel=.003)
    box('Static carriage food pusher face',(.204,-.112,.356),(.020,.211,.123),p['alloy'],.007)
    for y in [-.185,-.148,-.111,-.074,-.037]:rod('Pusher short blunt contact bead',(.191,y,.312),(.191,y,.392),.004,p['steel'],n=12)
    rod('Pusher handgrip stem',(.236,-.112,.427),(.294,-.112,.454),.012,p['steel'],n=20)
    sphere('Rounded pusher handgrip',(.302,-.112,.458),(.029,.031,.030),p['rubber'],segments=24,rings=12)
    path('Carriage front push handle',[(.080,-.244,.236),(.083,-.315,.235),(.224,-.315,.255),(.228,-.243,.258)],.012,p['alloy'])
    rod('Carriage push handle grip',(.100,-.315,.238),(.208,-.315,.253),.020,p['rubber'],n=28)
    box('Upper enclosed dressing housing',(cx,.059,.596),(.128,.092,.052),p['dark'],.010)
    box('Dressing housing metal lid',(cx,.059,.625),(.121,.086,.012),p['alloy'],.005)
    for x in [cx-.040,cx+.040]:screw('Upper housing lid screw',(x,.059,.633),p['dark'],r=.005)
    cyl('Small upper adjustment cap',(cx,.113,.596),.016,.019,p['rubber'],'Y',n=24,bevel=.003)
    box('Front switch surround',(-.121,-.232,.077),(.079,.011,.039),p['dark'],.005)
    for x,m in [(-.143,p['green']),(-.102,p['red'])]:cyl('Slicer front control',(x,-.242,.077),.010,.011,m,'Y',n=20,bevel=.002)
    box('Rear power-entry surround',(.125,.249,.080),(.064,.014,.039),p['dark'],.004)
    for x in [-.245,.245]:screw('Rear base housing screw',(x,.252,.077),p['dark'],'Y')
    return ('city-countertop-food-slicer','送り台と厚み調整板付きの卓上フードスライサー','Countertop food slicer with carriage and gauge plate',
        'デリカテッセンや飲食店の作業カウンター向けの卓上スライサー模型。部分外周ガードと中央カバーで囲んだ固定円盤、別体の厚み調整板とノブ、レールとスリーブで支えた傾斜送り台、押さえ板とガイド棒、前ハンドル、後部モーター外装、上部小カバーを造形しています。円盤だけではなく、食材を置く空の送り台と支持構造が一式に含まれます。食材、刃の可動・切断能力、衛生・食品接触適合性、電気・機械安全の検証は含みません。',
        'A countertop slicer prop for a delicatessen or restaurant work counter, with a fixed circular disc, partial perimeter guard and center cover, separate thickness gauge plate and knob, inclined empty carriage supported by a rail and sleeve, food-pusher face and guide bar, front handle, rear motor enclosure and small upper cover. It is a complete supported carriage assembly rather than an isolated disc. Food, blade motion, cutting capability, hygiene or food-contact compliance, and electrical or mechanical-safety validation are not supplied.',
        ['food-service','food-slicer','counter-appliance','厨房'])


def fryer():
    p=palette()
    for x in [-.185,.185]:
        for y in [-.225,.225]:
            cyl('Fryer cabinet adjustable-looking leg',(x,y,.081),.022,.122,p['steel'],n=28,bevel=.003)
            cyl('Fryer leg contact shoe',(x,y,.020),.032,.040,p['rubber'],n=28,bevel=.004)
            cyl('Fryer leg upper collar',(x,y,.138),.032,.022,p['alloy'],n=28)
    box('Fryer lower cabinet body',(0,0,.411),(.465,.566,.548),p['steel'],.009)
    box('Fryer cabinet underpan',(0,0,.145),(.433,.530,.022),p['alloy'],.005)
    for x in [-.184,.184]:
        for y in [-.218,.218]:screw('Underpan fixing head',(x,y,.133),p['dark'],r=.007)
    # Top is a thick open vat; no lid, solid cover, oil plane or hidden fill block.
    vat('Deep empty fryer vat',[(.444,.483,.032,.665),(.444,.483,.032,.874),(.455,.494,.035,.886),(.455,.494,.035,.897),(.421,.460,.030,.897),(.409,.448,.030,.882),(.377,.412,.039,.725)],(0,-.025,0),p['bright'])
    for x in [-.224,.224]:box('Upper cabinet side support panel',(x,0,.767),(.017,.565,.192),p['steel'],.004)
    box('Fryer upper front apron',(0,-.282,.773),(.453,.018,.188),p['steel'],.005)
    box('Front door dark perimeter reveal',(0,-.291,.410),(.421,.014,.494),p['dark'],.005)
    box('Closed fryer service door',(0,-.302,.410),(.408,.018,.480),p['steel'],.007)
    path('Front cabinet pull handle',[(-.090,-.317,.600),(-.090,-.345,.600),(.090,-.345,.600),(.090,-.317,.600)],.010,p['alloy'])
    for z in [.245,.565]:box('Cabinet door hinge',(.211,-.311,z),(.015,.024,.061),p['alloy'],.003)
    for x in [-.095,.095]:controls_knob('Fryer front rotary control',(x,-.298,.793),.026,p)
    cyl('Unlit front status lamp',(0,-.310,.839),.009,.011,p['amber'],'Y',n=24,bevel=.002)
    box('Raised rear control backsplash',(0,.251,.978),(.472,.088,.288),p['steel'],.012)
    box('Backsplash upper cap',(0,.251,1.127),(.480,.096,.018),p['alloy'],.005)
    box('Rear backsplash service panel',(0,.302,.973),(.394,.017,.209),p['alloy'],.008)
    for x in [-.173,.173]:
        for z in [.890,1.056]:screw('Rear backsplash screw',(x,.313,z),p['dark'],'Y',r=.006)
    for x in [-.132,-.088,-.044,0,.044,.088,.132]:box('Rear backsplash louver slot',(x,.313,.992),(.021,.006,.067),p['dark'],.002)
    rod('Rear basket resting crossbar',(-.180,.198,.989),(.180,.198,.989),.010,p['alloy'],n=24)
    for x in [-.177,.177]:rod('Basket rest short support',(x,.221,.947),(x,.198,.989),.010,p['alloy'],n=20)
    # Modest wire density preserves actual holes at all sides and the base.
    cx=0;cy=-.033;z0=.785;zt=.994;w=.326;d=.339
    for z,rr in [(z0,.0038),(zt,.005)]:path('Fryer basket perimeter wire',[(x,cy+y,z) for x,y in rounded_rect(w,d,.025,5)],rr,p['steel'],closed=True)
    for x in [-.132,-.088,-.044,0,.044,.088,.132]:
        path('Basket lengthwise U wire',[(x,cy-d/2,zt),(x,cy-d/2,z0+.014),(x,cy-d/2+.015,z0),(x,cy+d/2-.015,z0),(x,cy+d/2,z0+.014),(x,cy+d/2,zt)],.0025,p['steel'])
    for y in [-.133,-.089,-.045,-.001,.043,.087,.131]:
        path('Basket transverse U wire',[(-w/2,cy+y,zt),(-w/2,cy+y,z0+.014),(-w/2+.015,cy+y,z0),(w/2-.015,cy+y,z0),(w/2,cy+y,z0+.014),(w/2,cy+y,zt)],.0025,p['steel'])
    for z in [.855,.925]:path('Basket side horizontal restraint wire',[(x,cy+y,z) for x,y in rounded_rect(w,d,.025,5)],.0027,p['steel'],closed=True)
    for x in [-.105,.105]:
        path('Basket rear hooked support',[(x,cy+d/2,zt),(x,.177,1.017),(x,.205,1.017),(x,.216,1.006),(x,.216,.983),(x,.201,.978)],.005,p['steel'])
    for x in [-.041,.041]:
        path('Basket raised twin handle rail',[(x,cy-d/2,.971),(x,-.284,1.000),(x,-.420,1.103),(x,-.579,1.103)],.006,p['alloy'])
        box('Basket handle root clamp',(x,cy-d/2-.003,.976),(.021,.014,.049),p['steel'],.003)
    box('Basket long molded handle grip',(0,-.511,1.112),(.103,.177,.035),p['rubber'],.011)
    for y in [-.456,-.565]:screw('Basket handle top fastening',(0,y,1.131),p['alloy'],r=.005)
    box('Rear cabinet service panel',(0,.289,.424),(.375,.018,.435),p['alloy'],.006)
    for x in [-.158,.158]:
        for z in [.233,.614]:screw('Rear cabinet panel screw',(x,.301,z),p['dark'],'Y',r=.007)
    box('Rear unconnected inlet surround',(0,.304,.245),(.069,.017,.046),p['dark'],.005)
    return ('city-commercial-deep-fryer','開いた槽とワイヤーバスケット付きの業務用フライヤー','Commercial deep fryer with open vat and wire basket',
        '飲食店の厨房床に配置する独立キャビネット型フライヤーの静的プロップ。脚付きキャビネットと扉、厚い縁と底を備えた空の深い槽、穴が実際に開いたワイヤーバスケットと長い握り、背面の立上り部とバスケット受け、前操作部、背面点検パネルを造形しています。バスケットは槽内から上に出た固定位置で、油、食品、炎や熱表現は含みません。加熱・排油・温度制御・電気機能、食品接触適合性、衛生・防火・機械安全は実装または検証していません。',
        'A freestanding cabinet fryer prop for a restaurant kitchen floor, with raised legs and front service door, an empty deep vat with thick rim and floor, genuinely open wire basket and long grip, rear backsplash and basket rest, front controls and rear service panels. The basket is fixed partly above the vat; oil, food, flame and heat effects are absent. Heating, draining, temperature control and electrical function are not implemented, and food-contact suitability, hygiene, fire performance and mechanical safety are not validated.',
        ['food-service','deep-fryer','kitchen-appliance','厨房'])


def waffle():
    p=palette()
    for x in [-.125,.125]:
        for y in [-.142,.142]:cyl('Waffle iron contact foot',(x,y,.019),.026,.038,p['rubber'],n=28,bevel=.004)
    box('Waffle iron counter base',(0,-.003,.074),(.356,.404,.088),p['steel'],.012)
    box('Base underside access plate',(0,-.003,.034),(.293,.341,.013),p['alloy'],.006)
    for x in [-.108,.108]:
        for y in [-.128,.128]:screw('Underside access fixing',(x,y,.026),p['dark'],r=.005)
    box('Lower insulated housing',(0,-.006,.136),(.348,.348,.057),p['alloy'],.013)
    griddle('Lower closed recessed-cell griddle',p['iron'],(0,-.006,.180))
    # Back hinge axis is independent of the ground-centered placement origin.
    hinge=Vector((0,.165,.205));angle=-math.radians(102);R=Matrix.Rotation(angle,4,'X')
    def lid(co):return hinge+R.to_3x3()@Vector(co)
    def lidbox(name,co,size,material,bevel=.004):
        o=box(name,lid(co),size,material,bevel);o.rotation_euler[0]=angle;return o
    lidbox('Upper open metal housing',(0,-.165,.022),(.348,.348,.057),p['alloy'],.013)
    griddle('Upper closed recessed-cell griddle',p['iron'],lid((0,-.165,-.022)),angle,True)
    lidbox('Upper rear service panel',(0,-.165,.055),(.276,.278,.012),p['steel'],.007)
    for x in [-.112,.112]:
        for y in [-.277,-.053]:
            o=screw('Upper outer panel screw',lid((x,y,.064)),p['dark'],r=.005);o.rotation_euler[0]=angle
    for y in [-.220,-.185,-.150,-.115]:lidbox('Upper exterior cooling-slot detail',(0,y,.062),(.172,.010,.004),p['dark'],.001)
    for x in [-.131,.131]:
        box('Hinge lower support ear',(x,.162,.161),(.043,.060,.080),p['steel'],.006)
        rod('Lid hinge link',lid((x,-.044,.019)),(x,.165,.205),.017,p['alloy'],n=24)
    for x in [-.124,0,.124]:cyl('Back hinge barrel',(x,.165,.205),.023,.078,p['steel'],'X',n=32,bevel=.003)
    for x in [-.171,.171]:cyl('Hinge pin end cap',(x,.165,.205),.017,.015,p['dark'],'X',n=24,bevel=.002)
    for x in [-.126,.126]:
        path('Upper lifting handle support',[lid((x,-.302,.028)),lid((x,-.353,.061)),lid((x,-.402,.061))],.010,p['steel'])
    rod('Raised lid lifting handle crossbar',lid((-.134,-.402,.061)),lid((.134,-.402,.061)),.013,p['steel'],n=24)
    rod('Raised lid molded handgrip',lid((-.112,-.402,.061)),lid((.112,-.402,.061)),.021,p['rubber'],n=32)
    controls_knob('Waffle iron front control',(-.061,-.210,.079),.026,p)
    for x,mm in [(.052,p['green']),(.093,p['amber'])]:cyl('Unlit waffle iron indicator',(x,-.211,.083),.008,.009,mm,'Y',n=20,bevel=.002)
    box('Front control blank inset',(0,-.207,.077),(.296,.008,.056),p['dark'],.004)
    # Move the inset behind the controls, not over their front faces.
    for x in [-.139,.139]:screw('Front fascia fixing',(x,-.213,.078),p['steel'],'Y',r=.004)
    box('Rear power entry fitting',(0,.204,.076),(.062,.020,.042),p['dark'],.005)
    for x in [-.111,.111]:screw('Rear base fixing',(x,.203,.074),p['dark'],'Y',r=.005)
    return ('city-open-waffle-iron','二枚の格子プレートを開いた卓上ワッフルメーカー','Open countertop waffle iron with two gridded plates',
        'カフェや軽食店のカウンターに置く、上蓋を開いた角形ワッフルメーカー模型。厚い上下プレートの表面には立体的な格子と空の窪みを設け、下部筐体、後ろのヒンジ軸と支持耳、上蓋の持ち上げハンドル、前面ダイヤルと点灯していない表示部、裏面パネルを造形しています。開き角は固定され、食品、熱や蒸気の表現はありません。開閉・加熱・温度調整機能、食品接触適合性、衛生・電気・機械安全は実装または検証していません。',
        'A square waffle-iron prop for a cafe or snack counter, displayed with its upper lid fixed open. Both thick plates have modeled raised grids and empty recessed cells, supported by a lower enclosure, rear hinge pin and mounting ears, raised lid handle, front dial and unlit indicators, and underside access panel. The opening angle is fixed; food, heat and steam effects are absent. Opening, heating and temperature adjustment are not implemented, and food-contact suitability, hygiene, electrical and mechanical safety are not validated.',
        ['food-service','waffle-iron','counter-appliance','厨房'])


BUILDERS=[mixer,slicer,fryer,waffle]


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
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-025/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true',help='Reproduce GLB/STL/metadata without presentation images.')
    args=parser.parse_args(arg);out=Path(args.out);out=out if out.is_absolute() else ROOT/out
    if args.geometry_only:common.render=lambda *a,**k:None
    for builder in BUILDERS:
        reset();spec=builder()
        if args.only and spec[0]!=args.only:continue
        common.publish_asset(*spec,out,'scripts/city_expansion/food_service_appliances.py',azimuth=-55,elevation=30)
        if not args.geometry_only:underside(out/'_qa'/f'{spec[0]}-underside.png')
