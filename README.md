# levelscope — 모바일 게임 데이터 추출·요약·시각화 파이프라인

APK/XAPK/OBB/폴더에서 게임 데이터와 리소스를 찾아 디코딩하고, 산출물을 자동 생성합니다.
**장르를 가리지 않습니다** — 퍼즐·매치3뿐 아니라 RPG·방치형·슈터의 데이터 테이블도 같은
경로로 뽑습니다. 보드 그리드를 그리는 HTML 뷰어만 보드형 게임 전용입니다.

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

`hierarchy` 의 컴포넌트 **필드 값**에는 `TypeTreeGeneratorAPI` 와 .NET 8+ 런타임이
추가로 필요합니다 (IL2CPP 빌드는 스크립트 필드 구조를 번들에 담지 않기 때문).
없어도 실행은 되며, 이름·타입까지만 나오고 필드는 `null` 로 남습니다.

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

:: 레벨과 무관한 리소스는 설정 없이도 바로 뽑을 수 있습니다
:: (--source 기본값 auto = Addressables 번들까지 자동 발견)
py -m levelscope assets    --input <apk경로> --out out   :: 사운드·머티리얼·폰트·Spine·텍스트
py -m levelscope hierarchy --input <apk경로> --out out   :: 씬·프리팹 계층
```

`run_pixelflow.bat` 더블클릭으로도 실행됩니다(입력 경로는 bat 파일 안에서 수정).
새 설정을 시험할 때는 `--limit 20` 을 붙여 앞 20개만 먼저 돌려보세요.

## 입력

apk · xapk · obb · zip 파일과 압축 해제 폴더를 모두 받습니다. XAPK를 주면 내부
**base.apk · split apk · `Android/obb/*.obb`** 까지 훑어 레벨이 있는 곳을 자동으로
고릅니다. 레벨이 여러 컨테이너에 나뉘어 있으면 `input.merge_containers: true`.

## 디코딩

`codec: auto`로 두면 인코딩 체인을 자동 감지합니다 (gzip/zlib/bz2/xz/zstd/lz4/brotli,
base64·base64url·hex, `xxx:` 접두어, UTF-16, msgpack, 중첩 깊이 8). 명시 체인도 지원합니다.

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
  plugins/           게임 플러그인 (pixelflow, zenmatch, sheepnsheep, royalkingdom)
plugins/             프로젝트 전용 확장 자리
configs/             게임 설정 + template.yaml + icons/<게임>/
tests/               회귀 테스트 — python -m unittest discover -s tests -t .
tools/               verify_baseline.py (실제 APK 기준치 대조)
```

## 검증 상태 (게임 4종)

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

- 합성 데이터 회귀 테스트 347개
- xlsx의 Summary 수식은 Excel에서 열 때 자동 계산됩니다.
- `hierarchy` 실행 중 `Error generating tree nodes: Sequence contains no matching element`
  가 콘솔에 섞여 나올 수 있습니다. TypeTreeGeneratorAPI 내부 DLL이 찾지 못한 클래스에
  대해 직접 출력하는 메시지로, 다음 백엔드로 폴백되므로 무해합니다 — 최종 복원율은
  실행 끝의 `[typetree]` 줄이 정본입니다.
