# 목표 카드와 오디오 연결

## 목표 카드

[원작 코드 판독] HiddenGoal.Init0x21F4B28→GoalCard.SetHidden(true)0x1E02D5C: hiddenCover(+A8) GameObject 활성화. 카드 자체/목표 삭제가 아님. OnCardInteraction0x21F4B58은 hidden이면 cover off 후 AttachMechanic(None0). CardController.ReduceCard0x1D2BD08는 남은 수량 감소 후 remaining>0 경로에서 mechanic interaction(0x1D2BEF4..BF04)을 호출한다. 마지막1개면 바로 완료 경로이며 무조건 reveal frame을 강제하지 않는다. 단순 카드 탭으로 reveal된다는 근거 없음.

CheckHiddenCardMechanic0x1D2C134는 카드 완료 뒤 별도 조건부로 첫 hidden을 열고 return하는 경로가 있다. LINQ closure predicate의 전체 gate는 미해독. 따라서 Hidden 전체 동작을 완전 복원했다고 표시하지 않는다.

Bonus.Init0x21F4BCC는 card 보관만, OnCardInteraction0x21F4BD4는 ret. ctor/factory에 BonusValue50이 있지만 자동50코인 지급/별도 승리 조건의 근거 없음. [상대 세션 집계] numbered910맵3037목표 모두 mechanism0. 현재 알려진 실제 Hidden/Bonus 대표맵 없음. 테스트 시나리오는 자체라고 명시.

## 실제 오디오 이벤트 키 [원작 코드 판독]

followup_native_evidence.json은 ELF literal slot→RELA→metadata token→UTF8 offset 및 호출 직전 명령어를 보존한다. 아래는 문맥을 대조한 연결. key 이름만으로 비슷한 clip으로 대체하거나 모든 섭취마다 두 경로를 중복 호출하지 않는다.

| 이벤트/함수 | 정확한 key | 호출 RVA |
|---|---|---|
| ButtonTapSound.OnPointerDown, playSoundByDefault=true | `Sound 7` |0x1D6295C|
| 일반 섭취 LevelBehavior.OnPropEaten | `Hole_Eat_Normal` |0x21D8B30|
| 목표 섭취 LevelBehavior.OnPropEaten | `Hole_Eat_Goal` |0x21D8A10|
| 목표 연출 OnEffect 별도 경로 | `Hole_Eat_Goal` |0x21D93DC|
| Size 상승 TryExpandHole | `Hole_Level_Up` |0x21E8D90|
| 카드 제거 OnRemoveCard | `Interface Button` 후 `Goal_Card_Completed` |0x1D2C574 / 0x1D2C58C|
| Bomb guard 통과한 OnBombEaten | `Hole_Eat_Bomb` |0x21B2224|
| 클리어 전환 StateLevelCompleteTransition.OnEnter | `Firework2` |0x1D98218|
| 시간초과 GameRefManager.OnTimeUp | `22186 marimba failed ring double-full` |0x1E3C038|
| Growth 활성 | `Hole_GrowthUp` |0x1CC61E8|
| Hint 활성 | `Hole_Hint` |0x21EEB80|
| Magnet 활성 / Resume | `Hole_Magnet` |0x21F0B8C /0x21F1AB4|
| Shield 활성 / Resume (원문도 같은 키) | `Hole_Magnet` |0x1CC64C8 /0x1CC7438|
| Freeze OnFreeze | `Game Efx Freeze` |0x1EA17A4|

일반/목표 OnPropEaten에는 이전시각과 **DateTime.Now 차이 >100ms** 조건이 있다(0x21D89D0..DC,0x21D8AFC..B08); 같은 timestamp 필드+68 사용. 모든 물체마다 무제한 재생하는 해석과 다름. OnEffect 호출과의 상위 연출 타이밍/중복 방지 전체는 기존 source 흐름과 함께 판단.

`Firework2`는 클리어 전환 진입의 실제 소리이지 모든 승리 관련 소리의 전수 목록은 아니다. 시간초과 실패와 폭탄 실패 소리는 서로 다르다. 공통 fail에 하나의 소리를 강제로 묶는 근거 없음. 클릭도 이 ButtonTapSound 컴포넌트 경로의 키이며 모든 UI가 같은 컴포넌트를 사용한다는 전수 증명은 아님.

기존 `../results/GoodsHunt_assets.zip`의 audio/*.wav146개 경로/SHA는 literal_audio_evidence.json.audio에 있다. 호출 key와 AudioSystem 동적 카탈로그의 정확한 clip 선택/loop/pool/동시 재생 정책을 전수 복원했다는 뜻은 아니다. 설정 SoundData#140의 빈 list/preload4개만으로 이벤트 전체가 없다고 단정하지 않는다.
