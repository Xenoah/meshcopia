# Meshcopia

**人間とAIエージェントのための、無料3Dモデルとテクスチャ。**

[素材ライブラリ](https://xenoah.github.io/meshcopia/) · [Releases](https://github.com/Xenoah/meshcopia/releases) · [エージェント向けJSON](https://xenoah.github.io/meshcopia/api/catalog.json)

![Meshcopia library](https://github.com/Xenoah/meshcopia/releases/download/v1.3.0/desktop-catalog-full.png)

> **公開中**: [Meshcopia](https://xenoah.github.io/meshcopia/) · [正式版 v1.11.0](https://github.com/Xenoah/meshcopia/releases/tag/v1.11.0)。合計454素材（3Dモデル418点とテクスチャ36点）を無料で取得できます。

## できること

- 大きなサムネイル、名前・タグ・形式検索、カテゴリー、種類、並び替え。検索条件はURLで共有。
- 一覧からクイック3Dプレビュー。詳細で回転・拡大・ワイヤー・ライティング・材質を切替。
- GLB / glTF / STL / OBJ / STEPの元形式をプレビュー。Three.js / occt-import-js。FBXは配布用で、今回のブラウザ検証対象は表示ではなくリンクと実ダウンロード。
- 通常・鏡像リピートの1×1・2×2・4×4確認と球体表示。アトラスは非タイル素材として元の縦横比で表示。
- 通常のモデルZIPはFBX・必要テクスチャ・短い `LICENSE.txt` 1枚。一括ZIPは素材別フォルダーと共通LICENSE 1枚。テクスチャ単体作品の画像ダウンロードも維持。
- 既存137モデルと新作281モデルの検証済みFBX ZIPを通常取得に再利用。GLBはプレビュー、制作原本とQAは別に保持。FBXの材質・透過・裏面カリングは読み込み先により異なる場合があり、UnityやGodotで同じ見た目になるとは保証していません。
- 全素材 **CC BY 4.0**。商用利用・改変・再配布可。作者名・出典・ライセンス・変更点の表示が必要。
- 認証不要のJSON/NDJSONカタログ、個別マニフェスト、SHA-256、クレジットコピー。
- モバイル対応、キーボード操作、検索ショートカット `/`、JP/EN切替（素材と主要UI）。

### 素材制作・ダウンロードの共通ルール

新しい素材の形式・品質検証・ZIP構成は [共通制作ルール](docs/ASSET_PRODUCTION_RULES.md) に従います。利用者向けモデルZIPはFBXと必要テクスチャ、クレジットをまとめた短い `LICENSE.txt` 1ファイルのみ。既存Releaseは変更しません。旧Pagesのfull/models ZIPは生成を終了し、旧URLの互換性は保証しません。制作原本・履歴・過去のハッシュ台帳を保持します。現行取得先は [配布契約](docs/MINIMAL_DOWNLOADS.md) を参照。

> 既存173点の配布移行時は546,137,684 bytes。新作追加後も実ビルド全体の950MB容量ゲートと公開後の実Pages検査を必須にします。新作251点と追加30点は独立した検証証跡で反映します。新作サムネイルと追加STL原本は固定GitHub URLで提供し、GLBと選択取得チャンクをPagesに保持します。[新作反映の検証記録](docs/NEW_ASSETS_ACTIVATION.md)。

## 収録素材

**街路オリジナル12モデル（v1.4）**: ボラード、自転車ラック、歩道柵、段差スロープ、減速クッション、注水バリア、ごみ箱、分別ステーション、飲水台、宅配ロッカー、パーキングメーター、消火栓。実メッシュ画像、GLB/STL、原寸・三角形数・出元情報付き。小さな金具や滑り止めの分割数を調整し、シルエットと使いやすい軽さを両立。[制作・検証・制限](docs/CITY_ASSETS.md)。

**TreeTop Yokochoオリジナル60点（v1.3）**: 立体看板、椅子・テーブルセット、カウンター、棚、照明、能舞台、階段、設備、入口広場の家具など39モデル。元画像を保持した21テクスチャ（Mirror 9点、Clamp 12点）。外部スキャン画像は除外し、該当材質の置換を各モデルに明示。実メッシュのサムネイル、出元のオブジェクト名、SHA256、正確な三角形数・寸法を収録。[選定・出典・制限](docs/YOKOCHO_IMPORT.md)。

**Commons cafeオリジナル12点**: バースツール、ラウンジチェア、ソファ、丸テーブル、ペンダントライト、コーヒーカップ、観葉植物、エスプレッソマシン、グラインダー、PAスピーカー、DJコントローラー、展示台。[元ワールド](https://github.com/Xenoah/vrcworld_tech-tech-cafe)から独立したGLB/STLとして抽出。元の生成テクスチャ、UV、鏡像反復・Clamp設定を保持しています。[選定根拠・出典・再現手順](docs/COMMONS_IMPORT.md)。

**Commons cafe追加メッシュ12点（v1.2）**: ローテーブル、円形ステージ、機材ラック、ワークカウンター、コーヒー袋、ボトル6本セット、本6冊セット、テーブルキャンドル、リング照明、ポスターフレーム、スラットバーカウンター、壁付け本棚。

**Commons cafeテクスチャ9点（v1.2）**: オーク・漆喰・テラゾー・黒皮鋼・真鍮・織布は1254pxの鏡像リピート用ベースカラー。機材操作面・瓶ラベル・小物プリントは非タイルのアトラス。9点とも元PNGを無加工で配布し、元の出典とSHA-256を保持。

**3Dモデル8点**: スタジオチェア、アトリエランプ、ウッドスラットベンチ、テラコッタプランター、マーケット木箱、ガーデンアーチ、フィールドターミナル、ラウンドサイン。

**通常リピートのテクスチャ6点**: ライムストーン、シダーボード、クレイブリック、セージテラゾー、ヘアラインアルミ、コバルトセラミック。各1024px / Base Color・Normal・Roughness・Height。

初期8モデル・6テクスチャはMeshcopiaのオリジナルのプロシージャル素材です。Commons cafeの追加素材は元ワールドのオリジナル形状と生成画像を使用。サムネイルは実際の配布メッシュから描画しています。

保持している制作原本: 単位m、Y-up。初期モデルはGLB/OBJ/STL、Commons cafe素材はGLB/STL。配布モデルの基本形式はFBXです。GLBには色・PBR材質を保持し、Commons cafe素材は画像も埋め込んでいます。OBJにはMTLを同梱。STLは色を持ちません。UVの仕様は各素材に記載しています。ゲーム・VR向けの小道具で、3Dプリントや機構部品としては未検証です。

## テクスチャとAPIの反復方式

カタログの `schemaVersion` は **3.0.0**。モデルは `downloads.delivery`、テクスチャは `downloads.minimal` を使用します。`downloads.full` / `models` / `direct` とモデルの旧 `minimal` は公開APIから除外しました。`files[]` は制作原本・プレビュー用、モデルの配布ファイルは `downloads.delivery.files` です。`width` / `height` は実ピクセル寸法、`resolution` は長辺です。`wrapMode` を両軸に適用します。

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
python3 scripts/prepare-fbx-minimal-activation.py --repo "$PWD" --verification-mode durable-transport-attestation
python3 scripts/prepare-cohort-activation.py --repo "$PWD"
npm run check
```

既定のURLパスは `/meshcopia/`。ルート配信には `PUBLIC_BASE_PATH=''`、独自ドメインには `PUBLIC_SITE` を指定してビルドします。プレビューは通常 `http://localhost:4321/meshcopia/`。

## 素材を追加

```sh
npm run new:asset -- my-chair model
# _inbox/my-chair/asset.json、preview.webp、source/ を記入・追加
npm run import:inbox -- my-chair          # 検証のみ
npm run import:inbox -- my-chair --apply  # content/assets/ へ移動
# 素材をdraftで保存・コミットし、検証済み配布の承認後に公開対象へ追加
# 上記の二つの事前検証を、このコミットに対して実行してからチェック
npm run check
git add .
git commit -m "feat(assets): add my-chair"
git push origin main
```

新しい公開素材には、原本・バージョンに結び付いたFBX/テクスチャ配布の検証と、明示的な公開台帳への追加が必要です。draftの保存だけでは公開されません。

`_inbox/**` へのpushでもActionsが自動で取り込みます。既存IDは上書きしません。更新は `content/assets/<id>/` を直接変更し、versionとupdatedを更新します。`draft` は配信物に含めません。`hidden` は一覧から除外するだけで非公開ではありません。

詳細は [AGENTS.md](AGENTS.md)、[CONTRIBUTING.md](CONTRIBUTING.md)、[asset schema](docs/asset-schema.json) を参照。

## ビルドとリリース

`npm run build` が素材検証、配布manifest・共有chunk・JSON生成、Astro静的ビルドを行います。`npm run check` はその前後に現行URL・ハッシュ・旧ZIP除外・全体容量を検証します。mainへのpushでCIが動作し、公開条件が成立した場合にPagesへ進みます。`.release.json` のversionを変更すると、成功した検証後に対応するGitHub Releaseを作成します。同一タグは作り直しません。

今後のサイトReleaseには公開サイトZIP、カタログJSON、SHA256SUMSを添付。単体FBX/テクスチャZIPは検証済みの既存Releaseを使い、選択素材はブラウザーで一つのZIPにします。旧ZIPを入れ子にするall/models/textures集は新規生成しません。既存Releaseの添付は残します。GitHub Pagesは **Settings → Pages → Source: GitHub Actions** を使用し、`.github/workflows/publish.yml` が検証済みのAstroサイトを公開します。

## 素材の再生成

現在のビルドにはPython 3と匿名Release検証が必要です。オリジナルの生成コードを再実行する場合のみ:

```sh
python3 -m pip install -r scripts/requirements-assets.txt
python3 scripts/create-starter-assets.py
npm run check
```

## 継承とライセンス

[Xenoah/archive-3dmodels](https://github.com/Xenoah/archive-3dmodels) のAstro・Three.jsビューアとフォルダー投入→カタログ→ZIPの設計を継承。ビューア、ZIP writerは参照コミット `7d52500c361200884d56e8361757953474dfdb68` を基礎に改修。CC BY-NCの旧モデル、解析タグ、旧サイトの設定は移植していません。

本リポジトリのオリジナル素材・実装は [CC BY 4.0](LICENSE)。依存ライブラリはそれぞれのライセンスが適用されます。[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照。

## 出元・使用作品

任意の構造化 `usages[]` で制作元・再利用先、固定コミット、リポジトリ内パス、オブジェクト名を記録します。詳細ページに表示し、作品名・場所・識別子で検索できます。カタログ・NDJSON・個別JSONに含まれます。既存Releaseや履歴にある従来版ZIPの `asset.json` は保持しますが、現行の配布ZIPにメタデータファイルは追加しません。ライセンスの `provenance`、テクスチャ設定の `usage` とは別項目です。記入例と未知情報の扱いは [usage metadata](docs/USAGE_METADATA.md) を参照。
## 未公開の修正候補

初期モデル2点の面向き修正と家庭用冷蔵庫の候補は、公開カタログから分離して
[`asset-revisions/`](asset-revisions/) に保持しています。既存の前開き洗濯機、
車両、その他の公開素材は保持します。検証方法と公開前の残作業は
[修正候補のレビュー手順](docs/ASSET_REVISION_REVIEW.md)を参照してください。
このブランチへの追加はサイトへの掲載を意味しません。
