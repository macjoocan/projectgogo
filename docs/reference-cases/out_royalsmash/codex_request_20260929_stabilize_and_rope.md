# Codex 요청 — StabilizeIsland · Rope 원본 판독

2026-09-29 · 요청자 Claude Code (Unity 이식 세션)
대상 빌드 Royal Smash! 1.13.359 · `libil2cpp.so`

아래 둘은 **구조는 스키마로 확인했고 수치/식만 없다.** 우리가 지어낸 값으로 굳기 전에 원본을 받고 싶다.

---

## 1. 받침 라이더 안정화 (최우선)

lv32 가 시작하자마자 무너지던 원인이 여기였다. 원본 스키마에 있는데 우리가 통째로 안 옮긴 경로다.

| 심볼 | RVA | 필요한 것 |
|---|---|---|
| `Obstacle.StabilizeIsland(Platform, Vector3 linAccel, Vector3 angAccel, Vector3 angVel, Vector3 center)` | `0x383CA00` | **본문 전체.** 어떤 식으로 속도/힘을 먹이는지. ForceMode · 배수 · 조건 |
| `Obstacle.CollectTouchGroup(Obstacle start, HashSet<Obstacle> result)` | `0x382B638` | 순회 조건 (어떤 접촉을 섬에 넣는지) |
| `Platform.FixedUpdate` | `0x393FC20` | `m_linAccel 0x10C` · `m_angAccel 0x118` 계산부, `StabilizeIsland` 호출 지점과 인자 |
| `Platform.PointVelocity` | `0x393F7DC` | 본문 (호출처도) |
| `Obstacle.OnCollisionEnter` / `OnCollisionExit` | `0x3834C20` / `0x383C5B0` | `m_contacts` · `m_platformContacts` 를 넣고 빼는 조건 |
| `Obstacle.MaintainContactGraph` | — | 기본값과 켜고 끄는 지점 |

우리가 지금 넣은 임시 식(**[자체]**, `RsObstacle.StabilizeIsland`):

```
r = body.worldCenterOfMass - center
a = linAccel + (angAccel × r) + (angVel × (angVel × r))
body.linearVelocity += a * dt
```

실측 효과(플레이 모드, lv32, 발사 없이 7초):

| | 살아남은 블록 |
|---|---|
| 안정화 ON | **132 / 132** |
| 안정화 OFF | 15 / 132 (117개 바닥 낙하) |

lv31 · lv33 · lv51 · lv161 · lv627 은 ON 에서 전부 0 파괴로 회귀 없음.

---

## 2. 밧줄 (Rope)

피냐타가 안 매달려 있었다. 프리팹에 `Rope` · `AnchorA` · `AnchorB` · `TubeView` 노드는 있는데 **컴포넌트가 0개**다.

| 심볼 | 필요한 것 |
|---|---|
| `Core.Rope` 클래스 | **스키마 전체** — 필드·툴팁·저장값. 마디 수 · 마디 질량(툴팁에 "1.5-mass rod" 언급) · 조인트 종류와 설정 · `Visual Extension A` |
| `Pinata` 의 밧줄 결선 | `m_rope` (path_id 142) 가 실제로 무엇을 만드는지. `m_ropeAttachOffset` 를 어디에 먹이는지 |
| `Pinata.FixedUpdate` 또는 해당 경로 | `m_tiltStiffness`/`m_tiltDampingRatio`/`m_yawStiffness`/`m_yawDampingRatio`/`m_maxSpin` 을 **어떤 식으로** 토크에 넣는지 |
| `m_cameraGuardStiffness 100` · `m_cameraGuardDamping 16` | 무슨 용도인지 (카메라 밖으로 안 나가게 잡는 스프링?) |

이미 확보한 저장값(우리가 그대로 넣었다):
`startFrozen 1` · `tiltStiffness 60` · `tiltDampingRatio 1` · `yawStiffness 40` · `yawDampingRatio 1` ·
`maxSpin 4.5` · `ropeAttachOffset (0,0,0)` · `ropeExitHeight 15` · `ropeExitDuration 3` · `scale 1`

지금 우리 구현은 **AnchorA 를 피벗으로 한 ConfigurableJoint 한 개 + LineRenderer 한 줄**이다.
마디 사슬이 아니므로 스윙 느낌이 원작과 다를 수 있다. `Rope` 스키마를 받으면 교체한다.

---

## 3. 덤 — 유리병 파괴 이펙트

`PS_Jar_{Red,Blue,Orange,Pink,Purple,Yellow}` 6종이 프로젝트에 하나도 없다.
`Obstacle.m_impactEffect 0x70` · `m_explosionEffect 0x78` 을 읽는 호출 경로(어느 시점에 어디서 Instantiate 하는지)를 알려주면 이식한다.

---

## 4. 콜라이더 표현 — 프레임 저하의 실제 원인 (추가 2026-09-29)

"유리병 많으면 프레임 드랍" 을 런타임에서 쟀다. **파편이 아니라 멀쩡히 서 있는 블록이 비싸다.**

에디터 플레이 모드 · vsync off · 정지 상태 240프레임 중앙값:

| 레벨 | 동적 강체 | 콜라이더 | 프레임 |
|---|---|---|---|
| lv1 | 29 | 227 | 7.45 ms |
| lv32 | 132 | 1,154 | 24.40 ms |
| lv33 | 144 | 1,156 | 25.14 ms |
| **lv33 · 블록당 콜라이더 1개로 교체** | 145 | **148** | **9.93 ms** |

같은 레벨, 같은 블록 수, 콜라이더 표현만 바꿔서 **2.5배**다.

우리 `CylinderCollider` 임포터는 원통을 **BoxCollider 8개(Facet_0~7)** 로 근사한다.
각지거나 상자형은 12~13개다. 블록 144개면 콜라이더 1,152개고, 물리는 80 Hz · 솔버 35회로 돈다.

**확인 필요 — 원작 `CylinderCollider` / `BeveledBoxCollider` 가 실제로 무엇을 만드는가?**

| 심볼 | 알고 싶은 것 |
|---|---|
| `CylinderCollider` (`SolidInertiaTensor` 0x391F8C8) | `Awake`/`Start` 에서 Unity 콜라이더를 **몇 개** 어떤 타입으로 붙이는지. 볼록 MeshCollider 1개인지, Box N개인지 |
| `BeveledBoxCollider` (`SolidInertiaTensor` 0x391E040) | 같은 질문 |
| 면 수 상수 | 8 이 원작 값인지, 우리 임포터가 정한 값인지 |

볼록 MeshCollider 1개라면 우리가 샤프 수를 8배로 물고 있는 것이고, 고치면 프레임이 그대로 2.5배 난다.
**원작 확인 전에는 안 바꾼다.**

### 파괴 순간의 스파이크 (별건)

| 상황 | 그 한 프레임 |
|---|---|
| lv32 에서 132개 동시 파괴 | 308~352 ms |
| 조각 없이 130개 끄기만 | 264 ms |
| 조각 생성을 프레임당 8개로 분산 | 352 ms (효과 없음) |

지속 비용은 문제가 아니다 — 파편 828개가 살아 있는 동안 프레임은 11 ms 로 멀쩡한 레벨(24 ms)보다 가볍다.
스파이크의 75% 는 **블록을 끌 때 콜라이더 8개씩이 PhysX 에서 빠지는 비용**이다. 위 4번을 고치면 같이 줄어든다.
