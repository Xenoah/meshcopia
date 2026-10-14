"""Copy nine pinned original PNGs, preserving bytes and source wrap modes.

Requires Pillow; runs locally or as part of the one-time Commons expansion in CI.
Only catalog thumbnails are resized. No derived PBR maps are invented.
"""
from pathlib import Path
import argparse, importlib.util, json, shutil
from PIL import Image

spec=importlib.util.spec_from_file_location('cafe',Path(__file__).with_name('import-commons-cafe.py'))
cafe=importlib.util.module_from_spec(spec); spec.loader.exec_module(cafe)
TEXTURES=[
 ('warm_oak','オーク材','Warm oak','木目の細かな暖色のオーク。家具・床・壁のベースカラーに。','Warm oak grain for furniture, floors and walls.',.65,0),
 ('mineral_plaster','ミネラルプラスター','Mineral plaster','細かな砂目と穏やかな色むらを持つ漆喰。内壁や天井に。','Quiet mineral plaster with fine mottling for interior walls and ceilings.',.9,0),
 ('basalt_terrazzo','バサルトテラゾー','Basalt terrazzo','チャコール色の石片を散らしたテラゾー。床やカウンターに。','Fine charcoal basalt terrazzo for floors and counters.',.58,0),
 ('blackened_steel','黒皮鋼','Blackened steel','低コントラストの青灰色の黒皮鋼。家具フレームや工業プロップに。','Subtle blue-grey blackened steel for furniture frames and industrial props.',.65,.45),
 ('satin_brass','サテンブラス','Satin brass','細い磨き目を持つ落ち着いた真鍮。縁取り、照明、金具に。','Subdued satin brass for trims, lighting and fittings.',.48,.65),
 ('teal_woven','ティールの織布','Teal woven fabric','細密な織り目の深い青緑色の布。椅子やソファの張り地に。','Deep teal woven upholstery for chairs and sofas.',.96,0),
 ('relay_controller','RELAY R2 操作面','RELAY R2 panel','架空のDJコントローラー用の操作面。UVを画像に合わせて使用する非タイル素材。','Original fictional DJ panel artwork. Non-tileable; match your mesh UVs to the image.',.8,0),
 ('bar_labels','架空ブランドのボトルラベル','Fictional bottle labels','架空の6ブランドのラベルを3列×2段にまとめたアトラス。UVで使うセルを指定。','Six fictional bottle-label designs in a 3-column, 2-row atlas. Select cells with mesh UVs.',.84,0),
 ('cafe_props','カフェ小物プリント','Cafe prop prints','機材パネル・本の背表紙・コーヒー袋の4領域アトラス。元の縦横比を保持。','An atlas of equipment panels, book spines and coffee packaging in its original aspect ratio.',.73,0),
]

def run(args):
 source=args.source_root.resolve(); cafe.inputs(source,args.fetch)
 original={x['name']:x for x in json.loads((source/'Documentation/texture_provenance.json').read_text())}
 for name,title,en,desc,desc_en,roughness,metalness in TEXTURES:
  record=original[name]; wrap='mirror' if record['wrap'].startswith('Mirror') else 'clamp'
  slug='commons-'+name.replace('_','-'); folder=cafe.ROOT/'_inbox'/slug
  assert not folder.exists() and not (cafe.ROOT/'content/assets'/slug).exists(),f'Existing ID: {slug}'
  (folder/'source').mkdir(parents=True)
  relative='Unity/Assets/TheCommons/Textures/'+record['file']; src=source/relative
  shutil.copyfile(src,folder/'source'/record['file'])
  with Image.open(src) as image:
   width,height=image.size; thumbnail=image.convert('RGB'); thumbnail.thumbnail((1000,1000))
   thumbnail.save(folder/'preview.webp',quality=94,method=6)
  usage=('Mirror / MirroredRepeatWrappingを両軸に設定。通常Repeat用の対向辺一致は保証しません。' if wrap=='mirror' else 'Clampで使用。シームレス反復には対応しません。')
  usage_en=('Set both axes to Mirror / MirroredRepeatWrapping. Opposite edges are not guaranteed to match under ordinary Repeat.' if wrap=='mirror' else 'Use Clamp. This atlas does not support seamless tiling.')
  provenance=dict(method='Original AI-generated cafe texture, copied byte-for-byte from its recorded source',tool='Built-in image_gen (original generation); Pillow (thumbnail only)',
    rights='Xenoah original image. On 2026-10-14 the owner authorized its publication in the CC-BY-4.0 Meshcopia library. No third-party photograph or texture is included.',
    sourceUrl=cafe.SOURCE_URL,sourceCommit=cafe.COMMIT,sourcePixelsUnchanged=True,
    generatorUrl='https://github.com/Xenoah/meshcopia/blob/main/scripts/import-commons-textures.py',
    sourceFiles={relative:cafe.INPUTS[relative],'Documentation/texture_provenance.json':cafe.INPUTS['Documentation/texture_provenance.json']},
    changes='Original PNG is unchanged. A separate resized WebP thumbnail and metadata were added. Original '+record['wrap']+' sampling is retained.',
    generationBrief=record['prompt_material'])
  a=dict(id=slug,type='texture',title='コモンズ・'+title,titleEn='Commons '+en,description=desc+' ベースカラー画像のみ。'+usage,
    descriptionEn=desc_en+' Base color only. '+usage_en,category='materials' if wrap=='mirror' else 'atlases',
    tags=['commons','cafe','オリジナル','base-color',wrap,*name.split('_')]+(['鏡像リピート','material'] if wrap=='mirror' else ['atlas','アトラス','non-tileable']),
    author='Xenoah',license='CC-BY-4.0',version='1.0.0',status='public',created=cafe.DATE,updated=cafe.DATE,
    thumbnail='preview.webp',provenance=provenance,
    usages=[dict(relationship='original',project='Commons cafe',sourceUrl=cafe.SOURCE_URL,sourceRef=cafe.COMMIT,sourcePaths=[relative],context='Original world texture; no specific deployed scene usage asserted.')],seamless=wrap=='mirror',wrapMode=wrap,width=width,height=height,resolution=max(width,height),
    maps={'baseColor':record['file']},colorSpace={'baseColor':'sRGB'},roughness=roughness,metalness=metalness,usage=usage,usageEn=usage_en)
  (folder/'asset.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
  print('COPIED',slug,width,height,wrap,cafe.INPUTS[relative])

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,default=cafe.ROOT/'.cache/commons-cafe');parser.add_argument('--fetch',action='store_true')
 run(parser.parse_args())
