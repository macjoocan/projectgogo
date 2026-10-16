# v4 형상 고정 가중치 분리 연구

직접 작성한 실험 스크립트3개다. 원작 자산/Blender/GLB/렌더는 없다.
입력은 D:의 독립 연구 사본에 의존하므로 코드를 읽고 실행한다. import시 실행하는 연구 코드이며
공통 CLI나 무설정 자동 보정 기능이 아니다. 현재 후보는 미채택이다.

- intake_v4.py: Multi 입력6개를 C:에서 읽어 D:로만 선별 복사/해시.
- harmonic_v4.py: 고정 v4 형상에서 국소 harmonic 가중치 A/B,125skin·실제 렌더·명시 Action 저장.
- check_v4_preservation.py: 별도 재열기로70rest·5native Action/3500curves/459900keys·UV·손외weights 대조.

원본/라이브 Blender/Multi 코드는 변경하지 않는다. 연구 결과와 실패는
../../../docs/MULTI_HAND_V4_FOLLOWUP_20261016.md를 본다. Blender 런처는 별도
tools/watchdog.py로 프로세스 트리 private commit2.5GiB 제한을 적용했다.
