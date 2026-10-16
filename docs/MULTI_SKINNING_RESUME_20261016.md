# Multi 손가락·어깨 보정 재개 메모

사용자가 2026-10-16 메모리 보존을 명시 요청했다. 이번 기록은 재개 지침이며 자동 적용·커밋·푸시 권한을 추가하지 않는다.

## 읽을 순서

1. 이 문서와 MEMORY.md 최신 항목.
2. `D:/99.기타/out_hatintime/_reference/skinning_research_20261016/README.md`.
3. 같은 폴더 preservation_validation.json / stress_comparison.json / 각 후보 validation.json과 실제 PNG.
4. Multi 최신 `C:/00.SVN/Multi/web/docs/43-character-skinning-knowhow.md`.
5. 최신 native 파일은 `C:/00.SVN/Multi/web/assets/studies/motion-first-crew/final/original-retry-native.blend` 및 `.glb`. 이전 연구는 original-retry 파일을 선별 복사한 것이므로 최신과 동일하다 가정하지 말고 해시/구조부터 확인한다.

## 소유권과 제한

- Multi 코드·현재 라이브 Blender·원본 자산은 읽기 전용. 변경은 별도 D: 연구 폴더만.
- 원본 HatKid Body70 rest/계층/원본 소수 시간키 보존. DQ만 켜고 웹 개선이라 주장 금지.
- 메인 Multi가 대시보드와 278모션 라이브러리를 소유. 중복 개발 금지. 278에는 정지 pose5 포함이며 동일 의미의 모션 개수로 과장하지 않는다.
- 새 생성/외부 과금 없음. 순차 headless Blender 5.2.1, guard.py의 프로세스 트리 private commit cap2.5GiB 유지. C: 라이브 세션을 뺏지 않는다.

## 완료 연구와 실패 판정

원본 39,946정점/79,999삼각형, 70본, 기존 5클립을 25시점씩 평가했다. 후보당125스킨이며 기존 Multi155스킨 일정과 다르다. 5개 수정 후보 모두 적용 금지다.

| 후보 | 최대 팔 엣지 늘어남 | 최대 손가락 엣지 늘어남 |
|---|---:|---:|
| baseline |21.59mm|2.32mm|
| finger_weights_only |40.62mm|60.35mm|
| finger_fit |21.59mm|14.43mm|
| finger_fit_smooth |21.59mm|12.49mm|
| finger_continuous_probe |29.69mm|7.85mm|
| shoulder_local_probe |75.09mm|2.32mm|

손끝 성분/메시 geodesic으로 10digits 분리는 가능. 고정 관절과 생성 손바닥 위치가 달라 가중치만 주면 악화한다. 형상-fit 최대 이동98.15mm, 경계 가중치/변위 35회 평활화도 손바닥 찌그러짐 해결 못함. 실제 finger_curl 렌더를 반드시 볼 것. 단순 smoothing을 해결책으로 반복하지 않는다.

6종×5 합성 자세 검사, 4종×5자세 실제 Workbench 단색 렌더20장. 합성 overhead120/crosschest130/twist180은 원작 클립 검증과 별개다. 팔-몸통 비인접 교차 쌍 baseline overhead46/crosschest593, shoulder probe43/605. BVH 후보+선분 삼각형 검사, ROI 제한/공면 제외이므로 전신 무관통/깊이 검사가 아니다. 상완 covariance volume proxy twist180 baseline.972/probe.681; 실제 폐곡면 부피가 아니다.

preservation_validation.json PASS: 원본9선별파일 SHA 및 복사본 일치, 후보5 Blend save/reopen, 70본 rest/계층 및 5개 원본 커브 hash exact, GLB70joints/5animations 구조. GLB 실제 브라우저 스킨/시간키/픽셀 검증 아님. 메모리 피크0.81~0.95GiB. 후보 Blend/GLB는 실패 재현용, 현재 씬 적용 금지.

## 중요 후속 정정: GLB 시간키

Multi bmvaxm4pf-c 보고: NLA_TRACKS+force_sampling=False도24fps 재샘플 확인. 기존 연구의 GLB 구조 검사를 native 키 보존으로 확대하면 안 된다. 최신 Multi는 native localTRS 직접 출력으로 바꿨고 원본1050matrix max2.67e-5 및 GLB597870float exact라고 보고했다. 이는 상대 보고값이며 이 연구에서 독립 재검증한 값이 아니다. Blend 원본 커브/실제 export된 GLB키를 별도로 검증해야 한다.

## 다음 작업 — 승인됐지만 아직 구현 시작 전

고정 원본 관절에 맞춘 손바닥·손가락 기저부 continuous cage+굴곡 topology로 범위를 좁힌다. 새 독립 복사본에서 소수 손 자세와 원본5클립 동일 일정 A/B부터. 피부·옷·몸통 구역 분리, 기존 heat 가중치는 기준선 보존. geometry-fit 품질과 새 weights 품질을 분리하고 최대4weights/finite/rest+curve exact, 실제 렌더, 웹 LBS 검증 뒤에만 후보 반환한다.

어깨는 극단적으로 뼈대 자체가 몸통을 가로지르면 skin만으로 해결할 수 없다. 포즈/IK 변경은 원본 모션 보존과 별도 계약이다. corrective morph를 연구하면 웹에서도 동일 pose driver를 구동하고 GLB 재수입까지 검증해야 한다. 이번에 corrective 구현/지원이 완료됐다고 주장하지 않는다.

## 협업 / 전달

- Multi: `01a13903-609c-7691-a258-9a890e01beb7`.
- game-dev-team: `01a13d31-184e-7960-9eac-fed37eccf181`.
- 사용자 추가 대상: `01a13d2d-374a-7363-b819-4db64e27e540`.
- 최초 반환 game-dev-team delivered, Multi queued였으나 이후 bmvaxm4pf-c에서 README/보존보고서 수신·5후보 미채택/doc43 기록 ACK. 추가 대상 전달은 bmvaxmwib-d 사용자 브리지로 내용 수신됨. 자동 MCP queued를 delivered로 바꾸어 기록하지 않는다. 중복 전달 무한루프 금지, 현재 세션 ID는 추정하지 말고 필요 시 확인한다.

## 도구 수준과 축적 원칙

추출/보존/검증 기반은 갖췄지만 범용 자동 스킨 보정은 연구 단계다. 사례 수만 늘리는 대신 체형·손 길이·어깨 폭·옷 구조가 다른 실패/해결 쌍을 축적하고 동일 회귀 검사로 평가한다. 성공 샘플을 깨뜨리는 개선은 탈락. 자동 지원 범위/사람 보정 범위를 명시한다.

기존 Motion Remap0.2와 메시에 새 weights를 주는 이번 연구는 별개다. 자동 리타게팅 성공을 자동 스키닝 성공으로 설명하지 않는다. Motion Remap 정본 docs/MOTION_REMAP_KNOWHOW.md와 tools/motion_remap/, source ZIP/556test 등 기존 MEMORY 기록을 참조한다.
