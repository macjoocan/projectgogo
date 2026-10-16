# Score -> 성장 콜백 연결 확인 (reply-to bmv812vsn-24)

결론 [원작 코드 판독]: 일반 물체 경로의 성장 입력은 PropIncomeValue[cost]에서 나온 점수다. Score.Add/OnScoreAmountChanged/TryExpandHole 사이에서 raw cost로 되돌리거나 IncomeUpgrade 배율을 곱하지 않는다. currentScore 누적값을 difference로 넘기는 것도 아니다.

연결:
1. LevelBehavior.OnPropEaten RVA0x21D8664, 일반 물체 branch0x21D8B80~0x21D8BAC: Prop.cost 조회 -> Constant.PropIncomeValue[cost] 조회 -> int를 float로 변환. 0x21D88F0~0x21D88F8에서 해당 점수를 s0에 넣고 ScoreController.Add 호출.
2. ScoreController.Add RVA0x213FFE4: 진입 s0(amount)를 s8에 보관(0x2140000). currentScore+=s8(0x2140024~30). OnScoreChanged가 있으면 s0=s8(0x214004C) 후 delegate 호출(0x2140054). 이 함수에는 multiplier나 IncomeUpgrade 호출이 없다.
3. PlayerBehavior.Start RVA0x21E7930: 이 instance를 target으로 ScoreChangeDelegate를 만들고 ScoreController.add_OnScoreChanged(0x213FC48)에 등록(0x21E7A0C~28). 참조 메서드는 OnScoreAmountChanged임을 ELF relocation + 원본 metadata method definition으로 확인했다.
4. OnScoreAmountChanged RVA0x21E8ABC는 두 명령뿐: w1=1(requireActiveGame), b TryExpandHole0x21E8AC4. s0(difference)는 수정하지 않는다.
5. 따라서 TryExpandHole의 collectedCost+=difference에 일반 물체의 변환 점수가 그대로 들어간다.

등록 대상 교차 근거 score_subscription_method_refs.json:
- 0x4196C88 ELF .rela.dyn RELATIVE addend0x4394918 -> raw encodedusage0x6000CD61 -> method index26288 -> metadata offset0x5313A8, declaringType4351, name OnScoreAmountChanged.
- 0x4196C80 -> addend0x4394908 -> encoded0x6000CD63 -> method26289 -> metadata offset0x5313CC, declaringType4351, name OnForceChangedScore.
method definition stride36 / metadata methods table bytes6278760는 나누어떨어지고, 두 record의 name/declaring type가 기존 dump PlayerBehavior 선언과 독립 일치한다.

Force 경로도 OnForceChangedScore0x21E903C가 s0는 그대로, w1=0으로 TryExpandHole 호출한다. 일반 경로와 게임활성 요구 플래그가 다른 것이다.

주의: 이 결론은 일반 Prop branch의 score chain이다. Cash/Coin/Voxel 등은 다른 income table을 조회한다. 저장 IncomeUpgrade.additionalIncome을 성장 점수 배율에 넣을 근거는 이 경로에 없다. 별도 골드/클리어 정산에서는 쓰이는지 아직 미결이다.

예: 일반 cost4 물체는 성장 점수9, cost5는11. raw cost4/5를 성장 입력으로 쓰면 원작과 달라진다. price10의 임계5일 때 collectedCost0에서 점수9가 들어오면 한 단계 성장 후 잔여4를 유지한다. 이 예는 확인된 식으로 계산한 것이며 해당 물체가 초기 구멍에 물리적으로 들어갈 수 있다는 판정은 아니다.
