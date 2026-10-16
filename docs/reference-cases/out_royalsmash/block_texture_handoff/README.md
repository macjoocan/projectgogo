# 블록 재질 텍스처 인수인계

2026-09-16. 프로토 `C:\00.SVN\MiniApp\_reference\royalsmash\data\block-shader-params.json`의 51개 이름을 원본 Material 목록과 대조했다.

## 전달 결과

- 이름51개 모두 발견. 동명 Material이 있어 **원본 Material 오브젝트54개**를 구분 보존.
- null이 아닌 Texture 참조 **104/104곳**을 정확한 원본 파일+path_id로 연결. 오류0.
- 연결된 Texture2D **73개**를 `textures/`에 PNG 추출, 파일별 다시 열기 검증 완료.
- `manifest.json`의 `materials[].texture_slots`에 슬롯 이름, source file/path_id, texture_id, PNG, 원본 UV scale/offset.
- `textures[]`에 원본 texture명, APK 경로/ID, 해상도, 원본 texture format/color_space/mip_count, filter/wrap/aniso 설정, 원본 stream 경로, PNG SHA256.
- 보존된 APK만 읽었다. 기존 프로토/원본/추출 ZIP 변경 없음. `block_textures_verified.zip`에는 manifest에 등재된 PNG만 담는다. 폴더 파일 수가 아닌 manifest를 기준으로 사용할 것.

## 주요 이미지 예

| 용도/표본 | PNG |
|---|---|
| TableSquare 기본 표면 | `textures/000_Table_Square_v02.png` (2048²) |
| TableSquare MatCap | `textures/001_2_matcap.png` (256²) |
| Wood 기본 표면 | `textures/002_wood-f-10.png` (1024²) |
| 금속 MatCap | `textures/004_Metal-3_matc.png` (1024²) |
| 항아리 기본/마스크/MatCap | `007_jar_texture_v3_blue_2`, `008_jar_purple_mask`, `009_blue-p-1` |
| Bounce 기본/노멀 | `019_Bounce_x5_v03_lambert2_BaseMap`, `020_Bounce_x5_v03_lambert2_Normal` |
| 얼음 표면/거칠기 이름 텍스처 | `039_ice_Square_v02`, `040_Ice_Roughness` |
| ColorBox Blue MatCap | `textures/062_CB_blue.png` (256²) |
| 대포 AO/기본색 | `071_Cannon_s_Mixed_AO_Raw`, `072_Cannon_s_Base_color_sRGB` |

위 짧은 이름은 `textures/` 아래 `.png`다. 실제 역할은 **파일명 대신 manifest의 property 슬롯**으로 판정해야 한다. 일부 프로퍼티는 현재 셰이더가 사용하지 않는 과거 설정일 수 있다.

## 프로토에 반영할 때

1. Material명 하나만으로 덮어쓰지 말고 동명 source identity를 구분한다. 이번 결과는 재질→텍스처 연결이며 프리팹/Renderer→Material 슬롯 연결을 새로 검증한 결과는 아니다.
2. `_MainTex`/`_BaseMap`은 보통 mesh UV, MatCap은 카메라/노멀 기반 좌표다. 두 매핑을 혼용하지 않는다. 원본 UV/노멀·필요시 tangent가 프로토 메시에서 유지됐는지 확인한다.
3. scale/offset과 샘플러 wrap/filter를 보존한다. PNG에는 원본 mip chain·압축 포맷·Unity sampler 상태가 모두 들어가지 않는다. manifest를 함께 사용한다.
4. 기본색과 데이터 맵(노멀/마스크)의 색공간 처리를 분리한다. 원본 `color_space` 수치를 그대로 기록했지만 대상 엔진 설정과 해석을 검증해야 한다. sRGB 변환을 이중 적용하지 않는다.
5. **ColorBox Blue에 BaseColor도 MatCap도 있다.** 활성 TCP2_MATCAP, UseMatCap1, MatCapType1, CB_blue 참조. OmniShade와 Toony 합성식을 구분한다. `../shader_program_analysis/README.md` 및 실제 GLSL 참조.
6. 참조가 존재한다는 사실과 해당 셰이더 변형에서 실제 샘플한다는 사실은 다르다. 사용하지 않는 프로퍼티까지 모두 강제로 적용하지 않는다.

전체 게임 텍스처 전수 추출이 아니라 요청된 **현재 프로토51개 재질 이름**에 한정한 검증이다. PNG 픽셀 추출 성공이 원작 화면과의 렌더링 일치까지 의미하지는 않는다.
