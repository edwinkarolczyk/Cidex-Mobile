@echo off
setlocal EnableExtensions
title Warsztat Menager Mobile - przygotowanie Windows

echo ================================================
echo   WMM - Flutter + Android
echo ================================================
echo.

where winget >nul 2>&1
if errorlevel 1 (
  echo [BLAD] Nie znaleziono winget.
  echo Zainstaluj App Installer z Microsoft Store i uruchom BAT ponownie.
  pause
  exit /b 1
)

echo [1/4] Git...
where git >nul 2>&1
if errorlevel 1 (
  winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
  set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
) else (
  echo Git jest juz zainstalowany.
)

echo.
echo [2/4] Android Studio...
winget list --id Google.AndroidStudio -e >nul 2>&1
if errorlevel 1 (
  winget install --id Google.AndroidStudio -e --accept-package-agreements --accept-source-agreements
) else (
  echo Android Studio jest juz zainstalowane.
)

echo.
echo [3/4] Flutter SDK...
set "FLUTTER_DIR=%USERPROFILE%\dev\flutter"
if not exist "%FLUTTER_DIR%\bin\flutter.bat" (
  if not exist "%USERPROFILE%\dev" mkdir "%USERPROFILE%\dev"
  git clone https://github.com/flutter/flutter.git -b stable "%FLUTTER_DIR%"
  if errorlevel 1 goto :fail
) else (
  echo Flutter juz istnieje: %FLUTTER_DIR%
)

set "PATH=%FLUTTER_DIR%\bin;%PATH%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=[Environment]::GetEnvironmentVariable('Path','User'); $f='%FLUTTER_DIR%\bin'; if([string]::IsNullOrWhiteSpace($p)){$p=$f}elseif(($p -split ';') -notcontains $f){$p=$p.TrimEnd(';')+';'+$f}; [Environment]::SetEnvironmentVariable('Path',$p,'User')"

echo.
echo [4/4] Flutter Doctor...
call "%FLUTTER_DIR%\bin\flutter.bat" doctor -v

echo.
echo ================================================
echo JESLI ANDROID SDK NIE JEST GOTOWY:
echo 1. Uruchom Android Studio.
echo 2. Wejdz: More Actions ^> SDK Manager.
echo 3. Zainstaluj Android SDK, Platform-Tools i Command-line Tools.
echo 4. Wejdz: Device Manager i utworz emulator, np. Pixel 7.
echo 5. Potem uruchom w nowym oknie CMD:
echo    flutter doctor --android-licenses
echo    i zaakceptuj wszystko Y.
echo ================================================
echo.
pause
exit /b 0

:fail
echo.
echo [BLAD] Nie udalo sie przygotowac srodowiska WMM.
pause
exit /b 1
