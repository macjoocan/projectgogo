# 수정 후 물리 재검증 — 부분 통과, 튜닝 보류 권고

2026-09-16 19시경 검사. 이전 보고를 덮어쓰지 않고 최신 코드로 재검증했다. 프로토 코드는 수정하지 않았다. 실제 번들 Rapier0.14.0/Sim을 사용했고, 웹 `loop`/`ballExplosion`은 현재 소스를 그대로 추출해 VM에서 실행했다. DOM·렌더·FX·접촉콜백은 시간시험에서 stub 처리했다. **브라우저 전체 플레이/원작 실행 검증은 아니다.**

근거: `results.json`, `trajectory.json`, `ball_controller_prefix.json`. 재현 도구는 상위 폴더 `recheck_physics_revision.mjs`, `recheck_ball_trajectory.mjs`, `recheck_ball_controller_prefix.py`. 최신 프로토7파일 SHA256 및 검사 시작/끝 동일 여부를 results에 기록했다. 이전 진단의 옛 밀도 수식을 복사해서 다시 검사하지 않고 **현재 Sim 생성 경로**를 전수 실행했다.

## 판정 요약

| 항목 | 결과 |
|---|---|
| 명시 mass override | **통과**. 실제 Sim1,230건 중1%초과오차0건. 종전601건 해소. 최대상대오차6.36e-8 |
| 중력 | **연결 확인**. B.gravity=-24, actual world 생성 경로도-24 |
| 일반 blast 공유 | **통과**. 웹 gimmicks.blast와 Sim.blast 동일 fixture 속도차0 |
| 80Hz 물리 시간 | **실패**. 누산기는.0125이나 실제 world.timestep=.0166666675 |
| 공 첫 접촉 폭발 | **실패**. 웹 ballExplosion이 아직 별도 가산식; Sim은공통blast |
| 감쇠 override | **실패**. ad0 Pinata44건이 여전히.05 |
| 안정화 정책/quality | **미해결**. stabilizefalse도Fixed; quality별solver정책없음 |
| 웹/Sim 전체 동등성 | **미통과**. spawnY, bouncer, wake, 판정시간 차이 남음 |
| 대포 원작 근거 | **새 확인**. Gameplay BallController.InitialSpeed 저장값135; 프로토42 |

## P0: 고정 스텝 크기를 실제 엔진에 연결해야 함

`web/main.js:307`/`sim/core.mjs:38`에서 World 생성 후 `world.timestep=B.fixedStep` 설정이 없다. 현재파일 어디에도 timestep 지정이 없다. main992–999의누산기와 Sim.step은.0125씩차감하지만 Rapier는1/60씩진행한다.

실제웹loop소스에30/60/120Hz 각1초를입력했더니 모두79회step: motion.9875초, solver1.3166667초. 80회정상스텝으로보면모션1초당물리1.3333초다. 79회는경계의부동소수점잔여.0124999999에기인하며별도epsilon/정수tick검토대상이다. 핵심은 **매step의시간정의가다른것**이다.

수정방향: 웹clearWorld와Sim생성자에서실제timestep연결,world재생성마다유지. 설정후readback및한wall-second의solver/motiontime검사. maxStepPerFrame=.025는현재실제상한이아님(main은×4=.1,최대8step;별도dtclamp=.05). 이정책을[원작동일]이라고부르면안된다.

### 아직 렌더 프레임에 붙어 있는 상태

- main971의frameNo++, preSpeed수집, wakeAhead가substep밖이다. 30Hz 한프레임여러step에서preSpeed가갱신되지않는다. 제어자유낙하fixture에서30Hz49회/60Hz19회substep에현재속도와캐시가달랐다. 충돌원인으로사용되는값이므로매물리step직전갱신필요.
- quiet/sinceShot도RAF카운터다. **boardQuiet=true를고정한판정타이머fixture**에서최초judge가30Hz.8초/60Hz.4초/120Hz.2초. 실제정착시간실측은아니지만판정창이주사율종속임을재현한다. grace6프레임도같은문제.
- physAcc는최상단초기화만있고clearWorld/loadLevel리셋이없다. 레벨전환잔여시간을명시적으로처리할것.

## P0: 첫 공 폭발은 아직 웹/Sim이 다름

일반blast는공유돼통과했다. 그러나 `main.js:864` ballExplosion은방사성분에`upwards*k*.4`를더하고, Sim.contacts는shifted-center방향의공통blast를호출한다. preSpeed 갱신도*.4대*.5로다르다.

동일mass1 body@(1,0,0), center0, 현재공설정 force9/radius2.6/upwards.8/power1:

| 경로 | velocity x | velocity y | preSpeed |
|---|---:|---:|---:|
| 실제웹ballExplosion함수 | 5.538462 | 1.772308 | 2.215385 |
| Sim 첫접촉이호출하는blast | 4.324812 | 3.459850 | 2.769231 |

같은첫타격으로후속파괴임계도달여부까지달라질수있다. 첫접촉경로도공유하고, 공/고정/kinematic제외·power·preSpeed 정책을함께테스트할것. 일반blast만통과해도전체폭발동등성을통과시켜서는안된다.

## 남은 P1 및 근거 등급

- ad0 Pinata44건여전히B.damping.angular=.05. 검사한override1,230건모두stabilizefalse에서Fixed시작. `freezeUntilTouched`가의도적근사라면[자체]로명시하고원작동일주장을제거한다.
- 웹Y에는THEME.camera.spawn[1]=1을더하지만Sim은없음. 같은대포위치와groundy0이므로사격/바닥정리기준도같지않다.
- 웹applyBouncer 및wakeAhead 대응이Sim에없음. mass수정과일반blast수정만으로웹튜닝동등성을주장할수없다.
- family density를현재collider부피와레벨별override에서역산한값은 **프로토추정값**. 실제원작기본collider/기본밀도검증없이나머지97%엔티티의원작값으로승격할수없다. 이변경은새튜닝변수이므로별도추적할것.
- mass direct설정은현재main표본에서통과. 향후복합collider에하나의전체mass를각part마다주면중복질량이된다. 이번1,230건에그런실패는없었다.

## 대포 궤적: 원본 speed135 발견

원본 `UnityDataAssetPack.apk!assets/bin/Data/level2`의MonoBehaviour124를정확한MonoScript참조(fileID1/path3422, Core.BallController)로식별했다. 원본dump.cs453767이후의**직렬화필드순서**를따라leadingpayload를읽었다. native객체offset을fileoffset으로사용하지않았다.

| 필드 | 원본저장값 / 원본payload offset |
|---|---|
| InitialSpeed | **135.0**,32,raw00000743 |
| RandomSpinRange | (10,25),36/40 |
| AimContactOffset | .300000012,44 |
| bottomDeadZoneFraction | .25,48 |
| BallSpawnPosition | file0/path24→BallSpawnPos GO24/Transform80 |
| BallPrefab | file2/path40→sharedassets2.assets GO40 Ball |

Controller rawobjectSHA256 `6a9ce2514649e0d4caec00d91b080ae7bc14b3795f3bae97e51be828b9b651f0`. PPtr후속대상들이올바른GameObject/Transform/공Rigidbody로연결되는것까지교차검증했다. 기존생성자InitialSpeed5보다**이씬저장값135가구체적근거**다. 실행중override는여전히미관측.

이번에는legacyexport뿐아니라 **Controller가참조한공을원본에서직접확인**:

- sharedassets2.assets GO40 Ball, Rigidbody58: mass1.200000048, drag0,angularDrag0, **UseGravity=true, IsKinematic=false**, CCD2.
- Transform51 scale(.670000076,.670000076,.670000076), SphereCollider60 localradius.490000010. 저장상태그대로라면월드반경약.3283. 실행시scale변경은미확인.
- BallSpawnPos Transform80 localposition(0,.12,1.51), parent93cannon_anchor→78cannon_→62CannonBase→59Arena. 전체저장chain을JSON에보존. 로컬좌표를월드좌표/최종발사방향으로오인하지말것.

### 사용자 “원작은 직선, 프로토는 포물선”에 대한 판단

**현재프로토의휨은우연한버그가아니라의도된ballisticDir + gravity결과지만, 그정도가원작과맞는다는근거는없다.** webmain646이후와Sim.ballisticDir는낮은포물선해를계산하며speed42를쓴다. 원작은저장된일반공도중력을사용하므로사진만보고gravity0로바꾸는것은근거가약하다.

실제Sim.fireAt로현재대포→(0,4.44,0), 장애물없는격리시험:

| 시험 | 엔진dt | 속도 | 시작–목표직선위최대편차 | 목표z통과까지물리시간 |
|---|---:|---:|---:|---:|
| 현재프로토 |1/60|42|.6245유닛|.4833초|
| dt만수정한진단가정 |1/80|42|.6261유닛|.4875초|
| dt+원본저장속도를넣은진단가정 |1/80|135|.0584유닛|.1500초|

이는원작을실행한결과가아니라 **현재프로토발사식에서speed와dt만바꾼반사실시험**이다. 그러나속도135가42보다약3.21배이고,같은사거리의중력휨이대략속도의제곱에반비례해크게줄어드는설명과일치한다. 원작의“거의직선처럼빠르게나감”에대한강한개선근거다. **dt만고쳐서는휘는모양이사라지지않음**도검증했다.

권고순서: timestep정합수정 → speed135/정확spawn·AimContactOffset·공scale를분리대조 → 동일장면의원본연속프레임/동영상과화면궤적·비행시간비교. 중력0직선모드는원작근거없는[자체]선택이므로자동적용하지말것. radius를.3283으로바꿀경우기존density2.436을유지하면mass1.2가깨지므로명시mass보존필수. 원작발사함수본문을복원/이식하거나원작게임을실행하지않았다.

## 최종 권고

질량·중력·일반폭발수정은인정한다. 하지만 **timestep실효값과첫공폭발동등성수정전캠페인배율튜닝은보류**가맞다. 그다음frame기반판정/감쇠/스폰/기믹차이를정리한다. 판정은“부분통과”이며물리전체수정완료가아니다.
