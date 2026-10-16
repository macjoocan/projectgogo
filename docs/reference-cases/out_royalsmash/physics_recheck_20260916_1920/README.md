# 최신 물리 재검증 + 원본 오브젝트 물성 대조

검증: 2026-09-16 19:20–19:35 KST. 프로토 수정 없음. 원작/에뮬레이터 실행·CDN 접속 없음.

## 결론

이전 보고서의 P0 두 건(world timestep, 첫 접촉 폭발 불일치)은 해결됐다. **그러나 기본 오브젝트 물성까지 원본과 동일하다는 판정은 불가이며, 저장값 대비 구체적인 불일치를 새로 확인했다.**

레벨별 명시 질량을 적용하는 경로와, 명시값 없는 오브젝트의 기본 물성 경로를 구분해야 한다. 앞 경로의 통과가 뒤 경로의 정확성을 보장하지 않는다.

## 1. 최신 수정본 재검증

`results.json`은 현재 프로토의 실제 Sim + 번들 Rapier 0.14.0으로 실행했다. 웹은 현재 `world` 초기화, `loop`, `ballExplosion` 소스를 그대로 추출해 VM에서 실제 Rapier와 실행하고 렌더링·UI·접촉 이벤트 처리는 스텁으로 대체했다. **브라우저 E2E나 원작 런타임 비교는 아니다.** 입력 7개 해시 및 종료 시 무변경 검증 포함.

| 항목 | 결과 |
|---|---|
| 레벨 명시 질량 1,230개 | 1% 초과 불일치 0, 최대 상대 오차 약 6.36e-8 |
| 해당 1,230개 동마찰/반발/선형 감쇠 | 저장된 레벨 값과 불일치 0 (선형 감쇠는 전부 0이어서 설정 경로 누락을 탐지하지 못함) |
| 각 감쇠 | Pinata 44개: 레벨값 0인데 실제 .05, 잔존 |
| 실제 solver timestep | 웹/Sim 모두 .012500000186초, 설정 .0125와 일치 |
| 30/60/120Hz 1초 시험 | 모두 79 substeps, solver .987500015초; 부동소수 누산 잔여 1 step. 종전 1.333배 문제 해소 |
| 공통 폭발 + 실제 웹 첫 공 폭발 | 동일 입력의 웹/Sim 속도·preSpeed 차이 0 |
| 포탄 실효값(Sim) | speed 135.000005, mass 1.20000005, radius .328299999, gravityScale 1, CCD true |
| 정착 판정 | 초 단위로 수정됨. 첫 판정 .433/.417/.408초(30/60/120Hz); 프레임 경계 오차는 있지만 종전 .8/.4/.2초 문제는 해소 |

승리 판정 `destroyed >= targetTotal`, 정착 대상에서 `b.hit` 제외도 현재 코드에서 확인했다. 실제 전체 게임 클리어 E2E를 검증한 것은 아니다.

잔존: `stabilize:false` 진단의 1,230개가 최초 Fixed. 웹의 preSpeed/wakeAhead/frameNo(grace)는 아직 RAF마다 처리되고 substep 밖에 있어, 여러 substep에서 이전 preSpeed를 사용한다(이번 자유낙하 진단에서 30Hz 49회/60Hz 19회/120Hz 0회). Claude 답장에서도 spawnY +1 차이·Sim bouncer/wake 미연결·Pinata ad0는 미착수로 명시했다. 이들을 완료로 닫지 않는다.

대포는 원본에도 `UseGravity=true`인 저장 근거가 있으므로, 직선처럼 보인다는 이유로 무중력으로 바꾸면 안 된다. 원본 씬 InitialSpeed=135를 적용한 현재 결과는 빠른 탄도로 설명 가능하다. 포구 위치/조준 알고리즘과 실제 원작 런타임 궤적의 동일성은 미확정.

## 2. 이번에 새로 확보한 원본 근거

`LOCAL_LEVEL_APK_AUDIT.json` 인벤토리에서 Rigidbody가 있는 파일을 좁혀, 2MB 이하 직렬화 파일 160개를 순차 판독했다. 큰 파일 3개는 명시적으로 제외, 판독 오류 0. 원본 프리팹 루트 이름과 카탈로그 ID가 정확히 같은 **139종**을 확보했다. 카탈로그 나머지 2개 `_CannonBody`, `_CannonWheel`은 이 엔티티 프리팹 비교 대상이 아닌 시각 모델이다.

- `object_prefabs.json`: APK/파일/해시/path_id, 원본 Transform·Rigidbody·Collider, 스크립트 이름, Obstacle 저장 필드와 raw bytes.
- 133종에서 `Core.Obstacle` 상속 필드 판독. `Core.Entity.m_instanceId`를 먼저 읽고 Unity 직렬화 4바이트 정렬을 적용했다. C# 객체 메모리 offset을 파일 offset으로 사용하지 않았다.
- bool/범위/enum 검증 및 후속 `m_common` PPtr가 실제 `ObstacleCommon`으로 연결되는지 검증. 같은 이름의 UIElements.Box/Column이 아닌 **Core 네임스페이스 상속**을 사용했다.
- 루트 Rigidbody가 있는 132종은 native 타입트리 `m_Mass`도 확보했다. 파괴 조각의 Rigidbody를 본체로 오인하지 않도록 동일 루트 GO만 비교했다.
- `object_comparison.json`: 단위 인스턴스(레벨 override/scale 없음)를 실제 현재 Sim으로 만들어 effective mass/마찰/반발/감쇠/결합규칙을 조회한 결과. Fixed는 진단에 한해 Dynamic으로 전환 후 질량 재계산했다.

### 기본값 대조 결과

| 검사 | 저장 원본 대비 결과 |
|---|---|
| 본체 Rigidbody 질량 132종 | **132종 모두 1% 초과 차이** |
| Obstacle 동마찰 133종 | 132종 차이, Pinata만 일치 |
| Obstacle 반발계수 133종 | 37종 차이 |
| 원본 ComputeMass 읽기 ↔ native 저장 질량 132종 | 1% 초과 차이 0 |

아래 값은 **오버라이드 없는 단위 프리팹의 저장 기본값 ↔ 현재 프로토**이다. 원작 실행 중 최종값을 관측한 수치가 아니다.

| ID | 원본 질량 → 프로토 | 원본 동마찰 → 프로토 | 원본 반발 → 프로토 |
|---|---:|---:|---:|
| CanSquare_1 | 1.155 → .99990 | .45 → .60 | .10 → 0 |
| CanCone_1 | .90750 → .26600 | .54 → .60 | .10 → 0 |
| StoneSquare_1 | 5.14250 → 4.00000 | .54 → .60 | 0 → 0 |
| IceSquare_1 | 3.30000 → 3.00000 | .135 → .05 | 0 → 0 |
| ColorBoxSquareBlue_1 | 3.02500 → 2.59619 | .405 → .60 | 0 → 0 |
| JamJarRed_1 | 1.21000 → .99998 | .27 → .60 | .05 → 0 |
| WoodSquare_1 / BoxSquare_1 | 3.32750 → 2.50000 | .495 → .60 | 0 → 0 |
| PiggyBox_1 | 1.51250 → 2.49969 | .45 → .60 | .10 → 0 |

Main 700레벨 65,272엔티티 중 `phys`가 있는 것은 1,230개, 없는 것은 64,042개이다. 정적/기믹 엔티티까지 포함한 수이므로 **64,042개 전부 잘못됐다는 뜻은 아니다.** 다만 명시 질량 시험만으로 전체 물성 동등성을 선언할 수 없는 근거다. `B.mat`의 override mass/volume 최빈값은 본래 프리팹 기본값이 아니다. 예를 들어 Ice의 레벨 override 마찰 .05는 유효하더라도, 기본 프리팹은 .135이다.

## 3. 왜 질량이 다른가

원본 `Core.Obstacle.ComputeMass` RVA `0x383b340`을 오프라인으로 확인했다. `Component.get_transform` → `Transform.get_localScale` 호출, m_size·m_density·m_additiveMass 읽기, 상수 pool `0x14f3778`의 1.1, 최솟값 .25를 확인했다.

분석된 기본 식:

`max(0.25, (size.x * size.y * size.z * localScale.x * localScale.y * localScale.z * density + additiveMass) * 1.1)`

이는 **실제 collider 기하 부피 × family 밀도**를 쓰는 현재 fallback과 다르다. 원본 density 숫자를 단순히 Rapier setDensity에 넣는 것도 같은 식이 아니다. 종별 additiveMass까지 있으므로 원통/원뿔 부피와 질량을 섞지 않아야 한다. 계산식은 루트 Rigidbody 132개의 저장 질량과 교차 검증됐다.

근거: `mass_formula_evidence.json`, `ComputeMass_disassembly.txt`. 이 분석은 기본 메서드와 저장 프리팹을 설명하며, subclass/레벨/runtime override가 없다고 보증하지 않는다. 명시 `physicsMass`는 별도 경로로 유지해야 한다.

## 4. 다른 특성 팩터

- **정지 마찰:** 원본에는 별도 staticFriction이 있다. 프로토 생성 코드는 `df`만 단일 `.setFriction`에 전달하며 `sf`는 반영하지 않는다. 원작 PhysX와 Rapier가 동일한 마찰 모델이라고 볼 수 없다.
- **감쇠:** 일반 원본 본체 저장 drag 0/angularDrag .05와 프로토 기본은 맞지만, Pinata는 prefab 자체 `levelPhysicsOverride=true`, mass1, df/sf .15, b .5, ld/ad0이다. 현재 ad0 미적용은 별도 확정 불일치다. 값이 모두 0인 선형 감쇠 시험 통과가 `ph.ld` 전달 구현을 증명하지는 않는다.
- **결합 규칙:** 원본 frictionCombine/bounceCombine 값도 추출했다. Pinata frictionCombine 원본 enum값1, 프로토 기본0. 엔진별 enum 의미를 대응시켜야 하며 숫자만 복사하지 않는다.
- **충돌체:** 원본은 단일 메시 AABB가 아니라 복합 collider를 쓴다. 본체 Rigidbody에 연결된 enabled collider 기준 CanSquare_1/StoneSquare_1은 Box3, Blue_1은 Box12, JarRed_1은 Box14. CanCone_1은 MeshCollider. 프로토는 해당 물체에 box/cylinder/cone 단일 collider를 사용한다. 자식 계층의 별도 파편 Rigidbody collider는 제외했다. 원본 데이터에는 각 치수·중심·Transform·Mesh PPtr가 있으나, 이 비교에서 MeshCollider 메시 자체를 추출해 완전한 접촉 형상 등가 시험까지 하지는 않았다.
- **회전 관성/무게중심:** 원본 `useAnalyticInertia`와 centerOfMass 참조, 선언된 GlobalAngularInertiaMultiplier=.45가 존재한다. 프로토는 collider 기반 자동 관성에 의존한다. 저장 `m_InertiaTensor=(1,1,1)`을 최종 관성으로 복사하면 안 된다. 실제 원작의 관성 갱신 호출/효과를 확인해야 한다.
- **파괴/폭발 팩터:** Jar는 저장 explodeMinSpeed8/nonBallMultiplier1.5, Tnt10/2, 일반 다수10/1.5. 프로토 공통9/1.6과 다르다. `m_explodes`도 확보했지만 이것을 모든 파괴 가능 여부와 바로 등치하거나 기존 noShatter를 단순 치환하지 말 것. 원본 접촉 처리의 분기 의미 확인이 필요하다. Bouncer 저장 bounciness0이라는 사실 역시 특수 튕김 로직이 없다는 뜻은 아니다.

## 5. 구현 담당자에게 권고하는 순서

1. `object_comparison.json`의 ID별 원본 저장 기본값을 정본으로 삼고, family 중앙값/최빈값은 unknown fallback으로만 남긴다. mass/마찰/반발 적용을 먼저 수정한 뒤 전체 튜닝한다.
2. 우선순위는 명시 레벨 override → 원본 prefab의 활성 override → 원본 종별 기본 계산/저장값 → 추정 fallback. compound collider의 질량 총합과 COM/관성은 분리해 검증한다.
3. `ph.ld`, `ph.ad`를 실제 body에 반영하고, Pinata 활성 override와 마찰 결합규칙을 별도 처리한다. 정지 마찰·관성·복합 collider의 엔진 차이는 [근사]로 명시한다.
4. 현재 700레벨의 폭발 튜닝은 기본 질량·마찰이 달라지면 다시 달라질 수 있다. 튜닝 결과를 원작 물성의 검증 근거로 쓰지 않는다.
5. 웹/Sim의 공통 생성 로직 및 잔존 wake/spawn 차이를 정리한 후 실제 브라우저와 헤드리스의 같은 샷을 비교한다.

`original_runtime_physics_verified=false`. 로컬 정적 원본 근거와 현재 프로토 실행 결과를 대조한 것이지 원작을 실행하여 동일 동작을 확인한 것은 아니다.
