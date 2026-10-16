# PointsExplode 풀 생성·부모·레이어·스케일 판독

[원작 코드 판독] Goods Hunt 1.9.1 ARM64 원본 ELF 정적 선택 판독이다. 원작 실행/설치 변경/구현 소스 변경 없음. `declarations.json`에 선택 54개 메서드 RVA/ELF offset/범위 SHA와 capped0을 보존했다. 각 범위는 다음 선언까지이며 독립 심볼 크기 확정은 아니다. 모든 선택 메서드를 상세 해석했다는 뜻은 아니며 아래에 해석한 범위를 명시한다.

## Spawn — 0x1D65C10

1. 입력 GameObject가 Unity null이면 null 반환.
2. m_Pools(+28)를 순회하여 pool._gameObject(+10)가 입력 prefab과 같은 풀을 찾는다.
3. 있으면 ObjectPool.Get(1D65E00). 없거나 반환 인스턴스가 Unity null이면 새 ObjectPool(prefab)을 만들고 m_Pools에 추가한 뒤 Get.
4. 반환 GO.SetActive(true): **1D65DC4**.
5. GO.transform.SetParent(null): **1D65DD8..1D65DE0**.
6. 반환.

이 Spawn 본문에 set_layer/재귀 layer 변경/SetLocalScale/SetPosition/SetRotation 호출은 없다. SetActive(true)가 **부모 해제보다 먼저**다. OnEnable의 임의 일반 동작까지 없다고 주장하지 않는다.

## ObjectPool.Get / Create

- Get(1D65E00): stack(+18)에 항목이 있으면 Pop, 없으면 Create(1D66994); spawned list(+20)에 추가 후 반환.
- Create(1D66994): prefab(+10)을 **Instantiate<T>(original)** 한 인자 오버로드로 복제(1D669F8), clone.name=prefab.name(1D66A24). 별도 parent/pose/layer/scale 인자가 아니다.
- 주의: disasm 자동 주석의 Instantiate(original,position,rotation)는 공유 제네릭 오표기다. dump.cs GenericInst RVA269A534는 **Instantiate<object>(original)**에 대응한다. 마찬가지로 27AE0F0는 Stack.Pop, 2A4A520은 List.get_Item이다.

## SetParent 한 인자 오버로드 — 0x3CB11A8

3CB11D8..3CB11EC에서 x0=this/x1=parent/**w2=1**로 엔진 호출에 전달한다. 따라서 Spawn의 parent null 설정은 **worldPositionStays=true**다. 스케일을 1 또는 100으로 직접 재설정하는 호출이 아니다. 실제 엔진 내부 분해/수치 정밀도는 이 wrapper만으로 검증하지 않는다.

## 반납 — DespawnAndReset 0x1D66128

GO.SetActive(false)(1D66150) → GO.transform.SetParent(manager.transform)(1D66180, 위와 같은 worldPositionStays=true) → ObjectPool.Push(1D6681C). Push는 spawned list에서 제거하고 stack에 넣는다.

이 이름의 Reset을 localPosition0/localRotation identity/localScale1/layer reset으로 해석하면 안 된다. 해당 본문에 그런 setter는 없다. manager의 부모 스케일·외부 변경이 개별 재사용 시 미치는 수치 결과는 별도다.

## OnRemove 측 후처리

근거는 `../goal_card_code_audit_20261015/disasm_01d2d630.txt` 및 `disasm_01d2da44.txt`다.

- b__4에서 controller.cardParticle(+70)를 Spawn에 전달(1D2D7E8).
- 반환 FX를 저장하고 SetActive(false)(1D2D818).
- .07500000298 독립 지연 후 b__5: FX.SetActive(true)(1D2DABC) → FX.transform.position=card.transform.position(world)(1D2DB0C).
- 이 두 callback 본문에 추가 SetParent/SetLayer/SetLocalScale/카메라 좌표 변환은 없다. 카드 자체에 대한 DOScale은 별도이며 FX 배율 조정으로 옮기지 않는다.

따라서 이 좁은 경로에서는 **Canvas 하위 부착·UI layer 전환·임의 배율 조정이 확인되지 않는다.** Spawn은 오히려 parent를 null로 해제한다. 저장 Points subtree에는 별도 MonoBehaviour/UIParticle가 없다는 기존 조인과 일치한다.

## 유지되는 미결

`../card_projection_audit_20261015/`의 Overlay/null worldCamera, level2 저장 enabled camera의 layer0 미포함 사실은 이 판독으로 해소되지 않는다. 다른 씬/실행 중 카메라·Canvas 변경과 실제 원작 Points 표시 여부는 미확정이다. 이 원문을 근거로 특정 투영 카메라나 scale100을 만들지 않는다. 파생 UI 합성 adapter를 쓴다면 원작 경로와 구분한다. 별도 카드 UIParticle3398의 Play 소비는 이번 범위가 아니다.
