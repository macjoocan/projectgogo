# 파티클 스프라이트 — reply-to bmum7co8u-j

2026-09-29. 요청 4 Sprite + 비활성 루트 참조 1 + 공 Sparkle 1 = Sprite 6종, 원본 Texture2D 6종 PNG 추출 완료. 오류 0. Unity 화면 적용 검증은 Claude 담당.

**정정: fileID는 level2가 아니라 ParticleSystem 소유 파일 sharedassets2.assets의 externals 기준이다.** material.m_TexEnvs만 조사해 형상 텍스처가 없다고 결론 낸 앞선 안내는 불충분했다. UVModule의 sprite 참조를 반드시 함께 조사해야 한다.

| 노드 | sharedassets2 외부 PPtr | 실제 Sprite 파일#pathID | 이름 | 적용 |
|---|---|---|---|---|
| ImpactCircle | 266 / 2 | 810774de4b2ce3d4883eb812a64ae6ac#2 | particle | 켬 |
| SmokeBurst 및 (1) | 237 / 2 | 70783540ef1967546bc5e66c28c39da8#2 | Magic1 | 켬 |
| Glow | 175 / 2 | 5a4dff25b1c3c6d449e8013322f41d34#2 | Glow_001 | 켬 |
| Smoke | 154 / 3 | 4d56ba7e0cc3dc242a446b2dccab2cc0#3 | cloud_2x2_soft_translucent_heavy_2 | 켬 |
| PS_Cannon 루트 | 147 / 2 | 4c165d69fcde15a498a0c9b8079bf0a1#2 | soft_cricle_07 | **UVModule 꺼짐 유지** |

루트의 참조는 보존용이며 적용 대상이 아니다. 루트 ParticleSystem 전체를 끄라는 뜻도 아니다. UV 활성 자식은 5개/고유 Sprite 4개다.

## 파일 사용

- `node_sprite_bindings.json`: 원본 소유 파일, ParticleSystem pathID, external 경로, Sprite asset_key, **UVModule 전체 저장값**. frameOverTime/startFrame/cycles/timeMode 등 포함. [원작값]
- `manifest.json`: asset_key로 PNG 경로 확인. Sprite `sprite_settings`에 rect/pivot/border/PPU, `render_data`에 textureRect/textureRectOffset/atlasRectOffset/settingsRaw, `sprite_geometry_native`에 원본 vertices/uv/triangles. Texture2D PNG도 별도 제공. [원작값 및 픽셀 디코딩]
- `validation.json`: PNG 크기 및 alpha 검사, 오류 0. 화면 정합 완료를 뜻하지 않는다.

**Magic1 주의:** m_Rect=128×128이지만 textureRect=(0.0761205,0,123.847763,127.987091), textureRectOffset=(0.0761205,0). UnityPy Sprite PNG는 124×128이다. 이 PNG를 원본 128×128인 것처럼 늘리지 않는다. `textures/Magic1__1.png` 원본 128×128과 저장 rect/geometry를 사용해 Sprite를 재구성하는 경로를 권장한다. 단순 FullRect 재생성은 tight geometry까지 같은 결과라는 보장은 없다.

Smoke는 원본 Texture2D 128×128 중 Sprite rect=(0,0,64,64). 4칸 시트 전체를 하나의 sprite로 연결하면 안 된다. Unity rect는 아래쪽 원점이므로 PNG 좌상단 crop과 혼동하지 않는다. 원본 texture+rect 방식으로 만들면 이 문제를 피할 수 있다.

활성 4종 pivot=(0.5,0.5), border=(0,0,0,0). PPU는 particle=50, 나머지=25. 정확한 실수값은 JSON 사용.

## 엔진 연결 / 검증

Texture Sheet Animation의 Sprites 모드에 각 노드의 Sprite를 연결하고 원본 UVModule 값을 복원한다. 해당 모듈은 파티클 프레임의 UV를 지정하는 기능이다([Unity 공식 설명](https://docs.unity3d.com/Manual/PartSysTexSheetAnimModule.html)). 실제 draw에서 shader가 읽는 텍스처까지 올바른지 확인한다. AddSprite 호출 성공만으로 텍스처 바인딩 완료를 판정하지 않는다. 여전히 네모면 Frame Debugger에서 실제 _BaseMap/사용 셰이더 샘플 슬롯과 alpha를 확인한다. 필요 시 재질 복제본 또는 renderer별 프로퍼티로 texture를 지정하되, 공용 M_Additive 하나의 텍스처를 마지막 Sprite로 덮어 모든 노드가 같은 이미지가 되지 않게 한다. 이 fallback 배선은 [자체 이식]으로 구분한다.

기존 원본 Additive/Trail 혼합 상태 분리는 유지. RGBA의 alpha를 버리거나 alpha=1로 만들지 않는다. 실측은 자식별 단독 발사 + 전체 합성 + 1초 회수 순서로 확인한다.

공에도 같은 누락이 있을 수 있어 Ball/PS_Sparkle 및 BigBall/PS_Sparkle의 **star sharedassets1#622**를 같이 추출했다. 둘은 같은 Sprite다. 임의 신규 효과 추가가 아니라 저장 참조 보충이며 현재 활성 GameObject 상태는 기존 prefab_nodes를 따른다.

대포 반동 실측 보고는 수신했다. 일반 대포의 원위치 복귀는 확인된 것으로 기록하되 Big/Infinite 노드 전환, 연타, 바퀴 BakeMesh 검증은 여전히 미완료다.
