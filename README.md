# Warsztat Menager Mobile — WMM

**Warsztat Menager Mobile (WMM)** to aplikacja Android przeznaczona do pracy bezpośrednio z Warsztat Menager przez lokalne WM API. Telefon nie otwiera plików `WM_ROOT` samodzielnie — wszystkie odczyty i zapisy przechodzą przez kontrolowane API programu WM.

Repozytorium techniczne na razie nadal ma nazwę `edwinkarolczyk/Cidex-Mobile`; można je później przemianować na `Warsztat-Menager-Mobile` bez zmiany założeń aplikacji. Stary backend CIDEX pozostaje tylko jako przejściowa kompatybilność podczas migracji do WM API.

## Aktualny zakres v0.5

- branding **Warsztat Menager Mobile / WMM**,
- ciemny motyw zgodny z WM: grafit/czerń + pomarańczowy akcent,
- połączenie z komputerem przez Wi‑Fi/LAN,
- skanowanie QR połączenia z WM zamiast ręcznego przepisywania hosta i klucza,
- zachowanie ręcznego adresu/klucza jako opcji awaryjnej,
- Planista: podgląd i dodanie zlecenia,
- Maszyny: lista, wyszukiwanie, karta, QR, statusy, uwaga, serwis/awaria,
- Maszyny: zdjęcia z aparatu lub galerii i podgląd zdjęć z WM,
- Narzędzia: lista, karta, statusy i obsługa zdjęć przygotowana pod WM API,
- Dyspozycje: mobilny podgląd przygotowany pod WM API,
- Magazyn: mobilny podgląd stanów przygotowany pod WM API,
- brak mobilnej zakładki historii — WMM pokazuje tylko dane potrzebne na hali.

## Docelowa architektura

```text
Warsztat Menager Mobile (WMM)
        |
        | Wi-Fi / LAN
        v
WM API uruchomione przez Warsztat Menager
        |
        v
WM_ROOT/data
```

WMM nie ma własnej bazy będącej źródłem prawdy. Połączenie z WM ma być zestawiane przez QR generowany na komputerze, np.:

```text
WMM://CONNECT?host=192.168.1.50&port=8765&key=AB12CD
```

Telefon odczytuje host, port i klucz automatycznie. Użytkownik nie musi wpisywać tokenów ani adresu ręcznie.

## Kompatybilność przejściowa

Do czasu wdrożenia WM API aplikacja wysyła dwa nagłówki z tym samym kluczem:

```text
X-WMM-Key
X-Cidex-Token
```

Pierwszy jest docelowy dla WM. Drugi pozwala nadal testować funkcje Maszyn/Planisty na obecnym backendzie CIDEX podczas migracji. Po uruchomieniu kompletnego WM API nagłówek CIDEX będzie można usunąć.

## Zdjęcia — priorytet WMM

Zdjęcia są jedną z głównych funkcji aplikacji. Docelowy przepływ:

```text
WMM
 -> wybór / QR maszyny albo narzędzia
 -> aparat lub galeria
 -> kompresja po stronie telefonu
 -> WM API
 -> właściwy katalog/rekord w WM_ROOT
 -> natychmiastowy podgląd w WM i WMM
```

WMM nie zapisuje zdjęć bezpośrednio do udziału sieciowego. O właściwe miejsce, nazwę pliku i powiązanie z obiektem odpowiada WM API.

## Zakres mobilny

WMM ma obejmować funkcje potrzebne pracownikowi i brygadziście na hali, a nie kopiować cały desktopowy WM.

W aplikacji pozostają przede wszystkim:

- Maszyny,
- Narzędzia,
- Zlecenia / Planista,
- Dyspozycje,
- Magazyn w uproszczonym zakresie,
- QR,
- zdjęcia,
- statusy,
- proste uwagi i operacje wykonawcze.

Nie przenosimy do telefonu pełnej historii, ciężkiej administracji systemowej ani technicznych ekranów konfiguracji.

## Build APK

```bat
scripts\build_apk.bat
```

Po udanym buildzie powstaje:

```text
WMM.apk
```

GitHub Actions publikuje artefakt `WMM-apk`.

## Instalacja przez USB

```bat
scripts\install_phone.bat
```

## Najbliższy krok po stronie WM

Żeby całkowicie odłożyć CIDEX PC, Warsztat Menager musi dostać własny mały serwer API uruchamiany razem z WM. Powinien wystawić ten sam kontrakt `/api/v1/...`, który konsumuje WMM, oraz ekran z hostem i QR połączenia. To jest osobny zakres zmian w repo WM i powinien zostać wykonany dopiero po osobnej akceptacji zmian w kodzie WM.
