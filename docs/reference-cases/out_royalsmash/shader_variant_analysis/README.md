# 셰이더 변형 키워드·패스 연결 검증

2026-09-16. 원본 APK 및 기존 로컬 추출물만 분석. 게임·에뮬레이터 실행, CDN 요청, 인증/보호 우회 없음. 프로토타입 코드는 변경하지 않음.

## 결론

이전 `variant_keywords_mapped=false`는 **현재 복구한 GLES 프로그램 287개에 대해서는 해소**했다. 새 `program_keyword_pass_index.json`의 각 프로그램은 `variant_keywords_mapped=true`다. 단, **`runtime_selection_verified=false`는 유지**한다. 키워드/패스가 무엇인지를 아는 것과 특정 프레임에서 실제 선택됐음을 관측하는 것은 다르다.

| 검증 대상 | 결과 |
|---|---|
| OmniShade 프로그램 | 236개 키워드 및 패스 연결 확인 |
| Toony 프로그램 | 51개 키워드 및 패스 연결 확인 |
| 프로토타입 51종 이름에 대응하는 원본 재질 객체 | 54개 매핑, 주 패스 후보 모두 존재 |
| 실행 중 선택된 프로그램 | 미관측; 확정 아님 |

원본 코드 길이·SHA256·blob 경계를 검사하고, blob의 키워드 문자열을 `m_PlayerSubPrograms.m_KeywordIndices → m_KeywordNames`와 독립 대조했다. 287개 모두 일치한다. GLES 코드는 VERTEX/FRAGMENT가 함께 있으며 이 데이터에서는 `progVertex` 레코드가 연결점이다.

## 저장된 렌더링 환경

`globalgamemanagers` GraphicsSettings와 현재 Mobile QualitySettings 모두 base APK의 `globalgamemanagers.assets`, pathID **4147**을 참조한다. 객체명은 **Mobile_RPAsset**, 스크립트는 UniversalRenderPipelineAsset이다. 원본 IL2CPP SerializeField 선언 순서와 직렬화 폭/정렬로 복원한 제한된 prefix 값은 다음과 같다. 전체 custom payload를 복구한 것은 아니다.

- URP: 메인·추가 광원 PerPixel, 추가 광원 한도 4, 메인 그림자 지원, 추가 광원 그림자 미지원.
- **캐스케이드 1개, 그림자 거리 60, 소프트 그림자 지원**, 메인 shadowmap 512, RenderScale 1.
- renderer list의 원본 객체는 pathID 4148 `Mobile_Renderer`.
- level2 GameplayCamera의 UniversalAdditionalCameraData pathID 122: **m_RenderShadows=true**, m_RendererIndex=-1(기본), camera stack 비어 있음.
- level2 Light 104: enabled, Directional, intensity 1, Soft shadow, strength 0.75. Light 105: enabled, Directional, intensity 0.4, 그림자 없음. 이 값만으로 실행 시 활성 계층·가시성을 확정하지 않는다.

주의: 일반 QualitySettings의 shadowCascades=2, shadowDistance=40을 위 URP 값 대신 사용하면 잘못된 후보로 좁힐 수 있다. [Unity의 URP 설정 위치 안내](https://docs.unity3d.com/cn/6000.0/Manual/urp/birp-onboarding/quality-settings-location.html)도 그림자 캐스케이드를 URP Asset 항목에 대응시킨다.

## 재질별 후보와 조건부 축소

| 재질 / 주 패스 | 재질 기능 키워드가 맞는 후보 | 저장 환경에 부합하는 조건부 후보 |
|---|---|---|
| ColorBoxSquareBlue / Toony Main | 46, 58, 70, 82 | **58** |
| TableSquare / OmniShade UniversalForward | 152, 172, 187, 202, 213, 233, 244, 264, 275, 295, 306, 326, 337, 358 | **202** |

조건부 58/202는 유효 전역 키워드가 `_ADDITIONAL_LIGHTS`, `_MAIN_LIGHT_SHADOWS`, `_SHADOWS_SOFT`이고 캐스케이드 키워드는 없는 경우다. 저장된 설정이 유지되고, 해당 GLES subshader/pass를 사용하며, 실제 광원·shadow caster 및 렌더러 상태가 이 조합을 활성화한다는 **조건**이 필요하다. 화면 캡처나 런타임 관측 없이 이를 실제 선택으로 확정하지 않는다. [Unity는 스크립트의 재질/전역 키워드 변경을 지원한다](https://docs.unity3d.com/6000.0/Documentation/Manual/shader-keywords-scripts.html).

- ColorBox Blue의 이전 설명용 **41번**은 `TCP2_SPECULAR`가 없어 재질 전체 키워드와 맞지 않는다. 해당 샘플에서 확인한 MatCap 분기 자체는 근거지만, 구현할 전체 프로그램은 후보 46/58/70/82를 사용해야 한다.
- TableSquare의 **152번**은 런타임 광원/그림자 키워드가 없는 후보다. 가장 가까운 샘플이라는 이유만으로 실제 사용 프로그램이라 간주하지 말 것.
- `OUTLINE_PASS_DISABLED`, `_OPTFALLBACK_ALL`처럼 주 패스의 프로그램 키워드에 없는 저장 키워드는 별도로 기록한다. 누락을 숨기거나 실행 활성으로 간주하지 않는다. TableSquare의 disabledShaderPasses에는 MOTIONVECTORS, SRPDEFAULTUNLIT이 있다. 후보표는 비활성 패스의 실행을 뜻하지 않는다.
- `m_ValidKeywords` 기준의 정적 후보다. 키워드 scope/런타임 변경, renderer mode/기능, 기기 지원, pass enable, 가시성/컬링, fallback 선택은 실행 관측 없이 확정되지 않는다.

## 전달 파일

- `program_keyword_pass_index.json`: 코드 파일·해시·키워드·subshader/pass 연결 전체.
- `material_variant_candidates.json`: 원본 source identity를 보존한 재질별·패스별 후보, 패스에 없는 저장 키워드, disabled passes.
- `native_graphics_quality.json`: 네이티브 타입트리 원문.
- `urp_asset_prefix.json`, `urp_schema_evidence.json`: 원본 객체 해시, field offset/raw hex, 스키마 근거. 메모리 필드 offset을 파일 offset으로 사용하지 않음.
- `gameplay_camera_prefix.json`, `gameplay_scene_lighting.json`: 카메라 prefix 및 Light/RenderSettings 근거.
- `VALIDATION.json`, `summary.json`: 검증 결과, 상태 구분 및 조건부 후보.

실제 코드: `../shader_program_analysis/toony/gles_entry0058.glsl`, `../shader_program_analysis/omnishade/gles_entry0202.glsl`. 텍스처/UV/색공간/필터 메타데이터는 이전 `../block_texture_handoff/manifest.json`과 함께 사용한다.

이전 `shader_program_analysis/inventory.json`은 최초 추출 당시 상태를 보존하므로 false가 남아 있다. **현행 매핑 상태는 이 폴더의 새 인덱스가 우선**하며, 런타임 검증 상태와 혼합하지 않는다.

재현 스크립트: 상위 폴더 `map_shader_variants.py`, `inspect_render_variant_context.py`, `validate_shader_variants.py`. 원본 입력을 읽고 분석 산출물만 생성한다.
