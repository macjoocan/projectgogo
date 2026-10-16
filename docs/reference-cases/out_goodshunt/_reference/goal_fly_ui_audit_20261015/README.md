# Goal fly UI native reference and timeline

Original stored values / static code reading. Implementation is owned by the Goodhunt session. No source mutation or original execution. Numeric evidence is in `literal_values.json`; method disassembly/SHA remains in `../growth_fx_code_audit_20261015/` and existing `../end_flow_audit_20261015/`.

## Exact referenced prefab

`level2 GameRefManager#25745.ItemSampleMoveTile` stored PPtr **file2/path7141** resolves to **sharedassets2.assets ItemSampleMoveTile#7141**, GO2062 `/SampleMoveTile`, RectTransform5753. Root size150x150, stored scale1. Child `/SampleMoveTile/Icon`: GO2696, RectTransform4871, size105x105, stored scale(1,1,2). Component#7141.imgIcon -> local Image#6946.

`native_ui_chain.json` preserves both nodes' original GO/RectTransform/component fields, source keys/raw SHA and owning manager fields. Image6946 stores **null Sprite**, whiteRGBA. **No prefab Sprite PNG exists to export here.** Runtime OnEffect obtains the actual UID icon from CardController.GetIcon and calls SetIcon; do not name-match a default fruit PNG.

Bounds: one root/two nodes/zero sprite/zero errors verified; `verification.json` SHA. Sequential bounded extraction peak0.269GB/cap2.5GB.

## Parent, starting position and coordinates

OnEffect0x21D916C spawns the referenced prefab through GPoolManager, fills its icon, optionally reparents through the target's parent component chain, then ResetParams0x1ECD7EC. The optional reparent target type at generic lookup is not independently resolved here; preserve the source chain rather than claiming every canvas hierarchy is interchangeable.

ResetParams sets localScale=Vector3.zero; localRotation=Quaternion.identity; RectTransform anchorMin/anchorMax/pivot to static Center(0.5,0.5), anchoredPosition to static AnchorPos**(-60,0)** (cctor0x1ECDEB0/literal0xDB98F8). **It does not project the eaten prop's world position to the screen.** Consequently spawning the icon at the fruit's screen position is a derived choice unless a separate caller proves it.

AnimateToUI0x1ECBE20 reads RectTransform **world position** S and targetUI **world position** E after reset, stores callback and computes M=(E.x,(S.y+E.y)*0.5,S.z). It is not a two-dimensional anchored-position tween. Null self rect/target returns without invoking this method's callback; OnEffect's separate null-target path invokes its supplied callback directly.

## Source timeline (scaled time)

| Relative time from AnimateToUI | Action |
|---|---|
|0|DOKill(rect,false), rect.localScale=0, capture S/M/E and callback|
|0.2|PrimeTween.Delay<T> callback `<AnimateToUI>b__19_0`0x1ECE028 starts motion and visible-scale/alpha effects|
|0.2..0.8|DOPathPrimeWorld(S,M,E,duration0.60000002384,Ease4=PrimeTween.InOutSine)|
|0.2|set localScale=Vector3.one*0.25|
|0.2..0.6|Tween.Scale endValue0.94999998808,duration0.40000000596,Ease3=PrimeTween.OutSine|
|0.2..0.35|PlayEffect(0.15000000596): Image alpha reset0 then Tween.Alpha end1 over that duration; default ease settings are not newly decoded here|
|first scale completes +0.05|callback19_1 schedules19_3, then Scale end0.80000001192/duration0.15000000596/Ease4InOutSine|
|0.8 nominal|independent Delay0.60000002384 from the0.2 callback invokes19_2: GPoolManager.Despawn(tileGO), then supplied UnityAction, then callback=null|

The final callback is an independent scaled Delay, **not** attached as the path tween's OnComplete. Equal0.6 durations do not prove subframe ordering if the web scheduler differs. The chained scale nominally ends at the same time; do not round durations/reorder callbacks and call it bit-identical. No extra100% hold or final scale0 is present in this path.

Delegate binding is checked by ItemSampleMoveTile.<>c TypeDef307 static cache offsets:19_0+28,19_1+18,19_3+10,19_2+20. GenericInst mapping confirms0x26CE4C8=Tween.Delay<object>,0x26CE668=Tween.OnComplete<object>,0x26CC964=Tween.Custom<object> (not unrelated generic annotations).

## Path interpolation

DOPathPrimeWorld0x1ECDA3C stores exactly3 points and uses a scaled PrimeTween.Custom progress0->1 with the passed InOutSine ease. Update callback0x1ECDF80 evaluates0x1ECDC90 then calls Transform.set_position (world).

For input progress t in[0,1], the read Catmull-Rom algorithm is: u=(N-1)*t; i=min(floor(u),N-2); s=u-i; P0=points[max(i-1,0)],P1=points[i],P2=points[min(i+1,N-1)],P3=points[min(i+2,N-1)]. Return:

`0.5 * (2*P1 + (P2-P0)*s + (2*P0-5*P1+4*P2-P3)*s*s + (3*P1-P0-3*P2+P3)*s*s*s)`

This is **not** a quadratic Bezier through S/M/E. Native float operation order is preserved in ASM; this algebraic summary is not a float-bit parity fixture and does not introduce a new clamp for out-of-range t.

## Card quantity/removal/clear ordering

For the **OnEffect fly branch**, OnPropEaten0x21D8A8C supplies LevelBehavior.<>c__DisplayClass73_0.<OnPropEaten>b__0 (0x21DBC40). After the nominal0.8s fly callback, this executes **DoPunchCard0x21DBCC4**, then **ReduceCard0x21DBD94**. Do not decrement the same card immediately and then again on fly arrival.

There is also a separate direct ReduceCard branch at0x21D8D00. Do not impose0.8 seconds on every kind of goal event.

ReduceCard0x1D2BD08 decrements GoalCard.Qtity at0x1D2BEBC and updates quantity0x1D2BED0 immediately when called. Remaining>0 runs the reduced callback and returns. For quantity<=0, it removes the UID from CardController's dictionary and at0x1D2C0CC invokes the **onCardRemove** callback, then schedules OnRemoveCard0x1D2C114.

onCardRemove -> LevelBehavior.OnCardRemove0x21D9498 -> GameRefManager.OnGoalPropsRemoved0x1E3F594 can initiate clear immediately on last goal. **Clear is not universally gated by the subsequent card-removal animation completion**. The separate onCardRemoveAnimComplete callback is retained; existing FLOW.md documents processWinCondition+5A and the later0.3-second clear delay, Ending61 and result UI.

OnRemoveCard passes stored `animateCardDelay`+0x30 to ShowTick and schedules its next callback after that value+0.2 using DOVirtual.DelayedCall(ignoreTimeScale=true). Correction2026-10-15: an earlier version mislabeled this field as cardDoneScaleInTime; that field is actually+0x3C. Both stored values are0.2, so the number did not change. Flip and reflow callbacks have their own sequence. No single invented total card-animation duration is supplied here. Keep logical target completion, fly arrival, card removal animation and result popup as separate stages.

Further original UI pixel parity, optional reparent generic type, exact default alpha ease and all special goal-card branches remain unverified.
