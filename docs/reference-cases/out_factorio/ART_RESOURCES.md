# Factorio 아트·오디오 리소스

대상: Steam 기본 게임 2.0.77, core + base. **설치 데이터 전체 8,673개 파일 / 1,498,116,904바이트를 raw/data에 원형 보존했다.** 복사본 SHA256을 각각 원본과 대조했다. 실행 파일·PDB는 아트/데이터 사본에 넣지 않았고 C++ 엔진 소스는 복원하지 않았다.

## 확보 범위

| 종류 | 수량 | 상태 |
|---|---|---|
| PNG | 4,765 | 4,764개 디코딩 가능; 원본 0바이트 1개 별도 보존 |
| JPG | 1 | 디코딩 확인 |
| 이미지 미리보기 | 4,765 | 유효 PNG + JPG 전체 |
| OGG | 1,858 | 전체 복사·해시·페이지 구조 검증 |
| TTF | 35 | 글꼴 원본 보존 |
| Lua | 394 | 프로토타입·시나리오·도우미 원문 |
| CFG | 1,180 | 번역 등을 원문 보존 |
| ZIP | 40 | 총 86개 내부 엔트리 목록·CRC 검사 |
| 셰이더 | 306개 소스 + CSO 3 | metal/frag/psh/vert/vsh와 컴파일 파일 |

ZIP에는 메뉴 시뮬레이션·지도·블루프린트 등의 게임 바이너리도 포함된다. 보존 및 CRC 검증은 완료했지만 내부 map/blueprint 바이너리를 사람이 읽는 맵 좌표 목록으로 변환한 것은 아니다. dat·셰이더 바이너리도 원형 보존 범위다.

## 아트 구성 방식

이 설치본의 게임 아트는 PNG 시트와 Lua의 스프라이트 정의를 연결한다. 원본 제작용 Blender/FBX 프로젝트는 설치 데이터에서 찾지 못했다. 입체적으로 보이는 설비라도 설치된 파일은 방향·프레임·그림자 등으로 나뉜 이미지다.

- `filename` / `filenames` / `stripes`: 파일 한 장, 여러 장, 스트라이프 구성.
- `width`, `height`, `x`, `y`, `line_length`: 시트에서 자를 셀의 위치와 크기.
- `frame_count`, `direction_count`, `variation_count`: 시간 프레임·방향·변형을 구분.
- `layers`, `shift`, `scale`, `tint`: 여러 장 합성, 위치와 크기, 색상.
- `draw_as_shadow`, `draw_as_glow` 등: 본체와 다른 렌더링 역할.
- 아이콘의 `icons` 배열: 하나의 PNG가 아니라 여러 아이콘·마스크 합성일 수 있다.

따라서 시트 전체를 스프라이트 한 장으로 붙이면 크기·방향·그림자가 어긋난다. 아이콘 오른쪽의 작은 반복 그림은 mipmap일 수 있어 애니메이션으로 보면 안 된다.

프로토타입에서 파일 경로 참조 20,653건, 고유 경로 6,417개를 수집했다. 단일 파일 셀 구조 10,157건을 보존했고, 경계 검사가 통과한 다중 셀 항목 3,281건은 탐색기에서 첫 방향·단일 레이어로 볼 수 있다. 여러 프로토타입의 같은 참조가 포함되므로 고유 애니메이션 수가 아니다.

기본 재생은 편의를 위한 12 FPS다. 저장 `animation_speed`의 명목 속도는 60×값 FPS지만, 실제 게임에서는 설비 가동률 등 사용처에 따라 달라진다. 미리보기는 tint·전체 방향·레이어·그림자·run_mode를 원작처럼 합성하는 렌더러가 아니다.

## 빠졌거나 비어 있는 원본

1. `data/core/graphics/arrows/tip-arrow.png`: **원본부터 0바이트**. 복사 손상이 아니다. 프로토타입 파일 참조 목록에는 없었다.
2. `__base__/graphics/entity/bigass-explosion/hr-bigass-explosion-36f.png`: `explosion/big-artillery-explosion → animations/0/filename`이 참조하지만 원본 설치 폴더에 없다. 폭발 이미지 복원 완료로 표시하지 않았다. 사용되지 않는 잔재인지 설치 누락인지는 미확인이다.
3. `.bnvib` 166회 참조: switch_vibration_data 등 진동 관련 경로이며 해당 파일은 설치본에 없다. 고유 파일 수와 참조 횟수는 다르다. Windows 실제 사용 여부까지 검증하지 않았다.

나머지 이미지/오디오 파일 참조는 존재한다. headless 데이터 덤프 성공은 모든 그래픽이 실게임에서 렌더링된다는 검증이 아니다.

## 열어보기

- [아트·데이터 탐색기](Factorio_explorer.html): 한글/영문 검색, 원본 링크, 시트 미리보기, 프레임 셀, 오디오.
- [아트 표본 48개](art_overview.png): 실제 PNG 표본, 시트/mipmap 전체를 보여준다.
- [이미지 목록](image_manifest.json), [오디오 목록](audio_manifest.json), [모든 파일·해시](file_manifest.json).
- [파일 참조 원장](analysis/asset_references.json), [스프라이트 메타데이터](analysis/sprite_descriptors.json), [ZIP 내부 목록](analysis/archive_manifest.json).

오디오는 페이지 경계와 Vorbis 식별 헤더·길이를 검사했다. 모든 파일을 청취하거나 코덱 전체를 디코딩한 검사는 아니다. 글꼴·셰이더도 게임 내 표현을 전수 검증하지 않았다. HTML 브라우저 실조작은 미검증이며 JS 구문과 파일 연결을 별도로 점검했다.
