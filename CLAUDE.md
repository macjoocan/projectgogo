# CLAUDE.md — levelscope 작업 지침

이 저장소는 **levelscope**: 모바일 게임 APK/XAPK/OBB에서 데이터를 추출해
요약 xlsx · HTML 뷰어 · 디코딩 JSON zip을 생성하는 설정 기반 파이프라인이다.

**장르를 가리지 않는다.** 추출·디코딩·에셋·계층·카탈로그는 전부 장르 무관이고,
낯선 게임은 `fields: auto` 로 컬럼을 표본에서 자동으로 뽑는다. 다만 `board`/`palette`
와 HTML 뷰어의 그리드 렌더는 **보드형(퍼즐·매치3) 전용**이다 — 그리드가 없는 게임은
그 두 절을 빼고 `outputs` 에서 `html` 을 뺀다.
상세 문서는 `GUIDE.md`(**처음 보는 게임 뜯는 순서 — 실전 플레이북**), `MANUAL.md`(사용법
전체), `README.md`(빠른 시작), `CHANGELOG.md`(버전 이력).

## 기본 원칙

- 레벨 추출 요청이 오면 **새 코드를 짜지 말고 이 파이프라인을 실행**한다.
- 게임별 차이는 `configs/<게임>.yaml`로, 게임 고유 로직은 `levelscope/plugins/<게임>.py`로
  해결한다. 코어 수정은 모든 게임에 영향을 주므로 최소화한다.
- 산출물은 `out/`에 생성된다. `out/`은 커밋하지 않는다.
- 코어를 고쳤으면 **반드시 `tests/` 를 돌린다**(추가 설치 필요 없음).

## 자주 쓰는 명령

```bash
pip install -r requirements.txt                       # 최초 1회

# 전체 실행 (입력: apk / xapk / obb / zip / 압축해제 폴더 모두 가능)
python -m levelscope run --config configs/pixelflow.yaml --input <입력> --out out

# 처음 보는 게임의 첫 명령 — 프로파일 + 설정 초안 (설정 불필요)
python -m levelscope survey --input <apk> --configs configs

# 새 게임 인코딩 파악 (설정 없이 동작 — apk를 주면 내부 레벨 후보를 샘플링한다)
python -m levelscope detect --input <apk>
python -m levelscope detect --input <apk> --xor-scan   # 암호화 의심 시 XOR 키 복구

# 컨테이너 내부 경로 훑기 (levels_glob / data_file 잡을 때)
python -m levelscope ls --input <apk> --glob "assets/**/*.json"

# 설정 작성 중 샘플 JSON 구조 확인
python -m levelscope inspect --config configs/<게임>.yaml --input <입력>

# Unity 소스 목록만 (가장 싼 조회 — --split 이 내부에서 쓴다)
python -m levelscope sources --input <apk>

# 소스마다 별 프로세스로 (산출물이 소스별 zip 으로 나뉜다)
python -m levelscope sprites --input <apk> --out out --split

# 레벨 밖 리소스 (둘 다 설정 없이 동작)
python -m levelscope assets    --input <apk> --out out   # 사운드·머티리얼·폰트·Spine·텍스트
python -m levelscope hierarchy --input <apk> --out out   # 씬·프리팹 계층 JSON

# 테스트 (표준 unittest — pandas/PyYAML 없어도 돌아간다)
python -m unittest discover -s tests -t .

# 실제 APK로 기준치 대조
python tools/verify_baseline.py --zenmatch <xapk> --pixelflow <xapk|폴더>
```

## 실행 후 검증 체크리스트

1. 로그 `[decode] 성공 N / 실패 0` — 실패가 있으면 `out/<게임>_errors.txt` 와
   로그의 `자동 감지 제안` / `XOR 키 복구` 확인
2. 로그 `[palette] unity에서 N색 추출` — 자동 팔레트로 폴백됐다면 뷰어 색이 실제와 다름
3. xlsx Levels 행수 = `[input] 레벨 파일 N개` 와 일치
4. 뷰어 HTML을 브라우저(또는 Playwright)로 열어 콘솔 에러 0 확인
5. `run --limit 20` 으로 먼저 빠르게 돌려보면 설정 실수를 일찍 잡는다

## 새 게임 추가 절차

1. `ls` 로 내부 경로 확인 → 2. `detect` 로 인코딩 체인 파악(암호화면 `--xor-scan`) →
3. `configs/template.yaml` 복사 후 `levels_glob`(또는 `input.unity`), `codec`(그냥 `auto` 권장)
기입 → 4. `inspect` 로 구조 보며 `fields`/`board` 작성 → 5. `run --limit 20` → 6. `run` →
7. 필요 시 `levelscope/plugins/pixelflow.py` 를 본떠 플러그인 작성
(`split_levels` / `level_extras` / `entities` / `board` / `viewer_level`, 모두 선택).

**한 파일·에셋에 레벨이 여러 개 들어있는 게임**은 플러그인 `split_levels(data, record)`로
`[(세트명, 레벨id, 레벨 dict)]` 를 돌려주면 레코드가 그만큼 갈라진다
(`levelscope/plugins/sheepnsheep.py` 참고).

## 코드 구조

```
levelscope/container.py  입력 추상화 — 폴더/zip/apk/xapk/obb/중첩 apk를 한 인터페이스로.
                         컨테이너를 다루는 코드는 전부 여기를 거친다
levelscope/discover.py   Unity 소스 자동 발견 (`sources: auto`) — Addressables 번들 포함
levelscope/survey.py     APK 프로파일 + 설정 초안 (새 게임 온보딩의 0단계)
levelscope/catalog.py    Addressables 카탈로그 해독 — 번들 해시 → 원본 프로젝트 경로
levelscope/unity.py      UnityPy 로드·오브젝트 순회·페이로드 추출 공통 헬퍼
                         + ObjectIndex — PPtr을 파일 경계를 지켜 해석한다
levelscope/decode.py     코덱 체인 + 자동 감지. 새 코덱은 @step 데코레이터로 등록
levelscope/xorscan.py    반복키 XOR 키 복구 + 엔트로피/IoC 진단
levelscope/extract.py    레벨 수집 (파일형 levels_glob + Unity형 input.unity)
levelscope/schema.py     점 경로 매핑 ('a.b.c', 'a.*' = 래퍼 안의 유일한 리스트)
levelscope/palette.py    Unity 에셋 팔레트 추출 (UnityPy) + static/자동 폴백
levelscope/report_xlsx.py  xlsx (Levels/엔티티/Summary-수식)
levelscope/viewer.py     단일 HTML 뷰어 — grid 모드(RLE 그리드) + tiles 모드(스프라이트 스택)
levelscope/sprites.py    Unity 스프라이트/텍스처 → PNG zip
levelscope/assets.py     사운드(WAV)·머티리얼(JSON)·폰트·Spine·텍스트 → zip
levelscope/hierarchy.py  씬·프리팹 GameObject 트리 → JSON zip
levelscope/typetree.py   IL2CPP MonoBehaviour 필드 복원 (TypeTreeGeneratorAPI 다중 백엔드)
levelscope/flatbuf.py    스키마 없는 FlatBuffers 해독 (codec: flatbuffers)
levelscope/cli.py        run / inspect / detect / ls / sources / survey / sprites / assets / hierarchy
levelscope/split.py      `--split` 드라이버 — 소스마다 별 프로세스로 (산출물이 소스별로 나뉜다)
levelscope/plugins/      게임 플러그인 (정본 한 벌. v1.3의 양쪽 복사는 없앴다)
plugins/                 프로젝트 전용 확장 자리 (비어 있어도 됨)
configs/                 게임 YAML + icons/<게임>/ 뱃지 아이콘
tests/                   합성 데이터 회귀 테스트 (표준 unittest, 무설치)
tools/verify_baseline.py 실제 APK 기준치 대조
```

의존성 임포트는 필요할 때만 한다 — pandas/openpyxl은 xlsx를 낼 때, PyYAML은 설정을
읽을 때. 그래서 `detect`/`ls`/`sprites`/`assets`/`hierarchy` 는 그것들 없이도 동작한다.
이 성질을 깨지 말 것.

## 주의사항

- `decode.py` 자동 감지를 수정하면 `tests/test_decode.py` 를 반드시 통과시킬 것:
  gzip/zlib/bz2/xz/zstd/lz4/brotli, base64(중첩·url), hex(+대문자), 접두어, UTF-16,
  msgpack, 그리고 "hex ⊂ base64 문자셋 중복" 케이스 (`_plausible` 판별 로직).
- 새 코덱 스텝은 `@step("이름")` / `@step("접두어:", prefix=True)` 로 등록한다.
  `apply_step` 본문을 고칠 일은 없다.
- AES는 키가 필요해 자동 감지 대상이 아니다 — `aes_cbc:`/`aes_ecb:` 명시 체인.
  반복키 XOR은 `detect --xor-scan` 이 복구를 시도한다(범위·한계는 `xorscan.scan` 독스트링).
- xlsx Summary는 하드코딩 값이 아닌 수식(COUNTIF/AVERAGEIFS)으로 생성한다. 이 원칙 유지.
- 레벨이 파일이 아니라 Unity 에셋인 게임(예: Zen Match)은 `input.unity` 로 수집한다
  (`configs/zenmatch.yaml` 참고). 같은 이름의 에셋이 여러 번 나오면 `main_variantN`
  세트로 자동 분리된다. `type: MonoBehaviour` 로 ScriptableObject 레벨도 받는다.
- 레벨이 base.apk와 obb에 나뉜 배포는 `input.merge_containers: true` 로 합친다.
  기본값(false)은 "가장 많이 나온 컨테이너 하나만" 쓴다.
- **PPtr은 반드시 `unity.ObjectIndex` 로 해석할 것.** `m_FileID` 는 0이면 자기 파일,
  N>0이면 `assets_file.externals[N-1]` 이다. path_id는 파일마다 1부터 다시 시작하므로
  번들 전체에서 path_id만 찾으면 엉뚱한 에셋이 잡힌다 (실제로 `level0` 과
  `resources.assets` 에 같은 path_id가 있다).
- **`typetree` 백엔드 순서를 한 개로 줄이지 말 것.** AssetRipper 단독은 82%에서 멈춘다.
  못 읽는 클래스군(`I2.Loc.Localize`·UI LayoutGroup·Spine)이 갈라져 있어 AssetStudio
  폴백이 나머지를 메운다. 순서를 바꾸면 `MonoReader` 의 "클래스별 성공 백엔드 기억"이
  다시 학습하므로 정확도는 유지되지만 초기 시도 비용이 늘어난다.
- **못 읽은 것을 조용히 빼지 말 것.** 계층의 컴포넌트는 `"fields": null` 로 남기고,
  오디오는 WAV가 안 되면 `.fsb` 원본이라도 남긴다. "없다"와 "못 읽었다"는 다르다.
- 계층 JSON은 `hierarchy._dump` 로만 쓴다 — RectTransform에 NaN이 실제로 들어 있고,
  json 기본 설정은 그걸 `NaN` 리터럴로 뱉어 뷰어의 `JSON.parse` 를 통째로 깨뜨린다.
- `unity.load_bytes` 의 `yield` 를 try 안으로 되돌리지 말 것. with 본문의 예외가
  삼켜져 `RuntimeError: generator didn't stop after throw()` 로 바꿔치기된다
  (실제로 이 때문에 디버깅이 막혔다. `tests/test_unity_index.py` 가 이걸 지킨다).
- **`UnityPy.load()` 성공을 "Unity 파일"의 근거로 쓰지 말 것.** JSON·boot.config 같은
  아무 파일에나 성공하고 오브젝트 0개인 env를 준다. `discover.probe` 처럼
  `objects > 0` 을 봐야 한다. 동시에 확장자만으로 판정해도 안 된다 —
  `unity default resources` 는 확장자가 없는데 오브젝트 85개짜리 SerializedFile이다.
- **경로를 새로 하드코딩하지 말 것.** `sources` 기본값이 `data.unity3d` 하나였던 탓에
  Addressables 게임 전체가 누락됐고, CLI `--source` 기본값도 같은 이유로 자동 발견을
  무력화했다. 새 경로가 필요하면 `discover` 의 패턴 목록에 넣는다.
- **상한(max_count/max_nodes)에 걸려 못 처리한 것을 조용히 넘기지 말 것.** 어떤 소스를
  아예 열지 못했는지 이름까지 로그에 남긴다. 안 그러면 "그 번들은 비어 있었다"로 읽힌다.
- **Unity 파일 판정을 이름으로만 하지 말 것.** 확장자 없는 번들이 실제로 있다
  (Royal Kingdom, Play Asset Delivery 팩에 114개). 이름으로는 *확실한 것만* 걸러내고
  앞 32바이트 매직(`UnityFS`)을 본다. 후보 판정 전에 엔트리를 통째로 읽지 말 것 —
  `Container.head()`/`size_of()` 가 있다.
- **스트리밍 리소스는 번들 내부를 먼저 본다.** Addressables류 번들은 자기 오디오를
  `CAB-<hash>.resource` 로 안에 품는다. 밖에서 아무 `.resource` 로 대체하면 오프셋이
  안 맞아 소리가 깨진다(실제로 291개가 그랬다). `CAB-` 이름은 대체 금지.
- **번들 경계를 넘는 MonoScript 참조를 잊지 말 것.** 스크립트 정의와 사용처가 다른
  번들에 있는 게임이 있다(Royal Kingdom: 정의 `data.unity3d` / 사용 `datapack.unity3d`).
  `typetree.ScriptRegistry` 가 이걸 푼다 — 없으면 복원률이 14%까지 떨어진다.
  단, 스크립트 전용 번들만 미리 열 것(조건 없이 열면 90MB 번들을 두 번 읽는다).
- **헤더에 Unity 버전이 없는 번들을 "Unity 파일 아님"으로 버리지 말 것.** UnityPy 는
  버전을 못 읽으면 `No valid Unity version found` 로 **파싱 자체를 포기**하고, 그러면
  `discover.probe` 가 후보 탈락으로 처리한다. CookieRun: Crumble(Unity 6000.3)에서
  272MB·오브젝트 579,681개짜리 콘텐츠 번들이 그렇게 빠져 **게임의 3%만 뽑고 있었다.**
  같은 빌드의 다른 소스는 버전을 들고 있으므로 `unity.set_fallback_version` 으로 심고,
  버전을 알기 전에 실패한 번들 후보는 마지막에 다시 본다. 소스를 하나만 주는 경우
  (`--split`, `--source`)는 배울 데가 없으니 `--unity-version` 으로 넘긴다.
- **번들 bytes 를 리스트·dict 에 모으지 말 것.** 개수 상한 없이 모으면 Addressables
  게임에서 90MB 번들 수십 개가 동시에 살아 있고, UnityPy 가 풀면 3~5배로 부푼다
  (커밋 54GB 로 PC 가 멈춘 실제 사고. v1.21.0). 하나씩 열고 쓰고 놓는다. 여러 번들을
  같이 올려야 하면 bytes 가 아니라 **임시파일 경로**로 준다. "몇 개인지" 만 필요할 때는
  `Container.head()`/`size_of()`/이름만 훑고, 내용은 그때 읽는다.
- **오브젝트 reader 를 오래 들고 있지 말 것.** `ObjectReader` 는 `assets_file`·`reader`
  를 물고 있어 번들 env 전체를 붙잡는다. 색인·레지스트리에는 **값**(이름·ScriptRef 같은
  것)만 남긴다 — `typetree.ScriptRegistry.add_env` 가 그 예다.
- **낯선 장르는 `fields: auto` 부터.** 컬럼 경로를 손으로 적는 게 새 게임의 최대 병목
  이었다(퍼즐이면 기믹, RPG면 스탯, 방치형이면 생산·비용처럼 이름이 전부 다르다).
  `schema.infer_fields` 가 표본 200개에서 뽑는다 — 스칼라는 값, 리스트는 **개수**,
  중첩 dict 은 점 경로. **리스트 안쪽은 펼치지 않는다**(레벨마다 원소 수가 달라 컬럼이
  폭발한다). 상한(60컬럼)에 걸려 빠진 경로는 반드시 로그에 남긴다.
- **표본을 크기순으로 뽑지 말 것.** `survey` 가 그랬다가 Spine `.skel` 이 상위를 다 먹어
  레벨 4,500개짜리 계열을 통째로 놓쳤다. **계열(이름에서 숫자를 뭉친 것) 단위**로 센다.
- **FlatBuffers는 타입을 안 적어둔다.** 4바이트 값이 정수인지 오프셋인지 버퍼 하나로는
  못 가린다. 세 근거를 다 써야 한다 — 문자열의 널 종료자, 오프셋 대상의 4바이트 정렬,
  그리고 표본 다수결(`flatbuf.infer_schema`). 정렬 검사만 빼도 4,500개 중 1,462개가
  깨졌다. 다수결까지 해야 0이 된다.
- **바이너리 종결 스텝(flatbuffers·msgpack)은 zip 평문을 따로 만든다.** 파싱 직전
  바이트가 곧 원본 바이너리라, 그대로 넣으면 `levels/1.json` 이 바이너리가 된다.
  `cli._plain_bytes` 가 이 경우 디코딩 결과를 JSON으로 낸다.
- **FlatBuffers 빈 벡터(길이 0)는 정상이다.** 이걸 거부하면 "목록이 비어 있는" 필드가
  통째로 해석 불가가 되고 다수결이 그 슬롯을 스칼라로 잘못 확정한다. 반대로 **빈
  문자열은 문자열로 보지 말 것** — 빈 벡터의 길이 필드가 죄다 빈 문자열로 읽힌다.
- **FlatBuffers 스칼라 벡터는 int32 로 안 보이면 벡터가 아니다.** uint8 로 폴백하면
  아무 쓰레기나 "벡터"가 되어 진짜 스칼라를 덮어쓴다 — Royal Kingdom Lv9 의 얼음
  27칸 중 25칸이 그렇게 사라졌다(실제 화면 목표는 "얼음 27"). 빈 벡터도 **타입
  투표에서 빼고**, 스키마가 확정하기 전에는 받지 않는다. 안 그러면 0으로 채워진
  자리를 가리키는 스칼라가 통째로 빈 벡터가 된다.
- **뷰어 아이콘은 원본 이름으로 확인한 것만 붙인다.** 이름 유사도 자동 매칭이
  `Box`에 남색 사각형, `Ice`에 하늘 그라데이션 띠를 붙여 사용자가 "처음 보는 기믹"으로
  지목했다. 쓸 만한 원본이 없으면 (`Border` = 28x1 선) **아이콘을 붙이지 않는다.**
  기믹별 원본은 `Items-<이름>-*` / `<이름>_parts-*` / `<이름>_big`(목표 아이콘) 규칙을
  따르므로 이 이름들로 찾는다. 매핑 근거는 `configs/icons/<게임>/_mapping.json` 에 남긴다.
- **FlatBuffers 게임은 앱 안에 생성 코드가 남아 있는지 먼저 본다.** IL2CPP 덤프의
  `FTiledLevel`·`FTiledGrid`·`FTiledCell` 같은 클래스가 곧 스키마다 — 프로퍼티 순서가
  슬롯 순서이고, 벡터 원소 타입은 인덱서(`Cells(int j)`)에 있다.
  `tools/fbnames_from_dump.py` 가 이걸 `flatbuffers.names` 지도로 만든다.
  열거형(`TiledId`·`GoalType`)도 같은 덤프에서 나온다 — **게임마다 다시 뽑을 것.**
  Royal Kingdom 과 Royal Match 는 같은 스튜디오인데 6번이 `Match1` 과 `Orange` 로 다르다.
- **오브젝트를 path_id 만으로 찾지 말 것.** 한 번들 안 여러 SerializedFile이 같은
  path_id를 쓴다. 스프라이트를 뽑다가 Material이 잡힌 적이 있다 — `(파일명, path_id)`.
- **스프라이트 텍스처가 다른 번들에 있을 수 있다.** 혼자 열면 UnityPy가 현재 작업
  폴더에서 그 파일을 찾다 실패한다. `unity.load_bytes(deps=[...])` 로 참조 대상
  번들을 같이 올려 재시도한다 — 대상은 실패 메시지의 파일 이름으로 찾고,
  재시도 범위는 **오브젝트 id(파일명+path_id)** 로 집는다(이름으로 거르면 동명이인이 샌다).
- **카탈로그는 `catalog.json` 과 `catalog.bin` 두 포맷이 있다.** 바이너리 쪽이 최신이고
  (Addressables 1.21+ / Unity 2023+, PixelFlow 가 그렇다) 버전이 Binv1~v3 로 갈린다.
  오프셋 기반 객체 그래프라 직접 파서를 쓰면 조용히 어긋나므로 검증된 선택 의존성
  `addressablestools`(MIT, 무의존)로 읽는다. 없거나 파싱이 실패하면 문자열 목록만 내는
  폴백으로 내려간다 — **폴백을 지우지 말 것.**
- 카탈로그 해독은 **검증 후에만** 신뢰한다 (`catalog._parse_buckets`/`_parse_entries` 가
  블롭 크기·인덱스 범위를 확인). 검증 실패 시 매핑 없이 목록만 쓴다 — 잘못 푼 매핑으로
  이름을 붙이는 건 이름을 안 붙이는 것보다 나쁘다.
- **메모리 피크는 "가장 큰 번들 하나를 여는 값"이다.** 실측(CookieRun: Crumble):
  `UnityPy.load()` 로 오브젝트 58만 개 번들을 여는 데 1.83GB, 스프라이트 단계 전체가
  4.26GB. 우리 코드가 그 위에 얹는 건 `ObjectIndex` 0.02GB 뿐이다. 그래서 다음이
  **효과 없다**(전부 실측으로 확인) — 아틀라스 캐시 상한(피크 4.34→4.40GB, 시간 +56%),
  `--split`(한 소스가 88%를 차지하면 4.26→4.52GB), 씬 스트리밍(3.19→3.16GB).
  **효과가 있던 것은 단계 사이 `gc.collect()` 하나다**(5.50→4.51GB). 새 최적화를
  제안하기 전에 어디가 몇 GB인지 먼저 재라.
- **이름이 대소문자만 다른 스프라이트가 실제로 있다.** 원본이 표기를 혼용한다
  (`IconSnsFacebook`/`IconSnsFaceBook`, `shadow`/`Shadow`). zip 안에서는 다른 파일이지만
  Windows·macOS 는 대소문자를 구분하지 않아 **풀면 나중 것이 앞 것을 덮어써 조용히
  사라진다.** 실측 충돌: Zen Match 98 · Royal Kingdom 78 · Royal Match 38 · 그 외 2.
  그래서 `sprites._unique_key` 와 `categorize.relabel_zip` 은 충돌 판정을 **소문자로**
  한다. 이 비교를 대소문자 구분으로 되돌리지 말 것.
- **기준치가 늘어난 게 게임 업데이트 때문이라고 단정하지 말 것.** 도구가 고쳐져서
  늘어나기도 한다 — v1.24.0 의 Unity 버전 폴백 수정으로 CookieRun: Crumble 이
  스프라이트 1,229 → 10,443, 계층 노드 2,044 → 112,901 이 됐다. 기준치를 적을 때는
  **스킵 수와 사유까지** 함께 적는다(예: "10,443 추출 / 11건 스킵 — 0x0 런타임 생성
  텍스처"). 그 수가 나중에 늘면 그게 신호가 된다.
- PixelFlow 기준치(2026-08 v): 레벨 2384(8세트, 메인 3db568… 2100개만 isValid=true),
  슈터 160,313(파이프 포함), 팔레트 34색. 새 버전에서 크게 다르면 사용자에게 보고.
- Zen Match 기준치(v220000.1.762): TextAsset 4,502(main 4,493 + variant 9),
  board(v2) 6. **포맷 분포(layered/random)는 ±1 흔들릴 수 있다** — 이름이 중복된
  레벨 쌍에서 어느 쪽이 `main` 이 되는지가 UnityPy 버전·플랫폼에 따라 갈리기 때문.
  이 PC(Windows/UnityPy 1.25.3)에서는 main 기준 layered 3,705 / random 782,
  인수인계 문서(Cowork/Linux)는 3,704 / 783. 합계·main/variant 분리는 항상 일치.
- SheepNSheep 기준치(com.game.keepsheep v1.9.2): 에셋 8개 → **스테이지 87개 / 맵 40개**,
  타일 합 11,817, 디코딩 실패 0, 스프라이트 37개. `blockTypeData` 합×3 = 랜덤 타일 수가
  blockTypeData를 가진 73개 스테이지 전부에서 성립(`pool_ok` 컬럼). `defaultMapData` 14개는
  구형 스키마라 blockTypeData가 없어 `pool_ok='-'`. **일일 맵은 서버 배포라 APK에 없다.**
- 뷰어 아이콘 매핑 중 `splitObjects→PigCell`, `pixelWoodBlocks→HardPixel`(PixelFlow)과
  블록타입 id ↔ `card*` 스프라이트(SheepNSheep)는 이름 기반 **추정** 매핑 — 정정되면
  해당 config만 고치면 된다.
