"""Original architectural city props for Meshcopia, CC BY 4.0.
Static visual assemblies, not building/security/electrical/sanitation certifications.
Run with Blender --python script -- --only ID --output staging, or python+bpy.
"""
import bpy,math,sys,json,argparse,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
import infrastructure as I
import infrastructure_extra as E
from common import reset,publish_asset,render
box=E.box;cyl=E.cyl;bolt=E.bolt;bar=E.bar;mesh=E.mesh

def glass(name,color=(.25,.44,.48),alpha=.12):
    m=I.mat(name,color,0,.12);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=alpha;p.inputs['IOR'].default_value=1.45
    m.diffuse_color=(*color,alpha);m.surface_render_method='DITHERED'
    return m

def transform_since(before,pivot,angle,axis='Z'):
    transform=Matrix.Translation(Vector(pivot))@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-Vector(pivot))
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o.name not in before:o.matrix_world=transform@o.matrix_world

def rectangular_frame(name,x,y,z,w,h,rail,depth,m):
    for xx in [x-w/2+rail/2,x+w/2-rail/2]:box(name+' vertical',(xx,y,z+h/2),(rail,depth,h),m,.003)
    for zz in [z+rail/2,z+h-rail/2]:box(name+' horizontal',(x,y,zz),(w-2*rail,depth,rail),m,.003)

def glazed_entry_door():
    p=I.palette();metal=I.mat('Door anodized aluminum',(.18,.225,.24),.78,.36);g=glass('Entry door transparent glazing')
    for x in [-.515,.515]:box('Outer entry jamb',(x,.015,1.11),(.07,.145,2.22),metal,.006)
    box('Outer entry head',(0,.015,2.185),(.96,.145,.07),metal,.006)
    box('Accessible shallow threshold',(0,-.005,.015),(1.03,.20,.03),p['steel'],.006)
    for y in [-.07,-.025,.02,.065]:box('Threshold traction ridge',(0,y,.031),(.94,.006,.004),p['edge'],.0006)
    for x in [-.478,.478]:box('Outer compression seal',(x,-.01,1.105),(.008,.014,2.09),p['dark'],.002)
    box('Head compression seal',(0,-.01,2.149),(.95,.014,.008),p['dark'],.002)
    before={o.name for o in bpy.context.scene.objects}
    rectangular_frame('Door leaf rail',0,-.025,.04,.938,2.102,.055,.055,metal)
    box('Glazed leaf lower kick plate',(0,-.025,.177),(.828,.038,.164),metal,.005)
    rectangular_frame('Glazing EPDM seal',0,-.031,.275,.836,1.815,.012,.015,p['dark'])
    box('Tempered transparent glass pane',(0,-.025,1.1825),(.812,.008,1.791),g,.001)
    for y in [-.083]:
        for z in [.93,1.31]:bar('Pull handle stand off',(.342,-.025,z),(.342,y,z),.018,.018,p['steel'],.003)
        bar('Vertical door pull',(.342,y,.93),(.342,y,1.31),.024,.024,p['steel'],.005)
    for x in [-.37,.37]:box('Interior push bar mounting shoe',(x,.025,1.06),(.075,.065,.065),metal,.008)
    bar('Interior horizontal push bar',(-.37,.067,1.06),(.37,.067,1.06),.035,.028,p['steel'],.006)
    cyl('Lock escutcheon',(.342,-.058,.80),.020,.008,p['steel'],'Y',24,.001)
    box('Lock key recess',(.342,-.063,.8),(.003,.002,.013),p['dark'],.0004)
    box('Lower sweep gasket',(0,-.025,.045),(.83,.048,.012),p['dark'],.002)
    # Leaf is statically ajar; hinges remain on the fixed jamb at the swing axis.
    transform_since(before,(-.469,-.025,.04),math.radians(-12))
    for z in [.31,1.10,1.90]:
        cyl('Door hinge barrel',(-.477,-.025,z),.013,.105,p['steel'],n=24,b=.001)
        for dz in [-.036,0,.036]:I.ring('Hinge knuckle seam',(-.477,-.025,z+dz),.013,.0007,p['dark'],n=24,k=6)
        for dx in [-.026,.026]:box('Hinge fixing leaf',(-.477+dx,-.012,z),(.034,.006,.095),p['steel'],.001)
    # Compact closer body and articulated arm above the opening.
    box('Door closer housing',(-.27,-.087,2.175),(.28,.075,.055),p['steel'],.009)
    q=Vector((-.469,-.025,0))+Matrix.Rotation(math.radians(-12),3,'Z')@Vector((.589,0,2.145))
    box('Closer leaf mounting shoe',q,(.06,.03,.018),p['steel'],.002)
    bar('Closer link one',(-.23,-.11,2.20),(-.05,-.19,2.20),.017,.013,p['steel'],.001)
    bar('Closer link two',(-.05,-.19,2.20),(q.x,q.y,q.z+.009),.017,.013,p['steel'],.001)
    return ('city-glazed-entry-door','ガラス入り店舗入口ドア','Glazed shop entry door','少し開いたガラス戸、アルミ枠、気密パッキン、丁番、引手、浅い敷居と上部クローザーを備えた店舗入口。','A slightly open glazed entry with aluminum framing, transparent glass, compression seals, hinges, pull handles, shallow threshold and closer. Static visual prop.',['door','entry','glazed','shopfront','architecture','ガラス戸'])

def wall_intercom():
    p=I.palette();body=I.mat('Intercom dark powder coat',(.055,.073,.08),.46,.42);steel=p['steel']
    box('Rear mounting gasket',(0,.035,.155),(.126,.012,.31),p['dark'],.009)
    box('Intercom rear case',(0,.018,.155),(.12,.042,.304),body,.008)
    # Separate front frame and real speaker apertures: no fake painted holes.
    for x in [-.054,.054]:box('Faceplate side rail',(x,-.009,.155),(.012,.012,.286),steel,.002)
    for z in [.018,.292]:box('Faceplate end rail',(0,-.009,z),(.096,.012,.012),steel,.002)
    box('Camera and display panel',(0,-.01,.240),(.096,.014,.091),steel,.003)
    I.annulus('Camera bezel',(0,-.02,.264),.014,.010,.007,body,'Y',32)
    lens=glass('Intercom optical glass',(.018,.04,.055),.95)
    cyl('Intercom camera lens',(0,-.025,.264),.009,.003,lens,'Y',32,.0004)
    box('Small dark display surround',(0,-.02,.220),(.075,.007,.029),body,.004)
    box('Blank display glass',(0,-.025,.220),(.064,.003,.019),I.mat('Blank inactive intercom display',(.012,.029,.034),.1,.18),.002)
    # Speaker window bounded by separate sheet members; each horizontal slit is open.
    box('Speaker black backing',(0,.014,.158),(.095,.004,.074),p['dark'],.001)
    for i in range(9):box('Perforated speaker grille bridge',(0,-.01,.126+i*.0078),(.096,.014,.0035),steel,.0005)
    for x in [-.038,-.019,0,.019,.038]:box('Speaker grille rear vertical support',(x,-.001,.157),(.002,.004,.068),body,.0003)
    box('Call button lower faceplate',(0,-.01,.072),(.096,.014,.081),steel,.003)
    I.annulus('Call button ring bezel',(0,-.023,.078),.022,.018,.006,p['dark'],'Y',40)
    cyl('Unbranded call button',(0,-.027,.078),.017,.008,body,'Y',40,.001)
    box('Blank changeable name insert',(0,-.021,.047),(.057,.003,.013),p['paint'],.001)
    for x in [-.041,.041]:
        for z in [.025,.285]:bolt('Faceplate security screw',(x,-.018,z),p['edge'],'Y',.003)
    box('Overhanging weather lip',(0,-.002,.310),(.146,.093,.012),body,.003)
    for x in [-.028,0,.028]:cyl('Small auxiliary key',(x,-.022,.109),.0045,.005,body,'Y',16,.0005)
    return ('city-wall-intercom','壁付けインターホン','Wall entry intercom','開口したスピーカーグリル、カメラレンズ、無表示画面、呼出ボタンと背面ガスケットを持つ無印インターホン。','An unbranded entry intercom with real speaker-grille slots, recessed camera lens, blank display, call button and rear mounting gasket. Static nonfunctional prop.',['intercom','entry','wall','speaker','access','インターホン'])

def casement_window():
    p=I.palette();metal=I.mat('Window ivory powder coat',(.63,.64,.59),.2,.45);g=glass('Window transparent glazing')
    rectangular_frame('Window fixed outer frame',0,0,0,1.40,1.20,.065,.135,metal)
    box('Window central mullion',(0,-.002,.60),(.05,.12,1.07),metal,.004)
    # Slightly sloping sill and real open drainage weeps in its front lip.
    box('Sloped exterior sill',(0,-.047,.022),(1.46,.235,.035),p['steel'],.005,rot=(math.radians(4),0,0))
    for side in [-1,1]:
        cx=side*.34;before={o.name for o in bpy.context.scene.objects}
        rectangular_frame('Opening sash perimeter',cx,-.018,.078,.612,1.047,.045,.058,metal)
        rectangular_frame('Window glazing gasket',cx,-.021,.119,.53,.965,.010,.018,p['dark'])
        box('Casement glass pane',(cx,-.018,.6015),(.508,.008,.943),g,.0008)
        x=cx-side*.247
        box('Window latch base',(x,-.054,.58),(.027,.016,.085),p['steel'],.004)
        bar('Window lever handle',(x,-.066,.58),(x,-.066,.66),.014,.014,p['steel'],.003)
        if side==1:transform_since(before,(.646,-.018,.078),math.radians(20))
        for z in [.25,.95]:
            cyl('Sash hinge knuckle',(side*.649,-.018,z),.009,.085,p['steel'],n=20,b=.001)
            for dz in [-.025,.025]:I.ring('Hinge seam',(side*.649,-.018,z+dz),.009,.0006,p['dark'],n=20,k=6)
    # Lower weep slots are physical gaps between front sill lip segments.
    for x,w in [(-.58,.22),(-.22,.42),(.22,.42),(.58,.22)]:box('Sill drip edge segment',(x,-.158,.016),(w,.011,.024),metal,.002)
    return ('city-casement-window','片開き窓ユニット','Twin casement window unit','透明ガラス入りの二枚建て窓。片側の開いたサッシ、気密材、丁番、ハンドル、排水隙間のある水切りを含む。','A twin glazed casement unit with one sash statically open, transparent panes, seals, hinges, handles and a sill with real drainage gaps.',['window','casement','glazing','building','sill','窓'])

def solar_module_rack():
    p=I.palette();aluminum=I.mat('Solar frame anodized aluminum',(.36,.42,.46),.85,.34)
    cell=I.mat('Photovoltaic silicon cells',(.012,.029,.075),.32,.27);bus=I.mat('Cell silver conductors',(.42,.48,.55),.85,.30)
    polymer=I.mat('PV backsheet',(.72,.73,.68),.0,.72);glassmat=glass('Solar protective glass',(.30,.40,.48),.07)
    # One complete module, sixty separated cells; supported at a static 20-degree pitch.
    before={o.name for o in bpy.context.scene.objects}
    rectangular_frame('Module perimeter',0,0,0,1.10,1.86,.032,.04,aluminum)
    # rectangular_frame authors vertical XZ. Rotate the module flat, then tilt as a unit.
    # All remaining module geometry is authored in the same XZ plane.
    box('Solar backsheet',(0,.012,.93),(1.036,.009,1.796),polymer,.001)
    for ix in range(6):
        for iz in range(10):
            x=-.425+ix*.17;z=.133+iz*.177
            box('Individual silicon cell %02d %02d'%(ix,iz),(x,-.004,z),(.161,.003,.168),cell,.003)
            for dx in [-.044,0,.044]:box('Fine cell busbar',(x+dx,-.0062,z),(.0015,.0006,.16),bus,.0001)
    box('Solar transparent cover glass',(0,-.009,.93),(1.027,.005,1.786),glassmat,.001)
    # Rotate vertical panel around X by 110 degrees: positive local Z becomes rising +Y.
    T=Matrix.Translation(Vector((0,0,.48)))@Matrix.Rotation(math.radians(-70),4,'X')@Matrix.Translation(Vector((0,0,-.93)))
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o.name not in before:o.matrix_world=T@o.matrix_world
    # Rails follow panel underside at y +- .70. Ballasts and diagonal legs are connected.
    for y in [-.70,.70]:
        z=.48+y*math.tan(math.radians(20))-.043
        box('Crosswise module support rail',(0,y,z),(1.15,.052,.045),aluminum,.005)
        for x in [-.47,.47]:
            box('Rack ballast foot',(x,y,.045),(.23,.28,.09),I.mat('Concrete ballast %.2f %.2f'%(x,y),(.32,.33,.31),0,.9),.012)
            bar('Rack upright support',(x,y,.09),(x,y,z-.02),.032,.036,aluminum,.003)
            # Small top clamp embraces the visible module edge.
            cx=math.copysign(.548,x)
            box('Module edge clamp',(cx,y,z+.065),(.065,.055,.013),p['steel'],.002,rot=(math.radians(20),0,0))
            box('Module clamp side web',(math.copysign(.566,x),y,z+.034),(.018,.042,.055),p['steel'],.002)
            bolt('Module clamp bolt',(cx,y,z+.075),p['edge'],r=.005)
    for x in [-.47,.47]:
        bar('Rack longitudinal base',(x,-.70,.11),(x,.70,.11),.035,.035,aluminum,.003)
        bar('Rack diagonal strut',(x,-.68,.12),(x,.70,.48+.70*math.tan(math.radians(20))-.065),.026,.031,aluminum,.003)
    # Backside electrical detail is modeled but nonfunctional and unconnected to a circuit.
    junction=box('Rear junction box',(0,.24,.48+.24*math.tan(math.radians(20))-.065),(.19,.105,.034),p['black'],.007)
    junction.rotation_euler[0]=math.radians(20)
    for x in [-.055,.055]:
        pts=[(x,.24,.49),(x,.32,.43),(x,.44,.36),(x,.55,.35)]
        # Solid cable curves have sealed caps; no electrical simulation.
        from common import tube
        tube('Short rear solar cable',pts,.0045,p['dark'],2)
        cyl('Solar cable connector',(x,.56,.35),.009,.045,p['black'],'Y',20,.001)
    return ('city-solar-module-rack','架台付き太陽電池モジュール','Solar module on ballast rack','60枚のセル、透明保護板、固定クランプ、三角補強架台、重し、背面接続箱と短いケーブルを備えた太陽電池模型。','A single solar module with sixty cells, transparent cover, clamps, braced ballast rack, rear junction box and short connector cables. Static nonfunctional electrical-equipment prop.',['solar','photovoltaic','module','rack','roof','太陽電池'])

def scaffold_bay():
    p=I.palette();zinc=I.mat('Scaffold galvanized tube',(.34,.40,.42),.82,.43);wood=I.mat('Scaffold treated timber deck',(.31,.205,.105),0,.82)
    for x in [-1.16,1.16]:
        for y in [-.61,.61]:
            box('Scaffold ground bearing plate',(x,y,.018),(.23,.23,.036),zinc,.006)
            cyl('Screw jack stem',(x,y,.19),.017,.31,p['edge'],n=24,b=.001)
            for i in range(8):I.ring('Screw jack thread',(x,y,.065+i*.022),.018,.002,zinc,n=20,k=4)
            cyl('Adjustable jack collar',(x,y,.29),.033,.032,zinc,n=24,b=.002)
            bar('Jack collar turning bar',(x-.09,y,.29),(x+.09,y,.29),.014,.014,zinc,.001)
            I.annulus('Hollow scaffold standard',(x,y,1.745),.025,.020,2.91,zinc,n=32)
            for z in [.37,2.045,2.62,3.12]:
                cyl('Standard connection collar',(x,y,z),.035,.055,p['edge'],n=20,b=.002)
                bolt('Collar securing bolt',(x,y-.036,z),zinc,'Y',.007)
    # Every horizontal member spans directly between standards.
    for z in [.37,2.045,2.62,3.12]:
        for y in [-.61,.61]:I.rod('Longitudinal ledger',(-1.16,y,z),(1.16,y,z),.023,zinc,24)
        for x in [-1.16,1.16]:I.rod('End transverse ledger',(x,-.61,z),(x,.61,z),.023,zinc,24)
    for a,b in [((-1.16,.638,.39),(1.16,.638,2.045)),((1.16,.674,.39),(-1.16,.674,2.045)),((-1.19,-.61,.39),(-1.19,.61,2.045))]:
        I.rod('Diagonal scaffold brace',a,b,.016,zinc,20)
        for q in [a,b]:cyl('Brace terminal pin',q,.025,.10,p['edge'],'Y',20,.002)
    for i in range(6):
        y=-.505+i*.202
        box('Individual timber working deck plank',(0,y,2.085),(2.48,.19,.06),wood,.004)
        for x in [-1.10,1.10]:
            box('Deck end reinforcement band',(x,y,2.085),(.075,.192,.063),zinc,.001)
            bolt('Deck plank fastener',(x,y,2.119),p['edge'],r=.004)
    for y in [-.614,.614]:box('Long deck toe board',(0,y,2.195),(2.45,.024,.15),wood,.003)
    for x in [-1.225,1.225]:box('End deck toe board',(x,0,2.195),(.024,1.205,.15),wood,.003)
    # Integrated end ladder meets the lower transom and deck, not a floating accessory.
    for y in [-.24,.24]:I.rod('Access ladder stile',(1.18,y,.37),(1.18,y,2.13),.021,zinc,24)
    for i in range(7):I.rod('Ladder rung',(1.18,-.24,.52+i*.25),(1.18,.24,.52+i*.25),.018,zinc,20)
    return ('city-scaffold-bay','単独足場ベイ','Single scaffold bay','スクリュージャッキ、支柱、接続された水平材と斜材、木製足場板、幅木、上部手すりと側面はしごを持つ一区画。','A single scaffold bay with screw jacks, hollow standards, connected ledgers and braces, timber deck, toe boards, full upper rails and an end ladder. Static visual model, not a load-rated or safety-certified scaffold.',['scaffold','construction','deck','bracing','ladder','足場'])

def portable_toilet():
    p=I.palette();plastic=I.mat('Molded portable cabin teal',(.055,.19,.205),0,.62);rib=I.mat('Molded cabin reinforcement',(.07,.225,.24),0,.56);roofmat=I.mat('Portable cabin roof ivory',(.69,.71,.65),0,.57)
    for x in [-.43,.43]:box('Forklift-compatible skid',(x,0,.044),(.22,1.20,.088),p['black'],.018)
    box('Molded cabin floor',(0,0,.115),(1.18,1.18,.075),p['black'],.025)
    for y in [-.45,-.2,.05,.30,.5]:box('Floor traction ridge',(0,y,.155),(1.04,.012,.006),p['edge'],.001)
    # Three walls are separate thick molded panels. Their upper rear band is vented.
    for x in [-.567,.567]:
        box('Molded side wall',(x,0,1.15),(.045,1.16,2.02),plastic,.018)
        for y in [-.45,-.225,0,.225,.45]:box('Raised side shell rib',(x+math.copysign(.026,x),y,1.15),(.018,.045,1.86),rib,.008)
        for z in [.25,1.06,1.98]:box('Side horizontal stiffener',(x+math.copysign(.030,x),0,z),(.018,1.05,.055),rib,.009)
    box('Molded rear wall',(0,.567,1.11),(1.09,.045,1.94),plastic,.014)
    for x in [-.43,-.215,0,.215,.43]:box('Raised rear shell rib',(x,.598,1.12),(.045,.018,1.83),rib,.008)
    box('Rear vent upper header',(0,.567,2.18),(1.09,.045,.055),plastic,.012)
    for x in [-.48,-.32,-.16,0,.16,.32,.48]:box('Rear vent vertical bridge',(x,.567,2.113),(.028,.045,.08),rib,.003)
    # Front opening frame and shallow connected entrance threshold.
    for x in [-.51,.51]:box('Front cabin door jamb',(x,-.568,1.13),(.10,.075,1.96),plastic,.018)
    box('Door opening header',(0,-.568,2.12),(1.12,.075,.075),plastic,.018)
    box('Entrance threshold',(0,-.58,.16),(.96,.13,.04),p['black'],.006)
    before={o.name for o in bpy.context.scene.objects}
    rectangular_frame('Toilet door perimeter',0,-.592,.18,.91,1.88,.055,.043,plastic)
    box('Toilet door central skin',(0,-.592,1.12),(.8,.035,1.77),plastic,.018)
    for x in [-.32,-.16,0,.16,.32]:box('Door molded vertical rib',(x,-.618,1.13),(.027,.019,1.55),rib,.008)
    box('Door lower horizontal rib',(0,-.62,.33),(.72,.018,.045),rib,.008)
    box('Occupancy latch plate',(.31,-.629,1.13),(.085,.012,.12),p['steel'],.006)
    box('Blank occupancy indicator window',(.31,-.639,1.16),(.044,.006,.020),p['dark'],.003)
    box('Occupancy green indicator',(.31,-.643,1.16),(.027,.003,.012),I.mat('Occupancy indicator green',(.025,.30,.11),0,.58),.001)
    bar('Door exterior latch grip',(.28,-.66,1.105),(.36,-.66,1.105),.018,.023,p['black'],.004)
    for x in [.28,.36]:bar('Latch grip standoff',(x,-.63,1.105),(x,-.66,1.105),.014,.014,p['black'],.002)
    transform_since(before,(-.455,-.592,.18),math.radians(-11))
    for z in [.43,1.12,1.82]:
        cyl('Toilet door hinge barrel',(-.458,-.598,z),.014,.115,p['steel'],n=20,b=.001)
        box('Door hinge mounting plate',(-.49,-.607,z),(.06,.01,.10),p['steel'],.003)
    # Modeled interior seat/tank, intentionally static and without plumbing operation.
    box('Interior waste tank pedestal',(0,.25,.35),(.55,.53,.39),p['black'],.055)
    box('Interior seat support top',(0,.25,.553),(.57,.55,.045),roofmat,.035)
    # Seat opening cuts through the support so it is not a painted disk.
    support=bpy.context.object
    cutter=cyl('Seat aperture cutter',(0,.20,.55),.14,.20,roofmat,n=48,b=0);I.cut(support,cutter)
    seat=I.annulus('Molded toilet seat',(0,.20,.59),.205,.14,.028,roofmat,n=48);seat.scale.y=1.15
    cyl('Dark bowl recess',(0,.20,.43),.137,.015,p['dark'],n=48,b=.001)
    bar('Paper holder spindle',(-.49,-.06,.76),(-.36,-.06,.76),.014,.014,p['steel'],.002)
    cyl('Unbranded paper roll',(-.414,-.06,.76),.052,.085,roofmat,'X',32,.003)
    # Shallow arched roof is an enclosed original extruded shell profile.
    top=[(-.625,2.215),(-.57,2.255),(-.30,2.29),(0,2.305),(.30,2.29),(.57,2.255),(.625,2.215)]
    profile=top+[(y,z-.043) for y,z in reversed(top)]
    E.extrude_x('Arched cabin weather roof',profile,1.25,(0,0,0),roofmat,.006)
    for x in [-.40,0,.40]:I.tube('Roof molded strengthening ridge',[(x,y,z+.007) for y,z in top[1:-1]],.007,roofmat,2)
    crown=[(-.58,2.14),(.58,2.14),(.58,2.21),(.30,2.247),(0,2.262),(-.30,2.247),(-.58,2.21)]
    for x in [-.567,.567]:E.extrude_x('Curved side roof closure',crown,.045,(x,0,0),plastic,.003)
    box('Upper front roof closure',(0,-.568,2.19),(1.10,.055,.065),plastic,.009)
    I.annulus('Hollow rear vent stack',(.46,.63,1.25),.036,.031,2.1,p['black'],n=32)
    for z in [.55,1.75]:bar('Vent wall clip',(.46,.58,z),(.46,.63,z),.045,.025,p['steel'],.002)
    cyl('Vent rain cap',(.46,.63,2.325),.049,.018,p['black'],n=32,b=.003)
    for x in [.44,.48]:bar('Vent cap spacer',(x,.63,2.297),(x,.63,2.318),.006,.006,p['black'],.001)
    return ('city-portable-toilet','仮設トイレキャビン','Portable toilet cabin','補強リブのある樹脂外壁、少し開いた扉と使用表示錠、アーチ屋根、通気管、スキッドと簡易内装を備えた仮設トイレ。','A portable toilet cabin with ribbed molded shell, slightly open latched door, occupancy indicator, arched roof, vent stack, skids and modeled seat interior. Static visualization only, not sanitation or accessibility certified.',['portable toilet','construction','cabin','sanitation','utility','仮設トイレ'])

BUILDERS={'city-glazed-entry-door':glazed_entry_door,'city-wall-intercom':wall_intercom,'city-casement-window':casement_window,'city-solar-module-rack':solar_module_rack,'city-scaffold-bay':scaffold_bay,'city-portable-toilet':portable_toilet}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output','--out',dest='output',type=Path,default=Path(__file__).resolve().parents[2]/'_inbox');parser.add_argument('--only',choices=sorted(BUILDERS));parser.add_argument('--batch',choices=['entry','window-solar','site','all'],default='all')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    groups={'entry':['city-glazed-entry-door','city-wall-intercom'],'window-solar':['city-casement-window','city-solar-module-rack'],'site':['city-scaffold-bay','city-portable-toilet'],'all':list(BUILDERS)}
    chosen={args.only:BUILDERS[args.only]} if args.only else {slug:BUILDERS[slug] for slug in groups[args.batch]}
    existing=[str(args.output/slug) for slug in chosen if (args.output/slug).exists()]
    if existing:parser.error('Refusing to overwrite: '+', '.join(existing))
    for slug,builder in chosen.items():
        reset();spec=builder();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);publish_asset(*spec,out_dir=args.output,generator='scripts/city/infrastructure_architecture.py',azimuth=-60,elevation=20)
        path=args.output/slug/'asset.json';data=json.loads(path.read_text());data['usages'][0]['sourcePaths']+=['scripts/city/infrastructure.py','scripts/city/infrastructure_extra.py']
        if slug in ['city-glazed-entry-door','city-casement-window']:data['uv']+=' Glazing uses alpha-blended PBR transparency; appearance depends on viewer lighting and transparency sorting.'
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        if slug in ['city-solar-module-rack','city-scaffold-bay']:I.render_underside_qa(slug,args.output)

if __name__=='__main__':main()
