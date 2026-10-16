# 사례별 분석 연구 스크립트

직접 작성한 Goods Hunt / DKBI / Hat in Time / Royal Smash의 선택 분석·참조연결·검사 스크립트다. 게임 리소스, 원본 역어셈블/컴파일 셰이더 본문, 원본 테이블, 외부 도구 바이너리는 포함하지 않는다.

**범용 제품 CLI가 아닌 사례 재현용 연구 코드**다. 기본값에 당시 로컬 입력/출력 경로가 있으며 일부는 import 시 실행한다. 먼저 코드를 읽고 독립 복사본과 출력 경로를 지정한 후 실행한다. 무작정 import/일괄 실행하지 않는다. 필요한 로컬 원본/추출물/라이브러리는 저장소에 포함하지 않았다. 외부 소스 설치/게임 실행/ADB 연결을 자동으로 승인하는 문서가 아니다.

게시 시 모든 스크립트 Python 문법 컴파일을 검사했으나 다시 원작 전체 추출을 실행하지 않았다. 기존 실행 결과·실패와 정정은 docs/reference-cases/와 EXTRACTION_HISTORY.md에 보존한다. 전체 원본/리소스를 제외하므로 입력 파일이 없으면 그대로 실행되지 않는 것이 정상이다. 메모리 가드는 저장소 tools/watchdog.py를 사용하는 별도 런처를 적용한다.

hatintime의 scale decoder는 MD5에 없는 UE3 scale sidecar를 해독한다. `hatintime/ueviewer_patch/`에는 공개 UEViewer 포크의 로컬 C++ 3파일 변경분과 base 해시를 보존했다. third-party 바이너리는 배포하지 않는다.
