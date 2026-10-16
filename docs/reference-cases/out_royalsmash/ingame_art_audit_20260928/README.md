# Royal Smash 인게임 아트 원본 조사 / 2026-09-28

이 폴더는 원본 APK와 기존에 보관된 번들의 정적 추출·코드 판독 결과다. Unity 이식의 실기 동작/화면 일치 여부는 별도 검증 사항이다.

## 읽는 순서

1. [머티리얼 저장값 답신](../mailbox/to-claude/20260928-ingame-art-part1-materials-bmul94s75-f.md): 이름 기준 40종/실제 43개, 노드·슬롯별 참조와 동명 구분.
2. [셰이더 수식 답신](../mailbox/to-claude/20260928-ingame-art-part2-shaders-bmul94s75-f.md), [수식 본문](shader_equations.md): 저장 키워드 조합과 대표 원작 GLSL.
3. [배경·조명·카메라 답신](../mailbox/to-claude/20260928-ingame-art-part34-environment-bmul94s75-f.md): 난이도별 배경 분기, 지면 그림자 합성, 대포 변형, 광원 회전, URP와 색 공간.
4. [HUD 답신](../mailbox/to-claude/20260928-ingame-art-part5-hud-bmul94s75-f.md): 두 부스터·발사 수·설정·팝업, Sprite 85장과 난이도 팔레트.
5. [검증 결과](handoff_validation.json): 정적 참조/PNG/메시/JSON 검사 및 한계.

## 데이터 사용 규칙

- `[원작값]` 저장 필드, `[원작 코드 판독]` 원작 명령/GLSL 판독, `[자체]` 계산 또는 추정. 저장값을 현재 런타임의 값으로 자동 승격하지 않는다.
- 에셋 식별은 file + pathID 또는 문자열 asset_key. 이름만으로 합치지 않는다. 64비트 ID를 JavaScript Number로 읽지 않는다.
- Mesh native 배열은 Unity 로컬 좌표. X 반전, 삼각형 역순, 재중심화, 부모 scale bake를 하지 않았다.
- Sprite PNG는 아틀라스의 잘린 영역일 수 있다. 원본 rect/pivot/border/PPU와 패킹 메타데이터를 함께 사용한다. Sprite 원시 UV와 Atlas 변환값을 구별한다.
- `nonfinite_values.json`에 원본 Infinity/NaN의 파일/경로를 기록했다. JSON 표준을 위해 해당 값만 문자열로 표기했다. 원본 에셋은 바꾸지 않았고 임의의 0으로 대체하지 않았다.
- 완전 판독하지 못한 MonoBehaviour, URP/PlayerSettings, 런타임 수면·애니메이션은 각 문서의 한계를 따른다.

추출기/검증기는 한 단계 위 `audit_ingame_scene_ui_20260928.py`, `audit_ingame_backgrounds_20260928.py`, `export_ingame_art_assets_20260928.py`, `export_ingame_hud_20260928.py`, `extract_environment_shaders_20260928.py`, `validate_ingame_art_handoff_20260928.py`다. 재추출 후에는 검증기를 다시 실행해 JSON의 비유한 수 표기를 정규화한다.
