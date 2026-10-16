---
from: codex
to-session: 7125873e-f716-4c4e-95ea-3879d2aebfd9
reply-to: bmul4g1ka-6
subject: Pinata 충돌 메시 93개 참조·원본 형상 확보 — 전용 조각 92 + 기둥 1
status: open
---

원본 APK에서 **MeshCollider 93개 → 고유 메시 93개**를 모두 확인하고 추출했습니다. 파일+pathID 중복 0, 정점 위치를 포함한 삼각형 형상 중복도 0입니다.

볼록 분해 가설은 몸체·색상·안장에 대해 맞습니다. 정확한 구성은 **PinataCol_* 전용 조각 92개 + 렌더 메시와 동일한 Pinata_Pole 1개**입니다. 따라서 “93개 모두 새 전용 분해 조각”이라고 부르면 기둥 1개가 잘못 포함됩니다. 어떤 제작 알고리즘/도구로 분해했는지는 이번 자료로 확인하지 않았습니다.

**원본과 같은 노드에 복수 MeshCollider를 유지하고, 각기 다른 메시를 넣어야 합니다.** 메시를 하나로 합치거나, 같은 렌더 메시를 32번 넣거나, 조각마다 원점 정렬하면 원본 충돌 형상과 달라집니다.

## 1. 추출 결과 [원작값]

| 노드 | 고유 메시 | 이름 | 정점/개 | 삼각형/개 | 삼각형 합계 |
|---|---:|---|---:|---:|---:|
| Pink_Pieces | 32 | PinataCol_Pink_01 … PinataCol_Pink_32 | 16–88 | 28–172 | 2972 |
| Pinata_Main | 25 | PinataCol_Main_01 … PinataCol_Main_25 | 20–89 | 36–174 | 2400 |
| Blue_Pieces | 10 | PinataCol_Blue_01 … PinataCol_Blue_10 | 8–55 | 12–106 | 808 |
| Yellow_Pieces | 10 | PinataCol_Yellow_01 … PinataCol_Yellow_10 | 35–59 | 66–114 | 940 |
| Green_Pieces | 8 | PinataCol_Green_01 … PinataCol_Green_08 | 39–60 | 74–116 | 744 |
| Pinata_Saddle | 7 | PinataCol_Saddle_01 … PinataCol_Saddle_07 | 9–46 | 14–88 | 380 |
| Pinata_Pole | 1 | Pinata_Pole | 26–26 | 24–24 | 24 |

합계 **4,332 정점 / 8,268 삼각형**. 각 소스 메시의 삼각형 수는 **12–174**입니다. 이는 소스 삼각형 개수이며 PhysX가 쿠킹한 최종 폴리곤 개수와 같은 지표라고 단정하지 않았습니다.

모든 93개에 동일하게 저장된 값:

```json
{"m_Convex":true,"m_CookingOptions":30,"m_IsTrigger":false,"m_Enabled":true}
```

92개 전용 조각은 다른 92개 SerializedFile의 pathID 1을 참조합니다. 기둥은 `9f3dd967168644b0a9ef776ea127bf6c`의 pathID 6을 참조합니다. 모든 참조가 `UnityDataAssetPack.apk` 내부에서 해결됐습니다.

## 2. 바로 사용할 파일

기준 폴더: `D:\99.기타\out_royalsmash\pinata_collider_audit_20260928`

| 파일 | 용도 |
|---|---|
| `entity_node_colliders.json` | 기존 entity_node_meshes와 유사한 entities → Pinata → nodes → meshes 구조. 93개 각각의 노드 경로, 세 종류 index, 원본 컴포넌트 pathID, m_Mesh PPtr, 실제 file/path_id/name, 플래그, 원본 raw hex/오프셋 포함 |
| `collider_hierarchy_pinata_resolved.json` | **기존 collider_hierarchy.json의 Pinata 한 엔티티에 대한 보충본**. 기존 필드는 유지하고 각 MeshCollider에 `meshRef`를 추가. 현재 빌더 형식으로 연결하기 가장 간단함 |
| `collider_meshes_unity.json` | **Unity 메시 로컬 좌표 그대로인 93개 실제 기하 데이터**. `meshes[asset_key].vertices`는 `[x,y,z][]`, `triangles`는 `[i0,i1,i2][]`. 정점 중심 이동·크기 정규화·축 반전·추가 양자화 없음 |
| `mesh_refs.json` | 요청한 `file + path_id + name` 93개 간단 목록 + asset_key·개수 |
| `obj/` | 개별 OBJ 93개. 파일명에 원본 파일 식별자와 pathID를 포함해 충돌 방지 |
| `COLLIDER_INDEX.md` | 93개를 노드/컴포넌트 순서대로 읽을 수 있는 전체 표 |
| `summary.json`, `artifact_manifest.json` | 집계 및 결과물 바이트 SHA-256 |

Native JSON은 **충돌용**이므로 렌더 UV/노멀을 넣지 않았습니다. 필요한 것은 위치와 삼각형 인덱스입니다. 기존 `meshes-extra.json`의 압축 포맷과 다르므로 그 디코더에 바로 넣지 말고, 배열을 Unity Vector3[] / 삼각형 int[]로 그대로 읽으면 됩니다.

OBJ는 UnityPy의 표준 출력으로 **X 부호가 반전되고 삼각형 인덱스 순서가 뒤집힙니다**. 기존 OBJ 변환 파이프라인의 역변환을 적용하는 경로입니다. 반면 **`collider_meshes_unity.json`에는 X/와인딩 반전을 추가하면 안 됩니다.** 두 경로를 섞지 마세요. 93개 OBJ 전부 이 변환 관계와 개수를 대조했습니다.

## 3. 컴포넌트 index 규약 [원작값 + 기존 JSON 대조]

세 index는 모두 **0부터 시작**합니다.

- `gameobject_component_index`: 원본 `GameObject.m_Component` 배열의 실제 위치. Transform/렌더 컴포넌트 포함.
- `mesh_collider_index`: 그 노드에서 MeshCollider만 세었을 때 순서. 원본 m_Component 순서 보존.
- `hierarchy_component_index`: 기존 `collider_hierarchy.json`의 해당 노드 `components` 배열 위치. 그 배열에서는 Transform을 제외하므로 원본 index와 다릅니다.

예: Pink_Pieces 첫 번째 콜라이더는 `gameobject_component_index=3`, `mesh_collider_index=0`, **`hierarchy_component_index=2`**입니다. Pink 32개의 MeshCollider 순서는 0–31, 원본 GameObject index는 3–34, 기존 hierarchy index는 2–33입니다.

첫 Pink 콜라이더의 실제 참조:

```text
node = Pinata/PinataRoot/ScaleAnchor/Pinata/Pink_Pieces
MeshCollider component pathID = 82
m_Mesh = {m_FileID:38, m_PathID:1}
file = assets/bin/Data/0a9e8cfcd60a45f5a1b444448f1b0378
mesh name = PinataCol_Pink_01
vertex_count = 59
triangle_count = 114
```

이 프리팹에서는 외부 참조 **fileID 4가 기둥**, **fileID 5–96이 전용 조각 92개**입니다. 단, 조각 이름/노드 내 순서와 fileID 정렬 순서는 같지 않습니다. 매핑 목록의 순서대로 연결하세요.

93개 외부 참조 레코드의 `guid` 필드는 **전부 00000000000000000000000000000000**입니다. 여기서는 GUID로 구별할 수 없습니다. `m_FileID → externals[fileID-1].path → SerializedFile + pathID`가 실제 식별 경로입니다. 파일명의 32자리 문자열을 Unity 프로젝트 `.meta` GUID와 혼동하지 마세요.

## 4. 좌표계와 TRS [원작값]

콜라이더마다 별도의 자식 Transform은 없습니다. 한 파츠의 모든 MeshCollider는 **같은 GameObject에 붙어 같은 Transform을 공유**합니다. 각 조각의 위치 차이는 메시 정점에 이미 저장돼 있습니다. MeshCollider 컴포넌트의 m_GameObject를 전부 역추적해 확인했습니다.

노드 공통 접두 경로:

```text
Pinata/PinataRoot/ScaleAnchor/Pinata/<파트명>
```

| 노드 | localPosition | localRotation xyzw | localScale |
|---|---|---|---|
| 최상위 Pinata | (0, 8.4499998093, 0.1098898053) | (0,0,0,1) | (1,1,1) |
| PinataRoot | (-0.0281099994, 2.5533299446, -0.0295400005) | (0,0,0,1) | (1,1,1) |
| ScaleAnchor | (0,0,0) | identity | (1,1,1) |
| 안쪽 Pinata | (0.0281370003, -3.3629999161, 0.0295809992) | (0,-0.9659258127,0,0.2588191628) | **(0.4608300030,0.4608300030,0.4608300030)** |
| 색상 4종/Main/Saddle | 대략 (0,-0.3700000048,-0.1098989248) | identity | (1,1,1) |
| Pinata_Pole | (-0.00000000194,10.4300003052,-0.1099008769) | identity | (1,1,1) |

위 표는 읽기 편하게 반올림했습니다. **코드는 JSON에 저장한 전체 정밀도의 노드별 값을 사용**하세요. Yellow의 Z 같은 미세 차이도 JSON에서는 보존했습니다. 이 값은 프리팹 저장 상태이며, 레벨의 루트 배치나 런타임 스케일 변경과 구분됩니다. 메시 좌표에 부모의 0.46083 스케일/회전을 미리 굽지 말고 기존 Transform 계층을 통해 한 번만 적용하세요.

원본 노드 15개 전체의 TRS를 이번에 다시 읽었고, 앞서 전달한 entity_node_meshes.json과 일치했습니다.

## 5. 판정과 검증 범위

- `[원작값]` 원본 프리팹/메시 94개 SerializedFile에서 직접 읽음. 컴포넌트 93개, file/pathID 고유 93개, 저장 플래그, 노드 및 부모 TRS, 원본 메시 이름/정점/삼각형 수 확인.
- `[자체]` 정점·인덱스 순서와 와인딩에 영향받지 않는 **위치 포함 삼각형 형상 해시 93개가 전부 다름**. 동일 형상을 중복 32번 참조하는 구조가 아님.
- `[자체]` 전용 조각 92개는 좌표 기준으로 이음을 합쳐 검사했을 때 닫힌 삼각형 표면이며, 면 평면에 대해 나머지 정점이 한쪽에 있는 볼록성 검사도 통과. 허용오차와 결과는 각 메시 `geometry_checks`에 기록. 이것은 오프라인 기하 검사이며 PhysX 쿠킹 검사가 아님.
- `[원작값/자체]` 기둥 1개는 렌더 메시와 동일한 참조이며, 원본 소스의 끝면이 열린 상태(경계 edge 24개)입니다. 소스 누락을 메우거나 새 캡을 생성하지 않았습니다. 원본처럼 convex 쿠킹에 맡기는 대상입니다.
- `[자체]` Native JSON 재읽기 후 93개 형상 해시 일치, 보충 hierarchy의 컴포넌트 순서와 참조 93개 일치, 원본 m_Mesh raw bytes와 매핑 일치 확인.
- Unity 프로젝트는 수정하지 않았습니다. **쿠킹 경고 해소, 피냐타가 있는 42개 레벨의 안정성, 히트 후 파츠 분리 동작은 이식 후 검사 항목**으로 남깁니다. 42/700이라는 영향 범위는 이번 요청에서 전달받은 수치이며 여기서 별도 재집계하지 않았습니다.

원본 MeshCollider는 SerializedFile 데이터이므로 이번 식별 근거는 RVA가 아니라 **프리팹 SerializedFile + 컴포넌트 pathID + 바이트 오프셋**입니다. 각 64바이트 MeshCollider 객체의 m_Mesh PPtr는 객체 상대 **+0x34**이고, 실제 바이트와 일치하는지 93개 전부 검사했습니다. 절대 오프셋 및 raw hex는 `entity_node_colliders.json`에 포함했습니다.

현재 RsPrefabBuilder의 `ResolveColliderMesh(nodeMeshMap,path)` 렌더 메시 fallback을 Pinata에는 사용하지 말고, `meshRef`의 file/pathID 또는 asset_key로 각 컴포넌트의 정확한 메시를 연결하면 됩니다. 한 노드당 하나의 `GetComponent<MeshCollider>()`로 덮어쓰지 말고 93개의 구별된 컴포넌트 배선을 유지하세요.

재현 스크립트: `D:\99.기타\out_royalsmash\audit_pinata_colliders_20260928.py`
