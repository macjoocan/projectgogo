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
levelscope/concat.py     한 파일에 번들이 여러 개 이어붙은 배포를 세그먼트로 가른다
                         (`container.ConcatView` 가 이걸 가상 엔트리로 보여준다)
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
tools/analyze.py       원 클릭 진입점 (분석하기.bat 이 부른다) — 게임 인식·설정 선택·survey·
                       확인 후 `run --only` 로 단계를 나눠 돌리고 각 단계에 상한을 건다
tools/watchdog.py      메모리 상한을 걸고 실행 (넘으면 프로세스만 죽는다).
                       프로세스 트리 합산이 기본 — venv 스텁 때문에 필수다(--no-tree 는 진단용)
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
- **`typetree` 백엔드가 `Unable to load DLL 'capstone'` 로 다 죽으면 metadata 암호화로
  오진하지 말 것.** capstone.dll 은 x64 정상이어도 .NET Core 가 어셈블리 폴더의 native
  DLL 을 못 찾는다(.NET native 검색은 `os.add_dll_directory` 를 안 따름). 해결은
  **capstone.dll 을 파이썬 실행 파일 폴더로 복사** — `typetree.MonoReader.open` 이
  백엔드 import 전에 자동으로 한다(v1.29.0). 이 버그로 20 Minutes Till Dawn 은 정상
  metadata 인데도 필드 복원이 2.8% 였다. metadata 암호화는 magic(`fab11baf` 정상)으로
  판별한다 — 백엔드 실패만으로 암호화라 단정하지 말 것.
- **`typetree` 백엔드 순서를 한 개로 줄이지 말 것.** AssetRipper 단독은 82%에서 멈춘다.
  못 읽는 클래스군(`I2.Loc.Localize`·UI LayoutGroup·Spine·`UnityEngine.ProBuilder`)이
  갈라져 있어 AssetStudio
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
- **한 파일에 번들이 여러 개 이어붙어 있을 수 있다.** Clash of Critters 의
  `inpackage_aa_1.lpak`(108MB)은 커스텀 포맷이 아니라 `UnityFS` 번들 **1,369개를
  그냥 연달아 붙인 것**이다(세그먼트 합계 = 파일 크기의 100.0000%, 꼬리 0바이트).
  그냥 열면 **UnityPy 가 첫 번들만 읽고 멈춰서** 오브젝트 16개만 잡히고 108MB 가
  조용히 사라진다 — 펼치면 229,785개다. `container.ConcatView` 가 앞 64바이트의
  크기 필드를 보고 자동으로 판정·분할한다(`concat` 모듈).
  **펼치기를 소비자 쪽으로 옮기지 말 것** — 컨테이너 층이라서 discover·sprites·
  assets·hierarchy·extract·`--split` 이 전부 그대로 동작한다. 여섯 군데에 흩어
  놓으면 한 곳을 빠뜨렸을 때 그 단계만 조용히 3%를 뽑는다.
  **`ConcatView.glob` 의 두 갈래를 하나로 줄이지 말 것** — 세그먼트 이름 직접 조회
  (`find_first` 가 discover 가 찾은 소스 이름을 다시 찾는다)와 부모 경로 패턴
  (`sources: [.../*.lpak]`)이 둘 다 온다. 앞쪽을 빼먹었더니 survey 의 Sprite 집계가
  13 → 6 으로 **펼치기 전보다 나빠졌다.**
  **전부 맞아떨어질 때만 펼칠 것.** 중간에 어긋나면 원본을 그대로 쓴다 — 절반만
  인정하면 "일부만 뽑힌 것"이 정상처럼 보인다.
- **`0.0.0` 을 Unity 버전으로 받지 말 것.** Unity 는 번들 헤더의 버전을 지울 때 빈
  문자열이 아니라 `0.0.0` 을 넣는다(lpak 세그먼트 1,369개가 전부 `5.x.x`/`0.0.0`).
  값이 있으니 `if v:` 로는 안 걸러진다. `unity.is_real_version` 을 쓸 것 — 안 쓰면
  survey 가 "Unity 0.0.0" 이라 보고하고(실제 2022.3.62f3), 폴백으로 심으면 버전 없는
  형제 번들이 `0.0.0` 으로 열려 타입트리가 어긋난다.
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
- **"초기값이 비었다"를 "기능이 없다"로 적지 말 것.** 기능의 **존재** · **초기 활성
  상태** · **상태 전환 시 주입**은 서로 다른 주장이다. 덤프한 설정이 빈 배열이어도
  별도 경로가 나중에 값을 넣을 수 있다(실측: 초기 설정은 비어 있는데 승리 처리
  경로가 원소 셋을 주입하고 있었다). **설정 함수의 호출자를 전부 확인**하기 전에는
  부재를 주장하지 않고, 부재·활성 양쪽에 재현 근거(원본 해시·호출 주소)를 남긴다.
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
- **카탈로그가 번들 안에 들어 있을 수 있다.** `assets/aa/catalog.bundle` 안
  TextAsset `catalog` 가 그것이다(Clash of Critters, 5.7MB). `catalog.json`/
  `catalog.bin` 만 찾으면 **카탈로그가 있는데도 "카탈로그 없음"** 이 되고, 추출한
  아트에 원본 프로젝트 경로를 못 붙인다. `CATALOG_GLOB` 에 들어 있다.
- **카탈로그가 게임 고유 FlatBuffers 일 수 있다.** `addressablestools` 가
  `UnsupportedCatalogVersionError` 를 내면 포기하지 말고 `flatbuf` 로 본다 — 루트
  테이블 이름이 `AddressablesMainContentCatalog` 인 스튜디오 자체 포맷이었고,
  스키마 없이도 경로 12,945개가 나왔다. 단 **주소↔번들 매핑은 만들지 않는다**
  (슬롯 의미를 모른다). `decoded=False` 로 두고 경로 목록만 쓴다.
- **카탈로그의 번들 수와 APK 의 번들 수를 대조할 것.** Clash of Critters 는 카탈로그에
  10,810개인데 APK 에는 1,369개(12.7%)뿐이다 — 파일 이름 `inpackage` 그대로 나머지
  87%는 실행 시 받는다. 이걸 안 보면 "리소스 다 뽑았다"고 잘못 적는다.
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
- **`watchdog` 의 트리 합산 기본값을 끄지 말 것.** 가상환경의 `.venv\Scripts\python.exe`
  는 리다이렉터 스텁이라 실제 작업은 **손자 프로세스**가 한다. 대상 하나만 보면 스텁의
  1MB 만 재고 상한이 영원히 발동하지 않는다 — 실측 스텁 0.001GB / 손자 1.125GB, 보고값
  `최고 커밋 0.00GB`. v1.27.0 의 기본값이 그랬고, 그래서 감시가 있는데도 2026-08-22 에
  PC 가 응답을 멈췄다. `tests/test_watchdog.py` 가 이걸 지킨다.
- **무거운 추출을 한 프로세스에 몰지 말 것.** `run --only <산출물>` 로 나눠 부른다
  (`tools/analyze.py` 가 4단계로 그렇게 한다). 앞 단계 잔여와 다음 단계 할당이 겹쳐
  피크가 합쳐지고, 한 단계가 폭주하면 그 런의 산출물이 전부 날아간다. **독립 명령
  (`sprites`/`assets`/`hierarchy`)으로 나누지 말 것** — 그것들은 `--config` 를 안 받아서
  `max_count`·`categorize`·`max_nodes` 가 기본값(`--max 1000`)으로 떨어져 조용히 잘린다.
- **`typetree` 비용은 누수가 아니라 백엔드 초기화 고정비다.** `load_il2cpp` 는 백엔드마다
  IL2CPP 를 통째로 파싱한다 — PixelFlow(libil2cpp 193MB · metadata 42MB · Unity 6000)
  실측 **AssetRipper 2.86 / AssetStudio 1.38 / AssetsTools 0.70GB = 4.94GB** 가
  *아무것도 읽기 전에* 든다. 그래서 `MonoReader` 는 **첫 백엔드만 올리고 나머지는 폴백이
  필요해질 때** 올린다(`_warm_first` / `_generator`). 이 지연 로드를 되돌리지 말 것.
  읽기 루프는 평탄하다(실측 read 500→2500 구간 5.81→5.84GB, 노드 캐시 196개) — 캐시가
  `(백엔드, 클래스)` 단위라 `get_nodes` 는 클래스마다 한 번뿐이다.
  나머지 피크는 **가장 큰 루트 하나의 문서**다(PixelFlow 루트 `AB` 가 +2.11GB, 쓰고 나면
  회수). typetree 를 켜면 컴포넌트마다 필드 값이 실려서 `--no-typetree`(0.97GB · 9초)와
  크게 갈린다. 계층 필드가 필요 없으면 `--no-typetree` 가 정답이다.
- **.NET 백엔드는 주소 공간을 크게 예약한다 — 이걸 커밋으로 읽지 말 것.** 실측: 백엔드
  하나를 올리면 커밋 3.16GB인데 **예약은 259GB** 다(.NET GC 리전). Windows
  `Resource-Exhaustion-Detector` ID 2004 가 찍는 "consumed N bytes"는 이 **예약**이라
  109GB 같은 숫자가 나온다. 커밋 한도가 38GB인 PC에서 109GB 커밋은 애초에 불가능하다 —
  실제 피크는 6~7GB 였다. 사고의 원인은 이 숫자가 아니라 **한 프로세스에 다 몰아넣은 것**.
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
- **Steam(PC) 빌드도 된다 — 입력에 설치 폴더를 그대로 준다.** 단 **윈도우 IL2CPP 는
  코드가 `GameAssembly.dll`(루트)에 있고** 기본 탐색 패턴(`lib/*/libil2cpp.so`)은
  안드로이드 전용이라 못 찾는다. 그러면 survey 가 `IL2CPP(재료 일부 누락)` 이라 말하고
  MonoBehaviour 필드가 **전부 빈다.** `typetree.il2cpp: ["GameAssembly.dll"]` 한 줄로
  해결된다(metadata 는 기본 `*/Metadata/global-metadata.dat` 에 걸린다). 실측으로
  백엔드 3종이 PE 를 모두 정상 로드한다 — **PE 라서 안 되는 게 아니다.**
- **번들 경계를 넘는 MonoScript 참조는 세 가지가 다 있어야 풀린다.** SANABI 실측으로
  복원률이 **70.9% → 99.73%** (미해결 69,263 → 744) 가 된 과정이 그 근거다.
  ① **미리 여는 "스크립트 전용 번들"만으로는 부족하다** — 조건(MonoScript 100개 이상
  이고 MonoBehaviour 보다 많을 것)은 Royal Kingdom 처럼 정의를 한 곳에 몬 게임용이고,
  스크립트가 콘텐츠 번들에 흩어진 게임에서는 소스 836개 중 1개만 걸렸다.
  ② **런 중 누적**(여는 김에 `add_env`)은 공짜지만 **순서**에 걸린다 — 앞쪽 번들이
  뒤쪽 스크립트를 참조하면 그 시점엔 색인에 없다(73.8% 에서 멈춘다).
  ③ **온디맨드 대여가 결정적이다.** `discover.UnitySource.files` 가 번들 **내부**
  SerializedFile 이름을 이미 알고, 참조가 가리키는 것도 그 이름(`CAB-…`)이다.
  지도를 만들어 두면 필요한 번들만 한 번씩 열어 순서와 무관하게 푼다
  (`hierarchy._script_lender` + `ScriptRegistry(lender=)`). 99.4%.
  **지도에 소스 자신의 이름(basename)도 넣을 것** — 번들이 아닌 소스(kind=serialized)
  는 `files` 가 비는데 다른 번들은 그걸 소스 이름 그대로 참조한다.
  ④ **같은 파일이 여는 방식에 따라 다른 이름으로 불린다.** 소스로 열면 내부 이름
  (`8048103888263714719`), 다른 번들이 참조하면 externals 의
  `globalgamemanagers.assets`. 한쪽만 걸면 **스크립트 3,871개를 색인해 두고도**
  참조 2,033건을 못 푼다. `add_env(alias=...)` 로 양쪽에 건다. 99.73%.
  남은 744건은 **구조적으로 불가능**하다 — 743건이 `path_id == 0`(참조 자체가 빈
  슬롯이라 "없다"가 정답), 1건이 오브젝트 파손이다. 더 고칠 것이 없다.
- **측정 도구가 수정 경로를 타는지 먼저 확인할 것.** 위 ④ 를 고친 뒤 재측정했는데
  숫자가 안 줄었다 — 진단 스크립트가 `_script_registry` 를 안 쓰고 `alias` 없이
  `add_env` 를 부르고 있어서 **고친 경로를 아예 안 타고 있었다.** 그대로 믿었으면
  "고쳤는데 효과 없음"으로 잘못 결론 낼 뻔했다.
- **독립 ScriptableObject 는 어떤 산출물로도 안 나온다.** `hierarchy._classify` 는
  Transform 이 있는 파일만 분류하므로 MonoBehaviour 만 든 데이터 번들을 통째로
  건너뛰고, `assets` 의 종류에도 SO 가 없다. `input.unity` 의 `type: MonoBehaviour` 는
  **JSON 문자열을 품은** SO 용이라(`payload_bytes` 가 가장 긴 문자열을 꺼낸다) 구조화된
  필드에는 맞지 않는다. 데이터가 SO 에만 있는 게임은 `tools/dump_scriptableobjects.py`
  를 쓴다 — `m_GameObject` 의 path_id 가 0 이면 독립 에셋, 아니면 컴포넌트다.
- SANABI 기준치(Steam, WONDER POTION, Unity 2019.4.41f1 IL2CPP): Unity 소스 839 ·
  Addressables 번들 832 · 에셋경로 1,210(catalog.json 구형). **씬 139 = survey 와 일치**
  (prlg 14 · chap1~5 16/14/17/14/13 · chapending 3 · dlc 17 · 스피드런 srchap 19 + srdlc 6 ·
  시스템 6) · 프리팹 2,540 · **노드 178,108 = GameObject 수와 정확히 일치** ·
  MonoBehaviour 복원 **99.73%**(전체 273,980 중 273,236 — 고치기 전 70.9% 였다.
  위 "번들 경계를 넘는 MonoScript 참조" 항목 참고). 에셋 18,658(audio 1,804 ·
  material 16,797 · font 55 · text 2 — 넷 다 survey 와 일치, spine 0).
  스프라이트 **121,220 추출 / 실패 0 = survey 의 Sprite 수와 일치**(고치기 전에는
  118,982 / 스킵 2,238 이었다 — 전부 `FileNotFoundError('Resource file
  resources.assets.resS not found')`. 그 파일은 디스크에 152MB 로 있었는데,
  `sprites.py` 가 소스를 bytes 로 올리는 바람에 UnityPy 가 *파일 옆*에서 찾는
  `.resS` 를 못 만났다. `unity.load_bytes(path=...)` 로 실제 경로를 주게 고쳤다).
  Texture2D 223,869 장은 설정에서 일부러 뺐다
  (둘 다면 345,089 장). 분류는 **기타가 112,982(95%)** 다 — 기본 규칙이 CookieRun
  이름에서 나온 것이라 이 게임 약어를 모른다(`sprites.categories` 를 적어야 한다).
  독립 SO **35,076개** · 컴포넌트 238,079 — 합계 + 미해결 744 + 실패 81 = 273,980 으로
  survey 의 MonoBehaviour 수와 정확히 맞는다. 계층 쪽 복원은 **238,079/238,088(100.0%)**
  이고 스크립트참조없음 0 이다(SO 덤프는 독립 에셋까지 보므로 744 가 남는다).
  단계별 최고 커밋 계층 12.6 · 에셋 8.20 · 스프라이트 8.64GB.
  `VfxInfoSo` 계열은 `[SerializeReference]` 라 백엔드 3종이 모두 못 읽는다.
  **TextAsset 이 2개뿐이다** — 데이터 테이블이 없고 밸런스가 전부 SO 다:
  `PlayerHpState`×4(Easy `damageRate 0.0` = 무적 / Normal 1.0 / Hard `hpRegenRate 0.5` /
  **Very Hard `damageRate 999.0`** = 즉사) · `MainDifficultySo`×4 · `DLCDifficultySo`×4 ·
  `EnemyRespawnerSO`×37 · `BattleGateSO`×8 · `SceneData`×100(`targetFolderPath` 에
  원본 프로젝트 경로가 남아 있다) · `NewTilePalette`×12 · `RuleTileBrush`×22.
  **계층 zip 의 씬 파일 이름이 CAB 해시라 그대로는 어느 챕터인지 모른다** — 추출 로그의
  `[hierarchy] <번들>: <파일>(kind)` 줄로 매핑을 복원해 `sanabi_scene_index.json` 을 냈다.
  Addressables 게임 공통 문제다(Capybara 도 `CAB-…` 였다).
- 암살자 키우기 기준치(`highpixel.billion` v1.2.12, Unity 2022.3.62f3): TextAsset 93 →
  **데이터 테이블 86개 · 디코딩 실패 0**. 나머지 7은 의도적으로 제외 — `_words_filter`
  (욕설 필터) · `LineBreaking Leading/Following Characters`(Unity 줄바꿈 규칙) ·
  Spine 4개(`skeleton`, `03_brush up_illust` 의 atlas+json). 앞의 셋은 survey 가
  "디코딩 불가"로 지목하지만 **암호화가 아니라 JSON 이 아닌 것**이라 xor-scan 대상이
  아니다. 스프라이트 14,102(스킵 5) · 에셋 357 · 계층 씬 2 / 프리팹 195 / 노드 129,983 ·
  MonoBehaviour 복원 143,755/143,765(100.0%, 실패 10은 전부
  `DamageNumbersPro.DamageNumberMesh`). 단계별 최고 커밋 2.90 / 5.34 / 3.30 / **11.82GB**.
  **레벨 하나 = 테이블 하나**라 xlsx 는 목차가 된다(컬럼은 `Items` 개수 + IAP 설정 잡음).
  항목 단위 행이 필요하면 플러그인 `split_levels` 가 필요하다.
- Capybara Go 기준치(`com.habby.capybara` v1.8.13, Unity 2022.3.62f2): **Unity 소스
  2,285개**(Addressables 번들 1,919 · 에셋경로 14,768). 스프라이트 15,019(스킵 12 —
  Sprite 10,101 + Texture2D 4,930 = 15,031 과 일치) · 에셋 5,247(audio 401 ·
  material 2,469 · font 10 · **spine 1,708** · text 659 — TextAsset 2,367 이 정확히
  갈린다) · 계층 씬 2 / 프리팹 3,477 / **노드 360,346 = GameObject 수와 정확히 일치** ·
  MonoBehaviour 복원 332,151/372,104(**89.3%**). 단계별 최고 커밋 1.77 / 1.93 / 10.98GB.
  **복원율이 낮은 이유는 HybridCLR 이다** — 실패 상위가 `HotFix.UIAvatarCtrl`·`HotFix.UIItem`
  같은 `HotFix.*` 클래스인데, 그 정의는 `libil2cpp.so`/`global-metadata.dat` 가 아니라
  런타임에 올리는 관리형 `HotFix.dll`(16.6MB) 안에 있다. typetree 백엔드가 못 찾는 게 정상.
  **이 진단은 재측정으로 확정됐다.** SANABI 를 70.9 → 99.73% 로 올린 스크립트 대여·별칭
  수정을 적용해 다시 돌렸는데 **수치가 한 건도 안 움직였다**(332,151/372,104 · 실패
  38,092 · 참조없음 1,861 모두 동일). 참조를 푸는 것과 **필드 구조를 아는 것**은 다른
  문제다 — Capybara 는 참조없음이 1,861건(0.5%)뿐이라 애초에 참조는 거의 다 풀고
  있었고(SANABI 는 69,263건 = 29% 였다), 손실은 전부 `실패` 쪽이다.
  **89.3% 는 과소평가가 아니라 정확한 값이다.** 올리려면 `HotFix.dll` 에서 typetree 를
  뽑는 별도 작업이 필요하다.
  **데이터 테이블은 `tb<모듈>_<테이블>` 이름의 Luban 바이너리**다(`LubanSupport.dll` 동봉).
  JSON 도 압축도 아니고 길이 접두 문자열 + 고정폭 수치라 codec 자동 감지가 실패한다 —
  원본 바이트는 `_assets.zip` 의 `text/` 에 보존한다. 스키마는 `HotFix.dll` 에 있어
  IL2CPP 덤프보다 뽑기 쉽지만 새 코덱이 필요한 별도 작업이다.
  씬은 survey 7 / 계층 2 로 갈리는데, `scene-other_scenes_all_*.bundle` 이 내부파일 10개에
  오브젝트 34개뿐인 껍데기라 나머지는 GameObject 가 없는 씬 스텁이다(노드 수 일치가 근거).
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
- Clash of Critters 기준치(com.farlightgames.pgame.gp v0.46.1): Unity 소스 1,495
  (lpak 세그먼트 1,369 + serialized 126) · 오브젝트 229,785 · 스프라이트 4,117
  (실패 4,854 — 전부 `m_PathID == 0`, 그중 95개는 픽셀이 APK 에 없는 CDN 배급분
  자리표시자) · 에셋 1,561 · 계층 씬 3 / 프리팹 985 / 노드 53,875 / 필드 복원 99.7%.
  **레벨·밸런스는 APK 에서 안 나온다** — 암호화된 `pgame.pkg`(15MB)·`.jsone` 안이고
  `ff ff ff ff`+평문길이+8바이트 패딩 형식의 **8바이트 블록 ECB**(반복키 XOR 은
  `--xor-scan --max-keylen 64` 로 배제). 키는 `libil2cpp.so` 안. 별건이므로 손대기
  전에 사용자에게 묻는다.
- **Unity 가 아닌 게임도 온다 — 파이프라인이 안 도는 게 정상이다.** Hades(Steam,
  Supergiant 자체 엔진) 기준치: Lua 밸런스 15/15 파일(특성 487 · 적 208 · 무기 495 ·
  방 124 · 조우 124) — **lupa 로 실제 실행**해서 뽑는다(정적 파싱보다 정확하다).
  SJSON(주석 허용 · `=` · 콤마 없음) 100/100 · 맵 레이어 144/144 · 현지화 한국어 11,205.
  `.thing_bin`(SGB1) 레코드는 **`id(u32)·pad(2)·X(f32)·Y(f32)·flag(u8)·len·name`**,
  길이 접두는 매직 있으면 u32 / 없으면 u8 — 151개 중 143개가 헤더 count 와 정확히
  일치하고 Thing 177,278 · 고유 1,454종이 좌표째 나온다. `SGB1` 매직이 없는 8개는
  **다른 포맷이 아니라 다른 버전(9/12)** 이다. 상세는 `out_hades/README.md`.
- **압축 알고리즘을 추측하기 전에 바이너리가 무엇을 링크했는지 볼 것.** Hades `.pkg`
  를 1차에 "독자 압축(7종 × 40오프셋 전부 실패)"으로 적었는데, `x64/EngineWin64s.dll`
  문자열에 `LZ4_compressHC`·`LZ4_compress_HC_continue` 가 그대로 있다 — **LZ4 다.**
  같은 DLL 에 `=DXT5`·`=BC5U`·`Content/Win/Packages/BC3` 도 있다. 280조합을 돌리는
  비용보다 `strings` 한 번이 싸고 정확하다. (아직 해제는 못 했다 — 아래.)
- **"우연일 수 없다"를 쓰기 전에 우연의 기대값을 계산할 것.** Hades `.pkg` 가 LZ4
  라는 근거로 "세 파일이 모두 토큰 `0x50`으로 파일 끝에 맞으니 우연일 수 없다"고
  적었다가 취소했다 — 마지막 16바이트에서 `p+1+litlen == 끝` 을 만족하는 위치는
  **무작위 데이터에서도 기대값 1개**다. 끝단 검사 자체는 값싸고 쓸모 있지만,
  그 결과의 강도는 계산해서 적어야 한다(여기선 ≈0.4%, "시사적" 수준).
- **사전 의존도는 사전을 두 번 바꿔 풀어서 정확히 잴 수 있다.** LZ4/LZSS 계열에서
  사전을 `0x00` 과 `0xFF` 로 두 번 디코드하면 **달라지는 바이트가 곧 사전 유래분**이다.
  Hades `.pkg` 실측 38~76%(컬러부는 최대 95.9%) — 그래서 실루엣은 살고 색이 죽는다.
  "왜 절반만 맞나"를 감으로 말하지 말고 이렇게 수치로 특정한다.
- **의존도가 낮다고 깨끗한 건 아니다.** Hades BC3 91건 중 사전 의존 2% 미만이 1건
  있었는데(0.279%) 그것도 노이즈였다 — 사전 말고 프레이밍에 모르는 부분이 더 있다는
  뜻이다. **하나의 원인을 특정했다고 그게 유일한 원인이라고 적지 말 것.**
- **한 파일에서만 성립하는 규칙은 규칙이 아니다.** Hades 원본 Achilles 는 0-사전 +
  오프셋 94 에서 출력 길이와 입력 소비가 **둘 다 정확히** 맞아떨어졌지만, 같은 규칙이
  BC3·720p 변형에는 전혀 안 맞았다. 우연은 표본 하나에서 자주 나온다 —
  **포맷 규칙은 최소 3개 표본, 되도록 변형이 다른 것으로 교차 검증**하고 나서 적는다.
- **같은 값이 두 군데 있으면 대조해서 신뢰도를 만든다.** Hades `.pkg` 의 선언크기는
  엔트리 앞(BE uint32)과 XNB 헤더(LE uint32) 두 군데에 있다. 둘이 일치하는 2,291건만
  합산하고 어긋나는 349건은 뺐다 — 안 거르면 "압축 해제 시 615GB"(실제 6.12GB)라는
  말이 안 되는 수가 그대로 보고서에 실린다. **못 읽은 것은 빼되, 뺐다고 적는다.**
- **압축 해제 성공 판정을 "길이"로 하지 말 것.** `lz4.block.decompress(size=N)` 류는
  목표 크기를 주면 입력이 떨어질 때까지 뱉으므로 **거의 항상 N 근처 길이**가 나온다.
  Hades 에서 오프셋 수십 곳이 "출력 247,6xx / 목표 247,632"로 그럴듯했지만 전부
  쓰레기였다. 판정은 **알려진 평문(여기선 XNB 헤더 30바이트)과의 일치**로 한다.
- **`LZ4_compress_HC_continue`(링크드 블록)는 preset dictionary 를 뜻한다.** Hades
  `.pkg` 는 어느 시작점으로 읽어도 첫 시퀀스의 back-reference 가 그 시점 출력보다
  뒤를 가리킨다(출력 8바이트인데 오프셋 16). 사전 없이는 원리적으로 못 푼다 —
  사전을 엔진에서 찾는 것이 다음 수지 오프셋을 더 훑는 게 아니다.
- **평문 구간 길이가 엔트리마다 다르면 고정 오프셋 파싱이 조용히 깨진다.** Hades
  `.pkg` 의 `dataBytes` 를 "XNB 헤더 뒤 5번째 uint32"로 읽었더니 2,640개 중 223개만
  통과했다. 불변식(`선언크기 = dataBytes + 30`)으로 **유도**하게 바꾸니 448개가 됐다.
  나머지는 압축이 시작되는 지점이 엔트리마다 달라서다(`720p/AphroditeUpgrade` 는 앞
  16바이트까지만 평문). **못 읽은 2,192개를 "우연한 매치"로 넘기지 말 것** — 2GB 에서
  4바이트 패턴이 우연히 나올 기대값은 0.5회라 전부 진짜 엔트리다.
- **FSB5 이름 테이블에 개수 접두어는 없다.** `numSamples` 개의 uint32 오프셋 배열로
  바로 시작하고 문자열은 **널 종료**다. 첫 오프셋이 곧 `4 × numSamples` 라서 그걸
  개수로 읽으면 **정확히 4배**가 나온다(Hades VO 19,597 → 78,388 로 실제로 틀렸다).
  고친 뒤 샘플 28,290 = 이름 28,290 으로 맞는다. 오디오 **바이트**는 별개다 — FSB5
  Vorbis 는 코덱 헤더를 뱅크 밖 공용 코드북에 두고 잘라내므로 재생용 복원은 추가 작업.
- **FMOD `.strings.bank`(RIFF/FEV)의 STDT 는 접두어 공유 트라이다.** 8바이트 노드
  (u24+char / u24+u8)까지 보이지만 공개 스펙이 없다 — 검증 없이 풀면 틀린 이벤트 경로가
  나오므로 **재구성하지 않고** 널 종료 조각(Hades 2,334개 · 고유 1,665)과 루트
  네임스페이스만 낸다. 잘못 푼 매핑은 매핑 없음보다 나쁘다(카탈로그와 같은 원칙).
- Factorio 기준치(Steam, v2.0.77, **base 만** — Space Age DLC 미구매):
  `factorio.exe --dump-data` 가 정본이다. **Lua 를 파싱하지 말 것** — data.lua 단계를
  전부 거친 최종 상태를 JSON 으로 주고 mod 결과까지 반영한다. 프로토타입 224종 ·
  인스턴스 **2,800개**(`parameter-0~9` 제외 — 아래 참고).
  **설계 xlsx 20시트**: Recipes 217 · Technologies 196 · Items 253 · **Entities 292** ·
  Machines 36 · Power 12 · Logistics 49 · Enemies 15 · Combat 47 · Fluids 19 ·
  Modules 9 · Equipment 17 · Tiles 52 · Resources 38 · MapGen 133 · MapSettings 1,238 ·
  Signals 154 · Achievements 59 · Categories 208 · **Coverage 224**.
  **리소스 xlsx 5시트**: 그래픽 4,766장(1,108MB · 32억 픽셀) · 사운드 1,858개(149MB) ·
  현지화 50개 언어 키 287,790 · 기타 15종. 상세는 `out_factorio/README.md`.
- **전수 조사는 커버리지 대조표로 증명할 것.** Factorio 224종 중 179종 전부 반영 /
  7종 일부 / 38종 미반영인데, 미반영 861개는 전부 파티클·스프라이트·단축키 같은
  **비설계값**이다. 이걸 "추측"이 아니라 **각 인스턴스 이름이 실제로 어느 시트
  A열에 있는지 대조**해서 채운다 — 그래야 빠뜨린 설계축이 드러난다(1차에 99종이던
  것이 Entities·Achievements·Signals·MapGen 을 채우자 179종이 됐다).
  같은 이유로 **빈 셀을 남기지 말 것** — Factorio 엔티티 292개 중 건설비용이 없는
  204개에 전부 사유를 적었다(자연물 158 · 시나리오 배치물 18 · 에디터 전용 16 ·
  rail-planner 6 · 캡슐 투척 3 …). 빈칸은 "없다"와 "못 찾았다"를 구별하지 못한다.
- **Factorio 의 `parameter-0`~`parameter-9` 는 커버리지 집계에서 뺄 것.** 블루프린트
  파라미터용으로 **모든 프로토타입 종류마다 같은 이름**이 생긴다. 그냥 세면 무관한
  종류가 "일부 반영"으로 잡힌다 — `simple-entity` 가 Fluids·Items·Recipes 에 10개씩
  걸린 것이 그 착시였다(실제로는 한 개도 안 겹친다).
- **Factorio 스트림 공격은 데미지가 본체에 없다.** 웜·스피터·화염방사기는
  `attack_parameters.ammo_type.action.action_delivery` 가 `{type: stream,
  stream: "acid-stream-worm-big"}` 로 **별도 프로토타입**을 가리키고 실제 damage 는
  거기 있다. 따라간 뒤 `damage_modifier` 를 곱해야 맞는다(스피터 12/24/36/60,
  웜 36/48/72/96). 안 따라가면 8종의 데미지가 통째로 빈 채 표가 완성돼 보인다 —
  비터는 근접이라 본체에 있어서 "적 데미지는 다 뽑혔다"로 착각하기 쉽다.
- 뷰어 아이콘 매핑 중 `splitObjects→PigCell`, `pixelWoodBlocks→HardPixel`(PixelFlow)과
  블록타입 id ↔ `card*` 스프라이트(SheepNSheep)는 이름 기반 **추정** 매핑 — 정정되면
  해당 config만 고치면 된다.
