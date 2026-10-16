# Prop placement root TRS recheck

Evidence: code_audit_20261014/disasm_021e1b60.txt and disasm_021e22e8.txt; dump.cs PropBehavior TypeDef4342, PropPlacement TypeDef4322.

## Ordinary Prop contract

Init0x21E1B60 receives x2=data, retained in x21. At0x21E1C08 the data reference is stored to this+0x28. Ordinary branch0x21E1C4C..60 calls data.get_Scale0x21BA1C8 and saves the returned Vector3 directly to this.originalScale+0x90/+94/+98. This is **not** multiplied by the prefab's existing localScale.

Init dispatch at0x21E1D04..08 uses virtual entry+0x198, corresponding to ResetTransform slot6 (same16-byte entry pattern/base0x138). Base ResetTransform0x21E22E8 then performs:

| Call site | Input | Target |
|---|---|---|
| 0x21E23BC Transform.set_position | this.Data+0x18/+1C/+20 (Position) | this.transform, world position |
| 0x21E23E4 Transform.set_eulerAngles | this.Data+0x24/+28/+2C (Rotation) | this.transform, world Euler angles |
| 0x21E242C Transform.set_localScale | this.originalScale+0x90/+94/+98 | this.transform, local scale |
| 0x21E25C4 Rigidbody.set_position | this.Data+0x18/+1C/+20 | this._rigidbody+0x30, world position |

All are direct setter inputs. There is no add-original-position, multiply-original-rotation or multiply-prefab-root-scale operation in these chains. Rotation is Euler-angle assignment, not set_rotation(Quaternion) directly; port quaternion conversion must reproduce Unity Euler semantics separately.

Therefore a geometry/collider builder must traverse **descendants relative to the PropBehavior root**, excluding that root's pre-placement stored TRS. Placement replaces that root transform. Keep all actual child localPosition/localRotation/localScale, including renderer offsets and collider sibling structure. Do not erase legitimate child transforms to repair a root-bake error.

The same placement position is explicitly sent to the referenced Rigidbody, so do not leave its physics origin at a separate baked prefab world offset. The native method writes world position/rotation and local scale; a nonidentity parent is not interchangeable with all-local setters.

## Scope boundary

The placement Scale source is the **get_Scale return**, not a new claim that every serialized zero/default scale passes through unchanged. SpecialPropPlacement has a separate Init branch at0x21E1DEC copying +0x3C (scaleSize) to originalScale, plus optional child VoxelMeshScale logic. Virtual ResetTransform overrides also exist. Do not promote the ordinary Milk candidate fix into an unqualified rewrite of all special subclasses.

Milk prefab root coordinates and active runtime subclass were reported by the implementation session, not re-extracted in this narrow audit. This proves the ordinary base Init/ResetTransform placement contract; the implementation still needs to check those selected assets' component identity and compare root-relative geometry/collider positions.
