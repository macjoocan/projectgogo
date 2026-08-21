# 새 게임 분석 가이드

처음 보는 모바일 게임 패키지 하나를 받았을 때, 무엇을 어떤 순서로 하는지에 대한 실전
안내다. 명령 하나하나의 옵션은 `MANUAL.md`, 코드 수정 규칙은 `CLAUDE.md` 를 본다.

예시는 2026-08-20 에 실제로 뜯은 **CookieRun: Crumble**(Unity 6000.3.15f1, 459MB xapk)
이다. 수치는 전부 그때 실측값이다.

---

## 0. 시작 전 — 30초짜리 확인

패키지가 뭔지, 무엇이 들어 있는지부터 본다. 이걸 건너뛰면 엉뚱한 게임을 분석한다
(실제로 한 번 그랬다 — 방치형이라고 생각한 파일이 매치3였다).

```bash
python -c "import zipfile,json; z=zipfile.ZipFile(r'<입력>'); \
print([n for n in z.namelist() if n.endswith('.apk')]); \
print(json.loads(z.read('manifest.json')).get('package_name'))"
```

보는 것:

- **패키지명·앱 이름** — 기대한 게임인가
- **내부 apk 구성** — `config.arm64_v8a` / `config.x86_64` 중 무엇인가(ABI),
  `UnityDataAssetPack` 같은 에셋 팩이 따로 있는가
- **크기** — 400MB 이상이면 콘텐츠가 APK 안에 있다는 뜻이고, 100MB대면 상당량이 CDN이다

## 1. `survey` — 설정 없이 프로파일

```bash
python -m levelscope survey --input <입력> --configs configs
```

22초 · 0.8GB 로 이런 걸 알려준다.

- 엔진 버전 / IL2CPP 여부
- Unity 소스 목록과 오브젝트 수
- 리소스 규모(Sprite / Texture2D / MonoBehaviour / GameObject …)
- 씬 목록
- Addressables 카탈로그 해독 결과 — **APK 에 없는 번들(= CDN 배포분)까지 알려준다**
- 레벨 후보와 인코딩 추정, `configs/_suggested_<게임>.yaml` 초안

**꼭 확인할 두 줄:**

```
[discover] Unity 소스 N개 발견 (오브젝트 합계 ...) · 후보였지만 Unity가 아닌 것 M개
[survey] 카탈로그 번들 N개 중 M개가 APK에 없습니다
```

- `후보였지만 Unity가 아닌 것` 이 0이 아니면 의심한다. Unity 6000 대 번들은 헤더에
  버전이 없어 예전에는 여기서 통째로 빠졌다(그래서 게임의 3%만 뽑던 사고가 있었다).
  지금은 자동으로 버전을 배워 재시도하지만, 그래도 숫자를 본다.
- 카탈로그 번들이 전부 "APK에 없다"고 나오면 **콘텐츠가 서버 배급**이다. 그건 이 도구로
  가져올 수 없고, 가져오려 하지도 않는다(§6).

## 2. 설정 — `fields: auto` 로 시작

`_suggested_*.yaml` 초안을 `configs/<게임>.yaml` 로 옮기고, 컬럼은 손으로 적지 않는다.

```yaml
game: MyGame
input:
  levels_glob: "assets/data/**/*.json"     # 또는 input.unity (에셋형)
codec: auto
fields: auto        # 표본 200개에서 컬럼 자동 추론
outputs: [xlsx, zip, sprites, assets, hierarchy]
```

`board` / `palette` 와 `outputs` 의 `html` 은 **보드형(퍼즐·매치3) 전용**이다. RPG·방치형·
슈터면 그 세 개를 빼면 된다.

`fields: auto` 로그에서 이 줄들을 본다.

```
[fields] auto: 표본 N개에서 컬럼 M개 추론 (값 x · 개수 y)
[fields] auto: 값 종류가 갈려 N개 제외 — ...
[fields] auto: 상한(60개)에 걸려 N개 제외 — ...
```

제외된 게 많고 그중 중요한 필드가 있으면, 그때만 `fields` 를 손으로 적는다.

## 3. 추출

먼저 작게 돌려 설정 실수를 일찍 잡는다.

```bash
python -m levelscope run --config configs/<게임>.yaml --input <입력> --out out --limit 20
```

그다음 전체. 무거운 단계는 따로 돌려도 된다.

```bash
python -m levelscope run       --config configs/<게임>.yaml --input <입력> --out out
python -m levelscope sprites   --input <입력> --out out --game <게임> --types Sprite,Texture2D --max 40000
python -m levelscope assets    --input <입력> --out out --game <게임> --max 40000
python -m levelscope hierarchy --input <입력> --out out --game <게임> --max-nodes 300000
```

**상한을 넉넉히 준다.** 기본값(`--max 1000`, `--max-nodes 200000`)은 큰 게임에서 잘린다.
잘리면 로그가 `max_count(...) 도달로 중단` 이라고 말해 주니 그걸 보고 올린다.

소스가 여러 번들에 고르게 퍼진 게임은 `--split` 으로 소스별 zip 으로 나눌 수 있다.
한 번들이 대부분을 차지하는 게임에서는 메모리 이득이 없다(§5).

## 4. 검증 — 이것만 보면 된다

| 확인 | 정상 |
|---|---|
| `[decode] 성공 N / 실패 0` | 실패 0. 아니면 `out/<게임>_errors.txt` 와 `detect --xor-scan` |
| `[sprites] N개 추출 (실패 M개)` | 실패 사유를 읽는다. `픽셀 데이터 없음 (0x0 …)` 은 정상(런타임 생성 텍스처) |
| `[hierarchy] … truncated=False` | `True` 면 `--max-nodes` 를 올린다 |
| `[typetree] MonoBehaviour x/y 복원` | 90% 이상이면 충분. 낮으면 §6 |
| `survey` 의 리소스 수 ↔ 산출물 수 | Sprite 수가 zip 항목 수와 대체로 맞는가 |

`survey` 가 말한 리소스 수보다 산출물이 **크게** 적으면 소스가 빠진 것이다. 이게 이 도구에서
가장 자주 났던 사고다 — 개수를 꼭 대조한다.

## 5. 메모리 — 지켜야 할 선

실측(오브젝트 597,791개짜리 게임, 단계별 최고 커밋):

| 단계 | 최고 커밋 |
|---|---|
| `survey` | 3.7GB |
| `sprites` (10,443장) | 4.3GB |
| `assets` (322개) | 4.0GB |
| `hierarchy` (노드 112,901개) | 4.3GB |
| `run` 전체 | 약 4.5GB |

- 피크는 **가장 큰 번들 하나를 여는 값**으로 정해진다. `UnityPy.load()` 가 오브젝트
  58만 개를 파싱하는 데 1.83GB 든다. 우리 코드가 얹는 건 0.02GB 뿐이다.
- **돌리기 전에 여유를 본다.** 커밋 여유가 8GB 미만이면 안 쓰는 Unity 에디터를 닫거나
  `wsl --shutdown` 으로 회수하고 시작한다.
- 한 번에 **하나만** 돌린다. 여러 단계를 동시에 띄우지 않는다.
- `survey` 가 오브젝트 100만 개 이상을 보고하면 통짜 실행 전에 `--source` 로 번들 하나씩
  나눠 돌리는 걸 먼저 고려한다.

이 도구는 스스로 메모리 상한을 걸지 않는다. 걱정되면 상한 감시를 붙여 실행한다
(그러면 한계를 넘을 때 PC 가 멈추는 대신 프로세스만 죽는다).

## 6. 자주 막히는 지점

**컴포넌트 필드가 대부분 비어 있다**

`[typetree] 모든 백엔드 초기화 실패` 가 보이면 IL2CPP 메타데이터 버전을 확인한다.

```bash
python -c "import struct; d=open('global-metadata.dat','rb').read(16); \
print(struct.unpack_from('<II', d)[1])"
```

버전 39(Unity 6000.3 세대)는 `TypeTreeGeneratorAPI` 백엔드 3종과 Il2CppDumper 6.7.46
모두 아직 못 읽는다. **CPU 아키텍처 문제가 아니므로 arm64 빌드를 구해도 같다.**
다만 번들이 타입트리를 자체적으로 품고 있으면 IL2CPP 없이도 98% 넘게 읽힌다 — 먼저
`기본 읽기로 x/y` 줄을 확인한다.

**번들 해시 이름이 뭔지 모르겠다**

Addressables 카탈로그를 해독하면 원본 프로젝트 경로가 나온다. `catalog.json`(구형)과
`catalog.bin`(Addressables 1.21+ / Unity 2023+) 둘 다 읽는다. 바이너리 쪽은
`pip install addressablestools` 가 있어야 매핑까지 풀린다(없으면 문자열 목록만).

**콘텐츠가 APK 에 없다**

카탈로그가 "번들 N개가 APK에 없다"고 말하면 서버 배급이다. 주소는 보통 APK 안에
없고(`{...RemotePath.LoadPath}` 같은 런타임 치환자), 클라이언트가 로그인 후 서버에
물어본다.

**여기서 멈춘다.** 우리가 하는 일은 *가진 파일*을 정적 분석하는 것까지다. 게임 CDN 에서
번들을 내려받거나, 설정·인증 엔드포인트를 호출하거나, 기기 트래픽을 가로채는 것은
상대 회사 서버를 건드리는 일이고 ToS·법무 영역이다. 주소를 찾아냈다는 사실만 보고하고
접근하지 않는다.

## 7. 산출물 정리

```
out/<게임>_summary.xlsx           표 (Levels + 엔티티 + Summary 수식)
out/<게임>_viewer.html            보드형 게임만 — 그리드 렌더
out/<게임>_levels_decoded.zip     디코딩 평문 JSON
out/<게임>_sprites.zip            스프라이트·텍스처 PNG
out/<게임>_assets.zip             오디오·머티리얼·폰트·Spine·텍스트 + manifest.json
out/<게임>_hierarchy.zip          씬·프리팹 트리 JSON + index.json
out/<게임>_errors.txt             실패가 있을 때만
```

`out/` 과 추출한 이미지는 커밋하지 않는다. 재현에 필요한 것은 `configs/<게임>.yaml`
하나이므로 **그것만 저장소에 남긴다.**

### 산출물을 다시 읽을 때 두 가지

**① `out_*/*_sprites.zip` 을 glob 으로 긁지 말고 경로를 명시한다.** 같은 게임의 **구버전
zip 이 다른 폴더에 같은 이름으로** 남아 있을 수 있다. 실제로 `out_final\ZenMatch_sprites.zip`
은 79장짜리 초기 추출본이고 현행(`out_zenmatch\`)은 6,546장이다. glob 순서에 따라 구버전이
현행을 덮어쓰면 **장수가 줄어든 것을 알아채기 어렵다.**

**② 압축을 푼 뒤에는 zip 엔트리 수가 아니라 디스크 파일 수를 센다.** 이름이 대소문자만
다른 스프라이트가 실제로 있어서(원본이 `Facebook`/`FaceBook` 을 혼용) Windows·macOS 에서
풀면 나중 것이 앞 것을 덮어쓴다. **zip 은 멀쩡하고 엔트리 수도 맞기 때문에 엔트리 수
대조로는 절대 안 잡힌다.** 실측으로 5개 게임에서 151장이 그렇게 사라지고 있었다
(v1.24.0+ 에서 `_2` 접미를 붙여 고쳤지만, 그 이전에 뽑은 추출본은 손실이 남아 있다).
