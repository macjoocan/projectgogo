@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem  apk / xapk 파일을 이 파일 위로 끌어다 놓으세요.
rem  (또는 더블클릭하고 경로를 붙여넣기)

rem --- 파이썬 고르기: .venv 를 우선 쓴다 -----------------------------
rem  주의: batch 에서 `if cond cmd1 && cmd2` 는 cmd2 가 조건과 무관하게
rem  실행된다. 그래서 아래처럼 괄호 블록으로 명확히 나눈다.
set "PY="
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    set "PY=py"
  ) else (
    where python >nul 2>&1
    if not errorlevel 1 set "PY=python"
  )
  echo   [i] 가상환경이 없어 시스템 파이썬을 씁니다.
  echo       설치.bat 을 먼저 돌리는 편이 안전합니다.
  echo.
)

if not defined PY (
  echo   [!] 파이썬을 찾을 수 없습니다. 먼저  설치.bat  을 실행하세요.
  pause
  exit /b 1
)

rem --- 입력 받기 -----------------------------------------------------
set "INPUT=%~1"
if not defined INPUT (
  echo.
  echo   apk / xapk 파일을 이 파일 위로 끌어다 놓으면 분석이 시작됩니다.
  echo.
  set /p "INPUT=  또는 경로를 붙여넣고 Enter: "
)
if not defined INPUT (
  echo   입력이 없어 종료합니다.
  pause
  exit /b 1
)

"%PY%" "tools/analyze.py" "%INPUT%"

echo.
pause
