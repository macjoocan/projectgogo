# Prop.Update Y coordinate recheck (2026-10-15)

Evidence: `../code_audit_20261014/disasm_021e14a4.txt` (Update RVA0x21E14A4, ELF offset0x21DD4A4), `dump.cs` TypeDef4342.

## Confirmed coordinate chains

- Start manual-drop check: 0x21E1648 `x0=[this+0x50]` = MeshRenderer; 0x21E1654 Component.get_transform; 0x21E1660 Transform.get_position; compare returned **s1=world Y** at0x21E166C against -2.3 literal. If below, tail-call EnableInHoleDrop0x21E1718. This uses the renderer transform position, not Renderer.bounds.center/min.
- Slow Eaten check: 0x21E15E8 `x0=this` -> Component.get_transform0x21E15F0 -> get_position0x21E15FC; threshold -15 at0x21E1600 -> common compare0x21E16E4.
- Big Eaten check: 0x21E16A4 `x0=this` -> get_transform0x21E16AC -> get_position0x21E16B8; threshold -10 at0x21E16BC -> common compare.
- Small Eaten check: 0x21E16C8 `x0=this` -> get_transform0x21E16D0 -> get_position0x21E16DC; threshold -4 at0x21E16E0 -> common compare.

Thus Eaten uses **PropBehavior's own GameObject Transform world position**, not meshRenderer+0x50, Rigidbody+0x30, or bounds. Calling it Rigidbody rootY is equivalent only if the port independently verified that body's origin is the PropBehavior transform origin; a centered physics body may not be interchangeable.

Common `fcmp s1,s0` at0x21E16E4; b.pl returns for >= threshold on finite inputs; otherwise virtual dispatch at0x21E1710. This is a strict below test for ordinary finite positions. Do not reinterpret NaN behavior as gameplay.

## Branch gates matter

At0x21E1504 `_isInHoleDrop+0x82` false branches to0x21E1608. That inactive manual-drop path only checks IsActive+0x48, !IsEaten+0x49 and rendererY gate; it does **not** unconditionally run the root Eaten thresholds.

When in-hole-drop is true, drop velocity advances min(v+30*deltaTime,80). Own transform moves down by that speed*deltaTime, **except** `_isBigPropObject+0xD0 && isTriggered+0xD2`, which skips the manual position move. It still reaches the subsequent Eaten checks.

Then CanFallSlow+0x4A selects -15, otherwise runtime bigObject+0xD0 selects -10, otherwise -4; all guard !IsEaten. Serialized `_isBigProp+0x81` is a different field.

## Milk report boundary

Root vs visual-child offset around2 units alone does not establish a new renderer-based Eaten rule: the two coordinates are deliberately different in the original code. No threshold/offset correction is justified from this recheck. Log actual PropBehavior transformY, renderer transformY, body-origin offset, inHoleDrop, bigObject/CanFallSlow/isTriggered and per-substep displacement to determine whether the port's body origin or callback ordering differs. Milk1..5 native transforms were not re-extracted in this narrow check.
