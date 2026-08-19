# plugins/ — 프로젝트 전용 플러그인 자리

여기는 **레포를 고치지 않고 게임 플러그인을 추가하는 자리**다. 비워둬도 된다.

기본 제공 플러그인은 패키지 안에 하나만 있다:

    levelscope/plugins/pixelflow.py     슈터 대기열 (level_extras + entities + viewer_level)
    levelscope/plugins/zenmatch.py      타일 스택 (board + level_extras + viewer_level)

v1.3까지는 같은 파일이 `plugins/` 와 `levelscope/plugins/` 양쪽에 복사돼 있어서
"두 벌을 손으로 맞춰야" 했다. v1.4에서 패키지 안 한 벌로 정리했다.

## 새 플러그인 추가

`configs/<게임>.yaml` 의 `plugin: <이름>` 이 아래 순서로 찾는다.

1. `levelscope/plugins/<이름>.py`  (패키지 내장 — 배포에 포함할 것)
2. `plugins/<이름>.py`             (이 폴더 — 로컬/실험용)

구현할 함수는 전부 선택이다. 없으면 xlsx/HTML/zip 기본 산출물은 그대로 나온다.

```python
ENTITY_SHEET = {"name": "Shooters", "headers": [...]}   # entities 를 쓸 때만 필수

def level_extras(data) -> dict:           # Levels 시트 추가 컬럼
def entities(set_name, level, data) -> list[tuple]      # 엔티티 시트 행
def board(data) -> dict | None            # 보드 렌더를 직접 만들 때 (schema.board 대체)
def viewer_level(data) -> dict            # 뷰어 상세 (ma/sq, tiles 모드는 tl/lc/tw/th)
```

자세한 규격은 `MANUAL.md` 5장.
