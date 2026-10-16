# Props 名칭 중복 해소 원문 / 2026-10-14

Goodhunt manifest.unresolved 18개 레코드를 입력 목록으로 삼아 원본 props bundle을 읽었다. 이름은 대상 후보 선택에만 사용했고, 이후 계층과 메시·재질의 연결은 원본 PPtr로 보존했다. 동일 이름 후보가 여러 프리팹에 있어 49개 GO / 39개 루트의 관련 계층을 포함했다. 전체 551타입 추출이나 importer 구현은 하지 않았다.

- chains.json: 원문 요청 목록 / 발견 노드 / 루트별 원문 TRS와 부모·자식·컴포넌트 / MeshFilter·Renderer·콜라이더 등.
- native_object_index.jsonl, records.json: 새 GO/Transform/MeshFilter/Renderer 원문 레코드 색인. json_file은 이 폴더 기준이며 원본 색인에 append하지 않았다.
- GameObject/, Transform/, MeshFilter/, MeshRenderer/ 등의 개별 JSON: native read_typetree 원문. source SHA/raw SHA/파일/pathID는 색인에 기록.
- reference_edges.json: Mesh 및 Material 참조를 기존 results/native_object_index.jsonl의 정확한 serialized_file/path_id로 조인. 성공 status와 미해결 status를 구분했다.

source: input_prepared/assets/aa/Android/props_assets_all_8cfb9dc23d45f5ca0c92cd5f38151ff7.bundle
serialized_file: CAB-5388c821bd9df28739ab71fc81803c09
실행 peak private commit 약0.171 GB. 원본/기존추출물/Goodhunt 소스 수정 없음.

주의: pathID는 64bit 정수다. JavaScript Number로 JSON을 읽으면 정밀도가 유실될 수 있으므로 기존 lossless parser를 사용할 것. namesame이라고 다른 Mesh를 선택하지 말 것. 각 노드의 m_Mesh와 m_Materials를 적용하고 기존 native index의 OBJ/source를 찾을 것. OBJ는 UnityPy 좌표 변환 산출물이고, 원문 TRS/PPtr는 native값이다. 좌표계 정합은 importer 책임이며 중복 변환하지 말 것.

런타임 프리팹 선택/활성화·ThemeProps GUID 조인·흡수 게임 규칙을 검증했다는 뜻은 아니다. 이 파일로는 저장된 계층과 메시 참조만 확정한다.
