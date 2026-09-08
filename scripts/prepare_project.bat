@echo off
setlocal EnableExtensions
title CIDEX Mobile - przygotowanie projektu

cd /d "%~dp0\.."

set "FLUTTER=flutter"
where flutter >nul 2>&1
if errorlevel 1 (
  if exist "%USERPROFILE%\dev\flutter\bin\flutter.bat" (
    set "FLUTTER=%USERPROFILE%\dev\flutter\bin\flutter.bat"
  ) else (
    echo [BLAD] Nie znaleziono Flutter SDK.
    echo Najpierw uruchom scripts\setup_windows.bat
    pause
    exit /b 1
  )
)

echo ================================================
echo   CIDEX Mobile - generowanie projektu Android
echo ================================================
echo.

if not exist "android\" (
  echo [1/3] Generowanie plikow platformy Android...
  call "%FLUTTER%" create --platforms=android --org pl.cidex --project-name cidex_mobile .
  if errorlevel 1 goto :fail
) else (
  echo [1/3] Folder android juz istnieje - pomijam generowanie.
)

echo [2/3] Wgrywanie interfejsu CIDEX Mobile...
if not exist "lib" mkdir "lib"
copy /Y "template\main.dart" "lib\main.dart" >nul
copy /Y "template\pubspec.yaml" "pubspec.yaml" >nul

echo [3/3] Pobieranie zaleznosci...
call "%FLUTTER%" pub get
if errorlevel 1 goto :fail

echo.
echo ================================================
echo GOTOWE.
echo Teraz uruchom: scripts\run_emulator.bat
echo ================================================
echo.
pause
exit /b 0

:fail
echo.
echo [BLAD] Przygotowanie projektu nie powiodlo sie.
pause
exit /b 1
