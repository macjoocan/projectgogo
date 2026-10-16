# Soulbound 데이터 구조와 분석 범위

2026-09-30. 원본 설치 폴더는 읽기만 했다. 게임 실행·로그인·게임 서버 요청·인증 정보 열람은 하지 않았다. 분석 도구용 공개 소스와 Capstone은 별도로 받아 사용했다.

## 전체 구조

| 계층 | 내용 | 산출물 |
|---|---|---|
| GameMaker data.win | FORM 31개 청크, 이미지·사운드·오브젝트·룸·이름 색인 | survey.json |
| 이미지 | 아틀라스 344, TPAG 이미지 영역 17,533, 스프라이트 4,300 | sprite_metadata.json, atlases/, frames/ |
| 오디오 | WAV 156 + OGG 78 = 234 | audio_manifest.json, audio/ |
| 오브젝트 | 684개, 이벤트 1,401개, 부모/스프라이트/액션 참조 | objects_linked.json |
| 고정 룸 | 24개, 인스턴스 1,305, 레이어 306 | rooms.json, tilesets.json |
| 네이티브 코드 | x64 YYC, data.win에 CODE 청크 없음 | native_symbols.json, native_disassembly/ |
| 실행 중 데이터 | 월드·청크·아이템·능력치·던전·조정 변수 | schema_field_index.json |

오브젝트의 저장 uses_physics는 684개 모두 꺼져 있지만, 이는 해당 GameMaker 내장 물리 설정을 말한다. 게임에 충돌 처리가 없다는 뜻이 아니다. 시각 스프라이트가 저장된 오브젝트는 426개이며 나머지도 실행 중 렌더링할 수 있다.

오브젝트 이벤트 이름과 네이티브 심볼을 정확한 이름으로 대조해 1,378/1,401개를 연결했다. 나머지 23개는 억지로 유사 이름에 붙이지 않았다. 이름 연결은 본문의 동작 검증과 다르다.

## 코드 조사 방법과 신뢰 범위

Soulbound.exe의 `.data`에서 이름 포인터·코드 포인터·메타데이터 포인터의 24바이트 레코드 후보 49,969개를 찾았다. 이 중 49,515개는 PE `.pdata`의 함수 시작 주소와 일치한다. 이미지 베이스는 `0x140000000`이다.

맵·밸런스 관련 1,175개 함수를 Capstone으로 역어셈블했고 247개 메시지 변환 함수의 필드 참조를 정리했다. **1,175개 전부를 완전히 해석했다는 의미는 아니다.** 명명된 호출·필드 참조·선택한 본문을 조사했으며 전체 GML 소스 복원이나 실행 검증은 하지 않았다.

`schema_field_index.json`은 필드의 선언 원문이 아니라 네이티브 참조 색인이다. 조건부 필드, 별칭, 헬퍼 참조가 섞일 수 있으므로 이 파일만으로 완전한 서버 프로토콜을 생성하면 안 된다.

## 검증

- 오디오: 234개 파일 해시 및 참조 확인. WAV 컨테이너 길이·청크와 OGG 페이지 구조 확인. 실제 청취·전체 코덱 디코딩은 미검증.
- 룸: 타일 RLE 해제, 인스턴스 참조, 격자 크기와 타일 크기 대조. 타일 격자 대 룸 크기 불일치 0개.
- 오브젝트: 부모 참조 및 상속 순환 검사. 이벤트 심볼 연결의 미일치 보존.
- 원본 data.win과 EXE SHA256: 조사 전후 동일.
- 룸 PNG는 구조도다. 레이어 색과 인스턴스 점을 표시하며 원작 플레이 화면으로 사용하지 않는다.
- HTML은 로컬 카탈로그 방식이다. JS 구문과 파일 연결을 검사하되 브라우저 실동작은 미검증이다. 도구의 file:// 정책 차단을 우회하지 않았다.

상세 결과: [systems_validation.json](systems_validation.json), 기존 이미지 검증: [validation.json](validation.json).

## 보는 순서

1. [통합 구조 탐색기](Soulbound_systems.html): 룸, 오디오, 오브젝트, 필드 검색.
2. [맵 제작·배치 방식](MAP_PRODUCTION.md): 고정 룸, 월드 청크, 던전 조합.
3. [밸런스 시스템](BALANCE_SYSTEMS.md): 설정 로딩·성장·보상·스폰과 미확보 수치.
4. [이미지 탐색기](Soulbound_assets.html): 스프라이트 프레임·원점·PNG.

같은 폴더의 JS, PNG, audio 및 native_disassembly 하위 파일을 함께 유지한다. HTML만 복사하면 연결이 끊어진다.

## 재현 도구와 미완료

이미지 경로는 `extract_assets.py → validate_assets.py → build_catalog.py`, 이번 구조 경로는 `audit_structure.py → probe_native.py → index_native.py → build_systems_report.py`다. 스크립트의 입력 경로는 이 PC 설치본에 맞춰져 있다. Python/Pillow/Capstone 필요; 사용한 라이브러리 위치는 각 스크립트에 명시했다.

아직 하지 않은 범위는 충돌 마스크 전체 해석, sprite sequence/nine-slice 본문, 룸 asset layer의 세부 sprite/sequence 확장, 셰이더·폰트 전체 복원, 전체 네이티브 코드 해석, 실제 월드 청크와 운영 밸런스 payload 확보, 실플레이 대조다. 현재 산출물을 완전한 오프라인 게임 복원본으로 부르지 않는다.

직렬화 판독 참고 소스는 [UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool)의 Models 및 QoiConverter다. 복사한 참고 소스와 GPLv3 원문은 references/에 보존했다. 도구 라이선스와 게임 리소스 권리는 별개다. 리소스를 공개 저장소로 업로드하지 않았다.
