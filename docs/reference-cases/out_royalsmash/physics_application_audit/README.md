# 물리 적용 검증 — 튜닝 전 수정 필요

2026-09-16. 원본 APK 정적 읽기, 현재 프로토 코드 읽기, 프로토가 번들한 Rapier 0.14.0 및 실제 exported Sim/blast 함수로 로컬 진단. 프로토 수정 없음. 원본 게임·에뮬레이터·CDN 미실행. 브라우저 실측이나 원작 플레이 동등성 검증은 아님.

## 먼저 고칠 세 가지

1. **질량**: main700의 명시 mass override 1,230건 중 **601건이 목표 질량과 1% 넘게 다름**. box44/cylinder525/cone32. `web/main.js:465`, `sim/core.mjs:103` 부근은 `mass/(w*h*d)`를 밀도로 지정하지만 실제 콜라이더는 원통/원뿔이거나 colliderScale이 적용된다. 최소 밀도0.2도 가벼운 물체의 mass를 덮어쓴다.
2. **시간**: `web/main.js:957` 이후 RAF마다 `world.step()` 한 번. 물리용 accumulator 없음. Rapier timestep은 기본1/60, 렌더 dt는 기믹 이동에만 전달. `Sim.step(1/30)`도 실제 Rapier timestep은1/60 그대로. 주사율에 따라 물리와 기믹의 시간축이 어긋난다.
3. **웹/헤드리스 폭발 불일치**: `web/gimmicks.js:169`와 `sim/core.mjs:167`의 방향·upwards·속도 제한 계산이 다르다. 같은 fixture를 실제 두 함수에 넣어 결과 차이를 재현했다. 지금 헤드리스 튜닝이 웹에 그대로 적용된다고 볼 수 없다.

| 실제 Rapier 진단 | 요청값 | 실효값 |
|---|---:|---:|
| Pinata, main00201 index242 mass | 1 | 33.666317 |
| StoneCylinder_1, main00209 mass | 4 | 3.141593 |
| CanCone_1, main00395 mass | .75 | .230315 |
| Pinata angular damping | 0 | .05 |

격리 콜라이더로 전1,230건 검사하고, 실제 Sim 생성 경로에서 위 세 shape를 추가 검증했다. `runtime_probe.json`에 전수 결과와 assertion으로 재현한 항목 저장. `checks:[]`는 사용하지 않은 초기 필드이며, 실제 확인 결과는 `summary.confirmed_reproductions`다.

폭발 fixture: mass1 body@(1,0,0), center0, force25, radius10, upwards100. 웹 velocity=(.224989,22.498875,0), Sim=(22.5,1125,0). 차이를 드러내기 위한 진단 입력이며 원작 폭발 수치라는 뜻이 아니다. 웹은 shifted-center 방향과 maxSpeed40 제한; Sim은 별도 수직 가산이며 제한 없음.

렌더당1step 스케줄의 1초 자유낙하(g=-22) 재현: 30Hz→물리.5초/낙하2.772949, 60Hz→1초/11.045898, 120Hz→2초/44.091675. 실제 브라우저 FPS 측정이 아니라 **현재 스케줄을 제어된 step 수로 재현한 실험**이다.

수정 방향: mass override는 실제 콜라이더 mass로 설정하거나 실제 shape 부피·스케일까지 반영할 것. 복합 콜라이더/추가 질량의 중복 합산과 관성도 확인. 공통 fixed-step accumulator와 bounded catch-up을 쓰고, 기믹과 물리를 같은 dt로 진행. 웹/Sim 폭발·접촉·wake를 공유하거나 동등성 테스트할 것. [Rapier 공식 질량 문서](https://rapier.rs/docs/user_guides/javascript/colliders/).

## 새로 확인한 원본 프로젝트 저장 설정

원본 base APK `com.cyphergames.royalsmash.apk!assets/bin/Data/globalgamemanagers`. `original_native_settings.json`은 원본 해시와 전체 native 설정을 포함한다.

| 항목 | 원본 저장값 | 현재 프로토/주의 |
|---|---|---|
| PhysicsManager path10 gravity | (0,-24,0) | -22. -9.81 추측도 이3D설정과 다름 |
| TimeManager path8 fixed timestep | 1764000/141120000 = .0125초,80Hz | Rapier 기본1/60 |
| maximum allowed timestep | .025초 | 현재RAF dt clamp.05와 의미도 다름 |
| solver iterations/velocity iterations | 35/7 | Rapier8과 다른 solver. 숫자만 이식해 동등하다고 하지 말 것 |
| sleep threshold/contact offset | .01/.01 | 엔진별 의미 차이 |
| bounce threshold/max angular speed | 2/50 | 기본값 확보, 실효값 검증은 별개 |

등급은 **[원작 저장값]**. 런타임 Physics.gravity/fixedDeltaTime 변경 여부는 미관측이다. Physics2D/Cloth gravity를3D근거로 혼동하지 말 것.

## 설정을 읽었지만 적용되지 않는 부분

- 현재 data/levels.json: main700, entities65,272; stabilize=false700개. physicsQuality0=697/1=3. blanket freezeUntilTouched=true를 써서 stabilize=false도 실제 Sim의 bodyType은 **Fixed**(kinematic 아님)로 시작한다. 저장 stabilize=false만으로 원작의 다른 동결 로직까지 없다고 단정하지는 않는다.
- `phys.ld/ad` 대신 B.damping(0,.05) 일괄 적용. ld는 현재 전부0이라 우연히 일치하지만 ad0인 Pinata44건은 다르다.
- `phys.df`와 `phys.b`는 실제 friction/restitution으로 연결된다. `sf`는 별도 적용되지 않는다. Unity 정지/동마찰을 Rapier 한 계수로 완전히 대응시켰다고 하면 안 된다.
- physicsQuality에 따른 solver 분기 없음. 원본 enum High0/Medium1은 이전 구조 분석 근거.
- Sim 접촉에는 웹의 bouncer 처리, fast-body 앞쪽 wake 처리 등이 그대로 공유되지 않는다. 웹의 스폰Y+1도 Sim과 차이 있어 동등성 점검 필요.
- 일반 공의 actual Sim 값: radius.49000001, mass1.20047796, friction.30000001, restitution.10000000, damping0/0, CCD=true. **현재 구현에 연결됨**을 확인한 것이며 원작 최종 월드 반경/마찰 확인과는 다르다.

## Claude 우편함 질문 답변: 미확정값을 원작값으로 승격하지 말 것

기존 `../static_physics/constructor_defaults.json`에는 아래 **[생성자 명시 초기값]** 근거가 이미 있다. 파일의 source hash/instruction VA를 보존한다. 원본 serialized prefab/씬/런타임 override가 검증되지 않았으므로 **최종 밸런스값으로 자동 교체 금지**.

| 필드 | 현재 값 | 생성자 초기값 | 판정 |
|---|---:|---:|---|
| Obstacle.m_explodeMinSpeed | 9 | 10 | 최종 실효값 미확정 |
| Obstacle.m_explodeNonBallSpeedMultiplier | 1.6 | 1.5 | 동일 |
| Ball.firstContactExplosionForce | 9 | 3 | 동일 |
| Ball.firstContactExplosionRadius | 2.6 | 4 | 동일 |
| Ball.firstContactExplosionUpwards | .8 | .5 | 동일 |
| Ball.minSpeedToDecay | 3 | 10 | 현재 소비 경로도 별도 검증 필요 |
| BallController.InitialSpeed | 42 | 5 | 생성자 값만으로42→5 변경 불가 |
| Tnt.m_autoTriggerTntSpeed | 7 | 이번 범위에서 값 미확인 | 미확정 유지 |

TNT 의미 주의: dump.cs451827의 Pinata tooltip은 `m_killBlastTriggerSpeed`를 chain propagation speed(units/s), `Tnt.m_autoTriggerTntSpeed`와 같은 knob라고 설명한다. 따라서 단순 충돌 속도 임계치로 간주하지 말 것. 현재 web/gimmicks.js209–215는 범위 내 TNT를 즉시 재귀 격발한다. 원작 본문/지연 적용은 아직 미검증.

### family 밀도 / noShatter / 발사 위치 / rider

- 이전2,491건은 **main+loop 전체**다. 현재main은1,230건. 분포: Pinata44(mass1), Stone219(4/6/8/10/12), Box142(2.5/3/3.75/5/6/6.25), JamJar424(1/2/3), Can129(.75/1/2/5), Wood103(2.5/3.75/4.5/6.25/7.5), Ice161(3/4.5/6/7.5), Piggy8(2.5). 나머지 추정family를 덮을 표본은 여기 없다. **레벨override질량 ÷ mesh AABB를 원작family밀도로 확정할 수 없다.** 실제 collider 부피·중복·scale 및 기본값/override 의미가 필요하다. 원본밀도로 주장된 기존7종도 이번에 모두 새로 검증한 것은 아니다.
- `noShatter Can/Tnt`: `*_Broken_*` 메시가 검색되지 않았다는 사실만으로 `m_explodes=false`를 입증할 수 없다. 일반 파편·공유 prefab·런타임 생성 가능성을 배제하지 못한다. 이 플래그 값은 이번에 미확정. 사용자 원본 스크린샷에 온전한 캔이 날아가는 장면은 있지만 모든 상황에서 안 부서진다는 증명은 아니다.
- CannonBase 원본level2 Transform62 위치(0,4.440000057,-25.620000839), scale 약.477936, 하위 cannon_에 추가scale 약.241685 등 중첩변환이 있다. `cannon_scene_transform_chains.json`에 원본 chain보존. base좌표를 muzzle좌표로 치환하면 안 된다. 현재 -23.06은 아직[자체]. 이번level2 이름 검색에서 BallSpawnPos/CannonFireSpawnPos의 확정 연결을 못 했으므로 실제발사위치 답은 미확정.
- Ball 기존 prefab export의 rootScale=.67, SphereCollider.localRadius=.49이다. 그대로 유지 시worldRadius=.3283. BigBall1.5→.735, BarrageBomb.7→.343. 근거는 부분legacy hierarchy ZIP이므로 fresh 원본 식별+런타임scale 검증 전 경고 수준이다. **.49를 곧바로 원작worldRadius 또는 density2.436을 원작값으로 부르지 말 것.** Unity Rigidbody는mass1.2이고2.436은 현재sphere크기로 역산한 값이다.
- 회전 받침의 rider binding: 현재 로컬 판정 수정의 방향은 합리적이나 원작이 parenting/joint/contact 중 무엇을 쓰는지 확인하지 못했다. 고정 부모화가 원작 동작이라고 승격하지 말 것. 정지 스크린샷으로는 판정 불가.
- contactEventThreshold40, wake1.2/2.6, maxSpeed40의타family전용, escape30, floorLine.75는 현재[자체] 유지. 최종원작대응 확인 안 됨.

## 재현과 완료 기준

1. `../audit_physics_sources.py`로 저장설정/프로토input프로필 수집.
2. `node ../audit_physics_runtime.mjs`로 실제 번들/Sim 진단. 코드 해시는 source_hashes.json; 후속 확인8/8일치.
3. 수정 후 main1,230건mass허용오차, 30/60/120Hz 동일wall-time 상태, 웹/Sim 같은fixture impulse/contact 결과, stabilize/damping정책을 테스트.
4. 그 다음 캠페인 튜닝. 원작최종수치·발사위치가 다확정될 때까지 멈출 필요는 없지만, 엔진적용/웹동등성 오류를 보정배율로 덮어서는 안 된다.

진단 완료이지 **물리 수정 완료/원작동일성 통과가 아니다**. 이번 턴은 audit와 파일답장만 수행했다.
