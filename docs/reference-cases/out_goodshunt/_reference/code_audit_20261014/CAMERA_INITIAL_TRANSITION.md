# 초기 카메라 / reply-to bmv8191v5-26

## 확인된 카메라 변경 본문
[원작 코드 판독]
PlayerBehavior.UpdateCameraOffset RVA0x21E92D8: multiplier=baseCamOffset(static+0x14)*powerUpCamOffset(static+0x18). duration/ease를 그대로 CinemachineCameraController.SetOffsetMultiplier0x213EFDC에 전달한다. 반경을 추가로 곱하거나 여기서 1.5를 곱하는 명령은 없다.

CinemachineCameraController.SetOffsetMultiplier0x213EFDC: 이전 offset tween 종료 후 duration>0이면 현재Multiplier->목표Multiplier의 Tween.DoFloat + easing, 아니면 ApplyOffsetMultiplier0x213F168 직접 호출.
ApplyOffsetMultiplier0x213F168: OffsetMultiplier에 값을 저장하고 virtualCameras 배열 전체를 순회해 각 Transposer의 followOffset에 캐시된 XYZ*value를 대입. FOV 변경은 이 함수에 없다.
VirtualCameraCase.Initialise0x2140380: Transposer의 저장 FollowOffset(+0x2C,+0x34)을 case.followOffset(+0x18,+0x20)에 캐시.
SetFollowOffsetMultiplier0x213F2D4: 캐시 원문 XYZ 각각에 value를 곱해 transposer에 대입. 이미 변경한 현재오프셋에 반복해서 곱하는 누적 배율 방식이 아니다.

PlayerBehavior..cctor0x21EAFA4 literalRVA0xE0B0C0/raw0000a0400000803f0000803f0000803f:
baseRadius=5 / powerUpMultiplier=1 / detectRadiusMultiplier=1 / baseCamOffset=1. powerUpCamOffset=1은 0x21EAFF0 별도 literal대입. initial_player_static_literals.json 원문 보존. baseRadius5는 static 초기화값이며 레벨 시작 실제 Size1 반경으로 해석하지 말 것.
CinemachineCameraController..cctor0x213FA3C: OffsetMultiplier 초기값1.
OnRadiusChangedCallback0x21E9380: 선택 stage의 cameraOffsetMultiplier(+0x28)를 baseCamOffset에 저장(0x21E9454), 0x21E9630~54에서 baseCamOffset*powerUpCamOffset를 SetOffsetMultiplier에 전달.
TryExpandHole0x21E8AC4도 stage의 cameraOffsetMultiplier로 baseCamOffset 갱신 후 UpdateCameraOffset 호출.
ResetPlayer0x21E9834는 0x21E9BF0~F8에서 upgrade.transitionDuration/transitionEase를 읽어 UpdateCameraOffset을 호출한다. Reset 본문에서 임의1.5/1.65 거리 배율을 추가하는 근거는 없다. 선택stage와 그 전에 업데이트된 baseCamOffset 경계는 유지.

## 조작 전 vs 조작 후 카메라
CameraType 원작 enum(TypeDefIndex3704): Menu=0, Gameplay=1. UnityEngine.CameraType 동명 enum과 혼동 금지.
Controller.Awake0x213F40C 마지막0x213F5DC~E0: firstCamera 저장값으로 EnableCamera 호출. 현재 저장 firstCamera=0(Menu).
LevelController.OnJoystickTouched RVA0x21AF428, 명령0x21AF51C~524: w0=1 후 EnableCamera(0x213F600). 즉 최초 이동입력 경로가 Gameplay 카메라를 선택한다. 이어 EnablePlayerController 경로가 있다.
EnableCamera0x213F600: 전체 virtualCamera priority=0 후 선택 virtualCamera priority=100. 단순히 첫 저장 priority10/0을 영구 유지하지 않는다.

저장값:
Menu #98: FOV33, FollowOffset(0,40,-30), Composer trackedOffset(0,-5,2).
Gameplay #99: FOV30, FollowOffset(0,30,-22), Follow Player#33.
Brain 저장 defaultBlend m_Style1/m_Time2. 실제 화면의 정밀 blend 시점/실행값은 아직 직접계측하지 않았다.

## 화면 크기 차이의 해석
[계산/추론] 오프셋 길이만 단순 비교하면 |MenuOffset|=50, |GameplayOffset|=sqrt(1384)=37.20215. 동일 투영높이/동일배율/대상깊이라는 근사에서 FOV까지 포함한 화면상 크기비:
50/37.20215 * tan(33deg/2)/tan(30deg/2) ~= 1.49.
따라서 원작이 약1.5배 작다는 관찰은 Menu 화면과 Gameplay 웹 화면의 비교로 설명될 수 있다. Composer 타깃 오프셋/피치/대상깊이/뷰포트가 있어서 이 계산이 정확한 모든물체배율 증명은 아니다.

05_before_agent_input.png는 Level5 Size1, 타이머02:30이며 에이전트 입력 전 캡처다. 원작 Camera telemetry를 읽은 것은 아니므로 해당프레임=Menu라고 확정하지 않되, 첫입력 전 Menu일 수 있다는 원작본문근거가 있다. 이후06/08은 최초입력과 성장도 함께 진행돼 동일 Size1 게임카메라 기준으로 사용하기 어렵다.

권장 비교: 웹도 조작 전 Menu 구도/첫입력 Gameplay 전환을 분리하고, 성장 발생 전 같은Size1·같은뷰포트·같은물체로 대조. 원작에 없는1.5배 거리 보정을 게임카메라 정본값으로 넣지 말 것. intro매칭과 영구게임카메라 비교를 분리하면 된다.

근거 disasm_021e92d8 / 0213efdc / 0213f168 / 0213f2d4 / 02140380 / 021eafa4 / 0213fa3c / 0213f40c / 021af428 / 0213f600. 원본 실행/설치/프로젝트 수정 없음.
