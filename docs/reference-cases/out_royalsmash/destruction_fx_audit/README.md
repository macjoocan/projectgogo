# 오브젝트 파괴·이펙트 및 대포 발사 연출 검토

2026-09-16. 대상: 현재 `C:\00.SVN\MiniApp\_reference\royalsmash`. 원본 실행/에뮬레이터/CDN 접속 없음. 프로토 코드 수정 없음.

## [주장] 미달 — 원본 연결 대비 누락·다른 효과·파괴 상태 누락 확인

원본 오브젝트 139종의 연결을 대조했다. 유리병의 액체 효과는 원본에 있으며 현재 프로토에는 없다. 대포 포구 효과는 구현됐지만 발사 애니메이션·음향·잔상이 없고, 일반 공에 BigBall 착탄 효과를 중복 호출한다. 일부 효과가 존재한다는 것과 원작의 종류·트리거·파괴 결과까지 맞는 것은 다르다.

판정은 **구현/데이터 대조 미달**이다. 실제 브라우저 화면의 시각 품질과 원작 runtime 동등성은 **측정 불가**로 남긴다.

## [증거] 실행 및 산출물

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B -X utf8 'D:\99.기타\out_royalsmash\audit_destruction_sources.py'
node 'D:\99.기타\out_royalsmash\audit_destruction_runtime.mjs'
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B -X utf8 'D:\99.기타\out_royalsmash\summarize_destruction_audit.py'
git -c safe.directory='C:/00.SVN/MiniApp' -C 'C:\00.SVN\MiniApp' rev-parse HEAD
```

- repo HEAD `f6d2b2d8b49bf4bea5f7177ef1f48bad72228239`。작업 파일 기준은 `prototype_checks.json.sources`의 8개 SHA256이며 HEAD만으로 작업본을 식별하지 않는다. 실행 전후 해시 동일.
- 원본: APK serialized 프리팹139종, effect/보조 hierarchy15개, ParticleSystem 이미터53개, 판독 오류0. 저장 PPtr를 해석했으며 이름 검색만으로 관련 효과를 추정하지 않았다.
- 원본 `ObstacleCommon`은 pieces 배열 + 두 inline Feedback(SFX/haptic/alternatives/shake/punch) + 5개 float 순서로 판독하고 payload 끝까지 길이 일치 검증. 일반 Ball도 Feedback/retention 배열 포함 끝까지 길이 검증.
- 프로토: seed20260916, 현재 `breakBody`139종 호출 경로, 주입 접촉3건(ball/stone·TNT연쇄·Pinata임계), 실제 FX 모듈6종 생성/수명 시험. 렌더러 대신 실제 Three 오브젝트와 로컬 텍스처-loader 스텁을 사용. 접촉은 물리 충돌 E2E가 아닌 결정론적 이벤트 주입이다.
- 실제 FX 생성 수: muzzle71, impact16, dust14, tnt24, jar0, confetti36. tick3초 후 alive0. 참조 webp7개 존재 확인. 존재·생성·해제 시험이지 GPU 화질 검증이 아니다.

파일:

- `original_effects.json`: 원본 상세. APK/file/path_id, effect hierarchy, ParticleSystem/Renderer, material/texture PPtr, Cannon/Ball/Feedback.
- `prototype_checks.json`: 현재 파일 해시, 139종 파괴 호출 기록, 접촉3건 상태, FX6종 생성 결과.
- `handoff_effect_map.json`: 구현자가 읽기 쉬운 ID별 매핑과 이미터 요약. 원본 MinMaxCurve mode를 보존하고 올바르게 분류했다.

## [기준] 원본 저장 연결과 실제 프로토 소비 경로

### 오브젝트별 비교

| 분류 / ID 수 | 원본 저장 구성 | 프로토 현황·판정 |
|---|---|---|
| 유리병 JamJar /18 | 색상6종 `PS_Jar_Red/Blue/Orange/Pink/Purple/Yellow`; 유리병 파편4/6/7개; `jar_break` | 파편 그룹 수는18종 모두 일치. **색별 액체/유리 파티클은 미연결**, 공통 dust14개뿐. 파편의 형상·좌표까지 일치한 판정은 아님 |
| 돌 Stone /10 | `PS_Stone_Impact `, stone_break, 종별 파편 | 공통 dust로 대체. Square4 원본6개 vs 번들14개, Square5 원본9개 vs 번들1개 |
| 얼음 Ice /10 | `PS_Ice_Impact`, ice_break, 종별 파편 | 공통 dust. Square4/5는 Stone과 같은 파편 그룹 수 불일치 |
| 나무 Wood /10 | `PS_Wood_Impact`, boxCylinder_break | 공통 dust. WoodCylinder_1 원본3개 vs 번들9개 |
| 상자 Box /10 | `PS_Metal_Impact`, box_break/boxCylinder_break | 공통 dust. Square4/5 파편 그룹 수 불일치 |
| 컬러상자 ColorBox /45 | `PS_Metal_Impact`, box_break, 본체별 pieces11개 | 번들11개는 맞지만 **perBody=8 상한**으로 최대8개만 생성. 공통 dust |
| 기둥 Column /10 | `PS_Stone_Impact `, stone_break, pieces8~14 | 그룹 수 일치. 8개 초과는 상한 때문에 전부 나오지 않음. 공통 dust |
| 돼지 Piggy /1 | `PS_Metal_Impact`, box_break, pieces9 | 그룹9개지만 최대8개. 공통 dust |
| 캔 Can /11 | `PS_Metal_Impact`, can_hit/can_break, broken piece1개 | impact 종류 미연결. B.noShatter로 파괴경로 차단. **“broken 메시 파일이 없으므로 원본에 broken 처리도 없다”는 전제가 잘못됨** |
| TNT /2 | `PS_TNT_Explosion`, tnt_explode, shakeMode1 | 다른 프리팹 `PS_StickBomb_Impact`로 만든 preset 사용. 폭발 후 제거/집계 및 연쇄별 VFX 누락 |
| Pinata /1 | 별도 Pinata 클래스/전용 파괴 수명주기(이번 generic ObstacleCommon 없음) | 공통 confetti + impact. pop과 break 임계가 달라 pop 후 본체가 남는 경로 재현. 원본 전용 효과 전체 매핑은 미확정 |
| Bouncer /5 | `PS_Metal_Impact`, 특수 튕김 동작 | 자체 축소 dust bounce 사용. 정상공/강화 잔상 구분 미구현 |
| Table2 / Blocker3 / Hammer1 | 이번 Obstacle 기본 effect/파괴 테이블에 해당하지 않음 | 효과가 없다는 이유만으로 미구현 판정하지 않음. 고유 충돌·기믹별 원본 추가확인 필요 |

`impactEffect`는 충돌 효과, `explosionEffect`는 폭발 효과이다. 둘을 모두 “깨지는 순간 한 번”으로 합치지 않아야 한다. 원본 트리거의 전체 조건을 이번에 실행으로 증명한 것은 아니다.

#### 유리병의 액체 효과 — 확실한 누락 (P1)

`JamJarRed_1`의 Obstacle explosionEffect → `assets/bin/Data/668c75fb2fb1ca84e931ebd5b77eb3eb`, GO4 `PS_Jar_Red`.

이 프리팹에는 다음 **5개 이미터**가 연결되어 있다:

- 루트 flash: burst4.
- `JamParticle big`: burst6, Stretch 렌더, 수명 두 상수 .1/.6, 속도10/15.
- `Glass`: burst12, 유리 파티클.
- `JamParticle (1)`: burst50, Stretch 렌더, 수명 .2/.6, 속도10/30.
- `ImpactCircle`: burst8.

현재 `main.js:910` breakBody는 파편 생성 후 `burst('dust', tp)`만 부른다. `fx.js` SPEC에는 jar preset 자체가 없으며 실제 `burst('jar')` 생성0. 즉 병의 고체 조각은 일부 나오지만 **액체가 튀는 층과 별도 유리 입자층은 없다.** 물 표면용 WaterSplash를 유리병 잼 대체로 연결하면 안 된다.

#### TNT/Pinata 파괴 상태와 이펙트 (P1)

- `gimmicks.js:201` detonateTnt는 impulse와 `detonated=true`만 처리한다. 본체 제거·dead/hit·집계를 하지 않는다. generic 파괴는 `noShatter`의 TNT Infinity 때문에 막힌다.
- 주입 접촉에서 TNT2개 모두 detonated=true이나 둘 모두 dead=false/hit=false, destroyed0. 나중에 낙하하면 다른 경로로 집계될 수 있지만 **폭발 자체가 제거/집계를 완료하지 않는다.**
- VFX는 `main.js`의 직접 접촉 TNT에만 호출된다. 재귀로 터진 두 번째 TNT는 효과 호출이 없다.
- Pinata는 popped 임계8, 현재 일반 파괴 임계10이라 impact9에서 confetti가 나오고 popped=true이지만 dead/hit=false 및 destroyed0. 원본 전용 사망 동작과 통합해야 한다.

### 대포 발사 및 포탄 (P1/P2)

| 항목 | 원본 저장 근거 | 현재 프로토 |
|---|---|---|
| 포구 섬광·연기 | level2 MB124 → sharedassets2 GO38 `PS_Cannon` | `main.js:778` muzzle 호출, 실제71개 생성. **일부 구현**, 아래 범위 해석/shape/정렬 차이 있음 |
| 발사 애니메이션 | scene Animator102, `AC_Cannon`, Fire 상태·`Take 001` clip22 | cannon.lookAt로 조준 회전만 함. 발사 애니메이션/반동 재생 경로 없음. 원본 클립의 실제 반동 변위·시간은 이번에 재생하지 않음 |
| 발사음·진동 | shootFeedback → cannon_blast SfxAsset81 / Haptic_CannonFire80 | 웹 JS/HTML에 오디오/햅틱 재생 구현 없음. 모바일 진동 지원 차이는 별도 대체 가능 |
| 기본 포탄 잔상 | Ball GO40의 활성 TrailRenderer, time .12; PS_Sparkle 자식 | 구체만 생성. 기본 trail 및 sparkle 연결 없음 |
| 일반 공 첫 착탄 VFX | Ball MB82의 **m_firstImpactVfx=null**, firstImpactFeedback도 비어 있음 | 모든 일반 공 첫 접촉에 BigBall 기반 impact를 추가하고 **두 번 생성** |
| 발사 화면흔들림 | shootFeedback shakeMode0 | 안 흔들리는 것 자체는 누락으로 판정하지 않음. TNT shakeMode1과 구분 |

중복 원인: `main.js:844` 부근에서 `burst('impact')` 다음 `shockRing('impact')` 호출. `fx.js:194` shockRing은 고유 링이 아니라 **다시 impact를 .6배 크기로 호출**한다. 한 번 충돌에 impact16개×2=32개가 겹친다. fixture에서 scale1 / scale.6 두 호출을 재현했다. `shockRing('tnt')`도 preset 인자를 무시하고 impact를 부른다.

일반 포탄에 자체 firstImpactVfx가 없다는 것은 **충돌 대상의 material-specific impact도 없어야 한다는 의미가 아니다.** 대상 Can/Stone/Ice 등의 effect를 구분하여 호출해야 한다.

포구 기준도 다르다: 원본 별도 `CannonFireVfxSpawnPos` Transform87을 참조하며 로컬 pos(-.14,.42,5.42), scale≈8.657이다. 프로토는 공 발사점 `cannon + dir*muzzle3`을 VFX 위치로 공유한다. 원본 scale8.657을 월드 배수로 즉시 복사하지 말 것(부모 Transform과 spawn 구현까지 확인해야 함).

### 파티클 해석 오류 (P1) — “원본 커브가 없어 못 맞춤”이 아님

`fx.js:12` 및 `tools/dump-particles.py:mm`이 `minMaxState==3`을 두 커브로 오해하고 있다. **3=TwoConstants, 2=TwoCurves**이다. 원본 `dump.cs:1218308` enum과 [Unity 공식 소스](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Modules/ParticleSystem/Managed/ParticleSystemEnums.cs)가 일치한다. TwoConstants는 두 상수 사이에서 난수를 선택한다([Unity 문서](https://docs.unity3d.com/es/2020.2/ScriptReference/ParticleSystemCurveMode.TwoConstants.html)).

- Cannon SmokeBurst 속도는 저장 두 값35/40. 프로토는 scalar35×(.45~1) =15.75~35로 바꿨다.
- ImpactCircle 수명은 .09/.35, 프로토는 .0405~.09로 축소. 크기도 .02/.16인데 scalar 중심 임의 범위가 됐다.
- 커브 키가 비어 있는 것은 이 mode에서 정상일 수 있다. 실제 Curve/TwoCurves의 빈 커브 문제와 분리한다.
- shape/render도 서로 다르다. 원본 Stretch1과 Mesh4가 있는데 프로토는 전부 카메라 정면 PlaneGeometry다. Jar 액체를 둥근 공통 먼지로 대체하면 질감 차이가 커진다.
- 원본 gravityModifier를 옮겨도 현재 FX는 9.81을 하드코딩한다(`fx.js:215`). 원본 저장 Physics gravity=-24와 다른 기준이다. 원본 ParticleSystem gravity 적용 모드/런타임 변경 확인 후 맞출 항목이다.
- 알파 블렌드 그룹도 per-instance alpha 대신 RGB를 낮춘다(`fx.js:224`, material opacity1). 이는 투명 소멸과 같지 않아 연기가 어두워졌다 사라지는 현상을 만들 수 있다. 실제 픽셀 결과는 미측정.

### 파편 처리의 추가 차이 (P2)

- 그룹 매칭: Stone/Ice/Box의 Square4·Square5, WoodCylinder1 총7종은 native pieces 개수와 bundle 그룹 개수가 다름. Can11종은 native broken piece1개 vs bundle0. 이름/개수만으로 정확한 메시 매핑을 확정하지 않는다.
- 원본 CanSquare_1의 broken GO는 **기존 `Can_Square_1x1` Mesh를 재사용**한다. 별도 *_Broken_* 메시가 없어도 원본 broken 처리 구조는 존재한다. 이는 조각조각 부서짐이 아니라 한 덩어리 대체일 수 있다. 실제 파괴 조건은 별도 확인.
- 현재 전체 fragment budget180/perBody8. 원본 ColorBox11, Piggy9, Column8~14 전부 재현이 아니다(성능 근사로는 가능하나 라벨 필요).
- `fragments.js:92`에서 원본 조각 offset/geometry에 인스턴스 scale을 반영하지 않는다. 회전만 적용하고 별도 visual yaw도 전달하지 않아 스케일/회전된 본체와 파편 배치가 다를 수 있다.
- 원본 ObstacleCommon 저장값은 force8/radius2/upwards.1 또는.2/maxSpeed3/spin450°/s. 현재 공통2.6/1.2/.9/14/7과 다르다. **450°/s는 약7.854rad/s이므로 Rapier에450을 그대로 넣지 말 것.** 분포·적용 방식도 별도 비교해야 한다.
- 원본 ObstacleBreakSettings에는 독립 shrink/fade 지연·시간·곡선이 있다(`dump.cs:451530`). 현재2.4초 후 선형 opacity fade→3.2초 제거이며 shrink 없음. 원본 설정 asset의 실제 수치까지 이번에 확정하지 않았다.

## 권장 수정 순서

1. TNT와 Pinata의 “이펙트 발생 → 상태 종료/본체 전환 → 목표 집계”를 일관되게 하고 재귀 폭발마다 이펙트를 호출한다.
2. 일반 공 BigBall 중복 impact를 정리하고 대상별 impact/explosion/파편을 분리한다.
3. Jar 6색 liquid/glass/flash 이미터를 추가한다. `handoff_effect_map.json`의 참조와 원본 범위를 사용한다.
4. MinMaxCurve mode부터 고친 뒤 cannon 연기·flash를 맞춘다. 현재 임의 scalar 배율로 튜닝을 누적하지 않는다.
5. 발사 clip/반동, 기본 포탄 trail/sparkle, SFX 순으로 연결한다. 실제 화면 캡처로 위치·시간·크기를 검수한다.
6. 파편 그룹7종·캔 단일 broken 대체, 스케일/회전 전달, 수명/예산을 점검한다.

## [공백]

- 원작 게임 실행, 원작 runtime override/셰이더·재질 재할당, 동일 입력의 원작 영상 비교는 수행하지 않음.
- 실제 브라우저 GPU 렌더·청음·햅틱·발사 애니메이션 재생·전체 레벨 플레이 미실행. “회귀 없음” 주장하지 않음.
- 원본 ParticleSystemRenderer가 참조하는 일부 Material은 기본값/텍스처 null 상태로 저장돼 있다. 실제 보이는 텍스처/색이 runtime 재할당되는지는 미확정. 원본 효과명만으로 최종 재질까지 복원됐다고 주장하지 않음.
- Pinata 고유 파티클/줄 제거 전체 수명주기, Bouncer 강화 trail 상세, 글로벌 파편 shrink/fade asset 수치, SFX 클립 실제 재생시간은 추가확인 대상.
- 139종 breakBody 직접 호출은 그 handler의 분기 검사일 뿐, Table/Blocker 등 정상 게임 흐름에서 파괴돼야 한다는 주장이 아님.

## [잔여 위험]

현재 프로토는 다른 세션에서 동시에 작업 중이다. **이 보고서의 파괴/FX 파일 해시 시점**을 기준으로 읽고, 이후 수정은 재검증해야 한다. 원본 저장값을 그대로 옮겨도 엔진 차이·좌표·색공간·renderer mode·수명 모델 때문에 화면 동일성을 보증하지 않는다. `original_runtime_effects_verified=false`, `browser_visual_verified=false`.
