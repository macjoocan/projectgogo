# Obstacle layer / destruction audit — 2026-09-17

## [주장]

레이어 질의는 충족: 이 APK 빌드의 `Obstacle.Start()`가 `s_obstacleLayer = LayerMask.NameToLayer("Obstacle")`를 대입하며 저장된 TagManager에서 **7**이다. 8을 사용하는 것은 원작 근거와 불일치한다.

호출 이름 정정: 일반 블록 Ground/공중 첫 타격 경로는 **Complete → virtual SpawnBroken(strength)** 이다. `Explode`가 아니다. 전체 프로토 정확성/회귀는 **측정 불가(미실행)**.

## [증거]

재실행 명령:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B -X utf8 'D:\99.기타\out_royalsmash\audit_obstacle_layer.py'
```

네트워크 소켓 차단 audit hook 아래 APK 직렬화 데이터/ELF/metadata만 읽는다. 원작 코드는 실행하지 않는다. 출력 `native_index.json`의 여섯 검증 모두 true. lib SHA256:
`5819bd6f94ae20d0c877a4eaaa0ceabc43f1b6ce5fdb56997f2fd10b600cdf68`.

- `tag_manager.json`: APK의 `assets/bin/Data/globalgamemanagers`, TagManager pathID 3. 원본 파일 SHA256/분할 파일명 포함.
- `native_index.json`: 리터럴 역참조와 호출/대입 주소, 직접 분기 검색 결과, 검증값.
- `Obstacle_range.asm`: 0x3834C20–0x383DD1C 범위. 주소가 연속되어도 다른 클래스 함수가 사이에 포함되므로 dump.cs의 정확한 메서드 RVA를 기준으로 읽을 것.
- `Ball_OnCollisionEnter.asm`: 가상 슬롯 번호 교차 확인.
- `Tnt_Explode.asm`: base.Explode 직접 호출 확인용.

### 1. 레이어 대입

`Obstacle.Start` RVA 0x38376B0:

- 0x3837774–0x383779C: m_contacts가 이미 초기화됐으면 return.
- 0x38377D4–0x38377E0: 문자열 슬롯 0x823C9E0 역참조.
- ELF relocation → 0x8429D30 → metadata literal index 10911 → **Obstacle**.
- 0x38377E4: `LayerMask.NameToLayer` RVA 0x79F39B4 호출.
- 0x3837814: 반환값을 Obstacle static_fields +0x18 (`s_obstacleLayer`)에 저장.
- OnCollisionEnter 0x3834D20–0x3834D30도 m_contacts가 null이면 virtual Start(slot12)를 호출한다.

Awake나 .cctor에서 상수 7을 넣는 구조가 아니다. 동일 이름표를 사용한 초기화 결과가 7이다. 라이브 메모리를 관측한 값이라는 뜻은 아니다.

| index | 저장된 이름 |
|---|---|
| 0 | Default |
| 6 | Ball |
| 7 | Obstacle |
| 8 | LevelPlatform |
| 9 | BallPlatform |
| 10 | Ground |
| 11 | BrokenPieces |
| 12 | Blocker |
| 13 | Rope |
| 14 | ObstacleDetail |

### 2. SpawnBroken과 Explode를 구분해야 함

동일 빌드의 가상 함수 테이블 기준은 base 0x138 + slot × 16이다. slot12 Start의 0x1F8 호출(0x3834D2C), slot15 BallPunchesThrough의 0x228 호출(0x382A99C)로 교차 확인했다. dump.cs 선언:

| slot | 함수 | 함수 포인터 오프셋 |
|---|---|---|
| 20 | SpawnBroken, RVA 0x383CFB0 | 0x278 |
| 21 | Explode, RVA 0x383D600 | 0x288 |

- 비폭발형 분기: 0x383539C → 0x383540C. collider.gameObject.layer == 7이면 결정적 Ground/Ball 처리 대신 다른 경로로 간다. 이는 물리 충돌 전체 무시가 아니다.
- Ground 또는 허용된 공중 첫 Ball 타격: 0x3835594 Complete 호출 → 0x38355A4에서 **0x278/slot20** 로드 → 0x38355AC 호출. 즉 SpawnBroken.
- 폭발형 분기: 0x38353A4의 completed guard → 0x3835400에서 **0x288/slot21** 로드 → 같은 0x38355AC 호출. 즉 Explode.
- `Explode`는 자체적으로 0x383D6D4에서 Complete를 호출한다. Complete가 모든 종류의 파괴를 실행하는 함수라고 합치면 안 된다.

일반 블록용 속도 임계로 `m_explodeMinSpeed`를 공통 적용할 근거는 이 base 경로에 없다. 그러나 특수 파생 클래스의 추가 조건까지 전부 없다고 확장하지 않는다.

### 3. 추가 경로와 직접 호출 검색

- `EnterWater` RVA 0x383D978: 미완료일 때 m_explodes && detonateExploders이면 slot21 Explode(0x383DA44 → 0x383DA54).
- 비폭발형 && breakOnImpact && Common 및 Common+0x28 참조 유효: Complete(0x383DADC) → slot20 SpawnBroken(0x383DAE4 → 0x383DA54).
- 나머지 물 진입 경로는 Complete(0x383DAF4); 항상 Explode/SpawnBroken하는 것은 아니다.
- `FallOff` RVA 0x383DB38: Complete(0x383DB74) 후 GameObject 파괴 경로. Explode 호출 없음.
- ELF executable PT_LOAD를 4바이트 정렬 B/BL 대상으로 검색했을 때 base Explode RVA로의 직접 분기는 **1개**: Tnt.Explode 내부 0x393E360 → 0x383D600.
- 이 검색은 간접 가상 호출/델리게이트/리플렉션을 열거하지 않는다. 전체 Explode 호출자가 하나라는 주장이 아니다.

## [기준]

`il2cpp_dump/dump.cs`: Core.Obstacle TypeDefIndex1676의 필드/메서드/슬롯 선언, LayerMask.NameToLayer 선언. 동일 lib와 APK metadata의 리터럴, APK TagManager 원시 직렬화 결과를 교차한다. 난이도나 발당 제거 개수를 레이어 선택 기준으로 사용하지 않는다.

## [공백]

프로토 코드 변경/헤드리스 재측정/원작 실행/런타임 태그·레이어 변이 관측은 하지 않았다. Claude가 제시한 Table Surface 태그·씬 LevelController 248바이트 전량 파싱은 이번에 별도로 재추출하지 않았다. 특수 파생 클래스 전수 호출 그래프도 미검증. `runtime_verified=false`.

## [잔여 위험 / 다음 검증]

Claude가 제시한 Table의 Ground 태그와 layer8이 실제 이벤트 대상에서도 유지된다면, base 경로에서 layer8이라는 이유만으로 완료를 막을 수 없다. lv112 51/106 결과는 다른 소비 경로/초기화/접촉 이벤트를 점검할 단서이며 8로 바꾸는 근거가 아니다.

특히 태그 검사 대상과 레이어 검사 대상이 다르다. 0x3834D48에서 collision.rigidbody를 얻어 유효하면 그 GameObject를 태그 검사에 사용하고, 없으면 collision.gameObject를 사용한다. 반면 0x3834EAC–0x3834ECC의 레이어는 collision.collider.gameObject에서 읽는다. 프로토에서 둘을 root 또는 child 하나로 통일하면 결과가 달라질 수 있다.

권장 회귀 사례: 일반블록→layer7 블록, 일반블록→Ground-tag layer8 테이블, 일반블록→Ground-tag layer10, 접촉 중 Ball hit, 0.25초 공중 조건 전후 첫 Ball hit, Jar/Tnt threshold 전후, 물 진입, FallOff. 초기 정착 중 처리 시점 및 completed 중복 방지, 파편을 새 목표로 세지 않는지 각각 기록할 것. 아직 이 테스트들을 실행했다는 뜻은 아니다.
