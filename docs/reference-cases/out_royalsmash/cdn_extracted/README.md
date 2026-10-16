# Royal Smash CDN 추출 결과

2026-09-16. 다운로드한 31개 번들을 모두 로컬에서 처리했다.

## 산출물

| 파일 | 내용 |
|---|---|
| `RoyalSmash_CDN_sprites.zip` | 최초 추출 PNG 1,204개 |
| `RoyalSmash_CDN_recovered_sprites.zip` | 원본 APK Atlas_UI 참조를 연결해 추가 복구한 PNG 267개 |
| `RoyalSmash_CDN_components.zip` | MonoBehaviour 컴포넌트/설정 JSON 4,684개 + 출처 목록 |
| `RoyalSmash_CDN_named_settings.zip` | 위 4,684개 중 이름이 있는 설정 40개를 별도 정리한 부분집합 |
| `RoyalSmash_CDN_hierarchy.zip` | 프리팹 90개, GameObject 노드 7,147개와 컴포넌트 필드 |
| `RoyalSmash_CDN_assets.zip` | 머티리얼 49개, Spine 데이터 2개 |
| `RoyalSmash_CDN_meshes.zip` | Mesh 오브젝트가 없어 목록만 기록. 메시 추출 성공으로 세지 않는다. |

이미지 총 1,471개 = Sprite 1,230개 + Texture2D 241개. 스프라이트와 원본 아틀라스/텍스처를 함께 내보냈으므로 고유 그림 1,471종이라는 뜻은 아니다.
폴더별 두 이미지 ZIP을 함께 사용한다. 최초 추출 실패 267건은 원인·이력을 보존했고, 후속 267건 모두 복구되어 최종 미복구는 0건이다.

## 검증

- 다운로드 원본 31개의 SHA-256이 추출 전후 동일.
- 산출 ZIP 7개의 CRC, 모든 JSON의 엄격한 문법, PNG 1,471개의 파일 무결성 통과.
- 소스 31개 전부 처리, 개수 상한에 따른 누락 없음.
- Sprite/Texture2D/MonoBehaviour/GameObject 수를 원본 오브젝트 집계와 대조.
- 3GiB 메모리 중단 제한 아래 단계별 별도 프로세스로 처리. 측정 최고 private memory 1,094,483,968 bytes (약 1.02GiB).
- 기계 판독 결과: `EXTRACTION_VALIDATION.json`; 실행 기록: `execution.json`, `components_execution.json`, `atlas_execution.json`.
- 이름·클래스/오브젝트 개수·출처: `components_result.json`. 아틀라스 연결 근거: `atlas_recovery_result.json`.

267개 복구는 기존 APK의 `shared_common_local_assets_all.bundle`에서 Atlas_UI를 읽고, 각 Sprite의 AtlasTags와 RenderDataKey가 정확히 일치하는 항목을 연결한 것이다. 읽기용 메모리 객체의 참조만 보완했으며 APK·번들·게임 코드·보호 기능을 수정하지 않았다.

## 설정과 밸런스 해석 범위

이름이 있는 설정에는 `DailyTaskTaskIconConfig`, `SmashLeagueTierVisualConfig`, 보상 UI 애니메이션, 텍스트/Spine 애니메이션 관련 데이터 등이 있다. 40개를 곧바로 밸런스 테이블 40개라고 부르지 않는다.
이번 31개 번들의 TextAsset은 Spine 관련 `Dart_Nigth`, `Dart_Nigth.atlas` 두 개다. 추가 레벨 JSON TextAsset은 발견되지 않았다. 과거 “CDN에 약 700개 레벨” 추정은 이번 결과로 확인되지 않는다.
4,684개 JSON의 값은 에셋에 직렬화된 설정이며 서버 덮어쓰기·런타임 최종 밸런스를 검증한 값은 아니다. PPtr 참조는 원본 의미대로 남아 있어 참조 대상의 추가 해석이 필요할 수 있다.
이미지 육안 검수·게임 플레이·Unity 재임포트는 하지 않았다. AnimationClip/AnimatorController/Shader의 엔진 네이티브 파일 내보내기는 이번 산출물 범위에 포함하지 않았으며 원본 번들에 보존된다.

## 실행 환경

기존 levelscope 코어는 수정하지 않고 `run --only assets`, `sprites`, `hierarchy`를 사용했다. 추가 도구는 내장 타입트리 JSON 저장과 원본 아틀라스 참조 연결을 담당한다.
기존 Python312 venv 실행 경로 문제는 전역 수리하지 않았다. Blender Python 3.13과 별도 `../cdn_extraction_deps`의 UnityPy 1.25.3 등으로 이 작업의 실행 환경만 구성했다.
필요한 라이브러리는 PyPI에서 설치했다. 실제 추출 프로세스는 네트워크 호출을 금지하는 감사 훅 아래 실행했고 게임/CDN 추가 접속·로그인·게임 실행은 하지 않았다.
재현: `../extract_public_cdn.py`, `../export_cdn_components.py`, `../recover_cdn_atlas.py`, `../validate_cdn_extraction.py`.
