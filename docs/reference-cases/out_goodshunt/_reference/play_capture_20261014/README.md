# Goods Hunt 原作 실기 캡처 / 2026-10-14

ADB emulator-5554 / and.lhhpub.goodshunt. 저장 초기화·구매·광고·부스터 사용 없음. 일반 플레이는 현재 시도 상태를 변경한다. 에이전트가 조작을 마친 뒤 Pause 상태로 남겼으며 Quit/재시작은 누르지 않았다.

- 01_current.png: 로딩 화면, 인게임 아님.
- 02_after_load.png: Level03 로비. 초기 계정 기본값이라는 뜻 아님.
- 03_ingame.png: 사용자가 조작하던 Level3. Sizeup / +1 / 목표 카드 72 / 타이머 02:06 표본.
- 04_user_observation_5s.mp4: 사용자의 플레이 관찰. 실제 5.152444초. 15초 요청이었지만 파일 길이가 다르므로 실제 길이를 정본으로 사용.
- 05_before_agent_input.png: Level5, Size1, 목표 카드 16/16/16, 02:30. 최초 스폰 바로 직후라고 확정하지 않음.
- 06_after_move.png: 에이전트 조이스틱 이동 후 흡수·Sizeup·+1 화면.
- 07_agent_movement.mp4: 실제 9.818722초, 450x800. 입력은 capture_manifest 참조.
- 08_after_second_move.png: 두 번째 조이스틱 이동 후. 큰 빨간 테두리와 내부 벽/검은 바닥이 보임.
- 09_paused.png: 작업 종료 Pause 화면. 현재 시도 유지.

관찰: 홀은 검은 원판만으로 보이지 않는다. 빨간 테두리, 안쪽 벽의 밝은 사각 패턴, 깊이가 있는 내부가 보인다. 물체가 기울면서 홀 안으로 이동하고, +1 텍스트/반짝임과 Sizeup 문구가 보인다. 조작 중 배경 구도가 바뀌고 홀은 화면 중앙 근처에 남는다. 정확한 세계 속도·흡수력·성장 임계·코인/XP 산식은 이 관찰만으로 확정할 수 없다.

녹화 평균 cadence 약 4.66 / 7.94 fps는 녹화 파일 수치이며 게임 실제 FPS가 아니다. 초단위 물리/회전 애니메이션 정밀 재현에는 부족하다. PNG는 900x1600 원본 캡처다. 파일별 SHA256을 manifest에 보존했다.

홀 원문 자산 연결은 ../ingame_handoff_20261014/player_native_visual_physics_chain.json 참조: root GO sharedassets3#609 / Transform705, 195노드, 렌더·콜라이더 등 컴포넌트43건, 반올림 없는 native TRS/PPtr.
Hole_Entrance: MeshFilter1260 -> Mesh101, Renderer1214 -> Material7.
HoleVoid: MeshFilter1238 -> Mesh95, Renderer1212 -> Material6.
Mask: MeshFilter1248 -> Mesh92, Renderer1180 -> Material20.
위 참조는 모두 sharedassets3.assets fileID0이다. 다른 파일 참조는 원문 fileID를 유지하고 serialized_file_references.jsonl로 풀 것.
PlayerComponent1893 및 PlayerFx1895 원문 JSON은 ../results/GoodsHunt_structured_objects.zip 안의 0001/7f33b31645fd/MonoBehaviour/1893.json, 1895.json. raw 바이너리는 GoodsHunt_native_raw.zip의 동일 경로 .bin. component_fields.json에도 source SHA와 원문 필드를 복사했다.
