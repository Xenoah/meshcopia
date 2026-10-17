"""Original shared interior fixtures for Xenoah Meshcopia, CC BY 4.0.
Portable Blender recipe. Generic static visualization props, not engineered products.
Uses only its sibling common.py and Blender's bundled Python modules.
"""
import bpy, sys, math, argparse
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *


def palette():
    return dict(
        teal=mat('Deep petrol powder coat', (.050, .155, .171), .24, .36),
        cream=mat('Warm ivory enamel', (.70, .71, .64), .16, .36),
        steel=mat('Satin stainless fittings', (.43, .49, .50), .82, .27),
        dark=mat('Charcoal structural metal', (.055, .070, .073), .42, .38),
        rubber=mat('Soft charcoal contact pads', (.023, .029, .028), 0, .72),
        warm=mat('Plain warm timber tone', (.45, .235, .105), 0, .46),
        tray=mat('Slate grey drip pan', (.25, .33, .35), .20, .43))


def cyl(name, loc, radius, depth, material, axis='Z', vertices=32, bevel=.0015):
    o=cylinder(name, loc, radius, depth, material, vertices, bevel=bevel)
    if axis=='X': o.rotation_euler[1]=math.pi/2
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    # Cylinder end caps stay flat; smooth only the original side quads.
    for face in o.data.polygons: face.use_smooth=len(face.vertices)==4
    return o


def rod(name, start, end, radius, material, vertices=24):
    a,b=Vector(start),Vector(end)
    o=cyl(name, (a+b)/2, radius, (b-a).length, material, vertices=vertices, bevel=min(.001, radius*.12))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def beam(name, start, end, width, depth, material, bevel=.002):
    a,b=Vector(start),Vector(end)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def extrude_xz(name, outline, y0, y1, material, bevel=.001):
    """Closed extrusion of an x/z outline; real openings are omitted from outline."""
    count=len(outline)
    verts=[(x,y,z) for y in (y0,y1) for x,z in outline]
    faces=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name,verts,faces,material,bevel)


def sweep_planar(name, rz, angle, radius, material, segments=16):
    """Closed round tube following a sampled smooth path in a radial/Z plane."""
    radial=Vector((math.cos(angle),math.sin(angle),0)); side=Vector((-math.sin(angle),math.cos(angle),0))
    centers=[radial*r+Vector((0,0,z)) for r,z in rz]
    verts=[]
    for i,c in enumerate(centers):
        tangent=(centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)]).normalized()
        across=side.cross(tangent).normalized()
        for j in range(segments):
            q=j*math.tau/segments;verts.append(tuple(c+side*(math.cos(q)*radius)+across*(math.sin(q)*radius)))
    faces=[tuple(range(segments-1,-1,-1))]
    for i in range(len(centers)-1):
        for j in range(segments):
            k=(j+1)%segments;faces.append((i*segments+j,i*segments+k,(i+1)*segments+k,(i+1)*segments+j))
    faces.append(tuple((len(centers)-1)*segments+j for j in range(segments)))
    o=mesh(name,verts,faces,material,0,True)
    o.data.polygons[0].use_smooth=False;o.data.polygons[-1].use_smooth=False
    return o


def bezier_path(points, count=24):
    a,b,c,d=[Vector(p) for p in points]
    return [tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d) for t in [i/count for i in range(count+1)]]


def fastener(name, loc, material, axis='Z', radius=.005):
    return cyl(name,loc,radius,.004,material,axis,8,.0003)


def caster(x,y,turn,p):
    before=set(bpy.context.scene.objects)
    # The wheel axle is offset from the swivel axis; two fork cheeks surround it.
    cyl('Caster mounting stem',(0,0,.173),.012,.050,p['steel'],vertices=24)
    cyl('Caster swivel bearing',(0,0,.146),.028,.021,p['steel'],vertices=32)
    box('Caster crown plate',(.018,0,.129),(.073,.059,.014),p['steel'],.004)
    outline=[(-.017,.132),(.052,.132),(.069,.058),(.049,.043),(.028,.043),(.015,.103),(-.017,.111)]
    for yy in [-.031,.024]: extrude_xz('Closed caster fork cheek',outline,yy,yy+.007,p['steel'],.002)
    cyl('Nonmarking wheel',(.047,0,.053),.053,.041,p['rubber'],'Y',40,.006)
    cyl('Caster through axle',(.047,0,.053),.009,.075,p['steel'],'Y',24,.001)
    for yy in [-.023,.023]: cyl('Recessed caster hub',(.047,yy,.053),.026,.007,p['tray'],'Y',32,.002)
    for yy in [-.040,.040]: fastener('Axle head',(.047,yy,.053),p['dark'],'Y',.007)
    # One molded pedal on every fork is a static brake-like detail, not a working brake.
    box('Fixed caster brake pedal',(-.018,0,.102),(.042,.030,.009),p['dark'],.003,rot=(0,-.3,0))
    transform=Matrix.Translation((x,y,0)) @ Matrix.Rotation(turn,4,'Z')
    for o in set(bpy.context.scene.objects)-before:o.matrix_world=transform @ o.matrix_world


def book_trolley():
    p=palette()
    for x in [-.445,.445]:
        for y in [-.215,.215]:caster(x,y,.20 if y<0 else -.28,p)
    for x in [-.445,.445]:
        # Rounded top handles and uprights form continuous closed tube sweeps.
        yz=[(-.215,.18),(-.215,1.035)]
        for i in range(1,9):
            a=math.pi-i*math.pi/16;yz.append((-.145+.070*math.cos(a),1.035+.070*math.sin(a)))
        yz.extend([(.145,1.105)])
        for i in range(1,9):
            a=math.pi/2-i*math.pi/16;yz.append((.145+.070*math.cos(a),1.035+.070*math.sin(a)))
        yz.append((.215,.18))
        o=sweep_planar('Continuous end handle and legs',yz,math.pi/2,.017,p['teal'],16);o.location.x=x
        rod('Soft upper push grip',(x,-.125,1.106),(x,.125,1.106),.021,p['rubber'],24)
        for y in [-.215,.215]:cyl('Leg bumper collar',(x,y,.225),.030,.032,p['rubber'],vertices=28,bevel=.004)
    for y in [-.215,.215]:beam('Lower frame cross member',(-.445,y,.195),(.445,y,.195),.027,.027,p['teal'],.003)
    # Six inclined trays form three double-sided shelves, with genuine empty volume.
    slope=math.radians(12)
    for level,z in enumerate([.295,.590,.885]):
        for s in [-1,1]:
            box('Inclined book-support shelf',(0,s*.112,z+.024),(.852,.229,.012),p['cream'],.003,rot=(s*slope,0,0))
            box('Outer retaining shelf lip',(0,s*.228,z+.074),(.852,.012,.055),p['cream'],.003)
            rod('Continuous inclined-shelf cross support',(-.445,s*.192,z+.028),(.445,s*.192,z+.028),.012,p['teal'],24)
            for x in [-.422,.422]:
                # Solid end bookends follow the sloping tray rather than merely decorating it.
                before=set(bpy.context.scene.objects)
                outline=[(-.006,z+.002),(.228,z+.051),(.228,z+.218),(.055,z+.218),(-.006,z+.180)]
                side=extrude_xz('Dedicated shelf-end bookend',outline,x-.006,x+.006,p['cream'],.003)
                # Local outline is depth/height; swap local X/Y to the shelf's side plane.
                side.data.transform(Matrix(((0,1,0,0),(s,0,0,0),(0,0,1,0),(0,0,0,1))))
                bm=bmesh.new();bm.from_mesh(side.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(side.data);bm.free()
            for x in [-.35,.35]:beam('Under-shelf cradle',(x,0,z-.009),(x,s*.217,z+.036),.024,.017,p['teal'],.002)
        box('Central shelf back support',(0,0,z+.118),(.85,.016,.216),p['teal'],.004)
        for x in [-.445,.445]:
            rod('Shelf end frame bridge',(x,-.216,z-.006),(x,.216,z-.006),.012,p['teal'])
            for y in [-.10,.10]:fastener('Shelf end frame fixing',(x+(0.019 if x>0 else -.019),y,z+.055),p['steel'],'X')
    return ('city-library-book-trolley','図書館用の傾斜棚ブックトロリー','Inclined-shelf library book trolley',
        '図書館の書架間や返却カウンター付近で本を運ぶ、空の両面三段ブックトロリー。六つの傾斜棚、中央背当て、端部の本止め、棚下の支持材、握り付きの端部フレームと両側フォーク付き四輪キャスターを造形。床に配置する静的モデルで、本・人、積載能力の検証や車輪・ブレーキの動作は含みません。',
        'An empty double-sided three-tier book trolley for library stacks and return counters. Six inclined trays have central back supports, dedicated end bookends, underside cradles, gripped end frames and four offset casters with paired fork cheeks. Place on an interior floor. Books, people, load-rating validation and wheel or brake behavior are absent.',
        ['library','book-trolley','inclined-shelf','interior','図書館'])


def brochure_carousel():
    p=palette()
    # Low weighted base and recessed contact pads support the visible vertical mast.
    cyl('Weighted circular base',(0,0,.049),.288,.056,p['dark'],vertices=64,bevel=.008)
    cyl('Upper stepped base cover',(0,0,.082),.245,.025,p['teal'],vertices=64,bevel=.006)
    for i in range(4):
        a=math.tau*i/4+math.pi/4;cyl('Non-slip base pad',(.207*math.cos(a),.207*math.sin(a),.014),.037,.028,p['rubber'],vertices=24,bevel=.004)
    cyl('Stationary central mast',(0,0,.831),.025,1.490,p['dark'],vertices=40,bevel=.002)
    cyl('Lower bearing sleeve',(0,0,.595),.047,.077,p['steel'],vertices=40,bevel=.003)
    cyl('Lower bearing seat',(0,0,.549),.057,.015,p['teal'],vertices=40,bevel=.002)
    cyl('Upper bearing sleeve',(0,0,1.590),.045,.062,p['steel'],vertices=40,bevel=.003)
    cyl('Blank top cap',(0,0,1.628),.052,.022,p['teal'],vertices=40,bevel=.005)
    # Four radial columns, each with three separate empty pockets, not a signboard.
    for face in range(4):
        before=set(bpy.context.scene.objects)
        for z in [.672,.970,1.268]:
            beam('Radial pocket support',(0,-.022,z+.060),(0,-.153,z+.060),.018,.018,p['dark'],.002)
            box('Pocket rear plate',(0,-.160,z+.130),(.266,.006,.258),p['cream'],.004)
            box('Pocket floor',(0,-.202,z+.006),(.266,.086,.012),p['cream'],.003)
            # Closed front panel has a central finger-access notch and a real open top.
            outline=[(-.133,z),(.133,z),(.133,z+.123),(.055,z+.123),(.035,z+.088),(-.035,z+.088),(-.055,z+.123),(-.133,z+.123)]
            extrude_xz('Notched brochure pocket front',outline,-.249,-.242,p['teal'],.002)
            for x in [-.130,.130]:box('Pocket side cheek',(x,-.201,z+.066),(.006,.082,.132),p['cream'],.002)
            # Narrow return flanges and compact visible screws explain the mounting.
            for x in [-.080,.080]:
                box('Pocket back fixing tab',(x,-.151,z+.050),(.026,.018,.043),p['dark'],.002)
                fastener('Pocket front-facing fixing',(x,-.165,z+.047),p['steel'],'Y',.0045)
        rod('Column rear support rail',(0,-.137,.602),(0,-.137,1.548),.009,p['dark'],20)
        beam('Upper radial column stay',(0,-.025,1.573),(0,-.137,1.548),.017,.017,p['dark'],.002)
        beam('Lower radial column stay',(0,-.025,.595),(0,-.137,.602),.017,.017,p['dark'],.002)
        transform=Matrix.Rotation(face*math.pi/2,4,'Z')
        for o in set(bpy.context.scene.objects)-before:o.matrix_world=transform @ o.matrix_world
    return ('city-rotating-brochure-carousel','回転軸付きのパンフレットラック','Rotating brochure carousel',
        '公共施設のロビーや観光案内所の床に置く、十二ポケットのパンフレット用回転ラック。四方向三段の独立した空ポケットは底・背板・側板と指掛け切欠きを備え、中央軸、上下のベアリング外装、支持アームと重り入り風の円形台座で支えます。印刷物・看板は付属せず、軸受内部、回転アニメーションや荷重・転倒安定性の検証はありません。',
        'A twelve-pocket brochure carousel for public lobbies and visitor-information floors. Four three-tier faces have separate empty receptacles with floors, back and side walls, and finger-access notches. A central mast, visible upper/lower bearing housings, radial supports and weighted-looking circular base complete the assembly. No printed brochures or signboard are supplied; bearing internals, rotation animation, load and tip-stability validation are absent.',
        ['brochure','carousel','reception','interior','パンフレット'])


def coat_stand():
    p=palette()
    cyl('Central timber-tone upright',(0,0,.954),.026,1.630,p['warm'],vertices=40,bevel=.005)
    cyl('Steel base socket',(0,0,.132),.047,.211,p['dark'],vertices=40,bevel=.005)
    cyl('Base socket upper ferrule',(0,0,.243),.036,.028,p['steel'],vertices=32,bevel=.002)
    # Four curved splayed feet, with broad separate contact shoes.
    foot=bezier_path([(.026,.169),(.130,.164),(.230,.039),(.345,.034)],28)
    for i in range(4):
        a=math.tau*i/4
        sweep_planar('Curved splayed tubular foot',foot,a,.018,p['dark'],16)
        x,y=.342*math.cos(a),.342*math.sin(a)
        o=box('Non-slip foot shoe',(x,y,.015),(.082,.050,.030),p['rubber'],.010,rot=(0,0,a))
        cyl('Foot socket bolt',(.054*math.cos(a),.054*math.sin(a),.171),.006,.008,p['steel'],vertices=8,bevel=.0005)
    # Six upper hooks and three lower hooks are discrete curved arms, without lines or hoops.
    for z in [1.065,1.550]:
        cyl('Hook mounting collar',(0,0,z),.043,.069,p['dark'],vertices=40,bevel=.004)
        cyl('Collar retaining ring',(0,0,z-.038),.044,.012,p['steel'],vertices=32,bevel=.0015)
    upper=bezier_path([(.031,1.551),(.165,1.553),(.246,1.615),(.250,1.753)],32)
    for i in range(6):
        a=math.tau*i/6+math.pi/6
        sweep_planar('High coat hanging hook',upper,a,.011,p['dark'],16)
        r,z=upper[-1];sphere('Rounded high-hook tip',(r*math.cos(a),r*math.sin(a),z),(.023,.023,.028),p['warm'],20,10)
        rod('Hook root ferrule',(.029*math.cos(a),.029*math.sin(a),1.551),(.069*math.cos(a),.069*math.sin(a),1.554),.015,p['steel'],20)
    lower=bezier_path([(.029,1.065),(.108,1.044),(.167,1.061),(.170,1.138)],26)
    for i in range(3):
        a=math.tau*i/3
        sweep_planar('Low bag or coat hook',lower,a,.010,p['dark'],16)
        r,z=lower[-1];sphere('Rounded low-hook tip',(r*math.cos(a),r*math.sin(a),z),(.021,.021,.025),p['warm'],20,10)
    sphere('Smooth central finial',(0,0,1.790),(.034,.034,.041),p['warm'],28,14)
    cyl('Finial support neck',(0,0,1.768),.022,.042,p['dark'],vertices=28,bevel=.002)
    return ('city-public-coat-stand','公共ロビー用のコートスタンド','Public lobby coat stand',
        '公共ロビーや集会室の床に置く自立式コートスタンド。木調色の支柱、六本の上部ハンガーフック、三本の低いバッグ用フック、丸い保護端部、固定カラーと四本の湾曲した脚・滑り止め風パッドを造形。衣服・ハンガーは付属せず、耐荷重・転倒安定性や安全規格への適合は未検証。可動部のない静的内装モデルです。',
        'A freestanding coat stand for public lobbies and meeting-room floors. A timber-tone upright carries six high coat hooks, three lower bag hooks, rounded protective tips and fixing collars above four curved splayed feet with pad-like shoes. Clothing and hangers are not included. Load capacity, tip stability and safety-standard compliance are unvalidated. This is a static interior prop with no articulated parts.',
        ['coat-stand','hooks','lobby','interior','コート掛け'])


def umbrella_rack():
    p=palette()
    for x in [-.266,.266]:
        for y in [-.176,.176]:
            cyl('Vertical rack corner leg',(x,y,.306),.012,.575,p['teal'],vertices=24,bevel=.002)
            cyl('Non-slip rack foot',(x,y,.014),.022,.028,p['rubber'],vertices=24,bevel=.004)
            cyl('Rounded top corner cap',(x,y,.603),.014,.025,p['steel'],vertices=24,bevel=.003)
    # Two open grids constrain separate umbrella shafts without sealed cups or bins.
    for z in [.224,.574]:
        for y in [-.176,.176]:box('Grid front rear perimeter',(0,y,z),(.548,.018,.018),p['steel'],.005)
        for x in [-.266,.266]:box('Grid end perimeter',(x,0,z),(.018,.352,.018),p['steel'],.005)
        for x in [-.132,0,.132]:box('Individual-cell length divider',(x,0,z),(.010,.347,.014),p['steel'],.003)
        for y in [-.0587,.0587]:box('Individual-cell cross divider',(0,y,z),(.529,.010,.014),p['steel'],.003)
    for x in [-.266,.266]:
        rod('Lower drip-tray support crossbar',(x,-.176,.076),(x,.176,.076),.011,p['teal'],24)
        for y in [-.176,.176]:fastener('Grid corner clamp screw',(x,y-.012,.574),p['dark'],'Y',.005)
    for y in [-.128,.128]:box('Under-tray support slide rail',(0,y,.080),(.533,.018,.022),p['teal'],.003)
    # The shallow, empty pan is separate from the open upper storage cells.
    box('Removable-looking drip tray floor',(0,0,.094),(.493,.307,.012),p['tray'],.005)
    for y in [-.151,.151]:box('Raised drip tray long rim',(0,y,.113),(.493,.012,.041),p['tray'],.005)
    for x in [-.241,.241]:box('Raised drip tray end rim',(x,0,.113),(.012,.296,.041),p['tray'],.004)
    for x in [-.163,0,.163]:box('Drip tray anti-pooling support rib',(x,0,.103),(.012,.276,.009),p['tray'],.003)
    for s in [-1,1]:
        # Open rectangular lifting handle stands above the pan end, clear of cell volume.
        for y in [-.056,.056]:beam('Tray handle stand-off',(s*.242,y,.121),(s*.294,y,.154),.010,.011,p['steel'],.002)
        rod('Drip tray lift handle',(s*.294,-.057,.154),(s*.294,.057,.154),.008,p['steel'],20)
        for y in [-.061,.061]:fastener('Tray handle attachment',(s*.250,y,.123),p['dark'],'X',.005)
    return ('city-umbrella-drip-rack','個別マス付きの傘用水受けラック','Individual-cell umbrella drip rack',
        '公共施設や店舗の入口内側に置く十二マスの傘立て。上下二段の開いた格子、独立した細い支柱、脚パッド、低い支持バーと、持ち手・立ち上がり縁のある別体風の浅い水受けトレーを造形。空の個別収納部を持つラックで、植木鉢やごみ箱ではありません。傘・水、排水機能、トレー取り外しや物理動作は付属しません。',
        'A twelve-cell umbrella rack for the inside of public-building and shop entrances. Two open grids separate umbrella shafts above narrow corner posts, contact pads, low support bars and a separate-looking shallow drip tray with raised rims and lifting handles. The storage cells are empty and open, not a planter or litter receptacle. Umbrellas, water, drainage simulation, tray-removal animation and physics behavior are absent.',
        ['umbrella','drip-tray','entrance','interior','傘立て'])


def render_underside(out, slug):
    """An extra actual-GLB QA view with an explicit below-object fill light."""
    reset();bpy.ops.import_scene.gltf(filepath=str(out/slug/'source'/f'{slug}.glb'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)])
    center=(lo+hi)/2;span=max(hi-lo)
    bpy.ops.object.light_add(type='AREA', location=center+Vector((.5,-.8,-1.8))*span)
    fill=bpy.context.object;fill.data.energy=300*span*span;fill.data.size=1.5*span;look_at(fill,center)
    render(out/'_qa'/f'{slug}-underside.png',azimuth=-55,elevation=-28)
    bpy.data.objects.remove(fill,do_unlink=True)


BUILDERS=[book_trolley,brochure_carousel,coat_stand,umbrella_rack]
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='batches/batch-022/assets');parser.add_argument('--only',default='');parser.add_argument('--geometry-only',action='store_true')
    a=parser.parse_args(args);out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    if a.geometry_only:
        import common
        common.render=lambda *args,**kwargs:None
    for builder in BUILDERS:
        reset();spec=builder()
        if a.only and spec[0]!=a.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/shared_interior_furnishings.py',azimuth=-55,elevation=25)
        if not a.geometry_only:render_underside(out,spec[0])
