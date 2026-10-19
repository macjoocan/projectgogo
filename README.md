# levelscope — 게임 데이터 추출·분석·검증 도구와 사례 노하우

APK/XAPK/OBB/폴더에서 게임 데이터와 리소스를 찾아 디코딩하고, 산출물을 자동 생성합니다.
**장르를 가리지 않습니다** — 퍼즐·매치3뿐 아니라 RPG·방치형·슈터의 데이터 테이블도 같은
경로로 뽑습니다. 보드 그리드를 그리는 HTML 뷰어만 보드형 게임 전용입니다.

Unity 모바일 게임을 위한 공통 CLI를 중심으로, PC 게임·ECS·셰이더·모션을 분석하며 작성한
연구 스크립트와 실패·검증 노하우도 보존합니다. **사례 연구에서 판독한 기능이 모두 공통 CLI에
자동 통합된 것은 아닙니다.** 게임별 추가 판독과 입력 의존성은 각 문서를 확인하세요.

## 최신 성과와 진입점 — 2026-10-16

| 영역 | 현재 제공하는 것 | 시작 문서 |
|---|---|---|
| APK 언패킹·데이터 추출 | APK/XAPK/split/OBB/PAD·Addressables 탐색, 코덱 체인, FlatBuffers·FibMatrix, 레벨/설정/리소스/계층 출력 | [전체 작업 순서](GUIDE.md), [명령 매뉴얼](MANUAL.md) |
| 언패킹·분석 노하우 | 원본 식별, PPtr·64bit ID, native TypeTree/IL2CPP 폴백, 소비 코드 추적, 프로세스 메모리 감시, 실패/정정 기록 | [공통 노하우](ANALYSIS_KNOWHOW.md), [전체 추출 이력](EXTRACTION_HISTORY.md) |
| APK·미니앱 이식 사례 | Royal Smash/MiniApp의 런타임 배치·물리·시스템·UI, Goods Hunt의 trigger·성장·목표·FX, DKBI ECS·셰이더 및 기타 사례 | [최신 사례 요약](docs/APK_MINIAPP_KNOWHOW_20261016.md), [원문 전체 색인](docs/REFERENCE_CASES_ALL.md) |
| 사례 재현 코드 | 직접 작성한 분석·참조 연결·검사 Python 스크립트113개, UEViewer scale/sidecar/export-index 소스 변경 패치 | [연구 코드와 실행 주의](tools/case_studies/README.md) |
| 선택형 코드 분석 | REA 기반 JS/managed/native 정적 분석 및 저장 결과 요약·비교 | [REA 사용법과 검증 범위](tools/REA_INTEGRATION.md) |
| 모션 보정 | 독립 Blender Motion Remap0.2: 본 매핑·참조 자세·루트·2본 IK·접지·골반·명시 컨트롤 프로필·평가 스킨 export | [사용법](tools/motion_remap/README.md), [모션 노하우](docs/MOTION_REMAP_KNOWHOW.md) |

원문 설명160건과 연구 스크립트는 기존 작업의 출처·한계를 보존한 자료입니다.
연구 스크립트 일부는 로컬 경로를 사용하거나 import 때 실행하므로 먼저 읽고 독립 입력/출력으로
실행해야 합니다. **게임 리소스·추출 테이블·원본 바이너리·Blend/GLB·이미지·음원은 저장소에 포함하지 않습니다.**

현재 검증: Python 전체 **556개 실행, 3개 건너뜀, 실패0**. 게시한 사례 스크립트113개는
Python 문법 검사, UEViewer 변경 패치는 기준 소스에 `git apply --check`를 통과했습니다.
원작 전체 재추출이나 모든 게임의 플레이·GPU 정합성을 새로 검증한 결과는 아닙니다.

현재 미해결인 생성 캐릭터 손바닥·어깨 보정은 [독립 연구 상태](docs/MULTI_SKINNING_RESUME_20261016.md)에
분리했습니다. 실패 후보5개는 미채택이며, Blend 원본 커브 보존을 GLB native 시간키 보존으로
확대하지 않습니다. 원작 서버 규칙·실행 화면 동등성도 데이터 추출 성공과 별개입니다.

후속 [v4 가중치 분리 검사](docs/MULTI_HAND_V4_FOLLOWUP_20261016.md)도 최대 늘어남은 개선됐지만
Idle의 국소 면적 붕괴가 악화돼 미채택했습니다. native5 Action의 저장·재열기 검증 노하우와
실패 원인을 함께 보존합니다.

[표정 export 후속 노하우](docs/MULTI_EXPRESSION_EXPORT_KNOWHOW_20261016.md)에는
COLOR 채널·alpha 설정과 기본 Scene 재열기 검사를 추가했습니다. 담당 세션의 표정 구현/QA와
이 저장소 세션의 읽기 전용 파일 확인을 구분하며, 최종 사람 승인은 아직입니다.

**2026-10-19 사람 피드백:** 기존 얼굴 선호를 반영해 Multi 기본을 OriginalRetry 얼굴로 복원했고,
표정 후보는 revise·비교 기본 OFF입니다. [최신 상태와 검사 범위](docs/MULTI_FACE_FEEDBACK_20261019.md)를
참고하세요. 기존 모델/모션을 변경하거나 새 생성·독립 실험을 시작한 것은 아닙니다.

## 빠른 시작

처음 보는 게임을 처음부터 끝까지 뜯는 순서는 **[GUIDE.md](GUIDE.md)** 에 있습니다 —
어떤 명령을 어떤 순서로, 무엇을 확인하고, 어디서 막히는지까지.

**처음 보는 게임이면 `survey` 부터.** 설정 없이 APK를 던지면 뭐가 어디 있는지 보고하고
설정 초안까지 만들어 줍니다. 그리고 설정에 `fields: auto` 한 줄만 두면 표본에서 컬럼을
자동으로 뽑으므로, 필드 경로를 손으로 적지 않고 바로 표를 볼 수 있습니다.

```bat
py -m levelscope survey --input <아무 apk> --configs configs
```

| 산출물 | 내용 |
|---|---|
| `<게임>_summary.xlsx` | Levels 시트(레벨별 전 컬럼) + Shooters 등 엔티티 시트 + Summary(세트/난이도/기믹 집계, 수식) |
| `<게임>_viewer.html` | 보드 픽셀아트 렌더 + 스테이지 카드 + 상세 모달. 단일 파일, 오프라인 동작 |
| `<게임>_levels_decoded.zip` | 디코딩 평문 JSON 원문 (`levels/<세트>/<번호>.json`) + palette.json |
| `<게임>_sprites.zip` | 스프라이트·텍스처 PNG |
| `<게임>_assets.zip` | 사운드(WAV) · 머티리얼(JSON) · 폰트(TTF/OTF) · Spine(.atlas/.skel) · 텍스트 + manifest.json |
| `<게임>_hierarchy.zip` | 씬·프리팹 GameObject 트리 JSON (컴포넌트 필드 값 포함) + index.json |
| `<게임>_errors.txt` | 실패가 있을 때만 — 파일별 사유 |

## 설치 (Windows)

```bat
py -m pip install -r requirements.txt
```

UnityPy는 Unity 에셋에서 레벨·팔레트·스프라이트를 꺼낼 때 필요합니다.
`detect` / `ls` 는 pandas·openpyxl·PyYAML 없이도 동작합니다.

`hierarchy`의 컴포넌트 필드는 원본 native TypeTree가 있으면 이를 우선 사용합니다.
필드 구조가 없는 IL2CPP 빌드는 `TypeTreeGeneratorAPI`와 .NET 8+ 등 추가 백엔드가 필요할 수
있습니다. 복원할 수 없는 필드는 누락/실패로 구분하며 이름·타입만 있는 결과를 전체 필드 복원이라
판정하지 않습니다.

## 실행

```bat
:: PixelFlow — XAPK 해제 폴더나 apk 파일 아무거나 지정 가능
py -m levelscope run --config configs\pixelflow.yaml --input "D:\99.기타\xapk_unpacked" --out out

:: Zen Match — 레벨이 data.unity3d 안 TextAsset인 게임
py -m levelscope run --config configs\zenmatch.yaml --input "D:\99.기타\AAA.xapk" --out out

:: 새 게임: 내부 경로 훑기 → 인코딩 감지 → 샘플 구조 확인
py -m levelscope ls      --input <apk경로>
py -m levelscope detect  --input <apk경로>              :: 암호화 의심 시 --xor-scan
py -m levelscope inspect --config configs\mygame.yaml --input <apk경로>
:: 헤더에 Unity 버전이 없는 단일 번들이면 --unity-version 2019.4.41f1

:: FibMatrix Meta.bytes 게임 — 테이블별 JSON/raw zip
py tools\decode_fibmatrix.py --input <apk경로> --out out\meta_decoded.zip

:: 레벨과 무관한 리소스는 설정 없이도 바로 뽑을 수 있습니다
:: (--source 기본값 auto = Addressables 번들까지 자동 발견)
py -m levelscope assets    --input <apk경로> --out out   :: 사운드·머티리얼·폰트·Spine·텍스트
py -m levelscope hierarchy --input <apk경로> --out out   :: 씬·프리팹 계층
```

대화형 분석 진입점은 `analyze.bat` 또는 `분석하기.bat`입니다.
새 설정을 시험할 때는 `--limit 20` 을 붙여 앞 20개만 먼저 돌려보세요.

## 입력

apk · xapk · obb · zip 파일과 압축 해제 폴더를 모두 받습니다. XAPK를 주면 내부
**base.apk · split apk · `Android/obb/*.obb`** 까지 훑어 레벨이 있는 곳을 자동으로
고릅니다. 레벨이 여러 컨테이너에 나뉘어 있으면 `input.merge_containers: true`.

## 디코딩

`codec: auto`로 두면 인코딩 체인을 자동 감지합니다 (gzip/zlib/bz2/xz/zstd/lz4/brotli,
base64·base64url·hex, `xxx:` 접두어, UTF-16, msgpack, FibMatrix, 중첩 깊이 8).
명시 체인도 지원합니다.

레벨이 **FlatBuffers 바이너리**인 게임은 `codec: [flatbuffers]` 를 씁니다. `.fbs` 스키마
없이도 구조를 복원하며(필드명은 슬롯 번호), 표본 전체로 슬롯 타입을 확정합니다.
`configs/royalkingdom.yaml` 참고.

암호화된 레벨은 `detect --xor-scan` 이 반복키 XOR 키 복구를 시도하고, 실패하면
엔트로피·반복키 길이 진단을 보여줍니다. AES는 키를 확보해
`aes_cbc:<hexkey>:<hexiv>` 로 지정하세요. 전체 스텝 목록은 `MANUAL.md` 3장.

## 새 게임 붙이기

0. **`survey --input <apk> --configs configs`** — 엔진·백엔드·리소스 규모·레벨 후보를
   보고하고 `configs/_suggested_<게임>.yaml` 초안을 만듭니다. 레벨이 Unity 에셋인
   게임과 파일인 게임을 구분해 `input` 블록 모양을 맞춰 줍니다.
1. `ls` 로 내부 경로 확인 → `detect` 로 인코딩 파악 (초안이 이미 채워 두지만 확인용)
2. `inspect` 로 레벨 구조를 보면서 채우기:
   - `input.levels_glob`(파일형) 또는 `input.unity`(Unity 에셋형)
   - `codec` — `auto` 또는 명시 체인
   - `fields.scalars` / `fields.counts` — 컬럼 정의 (점 경로, `.*`=래퍼 안의 유일한 리스트)
   - `board` — 그리드가 있으면 정의 (HTML 렌더용), 없으면 삭제
   - `palette` — static hex 목록 또는 unity 자동 추출
3. 슈터 대기열처럼 게임 고유 구조는 `levelscope/plugins/<게임>.py` 작성
   (`pixelflow.py` 참고). 플러그인 없이도 기본 산출물은 모두 나옵니다.

자세한 내용: **MANUAL.md**(전체 매뉴얼) · **CLAUDE.md**(Claude Code용 지침) ·
**CHANGELOG.md**(버전 이력)

## 구조

```
levelscope/          파이프라인 코어
  container.py       입력 추상화 (폴더/zip/apk/xapk/obb/중첩 apk)
  discover.py        Unity 소스 자동 발견 (Addressables 번들 포함)
  survey.py          APK 프로파일 + 설정 초안   catalog.py  Addressables 카탈로그 해독
  unity.py           UnityPy 공통 헬퍼 + ObjectIndex(PPtr 해석)
  decode.py          코덱 체인 + 자동 감지   xorscan.py  XOR 키 복구·진단
  extract.py         레벨 수집             schema.py   점 경로 매핑
  palette.py         팔레트               sprites.py  스프라이트/텍스처
  assets.py          사운드·머티리얼·폰트·Spine·텍스트
  hierarchy.py       씬·프리팹 계층        typetree.py IL2CPP MonoBehaviour 복원
  report_xlsx.py     xlsx                viewer.py   HTML 뷰어
  cli.py             run/inspect/detect/ls/survey/sprites/assets/hierarchy
  flatbuf.py         스키마 없는 FlatBuffers 해독 (codec: flatbuffers)
  fibmatrix.py       FibMatrix Meta.bytes 설정 테이블 해독
  plugins/           게임 플러그인 (pixelflow, zenmatch, sheepnsheep, royalkingdom)
plugins/             프로젝트 전용 확장 자리
configs/             게임 설정 + template.yaml + icons/<게임>/
tests/               회귀 테스트 — python -m unittest discover -s tests -t .
tools/               verify_baseline.py · decode_fibmatrix.py · rea_bridge.py
  motion_remap/      독립 Blender 모션 보정 도구와 검증 코드
  case_studies/      입력 의존적인 사례 연구 코드·검사·파서 변경 패치
docs/                최신 노하우·사례 원문 색인·DKBI/모션 연구 인계
```

## 초기 추출 기준치 — 4종 baseline 보존

아래는 해당 버전/당시 입력의 기준치입니다. 최신 사례 전체 지원 범위는 상단의
[전체 추출 이력](EXTRACTION_HISTORY.md)과 [원문 색인](docs/REFERENCE_CASES_ALL.md)을 확인하세요.

레벨 파이프라인:

- PixelFlow (v0.31.3): 레벨 2,384 · 8세트 · 메인 2,100 · 실패 0 · 팔레트 34색 · Shooters 160,313행
- Zen Match (v220000.1.762): TextAsset 4,502 (main 4,493 + variant 9) · 실패 0 · 스프라이트 79
- SheepNSheep (v1.9.2): 에셋 8개 → 스테이지 87 / 맵 40 · 실패 0 · 스프라이트 37

리소스·계층 (v1.7.0 신규):

| | SheepNSheep | Zen Match |
|---|---|---|
| Unity | 2021.3.42f1 | 2022.3.62f2 |
| assets | 109개 (오디오 12 · 머티리얼 34 · 폰트 6 · Spine 30 · 텍스트 27), 실패 0 | 565개 (오디오 103 · 머티리얼 427 · 폰트 11 · Spine 24), 실패 0 |
| 씬 / 프리팹 / 노드 | 2 / 57 / 1,196 | 3 / 1,013 / 36,143 |
| MonoBehaviour 필드 복원 | 1,625/1,625 (100%) | 29,845/30,209 (98.8%) |

자동 발견·survey (v1.8.0 신규):

| | SheepNSheep | Zen Match | PixelFlow |
|---|---|---|---|
| Unity 소스 자동 발견 | 2개 | 16개 (Addressables 14 포함) | 24개 |
| Addressables 카탈로그 | 없음 | 번들 389 · **375개 원격(CDN)** | `catalog.bin` — 매핑 불가 |
| 레벨 후보 자동 판정 | 에셋형 `newMapLv[0-9]+\|PvpMap\|…` | 에셋형 `Level_[0-9]+` ×377 | 파일형 `assets/Levels/*/*.json` ×2,384 |
| 초안 codec 추정 | `auto` (혼합 감지) | `["json"]` | `["prefix:gzip:","base64","gunzip","json"]` |

Royal Kingdom (`gg.com.dreamgames.royalkingdom`, v1.9.0에서 추가 검증):

| 항목 | 값 |
|---|---|
| 구조 | APKS 래퍼 + Play Asset Delivery · 확장자 없는 번들 114개 |
| 자동 발견 소스 | 117개 |
| 리소스 추출 | 1,989개 (오디오 941 · 머티리얼 913 · Spine 134), 실패 0 |
| 씬 / 프리팹 / 노드 | 3 / 1,262 / 35,867 |
| 컴포넌트 필드 복원 | 10,110/10,158 (99.5%) |
| 레벨 데이터 | `[0-9]+` ×4,500 — **FlatBuffers, v1.10.0에서 복원 완료** |
| 레벨 복원 | 4,500개 · 보드 정합성(셀수=가로×세로) 4,500/4,500 · 실패 0 |
| 기믹 이름 | `TiledId` 열거형 복원 — 쓰인 178종 전부 이름 확정(미상 0) |
| 뷰어 | 게임 원본 기믹 이미지로 렌더 (아이콘 113종, 셀 커버리지 92.7%) |

세 게임 모두 초안이 사람이 쓴 설정과 일치했고, PixelFlow는 생성된 초안을 **손대지 않고**
돌려 레벨 2,384개를 찾아 30개 디코딩(실패 0)에 성공했습니다.

- 이 초기 기준치 기록 당시 합성 회귀 테스트347개. 현재 전체 실행 결과는 상단의556개 검사입니다.
- xlsx의 Summary 수식은 Excel에서 열 때 자동 계산됩니다.
- `hierarchy` 실행 중 `Error generating tree nodes: Sequence contains no matching element`
  가 콘솔에 섞여 나올 수 있습니다. TypeTreeGeneratorAPI 내부 DLL이 찾지 못한 클래스에
  대해 직접 출력하는 메시지입니다. 다음 백엔드 폴백이 성공했는지 확인하고, 실행 끝의
  `[typetree]` 복원율과 실제 누락 목록을 판정 기준으로 사용합니다.


## 선택형 코드 분석 연동

REA 정적 분석 어댑터의 설치·명령·검증 범위는 [REA_INTEGRATION.md](tools/REA_INTEGRATION.md)에 정리했다.
`python tools/rea_bridge.py capabilities`는 계획을 출력하고 `--execute`로 실행한다.
게임 에셋 추출과 별도 경로이며 IL2CPP 복원이나 원작 화면 동등성을 자동 보장하지 않는다.
