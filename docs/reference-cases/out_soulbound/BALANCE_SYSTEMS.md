# Soulbound 데이터·밸런스 시스템 조사

2026-09-30 로컬 설치본 정적 조사. **밸런스를 조정하는 구조와 로딩 경로는 확인했지만, 현행 몬스터 HP·드롭 확률·성장 계수 표는 확보하지 못했다.** 아래는 코드 참조에 근거한 설명이며 임의의 수치를 원작값으로 채우지 않았다.

## 설정을 어디서 가져오는가

각 Library는 캐시 로드와 클라이언트 요청 경로를 가진다. STRG에는 `libraries/{0}.json`도 존재한다. 따라서 전부 EXE 안의 고정 상수라고 보거나, 반대로 모든 로컬 계산이 없다고 보는 것은 모두 부정확하다.

| 영역 | 로딩 함수 RVA | 참조 요청 |
|---|---|---|
| 능력치·에너지·버프 | StatsLibrary.__load `0x593b5d0` | stats.list_energies, list_buffs |
| 스킬 | SkillsLibrary.__load `0x585d830` | skills.list_skills |
| 아이템 정의 | ItemsLibrary.__load `0x4f33480` | assets.get_item_intrinsics, get_item_types, get_icons_atlas |
| 보상 테이블 | LootTableLibrary.__load `0x4ff0f00` | crafting.get_loot_tables |
| 던전 | DungeonsLibrary.__load `0x667660` | tuning.list_dungeons, list_dungeon_objectives, list_storm_mods, list_party_size_modifiers |
| 조정 변수 | Tuning.refresh `0x59a7db0` | get_client_variables, get_server_variables_summary |

`is_client/is_server/is_single_player` 분기는 존재하지만 이것만으로 오프라인에서 전체 게임이 작동하거나 서버 정본이 전부 포함됐다고 판정하지 않는다.

## 시스템별 데이터 축

아래 필드는 수신 데이터 변환 함수의 참조다. 완전한 자료형 명세나 운영 payload의 실제 값은 아니다. 주소는 Soulbound.exe RVA다.

| 시스템 | 확인한 주요 필드 | RVA | 밸런스 의미 |
|---|---|---|---|
| Stat | stat, value | `0x354f410` | 이름별 능력치 값 |
| Energy | energyId, displayName, spriteId | `0x35481a0` | 에너지 종류 정의; 실시간 상태는 별도 |
| Skill | equationId, enabled, maxLevel, category, hidden | `0x34c8320` | 성장식 참조·성장 상한 |
| Buff | duration, stats, tier, stackCount, clearOnDeath, lootTableId | `0x3537000` | 지속시간·중첩·사망 후 유지 |
| ItemIntrinsic | rarity, stackLimit, containerSize, tags, isTradable, isSingleton, isUnlosable, properties | `0x2e46e00` | 공통 아이템 정의 |
| Item | quantity, state, equipmentSlotName, contained, properties, propertyChecksum | `0x327cbc0` | 소유 아이템의 개별 상태 |
| Recipe | consumes, produces, craftingTime, usageCount, skillRequirements, stationExperience, chanceOutput | `0x2d0a5d0` | 재화 소모·생산·시간·성장 조건 |
| LootTable | requirements, primaryRewards, secondaryRewards, enabled | `0x2ee4970` | 보상 테이블 구성 |
| LootTableRewardRoll | chance, rolls, reward, requirements | `0x2eec1e0` | 확률·시도 수·조건 |
| Reward | item, skill, energy, allegiance, lootTable, buff, flag | `0x32fd300` | 보상 결과의 여러 종류 |
| TuningVariableSummary | name, value, variants | `0x36ec710` | 변수 및 변형값 |
| TuningVariableVariant | variantId, value | `0x36eef20` | 선택 가능한 설정 변형 |

`chance`가 있다고 확률 단위를 0~1 또는 0~100으로 단정하지 않았다. `RarityConfig`(`0x528a890`)의 색·표시 이름은 드롭 확률이 아니다. 변형 설정의 존재만으로 실제 A/B 실험이 진행 중이라고 주장하지 않는다.

## 던전 난이도는 여러 축으로 구성

Dungeon(`0x3576c90`)에는 roomOrder, objectives, mobCaps, scalingFunctions, stormMods, partyModifiers, resources, spawnerConfig, appropriateGear, relics가 있다.

DungeonConfig(`0x3585810`)에는 minPlayers/maxPlayers, energyCost, gearLoss, bagWipePercentage, abilityLevelBrackets, eventCountdown, randomizedAbilities, isBossRaid, relicPoolMode가 있다. 즉 적의 HP만 조정하는 것이 아니라 입장 비용·손실·인원·장비·능력 선택까지 설정 계층이 나뉜다.

스폰 난이도 modifier(`0x359b7c0`)는 hp, moveSpeed, damage를 참조한다. 웨이브는 시간 제한·처치 완료 조건·총 개체 수를, 개별 스폰은 최소/최대 수량·주기·반복 수·첫 지연을 가진다. 맵 조합과 연결 관계는 [맵 제작 조사](MAP_PRODUCTION.md)에 정리했다.

## 경험치·레벨 계산

`DCPartyLevelSystem`은 던전 파티 진행용 경로다. 이를 영구 스킬 레벨과 같은 값으로 섞으면 안 된다.

- load `0x539b7b0`: 던전 scaling 및 tutorial starting_level 참조.
- add_xp `0x539de50`: 다음 레벨 필요 경험치 검사와 increase_level 경로.
- increase_level `0x539ed70`: level, level_rewards_remaining, total_xp_at_level_start, xp 갱신 관련 참조.
- set_next_level_xp `0x539fba0`: 파티 레벨·인원, override_level_brackets, room_scaling_brackets, party_size_modifiers, objective_and_level_up_brackets, round 참조. polynomial_sigmoid와 sigmoid 호출.

`Tuning.get_modifier`(`0x59aca60`)도 scaling_type, 방 수 구간, 파티 인원 modifier와 a~f/l/k/x0를 참조한다. 성장 곡선을 데이터로 교체하는 구조의 근거다. **계수 배열과 실제 결과값을 확보하지 못했으므로 레벨별 필요 경험치 표는 계산하지 않았다.**

보존한 수학 함수: sigmoid `0x5671800`, polynomial `0x5671be0`, polynomial_sigmoid `0x56723f0`. 특히 polynomial은 이름만 보고 보통의 5차 다항식으로 대체하면 안 된다. 추가 비선형 연산을 포함하는 경로가 있어 전체 식의 확정은 보류했다.

## 상태 동기화

`EntityComponentStats.update`(`0x2a5ae50`)는 revision_id, payload, new_stats, new_energies, health_snapshot_received를 참조한다. change_energy(`0x2a539b0`)는 value/capacity와 클라이언트·서버·싱글플레이 분기를 가진다. **정의 테이블과 실시간 상태가 분리되며, 상태에는 갱신 버전 개념이 있다.** 다만 서버의 권한 판정·검증 구현까지 복원한 것은 아니다.

## 조사 범위와 남은 수치

| 항목 | 현재 상태 |
|---|---|
| 로컬 이미지·오디오·오브젝트·룸 구조 | 추출 및 참조 검증 |
| 밸런스 정의의 필드와 로딩 경로 | 정적 코드 참조 확보 |
| 조정 변수 변형·파티 성장·웨이브 구성 경로 | 관련 함수 역어셈블 확보, 일부 판독 |
| 현행 HP·공격력·이속·스킬 성장 계수 | 미확보 |
| 드롭 확률·보상 수량·제작 비용·입장 비용 실값 | 미확보 |
| 서버 운영 던전 구성·월드 청크 | 미확보 |
| 실제 전투 승률·경제 수지 시뮬레이션 | 실행하지 않음; 입력 수치가 필요 |

STRG 76,806개에서 문자열 전체가 유효한 JSON object/array인 후보를 검사했지만 없었다. 이는 네이티브 코드로 만든 자료구조까지 없다는 뜻은 아니다. 표준 Local/Roaming의 Soulbound 캐시 후보도 찾지 못했다. 임의의 밸런스 값을 채워 시뮬레이션한 결과를 원작으로 제시하지 않는다.

공식 설명은 던전의 웨이브·층별 진행·추출과 영구 성장이라는 큰 구분을 뒷받침한다. [공식 던전 소개](https://soulbound.game/content/dungeon-system/). 2025-05-30 패치에는 파티 인원에 따른 보스/일반 몬스터 스케일 조정이 따로 언급되지만, 과거 수치를 이번 설치본의 현행값으로 사용하지 않았다. [당시 패치노트](https://soulbound.game/release-notes/update-5-17-5-dungeon-update/).

근거: [스키마 필드 원장](schema_field_index.json), [함수 참조 원장](function_reference_index.json), [구조 탐색기](Soulbound_systems.html). 다음 정량 분석에는 정상 플레이로 수신·저장한 해당 정의 payload와 버전 정보가 필요하다.
