@echo off
setlocal EnableExtensions
title Warsztat Menager Mobile - BUILD APK

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

echo ================================================
echo   WMM - WARSZTAT MENAGER MOBILE - BUILD APK
echo ================================================
echo.

if not exist "android\" (
  echo [1/6] Generowanie projektu Android...
  call "%FLUTTER%" create --platforms=android --org pl.cidex --project-name cidex_mobile .
  if errorlevel 1 goto :fail
) else (
  echo [1/6] Projekt Android jest gotowy.
)

echo [2/6] Wgrywanie aktualnych zrodel WMM...
python "scripts\apply_sources.py"
if errorlevel 1 goto :fail
python "scripts\apply_wmm_login.py"
if errorlevel 1 goto :fail

echo [3/6] Nazwa, ikona i uprawnienia Android...
python "scripts\patch_android.py"
if errorlevel 1 goto :fail

echo [4/6] Zaleznosci...
call "%FLUTTER%" pub get
if errorlevel 1 goto :fail

echo [5/6] Analiza kodu...
call "%FLUTTER%" analyze lib\main.dart test\widget_test.dart
if errorlevel 1 goto :fail

echo [6/6] Budowanie APK debug...
call "%FLUTTER%" build apk --debug
if errorlevel 1 goto :fail

set "APK=build\app\outputs\flutter-apk\app-debug.apk"
if not exist "%APK%" goto :fail

copy /Y "%APK%" "WMM.apk" >nul

echo.
echo ================================================
echo GOTOWE:
echo   %CD%\WMM.apk
echo ================================================
echo.
pause
exit /b 0

:fail
echo.
echo [BLAD] Build WMM APK nie powiodl sie.
echo Uruchom flutter doctor -v i sprawdz komunikaty powyzej.
pause
exit /b 1
