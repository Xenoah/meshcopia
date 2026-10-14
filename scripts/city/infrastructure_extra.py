"""Six original additional city infrastructure props. CC BY 4.0.
Blender 4.3+/bpy: meters, Z-up authoring, Y-up GLB via common.py.
Uses original local infrastructure helpers. No third-party models or textures.
"""
import sys, math, argparse, json
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import infrastructure as I
from common import reset, publish_asset, render

# Adaptive detail: small hardware and sheet edges use a single bevel segment.
def box(name,p,s,m,b=.003,rot=None):
    o=I.box(name,p,s,m,b,rot)
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1 if min(s)<.018 else 2
    return o

def cyl(name,p,r,d,m,axis='Z',n=32,b=.0015,r2=None):
    o=I.cylinder(name,p,r,d,m,axis,n,min(b,d*.2,r*.2),r2)
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1 if r<.015 else 2
    return o

def mesh(name,v,f,m,b=0):
    o=I.mesh(name,v,f,m,b)
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o

def bolt(name,p,m,axis='Z',r=.006):
    cyl(name+' washer',p,r*1.5,r*.28,m,axis,16,.0003)
    q=list(p);q['XYZ'.index(axis)]+=(-1 if axis=='Y' else 1)*r*.31
    cyl(name+' hex head',q,r,r*.65,m,axis,6,.0003)

def bar(name,a,b,width,depth,m,bevel=.002):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,depth,(b-a).length),m,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def extrude_x(name,profile,width,p,m,b=.001):
    n=len(profile);v=[(p[0]+x,p[1]+y,p[2]+z) for x in [-width/2,width/2] for y,z in profile]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,m,b)

def lathe(name,profile,m,n=64):
    # Unique axial pole vertices avoid collapsed triangles at radius zero.
    verts=[];rings=[]
    for r,z in profile:
        if r==0:rings.append([len(verts)]);verts.append((0,0,z))
        else:
            rings.append(list(range(len(verts),len(verts)+n)))
            verts.extend((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n))
    faces=[]
    for a,b in zip(rings,rings[1:]+rings[:1]):
        if len(a)==1 and len(b)==1:continue
        for i in range(n):
            j=(i+1)%n
            if len(a)==1:faces.append((a[0],b[i],b[j]))
            elif len(b)==1:faces.append((a[i],b[0],a[j]))
            else:faces.append((a[i],b[i],b[j],a[j]))
    return mesh(name,verts,faces,m)

def hollow_sweep(name,points,r,t,m,n=32):
    # Paths are in the YZ plane; fixed X normal gives a stable, untwisted frame.
    pts=[Vector(p) for p in points];v=[]
    for j,p in enumerate(pts):
        tangent=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized()
        u=Vector((1,0,0));w=tangent.cross(u).normalized()
        for radius in [r,r-t]:
            for i in range(n):v.append(tuple(p+radius*(u*math.cos(i*math.tau/n)+w*math.sin(i*math.tau/n))))
    f=[]
    for j in range(len(pts)-1):
        for i in range(n):
            k=(i+1)%n;a=j*2*n+i;b=(j+1)*2*n+i
            f.extend([(a,j*2*n+k,(j+1)*2*n+k,b),(a+n,b+n,(j+1)*2*n+k+n,j*2*n+k+n)])
    for j in [0,len(pts)-1]:
        for i in range(n):
            k=(i+1)%n;a=j*2*n
            f.append((a+i,a+k,a+n+k,a+n+i))
    o=mesh(name,v,f,m)
    for face in o.data.polygons:face.use_smooth=True
    return o

def sector(name,inner,outer,z0,z1,a0,a1,m,segments=None):
    steps=segments or max(1,math.ceil(abs(a1-a0)/math.radians(4)))
    verts=[]
    for z,r in [(z0,inner),(z0,outer),(z1,inner),(z1,outer)]:
        verts.extend((r*math.cos(a0+(a1-a0)*j/steps),r*math.sin(a0+(a1-a0)*j/steps),z) for j in range(steps+1))
    k=steps+1;f=[]
    for j in range(steps):
        f.extend([(j,j+1,k+j+1,k+j),(2*k+j,3*k+j,3*k+j+1,2*k+j+1),(j,2*k+j,2*k+j+1,j+1),(k+j+1,3*k+j+1,3*k+j,k+j)])
    f.extend([(0,k,3*k,2*k),(steps,2*k+steps,3*k+steps,k+steps)])
    return mesh(name,verts,f,m)

def roller_shutter():
    p=I.palette();sheet=I.mat('Shutter satin galvanized steel',(.32,.38,.40),.72,.48)
    rail=p['black'];width=2.85;height=2.5
    # U-shaped tracks remain open toward the rolling curtain.
    for sign in [-1,1]:
        x=sign*1.48
        box('Track closed side web',(x,0,1.25),(.035,.12,2.5),rail,.005)
        for y in [-.052,.052]:box('Track retaining flange',(x-sign*.037,y,1.25),(.074,.016,2.5),rail,.003)
        for z in [.22,.85,1.5,2.25]:bolt('Guide track fixing',(x,-.068,z),p['steel'],'Y',.007)
    slat_height=.059
    profile=[(.0,-slat_height/2),(-.009,-slat_height*.33),(-.016,0),(-.009,slat_height*.33),(.0,slat_height/2),(.007,slat_height/2),(-.008,0),(.007,-slat_height/2)]
    for i in range(41):extrude_x('Interlocking convex shutter slat %02d'%i,profile,width,(0,-.01,.077+i*.058),sheet,.0008)
    box('Bottom locking rail',(0,-.005,.039),(2.87,.075,.078),sheet,.008)
    box('Bottom flexible weather seal',(0,-.005,.006),(2.86,.061,.012),p['dark'],.002)
    for x in [-.8,.8]:
        bar('Pull handle standoff',(x-.065,-.04,.043),(x-.065,-.075,.043),.012,.012,p['black'])
        bar('Pull handle standoff',(x+.065,-.04,.043),(x+.065,-.075,.043),.012,.012,p['black'])
        bar('Recessed shutter pull',(x-.065,-.075,.043),(x+.065,-.075,.043),.012,.012,p['black'])
    cyl('Bottom rail lock cylinder',(0,-.047,.041),.014,.012,p['steel'],'Y',24,.001)
    box('Lock key slot',(0,-.054,.041),(.002,.001,.009),p['dark'],.0002)
    # Folded headbox rather than a solid oversized block; backside and ends modeled.
    box('Headbox front cover',(0,-.112,2.62),(3.08,.018,.25),sheet,.005)
    box('Headbox upper cover',(0,.012,2.75),(3.08,.265,.018),sheet,.004)
    box('Headbox rear return',(0,.138,2.62),(3.08,.018,.25),sheet,.004)
    for x in [-1.532,1.532]:box('Headbox end cap',(x,.012,2.62),(.016,.265,.25),rail,.005)
    cyl('Roller axle',(0,.015,2.6),.078,2.99,p['dark'],'X',32,.002)
    for x in [-1.41,1.41]:bolt('Headbox service screw',(x,-.124,2.63),p['steel'],'Y',.005)
    return ('city-roller-shutter','店舗用巻き上げシャッター','Shopfront roller shutter','41枚の成形スラット、開口した側面ガイド、頭上ボックス、引手と下端シールを備えた静的シャッター。','A static shopfront shutter with 41 formed slats, open side guide channels, folded headbox, pull handles and bottom weather seal.',['shutter','shopfront','store','roller','security','シャッター'])

def awning_panel(name,x0,x1,m):
    # Slight transverse fabric sag; front edge slopes down from the wall cassette.
    v=[];steps=10
    for layer in [0,1]:
        for x in [x0,x1]:
            for j in range(steps+1):
                t=j/steps;y=-.05-1.73*t;z=2.59-.54*t-.055*math.sin(math.pi*t)-layer*.004
                v.append((x,y,z))
    k=steps+1;f=[]
    for j in range(steps):
        f.extend([(j,j+1,k+j+1,k+j),(2*k+j,3*k+j,3*k+j+1,2*k+j+1),(j,2*k+j,2*k+j+1,j+1),(k+j+1,3*k+j+1,3*k+j,k+j)])
    f.extend([(0,k,3*k,2*k),(steps,2*k+steps,3*k+steps,k+steps)])
    mesh(name,v,f,m)

def retractable_awning():
    p=I.palette();frame=I.mat('Awning matte aluminum',(.095,.12,.13),.48,.48)
    fabrics=[I.mat('Canvas muted sage',(.18,.27,.22),0,.88),I.mat('Canvas warm linen',(.66,.61,.47),0,.9)]
    box('Wall cassette top',(0,0,2.64),(3.24,.22,.09),frame,.035)
    cyl('Fabric roller',(0,-.02,2.59),.065,3.05,p['paint'],'X',32,.003)
    for x in [-1.59,1.59]:box('Cassette end cap',(x,0,2.59),(.055,.23,.18),frame,.025)
    for i in range(12):
        x0=-1.5+i*.25;x1=x0+.25;awning_panel('Woven canopy stripe %02d'%i,x0,x1,fabrics[i%2])
        # Scalloped valance is a closed, thin solid ribbon, not an alpha plane.
        points=[]
        for j in range(9):
            x=x0+.25*j/8;drop=.135+.026*math.sin(math.pi*j/8)
            points.append((x,2.05-drop))
        verts=[(x,y,z) for y in [-1.79,-1.785] for x,z in [(x0,2.05),(x1,2.05),*reversed(points)]]
        n=11;faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
        mesh('Scalloped fabric valance %02d'%i,verts,faces,fabrics[i%2])
    box('Front tension bar',(0,-1.77,2.045),(3.11,.075,.07),frame,.016)
    for x in [-1.22,1.22]:
        box('Wall mounting foot',(x,.105,2.49),(.18,.035,.26),p['steel'],.009)
        for dx in [-.055,.055]:
            for z in [2.41,2.57]:bolt('Wall anchor',(x+dx,.08,z),p['steel'],'Y',.007)
        # Two articulated arms with offset elbow and exposed pivot caps.
        sign=1 if x>0 else -1
        a=(x,-.03,2.46);b=(x-sign*.27,-.85,2.25);c=(x,-1.73,2.015)
        bar('Inner folding support arm',a,b,.045,.055,frame,.005)
        bar('Outer folding support arm',b,c,.04,.047,frame,.005)
        for q in [a,b,c]:
            cyl('Support pivot axle',q,.033,.071,p['steel'],'X',24,.003)
        bar('Tension spring housing',(x-sign*.025,-.20,2.412),(x-sign*.20,-.70,2.29),.03,.036,p['steel'],.003)
    return ('city-retractable-awning','店舗用折り畳み式オーニング','Extended retractable awning','たわみのある縞キャンバス、波形垂れ幕、左右の関節アームと壁付けカセットを備えた展開状態のオーニング。','An extended static awning with gently sagging striped canvas, scalloped valance, articulated support arms and a wall cassette. No animation or load rating.',['awning','canopy','shopfront','canvas','shade','オーニング'])

def downspout():
    p=I.palette();zinc=I.mat('Downspout zinc finish',(.31,.37,.40),.77,.46)
    pts=[(0,0,3.35),(0,0,3.10)]
    # Smooth S-shaped top offset and open lower discharge elbow.
    for i in range(1,17):
        t=i/16;pts.append((0,-.16*(3*t*t-2*t*t*t),3.10-.32*t))
    pts.append((0,-.16,.38))
    for i in range(1,13):
        a=(math.pi/2)*i/12;pts.append((0,-.16-.19*(1-math.cos(a)),.38-.19*math.sin(a)))
    pts.append((0,-.47,.19))
    hollow_sweep('Continuous hollow rainwater downpipe',pts,.047,.003,zinc,32)
    for z in [.78,1.78,2.61]:
        I.annulus('Pipe coupling collar',(0,-.16,z),.052,.047,.075,zinc,n=40)
        I.annulus('Wall pipe clamp',(0,-.16,z+.09),.057,.052,.024,p['black'],n=40)
        box('Clamp wall anchor plate',(0,.03,z+.09),(.12,.025,.10),p['steel'],.007)
        bar('Clamp stand off',(0,.012,z+.09),(0,-.105,z+.09),.018,.018,p['black'],.002)
        for x in [-.041,.041]:bolt('Bracket wall fixing',(x,.012,z+.09),p['edge'],'Y',.005)
    I.annulus('Upper receiving socket',(0,0,3.325),.053,.047,.05,zinc,n=40)
    # Rolled seam on straight rear side; not a full-length coplanar decal.
    box('Folded longitudinal pipe seam',(0,-.111,1.58),(.006,.004,2.28),zinc,.001)
    return ('city-downspout','壁付け雨どい縦管','Offset rainwater downspout','中空の連続管、上部オフセット、開いた吐出口、継手と壁面支持金具を備えた雨どい縦管。','A hollow rainwater pipe with smooth upper offset, open discharge elbow, coupling collars and wall stand-off clamps. Decorative building equipment.',['downspout','rainwater','gutter','pipe','wall','雨どい'])

def roof_exhaust_cowl():
    p=I.palette();metal=I.mat('Spun galvanized cowl',(.35,.40,.42),.8,.43)
    flashing=box('Roof flashing plate',(0,0,.018),(.63,.63,.036),metal,0)
    cutter=cyl('Flashing aperture cutter',(0,0,.018),.143,.15,metal,n=64,b=0)
    I.cut(flashing,cutter);I.bevel_obj(flashing,.004,2)
    I.annulus('Raised flashing curb',(0,0,.064),.192,.15,.092,metal,n=64)
    I.annulus('Open exhaust riser',(0,0,.285),.15,.143,.49,metal,n=64)
    I.annulus('Riser upper bead',(0,0,.525),.159,.143,.018,p['steel'],n=64)
    # Dome, underside and rolled skirt form one closed spun-metal shell.
    profile=[(0,.77)]+[(.34*j/12,.77-.115*(j/12)**2) for j in range(1,13)]
    profile +=[(.34,.605),(.33,.605),(.33,.77-.115*(.33/.34)**2-.011)]
    profile +=[(.33*j/12,.77-.115*(.33*j/12/.34)**2-.011) for j in range(11,-1,-1)]
    cap=lathe('Mushroom weather cap',profile,metal,72)
    for face in cap.data.polygons:face.use_smooth=True
    for a in [0,math.tau/3,2*math.tau/3]:
        x,y=math.cos(a),math.sin(a)
        bar('Cowl cap support',(x*.146,y*.146,.46),(x*.26,y*.26,.69),.022,.018,p['steel'],.002)
        bolt('Cap retention rivet',(x*.29,y*.29,.69),p['edge'],r=.004)
    # Coarse safety screen under cap: spaced physical vertical strips around riser.
    for i in range(24):
        a=i*math.tau/24;x=.173*math.cos(a);y=.173*math.sin(a)
        bar('Circular bird guard wire',(x,y,.49),(x,y,.64),.003,.003,p['black'],.0003)
    I.annulus('Bird guard lower rim',(0,0,.493),.177,.171,.007,p['black'],n=48)
    I.annulus('Bird guard upper rim',(0,0,.638),.177,.171,.007,p['black'],n=48)
    for x in [-.25,.25]:
        for y in [-.25,.25]:bolt('Roof flange fixing',(x,y,.039),p['steel'],r=.009)
    return ('city-roof-exhaust-cowl','屋上換気ベンチレーター','Mushroom roof exhaust cowl','中空の立上り管、丸い雨よけ、支持材、防鳥格子と屋根取付フランジを備えた屋上換気口。','A mushroom roof exhaust with hollow riser, spun weather cap, cap supports, bird-guard strips and roof flashing flange. Static visual prop, not airflow-rated.',['roof','exhaust','ventilator','cowl','industrial','屋上換気'])

def security_camera():
    p=I.palette();body=I.mat('Camera warm grey coating',(.49,.52,.50),.23,.43)
    glass=I.mat('Optical dark lens',(.009,.021,.032),.35,.16)
    box('Wall mounting gasket',(0,.012,.22),(.125,.012,.19),p['dark'],.016)
    box('Wall mounting plate',(0,0,.22),(.116,.02,.182),body,.013)
    for x in [-.038,.038]:
        for z in [.158,.282]:bolt('Camera mount fixing',(x,-.014,z),p['steel'],'Y',.0045)
    bar('Wall camera support',(0,-.015,.19),(0,-.115,.16),.029,.032,body,.004)
    bar('Camera tilt bracket',(0,-.115,.16),(0,-.15,.27),.027,.03,body,.004)
    cyl('Tilt hinge axle',(0,-.15,.265),.031,.095,p['black'],'X',32,.003)
    for x in [-.052,.052]:cyl('Tilt locking screw',(x,-.15,.265),.012,.013,p['steel'],'X',6,.001)
    box('Camera enclosure',(0,-.205,.333),(.14,.29,.12),body,.026)
    box('Rear service seam',(0,-.064,.333),(.123,.01,.101),p['black'],.018)
    box('Rear end cap',(0,-.055,.333),(.124,.012,.102),body,.018)
    cyl('Front optical bezel',(0,-.356,.333),.047,.017,p['black'],'Y',48,.002)
    I.annulus('Lens retaining ring',(0,-.369,.333),.039,.031,.009,p['steel'],'Y',48)
    cyl('Recessed lens element',(0,-.369,.333),.030,.008,glass,'Y',48,.001)
    cyl('Inner lens aperture',(0,-.374,.333),.016,.002,p['dark'],'Y',32,.0003)
    for a in [0,math.pi/2,math.pi,3*math.pi/2]:
        cyl('Small infrared emitter',(math.cos(a)*.041,-.369,.333+math.sin(a)*.041),.004,.003,glass,'Y',12,.0004)
    # Three-sided sheet-metal weather hood projects past the lens without closing it.
    box('Weather hood roof',(0,-.22,.403),(.168,.345,.012),body,.004)
    for x in [-.078,.078]:box('Weather hood side lip',(x,-.22,.385),(.012,.345,.027),body,.003)
    hollow_sweep('Protected rear cable',[(0,-.044,.29),(0,-.031,.265),(0,-.04,.23),(0,-.02,.20)],.006,.0015,p['dark'],12)
    return ('city-security-camera','壁付け屋外監視カメラ','Wall-mounted exterior security camera','壁付け金具、角度調整ヒンジ、奥まったレンズ、日除けフードと背面ケーブル付きの静的カメラ模型。','A static exterior camera prop with wall mounting plate, tilt hinge, recessed optical lens, weather hood and rear cable. No recording or surveillance functionality.',['camera','security','wall','exterior','equipment','監視カメラ'])

def cable_tray_elbow():
    p=I.palette();metal=I.mat('Cable tray galvanized steel',(.37,.43,.46),.8,.44)
    inner=.32;outer=.58;start=0;end=math.pi/2
    # A single 90-degree tray. Open base slots and side perforations are true geometry.
    for lo,hi in [(inner,inner+.025),(.444,.456),(outer-.025,outer)]:
        sector('Continuous curved deck rail',lo,hi,0,.005,start,end,metal)
    for i in range(16):
        a=i*end/15;half=math.radians(1.25)
        for lo,hi in [(inner+.025,.444),(.456,outer-.025)]:
            sector('Radial deck bridge %02d'%i,lo,hi,0,.005,max(start,a-half),min(end,a+half),metal,2)
    for radius in [inner,outer]:
        lo=radius-.003;hi=radius+.003
        sector('Side web lower rail',lo,hi,.005,.028,start,end,metal)
        sector('Side web upper rail',lo,hi,.077,.098,start,end,metal)
        sector('Folded upper stiffening lip',lo-.006,hi+.006,.098,.103,start,end,metal)
        for i in range(1,15):
            a=i*end/15;half=math.radians(1.05)
            sector('Perforated side web post',lo,hi,.028,.077,max(start,a-half),min(end,a+half),metal,2)
    # Four splice tabs with bolt heads on each open end; ends remain open for joining.
    for angle in [0,math.pi/2]:
        for radius in [inner,outer]:
            x=radius*math.cos(angle);y=radius*math.sin(angle)
            # End joint stiffener is a short radial side plate within the tray envelope.
            a0=0 if angle==0 else end-math.radians(3)
            a1=math.radians(3) if angle==0 else end
            sector('Joining end web',radius-.0035,radius+.0035,.028,.077,a0,a1,metal,2)
            for z in [.038,.066]:
                if angle==0:
                    cyl('End splice bolt',(x+.004,y+.012,z),.005,.008,p['edge'],'X',6,.0005)
                else:
                    cyl('End splice bolt',(x+.012,y+.004,z),.005,.008,p['edge'],'Y',6,.0005)
    return ('city-cable-tray-elbow','曲がりケーブルトレイ','Perforated cable tray elbow','床面と側面に実際の開口、曲線リブ、端部接続金具を備えた90度ケーブルトレイ単体。','A single 90-degree cable tray elbow with genuine deck and side-wall apertures, curved stiffening lips and end splice hardware. Decorative geometry, not a rated electrical product.',['cable tray','elbow','industrial','utility','perforated','ケーブルトレイ'])

BUILDERS={
 'city-roller-shutter':roller_shutter,
 'city-retractable-awning':retractable_awning,
 'city-downspout':downspout,
 'city-roof-exhaust-cowl':roof_exhaust_cowl,
 'city-security-camera':security_camera,
 'city-cable-tray-elbow':cable_tray_elbow,
}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output','--out',dest='output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
    parser.add_argument('--only',choices=sorted(BUILDERS))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    chosen={args.only:BUILDERS[args.only]} if args.only else BUILDERS
    # Preflight the whole selection before emitting anything, never overwrite an asset.
    existing=[str(args.output/slug) for slug in chosen if (args.output/slug).exists()]
    if existing:parser.error('Refusing to overwrite existing assets: '+', '.join(existing))
    for slug,builder in chosen.items():
        reset();spec=builder()
        elevation=32 if slug=='city-cable-tray-elbow' else 24
        publish_asset(*spec,out_dir=args.output,generator='scripts/city/infrastructure_extra.py',azimuth=-60,elevation=elevation)
        metadata_path=args.output/slug/'asset.json'
        metadata=json.loads(metadata_path.read_text())
        metadata['usages'][0]['sourcePaths'].append('scripts/city/infrastructure.py')
        metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        if slug in ('city-retractable-awning','city-roof-exhaust-cowl'):
            I.render_underside_qa(slug,args.output)

if __name__=='__main__':main()
