"""Four original static active-park assets, CC BY 4.0, Xenoah.
Procedural geometry and constant-color PBR, no downloaded geometry or textures.
Not certified playground, exercise or competition equipment; not construction plans.
Run with Blender 4.3.2, CITY_RENDER_SAMPLES=48 and --threads 4.
"""
import sys, math, argparse
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(steel=mat('Satin stainless structural hardware',(.43,.49,.51),.78,.32),
        zinc=mat('Galvanized steel foot hardware',(.29,.35,.37),.7,.46),
        navy=mat('Deep petrol powder coat',(.026,.11,.15),.24,.44),
        teal=mat('Teal coated climbing tubes',(.025,.35,.34),.2,.48),
        amber=mat('Amber protective hub covers',(.88,.36,.055),0,.51),
        dark=mat('Charcoal rubber pads',(.022,.029,.032),0,.77),
        skin=mat('Muted blue grey riding composite',(.22,.35,.38),.08,.66),
        deck=mat('Charcoal anti slip deck',(.10,.14,.155),.08,.79),
        white=mat('Ivory white goal powder coat',(.83,.86,.82),.12,.41),
        rope=mat('Cream polymer goal net',(.72,.77,.66),0,.83))


def cyl(name,p,r,d,m,axis='Z',sides=24,bevel=.002):
    o=cylinder(name,p,r,d,m,vertices=sides,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o


def rod(name,a,b,r,m,sides=16,bevel=0):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,r,(b-a).length,m,sides=sides,bevel=bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def beam(name,a,b,w,h,m,bevel=.004):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(w,h,(b-a).length),m,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def fastener(name,p,m,axis='Z',r=.009):
    cyl(name+' washer',p,r*1.55,r*.28,m,axis,20,.0004)
    q=list(p);q['XYZ'.index(axis)]+=r*.45
    cyl(name+' hex head',q,r,r*.72,m,axis,6,.0005)


def oriented_fastener(name,p,normal,m,r=.012):
    p,n=Vector(p),Vector(normal).normalized()
    rod(name+' washer',p-n*.001,p+n*.003,r*1.6,m,20,0)
    rod(name+' hex head',p+n*.003,p+n*.012,r,m,6,.0005)


def sweep(name,points,r,m,sides=12):
    """Closed round tube with transport frames; cap normals are flat."""
    pp=[Vector(p) for p in points];verts=[];faces=[];old=None;u=None
    for i,p in enumerate(pp):
        t=(pp[min(i+1,len(pp)-1)]-pp[max(i-1,0)]).normalized()
        if old is None:
            helper=Vector((0,0,1)) if abs(t.z)<.9 else Vector((0,1,0))
            u=t.cross(helper).normalized()
        else:
            u=old.rotation_difference(t)@u;u=(u-t*u.dot(t)).normalized()
        v=t.cross(u).normalized();old=t
        for j in range(sides):verts.append(tuple(p+r*(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides))))
    for i in range(len(pp)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces += [tuple(reversed(range(sides))),tuple(range((len(pp)-1)*sides,len(pp)*sides))]
    o=mesh(name,verts,faces,m,0,True)
    for f in o.data.polygons:
        if len(f.vertices)!=4:f.use_smooth=False
    return o


def extrude_yz(name,outline,x,width,m,bevel=0):
    n=len(outline);verts=[(xx,y,z) for xx in [x-width/2,x+width/2] for y,z in outline]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,m,bevel)


def parallel_bars():
    p=palette()
    # Two long grip rails and four genuinely grounded load paths.
    for y in [-.36,.36]:
        rod('Long stainless grip rail',(-1.30,y,1.27),(1.30,y,1.27),.029,p['steel'],32,.002)
        for x in [-1.30,1.30]:sphere('Rounded grip rail terminal',(x,y,1.27),(.029,.029,.029),p['steel'],20,10)
        for x in [-.96,.96]:
            box('Ground anchor plate',(x,y,.015),(.26,.24,.03),p['zinc'],.012)
            cyl('Vertical coated support',(x,y,.627),.043,1.198,p['navy'],sides=32,bevel=.003)
            cyl('Post ground sleeve',(x,y,.076),.052,.11,p['navy'],sides=32,bevel=.004)
            cyl('Rail saddle riser',(x,y,1.223),.035,.077,p['steel'],sides=24,bevel=.003)
            cyl('Amber joint collar',(x,y,1.168),.050,.063,p['amber'],sides=32,bevel=.006)
            for dx in [-.089,.089]:
                for dy in [-.078,.078]:fastener('Base anchor',(x+dx,y+dy,.034),p['steel'],r=.010)
            # Four triangular gussets join each post sleeve to its foot plate.
            for sign in [-1,1]:
                outline=[(y+sign*.042,.030),(y+sign*.103,.030),(y+sign*.042,.195)]
                extrude_yz('Post foot lateral gusset',outline,x,.012,p['navy'],.002)
                o=extrude_yz('Post foot longitudinal gusset',[(sign*.042,.030),(sign*.106,.030),(sign*.042,.195)],0,.012,p['navy'],.002)
                o.rotation_euler[2]=math.pi/2;o.location.x=x;o.location.y=y
            for dy in [-.049,.049]:
                oriented_fastener('Collar captive bolt',(x,y+dy,1.168),(0,math.copysign(1,dy),0),p['steel'],.009)
            # Tiny saddle ring visibly intersects both post and rail, not a floating decoration.
            cyl('Grip rail support sleeve',(x,y,1.270),.034,.115,p['steel'],'X',32,.003)
    return ('city-outdoor-parallel-bars','屋外運動用の平行バー','Outdoor exercise parallel bars',
        '公園の運動エリアに配置する2本組の平行バー。長いステンレス風グリップ、4本の支柱、サドル接合部、保護カラー、三角補強板、接地プレートとアンカーボルトを造形。利用者、地面、基礎、落下保護舗装や他の運動器具は含みません。静的装飾モデルであり、耐荷重・運動器具安全規格・施工の認証や検証を受けた製品ではなく、施工指示にも使用できません。',
        'A paired exercise-bar assembly for park fitness areas, with long stainless-look grip rails, four uprights, saddle joints, protective collars, triangular foot gussets, base plates and anchor hardware. No people, ground, foundations, impact surfacing or other exercise equipment. Static decorative geometry, not certified or validated for load capacity, exercise-equipment safety or installation, and not construction instructions.',
        ['park','exercise','parallel-bars','fitness','平行棒'])


def quarter_pipe():
    p=palette();R=1.65;theta=math.radians(75);width=2.40
    def yz(t):return (-1.58+R*math.sin(t),.043+R*(1-math.cos(t)))
    endy,top=yz(theta);back=endy+.76
    # Closed riding skin with top and underside surfaces. Continuous curve, not steps.
    n=40;vs=[]
    for i in range(n+1):
        t=theta*i/n;y,z=yz(t)
        for x,below in [(-width/2,False),(width/2,False),(-width/2,True),(width/2,True)]:
            # Offset inward normal to preserve sheet thickness around the transition.
            vs.append((x,y+(.027*math.sin(t) if below else 0),z-(.027*math.cos(t) if below else 0)))
    fs=[]
    for i in range(n):
        a=i*4;b=(i+1)*4
        fs.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,a+2+4,a+2),(a+1,a+3,b+3,b+1)])
    fs += [(0,2,3,1),(4*n,4*n+1,4*n+3,4*n+2)]
    skin=mesh('Continuous curved riding skin',vs,fs,p['skin'],0,True)
    for i,f in enumerate(skin.data.polygons):
        if i>=4*n or i%4>=2:f.use_smooth=False
    # Flush wedge toe plate eliminates a blunt vertical lip at the entry.
    extrude_yz('Thin tapered transition lip',[(-1.76,.008),(-1.76,.015),(-1.548,.046),(-1.548,.014)],0,2.43,p['steel'],.001)
    for x in [-1.10,-.55,0,.55,1.10]:
        fastener('Toe plate countersunk visual fixing',(x,-1.69,.022),p['steel'],r=.005)
    # Open underside reveals five arched ribs rather than a solid triangular wedge.
    start=math.radians(17)
    for x in [-1.12,-.56,0,.56,1.12]:
        upper=[];lower=[]
        for i in range(25):
            t=start+(theta-start)*i/24;y,z=yz(t)
            upper.append((y+.012,z-.031));lower.append((y+.012,max(.035,z-.160)))
        extrude_yz('Curved structural rib',upper+list(reversed(lower)),x,.045,p['navy'],.003)
        beam('Deck underside longitudinal bearer',(x,endy+.055,top-.068),(x,back-.015,top-.068),.065,.075,p['navy'],.004)
        for y in [endy+.06,back-.065]:
            box('Deck ground foot',(x,y,.016),(.19,.17,.032),p['zinc'],.007)
            beam('Deck support leg',(x,y,.031),(x,y,top-.064),.060,.060,p['navy'],.004)
            for dx in [-.056,.056]:fastener('Deck foot fixing',(x+dx,y,.034),p['steel'],r=.007)
    # Width-spanning transverse bearers beneath the skin and the rear deck.
    for deg in [18,40,60,74]:
        y,z=yz(math.radians(deg));beam('Under curve transverse bearer',(-1.17,y+.025,z-.084),(1.17,y+.025,z-.084),.075,.060,p['navy'],.004)
    for y in [endy+.06,back-.065]:beam('Deck transverse bearer',(-1.18,y,top-.115),(1.18,y,top-.115),.07,.07,p['navy'],.005)
    for x in [-1.12,1.12]:
        beam('Ground side tie',(x,-1.105,.047),(x,back-.03,.047),.065,.06,p['navy'],.004)
        beam('Side diagonal deck brace',(x,endy+.065,.09),(x,back-.065,top-.15),.045,.045,p['navy'],.003)
        beam('Rear diagonal deck brace',(x,back-.065,.11),(-x,back-.065,top-.16),.04,.04,p['navy'],.003)
    # Five independently bounded deck panels make the transition to a level landing clear.
    for i in range(5):
        y=endy+.082+i*.138
        box('Raised landing deck panel',(0,y,top-.016),(2.4,.134,.040),p['deck'],.004)
        for x in [-1.10,1.10]:fastener('Deck panel fixing',(x,y,top+.006),p['steel'],r=.006)
    rod('Round transition coping',(-1.245,endy+.006,top+.005),(1.245,endy+.006,top+.005),.041,p['steel'],40,.002)
    for x in [-1.245,1.245]:cyl('Coping end plug',(x,endy+.006,top+.005),.038,.008,p['navy'],'X',32,.001)
    # Narrow curved edge strips protect the visible skin edge without enclosing the underside.
    for x in [-1.207,1.207]:
        line=[]
        for i in range(41):
            y,z=yz(theta*i/40);line.append((x,y,z-.015))
        sweep('Riding skin edge trim',line,.010,p['steel'],8)
        for deg in [17,39,60,73]:
            y,z=yz(math.radians(deg));oriented_fastener('Side trim fixing',(x,y,z-.015),(math.copysign(1,x),0,0),p['steel'],.005)
    # A low back guard and connected returns are part of this one ramp assembly.
    guard=top+.68
    for x in [-1.13,0,1.13]:
        rod('Back deck guard upright',(x,back-.036,top-.11),(x,back-.036,guard),.022,p['navy'],24,.002)
        box('Guard upright mounting saddle',(x,back-.038,top-.075),(.12,.09,.17),p['navy'],.008)
        oriented_fastener('Guard mounting bolt',(x,back+.01,top-.07),(0,1,0),p['steel'],.009)
    rod('Back guard top rail',(-1.16,back-.036,guard),(1.16,back-.036,guard),.024,p['navy'],24,.002)
    rod('Back guard intermediate rail',(-1.13,back-.036,top+.34),(1.13,back-.036,top+.34),.017,p['navy'],20,.001)
    for x in [-1.13,1.13]:
        rod('Guard short side return',(x,endy+.30,guard),(x,back-.036,guard),.022,p['navy'],24,.002)
        rod('Guard side return upright',(x,endy+.30,top-.03),(x,endy+.30,guard),.022,p['navy'],24,.002)
    return ('city-skate-quarter-pipe','開放フレーム式スケートランプ','Open-frame skate quarter pipe',
        'スケートパークの端部に置く単体クォーターパイプ。連続した曲面の滑走面、薄い導入リップ、丸いコーピング、上部デッキと低い後方ガード、5本の曲線リブ、横梁・脚・斜材を備えた開放式の下部構造を造形。スケートボード、利用者、隣接ランプ、地面や基礎は含みません。静的装飾用で、滑走性能・転落防護・構造安全・競技規格は未検証。認証された遊具や施工指示ではありません。',
        'One quarter pipe for the edge of a skate-park scene, with a continuously curved riding skin, thin approach lip, round coping, elevated deck and low rear guard, five arched ribs, cross bearers, legs and diagonal braces visible beneath the open frame. No skateboard, rider, adjacent ramp, ground or foundation. Static decorative geometry; riding performance, fall protection, structural safety and competition standards are unvalidated. Not certified play equipment or construction instructions.',
        ['park','skate','quarter-pipe','ramp','スケート'])


def climbing_dome():
    p=palette()
    # Create and clip an original frequency-two icosahedral edge network.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
    temp=bpy.context.object
    raw=[v.co.copy() for v in temp.data.vertices];edges=[tuple(e.vertices) for e in temp.data.edges]
    north=max(raw,key=lambda v:(v.z,-v.x));q=north.rotation_difference(Vector((0,0,1)))
    raw=[q@v for v in raw];bpy.data.objects.remove(temp,do_unlink=True)
    points=[];index={};links=set()
    def ix(v):
        key=tuple(round(float(c),7) for c in v)
        if key not in index:index[key]=len(points);points.append(Vector(key))
        return index[key]
    for a,b in edges:
        a,b=raw[a],raw[b]
        if a.z< -1e-6 and b.z< -1e-6:continue
        if a.z< -1e-6:a=a+(b-a)*(-a.z/(b.z-a.z))
        elif b.z< -1e-6:b=b+(a-b)*(-b.z/(a.z-b.z))
        if abs(a.z)<1e-6:a.z=0
        if abs(b.z)<1e-6:b.z=0
        ia,ib=ix(a),ix(b)
        if ia!=ib:links.add(tuple(sorted((ia,ib))))
    base=sorted((i for i,v in enumerate(points) if abs(v.z)<1e-6),key=lambda i:math.atan2(points[i].y,points[i].x))
    for a,b in zip(base,base[1:]+base[:1]):links.add(tuple(sorted((a,b))))
    world=[Vector((v.x*1.46,v.y*1.46,.112+v.z*1.34)) for v in points]
    for i,(a,b) in enumerate(sorted(links)):
        rod('Geodesic climbing strut %03d'%i,world[a],world[b],.0215,p['teal'],16,0)
    for i,v in enumerate(world):
        hub=sphere('Rounded strut hub %02d'%i,v,(.046,.046,.046),p['amber'],20,10)
        # Explicit faceted hub shading avoids thread-order variation in averaged
        # sphere pole normals and custom-normal encoding. Geometry and UVs stay intact.
        for polygon in hub.data.polygons:polygon.use_smooth=False
        n=Vector((v.x/1.46,v.y/1.46,(v.z-.112)/1.34)).normalized()
        if i not in base:oriented_fastener('Outward joint cap screw',v+n*.041,n,p['steel'],.012)
    for i in base:
        v=world[i];n=Vector((v.x,v.y,0)).normalized();t=Vector((-n.y,n.x,0))
        cyl('Ground shoe plate',(v.x,v.y,.015),.102,.030,p['zinc'],sides=16,bevel=.005)
        cyl('Ground shoe socket',(v.x,v.y,.067),.039,.087,p['navy'],sides=24,bevel=.003)
        for s in [-1,1]:
            pos=v+t*s*.069;fastener('Ground shoe anchor',(pos.x,pos.y,.034),p['steel'],r=.008)
        oriented_fastener('Shoe radial clamp screw',(v.x+n.x*.043,v.y+n.y*.043,.082),n,p['steel'],.009)
    return ('city-playground-climbing-dome','低いジオデシック登りドーム','Low geodesic climbing dome',
        '公園や遊び場の場面に置く低いジオデシック型ドーム。半球状の三角格子を作る実体のチューブ、丸い接合ハブ、外向き固定ねじ、地面に接するソケット付きシューとアンカーを造形。内部は実際に開いています。利用者、地面、基礎や落下保護舗装は含みません。静的装飾モデルで、荷重・開口部への挟み込み・転落・遊具安全規格の認証や検証はなく、施工指示ではありません。',
        'A low geodesic dome for park and playground scenes, with a hemisphere-like triangular network of solid tubular struts, rounded joint hubs, outward-facing fixings and socketed ground shoes with anchor hardware. The interior and triangular openings are genuinely open. No people, ground, foundations or impact surfacing. Static decorative geometry, without certification or validation for loads, entrapment openings, falls or playground safety standards; not construction instructions.',
        ['park','playground','geodesic','climbing-dome','ジャングルジム'])


def football_goal():
    p=palette();half=1.80;top=1.90;rear=1.22
    # One goal with a rounded-corner U frame, back support tubes and ground rails.
    frame=[(-half,0,.065),(-half,0,top-.115)]
    for i in range(1,9):
        a=math.pi-i*(math.pi/2)/8;frame.append((-half+.115+.115*math.cos(a),0,top-.115+.115*math.sin(a)))
    frame.append((half-.115,0,top))
    for i in range(1,9):
        a=math.pi/2-i*(math.pi/2)/8;frame.append((half-.115+.115*math.cos(a),0,top-.115+.115*math.sin(a)))
    frame.append((half,0,.065));sweep('Continuous rounded front goal frame',frame,.047,p['white'],24)
    for x in [-half,half]:
        sweep('Angled rear net support',[(x,0,1.69),(x,.10,1.69),(x,.43,1.64),(x,.54,1.54),(x,rear,.065)],.030,p['white'],20)
        rod('Side ground rail',(x,0,.065),(x,rear,.065),.037,p['white'],24,.002)
        cyl('Front upright bottom sleeve',(x,0,.12),.052,.15,p['white'],sides=32,bevel=.004)
        for y in [.06,rear-.07]:
            box('Rubber ground pad',(x,y,.015),(.15,.22,.030),p['dark'],.012)
            box('Ground pad saddle',(x,y,.044),(.12,.14,.025),p['zinc'],.007)
        for y,z in [(0,1.69),(rear,.065)]:
            oriented_fastener('Support joint captive bolt',(x+math.copysign(.038,x),y,z),(math.copysign(1,x),0,0),p['steel'],.010)
    rod('Rear transverse ground rail',(-half,rear,.065),(half,rear,.065),.030,p['white'],24,.002)
    rod('Upper rear net support crossbar',(-half,.43,1.64),(half,.43,1.64),.025,p['white'],20,.001)
    # Fine, actual geometric open net across roof and rear. No flat alpha texture.
    xnet=half-.015;zbottom=.082
    cross=[]
    for i in range(5):
        t=i/4;cross.append((.010+.43*t,top-.019-.245*t))
    for i in range(1,13):
        t=i/12;cross.append((.44+(rear-.44)*t,1.636+(zbottom-1.636)*t))
    # Shallow fixed sag is only shape; the net has no cloth simulation.
    for i in range(25):
        x=-xnet+2*xnet*i/24;bow=.026*(1-(x/xnet)**2)
        points=[(x,y+bow*math.sin(math.pi*j/(len(cross)-1)),z) for j,(y,z) in enumerate(cross)]
        sweep('Roof and rear longitudinal net cord %02d'%i,points,.0028,p['rope'],6)
    for j,(y,z) in enumerate(cross):
        points=[]
        for i in range(13):
            x=-xnet+2*xnet*i/12;bow=.026*(1-(x/xnet)**2)
            points.append((x,y+bow*math.sin(math.pi*j/(len(cross)-1)),z))
        sweep('Roof and rear transverse net cord %02d'%j,points,.0028,p['rope'],6)
    # Both side nets have clipped strands, not a filled side panel.
    def side_top(y):
        if y<=.44:return top-.019-.245*y/.44
        return 1.636+(zbottom-1.636)*(y-.44)/(rear-.44)
    def side_rear(z):
        if z>1.636:return .44*(top-.019-z)/.245
        return .44+(rear-.44)*(1.636-z)/(1.636-zbottom)
    for x in [-xnet,xnet]:
        for i in range(1,10):
            y=rear*i/10;z=side_top(y)
            rod('Side net upright cord',(x,y,zbottom),(x,y,z),.0028,p['rope'],6,0)
        for i in range(1,14):
            z=zbottom+(top-.019-zbottom)*i/14;y=side_rear(z)
            rod('Side net horizontal cord',(x,.008,z),(x,y,z),.0028,p['rope'],6,0)
        perimeter=[(x,.008,zbottom),(x,.008,top-.019),(x,.44,1.636),(x,rear,zbottom)]
        for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
            rod('Side net perimeter binding',a,b,.006,p['rope'],8,0)
        for point in perimeter:sphere('Rounded perimeter binding joint',point,(.006,.006,.006),p['rope'],12,6)
    # Attachment loops wrap the frame and join the nearest net boundary.
    for i in range(13):
        x=-1.68+3.36*i/12
        pts=[(x,.055*math.cos(a),top+.055*math.sin(a)) for a in [math.tau*k/16 for k in range(17)]]
        sweep('Crossbar net lacing loop',pts,.0035,p['rope'],6)
    for x in [-half,half]:
        for z in [.23,.53,.83,1.13,1.43,1.70]:
            pts=[(x+.055*math.cos(a),.055*math.sin(a),z) for a in [math.tau*k/16 for k in range(17)]]
            sweep('Upright net lacing loop',pts,.0035,p['rope'],6)
    return ('city-football-goal','実体ネット付き小型サッカーゴール','Small football goal with geometric net',
        '公園のレクリエーション場面用の単体サッカーゴール。丸い前枠、曲げた後部支持管、側面と後部の接地レール、ゴム足、屋根・後面・両側面に開口のある実体コードネットと固定ループを造形。ゴール前面は開いています。ボール、競技場、もう一方のゴール、利用者、地面や固定重りは含みません。静的装飾用で、転倒防止・競技規格・安全性は未検証。実用可能な競技器具や施工指示ではありません。',
        'One small football/soccer goal for park recreation scenes, with a rounded front frame, bent rear support tubes, side and rear ground rails, rubber feet, real open cord net across the roof, back and both sides, and lacing loops. The front mouth is open. No ball, pitch, second goal, people, ground or ballast. Static decorative geometry; anti-tip stability, sporting standards and safety are not validated. Not functioning competition equipment or construction instructions.',
        ['park','football','soccer','goal','net','サッカー'])


BUILDERS=[parallel_bars,quarter_pipe,climbing_dome,football_goal]
IDS=['city-outdoor-parallel-bars','city-skate-quarter-pipe','city-playground-climbing-dome','city-football-goal']
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='batches/batch-011/assets');ap.add_argument('--only',default='')
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    for fn,id in zip(BUILDERS,IDS):
        if a.only and a.only!=id:continue
        reset();spec=fn()
        bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH')
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        publish_asset(*spec,out,'scripts/city_expansion/active_park.py',azimuth=-55 if fn!=football_goal else -65,elevation=24 if fn!=football_goal else 18)
