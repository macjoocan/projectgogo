# PropAutoSleep: 타이머 기반 재비활성화 (reply-to bmv91tmvb-10)

기존 dump.cs 및 disasm만 재조회. 신규 추출/원작 실행/구현 변경 없음. 이번 범위는 base PropAutoSleep TypeDef25. 속도가 느린지 검사해 동적 Rigidbody를 잠재우는 엔진 sleep과 별개의 게임 코드다.

## 선언과 원문
`code_audit_20261014/dump.cs`871행 부근:
propBehavior+20, awakeDuration+28, stayAtSlowSpeedDuration+2C, lastPosition+30, lastRotation+3C, velMinMagnitute+4C, angularVelMinMagnitute+50, autoSleep+54.

| 메서드 | RVA | 기존 원문 파일 |
|---|---|---|
| SetMagnitute | 0x1CC58A0 | disasm_01cc58a0.txt |
| SetActive | 0x1CC58A8 | disasm_01cc58a8.txt |
| HoleOutProp | 0x1CC58EC | disasm_01cc58ec.txt |
| SetInactive | 0x1CC58F0 | disasm_01cc58f0.txt |
| IsAnimateAtHome | 0x1CC58FC | disasm_01cc58fc.txt |
| FixedUpdate | 0x1CC5918 | disasm_01cc5918.txt |
| SetSleep | 0x1CC5A40 | disasm_01cc5a40.txt |
| ctor | 0x1CC5A68 | disasm_01cc5a68.txt |

ファイル根目录は `_reference/code_audit_20261014/`。

## SetActive / HoleOutProp / SetInactive
[원작 코드 판독]
```
SetActive():
    enabled = true
    awakeDuration = 0
    autoSleep = propBehavior._useSimplePhysics ? 0 : 2

HoleOutProp():
    return  // 0x1CC58EC ret 한 명령

SetInactive():
    enabled = false  // 이 함수 단독으로 Rigidbody.Sleep하지 않음
```
PropBehavior+80은 `_useSimplePhysics`; +81 `_isBigProp`, +D0 runtimebig, +4A CanFallSlow와 혼동하지 않는다. SetActive는 stayAtSlowSpeedDuration을 여기서 초기화하지 않는다.

## FixedUpdate 정확한 분기
finite 정상값을 대상으로 옮긴 의사코드다. 부동소수 NaN/exception 의미까지 고수준 코드로 완전 대체했다고 주장하지 않는다.
```
if (awakeDuration < 0.5):
    if (this.transform.position.y < 6):
        awakeDuration += Time.fixedDeltaTime
    return

rb = propBehavior.Rigidbody
if (rb.isKinematic):
    rb.interpolation = 0
    this.enabled = false
    return

if (propBehavior.IsEaten): return
if (this.transform.position.y < -0.5): return

if (autoSleep > 0):
    autoSleep -= Time.deltaTime
if (autoSleep <= 0):
    awakeDuration = 0
    stayAtSlowSpeedDuration = 0
    propBehavior.SetInActive() // virtual slot10
```

- 초기0.5초 누적은 **y<6인 FixedUpdate에서만** 진행한다. y>=6이면 이 단계가 보류되며 duration을0으로 되돌리지는 않는다. 0.5에 도달한 그 스텝도 뒤의 autoSleep 카운트다운을 실행하지 않고 반환한다.
- 초기 대기를 통과한 다음에는 y>=6 제한이 다시 적용되지 않는다. y<-0.5인 동안에는2초 countdown이 보류된다.
- Update가 아니라 **FixedUpdate**다. 뒤 countdown에서 호출하는 API는 원문상 deltaTime이며 초기 누적은 fixedDeltaTime이다. 임의 렌더 프레임 타이머로 바꾸지 않는다.
- **속도/각속도/이동거리/회전량/접촉 상태/IsSleeping/홀 내부·외부/isTriggered를 검사하지 않는다.** 움직이는 중이라도 위 타이머/높이 조건이 만족되면 SetInActive에 도달할 수 있다.
- 생성자가 velMin/angularMin에0.10000000149를 쓰고 SetMagnitute가 값을 저장하지만, 이 FixedUpdate는 그 필드를 읽지 않는다. 선언만 보고 속도0.1 이하 유지시간 조건을 창작하지 않는다.
- IsAnimateAtHome()는 prop+38 반환 함수이지만 이 FixedUpdate에서 호출하지 않는다. 필드/함수 존재와 실제 소비 경로를 구분.

## 실제 kinematic 전환
0x1CC5A28..38은 클래스 vtable+1D8의 함수/MethodInfo를 tailcall. 선언상 PropBehavior.SetInActive가 slot10인 것과 일치하며, 별도 SetSleep0x1CC5A40도 같은 dispatch를 한다.

`disasm_021e2e60.txt`: velocity/angularVelocity0 → IsActive=false → interpolation0 → PropAutoSleep.SetInactive(enabledfalse) → ActiveCounter.CancelWaiting → rb.isKinematic=true → rb.Sleep → PropCullingManager.OnPropDeactivated.

즉 단순 `Cannon.body.sleep()`만으로는 IsActive/counter/kinematic/interpolation 상태까지 같은 경로를 재현하지 못한다. base의 virtual 메서드 호출이므로 개별 파생 프롭 override가 있으면 그 클래스 근거를 별도로 확인할 것.

## 다시 활성화
`PROP_ACTIVATION.md` / disasm_021e2b98.txt: ActivatePropImmediate는 IsActive=true → AutoSleep.SetActive → ActiveCounter.StartCounting → rb.isKinematic=false/interpolation1/WakeUp. layer7 진입의 !Eaten&&!Active&&gameplayActive 게이트 및 PullObjectInRange의 비활성 Activate 경로는 기존 자료대로 구분.

홀을 벗어나야만 sleep 타이머가 시작된다는 근거가 없다. HoleOutProp는 빈 함수다. 반대로 sleep 후 홀 안에 남은 객체가 어떤 상위 overlap/pull 스케줄로 재활성화되는지까지 이 문서만으로 보장하지 않는다. 웹 지면 재생성 wake 정책/접촉 wake 정책은 엔진 adapter와 게임 활성 계약을 따로 표시한다.

## 성능 재검증에 필요한 경계 [자체 제안]
현재 동일 경로 trace에 bodyType/IsActive/autoSleep component enabled/awakeDuration/autoSleep remaining/rootY/useSimplePhysics 및 SetInActive·Activate 호출 횟수를 넣어 A/B한다. shape/목표/성장/시간을 바꾸지 않고 이 누락된 lifecycle로 narrowphase 활성 개수가 줄어드는지 확인할 수 있다. y>=6의 초기 지연이나 y<-0.5의 낙하 예외를 임의로 제거해 성능을 올린 결과를 원작 복원이라고 하지 않는다. Cannon/PhysX solver·접촉 동등성은 별개 미검증이다.
