# PS_Jar_* 호출 경로와 파편 정정

## 저장 연결 [원작값]

`jar_effects_saved.json`: JamJar 18종 전부 `explodes=true`, `impactEffect=null`, `explosionEffect=PS_Jar_<색상>`.

| 색상 | 파일 (`assets/bin/Data/` 하위) | GameObject pathID |
|---|---|---:|
| Orange | 21b76b8caa88af54cad818f9fd8e6d73 | 1 |
| Red | 668c75fb2fb1ca84e931ebd5b77eb3eb | 4 |
| Blue | 9cd84db457b82f143bc28d5056d1965f | 4 |
| Pink | 533652b076e0ae746aec2382dcf33750 | 5 |
| Purple | bf92f68e2697f674489206fc710d6767 | 5 |
| Yellow | c48c30119cacc9840aba7aa9db3e5775 | 1 |

각 팩은 **ParticleSystem 5개 + Renderer 5개**: root / JamParticle big / Glass / JamParticle(색상별 이름차) / ImpactCircle. 유리 조각의 시각적 경로는 여기의 **Glass 파티클**이다. JSON에 Transform·모듈·renderer·참조 원문을 보존했다. 텍스처/UVModule/mesh PPtr까지 연결해야 하며, 하얀 billboard만 생성하면 재현이 아니다.

## 기본 폭발 경로 [원작 코드 판독]

```text
Obstacle.OnCollisionEnter (0x3834C20)
  explodes 분기 / 충돌 종류·속도 조건
  → virtual slot21 Explode(strength)
    기본 Obstacle.Explode (0x383D600)
      common.explodeFeedback.Play(strength, Feedback.Type 7)
      SpawnExplosionPerCell() (0x383D7C8)
      Complete() (0x383AAB8, 정산)
      GetComponentsInChildren<Collider>(true, buffer) → 모두 enabled=false
      Destroy(gameObject)
```

**0x3835400은 Explode 메서드 RVA가 아니라 OnCollisionEnter 안의 가상 함수 포인터 로드 주소**다. 주석을 정정한다.

기본 Explode에 **SpawnBroken 호출이 없다**. 일반 조각4/6/7개가 프리팹에 저장돼 있다는 사실로 이 경로에서 그 강체들이 생성된다고 결론 내릴 수 없다. 이전에 이를 근거로 원작 런타임 파편 수나 WebGL 부하를 계산한 설명은 철회한다. TNT override의 처리를 Jar 기본 폭발과 무조건 합치지도 않는다.

원작 Complete는 완료 플래그/정산을 하는 함수다. 이식본에서 Complete 내부에 visual dispatch를 모으는 설계는 가능하지만 [자체 구조]이며 재진입과 이중 정산/효과 생성을 막아야 한다.

폭발 분기 조건(0x383539C~5764): Ground이면 폭발 경로, Ball이면 보정 후 충격 속도>=m_explodeMinSpeed. 그 밖의 충돌이면 속도>=m_explodeMinSpeed*m_explodeNonBallSpeedMultiplier에 더해 **Abs(Dot(relativeVelocity.normalized,첫 contact.normal))>0.6**이 필요하다. 완료 플래그가 켜져 있으면 재발동하지 않는다. 단순히 모든 OnCollisionEnter에서 폭발시키면 부드러운 착지에도 연쇄 파괴가 난다. 필드별 수치는 엔티티 저장값을 사용한다.

### SpawnExplosionPerCell — 0x383D7C8

```csharp
if (!m_explosionEffect) return;
int n = Math.Max(1, m_size.x*m_size.y*m_size.z);
float half = (n-1)*0.5f;
for (int i=0; i<n; ++i) {
    Vector3 p = transform.position + transform.up*(i-half);
    Vfx.SpawnTransient(m_explosionEffect,p,transform.rotation);
}
```

**부피 셀 개수만큼 transform.up 방향에 1 world unit 간격으로 나열한다.** XYZ 격자 생성이 아니다. 이 호출에는 추가 lossyScale이나 충격 강도에 따른 효과 배율이 없다. n=1/2/3이면 효과 팩 1/2/3개, ParticleSystem 5/10/15개가 된다. 이름 접미사뿐 아니라 실제 m_size를 로그로 확인한다.

Vfx.SpawnTransient **0x39466C4**는 부모 null, attach=false, lifetime=1.0을 내부 Spawn(0x3946784)에 넘긴다. Spawn은 lifetime>0이면 그대로 DestroyAfterAsync(0x3946D5C)에 전달한다(0x3946AD8~6B18). 기존 muzzle transient와 같은 **1초 회수** 래퍼다. SpawnTransientFull로 임의 변경하지 않는다.

### impactEffect와의 차이

ImpactVfxFor **0x383C49C**의 기본 구현은 m_impactEffect를 반환한다. 일반 비폭발 충돌 분기에서 Ground/Ball 등의 조건을 통과하고 보정 후 충격 속도>10일 때 contact.point / LookRotation(-contact.normal)에 SpawnTransient한다(0x3835580).

Jar의 impactEffect는 null이다. **Jar 액체/Glass를 이 impact 경로에 연결하면 발동 조건이 달라진다.** explosionEffect 경로가 필요하다.

## Unity/WebGL 적용 순서 [자체]

1. JamJar의 explodes=true 설정을 읽고 일반 SpawnBroken으로 빠지지 않게 한다.
2. 6색 팩을 원본 계층/모듈/mesh/sprite/material 참조와 함께 임포트한다. 특히 Glass renderer를 누락하지 않는다.
3. 원물체 자식에 남기면 비활성화 시 함께 사라지므로 원본의 world spawn/회수 경로로 전달한다.
4. 동일 Jar에 같은 프레임 여러 접촉이 와도 한 번만 발동한다. 원물체 Collider 무효화와 완료 플래그를 확인한다.
5. 셀 1/2/3개 Jar를 단발 파괴하여 효과 생성 수와 Glass 표시를 실측한 뒤 동시 파괴를 측정한다.

**FPS 저하 원인은 미확정**이다. 원작에 없는 Rigidbody 파편 생성, Instantiate/Destroy, 투명 overdraw, 파티클 mesh, GC, 충돌 콜백 중 어느 것도 측정 없이 단독 원인으로 삼지 않는다. WebGL 개발 빌드에서 Main/Physics/Rendering 시간, GC Alloc, 활성 RB/Collider, PS/입자 수를 파괴 전후로 기록한다.

풀링이나 입자 수 절감은 [자체 최적화]다. 먼저 표시 경로를 복원하고 성능 변경은 독립 A/B로 측정한다. 최적화 수치를 원작 저장값과 섞지 않는다.
