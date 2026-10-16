# 실제 셰이더 프로그램 추가 발견

> 후속 검증 완료: [셰이더 키워드·패스 매핑 보고서](../shader_variant_analysis/README.md). 287개 프로그램의 키워드/패스 연결은 확정됐다. 이 폴더 inventory의 `variant_keywords_mapped=false`는 최초 추출 당시의 역사적 상태이며, 현행 상태는 새 인덱스를 따른다. 실행 중 선택 여부는 여전히 미검증이다. 아래 147/41번은 설명용 샘플이지 특정 재질의 최종 선택이 아니다.

2026-09-16. 원본 APK 로컬 정적 분석. 기존 AssetRipper 더미 .shader와 별도 경로다.

## 결과

- `omnishade/`: 원본 `OmniShade/Standard URP`의 **GLES GLSL 텍스트 236개**.
- `toony/`: 원본 `Toony Colors Pro 2/Hybrid Shader 2`의 **GLES GLSL 텍스트 51개**.
- 각 `gles_entryNNNN.glsl`에는 컴파일러가 출력한 VERTEX/FRAGMENT 조건부 코드가 들어 있다. 개발자가 작성한 HLSL 원문이나 바로 재사용 가능한 Unity ShaderLab 파일이 아니다.
- `inventory.json`에 APK 내부 경로, 원본 논리 파일 SHA256, 압축 길이, 해제 길이, blob entry/텍스트 offset·크기·SHA256 기록. 모든 텍스트를 길이 prefix와 소속 blob entry 경계로 검증했다.
- OmniShade 250,281바이트 → 7,911,848바이트; Toony104,462 →1,589,828바이트. platform9=GLES3Plus. 추가 서버 요청/보호 우회/게임 실행 없음.
- 기존 UnityPy ShaderProgram 파서는 이 Unity6 blob에서 헤더/키워드를 잘못 읽었다. 초기 잘못 읽은 파일은 `.invalid_probe.txt`로 보존했으며 **사용 금지**. `*_text_spans.json`은 초기 조사 자료. 최종 근거는 `gles_entry*.glsl`와 inventory다.

## 근사식을 교정할 직접 근거

### OmniShade

표본 `omnishade/gles_entry0147.glsl` 306행 이후:

1. MatCap UV에 `_MatCapTex_ST` 적용.
2. texture(_MatCapTex, uv).rgb 샘플.
3. log2 → `_MatCapContrast` 곱 → exp2.
4. `_MatCapColor.rgb`, `_MatCapBrightness` 곱.

이 표본에서 MatCap 보정은 수학적으로 대략
`pow(sample.rgb, contrast) * matcapColor.rgb * brightness`다.
**중간 회색을 1로 정규화하는 식이 아니다.** 0 입력/저정밀도/색공간 경계는 실제 연산 순서까지 봐야 한다. 이어지는 코드에 diffuse와 ambient의 합성 위치도 보존돼 있다.

중요: 이것은 확인한 컴파일 변형의 식이다. **모든 재질/모든 변형에 통째로 적용하지 말 것.** 재질 키워드, 실제 pass, perspective correction, 다른 blend 경로를 매칭하는 작업은 아직 남아 있다. 현재 inventory의 `variant_keywords_mapped=false`는 이 한계를 명시한다.

### ColorBox Blue는 Toony 경로

원본 `UnityDataAssetPack.apk!assets/bin/Data/bbb9901c33fba485793802873b5c71fb`, Material path_id1:

- Shader 외부 참조: `edd7abf643fa4bc4e8561d4c280c97cf` path_id1 = Toony Colors Pro2.
- `_BaseColor=(0,0.2518401146,1,1)`는 맞다.
- 그러나 `_UseMatCap=1`, `_MatCapType=1`, `_MatCapColor=(0,0.3411764205,0.6000000238,1)`, 활성 `TCP2_MATCAP` 및 `_MatCapTex → CB_blue`도 존재한다.
- 즉 **“BaseColor가 존재하므로 MatCap은 사용하지 않는다”는 결론은 성립하지 않는다.** 같은 Material에 과거/다른 셰이더의 사용하지 않는 저장 프로퍼티가 남을 수 있으므로 프로퍼티 존재만으로 활성 연산을 확정하면 안 된다.
- `toony/gles_entry0041.glsl` 361–368행에서 BaseMap×BaseColor 다음 MatCap×MatCapColor를 계산하고 `_MatCapType>=1`이면 앞의 base RGB를 그 값으로 선택하는 분기가 확인된다. 이 변형이 최종 게임에서 선택됐는지까지는 미확정이지만, 단순 BaseColor-only 해석을 재점검할 직접 근거다.
- `_SpecColor`와 `_SpecularColor`, `_BCSaturation`과 `_Saturation`도 셰이더별 실제 사용 여부를 구분해야 한다.

## 다른 확인 경로

- 공식 OmniShade [Features](https://www.omnishade.io/documentation/features): MatCap multiply/multiply-lighten, brightness/contrast, perspective correction 설명. 이는 개념 교차검증용이며 게임 빌드와 같은 버전의 정확한 식을 보증하지 않는다.
- 공식 [Release Notes](https://www.omnishade.io/documentation/release-notes): 버전별 표현 변경 가능성이 있으므로 최신 패키지를 원본과 동일하다고 가정하지 말 것.
- 보유한 정식 OmniShade/Toony 패키지 소스가 있다면 게임 빌드 버전과 대조할 가치가 있다. 이번 프로토 폴더에서는 해당 원본 .hlsl/.shader 소스를 찾지 못했다. 구매/설치/외부 소스 다운로드는 하지 않았다.

## 텍스처도 함께 전달

`../block_texture_handoff/README.md`와 `manifest.json` 참조. 원본 texture73개와 정확한 Material→slot→texture104개 연결, UV scale/offset·색공간·필터·wrap 메타데이터가 있다. 이 정보와 실제 컴파일 코드를 함께 사용해야 한다. 게임 프로젝트는 이번 분석에서 수정하지 않았다.
