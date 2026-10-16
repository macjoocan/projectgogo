# GoalCard / CardController 원문 판독 — UTF-8 정정본

Goods Hunt 1.9.1 ARM64 정적 판독. 실행 순서는 [원작 코드 판독], UI 저장 필드는 [원작값]이다. 원작 실행·화면 동일성 검증은 아니다. 원본은 `../ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so`, 선언은 `../code_audit_20261014/dump.cs`. declarations.json에 선택 83개 함수의 RVA/ELF offset/범위 SHA를 보존했다. capped 0. 함수 범위는 다음 선언까지이며 독립 심볼 크기 확정은 아니다.

## 추가 질문 답변

- OnRemove b__4의 카드 축소는 **지연 .1초 + duration .1초**가 맞다. `0x1D2D8CC`에서 s8=.10000000149, `1D2D8D0`에서 duration=s8, `1D2D8D4` DOScale. 이어 `1D2D930`에서 delay=s8, `1D2D934` SetDelay. OnComplete는 `1D2D968`. 명시 SetEase/SetUpdate는 없다.
- DoFlip의 앞면 전환 중간 callback은 **x=-현재 x**이며 abs(x)가 아니다. `1E03F80 fneg s0,s10` → `1E03F90 set_localScale` → `1E03FA0 ShowFront`. y/z 유지. 뒷면 분기는 x=-abs(x)다. 이 설명은 DoFlip callback의 scale 처리이며 ShowFront 함수 자체와 구분한다.
- 회전은 원문 목표와 RotateMode=0을 보존한다. quaternion.y>0이면 첫 Y=+90, 아니면 -90; 다음 Y=180. identity→-90→180의 웹 누적 각도·실제 최종 회전 방향은 이 자료만으로 확정하지 않는다.

## 잘못 붙은 자동 제네릭 주석

dump.cs GenericInst 대응: `26D0028=OnComplete<object>`(OnKill 아님), `26D0DBC=SetTarget<object>`(SetLoops 아님), `26D0EFC=SetUpdate<object>(bool independent)`. w1=1은 독립 업데이트다. Ease 1 Linear / 6 OutQuad / 27 OutBack. 자동 overload 주석으로 overshoot를 추가하지 않는다.

## ShowTick — 1E0332C

true: isTicking(+4A)/isShowTicking(+4C)=true → 기존 tickTween(+30) Kill(false) → quantity(+58) GO off / tick(+B0) GO on → tick.transform scale .5 즉시 → scale 1/duration, OutBack27. 두 tween target=card GO. OnComplete(1E03E08)에서 .1 독립 DelayedCall, target=card GO → 1E03EC8에서 isTicking=false.

false: 기존 isShowTicking이 true면 isPreviouslyShowTick(+4B)=true; isTicking/isShowTicking=false; tick GO off. quantity를 다시 켜는 코드는 이 분기에 없다. scale tween에는 명시 independent 설정이 없고 마지막 .1 delay만 독립 시간이다.

## SelfMoveToPos — 1E0355C

isMoving(+49)=true → 자기 transform.DOMove(world dest,moveDuration+E0,false) → OutQuad6 → SetTarget(card GO) → OnComplete → SetUpdate(true) → movingTween(+38) 저장. [원작값] duration=.30000001192. 기존 movingTween Kill은 이 본문에 없다.

완료 callback 1E03ED0: flip=true면 DoFlip(callback,true,1), 아니면 callback 즉시 호출. 이어 isMoving=false. 따라서 flip=true에서도 isMoving은 뒤집기 시작 직후 내려가고 공급 callback은 뒤집기 끝에 호출된다. MoveCardFromStack(1E03554)은 flip=false를 넘기며 MoveToPos(1E03744)는 인자를 전달한다.

## DoFlip — 1E03754

1. isFlipping(+48)=true; 기존 sequence(+40) Kill(false); 새 Sequence/SetTarget(card GO).
2. localRotation quaternion.y>0 ? 첫 Y=90 : -90.
3. halfDuration=backFlipTime × **.18000000715255737**. literal E0A330, 사용 1E03930..44. .5 상수가 아니다.
4. Append 자기 DOLocalRotate((0,sign90,0),halfDuration,RotateMode0), Linear1/target card GO.
5. 중간 callback 1E03F2C: needShowFont=true면 x=-x, ShowFront(difficulty+28), isPreviouslyShowTick이면 ShowTick(0,true). false면 x=-abs(x), ShowTick(1,false), ShowBack(difficulty). y/z 유지. **isFlipping=false는 이 중간에 쓴다.**
6. Append DOLocalRotate((0,180,0),같은 halfDuration,RotateMode0), Linear1/target card GO.
7. 최종 callback 1E0403C에서 공급 Action 호출. Sequence.SetUpdate(true).

backFlipTime=.5면 .09+.09≈.18초, 기본 인자1이면 약 .36초. Kill(false)는 완료가 아니므로 취소 때 OnComplete가 실행된다고 가정하지 않는다.

## OnRemoveCard — 1D2C380

보통의 nonnull 카드 경로:

1. _isCardAnimationActive(+B8)=true. ShowTick(animateCardDelay+30,true), 사운드 호출.
2. 독립 DelayedCall(animateCardDelay+.2,b__0), target controller GO. 저장 delay=.2이므로 명목 .4초.
3. b__0(1D2CF38): 카드 transform/원래 localScale 캐시, SetAsLastSibling → DoFlip(b__1,false,.5).
4. b__1(1D2D340) → DoFlip(b__2,true,.5).
5. b__2(1D2D3FC) → DoFlip(b__3,false,.5). 세 번 직렬, 각각 약 .18초.
6. b__3(1D2D4B8): 원래 scale×1.20000004768로 DOScale(.15000000596), Linear1, delay .1, target controller GO, OnComplete(b__4).
7. b__4(1D2D630): cardParticle/풀 유효 시 Spawn → FX GO off → .07500000298 독립 delay → b__5(1D2DA44)에서 GO on/카드 world position으로 이동. 여기 명시 PS.Play는 없다. FX 유무와 별도로 카드 DOScale(zero,.1), delay .1, target controller GO, OnComplete(b__6). 별도 .1 독립 delay로 b__54_7(1D2CDE0) 사운드 호출.
8. b__6(1D2DB20): FX/풀 유효 시 .5 독립 delay → b__8(1D2DD40)에서 FX Despawn. 별도로 독립 DelayedCall(0,b__9). target controller GO. 0 지연을 동기 호출로 바꾸지 않는다.
9. b__9(1D2D078): 그룹(+78)에서 카드 Remove → 공급 callback → 살아 있는 카드 GO SetActive(false). 이 지점은 Destroy/Despawn이 아니다. Remove 성공/그룹 남음이면 OnRearrangeCard. 그룹이 비고 대기 카드가 있으면 다음 그룹 인덱스·누적 수 갱신 후 AnimateCards(callback,false) 분기. 대기/그룹이 없으면 active flag를 내린다. 전체 분기는 해당 disasm 보존.

명시 independent인 delay/flip과, 명시 independent가 없는 scale tween이 섞인다. 전체를 unscaled로 합치지 않는다. +3C cardDoneScaleInTime=.2 / +40 cardDoneScaleOutTime=.1을 이 경로의 실제 상수 대신 임의 주입하지 않는다.

## OnRearrangeCard — 1D2C774

그룹 없거나 비면 active=false, 있으면 true. i마다 placeholder index=placeholderCards.Length-1-i, null 카드/음수·범위 밖 index/null placeholder는 건너뛰되 i는 진행한다. 목적지는 placeholder.position(world).

유효 카드 모두 같은 loop에서 MoveToPos(dest,callback,flip=false) 시작. **.12 stagger 없음.** 이동은 .3초 OutQuad/독립 업데이트. i==그룹.Count-1일 때만 callback을 붙이며 마지막 유효 카드로 재선정하지 않는다. callback 1D2CD0C는 active(+B8)=false 한 줄이다.

## 근거·한계

literal_values.json에 E0A330=.18/E0A4B0=1.2/E0A90C=.075/E0A1C4=.15/E0A44C=.1의 원본 4바이트·ELF offset을 보존했다. UI/Sprite 정본은 `../goal_card_ui_audit_20261015/`.

초기 AnimateCards coroutine도 선택 원문에는 있지만 이 문서는 제거/reflow를 우선 해석했다. 전역 DOTween 기본 ease/시간 설정, 프레임 양자화, 풀 자체 OnEnable/cleanup, 화면 동일성은 미확정이다. 논리 goal 완료와 전체 UI 연출 완료를 구분한다.
