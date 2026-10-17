# FBX配布移行レビュー（未公開）

ブランチ: `codex/fbx-distribution`。前回の文書コミットは
`82256c98897cd5238bcaa6fc146a5b607fe5ebdc`、前回の実装検証は `750764e`。
今回はユーザーの「旧URLは使えなくなってもいい」という変更に合わせ、旧Pages
ZIPの互換維持を終了します。mainへのマージ・Pages公開・既存Releaseの変更・
別配信リポジトリの作成は行っていません。

## 最新状態との照合

- `git fetch origin main` でmainが引き続き
  `7262f3e34559234de636cd5351d89fc733df008d`（stage10）であることを確認。
  前回からのmain差分はなく、取り込むClaude側の追加変更はありません。
- mainの最新検証run39037696325は成功。これはsource-only stage10であり、
  新素材のサイト公開を意味しません。
- 最新Releaseは `cohort-new251-v1.0.0`（ID415820647）、754添付、
  公開日時2026-10-17T13:57:23Z。サイト反映とは別です。
- 今回の検証対象は **original173 = 137モデル + 36テクスチャ**。
  new251とstage8〜10の30点は含めません。旧232候補は使用しません。

## 変更する公開物

- 旧 `full` / `models` ZIP **310個・532,070,717 bytes**をPagesの生成対象から
  外します。HTMLやredirectを同じZIP URLへ置くこともしません。
- APIの `schemaVersion` を **3.0.0**に更新。モデルは `downloads.delivery`、
  テクスチャは `downloads.minimal`。旧 `full/models/direct` とモデルの旧
  all-source `minimal` は公開しません。旧ZIPへのフォールバックもありません。
- `content/` の原本、GLBを含む既存プレビュー、テクスチャ画像、Git履歴、
  旧アーカイブのハッシュ台帳、既存Release添付は保持します。
  現行 `files[]` の原本/画像URLは提供を継続しますが、旧URL全般の互換保証はしません。
- サイトReleaseの生成物はサイトZIP・カタログ・チェックサム。
  旧ZIPを入れ子にするall/models/textures集は新規生成しません。
  既存Releaseのそれらの添付を削除する処理はありません。
- 通常モデルZIPは既存の検証済みFBX ZIPをそのまま再利用。
  一括ZIPは素材別フォルダー、FBXと必要テクスチャ、共通LICENSE一枚です。
  現在の137 FBXは画像埋め込み済み。外部依存FBXや追加cohortには別途検証済みadapterが必要です。

## 実容量

| 対象 | 全体dist bytes | 証拠 |
| --- | ---: | --- |
| 現行main `7262f3e` | 939,340,180 | [実ビルドbaseline](https://github.com/Xenoah/meshcopia/actions/runs/39041621871/job/117422108922) |
| 旧URL維持の前回FBX候補 `750764e` | 1,079,586,102 | [前回検証](https://github.com/Xenoah/meshcopia/actions/runs/39042655699/job/117425440168) |
| 今回の移行候補 | CIで計測して追記 | `measure-distribution.mjs` |

950,000,000 bytesの運用ゲートと1,000,000,000 bytesの上限は維持しています。
旧310 ZIPの除外量は固定台帳から算出した値であり、新しい全体distの実測値の
代用にはしません。`check-dist` と後続の移行検査も容量上限を検証します。

FBX単体の総量は599,103,132 bytes、通常FBX ZIP総量は572,507,759 bytesです。
旧通常モデルZIP総量181,983,181 bytesより大きく、FBX化自体が消費者の取得容量を
減らすとは主張しません。重複排除した同一サイトのchunk/manifestは前回実測
139,053,090 bytes。一括ZIPは無圧縮、最大50件、入力上限128 MiB
（モバイル/低メモリ時48 MiB）を維持します。

## 検証方法と現在の結果

専用ブランチのread-only CIで、必須の匿名Release検証から一度だけビルドし、
全137 FBXをその実出力から復元・ハッシュ照合します。全体テスト、現行リンク、
退役ZIPの実ファイル/参照の不在、単体/一括ZIP内容と実容量、FBX欠落、取消、
404後の再試行、戻る、選択解除、モバイル/no-JS、既存ビューアを検証します。
サイトReleaseのローカル生成も確認しますが、公開アクションはありません。

この移行の最終CI結果・実測容量は検証終了後に追記します。前回CIの成功した
機能試験を、今回のコードの検証結果として使い回しません。

候補サイトとchunkは、実ビルドのdistをブラウザー内で本番originへマウントして
検査します。Releaseへの実通信は置換しません。候補側の旧ZIP要求は404を検査し、
現行HTML/APIに旧ZIPリンクがないことを全件検査します。本番Pagesへの移行は
まだ実施していないため、本番の新chunk URLが取得できたという証拠ではありません。

[前回CORS診断](https://github.com/Xenoah/meshcopia/actions/runs/39042655699/job/117425440168)
ではRelease直接URL・API転送先の両方が本番originのfetchで失敗しました。
クリックによるダウンロードとは分け、ブラウザー一括取得は同一サイトのchunkを
使います。別ホストや第三者プロキシは導入しません。

## 公開前の残作業

1. 最新mainとClaudeの変更を再照合し、今回の正確なコミットのCIを親が確認。
2. mainへのマージ・デプロイは親の確認まで保留。source-onlyの公開状態と
   Release版番号の扱いも別途確認し、既存タグを上書きしません。
3. 公開後に実Pagesの現行カタログ、chunk、単体/一括ダウンロードを匿名取得して
   バイト/サイズ/ハッシュを確認。旧Pages ZIP URLの互換性は保証しません。
4. new251とその後の素材は別の対象範囲・adapter・容量検証として扱います。

実機Safari、FBXの新たなDCC/ゲームエンジンへの再インポートは未実施。
既存の検証済みFBXを同一バイトで再利用し、新しいインポート互換性は主張しません。

旧URL維持条件下の検証履歴・配信先比較は
[前回レポート](https://github.com/Xenoah/meshcopia/blob/82256c98897cd5238bcaa6fc146a5b607fe5ebdc/docs/FBX_DISTRIBUTION_REVIEW.md)
に保存されています。今回は旧URL移行が許可されたため、別配信先の選定は不要です。
