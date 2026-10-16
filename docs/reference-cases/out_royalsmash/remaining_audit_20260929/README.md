# 잔여 원본 판독 및 구현 전달 — 2026-09-29

원본 저장값과 코드 판독만 아래에 적었다. Unity 실행 검증은 아직 하지 않았다. C: 프로젝트는 수정하지 않았다.

## 1. 클리어 로고: Timeline과 애니메이션

`logo_timeline_decoded.json`: sharedassets1#2234에서 따라간 MonoBehaviour 11개를 전체 바이트 소비 검증하며 해독했다. `logo_controller_dependencies.json`은 컨트롤러 2개와 클립 3개의 원문이다.

`logo_clips_decoded.json`: 압축 streamed/constant 커브 복원. 3개 클립의 모든 대상 경로와 속성 CRC가 일치한다. 검산은 `logo_clips_validation.json`.

| 원본 클립 | 채널 | 키 | 시간 / fps / loop |
|---|---:|---:|---|
| sharedassets1#264 logo_anim_v02 | 91 | 363 | 0~2 / 60 / true |
| #265 logo_freeze_v02 | 77 | 153 | 0~0 / 60 / true |
| #271 LogoPSAnim | 4 | 38 | 0~1.4666667 / 60 / false |

freeze 클립의 길이 0은 저장값이다. 상수 채널의 시작/끝 키 시간이 같으므로 Unity에 굽는 단계에서 동일 시각·동일 값 키는 한 개로 넣어도 된다. 임의로 전체 클립을 2초로 늘리거나 loop를 끄지 않는다. Euler 채널은 `localEulerAnglesRaw`, 쿼터니언 채널과 혼용하지 않는다. `incoming_step`은 기존 cannon importer와 동일하게 처리한다.

Animator level1#1954는 실제 글자 로고의 ROYAL_SMASH_LOGO_V2 노드, controller sharedassets1#294. Animator #2018은 Root_Btn/PS_AnimatedTrail, controller #298이다. 각 클립의 animator_root를 기준으로 상대 경로를 바인딩한다. 글자는 SpriteRenderer이며 Image로 변환하면 대상 속성이 달라진다.

PlayableDirector level1#4822: Root_Btn/PlayableDirector, asset sharedassets1#2234. AnimationTrack #2250의 sceneBinding 대상은 Animator #2018이다. 실제 글자 Animator #1954와 구분한다.

| 트랙 | 시작 | 길이 | 연결 / 상태 |
|---|---:|---:|---|
| #2250 Animation | 0 | 2.05 | #2174 → 클립 #271 |
| #2251 PS_AnimatedTrail | 0.0333333 | 2.0166667 | exposed 1294477856 → level1 GO1621 |
| #2249 Confetti | 0 | 3.7333333 | exposed 485995621 → GO1435 |
| #2170 PS_LogoDust | 1.1666667 | 1.65 | exposed 1552296662 → null |
| #2169 PS_Light | 0.0666667 | 3.6666667 | exposed 448294385 → null, muted=true |

트랙의 active/updateParticle/searchHierarchy/postPlayback/seed는 JSON 원문대로. null 트랙에 임의 오브젝트를 넣지 않는다. Timeline 길이와 개별 AnimationClip 길이가 다르므로 서로 덮어쓰지 않는다. JSON 비유한 값은 문자열 `inf`로 보존했다.

LogoPSAnim 속성 CRC 검산: 1460864421=m_AnchoredPosition.x, 538195251=m_AnchoredPosition.y, 1087013301=EmissionModule.enabled. 파티클 두 노드의 emission enable 커브도 복원했으므로 위치만 재생하지 않는다.

검증 요청: 스킵 없는 승리에서 로고/색종이/Success 각각 캡처, 다음 승리 재생, 1.25초 이후 스킵 시 늦은 콜백 잔류 확인. 컨트롤러 전이는 dependencies 원문을 사용한다.

## 2. Barrage 표적 분산

`BarrageSpreadReference.cs`는 [원작 코드 판독]을 C#으로 옮긴 참고 구현이다. Unity에서 아직 컴파일/실행하지 않았다. 후보 수집과 폭발형 필터는 별도이며 이 파일만으로 전체 Pick 재현 완료가 아니다.

- ApplyEdgeInset 0x38300A4: 후보의 월드 XY 범위에서 좌우/위/아래 inset. 각 축 반폭에서 0.01을 뺀 값을 상한으로 제한. 후보가 모자라면 inset 배율 1→0.75→0.5→0.25→0으로 완화. 후보 좌표 자체를 이동시키지 않는다.
- GreedyFarthest 0x3830A30: 후보 XY 평균에 가장 가까운 점을 첫 표적으로 선택. 이후 이미 고른 점들까지의 최소 XY 거리가 가장 큰 후보를 선택. Z는 거리에 쓰지 않고 반환 좌표에는 보존한다. 동률이면 원래 순서상 앞 후보 유지. 기존 표적과 거리 <0.0001인 후보 제외.
- SelectSpread 0x38303CC: separation=max(0,입력). 최대 8번 재선택하며 부족하면 ×0.75. 충분하거나 separation<=0.05면 그 결과 반환. 8번 모두 실패하면 separation=0으로 마지막 재선택.
- ELF 상수 파일 오프셋: 0x14F36C8=-0.01, 0x14F38AC=0.05, 0x14F3A38=0.0001.
- Pick 0x382F8F8: CollectVisibleFrontPoints → inset → 조건부 폭발형 후순위 → 분산 선택. 비폭발 후보가 wanted 이상일 때만 폭발형을 제외한다. 무작위 섞기 금지.
- TryFrontVisible 0x3830814: 카메라에서 aim으로 Raycast, trigger 무시(1), 첫 충돌이 해당 장애물이어야 한다. 법선 z 판정도 존재한다. Collect/Bounds/Visible/Static 전체 asm을 동봉했으며 FaceSamples 원문 상수와 후보 수집 전체의 Unity 결과 대조는 미완료다.

## 3. 초기 3개와 예약 생명주기

[원작값] systems_audit_20260929/asset_values.json의 sharedassets0#272 Int_Booster_Barrage, #273 Int_Booster_BigCannon, #274 Int_Booster_InfiniteMoves 모두 persistent=true, IsSynced=false, m_defaultValue=3이다. SO의 기본 수량만이 아니라 영속 잔액 변수에도 3이 저장되어 있다. 해금/재시도 때마다 3개를 주라는 의미가 아니다. UseConfig=true이므로 이를 모든 외부 설정 상황에 고정된 실제 계정 잔액이라고 확대하지 않는다.

[원작 코드 판독] EconomyService.MigrateLegacyBalances 0x397A3B8는 Balance와 LegacyConfigKey를 가진 항목에서 migration flag가 없을 때 구 저장값을 읽어 Balance에 넣고 이관 표시를 저장한다. CurrencyEntry→잔액 변수 전 항목 매핑은 이 문서에서 추가 해독하지 않았다. 오프라인 새 저장소의 기본값 3과 기존 저장소 보존을 분리한다.

[원작 코드 판독] PreLevelBoosterToggle.OnDisable 0x39604E0는 리스너 해제이며 예약 해제 호출은 없다. Tutorial.OnDisable 0x3960EDC는 toggle의 0x91 무료 모드를 false로 복구하고 Refresh한다. 무료 튜토리얼 종료를 유료 재고 지급 이벤트로 바꾸지 않는다.

ClearPreLevelArmed 0x3995D94의 실행 세그먼트 직접 B/BL 참조는 TryAgainPopup.OnCloseButtonClicked 0x396C7C4 내 0x396C828 한 곳이다(`clear_prelevel_callers.json`). 직접 호출 검색은 인라인 필드 초기화나 간접 호출까지 없다고 증명하지 않는다. PlayPopup.Close/Toggle.Disable에서 직접 호출은 확인되지 않는다. 팝업을 닫을 때 무조건 모든 예약을 취소하는 자체 규칙을 원작 규칙으로 표기하지 않는다.

구매/광고는 사용자 지시대로 배선 자리만 둔다. 자동 성공/자동 지급/임의 코인 차감은 추가하지 않는다.

## 남은 검증 경계

로고 커브의 원본 경로·속성·바이트 소비는 검증 완료, Unity 화면/컨트롤러 재생 검증은 Claude 구현 후 필요. Barrage 분산 코드는 판독 완료이나 후보 수집 전체와 실제 표적 일치 검증은 남았다. 원본과 동일한 전체 런타임 맵 생성 및 700+ 레벨 검사는 별도 구현 작업으로 유지한다.
