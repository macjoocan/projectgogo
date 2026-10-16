# UI 연출 보충 — bmum55rwa-9 회신

2026-09-29. C: 프로젝트 수정 없이 원본 APK 재판독. 아래 값은 [원작값]. 플레이 결과 동등성은 Claude 측 확인 필요.

## +15 아이콘 확보

원본 sharedassets1.assets Sprite 목록에서 6종을 찾았고 PNG를 모두 추출했다. `badge_sprite_candidates.json`, `assets/manifest.json` 참조. UI Atlas 태그+RenderDataKey로 정확하게 해석했다. Sprite 원본 rect/pivot/border/atlas trim 정보도 manifest에 있으므로 잘린 PNG의 크기만으로 대체하지 않는다.

| 발사량 | 원본 Sprite pathID | 이름 |
|---:|---:|---|
| 5 | 564 | AddMoves05_icon |
| 10 | 350 | AddMoves10_icon |
| 15 | 591 | AddMoves15_icon |
| 20 | 551 | AddMoves20_icon |
| 25 | 439 | AddMoves25_icon.png |
| 30 | 486 | AddMoves30_icon |

15단계에10배지 대체는 제거하고 #591로 연결한다. 20/25/30 에셋 존재는 현재 이어하기 티어에서 도달한다는 뜻이 아니다. 현재 tierFirstFail=[1,4,8]이라 5/10/15만 선택된다.

## HorizontalLayoutGroup 저장값

`horizontal_layout_groups.json`: level1 내 14개, 각 header+상속 LayoutGroup+HorizontalOrVerticalLayoutGroup 저장 필드를 끝까지 해독했다. 14/14 byte 소비 일치. padding의 음수도 그대로 보존한다.

**UI/Canvas_Success/BottomButtonsLayout**

- padding left/right/top/bottom = 모두0
- childAlignment=4 (MiddleCenter)
- **spacing=0**
- childForceExpandWidth=true, childForceExpandHeight=true
- childControlWidth=false, childControlHeight=false
- childScaleWidth=false, childScaleHeight=false
- reverseArrangement=false

따라서 임시 spacing30을0으로 교체하고 ForceExpand 두 축도 확인한다. 화면에 원작과 다른 수의 버튼만 활성화하면 배치는 달라질 수 있다. 원본 child active 상태와 ad/continue 표시 상태를 함께 비교한다.

**UI/Canvas_Success/RewardParent/RewardsLayout**은 spacing=-212.2100067, MiddleCenter, ForceExpand 두 축true, Control/Scale 두 축false. **음수 간격을 오류로 간주해0으로 보정하지 않는다.** 수평 그룹별 전체 값은 JSON을 사용한다.

## Tween Target 52개 확인

`animation_targets.json`에는 원본 Target PPtr → 컴포넌트 종류 → 실제 GameObject 경로를 넣었다. **52/52가 소유 애니메이션과 같은 GameObject**를 가리킨다. 따라서 보고한31건의 자기 자신 대체가 다른 GameObject로 잘못 이동한 것으로 확인된 것은 아니다.

다만 GraphicAlpha는 Image 등 Graphic 컴포넌트를, CanvasGroupAlpha는 CanvasGroup을, Transform 계열은 Transform/RectTransform을 타깃으로 해야 한다. 단순 Transform ID 맵 실패와 참조 자체가 없음은 다르다. 노드가 같아도 `GetComponent` 종류/같은 타입 다중 컴포넌트 여부/생성 누락은 런타임에서 확인한다.

참조 해석 중 UnityPy가 노출한 숫자형 임시 SerializedFile 이름은 실행마다 달라질 수 있었다. 이 경우 **원본 파일 후보+pathID+raw SHA256**으로 단일 객체를 확인했다. 숫자형 파일명을 장기 asset key로 새로 사용하지 않는다. 이번 표의 target_asset_key는 실제 파일명으로 제공한다. animation_key는 기존 입력키를 유지해 교차 연결할 수 있게 했다.

## 반영 보고 판정

- 기본 사이클/하트/코인/실패 조건의 실행 결과는 Claude 보고로 기록한다.
- 로고 타임라인/runId/LastReward 즉시표시 구현 보고 수신.
- 커브13종 키·접선·가중치 보존 및 custom ease 조건 구현 보고 수신.
- 아직 미완료: PlayPurchaseExitAsync 실제 연결, Spine 리소스 연결, 상대 받침 기반 settle. 따라서 UI/클리어/실패 **모든 연출 완전 구현**으로 묶어 완료 표시하지 않는다.
- 첫 패널 OutValue(0,0)는 이전 원본 저장값을 유지. 이번 조사로 툴팁(0,60)의 추가 근거가 생긴 것은 아니다.

검증 범위: 14개 그룹 바이트 소비, 52개 Target 객체 해석, 6개 Sprite/atlas/PNG 추출. Unity 내 레이아웃과 연출은 별도 실측한다.
