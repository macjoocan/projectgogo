# 카드 Canvas / PointsExplode 투영 근거

## 후속 보완 — additive level3 Main Camera

이 문서의 원래 카메라 목록은 **level2에 한정**한다. additive gameplay level3를 제외하고 활성 카메라 전체에 layer0이 없다고 확대하면 안 된다. 기존 ingame_handoff 원문을 대조한 결과:

- level3 Camera37 / GO5 Main Camera: GO active=true, Camera enabled1, **cullingMask4087은 layer0을 포함**한다. 포함 layer는 0,1,2,4,5,6,7,8,9,10,11.
- perspective(orthographic=false), 저장 FOV30, near .30000001192 / far399, viewport(0,0,1,1), depth0, targetDisplay0, targetTexture=null.
- Transform27은 root(parent=null), position(0,30,-22), quaternion(.4500984847545624,0,0,.8929789662361145), scale1.
- Camera raw SHA `1b26fe42fdb280fa66c000d44775a5ee830b4f5b107658a8f252d73c9beec11f`; Transform raw SHA `3141218a419a0cc753e6874e7ca229ee6ad5823d0461aeb00f0d960f0661d2b6`.
- VCam98: enabled1 / priority0 / lens FOV33, near .3/far150; VCam99: enabled1 / priority10 / lens FOV30, near .3/far399, Follow33。이들은 virtual camera 설정이며 별도 렌더 카메라나 런타임 최종 pose를 뜻하지 않는다.

`level3_camera_followup.json`에 기존 source provenance·선택 필드·native Transform·인계 파일 SHA를 보존했다. 신규 원본 로드나 실행 없이 기존 원문만 재사용했다. **layer0이 렌더 mask에서 배제됐다는 장애물은 level3에는 없다.** 그러나 Overlay 카드의 실행 중 worldPosition과 최종 Cinemachine 카메라 상태가 측정되지 않았으므로 Points가 실제 frustum 안에서 보인다는 결론은 아니다. Canvas Overlay/null worldCamera 및 GPool parent=null 판독은 그대로다.

[원작값] 기존 data.unity3d에서 level2 Canvas17295, Controller29706의 부모 체인 및 level2 Camera3개만 선택했다. 원문 필드·PPtr·각 raw SHA는 chains.json. 원작 실행/구현 변경 없음. 선택 프로세스 peak .2706GB, cap2.5GB.

## Canvas17295

- GameObject3162 `Game`, Canvas enabled1.
- **m_RenderMode=0: Screen Space Overlay. m_Camera=null.**
- m_PlaneDistance=49.20000076294. 저장돼 있다는 사실이며 Overlay의 worldCamera 또는 물리 투영 거리라는 뜻이 아니다.
- sortingOrder0 / overrideSorting=false / targetDisplay0.
- CanvasScaler32183: ScaleWithScreenSize(1), reference857×1522, ScreenMatchMode Expand(1), referencePPU100, scaleFactor 저장1, dynamicPPU1.
- 같은 GO의 RectTransform은 저장 localPosition0 / rotation identity / **localScale(0,0,0)** / sizeDelta0. 이를 실행 중 lossyScale 또는 안 보임의 증거로 쓰지 않는다. Canvas 엔진 레이아웃 적용 이후 값은 이번 정적 자료에 없다.
- 부모 Transform8108 / GO31 `______________UI______________ `: position(0,1,4.050000190735), rotation identity, scale1, root.

Controller29706은 `Card Placement (1)` → `Panel` → `Game` → 위 UI root의 체인이다. 카드 배치와 Panel 저장 localPosition0/rotation identity/scale1. anchored position·anchor·pivot·sizeDelta·SafeAreaPanel 원문은 chains.json의 controller_ancestors에 보존했다. 런타임 safe area/CanvasScaler layout 이후 world position을 이 저장 TRS만 곱해서 확정하지 않는다.

## 같은 씬의 카메라

모두 viewport width=height=1, targetDisplay0, targetTexture=null. 아래 position/rotation은 저장값이다.

| Camera | 활성 저장값 | 투영 | near/far | viewport x/y | culling mask |
|---|---|---|---|---|---|
| 9171 MainHomeCamera | GO on / Camera enabled1 | ortho size5 | .5 / 50 | 0 / 0 | 8800: layers5,6,9,13 |
| 9172 Camera / CanvasCapture | GO chain on / **Camera enabled0** | ortho size5 | .30000001192 / 1000 | 0 / 0 | all bits |
| 9173 Camera / __3DUIZONE__ | GO chain on / Camera enabled1 | ortho size6 | .30000001192 / 30 | 0 / .00999999978 | 4096: layer12 |

- 9171 root position(0,0,4), rotation identity.
- 9172 local position0/rotation identity, parent CanvasCapture position(20000,20000,20000), identity/scale1.
- 9173 local position(0,0,-10), identity, parent __3DUIZONE__ position0/identity/scale1.

**level2의 저장 enabled 카메라 중 layer0을 그리는 것은 없다.** all-mask인9172는 꺼져 있고 CanvasCapture 아래에 있다. 이를 Points 전용 카메라로 지정할 근거가 아니다. 다른 씬/런타임 생성·활성화·mask 변경까지 부정하는 결론은 아니다.

## PointsExplode와 카드 UIParticle는 다르다

`../card_fx_asset_audit_20261015/chains.json` 재확인:

- PointsExplode GO1583와 자식은 모두 layer0. 선택 subtree에 Canvas/UIParticle/CanvasRenderer/별도 MonoBehaviour가 없고 Transform/PS/PSRenderer다.
- GoalCard의 UIParticle GO2109는 layer5, CanvasRenderer3773/UIParticle7231가 있으며 PS3398은 layer0이다. 이 UI 변환 처리와 Points를 같은 경로로 간주하지 않는다.
- 앞선 본문에서 b__5가 FX.transform.position=card.transform.position(world)을 쓰는 것은 확인됐지만, 이것만으로 Canvas 화면 좌표를 어느 카메라 world 좌표로 변환하는지 또는 원작에서 실제 어떻게 보이는지는 확정할 수 없다.

## 구현 인계 경계

현재 원문은 Overlay/null camera다. World Space Canvas나 특정 ortho 카메라를 원작값이라고 만들어 넣지 않는다. scale100 등의 임의 배율을 원작값이라고 할 근거도 없다.

남은 좁은 미결은 GPool.Spawn의 parent/layer/scale 계약, 실행 중 Canvas mode/카메라 활성·mask 변경, 실제 Points의 원작 화면 표시 여부다. 이 보고서는 그 본문을 새로 판독한 것으로 주장하지 않는다. 화면 검토용 별도 UI 합성 어댑터를 만들 경우 파생 구현임을 표시해야 한다. 카드 UIParticle3398의 실제 Play 호출은 이번 조사 범위가 아니다.
