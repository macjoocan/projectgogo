# 910맵 폭탄 후속 근거 (bmv8yo37f-l / bmv8yt8ow-n)

원작 미실행. 기존 구조화 JSON 순차 조회 및 로컬 ELF 메서드 3개만 추가 정적 판독. 대량 번들 재추출 없음. peak commit 0.150GB 이하. 생성 위치 전체 의사코드/일반 목표 누락 10건의 런타임 생성은 미결.

## 폭탄은 1.5초 후 자동 복구하지 않는다 [원작 코드 판독]
기존 code_audit_20261014/disasm_021b1f50.txt:
guard 통과 후 PauseClock(true) → DisablePlayerController → SetPlayerInvicible(1.5) → PlayerSPropFx(666) → SFX → GameRefManager.OnBombTriggering(1.5) → DelayedCall(1.5, closure, **ignoreTimeScale=true**). 무적 지속과 지연은 모두 명령어 fmov1.5로 확인.

GameRefManager.OnBombTriggering0x1E3AFC0: instance+D9=true, OnChangeGameState(Pause=1), 전달받은 delay 뒤 별도 callback 예약(ignoreTimeScale=true), IncrementBombCount(CurrentLevel). GamePlayState enum은 Play0/Pause1/Null2.

새 `bomb_disasm_01e42490.txt` callback0x1E42490: static GamePlayState==Null2이면 return. 아니면 PopupManager.LoadPopup(**PopupID.OutOfBox15**,null). 해당 enum 원문 dump.cs Type1122. 따라서 1.5초 뒤 clock/input을 무조건 재개하는 구조로 만들 근거가 없다. OutOfBox의 재시도/이어하기/닫기 복구 경로는 이번 판독에서 확인하지 않았다.

새 `bomb_disasm_021b2628.txt` SpecialProp closure0x21B2628: 오브젝트 SetActive(false) 후 stateNull2이면 return, 아니면 playingTime/remainingTime/goal수/holeSize/placement/difficulty/bombName을 수집해 **TrackEventLevelFail0x1DE3F1C** 호출. clock.Pause(false), EnablePlayerController 호출은 이 closure에 없음. 첫 SetActive 대상은 원문 singleton+28 → component+218이며 정확한 노드명은 이번 근거로 미확정. 이름 추정하지 말 것.

## 저장 활성화 필드 [기존 원작 저장값]
`prop_stored_activation_candidates.json`: 기존 structured_objects.zip에서 autoActivate/isHolder 필드를 가진 1008레코드(고유 prefab1008종이라는 뜻 아님)를 순차 조회. 각 JSON SHA 및 original native index source/file/path_id/rawSHA를 source_index로 연결. 원본 재파싱으로 새 schema를 생성한 것이 아님. 필드가 있는 레코드 전체를 보존하므로 importer의 원문 PPtr와 조인해서 사용할 것.

폭탄 TriggerableProp 저장레코드: CAB-5388c821bd9df28739ab71fc81803c09 **pathID1181109212370131174**, propType666, **autoActivate=true / isHolder=false / isObstacles=false**. 일반 후보 중 holdertrue23레코드, obstaclestrue12레코드. 수치는 이 기존 아카이브 후보 범위이며 전체 628prefab의 완전성 보증은 아님.

autoActivate는 TriggerableProp.CheckPropActivationRule0x21E6440에서 소비된다. Init automaticCheckingPhysics 인자와 호출 주체는 별개다. 저장true만으로 생성 순간 무조건 dynamic이라고 확대하지 않는다.

## 자동 생성 폭탄과 배치 폭탄을 구분 [원작 코드 판독]
새 `bomb_disasm_021df174.txt`: LevelBehavior.<InstantiateBombProps>d__62.MoveNext0x21DF174. randomBombs는 처음0. currentLevelOrder >= DifficultConfig.DifficultLevelStart 조건을 확인하고 LevelDifficulty가 Hard1/Super2일 때 각각 BombPerLevelHard(+18)/BombPerLevelSuperHard(+20)를 참조한다.

읽힌 명령어 산식: custom=Level.GetNumCustomBomb(), stored=Level.bombNumber, total=stored+custom; 해당 난이도 분기에서는 randomBombs=trunc(rate*total/100)-custom. .text0x21DF2E0~36C의 정수 multiply/divide-by-100 패턴. 범위 밖/다른 난이도에서는 초기0 유지. 산술 overflow/remote 실제값/실제 호출시점은 이번 증거로 별도 확정하지 않음. **Level672.bombNumber2만으로 무작위 폭탄 정확히2개를 생성한다고 주장하지 말 것.**

각 생성 시 Random.Range(int1,int4)→bombSize1..3, 원문 PropPlacement/Prop UID를 통해 prefab 로드/LeanPool.Spawn. TriggerableProp.AdjustPropSize(bombSize,false)0x21DF9E4~F8 → virtualInit(propData,placement,false)0x21DFA0C~1C → **OnEatenCallback(+88)=null**0x21DFA20~28. 자동 생성 폭탄을 일반 score/growth callback에 연결하는 것은 이 경로와 다르다. 배치된 TriggerableProp은 base.EatenCoroutine에서 callback 호출 후 IsEaten을 세우고 TriggerSProp으로 이어지는 원래 순서 유지. 배치 폭탄의 cost/일반 callback 배선에 따른 점수 여부는 그 개별 연결을 검증해야 하며 모든 폭탄 성장0이라고도 확대하지 않음.

위치 무작위 범위/튜토리얼 조건/회피거리/UID 문자열까지 포함한 전체 생성 알고리즘은 아직 번역 완료하지 않았다. 코드 바이트/BL근거는 보존했다. 웹에서 source-backed 범위 밖을 구성하면 파생 선택으로 표시해야 함.

## 기존 테마 자료
`../settings/0182_MapThemeDatabase.json`: provenance resources.assets#16512, rawSHA ba3039090f33765c05b31422d47f0d0529dd2c50e954099f64c4d1aed8c9fa60. _mapThemeContainers의 MapTheme/Label/MainThemeMaterial/TopThemeMaterial/SeaThemeMaterial/GroundThemeMaterials(proportion)/HoleGlowColor 원문 PPtr. GameMode enum 숫자를 이 MapTheme 숫자에 그대로 대입하지 말 것. mode별 GetMapTheme 선언/본문은 별도로 대조.

기존 level3 조명은 code_audit_20261014/LEVEL3_LIGHTING_REFERENCE.md 및 level3_light_chain.json/lighting_stored_values.json. 이는 **serialized scene level3**, 모든 테마별 별도 조명 검증 완료 자료가 아님.

목표 UID 부재10건/Level8 컨테이너 조사 완료 자료는 현재 없음. props에서 찾지 못한다는 이유만으로 목표를 임의 생성하거나 특수 목표라고 단정하지 않고, GetGoalCounts의0개정리와 실제 source 생성/배정 경로를 분리해야 한다.
