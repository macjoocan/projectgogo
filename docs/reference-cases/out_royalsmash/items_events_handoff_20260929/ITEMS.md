# 인게임 아이템 구현 명세

## 원본에서 확인된 부분

| 항목 | BigBall 큰 공 | InfiniteMoves 무한 발사 | Barrage 시작 전 포격 |
|---|---:|---:|---:|
| 원본 resourceType | 2 | 3 | 7 |
| 초기 보유 [원작값] | 3 | 3 | 3 |
| 1개 구매 [원작값] | 코인700 | 코인1500 | 코인500 |
| SO 파일 | sharedassets1.assets#2190 | #2191 | #2189 |
| SO unlockLevel | 0 | 0 | 26 |
| 교체용 해금 레벨 | 18 | 22 | 26 |
| 사용 UI | 인게임 버튼 | 인게임 버튼 | Play/TryAgain 시작 전 토글 |

18/22는 이전 HUD 해금 조사와 맞춘 **교체 설정**이며 SO 0을 그대로 사용하지 않는다. 가격 출처는 같은 파일#2192 BoosterPurchaseConfig. 가격2900인 일반 변수는 이 표를 대체하지 않는다.

**BigBall [원작값/코드]**: 대포 scale 1.5, postFireHold 0.5초. OnActivate **0x3998030**은 대포 variant/scale을 바꾼다. Fire **0x3998180**은 `ReplaceLoadedBall(m_bigBallPrefab)` 후 LaunchBall을 호출한다. 큰 공 프리팹의 물성을 사용하며, 대포 scale=1.5를 공 질량/파괴 배수=1.5로 해석하지 않는다. 임의 '모든 물체 즉시파괴'를 추가하지 않는다.

**InfiniteMoves [원작값/코드]**: duration3초, fillUp0.2초, tick0.25초, 마지막1초 tick0.125초. `GrantInfiniteMoves` **0x3998774**, `NotifyMoveUsed` **0x39919BC**: 활성화 후 대기하다 **첫 발사부터** 3초를 계산하며 그 기간 발사 수를 차감하지 않는다. 버튼을 누른 순간부터 카운트다운하는 구현은 수정한다.

**Barrage [원작값]**: 3발, 발사간격0.08초, throwSpeed135, fuse1초, maxFlight3초, blastSpeed2, radius6.5, upwards1, settle0.6초. min/maxSpawnDistance3/8, backOffset1, minSeparation2, edgeInset sides/top/bottom1. ChainDetonateTnt=false, autoTrigger range2.5/speed20은 별도 저장 필드다. 필드가 있다고 무조건 TNT 연쇄 효과를 켜지 않는다. 폭탄 전체 타깃 선정/폭발 식은 이번 판독 범위 밖이므로 기존 물리 구현을 쓰고 근사 타깃 선정은 자체로 표시한다.

**소모 관련 코드 경로**: BoosterManager.CanArm **0x3994B14**는 cannon.CanShoot와 연결. Toggle **0x3993F90**에서 Count/CanArm/취소 가능성을 검사. TryFireArmed **0x3991614**에 가상 Fire 호출 뒤 SpendOne(**0x399532C**) 및 armed 해제가 있다. SpendOne은 해당 resourceType 1개를 Economy.TrySpend로 소모한다. 원본은 이 호출 반환값을 바로 분기하지 않는 경로가 있으므로, 교체 구현은 아래 트랜잭션으로 실패 시 공짜 발사를 방지한다. Instant 효과와 pre-level 전체 소모 시점은 원본 동일로 단정하지 않는다.

## 교체용 사용 계약 [자체]

공통 상태: `Idle → Armed/Pending → Committed → Running → Finished`. 상태는 attemptId와 itemUseId를 가진다. 동시에 준비 가능한 인게임 아이템은 1개, 진행 중 효과도 1개. 잠금 팝업/이어하기/실패 대기/성공 확정/포격 중에는 신규 사용 불가.

| 조작/상황 | 결과 |
|---|---|
| 잠긴 아이템 탭 | 해금 안내, 지갑 변화 없음 |
| 보유 0 탭 | 구매 팝업(이름/효과/가격/현재잔액), 자동 구매 금지 |
| 구매 확인 | 코인 차감+아이템1개 지급을 한 저장 트랜잭션으로 처리, 자동 발사 없음 |
| 보유 아이템 선택 | 준비 상태, 아직 소모 없음 |
| 같은 버튼 재탭 / 다른 아이템 선택 | 미확정 준비 취소, 소모 없음 |
| 미확정 준비 상태에서 종료 | 준비 해제, 소모 없음 |
| 효과 확정 뒤 취소/실패 | 환불 없음 |
| 저장 실패 | 소비/효과 실행 금지, 오류 알림 후 재시도 |

### 큰 공

1. 선택 시 대포 variant와 scale 변경, 버튼 강조, 다음 공 예고. 취소하면 기본 variant/scale 복원.
2. 유효한 조준 입력에 재고/CanShoot 재확인. 아이템1개 차감, useId 기록, 일반 발사 수1 감소를 **같은 상태 커밋**으로 저장한 후 큰 공 발사. 일반 탄과 동시에 발사하지 않는다.
3. 발사 후 준비 해제. 대포 포즈 유지0.5초 후 기본 복원. 공의 실제 크기·질량·콜라이더는 큰 공 프리팹 기준.
4. 재고0/조준 실패/발사 준비 실패는 아무것도 차감하지 않음. 리소스 사전 생성 검증 후 커밋한다.

### 무한 발사

1. 선택 후 게이지를0.2초에 채우고 Pending 상태. 첫 발사 전에는 취소/다른 아이템 선택 가능, 소모 없음.
2. 첫 유효 발사에서 아이템1개를 확정 소모하고 remainingEffectSeconds=3. 첫 발사를 포함해 효과 중 모든 발사는 moves를 줄이지 않는다.
3. 시간원은 교체용 GameplayClock: 플레이가 가능한 동안에만 경과. 설정 팝업/앱 백그라운드는 정지. **원본 모든 포커스/일시정지 정책과 같다는 뜻은 아님.**
4. `elapsed < 3`이면 무료. `elapsed >= 3`이면 효과 종료를 먼저 처리하고 **postInfiniteLockout 0.5초 동안 발사 차단**, 그 뒤 일반 소비로 복귀한다. 추가 조사한 원본 BallController level2#124의 저장값이다(`../cannon_ball_vfx_20260929/ball_controller.json`). 만료와 발사 같은 프레임에는 무료 발사나 일반탄 소비 없이 입력을 무시한다. 자동 발사 cooldown은 별도0.2초다.
5. Running 중 다른 아이템 선택 불가. 성공/최종 실패/포기 시 즉시 종료, 잔여시간 이월·환불 없음.

### 시작 전 포격

1. Play/TryAgain에서 토글만으로 재고 차감하지 않는다. 창 취소 시 선택 해제.
2. 레벨 로딩 성공, 타깃/폭탄 사전 검증 후 아이템1개 차감하고 포격 실행. 무료 이벤트 지급권 사용 시 지갑 차감 대신 해당 일회권을 소비한다.
3. 3발을0/0.08/0.16초에 발사. 포격 동안 플레이 입력 잠금. 마지막 폭탄 해결(착탄 폭발 또는 maxFlight 처리) 뒤0.6초 대기 후 일반 조준 허용. 이 **잠금 종료 계약은 자체**다.
4. 포격은 기본 moves를 소모하지 않는다. 타깃이 없으면 시작 전 취소/무소모. 포격으로 전부 제거되면 정상 성공을 한 번만 확정하고 일반 조준을 켜지 않는다.
5. 근사 타깃 선택 v1: 활성 장애물 월드 중심 후보를 높이 내림차순, stable obstacleId 순으로 정렬. seed로 동률 순서를 고정하고 최소 간격2를 우선 만족하는3개를 선정. 부족하면 기존 후보를 순환 재사용. 빈 후보만 무소모. 이는 원본 타깃 선정 복원이 아니다.

## 저장/중단과 UI

- 효과 커밋 이후 프로세스 종료는 이미 소비한 것으로 보존한다. 물리 장면 중간 저장 복원은 v1에서 지원하지 않는다. 재실행 시 dangling attempt를 최종 실패1회로 정리, 아이템 재지급/중복소모 없음. 하트/연승 처리와 같은 attemptId 사용.
- 아이템 사용 이벤트는 `ItemUseCommitted(useId,attemptId,itemId,quantity=1,free)` 한 번. 선택/취소/구매는 '사용 미션'에 세지 않는다. 무료 실제 사용은 미션에 포함한다.
- 버튼: Locked / Empty / Ready / Armed / Running / Disabled. 수량은 지갑의 실제 수량; 무한 발사 게이지는 남은 효과시간. 화면 복원 때 오래된 tween/coroutine은 runId로 무효화.
- 사운드/진동은 기존 Feedback 참조를 연결하되 미연결이어도 효과·저장·입력이 멈추지 않게 한다.
- 인게임 아이템3종과 코인 이어하기(+5/+10/+15)는 별개. InfiniteLives는 메타 시간제 보상이지 인게임 큰 공/무한발사 아이템이 아니다.
