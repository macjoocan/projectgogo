# Prop 활성화 / 시작 배치 밀림 대응 (reply-to bmv82ctii-2b)

[원작 코드 판독] 모든 물체를 시작부터 dynamic으로 두는 것은 원작 ResetTransform 경로와 다르다. 비활성일 때에도 일반 콜라이더를 전부 끄는 구조는 아니다. Rigidbody 상태와 collider 상태를 분리해야 한다.

## ResetTransform 0x21E22E8
- 원문 PropPlacement Position/EulerAngles와 originalScale 복원.
- colliders(+0x40) 목록의 유효 Collider: material 복원, enabled=true(0x21E24BC~C8).
- _simpleColliders(+0x78) 목록: enabled=false(0x21E2578~80).
- Rigidbody position/rotation 동기화, velocity/angularVelocity 정리, isKinematic=true(0x21E2618~20), interpolation=0, Sleep().
- IsActive=false(+0x48); PropAutoSleep.SetInactive; IsEaten=false(+0x49); _isInHoleDrop=false(+0x82); dropVelocity=0; renderer enabled=true.
따라서 비활성 일반물체는 보이는 정적/kinematic 장애물로 남되, 겹친 배치를 처음부터 dynamic으로 밀어내지 않는다.

Init 0x21E1B60은 Prop/Data와 원문 scale/mass/drag/cached renderer.bounds.size를 연결하고 ResetTransform(slot6)를 호출하는 경로(0x21E1D04~08)가 있다. automaticCheckingPhysics=true면 CheckPropActivationRule(slot5)도 수행(0x21E1D8C~9C). Init 본문에 별도의 일괄 초기dynamic setter는 없다. _isBigPropObject는 cost>3 또는 저장 _isBigProp 플래그에서 정해지는 분기(0x21E1DA8~C8)다.

## SetInActive 0x21E2E60
velocity=0, angularVelocity=0, IsActive=false, interpolation0, AutoSleep.SetInactive, ActiveCounter.CancelWaiting, isKinematic=true, Sleep, culling OnPropDeactivated. 이 함수는 일반 collider를 일괄enabled=false로 만드는 명령이 없다.

## ActivateProp / ActivatePropImmediate
ActivateProp 0x21DA610은 PropActiveCounter의 static activeCount/max 비교를 한다. 한도 이하면 ActivatePropImmediate(slot9), 아니면 SetWaitingActive. 즉 한 프레임에 모든 nearby 물체를 무제한 동시에 dynamic으로 풀었다고 확대하지 않는다.
ActivatePropImmediate 0x21E2B98: IsActive=true, AutoSleep.SetActive, ActiveCounter.StartCounting, renderer true, 유효 rb.isKinematic=false, interpolation1, WakeUp. isObstacles면 ActivateTopProps도 호출. 명시적인 바깥 방향 impulse/push는 이 함수에 없다.

## layer7 트리거와 Nearby
OnTriggerEnter0x21E2A94: 상대layer7 + !IsEaten + !IsActive + gameplayActive이면 isTriggered=true 후 ActivateProp. 이 조건은 collider overlap 이벤트이며 임의 중심 거리 1개로 완전히 대체했다고 주장하지 말 것.

CheckPropActivationRule0x21E2118은 isHolder && !isObstacles일 때만 ActivateNearbyProps0x21E2130으로 이어진다.
ActivateNearbyProps:
- cachedBoundsSize.y <1이면 반환.
- 탐색 중심: 이 물체 transform.position + Y(cachedBoundsSize.y*0.5).
- radius = cachedBoundsSize.x * float32(0.8) *0.5 *1.25. 수학상 width*0.5와 같지만 원작 float 연산 순서는 그대로 보존.
- Physics.OverlapSphere(center,radius,layerMask0x200) = layer9 물체 탐색.
- 발견된 PropBehavior가 !isHolder && !isObstacles && !IsActive이면 ActivateProp 호출.
이는 홀을 중심으로 모든 물체에 적용하는 보편적 활성거리 공식이 아니라 holder가 주변 일반 물체를 깨우는 경로다.

원문 literal0xE0A3B0 bytescdcc4c3f=0.800000011920929. Init의 Renderer.bounds.extents를 2배해서 cachedBoundsSize에 저장하는 명령0x21E1CF4~D00까지 확인했다.

## 구현 반영 경계
시작 비활성 물체를 kinematic으로 유지하고 일반collider는 저장 형상대로 유지. 실제 overlap/layer 활성화 후 dynamic 전환. 임의 outward push 제거는 이 판독과 부합한다. 홀 근처에서 어떤 collider/layer7이 움직이는지는 ground 추가 판독에서 별도로 제공 예정이다. 이 문서만으로 정확한 원작 hole-fit 판정을 만들었다고 쓰지 않는다.

네이티브 프리팹 Rigidbody 저장값과 Init/Reset 후 런타임 상태는 다르다. prefab.isKinematic 값만 보고 모두dynamic을 유지하지 말 것. 검사에서는 입력 전 원문배치가 유지되는지와 활성화 후 물리 진행을 구분해 볼 것.
