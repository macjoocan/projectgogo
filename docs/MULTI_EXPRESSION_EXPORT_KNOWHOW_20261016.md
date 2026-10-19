# 표정 내보내기 — 색상 채널과 기본 Scene 검증

**현재 상태 정정 — 2026-10-19:** 사람은 기존 얼굴을 선호해 대시보드/HTML 기본을 OriginalRetry로
복원했다. 표정 후보는 revise·비교 기본 OFF이며 삭제/최종 승인하지 않았다.
이번 표적15자세 검사와 당시 전체 QA는 구분한다. [최신 얼굴 피드백](MULTI_FACE_FEEDBACK_20261019.md) 참조.

Multi bmvb1gbqk-l 후속. 담당 세션의 문서와 QA를 읽고, 이 세션에서는 원본 파일을 변경하지 않고
최종 두 파일의 SHA와 GLB JSON 구조만 독립 확인했다. 새 생성·3D 작업·라이브 Blender 조작·원본 교체 없음.
원화/atlas/모델/Blend/GLB/HTML은 저장소에 포함하지 않는다.

## 재사용할 두 가지 노하우

1. **Blender 표시와 실제 GLB 속성은 다를 수 있다.** Multi는 의도한 표시 alpha가 COLOR_1,
   기존 흰색이 COLOR_0로 나가 웹에서 기존 눈·입이 다시 나타나는 문제를 보고했다.
   실제 primitive attribute/accessor를 검사하고 의도한 채널을 COLOR_0로 승격했다.
   이번 읽기 전용 확인에서 Neck/Skin/기존 캐릭터 primitive에 COLOR_0가 있고,
   얼굴 atlas 및 기존 표면 재질의 alphaMode MASK/cutoff0.15를 확인했다.
   이 헤더 확인은 COLOR accessor 전체 값이나 GPU 동등성 검사가 아니다.
2. **곡선 보존과 기본 열림 화면도 별개다.** libraries.write로 Action을 보존해도 기본 Scene이
   비어 보일 수 있었다. Multi는 최종 파일을 save_as_mainfile로 활성 MotionFirst_Expressions에
   저장하고, Scene을 수동 선택하지 않은 독립 재열기에서12객체·캐릭터·5native Action을 검사했다.
   미연결 Action의 `{scene,*actions}` 명시 저장/곡선 해시 검사는 여전히 별도로 유지한다.

리그 사용자 속성을 Python으로 바꿀 때 rig.update_tag()+view layer 갱신이 필요했다는 보고도
보존한다. Blender material driver가 GLB의 표정 제어나 원작 이벤트로 자동 변환되는 것은 아니다.
이번 웹 제어는 담당 세션의 별도 face-expressions.js가 수행한다.

## 독립 확인 결과

- expressions-native.glb: 11,650,612B,
  SHA256 `5c907a6a8ae2a4ec826312d1df673517f2280dae7946b5baffa5bd9774e26a2d`.
- expressions-native.blend: 11,608,737B,
  SHA256 `5ff4f12e7fcca9be70a8ab282ea7395d1a1730d42e9db99d170a7115e2cdb98f`.
- GLB JSON:7meshes/1skin70joints/5animations, length 일치, COLOR_0/MASK 설정 확인.
- 로컬 확인 로그: `D:/99.기타/out_hatintime/_reference/expression_package_intake_20261016.json`.

표시/GPU/전체 모션 검사를 이번 세션에서 다시 실행한 것으로 해석하지 않는다.

## Multi 보고 범위와 미해결

검수용5표정+blink, atlas1회 생성/추가3D생성0, 원본 triangle/UV 표시 alpha 및 별도 머리·목·scalp·굴곡3표면.
QA 원문: `C:/00.SVN/Multi/web/assets/studies/motion-first-crew/source/face-expressions-v9/qa-summary.json`,
설계: `C:/00.SVN/Multi/web/docs/45-character-expression-plan.md`, 보정 정본:43문서.

상대 보고상 기본5종×25자세7메시 전체finite/head강체오차3.70e-7m, 두 GLB597870 sampler float exact
(시간 중복 제외460557), Blend5native/3500curves/459900keys reopen hash exact.
오프라인 HTML은 두 표정/손 모드 각각278×3의 뼈행렬·skin당2표본finite, 외부요청0,
286내장자산해시/실제다운로드/표정전환/390px 검사를 통과했다. 이 수치는 읽은 QA/상대 보고이며
이번 세션의 독립 브라우저/Blender 재실행 값이 아니다.

**사람 검수 미승인.** 근접 헤어 경계·특수모션 외형·전신 무관통·원작 표정 이벤트는 미완료.
손의 강한 curl 및 harmonic 후보의 Idle 면적 회귀도 그대로 미해결이다. 얼굴 구현을 손가락 보정이나
전신 최종 아트 승인으로 확대하지 않는다. 이 세션에서 C: 코드를 복제 구현하거나 현재 모델을 교체하지 않았다.
