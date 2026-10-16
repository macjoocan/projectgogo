# Goods Hunt 추가 코드 판독 1차 (2026-10-14)

## 범위와 근거
[원작 코드 판독] 원본 ARM64 libil2cpp.so 및 metadata31을 정적으로 읽었다. 원작 코드를 실행하거나 원본/계정/설치 파일을 변경하지 않았다. binary_receipt.json에 SHA256과 ELF PT_LOAD 주소 변환을 기록했다. RVA와 파일 offset을 혼동하지 말 것. .text에서 현재 차이는 0x4000이지만 모든 세그먼트에 고정 차이를 적용한 것은 아니다.

Il2CppDumper 실행은 peak 0.319 GB / 14.84초, Capstone 선택 메서드 판독은 peak 약0.10GB였다. 로그에 일반적인 'This file may be protected' 경고가 있으나 원본 입력 그대로 CodeRegistration 0x3f2a5c0 / MetadataRegistration 0x3ff9ad0을 찾고 dump.cs가 생성됐다. 메모리·출력량을 줄이기 위해 GenerateStruct=false로 실행했으므로 script.json/il2cpp.h 생성은 하지 않았다. 별도 복호화/보호 우회 작업은 하지 않았다. 덤프 성공만으로 모든 메서드 이름과 실행 규칙이 검증됐다고 주장하지 않는다.

선택 클래스의 *_declarations.cs는 필드/선언/RVA 근거다. disasm_*.txt는 해당 코드 바이트의 명령어 근거다. generic shared method는 같은 RVA에 여러 이름이 걸리므로 BL 주석의 대표 generic 이름을 그대로 의미로 확정하지 않는다. 함수 끝은 다음 메서드 RVA와 8192바이트 cap으로 제한한 판독 범위이며 완전한 symbol size 증명은 아니다.

## 1. 성장: 저장 price가 실제 성장 계산에 사용된다
PlayerBehavior의 필드:
- holeSizeUpgrade +0x38 / playerUpgradeStat +0x40
- maxSpeed +0xA4 / acceleration +0xAC
- canExpand +0xC9 / expandCost +0xCC / collectedCost +0xD0 / nextEnergyStage +0xD4
BaseUpgradeStage.price +0x10, HoleSizeUpgradeStage.radius +0x20 / maxSpeed +0x24 / cameraOffsetMultiplier +0x28.

ResetPlayer RVA 0x21E9834, 특히 0x21E9C44~0x21E9C84:
다음 단계가 존재하면 nextEnergyStage = upgrade의 현재 stage(+0x28) + 1. expandCost = 정수 price / 2(0 방향 절삭) 후 float 변환. collectedCost=0, ScoreController.OnReset 호출.

GetExpNeededToLevel RVA 0x21EAE28:
nextEnergyStage의 stage를 얻어 price/2 정수값 반환. stage 없으면 -1.

TryExpandHole RVA 0x21E8AC4:
- requireActiveGame=true일 때 difference>0와 LevelController.IsGamePlayActive 필요. false여도 difference>0은 필요.
- canExpand=false이면 반환.
- collectedCost += difference.
- collectedCost < expandCost이면 에너지 UI만 갱신.
- 임계에 도달하면 collectedCost -= expandCost로 잔여값 유지하고 nextEnergyStage의 radius/maxSpeed/cameraOffsetMultiplier를 적용한다.
- radius tween: HoleSizeUpgrade.transitionDuration / transitionEase 원문을 사용. 기존 저장값0.5초/enum14를 연결할 근거가 생겼다.
- Physics.gravity=(0,-PlayerUpgradeStat.Gravity[nextEnergyStage],0), acceleration=maxSpeed*5.
- nextEnergyStage++ 후 다음 stage가 있으면 다음 expandCost=float(price)*0.5; 없으면 canExpand=false 및 에너지UI비활성.
- 코드 본문은 한 호출당 한 단계 분기다. 잔여값을 처리한다는 이유로 임의 while 다단계 업그레이드 루프를 넣지 말 것.

HoleSizeUpgrade 저장 price[10,20,100,250,400,550,700,850,1000,1150,1300]의 절반은 [5,10,50,125,200,275,350,425,500,575,650]. 단계0 price0은 목록에 존재하지만 최초 currentStage 선택을 무조건0이라고 확정한 것은 아니다. 초기 단계·다른모드 override는 별도 확인 범위.

get_EffectiveRadius RVA 0x21E6EC4: baseRadius * powerUpMultiplier. detectRadiusMultiplier까지 곱한 값이라고 쓰지 말 것.

## 2. 먹힘: 접촉 즉시 삭제가 아니다
PropBehavior 선언과 실제 Update RVA 0x21E14A4의 교차 확인:
- renderer Transform.y < -2.3이면 EnableInHoleDrop(0x21E1718)로 전환. literal_floats.json의 -2.29999995와 일치.
- _isInHoleDrop=true일 때 _inHoleDropVelocity=min(v+30*deltaTime,80).
- 일반 객체는 Transform을 아래로 v*deltaTime 이동한다. 큰 객체의 isTriggered 분기가 있어 모든 객체에 일괄 동일 이동을 강제하지 말 것.
- EnableInHoleDrop의 일반 객체 경로는 v=abs(rb.velocity.y)로 초기화, velocity/angularVelocity 정리, isKinematic=true 및 collider 처리 경로가 있다. 순간 삭제로 대체하지 말 것.
- CanFallSlow이면 먹힘 높이 -15; 그 외 큰 객체이면 -10; 그 외 일반 객체이면 -4. 각 경계는 y < threshold다.
- 경계 통과 후 slot11 EatenCoroutine(0x21E2F88). IsEaten 재진입 가드가 있고 OnEatenCallback 호출 뒤 flag를 세우는 저장 코드 순서다. 내부 비활성화/후속 콜백도 있으므로 단순 즉시 Destroy와 동등하지 않다.

OnTriggerEnter RVA 0x21E2A94:
other.gameObject.layer==7이고 !IsEaten && !IsActive && 게임활성일 때 isTriggered=true 후 ActivateProp 호출. layer11에서는 !IsEaten인 Rigidbody.maxLinearVelocity=20 경로가 있다. OnTriggerEnter 자체가 목표 감소/점수 지급은 아니다.

PullObjectInRange RVA 0x21EAA94는 별도 흡인 경로다. PlayerUpgradeStat.Gravity[nextEnergyStage-1]을 사용하고 Rigidbody.AddForce(..., ForceMode 숫자5) 호출이 보인다. 전체 활성화/구멍 ground-collider 형상/크기 적합 판정과의 호출 관계는 아직 판독 완료하지 않았다. 이 메서드 단독으로 '흡수 반경 공식'을 확정하지 않는다.

## 3. 목표 수량: 종류별 배치 개수
Level.GetGoalCounts RVA0x21AECE8는 goalsUniqueIDs(+0x30)로 초기 dictionary를 만들고 props(+0x40)와 specialProps(+0x48)의 propUniqueID(+0x10)를 순회해 해당 목표를 +1 하는 경로를 가진다. 0개 목표 정리 경로도 있다. 특수 goal mechanic 및 이후 런타임 변경까지 이 한 메서드로 보장한 것은 아니다.

원문 계산과 실기 교차 확인:
- Level_003: 전체 props308, 목표 Apricot72. 실기 캡처03_ingame의 카드72와 일치.
- Level_005: 전체 props933, 목표 Dragonfruit16 / Persimmon_Red16 / Lychee_Peeled16. 실기05_before_agent_input의16/16/16과 일치.
'전체 배치 수와 목표 수가 다르다'는 것은 오류 근거가 아니다. 목표종류 UID를 정확히 필터해야 한다. 에셋명과 실제 진행 순서 조인은 별도이며 이 일치만으로 전체 초기순서를 확정하지 않는다.

## 4. cost -> 점수 변환: cost를 그대로 더하지 말 것
LevelBehavior.OnPropEaten RVA0x21D8664:
PropBehavior.Prop(+0x20)의 Prop.cost(+0x48)를 읽는다. 일반 객체 경로는 Constant.PropIncomeValue[ cost ]를 조회해 float로 변환하고 ScoreController.Add(0x213FFE4)에 넣는다. Cash/Coin/Voxel 계열의 별도 분기·테이블도 있어 모두 일반 객체와 동일하게 처리하면 안 된다.

Constant..cctor RVA0x1E5AD4C의 직접 literal 초기화:
PropIncomeValue = {0:0,1:1,2:2,3:3,4:9,5:11,6:13,7:18,8:20,9:22,10:25,11:27}.
CashObjectIncomeValue / CoinObjectIncomeValue = {0:0.150000006,1:0.150000006,2:2,3:3,4:9,5:11,6:13,7:18,8:20,9:22,10:25,11:27}.
VoxelObjectIncomeValue = {1:0.1000000015}.
InGameCoinReceiveValue = {1:1,2:2,3:3,4:4,5:5,6:6,7:8,8:10,9:15,10:30,11:50}.
constant_income_tables.json에 각 dictionary initializer call RVA와 rawbits를 보존했다. 선언의 static offset0/8/16/24/32 및 실제 static stores로 이름 순서를 확인했다. 문자열 사전 cachedIncomeStrings는 숫자 해석 대상에서 제외했다.

일반 객체 ScoreController 점수와 지갑 코인은 같은 축이 아니다. InGameCoinReceiveValue 테이블의 소비·실제 코인 정산 및 클리어 보상 지급 경로는 아직 최종 확정하지 않았다. Constant.COMPLETE_LEVEL_REWARD=15도 [원작 선언값]이며 현재 이식에 즉시 지급 규칙으로 넣을 충분한 본문 검증은 아니다.

## 미결
- ground/hole collider 갱신과 크기 적합성·활성화·흡인 전체 호출 순서
- 초기 currentStage와 모든 gameMode/부스터 분기
- 일반 점수와 특수 물체·골드 정산·클리어 보상 분리 구현
- GUID 주소 조인/실제 초기 levelRefs 선택
- DDA 캐시의 실제 적용 본문

새 코드는 Goodhunt 세션 소유다. 이 문서는 원본 판독 인계이며 구현/원작 실행 정합성 완료 판정이 아니다.


추가 정본: SCORE_GROWTH_CALLBACK.md / score_subscription_method_refs.json. 일반 물체 PropIncomeValue 점수가 Score.Add -> OnScoreAmountChanged -> TryExpandHole로 수정 없이 전달되는 등록/본문을 ELF relocation 및 metadata method record와 교차 확인했다.
