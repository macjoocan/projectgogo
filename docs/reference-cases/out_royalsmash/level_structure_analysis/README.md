# Royal Smash 레벨 구조 분석

2026-09-16 · APK 1.13.359 · 원본 로컬 데이터 전수 분석. 게임 실행 및 게임사 서버 접속 없음.

## 핵심 결론

레벨은 **이동/발사 횟수 관련 설정과 난이도 등 공통 설정 + 3D 오브젝트 배치 목록 + 오브젝트별 추가 설정**으로 구성된다. 격자 셀 배열 방식이 아니라 각각의 오브젝트가 위치와 회전을 갖는 구조다. 원본에서 확인한 1,560개 레코드를 컬렉션별로 분석했고, 객체 배치 150,648개와 서로 다른 Entity Id 139종을 확인했다. 139종에는 색·형태·크기 등의 이름 변형도 포함되므로 독립 기믹 139개라는 뜻은 아니다.

기존 `RoyalSmash_levels.zip`은 메인/루프가 섞여 있어 분석 입력으로 쓰지 않았다. 이전 원본 감사에서 확보한 파일 경로·object ID·컬렉션 매핑을 이용해 APK에서 다시 읽었고, **1,560개 전부 이전 감사의 내용 SHA-256과 일치**했다.

## 1. 두 컬렉션의 차이

| 지표 | 메인 RS 1 | 마스터/루프 RS1 Loop |
|---|---:|---:|
| 레벨 수 | 700 | 860 |
| 번호 | 1–700 | 1–860 |
| MoveCount 범위 | 17–33 | 15–36 |
| MoveCount 평균 | 22.50 | 20.31 |
| 배치 오브젝트 총수 | 65,272 | 85,376 |
| 레벨당 오브젝트 평균 | 93.25 | 99.27 |
| 레벨당 오브젝트 범위 | 15–268 | 26–321 |
| 사용된 Entity Id 수 | 139 | 138 |
| Normal / Hard / SuperHard | 495 / 137 / 68 | 602 / 172 / 86 |
| AndroidMoveCount 양수 레벨 | 285 | 189 |

두 컬렉션 간 완전히 같은 JSON 내용은 82종이다. 메인은 고유 내용 700종, 루프는 859종이며 합집합은 1,477종이다. 루프가 단순히 메인 700개를 이름만 바꾼 데이터는 아니다.

루프 쪽은 평균적으로 배치 수가 많고 MoveCount가 적다. 이는 **정적 수치의 차이**이며 실제로 더 어렵거나 승률이 낮다는 결론은 아니다. 충돌체·기믹·조작·런타임 설정에 따라 결과가 달라진다.

## 2. 레벨 공통 필드

아래 8개 필드는 1,560개 레코드 모두에 있으며 null·누락은 없다.

| 필드 | 타입 | 확인된 의미 및 주의점 |
|---|---|---|
| `Version` | 정수 | 레벨 데이터 버전. 전부 1. 앱 버전과 다르다. |
| `MoveCount` | 정수 | 레벨의 기본 횟수 설정. 실제 행동 차감·최종 횟수 적용은 런타임 로직 검증 별도. |
| `AndroidMoveCount` | 정수 | Android용 별도 횟수 필드. 474개 레벨에 양수, 나머지 1,086개는 0. 0을 플레이 가능 횟수 0으로 해석하면 안 된다. 0의 fallback 규칙은 이번 분석에서 확정하지 않음. |
| `Difficulty` | 정수 enum | 원본 코드로 확인: 0=Normal, 1=Hard, 2=SuperHard. 승률 값이 아니다. |
| `PhysicsQuality` | 정수 enum | 원본 코드로 확인: 0=High, 1=Medium. 6개만 Medium. `LevelPhysicsQualityOverride`는 별개 enum이므로 값 혼동 금지. |
| `BackgroundIndex` | 정수 | 배경 선택 관련 값. 1,559개가 -1, 메인 460번만 1. -1의 구체적 자동 선택 규칙 미확인. |
| `StabilizeOnSpawn` | bool | 스폰 시 안정화 관련 플래그. 원본 값은 모두 false. 실제 동작 미검증. |
| `Entities` | 배열 | 배치할 오브젝트 목록. 비어 있는 레벨 없음. |

레벨 번호와 컬렉션은 이 JSON 본문에 별도 필드로 들어 있지 않고 `levels/rs 1/00001` 같은 리소스 경로에서 얻는다. **레벨 키는 `(collection, number)`**다.

## 3. 오브젝트 한 개의 구조

```text
레벨: collection + number
 ├─ 공통 필드: Version, MoveCount, AndroidMoveCount, Difficulty 등
 └─ Entities[]
     ├─ Id              오브젝트 종류를 조회하는 문자열
     ├─ Position        {x, y, z}
     ├─ Rotation        {x, y, z, w} — Quaternion
     ├─ Scale           선택 필드, {x, y, z}
     └─ Custom          종류별 추가 설정 객체
```

`Id`, `Position`, `Rotation`, `Custom`은 150,648개 오브젝트 모두 존재하고 null이 없다. `Scale`은 73개에만 존재한다. 원본 `EntityData`도 `Nullable<Vector3> Scale`로 선언하므로 누락을 오류로 보거나 일괄 값으로 덮어쓰면 안 된다.

`Id`는 인스턴스 고유 ID가 아니다. 같은 레벨에 `CanCylinder_1` 같은 이름이 여러 번 나온다. 분석용 인스턴스 키는 `(collection, level number, entity array index)`로 잡아야 한다. 원본 `EntityDatabase.Get(string id)` / `TryGet(...)`가 종류 조회 구조를 뒷받침한다. 이번 작업에서 모든 Id를 실제 프리팹·충돌체에 연결한 것은 아니다.

`Rotation`은 오일러 각도 3개가 아닌 Quaternion 4성분이다. 전체 노름 검사에서 1과의 차이가 0.001을 넘는 것은 없었다. 위치는 3D 좌표지만 월드/로컬 기준, 단위, 스폰 후 정렬 규칙은 JSON만으로 확정하지 않는다. 위치 최솟값/최댓값은 오브젝트 중심의 범위이지 실제 메시/충돌체 크기를 포함한 레벨 경계가 아니다.

### 실제 메인 1번 예시

공통 설정: MoveCount 30, AndroidMoveCount 0, Normal, PhysicsQuality High. 오브젝트는 29개다. 아래는 그중 첫 번째 하나만 인용한 것이다.

```json
{
  "Id": "Table_Rect",
  "Position": {"x": 0, "y": 2, "z": -2},
  "Rotation": {"x": 0, "y": 0, "z": 0, "w": 1},
  "Custom": {"w": 5, "d": 2}
}
```

## 4. Custom에 들어 있는 기믹·물리 설정

중첩 객체를 점 경로로 펼치면 **52종 필드 경로**가 있다. 이는 모든 오브젝트에 52개 필드가 들어 있다는 뜻이 아니다. 종류와 레벨에 따라 선택적으로 저장된다. 아래 해석은 이름과 사용 오브젝트에 따른 설명이며, 수식·단위·보간 규칙까지 역구현한 것은 아니다.

| 묶음 | 대표 필드 | 실제 등장 대상 및 관찰 |
|---|---|---|
| 배치 방향 변형 | `randomYaw` | 148,096개에서 존재. true 81,783 / false 66,313. 랜덤 범위·시드는 미확인. |
| 받침대 크기 | `w`, `d` | Table_Rect / Table_Round, 각각 2,298개에서 존재. |
| 받침대 회전 | `rotate`, `rotAxis`, `rotSpeed`, `startup` | Table 계열. rotAxis는 관찰값상 ±Y 방향. |
| 받침대 이동 | `moveX/Y/Z.min/max/speed/dir` | Table 계열. 축별 이동 범위·속도 관련 구조. |
| 방해물 동작 | `bladeScale`, `rotSpeed`, `travel`, `travelDur`, `easeTime` | Blocker_L / M / S. |
| 해머 동작 | `cycleDur`, `rodLength`, `rodDiameter`, `hammer1Scale`, `hammer2Scale`, `curve`, `startPhase` | Hammer. 주기·형상·샘플 배열을 보존해야 한다. |
| 물리 개별 설정 | `physicsMass`, `physicsDynamicFriction`, `physicsStaticFriction`, `physicsBounciness`, damping 등 | 2,491개 오브젝트에서 관련 묶음이 명시됨. 전체 오브젝트의 공통 기본값이 아니다. |
| 피냐타 | `pinataScale`, `pinataExplosion*`, `pinataKillBlast*` | Pinata 88개에서 해당 값 확인. |

확인된 물리 입력값 예:

- `physicsMass`: 명시된 2,491개에서 0.75–12.
- `physicsDynamicFriction`, `physicsStaticFriction`: 약 0.05–0.60.
- `physicsBounciness`: 0 또는 0.5.
- Pinata 88개 모두 `pinataExplosionForce=10`, `Radius=4`, `Upwards=1`; `pinataKillBlastForce=25`, `Radius=10`, `Upwards=100`.

이 값은 추정이 아니라 JSON에 있는 값이다. 하지만 프리팹·컴포넌트 기본값과의 적용 순서, 후속 배율, 서버 덮어쓰기까지 확인한 최종 물리 결과는 아니다. 누락된 `Custom` 필드를 0으로 채우면 동작을 바꿀 수 있다.

## 5. 난이도 편성과 기믹 등장 순서

`Difficulty` 편성은 전체 1,560개에서 아래 규칙과 정확히 일치했다.

- 메인 1–19: 모두 Normal. 메인 20: Hard.
- 메인 21–700: 끝자리 4·7은 Hard, 끝자리 0은 SuperHard, 나머지는 Normal.
- 루프 1–860: 처음부터 끝자리 4·7은 Hard, 0은 SuperHard, 나머지는 Normal.

즉 대부분 구간은 **10레벨마다 Normal 7 / Hard 2 / SuperHard 1** 편성이다. 난이도 라벨의 주기이지, 각 레벨의 실제 클리어 난이도가 주기적으로 동일하다는 뜻은 아니다.

메인 컬렉션에서 해당 Id가 처음 등장하는 번호:

| Entity Id 예 | 메인 첫 등장 | 루프 첫 등장 |
|---|---:|---:|
| CanCylinder_1 | 1 | 11 |
| JamJarYellow_1 | 11 | 1 |
| StoneSquare_1 | 21 | 6 |
| IceSquare_1 | 41 | 1 |
| TntSquare_1 | 61 | 5 |
| BouncerCylinder_5 | 141 | 41 |
| Hammer | 161 | 42 |
| Pinata | 201 | 5 |

메인에서는 종류가 단계적으로 추가되는 모습을 볼 수 있다. 루프는 초반부터 후반 계열 Id를 함께 사용한다. 위 표는 **원본 데이터에서 해당 Id가 처음 보이는 시점**이며 튜토리얼 연출의 실행 시점을 검증한 것은 아니다. `PiggyBox_1`은 이번 데이터에서 메인에만 등장한다.

50레벨 묶음 집계는 `structure_profile.json`의 `bands_50`에 있다. 메인 1–50의 평균 MoveCount는 24.08 / 평균 배치 수 82.56, 메인 651–700은 19.84 / 108.30이다. 중간 구간은 오르내림이 있어 일직선 난이도 상승으로 단순화하면 안 된다.

## 6. 데이터 품질과 구현 시 주의점

- 원본 감사와 1,560/1,560 내용 해시 일치. 컬렉션+번호 중복 0. 공통 8필드의 누락/null 0.
- 오브젝트 필수 4필드 누락/null 0, 위치값 숫자/유한성 확인, Quaternion 노름 허용범위 초과 0.
- `Scale` 및 Custom 선택 필드의 높은 누락률은 종류별 선택 설정과 구분해야 한다. 일괄 결측값 보정 금지.
- 일부 숫자는 `1`/`1.0`처럼 정수·실수 표현이 섞인다. 숫자 타입 차이만으로 다른 기믹으로 분류하지 않는다.
- `moveY.dir=2`가 2개 있다. -1/0/1만 허용한다고 가정해 삭제하거나 고치면 안 된다. 원본 동작 해석이 추가로 필요하다.
- 공통 JSON에 별도 `Goals`, `WinRatio`, `ClearCondition` 필드는 없다. 오브젝트 수를 그대로 목표 개수·승률로 부르지 않는다. 승리 판정과 파괴 가능 여부는 게임 로직·프리팹 확인이 필요하다.
- 레벨 읽기, 구조 분석, 실행 재현은 다른 단계다. 이번에는 구조와 값의 존재를 검증했으며 플레이 테스트를 하지 않았다.

## 7. 산출물 / 다음 분석

- `structure_profile.json`: 필드별 타입·누락·분포, 컬렉션 비교, 좌표 분포, 50레벨 묶음, 중복 내용 그룹.
- `level_index.json`: 컬렉션을 보존한 1,560개 레벨 요약과 원본 경로. 완전한 레벨 원본 JSON 대신 분석용 색인이다.
- `entity_catalog.json`: Id 139종별 등장 빈도, 첫 등장 레벨, 사용 Custom 필드 및 예시값.
- `structure_examples.json`: Id별 원본 오브젝트 표본과 양 컬렉션 1–3번 구조 표본.
- `schema_code_evidence.txt`: LevelData / EntityData / Difficulty / PhysicsQuality / EntityDatabase 원본 클래스 선언.
- 재현: 상위 폴더 `analyze_level_structure.py`. 기존 원본·ZIP·게임 프로젝트 변경 없음.

후속으로 유용한 분석은 ① 컬렉션별 완전 재추출, ② Entity Id와 실제 프리팹/충돌체 연결, ③ AndroidMoveCount fallback 및 승리 판정 코드 확인, ④ 3D 배치 미리보기, ⑤ 실행 환경이 준비된 뒤 물리 재현 테스트다. 현재 정적 분석만으로 승률·완전한 게임 재현을 보장하지 않는다.
