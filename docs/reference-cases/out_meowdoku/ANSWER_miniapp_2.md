# Meowdoku 1.20.0 — MiniApp 추가 조사 답변 (2)

근거: `D:\99.기타\out_meowdoku\scripts_src` 디컴파일 소스, 번역표(`translations/`), 추출 텍스처.
규칙·수치·문자열만 적는다(코드 없음). 확인하지 못한 것은 **미확인**, 데이터로 추정한 것은 **추정**으로 표시한다.
"대조군"은 A/B 기본값(실험 미배정) 기준이다.

**갱신(2차)**: 첫 답변의 미확인 2건·추정 3건을 모두 확정했다. Godot 바이너리 씬(.scn)을 직접 파싱해(`tools/godot_rsrc.py`) 씬에 저장된 실제 값을 읽었다.
- 5절 인트로 실제 값 / 패턴 강조 구간 — 확정
- 6절 콤보 단계별 이미지 — 확정. **첫 답의 추정(08~17)은 7단계부터 틀렸다**(실제 Unreal·Insane·Epic·Breathtaking)
- 6절 진행 바 슬롯 모양 — 확정
- 10절 카운트다운 5.2초 — 확정

---

## 1. 승리 등급

### 1.1 걸음 수(step) 정의
- 보드 상태를 바꾼 **입력 1회 = 1걸음**이다. 누르고 끌다가 떼는 제스처 하나가 칸을 여러 개 바꿔도 1걸음이다.
- 포함:
  - X 표시·X 지우기: 기록되는 셀 변경이면 모두 해당(지우기 포함). 한 번의 스와이프로 여러 칸을 칠해도 1
  - 고양이 놓기: 1
  - 더블탭으로 고양이 놓기: 1 (첫 탭의 변경은 취소하고 고양이 1회로 센다)
  - 오답 표시(틀린 고양이): 1
  - 메모(draft) 표시: 1. 단 메모 고양이를 그 제스처에서 승격하지 않으면 걸음에서 뺀다
  - 도구: 마우스 1, 위치 찾기 1, 힌트 적용 1(빈칸이 실제로 바뀐 경우)
- 보드가 안 바뀐 제스처(빈 탭 등)는 0이다.
- 승리 시점의 누적값으로 등급을 매긴다(판 시작 시 0).

### 1.2 임계값 (판 크기별, 걸음 수 기준)
| 크기 | PERFECT | P5 | P10 | P20 |
|---|---|---|---|---|
| 4, 5 | 없음 | 없음 | 없음 | 없음 |
| 6 | = 6 | ≤ 16 | ≤ 20 | ≤ 30 |
| 7 | = 7 | ≤ 30 | ≤ 32 | ≤ 36 |
| 8 | = 8 | ≤ 25 | ≤ 32 | ≤ 40 |
| 9 | = 9 | ≤ 28 | ≤ 35 | ≤ 45 |
| 10 | = 10 | ≤ 30 | ≤ 38 | ≤ 50 |
| 11 | = 11 | ≤ 60 | ≤ 65 | ≤ 71 |
| 12 | = 12 | ≤ 70 | ≤ 75 | ≤ 80 |

- PERFECT = 걸음 수가 판 크기와 같음(고양이만 정확히 놓음). 판 크기보다 작으면 등급 없음.
- P20 를 넘으면 등급 없음. 4·5 크기는 표에 없어서 항상 등급 없음.
- 등급 이름(내부): PERFECT, P5, P10, P20, NONE.

### 1.3 표시
- **승리 토스트는 PERFECT·P5·P10 만 표시**한다. P20 은 토스트 노드가 있어도 띄우지 않는다.
- 토스트 1.3초 표시 후 숨김, 결과 화면 전환까지 1.5초 대기.
- 이번 판에 자동 X 배너(손으로 X 를 하나도 안 칠한 판)가 떴으면 토스트를 생략한다.
- 문구: 등급별 풀에서 무작위 1개. `{N}` = 걸음 수, `{CATS}` = 판 크기. 원문은 부록 A.
- A/B `win_toast` 설정은 코드에서 참조하지 않는다(위 동작이 항상 적용).

## 2. 레벨 선택 (51레벨 이후)

### 2.1 뱅크 선택 순서
- 후보군 = 일반 → LKStyle → GC 를 이어 붙인 목록 + 별도 lk_mod 목록.
  - 10×10 의 r3·r4 는 일반 뱅크를 빼고 LKStyle·GC 만.
  - GC 는 10×10 r1 과 11×11 에서만 포함.
  - 티어(N/H)를 지정했는데 결과가 비면 티어 없이 다시 모은다.
- 커서는 크기·등급·티어별로 저장되는 인덱스를 **순서대로 1씩** 진행한다(무작위 아님).
- 목록 끝에 닿으면 인덱스 0으로 돌아가고 **대칭 변환 번호를 +1**(0~7 순환)한다. 변환 0~7 = 회전·반전 8가지. lk_mod 는 변환하지 않는다.
- 50레벨까지는 같은 목록을 `인덱스 % 전체 개수`로 순환하고 변환은 쓰지 않는다.

### 2.2 lk_mod(LinkedIn 변형) 삽입
- 메인 경로(51+)에서만.
- 직전 lk_mod 이후 일반/LKStyle/GC 퍼즐을 **4판 전달하면 다음 1판을 lk_mod** 로 낸다(4판 + 1판 주기).
- lk_mod 후보: 판 크기가 같고, 등급이 같은 것(하드 레벨은 퍼즐의 `r`, 그 외는 `maxR` 로 비교). 예약 번호 20, 30, 53, 71, 72, 75, 114, 141, 164 는 제외(특수 레벨용).
- lk_mod 진행 인덱스는 크기·등급별로 따로 저장되고 **순환하지 않는다.** 다 쓰면 그 크기·등급에서는 더 이상 끼우지 않는다.

### 2.3 중복 제거 (`_pid_h`)
- 퍼즐 ID = 판 크기 + 16자리 해시(`_pid_h`) + 변환별 접미사(`_pid_s[변환번호]`).
  - 해시는 영역 지도를 8가지 변환한 뒤 정규화·직렬화해 사전순 최소인 것(정규형)의 SHA-256 앞 16자리.
  - 접미사가 변환별로 달라서, **같은 퍼즐이라도 다른 변환으로 나오면 다른 ID** 다.
- 최근 전달 기록 **100개**(저장됨, 오래된 것부터 버림)에서 같은 ID 를 찾는다. **다른 레벨 번호**로 나온 적이 있으면 중복이다(같은 레벨 재도전은 중복 아님).
- 중복이면 다음 후보를 고른다. 재시도 상한 = min(커서 예산, 최근 기록 수 + 1). 상한을 넘으면 중복이라도 그대로 낸다.

### 2.4 단일 칸 영역 조건 (`single_region_num`)
- 1차 스캔: 단일 칸 영역이 2개를 넘으면 건너뜀(예산이 1 남으면 그냥 통과).
- 최종 검사: 1개를 넘으면 탈락. 대조군 기본값(ALL_ONE)의 상한이 레벨·등급과 무관하게 **1**.
- SP·LK·lk_mod 출처는 이 검사를 하지 않는다.

### 2.5 후보 완화 7단계
후보가 끝나거나 예산(판크기² × 12)을 다 쓰면 다음을 차례로 시도한다.
1. 분산도 필터 해제(대조군은 처음부터 꺼져 있음)
2. 1차 단일 칸 제한(2개) 해제
3. A/B 단일 칸 제한(1개) 해제
4. 같은 등급에서 티어 지정 해제
5. 낮은 등급으로 1씩 내려가며 탐색
6. 높은 등급으로 1씩 올라가며 탐색(존재하는 최고 등급까지)
7. (단계 수 상한) 없으면 선택 실패

### 2.6 난수
- 엔진 전역 난수(`randi_range`)를 쓴다. 코드에서 시드를 고정하는 곳은 없다(엔진 시작 시 자동 시드).
- 레벨 선택에서 난수를 쓰는 곳: 전략 3 이상일 때 등급 뽑기(대조군 균등, 실험군 가중치), pre-cat 칸 선택, 토스트 문구.
- 뱅크 순서·변환·lk_mod 삽입은 난수가 아니라 저장된 진행 인덱스로 결정된다.

## 3. pre-cat (21레벨+ 사전 배치)
- **발동 조건**(모두 충족):
  - 일반 레벨, 21레벨 이상
  - 황금 물고기·컬러 챌린지·도구 비축 압박 레벨이 아님
  - 서버 추천 실험군이 아님
  - 아래 사유 중 하나 이상(직전 승리 처리에서 정해져 다음 레벨로 넘어옴)
    - (1) **직전 레벨이 하드**(슈퍼하드 포함)였고 이번 등급이 3 이상
    - (2) **고전**: 직전 레벨에서 2번 이상 실패했거나 부활을 쓰고 이김
    - (3) **강등**: 직전 승리 처리에서 DDA 전략이 내려감
- **확률 없음**: 조건이 맞으면 항상 놓는다. A/B `pre_cat`(ALWAYS/HALF/OFF) 설정은 코드에서 참조하지 않는다.
- **개수**: 1마리.
- **칸 선택**:
  - 빈 보드 기준으로 정답 칸마다 "추론에 필요한 기법 단계(rank)"를 계산한다.
  - **rank 3 이상**인 정답 칸 중 무작위 1칸(R3+ 판정). 없으면 놓지 않는다.
  - 실험 11511(높은 등급 우선)은 rank 최댓값 칸 중 무작위.
- 그 레벨에서 정한 위치는 저장(잠금)되어 재도전해도 같은 칸에 놓인다.

## 4. 황금 물고기 · 컬러 챌린지

### 4.1 황금 물고기(OneFish 삽입)
- **기본 비활성**(`golden_fish_func` = CONTROL).
- 켜진 경우:
  - 시작: 51레벨(조기 해금 실험군은 31레벨).
  - **주기**: 일반 레벨 **승리 4회마다**(연속일 필요 없음, 실패해도 카운트 유지) 다음 판이 황금 물고기 판이 된다.
  - "연승" 가속 실험군(STICKY_BOOST): 황금 물고기를 2판 연속 이긴 상태면 주기가 3회로 줄어든다.
  - **레벨 번호를 쓰지 않는다**(끼워 넣는 판). DDA 계산에서도 빠진다.
  - 크기: 첫 판 7×7, 이후 8 → 9 → 10 순환(SIZE_UP 실험군은 8,10,10,9,10,10). 뱅크 OneFish.
  - 등급: 현재 전략을 3~4로 자른 값(RANK_ALT 실험군은 3·4 번갈아).
  - **건너뛰기**: 실패 화면의 건너뛰기 링크로 넘길 수 있다. 넘기면 대기·카운트가 초기화되고 연속 건너뛰기 수 +1, 연승 0.
  - 건너뛰기 벌칙 실험군: 연속 2번 건너뛰면 다음 생성을 1회 막는다.

### 4.2 컬러 챌린지
- **기본 비활성**(`color_challenge_func` = CONTROL).
- 켜진 경우(SINGLE / SINGLE_QUIET / DUAL):
  - 해금: 황금 물고기 판을 **누적 4번** 거친 뒤(끝낸 판·건너뛴 판 모두 센다). 황금 물고기가 켜져 있어야 의미가 있다.
  - **주기**: 매 황금 물고기 판 이후 일반 레벨 **승리 2회째**에 대기 상태가 되어, 다음 판이 컬러 챌린지.
  - **레벨 번호를 쓰지 않는다.**
  - 크기: 첫 판 8×8, 이후 8 → 9 → 10 순환. 등급: 첫 판 3, 이후 현재 전략 4 이상이면 4, 아니면 3. 뱅크 ColorChallenge.
  - SINGLE_QUIET: 연속 2번 건너뛰면 그다음 컬러 챌린지는 현재 레벨 + 7 레벨 이후에야 생긴다.
- **팔레트**: 색 계열 3종 × 10색.
  - 빨강·노랑 계열: fae76e, f5cf48, d19c36, b67b51, edc893, 905631, ffb562, f59139, db7b62, a55645
  - 파랑·초록 계열: afdf89, 88af5c, 58ac54, 3e774c, c9dd5a, aebf3f, 72d374, 679238, 83debb, 4fbaa6
  - 보라·분홍 계열(실제 색은 하늘·남색 위주): bbdaf7, 92e2e1, 8ed4f8, 78b9ef, 6686b9, 9ab3f5, 7082d4, b692da, 8975bc, 565a97
- **패턴(모드)**:
  - SINGLE 계열: 전달 순번마다 계열 1개를 순환(빨강·노랑 → 파랑·초록 → 보라·분홍).
  - DUAL: 2계열 조합. 빨강·노랑 + 파랑·초록 조합은 금지 → (빨강·노랑, 보라·분홍)과 (파랑·초록, 보라·분홍) 두 쌍을 번갈아 씀.
  - 영역마다 색 이름 키가 있다(예: `COLOR_CHALLENGE_ICE_BLUE` = Ice Blue / 아이스 블루).

## 5. SP(특수) 레벨
- **프리필**: 일반 레벨과 같은 규칙이고, 10레벨 이하에만 적용된다. SP 레벨 중 해당하는 건 10레벨(패턴 digit1, 7×7) 하나다. 7레벨 이상이라 **1칸짜리 영역의 정답 칸**을 우선 1칸 채운다. 그 밖의 SP 레벨은 프리필 없음.
- SP 데이터에는 `colorMap`(영역 색 지정)과 `spRegion`(패턴을 이루는 영역 번호)이 있다.
- **인트로 연출**: A/B `board_intro` 기본값이 CONTROL 이라, 대조군은 SP 전용 인트로가 **없다**(일반 인트로와 같음).
  - 일반 인트로 [확정, 게임 화면 씬에 저장된 실제 값]: 아래 두 층이 동시에 움직인다.
    - 보드 전체: 투명 → 불투명 0.45초(LINEAR), 크기 1.3 → 1.0 을 0.48초(CIRC_OUT). 위치 이동은 꺼져 있다.
    - 칸 하나하나: 시작 시각 = 0.18초 + 순번 × 0.04초. 순번 = 열 + (n−1−행), 즉 왼쪽 아래 칸부터 오른쪽 위로 대각선.
      각 칸은 페이드 0.4초(SINE_OUT) + 크기 0 → 1 을 1.0초 동안 키운다.
    - 칸 크기 곡선(사용자 정의, 1.0초 기준): 0초 0 → 0.29초 1.1(튀어 오름) → 0.45초 0.97 → 0.57초 1.0 이후 유지.
    - 판 크기 n 이면 마지막 칸 시작은 0.18 + (2n−2)×0.04초. 10×10 이면 0.90초, 전체 끝은 약 1.9초.
    - A/B `game_grid_ui` 기본값(NOMAL)은 이 값을 바꾸지 않는다. SINGLE_LINE 실험군만 칸 크기를 LINEAR·0.4초로 바꾼다.
    - 스크립트 기본값(0.12초 간격·0.3초 페이드)은 씬 값으로 덮어써져 실제로 쓰이지 않는다.
  - PATTERN_FIRST 실험군: 패턴(spRegion) 칸이 0.18초에 먼저 나타난다. 나머지 칸은 max(0.4, 1.0 − 0.5) = 0.5초 뒤부터 대각선 순서로 나타난다(칸 크기 1.0초 − 0.5초 앞당김).
  - PATTERN_SWEEP 실험군 [확정, 셰이더·스크립트]: 인트로가 끝난 뒤 패턴 강조 오버레이를 0.8333초 재생한다. 세 가지가 겹친다.
    - 어둡게: 패턴이 아닌 칸을 검정으로 덮는다(패턴 칸은 뚫림, 보드 둥근 모서리에 맞춰 자름). 0~0.2초 알파 0 → 0.175, 0.6초까지 유지, 0.6~0.8333초 0으로.
    - 외곽선: 패턴 영역 둘레 64px 외곽선. 알파가 어둡게와 같은 시간표(0~0.2 등장, 0.6까지 유지, 0.8333까지 사라짐).
    - 빛 띠: 패턴 칸 위에만 흰색 띠(알파 0.35, 반폭 180px, 가장자리 부드러움 20px)가 **왼쪽 아래 → 오른쪽 위 45°**로 0~0.4333초 동안 한 번 지나간다.
  - LK_MOD_FREQ_BOOST 실험군에서는 lk_mod 출처 퍼즐에 특수 인트로를 쓰지 않는다.

## 6. 대조군 연출 문자열·기본값
| 항목 | 대조군 동작 | 원문 |
|---|---|---|
| 콤보 표시 | 정답 고양이 1마리마다 콤보 +1, 오답이면 0(X 표시는 무관). **3콤보부터** 애니메이션 `Encourage01_<단계>`, 단계 = min(콤보 − 2, 10). 음성 동반(`combo_voice` = REAL_MALE_B_TEXT2). 애니메이션 길이 약 1.02~1.07초 | 텍스트가 아니라 이미지. 아래 참고 |
| 고양이 배치 토스트 | **없음**(`cat_toast` = OFF) | — |
| 놓친 X 칭찬 | **항상 동작**(6×6 이상). 문구 없이 해당 칸에 손 애니메이션(STAR_EYE_CAT) | 문구 없음 |
| 풀마크 | **없음**(`full_mark_feedback` = NONE) | — |
| 승리 토스트 | 1.3절 | 부록 A |
| 결과 화면 | `pass_text` = V3_G1, 아래 규칙 | 부록 A |
| 실패 화면 | 제목 + 부활 버튼 + 남은 고양이 수. 격려 문구는 대조군에서 숨김 | 부록 A |
| 영역 어둡게 | **꺼짐**(`cat_found_grid` = OFF). 실험군 알파: G1 0.25, G2 0.15 | — |
| 진행 바 | `normal_top_ui` = CONTROL: 고양이 진행 바 **없음**, HARD 태그 표시. 슬롯형 진행 바는 실험군(CAT_PROGRESS 등 5~10번)에만 있음 | 슬롯 모양은 아래 |

**슬롯형 진행 바(실험군 전용) [확정]**:
- 영역 1개 = 슬롯 1칸(판 크기만큼, 최대 12칸). 순서는 영역 순.
- 칸 모양은 **고양이 머리 실루엣**(`cat_progress_slot`). 빈 칸은 베이지(F2E4D7) 실루엣, 고양이를 찾으면 그 칸이 고양이 얼굴로 바뀐다(튀어 오름 1.2배, 0.13초 커졌다가 0.22초 복귀).
- 크기: 칸 66px, 간격 2px, 좌우 여백 24px, 바 최대 폭 760px. 넘치면 칸 62px 로 줄이고 간격을 좁힌다.
- 바 배경은 양 끝이 둥근 띠(`cat_progress_bar_bg`, 884×84). 보드에 붙는 배치(LAYOUT_MIDDLE·FULL_OPEN)는 칸 68px, 간격 69px, 여백 56px, 위쪽 모서리 반경 40px.
- 변형별 차이:
  - COLORED: 빈 칸 실루엣을 영역 색 50% 알파로 칠함
  - SHOW_DONE_COLOR·FULL_OPEN: 찾은 칸 아래에 영역 색 점(`cat_progress_dot`) 표시
  - AUTO_SORT: 찾은 칸을 앞쪽으로 모음(이동 0.35초, 5칸 이상 떨어지면 0.5초, 칸마다 0.03초 지연)

**콤보 이미지 단어**(텍스처 `ui_mao_glc_pic_XX`): Nice, Great, Perfect, Excellent, Amazing, Unbelievable(01~06, 배경판 있는 a 버전 포함), Hawk Eye(07), Nice, Great, Perfect, Excellent, Amazing, Unbelievable, Incredible, Phenomenal, Spectacular, Legendary(08~17), Unreal, Insane, Epic, Breathtaking(18~21), Nice Meow, Great Kitty, Purr-fect, Excellent Kitten, Amazing Mew, Paw-some, Incredible Whiskers, Catnip Level, Epic Pounce, Legendary Furball(22~31).
- **대조군 단계별 이미지 [확정]**: 코드가 재생하는 플레이어 `AnimationPlayer2` 의 애니메이션을 씬에서 읽었다.
  | 단계(콤보) | 1(3) | 2(4) | 3(5) | 4(6) | 5(7) | 6(8) | 7(9) | 8(10) | 9(11) | 10(12+) |
  |---|---|---|---|---|---|---|---|---|---|---|
  | 이미지 | Nice | Great | Perfect | Excellent | Amazing | Unbelievable | Unreal | Insane | Epic | Breathtaking |
  | 파일 | pic_08 | 09 | 10 | 11 | 12 | 13 | 18 | 19 | 20 | 21 |
- 같은 씬의 다른 플레이어 3개(배경판 버전 01~06, Incredible~Legendary 08~17, 고양이 말장난 22~31)는 `combo_text` 실험용이다. `combo_text` 설정은 코드에서 참조되지 않아 실제로는 위 표만 쓰인다.

**놓친 X 칭찬 조건**:
- 손으로 X 를 칠한 칸이 어떤 고양이의 배제 구역에 있어야 한다.
- 그 고양이는 놓은 지 10초가 지났어야 하고, 같은 구역에 이미 수동 X 가 있어야 한다.
- 가장 최근 고양이의 구역이 아니어야 하고, 힌트가 X 를 친 칸이 아니어야 한다.
- 고양이 하나당 1회. 후보가 여럿이면 가장 오래된 고양이.

**결과 화면 문구 선택(V3_G1)**:
1. 하드(슈퍼하드) 레벨: 첫 시도 / 재시도 풀
2. 실수 0 이고 재시작·부활 없음: PERFECT 풀
3. 재시작·부활 없음: "상위 N%" 계산
   - N = 51 + 48 × √(max(0, P90 − 클리어초) / P90) + 0~1 난수
   - 크기별 P90: 4=44, 5=37, 6=107, 7=187, 8=265, 9=360, 10=431초
   - N ≤ 75 → PLAIN 풀
   - 지난 승리보다 N 이 오름 → AWESOME
   - N < 83 → PERCEPTIVE, < 91 → INTELLIGENT, 그 외 BRILLIANT
   - **실제 통계가 아니라 시간으로 만든 값**이다
4. 그 외(재시작·부활 있음): RETRY 풀

**실패 화면(대조군)**:
- 제목 `FAIL_TITLE_FISH`(황금 물고기면 `FAIL_TITLE_GOLDEN_FISH`)
- 부활 버튼 `FAIL_REVIVE_3FISH`(목숨 상한 3일 때. 다르면 `FAIL_REVIVE_NFISH`)
- `FAIL_REMAINING_CAT` + 남은 고양이 수
- 목숨: `health_points_rule` 기본값이 모든 레벨 3

## 7. barrage(가짜 응원 메시지)
- **기본 비활성**(`barrage_func` = DISABLED). 켜도 **11레벨 이상**, 일반 레벨에서만.
- **트리거**:
  - 판 안 경과 시간(광고 재생 중 제외) 60초 이후에, 마지막 조작 후 20초 동안 무입력이면 1회 시도한다.
  - 시도 뒤 다음 시도는 60초 후.
- **빈도**: 판당 최대 2회. SINGLE 은 1개, MULTI 는 1~3개를 동시에 띄운다.
- **중복 방지**: 한 판에서 같은 문구는 다시 안 쓴다. 일일 문구 4종은 그날 이미 보인 것을 제외한다.
- **문구 풀**: 8종 전체(부록 A). 숫자·이름 채우기:
  - BULLET_1: 10,000~1,000,000
  - BULLET_2: 100~999
  - BULLET_3: 20~99
  - DAILY_1: 4~7 + 닉네임
  - DAILY_2: 100~160 + 닉네임
  - DAILY_3: 닉네임
  - DAILY_4: 60~99
  - 닉네임은 로봇 닉네임 풀(`RobotNicknamePool.NAMES`)에서 무작위
  - 아이콘(근육·잎·별·번개)을 문구 안에 넣는다

## 8. 저장 / 이어하기
- **기본 = ON**(`normal_endgame_save`). 진행 중 판의 보드 상태(고양이·표시·오답·프리필·목숨 등)를 저장한다.
- **저장 시점**: 셀이 바뀔 때마다.
  - 고양이 놓기·오답이면 즉시 저장
  - 그 외(X 표시 등)는 0.5초 디바운스 후 저장
  - 클리어 후에는 저장하지 않음
- **stale gate**: 기본값(ON)에서는 **없음** — 며칠 뒤에 와도 그대로 이어한다. 아래는 실험군 전용이다.
  - STALE_RESTART(2): 마지막 접속 후 **3일** 이상 → 저장된 판을 버리고 같은 레벨을 처음부터
  - STALE_NEW_EASIER(3): **3일** 이상 → 저장된 판을 버리고 더 쉬운 새 퍼즐
  - STALE_NEW_EASIER_TWO_DAYS(4): 위와 같고 기준 **2일**
  - 복귀 1회당 한 번만 버린다(이미 버렸으면 다시 안 버림)
- **버리는 범위**: 진행 중이던 판의 보드 스냅샷만. 레벨 번호·DDA·뱅크 진행은 그대로다. 아직 시작 안 한 컬러 챌린지 스냅샷은 버리지 않고 표시만 한다.
- 참고: 그날 첫 판 완화(하루 첫 판 등급 −1)는 남은 스냅샷에 사용자가 놓은 고양이·표시·오답이 있으면 그날 기회가 없어진다.

## 9. DDA
- **시작값**: 전략 1. 51레벨 진입 시 2 미만이면 2로 올린다.
- **하한/상한**(승리 처리 시):
  | 레벨 | 하한 | 상한 |
  |---|---|---|
  | 6~20 | 1 | 2 |
  | 21~50 | 1 | 3 |
  | 51~100 | 1 | 4 |
  | 101~200 | 2 | 5 |
  | 201+ | 2 | 6 |
- 1~5레벨은 DDA 미적용(전략 1 고정).
- 승급: 연속 클린 승리 2판(51+ 1판). 강등: 연속 실패 2판(20 이하 1판), 21+ 같은 전략에서 재도전 레벨 2연속, 재도전·부활 승리.
- **레벨 선택 시 클램프**(대조군): 1~5레벨 1 / 6~20 ≤2 / 21~50 ≤3 / 51+ ≤4. 3 이상이면 2~상한 균등 무작위.
- **전략 → 난이도 매핑**:
  | 전략 | 등급 r | 티어 |
  |---|---|---|
  | 1~4 | 1~4 | N |
  | 5 | 4 | H |
  | 6 | 5 | N |
  | 7 | 5 | H |
  - 하드 레벨(21+ 10의 배수): r5·N 고정.
  - 대조군은 51+ 에서 4로 자르므로 일반 판은 최대 r4·N. 전략 5~7은 실험군·이벤트 모드에서 쓰인다.

## 10. 카운트다운 부활
- **기본 = OFF**(`revive_countdown` = CONTROL) 확인.
- 켰을 때(그룹 1~4):
  - 조건: 일반 레벨, 6×6 이상, 그 레벨에서 처음 실패, 놓은 고양이 수 ≥ floor(비율 × 판 크기). 비율은 그룹 1·3 = 0.5, 그룹 2·4 = 0.8.
  - 실패 화면 대신 카운트다운 화면이 뜬다. 버튼 문구 `FAIL_REVIVE_3FISH`, 무료 또는 광고 배지.
  - 버튼을 누르면 부활(목숨 회복 후 이어하기).
  - 시간이 다 되면: 그룹 1·2 = 그 레벨을 처음부터 다시 시작, 그룹 3·4 = 실패 화면 표시.
  - 켜진 경우 실패 화면의 부활 버튼은 숨긴다(황금 물고기 제외).
- **시간 [확정, 씬 애니메이션 `CountdownFill`]**: 총 **5.2초**. 이 애니메이션이 끝나면 시간 초과다.
  - 0~0.22초: 게이지·버튼 페이드인(게이지 크기 0.17초 동안 커짐)
  - 숫자: 0초 5 → 1초 4 → 2초 3 → 3초 2 → 4초 1 → 5초 0. 숫자가 바뀔 때마다 0.88~1.08초 구간에 튀는 연출(매초 반복)
  - 원형 게이지: 1 → 0 을 0~4.97초에 줄이고 5.0초에 0. 4.9~5.0초 게이지 사라짐. 끝부분 입자는 0.1~4.92초 방출
  - 5.1~5.2초: 화면 전체 사라짐 → 시간 초과 처리

---

## 부록 A. 문자열 원문 (영어 / 한국어)
#### 결과 화면 — 무실수 첫 시도(PERFECT) (14쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Perfect | 0 mistakes! Every cat perfectly placed! | 완벽 | 실수 0회! 모든 고양이를 정확히 찾았어요! |
| Flawless | 0 errors! Your logic is absolutely on point! | 무결점 | 오류 0개! 논리가 완벽하게 들어맞았어요! |
| Perfect | No mistakes, you're a true master! | 완벽 | 실수 하나 없이, 진정한 마스터네요! |
| Spot On | Not a single wrong mark. Well done! | 정확무결 | 틀린 표시가 하나도 없어요. 훌륭해요! |
| Expert | You placed every cat exactly where it belongs! | 전문가 | 당신은 모든 고양이를 정확한 자리에 두었어요! |
| Untouchable | A perfectly clean sheet! Your logic is amazing! | 범접 불가 | 완벽하게 깨끗한 성적! 당신의 논리는 놀랍네요! |
| Purr-fect | 0 errors! Every single move was calculated perfectly! | 야옹-펙트 | 0 실수! 모든 수가 완벽하게 계산되었어요! |
| Masterclass | Not a single slip-up! You are a puzzle pro! | 마스터클래스 | 단 한 번의 실수도 없이! 당신은 퍼즐 프로! |
| Exact | Every placement was 100% accurate and precise! | 정밀 | 모든 배치가 100% 정확하고 정밀! |
| Surgical | Precision logic with absolutely zero mistakes! | 외과 수술급 | 실수 없는 정밀한 논리! |
| Seamless | A perfectly smooth run from start to finish! | 매끄러움 | 처음부터 끝까지 완벽하게 매끄러운 진행! |
| Crystal Clear | A flawless execution from start to finish! | 수정처럼 맑음 | 처음부터 끝까지 완벽한 실행! |
| Stellar | Every single move was calculated and 100% correct! | 별처럼 | 모든 수가 계산되었고 100% 정답! |
| Immaculate | Spotless record! You make this look entirely too easy! | 완결 | 흠 없는 기록! 이걸 너무 쉽게 만드네요! |

#### 결과 화면 — 일반 승리(상위% 75 이하) (10쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Strategic | You totally owned this level. | 전략적 | 이 레벨을 완전히 장악했어요. |
| Clever | You navigated this level beautifully and smoothly. | 기지 | 이 레벨을 아름답고 매끄럽게 통과했어요. |
| Nice Work | A solid victory on your very first attempt! | 멋져요 | 첫 시도에 거둔 안정적인 승리! |
| Superb | You solved this grid with steady and calm logic! | 뛰어남 | 침착하고 꾸준한 논리로 이 판을 풀어냈어요! |
| Great Job | First try and you completely nailed the solution! | 아주 잘했어요 | 첫 시도에 해법을 완벽하게 찾아냈어요! |
| Smooth | A very clean solve on a pleasantly tricky grid! | 매끄럽게 | 적당히 까다로운 판을 아주 깔끔하게 풀었어요! |
| Awesome | Your strong intuition led you straight to the end! | 굉장해 | 예리한 직감이 곧바로 끝까지 이끌었어요! |
| Well Played | Masterful handling of this puzzle from top to bottom! | 훌륭한 플레이 | 이 퍼즐을 처음부터 끝까지 능수능란하게 다뤘어요! |
| Smart Move | You really proved your puzzle-solving skills here! | 묘수 | 여기서 퍼즐 실력을 확실히 증명했어요! |
| Wonderful | You cracked the code easily and swiftly! | 환상적 | 쉽고 빠르게 문제를 풀어냈어요! |

#### 결과 화면 — 상위% 75~83 (1쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Perceptive | Beat {pct} of players! You showed great observation! | 통찰력 | 플레이어 {pct}를 이겼어요! 뛰어난 관찰력을 보여줬어요! |

#### 결과 화면 — 상위% 83~91 (1쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Intelligent | Beat {pct} of players! You showed extraordinary logic! | 명석함 | 플레이어 {pct}를 이겼어요! 비범한 논리를 보여줬어요! |

#### 결과 화면 — 상위% 91 이상 (1쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Brilliant | Beat {pct} of players! You showed perfect performance! | 탁월함 | 플레이어 {pct}를 이겼어요! 완벽한 실력을 보여줬어요! |

#### 결과 화면 — 지난 판보다 상위%가 오름 (1쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Awesome | Beat {pct} of players! That's {diff} better than your last game! | 최고야 | 플레이어 {pct}를 이겼어요! 지난 판보다 {diff} 더 좋아졌어요! |

#### 결과 화면 — 재시도·부활 후 승리 (13쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Finally | A tricky puzzle, but you handled it beautifully! | 드디어 | 쉽지 않은 퍼즐이었는데 정말 멋지게 해냈어요! |
| Overcome | Not an easy grid, but you figured it out! | 역전 | 만만한 판이 아니었지만 끝내 알아냈어요! |
| Did It | That wasn't easy, but your logic prevailed! | 해냈다 | 쉽지 않았지만 당신의 논리가 이겼어요! |
| Success | You figured out the hidden trick in the end! | 성공 | 결국 숨겨진 함정을 꿰뚫어 봤어요! |
| Resolved | You patiently worked through all the tricky spots! | 해결 완료 | 까다로운 지점들을 끈기 있게 공략했어요! |
| Excellent | A bumpy road, but you successfully reached the destination! | 훌륭해 | 험난한 길이었지만 끝내 목적지에 도착했어요! |
| Cleared | You decoded the puzzle brilliantly and patiently! | 클리어 | 퍼즐을 훌륭하고 끈기 있게 해독했어요! |
| Good Job | You adapted your strategy and found the right solution! | 잘했어요 | 전략을 바꿔서 올바른 해법을 찾아냈어요! |
| Completed | The puzzle threw some curves, but you still won! | 완료 | 퍼즐이 몇 번이나 변수를 던졌지만 결국 이겼어요! |
| Got It | It took a moment, but the cats finally found their places! | 해냈어 | 시간이 좀 걸렸지만 고양이들이 드디어 제자리를 찾았어요! |
| Bravo | You successfully untangled this tricky grid! | 브라보 | 이 까다로운 판을 멋지게 풀어냈어요! |
| Persevered | A tricky board, but you saw it through to the end! | 끝까지 | 까다로운 판이었지만 끝까지 해냈어요! |
| Unlocked | You sorted out the mess and got the well-deserved win! | 돌파 | 엉킨 상황을 정리하고 값진 승리를 얻었어요! |

#### 결과 화면 — 하드 레벨 첫 시도 승리 (15쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Masterful | A HARD puzzle? Handled with ease! | 능수능란 | 어려움 퍼즐? 가볍게 해결! |
| Incredible | Solved a HARD grid this fast? Amazing! | 대단해 | 어려움 판을 이렇게 빨리 풀다니? 놀라워요! |
| Genius | Hard puzzles are just a warm-up for you! | 천재 | 어려움 퍼즐은 당신에겐 워밍업일 뿐! |
| Legendary | Only a sharp mind can beat this HARD grid! | 전설적 | 예리한 두뇌만이 이 어려움 판을 깰 수 있어요! |
| Sharp | This HARD puzzle was no match for your logic! | 예리함 | 이 어려움 퍼즐은 당신의 논리 앞에 상대가 되지 못했어요! |
| Outstanding | You crushed this HARD puzzle on the first try! | 탁월함 | 단번에 이 어려운 퍼즐을 박살냈어요! |
| Unstoppable | This HARD level couldn't slow you down! | 막을 수 없는 | 이 어려움 레벨도 당신을 멈추지 못했어요! |
| Mastermind | A true display of genius on this HARD grid! | 두뇌 마스터 | 이 어려움 그리드에서 진정한 천재의 진면목! |
| Phenomenal | Making a HARD puzzle look like an absolute breeze! | 경이로움 | 어려운 퍼즐을 산책처럼 만들어 버리네요! |
| Exceptional | Flawless logic right from the very start! | 특별함 | 처음부터 완벽한 논리! |
| Mind-blowing | A flawless victory on such a complicated grid! | 어마어마함 | 이렇게 복잡한 그리드에서 완벽한 승리! |
| Spectacular | Hard difficulty? Not for a brilliant mind like yours! | 화려함 | 어려운 난도? 당신 같은 명석한 두뇌엔 문제없어요! |
| Supreme | You navigated this challenging puzzle perfectly! | 최고 | 이 도전적인 퍼즐을 완벽하게 풀어냈어요! |
| Unreal | Truly top-tier logic on display right here! | 비현실적 | 진정한 최상급 논리를 여기서 선보였네요! |
| Glorious | What a swift and flawless victory over a HARD level! | 영광 | 어려움 레벨에서 이 얼마나 빠르고 완벽한 승리인가! |

#### 결과 화면 — 하드 레벨 재시도 승리 (15쌍, 무작위 1쌍)

| 제목(영) | 본문(영) | 제목(한) | 본문(한) |
|---|---|---|---|
| Finally | A tough puzzle, but you cracked it! | 드디어 | 까다로운 퍼즐이었지만 결국 풀어냈어요! |
| Persistence | Took effort but HARD level is beaten! | 끈기 | 고생했지만 어려움 레벨을 정복했어요! |
| Already? | You needed fewer tries than most to solve this! | 벌써? | 대부분의 사람보다 적은 시도로 풀어냈어요! |
| Overcome | That HARD puzzle didn't stop you! | 역전 | 그 어려움 퍼즐도 당신을 막지 못했어요! |
| Solved | What a brain teaser! Finally you got it! | 해결 | 정말 머리 아픈 문제였죠! 그래도 결국 해냈어요! |
| Triumph | Your persistence on this HARD puzzle really paid off! | 승리 | 이 어려운 퍼즐에서 당신의 끈기가 빛을 발했어요! |
| Resilient | You kept trying and finally cracked the hard code! | 불굴 | 계속 시도해서 결국 어려운 코드를 깨뜨렸어요! |
| Victory | Hard mode conquered through pure determination! | 승리 | 순수한 결심으로 어려움 모드를 정복! |
| Relentless | You never gave up, and it totally paid off! | 굴하지 않는 | 당신은 결코 포기하지 않았고, 완벽히 보상받았어요! |
| Gotcha | It took some extra work, but the win is proudly yours! | 잡았다 | 조금 더 노력이 필요했지만, 승리는 당당히 당신의 것! |
| Champion | True champions push through the hardest puzzles! | 챔피언 | 진정한 챔피언은 가장 어려운 퍼즐을 뚫어냅니다! |
| Unbroken | Hard mode tested you, but you stood strong and won! | 굳건함 | 어려움 모드가 당신을 시험했지만, 굳게 서서 이겼어요! |
| Way to go | It took some time, but the HARD level is all yours! | 잘했어요 | 시간이 걸렸지만 어려움 레벨은 온전히 당신의 것! |
| Nailed It | The struggle makes this hard-earned win even sweeter! | 정확 | 고생 끝에 얻은 이 승리는 더욱 달콤합니다! |
| Success | You outsmarted a truly stubborn and tricky puzzle! | 성공 | 진짜 고집스럽고 까다로운 퍼즐을 지혜로 이겼어요! |

#### 승리 토스트 (PERFECT/P5/P10 만 실제 표시, P20 은 표시 안 함)

| 키 | 영어 | 한국어 |
|---|---|---|
| `WIN_TOAST_PERFECT_01` | Purrfect! [b]{N}[/b] steps. [b]{N}[/b] cats. Zero doubt. | 완벽냥! [b]{N}[/b]수, [b]{N}[/b]마리, 의심 제로. |
| `WIN_TOAST_PERFECT_02` | [b]Flawless![/b] Every step, a cat. No hesitation. | [b]무결점![/b] 모든 수가 고양이로. 망설임 없이. |
| `WIN_TOAST_PERFECT_03` | Solved in [b]{N}[/b] moves. Exactly [b]{N}[/b] cats. | [b]{N}[/b]수로 클리어. 정확히 [b]{N}[/b]마리. |
| `WIN_TOAST_PERFECT_04` | Pure logic. No hesitation. | 순수한 논리. 망설임 없이. |
| `WIN_TOAST_PERFECT_05` | [b]Immaculate![/b] [b]{N}[/b] cats. [b]{N}[/b] moves. Not one wasted. | [b]완벽 그 자체![/b] 고양이 [b]{N}[/b]마리, [b]{N}[/b]수, 낭비 하나 없이. |
| `WIN_TOAST_PERFECT_06` | Every move was the only move. | 모든 수가 유일한 정답이었어요. |
| `WIN_TOAST_PERFECT_07` | [b]{N}[/b] for [b]{N}[/b]. As clean as it gets. | [b]{N}[/b]수에 [b]{N}[/b]마리. 이보다 깔끔할 순 없죠. |
| `WIN_TOAST_PERFECT_08` | No guessing. Just knowing. | 추측은 없었어요. 오직 확신뿐. |
| `WIN_TOAST_PERFECT_09` | The cats never stood a chance. | 고양이들은 애초에 승산이 없었어요. |
| `WIN_TOAST_P5_01` | So close to perfect. Nicely done. | 완벽에 아주 가까웠어요. 훌륭해요! |
| `WIN_TOAST_P5_02` | Clean solve. Just a step or two to spare. | 깔끔한 해결. 겨우 한두 수 차이예요. |
| `WIN_TOAST_P5_03` | Sharp thinking. Almost flawless. | 예리한 사고. 거의 완벽했어요. |
| `WIN_TOAST_P5_04` | Efficient and elegant. | 효율적이고 우아하게. |
| `WIN_TOAST_P5_05` | Nearly purrfect. Keep sharpening. | 거의 완벽냥. 계속 갈고닦아요. |
| `WIN_TOAST_P5_06` | Almost flawless — can you do it in [b]{CATS}[/b] next time? | 거의 완벽했어요 — 다음엔 [b]{CATS}[/b]수로 해볼래요? |
| `WIN_TOAST_P5_07` | The cats barely had time to hide. | 고양이들이 숨을 틈도 없었어요. |
| `WIN_TOAST_P10_01` | Top [b]10%[/b] today. The cats felt it. | 오늘 상위 [b]10%[/b]. 고양이들도 느꼈어요. |
| `WIN_TOAST_P10_02` | Faster than most. Well played. | 대부분보다 빨랐어요. 훌륭해요! |
| `WIN_TOAST_P10_03` | Sharp solve. Better than 9 in 10. | 예리한 해법. 열 명 중 아홉보다 낫습니다. |
| `WIN_TOAST_P10_04` | Above the pack. Nicely done. | 평균을 훌쩍 넘었어요. 잘했어요. |
| `WIN_TOAST_P10_05` | Clean game. Almost elite. | 깔끔한 한 판. 엘리트가 눈앞이에요. |
| `WIN_TOAST_P10_06` | The cats didn't make it easy. You made it look easy. | 고양이들은 쉽게 봐주지 않았는데, 당신은 쉬워 보이게 했어요. |
| `WIN_TOAST_P10_07` | One step closer to the top. | 정점에 한 걸음 더 가까워졌어요. |
| `WIN_TOAST_P20_01` | Solid solve. Better than most. | 안정적인 해결. 대부분보다 낫습니다. |
| `WIN_TOAST_P20_02` | Nice work. Above average and climbing. | 잘했어요. 평균 이상, 계속 상승 중. |
| `WIN_TOAST_P20_03` | Good moves. The cats didn't have it easy. | 좋은 수였어요. 고양이들도 힘들었죠. |
| `WIN_TOAST_P20_04` | Well played. You're getting sharper. | 훌륭해요. 점점 예리해지고 있어요. |
| `WIN_TOAST_P20_05` | Top [b]20%[/b] — the top 10% is closer than you think. | 상위 [b]20%[/b] — 상위 10%는 생각보다 가까워요. |
| `WIN_TOAST_P20_06` | Good game. Keep tightening. | 좋은 한 판. 계속 조여봐요. |
| `WIN_TOAST_P20_07` | Above average. Nice moves. | 평균 이상. 멋진 수였어요. |

#### 실패 화면 (대조군)

| 키 | 영어 | 한국어 |
|---|---|---|
| `FAIL_TITLE_FISH` | Out of Fishes | 멸치 소진 |
| `FAIL_REVIVE_3FISH` | Get 3 Fishes | 멸치 3개 받기 |
| `FAIL_REVIVE_NFISH` | Get %d Fishes | 멸치 %d개 받기 |
| `FAIL_REMAINING_CAT` | Remaining:  | 남음:  |
| `FAIL_TITLE_GOLDEN_FISH` | Out of Fish | 멸치 소진 |
| `FAIL_REVIVE_1FISH` | Get 1 Fish | 멸치 1개 받기 |

#### 실패 화면 격려 문구 (fail_text 실험군 전용 — 대조군 미표시)

| 키 | 영어 | 한국어 |
|---|---|---|
| `FAIL_ENC_LOW_1` | You can do this! | 당신은 할 수 있어요! |
| `FAIL_ENC_LOW_2` | Let's Try Again! | 다시 도전해 봐요! |
| `FAIL_ENC_LOW_3` | Jump right back in! | 바로 다시 시작해요! |
| `FAIL_ENC_LOW_4` | The search continues! | 탐색은 계속됩니다! |
| `FAIL_ENC_MID_1` | Great effort! | 훌륭한 시도였어요! |
| `FAIL_ENC_MID_2` | Don't give up now! | 지금 포기하지 마요! |
| `FAIL_ENC_MID_3` | Nice try! A few more to go! | 좋아요! 몇 마리만 더! |
| `FAIL_ENC_MID_4` | Keep it up, you're on the right track! | 잘하고 있어요, 방향이 맞아요! |
| `FAIL_ENC_HIGH_1` | Almost there! | 거의 다 왔어요! |
| `FAIL_ENC_HIGH_2` | The victory is in sight! | 승리가 눈앞이에요! |
| `FAIL_ENC_HIGH_3` | Just one more effort! | 조금만 더 힘내요! |
| `FAIL_ENC_HIGH_4` | You almost caught them all! | 거의 다 잡았어요! |
| `FAIL_REVIVE_PROMOTE` | [center][font_size=70][b][color=#FFCC00]%s[/color][/b][/font_size] of players used Revive to pass this level![/center] | [center]플레이어 [font_size=70][b][color=#FFCC00]%s[/color][/b][/font_size]가 부활로 이 레벨을 클리어했어요![/center] |

#### barrage 문구 풀 (전체 8종)

| 키 | 영어 | 한국어 |
|---|---|---|
| `GAME_PAGE_BULLET_1` | %d players have cleared this level today!{2} | 오늘 %d명의 플레이어가 이 레벨을 클리어했어요!{2} |
| `GAME_PAGE_BULLET_2` | You're playing together with %d players right now!{3} | 지금 %d명의 플레이어가 당신과 함께 플레이 중이에요!{3} |
| `GAME_PAGE_BULLET_3` | Players from %d countries are online right now!{4} | 지금 %d개국의 플레이어가 온라인이에요!{4} |
| `GAME_PAGE_BULLET_4` | Over 1 million hard levels solved in the last 24 hours!{5} | 지난 24시간 동안 100만 개 이상의 어려운 레벨이 풀렸어요!{5} |
| `GAME_PAGE_BULLET_DAILY_1` | {name} took %d minutes, but still cleared this level!{2} | {name}님은 %d분 걸렸지만 끝내 이 레벨을 클리어했어요!{2} |
| `GAME_PAGE_BULLET_DAILY_2` | {name} cleared this level in just %d seconds!{3} | {name}님은 단 %d초 만에 이 레벨을 클리어했어요!{3} |
| `GAME_PAGE_BULLET_DAILY_3` | {name} is now the highest level player today!{4} | {name}님이 오늘의 최고 레벨 플레이어예요!{4} |
| `GAME_PAGE_BULLET_DAILY_4` | Fastest clear today: %d seconds!{5} | 오늘의 최단 클리어: %d초!{5} |

#### 기타 (자동 X 배너 · 하드 태그)

| 키 | 영어 | 한국어 |
|---|---|---|
| `WIN_X_FREE_BONUS` | ✕-FREE BONUS! | ✕ 제로 보너스! |
| `GAME_HARD_TAG` | Hard | 어려움 |
| `GAME_HEADER_HARD` | (번역표에 키 이름 없음) |  |

---

## 추가 Q1. 프리필이 있는 판의 승리 등급 판정

**결론: 프리필 수를 빼거나 더하지 않는다. 걸음 수(사용자 입력만)를 판 크기 N 과 그대로 비교한다.**

- 프리필 고양이는 출처 PREFILL 로 보드에 직접 놓인다. 걸음 수를 올리는 경로(제스처 종료·도구)를 거치지 않으므로 **걸음 수 0** 이다.
- 판정은 1.2절 그대로다.
  - 걸음 < N → 등급 없음
  - 걸음 = N → PERFECT
  - 걸음 ≤ p5/p10/p20 → P5/P10/P20
  - 임계값 표도 보정 없이 같은 표를 쓴다.
- 따라서 1~10레벨(프리필 1칸)에서는 아래처럼 판정이 뒤집힌다.
  | 플레이 | 걸음 | 판정 |
  |---|---|---|
  | 정답 고양이만 N−1번 놓음(실제 최선) | N−1 | **등급 없음**(토스트 없음) |
  | 한 걸음 더 씀(X 1회 등) | N | **PERFECT** |
  | 그 이상 | N+1 이후 | P5/P10/P20 비교는 원래 표 그대로 |
- 해당 레벨: 판 크기 4·5(1·2레벨)는 원래 표에 없어 등급이 없다. 나머지 3~10레벨(크기 6,6,8,6,7,8,9,7)에 위 현상이 생긴다.
- 21레벨 이후 pre-cat(사전 배치 1마리)도 같은 경로(프리필 위치)로 놓이므로, pre-cat 이 들어간 판도 같다.
- 참고(걸음 수 초기화):
  - 새 레벨 시작·재시작: 0
  - 부활 후 이어하기: 유지
  - 앱을 껐다가 이어하기: 저장된 값 복원
  - 이어하기로 복원되는 고양이·표시도 걸음 수에 들어가지 않는다.
- 결과 화면(6절 V3_G1)의 PERFECT 풀은 걸음 수가 아니라 "실수 0 + 재시작·부활 없음"으로 고르므로, 프리필 판에서도 정상적으로 나온다.
