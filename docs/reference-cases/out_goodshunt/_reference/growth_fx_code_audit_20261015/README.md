# Growth and eating FX code evidence

Original AArch64 static code readings. Selected method disassembly and code SHA are in this directory; declaration boundaries are not independently measured symbol sizes and generic annotations can alias. No game execution, implementation edit or rendering-parity test.

## Natural size increase versus Growth button

**Correction:** `OnPlayerLevelUpFx` method starts at **0x21E9044**, not0x21E8D90. The earlier address is inside `TryExpandHole`0x21E8AC4 and must not be used as a method entry.

- TryExpandHole directly calls OnPlayerLevelUpFx at0x21E8C2C.
- OnPlayerLevelUpFx handles a punch tween and at0x21E9154 loads **BoosterType.None=100**;0x21E9158 calls PlayerFxComponent.PlayerBoosterFx0x21E9EB0. Its switch100 reaches field+0x28 **levelUpFx -> PS1520 -> SetPlay**.
- **Growth=101** (dump TypeDef1117). GrowthButton.OnUseBooster0x1D1DC68 gets its virtual booster type, at0x1D1DD6C calls PlayerBoosterFx, then at0x1D1DDA0 calls BoosterManager.ActivatePowerUp. PlayerBoosterFx101 reaches field+0x38 **growthFx -> PS1510 -> SetPlay**. Do not trigger levelUp1520 just because the Growth button expands the hole.
- Switch source table0xE0CBBA raw bytes[0,4,8,12,15] from input100..104, base0x21E9F04; target100 field28/101 field38/102 field30/103 return/104 field20. `literals_and_switch.json` preserves bytes/addresses.
- GrowthPowerUp.OnActivate0x1CC60D8 sets power-up range/camera parameters and plays its SFX; OnDeactivate0x1CC6204 calls ResetPowerUpValue. These bodies do **not** directly call the GrowthLoop functions. Do not add an unproven loop call into them as original behavior.

## Common SetPlay / SetStop

- SetPlay0x21EC93C enables the PS GameObject at0x21ECA24, calls ParticleSystem.Play()0x21ECA3C, replaces its existing delayed cleanup handle, reads **main.duration**0x21ECB2C, and schedules `PrimeTween.Tween.Delay(duration, callback, useUnscaledTime=false)`0x21ECB74. Delayed callback0x21EDB74 sets GameObject inactive and removes the dictionary entry. A looping stored PS is still subject to this source cleanup policy; do not invent loop=false as a shortcut.
- SetStop0x21ECE88 invokes `Stop(withChildren=true, stopBehavior=0)` at0x21ECEFC. Unity enum0 is StopEmittingAndClear. It also completes/removes cleanup or disables the GO according to the stored dictionary path; not just an emission toggle.

## Loop APIs: confirmed versus unresolved runtime trigger

- PlayGrowthLoopFX0x21ECDD8 -> field+0x88 **PS1487** -> SetPlay.
- StopGrowthLoopFX0x21ECE30 -> field+0x88 -> SetStop.
- PlayGrowthLoopEndFX0x21ECFD0 -> field+0x90 **PS1578** -> SetPlay.
- PlayGrowthLoopTween0x21ED0D8 kills existing `_loopSequence` with complete=false, creates a new Sequence and inserts one callback at1.0, another at**9.600000381469727** (literal0xE0A804). The1.0 delegate MethodInfo target is **not independently resolved in this handoff**. The9.6 callback `<>c.<PlayGrowthLoopTween>b__33_0`0x21EDA84 explicitly calls StopGrowthLoopFX then PlayGrowthLoopEndFX.
- StopGrowthLoopTween0x21ED2B0 kills that Sequence with complete=false, then StopGrowthLoopFX, then SetStop on field+0x90 (end FX). It does **not** play the end FX on cancellation.
- `direct_callers.json` is a streaming exact immediate B/BL query to six FX addresses. It finds natural sizeup and GrowthButton/FreezeButton one-shot callers, but no immediate B/BL caller to PlayGrowthLoopTween/StopGrowthLoopTween/PlayGrowthLoopFX. This is **not proof of no delegate/serialized/indirect invocation or runtime reachability**. Upper event binding remains unknown; do not equate a defined method to an observed Growth boost event.

## Normal eating and goal/card effects

- LevelBehavior.OnPropEaten0x21D8664 is preserved fully. Goal path gets CardController.GetCard at0x21D8A44, then calls **OnEffect0x21D916C** at0x21D8A8C. Ordinary eating audio/counting is separate; this method does not contain a direct universal PlayerFx particle call in the read body. No generic fruit-eaten particle root was newly established.
- OnEffect gets the goal UID icon via CardController.GetIcon0x21D9254, spawns `_refManager`'s referenced `ItemSampleMoveTile` prefab through **GPoolManager.Spawn0x1D65C10** at0x21D929C, sets its icon, resets parameters, and calls **EffectEatObjectAnimator.AnimateTileToUI0x1ECBD88** at0x21D9390. This forwards to **ItemSampleMoveTile.AnimateToUI0x1ECBE20**. It is a pooled icon-fly UI effect, not an identified world fruit-burst ParticleSystem. Null target path invokes the callback directly. Exact prefab asset PPtr remains to be joined from the owning GameRefManager field+0x28; no name-only assignment here.
- CardController.ReduceCard0x1D2BD08 and the existing `end_flow_audit_20261015/disasm_01d2c380.txt` completion paths establish value/tick/tween/sound/callback flow. LevelBehavior.OnCardRemove0x21D9498 removes goal data then calls GameRefManager.OnGoalPropsRemoved0x1E3F594; it is **not itself a particle-spawn routine**.
- Particle roots for a separate card-removal burst remain unconfirmed. `ghostEaten` name alone does not establish ordinary prop eating. Keep visual convenience effects explicitly derived until a concrete caller/asset chain is established.

74 selected methods after adding the goal-fly callback audit, no extraction cap hit. No speculative replacement of missing original events is included. Further goal-fly ordering is in `../goal_fly_ui_audit_20261015/README.md`.
