# Meshcopia

**人間とAIエージェントのための、無料3Dモデルとシームレステクスチャ。**

[素材ライブラリ](https://xenoah.github.io/meshcopia/) · [Releases](https://github.com/Xenoah/meshcopia/releases) · [エージェント向けJSON](https://xenoah.github.io/meshcopia/api/catalog.json)

![Meshcopia library](https://github.com/Xenoah/meshcopia/releases/download/v1.0.0/desktop-catalog.png)

> **公開状況**: Releaseの素材ZIPは取得可能です。GitHub Pagesは管理者が Settings → Pages → Source: GitHub Actions を選ぶ初回設定待ちです。設定後、Actionsの失敗したPagesジョブを再実行してください。

## できること

- 大きなサムネイル、名前・タグ・形式検索、カテゴリー、種類、並び替え。検索条件はURLで共有。
- 一覧からクイック3Dプレビュー。詳細で回転・拡大・ワイヤー・ライティング・材質を切替。
- GLB / glTF / FBX / STL / OBJ / STEPプレビュー。Three.js / occt-import-js。
- テクスチャの1×1・2×2・4×4タイル確認とPBR球体、各マップ表示。
- 全体ZIP、モデルのみZIP、単体ファイル。モデルのみZIPにも依存ファイルとライセンスを保持。
- 全素材 **CC BY 4.0**。商用利用・改変・再配布可。作者名・出典・ライセンス・変更点の表示が必要。
- 認証不要のJSON/NDJSONカタログ、個別マニフェスト、SHA-256、クレジットコピー。
- モバイル対応、キーボード操作、検索ショートカット `/`、JP/EN切替（素材と主要UI）。

## 初期収録

**3Dモデル8点**: スタジオチェア、アトリエランプ、ウッドスラットベンチ、テラコッタプランター、マーケット木箱、ガーデンアーチ、フィールドターミナル、ラウンドサイン。

**テクスチャ6点**: ライムストーン、シダーボード、クレイブリック、セージテラゾー、ヘアラインアルミ、コバルトセラミック。各1024px / Base Color・Normal・Roughness・Height。

すべて今回のために作成したオリジナルのプロシージャル素材です。サムネイルは実際の配布メッシュから描画。写真ベース・スキャン・写実素材ではありません。

モデル: 単位m、Y-up、GLB/OBJ/STL。GLBには色とPBR材質、OBJにはMTLを同梱。STLは色を持ちません。UVは基本的な平面投影で、方向性のあるテクスチャには再展開を推奨します。ゲーム・VR向けの小道具で、3Dプリントや機構部品としては未検証です。

## 開発

Node.js 22以上。

```sh
npm ci
npm run dev
npm run check
```

既定のURLパスは `/meshcopia/`。ルート配信には `PUBLIC_BASE_PATH=''`、独自ドメインには `PUBLIC_SITE` を指定してビルドします。プレビューは通常 `http://localhost:4321/meshcopia/`。

## 素材を追加

```sh
npm run new:asset -- my-chair model
# _inbox/my-chair/asset.json、preview.webp、source/ を記入・追加
npm run import:inbox -- my-chair          # 検証のみ
npm run import:inbox -- my-chair --apply  # content/assets/ へ移動
npm run check
git add .
git commit -m "feat(assets): add my-chair"
git push origin main
```

`_inbox/**` へのpushでもActionsが自動で取り込みます。既存IDは上書きしません。更新は `content/assets/<id>/` を直接変更し、versionとupdatedを更新します。`draft` は配信物に含めません。`hidden` は一覧から除外するだけで非公開ではありません。

詳細は [AGENTS.md](AGENTS.md)、[CONTRIBUTING.md](CONTRIBUTING.md)、[asset schema](docs/asset-schema.json) を参照。

## ビルドとリリース

`npm run build` が素材検証、ZIP・JSON生成、Astro静的ビルドを行います。`npm run check` はその前後に検証を実行します。mainへのpushでCIとPagesが動作します。`.release.json` のversionを変更すると、成功した検証後に対応するGitHub Releaseを作成します。`prerelease: true` でプレリリース、`false` で正式リリースです。同一タグは作り直しません。

リリースには公開サイトZIP、全素材ZIP、モデル集ZIP、テクスチャ集ZIP、カタログJSON、SHA256SUMSを添付。GitHub Pagesの初回設定は **Settings → Pages → Source: GitHub Actions** を選択してください。

## 素材の再生成

通常のビルドではPython不要。オリジナルの生成コードを再実行する場合のみ:

```sh
python3 -m pip install -r scripts/requirements-assets.txt
python3 scripts/create-starter-assets.py
npm run check
```

## 継承とライセンス

[Xenoah/archive-3dmodels](https://github.com/Xenoah/archive-3dmodels) のAstro・Three.jsビューアとフォルダー投入→カタログ→ZIPの設計を継承。ビューア、ZIP writerは参照コミット `7d52500c361200884d56e8361757953474dfdb68` を基礎に改修。CC BY-NCの旧モデル、解析タグ、旧サイトの設定は移植していません。

本リポジトリのオリジナル素材・実装は [CC BY 4.0](LICENSE)。依存ライブラリはそれぞれのライセンスが適用されます。[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照。
