# CardController29706 selected native UI

Stored original UI/assets only, plus existing static code evidence. Implementation/GPU parity and all special card branches remain separate.

`native_ui_chain.json` contains controller provenance/raw SHA/fields and selected34 nodes with full native GO/TRS/component fields: scene controller subtree, its cardPrefab subtree and cardParticle subtree. It also preserves ParticleSystem/Renderer/UIParticle on those selected nodes. `sprite_index.json` maps exact native Sprite keys to the12 cropped PNGs, with rect/pivot/border/atlas data and file/pixel/raw SHA in the main JSON. No name-only matching.

## Correct fields and values

`level2 GameRefManager#25745.cardController` local#29706; controller GO3126, root RectTransform19061.

| Field | IL2CPP offset | Stored value |
|---|---|---:|
| animateCardDelay |0x30|0.20000000298023224|
| cardPushingInterval |0x34|0.11999999731779099|
| cardFlippingInterval |0x38|0.11999999731779099|
| cardDoneScaleInTime |0x3C|0.20000000298023224|
| cardDoneScaleOutTime |0x40|0.10000000149011612|

**Correction to earlier FLOW/goal-fly notes:** +0x30 is animateCardDelay, not cardDoneScaleInTime. In OnRemoveCard0x1D2C380,0x1D2C530 loads+0x30 as ShowTick duration;0x1D2C594 loads+0x30 and0x1D2C5D4 adds literal0.2, then schedules DOVirtual.DelayedCall(ignoreTimeScale=true). Thus its stored delay is0.2+0.2=0.4seconds. Both fields happen to store0.2, but do not confuse their identities. Do not infer the scale-in/out fields are consumed at these particular call sites.

The previous documents were corrected in place, retaining an explicit correction note. Logical last-goal clear is still earlier than optional card animation completion; no new total animation gate was introduced.

## Exact prefab and particle refs

- `cardPrefab` scene file2#2100 -> **sharedassets2.assets GO2100**, Rect5312; GoalCard component **6753**.
- `cardParticle` scene file2#1583 -> **sharedassets2.assets GO1583**, Rect2899. This is a stored card FX reference; its existence alone does not establish every runtime spawn/activation condition.
- `_canvasGroup` local24502, canvas local17295; `cardGroup`GO2958; cardPlacementRect19061; cardAnchorsRect21134.
- Ordered placeholderCards RectIDs **18125,18090,18660,21797,19769,24383**, all level2/file0. Keep their native TRS rather than evenly spacing a guessed grid.

## GoalCard6753 fields and exact Sprites

- tick -> localImage6793 -> **file4 resources.assets Sprite2064 MBz_Check**,194x157, exactPNG`resources.assets_2064_sprite.png`.
- `_uiParticle` -> sharedassets2 local7231; original component/child PS data in the tree. Do not make this a generic world prop effect.
- back/hardBack/superBack -> sharedassets2 **798/720/676**.
- front/hardFront/superFront -> sharedassets2 **1288/874/912**.
- All six card-face PNGs252x309, with distinct native keys even where names are similar.
- anglePerRotate10; rotateInterval0.019999999552965164; moveDuration0.30000001192092896; iconScaleSize0.75. These are stored parameters, not proof of a new linear flip or reflow easing.
- Native tree includes sample bitmap number Sprite`7`; it is saved preview content, not a fixed quantity for gameplay. Goal UID icon and quantity remain runtime-driven.

## Existing code paths

- `end_flow_audit_20261015/disasm_01d2c380.txt`: OnRemoveCard/tick/.4-second delay.
- `disasm_01d2cf38.txt`: flip callback invokes GoalCard.DoFlip(needShowFront=false,backFlipTime0.5).
- `disasm_01d2d340.txt`: another flip callback invokes DoFlip(needShowFront=true,backFlipTime0.5).
- `disasm_01d2d078.txt`: on-removal callback, object cleanup and reflow branches.
- `code_audit_20261014/dump.cs`: GoalCard.ShowTick0x1E0332C,SelfMoveToPos0x1E0355C,DoFlip0x1E03754 declarations. Complete implementations of these methods were not newly decoded in this stored-data request; do not claim their full ease/rotation sequence from field names alone.

Validation:34nodes,12exactSprite PNGs,errors0; all PNG file SHA/dimensions/pixelSHA passed. `verification.json` contains native-chain SHA. Guard peak0.940GB/cap2.5GB/exit0. Original and product/physics source unchanged.
