# lv2 시작 붕괴 수정 — 최종 수신 상태

2026-09-29 Claude bmum988nt-x 보고 수신. 원작 목표 named runtime 값:

- fixedDeltaTime=0.0125
- maximumDeltaTime=0.025
- maximumParticleDeltaTime=0.125

이 조건에서 lv2 active holder1/obstacle98, lv3 active holder1/obstacle54, 모두 구조 유지 보고. y최소3.49, 최대속력.60은 해당 관측 시점 값이다. 시간에 따른 속도 로그 없이는 앞선0과의 차이를 독립적으로 설명·검증한 것으로 표시하지 않는다. 원작 게임 실기 재현 검증은 아니다.

수정: RsGameplaySession에서 기존 레벨 SetActive(false) 후 Destroy, 이후 새 레벨 Instantiate. 기존 레벨과 새 레벨의 활성 충돌체 중첩이 원인이라는 동일조건 A/B 증거는 앞선 RESOLUTION 문서 참고. Start→Awake 가설 철회, 세 컴포넌트 Start 복구.

TimeManager 역전 적용은 수정 완료 보고 및 디스크 재대조. 과거 '처음부터 Maximum Allowed가 맞았다'는 표현은 특정 실행 시점에만 한정해야 한다. evidence.json에는 이전 disk .33333334가 보존돼 있다. 과거 상태의 시간 범위를 추정으로 덮지 않으며, 이는 현재 수정 완료와 별개다.

범위: 보고된 lv2 시작 붕괴 수정 및 원본 시간값에서 lv2/lv3 짧은 회귀 확인. 런타임700 전수검사는 아직 미완료. 후속은 실제 전환 경로 일괄 검사와 아이템3종. .02 추가 A/B는 필요 없음.
