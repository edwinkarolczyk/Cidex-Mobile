@echo off
setlocal EnableExtensions EnableDelayedExpansion
title CIDEX Mobile - emulator Android

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

if not exist "pubspec.yaml" (
  echo [BLAD] Projekt nie jest przygotowany.
  echo Uruchom najpierw scripts\prepare_project.bat
  pause
  exit /b 1
)

set "SDK=%LOCALAPPDATA%\Android\Sdk"
set "EMU=%SDK%\emulator\emulator.exe"
set "ADB=%SDK%\platform-tools\adb.exe"

if not exist "%EMU%" (
  where emulator >nul 2>&1
  if errorlevel 1 (
    echo [BLAD] Nie znaleziono emulator.exe.
    echo Otworz Android Studio ^> Device Manager i zainstaluj emulator Android.
    pause
    exit /b 1
  ) else (
    set "EMU=emulator"
  )
)

if not exist "%ADB%" (
  where adb >nul 2>&1
  if errorlevel 1 (
    echo [BLAD] Nie znaleziono adb.exe.
    echo Zainstaluj Android SDK Platform-Tools w Android Studio.
    pause
    exit /b 1
  ) else (
    set "ADB=adb"
  )
)

set "DEVICE="
for /f "tokens=1" %%D in ('"%ADB%" devices ^| findstr /B "emulator-"') do set "DEVICE=%%D"

if not defined DEVICE (
  set "AVD="
  for /f "usebackq delims=" %%A in (`"%EMU%" -list-avds`) do if not defined AVD set "AVD=%%A"

  if not defined AVD (
    echo [BLAD] Nie ma zadnego utworzonego emulatora AVD.
    echo.
    echo Otworz Android Studio ^> Device Manager ^> Create device.
    echo Polecany: Pixel 7 lub podobny, Android API 35 lub nowszy.
    echo Po utworzeniu zamknij Android Studio i uruchom ten BAT ponownie.
    pause
    exit /b 1
  )

  echo Uruchamiam emulator: !AVD!
  start "CIDEX Android Emulator" "%EMU%" -avd "!AVD!"
  echo Czekam na uruchomienie Androida...
  "%ADB%" wait-for-device

  :wait_boot
  for /f "delims=" %%B in ('"%ADB%" shell getprop sys.boot_completed 2^>nul') do set "BOOT=%%B"
  if not "!BOOT!"=="1" (
    timeout /t 2 /nobreak >nul
    goto :wait_boot
  )

  for /f "tokens=1" %%D in ('"%ADB%" devices ^| findstr /B "emulator-"') do set "DEVICE=%%D"
)

echo.
echo Emulator gotowy: %DEVICE%
echo Uruchamiam CIDEX Mobile...
echo.
call "%FLUTTER%" run -d %DEVICE%

if errorlevel 1 (
  echo.
  echo [BLAD] Flutter run zakonczyl sie bledem.
  pause
  exit /b 1
)

endlocal
