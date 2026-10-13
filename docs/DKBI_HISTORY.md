# DKBI 분석 이력과 재개 지점

정리일: 2026-10-13. 마지막 확인된 추출·Unity 검증 보고서는 2026-10-08.
이번 갱신은 기존 근거 확인과 문서 정리이며, 게임 실행이나 새 전체 추출 결과가 아니다.

이 문서는 직접 작성한 분석 방법·상태·실패 이력만 포함한다. 원본 프로그램, 이미지,
추출 표, 메시, 컴파일 셰이더와 역어셈블 본문은 로컬에 보존하며 Git에 포함하지 않는다.

## 대상과 범위

- 설치 제품 속성: 도깨비의세계, supercat, 제품 버전26.102.018.
- 원본 Unity6000.3.24f1 / IL2CPP metadata39. 제품 버전과 엔진 버전은 별개다.
- 목표: 로그인·실서버 없이 로컬 필드 이동/타겟팅/기본공격/스킬 구현을 위한 근거 확보.
- 원본 설치본을 수정하거나 인증·서버 규칙을 복원하는 작업은 하지 않았다.
- 분석은 소범위 순차 실행. 원본 파일·추출 결과·공통 코어의 기존 변경을 보존한다.

## 단계별 이력

| 단계 | 확인한 것 | 검증 경계·남은 일 |
|---|---|---|
| 설치본·전체 추출 | 제품 속성, 자산 색인, native 자료와 표를 확보 | 파일 확보는 데이터 의미나 실행 성공을 뜻하지 않음 |
| metadata39 | 초기화·타입 선언과 일부 등록 상수 조사 | PE loader 모듈 누락/등록 주소0 뒤 exit0 이력은 dump 성공으로 취급하지 않음. 실제 메서드 본문/RVA 복원 미결 |
| 행동 그래프 | 선택3그래프85파라미터, 확장626파라미터의 원본 관계를 보존·대조 | node 이름과 파라미터만으로 실행 순서·시간 단위·공격 판정을 확정하지 않음 |
| 필드 데이터 | 선택필드의71영역/44스폰/4actor ID 관계 확보 | 실제 최초 진입·서버 활성 구역·typed join의 미확정 부분을 분리 |
| ECS 씬 연결 | 루트와 하위16섹션,6,897엔티티/261chunk,33hash를 구분 | TypeInfo32개/미확정1개. 타입 이름·배열 순서 일부는 호환 소스 기반 후보 |
| 렌더 참조 | shared681개와 render6,394개 연결, managed tail537개 해석·원본 재판독 | 객체 참조를 추출한 것과 원작 활성 렌더를 구분 |
| Action 측 native 자산 검증 | 메시259개, 텍스처137개, 재질126개 정보와 배치6,394개 확인 | 실제 렌더·물리·게임 룰 동등성 검사가 아님 |
| 지형 검토 씬 | TRS6,389개/행렬 적용5개/누락0, 위치 오차 검산 | wire 검토 씬은 runtimeReady=false, rendererActivationKnown=false. 물리·nav 미포함 |
| URP 연결 | pipeline/renderer 참조와 저장mode2=ForwardPlus의 enum 근거 확보 | 원작 package semver와 일부 feature 본문은 미확정. 로컬17.3.0을 원작 버전으로 쓰지 않음 |
| 원본 셰이더 재사용 | native 원문·컴파일 데이터 보존, Editor import와 번들 격리 시험 | 초기 load/support 성공 주장 철회. 원본 GPU 보존·호환성 미해결 |
| 원본 식 조사 | TerrainLit ForwardLit fragment 대표 DXBC 표본과 파라미터 매핑 확보 | 대표 표본이며 전체 variant·원본 HLSL 회수나 화면 동등성 증명이 아님 |

Action 측 검증은 전달받은 보고서와 기존 파일에서 확인했다. 이 문서 정리 중 Unity 검사를
다시 실행한 것은 아니다. 보고서에 없거나 서로 다른 수치가 있으면 해당 필드의 범위를 먼저 본다.

## ECS 조사에서 일반화한 기법

1. 루트 씬과 child section의 GUID를 실제 header와 대조한다. 루트 엔티티 수를 필드 전체 수로 읽지 않는다.
2. stable hash 원문/등록 상수/TypeInfo 크기/호환 패키지 계산을 별도 근거로 보존한다.
   해시 재계산 실패나 크기 일치만으로 타입 이름을 확정하지 않는다.
3. chunk flag를 먼저 해석한다. chunk component의 일반 entity stride0 분기를 놓치면
   그 뒤 Transform 후보가 연쇄적으로 틀어진다.
4. LocalTransform과 LocalToWorld는 부모가 있으면 다르다. 부모160개와 위치 차이를 연결하고,
   실제 월드 검토에는 해당 검증 조건 아래의 월드 행렬을 사용한다.
5. shared prefix와 managed tail을 길이·사용 count에 따라 구분한다. header0을 무조건 null로 읽지 않는다.
6. RMA 인덱스→object reference table→native PPtr→Mesh/Material을 연결한다.
   pathID나 material 이름만으로 모든 entity를 array0에 배치하지 않는다.
7. 메시 채널과 triangle 순서를 원본 바이트로 검증한다. OBJ 축 변환이나 임의 재중심화를 하지 않는다.
8. float bit-exact 비교와1e-6 근접 비교는 별도로 기록한다. 허용차 통과를 원문 일치라고 쓰지 않는다.

## 셰이더 성공 주장 정정

처음 NativeFormatImporter가 반환한 동일 이름 Shader와 `supported=true`는 최종 호환 성공이 아니었다.
Unity 자동 import가 native 파일을 Editor YAML로 변경하면서 compressedBlob/platform/stage 정보를
제거했다. 초기 pre/post 동일 해시 검사는 이미 변환된 구간이었다. reimport 후 unsupported를 확인했고,
컴파일 원문은 immutable bytes로 별도 보존했다. 초기 메모리 객체를 proxy라고 단정할 근거도 없다.

원문·프로그램·type hash를 유지한 번들 wrapper5변형은 실제 로더의 호환성 검사에서 모두 실패했다.
outer version, SerializedFile version, template flags, CAB 이름 변경은 이미 시도했으므로
다음 세션에서 새 해결법처럼 반복하지 않는다.

성공한 정상 대조군은 **TextAsset 번들**이다. 원본과 대조군은 SF22/platform19/TypeTree=true지만,
이것만으로 Shader 직렬화 호환성을 증명할 수 없다. Direct3D12와 원본 D3D 컴파일 정보도
별도 GPU 비교 대상이며 현재 bundle load guard의 원인으로 확정하지 않는다.

다음 최소 시험:

1. 현재 Editor에서 실제 Shader+Material을 담은 작은 정상 번들 생성 후 load/GPU 확인.
2. 동일 Shader 번들을 UnityPy로 변경 없이 roundtrip해 load/GPU 재검사.
3. 원본 class48과 대조군의 TypeTree 필드 경로·타입·version·meta flags 대조.
4. 대조군 통과 뒤 작은 원본 fallback Shader부터 원문 보존 시험.
5. 원본 load가 통과한 뒤 그래픽 API·픽셀 비교. 정확한 원작 Editor 버전 시험은 이후 후보이며 성공 보장은 없음.

이 시험의 완료 결과는 아직 없다. 원본47속성·TexEnv·pass와 컴파일 명령을 바탕으로 만든
검토용 셰이더는 **파생 구현**이다. 편집 가능한 원본 HLSL/ShaderGraph 소스는 확인한 범위에서
발견하지 못했으며, 파일명 조사 결과를 모든 payload의 부재 증명으로 확대하지 않는다.

## 현재 미결

- 원작 활성 렌더·renderer feature 실행과 최종 색감/그림자 동등성.
- collision raw후보349개의 형태·좌표계와 nav/pathing 복원.
- 입력·이동·타겟팅·공격의 실제 단위·타이밍·판정 본문.
- PC base/skin LUT를 runtime lookup으로 합성하는 본문·호출 순서.
- 실제 최초 필드와 서버 활성 규칙. 현재 조사 범위는 로컬 필드 재현이며 로그인 불필요.

## 로컬 근거와 재개

GitHub에 아래 파일들이 있다는 뜻이 아니다.

- 분석 정본: `../out_dkbi/systems_recovery_20261008/README.txt`.
- ECS: 같은 폴더 `ecs_selected/field_all_children_shared_binding_summary.json`,
  `field_all_children_shared_binding_validation.json` 및 child별 원문/offset 기록.
- URP: `urp/HANDOFF.txt`, `metadata/urp_original_declarations.json`.
- 셰이더: `shader_source/HANDOFF.txt`, `COMPATIBILITY_FOLLOWUP.txt`,
  `shader_compatibility_container_audit.json`.
- Action 프로젝트 로컬 `reference/`: `field_geometry_mesh_validation.json`,
  `field_geometry_scene_validation.json`, `native_field_texture_validation.json`,
  `native_shader_probe.json`, `native_terrain_material_validation.json`,
  `terrain_shader_dxbc_sample.json`.
- 재개 순서: Action 새 회신·Shader 대조군 결과→기존 근거 대조→필요한 소범위만 추가 조사.
  마지막 MCP 인계는 queued로 남아 있으므로 전달/반영 완료로 쓰지 않는다.

메모리 감시: 분석용 별도 프로세스 commit cap1536MB, RSS stop1280MB,
여유 RAM 시작6GiB/중단4GiB, timeout240초. 종료코드·로그·실제 파일 내용을 함께 확인한다.
독립 작은 Shader 비교 피크 RSS약82.6MB. 게임 전체 추출을 다시 돌릴 이유가 아니다.
