# Royal Smash 오프라인 정적 분석 결과

대상 버전: 1.13.359. 게임 실행 및 외부 요청 없이 원본 XAPK와 기존 dump.cs를 분석했다.

## 신규 확인 결과

7개 클래스에서 명시적인 생성자 초기값 51개를 복원했다.
기존의 씬 m_Script 연결 실패를 해결한 결과가 아니라, 컴파일된 생성자의 저장 명령과 상수 영역을 읽어 얻은 별도 근거다.

| 클래스 | 확인 항목 수 | 예시 |
|---|---:|---|
| BouncerSettings | 8 | m_minBallSpeed=8, m_ballSpeedMultiplier≈0.8, m_ballImpactSpeedMultiplier=1.5 |
| Ball | 9 | m_firstContactExplosionForce=3, Radius=4, Upwards=0.5, m_minSpeedToDecay=10 |
| ObstacleCommon | 5 | BreakForce/Radius/Upwards/MaxSpeed/Spin 초기값 |
| BarrageBombSettings | 9 | BlastSpeed=12, BlastRadius=6, AutoTriggerTntSpeed=20 |
| MagnetSettings | 2 | m_fieldRadius=6, m_attractionForce=60 |
| Obstacle | 10 | 마찰, 폭발 조건, 레벨별 물리 오버라이드 초기값 |
| BallController | 8 | InitialSpeed=5, AimContactOffset=0.5 |

각 항목의 정확한 float32 값, 원시 비트, 필드 오프셋, 저장 명령 주소, 상수 주소는
`static_physics/constructor_defaults.json`에 기록했다. 소수 표시는 읽기 쉽게 반올림한 예시다.
확인하지 않은 필드는 0으로 채우지 않았다.

## 검증과 한계

- 기존 Il2CppDumper의 필드 오프셋과 해당 생성자의 AArch64 저장 명령을 대조했다.
- ELF PT_LOAD 구간으로 가상 주소를 파일 위치에 매핑해 벡터 상수 안의 각 float32 값을 읽었다.
- 근거 디스어셈블리는 `static_physics/*_constructor.txt`, 원본 라이브러리 SHA-256은 JSON에 보존했다.
- 이 값은 생성자가 넣는 초기값이다. 직렬화된 씬/프리팹 값과 후속 코드가 덮어쓸 수 있다.
- 따라서 최종 플레이 수치, 특정 프리팹의 실제 설정값 또는 서버 운영 밸런스로 단정할 수 없다.
- 기존 씬/스크립트 연결 문제와 CDN 전용 리소스 부재는 여전히 남아 있다.

## 에뮬레이터 적용 가능성

- 제공된 XAPK의 네이티브 라이브러리 28개는 ELF machine 183(ARM64)로 일관된다.
  libil2cpp.usym.so는 ELF 라이브러리가 아닌 별도 심벌 자료다.
- 오전 Clash에서 확인된 ARM64 폴더 안의 x86_64 라이브러리 혼재 문제는 이번 라이브러리 목록에서 발견되지 않았다.
- 기존 x86_64 분석 AVD에서 ARM 변환 실행을 시도할 후보는 되지만, 이번 점검에서는 설치·실행하지 않았으므로 호환성 및 부팅 성공은 미검증이다.
- 오프라인 실행으로 로컬 메모리에서 씬/컴포넌트 값을 관찰할 가능성은 있다. 로그인·원격 자료가 필요하면 로딩 단계에서 막힐 수 있다.
- 오전의 격리 방식은 분석 흔적을 숨기는 방식이 아니다. 앱은 에뮬레이터/루팅을 로컬에서 감지할 수 있다.
- 사용자 조건을 유지하려면 실행 전에 외부 통신 차단을 재검증하고 실패 시 실행하지 않아야 한다.
  분석 인스턴스나 스냅샷은 이후에도 온라인으로 전환하지 않아야 저장된 이벤트의 지연 전송을 피할 수 있다.
- 게임사가 알 수 없다는 절대 보장은 할 수 없다. 이 결과는 오프라인 실험의 기술적 적합성 판단이다.
