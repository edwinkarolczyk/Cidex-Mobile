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

echo ================================================
echo   CIDEX Mobile - BUILD APK
echo ================================================
echo.

if not exist "android\" (
  echo [1/6] Generowanie projektu Android...
  call "%FLUTTER%" create --platforms=android --org pl.cidex --project-name cidex_mobile .
  if errorlevel 1 goto :fail
) else (
  echo [1/6] Projekt Android jest gotowy.
)

echo [2/6] Wgrywanie aktualnych zrodel CIDEX Mobile...
if not exist "lib" mkdir "lib"
copy /Y "template\main.dart" "lib\main.dart" >nul
copy /Y "template\pubspec.yaml" "pubspec.yaml" >nul

echo [3/6] Uprawnienia Android...
python "scripts\patch_android.py"
if errorlevel 1 goto :fail

echo [4/6] Zaleznosci...
call "%FLUTTER%" pub get
if errorlevel 1 goto :fail

echo [5/6] Analiza kodu...
call "%FLUTTER%" analyze
if errorlevel 1 goto :fail

echo [6/6] Budowanie APK debug...
call "%FLUTTER%" build apk --debug
if errorlevel 1 goto :fail

set "APK=build\app\outputs\flutter-apk\app-debug.apk"
if not exist "%APK%" goto :fail

copy /Y "%APK%" "Cidex_Mobile.apk" >nul

echo.
echo ================================================
echo GOTOWE:
echo   %CD%\Cidex_Mobile.apk
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
