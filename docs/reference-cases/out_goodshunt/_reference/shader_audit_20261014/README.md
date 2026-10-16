# 원본 compiler GLSL 확보 / 2026-10-14

원본 data.unity3d를읽기전용으로로드하고세Shader만선택했다.
- globalgamemanagers.assets#23 OmniShade/Standard URP:103 GLSL프로그램
- sharedassets2.assets#589 Toony Colors Pro 2/Hybrid Shader 2:9 GLSL프로그램
- resources.assets#1175 Shader Graphs/WorldUV:11 GLSL프로그램

inventory.json에원본Shader raw SHA/file/pathID,platform9의compressedsegment표본좌표,프로그램entryoffset/length/codeSHA를보존했다.각GLSL의길이접두사와blob entry포함범위검증123/123,각프로그램키워드헤더프레임검증123/123. .glsl은원작컴파일러출력그대로이며생성AI/Three재작성결과가아니다. 추출peak약0.20GB.

parsed_form.json에는프로퍼티선언/flags/subshaderpass/renderstate/keywordnames가있다. stripped parsed form의m_PlayerSubPrograms가비어있어컴파일entry와pass를이필드만으로확정연결하지않았다. 코드키워드와pass/재질조합을정적으로대조할수있지만실제런타임variant선택/GPU정합은미검증이다.

대표저장재질참조:
Void-Normal sharedassets3.assets#6 -> fileID1(globalgamemanagers.assets)#23 OmniShade
cart_toony 1 sharedassets3.assets#7 -> fileID6(sharedassets2.assets)#589 Toony
Envi_GrassTile_new resources.assets#30 -> fileID0#1175 WorldUV
관련원문재질필드는기존GoodsHunt_structured_objects.zip에있으며 component/asset import에필요한texturePPtr는기존externals표와연결한다.

'원본HLSL없음'과'원작계산식확인불가'는같은뜻이아니다. 이번GLSL을근거로조명/MatCap/UV/clip계산을읽을수있다. 다만Unity전용uniformbuffer/URP조명/texturebinding을Three/WebGL에연결하는adapter는파생구현이며해당원문을그대로ShaderMaterial에넣으면동작한다고주장하지않는다. 공개업로드/배포없음,로컬분석자료로만사용.

경로명entry0048 등숫자는blob program index이지레벨/재질번호가아니다. inventory의keywords와저장materialkeywords를대조하고원작runtime키워드까지고려할것. fullpixel동등성이나모든shader240종분석완료로확대하지않는다.
