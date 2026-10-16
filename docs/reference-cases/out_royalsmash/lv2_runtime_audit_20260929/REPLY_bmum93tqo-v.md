# bmum93tqo-v — 회귀 수신, 시간설정 역전 재정정

로비 lv1/lv2, lv2 실패 재시도, 클리어 후 lv3의 수동 4경로 통과 보고 수신. 런타임700 전수검사 완료는 아님.

보고에 붙인 YAML 및 C: 현재 파일을 읽기 확인했으나 여전히 Maximum Allowed=.125 / Maximum Particle=.025로 원작과 역전이다. 정정 브리지 bmum94rno-w 발송. `TimeManager.expected.yaml`은 원작 필드값을 옮긴 이식 참고본이며 APK 원본 YAML 자체는 아니다.

원작 목표는 **Time.maximumDeltaTime=.025 / Time.maximumParticleDeltaTime=.125 / Time.fixedDeltaTime=.0125**. 숫자열로만 나열하면 반복 혼동하므로 이름을 붙인 로그로 확인 요청. 이 두 항목 수정 후 lv2 짧은 회귀만 추가하면 되며 .02 A/B는 불필요.

과거 .02 기록은 유리수 오독이 아니다. evidence.json port_time_manager.text에 당시 `Fixed Timestep: 0.02` 원문이 보존돼 있다. 현재 유리수 1764000/141120000=.0125라는 사실과 공존한다. 당시 런타임과 디스크 값이 달랐던 이유를 추정으로 확정하지 않는다. 붕괴 원인은 별도로 확인된 old/new 활성 물리 중첩이다.
