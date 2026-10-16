# 대표 셰이더 연산 판독

이 문서의 식은 **[원작 코드 판독]**이다. 원본 GLSL을 읽어 기호로 정리했으며, 원본 HLSL 복구나 새 URP 셰이더의 화면 검증 결과가 아니다. 정적 후보 연결은 `material_pass_candidates.json`, 저장 키워드 전체19조합은 `saved_keyword_combinations.json`을 사용한다. 정밀도 mediump/highp 및 정점 보간 위치를 바꾸면 결과가 달라질 수 있다.

원본 경로는 `../shader_program_analysis/` 기준. 표본은 OmniShade `gles_entry0202.glsl`(TableSquare 조건부 후보), Toony `gles_entry0060.glsl`(JamJar_Blue 조건부 후보)다. 두 후보는 `_ADDITIONAL_LIGHTS`, `_MAIN_LIGHT_SHADOWS`, `_SHADOWS_SOFT` 조건이다. 원작 실행에서 이 번호를 관측하지 않았다.

## 1. OmniShade 202 — 전체 합성 순서

`N`은 보간한 월드 법선을 fragment에서 정규화한 값, `A`는 main texture RGB×_Brightness×_Color.rgb다. _Contrast는 이 표본에서 미사용이다. 샘플 alpha는 _IgnoreMainTexAlpha==0이면 saturate하고, 그렇지 않으면1; 마지막에 _Color.a를 곱한다(572–580행).

```text
n = max(dot(N,L), 0)
d = pow(max(n + _DiffuseWrap*(1-n), 0), _DiffuseContrast)
    * _DiffuseBrightness
direct = A * (mainLightRGB * probeOcclusion.x * d * mainLightEnabled
              + vertexAdditionalDiffuse)

M = pow(MatCapSample.rgb, _MatCapContrast)
    * _MatCapColor.rgb * _MatCapBrightness
lit = direct * M + mainSpecular
lit = lit * lerp(_ShadowColor.rgb, 1, finalShadowAttenuation)
lit = lit + _Emissive.rgb
lit = lit + A * SH9(N) * _AmbientBrightness

Y = dot(lit, (0.212672904, 0.715152204, 0.0721750036))
output.rgb = Y + _Saturation*(lit-Y)
```

근거: direct582–595, MatCap606–612, specular613–623, shadow/emissive843–857, SH ambient858–872, saturation873–875행. **ambient가 MatCap으로 함께 곱해지는 구조가 아니다.** 채도는 base texture에만 미리 적용하는 것이 아니라 이 표본에서는 조립 후 전체 RGB에 적용한다. _Saturation0은 회색,1은 원색이며2도 저장 가능하다. 대표 표본에는 Rim/Reflection 합성 코드가 없다.

추가광원 diffuse는 이 OmniShade 프로그램에서 **vertex** 단계241–284행에 계산해 TEXCOORD11로 전달된다. 설정 이름에 PerPixel이 있어도 이 실제 프로그램을 fragment additional-light loop로 바꾸면 동일 연산이 아니다. 추가광원은 거리/spot 감쇠를 곱하고 같은 diffuse pow식을 쓴다. main specular만 이 표본 fragment에 있다.

### Specular: reflection-vector Phong 형태

정점에서 `R=normalize(reflect(-L,Nvertex))`를 계산해 TEXCOORD3로 전달한다(285–290행). fragment는 보간된 R과 V를 다시 정규화해 다음을 계산한다.

```text
p = pow(max(dot(normalize(interpolatedR), normalize(V)),0), _SpecularSmoothness)
specColor = (sum(_SpecularColor.rgb) != 3)
          ? _SpecularColor.rgb : mainLightRGB*probeOcclusion.x
mainSpecular = mainLightEnabled ? p*_SpecularBrightness*specColor : 0
```

**Blinn half-vector나 GGX가 아니다.** `sum!=3` 조건을 임의의 RGB==white 비교로 바꾸지 않는다. 일반 흰색 범위에서는 같아 보여도 HDR 입력에서는 다를 수 있다.

### ANIME_SOFT와 Ramp

이 표본의 ANIME_SOFT는 위의 wrap→pow 명암식이다. Ramp 텍스처를 샘플하지 않는다. "ANIME_SOFT니까 Ramp를 읽는다"는 연결은 성립하지 않는다.

전달43개 원본 객체의 nonnull Ramp 슬롯은 ColorBoxSquareRed의 `_Ramp`1개를 확인했다. 그것도 `_RampType=0`이고 저장 활성 키워드에 Ramp texture 기능이 없다. 기존 슬롯5종 집계는 현재 원본43객체 범위와 다르다. **슬롯이 저장됐다는 이유만으로 활성 샘플이라고 판단하지 말 것.** Toony의 아래 대표도 텍스처 대신 threshold/smoothstep을 쓴다.

## 2. OmniShade MatCap UV와 회전

`Nview=normalize((float3x3)View*Nworld)`, `Pview`는 월드 위치를 View로 변환한 좌표다.

- **MATCAP_STATIC 꺼짐, PERSPECTIVE 꺼짐**: `uv=Nview.xy*0.5+0.5`. 이후 `_MatCapTex_ST.xy/zw`를 적용한다. 근거 OmniShade147 299–307행. Can_Cone의 재질 기능과 맞는 기본 변형이다(이 번호 자체는 광원/그림자 전역 키워드 없는 후보).
- **MATCAP_STATIC 꺼짐, PERSPECTIVE 켜짐**: `C=cross(normalize(Pview),Nview)`, `uv=float2(-C.y,C.x)*0.5+0.5`, 이후 ST. 근거202 569–571/596–606행. 중앙시선에서 일반 view-normal UV와 일치한다. cross 인자순서/부호를 뒤집지 않는다.
- **MATCAP_STATIC 켜짐**: 정점에서 월드 법선을 _MatCapRot로 돌린 값을 보간하여 `uv=interpolatedRotatedNormal.xy*0.5+0.5`, 이후 ST. 아래 static 표본의 fragment에서는 UV용 법선을 재정규화하지 않는다. STATIC과 PERSPECTIVE가 함께 저장돼 있어도 static 표본162의 UV에는 view position이 들어가지 않는다.

_MatCapRot는 **라디안**, 정점 단계의3축 회전이다. 2D UV 회전이나 degree 값을 넣는 자리가 아니다. 표본160/162 218–233행을 정리하면:

```text
s = sin(_MatCapRot.xyz); c = cos(_MatCapRot.xyz)
a = c.z*N.x - s.z*N.y
b = -s.y*a + c.y*N.z
t = s.z*N.x + c.z*N.y
rotatedN.x = c.y*a + s.y*N.z
rotatedN.y = c.x*t - s.x*b
rotatedN.z = s.x*t + c.x*b
```

즉 Z→Y→X 순서다. 활성 STATIC 원본은 Can_Cylinder 두 객체와 Cannon_material이다. TableSquare202 및 Can_Cone147에서 _MatCapRot는 미사용이다. 따라서 Can_Cone 동명 두 객체의 저장 _MatCapRot 차이가 현재 활성 기능에서 외관 차이를 만든다고 단정하면 안 된다. 원본 객체 식별은 그대로 보존한다.

**MATCAP_CONTRAST**: `exp2(log2(sample.rgb)*contrast)`다. `(sample-0.5)*contrast+0.5`나 `sample/0.5`가 아니다. 원문은 별도 epsilon clamp가 없으므로0 입력 취급을 임의로 바꾸면 완전 동일 연산이라 할 수 없다.

**_MATCAPBLEND_MULTIPLY**: 위 direct RGB에 `M`을 곱한다. **MULTIPLY_LIGHTEN** 표본162는 조립된 direct/lightmap RGB에 `(1+M)`을 곱한다(469–477행). max(original, original*M) 식이 아니다.

## 3. Toony60 — MatCapMask는 다른 셰이더의 기능

이 표본의 mask/합성은 OmniShade의 _MATCAPBLEND_MULTIPLY와 섞어서는 안 된다. 396–415행:

```text
B = sample(_BaseMap, baseUV).rgb * _BaseColor.rgb
M = sample(_MatCapTex, interpolatedMatcapUV).rgb * _MatCapColor.rgb
mask = sample(_MatCapMask, baseUV)[selectedChannel]
// channel 값: >=3 alpha, >=2 blue, >=1 green, 그 외 red
if (_MatCapType >= 1) { albedo=lerp(B,M,mask); additiveMatcap=0; }
else                 { albedo=B; additiveMatcap=M*mask; }
```

mask는 diffuse/specular를 모두 만든 최종 색에 곱하는 것이 아니다. 타입>=1이면 **조명에 들어갈 albedo를 먼저 교체**, 타입<1이면 MatCap을 최종 additive 항에 보탠다. mask 없는 Toony58은 타입>=1에서 albedo를 M으로 직접 바꾼다. JamJar_Blue 등의 저장 _MatCapType=1은 앞 경로다.

### Toony MatCap UV

이 표본은 정점에서 clip-space 기반 보정을 적용한다(145–171행). OmniShade의 cross 기반식과 다르다.

```text
screenXY = float2(clip.x, clip.y*_ProjectionParams.x)*0.5 + clip.w*0.5
screenXYZ = float3(screenXY, clip.z)/clip.w - 0.5
correction = screenXYZ.xy * screenXYZ.z
uv = (viewNormal.xy - 0.5*correction)*0.5 + 0.5
```

`viewNormal`은 원본 정점 법선의 inverse-transpose/world 정규화 후 View로 변환한 값이다. sample은 보간한 UV를 그대로 쓴다. 이 표본에는 OmniShade _MatCapRot나 _MatCapContrast 적용이 없다. 새 shader의 렌더 API clip-space 차이를 확인해야 하며, GLES에서 읽은 화면좌표식을 검증 없이 모든 API 공통 결과로 보장하지 않는다.

### Toony diffuse / ambient

fragment는 정규화한 월드 normal에 front/back face 부호를 적용한다. 원근에서는 V=normalize(camera-P), 직교에서는 View의 카메라 방향 성분을 선택한다. Main diffuse660–680행:

```text
x = dot(N,L)*0.5 + 0.5
t = saturate((x - (_RampThreshold-_RampSmoothing*0.5))/_RampSmoothing)
ramp = t*t*(3-2*t)
shade = lerp(_SColor.rgb, _HColor.rgb, ramp*shadowAttenuation*mainLightEnabled)
mainDiffuse = albedo * shade * mainLightRGB
ambient = _IndirectIntensity>0
        ? albedo*SH9(_SingleIndirectColor>0 ? V : N)*_IndirectIntensity : 0
```

_RampSmoothing=0에서 별도 epsilon을 추가하지 않은 원문이다. 추가광원의 diffuse는 `albedo*additionalLightRGB*_HColor*ramp*attenuation`; main처럼 _SColor 보간을 더하지 않는다(758–771행).

### Toony specular — GGX NDF 형태의 간소화 식

707–731행은 half-vector 기반의 GGX 분포 형태다. 전체 물리기반 GGX BRDF/Fresnel/Smith 구현이라고 부르지 않는다. 실제 스칼라식은 아래와 같다.

```text
H = (V+L) / sqrt(max(dot(V+L,V+L),0.001))
NoH = saturate(dot(N,H)); NoL = saturate(dot(N,L))
g = specMask * max(_SpecularRoughness,0.00001)
u = g*g
a2 = min(u,1)^2
D = (a2*0.318309873) / ((NoH*NoH*(a2-1)+1)^2 + 0.0001)
specFactor = D*0.157079637 / (u*u+1)
mainSpec = specFactor*shadowAttenuation*mainLightEnabled*NoL
           *mainLightRGB*_SpecularColor.rgb
```

specMask: _SpecularMapType>=5는 SpecGlossMap alpha, >=4 blue, >=3 green, >=2 red, >=1은 BaseMap alpha, 그 외1. _SpecularMapType 기본0인 재질에는 별도 맵 마스크가 없다. 추가광원 spec은 같은 식에 해당 light attenuation/NoL/color를 적용한다.

Toony60의 최종790행은 `ambient + mainDiffuse + additionalDiffuse + mainSpec + additionalSpec + additiveMatcap`이다. 이 표본에는 emissive/rim/fog 추가가 없다. `TCP2_RIM_LIGHTING_LIGHTMASK`와 `TCP2_REFLECTIONS_FRESNEL`라는 저장 하위 키워드가 있어도 상위 rim/reflection 기능이 활성이라는 뜻은 아니다.

## 4. Fog와 검증 범위

**[원작값]** level2 RenderSettings의 `m_Fog=false`. 전달 대상 GLES287개에서 `unity_FogColor`/`unity_FogParams` 심볼은0개이며, 두 대표의 최종 코드에도 fog blend가 없다. 로컬 `FOG` 키워드만 보고 포그를 임의 추가하지 않는다. 이것은 해당 추출 빌드/프로그램 범위의 결론이다.

정적 근거의 범위를 넘는 항목: 실제 frame의 pass/전역 키워드/renderer 선택, live 재질값 변경, 새 HLSL의 GPU 정밀도·색공간·화면 일치. 원문 GLSL과 declared property를 함께 제공했으며 런타임 동등성은 미검증이다.
