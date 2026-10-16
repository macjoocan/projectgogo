# Factorio 2.0.77 — 아트·데이터 통합 조사

2026-10-01. 입력 `D:\SteamLibrary\steamapps\common\Factorio`. core + base만 설치된 기본 게임이다. **설치 data 폴더 전체를 보존하고, 게임 공식 headless 기능으로 최종 data.raw·한국어 명칭·지도 미리보기를 생성했다.**

먼저 [Factorio_explorer.html](Factorio_explorer.html)을 열면 된다. 한글/영문 검색, 원본 이미지, 단일 시트 셀 재생, 오디오, 프로토타입, 제작법 생산량, 기술 해금, 맵 비교를 제공한다. HTML만 복사하지 말고 catalog.js·thumbnails·raw·prototypes를 함께 유지한다.

| 결과 | 수량 |
|---|---|
| 원본 data 파일 복사·SHA256 대조 | 8,673개 / 1,498,116,904바이트 |
| PNG | 4,765개 (원본 0바이트 1개 포함) |
| JPG / 오디오 / 글꼴 | 1 / 1,858 / 35 |
| Lua 원문 | 394개 |
| 최종 프로토타입 | 224유형 / 2,840개 |
| 제작법 / 기술 / 아이템 계열 | 217 / 196 / 251 |
| 파일 경로 참조 | 20,653건 |
| 맵 노이즈 식 / 함수 | 92 / 28 |


- [아트 리소스 구조와 누락 목록](ART_RESOURCES.md)
- [데이터·밸런스 조사와 실값](DATA_BALANCE.md)
- [맵 제작·생성 방식 및 실제 샘플](MAP_GENERATION.md)
- [Farmtorio 추가 전달 자료](farmtorio_handoff/README.md): 퀵바·피커·튜토리얼 순서·제작법별 벨트 비율 551행.
- [아트 표본](art_overview.png), [최종 data.raw JSON](run/script-output/data-raw-dump.json)
- [전체 파일·해시](file_manifest.json), [검증 상세](analysis/validation.json), [최종 검증](validation_final.json)

**확인된 원본 문제:** tip-arrow.png는 0바이트다. big-artillery-explosion이 참조하는 hr-bigass-explosion-36f.png는 설치 폴더에 없고, 진동용 .bnvib도 166회 참조되지만 없다. 임의 이미지로 채우지 않았다. 일반 제작/기술 참조 누락 및 기술 선행 순환은 0개다.

범위: 설치된 모든 data 파일 보존 + 실제 기본 게임 데이터 덤프 + 구조/밸런스/맵 조사. C++ 엔진 소스, 제작용 3D 원본, Space Age, 사용자 모드·세이브, 모든 시트의 합성 렌더러, 저장 바이너리 맵의 전체 좌표 변환은 포함하지 않는다. 따라서 '설치 데이터 전체 확보'와 '게임 전체 소스 복원'을 구분한다.

원본 설치 파일을 수정하지 않았다. CLI는 run/config.ini와 run/mods를 사용했고 개인 설정·세이브·인증을 읽는 대신 별도 쓰기 경로를 사용했다. 로그에 local/cloud player-data unavailable이 기록된다. 로그인·멀티플레이 서버 접속·구매·광고는 수행하지 않았다. 리소스는 로컬 연구 폴더에만 보존했다. 권리 문서: [eula](raw/data/eula.txt), [licenses](raw/data/licenses.txt).

## 재현과 검증 한계

1. `survey_extract.py`: 전체 복사·해시, 이미지 컨테이너, OGG 페이지 검사.
2. CLI `--dump-data`, `--dump-prototype-locale`: 최종 기본 게임 데이터와 한국어 명칭.
3. `analyze_data.py`: 유형별 JSON, 자산 참조, 제작/연구 그래프, 썸네일.
4. `write_reports.py`, `validate_delivery.py`: 보고서와 최종 검증.

Python은 Blender 5.2 내장 Python, Pillow는 기존 out_royalsmash/cdn_extraction_deps를 사용했다. 설치·사용 환경 경로는 스크립트에 명시되어 있다. 게임 데이터 실행과 맵 생성은 공식 Factorio CLI만 사용했다.

HTML은 JS 구문과 렌더 함수의 정적/모의 실행을 검사하지만 실제 브라우저 클릭·오디오 재생·Canvas 렌더는 미검증이다. 오디오는 전수 청취하지 않았고 프로토타입 값으로 계산한 생산량은 병목 없는 이론값이다. 계산 출처와 제외 조건은 보고서에 표기했다.
