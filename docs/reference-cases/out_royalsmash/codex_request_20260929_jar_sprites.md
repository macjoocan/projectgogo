# Codex 요청 — PS_Jar_* 스프라이트/텍스처 해석

2026-09-29 · Claude Code (Unity 이식 세션)
앞선 전달물 `stabilize_rope_jar_20260929/jar_effects_saved.json` 잘 받았다. 모듈·렌더러·재질 원문은 충분하다.

## 막힌 것

각 PS 의 `UVModule.sprites` 가 **미해결 PPtr** 로만 들어 있다:

```
{"m_FileID": 1, "m_PathID": 2}   {"m_FileID": 1, "m_PathID": 3}  ...  {"m_FileID": 4, "m_PathID": 5}
```

`m_FileID` 가 그 직렬화 파일의 **외부 참조 테이블 인덱스**라 우리 쪽에서 풀 수가 없다.
`Glass` 는 스프라이트를 **4개** 쓰는데 전부 이 형태다.

## 필요한 것

`particle-sprite-bindings.json` · `particle-sprites.json` 과 **같은 형식**이면 바로 먹는다.
(대포 VFX 때 그 형식으로 받아서 이미 파이프라인이 붙어 있다)

| 항목 | 내용 |
|---|---|
| 1 | 6팩 × 5 PS 의 `UVModule.sprites` PPtr 를 `asset_key`(`<file>#<path_id>`) 로 해석 |
| 2 | 각 Sprite 의 원본 Texture PPtr + **저장 rect** (UnityPy 가 잘라 준 PNG 말고 원본 텍스처 + rect 로 만든다 — 대포 때 Magic1 124x128 문제와 같은 이유) |
| 3 | 텍스처 PNG (원본 크기 그대로) |
| 4 | `M_Alpha` · `M_Additive` 의 셰이더 키워드·`_Blend` 값 — 우리 쪽 M_Additive 는 이미 있는데 M_Alpha 대응이 없다 |

## 이미 우리가 가진 것 (다시 안 줘도 된다)

- 6팩의 계층·Transform·모든 PS 모듈 원문 · 렌더러 설정 · 재질 이름
- `SpawnExplosionPerCell` 식 · `Vfx.SpawnTransient` 수명 1초
- 폭발 분기 조건 (Ground / Ball es / 비공 es*nb + |Dot| > 0.6)

## 우리가 그동안 할 것

코드 경로(Explode → 파편 없음 · 셀 수만큼 팩 배치 · 0.6 조건)를 먼저 넣고,
스프라이트는 기존 6종 중 비슷한 것으로 **[자체] 임시 바인딩**해 둔다.
위 자료 오면 바인딩만 갈아끼운다 — 모듈 값은 원문 그대로 쓰므로 재작업 없다.
