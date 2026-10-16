# A Hat in Time — 캐릭터·모션 1차 추출 및 파서 보강

작성: 2026-10-16. 대상 설치: `D:/SteamLibrary/steamapps/common/HatinTime`. 게임 설치 파일은 변경하거나 실행하지 않았다. 내부 리서치용이며 원본 자산의 외부 배포를 전제로 하지 않는다.

## 먼저 열어볼 파일

`HatinTime_character_motion_first_pass.zip`은 이 `_reference` 폴더 안의 빠른 확인용 묶음이다. 모델 미리보기·검증·안내만 포함하며, 전체 raw 약 3.70GB와 원본 패키지 약 5.55GB는 압축본 밖의 해당 폴더에 별도로 있다.

- `preview/HatKid_five_motions.glb`: 주인공 몸체·머리·다리, 각 파트의 스킨 가중치와 70개 뼈, 원래 기본 자세, 아래 5개 모션이 함께 있다.
- `preview/HatKid_five_motions.blend`: 같은 자료의 Blender 5.2 원본 작업 파일. 기본 자세로 열린다.
- `preview/select_motion.py`: Blender Text Editor에서 열어 ACTION 이름을 고른 뒤 실행하면 세 파트의 action slot을 함께 연결한다. 이후 타임라인을 재생한다.
- `preview_catlady/CatLady_scale_motion.glb` 및 `.blend`: **실제 비단위 스케일 모션 지원 검증용 추가 예제**. 191개 뼈와 대사 중 스케일 트랙을 함께 담았다.

| 구분 | 실제 원본 모션 이름 | 주의 |
|---|---|---|
| 대기 | Idle | 원본 추출 프레임·정밀 타이밍 사용 |
| 걷기 | Walk | 원본 뼈 이름으로 조인 |
| 뛰기 | RunCycle | 원본 뼈 이름으로 조인 |
| 공격 | Puncha | 원본 이름 그대로 유지 |
| 피격 관련 연속 동작 후보 | HandHurt | action 이름 `Hit_Candidate__HandHurt`. 일반 피격 게임 이벤트와의 연결은 미확정 |

원본 `Hurt1`~`Hurt5`는 각각 **1프레임 피격 포즈**다. 이를 임의로 긴 모션으로 만들지 않았다. 이 포즈들도 전체 raw 자료에 포함했다. 연속 동작을 보기 위한 HandHurt와 원래 피격 포즈를 구분한다.

머리·몸체·다리는 뼈 이름이 같아도 일부 rest pose가 다르다. 하나의 bind pose로 억지 통합하지 않고 **3개 스킨/3개 armature**를 같은 액션의 슬롯으로 연결했다. GLB에는 5개 애니메이션이 세 파트를 함께 움직이도록 들어 있다. 재질은 중립 미리보기용이며 원작 셰이더·의상 표현의 재현을 주장하지 않는다. 표본 텍스처는 `pilot/Startup/Texture2D/`에 있다.

## 전체 추출 자료

- `raw/`: 패키지별 `.md5mesh`와 `.md5anim`. 모델에는 정점·삼각형·UV·뼈 계층·기본 자세·스킨 가중치가 있고 모션에는 프레임별 위치·회전이 있다.
- 각 모션 옆 `.source.json`: 새 파서가 보존한 원본 export index, 프레임 수/길이/RateScale, 스케일 압축 형식과 오프셋, raw scale 키, rotation-only/이동 뼈 정책, additive 여부.
- `.compressed.bin`: 원래 애니메이션 압축 바이트 스트림. MD5로 표현할 수 없는 값을 다시 판독할 수 있도록 보존했다.
- `.scale.json`: 압축 바이트에서 별도 복원한 **뼈별 스케일 키와 실제 키 시간**. MD5 자체의 기능으로 오해하지 않는다.
- `recovered_collisions/`: 동명 `hat_kid_hat` 모델 2개와 `vault_ticket_Anims` 세트 2개를 export index별로 다시 분리한 자료. 이름만으로 덮어쓰던 누락을 보완했다.
- `source_packages/`: 모션·스킨 관련 원본 패키지의 바이트 동일 사본. 미해독 Notifies/CurveData 등도 원본 패키지에 남겨 두며, `source_package_manifest.json`으로 해시 대조한다. 이를 해당 속성의 의미 해독 완료로 세지 않는다.

### 집계 읽는 법

97개 패키지를 조사했다. 기본 추출 결과는 모델 파일 **680개**, 모션 파일 **3,054개**다. 바이트 해시 기준 중복을 제외하면 각각 **275개**, **1,295개**이며, 모션 이름은 1,028종이다. 이 수치는 고유 원작 캐릭터/고유 의미 동작 수가 아니다. 맵에 중복 저장된 자료가 있다.

원본 export table에는 SkeletalMesh 682개/AnimSequence 3,056개가 있다. 이 중 Engine.u의 각 1개는 `Default__` 클래스 기본 객체로 실제 스킨·모션과 구분했다. Startup의 동명 자산 충돌은 `recovered_collisions/`에서 분리 회수했다. 기본 raw 카탈로그 수치와 추가 회수 자료 수치를 단순 합산해 고유 자산 수로 쓰지 않는다.

`package_inventory.json`: 설치 원문 패키지·export index·직렬화 offset/size·선택 패키지 SHA. `motion_model_catalog.json`: 기본 raw 모델/모션의 뼈 이름·부모·프레임·파일 SHA. `duplicate_groups.json`: 동일 출력 바이트 그룹. `collision_recovery.json`: 추가 회수 index와 결과.

## 이번에 실제로 보강한 기능

1. UE3 UAnimSequence에서 누락되던 **ScaleCompressionFormat / CompressedScaleOffsets / bWasCompressedWithoutTranslations**를 실제 타입으로 읽도록 로컬 공개 파서를 수정·빌드했다. 경고만 숨기지 않았다.
2. raw scale 키·압축 원본·타이밍·이동 정책을 추가 출력했다.
3. 별도 디코더에 ACF_None/Identity와 constant/variable-time 키를 지원하고, 실제 발견된 **per-track Float96·Fixed48·IntervalFixed32**도 지원했다. uint8/uint16 시간, 오프셋 범위, 프레임 범위를 검사한다.
4. **3,054개 모션의 스케일 복원 오류 0**. 정확히 1이 아닌 키가 있는 파일 146개/트랙 3,421개다. 압축 오차에 따른 극소 차이도 포함하므로 전부 큰 시각 변화라고 보지 않는다.
5. Blender 변환기에 scale 채널과 이름 기반 뼈 연결을 추가했다. CatLady는 모델·모션의 뼈 순서가 달라도 이름으로 정확히 연결한다.
6. `index:<원본 export index>` 객체 선택을 추가해 동명 자산을 따로 회수할 수 있게 했다.

MD5 애니메이션 exporter는 원래 부모 계층을 알 수 없어 모든 비루트 parent를 0으로 쓴다. 소스 `ExportMd5.cpp`에 이 동작이 명시돼 있다. 따라서 **MD5anim의 가짜 parent0을 그대로 사용하지 않고, 이름이 일치하는 원본 mesh의 부모 계층을 사용**한다. 다른 캐릭터에 임의 리타기팅하지 않았다.

## 검증

- 기본 97개 목록/추출 오류 0. 확장 스케일 전수 처리 오류 0.
- 스케일 디코더 경계 fixture 7개 통과.
- 저장된 `.blend`를 다시 열어 원본 추출 트랙에서 독립 계산한 bone world matrix와 비교. 주인공 45개 표본, CatLady 3개 표본 검사 통과; 기준 최대 오차 .002 원본 단위. 실제 수치는 각 `validation.json`에 기록.
- 변형된 스킨 정점이 모두 finite인지 검사.
- GLB 실제 JSON 구조에서 주인공 스킨3/애니메이션5 및 scale 채널, CatLady 스킨1/스케일 모션1을 확인. 해시는 `glb_structure.json` 참조.
- 주요 추출·변환 프로세스는 2.5GB 메모리 가드를 적용했다. 기본 전수 추출 peak 약 .32GB, 확장 전수 약 .25GB, 미리보기 변환 약 .80GB였다. native 빌드는 기존 로컬 MSVC로 수행했다.

이는 **추출 데이터↔변환 파일의 검증**이다. 원작 실행 화면·게임 런타임의 IK/물리 머리카락/AnimTree 블렌딩/피격 이벤트·Notify 적용까지 같다는 뜻은 아니다.

## 도구·재현 경로

- 표본에 사용한 공개 Hat 전용 UE Viewer: `tools/umodel_hat/`.
- 수정 소스와 빌드된 파서: `tools/source/UEViewer-master/`. 원본은 `tools/UEViewer_source.zip`, 로컬 보강은 UnMesh3.h / ExportMd5.cpp / UmodelTool/Main.cpp 및 BuildTools의 MSVC 탐색 설정이다.
- `extract_all.py`, `enhance_all.py`, `decode_scale_tracks.py`, `test_scale_decoder.py`, `convert_hatkid_v2.py`, `convert_catlady.py`, `validate_hatkid.py`, `validate_catlady.py`.
- 재실행 로그/가드 receipt는 이 폴더에 보존했다. 실패한 이전 변환·빌드 로그도 숨기지 않았다. 현재 안내 파일만 최종본이다.

공개 소스·도구 근거: [UE Viewer 공식 설명](https://www.gildor.org/projects/umodel), [Hat 전용 포크 안내·모델/모션 호환 논의](https://www.gildor.org/smf/index.php?topic=6228.15), [사용한 공개 포크 소스](https://github.com/MrSoup678/UEViewer). 소스·바이너리 zip은 로컬 해시로도 식별한다.
