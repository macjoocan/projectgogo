# Ending61 로고 Spine 참조 체인

2026-10-15, 요청1p. 원작 실행/소스 수정 없음. data.unity3d에서 선택 참조만 읽었다. peak commit0.894GB/guard2.5GB. `chain.json`은 native PPtr/external 조인, 저장 필드/rawSHA, 출력 payloadSHA를 보존한다. PNG는 Texture2D decode이며 원본 GPU/Spine 재생 동등성 검증이 아니다.

실제 씬 root: level2 EndingTransition GO2141/StateLevelCompleteTransition30984. `/EndingTransition/Panel/EndgameFX/LogoSpine` **SkeletonGraphic26899**.

| 연결 | 실제 native 대상 |
|---|---|
| SkeletonGraphic.skeletonDataAsset file3/16620 | resources.assets **SkeletonDataAsset16620**, GOODS HUNT_SkeletonData |
| SkeletonDataAsset.skeletonJSON file0/1263 | resources.assets **TextAsset1263**, GOODS HUNT |
| atlasAssets file0/16619 | resources.assets **SpineAtlasAsset16619** |
| SpineAtlasAsset.atlasFile file0/1260 | resources.assets **TextAsset1260**, GOODS HUNT.atlas |
| SpineAtlasAsset.materials file0/106 | resources.assets **Material106**, GOODS HUNT_Material, Shader1190 |
| Material106._MainTex file0/1159 | resources.assets **Texture2D1159** |

바로 사용할 선택 추출물:

- `payload/skeleton_1263.json` **52314B**, 원문 Spine JSON. header version **4.2.40**, bones136/slots71, animations 키 **animation** 하나. 본 timeline 중 time3.7 값까지 존재하지만 이 숫자를 모든 Spine 채널/효과 전체 길이의 독립 검증으로 확대하지 않는다.
- `payload/atlas_1260.atlas` **708B**. 페이지 이름 **GOODS HUNT.png**, size2056×433, Linear/Linear. region의 rotate90/offset/원래 크기 유지.
- `payload/texture_1159.png` atlas texture decode. 웹 atlas resolver에서 **GOODS HUNT.png → 이 파일**로 명시 매핑. 이름이 다른 것을 자동 못 찾았다고 기본 텍스처로 떨어뜨리지 않는다. 재중심화/리사이즈/region 재패킹 안 함.

SkeletonDataAsset scale **.009999999776482582** / defaultMix **.20000000298023224**. SkeletonGraphic initialSkinName=default, startingAnimation="", startingLoop=false, timeScale1, unscaledTime=false, referenceScale1/layoutScale1. startingAnimation이 비어 있어 저장 상태만 인스턴스화하면 자동 로고 재생을 보장하지 않는다. 실제 StateLevelCompleteTransition.PlayLogo0x1D982F8의 SetAnimation/scale·fade 호출은 ../end_flow_audit_20261015 원문과 함께 연결.

**UI 재질과 atlas 재질은 다름**:

- SkeletonGraphic.m_Material=file3→resources.assets**97**, `SkeletonGraphicDefault-Straight`, shader1254.
- additiveMaterial **93**, multiply **95**, screen **96**. 네 재질의 원문 SavedProperties/키워드도 chain.json에 보존.
- atlas Material106을 UI Material97 대신 통째로 연결하지 않는다. 이름 Straight만으로 전체 PNG premultiply 여부/Spine blend 동등성을 검증했다고 하지 않으며 실제 픽셀/알파 비교 필요.

위 JSON/atlas/pixel은 새로 그린 로고가 아니며 원문에서 선택 추출했다. 공개 업로드/배포 없음. resources.assets에 동명 EndingTransition 저장본이 별도로 있지만 이 체인은 **level2 ID61 실제 씬 SkeletonGraphic26899**에서 시작했다.
