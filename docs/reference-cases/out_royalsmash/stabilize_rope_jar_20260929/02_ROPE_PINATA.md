# Rope 스키마와 Pinata 연결

## 원문 [원작값]

`assets/bin/Data/95094b71c5d0049f188cddc77bd37f68#142`, MonoBehaviour Rope, **160B 전체 소비**. `rope_saved_values.json`의 fields.offset은 실제 파일 payload 위치다. `Rope.schema.cs.txt`는 전체 클래스/메서드/툴팁을 보존한다.

| 필드 | 저장값 |
|---|---:|
| endA / endB | 같은 파일 Transform 28 AnchorA / 29 AnchorB |
| extraLength / visualExtensionA | 0 / 4.9099998474 |
| segmentCount / radius / mass | 7 / 0.0799999982 / 1 |
| rigidLinks | true |
| linearSpring / linearDamper | 120000 / 3000 (soft 링크일 때만 사용) |
| maxStretch | 0.0500000007 |
| bendSpring / bendDamper | 300 / 35 |
| solverIterations / solverVelocityIterations | 80 / 40 |
| linearDamping / angularDamping | 0.5 / 0.6000000238 |
| loadMassEqualization / segmentGravityScale | 1 / 1 |
| sleepOnSpawn | false |
| maxAngularVelocity / maxLinearVelocity | 8 / 50 |
| segmentMesh | fileID97 → `assets/bin/Data/Resources/unity default resources#10206`, Cylinder |
| ropeMaterial | fileID3 → `assets/bin/Data/d12c8bf7e68a5475c88ccaf53916a45c#1`, WreckingBall_Rope |

refs에 AnchorA/B의 원본 TRS와 GameObject도 포함했다. 기본 메시 Cylinder를 누락 자산으로 버리지 않는다. visualExtensionA는 튜브 표시용이며 물리 길이·마디·관절을 늘리는 값이 아니다.

## 생성과 연결 [원작 코드 판독]

`Rope.Build` **0x3941984**:

- segmentCount를 2~24로 clamp. 저장 Pinata는 7마디.
- 끝점 world 거리의 최솟값 .05, totalLength=`max(distance,.05)+max(extraLength,0)`, segLen=totalLength/N.
- anchor world 위치를 Rope 로컬로 바꾼 N+1개 노드. extraLength가 있으면 SlackLayout(0x3942824)을 사용한다. **SlackLayout 자체의 처짐 solver는 이번에 식으로 복원하지 않았다**. 저장 Pinata extraLength=0에는 불필요하다.
- 각 rod 위치=(node[i]+node[i+1])/2, 회전=`FromToRotation(up,(node[i]-node[i+1]).normalized)`; **up이 B→A 방향**.
- rod localScale=(radius*2, max(localNodeDistance,1e-4)*.5, radius*2).
- WireJoints → 양쪽 attached entity 충돌 제외 → ApplyPhysics(segLen).

`CreateSegment` **0x394244C**: Cylinder mesh/material, CapsuleCollider direction=1(Y), radius=.5,height=2, non-kinematic RB, interpolation=1, collisionDetection=3. 원통 크기는 위 Transform scale이 담당한다.

`WireJoints` **0x3942A84**:

- 첫 rod의 anchor=(0,+1,0) → endA.
- rod i>0의 anchor=(0,+1,0) → 이전 rod의 connectedAnchor=(0,-1,0).
- 마지막 rod에 **추가 Joint**: anchor=(0,-1,0) → endB.
- 따라서 양 끝이 연결된 7마디는 **Joint 8개**(내부6+말단2). 말단 connectedAnchor는 EndOffsetLocal 결과.
- free end는 해당 끝 관절이 없다. static end에는 EnsureAnchor로 강체를 확보한다. dynamic end에는 해당 entity RB를 쓴다.
- terminal마다 ApplyLoadEqualization. connectedMassScale=`1+(load.mass/segmentMass-1)*Clamp01(equalization)`; load 유효, equalization>0, segmentMass>0, mass 비율>1인 경우만 설정. **실제 entity.mass를 바꾸지 않는다.** (0x3943424)

`ConfigureLink` **0x3943190**:

```csharp
j.connectedBody = connected;
j.autoConfigureConnectedAnchor = false;
j.anchor = anchor;
j.connectedAnchor = connectedAnchor;
j.xMotion = j.yMotion = j.zMotion = rigidLinks ? Locked : Limited;
// soft만: linearLimit.limit=0, linearLimitSpring={spring,damper}
j.angularXMotion = j.angularYMotion = j.angularZMotion = Free;
// bendSpring>0만: rotationDriveMode=Slerp,
// slerpDrive={positionSpring=bendSpring,positionDamper=bendDamper,maximumForce=float.MaxValue}
// maxStretch>0: projectionMode=PositionAndRotation,
// projectionDistance=maxStretch,projectionAngle=180; 아니면 projectionMode=None
j.enableCollision = false;
j.enablePreprocessing = false;
```

`ApplyPhysics` **0x3942DB0**: mass=segmentMass; **inertiaTensor=Vector3.one*max(mass*segLen*segLen/12,0.001)**. 생성된 Capsule의 자동 관성을 그대로 쓰는 구조가 아니다. solver/damping/velocity cap은 저장값, maxDepenetrationVelocity=3. 마지막 SyncTransforms, sleepOnSpawn이 true일 때만 Sleep.

gravityScale>=.999이면 useGravity=true. 0<scale<.999이면 useGravity=false + `ApplyScaledGravity`(0x3943748)에서 awake rod에 gravity*scale를 Acceleration으로 가한다. scale<=0이면 중력 없음. 저장값1이므로 일반 중력 사용.

## attachOffset 좌표계 — 이름만 보고 local로 해석하지 말 것

Pinata.Start **0x3939EA4**, 0x393A2D0~A308에서:
`dynamicEndB=body; dynamicOffsetB=ropeAttachOffset*m_scale; rope.enabled=true`.

`SetDynamicEnd` 인수명은 localOffset이지만 실제 Build 코드에서는:

- `AttachPointWorld` **0x3941510**: `body.transform.position + dynamicOffset` (회전/TransformPoint 없음).
- `EndOffsetLocal` **0x39413DC**: `body.transform.InverseTransformVector(dynamicOffset)`로 Joint connectedAnchor를 만든다.

즉 offset은 **빌드 시 월드 벡터로 해석한 뒤 Joint 로컬로 변환**한다. 이미 m_scale을 곱했으니 다시 TransformPoint로 회전·스케일하지 않는다. 현재 저장값(0,0,0)에서는 오차가 숨겨지지만 nonzero에서 갈린다.

## Pinata 자세 제어 [원작 코드 판독]

Start에서 restHeading=`ProjectOnPlane(body.transform.forward,Vector3.up).normalized`, restPosition=body.transform.position, **restUpLocal=body.transform.InverseTransformDirection(Vector3.up)**, maxAngularVelocity=m_maxSpin을 저장/설정한다. authored body.local up을 무조건 Vector3.up으로 가정하면 안 된다. startFrozen이면 body.isKinematic=true. 이후 rope를 동적 B끝에 연결한다.

FixedUpdate **0x393C2EC**: body 유효/nonkinematic, simulationMode!=Script일 때 **Tilt → Yaw → ReturnBoost → CameraGuard**. 아래는 원작 수식을 옮긴 의사코드이며 복사 즉시 컴파일되는 완성 컴포넌트가 아니다.

### Tilt 0x393C3D4

```csharp
if (tiltStiffness <= 0 || !rope || !rope.GetEndSegment(1)) return;
rod = rope.GetEndSegment(1);
targetUp = rod.transform.up;
currentUp = body.transform.TransformDirection(restUpLocal);
c = Vector3.Cross(currentUp, targetUp);
s = c.magnitude;
springTorque = Vector3.zero;
if (s > 1e-4f)
    springTorque = c/s * Mathf.Atan2(s,Vector3.Dot(currentUp,targetUp)) * tiltStiffness;
relativeW = body.angularVelocity - rod.angularVelocity;
tiltW = Vector3.ProjectOnPlane(relativeW,targetUp);
torque = springTorque - 2*tiltDamping*Mathf.Sqrt(tiltStiffness)*tiltW;
body.AddTorque(torque,ForceMode.Acceleration);
```

여기서는 body에만 토크를 적용하며 말단 rod에 반작용 토크를 주지 않는다. 완전 반평행이라 cross가 0에 가까울 때도 임의의 대체 축을 만들지 않는다.

### Yaw 0x393C7B8

stiffness<=0, restHeading이 0에 가까움(sqr<1e-10), 현재 forward의 수평 투영 sqr<1e-6 중 하나이면 return.

```csharp
heading=Vector3.ProjectOnPlane(body.transform.forward,Vector3.up);
angleRad=Vector3.SignedAngle(heading,restHeading,Vector3.up)*Mathf.Deg2Rad;
spin=Vector3.Dot(body.angularVelocity,Vector3.up);
tau=yawStiffness*angleRad - 2*yawDamping*Mathf.Sqrt(yawStiffness)*spin;
body.AddTorque(Vector3.up*tau,ForceMode.Acceleration);
```

SignedAngle helper 0x394F6D4~F84C도 판독하여 acos(정규화 dot)·cross 부호·Rad2Deg 계수를 확인했다.

### CameraGuard 0x393CF00

distance<=0 또는 stiffness<=0이면 return.
`penetration=restPosition.z-distance-body.position.z`가 양수인 경우만:
`body.AddForce(Vector3.forward*(penetration*stiffness - damping*Min(body.linearVelocity.z,0)), Acceleration)`.
고정 world -Z 쪽의 단면 벽이다. 현재 카메라 forward나 거리 구면으로 계산하지 않는다. 벽으로 접근할 때만 감쇠한다.

### 아직 고수준 구현으로 옮기지 않은 부분

ApplyReturnBoost 역어셈블도 동봉했지만 장애물 탐색/복귀 부스트 전체를 고수준 구현으로 옮기지는 않았다. RopeTubeView의 전체 메시 생성/UV, SlackLayout, 절단/이탈 전체 시퀀스도 완성 코드로 제공하는 범위는 아니다. 이번 판독 대상은 Rope 저장 스키마와 위 연결/물리/자세 제어다. `Pinata.schema.cs.txt`에 관련 RVA와 전체 필드가 있다.
