"""Original roadside street objects authored by Claude, CC BY 4.0.

No third-party meshes, textures, brand identities, lettering or font files.
Usage: python scripts/city_expansion/frozen/batch-059/scripts/city_expansion/claude_roadside_objects.py --out DIR [--only ID ...]
(run with a Blender 4.5 `bpy` module or `blender -b --python ... --`).
"""
import sys, math, argparse
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

GENERATOR = Path(__file__).resolve().relative_to(ROOT).as_posix()


def sweep(name, profile, path, material=None, closed_profile=True, smooth=False, strip_caps=False):
    """Sweep a closed (u, v) profile along a polyline in the XY plane.
    u is measured along the path's left normal and v along Z."""
    pts = [Vector(p) for p in path]; rings = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a); t.z = 0; t.normalize(); nrm = Vector((-t.y, t.x, 0))
        rings.append([p + nrm * u + Vector((0, 0, v)) for u, v in profile])
    n = len(profile); verts = [tuple(v) for r in rings for v in r]; faces = []
    for i in range(len(rings) - 1):
        for j in range(n if closed_profile else n - 1):
            k = (j + 1) % n
            faces.append((i * n + j, i * n + k, (i + 1) * n + k, (i + 1) * n + j))
    if closed_profile and strip_caps:
        # Profile is front + reversed(back): close ends with quad strips across
        # the thickness, avoiding long thin n-gon fans and zero-area triangles.
        last = (len(rings) - 1) * n
        for j in range(n // 2 - 1):
            a, b, c, d = j, j + 1, n - 2 - j, n - 1 - j
            faces.append((d, c, b, a)); faces.append((last + a, last + b, last + c, last + d))
    elif closed_profile:
        faces.append(tuple(reversed(range(n))))
        last = (len(rings) - 1) * n; faces.append(tuple(range(last, last + n)))
    return mesh(name, verts, faces, material, 0, smooth)


# ---------------------------------------------------------------- utility pole
def concrete_utility_pole():
    concrete = mat('Spun concrete, light grey', (.50, .50, .48), 0, .82)
    steel = mat('Galvanized steel hardware', (.42, .45, .46), .78, .42)
    porcelain = mat('Glazed white porcelain', (.86, .86, .83), 0, .18)
    can = mat('Transformer grey paint', (.47, .52, .53), .35, .45)
    yellow = mat('Safety yellow sleeve', (.80, .58, .02), 0, .55)
    black = mat('Safety black sleeve', (.02, .02, .02), 0, .6)
    plate = mat('Blank enamel plate', (.80, .82, .80), .1, .35)
    cable = mat('Black insulated lead', (.012, .013, .014), 0, .55)
    H = 10.0; r0 = .175; r1 = .095
    prof = [(0, 0), (r0, 0)] + [(r0 + (r1 - r0) * z / H, z) for z in (0.5, 2, 4, 6, 8, H - .04)] + [(r1 - .015, H), (0, H + .01)]
    lathe('Tapered spun-concrete pole', prof, concrete, 40)
    radius = lambda z: r0 + (r1 - r0) * z / H
    # Base protective sleeve with alternating bands, slightly proud of the pole.
    for i in range(9):
        z0 = .05 + i * .2; m = yellow if i % 2 == 0 else black
        cyl(f'Protective sleeve band {i + 1}', (0, 0, z0 + .1), radius(z0) + .006, .2, m, verts=40, bevel=0)
    box('Blank pole identification plate', (0, -radius(2.4) - .006, 2.4), (.11, .012, .26), plate, .003)
    # Climbing step bolts, alternating sides, from 2.0 m upward.
    for i, z in enumerate([2.0 + .45 * k for k in range(15)]):
        ang = math.pi / 2 * (i % 4) + math.pi / 4
        d = Vector((math.cos(ang), math.sin(ang), 0)); r = radius(z)
        rod(f'Step bolt {i + 1}', d * (r - .02) + Vector((0, 0, z)), d * (r + .21) + Vector((0, 0, z)), .011, steel, 12)
        cyl(f'Step bolt nut {i + 1}', d * (r + .21) + Vector((0, 0, z)), .016, .024, steel, verts=6, bevel=.001).rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    # Two crossarms with braces and pin insulators.
    for k, (z, span) in enumerate([(9.55, 1.8), (8.85, 1.5)]):
        r = radius(z)
        box(f'Crossarm {k + 1}', (0, -r - .05, z), (span, .075, .075), steel, .004)
        for s in (-1, 1):
            bar(f'Crossarm {k + 1} brace {s}', (s * span * .36, -r - .05, z - .03), (0, -r - .01, z - .5), .04, .006, steel)
        cyl(f'Crossarm {k + 1} pole band', (0, 0, z), r + .012, .09, steel, verts=40, bevel=.002)
        cyl(f'Crossarm {k + 1} lower band', (0, 0, z - .5), radius(z - .5) + .012, .07, steel, verts=40, bevel=.002)
        for j, x in enumerate((-span / 2 + .12, -span / 6, span / 2 - .12)):
            cyl(f'Insulator pin {k + 1}.{j + 1}', (x, -r - .05, z + .07), .012, .08, steel, verts=12, bevel=0)
            ins = lathe(f'Pin insulator {k + 1}.{j + 1}', [(0, 0), (.035, 0), (.05, .02), (.075, .04), (.07, .06), (.05, .07), (.065, .09), (.06, .11), (.045, .13), (.04, .15), (0, .155)], porcelain, 32)
            ins.location = (x, -r - .05, z + .1)
    # Pole-mounted transformer on a hanger bracket.
    zt = 7.1; rt = radius(zt); tx, ty = 0, -rt - .34
    box('Transformer hanger plate', (0, -rt - .07, zt + .2), (.22, .04, .9), steel, .004)
    for dz in (-.15, .55):
        cyl(f'Transformer pole band {dz}', (0, 0, zt + dz), radius(zt + dz) + .012, .07, steel, verts=40, bevel=.002)
        box(f'Transformer bracket arm {dz}', (0, -rt - .17, zt + dz), (.1, .2, .05), steel, .003)
    lathe('Transformer tank', [(0, 0), (.21, 0), (.235, .02), (.235, .78), (.245, .8), (.245, .84), (.2, .9), (0, .92)], can, 48).location = (tx, ty, zt - .4)
    for i, zz in enumerate((-.2, .0, .2)):
        box(f'Transformer cooling rib {i + 1}', (tx, ty - .24, zt + zz), (.18, .03, .14), can, .004)
    for j, x in enumerate((-.12, .0, .12)):
        b = lathe(f'Transformer bushing {j + 1}', [(0, 0), (.03, 0), (.045, .03), (.03, .05), (.042, .08), (.028, .1), (.036, .13), (.02, .16), (0, .165)], porcelain, 24)
        b.location = (tx + x, ty + .02, zt + .52)
        smooth_tube(f'Bushing lead {j + 1}', [(tx + x, ty + .02, zt + .69), (tx + x * 1.8, ty + .05, zt + 1.0), (x * 4.5, -radius(8.85) - .05, 8.85 + .25)], .009, cable)
    cyl('Pole top cap', (0, 0, H + .03), r1 - .01, .05, concrete, verts=40, bevel=.006)
    return dict(id='city-concrete-utility-pole', title='コンクリート電柱', titleEn='Concrete utility pole',
                description='住宅地の道路脇に立つ、高さ約10mの配電用コンクリート柱です。テーパー付きの円柱、根元の黄色と黒の保護カバー（帯状の段差で表現）、無地の識別プレート、交互に突き出た足場ボルト、腕金2段と支持材、ピン碍子6個、柱上変圧器と吊り金具、ブッシングから腕金へ向かう短い引下げ線を造形しています。架空電線・通信線・支線・ステー、文字や記号、地中部分は含みません。',
                descriptionEn='A roughly 10 m spun-concrete distribution pole for residential roadsides. It models the tapered shaft, a yellow-and-black protective base sleeve represented as stepped bands, a blank identification plate, alternating climbing step bolts, two crossarms with braces, six pin insulators, a pole-mounted transformer with its hanger hardware, and short drop leads from the bushings toward the crossarm. Overhead power and telecom lines, guy wires, lettering, markings and the buried section are omitted.',
                tags=['utility-pole', 'power-distribution', 'transformer', 'insulator', '電柱'], view=(-60, 12))


# ---------------------------------------------------------------- guardrail
def w_beam_guardrail():
    white = mat('White painted steel', (.80, .81, .79), .25, .38)
    galv = mat('Galvanized post steel', (.48, .50, .50), .7, .45)
    dark = mat('Dark bolt steel', (.10, .10, .10), .6, .5)
    amber = mat('Amber retroreflector', (.85, .42, .03), 0, .2)
    H = .31; D = .083; T = .004; zc = .6
    n = 40; front = []
    for i in range(n + 1):
        t = -1 + 2 * i / n
        u = -D / 2 * (1 - math.cos(2 * math.pi * t)); du = -D / 2 * 2 * math.pi * math.sin(2 * math.pi * t) / (H / 2)
        k = math.hypot(du, 1)
        # Offset the rear face along the true section normal for uniform 4 mm steel.
        front.append(((u, H / 2 * t), (u + T / k, H / 2 * t - T * du / k)))
    # profile in (u, v): u is offset to the left of travel (+Y when travelling +X)
    prof = [(a[0], a[1] + zc) for a, b in front] + [(b[0], b[1] + zc) for a, b in reversed(front)]
    L = 4.0
    sweep('W-beam rail', prof, [(-L / 2, 0, 0), (L / 2, 0, 0)], white, strip_caps=True)
    # Flared terminal sections curving back toward the posts at both ends.
    for s in (-1, 1):
        path = []
        for k in range(13):
            a = k / 12 * math.radians(55); R = .55
            x = s * (L / 2 + R * math.sin(a)); y = R * (1 - math.cos(a))
            path.append((x, y, 0))
        if s < 0: path = list(reversed(path))
        sweep(f'Flared end terminal {"left" if s < 0 else "right"}', prof, path, white, strip_caps=True)
    posts = (-1.85, 0.0, 1.85)
    for i, x in enumerate(posts):
        cyl(f'Round post {i + 1}', (x, .17, .385), .057, .77, galv, verts=32, bevel=.002)
        cyl(f'Post cap {i + 1}', (x, .17, .775), .06, .012, galv, verts=32, bevel=.003)
        box(f'Bracket {i + 1}', (x, .07, zc), (.09, .12, .2), galv, .004)
        for dz in (-.05, .05):
            cyl(f'Beam bolt head {i + 1}{dz}', (x, -T / 2 - .002, zc + dz), .014, .008, dark, 'Y', 16, .002)
            cyl(f'Post through bolt {i + 1}{dz}', (x, .17, zc + dz), .009, .16, dark, 'Y', 12, 0)
    cyl('Round delineator reflector', (0, .17 - .058, .74), .035, .006, amber, 'Y', 32, .001)
    for x in (-L / 2 + .06, L / 2 - .06):
        for dz in (-.1, -.04, .04, .1):
            cyl(f'Splice bolt {x}{dz}', (x, -T / 2 - .002, zc + dz), .011, .007, dark, 'Y', 16, .0015)
    return dict(id='city-w-beam-guardrail', title='ガードレール（W形ビーム）', titleEn='W-beam guardrail section',
                description='道路の路肩に設置する白色塗装のW形ビーム防護柵です。4mのビームと両端の巻込み端部、丸パイプ支柱3本とキャップ、支柱ブラケット、ビームの締結ボルト頭、支柱上の丸形反射板を造形しています。連続設置用の継手部品、地中部分、道路標示や汚れは含みません。',
                descriptionEn='A white-painted W-beam roadside guardrail. It models a 4 m two-wave beam with flared terminal ends curving back at both sides, three round galvanized posts with caps and brackets, beam fastening bolt heads and a round delineator reflector on the center post. Continuation splices, buried post sections, road markings and weathering are omitted.',
                tags=['guardrail', 'w-beam', 'roadside-safety', 'barrier', 'ガードレール'], view=(-62, 18))


# ---------------------------------------------------------------- U barrier
def u_shaped_steel_barrier():
    steel = mat('Hot-dip galvanized pipe', (.55, .57, .57), .78, .36)
    yellow = mat('Yellow reflective band', (.86, .62, .02), .05, .35)
    base = mat('Galvanized base plate', (.42, .44, .44), .7, .5)
    dark = mat('Anchor bolt steel', (.12, .12, .12), .6, .5)
    W = 1.0; Hh = .8; r = .0303; R = .16
    pts = [(-W / 2, 0, .012)]
    pts.append((-W / 2, 0, Hh - R))
    for k in range(1, 12):
        a = math.pi / 2 * k / 12
        pts.append((-W / 2 + R - R * math.cos(a), 0, Hh - R + R * math.sin(a)))
    pts.append((-W / 2 + R, 0, Hh)); pts.append((W / 2 - R, 0, Hh))
    for k in range(1, 12):
        a = math.pi / 2 * k / 12
        pts.append((W / 2 - R + R * math.sin(a), 0, Hh - R + R * math.cos(a)))
    pts.append((W / 2, 0, Hh - R)); pts.append((W / 2, 0, .012))
    tube('U-shaped barrier pipe', pts, r, steel, 4, 2)
    for s in (-1, 1):
        x = s * W / 2
        for z0 in (.52, .62):
            cyl(f'Reflective band {s} {z0}', (x, 0, z0), r + .002, .06, yellow, verts=32, bevel=0)
        box(f'Base plate {s}', (x, 0, .006), (.2, .2, .012), base, .004)
        cyl(f'Base collar {s}', (x, 0, .04), r + .008, .07, base, verts=32, bevel=.002)
        for dx in (-.07, .07):
            for dy in (-.07, .07):
                bolt(f'Anchor nut {s}{dx}{dy}', (x + dx, dy, .017), .012, .01, dark)
    cyl('Center reflective band', (0, 0, Hh), r + .002, .12, yellow, 'X', 32, 0)
    return dict(id='city-u-shaped-steel-barrier', title='U字型車止め', titleEn='U-shaped steel barrier',
                description='歩道の入口や駐輪場に置く、溶融亜鉛めっき鋼管のU字型車止めです。曲げ加工したパイプ、黄色の反射帯、根元のカラーと表面設置用ベースプレート、アンカーナットを造形しています。チェーン、鍵付き脱着機構、埋設基礎は含みません。',
                descriptionEn='A galvanized steel-pipe U-shaped barrier for sidewalk entrances and bicycle parking. It models the bent pipe, yellow reflective bands, base collars, surface-mount base plates and anchor nuts. Chains, lockable removable sockets and buried foundations are not included.',
                tags=['bollard', 'vehicle-barrier', 'pipe-barrier', '車止め'], view=(-50, 20))


# ---------------------------------------------------------------- bus stop pole
def bus_stop_pole():
    concrete = mat('Cast concrete base', (.46, .46, .44), 0, .85)
    pole = mat('Pale grey powder coat', (.62, .64, .64), .3, .4)
    face = mat('Blank sign face white', (.86, .87, .86), 0, .35)
    rim = mat('Sign rim blue', (.05, .16, .42), .2, .4)
    panel = mat('Timetable panel off-white', (.78, .78, .74), 0, .6)
    glass = mat('Clear polycarbonate cover', (.75, .82, .85), 0, .05, alpha=.25)
    dark = mat('Black rubber and fixings', (.02, .02, .02), 0, .6)
    lathe('Weighted round base', [(0, 0), (.28, 0), (.285, .01), (.285, .1), (.27, .12), (.12, .14), (.06, .15), (0, .15)], concrete, 48)
    cyl('Rubber foot ring', (0, 0, .004), .286, .008, dark, verts=48, bevel=0)
    cyl('Sign pole', (0, 0, 1.33), .03, 2.4, pole, verts=32, bevel=.002)
    cyl('Pole cap', (0, 0, 2.55), .034, .03, dark, verts=32, bevel=.006)
    # Double-sided round flag sign, blank face, blue rim.
    cyl('Round flag sign disk', (0, 0, 2.18), .25, .012, face, 'Y', 64, .001)
    torus('Round flag sign rim', (0, 0, 2.18), .25, .012, rim, (math.pi / 2, 0, 0), 64)
    for z in (2.0, 2.36):
        cyl(f'Sign clamp {z}', (0, 0, z), .036, .04, dark, verts=24, bevel=.002)
    # Timetable case with transparent cover.
    box('Timetable case back', (0, -.05, 1.25), (.44, .05, .62), pole, .006)
    box('Blank timetable panel', (0, -.077, 1.25), (.40, .004, .56), panel, 0)
    box('Clear timetable cover', (0, -.083, 1.25), (.41, .006, .57), glass, .002)
    for z in (1.02, 1.48):
        box(f'Case mounting bracket {z}', (0, -.015, z), (.1, .04, .04), pole, .003)
    return dict(id='city-bus-stop-pole', title='バス停標識', titleEn='Bus stop pole',
                description='重量コンクリートの丸い台座に立つ、移動可能なバス停標識です。灰色の支柱と頭部キャップ、両面の丸い標識板と青い縁、取付金具、透明カバー付きの時刻表ケースを造形しています。停留所名・路線番号・時刻表・事業者名などの文字や図記号は含まず、無地の面として残しています。',
                descriptionEn='A movable bus stop pole on a weighted round concrete base. It models the grey pole and cap, a double-sided round flag sign with a blue rim, clamps, and a timetable case with a clear cover. Stop names, route numbers, timetables, operator branding, lettering and symbols are intentionally absent; sign faces and the timetable panel are blank.',
                tags=['bus-stop', 'transit', 'sign-post', 'バス停'], view=(-58, 16),
                transparentNote=('時刻表カバーはGLB内の半透明（アルファブレンド）材質です。', 'The timetable cover uses an alpha-blended GLB material.'))


# ---------------------------------------------------------------- A-frame sign
def a_frame_sidewalk_sign():
    wood = mat('Oiled oak frame', (.38, .22, .10), 0, .55)
    board = mat('Matte black chalkboard', (.03, .035, .033), 0, .9)
    metal = mat('Black steel hinge', (.05, .05, .05), .7, .45)
    chain = mat('Zinc spreader chain', (.5, .52, .52), .8, .35)
    W = .6; Hh = .95; spread = .32; t = .022
    ang = math.atan2(spread / 2, Hh)
    for s, side in ((-1, 'front'), (1, 'back')):
        rot = (s * ang, 0, 0); cy = s * spread / 4; cz = Hh / 2
        for x in (-W / 2 + .02, W / 2 - .02):
            o = box(f'{side} frame stile {x}', (x, cy, cz), (.04, t, Hh / math.cos(ang)), wood, .004); o.rotation_euler = rot
        for z in (.06, Hh - .05):
            zz = z; yy = s * (Hh - z) * math.tan(ang) * 0 + s * (spread / 2) * (1 - z / Hh)
            o = box(f'{side} frame rail {z}', (0, yy, zz), (W - .08, t, .05), wood, .004); o.rotation_euler = rot
        o = box(f'{side} chalkboard', (0, s * (spread / 2) * (1 - .5), Hh / 2 + .005), (W - .08, .008, Hh - .16), board, 0); o.rotation_euler = rot
    for x in (-W / 2 + .04, W / 2 - .04):
        cyl(f'Top hinge {x}', (x, 0, Hh - .005), .012, .05, metal, 'X', 16, .001)
    for s in (-1, 1):
        x = s * (W / 2 - .02)
        tube(f'Spreader chain {s}', [(x, -spread * .3, .32), (x, 0, .29), (x, spread * .3, .32)], .004, chain, 2, 4)
        for sy in (-1, 1):
            box(f'Rubber foot {s}{sy}', (x, sy * spread / 2, .006), (.045, .03, .012), metal, .003)
    return dict(id='city-a-frame-sidewalk-sign', title='A型スタンド黒板看板', titleEn='A-frame sidewalk chalkboard sign',
                description='店先の歩道に置く折りたたみ式のA型スタンド看板です。オーク調の木枠、両面の黒板パネル、上部の蝶番、開き止めのチェーン、ゴム足を造形しています。黒板は無地で、文字・メニュー・ロゴは含みません。開閉動作は付属しません。',
                descriptionEn='A folding A-frame sidewalk sign for shopfronts. It models an oak-toned frame, chalkboard panels on both faces, top hinges, spreader chains and rubber feet. Both boards are blank, without lettering, menus or logos; the folding motion is not rigged.',
                tags=['sidewalk-sign', 'a-frame', 'chalkboard', 'shopfront', '立て看板'], view=(-35, 18))


# ---------------------------------------------------------------- delineator
def lane_delineator_post():
    orange = mat('Orange polyurethane', (.85, .25, .02), 0, .5)
    white = mat('White reflective sheeting', (.86, .87, .85), 0, .25)
    base = mat('Black rubber base', (.025, .025, .025), 0, .75)
    steel = mat('Anchor bolt steel', (.35, .36, .36), .7, .45)
    lathe('Delineator base', [(0, 0), (.1, 0), (.103, .008), (.1, .03), (.06, .045), (.048, .05), (0, .05)], base, 48)
    lathe('Flexible delineator post', [(0, .04), (.043, .04), (.04, .1), (.04, .74), (.036, .78), (.025, .795), (0, .8)], orange, 40)
    for z in (.62, .7):
        cyl(f'Reflective band {z}', (0, 0, z), .0415, .05, white, verts=40, bevel=0)
    for k in range(3):
        a = k * math.tau / 3 + .3
        bolt(f'Base anchor bolt {k + 1}', (.075 * math.cos(a), .075 * math.sin(a), .03), .011, .01, steel)
    return dict(id='city-lane-delineator-post', title='ラバーポール（視線誘導標）', titleEn='Lane delineator post',
                description='車線の分離や右左折誘導に使う、オレンジ色の可とう性ラバーポールです。円形のゴム基部とアンカーボルト、上部の白い反射帯2本を造形しています。倒れて戻る弾性挙動、地中アンカー、路面標示は含みません。',
                descriptionEn='A flexible orange lane delineator post used to separate lanes and guide turns. It models the round rubber base with anchor bolts and two white reflective bands near the top. Flexing behavior, buried anchors and road markings are not included.',
                tags=['delineator', 'traffic-safety', 'lane-separator', 'ラバーポール'], view=(-50, 18))


# ---------------------------------------------------------------- controller cabinet
def traffic_control_cabinet():
    grey = mat('Pale grey cabinet paint', (.62, .65, .63), .3, .45)
    plinth = mat('Concrete plinth', (.45, .45, .43), 0, .85)
    dark = mat('Louvre shadow', (.06, .07, .07), .2, .6)
    steel = mat('Stainless handle', (.6, .62, .62), .85, .3)
    W, D, Hh = .66, .44, 1.28
    box('Concrete plinth', (0, 0, .09), (W + .16, D + .16, .18), plinth, .02)
    z0 = .18
    box('Cabinet body', (0, 0, z0 + Hh / 2), (W, D, Hh), grey, .008)
    prism('Rain hood', [(-W / 2 - .03, -D / 2 - .05), (W / 2 + .03, -D / 2 - .05), (W / 2 + .03, D / 2 + .03), (-W / 2 - .03, D / 2 + .03)], z0 + Hh, z0 + Hh + .025, grey, .004)
    mesh('Hood slope', [(-W / 2 - .03, -D / 2 - .05, z0 + Hh + .025), (W / 2 + .03, -D / 2 - .05, z0 + Hh + .025), (W / 2 + .03, D / 2 + .03, z0 + Hh + .06), (-W / 2 - .03, D / 2 + .03, z0 + Hh + .06),
                         (-W / 2 - .03, -D / 2 - .05, z0 + Hh + .025), (W / 2 + .03, D / 2 + .03, z0 + Hh + .025), (-W / 2 - .03, D / 2 + .03, z0 + Hh + .025)],
         [(0, 1, 2, 3), (1, 5, 2), (0, 3, 6), (3, 2, 5, 6)], grey)
    # Front door seam and panel, hinges and handle.
    box('Door seam shadow', (0, -D / 2 - .0005, z0 + Hh / 2), (W - .05, .002, Hh - .06), dark, 0)
    box('Front door panel', (0, -D / 2 - .004, z0 + Hh / 2), (W - .06, .008, Hh - .07), grey, .004)
    for z in (z0 + .2, z0 + Hh - .2):
        cyl(f'Door hinge {z}', (-W / 2 + .045, -D / 2 - .012, z), .01, .09, grey, verts=16, bevel=.001)
    box('Handle base', (W / 2 - .07, -D / 2 - .012, z0 + Hh * .55), (.035, .012, .14), steel, .004)
    box('Lever handle', (W / 2 - .07, -D / 2 - .03, z0 + Hh * .55 - .04), (.025, .025, .1), steel, .006)
    cyl('Key cylinder', (W / 2 - .07, -D / 2 - .02, z0 + Hh * .55 + .05), .009, .012, steel, 'Y', 16, .001)
    # Side louvres.
    for s in (-1, 1):
        for i in range(8):
            z = z0 + .25 + i * .035
            o = box(f'Side louvre {s} {i}', (s * (W / 2 + .008), 0, z), (.012, D * .6, .016), dark if i % 2 else grey, .002)
            o.rotation_euler = (0, s * .5, 0)
    box('Blank inspection label', (-.12, -D / 2 - .009, z0 + Hh - .14), (.16, .002, .07), mat('Blank label white', (.85, .85, .82), 0, .4), 0)
    return dict(id='city-traffic-control-cabinet', title='信号制御機キャビネット', titleEn='Traffic signal controller cabinet',
                description='交差点の歩道脇に置かれる信号制御機の屋外キャビネットです。コンクリート台座、淡灰色の筐体と傾斜付き雨よけ屋根、前扉の継ぎ目と蝶番、レバーハンドルと鍵穴、側面のガラリ、無地の点検ラベルを造形しています。内部機器、配線、文字や管理番号は含みません。',
                descriptionEn='An outdoor traffic signal controller cabinet for intersection sidewalks. It models the concrete plinth, pale grey enclosure with a sloped rain hood, front door seam and hinges, lever handle and key cylinder, side louvres and a blank inspection label. Internal equipment, wiring, lettering and asset numbers are omitted.',
                tags=['traffic-signal', 'controller-cabinet', 'utility-cabinet', '信号制御機'], view=(-52, 20))


# ---------------------------------------------------------------- no-entry sign
def no_entry_sign_post():
    pole = mat('Galvanized sign pole', (.55, .57, .57), .75, .38)
    red = mat('Red retroreflective sheeting', (.62, .03, .03), 0, .3)
    white = mat('White retroreflective sheeting', (.86, .87, .85), 0, .3)
    back = mat('Aluminium sign back', (.55, .56, .57), .6, .45)
    dark = mat('Clamp steel', (.25, .26, .26), .6, .45)
    cyl('Sign pole', (0, 0, 1.6), .0303, 3.2, pole, verts=32, bevel=.002)
    cyl('Pole cap', (0, 0, 3.21), .033, .02, dark, verts=32, bevel=.006)
    Z = 2.75; R = .3
    cyl('Sign blank aluminium disk', (0, -.045, Z), R, .004, back, 'Y', 72, .0005)
    cyl('Red sign face', (0, -.0485, Z), R - .004, .003, red, 'Y', 72, 0)
    box('White horizontal bar', (0, -.0505, Z), (.42, .002, .09), white, 0)
    torus('Rolled sign rim', (0, -.045, Z), R, .004, back, (math.pi / 2, 0, 0), 72, 8)
    for z in (Z - .16, Z + .16):
        box(f'Sign back channel {z}', (0, -.036, z), (.26, .014, .03), back, .002)
        torus(f'Pole clamp band {z}', (0, 0, z), .034, .006, dark, None, 32, 8)
        box(f'Clamp bolt block {z}', (0, -.03, z), (.05, .02, .025), dark, .003)
    return dict(id='city-no-entry-sign-post', title='車両進入禁止標識', titleEn='No-entry road sign post',
                description='道路の入口に立つ、車両進入禁止を示す丸い規制標識と支柱です。赤い反射面に白い横棒、アルミ板の巻き縁と裏面補強材、支柱への締付けバンドとボルト、頭部キャップを造形しています。補助標識・文字・規制時間の表示、地中基礎は含みません。',
                descriptionEn='A round no-entry regulatory road sign on a galvanized pole. It models the red retroreflective face with a white horizontal bar, rolled aluminium rim, rear stiffening channels, pole clamp bands and bolt blocks, and a pole cap. Supplementary plates, lettering, time restrictions and the buried foundation are not included.',
                tags=['road-sign', 'regulatory-sign', 'no-entry', 'sign-post', '道路標識'], view=(-40, 14))


BUILDERS = {
    'city-concrete-utility-pole': concrete_utility_pole,
    'city-w-beam-guardrail': w_beam_guardrail,
    'city-u-shaped-steel-barrier': u_shaped_steel_barrier,
    'city-bus-stop-pole': bus_stop_pole,
    'city-a-frame-sidewalk-sign': a_frame_sidewalk_sign,
    'city-lane-delineator-post': lane_delineator_post,
    'city-traffic-control-cabinet': traffic_control_cabinet,
    'city-no-entry-sign-post': no_entry_sign_post,
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
