# 특수 객체 처리 분기

[원작 선언값] PropType enum1121: Default0 / Coin1 / CollectObject2 / SpecialObject3 / Clock20 / Energy21 / SpeedBoost22 / MagnifyingGlass23 / Bomb666 / BlindMushroom667 / ReverseMushroom668. 숫자667/668을coin/weekly로추정하면안된다.

[원작 코드 판독]
TriggerableProp.CheckPropActivationRule0x21E6440: 저장autoActivate(+0xF8)가true일때 ActivateProp, 아니면return. 모든특수객체를원작일반holder규칙에끼워넣지말것.
TriggerableProp.EatenCoroutine0x21E6454는먼저 base.PropBehavior.EatenCoroutine0x21E2F88을호출하고, 이후virtualslot14 TriggerSProp을호출. TriggerSProp0x21E653C는 propType(+0xF4),this,null을 PropTypeExtensions.InvokeSPropBehavior0x1EDC594에전달.
SpecialProp.EatenCoroutine0x21E5980는역으로 propType(+0x100),null,this로 InvokeSPropBehavior를먼저호출하고그후base를호출. 따라서special/triggerable의이벤트정산순서를동일하게뭉개면안된다.

InvokeSPropBehavior의분기에서 SpecialPropController.OnCoinObjectEaten0x21B1A8C, OnWeeklyObjectEaten0x21B1CE4, OnTriggerPropBoosterBehavior0x21B2298 등별도경로확인. 전체switch/모드/재화정산을완전히번역한것은아니다.
OnBombObjectEaten(명칭은SpecialPropController.OnBombEaten)0x21B1F50은 Player.IsImmune(static+0x2A)/Shield(+0x2C)/Invicible(+0x2B) 및별도완료/시스템flag에서반환하는guard가있다. 입력prop.IsEaten(+0x49)이false이면반환하는경로도확인.
일반발동경로는 CountDownClock.Pause(true), DisablePlayerController, SetPlayerInvicible, PlayerFx.PlayerSPropFx, SFX, GameRefManager.OnBombTriggering0x1E3AFC0 및DelayedCall로이어진다. '폭탄도일반목표로점수만주고즉시삭제'와다른연출/상태전환이있다.
모든branch의골드/실패판정/continue/tut 예외를완전히복원한것은아니며,서버재화권한이나광고구매를이문서로연결하지않는다. 일반레벨preview에선미지원특수모드를제외한현재범위를유지할수있다.
