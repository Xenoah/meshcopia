"""Original compact city mobility props for Meshcopia. CC BY 4.0.

Run with Blender 4.3+:
  blender -b --python scripts/city/compact_mobility.py -- --output _inbox
Authoring: meters, Z up, front +X. GLB and matching STL: meters, Y up.
Static visualization geometry only. No riding, load-rating, manufacture,
mechanical function, collision, printability, or safety validation is implied.
No downloaded meshes, textures, branding, fonts or external image assets.
"""
from pathlib import Path
from mathutils import Vector
import argparse
import bpy
import json
import math
import sys

sys.path.insert(0, str(Path(__file__).parent))
import common

M = {}
GROUPS = {}
ACTIVE_GROUP = None
# Profile-specific resting alignment, including molded tire tread and beveled
# toe edge. This places both tires and toe on one plane within float32 precision.
SACK_AXLE_Z = .13435323


def group(name):
    global ACTIVE_GROUP
    ACTIVE_GROUP = name
    GROUPS.setdefault(name, [])


def register(obj):
    GROUPS[ACTIVE_GROUP].append(obj)
    return obj


def materials():
    palette = [
        ('Graphite powder coat', (.055, .070, .080), .65, .34),
        ('Slate blue coating', (.095, .235, .295), .55, .30),
        ('Warm ochre powder coat', (.69, .285, .065), .45, .40),
        ('Tire rubber', (.025, .031, .034), 0, .86),
        ('Grip and tread rubber', (.035, .042, .043), 0, .76),
        ('Rubber tread edge', (.052, .060, .062), 0, .82),
        ('Satin aluminum', (.49, .55, .58), .83, .29),
        ('Brushed steel', (.26, .30, .32), .80, .32),
        ('Dark axle steel', (.09, .11, .12), .78, .33),
        ('Amber reflector', (.95, .315, .020), .12, .23),
        ('Red reflector', (.63, .025, .016), .16, .24),
        ('Headlamp lens', (.83, .90, .86), .12, .18),
        ('Display glass', (.015, .065, .071), .35, .14),
        ('Display segments', (.52, .80, .69), .05, .40),
    ]
    for name, rgb, metal, rough in palette:
        M[name] = common.mat(name, rgb, metal, rough)


def box(name, loc, size, material, bevel=.003, rot=None):
    return register(common.box(name, loc, size, M[material], bevel, rot))


def cyl(name, loc, radius, depth, material, axis=(0, 0, 1), vertices=32, bevel=.001):
    obj = common.cylinder(name, loc, radius, depth, M[material], vertices, bevel=bevel)
    obj.rotation_euler = Vector(axis).to_track_quat('Z', 'Y').to_euler()
    for face in obj.data.polygons:
        face.use_smooth = abs(face.normal.z) < .5
    return register(obj)


def rod(name, start, end, radius, material, vertices=24, bevel=.001):
    start, end = Vector(start), Vector(end)
    return cyl(name, (start+end)/2, radius, (end-start).length, material,
               end-start, vertices, bevel)


def tube(name, points, radius, material, resolution=2):
    return register(common.tube(name, points, radius, M[material], resolution))


def bezier(points, steps=16):
    """Sample cubic Bezier segments; each segment shares its last anchor."""
    result = []
    assert (len(points)-1) % 3 == 0
    for i in range(0, len(points)-1, 3):
        a, b, c, d = [Vector(p) for p in points[i:i+4]]
        for j in range(steps):
            t = j/steps
            result.append(tuple((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d))
    result.append(tuple(points[-1]))
    return result


def ring(name, center, major, minor, material, segments=64, minor_segments=6):
    # Ring axis is Y, like every wheel/axle in these two models.
    bpy.ops.mesh.primitive_torus_add(major_segments=segments, minor_segments=minor_segments,
        location=center, major_radius=major, minor_radius=minor, rotation=(math.pi/2, 0, 0))
    obj = common.finish(bpy.context.object, name, M[material], smooth=True)
    return register(obj)


def polyprism(name, outline, axis, low, high, material, bevel=.002):
    """Extrude a 2D outline along axis 0/1/2, with correct face winding."""
    verts = []
    for height in (low, high):
        for a, b in outline:
            v = [a, b]
            v.insert(axis, height)
            verts.append(v)
    n = len(outline)
    # Flip if the cross product of 2D coordinates differs from extrusion axis.
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    obj = common.mesh(name, verts, faces, M[material], bevel)
    return register(obj)


def lathe_wheel(name, center, profile, material, segments=64):
    """Revolve a closed radial/axial tire section about Y, not a round toy torus."""
    x, y, z = center
    verts = [(x+r*math.cos(t*math.tau/segments), y+offset,
              z+r*math.sin(t*math.tau/segments))
             for t in range(segments) for r, offset in profile]
    k = len(profile)
    faces = [(i*k+j, ((i+1) % segments)*k+j,
              ((i+1) % segments)*k+(j+1) % k, i*k+(j+1) % k)
             for i in range(segments) for j in range(k)]
    return register(common.mesh(name, verts, faces, M[material], smooth=True))


def annular_sector(name, center, r0, r1, start, end, width, material, steps=24):
    """Closed solid sector, axis Y, angle measured in XZ plane."""
    x, y, z = center
    closed = abs(abs(end-start)-360) < .0001
    angles = [math.radians(start+(end-start)*i/steps) for i in range(steps if closed else steps+1)]
    verts = [(x+r*math.cos(a), y+side*width/2, z+r*math.sin(a))
             for side in (-1, 1) for r in (r0, r1) for a in angles]
    k = len(angles)
    faces = []
    for i in range(k if closed else k-1):
        j = (i+1) % k
        faces += [(i, j, k+j, k+i),
                  (2*k+i, 3*k+i, 3*k+j, 2*k+j),
                  (i, 2*k+i, 2*k+j, j),
                  (k+i, k+j, 3*k+j, 3*k+i)]
    if not closed:
        faces += [(0, k, 3*k, 2*k), (k-1, 3*k-1, 4*k-1, 2*k-1)]
    obj = common.mesh(name, verts, faces, M[material], bevel=.0006)
    # Continuous curved bands shade smoothly; flat side surfaces stay planar.
    for i, face in enumerate(obj.data.polygons):
        face.use_smooth = i < (k if closed else k-1)*4 and i % 4 in (2,3)
    return register(obj)


def fastener(name, loc, radius=.006, depth=.006, axis=(0, 1, 0)):
    return cyl(name, loc, radius, depth, 'Brushed steel', axis, 6, .0005)


def prepare_assemblies():
    """Apply modifiers, recalc outward normals, join only named static assemblies.

    No geometry-decimation or custom-normal transfer is needed. common._prepare
    assigns each resulting assembly its own UV0 atlas before exact-byte export.
    """
    # Do not bevel every longitudinal edge of an already smooth cylinder/arc.
    # Fine features receive a single chamfer instead of invisible micro-facets.
    for objects in GROUPS.values():
        for obj in objects:
            for modifier in obj.modifiers:
                if modifier.type == 'BEVEL':
                    modifier.limit_method = 'ANGLE'
                    modifier.angle_limit = math.radians(43)
                    modifier.segments = 2 if modifier.width >= .002 else 1
    bpy.ops.object.select_all(action='DESELECT')
    for name, objects in GROUPS.items():
        if not objects:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.convert(target='MESH')
        meshes = list(bpy.context.selected_objects)
        # Normals on original closed custom prisms/tire sections are reconciled
        # before modifier results are joined, without welding intersections.
        for obj in meshes:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            for layer in list(obj.data.uv_layers):
                obj.data.uv_layers.remove(layer)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
        bpy.context.object.name = name
        bpy.context.object.data.name = name+' mesh'


def scooter_wheel(label, x, motor=False):
    group(label+' wheel assembly')
    z = .125
    profile = [(.076, -.021), (.087, -.027), (.108, -.028),
               (.120, -.021), (.124, -.014), (.125, -.009),
               (.1239, -.008), (.1239, -.006), (.125, -.005),
               (.125, .005), (.1239, .006), (.1239, .008),
               (.125, .009), (.124, .014), (.120, .021),
               (.108, .028), (.087, .027), (.076, .021)]
    lathe_wheel(label+' road tire with circumferential grooves', (x, 0, z), profile, 'Tire rubber')
    for side in (-1, 1):
        ring(label+' tire molded sidewall ring', (x, side*.0275, z), .098, .0009, 'Rubber tread edge', 64, 6)
    cyl(label+' cast wheel rim', (x, 0, z), .079, .043, 'Satin aluminum', (0, 1, 0), 48, .002)
    for side in (-1, 1):
        cyl(label+(' motor end cover' if motor else ' hub inner disc'), (x, side*.025, z),
            .069 if motor else .062, .008, 'Graphite powder coat', (0, 1, 0), 48, .001)
        if motor:
            for i in range(10):
                a = i*math.tau/10
                outline = [(.024, -.004), (.062, -.004), (.065, .004), (.025, .005)]
                rotated = [(x+r*math.cos(a)-t*math.sin(a), z+r*math.sin(a)+t*math.cos(a)) for r,t in outline]
                polyprism(label+' motor cooling rib', rotated, 1, side*.031-.0015, side*.031+.0015, 'Dark axle steel', .0007)
        else:
            for i in range(5):
                a = i*math.tau/5
                outline = [(.016, -.010), (.064, -.006), (.067, .005), (.016, .012)]
                rotated = [(x+r*math.cos(a)-t*math.sin(a), z+r*math.sin(a)+t*math.cos(a)) for r,t in outline]
                polyprism(label+' broad cast rim spoke', rotated, 1, side*.030-.003, side*.030+.003, 'Satin aluminum', .0015)
        cyl(label+' axle hub', (x, side*.034, z), .019, .016, 'Dark axle steel', (0, 1, 0), 24, .001)
    rod(label+' axle', (x, -.061, z), (x, .061, z), .0065, 'Brushed steel', 16)


def electric_kick_scooter():
    rear, front = -.447, .455
    scooter_wheel('Rear hub-motor', rear, True)
    scooter_wheel('Front', front, False)
    group('Battery deck and underside assembly')
    outline = [(-.385, -.066), (-.358, -.084), (.230, -.084), (.278, -.056),
               (.278, .056), (.230, .084), (-.358, .084), (-.385, .066)]
    polyprism('Rounded battery deck enclosure', outline, 2, .133, .193, 'Slate blue coating', .008)
    outline2 = [(x*.985, y*.94) for x,y in outline]
    polyprism('Underside battery service cover', outline2, 2, .129, .137, 'Graphite powder coat', .003)
    for y in (-.076, .076):
        box('Deck edge protective strip', (-.058, y, .164), (.57, .011, .021), 'Graphite powder coat', .004)
    for x in (-.30, .18):
        for y in (-.053, .053):
            fastener('Recessed underside service screw', (x, y, .129), .004, .003, (0, 0, 1))
    # Rounded grip mat with modest physical ribbing, rather than image textures.
    group('Footboard traction mat')
    outline = [(-.345, -.061), (-.33, -.068), (.205, -.068), (.239, -.046),
               (.239, .046), (.205, .068), (-.33, .068), (-.345, .061)]
    polyprism('Inset nonslip deck mat', outline, 2, .192, .198, 'Grip and tread rubber', .002)
    for i in range(13):
        x = -.31+i*.041
        for side in (-1, 1):
            box('Raised interrupted deck grip rib', (x, side*.039, .199), (.0035, .041, .002), 'Rubber tread edge', .0005, (0,0,-side*.24))

    group('Rear swingarm and brake assembly')
    for side in (-1, 1):
        outline = [(-.459, .110), (-.472, .143), (-.403, .190), (-.315, .183), (-.317, .149)]
        polyprism('Rear wheel swingarm cheek', outline, 1, side*.049-.007, side*.049+.007, 'Graphite powder coat', .005)
        fastener('Rear axle nut', (rear, side*.060, .125), .008, .008)
    # Disc has a real open annular band and attached spokes, not a full black disk.
    annular_sector('Rear brake rotor annulus', (rear,-.039,.125), .048,.062,0,360,.003,'Brushed steel',64)
    cyl('Rear rotor center', (rear,-.039,.125), .019,.003,'Brushed steel',(0,1,0),24,.0004)
    for i in range(6):
        a=i*math.tau/6
        rod('Rear rotor spoke',(rear+.016*math.cos(a),-.039,.125+.016*math.sin(a)),
            (rear+.052*math.cos(a+.10),-.039,.125+.052*math.sin(a+.10)),.003,'Brushed steel',10,.0003)
    box('Rear brake caliper housing',(-.407,-.042,.172),(.045,.030,.027),'Dark axle steel',.006, (0,-.42,0))
    box('Rear caliper attachment',(-.385,-.051,.174),(.031,.013,.020),'Graphite powder coat',.003)

    group('Deck gooseneck and folding collar')
    outline = [(.212,.143),(.285,.151),(.367,.232),(.412,.306),(.397,.351),
               (.362,.343),(.334,.275),(.277,.215),(.217,.194)]
    polyprism('Cast curved deck gooseneck',outline,1,-.030,.030,'Slate blue coating',.008)
    # Folding boss is visibly connected to both neck and stem in a locked pose.
    cyl('Folding hinge body',(.382,0,.331),.034,.083,'Graphite powder coat',(0,1,0),32,.002)
    for side in (-1,1):
        fastener('Folding pivot cap',(.382,side*.046,.331),.011,.008)
    rod('Stem folding collar',(.379,0,.335),(.372,0,.391),.028,'Graphite powder coat',32,.003)
    box('Folding latch closed lever',(.350,-.036,.369),(.019,.014,.070),'Brushed steel',.005,(0,-.16,0))
    box('Latch release accent',(.352,-.045,.382),(.014,.008,.023),'Amber reflector',.002)

    group('Front fork assembly')
    for side in (-1,1):
        pts = bezier([(.406,side*.030,.294),(.413,side*.042,.246),
                      (.444,side*.045,.171),(.455,side*.045,.125)],12)
        tube('Swept front fork leg',pts,.013,'Graphite powder coat')
        cyl('Front axle dropout',(.455,side*.045,.125),.022,.014,'Graphite powder coat',(0,1,0),24,.002)
        fastener('Front axle cap',(.455,side*.061,.125),.009,.008)
        box('Fork amber reflector surround',(.434,side*.056,.205),(.046,.010,.020),'Dark axle steel',.004,(0,-.65,0))
        box('Fork amber reflector lens',(.434,side*.062,.205),(.036,.004,.012),'Amber reflector',.003,(0,-.65,0))
    rod('Fork crown',(.405,-.044,.291),(.405,.044,.291),.023,'Graphite powder coat',24,.002)
    rod('Lower steering bearing',(.406,0,.282),(.396,0,.324),.023,'Brushed steel',28,.002)

    group('Steering stem and handlebar')
    rod('Main raked steering mast',(.374,0,.386),(.270,0,1.119),.0205,'Slate blue coating',32,.002)
    rod('Upper mast collar',(.277,0,1.073),(.270,0,1.124),.024,'Graphite powder coat',32,.002)
    points = bezier([(.285,-.265,1.123),(.285,-.20,1.123),(.270,-.12,1.134),(.270,0,1.134),
                     (.270,.12,1.134),(.285,.20,1.123),(.285,.265,1.123)],14)
    tube('One-piece gently swept handlebar',points,.011,'Graphite powder coat')
    cyl('Handlebar clamp front cap',(.293,0,1.126),.023,.020,'Graphite powder coat',(1,0,0),24,.002)
    fastener('Handlebar clamp fixing',(.305,0,1.126),.006,.005,(1,0,0))

    group('Handle grips and riding controls')
    for side in (-1,1):
        rod('Ergonomic rubber handgrip',(.281,side*.157,1.125),(.285,side*.268,1.123),.017,'Grip and tread rubber',28,.002)
        for j in range(8):
            y=side*(.169+j*.012)
            ring('Shallow handgrip rib',(.284,y,1.124),.0171,.0007,'Rubber tread edge',24,4)
        cyl('Grip bar-end plug',(.285,side*.272,1.123),.0178,.008,'Graphite powder coat',(0,1,0),24,.002)
    cyl('Brake lever bar clamp',(.277,-.135,1.127),.017,.024,'Graphite powder coat',(0,1,0),24,.001)
    box('Brake lever master body',(.307,-.140,1.112),(.050,.033,.026),'Graphite powder coat',.006)
    tube('Curved brake lever',bezier([(.328,-.143,1.109),(.349,-.151,1.104),(.352,-.204,1.099),(.335,-.233,1.102)],14),.0045,'Satin aluminum',2)
    cyl('Brake lever pivot',(.324,-.143,1.120),.005,.006,'Brushed steel',(0,0,1),16,.0004)
    cyl('Throttle collar',(.277,.136,1.127),.018,.023,'Graphite powder coat',(0,1,0),24,.001)
    box('Thumb throttle paddle',(.286,.132,1.092),(.028,.022,.038),'Grip and tread rubber',.006,(0,-.30,0))
    box('Small control housing',(.261,0,1.143),(.065,.052,.025),'Graphite powder coat',.008,(0,-.20,0))
    box('Inset display lens',(.259,0,1.158),(.047,.037,.004),'Display glass',.003,(0,-.20,0))
    # Restrained non-linguistic indication; no brand, invented speed or rating.
    for i in range(3):
        box('Display battery indicator segment',(.248+i*.007,-.006,1.162),(.003,.009,.001),'Display segments',.0002,(0,-.20,0))
    cyl('Control power button',(.279,0,1.161),.0045,.002,'Rubber tread edge',(0,0,1),16,.0004)

    group('Connected brake cable and wire guides')
    pts = bezier([(.324,-.119,1.111),(.376,-.085,1.081),(.353,-.038,1.003),(.308,-.027,.950),
                  (.316,-.027,.843),(.340,-.027,.615),(.371,-.028,.397),
                  (.373,-.030,.284),(.251,-.058,.175),(.170,-.062,.158),
                  (-.020,-.070,.151),(-.235,-.067,.150),(-.394,-.052,.175)],14)
    tube('Single continuous brake cable housing',pts,.0028,'Grip and tread rubber',2)
    for z in (.54,.80,.99):
        x=.374-(z-.386)*(.104/.733)
        rod('Cable guide band',(x+.0005,0,z-.006),(x-.0015,0,z+.006),.022,'Graphite powder coat',24,.0007)

    group('Front and rear mudguards with lamps')
    annular_sector('Front close-fitting mudguard',(.455,0,.125),.137,.143,14,168,.074,'Graphite powder coat',38)
    annular_sector('Rear close-fitting mudguard',(-.447,0,.125),.136,.144,20,195,.077,'Graphite powder coat',42)
    for side in (-1,1):
        rod('Rear mudguard stay',(-.447,side*.049,.125),(-.508,side*.040,.248),.0038,'Brushed steel',12,.0005)
    box('Rear lamp bracket',(-.582,0,.163),(.016,.046,.033),'Graphite powder coat',.004,(0,.23,0))
    box('Rear red tail reflector',(-.591,0,.164),(.006,.035,.020),'Red reflector',.003,(0,.23,0))
    rod('Headlamp mounting boss',(.285,0,1.014),(.314,0,1.018),.012,'Graphite powder coat',24,.001)
    cyl('Compact forward lamp shell',(.328,0,1.020),.022,.037,'Graphite powder coat',(1,0,.06),32,.003)
    cyl('Forward headlamp lens',(.348,0,1.021),.0175,.005,'Headlamp lens',(1,0,.06),32,.001)
    # Side reflectors are attached to deck, not floating decoration.
    for side in (-1,1):
        box('Deck rear reflector trim',(-.298,side*.084,.165),(.075,.006,.022),'Graphite powder coat',.004)
        box('Deck rear red reflector',(-.298,side*.088,.165),(.064,.003,.014),'Red reflector',.002)

    group('Deployed kickstand assembly')
    cyl('Kickstand pivot boss',(-.168,.081,.145),.015,.020,'Dark axle steel',(0,1,0),24,.001)
    tube('Deployed side stand',bezier([(-.168,.091,.143),(-.173,.111,.111),(-.199,.143,.050),(-.226,.163,.008)],14),.006,'Brushed steel',2)
    box('Kickstand rubber foot',(-.227,.163,.007),(.040,.026,.014),'Grip and tread rubber',.005)


def sack_wheel(side):
    label = 'Left' if side < 0 else 'Right'
    group(label+' pneumatic wheel assembly')
    x, y, z = -.106, side*.240, SACK_AXLE_Z
    profile = [(.066,-.029),(.081,-.036),(.110,-.038),(.125,-.028),(.131,-.015),
               (.132,0),(.131,.015),(.125,.028),(.110,.038),(.081,.036),(.066,.029)]
    lathe_wheel(label+' pneumatic sack-truck tire',(x,y,z),profile,'Tire rubber',64)
    # Broad low ribs lie on the curved crown and merge into each tire sidewall.
    # These are static tread geometry, not a traction or material simulation.
    for i in range(24):
        a=i*math.tau/24
        points=[]
        for k in range(7):
            t=-1+2*k/6
            yy=.029*t
            rr=.1328-.006*(abs(t)**2)
            aa=a+.040*t
            points.append((x+rr*math.cos(aa),y+yy,z+rr*math.sin(aa)))
        tube(label+' molded transverse tire tread',points,.0017,'Rubber tread edge',1)
    for s in (-1,1):
        ring(label+' sidewall bead',(x,y+s*.036,z),.090,.0011,'Rubber tread edge',56,6)
    cyl(label+' pressed steel rim',(x,y,z),.068,.059,'Warm ochre powder coat',(0,1,0),48,.003)
    for s in (-1,1):
        cyl(label+' recessed hub dish',(x,y+s*.031,z),.053,.005,'Brushed steel',(0,1,0),40,.002)
        ring(label+' rim dish lip',(x,y+s*.034,z),.053,.003,'Satin aluminum',48,6)
        for i in range(5):
            a=i*math.tau/5
            start=(x+.022*math.cos(a),y+s*.035,z+.022*math.sin(a))
            end=(x+.047*math.cos(a),y+s*.035,z+.047*math.sin(a))
            rod(label+' pressed radial hub ridge',start,end,.003,'Satin aluminum',10,.0005)
        cyl(label+' axle hub',(x,y+s*.039,z),.023,.019,'Warm ochre powder coat',(0,1,0),28,.002)
    cyl(label+' axle end cap',(x,y+side*.052,z),.014,.009,'Dark axle steel',(0,1,0),24,.001)


def sack_hand_truck():
    sack_wheel(-1)
    sack_wheel(1)
    group('Curved upright tubular load frame')
    for side in (-1,1):
        y=side*.173
        pts=bezier([(0,y,.030),(-.003,y,.33),(-.015,y,.78),(-.026,y,1.069),
                    (-.030,y,1.136),(-.072,y,1.181),(-.134,y,1.181),
                    (-.162,y,1.181),(-.205,y,1.181),(-.240,y,1.181)],18)
        tube('Continuous upright and swept-back handle',pts,.016,'Warm ochre powder coat',2)
    for z in (.230,.478,.742,1.025):
        x=-.026*(z-.030)/1.039
        pts=bezier([(x,-.174,z),(x+.013,-.095,z),(x+.022,.095,z),(x,.174,z)],14)
        tube('Bowed transverse load support',pts,.012,'Warm ochre powder coat',2)
    # Vertical straps prevent a tall box/sack from falling between the crossbars.
    for y in (-.061,.061):
        outline=[(.013,.123),(.016,.245),(.001,.786),(-.013,1.028),
                 (-.019,1.028),(-.005,.786),(.010,.245),(.007,.123)]
        polyprism('Continuous upright load-retaining strap',outline,1,y-.014,y+.014,'Warm ochre powder coat',.0015)

    group('Reinforced toe plate assembly')
    outline=[(-.018,-.196),(.219,-.196),(.256,-.167),(.256,.167),(.219,.196),(-.018,.196)]
    plate=polyprism('Deep chamfer-corner lifting toe plate',outline,2,.005,.015,'Warm ochre powder coat',.0025)
    # The leading toe reaches the floor while the rear remains reinforced.
    # This is visible resting geometry, not a claimed lifting specification.
    for vertex in plate.data.vertices:
        vertex.co.z += .008*(1-vertex.co.x/.256)-.005
    # Bent back flange is one solid at the frame/base intersection.
    box('Toe plate bent rear flange',(-.013,0,.056),(.014,.391,.091),'Warm ochre powder coat',.002)
    for y in (-.116,.116):
        box('Longitudinal toe plate stiffening emboss',(.083,y,.0174),(.137,.018,.004),'Warm ochre powder coat',.002,(0,.03125,0))
    for side in (-1,1):
        outline=[(-.018,.018),(.074,.018),(-.018,.126)]
        polyprism('Toe plate side gusset',outline,1,side*.173-.005,side*.173+.005,'Warm ochre powder coat',.0015)
        fastener('Toe plate frame fixing',(-.020,side*.173,.070),.006,.006,(1,0,0))

    group('Axle and structural wheel brackets')
    rod('Continuous transverse steel axle',(-.106,-.293,SACK_AXLE_Z),(-.106,.293,SACK_AXLE_Z),.010,'Brushed steel',28,.001)
    for side in (-1,1):
        # Two-sided brackets meet the upright and axle, leaving the tires clear.
        outline=[(-.020,.070),(-.134,.105),(-.135,.153),(-.033,.250),(-.020,.250)]
        polyprism('Upright-to-axle steel cheek bracket',outline,1,side*.174-.006,side*.174+.006,'Warm ochre powder coat',.003)
        cyl('Axle bracket bearing collar',(-.106,side*.174,SACK_AXLE_Z),.022,.030,'Dark axle steel',(0,1,0),28,.002)
        fastener('Axle bracket retaining fastener',(-.030,side*.184,.213),.007,.007)
    rod('Lower frame crossbrace',(-.019,-.173,.117),(-.019,.173,.117),.012,'Warm ochre powder coat',28,.001)

    group('Rear stair glide supports')
    for side in (-1,1):
        y=side*.173
        pts=bezier([(-.014,y,.216),(-.060,y,.253),(-.095,y,.302),(-.099,y,.347),
                    (-.101,y,.447),(-.104,y,.627),(-.099,y,.724),
                    (-.091,y,.772),(-.054,y,.823),(-.020,y,.842)],16)
        tube('Curved rear glide support rail',pts,.012,'Warm ochre powder coat',2)
        box('Replaceable rear glide wear strip',(-.111,y,.537),(.015,.029,.345),'Grip and tread rubber',.005,(0,-.012,0))
        for z in (.390,.684):
            fastener('Rear glide recessed fixing',(-.121,y,z),.004,.004,(1,0,0))

    group('Protected ergonomic handle grips')
    for side in (-1,1):
        y=side*.173
        rod('Molded rearward hand grip',(-.128,y,1.181),(-.246,y,1.181),.020,'Grip and tread rubber',32,.003)
        for i in range(7):
            # Axis X rings: rotate the authored Y-axis torus into the grip axis.
            obj=ring('Molded handgrip ring',(-.143-i*.014,y,1.181),.0201,.0008,'Rubber tread edge',24,4)
            obj.rotation_euler=(0,math.pi/2,0)
        cyl('Flared handle grip stop',(-.126,y,1.181),.023,.010,'Grip and tread rubber',(1,0,0),28,.002)
        cyl('Rounded handgrip end plug',(-.250,y,1.181),.020,.008,'Dark axle steel',(1,0,0),28,.002)


ASSETS = {
    'city-electric-kick-scooter': dict(
        build=electric_kick_scooter,
        title='電動キックスクーター', title_en='Electric kick scooter',
        description='バッテリーデッキ、前後のタイヤ、ハブモーター、折りたたみ部、ブレーキレバーとケーブル、泥よけ、ライト、反射板、展開したスタンドを備えた無銘の電動キックスクーター。静止した配置用小道具で、走行機能・安全性・機構の作動は未検証。',
        description_en='Unbranded electric kick scooter with battery deck, profiled tires, rear hub-motor cover, folding collar, connected brake cable and lever, mudguards, lamps, reflectors and deployed kickstand. Static placement prop; not rigged and not validated for riding, safety or mechanical operation.',
        tags=['scooter', 'electric', 'micromobility', 'transport', 'キックスクーター'],
        azimuth=-61, elevation=19),
    'city-sack-hand-truck': dict(
        build=sack_hand_truck,
        title='二輪の荷運び台車', title_en='Two-wheel sack hand truck',
        description='袋や箱の運搬を表現する、湾曲した鋼管フレーム、奥行きのあるすくい板、荷支え、車軸、空気入りタイヤ風の二輪、グリップ、背面グライドを備えた縦型台車。パレットジャッキや買物カートとは異なる静止小道具。耐荷重・運搬作業・安全性は未検証。',
        description_en='Upright two-wheel hand truck for depicting sack or box hauling, with curved tubular frame, deep toe plate, fixed vertical load-support strips, transverse axle, pneumatic-style tires, protected grips and rear glide rails. Distinct from a pallet jack or basket shopping trolley. Static unrigged prop; no load rating, hauling performance or safety validation.',
        tags=['hand-truck', 'sack-truck', 'dolly', 'logistics', '荷運び', '台車'],
        azimuth=-48, elevation=21),
}


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output','--out',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox')
    parser.add_argument('--only',choices=list(ASSETS))
    parser.add_argument('--qa-extra',action='store_true',help='Render additional opposite-side and underside views of exact GLB.')
    args=parser.parse_args(argv)
    ids=[args.only] if args.only else list(ASSETS)
    for slug in ids:
        if (args.output/slug).exists():
            parser.error('Refusing to overwrite existing asset: '+str(args.output/slug))
    for slug in ids:
        data=ASSETS[slug]
        common.reset(); M.clear(); GROUPS.clear(); materials(); data['build']()
        prepare_assemblies()
        report=common.publish_asset(slug,data['title'],data['title_en'],data['description'],data['description_en'],
            data['tags'],args.output,'scripts/city/compact_mobility.py',data['azimuth'],data['elevation'])
        path=args.output/slug/'asset.json'
        metadata=json.loads(path.read_text())
        metadata['usages'][0]['selectors']=[slug, *GROUPS.keys()]
        metadata['usages'][0]['context']='Original static urban prop created for the Meshcopia library. Selectors name the generator asset ID and the exact exported mesh assemblies. No external deployment or reuse claimed.'
        metadata['uv']='Automatically unwrapped UV0 for each named static assembly; islands can overlap between assemblies. Not a packed unique lightmap or shared trim atlas. Solid-color PBR materials, no image textures. STL carries geometry only, without colors or UVs.'
        metadata['provenance']['alternateFormat']='Binary STL derived from the exact reimported GLB, meters and Y-up. Visual prop only, not manufacturing or print validated.'
        metadata['provenance']['assemblyMethod']='Original closed mesh components with bevels and curved tubes, converted and joined into named static assemblies before export. No external models or texture images; no decimation.'
        path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        if args.qa_extra:
            common.render(args.output/'_qa'/f'{slug}-side.png',-90,12,1000)
            common.render(args.output/'_qa'/f'{slug}-underside.png',130,-24,1000)
        print('COMPACT_MOBILITY_DONE '+slug,flush=True)


if __name__=='__main__':
    main()
