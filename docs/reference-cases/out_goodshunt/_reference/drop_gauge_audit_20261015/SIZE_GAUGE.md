# 원작 Size 게이지 시각 및 업데이트 경로 — 2026-10-15

## 저장 UI 체인
size_gauge_native_chain.json 43records(raw SHA 포함).
sharedassets3.assets PlayerComponent#1893 -> energyFill AlternativeLinearProgressBar#1870 -> rectProgressBar RT1814, Mask1894/RT1804, Border Image1864, BG1876, Fill Image1902/RT1815.
canvasProgressRT1817 ProgressBarAnchor -> Border RT1809 -> Canvas RT1801 / Canvas#1789(mode2=world space) -> Component957 -> FirstSkin705. 독립 screen HUD가 아니라 플레이어/바구니 부모와 함께 움직이는 월드 UI다.
PlayerComponent txtHoleSizeBitMap#1877/GO306 TxtSize_BitMap와 fill은 별도 컴포넌트. Bitmap font#1840/spacing-2/alignment4. 바구니의 모델 텍스처를 바꾸어 progress를 표현하는 구조도 아니다.
Bar RT1814 size(15.68999958,4), anchoredPos(0,4), localZ1.4, q(0.9659258127,0,0,0.2588191032). 전체 부모 TRS는 JSON 그대로.
Fill Image1902: m_Type1=Sliced, m_FillAmount1 저장. **filled Image.fillAmount 업데이트가 아님**. Sprite local#147 HEA_Progress_Booster_9_sliced, rect427x94, border(45,0,45,0), PPU200; fill RT1815 anchors left/middle, pivot(0,0.5), anchoredX=-2.130000114, initial width2.130000114/height4.
Mask RT1804은 bar stretch, sizeDelta0, localScale~0.99. Mask.showGraphic=false. Bar min0/max1/current0/isWholeNumberfalse/IsAnimate=true 저장.

## 값에서 폭으로
AlternativeLinearProgressBar.Awake0x1ECCFB8:
minFillSize=-imgFill.anchoredPosition.x;
maxFillSize=rectMask.rect.width + minFillSize.
UpdateUI0x1ECD1EC:
percent=(currentValue-minValue)/(maxValue-minValue);
fill.sizeDelta.x=minFillSize+(maxFillSize-minFillSize)*percent; height 유지.
즉 이 저장 레이아웃에서 width≈2.13+15.69*percent, anchoredX=-2.13. Mask로 숨겨져 0%는 보이는 폭0이 된다. CSS 폭0..100%는 adapter지만 배경/테두리/마스크와 정렬이 맞아야 한다. 숫자 m_FillAmount1만 복사하면 늘 full로 보인다.
CurrentValue setter0x1ECD1D0 -> TriggerOnValueChange0x1ECD020: min/max clamp, 현재 wholeNumberfalse. IsAnimate면 elapsedTime=0, 아니면 UpdateUI. UnityEvent invoke; 저장 persistentCalls는 empty.
IsAnimate Update0x1ECD2A8: **현재 이미지 폭에서 목표 폭으로** Lerp(t=clamp01(elapsed/0.349999994)); 이 호출 이후 elapsed+=deltaTime, clamp0..10. literal RVA0xE0A290 bytes3333b33e. 고정 시작 폭으로 한 번만 보간하는 duration tween과 다르며 Script Update 순서 전체 원작 frame대조는 아직 미검증.

## 성장 -> energy target
PlayerBehavior.TryExpandHole0x21E8AC4: 수집점수/성장 차감 규칙은 기존 SCORE_GROWTH_CALLBACK.md 사용. collectedCost/expandCost를 PlayerComponent.Energy로 전달. threshold미만도 ratio전달; level-up후 잔여cost를 다음cost로 나눈 ratio를 **같은 동기 호출 안에서** 전달(0x21E8F98..8FCC). 다음 stage없으면 IsEnergyActive=false -> bar GameObject.SetActive(false)(0x21E7E40), size text와 별도.
PlayerComponent.set_Energy0x21E8054: 새 값이 이전 target보다 작으면 energyFill.SetValueNoAnim(newValue) 먼저 호출. 이후 target=newValue, animating=true.
PlayerComponent.Update0x21EBF60: energyFill.CurrentValue를 target쪽으로 **MoveTowards(maxDelta=15*deltaTime)**한 뒤 setter. 프레임마다 lerp15%가 아니다. Mathf.Approximately 수준의 종료조건은 해당 disasm에 보존.
내려갈때 SetValueNoAnim0x1ECD284는 IsAnimatefalse ->currentValue=value ->UpdateUI즉시 ->IsAnimatetrue. 따라서 이 경로에서 강제100%hold를 근거로 확인하지 못했다. TryExpandHole/OnPlayerLevelUpFx에는 같은 호출 말미의 잔여ratio 전달을 기다리는 100%hold 계약을 발견하지 않았다. 원작값이라고 주장하지 말고 별도 시각 보정이라 표시하거나 원문 경로로 교체한다.

## Size label/scale
OnRadiusChanged0x21EC084 -> bitmap SetText: literal 'Size {0}'(0x4196DB0), arg=nextEnergyStage. canExpandfalse면 literal 'Max'(0x41844E8). ui_text_literals.json는 원본 metadata stringliteral index/offset 근거.
AdjustProgressBarSize(nextEnergyStage-1)0x21EC294: canvasProgressRT.localScale=one*GetProgressBarSize(level). HoleSizeUpgrade#1833 progressBarScaleValue의 **0-based index** 배열은 1.25,1.100000024,1,0.850000024,0.824999988,0.800000012,0.785000026,0.769999981,0.75999999,0.75999999,0.75999999,0.75. Initialise0x21F3320에서 index->value dict 구성. 범위밖 GetProgressBarSize fallback1을 전달하는 호출 패턴은 원문 disasm에 보존(sharedgeneric 선언 alias를 실제 고수준 이름으로 단정하지 않음).

## 추출/미결
original data.unity3d 읽기전용. native MonoBehaviour header만 있는 TypeTree는 이전 structured JSON을 **현재 raw SHA가 일치한 경우에만** 재사용; decode_mode/native_typetree_error 보존. 첫 시도 TypeTree size오류, 두번째 rawbytes JSON직렬화오류, 세번째 완료를 guard receipts에 각각 보존. v3 peakcommit0.334GB/exit0/43records. 선택 함수 ARM64disasm 생성, 게임/DLL 실행/원본 및 Goodhunt 구현 수정 없음.
실기 캡처 기존 play_capture_20261014/05 메뉴 초기 Size1 등 참고 가능. 이번에 프레임별 UI runtime 값이나 width를 원작에서 측정한 것은 아니다. 전체 UI Update 순서/활성화 재진입/최종 픽셀 동등성은 미확정.
