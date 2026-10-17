"""Original residential, parking and civic-safety street objects authored by Claude, CC BY 4.0.

No third-party meshes, textures, brand identities, lettering or font files.
Usage: python scripts/city_expansion/frozen/batch-063/scripts/city_expansion/claude_residential_civic_objects.py --out DIR [--only ID ...]
"""
import sys, math, argparse, random
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

GENERATOR = Path(__file__).resolve().relative_to(ROOT).as_posix()


def shell_box(name, center, size, material, bevel=.01):
    return box(name, center, size, material, bevel)


# ---------------------------------------------------------------- bicycle pay station
def bicycle_parking_pay_station():
    body = mat('Light grey kiosk enamel', (.7, .72, .7), .3, .4)
    accent = mat('Green accent panel', (.05, .35, .2), .2, .4)
    screen = mat('Dark LCD glass', (.02, .025, .03), 0, .08)
    keys = mat('Silver keypad', (.6, .62, .62), .8, .3)
    dark = mat('Slot shadow', (.02, .02, .02), .2, .6)
    box('Plinth', (0, 0, .04), (.5, .4, .08), dark, .01)
    box('Kiosk body', (0, 0, .7), (.42, .32, 1.24), body, .02)
    mesh('Sloped hood', [(-.24, -.2, 1.32), (.24, -.2, 1.32), (.24, .18, 1.36), (-.24, .18, 1.36), (-.24, -.2, 1.35), (.24, -.2, 1.35), (.24, .18, 1.42), (-.24, .18, 1.42)],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 6, 7, 3), (3, 7, 4, 0)], accent, .004)
    box('Accent stripe', (0, -.162, 1.22), (.42, .004, .08), accent, 0)
    box('Screen bezel', (0, -.163, 1.02), (.26, .006, .17), dark, .003)
    box('LCD screen', (0, -.167, 1.02), (.22, .002, .13), screen, 0)
    for r in range(4):
        for c in range(3):
            box(f'Key {r}{c}', (-.06 + c * .06, -.168, .86 - r * .04), (.045, .008, .03), keys, .003)
    box('Coin slot plate', (.13, -.164, .82), (.06, .006, .1), keys, .003)
    box('Coin slot', (.13, -.168, .84), (.006, .002, .03), dark, 0)
    box('Note slot', (.13, -.168, .79), (.04, .002, .006), dark, 0)
    box('Card reader', (-.12, -.17, .7), (.1, .02, .07), dark, .006)
    box('Change tray recess', (0, -.163, .42), (.16, .006, .08), dark, .004)
    box('Receipt slot', (.1, -.168, .6), (.07, .002, .008), dark, 0)
    for xx, zz, sx, sz in ((0, 1.25, .36, .004), (0, .15, .36, .004), (-.18, .7, .004, 1.1), (.18, .7, .004, 1.1)):
        box(f'Service door seam {xx} {zz}', (xx, .161, zz), (sx, .002, sz), dark, 0)
    return dict(id='city-bicycle-parking-pay-station', title='駐輪場の精算機', titleEn='Bicycle parking pay station',
                description='駅前の駐輪場に置く、自立式の料金精算機です。台座、淡灰色の本体と緑の傾斜屋根・帯、液晶画面、テンキー、硬貨・紙幣・カードの投入口、レシート口、つり銭受け、背面の保守扉の継ぎ目を造形しています。料金表・案内文などの文字、画面表示、決済機能は含みません。',
                descriptionEn='A freestanding pay station for station bicycle parking. It models the plinth, pale grey body with a green sloped hood and stripe, LCD screen, numeric keypad, coin, note and card slots, receipt slot, change tray and the rear service door seam. Price tables, instructions and other text, on-screen content and payment function are not included.',
                tags=['bicycle-parking', 'pay-station', 'kiosk', 'station', '精算機'], view=(-40, 12))


# ---------------------------------------------------------------- car park pay station
def car_park_pay_station():
    body = mat('Navy kiosk enamel', (.04, .08, .2), .3, .4)
    trim = mat('Brushed stainless trim', (.62, .64, .64), .85, .3)
    screen = mat('Dark LCD glass', (.02, .025, .03), 0, .08)
    lamp = mat('Lit header panel', (.9, .92, .95), 0, .3, emission=(1, 1, 1), strength=1.2)
    dark = mat('Slot shadow', (.02, .02, .02), .2, .6)
    concrete = mat('Concrete island', (.5, .5, .48), 0, .85)
    prism('Concrete island', [(-.45, -.35), (.45, -.35), (.45, .35), (-.45, .35)], 0, .15, concrete, .02)
    box('Kiosk body', (0, 0, .85), (.55, .4, 1.4), body, .02)
    box('Lit header', (0, -.205, 1.45), (.5, .012, .12), lamp, .003)
    box('Canopy', (0, -.05, 1.6), (.7, .6, .04), trim, .006)
    box('Canopy post', (0, .18, 1.57), (.08, .08, .06), trim, .004)
    box('Front panel', (0, -.203, .95), (.46, .006, .7), trim, .004)
    box('LCD screen', (0, -.208, 1.18), (.26, .004, .16), screen, .002)
    for r in range(3):
        for c in range(4):
            box(f'Button {r}{c}', (-.12 + c * .08, -.209, .98 - r * .05), (.06, .008, .035), dark if (r + c) % 3 else body, .003)
    box('Ticket slot', (-.12, -.21, .8), (.1, .006, .012), dark, 0)
    box('Coin slot', (.06, -.21, .82), (.008, .006, .035), dark, 0)
    box('Note slot', (.15, -.21, .82), (.07, .006, .008), dark, 0)
    box('Card reader', (.1, -.215, .7), (.12, .02, .07), dark, .006)
    box('Change tray', (0, -.21, .5), (.2, .02, .09), dark, .006)
    box('Intercom grille', (-.17, -.208, .68), (.06, .004, .06), dark, .002)
    for x in (-.4, .4):
        cyl(f'Bollard guard {x}', (x, -.25, .5), .05, .7, mat('Yellow guard paint', (.95, .55, .0), .2, .45), 'Z', 20, .004)
    return dict(id='city-car-park-pay-station', title='駐車場の精算機', titleEn='Car park pay station',
                description='時間貸し駐車場に置く、ひさし付きの料金精算機です。コンクリートの島、紺色の本体、発光する無地のヘッダー、ステンレスの前面とひさし、液晶画面と押しボタン、駐車券・硬貨・紙幣・カードの投入口、インターホン、つり銭受け、両脇の黄色い防護柱を造形しています。料金・案内の文字、画面表示、決済や通話の機能は含みません。',
                descriptionEn='A canopied pay station for pay-by-time car parks. It models the concrete island, navy body, a lit blank header, stainless front panel and canopy, LCD screen and buttons, ticket, coin, note and card slots, intercom grille, change tray and two yellow guard posts. Prices, instructions and other text, on-screen content and payment or intercom function are not included.',
                tags=['car-park', 'pay-station', 'parking', 'kiosk', '精算機'], view=(-42, 12))


# ---------------------------------------------------------------- height gantry
def height_limit_gantry():
    steel = mat('Galvanized gantry steel', (.52, .54, .54), .75, .4)
    yellow = mat('Yellow hazard band', (.95, .55, .0), .1, .4)
    black = mat('Black hazard band', (.02, .02, .02), .1, .5)
    chain = mat('Zinc hanging chain', (.55, .57, .57), .85, .3)
    W = 3.6; H = 2.6
    for x in (-W / 2, W / 2):
        box(f'Upright {x}', (x, 0, H / 2 + .1), (.15, .15, H + .2), steel, .008)
        box(f'Base plate {x}', (x, 0, .01), (.35, .35, .02), steel, .004)
        for k in range(8):
            box(f'Upright band {x} {k}', (x, 0, .15 + k * .2 + .1), (.152, .152, .2), yellow if k % 2 == 0 else black, 0)
    box('Top beam', (0, 0, H + .25), (W + .15, .15, .15), steel, .008)
    # Suspended warning bar on chains (clearance indicator), alternating bands.
    zb = H - .1; n = 18
    for k in range(n):
        x = -W / 2 + .1 + (W - .2) * (k + .5) / n
        cyl(f'Warning bar segment {k}', (x, 0, zb), .045, (W - .2) / n, yellow if k % 2 == 0 else black, 'X', 20, 0)
    for x in (-1.2, 0, 1.2):
        n_links = 6
        for i in range(n_links):
            z = zb + .06 + i * (H + .17 - zb - .06) / n_links
            o = torus(f'Chain link {x} {i}', (x, 0, z + .025), .02, .005, chain, (0, 0, (math.pi / 2) * (i % 2)), 12, 6); o.scale = (1, 1, 1.6)
    return dict(id='city-height-limit-gantry', title='高さ制限ゲート', titleEn='Height limit gantry',
                description='駐車場や高架下の入口に立つ、高さ制限の門型ゲートです。亜鉛めっきの2本の柱と上部の梁、柱の黄色と黒の帯、鎖で吊った黄黒の警告バー、柱脚のベースプレートを造形しています。制限高さの数字や注意文の文字、衝突時の揺れは含みません。幅約3.7m、警告バー下端は約2.45mです。',
                descriptionEn='A height-limit gantry for car park and underpass entrances. It models two galvanized uprights with a top beam, yellow-and-black bands on the uprights, a yellow-and-black warning bar hung on chains, and base plates. Clearance numerals and warning text, and swinging on impact, are not included. About 3.7 m wide; the warning bar underside is at about 2.45 m.',
                tags=['height-limit', 'gantry', 'car-park', 'clearance', '高さ制限'], view=(-55, 14))


# ---------------------------------------------------------------- disaster speaker pole
def disaster_warning_speaker_pole():
    concrete = mat('Concrete pole grey', (.52, .52, .5), 0, .82)
    steel = mat('Galvanized bracket steel', (.5, .52, .52), .75, .4)
    horn = mat('Grey horn speaker', (.6, .62, .6), .3, .45)
    dark = mat('Speaker throat shadow', (.03, .03, .03), .2, .6)
    box_m = mat('Grey equipment cabinet', (.55, .57, .55), .3, .45)
    panel = mat('Solar panel cells', (.03, .05, .12), .3, .15)
    lathe('Concrete pole', [(0, 0), (.16, 0), (.15, 4), (.12, 9.6), (.11, 9.7), (0, 9.72)], concrete, 32)
    z = 9.1
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4; d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((0, 0, z)) + d * .14
        bar(f'Speaker bracket {k}', base, base + d * .35 + Vector((0, 0, .05)), .04, .04, steel)
        o = lathe(f'Horn speaker {k}', [(0, 0), (.09, 0), (.09, .12), (.12, .2), (.2, .38), (.28, .5), (.27, .52), (0, .52)], horn, 32)
        o.location = base + d * .4 + Vector((0, 0, .05)); o.rotation_euler = Vector((d.x, d.y, -.35)).to_track_quat('Z', 'Y').to_euler()
        c = lathe(f'Horn throat {k}', [(0, .49), (.25, .49), (.25, .5), (0, .5)], dark, 32)
        c.location = o.location; c.rotation_euler = o.rotation_euler
        cyl(f'Driver can {k}', (0, 0, 0), .08, .14, horn, 'Z', 20, .006).location = o.location
    torus('Bracket band upper', (0, 0, z + .05), .145, .012, steel, None, 32, 6)
    torus('Bracket band lower', (0, 0, z - .05), .145, .012, steel, None, 32, 6)
    box('Equipment cabinet', (0, -.32, 2.4), (.45, .25, .7), box_m, .015)
    for zz in (2.15, 2.65): box(f'Cabinet band {zz}', (0, -.16, zz), (.1, .1, .05), steel, .004)
    box('Cabinet roof', (0, -.33, 2.77), (.5, .3, .03), box_m, .006)
    o = box('Solar panel', (0, -.45, 8.2), (.6, .04, .9), panel, .006); o.rotation_euler = (math.radians(-30), 0, 0)
    bar('Solar bracket', (0, -.12, 8.2), (0, -.4, 8.2), .05, .05, steel)
    tube('Cable conduit', [(0, -.16, 2.75), (0, -.16, 9.0)], .02, steel, 2, 4)
    box('Antenna mast', (0, 0, 9.9), (.03, .03, .4), steel, .004)
    return dict(id='city-disaster-warning-speaker-pole', title='防災行政無線のスピーカー柱', titleEn='Disaster warning speaker pole',
                description='地域に防災放送を流す、屋外拡声子局のスピーカー柱です。高さ約9.7mのコンクリート柱、上部の4方向のホーンスピーカーと金具・バンド、ソーラーパネル、配線管、柱脚の機器箱とアンテナを造形しています。放送や音響の機能、管理番号などの文字は含みません。',
                descriptionEn='An outdoor public-address speaker pole used for municipal disaster warnings. It models a roughly 9.7 m concrete pole, four horn speakers on brackets and clamp bands near the top, a solar panel, a cable conduit, an equipment cabinet at the base and a small antenna mast. Broadcast or acoustic function and asset-number lettering are not included.',
                tags=['disaster-warning', 'speaker', 'public-address', 'pole', '防災無線'], view=(-50, 10))


# ---------------------------------------------------------------- disaster storage shed
def disaster_supply_storage_shed():
    wall = mat('Cream steel shed panels', (.78, .76, .66), .3, .45)
    trim = mat('Green trim steel', (.07, .25, .14), .3, .4)
    roof = mat('Grey corrugated roof steel', (.45, .47, .47), .6, .45)
    dark = mat('Door gap shadow', (.02, .02, .02), .2, .6)
    base = mat('Concrete footing blocks', (.48, .48, .46), 0, .85)
    W, D, H = 2.1, 1.4, 1.9
    for x in (-W / 2 + .1, W / 2 - .1):
        for y in (-D / 2 + .1, D / 2 - .1): box(f'Footing {x}{y}', (x, y, .05), (.25, .25, .1), base, .01)
    box('Floor frame', (0, 0, .14), (W, D, .08), trim, .006)
    box('Wall shell', (0, 0, .18 + H / 2), (W, D, H), wall, .01)
    for k in range(12):
        x = -W / 2 + .1 + k * (W - .2) / 11
        box(f'Side rib {k}', (x, D / 2 + .006, .18 + H / 2), (.02, .012, H - .1), wall, .003)
    # Sliding double doors on the front.
    box('Door gap', (0, -D / 2 - .001, .18 + (H - .15) / 2), (.008, .002, H - .2), dark, 0)
    for s in (-1, 1):
        box(f'Sliding door {s}', (s * .45, -D / 2 - .012, .18 + (H - .15) / 2), (.88, .02, H - .2), wall, .006)
        box(f'Door handle {s}', (s * .06, -D / 2 - .03, 1.0), (.025, .02, .25), trim, .004)
    box('Door top rail', (0, -D / 2 - .03, H + .08), (W - .1, .04, .06), trim, .004)
    box('Door bottom rail', (0, -D / 2 - .025, .2), (W - .1, .03, .03), trim, .004)
    box('Blank notice plate', (0, -D / 2 - .025, 1.6), (.5, .004, .2), mat('Blank white notice plate', (.88, .88, .85), 0, .4), 0)
    zt = .18 + H; ridge = zt + .18
    mesh('Mono-pitch roof', [(-W / 2 - .1, -D / 2 - .15, zt + .02), (W / 2 + .1, -D / 2 - .15, zt + .02), (W / 2 + .1, D / 2 + .1, ridge), (-W / 2 - .1, D / 2 + .1, ridge),
                            (-W / 2 - .1, -D / 2 - .15, zt + .05), (W / 2 + .1, -D / 2 - .15, zt + .05), (W / 2 + .1, D / 2 + .1, ridge + .03), (-W / 2 - .1, D / 2 + .1, ridge + .03)],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 6, 7, 3), (3, 7, 4, 0)], roof, .004)
    # Infill between the level wall top and the mono-pitch roof.
    mesh('Rear roof infill', [(-W / 2, D / 2, zt), (W / 2, D / 2, zt), (W / 2, D / 2, ridge - .03), (-W / 2, D / 2, ridge - .03),
                              (-W / 2, D / 2 - .02, zt), (W / 2, D / 2 - .02, zt), (W / 2, D / 2 - .02, ridge - .03), (-W / 2, D / 2 - .02, ridge - .03)],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 6, 7, 3), (3, 7, 4, 0)], wall)
    for x in (-W / 2, W / 2):
        sgn = 1 if x > 0 else -1
        mesh(f'Side gable infill {x}', [(x, -D / 2, zt), (x, D / 2, zt), (x, D / 2, ridge - .03), (x - sgn * .02, -D / 2, zt), (x - sgn * .02, D / 2, zt), (x - sgn * .02, D / 2, ridge - .03)],
             [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], wall)
    for k in range(10):
        x = -W / 2 + k * W / 9
        rod(f'Roof corrugation {k}', (x, -D / 2 - .15, zt + .055), (x, D / 2 + .1, ridge + .035), .008, roof, 6)
    for x in (-W / 2 + .2, W / 2 - .2):
        box(f'Vent louvre {x}', (x, -D / 2 - .01, H - .1), (.25, .01, .12), trim, .003)
    return dict(id='city-disaster-supply-storage-shed', title='防災備蓄倉庫', titleEn='Disaster supply storage shed',
                description='公園や学校の敷地に置く、鋼製の防災備蓄倉庫です。コンクリートの基礎ブロック、緑の床枠、クリーム色の壁とリブ、前面の引き違い扉と取っ手・上下のレール、無地の掲示板、換気ガラリ、片流れのトタン屋根を造形しています。中の備蓄品、倉庫名や番号などの文字、扉の開閉は含みません。',
                descriptionEn='A steel disaster-supply storage shed for parks and school grounds. It models concrete footing blocks, a green floor frame, cream ribbed walls, front sliding double doors with handles and top and bottom rails, a blank notice plate, ventilation louvres and a mono-pitch corrugated roof. Stored supplies, shed names or numbers and other text, and door motion are not included.',
                tags=['disaster-prevention', 'storage-shed', 'park', 'emergency-supplies', '防災倉庫'], view=(-45, 16))


# ---------------------------------------------------------------- bamboo fence
def bamboo_fence_section():
    bamboo = mat('Weathered green-gold bamboo', (.45, .42, .2), 0, .55)
    post = mat('Charred cedar post', (.12, .08, .05), 0, .7)
    cord = mat('Black palm cord', (.03, .02, .015), 0, .9)
    rnd = random.Random(1063)
    L, H = 1.8, 1.2
    for x in (-L / 2, L / 2):
        cyl(f'Cedar post {x}', (x, 0, H / 2 + .05), .045, H + .1, post, 'Z', 20, .004)
        cyl(f'Post cap {x}', (x, 0, H + .105), .043, .01, post, 'Z', 20, .003)
    # Vertical split-bamboo screen (kenninji style) and three horizontal rails.
    n = 26
    for i in range(n):
        x = -L / 2 + .06 + i * (L - .12) / (n - 1)
        h = H - .04 + rnd.uniform(-.005, .005)
        cyl(f'Vertical bamboo {i}', (x, .0, h / 2 + .02), .028, h, bamboo, 'Z', 12, .002)
        for z in (.35, .75): torus(f'Node ring {i} {z}', (x, 0, z + rnd.uniform(-.03, .03)), .028, .003, bamboo, None, 12, 4)
    for z in (.25, .6, .95):
        for y in (-.035, .035):
            cyl(f'Rail bamboo {z} {y}', (0, y, z), .022, L, bamboo, 'X', 14, .002)
        for i in range(0, n, 3):
            x = -L / 2 + .06 + i * (L - .12) / (n - 1)
            torus(f'Cord tie {z} {i}', (x, 0, z), .04, .004, cord, (0, math.pi / 2, 0), 12, 4)
    cyl('Top cap bamboo', (0, 0, H + .02), .03, L + .06, bamboo, 'X', 14, .002)
    return dict(id='city-bamboo-fence-section', title='竹垣（建仁寺垣風）1区画', titleEn='Bamboo fence section',
                description='住宅の生け垣脇や料亭の前に立つ、建仁寺垣風の竹垣1区画です。焼き杉の柱2本と頭部、縦に並べた竹と節の輪、表裏に渡した3段の押し縁の竹、シュロ縄の結び、上部の笠竹を造形しています。竹は割り竹の断面ではなく丸竹で単純化し、風化の汚れや連続設置用の継ぎ手は含みません。',
                descriptionEn='One section of a kenninji-style bamboo fence for residential frontages and traditional restaurants. It models two charred-cedar posts with caps, vertical bamboo with node rings, three tiers of horizontal bamboo rails on both faces, black palm-cord ties and a top cap bamboo. Bamboo is simplified as round culms rather than split strips; weathering stains and joints for continuous runs are not included.',
                tags=['bamboo-fence', 'japanese-garden', 'fence', 'residential', '竹垣'], view=(-35, 15))


# ---------------------------------------------------------------- block wall
def concrete_block_wall_with_fence():
    block = mat('Grey concrete block', (.55, .55, .53), 0, .85)
    mortar = mat('Recessed mortar joint', (.38, .38, .36), 0, .9)
    cap = mat('Precast coping stone', (.6, .6, .58), 0, .8)
    fence = mat('Bronze aluminium fence', (.18, .14, .1), .6, .4)
    L = 2.4; bw, bh, t = .39, .19, .12; courses = 5
    for c in range(courses):
        off = 0 if c % 2 == 0 else bw / 2
        x = -L / 2 - off
        while x < L / 2 - .001:
            x0 = max(x, -L / 2); x1 = min(x + bw, L / 2)
            if x1 - x0 > .02:
                box(f'Block {c} {x0:.2f}', ((x0 + x1) / 2, 0, c * (bh + .01) + bh / 2 + .01), (x1 - x0 - .01, t, bh), block, .006)
            x += bw + .01
    box('Mortar core', (0, 0, courses * (bh + .01) / 2), (L - .006, t - .02, courses * (bh + .01)), mortar, 0)
    zc = courses * (bh + .01)
    box('Coping', (0, 0, zc + .03), (L + .02, t + .03, .06), cap, .008)
    zf = zc + .06
    for x in (-L / 2 + .05, 0, L / 2 - .05):
        box(f'Fence post {x}', (x, 0, zf + .4), (.04, .04, .8), fence, .004)
    for z in (zf + .05, zf + .75):
        box(f'Fence rail {z}', (0, 0, z), (L - .05, .03, .03), fence, .003)
    n = 30
    for i in range(n):
        x = -L / 2 + .09 + i * (L - .18) / (n - 1)
        box(f'Fence picket {i}', (x, 0, zf + .4), (.018, .018, .68), fence, .002)
    return dict(id='city-concrete-block-wall-with-fence', title='ブロック塀とアルミフェンス', titleEn='Concrete block wall with fence',
                description='住宅の敷地境界に多い、5段のコンクリートブロック塀と上部のアルミ縦格子フェンスです。1段ごとに半個ずらしたブロック、目地、笠木、フェンスの柱・上下の横材・縦格子を造形しています。長さ約2.4mの1区画で、控え壁・鉄筋・基礎の内部、構造的な安全性の検証は含みません。',
                descriptionEn='A five-course concrete block wall topped by an aluminium picket fence, common on residential boundaries. It models half-offset blocks per course, mortar joints, coping, fence posts, top and bottom rails and pickets. One section about 2.4 m long; buttresses, reinforcement, footing internals and structural safety verification are not included.',
                tags=['block-wall', 'fence', 'residential', 'boundary', 'ブロック塀'], view=(-40, 14))


# ---------------------------------------------------------------- gate pillar
def residential_gate_pillar():
    tile = mat('Warm grey stone tile', (.55, .52, .48), 0, .7)
    cap = mat('Dark slate cap', (.15, .15, .16), 0, .6)
    steel = mat('Dark bronze fittings', (.15, .12, .09), .6, .4)
    lamp = mat('Opal porch lamp, lit', (.95, .92, .85), 0, .3, emission=(1, .9, .75), strength=2)
    plate = mat('Blank house name plate', (.75, .72, .66), .2, .5)
    dark = mat('Slot and lens shadow', (.02, .02, .02), .2, .6)
    W, D, H = .5, .3, 1.35
    box('Pillar body', (0, 0, H / 2), (W, D, H), tile, .01)
    for k in range(7):
        box(f'Tile joint {k}', (0, -D / 2 - .0005, .15 + k * .18), (W - .004, .002, .006), dark, 0)
    box('Pillar cap', (0, 0, H + .03), (W + .06, D + .06, .06), cap, .01)
    box('House name plate', (0, -D / 2 - .008, 1.1), (.3, .014, .1), plate, .004)
    box('Mail slot frame', (0, -D / 2 - .008, .82), (.32, .014, .07), steel, .004)
    box('Mail slot flap', (0, -D / 2 - .016, .83), (.28, .004, .035), steel, .002)
    box('Intercom unit', (.12, -D / 2 - .012, .56), (.1, .022, .16), steel, .008)
    cyl('Intercom camera', (.12, -D / 2 - .024, .61), .012, .006, dark, 'Y', 16, .001)
    box('Intercom speaker grille', (.12, -D / 2 - .024, .54), (.05, .002, .03), dark, 0)
    cyl('Intercom call button', (.12, -D / 2 - .024, .49), .014, .006, plate, 'Y', 20, .001)
    box('Lamp bracket', (-.12, -D / 2 - .03, 1.25), (.06, .06, .04), steel, .004)
    box('Porch lamp', (-.12, -D / 2 - .06, 1.18), (.1, .1, .14), lamp, .01)
    box('Lamp cap', (-.12, -D / 2 - .06, 1.26), (.12, .12, .02), steel, .004)
    box('Delivery box', (0, D / 2 + .16, .25), (.45, .3, .5), steel, .015)
    box('Delivery box lid seam', (0, D / 2 + .005, .6), (.4, .004, .004), dark, 0)
    return dict(id='city-residential-gate-pillar', title='住宅の門柱', titleEn='Residential gate pillar',
                description='戸建て住宅の門の脇に立つ、機能門柱です。石調タイル張りの柱と目地、スレートの笠木、無地の表札、郵便受けの投函口とフラップ、カメラ付きインターホン、点灯する門灯、背面の宅配ボックスを造形しています。表札は無地で、住所・氏名・番地などの文字、インターホンの機能、配線は含みません。',
                descriptionEn='A functional gate pillar beside a detached house entrance. It models the stone-tiled pillar with joints, slate cap, a blank house name plate, a mail slot with flap, a camera intercom, a lit porch lamp and a rear parcel delivery box. The name plate is blank: no address, family name or house number; intercom function and wiring are not included.',
                tags=['gate-pillar', 'residential', 'mailbox', 'intercom', '門柱'], view=(-35, 12))


# ---------------------------------------------------------------- accordion gate
def accordion_sliding_gate():
    alu = mat('Champagne aluminium gate', (.62, .57, .48), .8, .35)
    dark = mat('Dark caster rubber', (.04, .04, .04), 0, .7)
    post = mat('Dark grey gate post', (.2, .21, .21), .5, .45)
    n = 12; W = 3.2; H = 1.25; amp = .12
    pts = [(-W / 2 + i * W / n, amp if i % 2 else -amp) for i in range(n + 1)]
    for i in range(n + 1):
        x, y = pts[i]
        box(f'Pantograph vertical {i}', (x, y, H / 2 + .07), (.03, .03, H), alu, .004)
        cyl(f'Caster {i}', (x, y, .035), .03, .025, dark, 'X', 16, .003)
        box(f'Caster fork {i}', (x, y, .065), (.035, .04, .04), alu, .003)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for z0, z1 in ((.2, H - .1), (H - .1, .2), (.2, .65), (.65, .2), (H - .1, .65), (.65, H - .1)):
            bar(f'Lattice bar {i} {z0} {z1}', (x0, y0, z0 + .07), (x1, y1, z1 + .07), .016, .008, alu, .001)
        bar(f'Top rail {i}', (x0, y0, H + .07), (x1, y1, H + .07), .02, .012, alu, .002)
    box('Fixed end post', (-W / 2 - .08, 0, .7), (.1, .1, 1.4), post, .008)
    box('Latch post', (W / 2 + .2, 0, .7), (.1, .1, 1.4), post, .008)
    box('Latch handle', (W / 2 + .03, 0, .85), (.06, .05, .15), alu, .006)
    box('Ground guide rail', (0, 0, .004), (W + .5, .06, .008), post, .002)
    return dict(id='city-accordion-sliding-gate', title='伸縮門扉（アコーディオン門扉）', titleEn='Accordion sliding gate',
                description='住宅や駐車場の入口に使う、アルミ製の伸縮門扉です。ジグザグに開いた縦材13本、菱形に交差する格子の斜材、上部の横材、各縦材の下のキャスター、固定側と受け側の柱、取っ手、地面のガイドを造形しています。部分的に伸ばした状態の静的形状で、伸縮・施錠の動作は含みません。',
                descriptionEn='An aluminium accordion sliding gate for house and car park entrances. It models thirteen zigzag verticals, diagonal lattice bars forming diamonds, top rails, casters under each vertical, a fixed post and a latch post with handle, and a ground guide. It is a static, partly extended shape; extending, folding and locking motion are not included.',
                tags=['gate', 'accordion-gate', 'residential', 'car-park', '伸縮門扉'], view=(-50, 18))


# ---------------------------------------------------------------- extinguisher box
def outdoor_extinguisher_box():
    red = mat('Fire red steel box', (.65, .04, .03), .3, .4)
    window = mat('Clear inspection window', (.75, .82, .85), 0, .05, alpha=.3)
    ext = mat('Extinguisher red cylinder', (.7, .05, .03), .2, .35)
    black = mat('Black hose and handle', (.03, .03, .03), .3, .5)
    lamp = mat('Red indicator lamp, lit', (.9, .05, .03), 0, .2, emission=(1, .1, .05), strength=3)
    post = mat('Galvanized stand', (.5, .52, .52), .75, .4)
    box('Base plate', (0, 0, .01), (.35, .3, .02), post, .004)
    box('Stand post', (0, .05, .3), (.06, .06, .58), post, .004)
    W, D, H, z0 = .3, .25, .65, .58
    # Hollow cabinet: back, sides and floor plates so the stored extinguisher is visible.
    t = .012
    box('Box back plate', (0, D / 2 - t / 2, z0 + H / 2), (W, t, H), red, .003)
    for sx in (-1, 1): box(f'Box side plate {sx}', (sx * (W / 2 - t / 2), 0, z0 + H / 2), (t, D, H), red, .003)
    box('Box floor plate', (0, 0, z0 + t / 2), (W, D, t), red, .003)
    box('Box ceiling plate', (0, 0, z0 + H - t / 2), (W, D, t), red, .003)
    mesh('Pitched lid', [(-W / 2 - .02, -D / 2 - .02, z0 + H), (W / 2 + .02, -D / 2 - .02, z0 + H), (W / 2 + .02, D / 2 + .02, z0 + H), (-W / 2 - .02, D / 2 + .02, z0 + H),
                         (-W / 2 - .02, 0, z0 + H + .07), (W / 2 + .02, 0, z0 + H + .07)],
         [(3, 2, 1, 0), (0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)], red, .004)
    for (xx, zz, sx, sz) in ((0, z0 + .03, W, .06), (0, z0 + H - .05, W, .1), (-W / 2 + .03, z0 + H / 2, .06, H), (W / 2 - .03, z0 + H / 2, .06, H)):
        box(f'Door frame strip {xx} {zz:.2f}', (xx, -D / 2 - .006, zz), (sx, .012, sz), red, .003)
    box('Inspection window', (0, -D / 2 - .013, z0 + H / 2 + .03), (W - .1, .004, H - .22), window, 0)
    lathe('Extinguisher cylinder', [(0, 0), (.075, 0), (.08, .02), (.08, .38), (.06, .44), (.025, .46), (0, .46)], ext, 32).location = (0, .01, z0 + .05)
    box('Extinguisher valve head', (0, .01, z0 + .54), (.05, .05, .05), black, .006)
    box('Carry handle', (.03, .01, z0 + .58), (.1, .02, .015), black, .004)
    tube('Discharge hose', [(.02, .01, z0 + .54), (.08, -.02, z0 + .5), (.09, -.02, z0 + .3)], .009, black, 2, 6)
    box('Door handle', (.11, -D / 2 - .02, z0 + .3), (.02, .02, .08), black, .004)
    cyl('Indicator lamp', (0, 0, z0 + H + .1), .035, .04, lamp, 'Z', 20, .006)
    box('Blank label band', (0, -D / 2 - .013, z0 + .08), (W - .06, .002, .06), mat('Blank white label', (.9, .9, .88), 0, .4), 0)
    return dict(id='city-outdoor-extinguisher-box', title='屋外消火器ボックス', titleEn='Outdoor fire extinguisher box',
                description='商店街や駐車場の歩道脇に立つ、赤い屋外用の消火器格納箱です。亜鉛めっきのスタンドと台板、切妻のふた、点検窓付きの扉と取っ手、中の消火器と弁・取っ手・ホース、頂部の赤色表示灯（発光材質）、無地のラベル帯を造形しています。「消火器」などの文字・図記号、扉の開閉、消火器としての性能は含みません。',
                descriptionEn='A red outdoor fire-extinguisher box on a stand for shopping streets and car parks. It models the galvanized stand and base plate, a gabled lid, a door with inspection window and handle, the extinguisher inside with valve head, handle and hose, a lit red indicator lamp on top and a blank label band. Text such as "fire extinguisher" and symbols, door motion and extinguisher performance are not included.',
                tags=['fire-safety', 'extinguisher', 'street-furniture', 'emergency', '消火器'], view=(-40, 14),
                transparentNote=('点検窓はGLB内の半透明（アルファブレンド）材質です。', 'The inspection window uses an alpha-blended GLB material.'))


BUILDERS = {
    'city-bicycle-parking-pay-station': bicycle_parking_pay_station,
    'city-car-park-pay-station': car_park_pay_station,
    'city-height-limit-gantry': height_limit_gantry,
    'city-disaster-warning-speaker-pole': disaster_warning_speaker_pole,
    'city-disaster-supply-storage-shed': disaster_supply_storage_shed,
    'city-bamboo-fence-section': bamboo_fence_section,
    'city-concrete-block-wall-with-fence': concrete_block_wall_with_fence,
    'city-residential-gate-pillar': residential_gate_pillar,
    'city-accordion-sliding-gate': accordion_sliding_gate,
    'city-outdoor-extinguisher-box': outdoor_extinguisher_box,
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
