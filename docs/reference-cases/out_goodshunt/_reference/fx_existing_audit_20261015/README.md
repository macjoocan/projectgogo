# Existing FX records handoff

Existing extraction records only; no new APK/native extraction, implementation change, PNG name matching, or GPU parity test.

`existing_fx_records.json` contains selected original fields, PPtrs and original record SHA/source ZIP paths:

- UI: 144 nodes with 111 ParticleSystem and 111 ParticleSystemRenderer records, across the existing six result UI roots, **not 111 Ending61 systems**. Also preserves UIParticle components and transforms on those nodes. Full ancestors remain in `../end_flow_audit_20261015/ui_native_nodes.json` (922 nodes).
- Player: 138 ParticleSystem / 138 ParticleSystemRenderer and PlayerFxComponent records whose GameObjects are in the previously extracted player subtree. Full hierarchy and ancestors remain in `../ingame_handoff_20261014/player_native_visual_physics_chain.json`. That earlier file intentionally excluded ParticleSystem components; do not treat it alone as a full FX export.
- 16 local Material records selected from ParticleSystemRenderer.m_Materials. These are a partial local-file join, not a complete external-reference/texture-resolution result.

## Ending61

Actual `level2` StateLevelCompleteTransition#30984.fireworkFx -> UIParticle#26477 at `/EndingTransition/Panel/EndgameFX/UIParticle` (GO375).

Stored UIParticle scale3D=(40,40,40), ignoreCanvasScaler=false, absoluteMode=false, positionMode=0, autoScaling=false, autoScalingMode=0, resetScaleOnEnable=false. Its 16 ordered ParticleSystem PPtrs:

`10043,9902,9995,9987,9931,9858,9309,9449,9921,9366,9760,9698,9845,9465,10186,9506` (all file0 level2).

Do not replace these IDs with resources.assets#17276: that is the separate saved ID60 variant. Existing FLOW.md and disasm_01d98890.txt establish the .5-second callback enabling the GO and calling UIParticle.Play.

## Player growth and other FX

sharedassets3.assets PlayerComponent#1893.playerFxComponent -> PlayerFxComponent#1895:

| Field | ParticleSystem pathID (file0) |
|---|---:|
| levelUpFx | 1520 |
| growthFx | 1510 |
| growthLoop | 1487 |
| growthLoopEnd | 1578 |
| bombFx | 1597 |
| freezeFx | 1552 |
| magnetFx | 1568 |
| lightning | 1580 |
| levelCompleted | 1570 |
| finalLevelComplete | 1539 |
| ghostEaten | 1556 |

These are saved references, not proof that normal prop eating plays any one of these particles. LevelBehavior.OnEffect and card-removal paths must retain their separate existing code evidence. Do not label ghostEaten as normal fruit eating from its name.

## Exact material / texture route and remaining gap

ParticleSystemRenderer.m_GameObject joins the same-file GameObject/Transform chain. Renderer.m_Materials and ParticleSystem UVModule/TextureSheetAnimation sprite references are both relevant; a textureless Material does not establish an untextured effect. Local material fields are packaged here; original per-record JSON lives in `results/GoodsHunt_structured_objects.zip`, with `results/native_object_index.jsonl` giving source / serialized_file / path_id / json_file / raw SHA. Native raw records remain in `results/GoodsHunt_native_raw.zip`.

For nonzero fileID, resolve the owning SerializedFile's externals before joining pathID. Sprite then uses its native texture/atlas PPtr; material uses native m_TexEnvs. Existing PNGs are not guaranteed exact by name: **no new exact texture-PPtr-to-PNG audit was performed here**. The Sprite1387 128-vs188 collision is precisely why this boundary matters. Further bounded texture joins should start from these native references rather than matching names.
