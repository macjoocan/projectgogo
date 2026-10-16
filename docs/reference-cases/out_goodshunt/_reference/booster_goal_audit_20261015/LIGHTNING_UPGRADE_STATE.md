# Lightning의 업그레이드 참조와 성장 커서는 다르다

2026-10-15, bmv94y8rb-1k 회신. 기존 자료 우선, 원작 실행/소스 수정 없이 소수 메서드 추가 판독. peak commit0.118GB. 아래는 정적 판독이며 런타임 계정 저장/원격 override 전수는 미확정.

**결론: 같은 HoleSizeUpgrade 객체/단계 배열을 참조하지만, Lightning의 NextStage는 PlayerBehavior.nextEnergyStage가 아니다. ForceAdd→TryExpandHole는 플레이 중 커서만 증가시키며, 이 경로에서 BaseUpgrade.UpgradeLevel은 갱신하지 않는다.** '계정 영구 업그레이드'라는 수명/저장 의미까지 여기서 확정하지 않는다.

## 같은 자산을 가리키는 체인

[원작값] settings/0172_HoleSizeUpgrade.json = sharedassets3.assets MonoBehaviour**1833**, upgradeType1, stages price0/10/20/... . settings/0175_UpgradesDatabase.json = sharedassets3.assets**1836**, upgrades PPtrs=[1833,1834,1835]. stored_components.json의 level3 UpgradesController#76은 upgradesDatabase file2/path1836, playerUpgradeStat file2/path1838. 파일명0172는 추출 번호이지 native pathID가 아니다.

[원작 코드 판독] UpgradesController.Initialise0x21570D4는 DB.upgrades 배열을 static activeUpgrades에 보관하고 type→그 배열의 객체 레지스트리를 만든다(0x2157168..17C,0x21572B4..CC). 복제 객체를 새로 만드는 경로가 아니다. GetUpgrade<object>**0x26FC314**는 이 dictionary에서 type key를 조회하고 cast한다. 별도 계정용 객체를 선택하는 인자가 없다.

PlayerBehavior.Init state machine MoveNext**0x21EB2DC**: 0x21EB3E4 `w0=1` → 0x21EB3E8 GetUpgrade0x26FC314 → 결과를 player.holeSizeUpgrade(+38)에 저장0x21EB3F4.

Lightning callback0x1EA2134도 **w0=1→동일 GetUpgrade0x26FC314**(0x1EA2198..9C). 정상 동일 레지스트리 아래 두 소비자는 같은 HoleSize1 객체를 사용한다. 실행 중 레지스트리가 다른 외부 코드로 교체되는 경우까지 조사한 것은 아니다.

## 상태는 둘

| 상태 | 소유자/offset | 조회/변경 |
|---|---|---|
| UpgradeLevel | BaseUpgrade +28 int | CurrentStage/NextStage/IsMaxedOut가 읽음 |
| nextEnergyStage | PlayerBehavior +D4 int | 플레이 성장 배열 인덱스, Reset에서 UpgradeLevel+1로 시작하고 흡수 성장 시+1 |

BaseUpgrade.CurrentStage0x21A89C8는 upgrades[UpgradeLevel], **NextStage0x21A8A08**는 upgrades[UpgradeLevel+1](배열 끝이면null). IsMaxedOut0x21A8994도 UpgradeLevel+1와 배열 길이 비교. Player의 +D4는 읽지 않는다.

Player.ResetPlayer0x21E9834: +38의 UpgradeLevel(+28)을 읽어 nextEnergyStage(+D4)=level+1(0x21E9C4C..5C), NextStage.Price/2로 초기 energy threshold(+CC) 설정(0x21E9C60..78), 잔여 energy(+D0)=0. completely=true일 때만 앞부분 virtual ResetUpgrade를 호출하는 경로가 있다(0x21E98BC..D0). 모든 재시작에서 객체 단계가 항상0이라고 확대하지 않는다.

TryExpandHole0x21E8AC4: +D0에 difference 추가→+CC 도달 시 임계 차감. **GetStage(nextEnergyStage)**를 통해 단계 설정(0x21E8C10..1C,0x21E8C54..60). 마지막 nextEnergyStage++ (0x21E8F54..60), 다시 GetStage(newIndex)(0x21E8F6C), 다음 Price*.5 threshold(+CC) 갱신. **BaseUpgrade.UpgradeLevel 쓰기나 UpgradeStage 호출 없음.**

GetStage의 정확한 generic RVA는 **0x27F72D4**. 기존 자동 disasm 주석에서 이 주소가 `TestUpgrade`로 잘못 표시된 것은 공유 generic 메서드 주석 파서의 별칭 오류다. dump의 GenericInstMethod 목록 및 `generic_027f72d4.txt` 원문은 입력 index로 upgrades[index]를 반환하는 조회이며 단계 쓰기 없음.

대조용 실제 UpgradeStage0x27F7284는 BaseUpgrade+28을 증가시키고 OnUpgraded를 호출한다. 이는 TryExpandHole에서 호출하지 않는다. ResetUpgrade0x21A8CCC는+28=0. HoleSizeUpgrade.Initialise0x21F3320는 progressBar dictionary를 구성하며 해당 본문에는 계정 저장 로딩/UpgradeLevel 증가가 없다. 계정 저장 여부/외부 UpgradeStage 호출 주체 전체는 이번 좁은 조사로 확정하지 않는다.

## Lightning 구현에 미치는 영향

Lightning 최종 callback은 매회 **upgrade.NextStage.Price 전체**를 ForceAdd한다. 그 ForceAdd의 Player callback이 nextEnergyStage를 올려도 upgrade.UpgradeLevel은 그대로이므로, **이 경로만 실행되면 두 반복이 읽는 Price는 같다**. 이전 인계에서 '다음 단계를 다시 조회한다'는 것은 getter를 매회 호출한다는 뜻이며, 다음 반복 Price가 자동으로 올라간다는 뜻으로 해석하면 틀린다.

따라서 Player의 현재 커서로 `stage[nextEnergyStage].price`를 Lightning에 넣거나, ForceAdd 뒤 upgrade.UpgradeLevel을 임의 동기화하지 않는다. 원본 객체의 UpgradeLevel을 별도로 유지한다. 일반 물체 수집의 price/2와 Lightning.NextStage.Price 전체도 구분한다.

[계산 예시/원작 실행 아님] UpgradeLevel0, nextEnergyStage1, 잔여0, stage prices[0,10,20,30,...], callback2회라면 각 ForceAdd10. 첫 호출 threshold5 차감→잔여5/cursor2/next threshold10, 둘째 호출 +10 후10 차감→잔여5/cursor3/next threshold15. UpgradeLevel은0 그대로. 저장·초기 상태가 다르면 결과도 다르며 모든 시점에 정확히 Size+2를 보장하는 규칙은 아니다.

증거: disasm_021570d4/021a89c8/021a8a08/021a8994/021eb2dc/021a8ccc/021f3320.txt, generic_026fc314/027f7284/027f72d4.txt, 기존 ../code_audit_20261014/disasm_021e9834/021e8ac4/021e903c.txt. generic_upgrade_ranges.json은 바이트 범위/해시. GetUpgrade512B 출력은 다음 함수 일부가 포함되며 첫ret0x26FC43C까지만 이 getter 본문으로 사용.
