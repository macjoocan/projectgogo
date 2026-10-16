# 로비 → Level2 시작 붕괴 조사

사용자 확인: 로비 LEVEL2 버튼으로 진입. 2026-09-29. C: 프로젝트는 읽기만 했고 Play 재현은 Claude에게 요청했다.

## 확인된 불일치: 시간 설정

| 설정 | 원본 APK | 현재 Unity 프로젝트 |
|---|---:|---:|
| Fixed Timestep | **0.0125 (80Hz)** | **0.02 (50Hz)** |
| Maximum Allowed Timestep | 0.02500000037 | 0.33333334 |
| Maximum Particle Timestep | 0.125 | 0.03 |
| Time Scale | 1 | 1 |

[원작값] `assets/bin/Data/globalgamemanagers#8 TimeManager`. 원본 fixed interval은 RationalTime 형식: 1764000 ticks × denominator1 / numerator141120000 = 0.0125초. 원시 hash는 evidence.json.

[현재 구현] ProjectSettings/TimeManager.asset. 검사 시점 _RS/**/*.cs에는 fixedDeltaTime 대입이 없었다. 프로젝트 저장값과 런타임 값이 같다는 최종 확인은 Play 로그 필요.

**기존 700레벨 안정성 검사는 240스텝/3초=80Hz로 명시적으로 돌린다.** 따라서 그 검사를 통과했다는 사실이 50Hz 실제 플레이를 검증한 것은 아니다. 시간 설정 불일치는 확정, 이것이 붕괴 단독 원인인지는 아직 미확정.

## 2레벨 정적 대조

- CanCylinder_1 98개 + Table_Rect 1개. physicsQuality=0, stabilize=false.
- 받침 p=(0,2,-2), size=(7,2), LevelSpawnPos=(0,1,0) 더해 배치.
- Resources/RS_Levels/Level_2.prefab의 위치 override **99개 모두 원본 위치+spawn offset와 multiset 일치**. 회전/각 하위 collider 전수 동치 검증까지 한 것은 아니다.
- prior spawn-stability.json: drift0.0723, fell0, penetration0, dynamic98, 통과.
- 현 CanCylinder_1: mass1.155, useAnalyticInertia=true, Cylinder radius.5/height1, multiplier(1,.5,1), explodes=false. 단순 누락으로 보이지 않음.
- RsGameplaySession은 Resources에서 프리팹 Instantiate. 기존 홀더 Destroy는 지연 호출이므로 실제 물리 스텝에서 홀더 중복이 없는지도 관측 필요. 코드만으로 중복 충돌이 발생했다고 확정하지 않는다.

## Claude 수정·재현 요청

1. 우선 **원본 시간 설정 3개 복원**. Fixed .0125, max .025, particle .125. Level별 임시 freeze나 collider 팽창으로 가리지 않는다. stabilize=false가 원본값이다.
2. 원인 분리용으로 동일 Level2/동일 경로에서 fixed interval만 .02 → .0125 A/B. 이후 나머지 시간 설정도 원본값으로 맞춘 최종 Play 확인. 실시간 3초의 비교라면 각 조건에 필요한 스텝 수가 다름에 유의.
3. 로비→Level2에서 시작 시 fixedDeltaTime/maximumDeltaTime, 홀더 수, 동적 RB98, 받침 최상면 및 10/40/240스텝 변위를 기록. 자동발사 없이 검사.
4. 그래도 무너지면 첫 변화 원인을 분리: 물리 위치 변화인지 Complete()→SetActive(false)로 받침 블록이 사라지는지. destroyed 카운트와 reason을 함께 기록. 에디터 Physics.Simulate 검사는 런타임 게임 판정 전체를 대신하지 않는다.
5. raw SpawnEntities / 저장 프리팹 Play를 같은 dt에서 비교. collider/관성 tensor가 Awake·OnEnable 후 같은지 확인.

원본 게임의 실기 lv2 거동은 이번에 관찰하지 않았다. 결과를 받기 전에는 '원본도 무너짐' 또는 '80Hz만으로 해결'이라고 확정하지 않는다.

재현 추출 스크립트: ../audit_lv2_runtime_20260929.py. evidence.json 및 source_level_00002.json 포함.
