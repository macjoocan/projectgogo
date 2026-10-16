# Selected player growth FX assets

`chains.json` preserves source native raw SHA, complete Material fields, exact Texture2D fields (image payload omitted), Sprite fields including rect/pivot/atlas data, per-particle UVModule, native references and resolved file/pathID joins.

## Exact external joins

References originate in `sharedassets3.assets`:

| PPtr | Resolved material | MainTex | Shader resolved |
|---|---|---|---|
| file4#79 | resources.assets#79 Circles_AB | resources.assets#945 Shockwave 256x256 | sharedassets0.assets#34 UI Extensions/Particles/Alpha Blended |
| file4#80 | resources.assets#80 Circles_Additive | resources.assets#916 Circle02 256x256 | resources.assets#1244 UI Extensions/Particles/Additive |
| file6#20 | sharedassets2.assets#20 Drop_AB | sharedassets2.assets#529 drop 128x128 | unity_builtin_extra#10721 Mobile/Particles/Alpha Blended |

Material shaders are resolved by each owning file's external table, not by carrying the caller's fileID table forward. Shader identities/raw SHA are recorded; compiler/pass equations for these three shaders were not decoded in this handoff. `sharedassets3.assets#27` was intentionally not duplicated.

## UV sprite joins

Four selected subtrees: levelUp1520=6PS, growth1510=6PS, growthLoop1487=7PS, growthLoopEnd1578=7PS. Their UVModule fields and sprite list order are in `ps_uv_groups` and `joins`.

26 systems contain 13 unique referenced Sprites; both enabled and disabled module references were resolved and preserved. Root1520 and1510 have UVModule.enabled=false despite mode1 references. Do not apply those sprite lists solely because they are non-null. All other selected systems' module enabled states remain recorded rather than overridden.

13 Sprite PNGs are cropped via UnityPy Sprite.image without resize/repaint. 16 full Texture2D PNGs comprise the three material textures and exact Sprite backing textures. Filenames include source serialized_file/pathID and distinguish `_sprite.png` from `_texture.png`; native sprite rect/pivot/trim are not replaceable with texture dimensions. Texture format/colorSpace/filter/wrap/mips fields and PNG/pixel SHA remain in JSON. No manually applied sRGB/linear transform was added.

The original particle module/renderer full data and hierarchy remain in `../fx_existing_audit_20261015/existing_fx_records.json` and `../ingame_handoff_20261014/player_native_visual_physics_chain.json`. These assets alone do not prove event selection, runtime streams/particle simulation or GPU equivalence.

Validation: all29 PNG file SHA/dimensions and all16 Texture2D decoded pixel SHA passed; subtree counts reproduce6/6/7/7. Sequential guard peak commit0.833GB/cap2.5GB/exit0. Original and implementation source files unchanged.
