# 구현 연결 계약 [자체]

## 타입과 이벤트

원본 숫자 enum은 어댑터에서만 사용하고 새 카탈로그/세이브는 stable 문자열 ID를 쓴다: coin,big_ball,infinite_moves,barrage,infinite_lives_seconds. 이전 형식의 분/초 단위와 혼용하지 않는다.

`AttemptStarted(attemptId,level,difficulty,startedUtcMs,participatingInstances[])`
`ItemUseCommitted(useId,attemptId,itemId,quantity,free)`
`AttemptWon(attemptId,level,difficulty,committedUtcMs)`
`AttemptLost(attemptId,reason=failed|quit|crash,committedUtcMs)`

Won/Lost는 같은 attemptId에 상호 배타적. 종료처리를 재실행해도 아무 변화 없이 기존 결과를 반환한다. 이벤트 인스턴스는 processedOutcomeIds/processedItemUseIds로 중복을 막는다. 기간 안에 참가한 인스턴스 snapshot에만 배포한다. Started 없이 수신한 outcome은 오류로 기록하고 보류하며 임의 새 시도를 만들지 않는다.

## 공용 컴포넌트

- `IClock`: NowUtcMs/GameplayDelta. 프로덕션 로컬 시계, QA용 수동시계. 원본 서버시간 서비스 호출 없음.
- `LocalWallet`: CanAfford/TryPurchase/Consume/Grant. 정수 금액, 음수 입력 거부.
- `LocalEventService`: List/Join/ApplyOutcome/ApplyItemUse/Tick/Claim/ClaimAll/Archive. 각 이벤트 계산은 순수 reducer로 작성.
- `OfflineOpponentProvider`: 저장 seed/목표/시각→점수. 네트워크/실제유저 계정 없음.
- `LocalSaveStore`: Load/Migrate/AtomicCommit. 지갑·아이템·이벤트·중복처리목록을 **하나의 저장 envelope**에 포함.
- `PresentationQueue`: 로고/기본결과/이벤트요약/수령 애니메이션. 상태 변경을 담당하지 않음. queue item마다 runId, 닫힌 화면의 콜백 무효화.

## 저장 계약

envelope: schemaVersion,revision,profileId,wallet,attempts,events,rewardLedger,lastSeenUtcMs,debugFlags. 이벤트: instanceId,eventId,configVersion,configSnapshot,startUtcMs,endUtcMs,status,progress,claimedRewardIds,seed,botTargets,resultSnapshot,cooldownUntilMs. 보상: claimId=`instanceId/rewardId`, payload, createdUtcMs,claimedUtcMs.

Claim 동작은 `검증→지갑 증가+claim 완료+revision 증가→한 번의 저장 커밋→성공 반환→연출`. 지갑 파일과 claim 파일을 따로 쓰지 않는다. 실패한 저장은 성공 UI를 띄우지 않는다. tmp를 같은 디렉터리에 쓰고 flush 후 교체, 이전 유효 snapshot을 backup으로 보존; 플랫폼 파일교체 실패도 처리. 앱 재시작은 checksum/schema 검증 후 최신 유효 revision을 로드. 영구 저장 완료 전 데이터를 외부 UI/물리에 확정처럼 공개하지 않는다.

진행 중 이벤트의 config는 snapshot 사용. JSON 업데이트는 새 인스턴스부터. 알 수 없는 item/event ID는 삭제하지 않고 보존하며 UI에 지원되지 않는 항목으로 표시. 마이그레이션 시 새 초기 보유3/시작코인1500을 기존 계정에 재지급하지 않는다.

시계는 effectiveNow=max(deviceUtc,lastSeenUtc)를 사용해 뒤로 돌렸을 때 시간이 늘어나지 않게 한다. 앞으로 돌리면 이벤트가 끝나는 것은 오프라인판의 허용 동작. 보안 서버시간과 동등하다고 주장하지 않는다. 이벤트 타이머는 앱 종료 중에도 경과, 인게임 무한발사 GameplayClock은 일시정지 중 정지. 두 시간을 섞지 않는다.

중간 물리장면 복구 없는 v1: 저장된 진행중 attempt는 재실행 시 crash finalLost를1회 기록. 이미 won 커밋된 시도는 실패로 바꾸지 않는다. 보상/아이템 트랜잭션과 이 정책을 함께 검증한다.

## seed와 정산

고정 PRNG: uint32 xorshift32, zero seed는1로 교정. 순서 x ^= x<<13; x ^= x>>17; x ^= x<<5; 매 단계 uint32 wrap. 봇별 jitter = next() % (2*j+1) - j. 봇 목표를 생성 즉시 저장하므로 플랫폼 난수구현 차이에 의존하지 않는다.

Tick(now)는 우선 endUtcMs<=now인 Active를 결과 snapshot과 함께 Settled로 전환, 그 다음 표시 점수 계산. outcome 적용도 동일 종료 검사 후 처리한다. 결과가 생성된 뒤 봇점수/순위/보상을 다시 계산하지 않는다. 레이스/리그의 elapsed는 start 기준 UTC milliseconds.

사다리/수집의 경계 달성 시 claimable을 추가하고, 수령은 별도. 종료 시 claimable reward ledger를 남긴 채 archive 가능. 수령함에는 만료일을 두지 않는다(v1). 새 인스턴스가 이전 claimId를 재사용하지 않는다.

## Claude 구현 순서

1. 기존 메타 config에 offline_catalog를 연결하고 아이템 선택/구매/소모/효과의 분리부터 완성. 큰 공 프리팹, 무한발사 첫발 시작, 포격 시작전 토글을 Gameplay에 실제 연결.
2. wallet/save/reward ledger와 attempt 중복 가드. 기존 기본보상 처리와 충돌하지 않도록 단일 커밋 진입점으로 합친다.
3. Daily/Streak 순수 reducer와 화면. 다음 Collection, Survival, Race/League를 같은 인터페이스에 추가.
4. 기본결과 후 이벤트 요약1장, claim 동작과 연출. 이벤트 로비버튼/목록은 리소스가 없으면 자체 UI로 표시 가능.
5. QA용 별도 패널: 모든해금, +1승, 최종실패, 아이템실제사용, 시간+1h/+1d, seed설정, 세이브 export/import, 이벤트만초기화. 기본 debug off. 실제 지갑의 무단 전체초기화 버튼은 확인 단계 추가.

## 필수 수용 시험

| 입력 | 기대 |
|---|---|
| 아이템 선택→취소→재선택 | 소모0 |
| 큰 공 중복 발사 콜백 | 아이템1/일반moves1 소모, 공1개 |
| 무한 선택 후10초 대기→발사 | 그때부터3초, 아이템1소모 |
| 무한 만료와 발사 동시 | 만료 우선, 0.5초 잠금으로 발사/소모0; 잠금 후 다음 발사부터 일반moves1 |
| 포격 로딩 실패 | 무소모, 입력 복원 |
| 포격으로 전체 제거 | 승리1회, 일반발사 활성 안 함 |
| 같은 승리 이벤트 두 번 | 기본보상·이벤트점수 모두1회 |
| 이어하기 창 표시·구매 | 이벤트 패배/연승 초기화 없음 |
| 최종실패+포기 콜백 | 하트/생존탈락/연승리셋1회 |
| 연승2 달성→실패→연승2 | 첫 단계 보상 재지급 없음 |
| 수집 경계 다중 통과 | 해당 모든 보상 수령 가능 |
| 참가 전 시작한 시도 성공 | 새 이벤트에 소급 점수 없음 |
| 정확히 종료시각에 승리 | 이벤트 점수 없음, 기본보상 정상 |
| 앱 종료 후 이벤트 만료 | 다음 실행에서1회 정산, 수령함 보존 |
| 같은 claim 두 번/재실행 | 지갑1회 증가 |
| 보상 저장 중 실패 | 지갑/claim 모두 이전 snapshot, 재시도 가능 |
| 같은seed/시각 두 실행 | 모의 점수·순위 동일 |
| 단말 시계 뒤로 변경 | 이벤트 남은시간 증가 안 함 |
| JSON 교체 후 실행 | 기존 event snapshot 유지, 다음 인스턴스에만 변경 |
| 미션 아이템 선택/구매/취소 | 사용 미션 진행0 |
| 결과 연출 스킵 | 저장된 진행/보상 유지, 뒤늦은 팝업 없음 |

순수 규칙 계산 검증과 Unity PlayMode/프리팹/저장 장애 시험을 분리해서 보고한다. 이번 Codex 전달은 구현 명세·로컬 설정·계산 검증이며 Unity 구현 완료 보고가 아니다.
