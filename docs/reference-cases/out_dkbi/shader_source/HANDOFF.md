Terrain/custom shader source availability audit, 2026-10-08

Scope: existing source installation file names, Addressables internal IDs, streamed TextAsset/Shader indices and Action's native TerrainLit report. No full shader/texture extraction and no Unity Editor load attempt here.

Results:
-24640 original installed files checked for .shader/.shadergraph/.shadersubgraph/.hlsl/.cginc/.compute suffixes:0 actual source files found.
-2657 indexed TextAsset rows checked for source-style name leads:0 found. This is a name scan, not exhaustive binary payload text scanning.
-Catalog source-style IDs2: Assets/AddressableResources/ui/shader/ui_automaticallyuseditem.shader and ui_incisiveitem.shader. These are logical IDs, not verified editable source payloads; no TerrainLit source-style ID found.
-Shader index430 rows all have blank names. Thus zero custom-shader NAME matches has no absence significance. Exact TerrainLit pathID998575624410370492 finds one preserved raw row.

Terrain native source:
bundle_key c837fa78dcf63c7e_25f33c4faf67b7e10e7411fad9fab6fd
serialized_file25f33c4faf67b7e10e7411fad9fab6fd
pathID998575624410370492, raw pack offset0, raw bytes1666636
SHA2568f1de53774528894dfa0daa75c303e937ef749c73b475e28ff4e3a5fb2a70c55
Existing Action field_material_reconstruction_evidence.json verifies SUPERCAT/Dokkaebi/TerrainLit baked native Shader, platform4 D3D11, compressed program blob1614745B, SHA4c67f81a730c15f9554e6dc0d22a28aafd323ce96bd67c15f4fadcdf81a79892. Parsed passes/properties/keywords are already in that report. This is compiled data preservation, not original HLSL/ShaderGraph recovery.

Editor reuse boundary:
No original Editor project/source .meta GUID topology discovered by this scoped scan. Exact isolated serialized-file native import/load/render test remains Action ownership. UnityFS header/rawShader/DXBC existence alone proves none of AssetDatabase import, dependency resolution, GPU execution or pixel equivalence. Keep these checks separate. Failed direct import would not mean compiled shader mathematical behavior is unavailable, but any reconstruction from bytecode is derived code, not recovered original editable source.

Other requested findings:
No new original input/move/attack timing units, collision/nav shape decoder or PC LUT MergeLUTs body/RVA recovered this pass. Existing field/graph/metadata and349 raw collider candidates are unchanged; do not fill gaps with assumptions described as original.

Evidence JSON: shader_source_availability.json; historical Action report timestamp retained and obsolete project-readiness statements not copied as current facts. Peak RSS37,449,728B, cap1536MB, sequential bounded process. Source/install/project unchanged.
