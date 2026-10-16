# Level007 적층 낙하 조사 / reply-to bmv8w8xq4-e

## 새로 읽은 원작값
`stack_physics_settings.json`: APK data.unity3d / globalgamemanagers#8 TimeManager, #10 PhysicsManager. 원본 raw SHA 포함. 소범위 순차 UnityPy 읽기, 원작 실행 없음, 첫 작업 peak commit 0.268GB.

| 항목 | 저장값 |
|---|---:|
| Fixed Timestep | 0.029999999329447746 |
| Maximum Allowed Timestep | 0.05000000074505806 |
| Maximum Particle Timestep | 0.03500000014901161 |
| Gravity.y | -40 |
| DefaultMaxDepenetrationVelocity | 10 |
| DefaultSolverIterations | 4 |
| DefaultSolverVelocityIterations | 1 |
| BounceThreshold | 3 |
| SleepThreshold | 0.004999999888241291 |
| DefaultContactOffset | 0.009999999776482582 |
| DefaultMaxAngularSpeed | 7 |

AutoSyncTransforms=false, simulationMode=0. Unity PhysX 설정을 Cannon solver 반복수에 수치만 복사해 동등성이라고 하지 않는다. 최대 관통 해소 속도 10은 전체 선속도 제한과 다른 값이다.

`stack_prop_parent_chains.json`: 정확한 이름 Plum_Red_Whole 원문 루트/자식 PPtr를 별도 추출. Apple이라는 정확한 이름의 GameObject는 이번 선택에서 발견되지 않았다; Apple225 매핑/치수는 이 조사로 확정하지 않음.

자두 Rigidbody: mass1, drag0, angularDrag20, useGravity=true, prefab.isKinematic=false, interpolate0, constraints0, **m_CollisionDetection=0**. ResetTransform 후 kinematic이 되는 런타임 상태와 저장값을 구분한다. SphereCollider radius0.1544291377067566, center(-0.01271386444568634,0.1544291377067566,0.009192824363708496), enabled=true, trigger=false. 부모 TRS는 JSON 그대로 사용. root와 collider node 둘 다 layer9. 원본 행렬 row9=4294962888, 자기 layer9 bit9=1; 원본에는 일반 prop끼리 충돌을 전부 끈다는 근거가 없다.

## 기존 코드 판독과 한계
- OnTriggerEnter 0x21E2A94: layer11 && !Eaten일 때 0x21E2B68 `fmov s0,20`, 0x21E2B74 `b Rigidbody.set_maxLinearVelocity(0x3D17FE0)`. **20은 layer11 진입 경로에서 쓰는 값**이다. 전 props 초기 maxLinearVelocity=20이라고 확대하지 않는다. 초기 선속도 상한은 현재 미확정; 저장 Rigidbody typetree에 해당 필드 없음.
- Init 0x21E1B60 / ResetTransform 0x21E22E8의 기존 판독은 원문 배치 복원, 속도 정리, kinematic/Sleep 경로다. 이 범위로 적층만을 위한 CCD/별도 초기 선속도 설정을 확정하지 않았다.
- CanFallSlow+4A는 일반 Update의 Eaten 임계를 -4에서 -15로 바꾼다. +D0 big flag와 별개. SetCanFallSlow0x21DECB0는 bool 저장만. 기존 direct BL scan0은 간접/inline/virtual 호출이 없다는 증거가 아니며, 적층 선택 상위 조건은 미확정이다. 타워라는 이유만으로 전부 켜지 않는다.
- 일반 Prop는 renderer.transform.position.y<-2.3 이후 EnableInHoleDrop에서 collider off/kinematic=true로 바뀌고 manual30*dt/max80이 시작된다. 기존 큰 impulse를 abs(velocity.y)로 물려받는 초기화와 max80 갱신을 기록할 것. 물리 적분과 수동 낙하를 같은 스텝에 중복 실행했는지도 분리한다.

## 구현 세션의 재현 로그에 요청할 항목 [자체 조사 제안]
한 렌더 프레임 안의 물리 substep별 rootY/rendererTransformY, velocityY before/after solver, 활성 전 collider overlap 깊이, IsActive/inHoleDrop/CanFallSlow, 정상 및 simple collider 상태, manual 위치 이동량, ground detach 시점, 최종 Eaten 호출 경로를 함께 기록한다. 위치의 큰 점프가 solver에서 시작됐는지, 활성화/부모 TRS 갱신인지, 같은 프레임 누적 substep인지 먼저 분리한다. 원본의 max depenetration10을 웹용 접촉 보정으로 적용한다면 파생 adapter로 표기한다; 임의 force-eat/slowfall로 증상을 숨기지 않는다.
