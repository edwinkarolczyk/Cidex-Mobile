# CIDEX Mobile

CIDEX Mobile to osobna aplikacja Android współpracująca z programem CIDEX na komputerze. Nie zmienia kodu ani konstrukcji Warsztat Menager i nie otwiera bezpośrednio plików `WM_ROOT` z telefonu.

## Aktualny zakres v0.3

- zaakceptowany ciemny, kolorowy interfejs z dużymi zaokrąglonymi kaflami,
- połączenie z lokalnym `CIDEX API`,
- zapamiętanie adresu API i tokenu na telefonie,
- Planista — podgląd aktualnych zleceń z WM,
- Planista — dodawanie nowego zlecenia z telefonu,
- produkt wybierany z aktualnej kartoteki produktów WM,
- walidacja Zlecenia wew, produktu i ilości przed zapisem,
- opcjonalna data wysyłki z kalendarza i uwagi,
- Maszyny — aktualna lista i wyszukiwarka,
- skanowanie prawdziwych kodów QR aparatem,
- ręczne wpisanie ID / treści QR do testów w emulatorze,
- otwarcie karty maszyny na podstawie istniejącego ID WM,
- podgląd statusu, hali, lokalizacji i terminu przeglądu,
- `Dodaj zdjęcie` — aparat lub galeria,
- `Zgłoś awarię` — wymagany opis,
- `Dodaj uwagę`,
- `Serwis / przegląd` — wymagany opis,
- `Oznacz jako sprawną`,
- podgląd zdjęć zapisanych przy maszynie,
- autor zapisów mobilnych: `Cidex`.

Zlecenia, zdjęcia i zmiany nie są zapisywane w telefonie jako osobny model danych. Aplikacja wysyła operację do CIDEX na komputerze, a CIDEX zapisuje ją zgodnie z istniejącą strukturą WM.

Nowe zlecenie z telefonu korzysta z tego samego bezpiecznego mechanizmu `add_order` co CIDEX PC. CIDEX nie tworzy przy tym rezerwacji materiałowych, nie zmienia magazynu i nie tworzy nowych pól w modelu WM.

## Przepływ

```text
CIDEX Mobile (Android)
        |
        | Wi-Fi / LAN
        v
CIDEX API na komputerze
        |
        v
WM_ROOT/data
```

## Planista — dodanie zlecenia z telefonu

W ekranie `Planista` użyj pomarańczowego przycisku `DODAJ ZLECENIE`.

Formularz zawiera:

- `Zlecenie wew` — wymagane,
- `Produkt` — wymagany, wybierany z bieżącej kartoteki WM,
- `Ilość` — wymagana, większa od zera,
- `Data wysyłki` — opcjonalna,
- `Uwagi` — opcjonalne.

Przy najważniejszych polach jest kontekstowa pomoc. Po poprawnym zapisie lista Planisty jest odświeżana, a wpis w historii zlecenia ma autora `Cidex`.

## 1. Przygotowanie CIDEX na komputerze

W repo `edwinkarolczyk/Cidex`:

```bat
git pull
run.bat
```

W zwykłym CIDEX ustaw poprawny `WM_ROOT`. Potem uruchom:

```bat
run_api.bat
```

Serwer pokaże m.in. adres telefonu i token:

```text
Emulator Android: http://10.0.2.2:8765
Telefon w LAN:    http://192.168.x.x:8765
Token:            ...
```

Przy pytaniu Zapory systemu Windows zezwalaj wyłącznie dla sieci prywatnych / firmowych.

## 2. Emulator Android

```bat
git clone https://github.com/edwinkarolczyk/Cidex-Mobile.git
cd Cidex-Mobile
scripts\setup_windows.bat
scripts\prepare_project.bat
scripts\run_emulator.bat
```

W aplikacji wejdź w ikonę ustawień i wpisz:

```text
Adres: http://10.0.2.2:8765
Token: wartość pokazana przez CIDEX API
```

Naciśnij `TESTUJ POŁĄCZENIE`, następnie `ZAPISZ`.

Emulator może nie mieć wygodnego obrazu z prawdziwego aparatu, dlatego ekran QR ma też pole ręcznego testu. Można wpisać np.:

```text
CIDEX:MACHINE:42
```

albo samo:

```text
42
```

## 3. Prawdziwy telefon Android

Telefon i komputer muszą być w tej samej sieci Wi-Fi/LAN. W ustawieniach aplikacji zamiast `10.0.2.2` wpisz adres LAN pokazany przez `run_api.bat`, np.:

```text
http://192.168.1.50:8765
```

Wtedy działa prawdziwy aparat QR, robienie i wysyłanie zdjęć oraz zapis zleceń Planisty przez CIDEX API.

## Kod QR maszyny

CIDEX używa istniejącego identyfikatora maszyny z WM. Zalecana treść QR:

```text
CIDEX:MACHINE:42
```

Nie jest tworzony nowy identyfikator maszyny. Dla kompatybilności API rozpoznaje też m.in. samo `42` i `cidex://machine/42`.

## Build APK

```bat
scripts\build_apk.bat
```

Po udanym buildzie:

```text
Cidex_Mobile.apk
```

Build zawsze kopiuje aktualne pliki z `template/`, ustawia uprawnienia `INTERNET` i `CAMERA`, wykonuje analizę i test, a dopiero potem buduje APK.

## Instalacja przez USB

Włącz `Opcje programistyczne -> Debugowanie USB`, podłącz telefon i uruchom:

```bat
scripts\install_phone.bat
```

## GitHub Actions

Workflow `Build CIDEX Mobile APK` automatycznie:

1. tworzy projekt Android,
2. składa aktualne źródła aplikacji,
3. dodaje wymagane uprawnienia,
4. pobiera zależności,
5. wykonuje `flutter analyze`,
6. wykonuje testy Flutter,
7. buduje debug APK,
8. publikuje artefakt `Cidex-Mobile-apk` z plikiem `Cidex_Mobile.apk`.

## Bezpieczeństwo

- endpointy `/api/v1/...` wymagają tokenu `X-Cidex-Token`,
- telefon nie dostaje bezpośredniego dostępu do udziału z `WM_ROOT`,
- nowe zlecenie jest tworzone przez istniejący mechanizm CIDEX bez rezerwacji materiałowych,
- CIDEX nie usuwa automatycznie zleceń,
- zdjęcia są ograniczone rozmiarem po stronie CIDEX,
- zmiany statusu i zdjęcia używają istniejącego modelu Maszyn WM,
- Awaria i Serwis / przegląd wymagają opisu,
- autor zapisu to `Cidex`.

## Co pozostaje przed oznaczeniem 100% produkcyjnym

Kod, testy automatyczne i budowa APK mogą zostać zweryfikowane w CI. Ostatni etap odbioru wymaga testu na kopii aktualnego `WM_ROOT` oraz na rzeczywistym telefonie lub emulatorze połączonym z komputerem z CIDEX API. Dopiero po takim teście należy podłączać zapis do właściwych danych produkcyjnych WM.
