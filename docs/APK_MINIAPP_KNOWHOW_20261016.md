# APK 언패킹·미니앱 이식 추가 노하우

2026-10-16. 기존 [전체 추출 이력](../EXTRACTION_HISTORY.md)과 [공통 판독 원칙](../ANALYSIS_KNOWHOW.md)의 후속이다. 직접 작성한 사례 문서는 [사례 색인](REFERENCE_CASES.md)에 연결한다. 저장소에는 원본/추출 리소스를 넣지 않는다.

## 공통 작업 순서

1. 패키지/버전/엔진/메타데이터 버전/입력 SHA를 기록하고 immutable 원문을 보존한다. APK/XAPK/split/PAD/OBB와 앱이 이미 내려받은 캐시는 출처를 따로 기록한다.
2. 이미 받은 캐시 조사와 새 네트워크 요청을 구분한다. 기기에서 다른 앱·계정 폴더를 수집하지 않고, 앱 범위와 수집 임시물만 관리한다. 캐시에 있다는 사실은 실제 사용 호출 증거가 아니다.
3. native TypeTree 우선, 외부 script+metadata 폴백, 배열/정렬/최종 바이트 소비를 검사한다. 선언·저장값·생성자 초기값·실제 소비값을 구분한다.
4. 객체 키는 owner serializedfile + fileID/PPtr + pathID로 유지한다. 64bit ID를 JS Number로 바꾸지 않는다. 이름·에셋명·enum 숫자가 비슷하다는 이유로 관계를 추정 확정하지 않는다.
5. 원본 export count→출력 count→실패/누락 목록→해시/독립 바이트 fixture를 단계별로 검사한다. 프로세스 exit0은 의미 복원 성공이 아니다.
6. 모델/설정/게임 규칙/화면/원작 런타임 동등성을 별도 판정한다. 이식 버그를 원작 규칙으로 보정하지 않는다.

## Royal Smash → MiniApp: 구조와 물리

- 700레벨은 공통 엔티티 자산+레벨 데이터 런타임 배치로 처리한다. 레벨별 프리팹 굽기는 이식 측 임시 구조였으며 원본 요구사항으로 일반화하지 않는다. 배치 규칙은 에디터/런타임 공통 팩토리에 두어 전수 검사와 실제 플레이가 갈라지지 않게 한다.
- 런타임 레벨 교체 시 Destroy 지연으로 old/new collider가 한 프레임 겹쳤다. 이전 홀더를 먼저 비활성화하고 파기→새 레벨 생성으로 수정. 총 홀더 수와 **활성** 홀더 수를 나눠 기록한다. 관찰 전용 자동 FixedUpdate 프로브와 Physics.Script 수동 스텝 검사는 서로 다른 버그를 드러낸다.
- 기믹 Start를 무조건 Awake로 옮기는 해결책은 잘못이었다. 인스턴스 후 데이터 주입보다 빨리 기준 pose를 캐시하면 회귀한다. 저장 Rigidbody 상태/해당 컴포넌트 실제 개수를 먼저 확인한다.
- Instantiate 후 kinematic 받침 Transform 배치가 물리 포즈에 반영되기 전에 진행하면 지지면이 어긋날 수 있다. 공통 빌드 끝 SyncTransforms와 독립 A/B로 확인한다. 전체 무너지면 solver 수치부터 임의 변경하지 않는다.
- 움직이는 받침 레벨을 월드 drift만으로 불안정 판정하지 않는다. 지지면 상대 변위, 회전/왕복 기믹이 실어 나르는 이동과 실제 탈락/자체 파괴를 구분한다.
- TimeManager는 필드명과 런타임 API로 대조한다. 원본 사례 fixedDt .0125 / maximumDt .025 / maximumParticleDt .125. 두 maximum 필드를 바꾸거나 Unity6 rational 표현을 무조건 float 오독이라고 설명했던 주장은 철회됐다.
- JamJar 비공 충돌 임계는 저장 nb 단독이 아니라 es*nb였다. 낮은 nb를 속도 임계로 잘못 쓰면 정착 진동만으로 터진다. 저장 파라미터와 소비 식을 함께 확인한다.
- source stabilize=false에서 spawn sleep/freeze 또는 facet collider 크기를 임의로 고치는 근거가 없었다. 콜라이더 합치기 성능 결정은 원작 형상 완전동등성과 별도로 표시한다.

## MiniApp 시스템·UI·FX

- 시작 하트 차감/최종 실패 차감, 재시도 번호/같은 시도 continue 번호, 연승 종류, 보상 확정/팝업 표시를 별도 상태로 모델링한다. 같은 UI를 재오픈해 재화를 중복 커밋하지 않는다.
- 저장 UI의 이름보다 실제 text/callback을 확인한다. PlayOnButton이 Quit인 사례가 있었다. TMP 키워드, 9slice border 설정 덮어쓰기, 원본 음수 spacing/target fallback을 임의 보정하지 않는다.
- 파티클 보존은 계층 노드 수가 아니라 ParticleSystem/Renderer/Material/UV sprite/Emission/GO active가 실제 연결됐는지 검사한다. 재질 TextureEnv가 비어 있어도 UVModule sprite가 형상을 공급할 수 있다.
- startSize와 루트 scale을 혼동하면 자식 위치도 밀려 화면 밖으로 간다. 입자 live count가 양수여도 화면에 그려진다는 뜻이 아니다. 효과 실행/카메라 투영/픽셀을 분리한다.
- 원본 HDR flag가 없는 Color는 CPU 값이 같아도 GPU 업로드에서 변환될 수 있었다. GetColor/Vector만으로 색공간 가설을 부정하지 않고 float RT 픽셀 probe로 검사한다. shader feature 분기/Forward+ 보조광 누락도 별도로 검사한다.

## Goods Hunt: 데이터·런타임 소비

- 로컬 Level 에셋1126개, numbered910개, 초기 일반195개, LD LevelLoop1300행은 서로 다른 모집단이다. 루프 편성을 초기 진행 순서나 신규맵 수로 세지 않는다.
- gameMode 숫자는 확인한 범위에서 테마 구분이었다. 일반/특수 플레이 규칙이라고 임의 해석하지 않는다. backgroundTheme와 factory 입력도 단순 등치하지 않는다. 숨은 목표 enum 존재와 910개 저장 목표에서 실제 사용되는지는 별도다.
- PropIncomeValue[rawcost]→Score.Add→callback difference→성장 소비를 따라간다. 업그레이드 계정 단계와 gameplay size 단계를 분리하며 이름이 HoleSize라고 같은 상태로 보지 않는다.
- 일반 props는 초기 kinematic/Sleep 및 원문 collider를 유지하고 trigger/lifecycle에 맞춰 활성화한다. 시작부터 전부 dynamic으로 두어 배치를 밀거나 임의 outward push로 숨기지 않는다. normalphysics .5초/2초 비활성 전환 복원이 실제 작업량을 줄였다.
- Unity angularDrag20을 Cannon angularDamping20으로 복사하면 pow(1-20,dt)에서 NaN이 났다. 물리 엔진 매개변수의 단위/수식 차이를 검증하고 파생 adapter를 표시한다. 성능 보정을 원작 값으로 주장하지 않는다.
- ordinary prefab root 저장 TRS는 placement가 덮어썼다. root pose를 geometry/collider에 bake한 뒤 배치를 다시 적용해 우유팩의 실제 visual과 물리 기준점이 크게 어긋났다. 자식 TRS는 유지하고 root override 계약을 확인한다.
- renderer.worldY<-2.3 drop 진입과 Rigidbody rootY 기반 Eaten을 혼동하지 않는다. inHoleDrop 진입 전 먹힘 검사/같은 step 전환 순서가 갑자기 사라짐의 원인이었다. bigObject/CanFallSlow 필드도 다르다.
- collider가 Capsule/MeshCollider이면 renderBBox fallback으로 정상 복원됐다고 쓰지 않는다. Kiwano/Mango/Starfruit의 실제 부모TRS와 source collider 연결을 복원해 검증했다.
- 지면 원본37top/156indices→74verts/534indices 및 clamp/inner update fixture는 렌더와 물리 topology의 기준이다. Cannon convex prism adapter의 접촉과 PhysX triangle mesh 동등성은 별개다.
- SAT 최적화는 형상/접촉 순서/최종 pose+state deepEqual과 CPU 시간을 함께 검사했다. 활성 lifecycle 복원은 작업량 변화이므로 pose-exact 최적화와 구분한다. CPU 개선을 실제 FPS/원작 PhysX 정합으로 확대하지 않는다.

## Goods Hunt: 소비 경로와 UI/FX

- 보유/언락/지속시간 저장값과 실제 scaled/unscaled 시간·게임 활성·일시정지·재사용 gate를 따로 판독한다. 공통 ActivatePowerUp 말미의 최초입력 이벤트가 카메라/시계도 시작했다.
- 목표 일반 baseProp fly callback의 .2delay+.6 이동 후 Reduce와 Triggerable directReduce를 나눈다. 숫자 감소/논리 clear와 카드 tick/flip/reflow 완료를 같은 시점으로 합치지 않는다.
- Spine TrackEntry 특정 float를 timeScale이라 추정하면 안 된다. 실제 선언 offset을 확인해 TrackTime1.65/SG.timeScale1을 분리했다. 절대scale .55/.65, color alpha .5→1, easing/hold 역시 각각 기록한다.
- PS renderer on이라도 emission off이면 방출하지 않는다. UV disabled인데 sprite가 참조돼 있다는 이유로 활성화하지 않는다. world PS를 overlay canvas에 임의 reparent/100배 확대하면 원본 표시 경로 복원이라 할 수 없다.
- Additive gameplay 카메라와 로비 카메라의 culling mask를 분리한다. 로비 layer0 제외만으로 모든 카메라에서 안 보인다고 단정하지 않는다. Pool parentnull/worldPositionStays와 실제 카드 worldPosition의 런타임 투영이 남으면 표시 여부는 미확정이다.
- 같은 이름 Sprite도 원본 rect/PPtr/atlas가 다를 수 있다. Exit 버튼128px 원본과188px 이름동일 PNG를 구분해 정확 원본을 선택했다.
- OBJ exporter X/normalX/triangle winding을 독립 확인한다. native shader 입력을 돌릴 때 좌표 복원과 출력 행렬 bridge/Three winding을 두 번 뒤집지 않는다. compiled GLSL main 보존이 SH/probe/shadow/GPU 전체 동등성을 의미하지 않는다.

## DKBI 후속·UE3 모션

- DKBI field16과 Town70, 저장 entity와 활성 NPC/renderer를 분리한다. native MeshMaterial PPtr exact 연결·Unity readback·파생 shader GPU 검토를 원작 Shader runtime load 성공/게임플레이 완료와 구분한다.
- 원본 shader와 정상 Shader+Material bundle의 타입트리가 일치해도 compiled blob/의존성/엔진 버전 호환성은 별도다. 자동 import가 blob을 제거한 뒤 cached isSupported를 원본 GPU 성공으로 주장했던 기록을 철회한다.
- UE3 모델/모션 이름 중복은 export index로 회수한다. MD5anim의 가짜 parent0은 source mesh 계층으로 대체하며 모델/모션 bone 순서는 이름으로 조인한다. 파트마다 bind rest가 다르면 이름70개가 같아도 한 스킨으로 합치지 않는다.
- MD5가 표현하지 못하는 compressed scale/실제 키 시간/rotation-only/additive 정책은 sidecar로 보존한다. None/Identity/Float96/Fixed48/IntervalFixed32 및 per-track header/time offset을 실제 bytes로 검사한다.
- 최신 모션 및 생성 스킨 검증의 추가 제한은 [Motion Remap 노하우](MOTION_REMAP_KNOWHOW.md), [Multi 재개 정본](MULTI_SKINNING_RESUME_20261016.md)을 본다. GLB native key 보존과 Blend 커브 보존은 별개다.

## 사례 축적 원칙

새 게임에서 해결된 항목은 공통 CLI/설정/사례 연구 중 어디에 속하는지 표시한다. 실패·정정·원문 offset/hash·독립 fixture·제품 회신 ACK를 남긴다. 사례가 늘었다는 이유만으로 범용 자동해독/전모션 무관통/서버 규칙 복원 성공을 주장하지 않는다.
