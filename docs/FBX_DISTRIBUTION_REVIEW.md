# FBX distribution candidate (not deployed)

Base: `7262f3e34559234de636cd5351d89fc733df008d` (stage10).
Implementation branch: `codex/fbx-distribution`. Main, Pages and existing Releases
are not changed by this branch's read-only workflow.

## Scope and measured constraints

- Site activation remains original173: 137 models and 36 standalone textures.
- new251 F run39035757342 and transfer39036941196 were both successful when
  rechecked. Release `cohort-new251-v1.0.0` has754 public attachments. This is
  separate from site activation. The 30 source-only stage8–10 additions are not
  covered by that251. No old232 candidate is used.
- Baseline full Astro build: **939,340,180 bytes / 1,197 files**, measured from
  actual `dist/` in [baseline job117422108922](https://github.com/Xenoah/meshcopia/actions/runs/39041621871/job/117422108922).
  Remaining operational headroom: **10,659,820 bytes** below950,000,000.
- Verified existing FBX payload total: **599,103,132 bytes**. Existing immutable
  FBX ZIP total: **572,507,759 bytes**. Reusing those ZIP URLs avoids making
  duplicate consumer archives; original full/models archives remain unchanged.
- Old ordinary minimal model ZIPs total **181,983,181 bytes**, while the reused
  FBX ZIPs total **572,507,759 bytes**. FBX selection is a format-policy change,
  not a claim that individual downloads become smaller. The original model
  payload inventory was **260,812,913 bytes**, versus **599,103,132 FBX bytes**.
- Content-defined gzip chunks reduce the extra FBX payload storage to roughly
  **138.4 MB**, or **139,053,090 bytes including manifests**. Compared with copying
  all599,103,132 payload bytes, this saves460,050,042 bytes (about76.8%).
  This is deduplicated extra transport storage, not smaller consumer FBX files.
- Final complete candidate `dist/`: **1,079,586,102 bytes / 2,172 files**;
  **140,245,922 bytes more than main** and **129,586,102 bytes above** the
  operational950,000,000-byte limit. This also exceeds the1,000,000,000-byte
  hard budget. Both budget assertions fail; they have not been relaxed.
- Actual browser fetch from the live Pages origin failed for both the direct
  Release URL and the API's redirected binary in
  [CI39042567048](https://github.com/Xenoah/meshcopia/actions/runs/39042567048/job/117424827052):
  both responses lacked `Access-Control-Allow-Origin`. Another attempt returned
  HTTP403 from the API; that response is not labeled a CORS failure. Click-based
  anonymous ZIP downloads passed separately. The shipped batch builder never
  fetches a Release URL or assumes its CORS.

## Implementation and verification

`downloads.delivery` binds ordinary FBX ZIPs and exact batch payloads to the
existing successful source/version-bound verification. Root `files`, previewUrl,
legacy ZIP fields and archive lock remain compatible. Textures keep their image
downloads. A missing/stale FBX disables model delivery and shows unknown size.

Batch transport reconstructs unchanged FBX from same-site gzip chunks; no new
export or importer claim is made. Final ZIP is uncompressed STORE with one model
folder per selection and one exact combined LICENSE. Size estimates include ZIP
headers and UTF-8 names, and the finished UI uses actual Blob.size.

The read-only workflow runs mandatory anonymous prep, all unit tests, build,
check-dist reconstruction of every FBX, actual single/selected browser ZIPs,
cancel/retry/Back/remove/clear/mobile/no-JS and viewer/texture regressions. Its
final capacity gate must remain blocking. Results are recorded in CI artifacts;
fixture tests do not establish publication or live-site availability.

## 検証対象と証拠

実装の検証対象は `750764efce5d5edefb4c65f856ce1945261535c0`。
最終結果の追記は文書だけの変更で、実装・設定・テストを変更しません。
[最終検証ジョブ（run39042655699、attempt2）](https://github.com/Xenoah/meshcopia/actions/runs/39042655699/job/117425440168)
で次を確認しています。

- 固定Node 22.23.3で177テスト成功。クラウド環境でも同じ最終コードの
  `npm test` が177/177成功しています。
- 必須の匿名FBX Release検証、`npm run check`、全137 FBXの実ビルドからの
  復元・バイト/ハッシュ照合が成功。
- FBX欠落・不正manifest・中断・404後の再試行をローカルfixtureで確認。
  fixtureは本番公開の証明とは分けています。
- 実生成ページ173件のリンク、3件の実Release ZIP、デスクトップ/モバイルの
  実データによる複数選択ZIP、その内容・実サイズ・取消・再試行・戻る・
  選択解除が成功。モデルはFBX、テクスチャ作品は画像、共通LICENSEは1枚。
- 137モデルのFBXリンク、6件の実ブラウザーダウンロード、モバイル/no-JSが成功。
- 既存GLB/STL/OBJプレビュー、表示設定、検索・絞り込み・ダイアログ再利用、
  repeat/mirror/clampテクスチャ、元PNG取得、球表示、言語切替と
  デスクトップ/モバイル表示が成功。
- 旧API175件の互換投影と固定ZIP310件の台帳・内容が一致。
  容量判定は2箇所とも同じ1,079,586,102 bytesで失敗しています。

**CI全体の結果はfailureです。残る失敗は容量超過のみです。**
初回attempt1はAPI403を伴うprep失敗で、検証済み結果として使っていません。
上記は全機能試験を通過したattempt2の結果です。
[最終artifact12105570025](https://github.com/Xenoah/meshcopia/actions/runs/39042655699/artifacts/12105570025)
には実ダウンロードZIP、スクリーンショット、サイズ・互換性・CORS・ブラウザー
試験のJSONを保存しています（SHA-256:
`37b4ef901ca6b4f7c504d356e53ffd865db935cda881a1652df54694d03d8d5d`）。

候補サイトとchunkは実ビルドの `dist/` をブラウザー内で本番originにマウント
して試験しています。Releaseへの要求は置換せず実通信しています。この区別は
artifactの `canonicalOriginRemount` / `liveSite` に記録し、未公開のchunk URLが
実際のPagesで取得できたという証拠にはしていません。

未実施: 選定前の新配信先への公開・本番originでの実バイト取得、公開後の
本番サイト試験、実機Safari、FBXの新たなDCC/ゲームエンジンへの再インポート。
既存の検証済みFBXを同一バイトで再利用しており、新しいFBXレンダリングや
インポート互換性の検証を行ったとは主張しません。
一括ZIPは無圧縮で、最大50件、入力上限は通常128 MiB・モバイル/低メモリ時48 MiBを
維持しています。実機モバイル全機種のメモリ耐性を保証する試験ではありません。

## Required before publication

1. Review the candidate and its exact final CI evidence. No automatic merge or
   deploy is requested by this change.
2. Resolve payload hosting: current Pages cannot retain every legacy URL and
   accommodate all new FBX data, even after deduplication. Use a separately
   reviewed immutable host with actual browser CORS and byte readback, or an
   approved capacity/URL migration. Do not disable the budget, overwrite Releases,
   delete originals or silently disable large-model downloads to pass it.
3. Bind that actual transport, rerun complete size and real browser checks, then
   obtain publication authorization. No guessed hostname or future-success flag
   is included here.
4. Integrate new251 only via its own reviewed adapter and capacity plan after
   reconciling Claude's latest main. No new251 or stage8–10 publication is claimed.

Local cloud network access blocks GitHub API and live Pages requests. Full real
release and browser verification therefore runs in read-only GitHub Actions.
The cloud workspace still runs source, unit and local browser fixture tests.

## 配信先の選択肢（2026-10-17確認、作成・契約・公開なし）

| 選択肢 | 費用と制限 | 互換性・CORSの確認状態 |
| --- | --- | --- |
| 同じXenoahアカウントの別プロジェクトPagesに配信データを分離 | 公開repoのPagesはGitHub Freeで利用可能。1サイト1GB・月100GBの帯域ソフト上限が残る。新repo/Pages設定と容量管理が必要 | 標準URLなら同じ `https://xenoah.github.io` originなので別パスへのfetchにCORSは不要、という設計上の判断。新しい実URL・バイト・ブラウザGETは未検証。元サイトの旧URLは維持できるがnew251を含めた長期容量は別途要計測 |
| Cloudflare R2 Standard等のオブジェクト配信 | R2は月10GB保存、100万Class A、1,000万Class Bが無料枠。超過は$0.015/GB月、$4.50/100万A、$0.36/100万B、外向き転送料なし。既存利用と合算・端数切上げ。独自ドメイン費用・契約条件は未確認 | `AllowedOrigins: https://xenoah.github.io` とGETを設定可能なことを公式文書で確認。実バケットのCORSは未検証。本番は独自ドメインを使い、開発用r2.devを本番配信先にしない。旧URLは元サイトに残す |
| 旧ZIP URLを移行して元サイトを縮小 | 配信先により費用が変わり未見積り | 現在の旧URL保持条件に適合しないため未実施。HTMLリダイレクトをZIP URLに置く方式は、保存済みURLのバイト/ハッシュ互換を壊すため不可 |

現在の条件では、旧URLを保持し、新しい配信データだけを別サイト/ホストへ
置く案が検討対象です。選定後には実URLを固定し、同一バイトの匿名readback、
本番originからのGET、取消・再試行・モバイル、全体容量を再検証します。
このブランチに架空の配信先や外部ホスト許可のバイパスは追加していません。

費用・仕様の一次資料:
[GitHub Pages利用条件・標準URL](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)、
[Pages容量・帯域上限](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)、
[R2料金](https://developers.cloudflare.com/r2/pricing/)、
[R2 CORS](https://developers.cloudflare.com/r2/buckets/cors/)、
[R2本番ドメインと開発URL](https://developers.cloudflare.com/r2/buckets/public-buckets/)。
