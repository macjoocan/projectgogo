"""levelscope — 퍼즐 게임 레벨 데이터 추출·요약·시각화 파이프라인.

설정(YAML)으로 게임별 인코딩·필드 구조를 정의하고,
게임 고유 로직은 plugins/<이름>.py 로 확장한다.

사용:
    python -m levelscope run --config configs/pixelflow.yaml --input <apk|xapk|folder> --out out/
"""
__version__ = "1.22.1"
