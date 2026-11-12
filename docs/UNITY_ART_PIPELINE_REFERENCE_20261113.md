# Unity 실사 그래픽 가이드의 3D 파이프라인 활용 검토

대상: https://www.youtube.com/watch?v=fBQvL5YR3eg — The Beginners Guide to Creating Realistic Graphics (In Unity), Isto Inc.

검토 범위: YouTube 웹페이지는 제목 외 본문 접근이 제한됐습니다. 공개 챕터/제작자 설명의 재게시 내용을 찾아 구간을 확인했고, 기술 판단은 Unity 공식 문서와 Graphics 저장소(Context7)를 대조했습니다. 전체 영상 시청·자막 전수 확인 또는 프로젝트 적용 실험을 완료한 검토가 아닙니다.

## 판단

활용 가치 높음. 기존 로컬 인계의 모션·리그 요구→GPT 원화→이미지 기반3D→Blender 정리 흐름에, 재질·조명·엔진 표시 품질을 확인하는 단계를 보완하는 용도. 생성기·리깅·모션 문제를 해결하는 기술로 취급하지 않습니다.

제안 흐름: 요구/목표엔진·카메라·플랫폼 확인→원화/3D/리그·토폴로지 정리→UV/PBR 정리→대상 셰이더용 텍스처 패킹→기준 조명 장면→실제 게임 카메라 비교→성능 측정.

## 영상 구간과 적용 후보

| 구간 | 주제 | 적용 후보 |
|---|---|---|
|02:32|LOD|기존 LOD 처리에 실제 카메라 거리별 실루엣·팝핑 비교 추가|
|03:22~07:32|재질과 제작/반입|BaseColor·Normal·Metallic·Roughness/Smoothness·AO의 의미와 색공간, 누락/반전/표면광택 검수|
|09:13|트림시트|벽/기둥/문틀/금속테두리 등 반복 환경 모듈의 공용 UV·재질 제작 후보. 캐릭터 전체에 자동 적용하지 않음|
|10:16|채널 패킹|대상 셰이더별 변환 프리셋과 채널 디버그 뷰. 파일 수 감소를 드로우콜/메모리 절감 보장으로 간주하지 않음|
|13:04|렌더 파이프라인|Unity URP/HDRP 또는 다른 엔진에 맞는 분기. 영상만 보고 기존 프로젝트 파이프라인 전환하지 않음|
|16:46~18:44|베이크/혼합 조명·반사 프로브|정적환경 간접광과 움직이는 캐릭터/반사 표시를 비교하는 작은 기준 장면|

## 먼저 검증할 세 가지

1. 기존3D모델 하나의 PBR 입력/재질을 정리하고, 고정조명·카메라에서 원본/수정 비교.
2. 작은 실내 장면에 정적환경 조명과 움직이는 캐릭터의 프로브/실시간 조명을 구성해 접지감·어두운 부분·금속반사 비교.
3. 동일 화면에서 텍스처/재질공유·LOD 적용 전후 GPU시간·드로우콜·텍스처메모리 측정. 플랫폼/해상도/카메라 고정.

정량적으로 자동검사할 후보는 채널/색공간/크기/참조누락/LOD구조입니다. 재질감·가독성·빛의 분위기·모션자연스러움은 렌더와 사람 검토가 필요합니다. 스타일라이즈드 아트에도 재질/조명 정합성 원리는 쓸 수 있지만 실사적 거칠기/미세노이즈를 그대로 늘리지 않습니다.

## 기술 근거

- URP Lit의 Smoothness 입력 및 재질 속성: https://docs.unity.com/en-us/engine/6000.0/manual/materials-and-shaders/built-in/shaders-in-universalrp/reference/lit-shader
- URP 채널 패킹: https://docs.unity.com/en-us/engine/6000.0/manual/materials-and-shaders/built-in/shaders-in-universalrp/channel-packed-texture
- HDRP Mask Map은 R Metallic/G AO/B DetailMask/A Smoothness, 데이터텍스처 sRGB비활성: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/Mask-Map-and-Detail-Map.html
- 렌더파이프라인의 플랫폼/기능 차이: https://docs.unity.com/en-us/engine/6000.0/manual/render-pipelines/choose-a-render-pipeline/pipeline
- 조명 구성 흐름: https://docs.unity3d.com/ja/current/Manual/lighting-configuration-workflow.html
- Light Probes: https://docs.unity3d.com/6000.0/Documentation/Manual/LightProbes.html
- Reflection Probes: https://docs.unity3d.com/6000.0/Documentation/Manual/ReflectionProbes.html

공개 챕터 확인 보조출처(기술 정확성의 정본으로 사용하지 않음): https://gridvids.com/isto-inc/the-beginners-guide-to-creating-realistic-graphics-in-unity

로컬 인계 대조: D:/00.project/GameDevTeam/docs/art/3d-production-handoff-2026-10-16.md. 설치 스킬·엔진 프로젝트 변경, 신규 유료 생성, Blender/Unity 실행은 하지 않았습니다. 실제 최신 프로젝트의 엔진/플랫폼 선택은 이번 검토에서 확정하지 않았습니다.
