# 카메라 FOV · Ground · ColorBox 밝기 후속 판독

2026-09-29. 원본 저장값/코드와 현재 Unity 이식본을 비교했다. C: Unity 프로젝트는 수정하지 않았다. [원작값]은 직렬화 데이터, [원작 코드 판독]은 native/GLSL 분석, [자체]는 참고 구현·계산·이식본 비교다. 화면 일치나 런타임 적용 완료를 뜻하지 않는다.

## 최신 실행측 회신 — bmum06q51-v

**HDR 선언 차이로 GPU 값이 낮아지는 현상은 Claude 실행측 probe에서 재현됐다.** Unity6000.0.62f1 / Direct3D11 / Linear / 1×1 ARGBFloat RT. raw 저장값 (.60000002,.34117642,.23759998)에 대해 Plain Color GPU=(.318547,.095307,.046052), HDR Color/Vector GPU=원문 그대로. SetColor 주입에서도 같았다. CPU GetVector/GetColor는 모두 원문을 돌려주므로 CPU 읽기만으로 이 현상을 배제할 수 없다. 앞선 bmum024ii-t의 "GPU 검산에서 재현 안 됨" 보고는 실제로 CPU 조회였으며 실행측이 정정했다.

실행측은 원본 HDR flags와 MatCap/Specular 분기를 같은 빌드에 반영했다고 보고했다. ColorBox의 HDR 차이는 확인됐지만 전체 화면의 개선량, 각 수정의 기여도, 유일한 원인이라는 주장은 하지 않는다. 이 절의 실행 결과는 **Claude 측 보고**이며 Codex가 자체 GPU 실행한 결과가 아니다. Forward+ 실행 A/B와 원작 화면 정밀 대조는 여전히 미완료다.

실측을 반영한 주의: 공식 최신 SetColor 문구의 설명을 해당 6000.0.62f1 런타임 동작 대신 사용하지 않는다. 이 환경에서는 주입 API에 따른 CPU 저장 차이가 없고, 일반 Color와 HDR Color의 **GPU 전달 차이**가 측정됐다.

## ColorBox만 어두운 현상: 원본 HDR 선언 누락

사용자 최신 관찰은 **전체가 아니라 ColorBox 같은 일부 엔티티만 어둡다**는 것이다. 기존 Forward+ 가설을 단독 원인으로 확정하지 않는다.

- [원작값] ColorBox 9색 모두 Toony다. 7색은 TCP2_MATCAP 활성, Black/White는 비활성. Blue의 무마스크 Main 후보는 GLSL 46/58/70/82; Red는 45/57/69/81. 실제 실행 variant는 캡처하지 않았다.
- [원작값] Toony `_MatCapColor`와 `_SpecularColor`는 Color + flags 16(HDR). `_BaseColor`, `_SColor`, `_HColor`는 HDR가 아니다.
- [자체] 조사 시점 RS_Toony에서는 두 HDR 속성이 일반 Color로 선언돼 있다. **저장 숫자와 속성 의미를 모두 보존해야 한다.** Blue 정상/low 프리팹은 실제 MaterialsRS의 `bbb9901c33fba485793802873b5c71fb_1.mat`에 연결되어 있다.
- [자체] ColorBox 9종과 Wood/WoodBox/JamJar_Blue의 해당 저장 색상을 비교해 오차 1e-7 이내 일치했다. 숫자 누락이 아니라 색공간 전달 경로를 검사할 이유다. Blue MatCapColor=(0, 0.34117642, 0.6), JamJar_Blue=(1,1,1)이므로 같은 잘못된 변환도 재질별로 영향이 다를 수 있다.
- **확인됨:** 위 실행측 probe에서 일반 Color의 GPU 값이 sRGB→Linear로 낮아지고 HDR은 raw 그대로 전달된다. 전체 게임 화면에서의 기여도는 변경별 A/B가 필요하다.

Unity 6000.0 문서는 SetColor의 동작이 속성 HDR/Gamma와 프로젝트 색공간에 의존한다고 설명한다. 따라서 `[HDR]`만 붙이고 추출 원문을 기존 SetColor로 다시 넣으면 안전하다고 단정할 수 없다. [Material.SetColor](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Material.SetColor.html), [HDR property flag](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rendering.ShaderPropertyFlags.HDR.html).

`ColorPropertyProbe.shader` + `ColorPropertyProbe.cs`는 이를 분리 측정하는 진단 자료다. C#은 Editor 폴더, shader는 Assets에 반입하고 `RS/Audit/Probe color property transfer`를 실행한다. 기존 씬/재질을 저장·변경하지 않는다. 1×1 Linear ARGBFloat RT에 Plain Color / HDR Color / Vector control을 각각 출력한다. 첫 실행은 raw 저장값, 두 번째는 SetColor(raw) 주입이며, 속성 flags·GetVector/GetColor·GPU 픽셀을 JSON 로그로 남긴다. GPU가 필요하므로 `-nographics`로 실행하면 안 된다. **Codex 쪽 GPU 실행은 미수행**이다.

검증 및 후속 A/B 순서:
1. 완료(Claude 보고): 위 probe로 선언 차이와 주입 API 차이를 분리했다.
2. 원본 HDR flags와 raw 저장값 복구는 실행측이 반영했다. 동일 씬/카메라/광원에서 HDR만 바꾼 전후 픽셀 비교는 남아 있다. 밝기 배율로 보상하지 않는다.
3. 아래 MatCap 비활성 분기도 실행측이 복원했다. 이 변경만의 전후 영향은 별도로 비교한다.
4. 별도 변경으로 Forward/Forward+ 및 보조 방향광 on/off를 비교한다. 여러 원인을 한 번에 바꾸지 않는다.

### MatCap 분기: 확인된 오류와 제외한 가설

`ToonyMatCapReference.hlsl` 및 복사한 GLSL 56/57/58/60 참조.

| 원본 기능 | 조명에 넣는 albedo | 마지막 가산 항 |
|---|---|---|
| MatCap 없음 (56) | B | 0 |
| 무마스크 MatCap, type>=1 (58) | M | 0 |
| 무마스크 MatCap, type<1 | B | M |
| 마스크 MatCap, type>=1 (60) | lerp(B,M,mask) | 0 |
| 마스크 MatCap, type<1 | B | M×mask |

B=BaseMap×BaseColor, M=MatCapTex×MatCapColor. 원본 `_MatCapMask` 기본 텍스처는 black이다. **무마스크 variant는 이 텍스처를 읽지 않는다.** 현재 이식본의 white mask=1은 ColorBox 무마스크 식과 같으므로, 이것 자체를 ColorBox 어두움 원인으로 지목하면 안 된다. 반면 현재 이식본은 MatCap 비활성 재질에도 무조건 샘플·가산한다. Wood는 비활성인데 텍스처 참조가 남아 있어 원본보다 밝아지는 별도 오류 후보다. 마스크 기본값만 black으로 바꾸면 무마스크 ColorBox까지 깨지므로 반드시 기능 분기를 함께 복원한다.

GLES clip-depth 기반 MatCap UV 식을 D3D에 옮긴 부분은 좌표 규약별 결과가 아직 미검증이다. 앞 두 차이를 검증한 뒤 같은 법선/카메라 위치의 MatCap UV를 비교한다. 근거 없이 텍스처를 감마 보정하거나 전체 광원을 올리지 않는다.

### 전체 Toony 기능표 및 JamJar rim

`toony_feature_inventory.json`은 26재질의 저장 float/키워드/candidate GLSL을 함께 보존한다. MatCap (활성,type) 분포는 (1,1)=14, (0,0)=8, (1,0)=4로 실행측 집계와 일치한다. 원본 비활성 MatCap은 Black/White, Ice_Cylinder, StoneCylinder, StoneSquare, TablePole, Wood, WoodBox. 비활성 specular는 ColumnSquare/ColumnCylinder/PiggyBox/StoneSquare/StoneCylinder 5종이다. 기능은 저장 valid keyword와 대응 GLSL을 기준으로 확인하며, 비활성 기능의 낡은 저장 숫자만 보고 켜지 않는다.

**JamJar Orange/Purple에는 rim 합성이 실제로 있다.** 대표 JamJar_Blue(entry60)에 없다는 이유로 이 2종까지 생략하면 안 된다. 후보는 49/61/73/85; soft/noncascade인 `toony_entry0061.glsl`을 동봉했다.

- lines685–697: `edge=1-max(dot(V,N),0)`; `t=saturate((edge-RimMin)/(RimMax-RimMin))`; `rim=t²*(3-2t)`.
- main rim=`rim*RimColor*(mainRamp*mainShadow*unity_LightData.z*MainLightColor)` (662–678에서 light mask 생성).
- additional rim=`rim*RimColor*sum(additionalRamp*distanceAtten*spotAtten*AdditionalLightColor)` (775–808).
- 이 항에는 albedo/BaseColor/HColor/SColor를 곱하지 않는다. `_RimContrast/_RimAmount` 등 남아 있는 다른 셰이더의 저장 속성을 넣지 않는다.
- 두 재질 모두 RimMin=.5, RimMax=1, UseRim=1, UseRimLightMask=1. Purple RimColor=(.3975901604,0,1), Orange=(.8307700753,.8307700753,.8307700753), alpha1. `_RimColor`도 원본 HDR 속성이다.
- `ToonyMatCapReference.hlsl`의 `RST_RimLightMasked`는 이 경로의 참고 함수다. 다른 rim 기능 조합으로 일반화한 구현은 아니다. 원본에 별도 rim epsilon은 없으며 저장 Min/Max가 다르다.

## Forward+ 차이는 별도 유지

`brightness_evidence.json`과 `target_snapshot` 참조. 조사 시점 QualitySettings의 현재/Standalone PC 품질이 PC_RPAsset→PC_Renderer의 RenderingMode=2(Forward+)를 선택한다. RS_Toony/RS_OmniShade는 `_ADDITIONAL_LIGHTS` 루프만 있고 `_FORWARD_PLUS` 대응이 없다. 설치된 URP ForwardLights.cs는 Forward+에서 `_ADDITIONAL_LIGHTS`를 끈다. RealtimeLights.hlsl도 Forward+에서 GetAdditionalLightsCount를 0으로 반환한다. pragma 하나를 추가하는 것만으로 추가 방향광 루프가 복원되지는 않는다.

따라서 이 설정이 실제 실행 중이라면 보조 방향광 0.4가 해당 분기로 들어가지 않는다. **실행 중 quality/currentRenderPipeline/renderer가 실제로 같은지는 별도 로그가 필요**하다. Forward(0)만 바꾼 A/B를 요청했다. 일부 재질만 눈에 띄게 어둡다는 관찰만으로 이 문제를 배제하거나 주원인으로 확정하지 않는다.

`texture_import_comparison.json`: 원본 73장 중 sRGB 플래그 차이는 normal 3장이다. 현재 두 셰이더는 이 normal 맵을 샘플하지 않으므로 해당 차이를 이번 어두움의 원인으로 단정하지 않는다. MatCap의 원본 color_space=1과 타깃 sRGB=1은 일치한다.

## FitCameraFovToTables

[원작 코드 판독] libil2cpp.so SHA256 `5819bd6f94ae20d0c877a4eaaa0ceabc43f1b6ce5fdb56997f2fd10b600cdf68`.

- Fit: RVA `0x399E858`; ViewportSpan: `0x399F830`; WidthFits: `0x399F9A8`.
- `autoFit`와 level/camera 유효성 확인 후 baseFov<0이면 현재 FOV를 캐시한다. 매 호출 시작 시 baseFov로 되돌린다. 생성자 baseFov=-1.
- `level.GetComponentsInChildren<Table>(true)`의 `Table.SurfaceRenderer`만 대상. getter `0x3944248`은 `m_filter.GetComponent<Renderer>()`. null 또는 renderer.enabled=false만 제외한다. activeInHierarchy 필터를 추가하지 않는다.
- 각 **Renderer.bounds 월드 AABB를 합친 후 그 합집합 AABB의 8개 모서리**를 WorldToViewportPoint로 투영한다. 블록 전체, 받침 기둥, collider bounds를 넣지 않는다.
- 판정: `minZ > 0 && minX >= horizontalMargin && maxX <= 1-horizontalMargin`. Y 범위는 계산하지만 판정에 사용하지 않는다. nearClip/farClip과 비교하지 않는다.
- baseFov가 맞으면 그대로. maxFov도 안 맞으면 maxFov에 두고 경고. 그 사이에서는 **24회 이분 탐색, 마지막 high(들어맞는 쪽)**를 선택한다.
- 저장 초기 FOV=30, margin=.01, maxFov=35. 위쪽 블록이 화면 밖이어도 이 함수는 폭만 맞추므로 반드시 오류는 아니다.

`CameraFovReference.cs`는 이 동작을 재구성한 참고 코드이며 원본 C# 복구본은 아니다. Table 의존성을 제거했으므로 호출자가 위 기준에 맞는 surface renderer 목록을 제공하고 baseFov 상태를 유지해야 한다. Unity 6000.0.62f1 참조 DLL 컴파일 성공(경고 0). 수학 검산 7건 성공. 실제 레벨 카메라/렌더 실행 검증과 구분한다.

## Ground RGB와 그림자

[원작 코드 판독] SG_Ground `sharedassets2.assets#19`, M_Ground `#6`. 원본 Forward 4개 variant 모두 `_ColorStart/_ColorEnd/_ZRange`를 읽지 않는다. 현재 Z 그라디언트 구현은 원본 식이 아니다.

`GroundReference.hlsl`은 entry5의 대수식을 옮긴 함수 모음이다. 엔진용 완성 shader/실행 검증본이 아니다.

- 이미 diffuse 비율이 적용된 상수 D=(.0361055769, .144683689, .00716756145), F0=.0399999991. D에 .96을 다시 곱하지 않는다.
- N/V/L 정규화, H=normalizeSafe(V+L), LoH=saturate(dot(L,H)). spec=`1/(max(LoH²,.100000001)*6.00012016)-6.10351562e-05`.
- 광원별 direct=`(D+F0*spec)*lightRGB*attenuation*saturate(dot(N,L))`.
- ambient는 정점에서 평가한 unclamped SH9를 보간한 값×D. probe는 reflect(-V,N)의 mip6 샘플을 HDR decode한 뒤 `0.5*(.0399999991 + (1-sat(NV))^4 * 2.23517418e-08)`을 곱한다. 저장 reflectionIntensity=0이나 실제 GPU probe를 캡처한 것은 아니다.
- RGB 주광 그림자는 shadowStrength 적용 후 거리 fade를 적용한다. 추가광은 distance/spot attenuation; 조사 variant에 추가광 shadowmap 샘플은 없다.
- alpha=`saturate((1-rawStrengthShadow)*.6)`이며 shadow depth<=0 또는>=1이면 0. **alpha에는 RGB용 거리 fade를 적용하지 않는다.** rawStrengthShadow는 필터링과 shadowStrength 적용 뒤 값이다.
- 최종은 indirect+main+additional, 상한65504. straight RGB이며 premultiply하지 않는다.
- 고정 pass: `Blend SrcAlpha OneMinusSrcAlpha, One OneMinusSrcAlpha`, `ZTest Always`, `ZWrite On`, `Cull Back`, material queue2000. RGB/alpha blend factor를 구분한다.
- Ground MeshRenderer pathID96은 저장 `m_SortingOrder=-3`, sortingLayerID=0. 코드의 ZTestAlways와 함께 순서를 보존해야 한다. 실행측이 이 순서 누락으로 생긴 덮어쓰기를 수정했다고 회신했다.

### Ground TRS는 누락되지 않았다

`ground_transform_chain.json` 원문 참조. 기존 `level2_ingame_scene.json`의 `nodes[].transform.m_LocalPosition/Rotation/Scale`에 있다.

- Arena: identity.
- Environment: p=(-2.0461535454,.3493623734,-7.9113726616), q=identity, s=1.
- Ground: p=(2.0461535454,-.3000000119,50.0999984741), q=(.7071068287,0,0,.7071068287), s=(502.6300964,236.2253418,45.7919235).
- [자체] 부모가 identity rotation/scale이므로 Ground 월드 p=(0,.0493623614,42.1886258125). local y=-.3을 world y=-.3으로 쓰면 안 된다.

## 파일과 검증 범위

- native ASM 원문/호출 주석: `Camera_*.asm`.
- 원본 Ground pass·variant 해시: `ground_forward_evidence.json`.
- ColorBox 원문·선언·현재 숫자 비교: `colorbox_material_evidence.json`.
- 카메라 수학 7건 / shadow fade 분리 4건: `numerical_validation.json`.
- C# 컴파일: `compile_validation.json`; 진단 probe C# 컴파일은 별도 `probe_compile_validation.json`이 있으면 그 결과를 확인한다.
- 이식본 스냅샷/해시는 조사 시점의 증거다. Claude가 이후 수정한 파일을 덮어쓰는 용도로 쓰지 않는다.

미결: 수정별 화면 A/B, Forward+ 실행 설정·보조광 A/B, Ground/rim/FOV 이식 검증. HDR GPU 전달 차이는 위 실행측 probe로 확인됐다. 원본 조준선 오브젝트 매칭은 계속 미확인이고 상시 전체 진행바/레벨 번호의 근거가 새로 생긴 것은 아니다.
