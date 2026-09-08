@echo off
setlocal EnableExtensions
title CIDEX Mobile - BUILD APK

cd /d "%~dp0\.."

set "FLUTTER=flutter"
where flutter >nul 2>&1
if errorlevel 1 (
  if exist "%USERPROFILE%\dev\flutter\bin\flutter.bat" (
    set "FLUTTER=%USERPROFILE%\dev\flutter\bin\flutter.bat"
  ) else (
    echo [BLAD] Brak Flutter SDK.
    echo Uruchom najpierw scripts\setup_windows.bat
    pause
    exit /b 1
  )
)

if not exist "android\" (
  echo Projekt Android nie jest przygotowany.
  call "scripts\prepare_project.bat"
  if errorlevel 1 exit /b 1
)

echo ================================================
echo   CIDEX Mobile - BUILD APK DEMO
echo ================================================
echo.

call "%FLUTTER%" pub get
if errorlevel 1 goto :fail

call "%FLUTTER%" build apk --debug
if errorlevel 1 goto :fail

set "APK=build\app\outputs\flutter-apk\app-debug.apk"
if not exist "%APK%" goto :fail

copy /Y "%APK%" "Cidex_Mobile_demo.apk" >nul

echo.
echo ================================================
echo GOTOWE:
echo   %CD%\Cidex_Mobile_demo.apk
echo ================================================
echo.
pause
exit /b 0

:fail
echo.
echo [BLAD] Build APK nie powiodl sie.
echo Uruchom flutter doctor -v i sprawdz komunikaty powyzej.
pause
exit /b 1
