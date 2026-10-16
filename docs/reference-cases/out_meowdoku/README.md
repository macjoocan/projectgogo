# Meowdoku 1.20.0 추출 결과

- 패키지: `com.oakever.meowdoku` · 입력 `~\Downloads\Meowdoku_+Brain+Puzzle+Games_1.20.0_APKPure.xapk`(302MB)
- 엔진: **Godot 4.3 이상**(`libgodot_android.so`, GDScript 바이트코드 GDSC v101). Unity가 아니어서 levelscope 범위 밖이고, 직접 풀었다
- 콘텐츠는 Play Asset Delivery 팩 `assetPackInstallTime.apk`에 프로젝트 파일이 낱개로 들어 있다(.pck 아님)
- 장르: Queens 계열 논리 퍼즐. N×N 판을 N개 영역으로 나누고 행·열·영역마다 고양이 1마리를 놓는다
- 추출일: 2026-10-16

## 레벨 (핵심)
- `assets/resources/levels/*.json` 58개. 확장자는 .json 이지만 **반복 XOR(25바이트 키)로 난독화**돼 있다
- 키는 문서에 적지 않는다. 복호화 스크립트가 58개 파일의 열별 바이트 빈도로 매번 복원한다(일치도 100%)
- **레벨 47,687개 · 뱅크 37개** (.pace.json 21개는 힌트·진행 속도 보조 데이터)
- 판 크기: 4×4~12×12 (8·9·10 이 대부분)
- 난이도 r(필요한 최고 풀이 기법 1~5): r1 1,039 · r2 5,253 · r3 14,191 · r4 20,756 · r5 6,242
- 레벨 필드: `regionMap`(N×N 영역 번호), `solution`(행별 정답 열), `r`, `steps`(풀이 단계), `r1~r5`(기법별 단계 수), `rating`, `seed` 등
- pace 필드: `r_seq`(단계별 기법), `hint_click_seq`, `g1~g4`
- 주요 뱅크: 일반 bankData4x4~12x12 · GC · LKStyle · OneFish · SingleRegion(6,196) · ClimaxFilters(6,000, 개발 메모 포함) · ColorChallenge(1,801) · HardR4(3,000) · SuperHard(11×11 275개, 평균 47단계) · SP/DigitsSP
- `bankDataLK`: 날짜가 붙은 일일 퍼즐 169개(2024/09/28~2025/04/18, 라벨 R1 Beginner~R5 Expert)

## 파일
| 경로 | 내용 |
|---|---|
| `Meowdoku_levels_summary.xlsx` | Banks(뱅크별 개수·크기·평균 r·단계) · r분포(뱅크별) · Levels(47,687행, pace 결합) |
| `levels_decoded/` | 복호화한 레벨 JSON 58개(원본 구조 그대로) |
| `textures/` | 텍스처 641장 PNG (WebP 320 · ETC2 RGBA 310 · ASTC 9 · ETC2 RGB 2, 실패 0) |
| `audio/` | 효과음·BGM 61개 .ogg (Godot 패킷 시퀀스를 Ogg 페이지로 재포장, ffmpeg 디코드 오류 0) |
| `spine/` | Spine 4.2.43 스켈레톤(.skel) 30 + 아틀라스(.atlas) 28 — 짝이 되는 PNG 는 textures/ 에 있다 |
| `raw/` | 에셋 팩 원본 전체(4,199개) |
| `scripts_src/` | 디컴파일한 GDScript 917개(.gd) |
| `fonts/` | 폰트 13개 원본(TTF/OTF, FreeType 로딩 확인) |
| `translations/` | 번역 75개 언어 × 2,686문장: `Meowdoku_translations.xlsx/.csv`(언어별 열) + 언어별 JSON. 키 이름 1,358개 복원, 나머지는 `#버킷:번호` |
| `Meowdoku_레벨진행_AB테스트.md` | 레벨 진행 구조와 A/B 테스트 정리 문서 |
| `ab_configs.csv` · `normal_level_groups.csv` · `normal_level_strategies.csv` | A/B 설정 160개 · normal_level 값 108개 대응 · 전략 87개 차이 |

## 스크립트 (디컴파일 완료)
- `scripts_src/` — GDScript 917개 전부 소스로 복원(코드 약 13.6만 줄, 바이트 끝까지 소비 917/917)
- 형식: Godot **4.6.1**, GDSC v101 = zstd 압축 토큰 버퍼. 토큰 이름 표 100개는 `libgodot_android.so` 의 token_names 배열(재배치 정보)에서 읽었다
- 토큰마다 원래 줄 번호가 있어 **줄 번호가 원본과 같다**. 주석은 바이너리에 없어서 빈 줄로 남는다
- 도구: `tools/gdc_decomp.py <원본폴더> <출력폴더>` (zstandard 필요 — levelscope .venv 에 설치함)

## 레벨 진행 규칙 (대조군 normal_level=0, 디컴파일 기준)
엑셀 `진행규칙(대조군 1-300)` 시트에 레벨별로 풀어 두었다.
- 선택 흐름: `LevelSelector.select` → A/B 값으로 전략 결정(`LevelSelectionStrategyResolver`, 실험 값 90여 개 → 전략 클래스 40여 개). 미배정 사용자는 `NLControlStrategy`
- 판 크기: 1~10레벨 = 4,5,6,6,8,6,7,8,9,7 / 11레벨부터 10판 주기 8,10,10,9,10,10,9,10,10,10
- 하드 레벨: 21 이상이면서 10의 배수 → r5 고정
- 특수 레벨(뱅크 고정): 10·20·30·40·50·55·60·62·70·75·80·90·100·123·456 = SP 뱅크, 200·250·314 = LK 뱅크
- 난이도(전략) 상한: 1~5레벨 1 고정 / ~20 ≤2 / 21~50 ≤3 / 51+ 2~4. 전략 3 이상이면 2~상한에서 무작위
- 동적 난이도(DDA, 6레벨부터): 연속 클린 승리 2판(51+는 1판)마다 +1, 연속 실패 2판(20 이하는 1판)이면 −1, 재도전·부활 사용 승리도 −1. 하한 1(101+는 2)
  - "클린"을 깨는 행동: 힌트 · 위치 찾기 · 메모(draft) · 마우스 도구 · 설정 기어
  - DDA 상한은 101+ 5, 201+ 6까지 오르지만 대조군 일반 판 선택기는 51+에서 4로 자른다
- 51레벨부터 메인 경로: 마지막 LK 계열 이후 4판마다 LinkedIn 변형 퍼즐(lk_mod) 1판 삽입. 그 외에는 일반 → LKStyle → GC 순서. 8가지 대칭 변환으로 재활용
- 후보 검사: 단일 칸 영역 수 상한, 같은 퍼즐(동형 포함) 중복 제거. 후보가 없으면 7단계로 완화(같은 등급 → 낮은 등급 → 높은 등급)
- 1~10레벨은 정답 1칸을 미리 채워 준다(7레벨부터는 1칸짜리 영역을 우선)
- 서버 추천: 일부 실험군(`is_server_rec_active`)은 서버에서 레벨을 받아 큐로 쓴다(`level_rec_manager.gd`, 20레벨 전에는 요청 안 함)

## 폰트·번역
- 폰트: RSCC(블록 zstd) 해제 → 리소스 안 바이트 배열(태그 31)에서 원본 추출. 13/13
- 번역: OptimizedTranslation = 해시 표 + 버킷 표 + smaz 압축 문자열. smaz 코드북 254개는 `libgodot_android.so` 에서 읽었다
  - 키 원문은 해시로만 남는다. 스크립트·리소스 문자열 후보와 숫자 변형을 같은 해시(FNV 계열)로 대조해 1,358/2,686개 키를 되찾았다
  - 75개 언어 모두 키 배치가 영어와 같아 행 단위로 맞췄다

## 못 푼 것
- 씬(.scn) 226개: Godot 바이너리 씬이라 이번엔 제외했다
- 번역 키 이름 1,328개: 코드에서 문자열을 조합해 만드는 키라 후보에 없었다(문장은 모두 있음)
