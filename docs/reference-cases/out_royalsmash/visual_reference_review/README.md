# 원본 스크린샷 19장 + 조명/재질 후속 판단

2026-09-16. 사용자 제공 원본 스크린샷 19장을 모두 직접 열어 검토했다. `source_screenshots/`에 픽셀 수정 없이 보관했다. 원본 게임 실행/접속 없음. 현재 프로토는 코드만 읽었고 같은 프레임의 비교 캡처를 새로 만들지는 않았다. 따라서 개선 방향 검토이지 **시각적 일치 통과/구현 완료 판정은 아니다**.

## 결론: 해결 가능한 항목이 남아 있다

| Claude 설명 | 재검토 결과 |
|---|---|
| Specular 추가 가능 | 맞음. roughness뿐 아니라 색·N/H·광원·shadow 감쇠·합성 위치도 필요. 원작과 같은 화면이 된다는 시간 보장은 못 함 |
| MeshMatcapMaterial은 기본적으로 그림자를 못 받음 | 맞음. 그러나 재질별 로직을 전부 새로 작성해야 하는 것은 아님. 공통 shadow-capable 기반으로 생성 코드/파라미터를 재사용할 수 있음 |
| SH 데이터는 추출물에 없음 | **정정 필요. 기존 gameplay_scene_lighting.json에27개 계수가 있고 APK 재독해와 전부 일치** |
| .34/.42가 Unity SH 계수 | 아님. 현행 materials.js 주석대로 프로토가 SH를 대신한 [자체] 스칼라 상수 |
| 런타임 변형은 미확정 | 맞음. 정적 후보 축소/후보간 공통동작 검증은 가능하지만 원작 실행 선택 관측은 별도 |
| SH를 바꿔도 차이는 작음 | 동일조건 비교 렌더 없이 크기를 단정할 근거 없음 |

## 1. SH: 데이터가 없는 문제가 아니라 실효 광원 선택 검증 문제

새 증거 `../shader_variant_analysis/ambient_probe_verified.json`:

- `UnityDataAssetPack.apk!assets/bin/Data/level2`, RenderSettings path103.
- 기존 `gameplay_scene_lighting.json`의 RenderSettings 전체와 재독해가 동일.
- raw serialized SH27개, `m_AmbientIntensity=1`, `m_AmbientMode=3`, `m_UseRadianceAmbientProbe=false`.
- source SHA256 b20f0c5959a331115f78f9af0e8112f53aa18df37d9320684349479fdeb4b343.
- **저장된 ambientProbe를 모든 블록의 실제 unity_SH* uniform이라고 단정하지 말 것.** Unity는 개별 Light Probe/lightmap 적용 시 해당 환경광 경로가 다를 수 있다. [Unity ambientProbe 문서](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/RenderSettings-ambientProbe.html).
- mode3는 Flat이며 Trilight(1)가 아니다. sky/equator/ground 세 색이 직렬화돼 있다는 이유만으로 반구광을 원작 설정이라 부르지 말 것. [Unity 공식 enum](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Runtime/Export/Graphics/GraphicsEnums.cs).
- Flat 상태의 실행 시 환경광 구성/재계산, renderer probe 사용 여부, runtime 교체는 미검증. raw27계수의 shader packing/기저 정규화·부호·축 변환을 확인해야 하므로 `unity_SHAr/Br/C`에 연속 복사하거나 Three LightProbe에 무검증으로 넣지 말 것.
- 검증 방향: 저장 Flat 환경색 경로와 저장 probe 경로를 **대안으로 각각** 렌더하고 중복 가산하지 않는다. coefficient→Unity SH evaluator→6축법선 결과와 Three evaluator 결과를 비교해 변환 단위 테스트. Unity→Three 좌표계 반전 시 SH기저/법선도 함께 대응시킬 것. linear광량에 sRGB 변환을 중복 적용하지 않는다.
- Toony61의648–664행은 SH에base와IndirectIntensity를 곱하며, `_SingleIndirectColor` 분기도 있다. 그 값을 재질별 보존한다. Purple indirect=.75, Red/Blue=1. 동일상수로 뭉개지 말 것. Omni는 AMBIENT키워드가 켜진 경우만 해당 항을 쓴다.

즉 **추가 원본 데이터를 찾을 수 없어서 상수밖에 못 쓰는 상태는 아니다.** 그러나 raw계수 확보≠최종실효SH확정도 명시해야 한다.

## 2. 그림자: 공통 기반을 한 번 바꾸고 기존 로직 재사용

프로토 번들 `three.module.js`는 **r169**. `../shader_variant_analysis/three_shadow_support.json`은 이 실제 번들의 ShaderLib.matcap/chunks/uniform inventory를 보존한다.

- 기본 Matcap shader에는 shadowmap 입력/샘플링이 없다. `receiveShadow=true`만으로 해결되지 않는다. [three 공식 설명](https://threejs.org/docs/pages/MeshMatcapMaterial.html).
- r169 renderer의30922–30926행 `materialNeedsLights`는 MeshMatcapMaterial을 포함하지 않는다. `matcapMaterial.lights=true` 한 줄만 추가하는 방법은 자동 uniforms 연결을 보장하지 않는다.
- **권장 설계안(미구현)**: ShaderLib.matcap의 vertex/fragment와 matcap uniforms를 공통 ShaderMaterial 기반으로 가져오고, lights uniforms를 병합해 `lights:true`로 연결한다. shadow vertex좌표/normalBias, fragment shadow sampling, light별 uniforms를 포함한다. 기존 material별 `toonyLight`/Omni조합/마스크/텍스처 parameter 생성 함수를 이 공통 기반 위에서 재사용한다. ShaderMaterial.lights는 광원 uniform 연결을 허용하지만 shadow 수식을 자동 작성하지는 않는다. [공식 ShaderMaterial 문서](https://threejs.org/docs/pages/ShaderMaterial.html#lights).
- 자동내장 map/matcap/UV defines·texture transform·alpha test·fog·outputColorSpace/tonemapping·clipping·instancing 지원과 material별 cache key는 명시적으로 재연결/검증해야 한다. `isShaderMaterial` 등 flag를 속이는 임시 방편 대신 실제 공통재질 클래스로 만들 것.
- Blue와Jar 2재질로 먼저 컴파일 및 shadow-on/off 검증 후 다른 family로 확장. 현행 main.js에는 renderer.shadowMap/PCFSoft, key.castShadow,1024map, block.cast/receive가 이미 있다. **그림자 생산과 재질의 그림자 수신을 구분**할 것.
- Toony61의 shadowStrength/fade는632–645, direct ramp에 shadow를 넣는 부분은665–679. 간접광은별도. 최종색 전체를 shadow로 곱하면 SH/emissive/재질별 tint까지 잘못 어둡힐 수 있다. Omni의_ShadowColor 경로는별도다.
- 원본 저장 설정 cascade1/distance60/Light104soft strength.75는 유지. 단, Unity shadowDistance는 Three shadow.camera.far와 같은 값이 아니다. 원본bias.05/normalBias.4도 엔진별 투영·단위 차이 검증 없이 그대로 이식하지 않는다. strength.75를 두 번 적용하지 않도록 주의. PCFSoftShadowMap이라는 이름이 원작URP필터와 픽셀동일을 보장하지 않는다.

따라서 ShaderMaterial로 옮기는 작업은 필요할 수 있지만 **재질51개를 각각 다시 만드는 문제는 아니다**. 공통기반 재구성과 대표재질 검증으로 줄일 수 있다. 현재 브라우저에서 패치 컴파일/성능/스크린샷 검증은 수행하지 않았다.

## 3. Specular: roughness만 켜는 것은 부족

`toony_lighting_source_params.json` 재확인:

| 재질 | Roughness | SpecularColor RGB | SpecularMapType |
|---|---:|---|---:|
| ColorBoxSquareBlue | .55 | (.25617978,.37752810,.4) | 0 |
| JamJar_Red | .25 | (.71569377,.59061903,.59061903) | 0 |
| JamJar_Purple | .25 | (1,1,1) | 0 |

Toony61은698–723의map selector,725–747의half-vector/roughness 및light attenuation,748의가산이 연결된다. 같은.25라고Red/Purple를같은흰광택으로그리면안된다. 모든재질에StandardMaterial roughness숫자만이식해동일BRDF라고하지말것. Purple61의rim과Red60의no-rim도구분한다.

기존 MatCap에 이미 밝은 무늬가 있는 점과 runtime specular는별개다. 둘다원본근거가있을수있으나, 임의specular를추가해화이트클리핑으로덮지않도록 A/B 분리할것. 현재코드의world/light/view좌표정합도같이검증한다. 기본Three MatCapUV와Toony vertex143–180의view/perspective보정이동등한지도아직입증되지않았다. 재질이밝은문제를빛세기하나로만해결하지말것.

## 4. 스크린샷에서 보이는 목표

아래 시간은 파일명에 든 캡처시각 식별자이며 게임 내 시각/프레임 간격을 뜻하지 않는다. 19장 전부검토; 대표근거를범주별로기록한다.

| 범주 / 대표 파일 시각 | 관찰 | 개선방향 / 담당 / 상태 |
|---|---|---|
| ColorBox 04-41-16,04-41-23,04-42-18,04-43-07 | 색을유지한넓은전면, 밝은bevel과어두운측면/왕관홈. 일부회전면은매우밝음 | 재질중심색과모서리광택을분리. 전면전체희게만드는보정금지. P1/Claude rendering/미검수 |
| Jar 04-41-38,04-41-52,04-42-01,04-43-00 | 몸통세로광택·측면감쇠·흰테두리과일라벨이동시에보존. 뒤쪽병은부분가림 | maskR연속mix+정확MatCapColor+spec/indirect순서. 화면상불투명한색병처럼보이며유리라는이름만으로transmission추가금지. P1/Claude rendering/미검수 |
| Stone/Can 04-41-13,04-41-46,04-41-49,04-42-10,04-43-24 | Stone은상대적으로무광·균열선;Can은금속성넓은밝기띠. 같은광택을공유하지않음 | family분기유지. 움직이는캔이온전한모습은보이나파괴플래그증명아님. P1/Claude rendering/미검수 |
| Ice 04-42-28,04-42-39,04-42-47,04-42-54,04-43-33 | cyan밝은외곽,내부파랑패턴. 일반Blue박스보다발광같은느낌이강함 | Blue재질노출의기준으로Ice를쓰지말것. 별도texture/rim/alpha경로확인. P1/Claude rendering/미검수 |
| Table/Cannon 04-41-32 등 | 보라받침/금테/빨강대포에국소광택과측면그라데이션. 대포발사flash가있는프레임도있음 | 평상시재질평가는flash없는프레임사용. 대포의+1MultiplyLighten근거유지. P1/Claude rendering/미검수 |
| 접촉/그림자 전반 | 병옆·적층경계·받침밑의어두운부분은보이지만모든장면에강하고선명한투영그림자가보이는것은아님 | 실시간그림자/AO/텍스처/MatCap의구분을정지이미지만으로확정금지. 그림자켜짐은구현필요하나강도를과장하지말것. P1/Claude rendering/미검수 |

UI/재생바/촬영overlay·발사flash·움직임blur·부분crop가섞여있다. 04-42-28은장면전체가상대적으로어두워보여 전역노출피팅의단독기준으로부적합. 밝기계측은같은레벨·포즈·카메라·색공간을맞춘프로토스크린샷과객체ROI로비교해야한다. 현재사진만으로정확한shaderID/SHuniform/물리속도/마찰/공반경을역산확정할수없다.

## 5. 실행할 수 있는 다음 순서

1. 물리답장에명시한 mass/time/web-sim 오류우선정리. 그와독립적으로고정pose 렌더시험장준비.
2. 대표 Blue/RedJar/PurpleJar/Stone/Cannon에서 base,mask,matcap,indirect,direct,specular,shadow를각각출력하는디버그모드.
3. 색공간·라벨·MatCapColor를맞추고공통shadow수신기반구축. 저장SH/Flat경로를검증된변환으로비교하며.34/.42임시상수를대체할근거확보.
4. 마지막specular/rim추가,재질별cachekey검증. cast대상움직일때그림자도움직이는지확인해AO와구분.
5. 동일구도의prototype/reference ROI 비교. globalexposure만으로전체를맞추거나maskmode를사진에맞춰무근거변경하지않는다.

`runtime_selection_verified=false`, `runtime_probe_selection_verified=false` 유지. 스크린샷과맞는후보를찾는것은시각일치근거이지실행선택관측증거가아니다. **정적불확실성은남지만현재해결할수있는누락까지막는이유는아니다.**
