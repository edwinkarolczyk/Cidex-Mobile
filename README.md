# Cidex Mobile

Pierwszy pionowy szkielet aplikacji mobilnej Cidex do obsługi danych Warsztat Menager przez API.

## Stan

- Flutter / Android,
- ciemny interfejs dopasowany do Cidex,
- ekran konfiguracji adresu API i tokenu,
- Planista: lista aktualnych zleceń,
- Maszyny: lista, karta maszyny, status, hala/lokalizacja,
- Skan QR maszyny,
- Zgłoszenie awarii / serwisu,
- Dodawanie uwagi,
- Zdjęcia z aparatu lub galerii,
- współpraca z `Cidex_Api.exe` / `cidex_api.py` z repo Warsztat-Menager.

## Endpointy używane przez aplikację

- `GET /api/v1/info`
- `GET /api/v1/planista/orders`
- `GET /api/v1/machines`
- `GET /api/v1/machines/{id}`
- `GET /api/v1/qr/resolve?code=...`
- `POST /api/v1/machines/{id}/status`
- `POST /api/v1/machines/{id}/note`
- `POST /api/v1/machines/{id}/photos`
- `GET /api/v1/media/machines/{id}/{plik}`

Nagłówek autoryzacji:

```text
X-Cidex-Token: <token>
```

## Uruchomienie na Windows

Najprościej uruchomić:

```bat
scripts\setup_windows.bat
```

Skrypt instaluje / sprawdza Git, Android Studio i Flutter SDK, a na końcu uruchamia `flutter doctor -v`.

Po instalacji otwórz Android Studio i dokończ Android SDK oraz emulator, jeśli `flutter doctor` pokaże braki.

Następnie:

```bat
scripts\prepare_project.bat
```

Skrypt utworzy platformę Android i wgra aktualne pliki z `template/` do projektu Flutter.

## Emulator Android

Po utworzeniu AVD w Android Studio (`Device Manager`) uruchom:

```bat
scripts\run_emulator.bat
```

Skrypt:

1. przygotuje projekt Android,
2. uruchomi pierwszy dostępny emulator AVD,
3. poczeka na start Androida,
4. uruchomi Cidex Mobile przez `flutter run`.

W emulatorze API uruchomione na tym samym komputerze jest dostępne pod:

```text
http://10.0.2.2:8765
```

## Fizyczny telefon

Telefon i komputer muszą być w tej samej sieci LAN / Wi-Fi.

Adres API na telefonie ustaw jako:

```text
http://IP_KOMPUTERA:8765
```

Na przykład:

```text
http://192.168.1.50:8765
```

Windows Firewall musi przepuszczać port 8765 dla sieci prywatnej.

## Budowanie APK lokalnie

```bat
scripts\build_apk.bat
```

Po sukcesie APK znajdziesz w:

```text
build\app\outputs\flutter-apk\app-release.apk
```

Skrypt kopiuje też plik do:

```text
dist\cidex-mobile.apk
```

## Instalacja przez ADB

Przy podłączonym telefonie z włączonym debugowaniem USB:

```bat
scripts\install_phone.bat
```

## GitHub Actions

Workflow `Build Cidex Mobile APK` buduje APK po każdym pushu na `main` i pozwala pobrać artefakt `cidex-mobile-apk` z zakładki Actions.
