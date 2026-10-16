# 그림자·진입 안내·클리어 연출·망치·TNT 보강

2026-09-29 사용자 요청. 원본 에셋 추출/ARM64 판독 및 C: 이식 코드 읽기 결과. Unity 실행 검증은 Claude 담당이며 이 문서는 적용 완료 보고가 아니다.

## 1. 그림자는 받침 위와 배경 지면을 구분

- **받침 상판 위에 떨어지는 블록 그림자**: 실제 상판 renderer/material에서 shadow receiver 경로를 확인해야 한다. 별도 지면 스프라이트에 그리는 것으로 해결되지 않는다. 상판의 receiveShadows, caster의 castShadows/ShadowCaster pass, 주광 shadows, 실행 URP Asset의 shadow 지원·거리·레이어를 로그로 대조한다. 현재 Toony에는 shadow sample 코드가 있으므로 코드 존재만으로 실제 수신을 판정하지 않는다.
- **배경 잔디/기둥 아래 지면 그림자**: 원본 Ground가 그림자 합성용 평면이다. 배경 SpriteRenderer와 별도다. `camera_ground_audit_20260929/GroundReference.hlsl`, `ground_forward_evidence.json`, `ground_transform_chain.json`이 정본.
- [원작값/코드] Ground MeshRenderer level2#96 sortingOrder=-3, 배경=-5. ShadowAlpha0.6. RGB는 고정 diffuse(0.0361055769,0.144683689,0.00716756145)의 조명 결과, 검정 단색/임의 Z 그라디언트가 아니다. alpha=saturate((1-rawStrengthShadow)*0.6), RGB용 거리 fade와 분리.
- 고정 패스 Blend SrcAlpha OneMinusSrcAlpha, One OneMinusSrcAlpha / ZTest Always / ZWrite On / Cull Back. 재질 저장의 낡은 blend 숫자보다 실제 패스가 기준이다.
- 현재 RS_GroundShadow.shader와 RS_Toony.shader에 그림자 코드가 있음은 정적 확인했다. 그러므로 실제 문제는 renderer/광원/URP/정렬/실행 variant를 재현 화면에서 분리 검사해야 한다. **원인 확정 전 광원 밝기나 알파를 임의로 올리지 않는다.**

## 2. 로비→게임 안내 이미지

[원작값] `level1#6355 LoadingScreen`, `UI/Canvas_Loading`. `loading_values.json`에 주소형 참조6개와 raw_hex 보존.

- m_minDuration=1.25, m_fadeOutDuration=0.25.
- fallback GUID a46cc402bbe3d42ec8cea02614635025, 목록 첫 항목과 같음.
- 로컬 bundle `assets/aa/Android/loadingscreens_local_assets_all.bundle`에서 **LoadingScreen_1** 확인.
- 이미지 **Charlie** PNG 추출: `assets/textures/loading_-5779257235841103873_Charlie.png`.
- 원본 번들의 GO/RectTransform/Sprite/MonoBehaviour 저장값은 `loading_local_bundle.json`. Sprite pathID6247649328221505535. Texture pathID-5779257235841103873.
- LoadingScreen.ShowInternalAsync RVA0x3958C48, PlayPopup.StartGame0x395EE94에 연결 경로가 있다. 로딩 안내는 실제 게임 내 강제 조작 튜토리얼과 별도 기능이다.

[자체 구현 연결] 로컬 안내화면 표시→레벨 준비→최소 노출시간 충족→fadeout→입력 개방 순으로 연결. 매번 임의 추가 대기를 누적하지 않는다. 원본 목록 전체 원격6종을 확보했다고 쓰지 않는다. 로컬 fallback1종으로 서버 없이 동작 가능하다. 페이드 ease와 모든 async 분기의 완전 등가는 아직 미검증이다.

## 3. 클리어 로고·색종이

[원작값] `level1#5692 LevelCompletedAnimationPopup`, `UI/Canvas_LevelCompleted_Logo`:

- Logo GameObject #62.
- m_confettiParticles=[level1#2045, level1#2100].
- animationDuration1.5 / confettiStartDelay0.8 / inputBlockerDuration0.5.
- 원본 OnEnable0x395659C, OnEnterCompletedAsync0x39566DC, ExitPopup0x39568EC, TriggerLevelSuccessEvent0x3956B70.
- 기존 판독 타임라인: 승리0→0.75 로고→1.25 탭스킵 허용→1.55 색종이→3.30 로고 종료/Success. 스킵 이후 늦은 작업은 runId로 무효화한다.

이번 추출 `celebration_loading_scene.json`: 로고/로딩 계층 합계53노드139컴포넌트, 원본 TRS·ParticleSystem 모듈·ParticleSystemRenderer·MonoBehaviour payload 보존. `asset_manifest.json`20자산, 이미지/재질 추출오류0. confetti_AB/M_Additive/M_Cypher_VFX 등 재질 및 파티클 UVModule 스프라이트를 포함한다.

현재 RsGameplayView.SuccessTimeline/PlayConfetti는 존재한다. 그러나 `GetComponentsInChildren<ParticleSystem>`에 실제 결과가0이면 호출만 있어도 화면은 비어 있다. 다음을 실측할 것:

1. canvasLogo 참조가 실제 캔버스인지, 원본 Logo 자식·스켈레톤/그래픽이 생성됐는지.
2. #2045/#2100 대응 파티클이 존재하고 재질/UVModule 스프라이트/renderer 정렬이 연결됐는지.
3. 파티클을 일반 UI Image로 대체하지 않았는지, Canvas 렌더 모드와 카메라가 원본 배선인지.
4. 로고의 Spine 등 raw payload만 읽고 실제 렌더 컴포넌트를 생략하지 않았는지. SuccessPopup.skeletonGraphic은 level1#5630으로 별도다.
5. 스킵 없는 승리에서 로고/파티클/Success 각각 스크린샷 확인. '코루틴 호출됨'만으로 시각 완료 판정하지 않는다.

## 4. 망치 크기·흰 재질

[원작값] 프리팹 `assets/bin/Data/46d28dd7256b2441b9ef78d27784dea3`. 전체 저장 노드/컴포넌트는 `hammer_prefab_source.json`.

- Material **Hammer** = `5b1c8859b8a164b638a30cbd7bcd3238#1`.
- Texture **Hammer_1k** = `e6b988dbdb4354c3db7294c7a6716288#1`.
- `hammer_material_assets.json`에 프로퍼티·참조, assets/textures 아래 PNG. 추출 오류0. 기존 entity_renderer_material_refs에는 Hammer 키가 없어 이번에 별도 확보했다.

[원작 코드 판독] `Hammer.ApplyScales 0x3833424`, asm동봉:

```text
pivot1.SetParent(rb.transform, true)
pivot2.SetParent(rb.transform, true)
pivot1.localScale = Vector3.one * h1
pivot2.localScale = Vector3.one * h2
d = (h1+h2)*0.5*rodDiameter
rod.localScale = (d, rodLength, d)
pivot1.SetParent(slot1, true)
pivot2.SetParent(slot2, true)
pivot1.localPosition = pivot2.localPosition = zero
pivot1.localRotation = identity
pivot2.localRotation = Euler(0,0,180)
```

둘째 회전의 literal은 ELF file offset0x14F39E4 값3.141592741(rad), 내부 EulerRad 호출. 현재 RsHammer는 기존 scale누적곱/rodDiameter직접사용/부모변경생략이므로 원본과 다르다. 레벨 설정을 두 번 적용해도 배율이 누적되지 않아야 한다. **원본 공식 복원 전 '너무 넓으니0.5배' 같은 임의 보정은 금지.**

## 5. TNT가 폭발 없이 사라짐

현재 RsObstacleRules.OnBallHit(explodes)→Complete→SpawnBroken→SetActive(false). Complete 내부에 RsTnt.Explode 호출이 없음을 정적으로 확인했다. RsTnt.Explode는 별도로 존재하지만 이 경로에서 사용되지 않는다. 사용자가 본 소멸 증상과 맞는 연결 누락이다.

[원작 코드 판독] `Tnt.Explode0x393E00C`는 OverlapSphere→강체중복제외/kinematic제외→AddExplosionForce→연쇄 예약→base Obstacle.Explode0x383D600 순. asm동봉. OverlapSphere0x393E12C는 **레이어 mask 없는 오버로드**다. 현재 코드의 Obstacle단일레이어 필터와 같지 않다.

[자체 수정 가이드] Complete에서 폭발형 분기를 복원하되 Explode→Complete 재진입으로 목표/보상을 두 번 올리지 않도록 완료 정산과 폭발 실행을 분리한다. 이미 _destroyed=true로 만든 뒤 필요한 폭발을 차단하지 않는다. 본체 비활성화 전에 폭발 VFX/SFX를 독립 수명으로 생성하고, 연쇄 지연 작업도 비활성화되는 TNT 호스트에 묶지 않는다. 실제 폭발력과 시각효과는 별도 항목으로 검증한다.

저장값 TntSquare_1/TntCylinder_1 힘12 반경6, 이름 Tnt는10/4라는 기존 원본 추출을 유지. Tnt 파괴 VFX/음성의 완전 배선은 이번 문서로 완료 판정하지 않는다.

## 6. 추가 사용자 요청: 로비·오프라인 진행

- 로비 초록 버튼은 스크린샷처럼 **레벨 N**. N은 저장 진행도, 샘플38을 하드코딩하지 않는다. 원본 프레임/폰트 외곽선·그림자·중앙정렬 보존.
- 플레이 이벤트/챕터 진행은 **서버 없이 클라이언트 저장**으로 구현하라고 사용자가 승인했다. 기존 items_events_handoff_20260929 활용. 원본 챕터 구간표를 이번 조사에서 확보하지 못했으므로 자체 구간표는 데이터로 분리하고 `[자체]` 표시.
- 이벤트 진행은 단일 확정 outcome에 연결, 중복 호출/재시작 시 중복 보상 방지. 이벤트 기간·진행·수령상태와 챕터 완료/보상수령을 저장한다. 표시용 진행과 지급 완료를 별도 상태로 둔다.
- 구매/광고는 **나중에 배선할 준비만**이라는 앞선 지시 유지. 이벤트 구현 때문에 광고 자동성공이나 구매 실행을 끼워 넣지 않는다.

Claude에게 원본 자료와 구현 요청 전달. 실제 수정/화면 검증 완료는 후속 회신으로 별도 확인한다.
