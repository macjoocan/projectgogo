@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==================================================================
echo   levelscope 설치  -  최초 1회만 실행하세요
echo ==================================================================
echo.

rem --- 1) 파이썬 찾기 -------------------------------------------------
rem  주의: batch 에서 `if cond cmd1 && cmd2` 는 cmd2 가 조건과 무관하게
rem  실행된다. 괄호 블록으로 나눈다.
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
  set "PY=py"
) else (
  where python >nul 2>&1
  if not errorlevel 1 set "PY=python"
)

if not defined PY (
  echo   [!] 파이썬이 없습니다.
  echo.
  echo       https://www.python.org/downloads/  에서 3.12 를 설치하세요.
  echo       설치 화면에서 "Add python.exe to PATH" 를 반드시 체크해야 합니다.
  echo       설치 후 이 창을 닫고 설치.bat 을 다시 실행하세요.
  echo.
  pause
  exit /b 1
)

"%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"
if errorlevel 1 (
  echo   [!] 파이썬 버전이 낮습니다. 3.9 이상이 필요합니다 ^(3.12 권장^).
  "%PY%" --version
  pause
  exit /b 1
)
for /f "delims=" %%v in ('"%PY%" --version') do echo   파이썬   : %%v

rem --- 2) 가상환경 ---------------------------------------------------
rem  시스템 파이썬을 건드리지 않도록 .venv 안에만 설치한다.
if exist ".venv\Scripts\python.exe" (
  echo   가상환경 : 이미 있음 ^(.venv^) - 패키지만 갱신합니다
) else (
  echo   가상환경 : .venv 를 만듭니다 ...
  "%PY%" -m venv .venv
  if errorlevel 1 (
    echo   [!] 가상환경 생성 실패. 위 메시지를 확인하세요.
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo   [!] .venv 가 만들어지지 않았습니다.
  pause
  exit /b 1
)
set "VPY=.venv\Scripts\python.exe"

rem --- 3) 패키지 -----------------------------------------------------
echo.
echo   패키지를 설치합니다. 처음이면 몇 분 걸립니다 ...
echo.
"%VPY%" -m pip install --upgrade pip --quiet
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo   [!] 설치 실패. 사내 프록시 환경이면 pip 프록시 설정이 필요할 수 있습니다.
  pause
  exit /b 1
)
echo.
echo   선택 패키지 ^(없어도 동작합니다^)
"%VPY%" -m pip install addressablestools

rem --- 4) 확인 -------------------------------------------------------
echo.
echo ------------------------------------------------------------------
echo   설치 확인
"%VPY%" -c "import UnityPy, PIL, pandas, yaml; print('   UnityPy', UnityPy.__version__, '/ Pillow / pandas / PyYAML  OK')"
"%VPY%" -m unittest discover -s tests -t . 2>&1 | findstr /C:"Ran " /C:"OK" /C:"FAILED"
echo ------------------------------------------------------------------
echo.
echo   끝났습니다.
echo   이제 apk / xapk 파일을  [ 분석하기.bat ]  위로 끌어다 놓으세요.
echo.
pause
