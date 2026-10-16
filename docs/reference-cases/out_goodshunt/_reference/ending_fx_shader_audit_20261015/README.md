# Ending61 selected textures and shader

Original stored values and compiler text; not a pixel/GPU parity claim. Only resources.assets Shader1198, Material100/101 and Texture1141/842 selected from original data.unity3d.

- Shader1198: `DC/DoubleCats_common_RGB_shader4.0_urp`; raw SHA `3ebfe3639acd98c56e74cbe61bed3b36647c2354d581b2f3ee7706d60c11cb16`.
- `inventory.json`: four platform9 GLES3 compiler texts, verified entry bounds, length, keyword prefix and SHA. Forward entry2(noninstanced)/3(INSTANCING_ON); DepthOnly6/7. Original platforms9 and18 stored; platform18 not decoded here.
- `ending_fx/parsed_form.json`: full parsed properties/pass/program references.
- `materials.json`: exact Material100 Flash and101 light stored fields and raw SHA.
- `resources_assets_1141.png/json`: Flash1,512x512 RGBA, stored format51 and m_ColorSpace1. Raw SHA `662504b8570140d6bf9f407f33c0294cde15df8b326a12fcc5786563270a3405`.
- `resources_assets_842.png/json`: magic_orb 1,512x512 RGBA, stored format51 and m_ColorSpace1. Raw SHA `dbfc8f9b3b5a5ec6fc280896d5a2ccc4e96c15e34166c6d685230c7d4889ad76`.

PNG bytes/pixel SHA, sampler settings/mips/streaming fields retained in each JSON. PNG is UnityPy Texture2D.image decode, no resize/repaint or manually applied color transform. Stored color enum1 is Gamma/sRGB intent; PNG pixel bytes are not already proof of a linear shader sample. Match sampler color-space handling separately.

## Forward state and alpha

The actual Forward pass RT0 has fixed Blend One OneMinusSrcAlpha for both RGB and A, operation Add. It does **not** bind `_SrcBlend` or `_DstBlend` as state. zWrite binds case-sensitive `_Zwrite`, zTest binds `_Ztest`, cull binds `_Cull`.

Material100: `_blend=1`, `_Blend=0`, `_Zwrite=0`, `_ZWrite=0`, `_Ztest=0`, `_Cull=0`, `_SrcBlend=5`, `_DstBlend=10`; disabled passes DepthOnly/SHADOWCASTER.

Material101: `_blend=1`, `_Blend=0`, `_Zwrite=0`, `_ZWrite=1`, `_Ztest=0`, `_Cull=2`, `_SrcBlend=1`, `_DstBlend=0`; disabled passes empty.

**Property names are case sensitive.** Do not merge `_blend` with `_Blend` or `_Zwrite` with `_ZWrite` using a case-insensitive dictionary. Mat101's Forward depth write follows `_Zwrite=0`, not `_ZWrite=1`. `_Ztest=0` is the stored Disabled enum, not proof of LEqual. Native DepthOnly is a separate fixed depth-writing pass; UI pass selection remains separately unverified.

Forward fragment tail in entry2: `A=clamp(computedAlpha,0,1); output.rgb=A*computedRGB; output.a=A*_blend`. Thus `_blend` changes output alpha, not fixed blend state; when `_blend=0`, premultiplied RGB still contributes and destination attenuation vanishes. For these two stored materials `_blend=1`. Do not replace with an arbitrary additive or straight-alpha shader.

The body also consumes custom particle vertex streams, masks/distortion/dissolution and camera depth. Both materials store `_Distance=0`; preserve full compiler formula and clearly label any web depth-texture approximation. This handoff does not prove Canvas UIParticle selects the same runtime pass or supplies identical streams/depth.

Validation: four GLSL SHA/length/keyword prefixes and two decoded PNG dimensions/file/pixel SHA passed. Guard receipt `../ending_fx_shader_receipt.json`: exit0, peak commit0.807GB, cap2.5GB.
