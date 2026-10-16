# PullObjectInRange 본문 판독 — 2026-10-14

[원작 코드 판독] PlayerBehavior.PullObjectInRange(Collider), RVA0x21EAA94.
- stat(+0x40).Gravity(+0x18)[nextEnergyStage(+0xD4)-1]를 먼저 읽는다. 현재 단계+1 인덱스를 잘못 쓰지 않는다. null/range는 원문 예외 경로, 무조건0으로 치환하지 않는다.
- Collider에서 out PropBehavior를 구하는 generic 호출0x2619644 -> outbuffer+8. 해당 shared generic 주석의 GetComponentsInParent 이름은 확정명으로 쓰지 않는다. prop가 없거나 IsEaten(+0x49)이면 반환.
- virtual slot3 반환값 -> native type resolve helper -> Type.op_Equality(typeof(TriggerableProp))이면 반환. TypeHandle0x4196D58 encoded0x4001805D -> types[49198] -> Il2CppType.data4346=TriggerableProp 독립 확인. typeof와 동일 비교라 단순 '모든 SpecialProp' 또는 모든 하위형식 제외라고 확대하지 않는다. helper 단계 전체 고수준 GetType 표현은 미확정이다.
- 자기 transform.position과 prop.transform.position의 **X,Z 차이만** 읽는다. dir=(player.x-prop.x, **-3**, player.z-prop.z), length=sqrt(dx*dx+9+dz*dz). prop의 실제Y 차이가 아니며 평면거리도 아니다.
- length<0.10000000149이면 반환. literal0xE0A44C.
- length>0.000009999999747면 dir/=length, 아니면 Vector3.zero. literal0xE0A578.
- !IsActive(+0x48): ActivateProp(0x21DA610) 호출 후 반환. 활성화한 같은 호출에서 힘까지 주지 않는다.
- active && length<3: rb.velocity=Lerp(rb.velocity, Vector3.zero, clamp01(Time.deltaTime*0.25)); 반환. dirY=-3이라 유한 정상 입력에서 length>=3이므로 이 분기는 정상 산술상 도달하기 어렵지만 원문대로 기록한다. 평면거리<3으로 '수정'하지 않는다.
- active && length>=3: rb.AddForce(normalizedDir * Gravity[nextEnergyStage-1], **ForceMode.Acceleration(5)**). 별도 dt 곱/Impulse로 바꾸지 않는다.

[호출 계기 미결]
이 함수 본문에 일반거리 제한/게임플레이 active 조건은 없다. 상위 호출의 공간/gate가 필요한 함수다. .text 전체 direct BL 스캔에서 target0x21EAA94 호출0, .rela.dyn function pointer reference0x42DA5C0 하나(메서드 등록 테이블 후보). 기존 structured MonoBehaviour JSON에서 PullObjectInRange 문자열0. 결과는 puller_call_scan.json/puller_serialized_callbacks.json에 보존. indirect/delegate/Unity event 또는 inline을 배제하지 않으므로 '사용 안 함'으로 확정하지 않는다.
PropPuller 타입 자체는 생성자만 있는 marker. sphere overlap이 있다는 이유만으로 모든 활성물체에 매프레임 이 힘을 적용하는 원작 계약이 확정된 것은 아니다. 웹에 연결한다면 상위 trigger/cadence를 [파생/확인 필요]로 분리해야 한다. 여기서는 원본을 실행하지 않았고 함수별 force 결과 실측은 없다.
