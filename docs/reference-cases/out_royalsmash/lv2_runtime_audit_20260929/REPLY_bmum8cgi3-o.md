# reply-to bmum8cgi3-o — 정상 재생 결과와 원인 판정 분리

일반 실제 재생에서 lv2/lv3 구조가 유지됐다는 보고는 수신했다. 그러나 Start→Awake가 lv2 붕괴를 고쳤다는 인과는 확정할 수 없다.

## 반증 가능한 정적 증거

C: 현재 `Resources/RS_Levels/Level_2.prefab` 및 그 의존 `Skins/original/Prefabs/CanCylinder_1.prefab`, `Table_Rect.prefab`의 script GUID를 대조했다. **RsPlatform/RsBlocker/RsHammer 모두 0개.** Level2는 CanCylinder_1 98개 + Table_Rect 1개다. 이 3개 스크립트의 변경이 해당 레벨에서 실행된다는 근거가 없다. 다른 씬 오브젝트에 존재한다면 실제 인스턴스 경로와 영향 연결을 별도로 제시해야 한다.

## 원작값: 받침은 저장 시점부터 kinematic

APK `assets/bin/Data/d2998e4c483174a2da3549a685a73a8e#25 Rigidbody`, GO #5(Table_Rect/Body/Surface) 원시 typetree 재추출:

- m_IsKinematic=true
- m_UseGravity=false
- m_Interpolate=1
- mass=1

`initialization_evidence.json`에 전체 원문과 raw SHA256을 제공했다. 현재 C: Table_Rect.prefab도 Surface Rigidbody는 m_IsKinematic=1이다. 따라서 '첫 Start 전 받침이 동적 중력체였다'는 설명은 이 두 저장본으로 뒷받침되지 않는다.

## 원작 코드 판독

- Platform.Start `0x393FA68–0x393FC20`: playing/rb 유효성 검사, 이동축 시작값·방향, 부모 및 local pose 캐시. **이 함수에는 isKinematic setter 호출 없음.** 시작축 값은 단순 0이 아니라 각 min/max 정렬 범위에 0을 clamp하는 계산이다.
- Blocker.Start `0x382BFD4–0x382C2FC`: 기준 위치와 시작 phase, transform 및 Rigidbody position/rotation, blade scale 설정. 이 범위의 직접 호출에 isKinematic setter 없음.
- Hammer.Start `0x3833310–0x3833424`: ApplyScales/BakeSamples, Rigidbody pose·axis 확보, ApplyPose(true). 이 범위의 직접 호출에 isKinematic setter 없음. 하위 helper 전체에 setter가 전혀 없다는 확대 주장은 하지 않는다.

주석을 달아 저장한 각 *.asm과 호출 목록을 참고. 원작이 이 세 초기화를 Awake에서 한다는 근거는 없다.

**Start 본문 통째로 Awake 이동은 별도 회귀 위험**: Instantiate 뒤 caller가 배치/기믹값을 주입하면 Awake의 기준 pose/phase 캐시는 그 이전 값을 잡는다. 단순 강체 플래그 보장과 배치 완료 후 기준값 캡처를 나누고, 후자를 원작처럼 올바른 시점에 수행해야 한다. 신규 패치를 검증 없이 일괄 되돌리라는 뜻은 아니다.

## 필요한 비교

1. 고정된 동일 씬·동일 로비 경로·잔류 오브젝트 없는 시작에서 시간 .02/.0125와 Start/Awake를 각각 분리해 비교한다. 원본 목표 설정은 .0125/.025/.125이고, .02 조건은 원인 분리용이다.
2. 매 실행 실제 level order, active holder 수, 세 컴포넌트 수와 경로, Time.fixedDeltaTime/maximumDeltaTime, 받침 rb.isKinematic/useGravity, 최초 파괴 reason을 기록한다.
3. 레벨 2는 세 컴포넌트 없는 상태에서 원래 패치 전 코드와 후 코드가 다른 결과를 내는지 먼저 확인한다. 동일하면 초기화 순서 원인 주장을 철회한다.
4. Play 모드 실제 자동 물리에서 검증한다. Script 모드 프로브의 안정 결과만으로 시간·라이프사이클 순서를 증명하지 않는다.

콜라이더 개수/치수합/질량합 일치는 유용한 배제 단서지만 center/rotation/레이어/활성상태/참조까지 완전 동치라는 뜻은 아니다. 현재 위치 99개 일치는 별도로 확인됐다.

현 상태: **정상 재생 보고 수신 / 원인 미확정 / 원본 TimeManager 불일치 및 받침 저장 kinematic 확인**.
