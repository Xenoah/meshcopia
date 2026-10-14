# Meshcopia

**人間とAIエージェントのための、無料3Dモデルとテクスチャ。**

[素材ライブラリ](https://xenoah.github.io/meshcopia/) · [Releases](https://github.com/Xenoah/meshcopia/releases) · [エージェント向けJSON](https://xenoah.github.io/meshcopia/api/catalog.json)

![Meshcopia library](https://github.com/Xenoah/meshcopia/releases/download/v1.3.0/desktop-catalog-full.png)

> **公開中**: [Meshcopia](https://xenoah.github.io/meshcopia/) · [正式版 v1.4.0](https://github.com/Xenoah/meshcopia/releases/tag/v1.4.0)。3Dモデル83点とテクスチャ36点を無料で取得できます。

## できること

- 大きなサムネイル、名前・タグ・形式検索、カテゴリー、種類、並び替え。検索条件はURLで共有。
- 一覧からクイック3Dプレビュー。詳細で回転・拡大・ワイヤー・ライティング・材質を切替。
- GLB / glTF / FBX / STL / OBJ / STEPプレビュー。Three.js / occt-import-js。
- 通常・鏡像リピートの1×1・2×2・4×4確認と球体表示。アトラスは非タイル素材として元の縦横比で表示。
- 全体ZIP、モデルのみZIP、単体ファイル。モデルのみZIPにも依存ファイルとライセンスを保持。
- 全素材 **CC BY 4.0**。商用利用・改変・再配布可。作者名・出典・ライセンス・変更点の表示が必要。
- 認証不要のJSON/NDJSONカタログ、個別マニフェスト、SHA-256、クレジットコピー。
- モバイル対応、キーボード操作、検索ショートカット `/`、JP/EN切替（素材と主要UI）。

## 収録素材

**街路オリジナル12モデル（v1.4）**: ボラード、自転車ラック、歩道柵、段差スロープ、減速クッション、注水バリア、ごみ箱、分別ステーション、飲水台、宅配ロッカー、パーキングメーター、消火栓。実メッシュ画像、GLB/STL、原寸・三角形数・出元情報付き。小さな金具や滑り止めの分割数を調整し、シルエットと使いやすい軽さを両立。[制作・検証・制限](docs/CITY_ASSETS.md)。

**TreeTop Yokochoオリジナル60点（v1.3）**: 立体看板、椅子・テーブルセット、カウンター、棚、照明、能舞台、階段、設備、入口広場の家具など39モデル。元画像を保持した21テクスチャ（Mirror 9点、Clamp 12点）。外部スキャン画像は除外し、該当材質の置換を各モデルに明示。実メッシュのサムネイル、出元のオブジェクト名、SHA256、正確な三角形数・寸法を収録。[選定・出典・制限](docs/YOKOCHO_IMPORT.md)。

**Commons cafeオリジナル12点**: バースツール、ラウンジチェア、ソファ、丸テーブル、ペンダントライト、コーヒーカップ、観葉植物、エスプレッソマシン、グラインダー、PAスピーカー、DJコントローラー、展示台。[元ワールド](https://github.com/Xenoah/vrcworld_tech-tech-cafe)から独立したGLB/STLとして抽出。元の生成テクスチャ、UV、鏡像反復・Clamp設定を保持しています。[選定根拠・出典・再現手順](docs/COMMONS_IMPORT.md)。

**Commons cafe追加メッシュ12点（v1.2）**: ローテーブル、円形ステージ、機材ラック、ワークカウンター、コーヒー袋、ボトル6本セット、本6冊セット、テーブルキャンドル、リング照明、ポスターフレーム、スラットバーカウンター、壁付け本棚。

**Commons cafeテクスチャ9点（v1.2）**: オーク・漆喰・テラゾー・黒皮鋼・真鍮・織布は1254pxの鏡像リピート用ベースカラー。機材操作面・瓶ラベル・小物プリントは非タイルのアトラス。9点とも元PNGを無加工で配布し、元の出典とSHA-256を保持。

**3Dモデル8点**: スタジオチェア、アトリエランプ、ウッドスラットベンチ、テラコッタプランター、マーケット木箱、ガーデンアーチ、フィールドターミナル、ラウンドサイン。

**通常リピートのテクスチャ6点**: ライムストーン、シダーボード、クレイブリック、セージテラゾー、ヘアラインアルミ、コバルトセラミック。各1024px / Base Color・Normal・Roughness・Height。

初期8モデル・6テクスチャはMeshcopiaのオリジナルのプロシージャル素材です。Commons cafeの追加素材は元ワールドのオリジナル形状と生成画像を使用。サムネイルは実際の配布メッシュから描画しています。

モデル: 単位m、Y-up。初期モデルはGLB/OBJ/STL、Commons cafe素材はGLB/STL。GLBには色・PBR材質を保持し、Commons cafe素材は画像も埋め込んでいます。OBJにはMTLを同梱。STLは色を持ちません。UVの仕様は各素材に記載しています。ゲーム・VR向けの小道具で、3Dプリントや機構部品としては未検証です。

## テクスチャとAPIの反復方式

カタログの `schemaVersion` は **2.1.0**。`width` / `height` は実ピクセル寸法、`resolution` は長辺です。`wrapMode` を両軸に適用します。

| wrapMode | 使い方 | seamless |
| --- | --- | --- |
| repeat | 通常の繰り返し。対向辺が一致 | true |
| mirror | 隣り合うタイルを反転。Mirror / MirroredRepeatWrapping | true（指定方式での連続性） |
| clamp | アトラス。UVで領域を選択し、繰り返さない | false |

鏡像リピート素材を通常Repeatで使用した場合の継ぎ目は保証しません。`maps` が `baseColor` だけなら法線・粗さ・高さの画像は含みません。`roughness` / `metalness` は元の材質に基づく球体表示用の数値です。

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

リリースには公開サイトZIP、全素材ZIP、モデル集ZIP、テクスチャ集ZIP、カタログJSON、SHA256SUMSを添付。GitHub Pagesは **Settings → Pages → Source: GitHub Actions** を使用し、`.github/workflows/publish.yml` が検証済みのAstroサイトを公開します。別のリポジトリへ複製した場合もこのSourceを選択してください。

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

## 出元・使用作品

任意の構造化 `usages[]` で制作元・再利用先、固定コミット、リポジトリ内パス、オブジェクト名を記録します。詳細ページに表示し、作品名・場所・識別子で検索できます。カタログ・NDJSON・個別JSON・通常ZIPの asset.json に含まれます。ライセンスの `provenance`、テクスチャ設定の `usage` とは別項目です。記入例と未知情報の扱いは [usage metadata](docs/USAGE_METADATA.md) を参照。
