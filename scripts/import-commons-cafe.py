"""Extract original reusable meshes from Xenoah's pinned cafe Blender scene.

Python 3.11 + bpy 4.5.14. Never executes the upstream build script or blend scripts.
Run with --source-root <checkout>, or --fetch to obtain the SHA-256-pinned inputs.
Outputs a validated _inbox collection. Existing IDs are never overwritten.
"""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, math, struct, urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'Xenoah/vrcworld_tech-tech-cafe'
COMMIT = '784e040a866c0081d6641c03cbf7f23d48a59dc2'
SOURCE_URL = f'https://github.com/{REPO}/tree/{COMMIT}'
DATE = '2026-10-14'
INPUTS = {
    'Blender/The_Commons_Compact.blend': 'bae03d811a95dc7b9b91805b90c5109eac8ae08ed3dbf31e1a83afeb1beed778',
    'Blender/build_world.py': 'a9246207facef7f2728df7511ab0c1e81bfe5f3cc94a2048022551a1edf62d7b',
    'Documentation/texture_provenance.json': '143ddf6b50f2d29c7a7b1934f2c87ed979297c1efdeaacc109edd387746493cd',
    'Unity/Assets/TheCommons/Textures/bar_labels_albedo.png': '6a0d1ffe7da88a68f3e8cd0f9b126bef3b3201f3acbc44f05a713b8e842c1da8',
    'Unity/Assets/TheCommons/Textures/basalt_terrazzo_albedo.png': 'a7eebda5bbb2404426a9a4a60e3b9434e30274167d7641a3338f426770bded54',
    'Unity/Assets/TheCommons/Textures/mineral_plaster_albedo.png': '2d835bd37e136fec4cd64709fef9173f554707ea2c28607693018b8cdcc4c1f3',
    'Unity/Assets/TheCommons/Textures/blackened_steel_albedo.png': 'ccb94abc7aeabb72a9398d67a0f6904b1fff755c987ddce7f9d2800172d61b1e',
    'Unity/Assets/TheCommons/Textures/cafe_props_albedo.png': 'bc3f26f6ec15b16436345e5cef34bbf245d22b7d2bcd90fa6fb033177cd99313',
    'Unity/Assets/TheCommons/Textures/relay_controller_albedo.png': 'c3209959d4d66776dc51f78d7b321a0b9359edc313057ac858cc251b4a9c03c6',
    'Unity/Assets/TheCommons/Textures/satin_brass_albedo.png': '03ac661503ff10aff54d0e881620a714a25aba843293c0580f7a945af9a4269c',
    'Unity/Assets/TheCommons/Textures/teal_woven_albedo.png': '9ccf88a755b0ecc9c44e6a44c51b460135395300d59f68e91353471a42d627cd',
    'Unity/Assets/TheCommons/Textures/warm_oak_albedo.png': 'cc38376743e54a2f0c72be72ee0c2e699a62d3de15d67c621277ecb38111c36d',
}


def asset(slug, title, english, category, collection, center, radius, names, count, description, en, rotation=0, z_range=None, xy_bounds=None):
    return dict(id='commons-'+slug, title=title, titleEn=english, category=category,
                collection=collection, center=center, radius=radius, names=names.split(),
                expected=count, description=description, descriptionEn=en, rotation=rotation,
                z_range=z_range, xy_bounds=xy_bounds)


ASSETS = [
    asset('bar-stool', 'コモンズ・バースツール', 'Commons bar stool', 'furniture', 'FURN_Bar', [2.9, 7], .35,
          'FURN_StoolBase FURN_StoolStem FURN_StoolFootrest FURN_StoolSeat', 4,
          '青緑の布張り座面、真鍮の支柱と足掛けを持つバースツール。元ワールドの1脚を独立化。',
          'A teal upholstered bar stool with a brass stem and footrest, extracted as one standalone seat.'),
    asset('lounge-chair', 'コモンズ・ラウンジチェア', 'Commons lounge chair', 'furniture', 'FURN_Cafe', [1.15, 2.4], .48,
          'FURN_SeatCushion FURN_BackCushion FURN_SeatLeg', 6,
          '面取りされた布張りクッションと真鍮の4本脚。カフェやラウンジの椅子に。',
          'Beveled upholstery and four brass legs for a cafe or lounge.', -math.pi/2),
    asset('lounge-sofa', 'コモンズ・ラウンジソファ', 'Commons lounge sofa', 'furniture', 'MODE_Lounge', [10.1, 4.55], .9,
          'FURN_SeatCushion FURN_BackCushion FURN_SeatLeg FURN_SofaArm', 8,
          '青緑の布張りと細い真鍮脚を使った2人掛けソファ。座面・背面・肘掛けを別メッシュで保持。',
          'A compact teal two-seat sofa with separate seat, back, arms and slender brass legs.', -math.pi),
    asset('round-table', 'コモンズ・カフェ丸テーブル', 'Commons round cafe table', 'furniture', 'FURN_Cafe', [2, 2.4], .12,
          'FURN_TableTop FURN_TableTrim FURN_TableBase FURN_TableStem', 4,
          'オークの天板、真鍮の縁、スチールの一本脚。卓上の小物を除いた独立テーブル。',
          'An oak top, brass edge and steel pedestal; supplied without tabletop props.'),
    asset('pendant-light', 'コモンズ・ペンダントライト', 'Commons pendant light', 'props', 'FURN_Bar', [3.6, 7.5], .1,
          'LGT_PendantDrop LGT_Shade LGT_Diffuser', 3,
          '黒皮鋼のシェードと暖色の発光面を持つ吊り下げ照明。発光材質付きの装飾モデル。',
          'A blackened-steel shade, suspension and warm emissive diffuser. Decorative geometry, no runtime light.'),
    asset('coffee-cup', 'コモンズ・コーヒーカップ', 'Commons coffee cup', 'props', 'FURN_Cafe', [1.88, 2.46], .04,
          'FURN_CoffeeCup FURN_Coffee FURN_Saucer', 3,
          '陶器色のカップ、コーヒー面、リング状の受け皿。カフェの卓上に置ける軽量な小物。',
          'A ceramic-colored cup, coffee surface and ring-shaped saucer. A lightweight cafe prop.'),
    asset('leaf-planter', 'コモンズ・観葉植物', 'Commons leafy planter', 'props', 'FURN_Cafe', [.85, 1], .7,
          'FURN_Planter FURN_Soil FURN_PlantStem FURN_Leaf', 20,
          '陶器色の鉢、土、9本の茎と立体的な葉。元ワールドから切り出したローポリの観葉植物。',
          'A low-poly ceramic-colored pot with soil, nine stems and modeled leaves from the original cafe.'),
    asset('espresso-machine', 'コモンズ・エスプレッソマシン', 'Commons espresso machine', 'technology', 'FURN_Bar', [4.4, 6.02], .5,
          'FURN_Espresso FURN_EspressoFace FURN_Portafilter', 4,
          '黒皮鋼の筐体と生成オリジナルの操作面を持つ架空のコーヒーマシン。操作機能のない装飾モデル。',
          'A fictional espresso machine with a blackened-steel body and original AI-generated panel artwork. Decorative only.'),
    asset('coffee-grinder', 'コモンズ・コーヒーグラインダー', 'Commons coffee grinder', 'technology', 'FURN_Bar', [5.2, 6.02], .1,
          'FURN_Grinder FURN_BeanHopper', 2,
          'スチールの本体とアンバー色の豆ホッパー。カフェカウンター向けの装飾モデル。',
          'A steel body with an amber-colored bean hopper for cafe counters. Decorative only.'),
    asset('pa-speaker', 'コモンズ・PAスピーカー', 'Commons PA speaker', 'technology', 'AV_Stage', [9.5, 16.2], .3,
          'AV_Speaker AV_Grille', 15,
          '黒い筐体と前面グリルを持つ縦長のPAスピーカー。音源や再生スクリプトは含みません。',
          'A tall black PA enclosure with modeled front grille strips; no audio or playback scripts.'),
    asset('dj-controller', 'コモンズ・DJコントローラー', 'Commons DJ controller', 'technology', 'AV_DJ', [14, 13.32], 1.1,
          'AV_RelayController AV_Jog AV_JogTrim AV_MixerKnob AV_FaderCap AV_DeckKnob AV_PerformancePad AV_Crossfader AV_PitchFader', 46,
          '架空のRELAY R2コントローラー。ジョグ、ノブ、フェーダー、パッドを立体化した装飾モデルで、操作面は生成オリジナル。',
          'A fictional RELAY R2 controller with modeled jog wheels, knobs, faders and pads plus original generated panel artwork. Decorative only.', math.pi),
    asset('display-plinth', 'コモンズ・展示台', 'Commons display plinth', 'furniture', 'AV_Stage', [17.8, 13.3], .1,
          'AV_DemoPedestal AV_DemoRim', 2,
          '黒皮鋼の円柱とシアンの発光リム。展示物や小型作品を載せられる独立した台座。',
          'A blackened-steel cylindrical plinth with a cyan emissive rim for displays and small exhibits.'),
]

EXPANSION = [
    asset('low-table', 'コモンズ・ローテーブル', 'Commons low table', 'furniture', 'MODE_Lounge', [10.1,5.6], .1,
          'FURN_TableTop FURN_TableTrim FURN_TableBase FURN_TableStem', 4,
          'オーク天板と真鍮の縁を持つ高さ約47cmのローテーブル。ソファ前やラウンジ向け。卓上の小物は含みません。',
          'A roughly 47 cm low oak table with a brass edge for sofas and lounges, without tabletop props.'),
    asset('round-stage', 'コモンズ・円形ステージ', 'Commons round stage', 'architecture', 'AV_Stage', [14,13.2], .1,
          'AV_Stage AV_StageEdge', 2,
          '直径4.8mの低い円形ステージ。オークの床とシアンの発光リムを保持し、周囲の設備を除いて独立化。',
          'A low 4.8 m circular stage with an oak floor and cyan emissive rim, without surrounding equipment.'),
    asset('equipment-rack', 'コモンズ・機材ラック', 'Commons equipment rack', 'technology', 'AV_BackOfHouse', [21,17.1], .4,
          'AV_Rack AV_RackUnit AV_StatusLED', 46,
          '9段の操作パネルとシアンの表示灯を備えた架空のAV機材ラック。元の生成パネル画像を同梱。',
          'A fictional AV rack with nine printed units and cyan indicators. Original panel artwork is embedded; decorative only.'),
    asset('dj-desk', 'コモンズ・ワークカウンター', 'Commons work counter', 'furniture', 'AV_DJ', [14,13.32], 2.4,
          'AV_DJDesk AV_DJFascia AV_DJLeg', 4,
          '幅4.9mのオーク天板、前板、2本脚。DJ機材や文字を除き、受付や作業用のカウンターとして独立化。',
          'A 4.9 m oak work counter with a front panel and two steel legs. DJ equipment and lettering are excluded.'),
    asset('coffee-bag', 'コモンズ・コーヒー袋', 'Commons coffee bag', 'props', 'FURN_Bar', [3.36,6.03], .08,
          'FURN_CoffeeBag FURN_BagFold', 2,
          '架空ブランドCOMMON GROUNDのコーヒー袋。上部の折り留めと生成オリジナルのパッケージ画像付き。',
          'A fictional COMMON GROUND coffee package with a top fold and original generated print.'),
    asset('bottle-set', 'コモンズ・ボトル6本セット', 'Commons six bottle set', 'props', 'FURN_Bar', [.84,7.2375], .65,
          'FURN_Bottle FURN_BottleNeck FURN_BottleCap FURN_BottleLabel', 24,
          '形状・高さの異なるボトル6本。架空の6ブランドのラベルを保持し、各部品を別メッシュで収録。',
          'Six bottles with varied heights, caps and original fictional-brand labels. Parts remain separate meshes.',
          -math.pi/2, z_range=[1.26,1.7]),
    asset('book-set', 'コモンズ・本6冊セット', 'Commons six book set', 'props', 'FURN_QuietRoom', [22.3375,1.4], .5,
          'FURN_Book', 6,
          'CODE・SOUND・SPACE・FORM・LIGHT・IDEASの背表紙を持つ本6冊。棚や机の装飾に使える独立したメッシュ。',
          'Six separate books with original CODE, SOUND, SPACE, FORM, LIGHT and IDEAS spine artwork for shelves or desks.',
          math.pi, z_range=[5.7,6.1]),
    asset('table-candle', 'コモンズ・テーブルキャンドル', 'Commons table candle', 'props', 'FURN_Cafe', [2,2.4], .05,
          'LGT_TableCandle LGT_CandleGlow', 2,
          '陶器色の細いキャンドルと暖色の発光部。テーブルや棚向けの軽量な小物。実ライトは含みません。',
          'A small ceramic-colored table candle with a warm emissive tip. No runtime light is included.'),
    asset('halo-light', 'コモンズ・リング照明', 'Commons halo light', 'props', 'LGT_Main', [14,6.4], .1,
          'LGT_Halo LGT_HaloLight', 2,
          '真鍮のリングと暖色の発光リングを持つ直径約3.5mの天井照明。吊り具と実ライトは含みません。',
          'A roughly 3.5 m brass ceiling ring with a warm emissive strip. Suspension and runtime lights are not included.'),
    asset('poster-frame', 'コモンズ・ポスターフレーム', 'Commons poster frame', 'props', 'AV_Gallery', [24.5,7.3], .1,
          'AV_PosterFrame_05 AV_PosterFace_05', 2,
          '真鍮の縁と黒い表示面を持つ縦長フレーム。元の文字や図柄を除き、表示面を別メッシュで保持。',
          'A portrait brass frame with a separate black display face. Original lettering and poster artwork are excluded.', math.pi),
    asset('bar-counter', 'コモンズ・スラットバーカウンター', 'Commons slatted bar counter', 'furniture', 'FURN_Bar', [3.95,5.75], 3,
          'FURN_BarReturn BarTopReturn FURN_BarFlute FURN_BarFootRail', 38,
          '幅5.3mの直線カウンター。オーク天板、縦スラット、真鍮の足掛けを保持。卓上の機材は含みません。',
          'A 5.3 m straight bar counter with an oak top, vertical slats and a brass foot rail; no countertop equipment.',
          xy_bounds=[1.2,5.2,6.7,6.51]),
    asset('floating-bookshelf', 'コモンズ・壁付け本棚', 'Commons floating bookshelf', 'furniture', 'FURN_QuietRoom', [24,1.4], 2.4,
          'FURN_ArchiveShelf FURN_Book', 75,
          'オークの棚板3段と本72冊。元の配置を保った壁付け本棚のセットで、壁や取付金具は含みません。',
          'Three floating oak shelves with 72 individual books in their original arrangement. No wall or mounting hardware is included.', math.pi),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inputs(source, fetch):
    def check(item):
        name, expected = item
        target = source / name
        if not target.exists() and fetch:
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/{name}', timeout=120) as response:
                data = response.read()
            assert sha(data) == expected, f'Upstream hash mismatch: {name}'
            target.write_bytes(data)
        assert target.is_file() and sha(target.read_bytes()) == expected, f'Input changed: {name}'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(check, INPUTS.items()))


def glb_info(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    length, kind = struct.unpack_from('<I4s', raw, 12)
    assert kind == b'JSON'
    document = json.loads(raw[20:20+length])
    binary = raw[28+length:]
    triangles = sum(document['accessors'][p.get('indices', p['attributes']['POSITION'])]['count']//3
                    for mesh in document['meshes'] for p in mesh['primitives'])
    hashes = []
    for image in document.get('images', []):
        assert 'uri' not in image, 'Textures must be embedded in the GLB'
        view = document['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        digest = sha(binary[start:start+view['byteLength']])
        assert digest in INPUTS.values(), f'Texture pixels/file changed: {image.get("name")}'
        hashes.append(digest)
    assert all('uri' not in b for b in document['buffers'])
    for s in document.get('samplers', []):
        assert s.get('wrapS', 10497) in [33648, 33071], 'Mirror or clamp sampler required'
        assert s.get('wrapT', 10497) in [33648, 33071], 'Mirror or clamp sampler required'
    return triangles, sorted(hashes)


def run(args):
    import bpy
    from mathutils import Matrix, Vector
    assert bpy.app.version[:3] == (4, 5, 14), bpy.app.version_string
    source = args.source_root.resolve()
    inputs(source, args.fetch)
    bpy.ops.wm.open_mainfile(filepath=str(source/'Blender/The_Commons_Compact.blend'), use_scripts=False)
    original_scene = bpy.context.scene
    original_objects = list(original_scene.objects)
    graph = bpy.context.evaluated_depsgraph_get()
    material_cache = {}

    def material(original):
        if original.name in material_cache:
            return material_cache[original.name]
        m = original.copy()
        m.name = original.name + '_Meshcopia'
        if m.get('texture_key'):
            # Match the source repository's standard glTF export: image -> base color.
            p = m.node_tree.nodes.get('Principled BSDF')
            image = next(n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE')
            filename = image.image.name
            if not filename.endswith('.png'):
                filename += '.png'
            image.image.filepath = str(source/'Unity/Assets/TheCommons/Textures'/filename)
            assert image.image.filepath.endswith('_albedo.png') and Path(image.image.filepath).is_file()
            image.image.reload()
            for link in list(p.inputs['Base Color'].links):
                m.node_tree.links.remove(link)
            m.node_tree.links.new(image.outputs['Color'], p.inputs['Base Color'])
        material_cache[original.name] = m
        return m

    selected_specs = [a for a in (EXPANSION if args.batch == 'expansion' else ASSETS) if not args.only or a['id'] in args.only]
    for spec in selected_specs:
        bpy.context.window.scene = original_scene
        graph = bpy.context.evaluated_depsgraph_get()
        objects = []
        for o in original_objects:
            if o.type != 'MESH' or o.name.split('.')[0] not in spec['names'] or spec['collection'] not in [c.name for c in o.users_collection]:
                continue
            center = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
            if spec['z_range'] and not spec['z_range'][0] <= center.z <= spec['z_range'][1]:
                continue
            if spec['xy_bounds']:
                x0,y0,x1,y1=spec['xy_bounds']
                if not (x0 <= center.x <= x1 and y0 <= center.y <= y1):
                    continue
            if max(abs(center[i]-spec['center'][i]) for i in [0, 1]) < spec['radius']:
                objects.append(o)
        objects.sort(key=lambda o: o.name)
        assert len(objects) == spec['expected'], (spec['id'], len(objects), spec['expected'], [o.name for o in objects])
        print('SELECT', spec['id'], [o.name for o in objects], flush=True)
        if args.inspect:
            continue
        folder = ROOT/'_inbox'/spec['id']
        assert not folder.exists() and not (ROOT/'content/assets'/spec['id']).exists(), f'Existing ID: {spec["id"]}'
        (folder/'source').mkdir(parents=True)
        scene = bpy.data.scenes.new(spec['id'])
        copies = []
        rotation = Matrix.Rotation(spec['rotation'], 4, 'Z')
        for o in objects:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(graph), depsgraph=graph, preserve_all_data_layers=True)
            me.transform(rotation @ o.matrix_world)
            for i, original_material in enumerate(list(me.materials)):
                me.materials[i] = material(original_material)
            copy = bpy.data.objects.new(o.name, me)
            scene.collection.objects.link(copy)
            copies.append(copy)
        vertices = [v.co.copy() for o in copies for v in o.data.vertices]
        low = Vector([min(v[i] for v in vertices) for i in range(3)])
        high = Vector([max(v[i] for v in vertices) for i in range(3)])
        offset = Vector(((low.x+high.x)/2, (low.y+high.y)/2, low.z))
        dimensions = high-low
        for o in copies:
            o.data.transform(Matrix.Translation(-offset))
        bpy.context.window.scene = scene
        bpy.context.view_layer.update()
        for o in copies:
            o.select_set(True)
        bpy.context.view_layer.objects.active = copies[0]
        file = folder/'source'/f'{spec["id"]}.glb'
        bpy.ops.export_scene.gltf(filepath=str(file), export_format='GLB', use_selection=True,
                                  export_yup=True, export_materials='EXPORT', export_image_format='AUTO',
                                  export_animations=False, export_cameras=False, export_lights=False)
        triangle_count, image_hashes = glb_info(file)
        stl = bytearray(b'Meshcopia / Xenoah / CC BY 4.0'.ljust(80, b'\0'))
        stl.extend(struct.pack('<I', triangle_count))
        count = 0
        for o in copies:
            o.data.calc_loop_triangles()
            for tri in o.data.loop_triangles:
                vs = [o.data.vertices[i].co for i in tri.vertices]
                vs = [Vector((p.x, p.z, -p.y)) for p in vs]  # Same right-handed Y-up basis as GLB.
                normal = (vs[1]-vs[0]).cross(vs[2]-vs[0]).normalized()
                stl.extend(struct.pack('<12fH', *normal, *(c for v in vs for c in v), 0))
                count += 1
        assert count == triangle_count, (count, triangle_count)
        (folder/'source'/f'{spec["id"]}.stl').write_bytes(stl)
        changes = 'Selected original meshes extracted; chamfers evaluated; pivot centered at base; meter scale and Y-up retained; original PNG bytes and mirror/clamp sampling preserved. Unity behaviors omitted.'
        provenance = dict(method='Original procedural cafe geometry with original AI-generated material images',
                          tool='Blender 4.5.14; Meshcopia cafe extraction script',
                          rights='Xenoah original assets. On 2026-10-14 the owner requested their publication in the CC-BY-4.0 Meshcopia library. No third-party model, SDK, vehicle, font or poster is included.',
                          sourceUrl=SOURCE_URL, sourceCommit=COMMIT,
                          generatorUrl='https://github.com/Xenoah/meshcopia/blob/main/scripts/import-commons-cafe.py',
                          sourceObjects=[o.name for o in objects], sourceCollection=spec['collection'],
                          sourceFiles={p:h for p,h in INPUTS.items() if not p.endswith('.png') or h in image_hashes},
                          embeddedImageSha256=image_hashes, changes=changes)
        metadata = {k:spec[k] for k in ['id','title','titleEn','description','descriptionEn','category']}
        metadata.update(type='model', tags=['commons','cafe','オリジナル',spec['category'],*spec['id'].split('-')[1:]],
                        author='Xenoah', license='CC-BY-4.0', version='1.0.0', status='public',
                        created=DATE, updated=DATE, thumbnail='preview.png', provenance=provenance,
                        unit='m', upAxis='Y', triangles=triangle_count,
                        dimensions=[round(dimensions[i],5) for i in [0,2,1]], preview=file.name,
                        uv='Original UVs; architectural materials use mirrored repeat, panel artwork uses clamp. STL has no colors or UVs. Not validated for 3D printing.')
        (folder/'asset.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        # Actual extracted mesh with the same standard materials, lit for a catalog thumbnail.
        scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=24
        scene.cycles.use_denoising=True; scene.cycles.seed=104
        scene.render.threads_mode='FIXED'; scene.render.threads=4
        scene.render.resolution_x=1000; scene.render.resolution_y=800; scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
        scene.world=bpy.data.worlds.new(spec['id']+' studio'); scene.world.use_nodes=True
        scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.10,.13,.17,1)
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
        scene.view_settings.view_transform='AgX'
        maxdim=max(dimensions); target=Vector((0,0,dimensions.z*.46))
        def aim(obj, point):
            obj.rotation_euler=(point-obj.location).to_track_quat('-Z','Y').to_euler()
        camera_data=bpy.data.cameras.new('Catalog camera'); camera=bpy.data.objects.new('Catalog camera',camera_data)
        scene.collection.objects.link(camera); scene.camera=camera; camera_data.type='ORTHO'
        camera.location=target+Vector((1.3,-2.1,1.25))*maxdim; aim(camera,target)
        inv=camera.rotation_euler.to_matrix().transposed()
        points=[inv@(v.co-target) for o in copies for v in o.data.vertices]
        width=max(p.x for p in points)-min(p.x for p in points)
        height=max(p.y for p in points)-min(p.y for p in points)
        camera_data.ortho_scale=max(width/.78,height*1.25/.76)
        for label, position, power, color in [('Key',(-2,-3,4),520,(1,.84,.67)),('Fill',(3,-1,2),320,(.65,.79,1)),('Rim',(0,3,3),620,(.70,.87,1))]:
            light_data=bpy.data.lights.new(label,'AREA'); light_data.energy=power*maxdim**2; light_data.color=color; light_data.shape='DISK'; light_data.size=maxdim*2.3
            light=bpy.data.objects.new(label,light_data); scene.collection.objects.link(light)
            light.location=target+Vector(position)*maxdim; aim(light,target)
        # A studio floor is only in the thumbnail, never in the model export.
        bpy.ops.mesh.primitive_plane_add(size=maxdim*200, location=(0,0,-maxdim*.004))
        floor=bpy.context.object; floor.name='Thumbnail studio floor'
        floor_mat=bpy.data.materials.new('Studio charcoal'); floor_mat.diffuse_color=(.035,.048,.06,1); floor_mat.use_nodes=True
        floor_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.035,.048,.06,1)
        floor_mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.84
        floor.data.materials.append(floor_mat)
        scene.render.filepath=str(folder/'preview.png')
        bpy.ops.render.render(write_still=True)
        print('EXPORTED',spec['id'],triangle_count,'triangles',file.stat().st_size,'GLB bytes',flush=True)
        bpy.context.window.scene=original_scene
        for o in list(scene.objects):
            bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(scene)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,default=ROOT/'.cache/commons-cafe')
    parser.add_argument('--fetch',action='store_true')
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--only',nargs='+')
    parser.add_argument('--batch',choices=['original','expansion'],default='original')
    run(parser.parse_args())
