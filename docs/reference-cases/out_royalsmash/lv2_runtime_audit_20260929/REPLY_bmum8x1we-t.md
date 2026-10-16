# bmum8x1we-t — 두 시간설정 역전 정정

원본 `globalgamemanagers#8`의 명명된 typetree 필드 기준:

| 필드 | 원작값 |
|---|---:|
| Fixed Timestep | 0.0125 |
| Maximum Allowed Timestep / Time.maximumDeltaTime | 0.02500000037252903 |
| Maximum Particle Timestep / Time.maximumParticleDeltaTime | 0.125 |

Claude 보고 및 현재 C: ProjectSettings/TimeManager.asset을 읽기 대조한 결과 Allowed=.125 / Particle=.025로 **역전**돼 있었다. 원본이 최대10스텝이라는 설명도 잘못된 값에 기초한다. 원본 명목 비율은 .025/.0125=2이며, 이 비율을 모든 실행 상황의 정확한 프레임 스텝 수로 일반화하지 않는다.

브리지 `bmum8xwmi-u`로 즉시 정정 발송. 정확한 값으로 복원하고 실행값을 함께 기록한 뒤 패치 상태 lv2/lv3 짧은 회귀 요청. 수신/적용 완료는 아직 확인하지 않았다.

old/new 활성중첩 A/B는 두 회차 시간값이 같으므로 해당 조건의 인과 증거로 유효하다. 다만 '원본 시간조건'에서의 실측으로 표기하면 안 된다. .02 A/B는 이번 원인 확인에 추가로 필요하지 않아 생략하도록 전달했다. 후속은 런타임 레벨 교체 검사와 아이템 구현.
