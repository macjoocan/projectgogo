# Soulbound Steam 설치본 조사 및 이미지 추출

2026-09-30. 입력 `D:\SteamLibrary\steamapps\common\Soulbound`.
원본 읽기 전용. 게임/EXE/DLL 실행, 로그인, 서버 요청, 원본 변경 없음. 별도 연구 폴더이며 levelscope 코어에 통합된 기능은 아니다.

## 2차 완료 — 이미지와 프레임 탐색

**`Soulbound_assets.html`을 브라우저에서 직접 열면 된다.** 같은 폴더의 catalog.js / frames / atlases를 함께 유지한다. 이름 검색, 페이지 이동, 다중 프레임 필터, 프레임 재생/선택, 저장 원점 표시, PNG/아틀라스 링크를 제공한다.

| 검증 항목 | 결과 |
|---|---:|
| TXTR 아틀라스 PNG | 344 / 344 |
| TPAG 영역 PNG, 투명 여백 복원 | 17,533 / 17,533 |
| SPRT 이름·원점·크기·프레임·속도 | 4,300 / 4,300 |
| 다중 프레임 스프라이트 | 1,663 |
| 스프라이트 전체 프레임 슬롯 | 17,734 |
| 그중 이미지 참조 | 17,487 |
| 그중 원본 null 참조 | 247 — 누락 이미지로 대체하지 않음 |
| PNG 합계 | 61,293,503 bytes, 약 58.5 MiB |

전수 검사: 모든 BZip2 eof/길이, QOI 픽셀 개수/스트림 소비량(잔여 0바이트), PNG 재열기 및 픽셀 해시, 원본 아틀라스 crop과 복원 프레임 픽셀, 영역 경계, 이미지 참조 확인. 원본 data.win SHA256 변경 없음. 픽셀 리사이즈가 필요한 영역은 0개였다. 전체 TPAG 중 46개는 SPRT 프레임에서 참조되지 않지만 함께 보존했다(다른 자원 사용처는 미연결).

원본 메타데이터 불일치 2종은 보존했다: `sDCMobHealthbarStatic` SPRT 36×13 / TPAG 36×14 (7프레임), `sMovementMask` SPRT 12×7 / TPAG 12×6 (1프레임). PNG는 TPAG 바운딩 크기를 유지하고 뷰어는 양쪽 크기를 수용하므로 강제 잘라내지 않는다.

뷰어는 생성했지만 **브라우저 실제 클릭/재생 검증은 미완료**다. 도구의 브라우저 보안 정책이 file:// 열기를 차단했으며 우회하지 않았다. PNG 표본은 직접 시각 확인했고, 뷰어 JS와 catalog.js는 Node --check 구문 검사를 통과했다. 프레임 속도 형식은 FPS 4,172종 / 게임 프레임당 배율 128종이다. 후자는 실제 게임 속도가 미확정이므로 미리보기 기본 12 FPS로 표시한다. 저장 속도와 미리보기 속도를 구분한다.

`contact_sheet.png`는 전체 색인에 고르게 분산된 48종 표본이다. 게임의 최종 셰이더/합성/스켈레톤 애니메이션을 재현했다는 뜻은 아니다.

## 확인한 것

**GameMaker 계열의 Windows x64 클라이언트**다. data.win의 FORM 컨테이너와 GEN8/SPRT/OBJT/ROOM/SCPT/TXTR 등 엔진 고유 청크, options.ini의 LLVM-WINDOWS 설정을 확인했다. 기존 RoyalSmash의 Unity/IL2CPP 도구에 바로 넣는 대상은 아니다.

data.win **41,782,136 bytes**, FORM 선언 크기와 실제 크기 일치. 전체 청크 31개를 끝까지 순회했다. 아래 항목의 테이블 포인터를 청크 경계 안에서 검증했고, 이름이 있는 자원의 문자열 참조 오류는 0건이다.

| 종류 | 색인 항목 수 | 이번 완료 범위 |
|---|---:|---|
| 스프라이트 SPRT | 4,300 | 이름/주소 및 프레임/원점/크기/속도 연결 |
| 배경·타일셋 BGND | 10 | 이름/주소 색인 |
| 오브젝트 OBJT | 684 | 이름/주소 색인 |
| 룸 ROOM | 24 | 이름/주소 색인; 전체 게임 맵 수라는 의미 아님 |
| 스크립트 SCPT | 48,591 | 이름/주소 색인; 함수 본문 복원이 아님 |
| 셰이더 SHDR | 164 | 이름/주소 색인 |
| 폰트 FONT | 24 | 이름/주소 색인 |
| 사운드 SOND | 234 | 이름/주소 색인 |
| 내장 오디오 AUDO | 232 | 포인터 테이블 검증 |
| 텍스처 TXTR | 344 | 전체 PNG 디코딩 |
| 텍스처 영역 TPAG | 17,533 | 전체 영역 PNG/배치 메타데이터; 스프라이트 수와 다름 |

외부 파일에는 비 소리 OGG 2개와 TTF 2개, 소개 MP4 1개도 있다. SOND 234와 AUDO 232의 차이를 누락으로 단정하지 않는다. 사운드별 참조 배선은 아직 하지 않았다.

## 이미지 경로

TXTR는 `2zoq` magic 및 12바이트 뒤 BZip2 stream, 해제 결과 `fioq` 헤더를 가진 GameMaker 전용 QOI다. 일반 QOI 디코더와 호환된다고 가정하지 않았다. `texture_probe.json`은 초기 표본 조사이고, 전체 디코딩 결과는 `export_validation.json` / `validation.json`이다.

이미지·프레임·원점 연결은 완료했다. 다음 미완료 범위는 충돌 마스크/sequence/nine-slice 상세 해석, 오디오 및 오브젝트/룸 배선이다. sequence/nine-slice는 주소만 보존했고 본문은 해석하지 않았다.

## 코드와 서버 데이터의 경계

data.win에는 **CODE 청크가 없다**. LLVM-WINDOWS 설정과 x64 EXE가 함께 있어 **YYC 네이티브 빌드로 판단**한다. SCPT 48,591개는 스크립트/함수 이름 엔트리이지 복원된 GML 코드가 아니다. 일반 GameMaker VM 디컴파일 경로를 적용했다고 주장할 수 없다. 실행 파일 내 함수 대응/역어셈블은 별도 작업이다.

libgmcurl.dll / libgmwebsocket.dll 및 web_dyn_tex 확장 설정이 있다. 네트워크·동적 텍스처 기능의 존재 근거이며, 어떤 맵/밸런스가 서버 전용인지는 아직 판독하지 않았다. 로컬 룸 24개로 서비스 전체 맵을 확보했다고 쓰지 않는다. env 내용은 이번 산출물에 포함하지 않았다.

## 산출물

- `survey_install.py`: 의존성 없는 읽기 전용 FORM/리소스 이름 색인 도구.
- `survey.json`: 원본 SHA256, 설치 파일 목록, 청크 경계, 이름 색인.
- `probe_textures.py` / `texture_probe.json`: 텍스처 표본 검증. PNG가 없다는 이유로 실패/암호화로 분류하지 않는다.
- `extract_assets.py`: GameMaker 전용 QOI와 TPAG/SPRT 읽기, PNG 추출. `--sample`은 처음 2개 아틀라스만 처리한다.
- `validate_assets.py`: 전수 PNG/픽셀/참조/원본 해시 검사. `validation.json` 생성.
- `build_catalog.py`: `catalog.js`와 `contact_sheet.png` 생성.
- `sprite_metadata.json` / `atlas_metadata.json`: 원본 주소, 인덱스와 출력 파일 연결.
- `Soulbound_assets.html`: 로컬 탐색기. 웹 서버나 게임 로그인 불필요.

재실행 순서: Python 3 + Pillow 환경에서 `extract_assets.py` → `validate_assets.py` → `build_catalog.py`. 이 PC에서는 Blender 5.2 내장 Python과 기존 `out_royalsmash/cdn_extraction_deps`의 Pillow 12.3.0을 사용했다. 의존 경로는 스크립트에 명시되어 있다.

이번 완료 범위는 설치본 색인과 내장 래스터 이미지 추출이다. 전체 에셋·플레이·네이티브 규칙·서버 맵 복원은 완료하지 않았다. 공개 저장소나 외부 서비스에 게임 리소스를 업로드하지 않았다.

## 참조

- [UndertaleModTool 프로젝트](https://github.com/UnderminersTeam/UndertaleModTool): GameMaker 데이터/자원 분석 도구. YYC는 VM 코드 디컴파일 대상이 아니다.
- [공식 CLI 구현](https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModCli/Program.cs): YYC일 때 코드가 실행 파일에 있음을 명시.
- [EmbeddedTexture 모델](https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModLib/Models/UndertaleEmbeddedTexture.cs): 텍스처 헤더와 QOI/BZ2 포맷 구분 근거. 제3자 라이브러리 자체를 이번에 설치하거나 실행하지는 않았다.
- [QoiConverter](https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModLib/Util/QoiConverter.cs): GameMaker 전용 픽셀 디코더 근거. 포팅한 추출 도구의 GPL 라이선스와 원문은 `references/`에 보존했다. 게임 에셋의 권리는 도구 라이선스와 별개다.
