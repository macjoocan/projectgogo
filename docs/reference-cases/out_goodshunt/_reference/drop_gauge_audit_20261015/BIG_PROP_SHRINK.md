# Level_006 큰 과일 정지: 원작 축소·낙하 근거

## 조사 범위
상대 요청 bmv8vkvh2-7: Kiwano index0/cost5, Mango_Red index311/cost4, Starfruit index312/cost5, placement.scale0.8은 **상대 세션의 관찰/매핑 보고**. 이 문서는 세 에셋의 collider 수치를 새로 추출하거나 실제 스폰을 독립 실행하지 않았다. 구현 importer/shape 검증은 상대 소유.

## 일반 Shrink() — 0x21E279C
meshRenderer가 UnityObject존재 판정을 통과하면 cachedBoundsSize(+A8,AC,B0)를 사용한다.
```
if cachedBoundsSize.sqrMagnitude < float32(9.999999439624929e-11): return
M=max(cachedBoundsSize.x,cachedBoundsSize.y,cachedBoundsSize.z)
transform.localScale=Vector3.one * float32(0.8999999761581421)/M
```
0x21E2800..2864/2868..2960. literal RVA0xE0A448=6666663f. **현재scale 또는 placement.scale을 곱한 값이 아니라 절대 localScale 대입**. cachedBounds는 Init에서 렌더바운즈 extents*2로 캐시한 값이라는 기존 판독과 연결한다. 가장 긴 축은 X/Z 한정이 아니라 XYZ 전체. 이 함수를 '홀반경보다크면0.9배축소'로 해석하면 틀리다.
renderer없음 경로0x21E28F8..2944는 Vector3.zero를 localScale로 쓰는 원문이다. 정상 에셋에 임의 renderer없는 경로를 만들지 말 것. 함수명 Shrink만으로 큰 물체의 일반 수집에 자동 호출된다고 확정하지 않는다. 반환값/원작분기를 임의 보정하지 않았다.

## ShrinkForMagnet(scaleFactor, lowFrictionMaterial) — 0x21E32F8
isShrunk(+A4) 또는 IsEaten(+49)이면 반환.
DOScale(one*scaleFactor, time float32(0.30000001192092896), delay0/unscaledfalse/updateMethod0).
rb.mass=originalMass(+9C)*10, rb.drag=0.
normal colliders(+40)가 있고 lowFrictionMaterial이 nonnull이면 각 nonnull collider.material=그재질.
isShrunk=true. simpleColliders(+78)를 이 루프가 수정하는 것은 아니다.
현재scale*factor나 originalScale*factor가 아니다. 추가 SetEase가 이 함수에는 없으므로 tween 기본 easing까지 여기서 확정하지 않았다. literal RVA0xE0A9D0=9a99993e.

## ResetScale() — 0x21E35D8
!isShrunk 또는 Eaten이면 반환.
DOScale(originalScale(+90..98),time0.3,delay0/unscaledfalse/updateMethod0).
**rb.isKinematic==false일때만** velocity/angularVelocity=0, mass=originalMass, drag=originalDrag(+A0) 복원. isKinematic을 여기서 true/false로 바꾸지 않는다.
normal collider.material=null(0x21E37F4..3800), isShrunk=false. 저장재질 PPtr를 다시 대입하는 코드와 구분.
ScalingProp(scaleValue)0x21E326C는 root scale=one*scaleValue 단순 대입. ResetInHoleDrop0x21E1B48은 flag82=false/velocity84=0만. 요청한 이름 ResetShrink는 해당 PropBehavior 선언에서 발견하지 못했고 정본 함수명은 ResetScale이다.

## 큰 물체 낙하 state와 일반 경로의 차이
PropBehavior.Init(+D0)=cost>3 OR prefab _isBigProp(+81); CanFallSlow(+4A)와 별개.
EnableInHoleDrop: !inHoleDrop ->flagtrue; big이면 반환. 따라서 **큰 물체는 일반 과일처럼 rb.isKinematic=true/콜라이더일괄false로 전환하지 않는다**.
Update: inHoleDrop인 동안 재차 EnableInHoleDrop를 부르는 루프가 아니다. velocity84는30dt/max80 갱신하지만 big && isTriggered(+D2)이면 Transform.down 수동이동을 건너뛴다. 원작은 이 상태에서 활성 Rigidbody의 중력/실제 충돌로 낙하할 수 있어야 한다. '큰 물체라 수동 이동 skip'과 '웹에서 모든 낙하 body를 KINEMATIC 처리'를 함께 구현하면 정지가 생길 수 있다. 이는 **구현 대조용 후보**이며 현재 웹 버그의 원인 확정은 아니다.
ActivatePropImmediate0x21E2B98는 rb.isKinematic=false/interpolation1/WakeUp; 재질/Shape/ground adapter와 별도로 확인할 것.
isTriggered write는 확인된 base 메서드에서 layer7 Enter(true), 조건부 Exit(false). 이미 Active일 때의 Exit를 무조건 false로 바꾸는 원문 근거는 없다. 각세션 소유 관측값 D0/D2/82를 먼저 확인하고, flag를 임의로 끄거나 자동Shrink로 강제먹음 처리하지 않는다.

## 호출자와 미결
.text 전체 direct BL scan 대상 Shrink/ShrinkForMagnet/ResetScale/SetCanFallSlow 모두0. big_prop_call_scan.json에 주소/상수/결과 보존. inline/indirect/delegate/실제 호출을 배제한 검사가 아니므로 'unused' 확정 아님. 원작의 일반 수집 조건에서 언제 축소해야 하는지 **아직 미확정**. native tangent 보정이나 큰 물체 전용 재진입 함수도 이번 근거에서 확인하지 않았다.
Magnet 전용 함수를 일반홀의 모든 big에 적용할 근거는 현재 없다. 적용 여부는 별도 상위调用 판독 후 판단.

## 권장 재현 로그 (웹 구현 세션 소유)
세UID와 hole 현재radius/원본compound TRS, rootY/rendererY, actual Rigidbody.type/mass/collisionResponse/sleepState/velocity.y, flags big/CanFallSlow/isTriggered/inHoleDrop, ground-contact 필터 및 실제 제외된 shape pair 기록.
'중앙에있다'와 '콜라이더가 실제 구멍을 통과한다'를 구분. Native collider와 placement0.8/부모scale/mesh scale을 혼동하지 않는다. 원본 PhysX와 convex-prism 접촉의 동등성은 미검증.
