"""Original neighbourhood street objects authored by Claude, CC BY 4.0.

No third-party meshes, textures, brand identities, lettering or font files.
Usage: python scripts/city_expansion/frozen/batch-061/scripts/city_expansion/claude_neighborhood_objects.py --out DIR [--only ID ...]
"""
import sys, math, argparse, random
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

GENERATOR = Path(__file__).resolve().relative_to(ROOT).as_posix()


def foliage_blob(name, center, radius, material, seed, squash=.85, rough=.22, subdiv=3):
    """Irregular clipped-foliage mass: icosphere with deterministic Perlin displacement."""
    from mathutils import noise
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1, location=(0, 0, 0)); o = bpy.context.object
    off = Vector((seed * 7.13, seed * 3.71, seed * 1.93))
    for v in o.data.vertices:
        n = v.co.normalized(); d = 1 + rough * noise.noise(n * 2.3 + off) + rough * .45 * noise.noise(n * 6.1 + off)
        v.co = Vector((n.x * radius * d, n.y * radius * d, n.z * radius * d * squash))
    o.location = center
    return finish(o, name, material, 0, True)


def superellipsoid(name, center, size, material, e_side=.25, e_top=.55, seg=24, rings=12, rot=(0, 0, 0)):
    """Rounded pillow/box shape (sandbags): blocky in plan, rounded in section."""
    def sp(w, m): c = math.cos(w); return math.copysign(abs(c) ** m, c)
    def sq(w, m): c = math.sin(w); return math.copysign(abs(c) ** m, c)
    a, b, c = size[0] / 2, size[1] / 2, size[2] / 2
    vs = [(0, 0, -c)]
    for i in range(1, rings):
        eta = -math.pi / 2 + math.pi * i / rings
        for j in range(seg):
            w = -math.pi + 2 * math.pi * j / seg
            vs.append((a * sp(eta, e_top) * sp(w, e_side), b * sp(eta, e_top) * sq(w, e_side), c * sq(eta, e_top)))
    vs.append((0, 0, c)); top = len(vs) - 1; fs = []
    for j in range(seg): fs.append((0, 1 + (j + 1) % seg, 1 + j))
    for i in range(rings - 2):
        for j in range(seg):
            r0 = 1 + i * seg; r1 = r0 + seg; k = (j + 1) % seg
            fs.append((r0 + j, r0 + k, r1 + k, r1 + j))
    last = 1 + (rings - 2) * seg
    for j in range(seg): fs.append((last + j, last + (j + 1) % seg, top))
    o = mesh(name, vs, fs, material, 0, True); o.location = center; o.rotation_euler = rot
    return o


def closed_box(name, corners_bottom, corners_top, material, bevel=0.0):
    vs = list(corners_bottom) + list(corners_top)
    return mesh(name, vs, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material, bevel)


# ---------------------------------------------------------------- divided bench
def divided_park_bench():
    wood = mat('Thermally modified ash slats', (.42, .27, .15), 0, .62)
    steel = mat('Graphite powder-coated steel', (.07, .075, .08), .55, .42)
    concrete = mat('Precast concrete foot', (.5, .5, .48), 0, .85)
    L = 1.9; seat_z = .44; depth = .46
    for x in (-L / 2 + .12, 0, L / 2 - .12):
        prism(f'Concrete foot {x}', [(-.06, -.24), (.06, -.24), (.06, .24), (-.06, .24)], 0, .06, concrete, .01)
        o = bpy.context.scene.objects[f'Concrete foot {x}']; o.location.x = x
        bar(f'Leg front {x}', (x, -.18, .06), (x, -.16, seat_z - .03), .05, .012, steel)
        bar(f'Leg back {x}', (x, .17, .06), (x, .22, .78), .05, .012, steel)
        bar(f'Seat bearer {x}', (x, -.24, seat_z - .025), (x, .2, seat_z - .025), .05, .03, steel)
    for i in range(5):
        y = -.21 + i * .1
        box(f'Seat slat {i + 1}', (0, y, seat_z), (L, .085, .035), wood, .006)
    for i in range(3):
        z = .55 + i * .095; y = .19 + (z - .55) * .14
        o = box(f'Back slat {i + 1}', (0, y + .02, z), (L, .03, .08), wood, .006); o.rotation_euler = (-.14, 0, 0)
    # Raised dividers between seat positions (anti-lying armrests).
    for x in (-L / 6, L / 6):
        pts = [(x, -.2, seat_z + .02), (x, -.2, seat_z + .2), (x, -.06, seat_z + .24), (x, .12, seat_z + .2), (x, .14, seat_z + .02)]
        smooth_tube(f'Seat divider {x}', pts, .014, steel, 3, 8)
    for x in (-L / 2 + .02, L / 2 - .02):
        pts = [(x, -.22, seat_z + .02), (x, -.22, seat_z + .22), (x, -.02, seat_z + .26), (x, .16, seat_z + .24), (x, .18, seat_z + .02)]
        smooth_tube(f'End armrest {x}', pts, .016, steel, 3, 8)
    return dict(id='city-divided-park-bench', title='仕切り付き公園ベンチ', titleEn='Park bench with seat dividers',
                description='公園や駅前広場に置く、仕切り付きの3人掛けベンチです。木製の座面と背もたれの板、黒い鋼製の脚と座受け、座席の間の曲げパイプの仕切り2本と両端の肘掛け、コンクリートの基礎ブロックを造形しています。銘板・寄贈表示などの文字、固定アンカーの地中部分は含みません。',
                descriptionEn='A three-seat park bench with seat dividers for parks and station plazas. It models wooden seat and back slats, graphite steel legs and seat bearers, two bent-tube dividers between seats and end armrests, and precast concrete foot blocks. Plaques, dedication text and buried anchors are not included.',
                tags=['bench', 'park', 'seating', 'street-furniture', 'ベンチ'], view=(-55, 22))


# ---------------------------------------------------------------- planter box
def sidewalk_planter_box():
    shell = mat('Weathering steel planter', (.32, .13, .05), .45, .7)
    soil = mat('Dark bark mulch', (.08, .05, .03), 0, .95)
    leaf = mat('Clipped boxwood foliage', (.035, .11, .03), 0, .85)
    stem = mat('Woody shrub stems', (.18, .11, .06), 0, .8)
    L, W, H, t = 1.5, .6, .55, .012
    closed_box('Planter outer wall', [(-L / 2, -W / 2, 0), (L / 2, -W / 2, 0), (L / 2, W / 2, 0), (-L / 2, W / 2, 0)],
               [(-L / 2, -W / 2, H), (L / 2, -W / 2, H), (L / 2, W / 2, H), (-L / 2, W / 2, H)], shell, .004)
    box('Top rim flange', (0, 0, H + .006), (L + .04, W + .04, .012), shell, .004)
    box('Mulch surface', (0, 0, H - .03), (L - .03, W - .03, .02), soil, 0)
    # A clipped boxwood hedge planted along the box: overlapping irregular masses.
    rnd = random.Random(61)
    for i in range(7):
        x = -L / 2 + .17 + i * .193
        r = .17 + rnd.random() * .03
        foliage_blob(f'Clipped shrub mass {i}', (x, rnd.uniform(-.04, .04), H + .1 + rnd.uniform(0, .03)), r, leaf, 61 + i, squash=.78, rough=.12)
        rod(f'Shrub stem {i}', (x, 0, H - .03), (x, 0, H + .05), .012, stem, 8)
    for x in (-L / 2 + .1, L / 2 - .1):
        box(f'Drain spacer foot {x}', (x, 0, -.0), (.08, W - .1, .02), shell, .003).location.z = .01
    return dict(id='city-sidewalk-planter-box', title='歩道のプランターボックス', titleEn='Sidewalk planter box',
                description='歩道や店先に置く、耐候性鋼の長方形プランターと植え込みです。箱形の外壁と上縁のつば、マルチング材の表面、刈り込んだ低木の葉の塊と幹、底の水抜き用スペーサー脚を造形しています。植物は簡略化した塊で、葉の一枚一枚、風の揺れ、土の内部、給水設備は含みません。',
                descriptionEn='A rectangular weathering-steel planter with clipped shrubs for sidewalks and shopfronts. It models the box wall and top rim flange, a mulch surface, simplified foliage masses with woody stems, and drainage spacer feet. Plants are simplified masses without individual leaves or wind motion; soil volume and irrigation are not included.',
                tags=['planter', 'shrub', 'greenery', 'street-furniture', 'プランター'], view=(-50, 24))


# ---------------------------------------------------------------- newspaper box
def newspaper_vending_box():
    body = mat('Gloss teal enamel', (.02, .22, .21), .2, .3)
    glass = mat('Scratched polycarbonate window', (.7, .78, .8), 0, .1, alpha=.3)
    steel = mat('Galvanized pedestal', (.5, .52, .52), .75, .4)
    dark = mat('Coin mechanism black', (.03, .03, .03), .4, .45)
    W, D, H, z0 = .5, .42, .62, .38
    cyl('Pedestal post', (0, 0, z0 / 2), .05, z0, steel, verts=24, bevel=.003)
    box('Pedestal foot plate', (0, 0, .006), (.4, .34, .012), steel, .004)
    box('Cabinet body', (0, 0, z0 + H / 2), (W, D, H), body, .012)
    o = closed_box('Sloped top', [(-W / 2 - .01, -D / 2 - .01, z0 + H), (W / 2 + .01, -D / 2 - .01, z0 + H), (W / 2 + .01, D / 2 + .01, z0 + H), (-W / 2 - .01, D / 2 + .01, z0 + H)],
                   [(-W / 2 - .01, -D / 2 - .01, z0 + H + .03), (W / 2 + .01, -D / 2 - .01, z0 + H + .03), (W / 2 + .01, D / 2 + .01, z0 + H + .07), (-W / 2 - .01, D / 2 + .01, z0 + H + .07)], body, .006)
    box('Front door frame', (0, -D / 2 - .006, z0 + H * .58), (W - .04, .012, H * .62), body, .006)
    box('Display window', (0, -D / 2 - .013, z0 + H * .6), (W - .12, .004, H * .45), glass, 0)
    box('Window shadow backing', (0, -D / 2 + .01, z0 + H * .6), (W - .12, .004, H * .45), dark, 0)
    box('Pull handle', (0, -D / 2 - .03, z0 + H * .3), (.16, .02, .025), steel, .005)
    box('Coin mechanism', (W / 2 - .09, -D / 2 - .016, z0 + H * .14), (.1, .02, .1), dark, .006)
    box('Coin slot', (W / 2 - .09, -D / 2 - .027, z0 + H * .17), (.025, .002, .004), steel, 0)
    box('Return button', (W / 2 - .09, -D / 2 - .028, z0 + H * .11), (.03, .006, .015), steel, .002)
    return dict(id='city-newspaper-vending-box', title='新聞自動販売ボックス', titleEn='Newspaper vending box',
                description='歩道に立つ、ペデスタル付きの新聞販売ボックスです。光沢塗装の箱と傾斜した天板、前扉の枠と半透明の見本窓、引き手、硬貨投入部と返却ボタン、亜鉛めっきの支柱と台板を造形しています。新聞・紙名・価格表示などの文字は含まず、扉の開閉や販売機構は動作しません。',
                descriptionEn='A pedestal-mounted newspaper vending box for sidewalks. It models the enamelled cabinet with sloped top, front door frame with a translucent display window, pull handle, coin mechanism with return button, and galvanized post and foot plate. Newspapers, titles, prices and other lettering are absent; the door and vending mechanism do not operate.',
                tags=['newspaper', 'vending', 'street-furniture', '新聞販売'], view=(-48, 18),
                transparentNote=('見本窓はGLB内の半透明（アルファブレンド）材質です。', 'The display window uses an alpha-blended GLB material.'))


# ---------------------------------------------------------------- two-tier bike rack
def two_tier_bicycle_rack():
    galv = mat('Hot-dip galvanized rack steel', (.52, .54, .54), .78, .4)
    rail = mat('Grey slide tray', (.36, .38, .38), .6, .45)
    rubber = mat('Black gas strut', (.04, .04, .04), .5, .4)
    L, D, H = 2.4, 1.9, 2.15
    for x in (-L / 2, L / 2):
        for y in (-.15, .55):
            box(f'Upright post {x}{y}', (x, y, H / 2), (.08, .08, H), galv, .006)
            box(f'Base plate {x}{y}', (x, y, .006), (.2, .2, .012), galv, .003)
        box(f'Top side beam {x}', (x, .2, H - .04), (.08, .9, .08), galv, .006)
    box('Top cross beam front', (0, -.15, H - .04), (L, .08, .08), galv, .006)
    box('Top cross beam back', (0, .55, H - .04), (L, .08, .08), galv, .006)
    n = 4; pitch = (L - .3) / (n - 1)
    for i in range(n):
        x = -L / 2 + .15 + i * pitch
        # Lower ground channel for one bicycle.
        box(f'Lower wheel channel {i + 1}', (x, .2 - .1, .04), (.07, 1.75, .06), rail, .006)
        box(f'Lower front wheel clamp {i + 1}', (x, -.55, .16), (.09, .06, .24), galv, .008)
        # Upper pull-out tray with lift strut, shown stowed.
        xu = x + pitch / 2 if i < n - 1 else None
        if xu is not None:
            box(f'Upper slide tray {i + 1}', (xu, .25, 1.55), (.08, 1.6, .05), rail, .006)
            box(f'Upper tray end stop {i + 1}', (xu, -.52, 1.62), (.1, .04, .12), galv, .006)
            rod(f'Upper tray lift strut {i + 1}', (xu, .4, 1.55), (xu, .5, H - .1), .014, rubber, 12)
            box(f'Upper tray hanger {i + 1}', (xu, .25, (1.55 + H - .08) / 2 + .02), (.04, .04, H - 1.62), galv, .004)
            box(f'Upper rail carriage {i + 1}', (xu, .25, 1.6), (.06, .2, .05), galv, .004)
    return dict(id='city-two-tier-bicycle-rack', title='2段式駐輪ラック', titleEn='Two-tier bicycle rack',
                description='駅前や集合住宅の駐輪場に設置する、上下2段の駐輪ラックです。亜鉛めっきの柱と梁、下段の車輪レール4本と前輪クランプ、上段の引出し式トレー3本と昇降補助ダンパー、吊り材と台車を造形しています。上段は収納位置で固定され、引出し・昇降の動作、自転車、番号札は含みません。',
                descriptionEn='A two-tier bicycle rack for station and apartment bicycle parking. It models galvanized posts and beams, four lower wheel channels with front-wheel clamps, three upper pull-out trays with lift-assist struts, hangers and carriages. Upper trays are fixed in their stowed position; pull-out and lift motion, bicycles and number plates are not included.',
                tags=['bicycle-parking', 'bike-rack', 'two-tier', 'station', '駐輪場'], view=(-55, 20))


# ---------------------------------------------------------------- sandbags
def sandbag_stack():
    bag = mat('Woven polypropylene sandbag', (.62, .58, .48), 0, .92)
    tie = mat('Bag tie cord', (.15, .12, .08), 0, .8)
    rnd = random.Random(1061)
    def sandbag(name, loc, rot):
        superellipsoid(name, loc, (.56, .36, .13), bag, .22, .6, 28, 12, rot)
        # Tied neck folded under one end.
        t = cyl(name + ' tied neck', (0, 0, 0), .028, .05, tie, 'X', 10, 0); t.rotation_euler = (0, math.pi / 2, rot[2])
        t.location = Vector(loc) + Vector((.3 * math.cos(rot[2]), .3 * math.sin(rot[2]), -.02))
    layers = [(5, 0.0), (4, .3), (3, .6)]
    z = .065
    for li, (count, off) in enumerate(layers):
        for i in range(count):
            x = -1.2 + off + i * .6 + rnd.uniform(-.015, .015)
            sandbag(f'Sandbag {li}.{i}', (x, rnd.uniform(-.015, .015), z), (rnd.uniform(-.02, .02), rnd.uniform(-.02, .02), rnd.uniform(-.04, .04)))
        z += .12
    return dict(id='city-sandbag-stack', title='土のうの積み上げ', titleEn='Sandbag stack',
                description='浸水対策として出入口や側溝の前に積む、ポリプロピレン製土のう12袋の三段積みです。枕状にふくらんだ袋の形、口を縛った紐の結び目、段ごとに半個ずらした積み方を造形しています。袋は単純化した形状で、織り目の質感、中の砂、変形の物理挙動、止水シートは含みません。',
                descriptionEn='A three-course stack of twelve polypropylene sandbags placed at doorways and gutters against flooding. It models pillow-shaped bags, tied neck knots and half-bag offset courses. Bags are simplified shapes without woven texture, contained sand, deformation physics or waterproof sheeting.',
                tags=['sandbag', 'flood-protection', 'disaster-prevention', '土のう'], view=(-40, 22))


# ---------------------------------------------------------------- gas meter
def gas_meter_assembly():
    meter = mat('Pale grey meter casing', (.66, .67, .65), .2, .45)
    pipe = mat('Yellow painted gas pipe', (.85, .6, .05), .2, .45)
    brass = mat('Brass valve body', (.55, .38, .12), .75, .35)
    dark = mat('Black dial window', (.02, .02, .025), 0, .2)
    wall = mat('Fibre-cement backing board', (.6, .58, .54), 0, .85)
    box('Backing board', (0, .015, .6), (.6, .03, 1.2), wall, .004)
    box('Meter casing', (0, -.11, .78), (.26, .16, .3), meter, .02)
    box('Meter top cap', (0, -.11, .945), (.27, .17, .03), meter, .01)
    box('Dial window', (0, -.191, .8), (.14, .004, .07), dark, 0)
    for x in (-.08, .08):
        cyl(f'Meter union nut {x}', (x, -.11, .975), .022, .04, brass, verts=6, bevel=.002)
        rod(f'Meter riser {x}', (x, -.11, .99), (x, -.11, 1.08), .014, pipe, 16)
    tube('Inlet pipe', [(-.08, -.11, 1.08), (-.08, -.11, 1.12), (-.08, .0, 1.12), (-.08, .0, 1.2)], .014, pipe, 3, 4)
    tube('Outlet pipe', [(.08, -.11, 1.08), (.08, -.11, 1.12), (.24, -.11, 1.12), (.24, -.11, .1), (.24, .0, .1)], .014, pipe, 3, 4)
    cyl('Main shutoff valve body', (-.08, -.11, 1.04), .024, .05, brass, verts=16, bevel=.002)
    box('Shutoff lever', (-.08, -.15, 1.04), (.012, .07, .012), pipe, .002)
    for z in (.3, .7):
        box(f'Pipe saddle clip {z}', (.24, -.11, z), (.05, .04, .02), meter, .003)
    box('Blank meter plate', (0, -.192, .72), (.12, .002, .035), mat('Blank plate', (.85, .85, .82), 0, .4), 0)
    return dict(id='city-gas-meter-assembly', title='屋外ガスメーターまわり', titleEn='Outdoor gas meter assembly',
                description='住宅の外壁に取り付ける、都市ガスのメーターと配管一式です。繊維セメントの取付板、灰色のメーター本体と目盛り窓、無地の銘板、ユニオンナット、黄色い入口・出口の配管と元栓レバー、配管押さえを造形しています。目盛りの数字・検定表示などの文字、壁の内部、実際のガス設備としての適合性は含みません。',
                descriptionEn='A wall-mounted residential gas meter with its piping. It models the fibre-cement backing board, grey meter casing with dial window and blank plate, union nuts, yellow inlet and outlet pipes with a shutoff valve lever, and pipe saddle clips. Dial numerals, certification markings and other lettering, the wall interior and suitability as real gas equipment are not included.',
                tags=['gas-meter', 'utility', 'building-services', 'wall-mounted', 'ガスメーター'], view=(-40, 14))


# ---------------------------------------------------------------- chain barrier
def chain_post_barrier_set():
    post = mat('Black and white post enamel', (.86, .87, .85), .2, .35)
    band = mat('Black post bands', (.03, .03, .03), .2, .4)
    chain = mat('Zinc chain links', (.55, .57, .57), .85, .3)
    base = mat('Cast iron base', (.08, .08, .08), .5, .5)
    xs = (-1.5, 0, 1.5)
    for i, x in enumerate(xs):
        lathe(f'Post base {i}', [(0, 0), (.16, 0), (.165, .02), (.12, .06), (.06, .08), (0, .08)], base, 40).location.x = x
        cyl(f'Post {i}', (x, 0, .48), .035, .8, post, verts=32, bevel=.002)
        for z in (.3, .55, .8):
            cyl(f'Post band {i} {z}', (x, 0, z), .0355, .06, band, verts=32, bevel=0)
        sphere(f'Post finial {i}', (x, 0, .9), (.045, .045, .045), post, 24, 12)
        torus(f'Chain eye {i}', (x, 0, .78), .02, .005, chain, (math.pi / 2, 0, 0), 16)
    for a, b in ((xs[0], xs[1]), (xs[1], xs[2])):
        n = 34; sag = .18
        for k in range(n):
            t = (k + .5) / n; x = a + (b - a) * t; z = .78 - sag * 4 * t * (1 - t)
            dz = -sag * 4 * (1 - 2 * t) / (b - a)
            ang = math.atan(dz)
            # Alternate links twist 90 degrees about the chain axis and pitch with the sag.
            o = torus(f'Chain link {a} {k}', (x, 0, z), .022, .0045, chain, (math.pi / 2 if k % 2 else 0, -ang, 0), 12)
            o.scale = (1.6, 1, 1)
    return dict(id='city-chain-post-barrier-set', title='チェーンポールの柵', titleEn='Chain post barrier set',
                description='敷地の境界や立入制限に使う、白黒のポール3本とたるませたチェーンの組です。鋳鉄の置き台、帯模様の支柱、球形の頭部、チェーン掛けの輪、交互に向きを変えた鎖の輪を造形しています。鎖は固定形状で揺れや張り具合の物理挙動はなく、注意札などの文字は含みません。',
                descriptionEn='A set of three black-and-white posts joined by sagging chains, used for site boundaries and access restriction. It models cast-iron bases, banded posts, ball finials, chain eyes and alternating chain links. The chain is static geometry without swing or tension physics; warning tags and other lettering are not included.',
                tags=['chain-barrier', 'stanchion', 'access-control', 'チェーン'], view=(-60, 20))


# ---------------------------------------------------------------- coin lockers
def coin_locker_bank():
    body = mat('Off-white locker enamel', (.78, .78, .74), .25, .4)
    door = mat('Pale blue locker door', (.33, .5, .62), .25, .38)
    dark = mat('Locker shadow line', (.03, .03, .03), .2, .6)
    lock = mat('Brushed stainless lock', (.6, .62, .62), .85, .3)
    plate = mat('Blank number plate', (.88, .88, .85), 0, .4)
    cols, rows = 4, 5; cw = .36; heights = [.3, .3, .3, .45, .45]; D = .57
    W = cols * cw + .04; H = sum(heights) + .04
    box('Plinth', (0, 0, .05), (W, D, .1), dark, .006)
    box('Carcass', (0, 0, .1 + H / 2), (W, D, H), body, .008)
    z = .12
    for r, h in enumerate(heights):
        for c in range(cols):
            x = -W / 2 + .02 + cw * (c + .5)
            box(f'Door {r}.{c}', (x, -D / 2 - .004, z + h / 2), (cw - .008, .008, h - .008), door, .003)
            box(f'Door seam {r}.{c}', (x, -D / 2 - .0005, z + h / 2), (cw - .002, .002, h - .002), dark, 0)
            box(f'Lock housing {r}.{c}', (x + cw / 2 - .07, -D / 2 - .016, z + h / 2), (.06, .014, .1), lock, .004)
            cyl(f'Key cylinder {r}.{c}', (x + cw / 2 - .07, -D / 2 - .024, z + h / 2 + .02), .009, .006, dark, 'Y', 16, .001)
            box(f'Coin slot {r}.{c}', (x + cw / 2 - .07, -D / 2 - .0235, z + h / 2 - .025), (.004, .002, .022), dark, 0)
            box(f'Number plate {r}.{c}', (x - .08, -D / 2 - .009, z + h - .04), (.07, .002, .03), plate, 0)
        z += h
    box('Top cornice', (0, -.01, .1 + H + .015), (W + .03, D + .02, .03), body, .006)
    return dict(id='city-coin-locker-bank', title='コインロッカー', titleEn='Coin locker bank',
                description='駅構内や観光地の通路に並ぶ、4列×5段・20口のコインロッカーです。台座と本体、上部のコーニス、高さの異なる扉と継ぎ目、ステンレスの錠ケースと鍵穴・硬貨投入口、無地の番号札を造形しています。番号・料金・注意書きなどの文字、扉の開閉、鍵や精算の機能は含みません。',
                descriptionEn='A 4×5, twenty-door coin locker bank for stations and tourist walkways. It models the plinth and carcass, top cornice, doors of two heights with seams, stainless lock housings with key cylinders and coin slots, and blank number plates. Numbers, prices, notices and other lettering, door motion, keys and payment function are not included.',
                tags=['locker', 'coin-locker', 'station', 'storage', 'コインロッカー'], view=(-38, 14))


# ---------------------------------------------------------------- capsule toy machines
def capsule_toy_vending_machines():
    frame = mat('White moulded vending frame', (.86, .86, .84), .1, .35)
    acrylic = mat('Clear acrylic globe', (.82, .88, .9), 0, .04, alpha=.25)
    metal = mat('Chrome crank knob', (.7, .72, .72), .9, .2)
    red = mat('Red capsule shell', (.7, .06, .05), 0, .3)
    blue = mat('Blue capsule shell', (.05, .2, .65), 0, .3)
    yellow = mat('Yellow capsule shell', (.9, .65, .05), 0, .3)
    white = mat('White capsule half', (.9, .9, .88), 0, .3)
    dark = mat('Chute shadow', (.02, .02, .02), 0, .6)
    cols = 2; rows = 2; W = .42; D = .4; Hm = .62; base_h = .22
    box('Stand base', (0, 0, base_h / 2), (cols * W + .04, D + .04, base_h), frame, .01)
    rnd = random.Random(7)
    colors = [red, blue, yellow]
    for r in range(rows):
        for c in range(cols):
            x = -W / 2 + c * W if cols == 2 else 0; z0 = base_h + r * Hm
            box(f'Machine lower body {r}.{c}', (x, 0, z0 + .17), (W - .02, D - .02, .34), frame, .015)
            box(f'Price window {r}.{c}', (x - .1, -D / 2 + .005, z0 + .29), (.12, .004, .06), dark, 0)
            cyl(f'Crank dial {r}.{c}', (x + .02, -D / 2 + .002, z0 + .2), .07, .025, frame, 'Y', 40, .004)
            box(f'Crank handle {r}.{c}', (x + .02, -D / 2 - .03, z0 + .2), (.11, .03, .03), metal, .008)
            box(f'Capsule chute {r}.{c}', (x + .02, -D / 2 + .003, z0 + .07), (.12, .006, .09), dark, 0)
            box(f'Chute flap {r}.{c}', (x + .02, -D / 2 - .004, z0 + .1), (.13, .008, .03), frame, .004)
            # Transparent capsule case above the mechanism; blank card header on top.
            box(f'Case floor {r}.{c}', (x, 0, z0 + .345), (W - .04, D - .04, .01), frame, .003)
            box(f'Capsule case {r}.{c}', (x, 0, z0 + .45), (W - .04, D - .04, .2), acrylic, .008)
            for k in range(16):
                cx = x + rnd.uniform(-.15, .15); cy = rnd.uniform(-.14, .14); cz = z0 + .385 + (k // 6) * .06 + rnd.uniform(0, .02)
                sphere(f'Capsule {r}.{c}.{k}', (cx, cy, cz), (.032, .032, .032), colors[(k + r + c) % 3], 12, 6)
            box(f'Display card header {r}.{c}', (x, -.02, z0 + .57), (W - .02, D - .06, .04), frame, .004)
            box(f'Blank display card {r}.{c}', (x, -D / 2 + .012, z0 + .57), (W - .08, .002, .032), white, 0)
            box(f'Top cap {r}.{c}', (x, 0, z0 + Hm - .02), (W - .02, D - .02, .03), frame, .008)
    return dict(id='city-capsule-toy-vending-machines', title='カプセルトイ自販機（2×2台）', titleEn='Capsule toy vending machines, 2×2',
                description='商店街や駅の通路に並ぶ、上下2段×2列のカプセルトイ自販機です。共通の台座、各台の本体と回転ダイヤル・ハンドル、取出し口とふた、価格窓、無地の見本カード枠、透明な陳列ケースと中の赤・青・黄のカプセルを造形しています。カードや本体に商品名・キャラクター・ロゴなどの図柄はなく、ハンドルの回転や景品の排出は動作しません。',
                descriptionEn='A 2×2 bank of capsule toy vending machines for shopping streets and station passages. It models the shared stand, each machine body with rotary dial and crank, dispensing chute and flap, price window, blank display-card frames, and transparent display cases with red, blue and yellow capsules. Cards and bodies carry no product names, characters or logos; crank rotation and capsule dispensing do not operate.',
                tags=['capsule-toy', 'gachapon', 'vending', 'shopping-street', 'ガチャガチャ'], view=(-42, 15),
                transparentNote=('陳列ケースはGLB内の半透明（アルファブレンド）材質です。', 'The display cases use an alpha-blended GLB material.'))


# ---------------------------------------------------------------- sanitizer stand
def hand_sanitizer_stand():
    steel = mat('Satin stainless stand', (.62, .64, .64), .85, .3)
    white = mat('White dispenser housing', (.88, .88, .86), 0, .35)
    grey = mat('Grey pedal rubber', (.2, .2, .2), 0, .7)
    bottle = mat('Translucent refill window', (.75, .85, .9), 0, .1, alpha=.4)
    box('Weighted base plate', (0, 0, .01), (.32, .32, .02), steel, .006)
    box('Foot pedal', (0, -.1, .04), (.12, .14, .03), grey, .008)
    rod('Pedal pull rod', (0, -.04, .045), (0, .02, .9), .004, steel, 8)
    box('Column', (0, .03, .5), (.06, .06, .98), steel, .006)
    box('Dispenser housing', (0, -.02, 1.08), (.14, .1, .22), white, .015)
    box('Refill window', (0, -.072, 1.1), (.05, .004, .08), bottle, 0)
    cyl('Nozzle', (0, -.075, .98), .008, .03, grey, 'Z', 12, .001)
    box('Drip tray', (0, -.06, .78), (.14, .1, .015), steel, .004)
    box('Blank instruction plate', (0, -.002, .55), (.12, .004, .18), white, .002)
    return dict(id='city-hand-sanitizer-stand', title='足踏み式消毒液スタンド', titleEn='Foot-pedal hand sanitizer stand',
                description='店舗や施設の入口に置く、足踏みペダル式の手指消毒液スタンドです。重りの台板と踏み板、引き棒、ステンレスの支柱、白いディスペンサーと残量窓、ノズル、受け皿、無地の案内板を造形しています。案内の文字や図記号、液体、ペダルと吐出の動作は含みません。',
                descriptionEn='A foot-pedal hand sanitizer stand for shop and facility entrances. It models the weighted base plate and pedal, pull rod, stainless column, white dispenser with refill window, nozzle, drip tray and a blank instruction plate. Instruction text and symbols, liquid and pedal or dispensing motion are not included.',
                tags=['sanitizer', 'hygiene', 'entrance', 'stand', '消毒液'], view=(-45, 16),
                transparentNote=('残量窓はGLB内の半透明（アルファブレンド）材質です。', 'The refill window uses an alpha-blended GLB material.'))


# ---------------------------------------------------------------- tree support frame
def tree_support_frame():
    pole = mat('Peeled cedar support pole', (.45, .32, .19), 0, .7)
    bark = mat('Young tree bark', (.25, .17, .1), 0, .85)
    leaf = mat('Young tree canopy', (.05, .14, .035), 0, .85)
    cord = mat('Palm fibre binding cord', (.2, .13, .07), 0, .9)
    pad = mat('Burlap trunk wrap', (.48, .38, .24), 0, .95)
    lathe('Young tree trunk', [(0, 0), (.06, 0), (.055, .6), (.045, 1.4), (.035, 2.2), (.02, 2.7), (0, 2.75)], bark, 20)
    rnd = random.Random(1062)
    for k in range(9):
        a = k * 2.399; rr = .25 + .1 * (k % 3); z = 2.15 + .1 * (k % 4) + (.35 if k == 8 else 0)
        c = (rr * math.cos(a) if k < 8 else 0, rr * math.sin(a) if k < 8 else 0, z)
        foliage_blob(f'Canopy mass {k}', c, .3 + rnd.random() * .1, leaf, 1062 + k, squash=.8, rough=.25)
    for ang in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        rod(f'Branch {ang:.2f}', (0, 0, 1.9 + ang * .05), (.35 * math.cos(ang), .35 * math.sin(ang), 2.3 + ang * .05), .02, bark, 10)
    # Torii-style frame: two posts, upper and lower cross rails, bound to trunk.
    for x in (-.45, .45):
        cyl(f'Frame post {x}', (x, 0, .8), .045, 1.6, pole, verts=20, bevel=.004)
        cyl(f'Post top {x}', (x, 0, 1.605), .043, .01, pole, verts=20, bevel=.004)
    for z in (1.45, .9):
        cyl(f'Cross rail {z}', (0, 0, z), .035, 1.05, pole, 'X', 20, .004)
        cyl(f'Trunk wrap {z}', (0, 0, z), .065, .14, pad, verts=24, bevel=.004)
        for s in (-1, 1):
            torus(f'Binding cord {z} {s}', (s * .45, 0, z), .05, .006, cord, None, 20, 6)
    for k in range(3):
        torus(f'Trunk binding {k}', (0, 0, 1.4 + k * .05), .067, .005, cord, None, 20, 6)
    return dict(id='city-tree-support-frame', title='街路樹の鳥居型支柱', titleEn='Street tree support frame',
                description='植えたばかりの街路樹を支える、杉丸太の鳥居型支柱です。2本の柱と上下2段の横木、幹に巻いた麻布、柱と幹を結ぶシュロ縄、若木の幹と枝、簡略化した樹冠を造形しています。樹冠は葉の塊で表現し、根鉢・植え桝・風による揺れは含みません。',
                descriptionEn='A torii-style cedar-pole support frame for a newly planted street tree. It models two posts with upper and lower cross rails, burlap trunk wraps, palm-fibre bindings tying posts and trunk, and a young trunk with branches and a simplified canopy. The canopy is represented as foliage masses; root ball, tree pit and wind motion are not included.',
                tags=['street-tree', 'tree-support', 'landscaping', '支柱'], view=(-50, 12))


BUILDERS = {
    'city-divided-park-bench': divided_park_bench,
    'city-sidewalk-planter-box': sidewalk_planter_box,
    'city-newspaper-vending-box': newspaper_vending_box,
    'city-two-tier-bicycle-rack': two_tier_bicycle_rack,
    'city-sandbag-stack': sandbag_stack,
    'city-gas-meter-assembly': gas_meter_assembly,
    'city-chain-post-barrier-set': chain_post_barrier_set,
    'city-coin-locker-bank': coin_locker_bank,
    'city-capsule-toy-vending-machines': capsule_toy_vending_machines,
    'city-hand-sanitizer-stand': hand_sanitizer_stand,
    'city-tree-support-frame': tree_support_frame,
}


def main(argv):
    p = argparse.ArgumentParser(); p.add_argument('--out', required=True); p.add_argument('--only', nargs='*')
    args = p.parse_args(argv)
    for slug, fn in BUILDERS.items():
        if args.only and slug not in args.only: continue
        reset(); spec = fn(); assert spec['id'] == slug
        build_asset(spec, args.out, GENERATOR)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
