@echo off
setlocal EnableExtensions
title Warsztat Menager Mobile - przygotowanie projektu

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
echo   WMM - przygotowanie Android
echo ================================================
echo.

if not exist "android\" (
  echo [1/4] Generowanie plikow platformy Android...
  call "%FLUTTER%" create --platforms=android --org pl.cidex --project-name cidex_mobile .
  if errorlevel 1 goto :fail
) else (
  echo [1/4] Folder android juz istnieje - pomijam generowanie.
)

echo [2/4] Wgrywanie aktualnych zrodel WMM...
python "scripts\apply_sources.py"
if errorlevel 1 goto :fail

echo [3/4] Ustawianie nazwy, ikony, INTERNET, CAMERA i lokalnego HTTP...
python "scripts\patch_android.py"
if errorlevel 1 goto :fail

echo [4/4] Pobieranie zaleznosci...
call "%FLUTTER%" pub get
if errorlevel 1 goto :fail

echo.
echo ================================================
echo GOTOWE.
echo Emulator: serwer WMM = http://10.0.2.2:8765
echo Token 6 znakow wpisz w ustawieniach aplikacji.
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
