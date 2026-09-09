@echo off
setlocal EnableExtensions
title CIDEX Mobile - instalacja na telefon

cd /d "%~dp0\.."

if not exist "Cidex_Mobile.apk" (
  echo [BLAD] Brak Cidex_Mobile.apk.
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
echo Instalowanie CIDEX Mobile na telefonie...
"%ADB%" -d install -r "Cidex_Mobile.apk"

if errorlevel 1 (
  echo.
  echo [BLAD] Instalacja nie powiodla sie.
  echo Sprawdz Debugowanie USB i zaakceptuj klucz RSA na telefonie.
  pause
  exit /b 1
)

echo.
echo GOTOWE - CIDEX Mobile zainstalowany.
pause
