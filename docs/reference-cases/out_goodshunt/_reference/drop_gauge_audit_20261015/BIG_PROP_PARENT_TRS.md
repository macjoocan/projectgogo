# 큰 과일 부모 계층 — 2026-10-15

reply-to bmv8vrx1o-a / bmv8vu9ph-b. [원작값] `big_prop_parent_chains.json`은 props 번들 하나에서 이름 후보 6개, 원문 부모 PPtr로 묶인 루트 3개를 읽었다. UID/Level006 배정은 상대 매핑과 별개다. 좌표 변환이나 크기 정규화 없음. 모든 원문 TRS, Collider, Rigidbody와 raw SHA를 JSON에 보존했다. 실행 peak commit 0.124GB, exit 0.

- Kiwano: root scale 1 → HEA_Fru_Kiwano_01 scale 12.2322540283, position (-0.11,2.662400007,0), quaternion (0,1,0,0) → Collider scale 0.98591810465, position (-0.0089926198,-0.2176540941,0), quaternion (0,-1,0,0). Capsule radius 0.1816209406, height 0.4439807236, direction 1, center (0.0011429859,0.2219903618,-0.0008929488).
- Mango_Red: root scale 1 → HEA_Fru_Mango_Red_224 scale 6.0366840363, position (0,2.8499999046,0.000000094484), identity rotation → Collider identity TRS. Capsule radius 0.31008452, height 0.79785091, center.y -0.06446493417; exact full values in JSON.
- Starfruit: root scale 1 → Collider identity position/rotation, scale 9. MeshCollider convex=true, cookingOptions=16, local fileID 0/pathID 5216257869460497083. Collider is a sibling of visual HEA_Fru_Starfruit_01 (scale 8.5), not its child; do not multiply 8.5 into collider scale 9.

Kiwano/Mango capsules inherit their visual-parent scales. Applying collider-node scale alone loses those factors. Original placement scale 0.8 is a separate root-level runtime input, not baked into these stored values.

[원작 코드 판독] Existing `code_audit_20261014/PROP_ACTIVATION.md`: Init 0x21E1B60 caches original scale/mass/drag/bounds and calls ResetTransform; ResetTransform 0x21E22E8 restores placement/original scale and collider enabled/material/Rigidbody state. Generic scaling operations are documented separately in BIG_PROP_SHRINK.md. This handoff has not established a capsule radius/height Resize setter call in these fruits' initialization. Preserve stored dimensions; runtime Resize existence remains unknown, not proven absent globally.

[상대 보고] bmv8vu9ph-b reports Level006 automatic movement collected all three fruits at Size4/r2, DYNAMIC, triggered and inHoleDrop, manualDrop=false; comparison is fallback Box versus native-derived proxies. This is implementation regression evidence, not an independent original-game physics/parity test.
