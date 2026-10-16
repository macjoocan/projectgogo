# 최초 입력과 타이머 게이트 / reply-to bmv81k76k-28

[원작 코드 판독] 일반 시작 경로는 첫 조이스틱 이동 입력에서 카메라·게임활성·시계 시작을 연결한다. 플레이 버튼에서 곧바로 시간을 감소시키는 것과는 다르다. 튜토리얼 분기가 있으므로 '모든 모드의 아무 화면 탭에서 무조건 시작'이라고 확대하지 말 것.

## 호출 순서
LevelController.OnJoystickTouched RVA0x21AF428:
1. 0x21AF508 remove_OnMovementInputActivated 호출. 최초 이동 활성화 callback의 재호출을 제거하는 경로.
2. 0x21AF51C~524 CameraType.Gameplay=1로 EnableCamera.
3. 0x21AF528 EnablePlayerController(0x21AF5C4).
4. 별도 저장 callback을 호출하고 TutorialManager 분기 확인.
5. 조건 통과 시 0x21AF5BC에서 GameRefManager.StartTimer(0x1E3A6A0)로 tail call.
카메라 blend 완료를 2초 기다린 다음 StartTimer를 호출하는 await/delay 경로는 이 본문에 없다. 정상 경로에서는 첫 입력 처리 안에서 바로 이어진다.

EnablePlayerController RVA0x21AF5C4:
0x21AF628 LevelController.IsGamePlayActive(static+0x18)=true.
PlayerBehavior.EnablePlayerPhysics 호출 후 JoystickAdapter.EnableMovementControl(0x1CC9E24).

## 튜토리얼 예외를 그대로 구분
OnJoystickTouched 후반:
- TutorialManager +0x1B9 _isCheckTutDone가 false이면 0x21AF594로 반환.
- +0x184 _inGameTut가 true이면 반환.
- PropType 숫자666(0x29A)으로 IsOnLevelTutorialBoomLevel(0x1EDCC4C)를 호출해 true이면 반환.
그 외 StartTimer 경로다. 이 조건을 모든 튜토리얼의 의미/전체 진행표로 해석한 것은 아니며, 튜토리얼 대기/별도 시작 경로는 추가 조사 범위다.

## 실제 시계 시작 연결
GameRefManager.StartTimer RVA0x1E3A6A0:
CurrentLevel(+0xDC)!=0이면 EnableGameplayInteraction(false,false) 후 OnStartTimer static delegate(+0x20)를 호출. 이어 OnStartGameplayAnim(+0x10) 호출.
EnableGameplayInteraction0x1E3A760은 disableTouch(+0xD9)=false, pause/booster 관련 플래그 해제 경로를 갖는다.

ClockController.Awake0x1D2E8B0는 0x1D2EA0C add_OnStartTimer(0x1E39998)에 콜백 등록.
등록 메서드를 clock_subscription_method_ref.json의 ELF .rela.dyn + metadata method record로 교차 확인:
metadataUsage pointer0x4179390 -> relocation addend0x43842C0 -> encoded0x60002865 -> method index5170 / declaringType952 / name <Awake>b__42_1.
해당 body RVA0x1D3188C는 mov w8,1; strb w8,[this,+0x70]; ret. _canStartTimeClock=true를 설정한다.
ClockController._Update RVA0x1D2EB94, 0x1D2EC48~54:
_canStartTimeClock(+0x70)==false이면 반환. _isAddingTime(+0x90)==true일 때도 반환. 추가 pause/freeze 등 조건 이후 카운트다운을 진행한다.
즉 StartTimer라는 이름만 본 것이 아니라 이벤트 등록/수신 flag/Update 소비까지 확인했다.

## 이식 가이드와 검증 범위
일반 레벨 준비 상태에서는 최대 시간을 표시하되 countdown flag는 별도 유지. 첫 OnMovementInputActivated에 카메라 Gameplay/IsGamePlayActive=true/정상 조건 StartTimer를 한 번 실행하도록 구성하는 것이 근거에 맞다. Intro부터 시간 차감하거나 2초 카메라 blend만큼 시간을 추가 대기하는 것은 이 본문과 다르다.

05_before_agent_input.png의 Level5 02:30 표시는 first-input clock gate와 부합한다. 그 프레임의 런타임 flag를 직접 읽은 것은 아니므로 한 장만으로 정확한 전체 시도 상태를 확정하지 않는다.
AutoStartLevel0x21AF3D0는 현재 빌드에서 ret 한 명령이다. 이 stub을 임의 자동 카운트다운 근거로 사용하지 말 것. 다른 시작 경로가 전혀 없다는 뜻도 아니다.

근거 원문: disasm_021af428 / 021af5c4 / 01e3a6a0 / 01e3a760 / 01d2e8b0 / 01d3188c / 01d2eb94 / 021af3d0. 추가 판독 peak 약0.10~0.17 GB, 원작 실행·파일 수정·계정 조작 없음.
