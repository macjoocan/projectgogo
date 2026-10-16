# 부스터 원문 계약

## 저장값과 UI

[원작값] level3는 씬 이름이며 플레이 스테이지3이라는 뜻이 아니다. 저장 payload와 native provenance는 stored_components.json. BoosterInfo는 ../settings/0294~0300 파일.

| 종류 | enum | 해금 표시 레벨 | 실제 지속시간 | 추가 값 |
|---|---:|---:|---:|---|
| Growth |101|4|10초|range 1.600000023841858, camera 1.2000000476837158|
| Compass/Hint |103|6|15초|rotationSpeed10, onscreen5/offscreen10, sort .5초|
| Magnet |102|8|10초|detect 3.5, attractionSpeed80, absolute shrink .8999999761581421|
| Freeze |104|10|15초|발동 callback 지연 .25초 unscaled|
| ExtraTime |105|16|+60초 설명값|별도 prebooster 경로|
| Lightning |106|14|지속시간 여기서 미확정|별도 prebooster 경로|
| Shield |107|31|15초|push radius4, 기본 pushForce100|

Hint/Magnet 씬 저장 duration=0이나 PlayerBehavior.ActivateHint0x21EA154/ActivateMagnet0x21EA118가 각각15/10을 전달한다. Growth0x21EA190=10, Shield0x21EA2F8=15. 저장0을 실제0초로 쓰지 않는다.

[원작값] native 5슬롯 좌→우 **Growth, Compass, Magnet, Freeze, Shield**. x=-336.700012/-171/-.400000006/168.330002/336.200012. 부모 `Game/Panel/Booster Placement`. 원본 Canvas 좌표이며 모바일 픽셀로 단정하지 않는다.

[원작 코드 판독] IsUnlockable0x1E2FB34는 BoosterInfo.unlockLvl <= GameData.GetCurrentDisplayLevel(). 에셋 Level_### 번호와 무조건 등치하지 않는다. ExtraTime0x1EA1950→Clock.PrepareAddTime0x1D30BFC→StateGame.OnUsePreboosterTime0x1D7A024; Lightning0x1EA17D0→StateGame.OnUsePreboosterLightning0x1D7A0DC. 이 둘을 원본 5슬롯에 추가할 근거 없음. +60 실제 완료 callback 전체/Lightning 수량 전체는 미확정.

## 공통 활성·시간·재사용

[원작 코드 판독] PowerUpBase.Activate0x21F2180: 인자d==0이면 저장 duration, 아니면 d. duration/remainingDuration을 그 값으로 **재설정**, isActive=true, OnActivate 호출. API 자체에 이미 활성인 경우 차단 없음. 누적 더하기가 아니다.

Update0x21F20D8: isActive && LevelController.IsGamePlayActive && !isPaused일 때 scaled deltaTime 차감. remaining>0이면 Effect, <=0이면 Deactivate이며 만료 프레임 Effect는 호출하지 않는다. ReactOnState0x21F21F0: Play0→Pause1은 pause, Pause1→Play0 resume, Null2는 Deactivate/Clear. Growth 숫자 modifier는 pause 중 유지되며 지속시간이 멈춘다.

실제 버튼의 공통 ActivatePowerUp0x1EA1180 끝에서 **OnJoystickTouched 호출**은 구현 세션이 추가 확인한 근거. 따라서 버튼 사용이 첫 입력 역할로 게임/타이머/카메라를 시작한다. Update만 따로 호출하고 게임 활성 전이라고 영원히 대기시키면 원본 버튼 흐름과 다르다.

UI는 PressBtn0x1E2F9AC→IsActuallyDisabled0x1E2F154에서 counting/preventPress/isBuying/complete/spawning/기타 게임 gate를 검사한다. 같은 버튼 cooldown 중 재사용 차단. 내부 Activate API의 reset 정책과 UI 차단을 구분한다. StartCountCoroutine0x1E2FDB0은 이미 counting이면 return. ReactOnState0x1E306F0은 pause에 동일 enumerator 중지/resume, Null에 reset. 구매·광고는 별도 미배선 정책.

## Freeze

[원작 코드 판독] FreezeButton.OnUse0x1D1D328: OnJoystickTouched 후 Clock.isFreeze 검사. FX 다음 DelayedCall(.25,callback,**ignoreTimeScale=true**):0x1D1D4DC~4E0. 앞서 false로 전달한 문구는 폐기. callback0x1D1D784→BoosterManager.OnFreeze0x1EA171C→Clock.StartFreeze0x1D30F94. 이미 countdown coroutine이 있으면 return, 중복 활성 refresh/add 없음.

Clock._Update0x1D2EB94: CanStart && !paused && !SplashAd 후 frozen이면 elapsed += 전달dt. **elapsed>15 엄격 비교**에 EndFreeze0x1D2F078. 그 동안 일반 시간 감소를 건너뛴다. 물리 timeScale=0이 아니다. UI15초 cooldown과 .25초 후 실제 효과 시작을 분리한다.

## Magnet

[원작값/코드 판독] OnActivate0x21F08AC: Magnet trigger on, SetPowerUpValue(Magnet, range1, detect3.5, camera1, speed0). **0x21F0B08에서 instance+40 attractionSpeed를 읽고 +88하여 Shield.static+4에 대입(0x21F0B68)**. 저장80이면168. 기존 Shield100에88을 누적하는 식이 아니다. OnDeactivate0x21F14A8→Shield.ResetPushForce0x1CC7604는100으로 대입.

`notSuckingBoom`은 private bool +70, SerializeField 없음. ctor0x21F1C54/Start0x21F0888/OnActivate0x21F08AC에서 +70 대입이 발견되지 않음. [계산/조인] 새 인스턴스의 관리 메모리 zero-init이면 false. **저장true 또는 Activate때true라는 근거 없음**. 전체 외부 reflection/native쓰기까지 전수 부정한 것은 아니다. true일 때만 isHazzardObject0x21F1824(TriggerableProp && propType666) 제외. false에 폭탄을 임의 제외하지 않는다.

AttractNearbyObjects0x21F0C34는 공통 Update에서 호출한다. center=playerTransform.position, radius=EffectiveRadius*3.5, mask=0x200(layer9), buffer512. null/Eaten 제외. UID별1개/nearest sort가 아니다.

신규 물체 ShrinkForMagnet0x21E32F8: 이미 shrunk/Eaten return, DOScale(Vector3.one*.9,.3) **절대 scale**, originalMass*10, drag0, normalCollider에 lowFrictionMaterial, shrunk=true. 원래scale*.9가 아니다. sphere 밖/종료 시 ResetScale0x21E35D8: originalScale로 .3초 tween, dynamic rb의 속도0/원래mass·drag 복구, normalCollider.material=null, shrunk=false. kinematic을 임의변경하지 않는다.

힘: dir=(player.x-prop.x,0,player.z-prop.z). dXZ<.10000000149면 force skip; normalize epsilon9.999999747e-6. inactive이면 ActivateProp만 하고 이번 호출 힘 skip. 이미 active이고 d>EffectiveRadius/**1.4199999570846558**이면 AddForce(normalize(dir)*80, Acceleration5), 이후 speed>16이면 normalize(v)*16. 안쪽은 dynamic일 때 velocity=Lerp(v,(0,-30,0),Clamp01(deltaTime)); 이 near 분기에 far speed16 clamp를 추가하지 않는다. Acceleration 경로에 별도 dt를 한 번 더 곱하지 않는다.

종료는 modifier/추적 Shrink 복구/trigger off/Shield힘100. .8초 unscaled callback0x21F1DA0는 SFX 정리용이며 전체 종료를 .8초 늦추는 정책이 아니다.

## Shield

[원작 코드 판독] Activate0x1CC6314에서 IsShieldActive static+2C=true(0x1CC671C), Deactivate0x1CC6BEC에서 false(0x1CC6CE8). OnBombEaten0x21B1F50의 IsImmune/IsShieldActive/Invincible guard가 실패 연출 진입을 막는다. 배치 폭탄의 base Eaten/score callback 자체를 취소한다는 뜻 아님.

PushAwayBombs0x1CC6D08: playerTransform.position 중심 **radius4 상수**, layer9, TriggerableProp propType666 && CompareTag("Bomb") && attachedRigidbody. 외향3D 정규화 벡터에 **pushForce * Time.fixedDeltaTime**를 곱해 AddForce(VelocityChange2). 공통 Update에서 호출되더라도 원문 explicit fixedDeltaTime을 유지하며 추가로 dt를 중복 곱하지 않는다. 기본힘100(.cctor0x1CC76F0/Reset0x1CC7604); 자석 중168은 위 계약.

drag=1 후1초 **unscaled** 지연 복구. 기존 해당 rb 지연 취소 후 재예약. callback0x1CC7A08은 closure+18 저장float를 Rigidbody.drag에 대입한다. 이 값은 상위 DDA BombDragModifier 조회 결과이며 무조건0으로 고정하지 않는다.

[원작값+조인] followup_native_evidence.json: props bundle CAB-5388c821bd9df28739ab71fc81803c09 TriggerableProp1181109212370131174→GO**4642716059992348902** nameBomb, m_Layer9, m_Tag**20001**, active=true. data.unity3d/globalgamemanagers TagManager#3 custom tags [FallingItem_Physics,Bomb,effect,Column,Fridge], Bomb은 index1. 사용자태그20000+index와 일치. 원문 rawSHA도 보존. 전체 폭탄 변형이 이 GO와 동일하다는 전수보장은 아님.

## Hint/Compass

[원작 코드 판독] Activate0x21EE9CC가 LevelBehavior.GoalPropData(+A0)의 dictionary values 리스트들을 allGoalProps에 평탄화한다. **개별 물체 단위**, UID당1개 아님. Update0x21EECCC는 null/IsEaten 필터 후 Time.time>=nextSortTime 때 player와 3D squared distance sort, nextSortTime=Time.time+.5. scaled Time.time이며 공통 PowerUpBase 게임활성/pause gate 아래 호출. onscreen 최대5/offscreen최대10.

IsPropVisible0x21EF304는 WorldToViewportPoint: z>0, x/y[0,1]. occlusion raycast가 아니다. 필터 predicate0x21EFFEC의 본문은 null 또는 prop.IsEaten(+49)만 검사한다. **이미 완료된 goal UID인지 재조회하는 분기는 이 루프에 없음**. 활성화 당시 복사한 리스트에서 먹지 않은 같은UID 물체를 '카드가 완료됐으니' 임의 제거할 근거 없음. 다만 원본 GoalPropData 생성·수정 전체를 이 분석으로 완전 복원했다고 주장하지 않는다. predicate 초입0x21F0000 외부 branch0x3F23854는 별도 미해독이므로 전체 CFG 실행 증명은 보류.
