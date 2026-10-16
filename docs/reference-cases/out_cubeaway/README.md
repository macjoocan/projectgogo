# Cube Away - 3DPuzzle 1.6.1 추출 결과

- 패키지: `jp.co.goodroid.hyper.puzzle.arrows3dcubepuzzle` (goodroid)
- 입력: `~\Downloads\CubeAway+-+3DPuzzle_1.6.1_APKPure.xapk` (202MB, arm64 전용)
- 엔진: Unity 6000.0.62f1 · IL2CPP · global-metadata 비암호화 · 번들 `data.unity3d` 1개 · Addressables 없음
- 추출일: 2026-10-16

## 스테이지 데이터 — APK에는 없고, LDPlayer 실행 프로세스 메모리에서 복원

스테이지는 서버 마스터 데이터로 내려온다. `GameMasterModel`이 실행 시 `DownloadUrl`에서
마스터 테이블 49개(`StageNormal`, `StageNormalOrder`, `GimmickTutorial`, `Booster`, `StageTheme` 등)를
받는다. 디스크엔 평문 캐시가 없다. APK에 남은 레벨은 코드 내장 테스트 스테이지 5개뿐이다.

**2026-10-16 LDPlayer 복원:** 사용자가 LDPlayer(루팅)에서 게임을 실행해 둔 상태에서, 실행 중인
프로세스의 쓰기 가능 메모리(1.5GB)를 덤프해 il2cpp 객체를 복원했다. 외부 요청 없음·게임 조작 없음.
- `System.String` klass 포인터로 문자열 객체 26,637개 복원
- 화살표 문자열을 가리키는 포인터를 역추적해 `StageNormalDTO` klass 확정 → dump.cs 오프셋대로 필드 복원
- **StageNormal 502행 (Id 1~502 연속, 결손 0, 읽기 실패 0)**, StageId 1~2213
- Parameter 228행 (게임 파라미터 키/값)
- **2차(같은 날, 몇 스테이지 더 진행 후 재덤프): StageNormalOrder 2,998행 · Booster 5행 추가 확보.**
  1차에서 Order 를 놓친 건 검증 코드 버그(StageId 를 스테이지 Id 목록과 대조)였다. GimmickTutorial 은 없음.
  - 레벨 1~198 은 서로 다른 스테이지, **199부터 140개 스테이지가 주기 140으로 무한 반복**(2998까지)
  - 레벨이 쓰는 스테이지 200종(전부 복원본 502개 안). 나머지 302개는 현재 순서표에서 안 쓰임
  - CellType = 난이도 등급: Normal 1,955 · Hard 703 · SuperHard 340 (Medium 미사용) ↔ 클리어 코인 80/120/200
  - MaxHearts(레벨별 인게임 하트) 2~5, 쉬운 레벨은 0. MoveCount·TimeLimit 은 전부 0(미사용)
  - 초반 난이도 스파이크: 레벨 8 SuperHard(20³, 154화살표), 18 Hard(22³, 366), 28 SuperHard(24³, 454 — 최대)
- 원본 덤프는 기기 식별값이 섞여 있어 삭제. 결과물만 보관.

| 파일 | 내용 |
|---|---|
| `CubeAway_stages_summary.xlsx` | Stages(502행) · 50단위 구간 · 기믹 첫등장 · Parameter · **레벨순서(2998, 스테이지 통계 결합)** · 레벨구간(100) · 스테이지재사용 · Booster |
| `device_master/stage_normal_order.json` · `booster.json` | Order·Booster 원본 필드 |
| `CubeAway_stages_decoded.zip` | 스테이지별 구조화 JSON (arrows/gimmicks/voxels/cornerless_edges) |
| `device_master/stage_normal.json` | 원본 필드 그대로 (ArrowsJson 압축 문자열 포함) |
| `device_master/parameter.json` | Parameter 테이블 |

기믹 실사용(502개 중): changer 342 · reverse_changer 213 · pause 206. 첫 등장 pause 25, changer 27,
reverse_changer 336. Bomb·BendCw·MovingWall 등 나머지 enum 은 이 502개에서 쓰이지 않음.

ArrowsJson 실제 포맷(압축): `|방향,#색[,eid:ID][,branch][,double][,shared:x,y,z:면,parent:ID],x,y,z:면 x,y,z:면 …`
— 화살표는 `|` 구분, 셀은 공백 구분. `branch`/`shared`/`parent` 는 갈래 화살표(부모와 셀 공유).
GimmicksJson: `[{"cell":"x,y,z:면","type":"changer","exitDir":"up"}, …]`.
VoxelsJson: `[[x,y,z], …]` (빈 칸이 있는 비정육면체 형태). CornerlessEdgesJson: `[[x,y,z,면1,면2], …]`.

## 파일

| 파일 | 내용 |
|---|---|
| `code_data/test_stages/stage_NNN_arrows.json` | 코드 내장 테스트 스테이지 5개 (화살표 배열) |
| `code_data/master_schema.json` | 마스터 테이블 49개 목록 + DTO 필드 정의 |
| `code_data/game_constants.json` | 인게임 상수 (화살표 크기·속도·카메라·기믹 연출 등 27개 클래스) |
| `code_data/enums.json` | GimmickType·BoosterType·ArrowDirection·CubeFaceType·StageType 등 |
| `CubeAway_sprites.zip` | Sprite·Texture2D 1,924장 (실패 6 = 런타임 생성 폰트 텍스처) |
| `CubeAway_assets.zip` | 오디오 55 · 머티리얼 136 · 폰트 6 · 텍스트 5 |
| `CubeAway_meshes.zip` | 메시 33개 OBJ (셀 조각 `Cell_sh_1~30`, `cell_frags` 등) |
| `CubeAway_hierarchy.zip` | 씬 10 · 프리팹 187 · 노드 6,448 (MonoBehaviour 필드 98.8% 복원) |
| `CubeAway_il2cpp_dump.zip` | Il2CppDumper 결과 (dump.cs · DummyDll · script.json) |

## 스테이지 포맷 (StageNormalDTO)

`Id, StageId, TutorialId, SizeX/Y/Z, ArrowsJson, VoxelsJson, GimmicksJson, CornerlessEdgesJson,
BgColor, BgColorCenter, SolidColor, WireColor, CameraYaw/Pitch/Radius/TargetY, LevelTextColor`

`ArrowsJson` 원소는 두 형식이 섞여 있다.

- 면 좌표형: `{"face":"+z","u":2,"v":2,"dir":"right","color":"#111111","cells":[[2,2],[1,2]]}`
  — 여러 면을 넘어가는 화살표는 `segments: [{face, cells}, ...]`
- 복셀 좌표형: `{"cells":["3,0,0:+z","2,0,0:+z"],"dir":"right","color":"#111111"}` — `x,y,z:면`

진행 설정은 `StageNormalOrderDTO`: `MoveCount, TimeLimit, MaxHearts, ClearCoinCount,
ClearRewardId, IsRepeat, IsShowAdsOnClear/Exit/Reset, SwipeTutorial, PinchTutorial` 등.

기믹 종류(GimmickType): Pause · Changer · BounceWall · Cornerless · ReverseChanger · Bomb ·
BendCw · VertexRotation · MovingWall. 부스터(BoosterType): Hint · Eraser · Cane · ExtraMove · Scan.
