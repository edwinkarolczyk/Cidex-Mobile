# Warsztat Menager Mobile — WMM

**Warsztat Menager Mobile (WMM)** to aplikacja Android dla Warsztat Menager. Repozytorium techniczne pozostaje `edwinkarolczyk/Cidex-Mobile`, a komunikacja z komputerem nadal odbywa się przez istniejący **CIDEX API** — zmieniony został branding, nazwa aplikacji i wygląd mobilny.

WMM nie zmienia kodu ani konstrukcji Warsztat Menager i nie otwiera bezpośrednio plików `WM_ROOT` z telefonu.

## Aktualny zakres v0.4

- nazwa aplikacji: **Warsztat Menager Mobile**,
- skrót w interfejsie: **WMM**,
- ciemny motyw zgodny z Warsztat Menager: czarne/grafitowe tło, pomarańczowy akcent i kolory tylko dla statusów,
- znak aplikacji w stylu WM: szare koło zębate + pomarańczowy klucz + ciemny element karty/serwisu,
- Planista — podgląd zleceń i dodawanie nowego zlecenia z telefonu,
- produkt wybierany z bieżącej kartoteki WM,
- Maszyny — lista, wyszukiwarka i karta maszyny,
- skan QR po istniejącym ID maszyny,
- dodawanie zdjęcia z aparatu lub galerii,
- zgłoszenie awarii, uwagi i serwisu/przeglądu,
- oznaczenie maszyny jako sprawnej,
- połączenie przez Wi-Fi/LAN z kontrolowanym API na komputerze.

## Architektura

```text
Warsztat Menager Mobile (WMM)
        |
        | Wi-Fi / LAN
        v
CIDEX API na komputerze
        |
        v
WM_ROOT/data
```

Repozytorium `Cidex-Mobile`, techniczny pakiet Flutter `cidex_mobile`, nagłówek `X-Cidex-Token` i backend CIDEX pozostają bez zmiany, żeby nie zrywać zgodności. W aplikacji użytkownik widzi nazwę **WMM / Warsztat Menager Mobile**.

## Token

CIDEX generuje dla WMM krótki token **6-znakowy**, np.:

```text
7K4M2P
```

Używane są duże litery i cyfry bez najbardziej mylących znaków. Po aktualizacji stary długi token zostanie jednorazowo zastąpiony nowym 6-znakowym kodem — trzeba wtedy wpisać nowy token w ustawieniach WMM.

## Uruchomienie po stronie komputera

W repo `edwinkarolczyk/Cidex`:

```bat
git pull
run.bat
```

W CIDEX ustaw poprawny `WM_ROOT`, a potem uruchom Mobile API z programu albo:

```bat
run_api.bat
```

Serwer pokaże adres telefonu oraz token.

## Telefon

Telefon i komputer muszą być w tej samej sieci Wi-Fi/LAN. W ustawieniach WMM wpisz adres komputera, np.:

```text
http://192.168.1.50:8765
```

oraz aktualny 6-znakowy token. Następnie użyj `TESTUJ POŁĄCZENIE` i `ZAPISZ`.

## QR maszyny

Techniczny format QR pozostaje zgodny z CIDEX:

```text
CIDEX:MACHINE:42
```

WMM rozpoznaje też samo ID, np. `42`. Nie jest tworzony nowy identyfikator maszyny.

## Build APK

```bat
scripts\build_apk.bat
```

Po udanym buildzie powstaje:

```text
WMM.apk
```

GitHub Actions publikuje artefakt **`WMM-apk`** z plikiem `WMM.apk`.

## Instalacja przez USB

```bat
scripts\install_phone.bat
```

Skrypt instaluje `WMM.apk` na podłączonym telefonie.

## Bezpieczeństwo i zgodność

- telefon nie dostaje bezpośredniego dostępu do udziału `WM_ROOT`,
- endpointy nadal wymagają technicznego nagłówka `X-Cidex-Token`,
- nowe zlecenia nie tworzą automatycznych rezerwacji materiałowych,
- CIDEX nie usuwa automatycznie zleceń,
- zdjęcia są ograniczone rozmiarem po stronie backendu,
- Awaria i Serwis / przegląd wymagają opisu,
- techniczny autor zapisu w danych WM pozostaje `Cidex`, aby zachować zgodność z istniejącym mechanizmem historii.

## Odbiór produkcyjny

Przed podłączeniem do właściwego `WM_ROOT` wykonaj pełny test na jego kopii: Planista, maszyna po QR, uwaga, awaria, serwis i zdjęcie. Kod WM pozostaje niezależny i nie jest przez WMM/CIDEX modyfikowany.
