"""Original roadwork, market and service street objects authored by Claude, CC BY 4.0.

No third-party meshes, textures, brand identities, lettering or font files.
Usage: python scripts/city_expansion/frozen/batch-062/scripts/city_expansion/claude_roadwork_market_objects.py --out DIR [--only ID ...]
"""
import sys, math, argparse, random
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

GENERATOR = Path(__file__).resolve().relative_to(ROOT).as_posix()


def wheel(name, center, radius, width, tyre, rim, axis='Y', spokes=0, spoke_mat=None):
    rot = (math.pi / 2, 0, 0) if axis == 'Y' else (0, math.pi / 2, 0)
    torus(name + ' tyre', center, radius - width * .35, width * .38, tyre, rot, 40, 10)
    cyl(name + ' rim', center, radius * .62, width * .7, rim, axis, 32, .003)
    cyl(name + ' hub', center, radius * .18, width * 1.05, rim, axis, 16, .003)
    for k in range(spokes):
        a = k * math.tau / spokes; c = Vector(center)
        d = Vector((math.cos(a), 0, math.sin(a))) if axis == 'Y' else Vector((0, math.cos(a), math.sin(a)))
        rod(f'{name} spoke {k}', c + d * radius * .18, c + d * radius * .62, .0035, spoke_mat or rim, 6)


# ---------------------------------------------------------------- security light
def pole_mounted_security_light():
    pole = mat('Galvanized lighting pole', (.52, .54, .54), .75, .4)
    head = mat('Grey luminaire housing', (.35, .37, .38), .5, .4)
    lens = mat('Frosted LED lens, lit', (.9, .92, .95), 0, .3, emission=(1, .97, .9), strength=3)
    panel = mat('Small solar panel cell', (.03, .05, .12), .3, .15)
    lathe('Lighting pole', [(0, 0), (.055, 0), (.055, .03), (.045, .05), (.042, 3.2), (.038, 3.25), (0, 3.26)], pole, 28)
    cyl('Pole flange', (0, 0, .012), .12, .024, pole, verts=28, bevel=.004)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4; bolt(f'Flange nut {k}', (.09 * math.cos(a), .09 * math.sin(a), .03), .011, .01, head)
    smooth_tube('Curved bracket arm', [(0, 0, 3.0), (0, -.18, 3.12), (0, -.45, 3.16), (0, -.6, 3.15)], .022, pole, 3, 10)
    box('Luminaire housing', (0, -.68, 3.13), (.16, .3, .07), head, .015)
    box('LED lens', (0, -.68, 3.093), (.13, .25, .006), lens, 0)
    box('Driver box', (0, .07, 2.6), (.1, .06, .16), head, .01)
    o = box('Solar panel', (0, .12, 3.3), (.32, .26, .025), panel, .004); o.rotation_euler = (math.radians(-25), 0, 0)
    box('Solar panel frame', (0, .12, 3.29), (.34, .28, .015), head, .003).rotation_euler = (math.radians(-25), 0, 0)
    rod('Panel bracket', (0, 0, 3.24), (0, .12, 3.28), .012, pole, 10)
    return dict(id='city-pole-mounted-security-light', title='防犯灯（ソーラー付き）', titleEn='Pole-mounted security light with solar panel',
                description='住宅地の生活道路に立つ、ソーラーパネル付きのLED防犯灯です。フランジ付きの細い鋼管柱とナット、曲げパイプの腕、灯具と発光するLEDレンズ、電源ボックス、傾けた小型ソーラーパネルと枠・取付腕を造形しています。発光は材質の自発光のみで、照明器具としての配光、配線、管理番号の文字は含みません。',
                descriptionEn='A solar-assisted LED security light for residential lanes. It models the slim flanged steel pole with nuts, a curved bracket arm, the luminaire with a lit LED lens, a driver box and a tilted small solar panel with frame and bracket. Illumination is an emissive material only; photometric light, wiring and asset-number lettering are not included.',
                tags=['street-light', 'security-light', 'solar', 'residential', '防犯灯'], view=(-55, 12))


# ---------------------------------------------------------------- temporary signal
def temporary_traffic_signal():
    yellow = mat('Yellow trailer paint', (.92, .58, .02), .3, .45)
    dark = mat('Black signal housing', (.03, .03, .03), .4, .5)
    red = mat('Red signal lens, lit', (.8, .04, .02), 0, .2, emission=(1, .08, .03), strength=3)
    amber = mat('Amber signal lens, unlit', (.35, .2, .02), 0, .2)
    green = mat('Green signal lens, unlit', (.02, .25, .12), 0, .2)
    tyre = mat('Trailer tyre rubber', (.02, .02, .02), 0, .85)
    rim = mat('Grey wheel rim', (.45, .46, .46), .7, .4)
    battery = mat('Grey battery box', (.4, .42, .42), .3, .5)
    box('Trailer chassis', (0, 0, .42), (1.4, .9, .08), yellow, .01)
    box('Battery and controller box', (0, 0, .62), (.9, .7, .34), battery, .02)
    box('Battery lid', (0, 0, .8), (.92, .72, .03), yellow, .008)
    for y in (-.5, .5): wheel(f'Wheel {y}', (0, y, .26), .26, .14, tyre, rim, 'Y')
    for y in (-.5, .5): box(f'Mudguard {y}', (0, y, .5), (.6, .16, .03), yellow, .006)
    bar('Drawbar', (.7, 0, .42), (1.3, 0, .38), .06, .06, yellow)
    cyl('Hitch coupler', (1.32, 0, .38), .04, .08, dark, 'Z', 16, .004)
    for x in (-.6, .6):
        for y in (-.4, .4):
            box(f'Outrigger jack {x}{y}', (x, y, .2), (.05, .05, .4), yellow, .004)
            cyl(f'Jack pad {x}{y}', (x, y, .01), .07, .02, dark, 'Z', 16, .003)
    box('Telescopic mast lower', (-.2, 0, 1.6), (.12, .12, 1.6), yellow, .006)
    box('Telescopic mast upper', (-.2, 0, 2.6), (.09, .09, .6), yellow, .005)
    zc = 2.55
    box('Signal head housing', (-.2, -.12, zc), (.36, .2, 1.02), dark, .02)
    for i, (z, lens) in enumerate([(zc + .32, red), (zc, amber), (zc - .32, green)]):
        cyl(f'Signal lens {i}', (-.2, -.223, z), .12, .01, lens, 'Y', 40, .002)
        pts = [(.15 * math.cos(math.pi * k / 10), .15 * math.sin(math.pi * k / 10)) for k in range(11)]
        for k in range(10):
            (x0, z0), (x1, z1) = pts[k], pts[k + 1]
            mesh(f'Visor {i}.{k}', [(-.2 + x0, -.225, z + z0), (-.2 + x1, -.225, z + z1), (-.2 + x1, -.38, z + z1 * .9), (-.2 + x0, -.38, z + z0 * .9),
                                    (-.2 + x0 * 1.04, -.225, z + z0 * 1.04), (-.2 + x1 * 1.04, -.225, z + z1 * 1.04), (-.2 + x1 * 1.04, -.38, z + z1 * .94), (-.2 + x0 * 1.04, -.38, z + z0 * .94)],
                 [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], dark)
    box('Backplate', (-.2, -.015, zc), (.5, .02, 1.16), dark, .006)
    return dict(id='city-temporary-traffic-signal', title='仮設信号機（トレーラー式）', titleEn='Temporary traffic signal trailer',
                description='片側交互通行の工事区間に置く、トレーラー式の仮設信号機です。黄色いシャシーと泥よけ、2輪の車輪、牽引棒と連結器、四隅のジャッキと接地パッド、バッテリー・制御箱、伸縮マスト、背板付き3灯の灯器とひさしを造形しています。赤レンズが点灯（発光材質）、黄・青は消灯状態で、信号の切替、走行、配線、注意書きの文字は含みません。',
                descriptionEn='A trailer-mounted temporary traffic signal for alternating one-lane roadworks. It models the yellow chassis and mudguards, two wheels, drawbar and coupler, corner jacks with pads, battery and controller box, telescopic mast, and a three-lamp head with backplate and visors. The red lens is lit with an emissive material and the amber and green lenses are unlit; signal switching, towing, wiring and warning lettering are not included.',
                tags=['roadworks', 'temporary-signal', 'traffic-control', 'trailer', '仮設信号'], view=(-55, 14))


# ---------------------------------------------------------------- arrow board
def construction_arrow_board():
    frame = mat('Galvanized stand frame', (.5, .52, .52), .75, .4)
    face = mat('Blue sign face', (.02, .12, .42), 0, .35)
    arrow = mat('White reflective arrow', (.88, .89, .87), 0, .25)
    rim = mat('Yellow-black border band', (.9, .58, .02), 0, .4)
    weight = mat('Black rubber base weight', (.03, .03, .03), 0, .8)
    W, H = .55, 1.4; z0 = .25
    box('Sign panel', (0, 0, z0 + H / 2), (W, .012, H), face, .004)
    for k in range(12):
        z = z0 + .02 + k * (H - .04) / 12
        box(f'Border band {k}', (0, -.007, z + (H - .04) / 24), (W, .002, (H - .04) / 12 - .004), rim if k % 2 == 0 else weight, 0)
    box('Inner face', (0, -.009, z0 + H / 2), (W - .07, .002, H - .07), face, 0)
    for i in range(3):
        zc = z0 + .3 + i * .4
        # Chevron arrow pointing left, built as a flat extruded outline.
        out = [(-.18, 0), (-.02, .14), (.06, .14), (-.06, .03), (.2, .03), (.2, -.03), (-.06, -.03), (.06, -.14), (-.02, -.14)]
        slab(f'Arrow {i}', [(x, zc + y) for x, y in out], -.0115, -.0105, arrow)
    for x in (-W / 2 + .05, W / 2 - .05):
        box(f'Stand upright {x}', (x, .02, .6), (.03, .03, 1.2), frame, .004)
        bar(f'Rear leg {x}', (x, .03, 1.0), (x, .45, .02), .03, .03, frame)
    box('Base runner', (0, .02, .03), (W + .2, .08, .04), frame, .004)
    for x in (-W / 2 - .05, W / 2 + .05): box(f'Rubber weight {x}', (x, .02, .07), (.18, .3, .08), weight, .015)
    return dict(id='city-construction-arrow-board', title='工事用矢印板', titleEn='Construction arrow board',
                description='工事区間の手前で車線の変更を促す、自立式の矢印板です。青い板面と白い矢印3つ、黄色と黒の縁取り、亜鉛めっきの支柱と後ろ脚、ベースの横材とゴムの重しを造形しています。矢印は記号の形状で、注意文や工事名などの文字、点滅灯、転倒時の挙動は含みません。',
                descriptionEn='A freestanding arrow board that guides drivers to change lanes ahead of roadworks. It models the blue panel with three white chevron arrows, a yellow-and-black border, galvanized uprights and rear legs, a base runner and rubber weights. Arrows are symbolic shapes only; warning text, project names, flashing lamps and tip-over behavior are not included.',
                tags=['roadworks', 'arrow-board', 'traffic-control', 'sign', '矢印板'], view=(-35, 14))


# ---------------------------------------------------------------- power pedestal
def outdoor_power_pedestal():
    body = mat('Stainless outlet pedestal', (.6, .62, .62), .85, .3)
    cover = mat('Grey weatherproof cover', (.3, .32, .33), .1, .45)
    dark = mat('Socket face black', (.03, .03, .03), .1, .5)
    shadow = mat('Socket shadow', (.0, .0, .0), 0, .7)
    concrete = mat('Concrete pad', (.48, .48, .46), 0, .85)
    box('Concrete pad', (0, 0, .04), (.45, .45, .08), concrete, .01)
    prism('Pedestal body', [(-.12, -.1), (.12, -.1), (.12, .1), (-.12, .1)], .08, 1.15, body, .01)
    mesh('Rain cap', [(-.15, -.14, 1.15), (.15, -.14, 1.15), (.15, .13, 1.15), (-.15, .13, 1.15), (-.15, -.14, 1.17), (.15, -.14, 1.17), (.15, .13, 1.21), (-.15, .13, 1.21)],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 6, 7, 3), (3, 7, 4, 0)], body, .004)
    for i, z in enumerate((.95, .7)):
        for x in (-.055, .055):
            box(f'Socket plate {i}{x}', (x, -.103, z), (.09, .006, .09), dark, .003)
            o = box(f'Hinged cover {i}{x}', (x, -.13, z + .03), (.095, .012, .07), cover, .004); o.rotation_euler = (math.radians(35), 0, 0)
            cyl(f'Socket pin recess {i}{x}', (x, -.107, z - .01), .02, .004, shadow, 'Y', 20, 0)
    box('Breaker window', (0, -.103, .45), (.16, .004, .1), dark, 0)
    box('Lockable breaker door', (0, -.106, .45), (.18, .004, .14), cover, .003)
    cyl('Door lock', (.07, -.11, .45), .008, .008, body, 'Y', 12, .001)
    box('Blank rating label', (0, -.103, 1.06), (.1, .002, .04), mat('Blank label', (.86, .86, .83), 0, .4), 0)
    return dict(id='city-outdoor-power-pedestal', title='屋外コンセント盤', titleEn='Outdoor power outlet pedestal',
                description='マルシェや屋台の会場、キャンプ場の区画に立つ、屋外用のコンセント盤です。コンクリートの台座、ステンレスの柱状の本体と雨よけの笠、上下2段・計4口のコンセントと開いた防水ふた、ブレーカーの窓と施錠扉、無地の定格ラベルを造形しています。電気的な機能、配線、定格表示の文字は含みません。',
                descriptionEn='An outdoor power outlet pedestal for markets, food-stall venues and camp pitches. It models the concrete pad, stainless body with rain cap, four sockets on two levels with raised weatherproof covers, a breaker window behind a lockable door, and a blank rating label. Electrical function, wiring and rating text are not included.',
                tags=['power-outlet', 'utility', 'market', 'pedestal', 'コンセント'], view=(-45, 16))


# ---------------------------------------------------------------- parasol
def street_vendor_parasol():
    canopy_a = mat('Cream canvas canopy', (.82, .76, .6), 0, .85)
    canopy_b = mat('Terracotta canvas canopy', (.55, .18, .1), 0, .85)
    pole = mat('Natural ash pole', (.6, .45, .28), 0, .55)
    rib = mat('Steel canopy ribs', (.3, .31, .31), .7, .4)
    base = mat('Granite parasol base', (.32, .32, .31), 0, .6)
    lathe('Granite base', [(0, 0), (.25, 0), (.26, .01), (.25, .07), (.05, .09), (0, .09)], base, 40)
    cyl('Base socket', (0, 0, .15), .035, .14, rib, 'Z', 20, .003)
    cyl('Parasol pole', (0, 0, 1.2), .022, 2.2, pole, 'Z', 20, .002)
    n = 8; R = 1.25; zt = 2.3; ze = 1.95
    for k in range(n):
        a0 = k * math.tau / n; a1 = (k + 1) * math.tau / n
        p0 = (R * math.cos(a0), R * math.sin(a0), ze); p1 = (R * math.cos(a1), R * math.sin(a1), ze)
        mid = ((p0[0] + p1[0]) / 2 * .97, (p0[1] + p1[1]) / 2 * .97, ze + .02)
        m = canopy_a if k % 2 == 0 else canopy_b
        mesh(f'Canopy panel {k}', [(0, 0, zt), p0, mid, p1, (0, 0, zt + .004), (p0[0], p0[1], ze + .004), (mid[0], mid[1], mid[2] + .004), (p1[0], p1[1], ze + .004)],
             [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (1, 5, 6, 2), (2, 6, 7, 3)], m, 0, False)
        rod(f'Canopy rib {k}', (0, 0, zt - .01), (p0[0] * .99, p0[1] * .99, ze - .005), .006, rib, 6)
        rod(f'Rib stretcher {k}', (0, 0, 1.75), (p0[0] * .45, p0[1] * .45, zt - (zt - ze) * .45 - .01), .005, rib, 6)
        # Scalloped valance flap below each panel edge.
        mesh(f'Valance {k}', [p0, p1, (p1[0], p1[1], ze - .12), (p0[0], p0[1], ze - .12)], [(0, 1, 2, 3)], m)
    cyl('Runner', (0, 0, 1.75), .035, .08, rib, 'Z', 16, .004)
    lathe('Finial', [(0, zt), (.03, zt), (.035, zt + .04), (.02, zt + .08), (0, zt + .1)], pole, 16)
    return dict(id='city-street-vendor-parasol', title='露店用パラソル', titleEn='Street vendor parasol',
                description='朝市や露店の売り場に立てる、8枚張りの布製パラソルです。御影石の台座と差し込み口、木の柱、生成りとテラコッタ色の交互の布、骨と受け骨、ろくろ、頭の飾り、縁の垂れ幕を造形しています。布は無地で、開閉や風での揺れは動作せず、売り物や看板の文字は含みません。',
                descriptionEn='An eight-panel canvas parasol for morning markets and street stalls. It models the granite base with socket, a wooden pole, alternating cream and terracotta canvas panels, ribs and stretchers, runner, finial and a valance around the edge. The canvas is plain; opening, closing and wind motion are not rigged, and goods or sign lettering are not included.',
                tags=['parasol', 'market', 'street-vendor', 'shade', 'パラソル'], view=(-50, 20))


# ---------------------------------------------------------------- crate seating
def plastic_crate_seating():
    crate_a = mat('Yellow polypropylene crate', (.92, .6, .02), 0, .55)
    crate_b = mat('Red polypropylene crate', (.62, .06, .04), 0, .55)
    plank = mat('Rough sawn plank', (.5, .36, .22), 0, .75)
    hole = mat('Hand hole shadow', (.01, .01, .01), 0, .8)
    W, D, H, t = .45, .32, .3, .012
    def crate(name, loc, m):
        x0, y0, z0 = loc
        box(name + ' floor', (x0, y0, z0 + t / 2), (W, D, t), m, .003)
        for s in (-1, 1):
            box(f'{name} long wall {s}', (x0, y0 + s * (D / 2 - t / 2), z0 + H / 2), (W, t, H), m, .003)
            box(f'{name} short wall {s}', (x0 + s * (W / 2 - t / 2), y0, z0 + H / 2), (t, D - 2 * t, H), m, .003)
            box(f'{name} hand hole {s}', (x0 + s * (W / 2 - t / 2), y0, z0 + H - .07), (t * 1.2, .1, .035), hole, 0)
            for k in range(3):
                box(f'{name} wall rib {s}.{k}', (x0 - W / 2 + .1 + k * .125, y0 + s * (D / 2 + .002), z0 + H / 2), (.012, .006, H - .02), m, .002)
        box(name + ' top rim', (x0, y0, z0 + H - .008), (W + .006, D + .006, .016), m, .003)
    crate('Lower crate A', (-.24, 0, 0), crate_a); crate('Upper crate A', (-.24, 0, H), crate_b)
    crate('Lower crate B', (.24, 0, 0), crate_b); crate('Upper crate B', (.24, 0, H), crate_a)
    crate('Side stool crate', (.95, .1, 0), crate_a)
    box('Bench plank', (0, 0, 2 * H + .015), (1.2, .28, .03), plank, .004)
    box('Stool cushion board', (.95, .1, H + .012), (.42, .3, .024), plank, .004)
    return dict(id='city-plastic-crate-seating', title='ケース積みの屋台席', titleEn='Plastic crate seating',
                description='路地の屋台や立ち飲み屋の前で、樹脂製の運搬ケースを積んで作る簡易な席です。2段積みのケース2組に渡した板の長椅子と、ケース1個に板を載せた丸椅子を造形しています。ケースの壁・底・取っ手穴・リブ・上縁を個別に作り、銘柄・社名・ロゴなどの文字や図柄は含みません。',
                descriptionEn='Improvised seating built from stacked plastic crates in front of alley food stalls and standing bars. It models a plank bench across two double-stacked crate pairs and a single-crate stool with a board seat. Crate walls, floors, hand holes, ribs and top rims are modelled individually, with no brand names, company names, logos or other lettering.',
                tags=['crate', 'seating', 'yokocho', 'street-food', 'ビールケース'], view=(-40, 22))


# ---------------------------------------------------------------- hanging sign
def hanging_shop_sign():
    iron = mat('Black wrought iron bracket', (.03, .03, .03), .6, .45)
    board = mat('Blank painted sign board', (.12, .2, .16), 0, .55)
    edge = mat('Gilded edge moulding', (.6, .45, .15), .8, .35)
    wall = mat('Plaster wall plate', (.7, .68, .62), 0, .85)
    box('Wall mounting plate', (0, .02, 1.0), (.12, .02, .5), wall, .006)
    box('Bracket backplate', (0, 0, 1.0), (.06, .012, .42), iron, .003)
    bar('Bracket arm', (0, -.006, 1.2), (0, -.9, 1.2), .03, .016, iron)
    smooth_tube('Bracket brace scroll', [(0, -.01, .82), (0, -.2, .95), (0, -.45, 1.08), (0, -.7, 1.18)], .008, iron, 2, 10)
    # Two scroll curls bridging the gap between the arm and the brace.
    for y, z, r in ((-.35, 1.1, .085), (-.55, 1.15, .043)):
        torus(f'Scroll curl {y}', (0, y, z), r, .006, iron, (0, math.pi / 2, 0), 24, 6)
    for y in (-.25, -.75):
        rod(f'Chain hanger {y}', (0, y, 1.19), (0, y, 1.1), .004, iron, 6)
        torus(f'Hanger ring {y}', (0, y, 1.1), .015, .004, iron, (0, math.pi / 2, 0), 12, 6)
    box('Sign board', (0, -.5, .82), (.03, .62, .5), board, .006)
    for z in (.575, 1.065): box(f'Board edge {z}', (0, -.5, z), (.04, .64, .02), edge, .004)
    for y in (-.19, -.81): box(f'Board side edge {y}', (0, y, .82), (.04, .02, .5), edge, .004)
    return dict(id='city-hanging-shop-sign', title='吊り下げ看板（無地）', titleEn='Hanging shop sign, blank',
                description='店先の壁から張り出す、鍛鉄の腕金に吊るした看板です。壁の取付板と背板、腕金と渦巻き飾りの支え、吊り輪、深緑の看板板と金色の縁を造形しています。板面は店名やロゴのない無地で、揺れの動作や壁への固定金具の内部は含みません。',
                descriptionEn='A projecting shop sign hung from a wrought-iron bracket. It models the wall mounting plate and backplate, bracket arm with scrolled brace, hanger rings, and a deep-green board with gilded edge mouldings. The board is blank without shop names or logos; swinging motion and concealed wall fixings are not included.',
                tags=['shop-sign', 'projecting-sign', 'storefront', 'wrought-iron', '吊り看板'], view=(-40, 12))


# ---------------------------------------------------------------- coffee tricycle
def tricycle_coffee_cart():
    body = mat('Sage green cart paint', (.28, .38, .3), .3, .4)
    wood = mat('Oiled walnut counter', (.25, .15, .08), 0, .5)
    steel = mat('Polished steel tube', (.6, .62, .62), .85, .25)
    tyre = mat('Black bicycle tyre', (.02, .02, .02), 0, .8)
    rim = mat('Silver bicycle rim', (.7, .72, .72), .85, .3)
    seat = mat('Brown saddle leather', (.3, .17, .08), 0, .55)
    canvas = mat('Striped canopy canvas', (.85, .82, .72), 0, .85)
    box('Cargo box', (.35, 0, .62), (.8, .62, .55), body, .02)
    box('Counter top', (.35, 0, .91), (.86, .68, .03), wood, .006)
    box('Front service hatch', (.35, -.32, .65), (.6, .012, .38), wood, .006)
    for y in (-.36, .36): wheel(f'Front wheel {y}', (.35, y, .25), .25, .045, tyre, rim, 'Y', 16, steel)
    cyl('Front axle', (.35, 0, .25), .015, .76, steel, 'Y', 12, .002)
    wheel('Rear wheel', (-.75, 0, .32), .32, .04, tyre, rim, 'Y', 20, steel)
    bar('Down tube', (-.1, 0, .45), (-.45, 0, .85), .035, .035, body)
    bar('Seat tube', (-.55, 0, .35), (-.5, 0, .85), .03, .03, body)
    bar('Chain stay', (-.75, 0, .32), (-.4, 0, .35), .025, .025, body)
    bar('Seat stay', (-.75, 0, .32), (-.52, 0, .82), .022, .022, body)
    box('Saddle', (-.5, 0, .9), (.25, .14, .05), seat, .02)
    cyl('Crank hub', (-.4, 0, .35), .07, .05, steel, 'Y', 24, .004)
    for s in (-1, 1): bar(f'Crank arm {s}', (-.4, s * .05, .35), (-.4 + .14 * s, s * .08, .35 - .1 * s), .02, .012, steel)
    bar('Handlebar stem', (-.05, 0, .92), (-.08, 0, 1.08), .03, .03, steel)
    rod('Handlebar', (-.08, -.28, 1.08), (-.08, .28, 1.08), .012, steel, 10)
    for y in (-.28, .28): cyl(f'Grip {y}', (-.08, y, 1.08), .017, .1, tyre, 'Y', 12, .003)
    for x in (.0, .7):
        for y in (-.3, .3): rod(f'Canopy post {x}{y}', (x, y, .93), (x, y, 1.75), .01, steel, 8)
    n = 6
    for i in range(n):
        x0 = -.05 + i * .8 / n; x1 = x0 + .8 / n
        mesh(f'Canopy stripe {i}', [(x0, -.38, 1.72), (x1, -.38, 1.72), (x1, .38, 1.72), (x0, .38, 1.72), (x0, 0, 1.82), (x1, 0, 1.82)],
             [(0, 1, 5, 4), (4, 5, 2, 3)], canvas if i % 2 == 0 else body)
    lathe('Espresso boiler', [(0, 0), (.1, 0), (.1, .22), (.06, .28), (0, .29)], steel, 32).location = (.55, .1, .925)
    box('Grinder', (.2, .15, 1.05), (.12, .14, .22), body, .015)
    box('Cup stack', (.2, -.15, .97), (.08, .08, .1), mat('White paper cups', (.92, .92, .9), 0, .5), .02)
    return dict(id='city-tricycle-coffee-cart', title='三輪コーヒーカート', titleEn='Tricycle coffee cart',
                description='公園や駅前で営業する、前2輪の三輪自転車型コーヒーカートです。荷台の箱と木の天板、前面の販売口のふた、スポーク付きの前輪2つと後輪、フレーム・サドル・クランク・ハンドル、ストライプの屋根と支柱、エスプレッソのボイラーとグラインダー、紙コップの束を造形しています。店名やロゴ、メニューの文字、走行・調理の動作は含みません。',
                descriptionEn='A front-loading tricycle coffee cart for parks and station plazas. It models the cargo box with walnut counter and front service hatch, two spoked front wheels and a rear wheel, frame, saddle, cranks and handlebar, a striped canopy on posts, an espresso boiler, grinder and a stack of paper cups. Shop names, logos, menu text and riding or brewing motion are not included.',
                tags=['coffee-cart', 'tricycle', 'street-food', 'mobile-vendor', 'コーヒーカート'], view=(-55, 18))


# ---------------------------------------------------------------- emergency call post
def emergency_call_pillar():
    body = mat('Signal red pillar enamel', (.62, .05, .04), .3, .35)
    panel = mat('Brushed stainless call panel', (.6, .62, .62), .85, .3)
    dark = mat('Speaker grille black', (.02, .02, .02), .3, .5)
    lamp = mat('Blue beacon lens, lit', (.1, .3, .9), 0, .2, emission=(.2, .45, 1), strength=3)
    button = mat('Yellow call button', (.9, .62, .02), 0, .3)
    concrete = mat('Concrete footing', (.48, .48, .46), 0, .85)
    cyl('Footing', (0, 0, .05), .22, .1, concrete, 'Z', 32, .01)
    lathe('Pillar body', [(0, .1), (.13, .1), (.13, 1.75), (.125, 1.78), (0, 1.79)], body, 40)
    cyl('Beacon base', (0, 0, 1.81), .07, .04, dark, 'Z', 24, .004)
    lathe('Beacon lens', [(0, 1.83), (.06, 1.83), (.06, 1.93), (.04, 1.97), (0, 1.98)], lamp, 24)
    box('Call panel', (0, -.12, 1.3), (.16, .04, .36), panel, .01)
    cyl('Call button', (0, -.142, 1.24), .03, .012, button, 'Y', 32, .003)
    torus('Button ring', (0, -.141, 1.24), .033, .004, dark, (math.pi / 2, 0, 0), 24, 6)
    for k in range(5): box(f'Speaker slot {k}', (0, -.141, 1.36 + k * .016), (.08, .002, .006), dark, 0)
    cyl('Camera dome', (0, -.13, 1.6), .035, .02, dark, 'Y', 20, .004)
    box('Blank instruction plate', (0, -.131, .95), (.14, .002, .18), panel, 0)
    for z in (.4, 1.0):
        torus(f'Reflective band {z}', (0, 0, z), .131, .006, mat('White reflective band', (.86, .86, .84), 0, .3), None, 40, 6)
    return dict(id='city-emergency-call-pillar', title='非常通報ポール', titleEn='Emergency call pillar',
                description='公園や駅前、駐車場に立つ、非常時の通報用ポールです。コンクリート基礎、赤い円柱の本体と反射帯、頭部の青い点灯ビーコン（発光材質）、ステンレスの通話パネルと黄色い呼出しボタン、スピーカーの穴、カメラドーム、無地の案内板を造形しています。案内文・電話番号などの文字や記号、通話・録画などの機能は含みません。',
                descriptionEn='An emergency call pillar for parks, station plazas and car parks. It models the concrete footing, red cylindrical body with reflective bands, a lit blue beacon on top (emissive material), a stainless call panel with a yellow call button, speaker slots, a camera dome and a blank instruction plate. Instructions, phone numbers and other lettering or symbols, and calling or recording functions are not included.',
                tags=['emergency', 'call-point', 'safety', 'public-space', '非常通報'], view=(-45, 12))


BUILDERS = {
    'city-pole-mounted-security-light': pole_mounted_security_light,
    'city-temporary-traffic-signal': temporary_traffic_signal,
    'city-construction-arrow-board': construction_arrow_board,
    'city-outdoor-power-pedestal': outdoor_power_pedestal,
    'city-street-vendor-parasol': street_vendor_parasol,
    'city-plastic-crate-seating': plastic_crate_seating,
    'city-hanging-shop-sign': hanging_shop_sign,
    'city-tricycle-coffee-cart': tricycle_coffee_cart,
    'city-emergency-call-pillar': emergency_call_pillar,
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
