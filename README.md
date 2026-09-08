# CIDEX Mobile

Pierwsza wersja demonstracyjna interfejsu mobilnego dla Androida.

## Zasady

- CIDEX Mobile jest osobnym projektem od Warsztat Menager.
- Nie zmienia konstrukcji ani kodu WM.
- Docelowo komunikuje się z CIDEX PC przez lokalne API.
- WM pozostaje właścicielem danych w `WM_ROOT`.
- Na obecnym etapie aplikacja działa w trybie DEMO i nie zapisuje niczego do WM.

## Co zawiera demo v0.1

- ciemny, kolorowy interfejs zgodny z zaakceptowanym kierunkiem,
- ekran główny z dużymi kaflami,
- Planista z przykładowymi zleceniami,
- ekran skanowania QR w trybie demonstracyjnym,
- lista maszyn,
- karta `Maszyna 42 — BLELL`,
- przyciski: Dodaj zdjęcie, Zgłoś awarię, Dodaj uwagę, Serwis / przegląd,
- podgląd aktualnych wartości z WM w wersji demonstracyjnej,
- oznaczenie autora `Cidex`.

QR, aparat, zdjęcia i połączenie z prawdziwym CIDEX API będą podpinane po zatwierdzeniu UI na telefonie/emulatorze.

## Najprostszy test na Windows + emulator Android

1. Pobierz repozytorium:

```bat
git clone https://github.com/edwinkarolczyk/Cidex-Mobile.git
cd Cidex-Mobile
```

2. Uruchom:

```bat
scripts\setup_windows.bat
```

3. Uruchom Android Studio przynajmniej raz i w `Device Manager` utwórz emulator, np. Pixel 7 z aktualnym obrazem Androida.

4. Przygotuj projekt Flutter:

```bat
scripts\prepare_project.bat
```

5. Uruchom emulator i aplikację:

```bat
scripts\run_emulator.bat
```

## Build APK

```bat
scripts\build_apk.bat
```

Po udanym buildzie w katalogu głównym pojawi się:

```text
Cidex_Mobile_demo.apk
```

## Instalacja na telefonie przez USB

Włącz w Androidzie `Opcje programistyczne -> Debugowanie USB`, podłącz telefon i uruchom:

```bat
scripts\install_phone.bat
```

## Jak emulator będzie łączył się z CIDEX PC

W emulatorze Androida adres `localhost` oznacza sam emulator. Aby połączyć się z usługą uruchomioną na komputerze-hostcie, użyj specjalnego adresu:

```text
http://10.0.2.2:8000
```

Przykład docelowy:

```text
CIDEX Mobile (emulator)
    -> http://10.0.2.2:8000
    -> CIDEX API na PC
    -> WM_ROOT
```

Na prawdziwym telefonie w tej samej sieci Wi-Fi zamiast `10.0.2.2` używa się adresu LAN komputera, np. `http://192.168.1.50:8000`.

## GitHub Actions

Workflow `Build demo APK` buduje wersję demonstracyjną automatycznie. Gotowy plik znajduje się w artefaktach uruchomienia workflow jako `Cidex-Mobile-demo-apk`.
