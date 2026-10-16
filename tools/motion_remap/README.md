# Levelscope Motion Remap 0.2

추출한 뼈대 모션을 다른 스킨 캐릭터의 뼈대로 옮기는 **독립 구현**입니다.
Auto-Rig Pro의 공개 Remap 설명에서 작업 흐름을 참고했으며, 해당 애드온의 코드·프리셋을
포함하거나 의존하지 않습니다. 동일 알고리즘·품질·완전한 대체를 주장하지 않습니다.

## 지원 범위

- Blender 5.x용 패널과 백그라운드 Python API. 실제 실행 검증 버전은 5.2.1 LTS입니다.
- 본 이름/네임스페이스의 보수적 자동 대응 초안, JSON 저장·재사용, 중복/미확인 본 거부.
- 복제한 타깃 뼈대와 스킨 메시에서 작업. 원본 rest/bind pose·스킨 가중치·메시를 수정하지 않습니다.
- 본별 소스 자세 참조 스냅샷(A/T 자세 보정), 타깃 로컬 회전 오프셋, 이동량 배수·위치 오프셋.
- 부모-자식 구간 길이 비율의 중앙값으로 이동 스케일 자동 산정. 수동 비율도 가능.
- 루트 이동·회전, 선택 축의 제자리 모션, 선택 본의 추가 로컬 이동과 스케일 트랙.
- 직접 연결된 upper/lower/end에 대한 무신장 2본 IK, 소스/고정 pole, 손끝·발끝 아래 자식 전파.
- 여러 Action과 Blender 5 Action Slot 처리, quaternion 부호 연속성, 소수 프레임 원본 키 보존.
- 복제본 `.blend`, 스킨·애니메이션 `.glb`, 검증용 `.json` 내보내기.
- 과대 작업 사전 bone-frame 제한, 예외 시 생성 데이터 회수, 소스 Action/Slot/NLA/시간/pose 복구.
- 접촉 높이·속도·지속시간 기반 발 접지 구간 추정과 수동 구간, 전환 블렌드, 발 위치·회전 잠금.
- 월드 Z 평면/명시한 평가 메시 지면 raycast, 발 관통 방지·경사 정렬, 도달 범위 기반 골반 보정.
- 제한된 루트 궤적 필터, 루프 끝부분 이음 보정, 소스 곡선 중간점 기반 적응형 샘플링.
- 명시적 FK/IK/pole/커스텀 속성 프로필로 복제 컨트롤 리그 구동, 평가된 변형 본 오차 검사.
- 움직이는 소스 오브젝트 위치·회전·양의 균일 스케일을 루트 모션으로 합성하는 선택 옵션.
- 제약·B-Bone 평가 결과를 일반 스킨 뼈대로 bake하는 별도 경로. 매 샘플 원본 변형 정점과 대조.

## 사용 방법

1. `motion_remap` 폴더를 ZIP으로 묶어 Blender Preferences의 **Install from Disk**로 설치합니다.
   배포 ZIP은 해당 폴더가 루트 디렉터리인 애드온 ZIP입니다. 수동 등록도 가능합니다:

   ```python
   import sys
   sys.path.insert(0, r"D:/path/to/levelscope/tools")
   import motion_remap
   motion_remap.register()
   ```

2. Blender에서 원본 모션 뼈대와 타깃 스킨 캐릭터를 엽니다. FBX/BVH/GLB 입력은 먼저
   Blender 기본 임포터로 가져옵니다. 원본 파일을 덮어쓰지 말고 작업용 `.blend`를 만듭니다.
3. 3D View 사이드바 **Motion Remap**에서 Source/Target과 새 Preset JSON 경로를 지정합니다.
4. **Create mapping draft**를 누릅니다. JSON의 `bones`를 확인하고 `root`를 타깃 본 이름으로
   지정합니다. 이름 추정은 정답이 아니므로 팔·다리·좌우를 반드시 검토합니다.
   본 이름이 완전히 다른 리그는 직접 매핑합니다. JSON은 외부 편집기에서 저장하거나 Blender
   Text Editor에서 **Save**해야 디스크의 프리셋에 반영됩니다.
5. 필요하면 소스의 작업 자세를 타깃 기본 자세에 맞춘 뒤 **Capture source correction pose**로
   별도 `_reference.json`을 저장합니다. source_reference는 본의 armature-space 회전 참조입니다.
   소스 bind pose를 바꾸지 않지만, 임의 동작 중간 프레임을 넣으면 그 동작을 기준으로 삼으므로
   보정용 정지 자세에서 캡처합니다. 이동이 있는 자세의 위치까지 재정의하는 기능은 아닙니다.
6. JSON의 `approved`를 `true`로 바꾸고 저장합니다. `ik_chains`는 필요한 팔다리만 설정합니다.
7. Actions glob을 `Walk*` 등으로 좁힌 뒤 **Bake to copied target**를 누릅니다.
   출력 Collection/`Remap__...` Action/`MotionRemap_Report.json` Text를 확인합니다.
   Frame step은 추가 정규 샘플 간격이며 원본 키는 그 간격과 관계없이 보존합니다.
8. 접지/골반/지면 등은 `advanced_preset.json`의 `postprocess`를 본 이름·단위에 맞춰 설정합니다.
   원하는 접촉 구간을 알면 auto 추정보다 `contact.mode=manual`과 프레임 구간을 사용합니다.
9. 컨트롤 리그는 원본 Target을 그대로 두고 `target_mode=deform_proxy`로 먼저 기준 뼈대 모션을
   만듭니다. **Create control profile draft** → JSON 검토 → **Bake copied control rig** 순서로
   FK/IK 컨트롤·pole·IK/FK 속성을 연결합니다. `verify_bones`와 허용 오차는 필수입니다.
10. **Last output**와 새 출력 폴더를 지정하고 **Export last plain output**로 Blend/GLB를 저장합니다.
   컨트롤 리그나 분절 B-Bone의 최종 스킨이 필요하면 **Evaluated skin source**에 해당 리그를
   지정하고 해당 Action 이름으로 **Bake evaluated skin / B-Bones** 후 일반 뼈대 출력물을 내보냅니다.

### 백그라운드 실행

```powershell
& '<Blender>/blender.exe' --background --factory-startup --python-exit-code 1 `
  --python tools/motion_remap/batch.py -- `
  --input '<작업용.blend>' --source 'SourceRig' --target 'TargetRig' `
  --preset '<검토한.json>' --actions 'Walk*' --out 'out/motion_remap/run01'
```

새 출력 경로를 사용합니다. 기존 출력·입력 파일을 덮어쓰지 않습니다.
대형 모션 라이브러리는 여러 작업으로 나눠 실행하고 외부 프로세스 트리 메모리 감시를 붙입니다.
기본 `max_samples=200000`은 전체 본 수 × 샘플 수의 합 제한입니다. GLB 내보내기는 원본 소수
프레임 키를 유지하도록 강제 정수 샘플링을 끕니다. `.blend`에는 입력과 결과가 함께 들어 있고,
`.glb`에는 결과 리그와 해당 스킨 메시만 들어갑니다.

컨트롤 리그까지 생성해 Blend에 보관하려면 위 명령에 `--control-profile <검토한-profile.json>`을
추가합니다. GLB에는 기준 일반 뼈대를 선택해 내보내며, 컨트롤 리그는 Blend에 별도로 보관됩니다.
분절 본·제약의 최종 변형을 그대로 샘플링하려면 다음 별도 경로를 사용합니다(리타게팅 아님):

```powershell
& '<Blender>/blender.exe' --background --factory-startup --python-exit-code 1 `
  --python tools/motion_remap/batch.py -- --input '<컨트롤 모션.blend>' `
  --source 'ControlRig' --actions 'Controls__Walk*' --deform-export-only `
  --out 'out/motion_remap/deform01'
```

## 접지·골반·컨트롤 리그 설정

`advanced_preset.json`과 `control_profile_example.json`은 검토 전 예시이며 특정 Rigify 버전의
정본 프리셋이 아닙니다. 이름·IK/FK 값은 실제 리그에서 확인해야 합니다.

| 설정 | 동작과 단위 |
|---|---|
| target_mode=deform_proxy | 복제 기준 리그에서 제약/driver를 제거. 분절 본은 중간 기준 리그에서만 직선화 |
| object_motion=root | 소스 오브젝트 이동/회전/균일 스케일을 클립 첫 시점 기준 루트에 합성 |
| postprocess.feet[].contact | auto는 높이·속도·최소 지속시간/간격으로 추정. 속도는 월드 수치단위/초, 높이는 월드 단위 |
| contact.floor | 소스 발 head의 접촉 높이. 생략하면 클립 내 최소 높이로 추정 |
| contact.intervals | manual일 때 접촉 프레임 구간. 양 끝을 포함하며 겹침 불가 |
| contact.blend_frames | 접지/이탈 양 끝의 smoothstep 전환 폭. 확실한 고정 구간은 weight=1 |
| feet[].sole_offset | 지면에서 발 본 head까지 높이. 발바닥 꼭짓점이 아니라 본 head를 풀므로 실제 발바닥 기준값 필요 |
| feet[].lock_rotation | 접지 중 첫 회전 고정. 지면 정렬이 켜져 있으면 정렬이 후순위로 적용 |
| ground | objects가 비면 height 평면. 아니면 지정 Mesh만 raycast. 월드 Z-up |
| pelvis | max_shift는 월드 단위, 축 제한은 타깃 armature 축. 제한 안에서 두 발의 도달 범위를 반복 투영 |
| trajectory | root 이동을 tridiagonal 필터로 평활화. max_deviation은 타깃 armature 수치단위/축 |
| loop | 끝 blend_frames 동안 첫 자세로 접근. root 기본 제외, root=true는 루트도 이음 보정 |
| postprocess.strict | true이면 max_contact_error(기본 .005 월드 단위) 초과 시 실패·정리 |
| adaptive | 소스 월드 자세의 구간 중간점 오차로 세분화. position/scale tolerance, rotation(degrees), max_depth |
| adaptive.strict | 깊이 한도에서 허용 오차가 미충족이면 실패. false이면 unresolved_intervals 기록 |
| control profile | fk/ik control 대응, pole/기존 스위치 속성, verify_bones와 월드 위치/회전 허용 오차 필수 |

실제 처리 순서는 FK/IK 기준 bake → 루트 궤적 필터/루프 이음 → 접지 목표/지면 → 골반 평활화 →
도달 범위 재투영 → 발 IK/회전 → 스킨/오차 검사입니다. 평활화가 발 잠금을 풀지 않게 마지막에
도달 범위를 다시 적용합니다. 이동 한계로 목표가 불가능하면 `contact_satisfied=false`와 실제 오차를
남기고, strict 설정이면 결과를 성공 처리하지 않습니다.

바닥 높이·접촉 임계값은 사용자가 정하는 보정 설정이며 원작 게임 물리 값이 아닙니다.
특히 제자리 걷기는 발 head가 월드에서 계속 움직일 수 있으므로 자동 판독이 정확하지 않을 수 있습니다.
그때는 수동 구간을 지정합니다. 지면은 정적인 메시 기준이며 움직이는 받침의 로컬 접지 추적은 지원하지 않습니다.

### 분절 B-Bone / 평가 스킨 내보내기

`deform_export.bake_deform_export`는 분절 수 N의 본을 N+1개 일반 본과 인접 2본 가중치로 나누고,
Blender의 rest/pose segment matrix를 사용합니다. 매 프레임 원본 평가 스킨 정점과 결과를 대조해
위치 차이 .002 월드 단위 초과 시 실패합니다. 기본 최대5백만 vertex-frame/20만 bone-frame입니다.
일반 본의 제약 모션도 같은 경로로 굽습니다. 원본 메시·본·가중치는 수정하지 않습니다.
이 경로는 단일 Armature modifier의 선형 vertex-group 스키닝용입니다. Preserve Volume, envelope,
shape key, 추가 메시 modifier, 변하는 rest 형상, 표현 불가능한 shear는 조용히 버리지 않고 거부합니다.

## 프리셋 의미

`example_preset.json`은 설명용 이름입니다. 특정 게임/Mixamo/ARP와 검증된 프리셋이 아닙니다.

| 키 | 의미 |
|---|---|
| root | 이동을 복사할 타깃 본. hip/pelvis를 쓰면 pelvis 이동을 옮김 |
| scale_ratio | 월드 공간 이동 비율. auto는 대응 구간 길이 비율의 중앙값 |
| alignment_wxyz | 소스 월드 방향을 타깃 쪽으로 정렬할 quaternion. 기본 identity |
| in_place_axes | 타깃 armature 축에서 루트 이동을 **첫 샘플 위치**에 고정. 보통 Z-up은 X/Y |
| source_slot | 여러 슬롯이 있는 Action에서 소스 리그에 해당하는 정확한 slot.name_display |
| bones[].source_reference_wxyz | 소스 본 rest 회전 뒤에 적용하는 참조 자세 quaternion |
| bones[].rotation_offset_wxyz | 결과 본의 로컬 축에서 추가하는 quaternion |
| bones[].translation | 루트 이외 본의 추가 로컬 이동 복사. 기본 false, 얼굴 등 필요할 때만 |
| bones[].scale | 소스 pose scale 복사. 기본 true. 체형 길이 변경과 별개 |
| bones[].location_multiplier | 이동 복사 배수. 기본 1 |
| bones[].location_offset | 타깃 armature 공간의 추가 위치. 기본 0 |
| ik_chains[].upper/lower/end | 타깃의 직접 부모-자식 3본. end의 **head**를 손발 목표로 사용 |
| ik_chains[].pole_mode | source: 소스 관절 방향 / fixed: 타깃 armature 공간 pole 벡터 |

루트·팔다리·얼굴은 별도 정책으로 설정합니다. 매핑하지 않은 본은 부모에 종속된 기본 자세를 유지하고
보고서에 남깁니다. 2본 IK는 대응 팔다리의 소스 rest 대비 끝점 변화와 타깃 rest 끝점으로 목표를
만들며, 도달 범위를 벗어나면 길이를 늘리는 대신 clamp하고 횟수를 기록합니다.

## 현재 한계

- 자동으로 모든 Rigify/ARP/custom 리그의 의미를 판독하지 않습니다. 명시적 프로필을 검토해야 하며,
  IK/FK 속성·pole 방향·복잡한 역구동은 실제 평가 오차를 기준으로 통과/실패를 판단합니다.
  캐릭터 자동 리깅이나 새 컨트롤러 생성은 제공하지 않습니다.
- 접지 검출은 추정이며 임계값/수동 구간/발바닥 오프셋을 조절해야 합니다. 동적 물리 충돌이나
  미끄러짐의 보편적 해결을 보장하지 않습니다. 가동 범위를 벗어난 목표는 잔여 오차가 남을 수 있습니다.
- 반사/비균일 오브젝트 스케일/전단은 여전히 기본 리타게팅에서 거부합니다. 움직이는 양의 균일
  오브젝트 변환은 object_motion=root에서만 허용합니다.
- 본 회전은 armature 공간 rest-relative delta를 정렬해서 적용하는 자체 방식입니다.
  큰 체형 차이·꼬리·옷·머리·손가락은 추가 검토가 필요합니다. Euler 전환은 요구하지 않습니다.
- 본 크기/회전 결합으로 표현 불가능한 shear가 생기면 오차 검사를 통해 실패 처리합니다.
- 원본 키와 정규 샘플을 보존해도 모든 키 사이 연속 곡선의 완전 일치는 보장하지 않습니다.
  적응형 샘플도 소스 중간점 검사이며 최종 타깃 전체시간 오차의 엄밀한 상한 증명이 아닙니다.
  특수 보간/급격한 모션에는 더 촘촘한 샘플·최종 타깃 독립 오차 검사가 필요합니다.
- 여러 모듈형 부품의 bind pose가 다르면 각각 처리합니다. HatKid의 Body/Head/Legs를
  이름이 같다는 이유로 하나의 스킨 뼈대로 합치지 않습니다.
- FBX/GLB 익스포터는 별도 포맷 변환 단계입니다. 게임 런타임 IK/Notify/AnimTree/화면 동등성은
  이 도구가 검증한 사항이 아닙니다.

## 구현·검증 근거

- 기능 조사: [Auto-Rig Pro 공개 Remap 문서](https://www.lucky3d.fr/auto-rig-pro/doc/remap_doc.html).
  UI 개념 참고이며 내부 구현·코드·전용 프리셋은 가져오지 않았습니다.
- 구현 API: [Blender Bone.convert_local_to_pose](https://docs.blender.org/api/5.0/bpy.types.Bone.html),
  [Blender Action Slot](https://docs.blender.org/api/5.0/bpy.types.ActionSlot.html).
- `python -m unittest tests.test_motion_remap`은 Blender 없이 JSON 대응 정책을 검사합니다.
- `verify_blender.py`는 합성 뼈대의 identity/비율/자세 참조/IK/복구/저장 재열기를 검사합니다.
- `verify_hat.py`는 로컬 HatKid 추출본의 70본 Body/5동작에 대한 검증입니다.
  원본 게임 자산은 도구 ZIP·저장소에 포함하지 않습니다. 결과·실패 로그는 `out/motion_remap/`에 보관합니다.
- `verify_advanced.py`: 접지/골반/경사 지면/궤적/루프/적응형 키/이동 오브젝트/FK driver/실패 복구.
- `verify_adapters.py`: 실제 IK 컨트롤 제약 및 분절 B-Bone 스킨의 정점 대조와 GLB 출력.
- `verify_hat_contacts.py`: 추출한 실제 HatKid 다리와 검증용 80% 길이 타깃의 Idle 접지/골반/유한 스킨.
## GLB 시간키 검증 주의 — 2026-10-16

Blend의 소수 프레임 키 보존과 export된 GLB 시간키 보존은 별도입니다.
Multi의 후속 실험에서 `NLA_TRACKS + force_sampling=False`도 실제 24fps 재샘플이 확인됐습니다.
이 도구의 GLB 저장/클립 수/스킨 구조 검사만으로 원본 native 시간키가 정확히 보존된다고
판단하지 마세요. native localTRS 직접 출력 및 전체 float 대조는 Multi의 별도 구현이며,
현재 Motion Remap 내보내기에 통합·검증된 기능이 아닙니다. 웹 사용 전 실제 GLB 키와
브라우저 평가 자세를 별도로 비교해야 합니다.

