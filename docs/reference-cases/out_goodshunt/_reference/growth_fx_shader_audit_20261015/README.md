# Growth FX shader evidence

Selected original shaders only. `inventory.json` contains native key/raw SHA, compiler segment/blob offsets, keyword tuples, lengths and SHA. Each label directory contains `parsed_form.json` and GLES3 compiler text. `pass_summary.json` preserves pass states and per-pass program references; do not select by shader name/keywords alone.

| Material | Shader native key | Actual particle pass |
|---|---|---|
| resources#79 Circles_AB | sharedassets0.assets#34 | SrcAlpha / OneMinusSrcAlpha, ZWriteOff, CullOff, RGB-only mask14, ZTest from `unity_GUIZTestMode` |
| resources#80 Circles_Additive | resources.assets#1244 | SrcAlpha / One, ZWriteOff, CullOff, RGB-only mask14, ZTest from `unity_GUIZTestMode` |
| sharedassets2#20 Drop_AB | unity_builtin_extra#10721 | SrcAlpha / OneMinusSrcAlpha, ZWriteOff, CullOff, RGBA mask15, fixed ZTest4 LEqual |

The first two are UI Extensions shaders and **do not have a fixed LEqual/Always ZTest in parsed state**; the UI runtime uniform supplies it. Their fragment formula is `2 * vertexColor * _TintColor * texture(_MainTex,uv)` (RGBA, not only RGB). Drop is `vertexColor * texture(_MainTex,uv)` with no extra2/Tint multiplier in its extracted fragment. Compiler variants are preserved rather than all collapsed to one.

First three shader text counts4/4/1. HolySmoke adds60 texts,69 total; all code length/SHA/keyword prefix checks passed. This does not mean69 unique materials/Forward variants or shader/pixel equivalence.

## HolySmoke #27

`holy_smoke_shader_identity.json`: sharedassets3.assets#27 HolySmoke_Soft -> owner external file4 resources.assets#1174 `Piloto Studio/UberFXSG`. Stored `_SURFACE_TYPE_TRANSPARENT` and `_USESOFTALPHA` combination:

- **Universal Forward uses blob8**, `holy_smoke/p9_s0_entry0008.glsl`.
- Same two compiler keywords also occur in blob21, but that maps to **DepthNormalsOnly**, not Forward. `pass_summary.json` confirms the pass association.
- Forward binds `_SrcBlend/_DstBlend/_ZTest/_ZWrite/_Cull`. Mat27 resolves to5/1/4/0/0: SrcAlpha/One, LEqual, ZWriteOff, CullOff. Different from Ending Shader1198's fixed One/OneMinusSrcAlpha.
- Forward body includes `_USESOFTALPHA` depth soft-fade and channel selection/detail noise. Do not replace it by a named additive sprite formula. Original matrix/depth/stream inputs and runtime fidelity remain unverified in the web renderer.

Texture join: `_MainTex` -> **sharedassets3.assets#48 SmokeHarsh256x256**, `_DetailNoise` -> **sharedassets3.assets#68 Packed_HolyDust256x256**, both file0 relative to the material owner, not resources.assets. These are **not** in the earlier16 Texture2D list. Exact selected PNGs and original fields/raw SHA/PNG/pixel SHA are in `holy_smoke_textures.json`; no resize/repaint/manual color conversion.

Guard peak0.786GB/cap2.5GB/exit0. Original, physics and implementation source unchanged. Renderer.enabled and module.enabled selection remain the implementation session's native data contract; do not turn null-sprite roots on to fill a visual gap.
