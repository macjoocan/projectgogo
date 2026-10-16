# Royal Smash 재질 복원 보강 자료

2026-09-29. 기존 자료에 더해 **43개 재질의 실제 Forward 후보 186개**에서 사용하는 속성과 텍스처를 대조했다. 원본 기능이 현재 구현에서 빠진 지점을 정리한 자료이며, C: Unity 프로젝트는 읽기만 했다. 사용자가 승인한 내부 재현 작업용 로컬 자료다.

먼저 `material_catalog.html`을 열면 재질·엔티티 이름으로 검색하면서 텍스처 샘플과 원본 사용값을 볼 수 있다. **텍스처 샘플은 완성된 3D 렌더 미리보기가 아니다.** 기계 입력은 `material_recipes.json` / `feature_values.json`, 기능 식은 `MaterialFeatureReference.hlsl`을 사용한다.

## 이번에 추가로 확인한 차이

| 복원 항목 | 대상 | 원본 동작 / 현재 조사 시점 차이 |
|---|---|---|
| 같은 이름의 다른 텍스처 | fan_mat, Pinata | 서로 다른 MatCap 원본 2개가 이름으로 합쳐졌다. 이 2재질에 다른 이미지가 연결됨을 픽셀로 확인 |
| MatCap 활성 분기 | IceSquare_Shader | 원본 MATCAP 꺼짐, 텍스처 null. 이식본은 무조건 곱해 direct diffuse가 없어질 수 있음 |
| MatCap 혼합 방식 | fan_mat, Cannon_material | 원본 `direct*(1+M)`, 이식본 `direct*M` |
| 기본 텍스처 대비 | BoxCylinder, Box_Square, Cannon_material | 원본 텍스처 RGB에 Contrast=.8의 거듭제곱 적용. 이식본 미구현 |
| 테두리 광택(Rim) | BigWood, IceSquare_Shader, TntCylinder, Can_Square 2객체, TntSquare | Omni 원본 RIM 6객체. Toony JamJar rim과 다른 식 |
| 위치별 광택 강도·폭 | IceSquare_Shader, M_CannonBall | SpecularTex의 R/Alpha로 강도와 Phong 지수 조절. 텍스처 연결만이 아니라 샘플 코드 필요 |
| 대포 음영 텍스처 | Cannon_material | LightmapTex를 별도 UV/ST로 읽어 direct에 곱함. 현재 속성/샘플링 없음 |
| 표면 요철 | Bouncer, StoneSquare, StoneCylinder | AG 포장 노멀맵 3장, 원본은 alpha=X, green=Y. 현재 셰이더에 입력 없음 |
| 앞·뒷면 표시 | 23재질 | 원본 Cull이 재질별로 다른데 Omni Back / Toony Off로 고정됨 |

겹치는 항목이 있으므로 위 건수를 합쳐 엔티티 수로 읽으면 안 된다. 정적 차이 목록에 걸린 재질 객체는 30/43이다. **이것이 30개가 모두 육안으로 틀렸거나 구현 전체의 정확도가 13/43이라는 뜻은 아니다.** 이식본은 Claude가 수정 중이므로 `target_gap_inventory.json`의 스냅샷 해시·시점을 기준으로 본다.

## 1. 이름 충돌: 원본 이미지는 다른데 한 파일로 합쳐짐

두 Texture2D 모두 이름이 `matcap0  (3)`, 크기가256×256이다. 이름·크기만으로 합치면 안 된다.

| 원본 asset_key | 올바른 재질 | 동봉 파일 |
|---|---|---|
| 98a9236bbda03f3469b1290a30a7d611#1 | fan_mat / Pinata | identity_textures/98a9236bbda03f3469b1290a30a7d611_1.png |
| 1126081b059fefc46ba0e1290d0bda21#1 | TntCylinder / Can_Square 2객체 / TntSquare | identity_textures/1126081b059fefc46ba0e1290d0bda21_1.png |

현재 `matcap0_3.png`의 decoded RGBA SHA256은 `da5134d86ef5a288f022b4c28b946e435137c80cbd0aa943a0bfe83119d5f7e4`로 두 번째와 일치한다. 첫 번째는 `8f3e8d9a8be8da1baf99c61119869d38c6dd971865e2df101bd383c4c32cec19`로 다르다. fan/Pinata의 실제 target 재질 참조도 같은 PNG로 이어진다.

`texture_identity_patch.json`에 정확한 사용 재질키/슬롯/원본·동봉PNG 경로/해시를 넣었다. **두 에셋을 다른 GUID로 반입하고 PPtr의 file#pathID로 연결**해야 한다. 기존 파일 하나를 덮어써서 여섯 재질을 같이 바꾸지 않는다. 기존 재질 동명3쌍을 분리한 원칙을 텍스처에도 적용한다.

## 2. Omni 기능 식과 합성 순서

아래는 [원작 코드 판독], 동봉 `source_programs/omnishade_*.glsl`이 근거다. 실제 runtime variant를 GPU 캡처한 것은 아니며, 저장 기능 키워드에 대응하는 후보의 식을 판독했다.

**기본 색:** entry204 lines561–565, entry193 lines567–571. BASE_CONTRAST이면 `A=pow(MainTex.rgb,Contrast)*Brightness*Color.rgb`; 아니면 `A=MainTex.rgb*Brightness*Color.rgb`. 대비는 `(x-.5)*c+.5`가 아니다. 텍스처 샘플의 색공간 변환 뒤 수행한다. 원본 pow는 `exp2(log2(x)*c)`이며 임의 epsilon을 넣지 않았다.

**대포 Lightmap:** entry193 lines560/588–593. `uvLM=rawUV0*LightmapTex_ST.xy+LightmapTex_ST.zw`. `LM=(sample.rgb*LightmapBrightness+max(1-LightmapBrightness,0))*LightmapColor.rgb`. direct에 LM을 곱한 다음 MatCap을 적용한다. 저장 brightness=.8. MainTex에 이미 변환한 UV를 다시 LM에 넣지 않는다. 이것은 작성된 음영 텍스처이고 Unity의 baked GI/lightmapIndex 경로가 아니다.

**MatCap:** entry193 lines596–602, fan entry196 lines605–608. M은 기존 식대로 가공한 MatCap sample×Color×Brightness다. `MATCAP`이 없으면 direct를 그대로 둔다. `_MATCAPBLEND_MULTIPLY`는 direct×M, `_MATCAPBLEND_MULTIPLY_LIGHTEN`은 direct×(1+M). lighten을 max(direct,direct×M)으로 바꾸면 다르다. 해당 lighten 활성 재질은 fan_mat/Cannon_material 2개이며, Ice에는 하위 blend 키워드가 남아 있어도 상위 MATCAP이 꺼져 있다.

**Specular map:** entry197 lines566–567/603–614, entry201 lines619–630. R×SpecularBrightness가 강도, `max(A×SpecularSmoothness,1)`이 Phong 지수다. 반사 벡터 기반 Phong 모델과 specular 색 선택 규칙은 기존 자료를 유지한다. **파일 이름 Ice_Roughness를 보고 GGX roughness의 R값으로 넣으면 틀린다.** 원본은 R/Alpha 두 채널을 위 방식으로 소비한다. non-map 경로의 Smoothness에 임의로 같은 clamp를 추가하지 않는다.

**Omni Rim:** entry199 lines585–595/639. `nv=max(dot(V,N),0)`, inverse=0이면 x=1−nv, 그 외 x=nv. `a=min(pow(x,RimContrast)*RimAmount,1)*RimColor.a`; `rimRGB=RimColor.rgb*a`. 이 항은 MatCap/direct/specular 이후, **전체 shadow-color 곱 이전**에 더한다. 그 뒤 emissive, ambient, 선택적 saturation 순서다. Toony JamJar처럼 광원별 ramp를 곱하는 식이 아니다. 원본 `_RimColor`는 HDR 속성이다.

| 재질 | Rim RGB (원본 저장) | Amount | Contrast | Inverse |
|---|---|---:|---:|---:|
| BigWood | .96226418, .34658065, .20879304 | .1 | 2.2 | 0 |
| IceSquare_Shader | 0, .08016753, 1 | 1 | 5 | 0 |
| TntCylinder / Can_Square 2객체 / TntSquare | 1,1,1 | .1 | 6.7 | 0 |

표는 읽기 좋게 반올림했다. 적용 시 `feature_values.json`의 원문 float를 사용한다. Can_Square 동명2개는 다른 자산으로 유지한다.

합성 순서: **기본색/대비 → direct lighting → 별도 Lightmap → MatCap → specular → Omni rim → shadow color → emissive → ambient → 해당 keyword의 saturation**. 새로운 효과를 마지막에 임의로 더하지 않는다.

## 3. Toony 노멀맵은 RGB가 아니라 AG

[원작값] Bouncer/StoneSquare/StoneCylinder 모두 BumpScale=1, Normal Texture color_space=0. PNG의 RGB는 대부분 같은 회색값이며 alpha가 별도로 변한다. 이것을 RGB XYZ로 해석하면 잘못된 법선이다.

[원작 코드 판독] entry62 lines400–411:

1. rawUV0에 **BumpMap 자체 ST** 적용.
2. x=sample.a×2−1, y=sample.g×2−1.
3. z=max(sqrt(1−min(x²+y²,1)),1e−16).
4. 그 다음 x/y에 BumpScale을 곱한다. z를 scale 뒤 다시 계산하지 않는다.
5. T*x+B*y+faceSignedNormal*z로 월드 법선 조립. 조사 원문에는 이 뒤의 재정규화가 없다.

T는 원본 tangent를 world 변환 후 정점에서 정규화한다. B=cross(Nvertex,Tvertex)×tangent.w×world determinant 부호. 현재 RsMeshImporter에는 RecalculateTangents가 있으므로 tangent 스트림을 셰이더에 전달할 수 있다. **현재 tangent가 원본과 수치적으로 동일하다는 검증은 별도**다. OBJ/압축 메시 재구성 경로에서 임의로 노멀 X나 UV를 다시 뒤집지 않는다.

Bouncer의 normal-map variant는 이 변형된 월드 법선을 view로 변환한 xy×.5+.5를 **fragment에서 MatCap UV로 사용**한다(entry62 lines412–416). 노멀맵 없는 Toony의 clip-depth 보정식을 그대로 적용하는 경로가 아니다. Stone 둘은 MatCap 자체가 비활성이다.

재현 경로: 원본 packed PNG를 Default RGBA / sRGB=false / alpha 보존 / alphaIsTransparency=false로 읽고 동봉 HLSL의 AG 해독을 적용한다. 일반 RGB normal-map 변환기로 다시 포장한 뒤 AG 해독을 중복 적용하지 않는다. 원본 PNG를 수정할 필요가 없다.

## 4. 텍스처 설정과 연결

`texture_import_contract.json`은 Forward 후보가 실제로 읽는 **고유63개**를 묶는다. 연결되지 않은 기본 텍스처(null)는 `material_recipes.json`에 별도로 보존했다. 63개 중 이름으로 찾은 target PNG 62개는 원본과 RGBA 픽셀이 같고, 한 개는 위 충돌 때문에 달랐다. 이는 PNG 파일 비교이며 **Unity 임포트 후 GPU 압축·샘플 값의 일치 검증은 아니다.**

- 60개 color_space=1, normal3개만0. 파일 이름이 mask/AO/roughness라고 무조건 Linear로 바꾸지 않는다. 이 원본의 Ice_Roughness와 Cannon AO 등은1이다.
- mip_count=1은61개. StoneSquare와 StoneCylinder normal만11개(1024→1)다. Bouncer normal은1개다. 이름이나 normal 여부만으로 mip 생성 여부를 통일하지 않는다.
- 설정표는 원본 filter/wrap/aniso/bias와 크기, scale/offset을 포함한다. 조사된63개 모두 bilinear1/aniso1/bias0/Repeat0이다.
- PNG는 기본 mip 이미지다. mip가11개인 두 에셋을 Unity에서 재생성한 경우 **원본의 각 압축 mip 바이트까지 동일하게 복원했다는 뜻은 아니다.** 정확한 저해상도 mip가 필요하면 원본 Texture2D 저장 데이터를 따로 유지해야 한다.
- 아직 미선언인 BumpMap/SpecularTex/LightmapTex는 기존 importer의 HasProperty 검사에서 건너뛴다. 셰이더에 속성·샘플링 코드를 추가한 뒤 importer를 재실행해야 실제 슬롯에 연결된다.

## 5. Cull / 깊이 / blend 원본 유지

[원작값+원작 코드 판독] Omni17개: Cull Off9 / Back8. Toony26개: Off12 / Back14. 현재 스냅샷의 Omni Back고정/Toony Off고정과 다른 재질이23개다. `_Cull`을 선언하고 `Cull [_Cull]`로 저장값을 사용한다. 원본 Main/ShadowCaster/DepthOnly/DepthNormals 모두 같은 속성을 참조한다. **Omni Outline만 Front 고정**이며 현재 요청 재질은 OUTLINE_PASS_DISABLED라 이 패스를 새로 켤 근거가 없다.

이43개는 저장 Blend One/Zero, ZWrite1, ZTestLEqual4다. 재질별 수치와 고정/속성참조 구분은 `original_all_pass_states.json`, 해석된 재질별값은 `material_recipes.json.render_state`에 있다. front/back 부호를 fragment에서 처리한다고 해서 Cull을 전부Off로 바꾸면 원본과 같아지지 않는다.

## 파일 구성 / 검증 범위

- `material_catalog.html`: 검색·셰이더 필터·원본 텍스처·사용값을 보는 로컬 문서.
- `material_recipes.json`:43개 파일키별 선언 type/flags, 저장값/원본기본값 구분, Forward 사용속성, 텍스처 PPtr+ST, 원본 노드·슬롯, 현재 차이.
- `feature_values.json`: 신규 기능의 활성 조건과 핵심값을 작게 분리.
- `texture_import_contract.json`, `texture_identity_patch.json`, `identity_textures/`: 텍스처63개 설정 및 이름충돌2장.
- `shader_property_contracts.json`, `original_all_pass_states.json`: 선언·렌더 상태 원문.
- `program_usage_index.json`, `source_programs/`:186개 후보의 실제 사용 행번호·해시와 추가 판독 GLSL.
- `MaterialFeatureReference.hlsl`: 복원용 함수 모음. 완성 shader나 엔진 실행 검증본은 아니다.
- `target_gap_inventory.json`, `target_snapshot/`: 조사 시점 코드의 비교 증거. 이후 Claude 파일에 덮어쓰지 않는다.
- `validation.json`: 정적 참조·별도 대수 검산7건. build_material_recovery_20260929.py와 make_material_catalog_20260929.py로 재생성 가능.

원본의 저장 REFLECTION/FRESNEL 하위 설정이나 Ramp 텍스처가 있어도, 조사한43재질의 대응 Forward 후보에서는 Reflection 속성·Ramp sampler를 읽지 않는다. **근거 없이 PBR reflection/metallic/roughness 효과를 추가하지 않는다.** 기존 HDR/MatCap/보조광 문제와 이번 재질별 기능을 하나씩 분리 적용하고, 동일 카메라·광원·메시에서 비교해야 기여도를 알 수 있다. 여기서는 Unity 빌드/실행이나 원작 실기 화면 동등성 검증을 하지 않았다.


## 추가 확보: 핵심 목록 밖의 보조 재질 8개

핵심 43개에 **보조 8개를 더해 총 51개 재질 객체**를 정리했다. 원본 프리팹의 추가 렌더러 슬롯 24개를 추적했고, 8개 모두 APK에서 다시 읽은 저장 트리가 기존 추출본과 일치했다. 핵심 43개의 Forward 186후보 분석 범위를 보조 8개 전체로 확대 해석하지 않는다.

| 재질 | 원본 셰이더 | 슬롯 수 | 연결 대상 / 주의점 |
|---|---|---:|---|
| Spiral_mat | OmniShade | 3 | Blocker L/M/S의 Pole. MATCAP 비활성 |
| fan_mat_02 | OmniShade | 3 | Fan 보조 슬롯. MatCap multiply-lighten, matcap4 |
| fan_mat_02 1 | OmniShade | 6 | Fan/PatchHole. multiply-lighten, 98a9236…#1 MatCap |
| M_BlobShadow | URP/Unlit | 2 | Table_Rect/Round의 Table_Pole/BlobShadow |
| lambert8 / lambert9 / lambert11 | URP/Lit | 9 | Blocker L/M/S의 Fan (1), 재질 3개 |
| WreckingBall_Rope | Toony | 1 | Pinata/Rope/TubeView. UseMatCap=0, UseSpecular=0 |

`auxiliary_materials.json`에 저장값·키워드·큐·ST·셰이더 선언·원본 해시를, `auxiliary_renderer_slots.json`에 노드 경로와 **원본 slot_index**를 넣었다. Blocker L과 M/S의 슬롯 순서가 다르므로 이름순 정렬로 다시 붙이면 안 된다. `auxiliary_textures/`의 고유 6장은 모두 원본 color_space=1, mip_count=1이다. 기존 핵심 텍스처와 중복될 수 있으므로 63+6을 전체 고유 개수로 표시하지 않는다.

**M_BlobShadow [원작값]:** custom renderQueue=2999, Surface=1, SrcBlend=5, DstBlend=10, ZWrite=0, Cull=2. BaseColor=(0.0699998811, 0.0699998811, 0.0699998811, 0.7921568751). BaseMap은 `5440275c10bb24403ab611e632aed01d#1`의 softcenter다. SG_Ground와 별개의 투명 Unlit 재질이다. 이 값은 저장 상태이며 해당 셰이더의 전체 컴파일 pass를 재판독했다는 뜻은 아니다.

**lambert 3개 [원작값]:** Metallic=0, Smoothness=0, Cull=2. 원본 BaseColor와 lambert11의 BaseMap을 보존한다. Toony/Omni 둘 중 하나로 강제 치환하지 않는다. 임포터는 **OmniShade / Toony / URP Lit / URP Unlit**을 명시적으로 구분해야 한다. URP 버전 간 최종 화면 동등성은 적용 후 확인한다.

보조 fan_mat_02 1도 이름 충돌 첫 번째 MatCap(98a9236…#1)을 쓴다. `texture_identity_patch.json`에 추가 사용처를 넣었으며, 이 보조 슬롯의 현재 Unity 배선은 별도로 검증하지 않았다. 핵심 두 재질에서 확인한 오배선과 구분한다.

보조 Omni 3개는 기존 컴파일 후보 정보를 동봉했다. WreckingBall_Rope와 URP Lit/Unlit의 정확한 실행 variant까지 검증한 것은 아니다. 저장된 하위 키워드만 보고 꺼진 부모 기능을 켜지 않는다.

미리보기: `auxiliary_material_catalog.html`. `outside_current_material_scope.json`은 발견 당시의 범위 밖 24슬롯 기록이며, 지금은 위 보조 파일로 모두 해소했다. 미확보 목록으로 사용하지 않는다.
