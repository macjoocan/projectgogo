# 대포 본·스킨·발사 클립 복원 — reply-to bmum6o91v-h

2026-09-29. C: 프로젝트 수정 없음. 본 3세트와 SkinnedMeshRenderer 6개, 발사 클립 3개를 복원용 JSON으로 정리했다. Unity 실제 재생 검증은 아직 하지 않았다.

## 자료와 근거

- `rigs.json`: [원작값] level2 Transform의 local TRS, 부모 PPtr, 렌더러 6개의 **순서가 있는** bones/rootBone/mesh/material 연결. path는 Animator 루트 기준 상대 경로다. Animator 루트 자체는 path="".
- `clips_decoded.json`: [원작 저장 데이터 디코딩] 3개 클립 각각 5개 본 × 위치3/회전4/스케일3 = 50개 scalar 채널. CRC 경로 전부 해결. 시간·값·다항식 계수를 보존하고 in/out tangent를 계산했다. 근거는 원본 animation_dependencies.json, 형식 대조는 [AssetStudio AnimationClip.cs](https://github.com/Perfare/AssetStudio/blob/master/AssetStudio/Classes/AnimationClip.cs)의 StreamedClip/FindBinding이다.
- `validation.json`: 스트림 1716/5084/1860 bytes 완전 소비, 경로 누락 없음, 150개 채널 모두 키 있음. 저장 샘플레이트와 시간을 사용하고 30fps로 일괄 변환하지 않는다.
- 재현 스크립트: 상위 `decode_cannon_animation_20260929.py`.

| 클립 | 루트 | streamed / constant | 키 수 |
|---|---|---:|---:|
| sharedassets2#22 Take 001 | Cannon_Hit | 9 / 41 | 154 |
| sharedassets2#20 Hit | Big_Cannon_Hit | 26 / 24 | 267 |
| sharedassets2#21 Hit | Infinity_Cannon_Hit | 9 / 41 | 160 |

모두 길이 0.3333333433초. `m_MuscleClip`이라는 이름이지만 이 자료의 바인딩은 Transform이다. Humanoid 근육 이름으로 바꾸지 않는다. sentinel -FLT_MAX/+Infinity는 애니메이션 키로 넣지 않았다.

## 연결 순서

1. 기존 cannon_anchor 및 그 상위 조준/배치 TRS를 유지하고, 각 Animator 루트 아래 rigs.json의 원본 TRS를 만든다. 저장 단위가 커 보여도 100분의 1로 임의 조정하지 않는다.
2. 정적 MeshRenderer를 같은 메시를 사용하는 SkinnedMeshRenderer로 교체한다. 원본 `m_Bones` 순서를 따른다. **Big_Cannon_Hit 바퀴는 R_Whell → L_Whell**, 일반/무한은 L_Whell → R_Whell이다. 이름순 정렬 금지.
3. 메시 원본은 `../cannon_ball_vfx_20260929/assets/meshes_native.json`. native vertices/bindposes/bone_indices/bone_weights를 쓴다. 축 반전, 재중심화, scale bake 없음. bindpose는 원본 행렬을 그대로 넣고 현재 Transform로 재생성하지 않는다.
4. clips_decoded.json의 path/property로 에디터 `AnimationUtility.SetEditorCurve`를 사용한다. `m_LocalRotation.x/y/z/w`는 쿼터니언이고 Euler가 아니다. WeightedMode.None; 자동 smooth tangent로 덮지 않는다. `incoming_step=true`인 키는 in tangent를 +Infinity로 설정한다. JSON에 Infinity를 직접 저장하지 않기 위한 별도 플래그다. 계수 coeff는 검산용이다.
5. 기존 컨트롤러의 해당 motion에 생성한 비-Legacy 클립을 연결한다. loop 값은 JSON의 원작 값 사용. 시작 상태와 Fire 전이는 기존 판독대로 유지한다.
6. 단발, 연속 발사, Big/Infinite 전환, 애니메이션 끝 복귀를 실제 플레이로 확인한다. 특히 무한 발사 cooldown .2초는 클립 길이 .333초보다 짧다. 컨트롤러의 self-transition/interruption을 임의로 바꾸지 말고 저장 전이값과 대조한다.

## 바퀴 메시 가중치 주의 — 미확정 부분 분리

몸체 메시 #17/#13/#16에는 정점별 weights와 indices가 모두 있다. 바퀴 #15/#18/#14는 원본 VertexData에서 BlendWeight(channel12) dimension=0, BlendIndices(channel13) dimension=1이고 m_Skin 없음, m_VariableBoneCountWeights.m_Data=[]다. **추출 JSON에 bone_weights가 없는 것은 원본 채널 자체가 없는 것**이다.

바퀴를 rigid single-bone으로 재구성해 각 정점의 저장 index에 weight=1을 주는 것은 합리적인 복원 후보이나 이번 자료에서는 Unity 원본 로더의 암묵 가중치 처리까지 검증하지 않았다. [자체 복원/검증 필요]로 두고, 원본 BoneNameHashes·바퀴 위치 및 BakeMesh 결과로 검증 후 확정한다. 원본 저장 weight=1이라고 기록하지 않는다. 0 가중치를 넣으면 메시가 사라질 수 있다.

## 완료 판정

본/바인딩/원본 커브 데이터 확보는 완료. Unity에서 클립 재생, 바퀴 단일 가중치 복원, bounds 및 스킨 변형 검증은 미완료다. 컨트롤러가 경고 없이 반응하는 것만으로 대포 애니메이션 완료로 묶지 않는다. 아이템 구현은 계속 진행해도 된다.
