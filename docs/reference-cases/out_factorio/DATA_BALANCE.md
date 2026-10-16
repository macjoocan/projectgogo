# Factorio 데이터와 밸런스 전반

기준: **설치된 2.0.77 기본 게임(core + base), 추가 모드 없음**. Space Age·quality·elevated-rails 패키지는 설치되어 있지 않다. 기본 파일에 확장팩 호환 필드가 등장해도 확장팩 전체 데이터가 있다는 뜻은 아니다.

## 데이터는 어떻게 만들어지는가

```text
core / base Lua 정의
   → data.lua 실행
   → data-updates.lua가 생성·수정 (예: 유체별 배럴 제작법)
   → 게임의 --dump-data
   → 최종 data.raw JSON 2,840 프로토타입 / 224 유형
   → 엔진이 검증·기본값 적용·게임 상태와 조합
```

모드 일반 흐름에는 data-final-fixes 단계도 있다. 이번 활성 core/base에는 그 단계의 추가 파일이 없었다. Lua를 정규식으로 추정 실행한 것이 아니라 게임의 공식 덤프 결과를 사용했다.

**data.raw 덤프에도 생략된 엔진 기본값은 있다.** 예를 들어 톱니바퀴의 energy_required는 덤프에 없으며, 동봉 2.0.77 API의 RecipePrototype 기본값 0.5초로 보완했다. 보완 출처를 analysis/api_literal_defaults.json과 각 레시피 time_source에 구분했다. 문서의 예시 코드는 현행 설정값으로 사용하지 않았다.

## 데이터 축과 확보량

| 종류 | 수량 | 주요 역할 |
|---|---|---|
| recipe | 217 | 소모·생산·시간·제작 카테고리 |
| technology | 196 | 선행 연구·과학 팩·효과·행동 트리거 |
| item | 173 | 일반 아이템; ammo/tool 등 별도 타입 제외 |
| fluid | 19 | 온도·열용량·색상·유체 정의 |
| resource | 6 | 채굴·고갈·맵 자동 배치 |
| unit | 8 | 적 체력·이동·공격 |
| noise-expression | 92 | 맵의 높이·습도·자원·적 확률식 |
| noise-function | 28 | 재사용 맵 함수 |


아이템 계열 전체(탄약·도구·장비 아이템 등의 파생 타입 포함)는 **251종**이다. 모든 유형은 [prototypes/](prototypes/) 및 탐색기에 포함했다. 시나리오 Lua 7종(freeplay/pvp/rocket-rush/sandbox/supply/team-production/wave-defense), 캠페인 3종(tight-spot/transport-belt-madness/tutorial)과 튜토리얼도 raw/data/base에 보존했다. 프로토타입은 정적 규칙이고 control.lua는 실제 세션의 목표·시작 지급·이벤트 처리 등을 담당한다.

## 생산량: 시간 × 설비 속도 × 공급 조건

[문서+계산] 무보너스에서 제작 1회 시간 = energy_required ÷ crafting_speed. 분당 총생산 = 60 × crafting_speed ÷ energy_required × 1회 결과 수량.

| 설비 | 기본 제작 속도 | energy_usage | 오염/분 | 톱니바퀴/분 | 자동화 과학 팩/분 |
|---|---|---|---|---|---|
| assembling-machine-1 | 0.5 | 75kW | 4 | 60.0 | 6.0 |
| assembling-machine-2 | 0.75 | 150kW | 3 | 90.0 | 9.0 |
| assembling-machine-3 | 1.25 | 375kW | 2 | 150.0 | 15.0 |


모든 계산은 재료·전력 충분, 모듈·비콘·생산성·품질 없음, 입력/출력 운반과 틱 반올림 제외 조건이다. energy_usage는 저장 프로토타입 값이며 실제 전력 소비를 단순히 모든 상태에서 동일하다고 해석하면 안 된다.

- 철판: 철광석 1 → 철판 1, 기준 3.2초. 돌 용광로 속도 1에서 0.3125개/초.
- 강철: 철판 5 → 강철 1, 기준 16초. 동일 속도의 철판 용광로와 강철 용광로는 철 공급 관점에서 1:1 비율이다.
- 구리 전선: 구리판 1 → 전선 2, 기준 0.5초. 전자 회로: 철판 1 + 전선 3 → 회로 1, 기준 0.5초. 동일 속도 설비라면 전선:회로 설비 수는 3:2다.
- 운송 벨트 저장 speed는 0.03125 / 0.0625 / 0.09375. 동봉 API 식 speed×480에 따라 양쪽 레인이 찬 직선 기준 **15 / 30 / 45개/초**다. 기본 벨트 15개/초를 철판으로 채우는 돌 용광로는 이론상 48대, 속도 2 용광로는 24대다.

근거: [prototypes/recipe.json](prototypes/recipe.json), [prototypes/assembling-machine.json](prototypes/assembling-machine.json), [prototypes/furnace.json](prototypes/furnace.json), [prototypes/transport-belt.json](prototypes/transport-belt.json), API의 RecipePrototype.energy_required와 TransportBeltConnectablePrototype.speed.

## 확률·촉매를 구분해야 하는 제작법

우라늄 정제는 광석 10개, 기준 12초. U-235 결과는 수량 1/확률 0.007, U-238은 수량 1/확률 0.993이다. 이것을 매회 확정 지급으로 계산하지 않았다.

코바렉스는 U-235 40 + U-238 5를 넣고 U-235 41 + U-238 2를 반환한다. 기본 순증가는 U-235 +1, U-238 -3이다. U-235 결과의 ignored_by_productivity=40, U-238 결과의 ignored_by_productivity=2를 보존했다. 총출력과 순이익·생산성 적용량을 섞으면 경제 분석이 크게 틀린다. 탐색기의 간단 계산기는 **총출력**이며 촉매 반환을 순생산으로 표시하지 않는다.

## 연구·진행도

기술 196개의 선행 링크와 unlock-recipe를 전수 연결했다. 참조 누락과 선행 순환은 0개다. 일반 연구의 unit에는 count 또는 count_formula, 과학 팩 재료, time이 있다. 무한 연구 공식은 문자열 원문 그대로 보존했다.

모든 기술이 과학 팩 소비형은 아니다. 예를 들어 steam-power는 철판 50개 제작, electronics는 구리판 10개 제작, oil-processing은 원유 채굴 트리거다. automation-science-pack의 트리거는 연구소 제작이다. 행동 트리거 기술을 비용 0의 즉시 연구로 바꾸면 진행 순서가 달라진다.

automation 기술은 자동화 과학 팩 1개씩 10회, 단위 10초다. 기본 연구 속도 1 기준 연구소 시간 합은 100초이며 팩 제조·운반 시간은 별도다. force 연구 속도·생산성, 지도 난이도 기술 비용 배수도 실제 플레이 결과에 영향을 준다.

근거: [정리된 연구 데이터](analysis/technologies.json), [기술 그래프](analysis/technology_graph.json), [prototypes/technology.json](prototypes/technology.json).

## 채굴·에너지·설비

철·구리·석탄·돌의 mining_time은 1, 우라늄은 2이고 황산 10이 요구된다. 자원량·채굴 속도·연구 생산성·전력·출구 막힘은 별도 축이다. 원유는 고체 광석과 같은 고갈/출력 모델로 계산하면 안 된다.

대표 저장값: 보일러 energy_consumption 1.8MW, 태양 전지판 production 60kW, 축전지 buffer_capacity 5MJ 및 입출력 300kW, 원자로 consumption 40MW와 neighbour_bonus 1. 태양 전지판 60kW는 하루 평균 발전량이 아니고 원자로 40MW는 바로 전력망에 공급되는 전기 출력이 아니다. 열·증기 변환과 환경 조건을 구분해야 한다.

[설비 요약](analysis/machines.json)은 제작·채굴·연구·운송·발전·투입기를 함께 담는다. 전체 필드와 유체/열 정보는 유형별 JSON에 보존했다.

## 적·오염·진화·확장

| 유닛 | max_health | movement_speed 원값 | 공격 cooldown 틱 |
|---|---|---|---|
| small-biter | 15 | 0.2 | 35 |
| medium-biter | 75 | 0.24 | 35 |
| big-biter | 375 | 0.23000000000000004 | 35 |
| behemoth-biter | 3000 | 0.3 | 50 |
| small-spitter | 10 | 0.185 | 100 |
| medium-spitter | 50 | 0.165 | 100 |
| big-spitter | 200 | 0.15 | 100 |
| behemoth-spitter | 1500 | 0.15 | 100 |


cooldown만으로 실제 DPS를 확정하지 않는다. 피해 action·투사체·저항·사거리·목표 접근이 추가로 관여한다. 이동 값도 위 표에서는 단위 변환하지 않은 저장값이다.

기본 enemy_evolution은 time_factor 0.000004, destroy_factor 0.002, pollution_factor 0.0000009다. 소스 주석의 입력 단위는 각각 초, 파괴된 스포너, 오염 단위다. **이 세 값을 단순 선형 합산한 값이 곧 현재 진화도라고 주장하지 않는다.** 실제 엔진 누적 규칙은 별도다.

스포너 result_units는 진화도에 따른 후보별 가중치 곡선을 가진다. small-biter는 (0,0.3)→(0.6,0), medium은 (0.2,0)→(0.6,0.3)→(0.7,0.1), big은 (0.5,0)→(1,0.4), behemoth는 (0.9,0)→(1,0.3)이다. 개별 y값을 정규화 없이 최종 등장 확률로 읽지 않는다.

확장 쿨다운 저장 범위는 14,400~216,000틱(60틱/초에서 4~60분)이다. 소스 주석의 식은 `lerp(max, min, -e² + 2e)`. 범위값뿐 아니라 진화도 의존성이 있다. Pollution diffusion_ratio=0.02, min_to_diffuse=15 등도 [map-settings](prototypes/map-settings.json)에 포함했다. death-world 등 프리셋은 이 기본값 일부를 덮어쓴다.

## 신뢰 범위

실제 설치본의 기본 밸런스 데이터와 실행 후 생성된 레시피는 확보했다. 모드·플레이어 세이브·서버별 설정·런타임 연구 보너스·Space Age 데이터는 포함하지 않았다. 게임 엔진 C++의 모든 물류·AI·전투 알고리즘을 역공학 완료한 것도 아니다. 연구/레시피 연결은 정적으로 검증했고 실전 공장·전투 시뮬레이션 전수 검증은 하지 않았다.

근거 원장: [최종 data.raw](run/script-output/data-raw-dump.json), [동일 버전 API](reference_docs/prototype-api.json), [소스 행 색인](analysis/source_line_index.json), [검증 결과](analysis/validation.json).
