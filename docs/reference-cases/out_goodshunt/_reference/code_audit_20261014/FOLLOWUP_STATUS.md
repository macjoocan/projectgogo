# Goods Hunt 후속 인계 상태 — 2026-10-14

## 현재 구현 세션 회신
bmv82jl5v-2d: 초기 KINEMATIC + 원래 collider 유지 / fit 진입 시 DYNAMIC / 임의 outward push 제거. Level_005 빈 공간 이동 후 933개 position/rotation exact 보존 회귀 통과는 상대 세션 보고이며 이 분석 세션의 독립 재실행 결과가 아니다. fit 활성계기는 웹 가정으로 유지.

## 신규 원본 근거
- PROP_ACTIVATION.md: Init/Reset/Activate/Inactive 및 layer7 트리거·holder Nearby 제한 조건.
- GROUND_AND_TRIGGER.md, hole_trigger_native_chain.json: 실제 collider 형상/부모 TRS/root radius scale, Ground MeshCollider 갱신과 extrusion, static 활성 한도.
- CAMERA_BLEND_DAMPING.md: EaseInOut 2초와 exp damping 원작식.
- SPECIAL_PROP_BRANCHES.md: 특수 타입 enum/콜백 순서/Bomb guard.
- ../shader_audit_20261014/README.md, inventory.json: compiler GLSL 123개 및 keyword/entry 검증.

## 미결
지면 outer-bound/삼각형 전체 독립 재현, 웹 물리의 fit·접촉 동등성, waiting counter 전체 흐름, marker pull 호출 연결, 특수 모드 전체 타이밍, Cinemachine 전체 업데이트 순서, 실제 shader variant/pass 매핑 및 웹 GPU 대조는 완료하지 않았다. 원문 enum/값/주소와 구현 가정을 섞지 않는다.

## 전달
위 4건 추가 인계는 Goodhunt 세션 01a139fa-e45c-7783-99c4-04acc274b5ca에 MCP session_send로 전달 완료 확인. 상대 프로젝트 코드는 변경하지 않았다. 원본 설치/계정/서버 조작 없음.

## 후속 2i/2j 판독 및 전달
GROUND_TOPOLOGY_REFERENCE.md / ground_reference.py / ground_fixtures.json: 요청 3함수에 InitSurfaceGround를 더해 37top/156indices 및 74extruded/534indices 독립 계산. 중앙 면적/indices/closure/extrusion 검산 통과, Android sincosf 최하위 비트·PhysX runtime 미검증. Update는 diff만 더하며 clamp하지 않는 원문 유지.
PULLER_FORCE_REFERENCE.md: 실제 방향 Y=-3, Gravity[nextEnergyStage-1], Acceleration5/비활성 Activate후return. 호출 계기 미결 유지.
LEVEL3_LIGHTING_REFERENCE.md / level3_light_chain.json: 파일 level3의 Light/부모TRS/SH27 원문. Gamma 프로젝트/Hard shadow strength0.3. 파일명을 Stage3와 혼동하지 않음.
위 자료 각각 MCP 전달 완료 확인. bmv84fw3p-2l에서 Goodhunt는 5fixture vertices/indices deepEqual 및 총14unit PASS 보고, browser 검증은 당시 진행 중. 이 세션의 웹 독립 실행 검증은 아님.
