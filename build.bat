@echo off
setlocal
title Zametki - APK build
cd /d "%~dp0"

echo ================================================
echo   Zametki: APK build
echo ================================================
echo.

echo %~dp0 | find /i "\Temp\" >nul
if not errorlevel 1 (
  echo The project is running from inside the zip archive.
  echo Right-click the zip, choose "Extract All", then run build.bat from the extracted folder.
  echo.
  pause
  exit /b 1
)

set MODE=%~1
if "%MODE%"=="" set MODE=apk

where wsl >nul 2>nul
if %errorlevel% neq 0 goto :no_wsl

set CHK=
for /f "delims=" %%i in ('wsl bash -c "echo wsl-ok" 2^>nul') do set CHK=%%i
if not "%CHK%"=="wsl-ok" goto :no_distro

set WSLDIR=
for /f "delims=" %%i in ('wsl wslpath -a "%cd%" 2^>nul') do set WSLDIR=%%i
if not "%WSLDIR:~0,1%"=="/" goto :no_distro

echo Project folder: %WSLDIR%
echo Mode: %MODE%
echo The first build takes 20-40 minutes. Ubuntu may ask for your password.
echo.

wsl bash -c "tr -d '\r' < '%WSLDIR%/tools/wsl_build.sh' > /tmp/zametki_wsl_build.sh && bash /tmp/zametki_wsl_build.sh '%WSLDIR%' %MODE%"
if %errorlevel% neq 0 goto :failed

dir /b "%cd%\bin\*.apk" "%cd%\bin\*.aab" >nul 2>nul
if %errorlevel% neq 0 goto :failed

echo.
echo DONE. The APK is in the "bin" folder.
explorer "%cd%\bin"
pause
exit /b 0

:no_wsl
echo WSL is not installed.
echo.
echo Open PowerShell as Administrator and run:
echo     wsl --install -d Ubuntu
echo Restart the computer, create the Ubuntu user and password, then run build.bat again.
echo.
pause
exit /b 1

:no_distro
echo WSL is present, but no Linux distribution (Ubuntu) is installed or it is not ready.
echo.
echo Open PowerShell as Administrator and run:
echo     wsl --install -d Ubuntu
echo Restart the computer, open "Ubuntu" from the Start menu once, create a user and password,
echo then run build.bat again.
echo.
echo If this keeps failing, use the GitHub Actions route described in README.md.
echo.
pause
exit /b 1

:failed
echo.
echo BUILD FAILED or no APK was produced. Scroll up to see the error and send a screenshot of it.
echo.
pause
exit /b 1
