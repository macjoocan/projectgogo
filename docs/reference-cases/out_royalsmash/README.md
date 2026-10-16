# Royal Smash! - Physics Puzzle 1.13.359 — 추출 데이터

> **2026-09-28 Unity 이식 후속 판독:** `unity_bridge_20260928/README.md` — TNT 3종, 공유 BouncerSettings, Pinata 수치·부품 순서, Hammer 축(+Z 기준 및 계산식), 160종 노드별 메시 참조 확인. 15개 MonoBehaviour 전체 페이로드 경계와 원본 APK/ELF 해시 검증. 아래 오래된 “값 미확보” 설명 중 이번 대상은 이 후속 결과를 우선한다.


> **레벨 구조 분석 완료:** `level_structure_analysis/README.md` — 메인/루프 1,560개 전수 분석, 배치 150,648개, Entity Id 139종, Custom 필드 경로 52종. 필드·난이도 주기·기믹 첫 등장·명시 물리 설정과 검증 한계를 정리했다. 기존 혼합 ZIP을 분석 입력으로 쓰지 않았다.

> **2026-09-16 레벨 정정:** 원본 APK 재검사에서 메인 `RS 1` 700개 + 루프 `RS1 Loop` 860개 = 1,560개 레벨 JSON을 확인했다. 기존 `RoyalSmash_levels.zip` 860개는 두 컬렉션이 섞인 결과(메인 349 + 루프 511)다. 기존 ZIP에 없는 고유 내용 655종을 확인했다. 아래 기존 수치는 과거 산출물 설명이며 올바른 메인 레벨 순서로 쓰지 않는다. 근거: `LOCAL_LEVEL_FINDINGS.md`, `LOCAL_LEVEL_APK_AUDIT.json`. 아직 컬렉션별 재추출/기존 산출물 교체는 하지 않았다.

> CDN 후속 추출 완료: `cdn_extracted/README.md` — PNG 1,471개, 컴포넌트 JSON 4,684개(이름 있는 설정 40개 부분집합), 프리팹 90개. 최초 이미지 실패 267개는 원본 APK 아틀라스로 모두 복구했다. 최종 런타임 밸런스나 추가 700레벨 복구를 뜻하지 않는다.

> 2026-09-16 최신: 일반 CDN 다운로드가 허용되어 원격 번들 31개(77,351,176 bytes)를 인증 우회 없이 확보했고 내용 CRC까지 31개 모두 일치했다. `CDN_PUBLIC_RESULT.md`, `cdn_public/bundles/` 참조. 아래 “원격 약 700개 레벨”은 과거 미검증 추정이므로 성과로 인용하지 않는다. 새 번들의 밸런스/레벨 추출은 아직 하지 않았다. 기존 생성자 기본값 51개 복구 결과는 `STATIC_PHYSICS_RESULT.md` 참조.

입력: `Royal+Smash!+-+Physics+Puzzle_1.13.359_APKPure.xapk` (`com.cyphergames.royalsmash`)
엔진: **Unity 6000.0.62f1 · IL2CPP**, Addressables. metadata **비암호화**.
데이터는 `UnityDataAssetPack.apk`(Play Asset Delivery) 안에 **1MB `.splitN` 청크로 분할** —
재조립 후 levelscope로 오프라인 정적 추출.

## 산출물

| 경로 | 내용 |
|---|---|
| `RoyalSmash_levels.zip` / `_combined.json` | **레벨 860개(JSON)** — 물리 퍼즐 레이아웃·밸런스 |
| `RoyalSmash_level_balance.csv` | **레벨별 밸런스 표** — MoveCount·난이도·엔티티 수 |
| `RoyalSmash_entity_usage.json` | 물리 오브젝트 139종 사용 빈도 |
| `RoyalSmash_meshes.zip` | **3D 메시 658개(OBJ)** — 물리 오브젝트 모델·파괴 조각 |
| `RoyalSmash_sprites.zip` | 스프라이트 793 PNG |
| `RoyalSmash_assets.zip` | 설정/로컬 MonoBehaviour JSON 836 · 오디오 11 WAV · 폰트 6 · Spine |
| `localization/` | **UI 텍스트 38개 언어** (각 ~420개 키) |
| `config/` | 설정 번들 6종 (아래) |
| `RoyalSmash_hierarchy.zip` | 씬 1 · 프리팹 83 (GameObject 트리·컴포넌트 타입) |
| `RoyalSmash_scripts_decompiled.zip` | AssetRipper 스텁 135개(참고용) |
| `il2cpp_dump/dump.cs` | **Il2CppDumper 전체 클래스·필드 구조 14,219개**(진짜 필드명·타입·오프셋) |
| `il2cpp_dump/gameplay_physics_fields.json` | **게임플레이 물리 클래스 81개**의 진짜 필드명(Ball·Bouncer·Obstacle 등) |

## 레벨 밸런스 (핵심)

레벨은 `UnityDataAssetPack.apk` 의 `assets/bin/Data/<hash>` SerializedFile 마다 **번호 이름
JSON TextAsset 1개**로 들어 있다(총 860개 로컬 추출). 각 레벨 구조:

```
{ Version, MoveCount, AndroidMoveCount, Difficulty, PhysicsQuality,
  StabilizeOnSpawn, BackgroundIndex,
  Entities: [ { Id: "IceSquare_1", Position:{x,y,z}, Rotation:{x,y,z,w}, Custom:{...} }, ... ] }
```

- **밸런스 수치**: `MoveCount`(15~36, 평균 21.1)·`AndroidMoveCount`(플랫폼별 무브)·`Difficulty`
  (0 쉬움 605 / 1 보통 170 / 2 어려움 85)·`PhysicsQuality`·엔티티 배치.
- **물리 오브젝트 139종**: IceSquare·JamJar(색상)·CanSquare·StoneSquare·BoxSquare 등 —
  `RoyalSmash_entity_usage.json` 에 사용 빈도. 레벨별 요약은 `RoyalSmash_level_balance.csv`.
- 카탈로그 83개 중 원격 31개는 아트/UI 등의 번들이며, 이들에서 추가 레벨 JSON은 발견되지 않았다.
  원본 APK의 실제 레벨은 위 정정대로 두 컬렉션 1,560개다. 과거 “원격 약 700개” 추정은 근거가 없다.

## 설정·텍스트

- **`localization/<lang>.json`** — 38개 언어 UI 텍스트 (Unity Localization StringTable).
  예: `"Sticky Bomb"`, `"Level {n}"`, `"More Lives"`, `"Out of Lives"`.
- **`config/`** (번들 임베드 typetree로 필드명 복원):
  - `gameplaybackgrounds_local` — 배경 스케일/물리 연출
  - `sequences` — UI 팝업 시퀀스(WellDone·DailyTask·ProgressOffer 등)
  - `shared_common_local` — 햅틱·UI 애니메이션 이징
  - `liveops_offer_welcome`·`liveops_roadrunner` — 라이브옵스 이벤트 UI(텍스트 애니메이션)
  - `loadingscreens_local`

## 추출 방법 (요약)

- `UnityDataAssetPack.apk` 안 `level1`·`sharedassets1/2.assets` 는 **`.split0`,`.split1`… 로
  1MB씩 분할**(Play Asset Delivery). 순번대로 concat → 원본 SerializedFile 복원.
- 재조립본 + 번들 + metadata + libil2cpp 를 한 폴더로 묶어 levelscope 에 입력(폴더 입력).
  discover 가 Unity 6000.0.62f1 감지, 번들은 **임베드 typetree** 로 설정 MonoBehaviour 를
  필드명 그대로 복원.

## 물리 밸런스 필드 (Il2CppDumper — 진짜 구조)

metadata 비암호화라 Il2CppDumper 로 전체 클래스·필드 구조를 복원(`dump.cs`, 14,219 클래스).
게임플레이 물리 클래스의 **진짜 필드명**(`gameplay_physics_fields.json`):
- `BouncerSettings`: `m_minBallSpeed`, `m_ballSpeedMultiplier`, `m_ballImpactSpeedMultiplier`,
  `m_maxSpeedMultiplier` — 공(포탄) 속도.
- `ObstacleCommon`: `BreakForce`, `BreakRadius`, `BreakUpwards`, `BreakMaxSpeed`, `BreakSpin` — 파괴.
- `Ball`: `m_firstContactExplosionForce/Radius/Upwards`, `m_minSpeedToDecay`.
- `Obstacle`: `m_additiveMass`, `m_explodeMinSpeed`, `m_explodeNonBallSpeedMultiplier`,
  `m_levelMassOverride`. `BarrageBombSettings`: `BlastSpeed/Radius`. `MagnetSettings`:
  `m_attractionForce`, `m_repulsionForce`. `Pinata`·`Tnt`·`Platform`·`Blocker`·`Magnet` 등.

**실제 VALUE 가 확보된 것** (번들 임베드 typetree, `config/gameplaybackgrounds_local.json`):
`m_entryLinearDrag: 8.0` · `m_mainLinearDrag: 4.0` · `m_contactRamp: 0.15` · `m_entrySlam: 0.5` ·
`m_entrySlamHorizontal: 0.25` · `m_angularDrag: 3.0` · `m_obstacleAngularDrag: 8.0` ·
`m_breakOnImpact: 0` · `m_killDepth: 14.0` · `m_volumeDepth: 16.0` · `m_entryDepth: 0.1`.

**VALUE 미확보(필드명은 확보)**: `Ball`/`BouncerSettings`/`ObstacleCommon` 등의 인스턴스 값
(`m_minBallSpeed`, `BreakForce` 등의 실제 숫자)은 미확보 — 이 컴포넌트들의 MonoBehaviour 가
IL2CPP `m_Script` 해시 불일치로 해석 안 됨(DummyDll 로도 안 붙음). 값은 프리팹/씬 인스턴스나
생성자 코드에 있어 이 경로로는 못 뽑는다. **필드명은 진짜, 숫자는 "미확인"으로 두고 지어내지 말 것.**
`winRatio` 는 **필드 자체가 없음**(dump.cs 에 부재) — 지어낸 지표로 확정.

## 한계 (미확보)

- **레벨 레이아웃·밸런스는 확보**(위 참조 — JSON 데이터 파일에 있었음). 다만 **씬(level0/1/2)의
  MonoBehaviour 컴포넌트 필드 값**(게임플레이 로직 설정)은 복원 못 함 — 씬 스크립트가 별도
  `_monoscripts.bundle` 의 번들 경계 참조라 외부 링크가 끊긴다(Unity 6 IL2CPP). 씬 구조
  (GameObject·Transform·컴포넌트 타입)는 `RoyalSmash_hierarchy.zip` 에 있으나 필드는 `null`.
  레벨 데이터는 씬이 아니라 JSON 데이터파일에 있으므로 이 한계와 무관하게 확보됨.
- 별도 `RemoteLevels` 갱신 코드가 있지만 현재 서버 manifest와 배포 레벨 수는 확인하지 않았다.
  Addressables 원격 번들 31개를 레벨 배포분으로 간주하지 않는다.
- 씬 컴포넌트 필드 복원은 **AssetRipper 2.0.0 까지 시도했으나 실패**. AssetRipper 는 번들
  MonoBehaviour(임베드 typetree)는 필드 복원 + C# 스크립트 135개 디컴파일까지 했으나,
  **씬(level1) MonoBehaviour 1,724개는 전부 미해결**(`guid: …deadbeef…`) — UnityPy·levelscope
  hierarchy·ScriptRegistry·통합 env·직접 PPtr 에 이어 5번째로도 같은 벽. 씬 m_Script 가 GUID
  기반 외부참조인데 어느 도구도 그 스크립트를 IL2CPP 클래스에 연결 못 함. 이 빌드의 구조적
  한계로 확정. **레벨 밸런스·메시·설정·텍스트는 씬과 무관하게 이미 확보됨.**
