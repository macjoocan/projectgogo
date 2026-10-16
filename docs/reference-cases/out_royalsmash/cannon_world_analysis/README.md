# 원본 대포 월드 Y / 공 생성 위치 확인

2026-09-16 21:45 KST · Royal Smash 1.13.359 · 오프라인 원본 씬/네이티브 호출 분석 및 프로토 진단.

## [주장]

**원본 씬 CannonBase의 월드 Y는 4.44다. LevelSpawnPos의 +1을 더하지 않는다.** 대포가 낮다는 이유로 올리거나 해머를 다시 늘일 근거는 이번 결과에 없다. 다만 이 값만으로 원작에서 해머 아래 통과가 의도된 설계인지, 해머 구현 전체가 맞는지까지 확정할 수는 없다.

| 대상 | 원본 저장 씬의 월드 위치 XYZ | 의미 |
|---|---|---|
| CannonBase Transform62 | (0, 4.4400001, -25.6200008) | 대포 상위 기준점 |
| Cannon 필드 대상 cannon_anchor Transform93 | (-.002848, 4.0099270, -25.8671160) | 실제 조준 대상으로 참조되는 객체 |
| BallSpawnPosition 대상 BallSpawnPos Transform80 | (-.000354, 4.0762851, -25.7052367) | 저장 pose의 공 생성 지점 |
| CannonFireVfxSpawnPos Transform87 | (-.010056, 4.2468855, -25.2854199) | 발사 VFX 위치 — 공 생성 위치와 다름 |
| LevelSpawnPos Transform48 | (0, 1, 0) | 레벨 엔티티 배치 기준 |

위 값은 **저장 씬의 부모 TRS를 합성한 값**이다. 애니메이션/조준/특수 대포/스케일 변경 후의 모든 발사에서 공 Y가 항상4.076285라는 뜻은 아니다.

### +1을 더하면 안 되는 이유

`Arena(Transform59, identity)` 아래에 `CannonBase(62)`와 `LevelSpawnPos(48)`가 **형제**로 있다. 대포가 LevelSpawnPos의 자식이 아니다. 따라서 레벨 엔티티를 +1 하는 것과 별개로, CannonBase4.44에 +1을 더하면 대포를 원본 저장 기준보다 1 높이는 것이다. 5.44는 낮은 값이 아니라 이 기준에서는 높은 값이다.

### 최신 프로토는 이미 y4.44

21:44 검사 스냅샷에서 `web/balance.js`의 `CANNON.pos=[0,4.44,-23.06]`, `cannonFor()`는 그대로 반환한다. `Sim.fireAt` 실제 실행에서도 cannon.y=4.44였다. 우편의 "현재5.44"는 이 코드 스냅샷과 다르다. 오래 열린 브라우저의 코드 캐시/실행 상태는 이번에 측정하지 않았다.

그러나 대포 기준점과 공 시작점은 같지 않다. 프로토는 `B.ball.muzzle=3`만큼 조준 방향 앞으로 공을 생성한다. 실제 현재 Sim.fireAt 실행 결과:

| 조준점 XYZ | 프로토 공 시작 Y | 프로토 공 시작 Z | 최초 속력 |
|---|---:|---:|---:|
| (0,4.44,0) | 4.472816 | -20.060179 | 135 |
| (0,8,0) | 4.930358 | -20.100346 | 135 |
| (0,12,0) | 5.406513 | -20.219955 | 135 |

원본 저장 BallSpawnPos의 z=-25.705와 비교하면 프로토는 이 표본에서 약5.5~5.6유닛 앞이다. 이것은 **저장 pose와 프로토 실행값의 비교**이며 원작 런타임 오차 실측은 아니다. 대포 z 자체도 원본-25.62 대신-23.06이라는 [자체] 프레이밍 보정이다.

### 발사 계산도 같은 식이 아니다

원본 `ComputeLaunchVelocity(start,target,speed)`의 일반적인 수평거리가 있는 분기를 읽으면, 수평거리 / speed로 도달시간을 정하고 높이차와 Physics.gravity.y로 수직 성분을 계산한다. 즉 speed135는 이 경로에서 **수평 속력 기준**이다. 프로토 `ballisticDir`는 전체 속력135인 낮은 탄도해를 구하고, 포구3유닛 이동 후 다시 푼다. 둘 다 중력을 고려하지만 같은 계산이라는 판정은 불가하다. 이는 네이티브 산술 흐름 분석이지 원작 코드를 프로토로 이식한 것이 아니다.

원본 일반 LaunchBall은 기존 Rigidbody.position을 입력으로 쓰고 isKinematic=false/useGravity=true 후 AddForce(mode2=같은 빌드 VelocityChange)를 호출한다. 원본이 중력 없는 직선 운동이라는 설명도 맞지 않는다. 첫 접촉 폭발의 mode1Impulse와 **발사 mode2를 혼동하지 말 것**.

## [증거]

재현 명령:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B -X utf8 'D:\99.기타\out_royalsmash\audit_cannon_world.py'
node 'D:\99.기타\out_royalsmash\verify_cannon_world.mjs'
```

- `scene_evidence.json`: APK 이름/직렬화 파일 SHA256, 참조 필드 오프셋, GameObject→Transform 전환, 부모 체인 원본 pos/quaternion/scale, 계산한 월드 위치. BallController124 payload 해시가 이전 완전 판독 결과와 일치함을 assert했다. PPtr은 파일 경계를 지키는 levelscope.ObjectIndex로 해석했다.
- `validation.json`: 별도 Three.js Matrix4 TRS 합성으로3참조 교차 검증, 최대 오차8.9e-16. 실제 Rapier 몸체를 생성하는 Sim.fireAt3표본. 입력 프로토4파일 SHA256 및 검사 중 변경 없음.
- `native_index.json`과4개asm: 원본 libil2cpp SHA256 일치, 제한된 함수 범위와 정확한 API RVA 매칭. 원본 프로그램 실행은 하지 않았다.
- `ResetBall.asm`: 0x398F70C에서 Controller+0x38(BallSpawnPosition) 읽기 → 0x398F718 get_transform → 0x398F724 Transform.get_position → 생성 호출0x398F7AC.
- `LaunchBall.asm`: 0x39918F8 Rigidbody.get_position → 0x399190C ComputeLaunchVelocity, 0x3991928 isKinematic(false), 0x3991938 useGravity(true), 0x399194C mode2 → 0x3991954 AddForce.
- `ComputeLaunchVelocity.asm`: 0x3992930/34 XZ차, 0x3992954–60 수평거리, 0x39929B4 수평거리/speed, 0x39929E0 Physics.gravity, 0x39929EC–2A14 높이/시간 및 중력 보상. 수평거리가 거의0인 예외 분기는 이번 비교 범위 밖.
- `LaunchCurrentBall_AimCannon.asm`: 0x3991348 Cannon.rotation 변경 및 0x39913BC Rotate 호출. 저장 pose를 불변 런타임 pose로 취급하면 안 된다는 직접 근거.

## [기준]

씬: `UnityDataAssetPack.apk/assets/bin/Data/level2`. MonoBehaviour124 Core.BallController의 `BallSpawnPosition`은 offset52 PPtr(0,24) **GameObject**, Cannon은 offset64 PPtr(0,29) **GameObject**다. 각각의 Transform은80과93이다. PathID24/29를 Transform으로 오인하지 않았다. 발사 VFX 참조 offset100은 Transform87.

비교는 같은 월드 좌표계와 같은 종류의 기준점을 맞춰야 한다. CannonBase 높이, 포신 조준 객체 높이, 공 spawn, VFX spawn을 섞지 않는다. 원본 저장값/네이티브 소비 경로/프로토 실행값/원작 런타임 실측을 별도 근거 등급으로 유지했다.

## [공백]

- 원작 런타임 조준·Animator·특수 대포·스케일 변경 후 유효 공 생성 위치 미관측. 저장4.0763을 모든 발사의 고정 Y로 강제하는 변경을 권고하지 않는다.
- 원작 해머와 공의 실제 동시 상태, 동일 조준/발사 시점에서의 접촉 여부는 미측정. Claude의162발0접촉 결과는 이번에 재실행하지 않았다.
- 원본 해머 피벗/로드/회전위상/스케일 전 체인의 정합성을 이번 대포 조회만으로 인증하지 않는다.
- 최신 볼 수정 답신122935의 표면/AABB·저속·Bouncer 수정은 이번 별도 대포 작업에서 재검증하지 않았다. 과거21:18의 실패를 최신 코드에서도 그대로라고 단정하지 않는다.

## [잔여 위험 / 다음 순서]

1. 대포 기준점에 LevelSpawnPos+1을 중복 적용하지 말 것. 현재 함수는4.44이므로 추가 높이 변경 없이 보존.
2. 원본 공 생성 참조 및 런타임 조준 영향, 프로토 자체z/포구3유닛/발사 계산을 분리해 동일 조준 조건으로 비교할 것. 메시에 맞춘 화면 보정값을 물리 정본으로 부르지 말 것.
3. 해당 해머 레벨·조준점·발사시각을 고정하고 해머 collider의 월드 위치/회전과 공 궤적을 함께 기록해야 마무리 판정 가능. 맞히기 위해 대포나 해머를 임의로 늘리지는 말 것.

결론: **대포 월드 기준Y 확인은 완료. "프로토 대포가 낮아서 못 맞힘"은 현재 근거로 지지되지 않음. "원작도 반드시 해머 아래로 지나가는 설계"와 "해머 구현 완료"는 아직 미확정.** 프로토는 수정하지 않았고 게임사 통신/원작 실행/튜닝은 하지 않았다.
