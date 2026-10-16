# level3 파일 조명 저장값 — 2026-10-14

[원작값] level3_light_chain.json은 Light#41/GO21/Transform36/부모Transform35와 RenderSettings#40 원문 및 rawSHA를 보존. **level3는 SerializedFile 이름이며 3스테이지라는 뜻이 아니다.** 현재 캡처 시점 실제 loaded scene/light modification을 실측한 자료가 아니다.

Directional Light: enabled1, GO active true, type1, Color(1,1,1,1), intensity1.0, bounce1.0, colorTemperature6570/use=false.
Transform36 q=(-0.14869080483913422,0.760908305644989,-0.6030883193016052,-0.18760114908218384), p0/s1. Parent 이름Light/Transform35는 회전identity. 계산 local forward는 JSON의 calculated_local_forward이며 원문 q를 별도 normalize하지 않았다.
Shadows.type1 = **Hard**, strength0.30000001192092896, bias0.05000000074505806, normalBias0.4000000059604645, near0.20000000298, resolution1.
m_CullingMask.bits896 = layer7/8/9, renderingLayerMask1. layer번호와 웹bitmask 대응은 importer 계약으로 별도.

RenderSettings: fog=false, ambientMode3(Flat), ambientSkyColor gray0.40566039085388184, ambientIntensity2.0, reflectionIntensity1.0, Sun local#41, skybox fileID3/pathID2. ambient equator/ground/indirectSpecular와 m_AmbientProbe sh[0..26]는 **모두 원문 JSON에 보존**.
저장 SH27개와 GPU unity_SHAr/SHBr 등 shader packed uniforms는 같은 배열이 아니다. packing/감마/라이팅 runtime 변경 대조 없이 저장 SH를 그대로 7vec4에 밀어넣지 않는다. Flat ambient 저장값과 baked m_AmbientProbe도 실제 runtime 선택을 구분.

PlayerSettings globalgamemanagers#1 m_ActiveColorSpace=0, 원본 ColorSpace enum TypeDef9792 Gamma0/Linear1 => **Gamma 프로젝트**. 앞 게임(RoyalSmash의 Linear) 값과 섞지 말 것. lighting_stored_values.json에는 original player/graphics/quality/light/settings 전체 표본이 있다. 원본텍스처 색공간/셰이더출력/Three outputColorSpace pipeline이 각각 다르므로 '모든 텍스처 gamma 해제'로 단순 치환하지 않는다.

추출 read-only UnityPy 선택 로드; level3_light_chain receipt peak commit0.181GB. source data.unity3d/원본 설치 변경 없음. 원본 실행/현재 GPU parity 검증 없음.
