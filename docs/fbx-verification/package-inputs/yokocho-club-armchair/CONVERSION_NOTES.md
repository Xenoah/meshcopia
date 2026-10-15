# Meshcopia FBX / FBX 変換について

This FBX is an additional interchange download. The original GLB and STL remain unchanged. / この FBX は追加の交換形式です。元の GLB・STL は変更していません。

## Coordinates and geometry / 座標と形状
- Meters, Y-up, original origin and placement. FBX binary version 7.4, with UnitScaleFactor=100 (one file unit is one meter).
- 元モデルの寸法・原点・配置姿勢を保持。単位 m、Y-up。
- Static meshes only. No rigging, animation, simulation, collision setup or working mechanisms are added.
- 静的メッシュです。リグ・アニメーション・物理挙動・コリジョン・機械動作は追加していません。
- Mesh triangles, split normals, UVs and material assignments are checked after clean FBX reimport in Blender 4.3.2. Explicit tangent/binormal arrays are not stored; the receiving application must calculate tangents from the normals and UVs.
- Blender 4.3.2 の新規シーンへの再読込で形状・法線・UV・材質割当を確認。接線は保存せず、読み込み先で法線・UV から再計算します。

## Materials / 材質
- Embedded PNG/JPEG images are included in the FBX; the verified Blender import needs no external texture files. Other importers may require their normal “extract embedded media/textures” operation.
- テクスチャ画像は FBX に内蔵。読み込み先によっては通常の画像抽出操作が必要です。
- FBX Phong materials are not lossless glTF metallic/roughness PBR. Lighting and shader appearance can differ. Roughness is carried using Blender's FBX shininess convention; other applications may need the embedded grayscale roughness map reconnected as linear data. Normal maps are linear/non-color data.
- FBX と glTF PBR は同一ではありません。光沢・金属感・照明による見え方が変わる場合があります。粗さ画像・法線画像はリニアデータとして設定してください。
- Base-color and emission tints are baked into derived images where necessary. Mirrored-repeat images are expanded to a 2×2 mirrored image with half-scale texture coordinates. These changes do not move mesh vertices.
- 必要に応じて色係数を画像へ焼き込み、ミラー反復を派生画像と座標スケールで保持しています。頂点位置は変更していません。
- The street tree uses a derived primary UV color atlas for leaf vertex colors and retains the original UVs as a second layer. Two colored bottle-display models use material color variants. Original editable vertex colors remain as linear floating-point FBX attributes; choose LINEAR color import if editing those attributes. Basic rendered colors do not require a custom vertex-color shader.
- 街路樹は葉の色を派生 UV 画像へ保持し、元 UV も第2レイヤーに残しています。ボトル棚2点は材質色を分割。元頂点色はリニア値で保持し、通常の見た目の復元に専用頂点色シェーダーは不要です。
- AO is not mapped to a portable FBX material channel. The unchanged source GLB retains the original AO data. FBX export uses CullingOff, so originally single-sided materials may need backface-culling settings reapplied in the receiving application.
- AO と片面カリングは完全互換ではありません。必要な設定は元 GLB を参照し、読み込み先で調整してください。
- Where a source material uses physical transmission/IOR, an explicitly recorded alpha approximation may be used. This is not equivalent optical refraction. Refer to the per-model conversion report for the actual settings.
- 元材質に物理的な透過・屈折率がある場合、明記した透過度で近似することがあります。物理的に同じ屈折ではありません。実際の設定は個別の変換記録を参照してください。

## Validation limits / 確認範囲
- Blender-to-Blender interchange QA only. Unity, Unreal, VRChat and other engines have not been tested. No engineering, safety, medical, printability or real-device certification is implied.
- Blender 間の交換確認であり、Unity・Unreal・VRChat 等での実機検証済みという意味ではありません。実用品の設計・安全性能・医療用途・印刷適性の認証ではありません。
- Refer to this model's individual description for purpose, placement, dimensions and any model-specific limitations.
- 用途・配置・寸法・固有の制約は個別モデル説明を参照してください。

## Attribution / クレジット
Original Meshcopia asset by Xenoah. FBX conversion and compatibility derivatives retain the original CC BY 4.0 license. Attribute Xenoah / Meshcopia, link https://github.com/Xenoah/meshcopia and https://creativecommons.org/licenses/by/4.0/ , and indicate that the file was converted to FBX with material/texture adaptations.
