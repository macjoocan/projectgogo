# 配置 폭탄 callback / 0개 목표 정리 (bmv8yyvyn-q)

## 목표 UID 0개는 반환 전에 제거 [원작 코드 판독]
기존 `code_audit_20261014/disasm_021aece8.txt`:
- goalsUniqueIDs에서 유효 UID dictionary 초기화 → props 및 specialProps 카운트.
- 0x21AF054..068: 복사한 키 목록의 현재 UID를 dictionary에서 읽음. 0x21AF06C/070 `ldr w8,[sp,#28]; cbnz ...`.
- 0이면 **0x21AF080 Remove** 호출. 모든 키 검사 후 0x21AF0E8에서 dictionary를 반환한다.
- 뒤에는 원문 키 복사 목록의 index6부터 추가 Remove하는 0x21AF09C..0E4 분기도 있다. 키 목록 순서/처리 전후를 보존해야 하며 여기서 별도 웹 정렬로 바꾸지 않는다.

따라서 source goalsUniqueIDs 원문은 감사/표시에 보존하되 **반환 목표 데이터에0을 영구 유지해 클리어 불가능하게 만드는 것은 이 함수와 다르다**. 부재10건은 원문 목표 UID와 유효 반환 목표를 함께 기록한다. 누락 목록만으로 런타임 컨테이너 생성이 필수라는 증거가 되지 않는다. GetGoalCounts만으로 뒤의 목표 시스템 전체가 확정된 것은 아님.

## 배치 specialProps의 callback [원작 코드 판독]
`bomb_disasm_021dc248.txt` = LevelBehavior.<InitProp>d__57.MoveNext 0x21DC248, 다음 선언0x21DF10C까지 제한 정적 판독.

보통 props 분기: 0x21DCC10..24에서 method slot **0x4196B48**을 읽고 target=this LevelBehavior로 PropBehaviorDelegate 생성 → 0x21DCC28 prop+88에 저장.

specialProps 분기: 0x21DDAEC..DB00에서 **동일 method slot0x4196B48**, 동일 LevelBehavior target으로 delegate 생성 → **0x21DDB04 prop+88에 저장**. 앞에는 원문 cost 테이블을 통한 maxPrice 누적0x21DDAB0..DAD8도 있다. 따라서 **배치된 specialProps에 일반 콜백이 연결되지 않는다고 구현하면 틀린다**. 자동 생성 InstantiateBombProps의 callback=null과 다르다. 이 조사에서는 slot의 메서드 토큰을 별도로 재해석하지 않았지만 양쪽이 동일한 callback 생성 경로라는 바이트 근거는 확보했다.

TriggerableProp.EatenCoroutine0x21E6454: base0x21E2F88를 먼저 호출 → virtualTriggerSProp. base는 callback(+88)호출 후 IsEaten+49=true. 이후 bomb handler에서 IsEaten이true인지 검사하는 순서와 연결된다. 배치 Bomb cost의 실제값은 해당 Prop 자산을 기준으로 기존 importer의 값을 유지한다. callback배선 근거만으로 폭탄 cost/성장값을 임의0이나다른값으로 바꾸지 않는다.

specialProps 초기화에는 별도 Bomb DDA 활성화도 보인다: 0x21DD900 placement.ddaZone+58 → **DDAManager.ShouldActivateBomb0x1EBACA4** → 0x21DD91C GameObject.SetActive(result). 저장5395개가 모두 실행 시 활성이라는 보장은 이 조인만으로 성립하지 않는다. DDA본문은 이번 범위에서 미판독이다.

## DifficultConfig 기본 저장값
`settings/0032_DifficultConfigSO.json`: sharedassets1.assets#11.
`settings/0058_DifficultConfigSO.json`: sharedassets1.assets#37.
둘 다 raw SHA77edbd91b4d39bd3fdb6f539719a5a0f35fbe67678a53394a16a68c0f9a3df01. Data: DifficultLevelStart100, BombPerLevelHard100, BombPerLevelSuperHard100, TimePerLevelHard100, TimePerLevelSuperHard100, IsDescreaseTimeInLevelLoop=false, TimeDecreaseInLevelLoop0. 저장 기본값이며 RemoteConfigUtils의 실행 중 선택/override값까지 확정하는 것은 아니다.
