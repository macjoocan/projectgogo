# OnPropEaten fly versus direct card reduction

Static branch reading from `../growth_fx_code_audit_20261015/disasm_021d8664.txt`, same code as `code_audit_20261014/disasm_021d8664.txt`. No new extraction/implementation changes.

## Two gates

1. **Is this prop UID an outstanding goal?** At0x21D88D0 load `LevelBehavior._goalData+0x88`; read `prop.Prop.propUniqueID` at0x21D88E0 and perform dictionary key membership0x21D88E8; save bool to **w24**0x21D88EC. This is outstanding target UID membership, not every prop collected. Generic annotation misleadingly says `ContainsValue`; the caller's string-key argument and Dictionary<string,int> declaration establish key membership. Do not implement value membership on counts.
2. **Runtime special component type:**0x21D8904..892C checks the runtime object against the TypeInfo slot0x4175F88; the matching path at0x21D8C04 reads **+0xF4 PropType** (TriggerableProp's declaration/getter0x21E6428). Ordinary base PropBehavior lacks that field and falls through0x21D8930.

## Ordinary non-Triggerable prop

After scoring/floating text,0x21D8944 tests the goal-membership bool. False -> normal-eating branch0x21D8A94, **no card reduction**. True -> GetCard0x21D8A44 -> **OnEffect0x21D8A8C**, with the delayed callback0x21DBC40. Therefore ordinary current-goal props use the fly path. No size/cost/big/CanFallSlow/throttle distinction selects direct reduction here.

The100ms check at0x21D89D0..89DC only skips the optional goal SFX to0x21D8A18. It **does not skip OnEffect or switch to direct reduction**. Low frame rate or rapid collection is not a source reason to replace fly with direct.

## Triggerable runtime component

Matching runtime type jumps to0x21D8C04. If PropType+F4==Coin1, ShowFloatingTextForBonusCoin is called first0x21D8C20; **other PropType values also proceed to the same later goal test**. At0x21D8C30, goal-membership false jumps to the collected-price completion check, with no card reduction. True -> **DoPunchCard0x21D8C54** -> **ReduceCard0x21D8D00** immediately. Thus this direct branch is not limited to Coin1; Coin1 only adds bonus text.

Earlier runtime-type/coin-component flags at0x21D8828..885C and0x21D8BB0..8C00 select score tables and bonus flags. They must not be conflated with the later goal bool: w24 is reused at0x21D88EC. This note does not reclassify unknown subclasses from names alone.

## Implementation rule for the current ordinary-props web scope

For a source-backed ordinary PropBehavior whose UID is in the current outstanding goal set: OnEffect/fly -> delayed callback -> DoPunchCard/ReduceCard once. For a non-goal UID: no card reduction. Use direct reduction only when the original runtime special component/type branch has been established, not because a native renderer is disabled or an icon fails to resolve.

OnEffect's null target path invokes the supplied callback directly0x21D9398..93A8. That is a separate fallback after selecting OnEffect. It does not change the main classification above. AnimateToUI's own invalid-rect/target early return is yet another condition and does not itself invoke the callback.

Runtime TypeInfo slot exact decoded metadata binding was not separately exported anew in this note; the TriggerableProp identification is supported by the matching type-check branch, +F4 native field/getter layout and existing special-prop audit. Preserve actual component class/PPtr provenance rather than using UID/name heuristics.
