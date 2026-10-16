# 인게임 종료 최소 정본 — bmv95brdo-1m

2026-10-15, Goods Hunt1.9.1. 기존 추출 우선 + 로컬 ARM64 정적 판독. 구현 소스/원작 파일 변경·원작 실행·로그인 없음. 종료 관련233개 함수(다음 선언 경계, cap초과0), UI6루트/922노드/118고유Sprite참조/해석오류0. UI peak commit0.369GB, 코드0.127GB. 최초 UI JSON 저장은 bytes 직렬화 오류로 실패했으나 bytes를 base64+길이+SHA로 보존하여 재실행 성공. PNG/음원/Spine 애니메이션을 새로 구웠다는 뜻 아님.

읽을 자료:

- `FLOW.md`: 최종 목표/클리어 전환/시간초과/폭탄/로컬 retry·next 경계.
- `ui_native_nodes.json`: 원본 GO/Transform/컴포넌트/기존 structured MB payload/Sprite rect·atlas/PPtr/rawSHA. 각 root는 독립 식별. 게임 로직/경제·광고 UI를 구현하라는 요청은 아님.
- `stored_ui_components.json`: 결과 UI 스크립트의 저장 필드와 원본 provenance. buttonContinue 등 PPtr를 ui_native_nodes의 file/pathID로 조인.
- `literal_values.json`: 종료 지연/scale 상수 원문 byte/ELFoffset/형식. **선언 CELEBRATION_DURATION2.15와 실제 스케줄2.4를 혼동하지 않는다.**
- `declarations.json`, `disasm_*.txt`: 메서드/RVA/ELFoffset/코드SHA. 공유 generic annotation에 별칭 오류가 있을 수 있으며 조건·인자·데이터 흐름을 우선.

## UI 원문 식별

| UI | serialized file | component pathID | GO | Transform |
|---|---|---:|---:|---:|
| Compliment(성공 결과) |level2|25737|33|17392|
| TimeUp |level2|27293|1681|18744|
| FailPopupPnl |level2|29580|4131|20830|
| OutOfBox |level2|30257|4809|21382|
| EndingTransition(실제 ID61과 일치하는 씬본) |level2|30984|2141|19160|
| EndingTransition(이름 같은 별도 저장본) |resources.assets|20282|3728|13365|

**동명 resources 저장본의 id=60, 씬본은61**. resources본을 같은 런타임 정본이라고 교체하지 않는다. enum60=CupPackOpen/61=EndingTransition과 어긋나는 저장상태 자체를 보존한다. 다른 결과 스크립트의 저장 id는0인 것도 있으며 런타임 호출 PopupID(Compliment7/TimeUp9/Fail5/OutOfBox15)와 구분한다. 로더가 모두 stored id0으로 라우팅하면 틀린다. 전체 PopupManager 등록·주입 경로는 여기서 전수 복원하지 않았다.

실제 PersistentCall:

- `/Compliment/Panel/Background/Button Continue` Button25771→StateCompliment25737.`OnHomeClicked`.
- `/TimeUp/Panel/TimeUpPanel/Button Close` Button30884→StateTimeUp27293.`OnNoThanksClicked`.
- `/OutOfBox/Panel/Content/Button Close` Button30263→StateOutOfBox30257.`OnNoThanksClicked`.
- `/FailPopupPnl/Panel/Background/Button Try Again` Button29585→StateFail29580.`OnRestartClicked`; ButtonClose29588→동일State.`OnHomeClicked`.

스프라이트118개는 키 `serialized_file#pathID`로 식별하고 name은 참고만 한다. 예 resources.assets#2048 GreenButtonInside, #2180 Clock1, #1635 BG_Popup_StartLevel_Normal. 64bit pathID는 기존 lossless parser 사용. native 참조를 이름 유사도로 대체하지 않는다. TMP/Spine/Particle/Animator payload 및 렌더 상태는 자료 보존 단계이며 원작 픽셀/재생 동등성 검증은 별도다.

저장 UI 시간: 주요 결과창 duraIn=.40000000596, durationOut=.10000000149; EndingTransition은 in/out .4. Compliment.delayF=1.01999998093. CardController는 animateCardDelay.2/cardFlippingInterval.12/cardDoneScaleIn.2/cardDoneScaleOut.1. 이 저장값만으로 모든 패널 전체 재생 타임라인을 만들어 냈다는 뜻은 아니다.
