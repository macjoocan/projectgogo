# Royal Match 블록 흐름·드롭 속도/팩터 조사

## 결론

현재 `out_royalmatch`에 보관된 레벨 데이터만으로는 블록이 흐르는 실제 속도(초당 칸, world-unit/s)나 드롭 속도 팩터의 숫자값을 확인할 수 없습니다. 레벨 파일은 보드 배치와 이동 경로를 담고 있으며, 속도·보간·틱 간격은 별도의 게임 로직/런타임 설정에 있을 가능성이 높습니다.

따라서 `ConveyorBelts`의 경로 길이를 속도로 오인하면 안 됩니다. 경로가 5칸이라고 해서 5칸/s라는 뜻은 아닙니다.

## 확인된 블록 이동 관련 데이터

### ConveyorBelts

- 기믹 분석표 기준 사용 레벨: **705개**, 전체의 **4.9%**
- 최초 등장 레벨: **3801**
- 레벨 JSON 필드: `ConveyorBelts[].MagnetCells[]`
- 각 셀: `Cell.X`, `Cell.Y` 상대 좌표와 `DirectionTiledId` 방향/타일 ID
- 샘플 경로: 16셀(10009), 5·3·5셀(10018), 4셀 경로 다수(10028)

확인되지 않은 값:

- `speed`, `moveSpeed`, `flowSpeed`, `velocity`
- `factor`, `speedFactor`, `dropFactor`
- 초당 이동 칸 수, 이동 duration, tick interval
- conveyor별 속도 override

### 일반 블록 낙하/드롭

`Grid.Items`·`Grid.Cells`는 초기 보드 상태를 정의합니다. 매칭 후 빈칸을 채우는 순서, 중력 속도, 연쇄 대기시간, 새 블록 생성 확률/가중치는 레벨 파일에서 직접 확인되지 않았습니다. `Goals`, `Move`, `Grid`는 목표·초기 배치 데이터이지 런타임 낙하 물리 파라미터가 아닙니다.

### 관련 기믹

| 항목 | 사용 레벨 | 확인된 의미 | 속도값 |
|---|---:|---|---|
| ConveyorBelts | 705 | 경로 셀과 방향 타일 | 미확인 |
| Slots | 464 | 특수블록 슬롯 생성·보관 후보 | 미확인 |
| ShifterGrids | 266 | 지정 셀 이동 구조 후보 | 미확인 |
| PorcelainGroups | 364 | 타격 시 아이템을 뱉는 구조 후보 | 미확인 |

## 현재 확보된 ‘팩터’ 후보

레벨 데이터에서 확인되는 수치는 이동 속도 팩터가 아니라 구성값입니다.

- 경로 길이: `MagnetCells` 개수
- 경로 방향: `DirectionTiledId`
- 슬롯 수: `Slots` 배열과 `StartIndex`
- 기믹 진행 단계 후보: `Target`, `Order`, `CellCount`, `Width`, `Height`
- 초기 블록/기믹 ID: `Grid.Items`, `Grid.Cells`

관측 이동시간 `T`가 확보되면 `속도 = 경로 칸 수 / T`로 역산할 수 있지만, 현재 폴더에는 프레임별 좌표나 이동 로그가 없습니다.

## 판정

1. 보드 측 드롭 규칙: **부분 확인** — 초기 블록, 빈칸, 기믹 경로와 방향.
2. 컨베이어 실제 흐름 속도: **미확인** — 런타임 코드/숫자 설정 필요.
3. 일반 블록 낙하 속도: **미확인** — 중력·보간·settle 파라미터 필요.
4. 블록 생성 확률·가중치: **미확인** — RNG pool 또는 서버/클라이언트 설정 필요.
5. 레벨별 속도 배율: **현재 레벨 JSON에서 미확인**.

## 다음 확인 대상

정확한 숫자를 얻으려면 IL2CPP 메타데이터와 native library, 런타임 로그, AssetBundle의 gameplay 설정/ScriptableObject, 또는 관련 클래스 역어셈블 결과가 필요합니다. 우선 검색할 키워드는 `Conveyor`, `ConveyorBelt`, `Drop`, `Gravity`, `Fall`, `Refill`, `Spawn`, `Settle`, `MoveDuration`, `TileSpeed`, `AnimationDuration`, `RandomWeight`입니다.

**요약:** 현재 폴더에서 확정할 수 있는 것은 어떤 블록이 어디로 흐르는지까지이며, 얼마나 빠르게 흐르는지와 어떤 배율로 드롭되는지는 원본 실행 코드/런타임 설정 없이는 확정할 수 없습니다.

## APK·바이너리 전수 검색 추가 결과 (2026-10-07)

`out_royalmatch` 내부와 `C:\Users\NHN\Downloads`, `D:\99.기타`의 APK/XAPK 후보를 확인했다. 현재 `out_royalmatch`에는 RoyalMatch 전용 APK, `libil2cpp.so`, `global-metadata.dat`, managed DLL 또는 native library가 없다. 발견된 APK들은 Hades, Random Dice Wars, Stardew Valley, Wizard of Legend 등 다른 앱으로 확인되며 RoyalMatch 바이너리로 사용할 근거가 없다.

따라서 현재 확보된 `latest_data.unity3d`, `latest_datapack.unity3d`, assets/hierarchy/levels 산출물만으로는 속도 코드를 직접 역어셈블할 수 없다. 이 자료에서 추가로 확정된 것은 ConveyorBelts 경로·방향 타일뿐이며, 속도 숫자는 여전히 미확인이다.

속도·팩터를 확정하려면 RoyalMatch APK 또는 실행 중 추출된 다음 파일이 필요하다.

- `libil2cpp.so` 및 `global-metadata.dat`
- `assets/bin/Data/Managed/Metadata/global-metadata.dat`
- `assets/bin/Data/Managed/` DLL 또는 IL2CPP dump
- gameplay 관련 ScriptableObject/AssetBundle 원본
- 프레임별 블록 위치 또는 Unity Profiler/로그

현재는 타 앱 APK를 RoyalMatch로 오인해 분석하지 않았다.

## Royal Match 3.8.1.74 APK 추가 분석

대상 XAPK: `Royal+Match_38174_APKPure.xapk`

추출물:

- `com.dreamgames.royalmatch.apk` 64,102,460 bytes
- `UnityDataAssetPack.apk` 141,036,137 bytes
- `config.arm64_v8a.apk` 38,073,990 bytes
- `global-metadata.dat` 17,471,788 bytes, IL2CPP metadata version 31
- `libil2cpp.so` 89,601,608 bytes
- Il2CppDumper dump: `apk_38174/il2cpp_dump/dump.cs`

### 확정된 생성/드롭 데이터

`FTiledSet`에 다음 필드가 실제로 존재한다.

- `CanFall: bool`
- `CreateRatio: int`
- `Elements[].Id`
- `TargetColumns`, `TargetFills`, `TargetFillRatios`, `MaxItemCounts`

14,300개 레벨 전수 스캔 결과:

- `Sets`: 14,300/14,300 레벨에 존재
- `CanFall=1`: 14,852개 set 레코드
- `CreateRatio` 분포: 1이 14,818개로 대부분. 그 외 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 18, 20, 50, 51, 99, 100, 999, 1000, 2500, 4000, 9999, 20000, 99999, 999999 등도 존재

`CreateRatio`는 **블록 생성 선택에 직접 관련된 레벨 데이터 팩터 후보**다. 다만 코드 본문이 dump.cs에는 없으므로 이 값이 확률 가중치인지, 정규화 전 비율인지, 특정 세트 우선순위인지까지는 네이티브 판독이 필요하다. 숫자를 확률로 바로 해석하지 않는다.

### 컨베이어 런타임 코드

IL2CPP dump에서 실제 전용 클래스가 확인됐다.

- `Royal.Scenes.Game.Mechanics.Items.ConveyorBeltItem.ConveyorBeltHelper`
- `ManualUpdate()` RVA `0x30AAC2C`
- `MoveConveyorBelts()` RVA `0x30AB310`
- `UpdateCells()` RVA `0x30B0954`
- `UpdateGroup()` RVA `0x30B0A9C`
- `GetConveyorBeltData(int)` RVA `0x30?` 계열 / 모델 데이터 접근은 `GetConveyorBeltItems`, `GetShelfTotalSize`로 확인
- 컨베이어는 `animationQueues`, `Sequence`, `ConveyorBeltItemModel[]`을 사용하며, 레벨 JSON의 경로를 런타임에서 셀/아이템 그룹으로 갱신한다.

중요하게, `ConveyorBeltHelper` 자체에는 공개된 `speed` 숫자 필드가 없다. 흐름 속도는 `MoveConveyorBelts()`가 생성하는 animation `Sequence` 또는 별도 공통 애니메이션 설정에서 정해질 가능성이 높다.

### 낙하·생성 관련 런타임 타입/필드

메타데이터에서 다음 이름들이 확인됐다.

- `Falling`, `isFalling`, `CellHasTargetItemFallingThroughBlankCells`
- `ShouldWaitForFallingMatchItems`
- `GetSpeedMultiplier`, `speedMultiplier`, `SpeedMultiplierOnRefill`
- `GoSpeedMultiplierConst = 10`
- `ThrowSpeedMultiplier = 1`
- `MaxFallSpeed = 2`가 여러 낙하/연출 타입에 존재하나, 모든 일반 블록 낙하의 공통값이라고 단정하지 않음
- `progressSpeedMultiplier`, `speedAdjuster`, `AnimationSpeedMultiplier = 0.9` 등은 별도 UI/연출에도 사용되므로 드롭 속도와 분리 필요

### 다른 생성 팩터

`TableGameVaseSpawner`에는 다음 저장 필드가 있다.

- `throwSpeed`
- `spawnFalloffExponent`
- `vaseMaxSpeed`
- `vaseGravityScale`
- `mergeMoveDuration`
- `mergeSpawnDelay`
- `mergeSpawnScaleRatio`
- `mergeCooldownAfterSpawn`
- `mergeBounceSpeedMinScale`, `mergeBounceSpeedMaxScale`
- `mergeBounceMinVelocity`, `mergeBounceMaxVelocity`

이것은 일반 블록 리필이 아니라 Vase/Porcelain 계열 생성·투척 동작용이다.

### 아직 숫자 확정이 안 된 부분

Il2CppDumper는 클래스·필드·RVA를 복원했지만 함수 본문을 C#으로 복원하지 않는다. 따라서 다음 값은 다음 단계에서 `libil2cpp.so`를 RVA별 역어셈블해야 한다.

1. `ConveyorBeltHelper.MoveConveyorBelts()`의 Sequence duration/step interval
2. `CreateRatio`를 실제 RNG 가중치로 적용하는 함수
3. 일반 refill/fall 함수의 가속·최대속도·settle duration
4. `SpeedMultiplierOnRefill`의 기본값과 적용 조건
5. `GoSpeedMultiplierConst=10`, `MaxFallSpeed=2`가 적용되는 정확한 타입

이번 APK로 인해 이전의 “관련 native/metadata가 없다”는 판단은 해소됐다. 이제 실제 속도 숫자까지 역산·확정할 수 있는 원본이 확보됐다.

### APK에서 추가로 확정된 속도 상수

`Royal.Scenes.Game.Mechanics.Fall.FallComponent`가 일반 블록 낙하의 핵심 타입으로 확인됐다.

- `InitialSpeed = 4`
- `MinimumCrossSpeed = 4`
- `StraightAcceleration = 0.5`
- `CrossAcceleration = 0.5`
- `MaxSpeed = 20`
- `SpeedMultiplierOnRefill = 0.8`
- `FillItemFallOffset = 1.5`
- `StraightFallOffset = 1.25`
- `CrossFallOffset = 1.7`
- `ManualUpdate()` RVA `0x2D36AF4`
- `FallWithConstantSpeed()` RVA `0x2D36DC4`
- `FallToFillingCell()` RVA `0x2D36F94`
- `FallToNextCell()` RVA `0x2D37214`
- `FallStraight(...)` RVA `0x2D3773C`
- `FallCross(...)` RVA `0x2D37D90`

이제 일반 블록 드롭에 대해서는 단순 추정이 아니라 **초기속도 4, 직선/교차 가속도 0.5, 최대속도 20, 리필 배율 0.8**을 원본 코드 상수로 기록할 수 있다. 단위는 게임 내부 좌표/초로 보이며, 정확한 월드 단위 환산은 `CellView` 간격과 실제 `deltaTime` 판독이 추가로 필요하다.

`ConveyorBeltView`에는 컨베이어 칸 이동에 직접 쓰이는 `moveDuration` 필드가 확인됐다.

- `moveDuration` offset `0xF8`
- `Init(...)` RVA `0x338942C`
- 화살표 연출 `MoveArrow()` RVA `0x3383300`
- `ConveyorBeltHelper.MoveConveyorBelts()` RVA `0x30AB310`

`moveDuration`의 초기 대입값은 dump.cs에 저장값으로 나오지 않으므로 `ConveyorBeltView.Init`와 `MoveConveyorBelts` native 본문을 추가 역어셈블해야 한다. 따라서 컨베이어의 정확한 초당 칸 수는 아직 보류하지만, 이제 조사 대상 필드와 함수가 정확히 좁혀졌다.

## Factor catalog — APK 원작 근거 확장

### 공식성/근거 등급
공개 공식 문서가 아니라 사용자가 제공한 원본 APK의 IL2CPP 메타데이터·원본 네이티브 코드 구조와 레벨 데이터에서 확인한 값이다. 따라서 아래 표에서 “원작 APK”는 가장 강한 로컬 원본 근거이며, 공개 공식 문서와 동일한 의미로 사용하지 않는다.

### 일반 블록 낙하의 확정 상수 `[원작 APK IL2CPP]`
`Royal.Scenes.Game.Mechanics.Fall.FallComponent`에서 다음 값이 직접 확인된다.

| 항목 | 값 | 의미 |
|---|---:|---|
| InitialSpeed | 4 | 일반 낙하 시작 속도 후보 |
| StraightAcceleration | 0.5 | 수직/직선 낙하 가속 |
| CrossAcceleration | 0.5 | 교차·측면 낙하 가속 |
| MaxSpeed | 20 | 일반 낙하 속도 상한 |
| MinimumCrossSpeed | 4 | 교차 낙하 최소 속도 |
| SpeedMultiplierOnRefill | 0.8 | 리필로 생성된 블록 속도 배율 |
| FillItemFallOffset | 1.5 | 리필 낙하 오프셋 |
| StraightFallOffset | 1.25 | 직선 낙하 오프셋 |
| CrossFallOffset | 1.7 | 교차 낙하 오프셋 |
| FloatPrecision | 0.001 | 계산 허용 오차 |
| ScrollMaxSpeed | 28 | FallComponent의 스크롤 관련 상한으로 보이며 일반 블록 MaxSpeed=20과 분리 |

관련 메서드: `ManualUpdate` RVA `0x2D36AF4`, `FallWithConstantSpeed` `0x2D36DC4`, `FallToFillingCell` `0x2D36F94`, `FallToNextCell` `0x2D37214`, `FallStraight` `0x2D3773C`, `FallCross` `0x2D37D90`.

### 블록 생성/드롭 선택 계수 `[원본 레벨 데이터]`
`FTiledSet`의 `CanFall`과 `CreateRatio`가 세트별로 저장된다. `CanFall`은 낙하 가능 여부이고, `CreateRatio`는 생성 선택 가중치/비율 후보다. CreateRatio를 속도나 확률 퍼센트로 단정하면 안 된다.

- 14,300개 레벨에서 `Sets`가 모두 존재
- `CanFall=true` 세트 레코드 14,852개
- CreateRatio=1이 14,818건으로 대부분을 차지
- 그 외 값은 2~999,999까지 존재하며 특수 레벨/세트 값으로 보임
- 현재 데이터만으로는 실제 샘플링 식, 정규화 방식, 난수 시점은 확정하지 않음

### 컨베이어/흐르는 블록 `[원작 구조, 수치 미확정]`
`ConveyorBeltView`에 `moveDuration` 필드가 있고 `Init` RVA `0x338942C`, `MoveArrow` RVA `0x3383300`, `ArrowMovementFinished` RVA `0x338A010`이 확인된다. `ConveyorBeltHelper.MoveConveyorBelts` RVA `0x30AB310`, `ManualUpdate` RVA `0x30AAC2C`, `UpdateCells` RVA `0x30B0954`, `UpdateGroup` RVA `0x30B0A9C`가 흐름을 담당한다.

현재 확보한 dump만으로 `moveDuration`의 숫자 대입값이나 셀당 이동 시간은 확정하지 않았다. 따라서 컨베이어 속도는 임의값을 넣지 않고 `moveDuration` 원본 필드와 위 네이티브 메서드를 추가 역어셈블해야 한다.

### 별도 시스템으로 분리할 값
`TableGameVaseSpawner`에는 `throwSpeed`, `vaseMaxSpeed`, `vaseGravityScale`, `mergeMoveDuration`, `mergeSpawnDelay`, `mergeBounceSpeedMinScale/MaxScale` 등이 있으나, 이는 일반 블록 낙하가 아닌 유리병/병합 생성 시스템 값이다. 일반 드롭 속도 표에 섞지 않는다.

`FireworkRocketPilot`의 `GoSpeedMultiplierConst=10`, `MaxGoSpeedConst=50`, `StartOutSpeedConst=13` 및 UI/보상 파티클의 `MaxFallSpeed` 등은 블록 낙하 계수가 아니므로 제외했다.

전체 항목은 `ROYALMATCH_DROP_FACTOR_CATALOG.json`에 구조화했다. 값의 출처와 확정도를 함께 기록했으며, 수치 미확정 항목은 `runtime/asset field` 또는 `runtime algorithm`으로 표시했다.

## 단위·업데이트식 정정

현재 dump.cs의 상수명과 `StateChangedTime` 필드만으로 `GetAcceleratedSpeed()`의 실제 본문을 확정할 수 없다. 따라서 `StraightAcceleration=0.5`, `CrossAcceleration=0.5`의 단위를 `units/s²`로 단정하지 않는다. 현재 구현·검증 메모에서는 **원본 업데이트식 미확정**으로 표시한다.

확인된 동작 가설/관찰:

- 연속으로 셀을 이동할 때는 현재 속도가 유지될 가능성이 있음.
- 아래 블록과 간격을 맞추거나 이동이 막히면 시작 속도로 재설정될 가능성이 있음.
- 셀 간격 1 기준으로 InitialSpeed 4는 약 4셀/s, 리필 배율 0.8 적용 시 약 3.2셀/s로 해석 가능.
- 짧은 낙하에서는 0.5 계수의 체감 효과가 작을 수 있음.
- `FallSquash`의 Stretch/Squash/Bounce는 시각 연출이며 이동 속도 계산과 분리한다.

다음 확정 대상:

1. 원본 셀 간격 및 월드 단위
2. `GetAcceleratedSpeed()` 네이티브 본문
3. `SetFallState()` 또는 상태 전환 시 `CurrentSpeed` 초기화 여부
4. `FallToNextCell()`·`FallToFillingCell()`에서 연속 이동과 대기 이동의 차이

그 전까지는 `speed += 0.5f * deltaTime` 또는 프레임당 `speed += 0.5f` 어느 쪽도 원본 공식으로 적용하지 않는다.
