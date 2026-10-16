# 대포공 텍스처·발사 이펙트·사운드 복원 인계

2026-09-29. 원본 APK를 재판독해 41노드/82컴포넌트/21에셋을 추출했다. Mesh 7종, PNG 7장, 오디오 WAV 1개. export 오류0. Unity에 실제 반영/화면 대조는 Claude 담당이며 아직 이 자료만으로 완료 판정하지 않는다.

## 공이 무늬 없이 보이는 문제

**[원작값] 일반 공** root=`sharedassets2.assets#40` Ball. Bullet_Ball 메시=`6e342fcf80f954db690fb7e852ad809d#1`.

| 노드 | Renderer | Material |
|---|---|---|
| Ball/geo | sharedassets2.assets#55 | sharedassets1.assets#3 M_CannonBall |
| Ball/geo/shadow | sharedassets2.assets#54 | 같은 M_CannonBall |

M_CannonBall shader는 **OmniShade/Standard URP**. `_MainTex`와 `_SpecularTex` 둘 다 **sharedassets1.assets#191 Standart_BulletBall**(원본 철자 그대로). `_MatCapTex`는 **fa18bb4773bdf62499cfd3d309f0e0a7#1 1_matcap**. PNG 파일은 assets/manifest.json의 해당 key에 기록했다. m_FileID=0은 **자기 파일의 정상 참조**이며 null이 아니다. null 판단은 pathID=0으로 한다.

**큰 공**: BigBall/geo renderer sharedassets1#1284는 M_CannonBall_Big #4, `_MainTex`=sharedassets1#166 Big_BulletBall, `_MatCapTex`=동일1_matcap. **BigBall/geo/shadow renderer#1283은 일반 M_CannonBall#3**다. 자식까지 모두 큰 공 재질로 덮으면 원본과 달라진다.

`assets/meshes_native.json`은 UV/normal/tangent/submesh를 포함한 native Unity 메시다. 기본 Sphere의 UV에 텍스처만 얹으면 무늬 위치가 달라질 수 있다. 프리팹 local TRS/활성 상태는 prefab_nodes.json 및 prefab_components.json에 보존했다. X 반전·삼각형 역순·재중심화·scale bake를 추가하지 않는다.

**복원 순서 [자체]**

1. 현재 런타임 ballPrefab이 어느 프리팹인지 확인하고, 로비→Gameplay와 독립 Gameplay 씬 모두 같은 프리팹을 쓰도록 배선.
2. native Bullet_Ball 메시와 UV를 연결한 뒤 각 Renderer 슬롯의 원본 Material key를 연결.
3. `assets/manifest.json` Material.data의 saved properties/keywords를 기존 RS OmniShade 변환기로 처리. `_MainTex`를 URP Lit의 `_BaseMap` 슬롯에 잘못 넣지 않는다. 사용한 RS shader의 실제 프로퍼티와 맞춘다.
4. 기존 material_recovery_20260929의 HDR/키워드/색공간 계약을 그대로 적용. 이름만으로 다른 텍스처와 합치지 않는다.
5. 발사 전 장전공/발사 후 일반공/큰공을 각각 확인. 런타임에 새 material/color를 덮는 코드가 있는지도 검사.

텍스처와 재질이 원본에 존재함은 확인했다. **현재 누락 원인을 임포트 실패/프리팹 오배선/UV 누락 중 하나로 확정한 것은 아니다.** 위 연결을 실측해야 한다.

## 발사 이펙트 호출 경로

**[원작값]** BallController=`level2#124`, 176바이트 전체 해독, `ball_controller.json` 참조.

- CannonFireVfxPrefab → **sharedassets2.assets#38 PS_Cannon**
- CannonFireVfxSpawnPos → **level2 Transform#87**. 부모 체인 전체 `vfx_spawn_chain.json`; BallSpawnPosition(GO#24)과 다른 참조다.
- CannonAnimator → level2#102. 대포 anchor 아래 일반/큰공/무한 대포 계층/Animator/controller/clip 원문도 함께 제공.
- shootFeedback Sfx → sharedassets2#81 cannon_blast, Haptic → #80 Haptic_CannonFire. ShakeMode=0, PunchSizeMode=0.
- postInfiniteLockout=0.5초, autoShootCooldown=0.2초, cannonScaleTweenDuration=0.2초. 무한 발사 종료 직후 탭 연타가 일반 moves를 바로 소모하지 않게 하는 잠금이 별도로 있다.

**[원작 코드 판독]** `LaunchCurrentBall` **0x3990E24** 순서:

1. 발사 준비/공 확인 → 탄도 계산 → AimCannon.
2. ActiveCannonAnimator에 Fire trigger(**0x3990F88**).
3. spawn Transform의 **world position/rotation**으로 Vfx.SpawnTransient(**0x3991010**).
4. m_shootFeedback.Play(**0x3991028**).
5. BoosterManager.TryFireArmed 또는 일반 LaunchBall로 분기.
6. NotifyMoveUsed 후 다음 공 ResetBall.

즉 **아이템탄도 공통 발사 연출을 지나간다.** 낮은 단계 LaunchBall(**0x3991818**)만 직접 호출하면 이 공통 연출이 빠진다. 검사 시점 `Assets/_RS/Runtime/RsCannon.cs`에는 SpawnTransient/ParticleSystem/SetTrigger/CannonFireVfx 호출이 없었다. 이후 Claude 변경분은 재확인 필요.

## PS_Cannon 원본 구성과 수명

| 노드 | ParticleSystem pathID (sharedassets2.assets) |
|---|---:|
| PS_Cannon | 69 |
| ImpactCircle | 61 |
| SmokeBurst | 66 |
| SmokeBurst (1) | 64 |
| Glow | 63 |
| Smoke | 67 |

전부 포함한 ParticleSystem module/curve/gradient/burst/renderer 데이터는 `prefab_components.json`. 공 자체에는 별도 PS_Sparkle 및 TrailRenderer가 있다. 이들까지 발사 순간 VFX로 재생성하지 않는다.

- M_Additive=`6a70488c36d65dc4ab8ff395d7d36ef6#1`: **Universal Render Pipeline/Particles/Unlit**, 저장 SrcBlend=5/DstBlend=1, 텍스처 참조 없음. 파티클 vertex color/alpha가 작동하는 셰이더로 배선한다. OmniShade로 일괄 치환하지 않는다.
- M_TrailBall=`sharedassets1.assets#104`: 같은 shader family, SrcBlend=5/DstBlend=10. trail을 additive로 뭉뚱그리지 않는다.
- **원본 PS_Cannon 루트는 looping=true, length5**이지만 원본 SpawnTransient(**0x39466C4**)가 Spawn에 **lifetime=1.0초**를 전달한다. Spawn(**0x3946784**)은 lifetime>0이면 LongestPlay를 건너뛰고 DestroyAfterAsync로 넘긴다(**0x3946AD8–0x3946B18**). 루트 duration5만 보고 영구 반복하거나5초 유지하지 않는다.
- `Vfx_SpawnTransient.asm`, `Vfx_Spawn.asm` 제공. Spawn은 월드공간 시스템 여부에 따른 부모/scene 처리도 한다. 전환 씬에 남는 고아 이펙트가 없도록 Gameplay 소유권을 정한다.
- [자체] 풀링하면 모든 child particle과 trail을 Stop/Clear하고 TRS/시드/시간을 초기화. 1초 재생 후 반환, 오래된 비동기 반환이 재사용 인스턴스를 회수하지 않게 generation ID 사용. 원본과 동일한 pooling 주장 금지.

## 발사음과 진동

`audio/cannon_blast.wav` 실제 추출 완료. source AudioClip=sharedassets2#23, mono44100Hz, 원본 길이 약0.936초. `shoot_sfx.json`: SfxAsset volume1/volumeVariance0.1/pitch1/pitchVariance0.15/cooldown0.05초, 단일 AudioData clip volume1/pitch1/weight1. 변동 분포의 정확한 샘플링 식은 아직 판독하지 않았으므로 재생 구현에서 임의 분포는 [자체]로 표기한다.

Haptic_CannonFire raw/script 참조는 `shoot_feedback_sources.json`에 보존. 전체 진동 timeline은 미해독이며 데스크톱에서는 no-op 가능. 음소거 설정을 통과하고 UI 클릭/무효 조준에는 재생하지 않는다.

## Claude 수용 시험

- 장전공/발사공 모두 원본 줄무늬 텍스처 표시, UV/재질 슬롯 일치.
- BigBall geo와 shadow의 서로 다른 재질 유지.
- 일반/큰공/무한 발사 각각 muzzle VFX와 trigger1회, 발사음1회. 로드/미스탭/아이템 선택만으로 이펙트 없음.
- 100회 연속 발사 후1초 이상 대기했을 때 muzzle VFX 잔류 없음(공 trail 수명은 별도).
- 대포가 좌우 회전할 때 원본 spawn Transform을 따라 위치/각도 맞음. 발사 이후 월드 연기와 대포가 비정상적으로 함께 회전하지 않음.
- 로비 복귀/재시작/일시정지 뒤 중복 sound/ghost effect/오래된 cleanup callback 없음.
- particle vertex color·alpha·burst·size/lifetime curve를 대조. 이미지만 비슷하게 만드는 임시 white quad를 원본 재현으로 표시하지 않음.

자료 검증: export 오류0, PNG decode/hash·native mesh triangle/UV·WAV 헤더는 별도 validation에 기록. 게임 내 외형·파티클 실측은 아직 미검증.
