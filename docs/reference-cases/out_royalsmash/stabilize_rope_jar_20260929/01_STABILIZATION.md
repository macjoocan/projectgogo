# 회전 받침: 원작 보정식과 순서

## StabilizeIsland — 0x383CA00 [원작 코드 판독]

```csharp
// center는 호출한 Platform의 rb.position. body COM과 다르다.
Vector3 r = body.worldCenterOfMass - center;
Vector3 a = linAccel
          + Vector3.Cross(angAccel, r)
          + Vector3.Cross(angVel, Vector3.Cross(angVel, r));
if (a.sqrMagnitude > 1e-4f)
    body.AddForce(a, ForceMode.Acceleration); // 0x383CDD0, mode 5
```

질량 계수·추가 boost·수동 dt 곱·AddTorque·Coriolis 항은 없다. `linearVelocity += a*dt`는 Claude의 임시 구현이며 이 API와 완전히 같은 실행 의미라고 보장하지 않는다. 관통 해소·접촉 풀이와 동일 스텝에 힘을 누적시키는 원작 API를 사용한다.

대상 선정:

1. 호출마다 static stamp(+0x28)를 증가시키고 Queue(+0x10)를 비운다.
2. static `s_alive`(+0x20)에서 `m_platformContacts`(+0xE0)에 해당 Platform이 있는 장애물을 seed로 넣는다.
3. BFS dequeue한 장애물의 body(+0xC8)가 유효하고 non-kinematic이면 위 가속도를 적용한다.
4. body가 없거나 kinematic이어도 그 장애물의 `m_contacts`(+0xD0) 순회 자체는 한다.
5. 이웃은 유효하고 이번 stamp 미방문이며, **platformContacts가 비었거나 해당 Platform을 포함할 때만** 방문한다. 다른 Platform만 접촉하는 이웃으로는 넘어가지 않는다.

따라서 상판에 직접 닿은 첫 층만 보정하면 안 된다. 위에 연결된 탑 전체가 대상이다. 두 받침에 걸친 경우도 원작은 호출별 stamp이므로 프레임 전체에 1회만 적용하는 별도 제한을 임의로 넣지 않는다. 이 함수 자체에 법선/updot, completed, sleeping 검사나 힘 상한은 없다.

## Platform.FixedUpdate — 0x393FC20 [원작 코드 판독]

1. playing이 아니거나 Animated가 아니거나 RB가 없거나 `Physics.simulationMode==Script(2)`면 return.
2. `dt=Time.fixedDeltaTime`, prevElapsed를 저장하고 elapsed+=dt. **prevElapsed<0.001이면 return**.
3. startup>0이면 `ramp=SmoothStep01((elapsed-0.001)/startup)`, 아니면 1.
4. Step으로 x/y/z offset을 구한 뒤 **`localPos=baseLocalPos + baseLocalRot * offset`**. 회전된 받침에서 offset을 그대로 더하면 다른 경로가 된다.
5. polePivot의 localScale.y=`(yOffset+1.5)/1.5`. x/z 유지.
6. axis.sqrMagnitude>1e-6이면 normalize, 아니면 Vector3.up. `spin=Normalize(spin*AngleAxis(speed*ramp*dt,axis))`.
7. targetWorldPos=parent.TransformPoint(localPos), targetWorldRot=parent.rotation*spin. 부모 없으면 그대로.
8. dt>0 && velInit일 때 **연속된 target world pose** 차분으로 velocity/accel을 구한다.
9. prevWorldPos/Rot를 이번 target으로 저장하고 velInit=true.
10. **MovePosition(target) → MoveRotation(target) → StabilizeIsland** 순서.

```csharp
vNew = (targetWorldPos - prevTargetWorldPos) / dt;
dq = targetWorldRot * Quaternion.Inverse(prevTargetWorldRot);
dq.ToAngleAxis(out degrees, out axis);
if (degrees > 180) degrees -= 360;
wNew = axis.sqrMagnitude > 1e-6f
     ? axis.normalized * (degrees * Mathf.Deg2Rad / dt) : Vector3.zero;
linAccel = (vNew - LinearVelocity) / dt;
angAccel = (wNew - AngularVelocity) / dt;
LinearVelocity = vNew;
AngularVelocity = wNew;
```

**보간된 `_driven.transform.position/rotation`을 이전 pose로 삼지 않는다.** 보간 지연이 가속도에 섞일 수 있다.

StabilizeIsland 호출 조건: linAccel.sqrMagnitude>0.01 **또는** angAccel.sqrMagnitude>0.01 **또는** AngularVelocity.sqrMagnitude>0.01. 일정 회전 중에도 구심가속도 항을 계속 적용한다. center는 Move 호출 뒤 getter로 읽은 **rb.position**(0x39402B0), 호출은 0x3940308. targetWorldPos나 worldCenterOfMass로 치환하지 않는다.

`Platform.Start` 0x393FA68: baseLocalPos/baseLocalRot와 부모를 캐시, **spin=baseLocalRot**, elapsed=0, velInit=false. x/y/z 시작값은 각각 Clamp(0,min(Min,Max),max(Min,Max)). base 회전을 spin과 최종 worldRot에 이중으로 곱하지 않는다. 기믹값/배치 주입 후 Start라는 기존 계약 유지.

## 접촉 관리 / 기본값

- MaintainContactGraph: static constructor의 **0x383DCB0에서 true** 저장. getter 0x383AFD0, setter **0x383B030**.
- setter는 값이 바뀔 때 살아 있는 모든 장애물의 m_contacts를 Clear한다. platformContacts를 지우는 코드는 없다.
- 직접 B/BL 검색에서 setter 호출은 debug `set_Contact_Group_Calculations` 0x379F378의 0x379F438 한 곳. 인라인/간접 쓰기 부재까지 보증하는 검색은 아니다.
- Enter 0x3834C20: collider GO layer가 s_obstacleLayer이면 flag를 확인한 뒤 상대 RB의 Obstacle을 HashSet에 추가(자기 자신 제외). 다른 layer이면 상대 RB로 `Platform.FromRigidbody`를 조회하여 platformContacts에 Add한다(0x38351F0~5248).
- platformContacts는 **List**이고 중복을 허용한다. compound 접촉에서 Enter마다 Add, Exit마다 Remove 1개. HashSet으로 바꾸면 첫 Exit에 지지 정보가 사라질 수 있다.
- Exit 0x383C5B0: touchingCount>0이면 감소, 0이면 airborneSince=Time.time. flag가 true이면 장애물 이웃 제거. 별도로 Platform 조회 후 platformContacts에서 1개 제거.
- m_contacts는 원작 HashSet이며 접촉 쌍별 refcount는 아니다. 더 튼튼한 refcount 구현을 도입하면 [자체 개선]으로 구분한다.
- OnEnable/OnDisable은 s_alive 등록/제거. OnDisable(0x38385B4)은 swap-remove와 aliveIndex=-1이며 모든 접촉 리스트를 정리하는 함수라고 해석하면 안 된다.
- `CollectTouchGroup` 0x382B638은 일반 BFS: null start면 return, queue만 Clear, **result는 Clear하지 않는다**. result.Add(start) 후 enqueue, 접촉 이웃의 result.Add가 true일 때 enqueue. StabilizeIsland의 다른 받침 경계 검사는 이 함수에는 없다.

## PointVelocity — 0x393F7DC

AngularVelocity.sqrMagnitude <1e-12이면 LinearVelocity만 반환. 그 외:
`LinearVelocity + Cross(AngularVelocity, point - (rb ? rb.position : transform.position))`.
이번 직접 B/BL 검색에서 호출자는 0개. 인라이닝이나 간접 호출까지 없다는 뜻은 아니다.

## 이식 검증 제안 [자체]

원작 시간값 fixedDeltaTime=.0125 / maximumDeltaTime=.025 / maximumParticleDeltaTime=.125 유지. 기존 old root 비활성화 후 Destroy, 배치 완료 SyncTransforms를 유지한다.

lv31/32/33을 로비 진입·재시도 양쪽에서 무입력 7초 재생: 활성 장애물/파괴 수, 플랫폼 seed 수/BFS 수, 보정 호출 수, target pose velocity/accel을 기록한다. 비교 변수는 보정 ON/OFF 하나만 둔다. 초기 접촉 형성 전 별도 전체 강제 seed를 넣지 않는다.

움직이는 받침의 월드 이동량을 붕괴로 판정하지 않는다. 지지 받침 좌표로 환산한 상대 변위와 실제 파괴·낙하를 함께 본다. 원작 자체가 Script 모드에서 Platform.FixedUpdate를 건너뛰므로 수동 Physics.Simulate 검사만으로 이 경로를 검증했다고 쓰지 않는다.
