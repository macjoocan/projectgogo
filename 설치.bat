@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem  levelscope 최초 1회 설치

where py >/dev/null 2>&1 && (set PY=py) || (set PY=python)

echo.
echo   필요한 패키지를 설치합니다. 몇 분 걸릴 수 있습니다.
echo.
%PY% -m pip install -r requirements.txt
echo.
echo   Addressables 바이너리 카탈로그 해독용 (선택, 없어도 동작)
%PY% -m pip install addressablestools

echo.
echo   설치 확인:
%PY% -c "import UnityPy, PIL; print('  UnityPy', UnityPy.__version__, '/ Pillow OK')"
%PY% -m unittest discover -s tests -t . 2>&1 | findstr /C:"Ran " /C:"OK" /C:"FAILED"

echo.
echo   끝났습니다. 이제 분석하기.bat 에 apk 를 끌어다 놓으세요.
pause
