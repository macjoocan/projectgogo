# 지하 과일 끌림 관련 원작 낙하 조건 — 2026-10-15

## 확정 필드 및 정정
PropBehavior TypeDef4342: IsActive+48 / IsEaten+49 / CanFallSlow+4A / _isBigPropObject+D0 / isTriggered+D2 / _isInHoleDrop+82 / dropVelocity+84. 앞 임시 브리지의 CanFallSlow(+D0) 표기는 잘못되었고 정정했다. +D0는 큰 물체 여부이며 CanFallSlow와 별개다. _isBigPropObject는 Init에서 cost>3 또는 저장 _isBigProp로 결정하는 기존 판독 범위.

## Update 0x21E14A4
_isAnimateAtHome(+38) true면 반환.
아직 inHoleDrop이 아니면 !active 또는 eaten은 반환. meshRenderer가 있고 **meshRenderer.transform.position.y < -2.3**일 때만 EnableInHoleDrop 호출. root centerY=0/AABB centerY=0/layer13 진입과 동일한 조건이 아니다.
이미 inHoleDrop이면 v=min(v+30*deltaTime,80). **bigObject && isTriggered**이면 아래 Transform 이동을 건너뛴다. 그 외 transform.position += Vector3.down * v * deltaTime.
이후 Eaten Y 비교 순서: CanFallSlow true -> rootY<-15; 아니고 bigObject -> rootY<-10; 그외 -> rootY<-4. 모두 엄격한 <. 조건 만족 시 virtual slot11 EatenCoroutine이며 rootY<-4가 모든 특수물체의 공통 기준은 아니다.

## EnableInHoleDrop 0x21E1718
이미 inHoleDrop이면 반환. 먼저 inHoleDrop=true.
**bigObject(+D0) true면 그 자리에서 반환**: 아래 일반 경로의 속도 초기화/kinematic/collider disable을 실행하지 않는다. CanFallSlow(+4A)는 이 분기에서 읽지 않는다.
!bigObject 경로: Rigidbody 있으면 v=abs(velocity.y), velocity=0, angularVelocity=0, isKinematic=true; rb없으면 v=0.
normal colliders(+40) 각 nonnull Collider.enabled=false (0x21E1910..1920).
simple colliders(+78)도 각 nonnull Collider.enabled=false (0x21E19C0..19D0).
ShadowProxy(+B8)가 있으면 SetShadowEnabled(false).
따라서 일반 과일이 이 전환을 지난 뒤에도 동적 body+ground contact로 남아 prism과 계속 충돌하는 구현은 원문과 다르다. 반면 아직 rendererY=-2.3에 못 도달한 반잠김 물체에 ground contact를 영구 제외하는 규칙은 이 원문에서 나오지 않는다.

## layer callbacks
OnTriggerEnter 0x21E2A94:
- layer7: !Eaten && !Active && IsGamePlayActive -> isTriggered=true; ActivateProp.
- layer11: !Eaten -> rb.maxLinearVelocity=20. 이 함수에서 즉시 Eaten/Collider-off하는 호출 없음.
- layer13: **이 base 함수에 해당 분기 없음**. layer13 명칭 PropDropIn만 보고 직접 manual-drop callback을 추가한 원작 근거로 쓰지 않는다. 다른 소비자/override/physics filter에서의 전체 사용은 아직 미확정.
OnTriggerExit0x21E297C: layer7 && !Eaten && !Active && gameplayActive일때만 isTriggered=false. ActiveCounter waiting이면 CancelWaiting, 그외 virtual slot8 HoleOutOfProp -> PropAutoSleep.HoleOutProp. 이미 active 물체가 홀을 벗어나면 자동으로 지면 위로 복구한다는 일반 계약이 아니다.
SetCanFallSlow0x21DECB0는 bool을+4A에 저장만 한다. 상위 선택 조건은 별도 미결.
이번 확인 함수들에서는 Physics.IgnoreCollision로 ground와 한 쌍만 제외하는 호출을 찾지 않았다. 프로젝트 전체에 그런 경로가 없다는 뜻은 아니다.

## 웹 보정 경계와 검증 제안
상대 v7의 AABBcenter<0일때 ground 전용 group2만 영구 제외는 **solid-prism adapter 보정**이다. native triangle 데이터/원작 낙하 gate는 그대로 보존하고 원작 계약으로 표시하지 않는다. 일부 잠김/다중 compound/큰 물체/재시작에서 예외가 없는지는 해당 구현 QA 범위.
재현 기록에는 rootY/rendererY/bigObject/CanFallSlow/isTriggered/inHoleDrop/normal+simple collider 상태 및 ground contact 전후를 함께 기록한다. rootY 하나만으로 원작 gate 도달을 판정하지 않는다.
원작 runtime/PhysX 재현은 이번에 실행하지 않았다. 웹 버그 원인 확정은 상대 구현 세션 A/B 근거와 분리한다.
