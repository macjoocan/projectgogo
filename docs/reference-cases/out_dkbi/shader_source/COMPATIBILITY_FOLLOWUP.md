DKBI TerrainLit compatibility follow-up, 2026-10-08

Status: original compiled shader reuse NOT solved. Derived review renderer remains valid work; do not mark original GPU fidelity or gameplay readiness.

Confirmed local reread:
 shader_compatibility_container_audit.json independently reads original 1.7MB terrain archive and successful Unity TextAsset control, sequentially. Both serializedVersion22, targetPlatform19, enableTypeTree=true. Original engine6000.3.24f1; current control6000.3.15f1. Original Shader native class48 (not130), path998575624410370492, type hash57f0dd2d4ef24437b4655529a673a936. Successful control has ONLY class142 AssetBundle and class49 TextAsset: it is not a Shader control.
 Audit tree_sha256 is this script's EndianBinaryWriter dump output; do NOT equate it to the adapter's canonical tree hash using a different serialization convention. Whole archive SHA matches preserved65796315aecc1feb528cc02a273be475af86c7ff5be8c82b063066925f6a788b.
 Guarded rerun succeeded, peak RSS82591744 bytes, commit cap1536MB. Initial dump_blob API mismatch failed explicitly (shader_compatibility_container.log); no initial success claimed.

Action-reported observations, bridge bmuzb1l8q-13 / bmuzb5wf4-15:
 NativeFormatImporter transforms native1,743,004B SHA8712c644... into derived YAML226,108B SHAd4b80ae2..., losing compressedBlob/platform/stageCounts. Shader supported=true initially was transient cache; reimport reports unsupported. Initial probe unchanged pre/post concerned already converted bytes, not original preservation. Do not label original loaded object a proxy without evidence.
 Five adapters preserve raw/program/blob/type hashes but fail actual AssetBundle compatibility guard before obtaining usable Shader. Version/metadata/outer flags/CAB-name rewrites already tried; do not repeat them as a proposed fix.
 Editor GraphicsAPI is Direct3D12. Original compilerPlatform4 D3D compiled data does not alone establish D3D11-only incompatibility. Treat changing GraphicsAPI as a separate downstream test, not an explanation of the present bundle guard.

Next bounded diagnostic, Action owns Unity execution:
 1. Build a minimal real Shader+Material AssetBundle with current6000.3.15f1, StandaloneWindows64, TypeTrees retained. Record shader class48 serialized tree fields/versions/flags/hash, engine/API, load result, isSupported and a small GPU render. Keep generated source explicitly CONTROL, not original.
 2. Unmodified UnityPy roundtrip that same Shader bundle. Record whole-file changes and raw per-object equivalence; test actual load and GPU again. Existing TextAsset roundtrip is insufficient. Failure here locates a serializer/control issue before involving original shader.
 3. Compare original class48 TypeTree to actual generated class48 tree by full field path/type/version/meta flags. Preserve every difference. Matching platform/version22/TypeTrees above does not establish Shader schema equality.
 4. Only if controls pass, use the successful control container for a minimal ORIGINAL dependency shader first, then TerrainLit with ordered original dependencies. Raw shader/program preservation must remain a hard condition. Do not make unsupported hash-only edits or overwrite Editor imported .asset files.
 5. If native original bundles load and yield an actual supported Shader, render+readback before equivalence claims. A D3D11 isolated test may then separate GPU backend behavior. Current project API must be recorded and restored, coordinated with user editor activity.
 Exact6000.3.24f1 is a possible later isolated compatibility test, NOT a guaranteed solution. Not installed here, no installation/project migration requested or performed this pass.

Parallel implementation route:
 Continue marked-derived review terrain shader from original47 properties, TexEnvs, passes and compiled instruction evidence. Do not stop geometry/material restoration while native reuse is blocked. Recover equations from retained bytecode where needed; label reconstructed HLSL derived, never recovered editable source. No exact appearance guarantee without original screenshot/GPU comparison.

Unchanged unknowns: input timing/units, nav/collision interpretation, LUT body/composition, runtime renderer activation. No new substitute gameplay rules.
