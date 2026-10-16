# Ground 및 홀 trigger 판독 (2026-10-14)

## 실제 저장 trigger
hole_trigger_native_chain.json은 First Skin 원본 native GO layer/Collider/부모 TRS를 함께 보존한다. 단순 중심거리 boolean을 원작형상이라고 쓰지 말 것.
- PropActiveTrigger: GO608 / Capsule1461 / TR703 / layer7 / isTrigger=true enabled=true / radius0.99 height100 direction1 / center(0,25.190315,0) / nodePos(0,23,0).
- PropPullerTriggger: GO186 / Sphere1459 / TR1150 / layer7 / isTrigger=true enabled=true / radius1.065000057 / nodePos(0,0,0).
- PropEattenTrigger: GO399 / Box1283 / TR984 / layer11 / trigger / size(2.25,2.25,2.25) / nodePos(0,-4,0).
- PropDropIn: GO558 / Box1376 / TR1082 / layer13 / trigger / size(2.25,1.49,2.25) / nodePos(0,-1.3,0).
- MagnetTrigger는 별도 layer7 capsule이며 저장 node scale2.85. 일반 홀에 항상 켜야 한다는 뜻은 아니다. GameObject.SetActive와 Collider.enabled는 서로 다르므로 JSON의 active도 확인할 것.

PlayerComponent.OnRadiusChanged0x21EC084, 0x21EC120~158: PlayerComponent의 루트Transform localScale = Vector3.one * radiusValue * float32(0.98). native literal0xE0A584 bytes48e17a3f. visual scale만 바꾸고 trigger 부모 scale를 고정하면 원작과 다르다. First Skin -> Component -> Box -> TriggerBody -> trigger 부모 연결은 JSON 원문 사용. OnRadiusChanged가 받은 값과 최초 Initialize scale는 구분.

## Ground는 실제 구멍 있는 충돌 메시
GroundMesh.Awake0x21D5408은 native Mesh 생성 / MeshFilter.sharedMesh / MeshCollider.sharedMesh 연결 후 GO layer6으로 지정한다.
GroundBehavior.FixedUpdate0x21D1938 -> SurfaceFixedUpdate0x21D193C:
player.position의Y를0으로 투영, EffectiveRadius(baseRadius*powerUpMultiplier)와 이전 radius를 비교. radius가 달라지면 RecalculateSurface0x21D1AD4. 같으면 이동diff.sqrMagnitude>float32(0.0001)일 때 UpdateSurfacePosition0x21D1E60. 매 시각 프레임에 무조건 모든 지면을 재생성하는 경로는 아니다.
RecalculateSurface는 Player.position/EffectiveRadius, ground halfSize를 사용한다. 0x21D1D14~40의 각도 표본은 i/24*360deg이며 i=0..23의 24개 표본(0x21D1DA8~B0에서 증가 후24와 비교). 이후 list index0을 사용하는 후처리와 append가 별도로 있으므로 25회 sincos 호출로 해석하지 말 것. sincosf PLT0x3F23D20를 호출하고 circle x/z를 ground의 +/-halfSize 범위로 clamp한다. 실제 한계/triangles/outer vertices 목록은 disasm 원문에 보존.
GroundMesh.Set0x21D2250는 입력 surfacevertices와 복제된 아래쪽 정점으로 측면을 만든다. 아래 방향10유닛 오프셋(0x21D2414~88). Mesh.Clear/SetVertices/SetTriangles/MarkModified 후 MeshFilter.mesh와 MeshCollider.sharedMesh 모두 같은 mesh로 갱신(0x21D266C~26DC).
즉 원작은 지면 지지가 실제로 구멍에서 사라지는 물리 구조다. 물체 fit 중심점<=r이면supportoff 같은 웹가정과 동일하다고 주장하지 않는다. 물체의 native collider와 회전/배치가 바닥삼각형과 접촉하면서 낙하에 들어간다. 이번 확인 범위에서 모든 물체를 가르는 단일 cost/radius fit 공식은 확인하지 않았다.

CreateGroundCollider0x21CFA7C는 다른 layer11 trigger Box를 만든다: bounds중앙XZ / worldY -7.5 / 높이1, XY바닥 support대용이 아니다. 홀위 원형 지지면과 이 아래 trigger를 혼동하지 말 것.

## 활성물체 제한
PropActiveCounter..cctor0x1CC582C의 raw literal0xE0AC80:
ActivePropsCount0 / MaxActiveProps1000 / MaxActivationsPerFrame10 / activationsThisFrame0.
currentYThreshold0 / yThresholdStep2 / lastFrameCount -1.
이 수치는 static 초기값이다. 런타임 변경 및 waiting Update의 모든 조건을 그대로 이식 완료한 것은 아니다. 기존 PROP_ACTIVATION.md의 한도/대기 경로 근거를 보강하며, 시간예산/PhysX 성능을 근거 없이 원작값으로 바꾸지 않는다.

## 미결과 적용 경계
ground poly의 모든 outer-bound 분기/triangles를 독립 실행 재현·검산한 것은 아니다. native shape 파편/ring 자체 world복원과 Web physics triangulation QA가 다음 구현 작업이다. PhysX와 현재 웹 엔진의 접촉해결까지 동등하다는 보장은 없다. PropPuller MonoBehaviour 자체는 생성자만 있는 marker이고, sphere overlap에서 PullObjectInRange를 호출하는 전체 별도물리/marker 소비 경로는 미확정이다.
