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
echo   CIDEX Mobile - przygotowanie Android
echo ================================================
echo.

if not exist "android\" (
  echo [1/4] Generowanie plikow platformy Android...
  call "%FLUTTER%" create --platforms=android --org pl.cidex --project-name cidex_mobile .
  if errorlevel 1 goto :fail
) else (
  echo [1/4] Folder android juz istnieje - pomijam generowanie.
)

echo [2/4] Wgrywanie CIDEX Mobile...
if not exist "lib" mkdir "lib"
copy /Y "template\main.dart" "lib\main.dart" >nul
copy /Y "template\pubspec.yaml" "pubspec.yaml" >nul

echo [3/4] Ustawianie INTERNET, CAMERA i lokalnego HTTP...
python "scripts\patch_android.py"
if errorlevel 1 goto :fail

echo [4/4] Pobieranie zaleznosci...
call "%FLUTTER%" pub get
if errorlevel 1 goto :fail

echo.
echo ================================================
echo GOTOWE.
echo Emulator: CIDEX API = http://10.0.2.2:8765
echo Token wpisz w ustawieniach aplikacji.
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
