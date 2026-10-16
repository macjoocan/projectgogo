# lv2 시작 붕괴 — 수정 결과 및 앞선 가설 정정

2026-09-29, Claude bridge bmum8phao-r 실측 보고 수신. Codex는 현재 C: RsGameplaySession.cs에 `old.gameObject.SetActive(false); Destroy(old.gameObject);` 후 새 프리팹 Instantiate가 들어간 것을 읽기 확인했다. Codex가 직접 Play 재현한 것은 아니다.

## 결론

Claude의 동일 조건 자동 물리 A/B에서 기존 레벨의 지연 제거 동안 새 레벨과 활성 콜라이더가 중첩됐다. 먼저 기존 홀더를 비활성화한 뒤 Destroy하도록 수정하여 중첩을 제거했다. 이는 이식 로더 수정이며 원작 코드의 동일 구현을 판독했다는 뜻은 아니다.

| 관측 | 수정 전 | 수정 후 |
|---|---:|---:|
| 첫 FixedUpdate 장애물 | 126 (28+98) | 98 |
| 첫 FixedUpdate 홀더(비활성 포함) | 2 | 2 |
| 다음 프레임 홀더 | 1 | 1 |
| 이후 속력 | 5.64부터 튐 | .30/.60/.90/1.20/1.50 침강 |

최종 lv2 장애물98, y최소3.49, 최대속력0, 구조 유지 보고. 홀더 총수가2인 것 자체보다 **동시에 활성인 물리 객체 수**가 검증 기준이다. 자동 FixedUpdate에서 포착한 이 사례를 'Destroy가 있으면 언제나 첫 물리 스텝 전에 중첩한다'는 일반 규칙으로 확대하지 않는다.

## 철회 / 제한

- Start→Awake 원인설은 철회. lv2/lv3에 해당 세 컴포넌트0개이며 Claude가 Start로 복귀시킴.
- '현재 유니티 실제 플레이가50Hz'라는 Codex 앞선 표현은 정정한다. 확인한 것은 **디스크 TimeManager.asset=0.02**였고, Claude A/B 런타임 실측은 처음부터 **0.0125**였다고 보고했다. 이번 붕괴를50Hz 탓으로 결론 내리지 않는다.
- 디스크 저장설정(.02/.33333334/.03)과 원본(.0125/.025/.125)의 차이는 읽기 재확인했다. 실행값이 어디서 설정되는지는 별도 미결이다. 새 에디터 세션/빌드에서 초기 설정을 검증할 항목이며, 해결된 lv2 버그의 원인과 혼합하지 않는다.
- Script 모드 수동 스텝의 안정성은 실제 로더 자동 물리 순서의 증거가 아니다.

## 전달한 원작 초기화 근거

REPLY_bmum8cgi3-o.md 및 initialization_evidence.json, Platform_Start/Blocker_Start/Hammer_Start.asm 제공 완료. Table_Rect Surface RB 원본부터 kinematic=true/useGravity=false. 세 Start 범위 직접 setter 없음. helper/전체 생애에 setter가 없다는 확대 주장은 하지 않음.

## 다음 검증 범위

실제 로비 경로에서 lv1→2, lv2 재시도, lv2→3 전환 시 active 홀더1, active 장애물 기대 수, 무발사 안정, 잔류 공/파편 정리를 확인한다. 비활성 옛 홀더를 포함한 개수로 오탐하지 않는다. 700 에디터 스윕과 별도 런타임 검증으로 관리한다.
