# 카드 완료 파티클 — 선택 원본 자산 인계

[원작값] Goods Hunt 1.9.1의 기존 data.unity3d에서 선택 참조만 추출했다. 구현 소스 변경/원작 실행은 없다. resource-extract 방식의 내부 분석용 인계다. 원작 GPU 동일성은 미검증이다.

`chains.json`: 원본 GO/Transform/PS/Renderer/UIParticle 필드, 재질과 Shader·Texture·UV Sprite의 owner별 PPtr 조인, 원본 raw SHA. `inventory.json`: 셰이더 프로그램 bounds/키워드/GLSL SHA. `pass_summary.json`: 고정 pass 상태. 각 shader 폴더의 parsed_form.json과 p9_*.glsl은 원문이다. `verification.json`: 비-null 참조 미해결0, PNG/GLSL 검사 오류0.

## 대상 수·활성 상태

PointsExplode GO1583 아래 PS는 **5개**다. 저장 상태에서 보이는 자식은 3개이고, 카드 UIParticle에는 별도 1개가 있다.

여기서 3개는 GO active/Renderer on인 후보 수이며 방출 수가 아니다. PS3349는 EmissionModule.enabled=false 및 SubModule.enabled=false이므로 강제 Emit하지 않는다. 저장 방출 후보는 Stars3399와 Shockwave3413의 2개로 분리한다. 실제 표시 여부는 별도 투영·호출 검증이 필요하다.

| PS / Renderer | 노드 | 저장 상태 | 재질 |
|---|---|---|---|
| 3342 / 3492 | PointsExplode 루트 | GO on, Renderer **off** | sharedassets2#17 |
| 3349 / 3571 | efx bulb compliment | GO on, Renderer on | resources#81 |
| 3399 / 3524 | Stars | GO on, Renderer on | resources#81 |
| 3413 / 3580 | Shockwave | GO on, Renderer on | resources#390 |
| 3451 / 3587 | ShockwaveLoop | GO **off**, Renderer on | resources#390 |
| 3398 / 3544 | GoalCardPrefab/UIParticle/Particle System | GO on, Renderer on | sharedassets2#89 |

표의 sharedassets2는 sharedassets2.assets, resources는 resources.assets다. 루트 Renderer와 비활성 Loop를 일괄로 켜지 않는다.

GoalCard6753._uiParticle=sharedassets2#7231. UIParticle7231.m_Particles=[3398], m_Scale3D=(10,10,10), m_IgnoreCanvasScaler=false, m_AbsoluteMode=false, m_PositionMode=0, m_AutoScaling=false, m_AutoScalingMode=2, m_ResetScaleOnEnable=false. 단순한 world PS의 치수와 혼동하지 않는다.

## 정확한 재질·텍스처·Shader 조인

| 재질 | MainTex / PNG | Shader |
|---|---|---|
| sharedassets2#89 Light_Mat | sharedassets2#392 Light_3, 328×328 | globalgamemanagers.assets#9 UI Extensions/UIAdditive |
| sharedassets2#17 CFX_WhiteCircle | sharedassets2#319 CFX_T_WhiteCircleSmall, 32×32 | sharedassets2#591 Legacy Shaders/Particles/Additive (Soft) |
| resources#81 Star | resources#697 Star, 61×64 | resources#1235 UI Extensions/UILinearDodge |
| resources#390 Aura | resources#608 glow2, 256×256 | sharedassets0.assets#35 UI/Additive |

PNG 명은 `<serializedfile>_<pathID>_texture.png`. raw SHA/PNG SHA/pixel SHA/Texture 색공간·포맷·mip 필드는 chains.json에 있다. 이름 Star가 같다고 Sprite1135/Texture697/Texture932를 대체하지 않는다.

**6개 PS 모두 UVModule.enabled=false.** 비-null UV Sprite 참조는 보존용이며 이 저장 상태에서는 적용하지 않는다. Sprite4개와 해당 backing Texture4개도 별도 추출해 atlas/rect/pivot/border 원문을 보존했지만 활성 텍스처로 배선하지 않는다.

UV 참조: PS3398→sharedassets2 Sprite1135, PS3349→resources Sprite2122, PS3399→resources Sprite1663, PS3413/3451→resources Sprite2354. PS3342는 null. disabled 상태 유지.

## 셰이더 식과 pass

GLSL fragment 원문 기준. T=texture(MainTex,uv), C=vertex COLOR. 실제 vertex COLOR가 uniform tint를 포함하는지는 각 GLSL vertex 경로를 그대로 확인한다.

- **uiadditive**: Q=T*C. Q.a<.01이면 discard. 출력=(Q.rgb*Q.a,Q.a). Blend **One/One**(RGB·alpha), ZWrite0/Cull0, ZTest는 **unity_GUIZTestMode** 참조, ColorMask는 _ColorMask. 원문 entry0001, 빈 키워드.
- **lineardodge**: Q=T*C. Q.a<.01 discard. 출력=(Q.rgb*Q.a,Q.a). Blend **SrcAlpha/One**, ZWrite0/Cull0, ZTest=unity_GUIZTestMode. 원문 entry0001, 빈 키워드. 출력에 이미 alpha가 곱해졌어도 blend를 One/One으로 바꾸지 않는다.
- **uiaura**: Q=(T+_TextureSampleAdd)*C. 빈 키워드 출력=(Q.rgb*Q.a,Q.a). Blend **One/One**, ZWrite0/Cull0, ZTest=unity_GUIZTestMode. entry0002는 빈 키워드, 0003 ALPHACLIP, 0004 CLIP_RECT, 0005 둘 다. 클리핑 변형은 해당 원문을 사용한다.
- **softadditive**: 빈 키워드 Q=T*C, 출력=(Q.rgb*Q.a,Q.a). Blend **One/OneMinusSrcColor**(native dest=6), ZTest LEqual4/ZWrite0/Cull0. entry0002 빈 키워드, 0003 SOFTPARTICLES_ON. 원본 PointsExplode 루트 Renderer가 off이므로 이를 켜기 위한 근거가 아니다.

재질 저장 _SrcBlend=1/_DstBlend=0/_ZWrite=1이 남아 있어도 이 Shader의 고정 pass와 같다고 가정하면 안 된다. native Shader identity/raw SHA는 chains.json 및 inventory.json에 보존했다. UI ZTest 런타임 값/Stencil·Canvas 합성/GPU 표현은 이 추출로 새로 확정하지 않는다.

## 기존 자료 재사용

`existing_reuse.json`에 exact raw SHA 비교 결과를 기록했다. 이번 Shader4개는 검사한 기존 성장/엔딩/기본 shader inventory와 raw SHA 일치가 없다. 이름·수식 유사성으로 같은 자산이라고 하지 않는다.

UV가 꺼진 Sprite2354의 backing resources Texture916 Circle02만 기존 `../player_fx_material_audit_20261015/resources.assets_916_texture.png`와 raw object SHA가 같다. 이는 보존 참조 재사용이며 현재 Aura MainTex608을 대체하는 근거가 아니다.

## 검증 범위

PS6/재질4/Shader4/GLES3 GLSL8/Sprite PNG4/Texture PNG8. 모든 nonnull PPtr 조인 성공. PNG 크기·파일 SHA·pixel SHA, GLSL SHA 검사 통과. 자산 조인 프로세스 peak .7883GB, 셰이더 선택 프로세스 peak .1831GB, 각각 2.5GB 가드. 원본 전체 재추출·원작 실행·구현 프로젝트 수정 없음. PS 수/활성 수/Emission 수를 동일하게 세지 않는다.
