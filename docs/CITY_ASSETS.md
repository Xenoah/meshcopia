# オリジナル街モデル: ソースと再生成

このコレクションは Meshcopia のために制作したオリジナルです。既存の街並み作品からの抽出ではありません。各 `asset.json` の `usages` は制作プロジェクト・セレクター・ソースを示し、外部作品での使用実績を意味しません。公開対象は `status: public` の素材のみです。

## 利用前の確認

[日本語導入ガイド](CITY_IMPORT_GUIDE.md)と[メタデータ確認表](CITY_METADATA_LIMITATIONS_CHECKLIST.md)を参照してください。静的なゲーム・可視化用素材で、単位はメートル、GLB は Y-up。STL は形状のみです。製造、構造、安全、医療、交通制御、アクセシビリティ適合、3D プリント、Unity／VRChatでの動作は保証しません。

多くのモデルは定数色 PBR 材質と部品ごとの UV0 を持ちます。固有のライトマップ UV2 ではありません。街路樹は例外として、埋め込み樹皮色・接空間法線画像、タンジェント、葉の頂点色、両面の開いた葉を含みます。これらを汎用の結合処理で失わないでください。

## 再生成の手順

`scripts/city/` に21本の生成・後処理スクリプトを収録しています。`usages[].sourcePaths` と `selectors`、`provenance` の生成元・後処理・ハッシュを照合してください。Blender 4.3.2 と公式 bpy 4.5.14 由来の配布物が混在します。現在のソースや異なる Blender 版での再生成が、既存の配布バイトと一致するとは主張しません。既存配布ファイルを再生成物で上書きせず、必ず別の出力先を使用します。

例:

```sh
blender -b --python scripts/city/access.py -- --output city-new --only city-bollard
blender -b --python scripts/city/infrastructure_manhole_optimized.py -- --output city-cover-new
```

Blender 同梱の Python、bpy、mathutils と、同環境の NumPy を使用します。通常の Python で実行する場合は互換性のある公式 bpy パッケージが必要です。環境やレンダラーによって画像が変わるため、形状と実際の GLB を再インポートした画像を両方確認します。生成物は draft です。ソース修正だけでは既存配布物は変わりません。

## 静的部品のグループ化

元の形状を生成した後、対象モデルのみ別出力先にグループ化します。

```sh
python scripts/city/group_static_assemblies.py --input city-new/city-hvac-condenser --output city-grouped
blender -b --python scripts/city/render_grouped_assemblies.py -- --input city-grouped/city-hvac-condenser --output city-render
blender -b --python scripts/city/civic_grouped_assets.py -- --source city-new/city-shopping-trolley --output city-grouped --profile trolley
```

インフラ7種は `group_static_assemblies.py`、自転車・ショッピングカート・自販機は `civic_grouped_assets.py` と `civic_static_groups.py` を使用します。検査蓋の元形状には `infrastructure_manhole_optimized.py` の微細踏み模様最適化を適用します。グループ化は汎用最適化器ではなく、対象の名前付き静的部品向けです。樹木・未知の属性・アニメーションへ無条件に適用しないでください。

前後の三角形位置、法線、UV、材質と寸法を照合し、実際の出力を前後から描画します。ノード／プリミティブ数の削減は実測ドローコールや FPS の保証ではありません。GLB のハッシュ、STL のハッシュ・三角形数、メタデータ、サムネイルの一致を検証してから通常の取込・公開工程へ進めます。

## 権利と公開

作者 Xenoah、CC BY 4.0。元の作者表示、ライセンスへのリンクと変更内容を保持してください。`LICENSE` と各素材メタデータを参照してください。公開には通常の `npm run check`、実ファイルの視覚確認、ブラウザ検証が必要です。ローカル検証・候補選定・ソースの保存は、公開完了の証拠ではありません。
