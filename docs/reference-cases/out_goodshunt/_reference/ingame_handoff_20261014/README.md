# Goods Hunt 인게임 저장값 인계 (2026-10-14)

범위: 원본을 수정하지 않고 기존 추출물에서 선택한 컴포넌트와 원본 Transform을 추가 정리했다. importer 구현은 Goodhunt 세션 소유다. 이번 작업은 약 0.174 GB peak private commit으로 순차 실행했다.

## 근거 파일
- component_fields.json: 선택 컴포넌트 20개. source/serialized_file/path_id/raw_sha256 및 원문 필드. [원작 저장값]
- component_native_transforms.json: 컴포넌트와 GameObject/Transform 연결 14건. 반올림하지 않은 native TRS와 부모/자식 PPtr. [원작 저장값]
- hierarchy_paths.json: 기존 계층 내 경로 10건. 이 파일의 TRS는 export 과정에서 반올림됐으므로 정확한 수치 적용에는 native 파일을 사용한다.
- level_guid_order.json: Main/HEA 각각 levelRefs 910개. 저장 배열 순서만 확인. 실제 레벨 파일 주소 조인은 미확정.
- goal_count_candidates.json: 선택 레벨의 goalsUniqueID와 동일한 props.propUniqueID 개수. [계산]이며 실제 목표 UI 수량으로 확정하지 않는다.

## 카메라: 메뉴와 게임을 분리할 것
level3 Camera #37 / Main Camera GO #5: 저장 위치 (0,30,-22), quaternion (0.4500984847545624,0,0,0.8929789662361145), FOV 30, near 0.3, far 399, perspective.

Gameplay Virtual Camera #99 / GO #16 / Transform #32: priority 10, FOV 30, Follow #33(Player). componentOwner #29의 CinemachineTransposer #90은 followOffset (0,30,-22), X/Y damping 0.1, Z damping 0.

Menu Virtual Camera #98 / GO #15 / Transform #31: priority 0, FOV 33, Follow null. componentOwner #30의 Transposer #95는 offset (0,40,-30), damping 0. Composer #96는 trackedOffset (0,-5,2), screen (0.5,0.5), damping (0.5,0.5), softZone (0.8,0.8).

CinemachineCameraController #118에는 cameraType 0 -> #98, 1 -> #99와 firstCamera 0이 저장돼 있다. 숫자 enum의 실제 이름, 런타임 선택·전환 조건은 판독하지 않았다. Brain #117의 defaultBlend m_Style 1 / m_Time 2도 저장값이며 실제 전환 연출 관찰 결과가 아니다.

## 홀·조작·성장
현재 선택된 실제 컴포넌트 이름은 PlayerBehavior(level3#100), PlayerComponent(sharedassets3.assets#1893), PlayerFxComponent(#1895)다. HoleController라는 이름으로 흡수 로직을 복원했다고 주장하지 않는다.

PlayerBehavior wallPadding = 0.15000000596046448. 시각/성장/속도/자석 등 컴포넌트 PPtr는 JSON 원문 참조.
JoystickAdapter level3#110: handleRange 1 / deadZone 0 / snapX,Y false / moveThreshold 1.25 / joystickType 2 / axisOptions 0. 입력의 월드 방향 변환·흡수 판정·충돌 처리 본문은 미확정.

settings/0172_HoleSizeUpgrade.json (sharedassets3#1833):
- radius: 1,1.3,1.6,2,2.5,3,3.5,4.3,4.7,5.1,5.5,6
- maxSpeed: 5,6,7,8,9,10,11,13,14,15,16,17
- cameraOffsetMultiplier: 1,1.1,1.15,1.2,1.5,1.75,2,2.4,2.6,2.85,3.1,3.4
- price: 0,10,20,100,250,400,550,700,850,1000,1150,1300 / currencyType 0
- transitionDuration 0.5 / transitionEase 14 (enum 이름 미확정)
위 목록은 읽기 쉬운 반올림 표기이며 적용에는 component_fields.json의 원문 float를 사용한다. price를 XP 임계 또는 실제 코인 비용이라고 단정하지 않는다. 현재 플레이에서 이 테이블을 소비하는 코드 본문도 아직 검증하지 않았다.

settings/0177_PlayerUpgradeStat.json: Gravity 40,45,50,55,60,65,67,70,75,80,80,80,80,80,80. 적용 단위·시점 미확정.
PhysicsManager: gravity (0,-40,0). TimeManager: fixed 0.0299999993 / maximum 0.0500000007 / particle maximum 0.0350000001 / timeScale 1. 저장 설정이며 실행 중 변경 여부는 미확정.

## 레벨·목표·보상 경계
Main levelRefs의 원문 GUID 순서 확보와 GUID -> 실제 레벨 주소 연결은 다른 단계다. assets/aa/catalog.bundle 주소 조인이 해결되기 전에는 Level_001 같은 에셋명 선택을 명시적 참조맵 선택으로만 제공한다. LD LevelLoop 1300개를 초기 진행 순서로 사용하지 않는다.
ThemeProps의 uniqueID -> prefabReference GUID / cost는 저장 관계다. cost가 골드·XP·성장 점수 중 무엇인지, IncomeUpgrade의 price/additionalIncome이 현재 규칙에 적용되는지는 미확정. goalsUniqueID로 세는 후보 수량은 홀더·특수 목표·런타임 생성 규칙을 반영했다고 주장하지 않는다.

## 실제 화면 캡처
현재 확보된 원작 플레이 스크린샷/영상은 없다. 확인 시 LDPlayer가 종료돼 ADB 기기 목록이 비어 있었다. 에뮬레이터 실행 상태라면 ADB로 원작 화면 캡처는 가능하지만 이번 인계에 실제 플레이 관찰 증거는 포함되지 않는다. 보고서·추출맵 시각화·구현 화면을 원작 실기 캡처로 분류하지 않는다.
