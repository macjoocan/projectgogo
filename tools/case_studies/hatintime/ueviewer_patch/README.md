# UEViewer 로컬 변경 패치

공개 Hat용 UEViewer 포크(https://github.com/MrSoup678/UEViewer)의 로컬 소스 zip과 비교한 변경분이다. upstream 저작권/라이선스 조건을 그대로 따른다. 외부 소스/바이너리 전체를 우리 코드로 재배포하지 않으며 게임 원문은 없다.

UnMesh3.h의 UE3 scale 직렬화 속성, ExportMd5.cpp의 metadata/compressed sidecar, Main.cpp의 export index 선택 보강을 담았다. provenance.json은 사용한 로컬 base archive 및 세 파일 원문 해시다. 특정 upstream HEAD와 동일한 버전이라고 단정하지 않는다. base 파일 해시가 다르면 자동 적용하지 말고 검토한다.

패치는 `git apply --check motion-sidecar-and-export-index.patch`로 base 호환성을 먼저 확인한다. MSVC 환경 탐색/로컬 절대경로 빌드 설정과 exe/dll/pdb는 포함하지 않는다. 기존 로컬 빌드/전수 scale 검증 결과는 docs/reference-cases/out_hatintime/_reference/README.md를 참고한다. 이번 게시에서는 새 native 빌드를 수행하지 않았다.
