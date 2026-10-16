# 종료·재시도·다음 단계 흐름

[원작 코드 판독] 일반 GameModeBase 경로 기준. Bonus override 등 모든 모드의 동일한 결과를 보장하지 않는다. 재화/라이브옵스/광고/구매는 조사 범위 밖. 해당 호출이 있는 곳은 지우고 '원본에서 없었다'고 하지 않고 로컬 adapter 경계로 둔다.

## 1. 마지막 목표: 숫자0과 화면 카드 제거 완료는 별도 콜백

`LevelBehavior.OnPropEaten0x21D8664` → `CardController.ReduceCard0x1D2BD08`에 reduced/cardRemove/cardRemoveAnimComplete 세 callback 전달(0x21D8D00). 목표의 마지막 수량은 UpdateQuantity 후 dictionary에서 제거하고 onCardRemove 호출(0x1D2C0B8..CC), OnRemoveCard 연출을 예약한다(0x1D2C114).

`LevelBehavior.OnCardRemove0x21D9498`는 GoalPropData(+88) UID 제거 후 **GameRefManager.OnGoalPropsRemoved0x1E3F594** 호출. 후자는 남은 goal dictionary count가0이고 isComplete(+58)가false일 때만 종료 분기로 들어간다(0x1E3F624..664). complete=true, +5A=false, PlayFinalLevelCompleted/PlayFinnishGameFx, DisablePlayerController0x21AF694, PauseMusic. 중복 목표 콜백으로 두 번 결과창을 띄우지 않는다.

실제 카드 애니메이션 완료 callback은 `LevelBehavior.OnCardRemoveAnimComplete0x21D9500`→`OnLevelEndAllAnimComplete0x1E3F79C`. 이 함수는 +5A가true인 경우에만 진행하며 현재 앞 경로는false를 쓴다. **모든 클리어가 카드 애니메이션 완료를 무조건 기다린다고 일반화하지 않는다.** OnGoalPropsRemoved의 말미는 현재 GameMode의 virtualslot13 OnClearLevel(false) 호출이다.

OnRemoveCard0x1D2C380는 카드 연출용 지연도 있다: 저장 **animateCardDelay(+0x30)**+**.2** 후 callback, ignoreTimeScale=true(0x1D2C590..5D8). 이전 문서의 cardDoneScaleInTime(+30) 표기는 필드명 오기이며 2026-10-15 정정: cardDoneScaleInTime은 +0x3C이다. 두 저장값이 모두 .2라 이 정정은 기존 숫자를 바꾸지 않는다. ShowTick 인자로도 +0x30을 쓴다(0x1D2C530). flip callback0x1D2CF38은 GoalCard.DoFlip(callback,needShowFront=false,backFlipTime=.5)를 호출. 전체 카드 재배열/모든 special 카드 조합까지 UI 동등성 검증한 것은 아님.

일반 props 전부 먹음은 별도 `OnAllPropInLevelCollected0x1E3F818` 경로. 목표 완료와 수집물 전체개수를 동일한 승리 조건으로 바꾸지 않는다.

## 2. 기본 클리어 commit → .3초 → EndingTransition → 성공 결과

`GameModeBase.OnClearLevel0x21F37B0` → `LevelController.OnLevelCompleted0x21AF75C`(입력 비활성화/배너숨김) → `GameRefManager.OnClearLevel0x1E3F9BC`.

OnClearLevel은 complete 상태·기록/진행 갱신 및 경제·이벤트 코드를 포함한다. 현재 범위에서 commit을 UI닫기 시점까지 미루는 근거 없음. 일반 레벨 IncreaseLevel은0x1E402BC에 있고 Bonus 분기는별도다. 로컬 StageState outcome/진행 단일 commit은 해당 원작 순서를 따르는 adapter로 구분하고 경제 호출을 복제하지 않는다.

0x1E3FE28 **ClockController.OnClear0x1D3132C** 호출→freezeFlag(+7D)=false→**OnAfterClockCleared0x1E3F8F8**→**C_WaitForGoalCard** state machine0x1E45B38.

이름과 달리 그 코루틴을 단순 '모든 카드 애니메이션이 끝날 때까지 대기'로 해석하면 틀린다. 확인한 실행 순서:

1. **.30000001192092896초 UniTask.Delay**, ignoreTimeScale=false, cancellation=owner destroy(0x1E45C94..CE0).
2. **OnChangeGameState(Pause1)**(0x1E45E64). 이 직전 .3초 동안 Clock 소비가 정확히 어느 외부 gate에서 멎는지까지 이번 조사로 완전 확정하지 않았다. 입력 차단·complete 상태와 Pause 시점을 따로 보존.
3. 현재 GameMode.GetCompletePopupID를 저장. 기본 GameModeBase의 반환은 Compliment7(아래 추가 확인 경계 참조), Bonus 등 override는 별도.
4. **StateGame.PlayWinFireworks0x1D7B240**: PopupID.EndingTransition**61** LoadPopup→반환 **2.3000001907348633초**.
5. `WaitUntil(predicate)`에 위2.3초 `TimeoutWithoutException`을 연결한 await 경로. predicate0x1E428A8는 **StateLevelCompleteTransition.isSkipped staticbool**을 읽는다. 같은 TypeInfo slot0x417C3A0을 전환 OnEnter가false, skip callback이true로 쓰는 것을 교차 대조했다. 전체 카드 개수 predicate가 아니다.
6. 대기 완료 뒤 저장된 completePopupID를 LoadPopup(0x1E460DC..E4). 즉 전환과 결과는 별도창이다.

`OnClearLevel` 이후 시간/UI/게임 상태를 모두 timeScale=0으로 뭉개지 않는다. scaled 첫delay와 unscaled 전환 callback이 함께 존재한다.

## 3. EndingTransition 자체 타임라인

OnEnter0x1D980DC: isSkipped=false; `Firework2` SFX; fireworkFx GO off; .5초 뒤 FX를 on하고 **UIParticle.Play**(callback0x1D98890). 일반 ParticleSystem.Play만 호출하고 UI Particle을 무시하면 빈 화면이 될 수 있다.

PlayLogo0x1D982F8: Spine SetAnimation 및 fade/scale. 저장 기준 scale*.55로 .5초, hold 약1.400000095, 마지막 축소 .125초 경로가 있다. 세부 easing/Spine track 등 원문을 참조하며 임의 WellDone 폰트 텍스트를 원본 로고라고 하지 않는다.

OnEnter는 별도로 **2.400000095초 unscaled DelayedCall**→0x1D988D0→자신 ClosePopup(showPrevious=false). 선언 `CELEBRATION_DURATION=2.15`를 이 실제스케줄 대신 쓰지 않는다. 외부2.3초 timeout과 이2.4초는 **별도 스케줄**이며 한 값으로 맞추지 않는다.

Skip 버튼 Awake callback0x1D9874C: 즉시 isSkipped=true, **.10000000149초 unscaled** 후 별도 callback. 스킵/자동종료가 늦게 깨어나는 중복 result/FX를 만들지 않도록 로컬 runId 가드는 자체 방어로 표기 가능. 원본 가드 구현과 같다고 주장하지 않는다.

## 4. TimeUp와 Bomb는 일반 Fail보다 앞선 서로 다른 창

Clock.OnTimeUp0x1D2F528→GameMode virtual OnLevelTimeOut. **GameModeBase.OnLevelTimeOut0x21F3834**는 gameplay active인 경우 **TimeUp9 LoadPopup**→GameRefManager.OnTimeUp0x1E3BFBC(Pause1, +D9=true, 실패음, DDA카운트)→LevelController.OnTimerFinish0x21AF690. 무조건 처음부터 Fail5를 띄우는 경로가 아니다. Timer zero 판정의 1회 flag 등은 기존 Clock._Update 계약 유지.

Bomb는 기존 ../drop_gauge_audit_20261015/BOMB_FLOW_EXISTING_VALUES.md가 정본. IsImmune/Shield/Invincible guard 통과→시계pause/입력차단/1.5초 무적/FX→OnBombTriggering1.5. **1.5초 unscaled 뒤 OutOfBox15**. 자동 복구/자동 이어하기 없음.

구매·광고를 미배선할 때는 TimeUp/OutOfBox의 이어하기 버튼을 성공 처리하지 않는다. 실패를 포기하는 close도 별도 흐름:

- OutOfBox.OnNoThanksClicked0x1DA67DC는 경고/분기 후 최종 CloseAllPopups→**Fail5**(0x1DA6FF8..701C).
- TimeUp.OnNoThanksClicked0x1DBD62C는 UpdateWarning0x1DBB77C로 이어지고 최종 **Fail5**(0x1DBBF98..FA4). 경고창/경제 분기까지 모두 자동 우회한 원작 UI라고 주장하지 않는다.
- 두 코드에 하트·이벤트·광고/상점 처리가 있지만 로컬 무료/경제제외 정책은 구현 세션의 자체 경계.

## 5. Retry와 Next의 로컬 adapter 경계

Fail.TryAgain 원문 PersistentCall→StateFail.OnRestartClicked0x1D76494. 해당 함수는 하트 등 조건/전면광고 callback이 있으며, 광고를 보상 성공으로 위장하지 않고 로컬 검사경로에서 별도 다음 동작을 선택한다.

확인된 재시작 payload는 **StateFail.<ChangeState>d__26.MoveNext0x1D76AE0**: LevelController.RestartLevel0x21AF970 → GameRefManager.StartLevel(**LevelStartPlacement.Fail0**)0x1E3BA98 → OnChangeGameState(Play0) → CardStack/icon 정리 → draggable/effects 정리 → InitGame(true) 호출0x1D76C68 → WaitUntil 로딩조건 → .3000000119초 WaitForSeconds → CloseAllPopups. 새 레벨로 증가시키는 흐름 아님. 전체 로딩 predicate 해석은 미완이며 자체 재시작 로더의 완료조건을 명시.

성공창 버튼은 이름 Continue여도 원문 메서드가 **OnHomeClicked0x1D70C20**. 단순 다음 numbered map 직접로드가 아니다. ChangeState0x1D70CB4에는 **현재레벨==1** 조건 분기에서 튜토리얼 마무리→Null2→OnGameToHome(false)→StatePrebooster.OnPlayClicked(**Next3**,true) 경로(0x1D70E48..F10)가 있고, 다른 레벨은 별도 홈·광고·다이얼로그 라우팅 분기를 가진다. 모든 레벨 자동 next나 항상 홈 한 가지만 원작이라고 단정하지 않는다.

사용자 범위가 인게임만이므로 '성공 결과→로컬 다음 맵/로컬 준비 선택'은 **자체 라우팅 adapter**로 표시하고 원작 결과 연출/commit과 분리할 수 있다. 초기 조작 전 clock/menu camera gate, 원본2회 Lightning/+60 prebooster 계약은 다음 시작에서도 유지한다.

## 확인 범위와 남은 부분

원문 종료 지연/콜백/UI refs를 확보했지만 모든 원격 이벤트·광고·홈 다음 경로를 오프라인으로 동등 구현한 것은 아니다. GameMode별 completePopup 반환 전체, 카드 특수 연출 전체, Clock 첫.3초 gate 전체, loading WaitUntil predicate 전체, Spine/파티클 실제 GPU 표현은 추가 검증 대상. 원작 상수를 임의 즉시성공/공통실패창으로 대체하는 근거는 없다.
