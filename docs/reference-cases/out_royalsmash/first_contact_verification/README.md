# 일반 Ball 첫 접촉 폭발 — 원본 재검증

2026-09-16 20:30 KST / Royal Smash 1.13.359 로컬 APK / 정적 분석만.

## [주장]

**충족: 요청한 5개 필드의 일반 공 프리팹 저장값과 출처를 확인했다.**
**측정 불가: 원작 실행 중 최종 힘·런타임 배율·프로토 동등성.**

중요 정정: 이 필드는 BallController 본문이 아니라 `Core.Ball` 본문에 있다.
`BallController.BallPrefab` 참조를 따라가면 요청한 일반 공이 나온다.

| 필드 | 원본 저장값 | 오브젝트 시작 기준 byte offset | 사용자 필드 시작 기준 offset | little-endian raw hex |
|---|---:|---:|---:|---|
| m_firstContactExplosionForce | 3 | 68 (0x44) | 36 | 00004040 |
| m_firstContactExplosionRadius | 2 | 72 (0x48) | 40 | 00000040 |
| m_firstContactExplosionUpwards | 0.5 | 76 (0x4C) | 44 | 0000003f |
| m_firstContactExploderMultiplier | 1.2 ≈ 1.2000000476837158 | 80 (0x50) | 48 | 9a99993f |
| m_minSpeedToDecay | 10 | 200 (0xC8) | 168 | 00002041 |

모두 float32다. 표의 offset은 직렬화된 오브젝트 기준이다. `dump.cs`의 `// 0x3C` 등은 **IL2CPP 실행 시 메모리 오프셋**이므로 이 표와 다르다.

## [증거]

재현 명령 (PowerShell):

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B -X utf8 'D:\99.기타\out_royalsmash\verify_first_contact_payload.py'
```

결과: controller_bytes=176, ball_bytes=204, chain=[124,40,82], matches_previous=true.

- `UnityDataAssetPack.apk / assets/bin/Data/level2 / MonoBehaviour 124`: MonoScript의 namespace/class가 `Core.BallController`인지 확인.
- 컨트롤러 오브젝트 offset 116의 `BallPrefab` PPtr를 해당 externals로 해석 → `sharedassets2.assets / GameObject 40 / Ball`.
- GO40의 실제 컴포넌트 목록에서 MonoScript `Core.Ball`인 `MonoBehaviour 82`를 확인.
- 두 MonoBehaviour 모두 사용자 필드 시작 offset 32. 컨트롤러의 남은 Feedback/시간 필드까지 읽어 **176/176 bytes** 소진.
- Ball의 앞 Material/Renderer 참조, 수명/경계/fade, 요청 4개 float, VFX/Feedback/WaterSplash/감속 배열을 순서대로 읽고 마지막 minSpeedToDecay까지 **204/204 bytes** 소진.
- 과거 `destruction_fx_audit/original_effects.json`의 `ball.values` 및 `ball.minSpeedToDecay`와 이번 APK 재판독 5개 값이 정확히 일치.
- [payload_evidence.json](payload_evidence.json)에 전체 object raw hex, 각 필드 offset/hex/value, object/SerializedFile SHA256, APK 경계 저장.
- 입력은 로컬 3개 SerializedFile만 로드했다. MonoScript는 별도 base APK의 `globalgamemanagers.assets`에 있으므로 AssetPack만 검색하면 누락된다. 도구는 APK 간 경계까지 확인한다.

검사 대상은 씬에 연결된 일반 Ball 1개, 무작위 시드/시뮬 판수 없음. 프로토 검사 시점 SHA256:

- `web/balance.js`: `756af80cc1d2867fb15906222a0b076a5bacf1eda918c20daa35768ed7948e14`
- `web/main.js`: `2ada0aa70883daf9f5d270512c890a20e597674cf24f2a1c14374ba14601730b`

## [기준]

필드 순서는 `../il2cpp_dump/dump.cs`의 `Core.Ball` 450003–450037행. 컨트롤러는 453773–453805행. 이후 PPtr와 가변 배열, 전체 바이트 길이로 경계를 교차 검증했다. 생성자 기본값이나 시뮬 추정값을 사용하지 않았다.

현재 프로토 `web/balance.js:108`부터는 Force 9 / Radius 2.6 / Upwards 0.8 / minSpeedToDecay 3이다. 일반 공 저장값 기준으로 각각 **3 / 2 / 0.5 / 10**과 불일치한다. `m_firstContactExploderMultiplier`는 1.2지만 현재 확인한 `B.ball`에 대응 항목이 없다.

이 값들은 기존 보고서에 이미 들어 있었지만 질문과 직접 연결된 raw offset 답신이 빠져 있었다. 이번 우편으로 미확인 항목을 명시적으로 정리한다.

## [공백]

- 게임/에뮬레이터/브라우저 실행, 프로토 코드 수정, 700레벨 튜닝·시뮬은 하지 않았다.
- 일반 Ball 이외 BigBall/특수 대포 프리팹 선택과 실행 중 덮어쓰기는 확인하지 않았다.
- BallController에 `FirstContactForceMultiplier`, Ball에 impactScale 관련 런타임 필드가 있다. 저장값만으로 그 최종 효과나 적용 순서를 확정하지 않는다.
- ForceMode, 실제 폭심 선택, 거리 감쇠·대상 수집·중복 collider 집계까지 이번 payload 확인으로 검증된 것은 아니다. 따라서 `Force / mass`를 원작의 확정 Δv로 단정하지 않는다.
- `m_firstContactExploderMultiplier`의 Tooltip은 첫 타격이 폭발성 장애물(Jar 등)이면 힘을 곱한다고 설명한다. 조건부 사용의 단서이며 무조건 전체 폭발에 1.2를 곱하라는 뜻이 아니다. `m_explodes`와 noShatter를 동일시하지 않는다.
- `minSpeedToDecay=10`은 감속 적용 문턱 필드다. 공을 속도10에서 삭제하거나 파괴 임계값으로 쓰라는 뜻이 아니다. 동작까지 동일하게 만들려면 소비 경로 확인 필요.

## [잔여 위험 / 전달 권고]

700레벨 튜닝은 계속 보류. 먼저 5개 저장값을 공통 설정/소비 경로에 반영하고, 웹과 Sim이 같은 값·조건을 쓰는지 확인해야 한다.

특히 `web/main.js:910–912`는 현재 force에 `levelPower`, radius에 `cbrt(levelPower)`를 곱한다. 기본값만 바꿔도 실제 사용값은 달라질 수 있다. 이 배율을 원본과 동일하다고 이번 자료로 정당화할 수 없다. 원본 런타임 배율과 프로토 자체 보정은 별도로 표시한다.

대표 단일 충돌/첫 충돌 1회성/Jar 조건부 배율/감속 문턱/웹·Sim 일치부터 재검증한 뒤 튜닝 재개 여부를 판단한다. 저장값 확보는 해결됐으나 **원작 물리 전체 확정** 선언은 아직 이르다.
