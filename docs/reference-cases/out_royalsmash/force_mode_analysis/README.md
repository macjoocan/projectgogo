# 첫 접촉 폭발 ForceMode와 원작 배율 경로

2026-09-16 20:46 KST / Royal Smash 1.13.359 / 로컬 정적 분석.

## [주장]

1. **충족: 일반 Ball의 ApplyFirstContactExplosion은 ForceMode.Impulse(1)를 넘긴다.** Acceleration/VelocityChange가 아니다. 현재 Rapier applyImpulse와 힘 적용 모드의 종류는 대응한다. 이것이 폭발 구현 전체의 일치를 뜻하지는 않는다.
2. **충족: 원작에도 첫 접촉 힘 배율 설정이 존재한다.** 키는 `first_contact_force_multiplier`, Config.Get<int>의 fallback은 1. 별도로 `ball_mass_multiplier`도 있으며 fallback 1이다.
3. **미확정: 실제 플레이 시 그 설정에서 읽은 값.** 로컬에서 찾은 호출 기본값과 실행 중 선택된 설정값을 구분해야 한다.
4. **프로토의 레벨별 power 및 반경 cbrt(power)는 [자체].** 확인한 원작 경로의 힘 배율과 동등한 구현이 아니다. 원작 배율 자체가 없다는 결론도 틀리다.

이번 결과는 사용자 제공 lv1/3/9 클리어 차이의 원인을 하나로 확정하지 않는다. 보고된 무브 결과는 Claude의 시뮬 결과이며 이번에 재실행하지 않았다. MoveCount 예산만으로 동일한 조준 정책의 클리어를 보장할 수도 없다.

## [증거]

재현 명령:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B -X utf8 'D:\99.기타\out_royalsmash\audit_force_mode.py'
```

`index.json`에 입력 libil2cpp SHA256, metadata SHA256/소속 APK, 검증 8항목, 프로토 3파일 SHA256을 남겼다. 코드 이식은 하지 않고 호출·필드·설정 키를 분석했다. 원본 바이너리/metadata를 실행하거나 수정하지 않았다.

### ForceMode

- `Ball.ApplyFirstContactExplosion`: RVA `0x382AAFC` (dump.cs:450111).
- `0x382AEE4`: `mov w1, #1`.
- `0x382AEEC`: `bl 0x7A9E990`.
- 목적지 `0x7A9E990`은 dump.cs:1302680의 `Rigidbody.AddExplosionForce(float, Vector3, float, float, ForceMode)`와 일치.
- 실제 wrapper는 `0x7A9E9BC`에서 w1을 보존한다. AArch64의 FP 인자는 s0=force, s1–s3=center, s4=radius, s5=upwards이고, x0=this, w1=mode이다. 앞의 OverlapSphere 인자와 혼동하지 않았다.
- **같은 빌드** `ForceMode_schema.txt`: Force0 / Acceleration5 / Impulse1 / VelocityChange2.

근거 파일: `Ball_FirstContact.asm`, `Rigidbody_AddExplosionForce.asm`, `ForceMode_schema.txt`.

Impulse는 질량을 고려하는 순간 충격이다. Acceleration으로 교체해 난이도를 맞출 근거는 없다. [Unity ForceMode](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ForceMode.html)

### 원작 설정 배율의 출처와 소비

`BallController.OnEnable` (`0x398F284`)에서 다음 두 값을 읽는다.

| 저장 대상 | 설정 키 | fallback | 설정 읽기 / 필드 저장 RVA |
|---|---|---:|---|
| FirstContactForceMultiplier, 메모리 +0x130 | first_contact_force_multiplier | 1 (int → float) | 0x398F31C / 0x398F334 |
| BallMassMultiplier, 메모리 +0x134 | ball_mass_multiplier | 1 (int → float) | 0x398F338 / 0x398F344 |

호출 대상 `0x483A00C`는 `Config.Get<int>(string key, int defaultValue, uint _flags=10)`이다. **인자10은 배율이나 상한이 아니라 flags**다. Config_GetInt.asm의 실패 경로가 defaultValue를 반환함도 확인했다.

키는 이름 검색으로 추측하지 않았다. ELF RELATIVE relocation → metadata usage → string literal 테이블을 연결했다:

- GOT `0x82434D0` → `0x843D4E0` → token `0xA000A333` → literal 20889 → first_contact_force_multiplier.
- GOT `0x82434C8` → `0x8439438` → token `0xA0009309` → literal 18820 → ball_mass_multiplier.

힘 배율 소비는 `Ball_FirstContact.asm`의 `0x382AC20`(+0x130 읽기), `0x382AC40`(저장 force와 곱하기). 직접 맞은 Obstacle이 유효하고 +0x60의 m_explodes가 true면 `0x382AC50–5C`에서 저장 ExploderMultiplier(일반 Ball1.2)를 추가로 곱한다. 따라서 이 조건은 이제 Tooltip뿐 아니라 native 분기에서도 확인됐다. 파괴 가능 여부/noShatter와 동일시하지 말 것.

반경은 `0x382AC8C`에서 OverlapSphere용으로, `0x382AED0`에서 AddExplosionForce용으로 **Ball +0x40 저장값을 그대로 읽는다.** 확인한 함수 안에는 배율로 radius를 확대하는 계산이 없다.

별도 질량 배율은 `BallController.ResetBall`의 `0x398F870–880`에서 **공 Rigidbody 질량**에 적용된다. Obstacle.m_levelMassOverride(개별 장애물 질량)와 다른 항이다.

### 추가로 확인된 실행 시 조건

`LighterGameplay.Enabled` (`0x382B5AC`)는 `Config.Get<bool>("lighter_gameplay_01", false, 10)` 경로다. 키도 relocation/metadata로 확인했다.

첫 접촉 폭발의 upwards는 이 설정이 true일 때 **1.8배**, false일 때1배다 (`0x382AC74–90`, `0x382ADAC`, 상수0x14F3888). 일반 공 저장 upwards0.5라서 이 호출 인자는 false시0.5, true시약0.9다. 이번에 실제 선택 상태는 확인하지 않았다.

## [기준 / 프로토와의 비교]

| 항목 | 확인된 원작 경로 | 현재 프로토 |
|---|---|---|
| 모드 | Impulse1 | applyImpulse — 모드 종류 대응 |
| 힘 배율 | Config의 first_contact_force_multiplier | tuning[lv.order].power |
| 반경 배율 | 해당 함수는 저장 radius 직접 사용 | radius*cbrt(levelPower) — 자체 |
| 공 질량 배율 | 별도 ball_mass_multiplier | 해당 연결 이번에 검증 안 함 |
| Jar 등 조건 | directHit 유효 + m_explodes일 때1.2 | 전달된 상태로는 아직 소비 미구현 |
| 대상 수집 | OverlapSphereNonAlloc / collider 겹침 | bodies 중심점이 반경 안인지 |
| 폭발 거리·적용점 | Unity AddExplosionForce 호출 | rb.translation 기준 거리 + applyImpulse |

원본 LevelData의8필드 및 기존1,560레벨 구조 색인에는 `power`나 첫 접촉 힘 배율 루트 필드가 없다. 이는 **검사한 스키마/데이터 범위의 결과**이지 런타임 설정 시스템이나 모든 코드 경로의 부재 증명은 아니다. 프로토 `main.js:357`의 `tuning[lv.order]?.power ?? 1`과 `:910–911`의 힘·반경 동시 확대는 원작 레벨 데이터에서 복구한 식이 아니다.

또한 현재 `gimmicks.js:178–187`은 body 중심으로 대상과 감쇠를 결정한다. Unity 문서는 가까운 collider 표면점 기준으로 폭발 작용점/거리를 정하고, 내부 등 예외에서 질량 중심을 쓴다고 설명한다. 따라서 중심이 반경 밖이어도 표면이 겹친 긴 블록을 프로토가 누락할 수 있다. 실제 오차 방향/크기는 장면별 검증 필요다. [Unity AddExplosionForce](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rigidbody.AddExplosionForce.html)

원작 native 경로는 attachedRigidbody와 Obstacle을 확인하고 직접 맞은 Obstacle과 같으면 폭발 대상에서 제외한다(`0x382AE80–90`). 프로토 blast는 directHit 인자 없이 공만 제외한다. 이 차이는 주변 대상 누락과 반대 방향으로 작용할 수도 있으므로 단일 power 보정으로 묶으면 안 된다. 원작의 그룹/중복 제거 분기는 별도 추가 확인 대상이다.

## [공백]

- first_contact_force_multiplier / ball_mass_multiplier / lighter_gameplay_01의 **실제 적용값**은 미확정. 기존 config/*.json6개 문자열 검색에서는 해당 키를 못 찾았다. 로컬 모든 컨테이너의 설정을 전수 복원했다는 뜻은 아니다. 서버가 어떤 값을 준다고도 확정하지 않는다.
- 프로토 수정, 물리 실행 테스트, 원작 게임/에뮬레이터 실행, 게임사 통신, 700레벨 튜닝은 하지 않았다.
- ForceMode 확인만으로 Unity PhysX와 Rapier의 collider/관성/접촉점/충돌 시점/휴면·해제/감쇠/파괴 경로의 동등성이 보장되지 않는다.
- 원작 호출 범위를 넘어선 모든 메모리 쓰기·후킹·특수공/버프 경로를 부재로 증명한 것은 아니다. 일반 Ball 호출과 Controller 설정 경로에 한정한다.
- 과거 첫 접촉 보고서에서 미확정이던 ForceMode와 조건부1.2 분기는 이번 결과로 갱신된다. runtime_verified=false는 유지한다.

## [잔여 위험 / 다음 검증 순서]

**700레벨 튜닝 보류 유지.** `levelPower`는 지금도 [자체] 보정이고, 원작 Config 힘 배율은 별도 [원작 경로·실효값 미확정]으로 기록한다. 원작 배율의 존재를 power/cbrt(power)의 근거로 바꿔 쓰지 않는다.

1. 기본값 시험에서는 자체power1, 원작 Config fallback1, LighterGameplay fallbackfalse를 명시해 고정한다. fallback은 실행 실측값이 아니다.
2. 질량0.5/1/2인 동일 fixture로 impulse의 Δv 질량 역비례를 검증한다. 이것은 모드 시험이며 전체 엔진 일치 판정은 아니다.
3. 중심이 반경 밖/표면만 반경 안인 블록, 직접 타격 블록/주변 블록, 복합 collider의 한 몸체 중복을 각각 검증한다.
4. firstContact의 위치·시점, Jar 조건부1.2, 원작 감속 배열 및 minSpeedToDecay 소비, 누락된 복합 collider/관성을 점검한다. 같은 함수 공유는 코드 중복 해소이지 호출 입력/시점의 일치 증명이 아니다.
5. 대표 레벨 동일 조준/시드/실행시간의 변화 원인을 로그로 분리한 뒤, 남는 차이에 한해 자체 튜닝 여부를 판단한다.
