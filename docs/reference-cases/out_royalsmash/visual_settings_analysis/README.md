# Royal Smash 원본 재질·셰이더·카메라 위치

**후속 발견:** 실제 GLES 컴파일 GLSL 텍스트 OmniShade236개/Toony51개를 추가 확보했다. `../shader_program_analysis/README.md` 참조. 블록51개 재질 이름 기준 texture73개/정확한 참조104곳은 `../block_texture_handoff/README.md` 및 ZIP에 보존했다. 아래 원본 HLSL 미복구/옛 더미 셰이더 경고는 여전히 유효하지만, 실제 연산 코드가 전혀 없다는 뜻은 아니다.

확인일: 2026-09-16. 대상: Royal Smash 1.13.359. 원본 APK와 이미 받은 CDN 번들만 오프라인으로 읽었다. 게임/에뮬레이터 실행, 추가 다운로드, 인증·보호 우회 없음.

## 바로 사용할 자료

이 문서의 절대 경로: `D:\99.기타\out_royalsmash\visual_settings_analysis\README.md`.

| 파일 | 내용 |
|---|---|
| `materials.json` | 원본 APK 946개 + CDN 49개 Material 직렬화 값. source/APK/file/path_id, 셰이더 참조, 텍스처 참조, keywords, renderQueue, floats/colors/texture scale·offset 포함 |
| `shaders.json` | APK 113개 + CDN 38개 Shader의 이름·프로퍼티 선언·키워드·플랫폼·컴파일 데이터 크기. 원본 HLSL 소스가 아님 |
| `cameras.json` | 원본 씬 3개의 Camera 전체 설정, GameObject, Transform 및 부모 체인 |
| `camera_script_links.json` | 실제 씬 컴포넌트에서 정확한 외부 MonoScript 참조로 확인한 카메라 관련 스크립트 식별 |
| `camera_code_declarations.json` | dump.cs의 카메라 관련 클래스 선언과 원문 행 번호. 메서드 본문은 복원된 실행 코드가 아님 |
| `table_square_reference_evidence.json` | TableSquare → 실제 셰이더·메인 텍스처·MatCap 텍스처 연결을 원본 외부 파일+path_id로 검증한 표본 |
| `legacy_shader_export_check.json` | 기존 AssetRipper `.shader` 26개가 모두 더미 exporter 결과임을 확인한 파일별 기록 |
| `summary.json`, `validation.json` | 수량, 원본 SHA 검증, 파싱 한계와 검증 결과 |

수량은 **직렬화 오브젝트 수**다. 고유 재질 종류/셰이더 종류/실제 화면 사용 횟수가 아니며 폰트·엔진 내부 리소스와 중복도 포함한다. source `file`+serialized file+`path_id`를 함께 보존해야 한다. 바이트에서 직접 로드한 파일의 `serialized_file`은 도구 생성 이름일 수 있으므로 원본 `apk`/`file` 경로가 우선 출처다.

## 1. 기존 추출물 및 원본 위치

기준 폴더: `D:\99.기타\out_royalsmash`.

- 기존 읽기 쉬운 재질: `RoyalSmash_assets\material\*.json`, 원본 ZIP `RoyalSmash_assets.zip`의 `material/` 835개. 대부분 폰트/UI이며 shader 미해석 120개, null 6개가 있다. 미해석 표기는 원본에 셰이더가 없다는 뜻이 아니다.
- CDN 재질: `cdn_extracted\RoyalSmash_CDN_assets.zip`의 `material/` 49개. 원본 다운로드 번들은 `cdn_public\bundles\` 31개.
- 원본 APK: `lab_apks\com.cyphergames.royalsmash.apk`, `lab_apks\UnityDataAssetPack.apk`.
- 원본 XAPK: `C:\Users\NHN\Downloads\Royal+Smash!+-+Physics+Puzzle_1.13.359_APKPure.xapk`. 기존 원본 대조 SHA와 현재 APK 3개의 SHA 일치 재확인.
- 중요한 논리 파일: base APK의 `assets/bin/Data/globalgamemanagers.assets`, `sharedassets0.assets`; AssetPack의 `assets/bin/Data/sharedassets1.assets`(Material118/Shader9), `sharedassets2.assets`(Material5/Shader1), 해시 이름 직렬화 파일들, `assets/aa/Android/gameplaybackgrounds_local_assets_all.bundle`(Material6/Shader8).
- `.split0`, `.split1` 등은 숫자 순서로 연결해야 한 Unity 파일이 된다. 기존 835개 JSON만으로 원본 전체를 대표하지 말 것.

## 2. 재질의 중요한 실물 근거: OmniShade + MatCap

`UnityDataAssetPack.apk!assets/bin/Data/022974a357901497b8e12b4a565b88f1`, Material `TableSquare`, path_id=1:

| 연결 | 정확한 외부 파일 (`assets/bin/Data/` 아래) | path_id | 실제 이름 |
|---|---|---:|---|
| Shader | `a2a06e22c08354d9699356710b69ca9c` | 1 | `OmniShade/Standard URP` |
| `_MainTex` | `1b0f343342a0a6c43af07490d25aba90` | 1 | `Table_Square_v02` |
| `_MatCapTex` | `078ccde7743428f4d9b5a65bec0062b6` | 1 | `2_matcap` |

저장값 예: `_MatCapBrightness`≈5.3, `_MatCapContrast`≈0.8, `_MatCapPerspective`=1, `_DiffuseContrast`≈5.4, `_SpecularBrightness`≈0.16, `_SpecularSmoothness`=4, `_Saturation`=.75. 활성 키워드에 MATCAP/MATCAP_CONTRAST/MATCAP_PERSPECTIVE/DIFFUSE/SPECULAR 등이 있다. 셰이더 프로퍼티 선언 165개, 컴파일 blob 250,281바이트.

**해석:** 이 표본의 외관을 일반 PBR 색상·roughness만으로 대체하면 MatCap 기반 표면 표현을 놓칠 수 있다. 전체 재질이 모두 같은 설정이라는 뜻은 아니다. 색공간/텍스처 방향/블렌드 구현은 별도 검증이 필요하다.

확인된 다른 셰이더 이름: `Toony Colors Pro 2/Hybrid Shader 2`, `Shader Graphs/SG_Ground`, `Shader Graphs/SG_Landscape`, `RoyalSmash/Water/Stylized Surface`, `RoyalSmash/Water/Float Ring`, `Cypher/2D/Unlit`, `Cypher/VFX/Default`, URP Lit/Simple Lit/Unlit 등. 이름 목록은 `summary.json` 참조.

### 기존 .shader 파일 주의

옛 출력: `C:\Users\NHN\AppData\Local\Temp\claude\D--99---\6ee55866-9dd4-42f5-ab2b-cebba14aa29a\scratchpad\rs_export2\ExportedProject\Assets\Shader\`.

여기 `.shader` 26개 모두 `DummyShaderTextExporter` 표시가 있다. 예를 들어 `RoyalSmash_Water_Stylized Surface.shader`는 프로퍼티 목록 뒤 fragment가 흰색을 반환하는 더미 구현이다. **원본 효과 코드로 사용하면 안 된다.** 원본 APK의 Shader 컴파일 데이터 및 파싱 메타데이터는 존재하지만, 편집 가능한 원본 `.shadergraph`/HLSL 전체를 확보했다는 뜻이 아니다. 임시 폴더 경로보다 이번 JSON과 보존된 APK를 우선 근거로 사용한다.

## 3. 인게임 카메라: GameplayCamera

정확한 출처: `UnityDataAssetPack.apk!assets/bin/Data/level2`.
Camera path_id=95 → GameObject path_id=9 (`GameplayCamera`) → Transform path_id=56. 루트 Transform이므로 저장된 로컬 변환은 씬 저장 상태의 월드 변환과 같다.

| 설정 | 저장값 |
|---|---|
| 투영 | **Perspective** (`orthographic=false`) |
| FOV | **30°** |
| 위치 | **(0, 8.85000038, -40)** |
| Quaternion (x,y,z,w) | **(0.0436194055, 0, 0, 0.999048293)** — X축 약 +5° |
| Scale | (1,1,1) |
| Near/Far clip | 약 0.3 / 1000 |
| Viewport | (0,0,1,1), 전체 화면 |
| 활성 | GameObject active, Camera enabled |
| 레이어 / Culling mask | GameObject layer16 / 0xFFFFFFFF |
| HDR / MSAA 허용 | true / true (최종 파이프라인 사용 확정은 아님) |
| 저장된 orthographic size | 5 — 원근 모드이므로 이것을 화면 크기로 쓰면 안 됨 |

GameplayCamera에 붙은 MonoBehaviour는 원본 참조상 `UniversalAdditionalCameraData`, `FPSSetter`, `Core.CameraShake`다. CameraShake 커스텀 필드/런타임 흔들림 크기는 이번에 해독하지 않았다.

혼동 금지: `level1`의 `MainCamera`는 **직교 size41**, 위치(0,1,-10), 회전 identity다. `level0`의 `Main Camera`는 **직교 size5**다. 이들을 인게임 원근 카메라로 대체하지 말 것. 원본 코드 선언에 `Core.GameplayCameraSwitch`의 메뉴 카메라 목록과 scene load/unload/RestoreMenuCameras 메서드가 존재한다(dump.cs 450625행부터). 선언만으로 실행 타이밍 전체를 확정하지는 않았다.

### 정적 분석의 한계

카메라 3개/Material995개/Shader151개를 직접 파싱하는 데 오류는 0개였다. 씬 MonoBehaviour 커스텀 payload 1,727개는 타입트리 부족으로 완전 파싱되지 않았으며 오류를 `summary.json`에 보존했다. 별도 표준 헤더 읽기로 script identity 8개를 연결했지만 커스텀 payload 해독 성공으로 간주하지 않았다.

현재 값은 **원본 씬에 저장된 초기값**이다. 최종 플레이 중 화면비 보정, 움직임/흔들림, 줌·FOV 변경 여부 및 실제 프레임 결과는 미검증이다. `CameraSizeController` 등이 바이너리에 있다는 것만으로 GameplayCamera에 적용된다고 주장하면 안 된다. 재현 시 위 값을 출발점으로 삼되 Unity/대상 엔진 좌표계와 카메라 전방축 차이를 변환해야 한다.

## 재검증

스크립트 `../inspect_visual_settings.py`, `../inspect_camera_links.py`. Blender 번들 Python + 기존 `cdn_extraction_deps`를 사용하며 네트워크 연결 audit hook을 차단한다. APK 원본·기존 ZIP·게임 프로젝트 파일은 수정하지 않았다.
