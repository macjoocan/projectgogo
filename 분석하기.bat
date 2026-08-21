@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem  levelscope 원 클릭 실행
rem  사용법: 이 파일에 apk / xapk 파일을 끌어다 놓으세요.
rem         (또는 더블클릭 후 경로를 입력)

where py >/dev/null 2>&1 && (set PY=py) || (set PY=python)

if "%~1"=="" (
  echo.
  echo   apk / xapk 파일을 이 파일 위로 끌어다 놓으면 분석이 시작됩니다.
  echo.
  set /p INPUT=  또는 여기에 경로를 붙여넣고 Enter: 
) else (
  set INPUT=%~1
)

if "%INPUT%"=="" (
  echo   입력이 없어 종료합니다.
  pause
  exit /b 1
)

%PY% toolsnalyze.py "%INPUT%"

echo.
pause
