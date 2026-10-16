# 910맵 노출: 기존 근거 인계 (bmv8ylxei-k)

새 번들/원작 실행/대량 추출 없이 기존 dump.cs와 판독 문서만 조회했다. 이 문서는 모드별 실행 본문을 새로 판독한 결과가 아니다.

## 확정 선언 경로
`../code_audit_20261014/GameModeType_declarations.cs` TypeDef1119 원문:
Normal0, Bonus1, Ice2, Water3, Desert4, Mart5, Mart2=6, Mart3=7, Mart4=8, Box9, Vegetables11, Sea12, FastFood13, Toy14, MeatAndSeaFood15, Stationaries16, Cosmetics17, Drink18, Pets19, Fitness20, Cooking21, Garden22, Disco23, Universal24, Garden2=25, Egypt26. **10은 이 enum에 선언 없음.**

`GoalCardMechanicType_declarations.cs` TypeDef4375: None0 / Hidden1 / Bonus2. GameMode, MapTheme, GoalMechanic은 서로 다른 축이다. 모드가 0이 아니라는 사실만으로 모든 맵에 별도 목표 기믹이 필요하다고 확정하지 않는다. 모드 이름만으로 일반 props 배치와 특수 생성의 호환 여부도 확정하지 않는다.

`Level_declarations.cs` 및 dump.cs TypeDef4301의 저장 필드: gameMode+24, backgroundTheme+28, backgroundOption+2C, goalsUniqueIDs+30, goalMechanicTypes+38, props+40, specialProps+48, decors+50, levelTileMap+58.

## 이미 판독된 공통 목표 계산
`../code_audit_20261014/README.md` 3절; `disasm_021aece8.txt`가 존재하면 해당 명령어 원문 사용. Level.GetGoalCounts0x21AECE8: 목표 UID로 dictionary 생성 후 **props와 specialProps 둘 다** propUniqueID를 순회해 목표 카운트. 별도 mechanic/런타임 생성까지 이 함수가 보장하는 것은 아님. GetGoalMechanicTypes0x21AF190은 기존 선언 확보, 전체 의미 판독 완료 아님.

SpecialPropPlacement(Type4323, dump.cs153674 부근)은 PropPlacement 파생이며 scaleSize+3C, color+48, ddaZone+58, voxelMeshScale+5C 추가. 공통 PropPlacement.scalar scale만 복제해 특수 배치를 전부 처리했다고 하면 누락된다. SpecialProp(Type4344) Init0x21E3D68, AssignCup0x21E3DD4, AssignCupPack0x21E442C 선언 있음; 각각 본문/런타임 생성 관계는 이번 기존자료 조회에서 확정하지 않음.

## 모드별 생성이 따로 존재한다는 선언 근거
dump.cs Type4377 GameModeBase: abstract SpawnAdditionObject(slot10), virtual StartNewLevel0x21F35F8 및 시작/일시정지/클리어 팝업 선택. Type4378 GameModeMechanicFactory.InjectGameMode(GameModeType)0x21F3A2C. GModeNormal/GModeMart/GModeBonus/GModeIce/GModeWater/GModeDesert/GModeBox/GModeVegetables/GModeSea/GModeFastFood/GModeToy/GModeMeatAndSeaFood/GModeStationaries/GModeCosmetic/GModeDrink 관련 타입 선언 보존.

예: GModeBox.SpawnAdditionObject0x21F47A0, GModeDesert.SpawnAdditionObject0x21F4800, GModeBonus.SpawnAdditionObject0x21F4560. **이름과 RVA 확보는 생성 규칙 판독과 다르다.** 각 모드 specialProps/goal/추가 생성/승패 흐름을 통합한 검증 완료 문서는 현재 확인하지 못했다. 모든 enum 값이 factory에서 구현된다고도 이번 조회로 단정하지 않는다.

## 구현 인계
전체 맵 버튼/명시적 참조맵 선택은 실제 진행 순서와 분리. 일반 props asset chain 재사용과 특수 목표/생성 복원은 별도 상태로 표시한다. 아직 지원하지 않는 mechanic을 조용히 None 처리하거나 누락 specialProps를 빈 배열로 만들어 클리어 가능하다고 주장하지 않는다. 현재 수신 세션이 수행하는 910맵별 props/specialProps/goalMechanic/UID 빈도 집계가 다음 좁은 조사 대상을 고르는 기준이다. 원본 맵이나 기존 195맵 구현을 여기서 변경하지 않았다.
