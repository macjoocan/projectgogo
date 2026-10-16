# 볼 물리 수정 재검토 — 부분 통과, 완료 판정 보류

2026-09-16 21:18 KST. 대상: `C:/00.SVN/MiniApp/_reference/royalsmash`의 현재 파일. 프로토 수정 없이 실행 진단만 수행했다.

## [주장]

**요청했던 directHit 제외와 조건부 ExploderMultiplier 1.2는 제대로 연결됐다. 하지만 볼 물리 전체 수정 완료는 아니다.** 표면 범위/감쇠의 원작 대응 문제와 웹–Sim 두 가지 동작 차이를 재현했다. 700레벨 튜닝 보류 유지가 타당하다.

### 1. [P1] 중심 거리 방식이 Unity와 같다는 주장은 정정 필요

- 위치: `web/gimmicks.js:175–196`. 중심이 반경 밖이면 대상에서 제외하며, 힘도 rb.translation 거리로 감쇠한다. `[근사 아님]` 주석은 근거와 반대다.
- fixture: 폭심0, 반경2, 질량1 박스 중심x=2.5, 반치수(1,.25,.25). Rapier의 실제 collider 최근접점은 x=1.5로 폭발 구와 겹친다. 현재 `blast`의 속도 변화는 **0**.
- Unity 문서상 외부 폭심은 가까운 표면점을 사용하고, 적용점까지의 거리로 감쇠한다. 내부/활성 collider 없음은 질량중심을 사용하는 예외다. 따라서 이 fixture의 surface-distance 선형 감쇠 기대 충격량은 **0.75**(force3, upwards0)이지 0이 아니다. 이는 문서 기반 계산이며 원본 게임 실측이 아니다. [Unity AddExplosionForce 공식 문서](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rigidbody.AddExplosionForce.html)
- Overlap 수집만 넓히고 감쇠를 중심 기준으로 남기면 해결되지 않는다. 회전·복합 collider 최근접점, 내부 예외, 작용점/방향 및 각속도 영향까지 분리해 시험할 것. `thawAround`가 먼저 중심 기반으로 누락시키는지도 함께 확인할 것. Unity PhysX 전체를 검증 없이 단일 식으로 동일하다고 부르지 말 것.

### 2. [P1] 튕김판의 공 가속이 Sim에 없다

- 웹 `main.js:868`은 `applyBouncer(ballRec,B.ball.speed)`를 호출한다. Sim의 contacts 기믹 분기는 TNT/Pinata만 처리하며 applyBouncer import/호출이 없다.
- 같은 접촉 이벤트, 공 속도20에서 웹 **27**, Sim **20**. 실제 production handler와 Rapier rigidbody로 재현했다.
- 웹·Sim 공통 접촉 처리 또는 동일 소비 경로로 맞추고, 재접촉·속도 상한·저속 접촉을 함께 회귀 시험할 것. 1.35 등의 Bouncer 수치 자체는 현재 코드도 `값 미확인`으로 표시하므로, 이번 시험은 **프로토 내부 동등성 검증**이지 원작 Bouncer 수치 인증이 아니다.

### 3. [P2] 낮은 속도의 첫 접촉에서 웹과 Sim 상태 전이가 다르다

- `sim/core.mjs:270`은 impact < wakeMinSpeed(1.2)면 첫 접촉 처리 전에 반환한다. 웹 `handleContacts`에는 이 조기 반환이 없다.
- impact0.6 fixture: 웹 폭발1회/firstContact=true/주변 속도1.5, Sim 폭발0회/firstContact=false/주변 속도0.
- 그 결과 Sim은 나중에 더 센 접촉에서 첫 폭발을 실행할 수도 있다. 어느 조건이 원작인지 별도 확인하되 웹·Sim 불일치는 먼저 해소해야 한다. 실제 장면에서 이런 contact-force 이벤트가 발생하는 빈도는 측정하지 않았다.

### 4. 남은 구현/표기 공백

- `minSpeedToDecay=10`은 balance.js에만 남아 있고 web/sim에서 소비되지 않는다. 원작 `hitVelocityRetention=[.5,.8,.8,.8]`의 대응도 현재 검색 범위에서 없다. 저장값을 곧바로 삭제 임계나 매 타격 감속식으로 추측해 넣지 말고 native 소비 조건을 확인할 것.
- `balance.js:124–127`은 exploderMultiplier를 아직 미적용이라고 적었지만 실제 적용된다. 주석/src 갱신 필요.
- power8 fixture는 force24/radius4를 전달한다. **반경2 유지라는 표현은 power1일 때만 맞다.** `radius*cbrt(power)`는 여전히 [자체]이며 확인한 원작 함수는 저장 반경을 직접 사용한다.
- Config fallback1/false로 비교하는 것은 허용되는 명시적 가정이다. 실제 `first_contact_force_multiplier`, `ball_mass_multiplier`, `lighter_gameplay_01` 선택값을 확인한 것은 아니다. 곱하기1 생략 자체는 결함이 아니다.

## [증거]

재현: `node D:/99.기타/out_royalsmash/review_ball_revision_20260916.mjs`

`results.json`: 11개 시험 묶음, 입력8파일 SHA256, Rapier0.14.0, 검사 시작/끝 해시 동일. 파일은 이후 변경될 수 있으므로 이 해시 시점에 한정한다. `web_handlers_executed.txt`에 실제 실행한 웹 함수 본문을 보존했다.

| 확인 항목 | 결과 |
|---|---|
| 질량 .5 / 1 / 2에 같은 impulse | 속도 3 / 1.5 / .75, 질량 역비례 통과 |
| directHit 제외 | 웹/Sim 모두 추가 폭발 속도0; 주변 물체에는 적용 |
| 일반 대상 / explodes=true | 주변 속도1.5 / 1.8, 조건부1.2 통과 |
| collider1/2 순서 반전 | 동일 결과 |
| 같은 접촉 두 번 입력 | 최초 폭발1회, 빠른 접촉 경로 통과 |
| physFor 원본 플래그 전달 | JamJar18 + Tnt2 모두 true 전달 |
| 저속 첫 접촉 | 웹/Sim 불일치 재현 |
| 튕김판 접촉 | 웹/Sim 불일치 재현 |
| 자체 power8 | force24/radius4, 원작 반경 고정과 별개 |
| 중심 밖/표면 안 | 프로토 누락 재현 |

스크립트 exit0은 **기대했던 성공과 알려진 불일치가 모두 재현됨**을 뜻한다. 전체 적합성 통과를 뜻하지 않는다. directHit 추가 폭발0은 직접 충돌 충격까지0이라는 뜻이 아니다.

## [기준]

- 저장 force3/radius2/upwards.5/ExploderMultiplier1.2: `../first_contact_verification/README.md`.
- native ForceMode1Impulse, 직접 맞은 Obstacle 제외, m_explodes 분기, Config 경로: `../force_mode_analysis/README.md` 및 asm/index 증거.
- 수정 구현의 소비 경로: 최신 production `main.js`, `gimmicks.js`, `balance.js`, `Sim.prototype.contacts/blast`.
- Unity API 의미와 원본 바이너리 호출 증거, 프로토 실행 결과를 서로 다른 근거 등급으로 유지했다.

## [공백]

- 주입한 contact-force 이벤트로 실제 handler를 실행했다. 엔진이 접촉 이벤트를 생성하는 시점/문턱, 브라우저 RAF/렌더링, 원작 Unity 실행은 이번 시험 대상이 아니다. 비물리 효과는 stub, rigidbody와 impulse는 실제 Rapier였다.
- 원작 런타임 설정, 그룹별 제외/중복 규칙, 원작 감속 전체 흐름, compound collider 관성·작용점의 일치는 미확정.
- lv1/3/9 무브 차이, 144 기둥 초기 자세, 대포 월드Y 요청은 이번 볼 수정 검토에서 재시험하지 않았다. 특히 대포Y는 이 답장으로 해결 처리하지 않는다.

## [잔여 위험]

프로토끼리도 아직 완전히 같지 않다. 튜닝으로 덮기 전에 표면 거리 대응과 웹/Sim 접촉 경로를 정리해야 한다. 이번 검토로 원작과 동일하다고 인증할 수 없으며 `original_runtime_physics_verified=false`를 유지한다. 프로토 코드·설정은 수정하지 않았고 원작 게임/에뮬레이터/CDN 접근 및 700레벨 튜닝도 하지 않았다.
