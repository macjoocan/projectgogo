---
from: codex
subject: Royal Smash 원본 판독 5건 — TNT·Bouncer·Pinata·Hammer 축·노드 메시
status: open
reply-to: bmul1brgo-1
---

# Royal Smash Unity 이식: 원본 판독 5건 답신

요청 ID: `bmul1brgo-1`. 원본 APK 1.13.359 / Unity 6000.0.62f1을 오프라인으로 재판독했다. 아래 수치는 생성자 기본값이나 툴팁 예시가 아니라 해당 프리팹/설정 오브젝트의 **저장값**이다. 원본 ELF의 실행 코드 판독은 별도로 표시했다. C:\00.SVN의 이식 프로젝트는 수정하지 않았다.

- `[원작값]`: 원본 저장 바이트 또는 명시된 원본 실행 코드에서 확인한 값·규칙. 실제 라이브 실행 관찰이라는 뜻은 아니다.
- `[원작필드]`: dump.cs의 필드 선언/메모리 오프셋. 이것만으로 숫자 값이 확정되지는 않는다.
- `[자체]`: 이번 추출기의 파일 형식·검증용 표현. 게임 값으로 사용하지 않는다.

**오프셋 주의:** 표의 `메모리`는 IL2CPP 인스턴스 오프셋, `오브젝트`는 직렬화된 MonoBehaviour 원시 데이터 시작 기준, `페이로드`는 그 안의 사용자 필드 시작 기준이다. 저장값에는 함수 RVA가 없다. SerializedFile 내 절대 위치는 `serialized_file_object_offset + object_offset`으로 계산한다. 모든 위치와 원시 hex를 `stored_values.json`에 기록했다.

## 1. Tnt — 프리팹마다 값이 다름

| [원작값] 프리팹 | blastForce | blastRadius | blastUpwards | autoTriggerTntRange | autoTriggerTntSpeed |
|---|---:|---:|---:|---:|---:|
| TntSquare_1 | 12 | 6 | 1 | 2.5 | 20 |
| Tnt | 10 | 4 | 1 | 2.5 | 20 |
| TntCylinder_1 | 12 | 6 | 1 | 2.5 | 20 |

**일반 이름 `Tnt`의 10/4를 `TntSquare_1`·`TntCylinder_1`에 공통 적용하면 원작 저장값과 달라진다.**

| 필드 | [원작필드] 메모리 | 오브젝트 | 페이로드 |
|---|---|---|---|
| `m_blastForce` | `0xF0` | `0xcc` | `0xac` |
| `m_blastRadius` | `0xF4` | `0xd0` | `0xb0` |
| `m_blastUpwards` | `0xF8` | `0xd4` | `0xb4` |
| `m_autoTriggerTntRange` | `0xFC` | `0xd8` | `0xb8` |
| `m_autoTriggerTntSpeed` | `0x100` | `0xdc` | `0xbc` |

출처(모두 `UnityDataAssetPack.apk/assets/bin/Data/`):

- `TntSquare_1`: `00cc6f31f6b5f4a4097a77be44f8bdb7`, MonoBehaviour pathID `41`, object 시작 `0x13c0`, 길이 `224` bytes.
- `Tnt`: `9f047d54693a7413788b43879cbe133a`, MonoBehaviour pathID `7`, object 시작 `0x4b0`, 길이 `224` bytes.
- `TntCylinder_1`: `e45c082554bb64eec86bd2f63c1fdea2`, MonoBehaviour pathID `39`, object 시작 `0x12f0`, 길이 `224` bytes.

관련 코드 위치: `Tnt.Explode RVA 0x393E00C / 파일 0x393A00C`, 생성자 `0x393E480 / 0x393A480`. 이번 표는 생성자 값이 아니라 위 저장 페이로드를 기준으로 한다.

## 2. BouncerSettings — minBallSpeed 실값 8

[원작값] `BouncerCylinder_1`부터 `_5`까지 모두 같은 설정을 참조한다: `86469d2c57d74831ac790ce740f5420d`, pathID `1`, 이름 `BouncerSettings`. payload 시작 `0x30`, 전체 길이 `104` bytes.

| 필드 | 저장값 | [원작필드] 메모리 | 오브젝트 | 페이로드 | float32 원시 hex(LE) |
|---|---:|---|---|---|---|
| `m_capZoneHeight` | **0.2** | `0x18` | `0x30` | `0x0` | `cdcc4c3e` |
| `m_capZoneHeightTall` | **0.3** | `0x1C` | `0x34` | `0x4` | `9a99993e` |
| `m_pushFraction` | **0.087** | `0x20` | `0x38` | `0x8` | `0e2db23d` |
| `m_ballSpeedMultiplier` | **0.68** | `0x24` | `0x3c` | `0xc` | `7b142e3f` |
| `m_ballImpactSpeedMultiplier` | **1.5** | `0x28` | `0x40` | `0x10` | `0000c03f` |
| `m_minBallSpeed` | **8** | `0x2C` | `0x44` | `0x14` | `00000041` |
| `m_maxSpeedMultiplier` | **0.8** | `0x30` | `0x48` | `0x18` | `cdcc4c3f` |

`m_minBallSpeed=8`은 툴팁과 실제 저장값이 일치한다. `m_pushFraction=0.087`, `m_ballSpeedMultiplier=0.68`, `m_maxSpeedMultiplier=0.8`을 툴팁의 예시 숫자로 덮어쓰지 않는다. 표의 소수는 읽기 편한 십진 표기이며 JSON에는 정확한 float32 판독값이 있다.

관련 코드: `get_MinBallSpeed RVA 0x38359EC / 파일 0x38319EC` (`+0x2C` 필드). `CapZone RVA 0x383482C / 파일 0x383082C`.

## 3. Pinata — 타격 값과 실제 List 순서

[원작값] `95094b71c5d0049f188cddc77bd37f68`, MonoBehaviour pathID `143`, root GameObject pathID `9`, 전체 `684` bytes.

| 필드 | 저장값 | [원작필드] 메모리 | 오브젝트 | 페이로드 | 원시 hex(LE) |
|---|---:|---|---|---|---|
| `m_hitMomentumMultiplier` | **4.75** | `0x154` | `0x248` | `0x228` | `00009840` |
| `m_hitFlatten` | **0.4** | `0x158` | `0x24c` | `0x22c` | `cdcccc3e` |
| `m_hitMaxSpeed` | **40** | `0x15C` | `0x250` | `0x230` | `00002042` |

`m_pinataParts` 메모리 `0xF0`: 저장 count는 object `0xCC`, 값 `6`. PPtr은 `fileID:int32 + pathID:int64`, 엔트리당 12 bytes이며 아래는 **저장 List 순서**다.

| List index | GameObject 이름 | fileID / pathID | PPtr 오브젝트 위치 | TakeHit 순서 |
|---:|---|---|---|---|
| 0 | `Pinata_Saddle` | `0 / 3` | `0xd0` | 1번째 |
| 1 | `Pink_Pieces` | `0 / 11` | `0xdc` | 2번째 |
| 2 | `Yellow_Pieces` | `0 / 12` | `0xe8` | 3번째 |
| 3 | `Green_Pieces` | `0 / 5` | `0xf4` | 4번째 |
| 4 | `Blue_Pieces` | `0 / 8` | `0x100` | 5번째, 마지막 타격 |
| 5 | `Pinata_Main` | `0 / 4` | `0x10c` | 5번째, 마지막 타격 |

[원작값: 실행 코드] `Pinata.TakeHit RVA 0x393B0CC / 파일 0x39370CC`: `0x393B130~0x393B158`에서 증가 전 hit count를 `BurstPart(index)`에 넘기고, 증가 후 count가 `parts.Count-1` 이상이면 마지막 분기로 이동한다. `0x393B238~0x393B254`에서 `Count-2`, `Count-1`을 차례로 `BurstPart`에 넘긴다. 따라서 6개 부품은 **안장 → 분홍 → 노랑 → 초록 → (파랑 + 본체)**, 총 5회의 TakeHit로 제거된다. 마지막 둘은 같은 호출 내 처리이며 따로 6번째 타격을 요구하지 않는다. `BurstPart RVA 0x393B6D4 / 파일 0x39376D4`.

## 4. Hammer.m_axis — 저장 프리팹 기준 +Z

**[원작값: 실행 코드] `m_axis = m_rb.rotation * Vector3.forward;`**

`Hammer.Start RVA 0x3833310 / 파일 0x382F310`:

- `0x3833374~0x3833378`: `m_rb(+0x70)`의 `Rigidbody.get_rotation` 호출 (`RVA 0x7A9C940`).
- `0x38333B8~0x38333D4`: Vector3 타입 슬롯 `0x8235A90`의 static fields `+0x48/+0x50`, 즉 `forwardVector`를 읽는다. `Vector3.get_forward RVA 0x79DF00C`가 동일 타입 슬롯과 오프셋을 읽는 것으로 교차 확인했다.
- `0x38333D8`: `Quaternion.op_Multiply(Quaternion, Vector3)` (`RVA 0x79DFE28`).
- `0x38333E8`, `0x383340C`: 결과 xyz를 `m_axis(+0x94/+0x98/+0x9C)`에 저장한다.
- `Vector3..cctor RVA 0x79DF4F8`의 `0x79DF5B4/0x79DF5B8`에서 forward를 `(0,0,1)`로 초기화한다.

[원작값: 저장 참조] Hammer 파일 `46d28dd7256b2441b9ef78d27784dea3`, MonoBehaviour pathID `31`. `m_rb`는 object `0xDC` / payload `0xBC`에 저장된 `(fileID=0,pathID=27)`이며 **HandleRB** GameObject pathID `3`, Transform pathID `15`로 연결된다. Hammer root와 HandleRB의 저장 회전은 모두 `(0,0,0,1)`이다. 따라서 추가 배치 회전이 없는 저장 프리팹 기준 축은 **`(0,0,+1)`**이다.

`Handle` Transform pathID `13`의 Y 180도 회전은 HandleRB 아래 자식의 회전이다. 그 자식의 forward를 축 계산에 대입하면 안 된다. 레벨에서 root/부모를 회전했다면 축도 위 식으로 계산해야 하므로 모든 인스턴스에 +Z를 하드코딩한다는 뜻은 아니다.

[원작필드] `m_axis(+0x94)`에는 SerializeField가 없고 직렬화 페이로드에도 없다. `Start`에서 계산한 값이다. `ApplyPose RVA 0x38337D8`의 `0x3833800~0x383380C`에서 이 축을 `Quaternion.AngleAxis`로 넘기는 것도 확인했다.

## 5. 엔티티 노드별 메시 매핑

[원작값] `entity_node_meshes.json`에 160종 / 3,649노드 / 1,177 MeshFilter·SkinnedMeshRenderer 참조를 기록했다. 비어 있지 않은 참조 1,169개를 **외부 파일 + pathID**로 전부 해결했고, 고유 메시 539개를 식별했다. 이름만으로 조인하지 않았다. 저장 null 참조는 8개로 보존했다.

[자체: JSON 사용법] `entities[entityId].nodes[]`에서 `path`, `transform_path_id`, `parent_transform_path_id`, `gameobject_path_id`, `local_position/rotation/scale`, `active_self`, `meshes[]`를 사용한다. `meshes[]`에는 컴포넌트 pathID, 원래 m_Mesh PPtr, 외부 경로, 실제 Mesh 이름/파일/pathID가 있다. 부모와 활성 상태를 유지하고, 동일 이름 노드는 Transform pathID로 구분한다. 좌표는 원본 Unity 값이다.

### Hammer: 3개 MeshFilter / 실제 메시 2종

공통 프리팹 파일 `46d28dd7256b2441b9ef78d27784dea3`, 메시 파일 `5cfcd9c5c799c4c2b9fa4edec5b773cf`.

| 노드(공통 Hammer/HandleRB/Handle/ 생략) | MeshFilter pathID | m_Mesh fileID/pathID | 실제 메시 이름 | 검증된 기존 OBJ |
|---|---:|---|---|---|
| `Hammer_Handle` | 25 | `3 / 1` | `Hammer_Handle` | `Hammer_Handle_1.obj` |
| `Hammer_Handle/Hammer1Pos/Hammer1/HammerHead` | 26 | `3 / 2` | `Hammer_Handle1` | `Hammer_Handle1_2.obj` |
| `Hammer_Handle/Hammer2Pos/Hammer2/HammerHead` | 24 | `3 / 2` | `Hammer_Handle1` | `Hammer_Handle1_2.obj` |

두 머리 노드의 이름은 `HammerHead`지만 실제 메시 이름은 **`Hammer_Handle1`**이다. 이름 유사도로 `Hammer_Handle`을 붙이면 잘못 연결된다.

### Table: 상판은 m_master → SliceInto → Surface에 할당

상판 `Surface`의 MeshFilter.m_Mesh는 네 프리팹 모두 `(0,0)`이다. 누락을 임의로 보완하지 않고, Table 컴포넌트의 실제 소스 참조를 별도 기록했다. `m_master` 메모리 `0x160`, object `0xA4`; `m_masterCollider` 메모리 `0x168`, object `0xB0`; `m_filter` 메모리 `0x170`, object `0xBC`.

| 프리팹 | 상판 m_master 이름 | 소스 파일 / Mesh pathID | 별도 masterCollider |
|---|---|---|---|
| `Table_Rect_Hard` | `Hard_Level_Sqaure_Table_8x8` | `20381bfddcb7d9046a87875869a78c65 / 1` | `null` |
| `Table_Round` | `Round_table_8x8` | `b11b14b169b874319ad2dabf2f85aaa4 / 1` | `Round_table_Coll_8x8` |
| `Table_Round_Hard` | `Hard_Level_Round_Table_8x8` | `ca9c88b4a6f395948bc27e6b0e656f14 / 1` | `Round_table_Coll_8x8` |
| `Table_Rect` | `Sqaure_Table_8x8` | `dc6715053af714db184f9a5b652a0359 / 1` | `null` |

`Sqaure` 철자는 원본 메시명 그대로다. `Table.Apply RVA 0x3944388 / 파일 0x3940388`: `0x3944418`에서 m_master를 읽고 `0x3944424`에서 SliceInto(`0x3944584`) 호출, `0x3944438~0x3944448`에서 m_filter에 결과를 set_sharedMesh(`0x79C3454`)로 할당한다. 기존에 확인한 9-slice 로직에 이 소스를 연결하면 된다. 일반 기둥 메시들은 `Table_Pole1`/`Table_Pole2`, Hard 기둥은 `Hard_Level_Table_Pole1`이다. Hard의 `table_Pole_v02` MeshFilter 두 개는 저장 null이므로 일반 기둥 메시를 임의로 붙이지 않는다.

### 기존 OBJ와의 교차 검사 및 남은 범위

- 고유 메시 539개 중 기존 OBJ **534개는 원본 Mesh에서 같은 exporter로 재생성한 전체 텍스트와 일치**했다 (`obj_mapping_verified=true`).
- Unity 기본 메시 4종 `Cube(10202)`, `Cylinder(10206)`, `Sphere(10207)`, `Quad(10210)`는 원본 main APK의 `assets/bin/Data/Resources/unity default resources`에서 이름·pathID를 확인했다. 기존 `RoyalSmash_meshes` 폴더에는 해당 OBJ가 없다. 이름은 추정이 아니다.
- `Can2Square_4/BrokenPieces/Can_Square_broken`: 원본 파일 `4c714bb26945e4e349afe180d6cf9694`, Mesh pathID `2`, 이름 `Can_Square_1x4`. 기존 `Can_Square_1x4_2.obj`는 동일 exporter 재생성 결과와 **불일치**한다. 실제 원본 참조 매핑은 확정했지만 이 기존 OBJ를 검증 완료로 표시하지 않았다. 기존 파일은 덮어쓰지 않았다.
- 저장 null 8개: Table Surface 4개, Hard table_Pole_v02 2개, Pinata/Rope/TubeView 1개, WreckingBall/View 1개. Table 생성 경로는 이번에 확인했다. 나머지 null 노드의 런타임 생성/할당 경로는 이번 범위에서 추가 판독하지 않았다.
- 로컬 저장 참조·값·정적 실행 경로를 확인했다. 이식 프로젝트 실제 플레이, 레벨 Custom 덮어쓰기, 원작 라이브 화면 일치 검증은 수행하지 않았다.

## 근거 파일과 재현

기준 폴더: `D:\99.기타\out_royalsmash\unity_bridge_20260928\`

- `stored_values.json`: 15개 컴포넌트 전체 저장 필드, 원시 hex, 메모리/직렬화 오프셋, 참조 대상, 끝까지 판독 검증.
- `entity_node_meshes.json`: 160종 노드별 매핑과 Table 상판 소스.
- `sources.json`: 읽은 SerializedFile의 APK member 경로·SHA256.
- `verification.json`: 원본 APK 3개와 native library 해시 검증, 필드/참조 검증, 정확한 한계.
- `*_schema.txt`, `*.asm`: dump.cs 선언과 이번 판독 대상 역어셈블. Table.Slice/Platform.Step은 중복 역어셈블하지 않았다.
- 생성기 `D:\99.기타\out_royalsmash\audit_unity_bridge_5.py`; 검증/답신 생성기 `finalize_unity_bridge_5.py`.

검증한 libil2cpp.so SHA256: `5819bd6f94ae20d0c877a4eaaa0ceabc43f1b6ce5fdb56997f2fd10b600cdf68`. 원본 `config.arm64_v8a.apk`의 lib/arm64-v8a/libil2cpp.so와 일치한다.

메모리 주소는 SerializedFile 위치와 구분해야 한다. 코드 주소에 대해서만 ELF PT_LOAD로 `파일 오프셋 = RVA - 0x4000`을 재확인했다.
