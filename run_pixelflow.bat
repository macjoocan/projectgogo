@echo off
rem PixelFlow 레벨 추출 — 입력 경로를 환경에 맞게 수정하세요
set INPUT=D:\99.기타\xapk_unpacked
py -m levelscope run --config "%~dp0configs\pixelflow.yaml" --input "%INPUT%" --out "%~dp0out"
pause
