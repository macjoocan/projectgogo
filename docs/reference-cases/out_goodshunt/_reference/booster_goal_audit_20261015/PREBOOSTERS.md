# ExtraTime / Lightning 실제 적용 콜백

2026-10-15. [원작 코드 판독] 아래 RVA의 disasm 파일은 같은 폴더, 원본 ELF offset/읽은 코드 SHA 포함. 원작 미실행. 메서드 경계는 다음 선언 기준. 구매·광고·계정 소비·prelevel 선택 UI 전체를 복원했다는 뜻은 아니다.

## ExtraTime: 실제 +60초

BoosterManager.OnExtraTime0x1EA1950 → Clock.PrepareAddTime0x1D30BFC → StateGame.OnUsePreboosterTime0x1D7A024 → C_PreBoosterFlyingAnim(type1). enum PreBoosterType은 Lightning0/ExtraTime1.

비행 coroutine MoveNext0x1D7C2A0에서 type1은 DoExtraTimerSeq0x1D7A340 호출(0x1D7CA18). 도착 연출 콜백 **StateGame.<>c__DisplayClass121_0.<DoExtraTimerSeq>b__2 0x1D7B92C**가 실제 적용한다:

- 0x1D7B9D0 `mov w8,#0x42700000` → float **60**.
- 0x1D7B9DC Clock.AddTime0x1D30CC4(60) 호출.
- AddTime0x1D30DF8..E14: remaining(+74)에 +60, AddTotalTime(amount,false)도 호출. 표시용 tween은 이전 remaining→새 remaining **1초**.
- PrepareAddTime은 isPaused(+90)=true만 대입. AddTime의 OnKill callback0x1D31D74가 해당 bool=false 복구. OnStepComplete0x1D31CB4는 시간 문자열/slider 갱신.

설명 문자열만 보고60을 채운 것이 아니라 실제 실행 경로의 상수와 AddTime 호출을 확인했다. timeScale=0으로 전체 물리를 정지시키는 함수가 아니다. 표시 tween을 실제 게임 시간 증가와 따로 두고, 완료/kill시 pause 복구 계약을 보존한다. 구매 성공 시 자동 prelevel 선택 여부 등은 별도 미확정.

## Lightning: 이 버튼은 2회 강제 성장 점수 적용

**LightningButton.<Execute>b__6_0 0x21F5A84**: 0x21F5AC4 `mov w1,#2` → 0x21F5AD0 **BoosterManager.OnUseLightning(int levelIncrease)0x1EA17D0**. 따라서 이 prebooster 버튼의 인자는 **2**. `Constant.Booster.LIGHTNING_VALUE=10` 선언만으로10을 넣는 해석은 폐기. 다른 호출 주체가 다른 levelIncrease를 전달할 수 있으므로 모든 호출이2라는 전수 주장도 하지 않는다.

LightningButton.Execute0x21F4E74는 해금 검사 뒤 queue등록: PreBoosterType.Lightning0, duration1.5, callback=<Execute>b__6_0(0x21F51DC..F4). 이1.5는 queue 연출용이며 지속효과15초와 다르다. Execute에는 선택/사용수량 처리도 있으나 이 문서로 원격·유료 소비를 복원하지 않는다.

OnUseLightning은 CheatPanel.IsNoBooster면 return. closure.levelIncrease에 인자를 저장하고 StateGame.OnUsePreboosterLightning(callback)0x1D7A0DC 호출. 비행 coroutine→DoLightningSeq0x1D7A6E8→마지막 UI callback0x1D7BC34가 전달받은 callback을 호출(0x1D7BDBC..DDC). PlayerFx.PlayLightningFX0x21ECD80/DoStarExplodeFx0x1EA1EB0는 별도 시각 효과다.

최종 **BoosterManager.<>c__DisplayClass78_0.<OnUseLightning>b__0 0x1EA2134**:

```
upgrade = GetUpgrade(UpgradeType.HoleSize /*1*/)
for i=0; i<levelIncrease; ++i:
    if !upgrade.IsMaxedOut:
        ScoreController.ForceAdd(float(upgrade.NextStage.Price))
```

가격은 BaseUpgradeStage.private price+10 int와 선언 대조. 반복마다 NextStage getter를 호출하지만 **이 getter는 BaseUpgrade.UpgradeLevel+1 기준**이다. ForceAdd→플레이 성장은 별도 nextEnergyStage만 바꾸므로, 이 경로만 있으면 반복의 Price는 같다. 현재 플레이 cursor의 다음 price로 대체하거나, 일반 먹기값 price/2를 넣거나, 성장단계 인덱스만 임의+2하면 원문과 다르다. 자세한 구분은 LIGHTNING_UPGRADE_STATE.md. 이 callback은 물체/목표 수량을 제거하지 않는다.

ScoreController.ForceAdd0x2140068는 currentScore+=amount 후 **OnForceScoreChanged(static+20)**에 difference를 즉시 전달. 일반 OnScoreChanged와 별도. PlayerBehavior 초기화0x21E7930에서 force 이벤트 구독, **OnForceChangedScore0x21E903C**는 `TryExpandHole(difference,requireActiveGame=false)`로 연결된다. 최초 조작 전 게임활성 gate 때문에 Lightning 성장이 무시되면 이 force 경로 누락을 먼저 볼 것. 한 호출당 한 단계/잔여 차감 등 기존 TryExpandHole 계약은 유지.

UI5슬롯 Growth/Compass/Magnet/Freeze/Shield에 둘을 임의 삽입하지 않는다. 로컬 무료 검사 경로를 추가하면 원작 prebooster 실행 계약과 자체 UI·재고 정책을 분리한다.
