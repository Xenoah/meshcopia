# Existing-public-137 FBX verification / 公開済み137モデルのFBX検証

This workflow verifies additional FBX derivatives only. Original GLB/STL, metadata, all 310 historical archives, release configuration, and the main publishing workflow remain unchanged. No new model is made public by this branch.

この検証は公開済み137モデルの追加FBXのみを対象にします。元GLB/STL、メタデータ、既存310 ZIP、Release設定、main公開ワークフローは変更しません。このブランチで新規モデルを公開しません。

The primary future download is a complete eight-entry model ZIP. Embedded images are checked in a clean Blender import. This is Blender-to-Blender evidence, not Unity/Unreal certification. Split normals and UV data are retained; explicit tangent/binormal arrays are not exported. FBX Phong does not losslessly reproduce glTF metallic-roughness PBR. See the reviewed conversion notes and each report for material changes and tolerances.

将来の主ダウンロードはモデル単位の8ファイル入りZIPです。埋め込み画像をクリーンなBlender再読込で検証します。Unity/Unrealへの対応保証ではありません。法線・UVを保持しますが明示的な接線・従法線は出力しません。FBX PhongはglTFの金属度・粗さPBRを完全には再現しません。材質変更と許容差は変換ノート・各検証結果をご確認ください。

Expected byte hashes must be independently reviewed and finalized before running. Missing expectations stop before conversion. The seven approved public pilots run before all remaining models. Exact FBX and ZIP byte differences fail; there is no automatic acceptance. Frozen ZIP notices describe the reviewed local conversion, while a separate CI report records actual fresh-run measurements and hashes.

実行前に期待バイトハッシュの独立レビュー・確定が必要です。期待値が未確定なら変換前に停止します。公開済み7モデルの先行検証後に残りを処理します。FBX/ZIPバイトが異なる場合は失敗し、自動承認しません。ZIP内の固定ノートはレビュー済みローカル変換を記述し、CIの実測値・ハッシュは別レポートに記録します。
