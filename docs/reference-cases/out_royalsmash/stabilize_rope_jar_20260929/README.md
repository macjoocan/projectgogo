# StabilizeIsland / Rope / PS_Jar 원본 판독

2026-09-29. 요청 원문: `C:\00.SVN\royalsmash\out_royalsmash\codex_request_20260929_stabilize_and_rope.md`.

## 결론과 적용 순서

1. **lv31~33: 원작은 접촉 섬 전체에 받침 가속도를 전달한다.** `01_STABILIZATION.md`의 식과 BFS 경계를 이식한다. 마찰 증가·회전 지연·속도 하향을 먼저 넣을 근거는 없다. Claude의 임시식과 벡터 식은 같지만 원작은 `AddForce(…, Acceleration)`이며 target pose 차분, 접촉 관리, 호출 임계도 함께 필요하다.
2. **Pinata: 단일 Joint가 아니라 7마디 강체 Rope.** `rope_saved_values.json`은 원문 160바이트를 전부 읽었으며 미해석 꼬리 0바이트. `02_ROPE_PINATA.md`에 연결 좌표계·8개 관절·관성·스프링 식을 기록했다.
3. **JamJar: 기본 Explode → PS_Jar 호출 경로를 복원한다.** 일반 `SpawnBroken`을 넣는 것은 원작 경로가 아니다. `03_JAR_CALL_PATH.md`와 `jar_effects_saved.json`(18종 → 효과 6팩, 팩당 PS 5개)을 사용한다. 실제 WebGL 프레임 저하 원인은 이번 정적 판독만으로 확정하지 않았다.

## 증거 구분

- `[원작값]`: APK 직렬화값. Rope는 raw bytes/필드별 파일 오프셋/외부 참조를 함께 제공.
- `[원작 코드 판독]`: 동일 libil2cpp.so의 ARM64 명령. 메서드 RVA는 각 문서 및 `asm_index.json`.
- `[자체]`: 통합/검증 제안. 원본에서 정한 수치로 주장하지 않는다.
- Claude가 보고한 ON/OFF 결과는 타 세션의 실행 결과이며 이 세션에서 재실행한 것으로 쓰지 않는다.

`provenance.json`에 native/dump SHA256, `constants.json`에 주요 float의 ELF 파일 오프셋과 비트 패턴이 있다. `.schema.cs.txt`의 `0x…`는 **managed 객체 필드 오프셋**이며 직렬화 파일 오프셋과 다르다.

`*.asm`은 요청 메서드 RVA부터 다음 dump 등록 RVA까지 추출한 구간이다. dump에 없는 helper가 뒤에 포함될 수 있으므로 정상 ret/tail branch와 주소 범위로 구분한다. 호출 주석은 주소 대응표이며 인라이닝/가상 호출 전체 복원을 뜻하지 않는다. `direct_xrefs.json`은 executable PT_LOAD의 직접 B/BL만 검색한 결과다.

## 실행 확인 범위

검증 완료: native 명령/상수 대조, Rope 원문 전체 소비, endpoint/mesh/material PPtr 해석, Jar 18종 저장 참조 → PS_Jar 6팩 확인, ForceMode enum 5=Acceleration 확인.

미실시: C: Unity 코드 변경, Editor/WebGL 실행·프로파일링, 원작 실기와 화면 비교. 이 폴더는 연구·이식 자료이며 설치만으로 게임이 수정되지는 않는다.

과거 설명 정정: 초기 회전 대기 부족을 우선 원인으로 본 설명은 보류한다. 저장 BrokenPieces 수를 원작 Jar 런타임 파편 수나 FPS 원인으로 사용한 설명도 철회한다. 원작 호출 경로가 우선이다.
