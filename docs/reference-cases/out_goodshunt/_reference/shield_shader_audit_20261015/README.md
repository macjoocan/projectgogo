# ShaderShield 원본 compiler GLSL 인계

2026-10-15, sharedassets3.assets **Material13 → Shader103**, 원작 실행 없음. resource-extract 기존 bounded parser 재사용, peak commit **0.205GB**, guard2.5GB, 정상 종료. 이 자료는 원본 ShaderGraph 편집 소스가 아니라 **배포 빌드에 보존된 compiler GLSL/parsed form**이다. 웹 이식/GPU/원작 화면 동등성은 미검증.

`material13.json`: 원문 SavedProperties/키워드/렌더 queue+rawSHA. `shield/parsed_form.json`: 프로퍼티 선언/패스 상태. `inventory.json`: 원본 rawSHA, segment/entry/keyword/GLSL SHA 및 길이 검증. platform9(GLES3) segment0은59940B, blob entry10개, GLSL 텍스트 **5개 추출**. 10개 전부가 서로 다른 GLSL이라는 뜻 아님. entry2/3은 조명·shadow 변형, entry5 ShadowCaster 코드, entry7 normal 코드, entry9 Universal2D형 코드. 최종 실행 variant 선택은 런타임 상태와 대조해야 한다.

## 원작값

- 이름 `Shader Graphs/ShaderShield`, shader rawSHA4258489b1bc130e4ac4ed146cb605f127f1a18370db166f19146ca796fa930e2.
- Material rawSHA771e855eb8b5002b95d461a2d812ee59895f1946b9d79e492132ae73441ce316.
- _MainTex=file0/path71, scale1/offset0. 직접 UV0 sampling이며 fragment에서 ST를 추가 적용하지 않는다.
- _FrontColor=(0,.6658520698547363,29.463499069213867,1).
- _BackColor=(0,5.215367794036865,19.371360778808594,.4000000059604645).
- _FresnelColor=(2.6594221591949463,0,383.498046875,1), power5.
- 위 세 Color 선언 **flags16(HDR)**. _VertexAmount vector=(.0005000000237487257,.0005000000237487257,.0005000000237487257), frequency0.
- queue3013. 저장 _Opacity1은 **parsed shader property 선언/이 GLSL uniform·실행 식에 없음**. ShaderGraph가 소비한다고 만들어 넣지 말 것.
- **Universal Forward**: Blend RGB One/One, alpha One/One, Add; CullOff, ZTestLEqual(4), ZWriteOff. SourceAlpha/One은 **Universal2D 패스**의 상태이며 Forward에 섞으면 틀린다.
- ShadowCaster ZWriteOn/ColorMask0/CullOff. DepthNormals ZWriteOn/CullOff. 모두 parsed form 원문 보존.

## 식 판독 (entry0002 line91~ / fragment270~409)

버텍스: `pOS += sin(_TimeParameters.x*_VertexFrequency) * (normalOS*_VertexAmount)`. 저장 frequency0이므로 기본값에선 변형0. 임의 pulsation 속도를 더하지 않는다. world normal은 inverse-transpose 계열 WorldToObject dot 후 정규화. vertex SH는 실제 코드대로 감마 변환되는 경로가 있으므로 웹 SH를 선형 값 그대로 넣었다고 같다고 하지 않는다.

컴파일된 fragment의 세 HDR색 모두 아래 성분별 함수를 거친다. 이것은 **셰이더 내부 명시 변환**이며 임포터 CPU 변환과 구분한다:

```
G(c) = c<=.00313080009 ? c*12.9232101
                       : 1.05499995*exp2(log2(abs(c))*.416666657)-.0549999997
T = texture(_MainTex, UV0)  // 원본 mip bias uniform 포함
front = T.rgb*G(_FrontColor.rgb)
back  = T.rgb*G(_BackColor.rgb)
A = saturate((T.a*_FrontColor.a)*(T.a*_BackColor.a))
D = .959999979 * (frontFacing?front:back) * A
```

**알파는 앞/뒤 선택이 아니라 T.a 제곱 × Front.a × Back.a**. Fresnel/Opacity로 대체하지 않는다. 앞뒷면 모두 같은 worldNormal을 쓰며 이 코드에 backface normal 반전 없음.

V는 perspective에서 normalize(camera-worldPos), ortho에서 view matrix의 z축. N=normalize(worldNormal). 직접광은 main light만 읽는 표본이며, L=mainLightPosition.xyz, H=normalize(V+L):

```
NL=saturate(dot(N,L)); NH=saturate(dot(N,H)); LH=saturate(dot(L,H)); NV=saturate(dot(N,V))
den = 3*max(LH*LH,.100000001)*pow(1.00001001-.9375*NH*NH,2)
spec = .0625/den - .0000610351562
direct = (D + .0399999991*spec) * NL * mainLightColor * shadowAttenuation * unity_LightData.z
indirectDiffuse = interpolatedVertexSH * D
env = decodedSpecCube(reflect(-V,N),lod=4.05000019)
indirectSpec = env*(.0399999991+.5*pow(1-NV,4))*.941176474
rim = pow(1-saturate(dot(normalize(N),normalize(V))),_FresnelPower) * G(_FresnelColor.rgb)
emission = frontFacing ? rim : front
RGB = direct + indirectDiffuse + indirectSpec + emission
RGBAout = min(vec4(RGB,A),65504)
```

env HDR decode와 shadow strength/fade/noncascade 범위 분기는 원문 entry2에 있다. 위 decodedSpecCube/shadowAttenuation은 이 부분을 줄인 표기다. 그림자 없는 Lambert만으로 같다고 하지 않는다. **뒷면 emission은 Back색이 아니라 front=T.rgb*G(FrontColor)**. FresnelColor.a는 이 식에서 미사용. 출력 RGB 전체에 A를 다시 곱하지 않으며 Forward One/One으로 더한다. 톤매핑·출력 색공간·mediump 정밀도·SH/반사 probe가 맞지 않으면 픽셀 동등성은 보류한다.

Universal2D entry9는 Fresnel과 조명 없이 앞/뒷면색×T.rgb를 출력하고 alpha1이다. 이 패스를 Forward 대신 사용하지 않는다.
