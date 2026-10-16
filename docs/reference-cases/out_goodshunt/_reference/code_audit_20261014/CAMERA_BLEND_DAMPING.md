# 카메라 보간 판독 보충

[원작값/원작코드판독]
CinemachineBlendDefinition.Style(enum14938): Cut0, EaseInOut1, EaseIn2, EaseOut3, HardIn4, HardOut5, Linear6, Custom7.
Brain defaultBlend stored style1/time2는 EaseInOut 2초다. Linear라고 쓰지 말 것.
CreateStandardCurves0x23431E0: style1인 standard array index1을 AnimationCurve.EaseInOut(0,0,1,1)로 생성(0x2343278~32D0); native Unity AnimationCurve.EaseInOut RVA0x3C59B38로 대조. 단순선형 alpha=t/2가 정본이 아니다.

Damper.Damp0x2365800:
if dampTime <0.0001 or abs(initial)<0.0001: return initial;
if deltaTime <0.0001: return0;
return initial*(1-expf((-4.605170249938965/dampTime)*deltaTime)).
이는 적용할 delta를 반환하며 잔여 오차 자체를 반환하는 함수가 아니다.
0xE0A6D4 raw8e5d93c0, 0x3F23D80 PLT index18(.plt0x3F23C40 / 16bytesstub)은 .rela.plt dynsym expf로 독립 확인했다.

Gameplay Transposer X/Y damping0.1 / Z0. 저장된0.1을 매프레임0.1비율 선형lerp로 해석하면 틀린다. deltaTime과 dampingTime으로 위 식을 적용하는 경로를 써야 한다. Transposer의좌표계/이전pose/reset/targetWarp 및 Brain의정밀업데이트순서 전체를 수학적으로 복제했다는 뜻은 아니다. 원작 vector Damp와 Transposer.TrackTarget body는 추가 disasm에 보존했으며 별도 frame-by-frame 검증은 아직 없다.

CAMERA_INITIAL_TRANSITION.md의 Menu -> 첫입력 Gameplay 전환과 연결한다. Intro의2초 EaseInOut과 각축 target follow damping은 서로 다른 축이며 중복으로같은 lerp를 두 번 넣는 것이 아니다.
