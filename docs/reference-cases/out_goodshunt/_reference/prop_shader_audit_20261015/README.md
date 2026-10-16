# Prop OmniShade 별도 Shader 확인

2026-10-15, 요청1p. 지정 Shader 한 개만 bounded 추출. 원본 실행/소스 수정 없음, peak commit0.093GB.

원본: `../input_prepared/assets/aa/Android/propsdependencies_assets_assets_omnishade_shaders_omnishadeurp.shader_252f808c015943bc0904a80b2aa1ec4d.bundle`.

- serialized file **CAB-132b7aa310b4a64d3f77f2b71c0dbd0c**.
- Shader pathID **-8143037723478795692** (64bit lossless 유지).
- rawSHA **adaa7c18253058042e447768bd1f68f9d486b7796be0ca5ce2232f443f3e9a6b**, 기존 index 및 상대 세션 제공값 일치.
- 실제 parsed name **OmniShade/Standard URP**. 이름·선언·pass와 compiler text로 같은 계열 확인. **globalgamemanagers.assets#23과 완전히 같은 Shader/variant 집합은 아님**.

| 항목 | 기존 global#23 | 이 Prop Shader |
|---|---:|---:|
| 추출 GLES3 compiler text 프로그램 |103|188|
| 고유 compiler code SHA |72|131|
| 프로퍼티 이름 개수 |158|158|

교집합: 고유 codeSHA **44개** 동일. (정렬된 keyword tuple, codeSHA) 조합 **52개** 동일, Prop에만136/기존에만51. `comparison.json` 수치. 전체 프로그램이 같다고 확장하지 않는다. 키워드/텍스트 SHA는 inventory.json 각 entry에 보존. 같은 소스 계열이어도 스트립된 변형/전역 키워드/조명·shadow 등의 차이를 갖는다.

자료: `prop_omnishade/parsed_form.json`과 **188개 .glsl**, `inventory.json`에 플랫폼9(segment0 decompress4359468B)의 offset/length/entry/keyword prefix/codeSHA. 플랫폼18 원문 존재와 별개로 이번 텍스트 추출은 GLES3만 대상으로 한다.

패스 이름: UniversalForward / Outline / ShadowCaster / DepthOnly / DepthNormals, 별도 Fallback subshader. 각 blend/z/cull/property flags/default/keyword 선언은 parsed form 원문 기준. 임의 Lambert로 이 모든 기능을 대체한 것을 원작 식이라고 하지 않는다.

재질 연결 시 **native shader key가 이 CAB/pathID인 재질을 이 자료에 조인**한다. 기존 global#23 inventory의 blob entry 숫자로 대입하지 않는다. keyword set 정렬→재질 기능 키워드 대조→전역 조명/SH/shadow/renderer 키워드 및 pass를 구분한다. 저장 material keywords만 부분 일치했다고 실제 실행 variant가 확정되는 것은 아니다. 실제 Prop128조합과 runtime 선택의 전수 join/GPU parity는 구현 세션 후속 검증이다. 이 선택 추출에서 Props 재질 전체/임포터를 중복 처리하지 않았다.
