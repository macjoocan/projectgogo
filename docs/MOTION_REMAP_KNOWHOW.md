# 모션 리타게팅 보정 노하우

갱신: 2026-10-16. 검증된 도구 동작과 추가 검토가 필요한 시각 품질을 구분합니다.
코드는 `tools/motion_remap/`, 사용자 안내는 해당 폴더 `README.md`입니다.

## 재현해 확인한 주의점

1. **뼈대 이름 집합이 같아도 bind pose가 같지는 않습니다.** HatKid Body/Head/Legs는
   같은 이름 70개를 쓰지만 머리카락 일부 기본 자세가 다릅니다. 부품별 원본 뼈대·스킨을
   보존하고 각자 변환해야 합니다. 여러 부품을 하나의 바인드 행렬로 통합한 검증은 없습니다.
2. **본 순번을 매핑 키로 쓰지 않습니다.** 이름 기반 초안을 만들되 네임스페이스 제거 후
   이름이 겹치면 미결로 둡니다. source/target 양쪽 one-to-one 검증과 검토 승인 플래그를 둡니다.
3. **기본 자세 보정은 별도 참조 회전으로 저장합니다.** 원본 rest/bind pose를 Edit Mode에서
   바꾸거나 스킨 가중치를 다시 굽는 대신, 소스 기본 회전 뒤의 참조 quaternion을 JSON에 둡니다.
   보정용 포즈와 실제 모션 프레임의 구분이 필요하며 위치 재정의까지 지원하는 것은 아닙니다.
4. **이동은 단위·체격·오브젝트 스케일을 분리합니다.** auto ratio는 매핑된 부모-자식 길이의
   월드 비율 중앙값, 로컬 이동 배수는 world ratio × source object scale / target object scale입니다.
   정적인 회전·위치는 보존하며 원본 오브젝트 변환을 강제로 0으로 만들지 않습니다.
5. **소수 프레임 키를 버리면 같은 뼈대도 틀립니다.** 최초 HatKid identity 검증은 정수 프레임만
   bake해 중간 표본 최대 오차 0.865829(원본 수치 단위)이 났습니다. 원본 슬롯 키 시간과 정규
   샘플의 합집합을 bake한 뒤 같은 검사 오차는 0.0000305176으로 줄었습니다. 첫 실패 로그도 보존합니다.
   GLB 익스포터의 강제 정수 샘플링도 끕니다. 키 사이의 모든 연속 시각이 완전히 같다는 의미는 아닙니다.
6. **Blender 5 Action Slot을 명시합니다.** 여러 슬롯을 가진 Action에서 어떤 리그의 키인지
   모르면 거부합니다. 소스 Action/Slot/NLA/현재 시간/pose는 성공·실패 모두 복구합니다.
7. **FK와 IK 검사 범위를 나눕니다.** 2본 IK는 끝점·구간 길이·도달 불가능 목표·pole 특이점·
   끝점 아래 자식 전파를 검사합니다. 접지 검출/발 잠금/발 미끄러짐 제거는 미구현입니다.
8. **출력 성공을 움직임 보존으로 쓰지 않습니다.** 실제 스킨·애니메이션 개수를 읽고, 저장한
   Blend를 재열어 행렬·가중치·유한 정점을 확인합니다. 원작 게임 화면/런타임 절차 IK와는 별개입니다.

## 2026-10-16 검증 스냅샷

- Blender 5.2.1 LTS 합성 검사: 동일 뼈대 2클립, 위치/스케일, 소수 프레임, 다른 기본 roll,
  체격/오브젝트 스케일 합성 3배, 제자리 축, 참조 자세, IK, 실패 복구, 저장/재열기 통과.
- 로컬 HatKid **Body 부품만** 70본/5클립(Idle/Walk/Run/Attack/Hit_Candidate):
  3시점씩 총1,050본 행렬 표본, 최대 오차 0.0000305176. 저장 재열기 표본 차이0.
- 출력 GLB는 스킨1/애니메이션5 존재. GLB의 모든 시간/변형 정점이 원본과 일치한다는 검증은 아닙니다.
- HatKid 입력 Blend SHA 불변/원본 rest 불변/저장 후 변형 정점 유한성 통과.
- 실제 HatKid 검사 프로세스 트리 최고 커밋 약1.117GiB, 감시 상한2.5GiB/51.34초.
- 전체 기존+새 Python 검사549개 실행/실패0/skip3. Blender 합성 검사는 별도 실행입니다.

로컬 근거: `out/motion_remap/hat/verification.json`, `hat_diagnostic.json`,
`out/motion_remap/synthetic_v2/verification.json`, `out/motion_remap/unittest.log`.
세부 프로세스 영수증은 `../out_hatintime/_reference/remap_*_receipt.json`입니다.

## 0.2 보강 — 2026-10-16

0.1에서 남긴 주요 기법을 별도 모듈로 구현했습니다. `contacts.py`/`postprocess.py`는 접촉 구간
자동 추정·수동 구간·위치/회전 잠금·지면 raycast·골반 보정·궤적 필터·루프 이음을 처리합니다.
`sampling.py`는 소스 곡선 중간점 검사에 따른 적응형 키 추가, `controls.py`는 명시적
FK/IK/pole/IK-FK 속성 프로필과 실제 평가 오차 검사, `deform_export.py`는 분절 B-Bone과
제약 모션을 일반 선형 스킨 뼈대로 변환합니다. UI와 batch CLI 양쪽에서 사용할 수 있습니다.

새 검증에서 확인한 노하우:

1. **소프트 필터 뒤에 하드 제약을 재적용합니다.** 골반 스무딩이 접지 구간 가장자리의 보정을
   약하게 만들어 발 잔여 오차가 약0.10 생겼습니다. 스무딩 후 도달 범위 재투영으로 해결했습니다.
   합성 짧은 다리/양발 고정 검사에서 발 드리프트 약4.2e-7, 골반 이동0.448 이내를 확인했습니다.
2. **계산한 IK 목표 오차와 최종 포즈 오차를 구분합니다.** 행렬→TRS 분해 후 실제 자세를 다시
   평가합니다. 최종 HatKid 접지 목표 기준 오차는 약7.3881e-6입니다(초기 목표 계산만의2.387e-6과 구분).
3. **리그 복제는 Object ID만 바꾸는 일이 아닙니다.** self-target 제약, 다중 타깃 Armature 제약,
   Object/Armature-data driver 변수의 ID를 모두 복제본으로 연결합니다. 원본 제약 수/상태는 유지합니다.
   FK/IK 스위치는 이름으로 추측하지 않고 프로필에서 지정하며, verify_bones의 위치/회전/스케일을 검사합니다.
4. **B-Bone은 곡선을 버리고 직선화한 것을 완성품으로 보지 않습니다.** 중간 기준 리그는 직선
   프록시일 수 있지만, 최종 곡선 스킨은 Blender segment rest/pose 행렬과 인접 가중치로 변환하고
   매 샘플 평가 정점을 원본과 대조합니다. 선형 스킨 검사에서 최대 약2.3889e-7을 확인했습니다.
5. **회전 오차의 acos(dot) 부동소수점 바닥에 주의합니다.** 거의 같은 quaternion에서도 float32
   dot의 반올림으로 약0.0396도처럼 보일 수 있어, 상대 quaternion의 xyz/w를 atan2로 측정합니다.
6. **적응형 샘플의 범위를 정확히 씁니다.** 비선형 소스3샘플→32샘플, 중간점63회 평가를 확인했습니다.
   최종 타깃의 별도81시점 최대 위치 오차는0.007172였습니다. 소스 midpoint tolerance .005가
   최종 타깃 전체시간 오차 상한이라는 주장은 하지 않습니다. 깊이 상한 미충족 구간도 남깁니다.
7. **도달 불가능함을 숨기지 않습니다.** pelvis.max_shift로 보정량을 제한하고 남은 실제 발 오차를
   contact_satisfied/max_contact_error_world로 남깁니다. strict 모드는 실패·생성물 회수로 끝냅니다.

최종 검증 정본:

| 항목 | 로컬 근거 | 범위 |
|---|---|---|
| Python 전체 | out/motion_remap/unittest_v2.log | 556 tests, skipped3, 실패0 |
| 0.1 기본 회귀 | out/motion_remap/v2_final_baseline/verification.json | 합성11체크/스킨 저장 재열기 |
| 접지/제약/driver | out/motion_remap/controls_scale_release/verification.json | 자동/수동/불가능 접지, 경사 지면, 골반, 루프, 소스 object TRS, FK/복구 |
| IK/B-Bone | out/motion_remap/ik_scale_release/verification.json | 실제 Blender IK, B-Bone4분절→5본, 원본 정점 대조, GLB1스킨/1동작 |
| 실제5동작 | out/motion_remap/hat_v2_identity/verification.json | Body70본/5클립 identity, 최대3.0518e-5, 저장 재열기0 |
| 실제 체형 보정 | out/motion_remap/hat_contacts_release/verification.json | HatKid Legs/길이80% 검증 타깃/Idle1080샘플/유한 스킨/입력SHA·rest 불변 |
| 사용자용 CLI | out/motion_remap/control_cli_release/remapped.json | 원본 모션→프록시→컨트롤 복제/검사→Blend·GLB |
| 평가 스킨 CLI | out/motion_remap/deform_cli_release/remapped.json | B-Bone 평가 소스→일반 스킨 출력 |

실제 접지 예제는 설정한 월드Z 평면/발목-발끝 sole offset을 썼으며 원작 게임 지면의 복원이 아닙니다.
최종 Hat identity 최고커밋1.121GiB/50.21초, 접지0.885GiB/98.56초(상한2.5GiB)입니다.

## 남은 일반화/입력 제한

주요 기법의 구현과 지정 사례 검증을 완료했지만 모든 게임·모든 Rigify 버전의 무설정 호환성을
의미하지 않습니다. 실제 사용자 타깃/모션 종류의 시각 검토 사례는 더 쌓아야 합니다.
접촉 이벤트가 없는 클립의 auto 구간은 추정이며 제자리 걷기·불규칙 모션은 수동 구간이 필요할 수 있습니다.
지면은 월드Z 정적 메시/평면 보정이며 움직이는 받침/동적 물리와의 충돌 해결은 별개입니다.
비균일/반사/전단 객체 변환, Preserve Volume/shape key/추가 modifier를 포함한 평가 스킨은
현재 명시적으로 거부합니다. fulltime/pixel/game-runtime 동등성, 자동 리깅은 보증하지 않습니다.
## 후속 한계 정정 — 2026-10-16

`NLA_TRACKS + force_sampling=False`가 native 키 보존을 보장하지 않는다는 Multi 실험을 수신했다.
Blend 원본 커브 해시/소수 키와 GLB actual accessor 시간을 분리해서 검증한다.
기존 GLB 클립 수/70본/스킨 구조 성공을 native 시간키 exact로 확대하지 않는다.
Multi native localTRS 직접 출력은 별도 소유 구현이며 이 도구에 통합됐다고 주장하지 않는다.
생성 모델의 손가락·어깨 자동 스키닝은 Motion Remap 성공 범위가 아니다.
독립 후보5종 미채택 및 후속 연구 조건은 `MULTI_SKINNING_RESUME_20261016.md`를 참조한다.

