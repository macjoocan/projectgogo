# Goods Puzzle: 3D Sorting Games 4.8.0 — 추출 데이터

입력: `Goods+Puzzle_+3D+Sorting+Games_4.8.0_APKPure.xapk`
(`sorting.games.goods.sort.triple.match3d.puzzle.stuff`)
엔진: **Unity 2022.3.62f2 · IL2CPP**, Addressables. metadata **비암호화**.
번들에 **typetree가 임베드**돼 있어 ScriptableObject 설정을 필드명 그대로 복원 가능 —
levelscope + UnityPy(fallback 버전 2022.3.62f2)로 오프라인 정적 추출.

## 산출물

| 경로 | 내용 |
|---|---|
| `GoodsPuzzle_levels.zip` / `GoodsPuzzle_levels_combined.json` | **레벨 258개**(JSON) — 레벨 레이아웃 |
| `config/` | **설정 ScriptableObject 33종** + 바이너리 테이블 + product ID |
| `GoodsPuzzle_sprites.zip` | 스프라이트 753 PNG |
| `GoodsPuzzle_assets.zip` | 오디오 48 WAV · 폰트 30 · Spine 6 · TextAsset 600여 · 머티리얼 |
| `GoodsPuzzle_meshes.zip` | **3D 메시 80개(OBJ)** — goods 3D 모델 등(총 ~90k 정점) |
| `GoodsPuzzle_hierarchy.zip` | **씬 5 · 프리팹 340** — GameObject 트리 + typetree 복원 컴포넌트 필드 |

## 레벨 (핵심 콘텐츠)

`table_assets_all` 번들의 TextAsset 258개(`1`~, `m1`~ 계열). 예: 레벨 1 =
`{Id, Width, Height, Shelves:[{ShelveType, Position:{x,y,z}}], Conveyors, Drops}`.
3D 정리 퍼즐의 선반 배치·컨베이어·드롭 구성이 그대로 들어 있음. 258/258 JSON 파싱 성공.

## 설정 (`config/`)

번들의 ScriptableObject를 typetree로 복원한 JSON:
- **`leveldifficultyconfig.json`** — 난이도 3티어(Difficulty 0/1/2)
- **`levelfeatureconfig.json`** — 레벨 피처 타입
- **`comboconfig.json`** — 콤보 16단계 타임(comboTimes)·별점
- **`productconfig-u_0`~`u_22`, `-b_1`, `-f_1`** — 상품(goods) 프리팹 설정(티어별)
- `shelfconfig`·`shelfwidgetconfig`·`textmaterialconfig`·`leaderboardassetconfig` 등
- **`product_ids.json`** — goods 카탈로그 ID 395종(animals_001_01 …)
- `product_data.json`·`level_data.json`·`unlock_data.json` — 원본 **커스텀 바이너리 테이블**
  (헤더 + 길이접두 레코드; 가변 타입태그 필드라 수치 완전 디코드는 미완, ID·구조는 확보).
  실사용 설정은 위 ScriptableObject JSON이 정본.

## 참고

- Addressables 카탈로그 123개 번들 중 **49개는 원격(CDN) 배포분**이라 APK에 없음 — 일부
  콘텐츠는 런타임 스트리밍. APK 내 로컬 74개 번들에서 위 산출물을 전부 확보.
- metadata 비암호화 + 번들 내장 typetree 덕에 IL2CPP 덤프 없이 설정을 필드명 그대로 복원.
