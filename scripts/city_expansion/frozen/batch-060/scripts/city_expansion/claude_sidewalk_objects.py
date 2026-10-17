"""Original sidewalk and kerbside street objects authored by Claude, CC BY 4.0.

No third-party meshes, textures, brand identities, lettering or font files.
Usage: python scripts/city_expansion/frozen/batch-060/scripts/city_expansion/claude_sidewalk_objects.py --out DIR [--only ID ...]
"""
import sys, math, argparse
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

GENERATOR = Path(__file__).resolve().relative_to(ROOT).as_posix()


def wire_grid(prefix, origin, u, v, nu, nv, r, material):
    """Welded wire panel: nu wires along v spaced over u, nv wires along u spaced over v."""
    o = Vector(origin); u = Vector(u); v = Vector(v)
    for i in range(1, nu):
        a = o + u * (i / nu); rod(f'{prefix} wire u{i}', a, a + v, r, material, 6)
    for j in range(1, nv):
        a = o + v * (j / nv); rod(f'{prefix} wire v{j}', a, a + u, r, material, 6)


def frame_rect(prefix, corners, size, material):
    for i in range(4):
        bar(f'{prefix} frame {i}', corners[i], corners[(i + 1) % 4], size, size, material, .002)


# ---------------------------------------------------------------- refuse cage
def folding_refuse_collection_cage():
    green = mat('Moss green powder coat', (.09, .20, .11), .3, .45)
    wire = mat('Green coated wire mesh', (.11, .24, .13), .2, .5)
    steel = mat('Zinc hinge and latch', (.5, .52, .52), .8, .35)
    W, D, Hh = 1.2, .8, .9; s = .03
    for x in (-W / 2, W / 2):
        for y in (-D / 2, D / 2):
            box(f'Corner post {x} {y}', (x, y, Hh / 2), (s, s, Hh), green, .003)
            box(f'Foot pad {x} {y}', (x, y, .004), (.06, .06, .008), steel, .002)
    for z in (.03, Hh):
        frame_rect(f'Ring {z}', [(-W / 2, -D / 2, z), (W / 2, -D / 2, z), (W / 2, D / 2, z), (-W / 2, D / 2, z)], s, green)
    r = .0025
    wire_grid('Front', (-W / 2, -D / 2, .03), (W, 0, 0), (0, 0, Hh - .03), 24, 17, r, wire)
    wire_grid('Back', (-W / 2, D / 2, .03), (W, 0, 0), (0, 0, Hh - .03), 24, 17, r, wire)
    wire_grid('Left', (-W / 2, -D / 2, .03), (0, D, 0), (0, 0, Hh - .03), 16, 17, r, wire)
    wire_grid('Right', (W / 2, -D / 2, .03), (0, D, 0), (0, 0, Hh - .03), 16, 17, r, wire)
    # Hinged mesh lid, shown closed and slightly proud of the top ring.
    zl = Hh + .03
    frame_rect('Lid', [(-W / 2 - .01, -D / 2 - .03, zl), (W / 2 + .01, -D / 2 - .03, zl), (W / 2 + .01, D / 2, zl), (-W / 2 - .01, D / 2, zl)], .025, green)
    wire_grid('Lid', (-W / 2 - .01, -D / 2 - .03, zl), (W + .02, 0, 0), (0, D + .03, 0), 24, 17, r, wire)
    for x in (-W / 3, W / 3):
        cyl(f'Lid hinge {x}', (x, D / 2 + .005, Hh + .015), .012, .08, steel, 'X', 16, .001)
    rod('Lid grab handle', (-.12, -D / 2 - .06, zl), (.12, -D / 2 - .06, zl), .008, steel, 12)
    for x in (-.12, .12): rod(f'Handle leg {x}', (x, -D / 2 - .03, zl), (x, -D / 2 - .06, zl), .008, steel, 12)
    box('Front latch', (0, -D / 2 - .02, Hh - .02), (.06, .02, .05), steel, .003)
    box('Blank notice plate', (0, -D / 2 - .006, .6), (.24, .004, .16), mat('Blank white plate', (.82, .83, .8), 0, .4), .002)
    return dict(id='city-folding-refuse-collection-cage', title='折りたたみ式ごみ集積ボックス', titleEn='Folding refuse collection cage',
                description='住宅地のごみステーションに置く、緑色の網目ボックスです。角柱と上下の枠、溶接金網の4面、蝶番付きの網ふたと取っ手、前面の留め金、無地の掲示板、脚部パッドを造形しています。ふたは閉じた状態で、折りたたみ・開閉動作、ごみ袋、文字の掲示は含みません。',
                descriptionEn='A green welded-mesh refuse collection cage for residential collection points. It models corner posts, top and bottom frames, four mesh walls, a hinged mesh lid with grab handle, front latch, a blank notice plate and foot pads. The lid is shown closed; folding or opening motion, refuse bags and lettered notices are not included.',
                tags=['refuse', 'garbage-station', 'mesh-cage', 'waste-collection', 'ごみ集積所'], view=(-50, 26))


# ---------------------------------------------------------------- pushcart stall
def pushcart_food_stall():
    wood = mat('Weathered cedar boards', (.36, .22, .12), 0, .7)
    dark_wood = mat('Dark stained timber', (.16, .09, .05), 0, .65)
    top = mat('Scrubbed counter board', (.55, .40, .25), 0, .6)
    iron = mat('Black iron fittings', (.04, .04, .04), .6, .5)
    roof = mat('Galvanized corrugated roof', (.48, .50, .50), .7, .45)
    cloth = mat('Plain indigo cotton curtain', (.05, .08, .2), 0, .85)
    lantern = mat('Red paper lantern', (.62, .05, .03), 0, .6, emission=(1, .25, .1), strength=.6)
    pot = mat('Aluminium stock pot', (.6, .62, .63), .85, .3)
    L, D = 1.7, .8; zb = .45; hb = .5
    box('Cart body', (0, 0, zb + hb / 2), (L, D, hb), wood, .01)
    for i in range(8):
        box(f'Body plank seam {i}', (-L / 2 + .1 + i * .214, -D / 2 - .002, zb + hb / 2), (.006, .004, hb - .02), dark_wood, 0)
    box('Customer counter', (0, -.05, zb + hb + .03), (L + .12, D + .25, .05), top, .006)
    for x in (-L / 2 - .02, L / 2 + .02):
        for y in (-D / 2 + .02, D / 2 - .02):
            box(f'Corner post {x}{y}', (x, y, (zb + 2.15) / 2), (.07, .07, 2.15 - zb), dark_wood, .006)
    # Wheels on the long sides near the middle.
    for y in (-D / 2 - .06, D / 2 + .06):
        torus(f'Wheel rim {y}', (0, y, .45), .42, .03, dark_wood, (math.pi / 2, 0, 0), 48, 8)
        torus(f'Iron tyre {y}', (0, y, .45), .45, .012, iron, (math.pi / 2, 0, 0), 48, 6)
        cyl(f'Hub {y}', (0, y, .45), .07, .12, dark_wood, 'Y', 24, .006)
        for k in range(10):
            a = k * math.tau / 10
            rod(f'Spoke {y} {k}', (0, y, .45), (.41 * math.cos(a), y, .45 + .41 * math.sin(a)), .014, dark_wood, 8)
    cyl('Axle', (0, 0, .45), .025, D + .3, iron, 'Y', 16, .002)
    for y in (-D / 2 + .1, D / 2 - .1):
        bar(f'Push handle {y}', (L / 2, y, zb + .35), (L / 2 + .55, y, zb + .5), .045, .045, dark_wood)
        box(f'Rest leg {y}', (-L / 2 + .1, y, zb / 2), (.06, .06, zb), dark_wood, .004)
    rod('Handle crossbar', (L / 2 + .55, -D / 2 + .1, zb + .5), (L / 2 + .55, D / 2 - .1, zb + .5), .02, dark_wood, 12)
    # Roof frame and gabled corrugated roof with deep eaves.
    zr = 2.15
    for y in (-D / 2 + .02, D / 2 - .02):
        box(f'Eave beam {y}', (0, y, zr), (L + .2, .07, .08), dark_wood, .006)
    ridge = zr + .28; ov = .35
    for s in (-1, 1):
        y0 = s * (D / 2 + ov); z0 = zr + .02
        n = 9
        for i in range(n):
            x0 = -L / 2 - .2 + i * (L + .4) / n; x1 = x0 + (L + .4) / n
            mesh(f'Roof sheet {s} {i}', [(x0, 0, ridge), (x1, 0, ridge), (x1, y0, z0), (x0, y0, z0),
                                         (x0, 0, ridge + .012), (x1, 0, ridge + .012), (x1, y0, z0 + .012), (x0, y0, z0 + .012)],
                 [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], roof)
            rod(f'Roof corrugation {s} {i}', (x0 + .05, 0, ridge + .015), (x0 + .05, y0 * .98, z0 + .015 + (ridge - z0) * .02), .006, roof, 6)
    box('Ridge board', (0, 0, ridge + .02), (L + .4, .08, .04), dark_wood, .004)
    for x in (-L / 2 - .02, L / 2 + .02):
        bar(f'Gable strut {x} front', (x, -D / 2 + .02, zr), (x, 0, ridge), .05, .05, dark_wood)
        bar(f'Gable strut {x} back', (x, D / 2 - .02, zr), (x, 0, ridge), .05, .05, dark_wood)
    # Plain curtain panels and lantern on the customer side.
    for i in range(4):
        x = -L / 2 + .25 + i * .4
        box(f'Plain curtain panel {i + 1}', (x, -D / 2 - .04, zr - .2), (.36, .008, .34), cloth, 0)
    rod('Curtain rod', (-L / 2 - .02, -D / 2 - .04, zr - .02), (L / 2 + .02, -D / 2 - .04, zr - .02), .008, iron, 8)
    ln = lathe('Paper lantern', [(0, 0), (.08, 0), (.08, .02), (.12, .05), (.155, .12), (.165, .2), (.155, .28), (.12, .35), (.08, .38), (.08, .4), (0, .4)], lantern, 32)
    ln.location = (L / 2 - .15, -D / 2 - .2, zr - .62)
    for z in (0, .38): cyl(f'Lantern cap {z}', (L / 2 - .15, -D / 2 - .2, zr - .62 + z + .01), .085, .025, iron, verts=32, bevel=.002)
    for k in range(7):
        r = [.1, .14, .16, .165, .16, .14, .1][k]
        torus(f'Lantern rib {k}', (L / 2 - .15, -D / 2 - .2, zr - .62 + .05 + k * .05), r, .003, dark_wood, None, 32, 4)
    rod('Lantern hook', (L / 2 - .15, -D / 2 - .2, zr - .21), (L / 2 - .15, -D / 2 - .2, zr - .05), .004, iron, 6)
    rod('Lantern bracket', (L / 2 - .15, -D / 2 - .2, zr - .05), (L / 2 - .15, -D / 2 + .02, zr - .05), .006, iron, 6)
    # Cooking pot inside the cart behind the counter.
    lathe('Stock pot', [(0, 0), (.17, 0), (.18, .01), (.18, .26), (.19, .27), (.18, .28), (0, .27)], pot, 40).location = (-.3, .15, zb + hb + .06)
    cyl('Pot burner ring', (-.3, .15, zb + hb + .04), .2, .03, iron, verts=32, bevel=.003)
    for k in range(3):
        box(f'Ladle rest {k}', (.35 + k * .18, .2, zb + hb + .1), (.14, .14, .08), pot, .01)
    return dict(id='city-pushcart-food-stall', title='屋台（手押し車）', titleEn='Pushcart food stall',
                description='夜の街角に出る木製の手押し屋台です。板張りの車体と客側カウンター、木製スポークの大車輪と鉄輪・車軸、押し手と休み脚、四隅の柱とトタンの切妻屋根、無地の藍色のれん、赤い提灯と骨組み、寸胴鍋と火口、具材入れを造形しています。のれんと提灯は無地で、屋号などの文字、食品、人物、走行・開閉動作は含みません。',
                descriptionEn='A wooden pushcart food stall for night-time street corners. It models the planked body and customer counter, large wooden-spoked wheels with iron tyres and axle, push handles and rest legs, corner posts with a corrugated gabled roof, plain indigo curtain panels, a red paper lantern with ribs, a stock pot on a burner ring and ingredient trays. The curtain and lantern are blank, with no shop name or lettering; food, people and wheel or folding motion are not included.',
                tags=['food-stall', 'yatai', 'pushcart', 'night-market', '屋台'], view=(-58, 18))


# ---------------------------------------------------------------- mailbox bank
def wall_mailbox_bank():
    body = mat('Warm grey powder coat', (.42, .42, .40), .35, .42)
    door = mat('Satin silver door', (.62, .63, .63), .65, .32)
    dark = mat('Slot shadow', (.03, .03, .03), .2, .6)
    knob = mat('Black dial lock', (.03, .03, .035), .3, .45)
    plate = mat('Blank name card', (.86, .86, .83), 0, .5)
    cols, rows = 3, 4; cw, rh, D = .33, .16, .34; gap = .006
    W = cols * cw + .03; Hh = rows * rh + .03
    box('Mailbox carcass', (0, D / 2, Hh / 2), (W, D, Hh), body, .006)
    for c in range(cols):
        for r in range(rows):
            x = -W / 2 + .015 + cw * (c + .5); z = .015 + rh * (r + .5)
            box(f'Door {c}{r}', (x, -.004, z), (cw - gap, .008, rh - gap), door, .003)
            box(f'Insertion slot {c}{r}', (x - .02, -.009, z + .04), (.24, .004, .028), dark, 0)
            box(f'Slot flap {c}{r}', (x - .02, -.012, z + .052), (.25, .006, .012), door, .002)
            box(f'Name card window {c}{r}', (x - .05, -.009, z - .03), (.12, .003, .035), plate, 0)
            cyl(f'Dial lock {c}{r}', (x + .11, -.014, z - .02), .02, .016, knob, 'Y', 24, .003)
            cyl(f'Dial ring {c}{r}', (x + .11, -.009, z - .02), .026, .004, door, 'Y', 24, .001)
    box('Top cap', (0, D / 2 - .01, Hh + .008), (W + .02, D + .02, .016), body, .004)
    return dict(id='city-wall-mailbox-bank', title='集合郵便受け（12戸）', titleEn='Wall mailbox bank, 12 units',
                description='集合住宅のエントランスに並ぶ、3列×4段・12戸分の壁付け郵便受けです。灰色の本体と天板、銀色の扉、投函口とフラップ、無地の名札窓、ダイヤル錠を造形しています。原点は底面中央で、壁取付けの高さ・ビスは含みません。名札・部屋番号などの文字、郵便物、扉の開閉動作はありません。',
                descriptionEn='A 3×4, twelve-unit wall mailbox bank for apartment entrances. It models the grey carcass and top cap, satin silver doors, insertion slots with flaps, blank name-card windows and dial locks. The origin is at the bottom center; wall mounting height and screws are not included. No names, unit numbers or other lettering, mail, or door motion is provided.',
                tags=['mailbox', 'apartment-entrance', 'post', 'wall-mounted', '集合ポスト'], view=(-35, 15))


# ---------------------------------------------------------------- bike share dock
def bike_share_dock():
    teal = mat('Deep teal powder coat', (.02, .23, .24), .35, .4)
    grey = mat('Graphite steel', (.12, .13, .13), .55, .45)
    screen = mat('Dark display glass', (.01, .015, .02), 0, .08)
    lamp = mat('Dock status light green', (.1, .6, .2), 0, .3, emission=(.2, 1, .4), strength=1.5)
    rubber = mat('Black bumper rubber', (.02, .02, .02), 0, .75)
    n = 5; pitch = .75; L = pitch * (n - 1) + .9
    box('Ground rail base', (0, 0, .03), (L, .32, .06), grey, .01)
    for i in range(n):
        x = -L / 2 + .45 + i * pitch
        prism(f'Dock post {i + 1}', [(-.06, -.09), (.06, -.09), (.08, .1), (-.08, .1)], .06, .72, teal, .01)
        o = bpy.context.scene.objects[f'Dock post {i + 1}']; o.location.x = x
        box(f'Lock jaw housing {i + 1}', (x, -.12, .55), (.12, .1, .16), grey, .015)
        box(f'Lock jaw slot {i + 1}', (x, -.172, .55), (.03, .006, .1), rubber, 0)
        cyl(f'Status light {i + 1}', (x, -.02, .725), .018, .01, lamp, verts=24, bevel=.002)
        box(f'Wheel bumper {i + 1}', (x, -.22, .1), (.1, .14, .08), rubber, .01)
    xk = -L / 2 - .25
    box('Kiosk plinth', (xk, 0, .05), (.42, .36, .1), grey, .01)
    box('Kiosk column', (xk, 0, .95), (.36, .26, 1.7), teal, .02)
    mesh('Kiosk canopy', [(xk - .22, -.2, 1.8), (xk + .22, -.2, 1.8), (xk + .22, .16, 1.86), (xk - .22, .16, 1.86),
                          (xk - .22, -.2, 1.83), (xk + .22, -.2, 1.83), (xk + .22, .16, 1.89), (xk - .22, .16, 1.89)],
         [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], grey)
    box('Kiosk screen bezel', (xk, -.133, 1.32), (.28, .008, .36), grey, .004)
    box('Kiosk touch screen', (xk, -.138, 1.32), (.25, .004, .32), screen, 0)
    box('Card reader', (xk, -.15, 1.02), (.12, .04, .09), grey, .008)
    box('Card reader window', (xk, -.171, 1.02), (.08, .002, .05), screen, 0)
    box('Blank map panel', (xk, .133, 1.1), (.3, .006, .8), mat('Blank panel off-white', (.8, .8, .76), 0, .5), 0)
    return dict(id='city-bike-share-dock', title='シェアサイクル駐輪ドック', titleEn='Bike-share docking station',
                description='歩道に設置するシェアサイクルのドック5基と操作端末です。低い床レール、ロック爪付きのドック柱と前輪当て、各ドックの状態表示灯、ひさし付きの端末柱、タッチ画面・カード読取部・無地の案内板を造形しています。自転車、事業者名やロゴ、画面表示、電気的な機能は含みません。',
                descriptionEn='A five-dock bike-share station with a payment kiosk for sidewalk installation. It models the low ground rail, dock posts with lock-jaw housings and wheel bumpers, a status light on each dock, a canopied kiosk column, touch screen, card reader and a blank information panel. Bicycles, operator names or logos, on-screen content and electrical function are not included.',
                tags=['bike-share', 'docking-station', 'micromobility', 'kiosk', 'シェアサイクル'], view=(-60, 22))


# ---------------------------------------------------------------- parking lock
def parking_flap_lock():
    black = mat('Black cast housing', (.03, .03, .03), .4, .55)
    yellow = mat('Yellow powder-coated flap', (.95, .55, .0), .2, .4)
    stripe = mat('Black flap stripe', (.02, .02, .02), .2, .5)
    steel = mat('Stainless anchor bolts', (.55, .57, .57), .85, .3)
    L, W, h = .95, .42, .07
    mesh('Low ramped base housing', [(-W / 2, -L / 2, 0), (W / 2, -L / 2, 0), (W / 2, L / 2, 0), (-W / 2, L / 2, 0),
                                     (-W / 2 + .03, -L / 2 + .08, h), (W / 2 - .03, -L / 2 + .08, h), (W / 2 - .03, L / 2 - .08, h), (-W / 2 + .03, L / 2 - .08, h)],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], black, .004)
    ang = math.radians(32); fl = .5; hy = .12; fw = .34; t = .018
    ca, sa = math.cos(ang), math.sin(ang)
    def on_flap(u, v, w=0.0):
        """u across (X), v along the raised flap from the hinge, w along its upper normal."""
        return (u, hy - v * ca - w * sa, h + v * sa + w * ca)
    def plate(name, u0, u1, v0, v1, w0, w1, material, bevel=.003):
        vs = [on_flap(u, v, w) for w in (w0, w1) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        return mesh(name, vs, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material, bevel)
    plate('Raised lock flap', -fw / 2, fw / 2, 0, fl, 0, t, yellow)
    for k, v in enumerate((.17, .33)):
        plate(f'Flap stripe {k + 1}', -fw / 2 + .01, fw / 2 - .01, v - .03, v + .03, t, t + .002, stripe, 0)
    cyl('Flap hinge barrel', (0, hy, h), .022, fw + .02, black, 'X', 20, .002)
    for x in (-.11, .11):
        bar(f'Flap strut {x}', (x, hy - .3, h), on_flap(x, fl * .55, -.005), .025, .025, black)
        cyl(f'Strut pivot {x}', (x, hy - .3, h + .01), .016, .04, black, 'X', 16, .002)
    for x in (-W / 2 + .05, W / 2 - .05):
        for y in (-L / 2 + .04, L / 2 - .04):
            bolt(f'Anchor bolt {x}{y}', (x, y, .012), .011, .008, steel)
    return dict(id='city-parking-flap-lock', title='コインパーキングのロック板', titleEn='Coin parking flap lock',
                description='時間貸し駐車場の車室中央に置く、車両固定用のロック板装置です。前後が傾斜した黒い低床ハウジング、上がった状態の黄色いフラップと黒い帯、蝶番の軸と支え、アンカーボルトを造形しています。フラップは約32度で固定され、上下動作、センサー、配線、精算機、区画線は含みません。',
                descriptionEn='A coin-parking flap lock placed in the middle of a pay-parking bay. It models the low black ramped housing, the yellow flap with black stripes in its raised position, hinge barrel and struts, and anchor bolts. The flap is fixed at about 32 degrees; raising and lowering motion, sensors, wiring, pay stations and bay markings are not included.',
                tags=['parking', 'flap-lock', 'coin-parking', 'car-park', 'ロック板'], view=(-40, 28))


# ---------------------------------------------------------------- pedestrian signal
def pedestrian_signal_head():
    pole = mat('Grey signal pole paint', (.55, .57, .56), .4, .4)
    housing = mat('Dark grey signal housing', (.08, .09, .09), .3, .5)
    red = mat('Red signal lens, unlit', (.35, .03, .02), 0, .15)
    green = mat('Blue-green signal lens, lit', (.05, .45, .4), 0, .15, emission=(.15, 1, .8), strength=2.0)
    steel = mat('Band clamp steel', (.4, .42, .42), .7, .4)
    lathe('Signal pole', [(0, 0), (.07, 0), (.07, .02), (.06, .04), (.06, 3.0), (.055, 3.02), (0, 3.03)], pole, 32)
    cyl('Pole base flange', (0, 0, .015), .14, .03, pole, verts=32, bevel=.006)
    for k in range(6):
        a = k * math.tau / 6; bolt(f'Base nut {k}', (.11 * math.cos(a), .11 * math.sin(a), .035), .012, .01, steel)
    zc = 2.55; y = -.06 - .14
    for i, (z, lens) in enumerate([(zc + .19, red), (zc - .19, green)]):
        box(f'Lamp housing {i + 1}', (0, y, z), (.32, .26, .36), housing, .02)
        cyl(f'Lamp lens {i + 1}', (0, y - .13, z), .13, .01, lens, 'Y', 48, .002)
        # Hood visor wrapping the top and sides of each lens.
        pts = []
        for k in range(13):
            a = math.pi * k / 12
            pts.append((.155 * math.cos(a), .155 * math.sin(a)))
        for k in range(12):
            (x0, z0), (x1, z1) = pts[k], pts[k + 1]
            mesh(f'Visor {i + 1}.{k}', [(x0, y - .13, z + z0), (x1, y - .13, z + z1), (x1, y - .33, z + z1 * .9), (x0, y - .33, z + z0 * .9),
                                        (x0 * 1.03, y - .13, z + z0 * 1.03), (x1 * 1.03, y - .13, z + z1 * 1.03), (x1 * 1.03, y - .33, z + z1 * .93), (x0 * 1.03, y - .33, z + z0 * .93)],
                 [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], housing)
    for z in (zc - .25, zc + .25):
        torus(f'Pole band {z}', (0, 0, z), .065, .008, steel, None, 32, 6)
        box(f'Mounting arm {z}', (0, -.1, z), (.06, .08, .05), steel, .004)
    box('Rear junction box', (0, .07, zc - .55), (.12, .06, .16), housing, .01)
    return dict(id='city-pedestrian-signal-head', title='歩行者用信号機', titleEn='Pedestrian signal head on pole',
                description='横断歩道の端に立つ歩行者用信号機と支柱です。フランジ付きの丸柱、上下2灯の灯器箱とひさし、取付バンドと腕、背面の接続箱を造形しています。下の青緑レンズは点灯（発光材質）、上の赤レンズは消灯状態です。人形の図記号、押しボタン、待ち時間表示、配線、信号の切替動作は含みません。',
                descriptionEn='A pedestrian signal head on its own pole at the end of a crosswalk. It models the flanged round pole, two stacked lamp housings with hood visors, mounting bands and arms, and a rear junction box. The lower blue-green lens is lit using an emissive material and the upper red lens is unlit. Walking-figure pictograms, push buttons, countdown indicators, wiring and signal switching are not included.',
                tags=['traffic-signal', 'pedestrian-signal', 'crosswalk', '歩行者信号'], view=(-50, 12))


# ---------------------------------------------------------------- recycling bin
def bottle_can_recycling_bin():
    shell = mat('White rotomoulded polyethylene', (.82, .83, .82), 0, .55)
    blue = mat('Blue polyethylene lid', (.05, .22, .55), 0, .5)
    dark = mat('Opening shadow', (.01, .01, .012), 0, .8)
    grey = mat('Grey lock and hinge', (.25, .26, .26), .5, .45)
    W, D, Hh = .48, .4, .82
    box('Bin body', (0, 0, Hh / 2), (W, D, Hh), shell, .03)
    # Sloped blue top with two round deposit openings.
    zt = Hh; zb2 = Hh + .16
    mesh('Sloped lid', [(-W / 2, -D / 2, zt), (W / 2, -D / 2, zt), (W / 2, D / 2, zt), (-W / 2, D / 2, zt),
                        (-W / 2, -D / 2 + .06, zt + .08), (W / 2, -D / 2 + .06, zt + .08), (W / 2, D / 2, zb2), (-W / 2, D / 2, zb2)],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], blue, .015)
    slope = math.atan2(zb2 - zt - .08, D - .06)
    for x in (-.11, .11):
        o = cyl(f'Deposit opening {x}', (x, .04, (zt + .08 + zb2) / 2 + .002), .065, .012, dark, 'Z', 40, 0)
        o.rotation_euler = (slope, 0, 0)
        t = torus(f'Opening rim {x}', (x, .04, (zt + .08 + zb2) / 2 + .006), .066, .008, blue, (slope, 0, 0), 40, 6)
    box('Front service door seam', (0, -D / 2 - .001, .38), (W - .1, .002, .6), dark, 0)
    box('Front service door', (0, -D / 2 - .004, .38), (W - .11, .006, .59), shell, .008)
    cyl('Door lock', (W / 2 - .1, -D / 2 - .01, .55), .016, .012, grey, 'Y', 20, .002)
    for z in (.15, .6): box(f'Door hinge {z}', (-W / 2 + .06, -D / 2 - .008, z), (.02, .01, .06), grey, .003)
    box('Blank label panel', (0, -D / 2 - .008, .74), (.3, .002, .06), blue, 0)
    for x in (-W / 2 + .05, W / 2 - .05):
        for y in (-D / 2 + .05, D / 2 - .05):
            cyl(f'Leveling foot {x}{y}', (x, y, .006), .025, .012, grey, verts=16, bevel=.002)
    return dict(id='city-bottle-can-recycling-bin', title='自販機横のびん・缶回収箱', titleEn='Bottle and can recycling bin',
                description='自動販売機の横に置く、空きびん・缶の回収箱です。白い樹脂の本体、二つの丸い投入口を持つ傾斜した青いふた、前面の点検扉と錠・蝶番、無地のラベル帯、アジャスター脚を造形しています。分別表示の文字や図記号、中の容器、扉の開閉動作は含みません。',
                descriptionEn='A recycling bin for empty bottles and cans, placed beside vending machines. It models the white polyethylene body, a sloped blue lid with two round deposit openings, the front service door with lock and hinges, a blank label band and leveling feet. Sorting text and symbols, contained bottles and door motion are not included.',
                tags=['recycling-bin', 'vending', 'bottles-cans', 'waste', '回収箱'], view=(-48, 26))


# ---------------------------------------------------------------- A-type barricade
def a_type_barricade():
    yellow = mat('Yellow polyethylene', (.95, .55, .0), 0, .45)
    black = mat('Black stripe polyethylene', (.02, .02, .02), 0, .5)
    white = mat('White reflective strip', (.86, .87, .85), 0, .3)
    W = 1.2; Hh = .8; spread = .5
    for s in (-1, 1):
        x = s * (W / 2 - .05)
        bar(f'Leg front {s}', (x, -spread / 2, 0), (x, -.03, Hh - .02), .06, .035, yellow)
        bar(f'Leg back {s}', (x, spread / 2, 0), (x, .03, Hh - .02), .06, .035, yellow)
        box(f'Head cap {s}', (x, 0, Hh - .02), (.08, .1, .05), yellow, .01)
        bar(f'Leg spreader {s}', (x, -spread / 2 + .07, .2), (x, spread / 2 - .07, .2), .025, .025, yellow)
        for y in (-spread / 2, spread / 2):
            box(f'Foot pad {s}{y}', (x, y + (.02 if y < 0 else -.02), .01), (.09, .08, .02), black, .004)
    # Top beam with alternating yellow/black segments on both faces.
    n = 8; seg = (W - .2) / n
    for i in range(n):
        x = -W / 2 + .1 + seg * (i + .5)
        box(f'Top beam segment {i}', (x, 0, Hh - .1), (seg, .045, .14), yellow if i % 2 == 0 else black, .002 if i in (0, n - 1) else 0)
    box('Lower rail', (0, 0, .42), (W - .2, .035, .06), yellow, .006)
    for y in (-.024, .024):
        box(f'Reflective strip {y}', (0, y, Hh - .1), (.12, .002, .1), white, 0)
    return dict(id='city-a-type-barricade', title='A型バリケード', titleEn='A-type road barricade',
                description='工事現場や通行止めで使う、樹脂製のA型バリケードです。左右のA字脚と開き止め、上部の黄色と黒の交互帯の横木、下段の横木、中央の白い反射板、脚先のパッドを造形しています。文字・注意書き・連結金具・点滅灯は含みません。',
                descriptionEn='A plastic A-type barricade used at roadworks and closures. It models two A-frame legs with spreaders, a top beam with alternating yellow and black segments, a lower rail, a white center reflector and foot pads. Lettering, warnings, coupling hardware and flashing lamps are not included.',
                tags=['barricade', 'roadworks', 'traffic-control', 'temporary', 'バリケード'], view=(-50, 22))


# ---------------------------------------------------------------- crossing flag holder
def crossing_flag_holder():
    pole = mat('Galvanized post', (.5, .52, .52), .75, .4)
    box_m = mat('Yellow flag box', (.95, .55, .0), .1, .45)
    flag = mat('Plain yellow flag cloth', (.95, .62, .0), 0, .8)
    stick = mat('Natural bamboo stick', (.6, .48, .26), 0, .6)
    dark = mat('Clamp steel', (.2, .21, .21), .6, .45)
    cyl('Post', (0, 0, .7), .024, 1.4, pole, verts=24, bevel=.002)
    box('Base plate', (0, 0, .005), (.18, .18, .01), dark, .003)
    cyl('Post cap', (0, 0, 1.405), .026, .012, dark, verts=24, bevel=.004)
    zb = 1.0; y = -.1
    box('Flag box back', (0, y + .055, zb), (.24, .01, .4), box_m, .003)
    box('Flag box front', (0, y - .055, zb - .05), (.24, .01, .3), box_m, .003)
    for x in (-.115, .115): box(f'Flag box side {x}', (x, y, zb - .05), (.01, .1, .3), box_m, .002)
    box('Flag box bottom', (0, y, zb - .195), (.24, .12, .01), box_m, .002)
    for z in (zb - .12, zb + .12):
        torus(f'Pole clamp {z}', (0, 0, z), .028, .005, dark, None, 24, 6)
        box(f'Clamp tab {z}', (0, -.04, z), (.05, .03, .03), dark, .003)
    for k in range(4):
        x = -.075 + k * .05; tilt = (k - 1.5) * .06
        base = Vector((x, y + (k % 2) * .03 - .015, zb - .18)); top = base + Vector((tilt, -.03, .62))
        rod(f'Flag stick {k + 1}', base, top, .007, stick, 8)
        mesh(f'Plain flag {k + 1}', [(top.x, top.y, top.z - .02), (top.x + .24, top.y - .02, top.z - .04), (top.x + .24, top.y - .02, top.z - .22), (top.x, top.y, top.z - .2),
                                    (top.x, top.y + .002, top.z - .02), (top.x + .24, top.y - .018, top.z - .04), (top.x + .24, top.y - .018, top.z - .22), (top.x, top.y + .002, top.z - .2)],
             [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], flag)
    return dict(id='city-crossing-flag-holder', title='横断旗の旗立て', titleEn='Crossing flag holder',
                description='通学路の横断歩道脇に置く、横断旗を入れる黄色い箱と支柱です。表面設置の支柱とベース、取付バンド、前が低い旗入れ箱、竹の柄の無地の黄色い旗4本を造形しています。旗は文字のない無地で、布のなびきや揺れは静的な形状です。',
                descriptionEn='A yellow crossing-flag box on a post beside a school-route crosswalk. It models the surface-mounted post and base plate, clamp bands, a flag box with a lower front, and four plain yellow flags on bamboo sticks. The flags carry no lettering, and the cloth is static geometry without wind motion.',
                tags=['crosswalk', 'school-route', 'flag-holder', 'pedestrian-safety', '横断旗'], view=(-45, 14))


# ---------------------------------------------------------------- temporary fence
def temporary_mesh_fence_panel():
    galv = mat('Galvanized fence tube', (.55, .57, .57), .8, .35)
    wire = mat('Galvanized welded mesh', (.5, .52, .52), .8, .4)
    foot = mat('Grey moulded concrete foot', (.42, .42, .4), 0, .85)
    clamp = mat('Coupler steel', (.3, .31, .31), .7, .4)
    W, Hh, z0 = 2.4, 1.8, .1
    r = .019
    for x in (-W / 2 + .02, W / 2 - .02):
        rod(f'Upright tube {x}', (x, 0, .02), (x, 0, z0 + Hh), r, galv, 16)
        box(f'Concrete foot block {x}', (x, 0, .07), (.58, .22, .14), foot, .02)
        for dx in (-.18, .18):
            cyl(f'Foot socket {x}{dx}', (x + dx, 0, .15), .03, .03, foot, verts=16, bevel=.004)
    for z in (z0 + .03, z0 + Hh - .03):
        rod(f'Rail tube {z}', (-W / 2 + .02, 0, z), (W / 2 - .02, 0, z), r, galv, 16)
    wire_grid('Fence mesh', (-W / 2 + .02, 0, z0 + .03), (W - .04, 0, 0), (0, 0, Hh - .06), 24, 9, .0022, wire)
    for z in (z0 + .3, z0 + Hh - .3):
        for x in (-W / 2 + .02, W / 2 - .02):
            cyl(f'Panel coupler {x}{z}', (x, 0, z), .03, .07, clamp, verts=16, bevel=.004)
            bolt(f'Coupler bolt {x}{z}', (x, -.034, z), .009, .008, clamp, 'Y')
    return dict(id='city-temporary-mesh-fence-panel', title='仮設メッシュフェンス', titleEn='Temporary mesh fence panel',
                description='工事現場やイベント会場を囲う、置き式の仮設メッシュフェンス1枚です。亜鉛めっきの外枠パイプ、溶接金網、端部の連結クランプとボルト、パイプを差し込むコンクリート製の脚ブロックを造形しています。隣のパネル、目隠しシート、看板や文字、転倒防止の控えは含みません。',
                descriptionEn='One freestanding temporary mesh fence panel for construction sites and events. It models the galvanized frame tubes, welded mesh, end couplers with bolts and concrete foot blocks that receive the uprights. Adjacent panels, privacy sheeting, signs or lettering and anti-tip stays are not included.',
                tags=['temporary-fence', 'construction-site', 'crowd-control', 'mesh-fence', '仮囲い'], view=(-55, 18))


# ---------------------------------------------------------------- light box sign
def sidewalk_light_box_sign():
    frame = mat('Black aluminium frame', (.03, .03, .03), .6, .4)
    face = mat('Blank lit acrylic face', (.92, .9, .84), 0, .3, emission=(1, .94, .82), strength=1.2)
    base = mat('Black steel weight base', (.05, .05, .05), .5, .5)
    rubber = mat('Grey caster rubber', (.15, .15, .15), 0, .7)
    W, D, Hh, z0 = .42, .22, .9, .16
    box('Light box frame', (0, 0, z0 + Hh / 2), (W, D, Hh), frame, .01)
    for y in (-D / 2 - .002, D / 2 + .002):
        box(f'Lit face {y}', (0, y, z0 + Hh / 2), (W - .05, .004, Hh - .05), face, 0)
    box('Top cap', (0, 0, z0 + Hh + .01), (W + .02, D + .02, .02), frame, .006)
    box('Weighted base', (0, 0, .07), (W + .12, D + .2, .06), base, .01)
    box('Base neck', (0, 0, .12), (W - .04, D - .02, .06), base, .006)
    for x in (-W / 2, W / 2):
        for y in (-D / 2 - .07, D / 2 + .07):
            cyl(f'Caster {x}{y}', (x, y, .022), .022, .02, rubber, 'X', 16, .002)
            box(f'Caster fork {x}{y}', (x, y, .045), (.03, .03, .02), frame, .003)
    cyl('Power cord gland', (0, D / 2 + .004, .2), .01, .02, rubber, 'Y', 12, .002)
    return dict(id='city-sidewalk-light-box-sign', title='電飾スタンド看板', titleEn='Illuminated sidewalk light-box sign',
                description='飲食店の店先に置く、キャスター付きの電飾スタンド看板です。黒いアルミ枠と天板、両面の無地の発光アクリル面、重りの台座とキャスター、電源コードの出口を造形しています。面は文字のない無地で、発光は材質の自発光のみです。電源コード、照明器具、店名やメニューは含みません。',
                descriptionEn='A castered illuminated light-box sign for restaurant frontages. It models the black aluminium frame and top cap, blank lit acrylic faces on both sides, a weighted base with casters and a power-cord gland. Faces are blank; illumination is only an emissive material. Power cords, light fittings, shop names and menus are not included.',
                tags=['light-box', 'shop-sign', 'sidewalk-sign', 'illuminated', '電飾看板'], view=(-50, 15))


BUILDERS = {
    'city-folding-refuse-collection-cage': folding_refuse_collection_cage,
    'city-pushcart-food-stall': pushcart_food_stall,
    'city-wall-mailbox-bank': wall_mailbox_bank,
    'city-bike-share-dock': bike_share_dock,
    'city-parking-flap-lock': parking_flap_lock,
    'city-pedestrian-signal-head': pedestrian_signal_head,
    'city-bottle-can-recycling-bin': bottle_can_recycling_bin,
    'city-a-type-barricade': a_type_barricade,
    'city-crossing-flag-holder': crossing_flag_holder,
    'city-temporary-mesh-fence-panel': temporary_mesh_fence_panel,
    'city-sidewalk-light-box-sign': sidewalk_light_box_sign,
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
