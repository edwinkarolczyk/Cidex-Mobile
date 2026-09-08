@echo off
setlocal EnableExtensions
title CIDEX Mobile - instalacja na telefon

cd /d "%~dp0\.."

if not exist "Cidex_Mobile_demo.apk" (
  echo [BLAD] Brak Cidex_Mobile_demo.apk.
  echo Najpierw uruchom scripts\build_apk.bat
  pause
  exit /b 1
)

set "ADB=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
if not exist "%ADB%" (
  where adb >nul 2>&1
  if errorlevel 1 (
    echo [BLAD] Nie znaleziono adb.exe.
    echo Zainstaluj Android SDK Platform-Tools.
    pause
    exit /b 1
  ) else (
    set "ADB=adb"
  )
)

echo Podlaczone urzadzenia:
"%ADB%" devices
echo.
echo Instalowanie na fizycznym telefonie...
"%ADB%" -d install -r "Cidex_Mobile_demo.apk"

if errorlevel 1 (
  echo.
  echo [BLAD] Instalacja nie powiodla sie.
  echo Sprawdz Debugowanie USB i zaakceptuj klucz RSA na telefonie.
  pause
  exit /b 1
)

echo.
echo GOTOWE - CIDEX Mobile demo zainstalowany.
pause
