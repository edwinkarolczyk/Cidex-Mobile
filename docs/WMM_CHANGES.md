# WMM — zmiany bieżące

## 2026-09-25 — WMM 0.5.32

- Planista: dotknięcie zlecenia otwiera szczegóły półproduktów i ich operacji technologicznych.
- Operacje można oznaczać jako wykonane bezpośrednio z telefonu po potwierdzeniu.
- Zapis trafia do kanonicznego postępu Planisty WM; nie powstaje osobny stan lokalny WMM.
- Kolejność operacji jest pilnowana przez WM, a wykonania nie można cofnąć z telefonu.
- Ostatnia operacja aktualizuje wykonanie półproduktu zgodnie z regułami desktopowego WM.

## 2026-09-24 — WMM 0.5.31

- Zamknięte Dyspozycje wyświetlają się na końcu listy, także za rekordami o nierozpoznanym statusie.
- Filtr statusów: Wszystkie, Aktywne, Nowe, W toku, Wstrzymane i Zakończone.
- Ostatnio wybrany filtr jest przechowywany lokalnie w telefonie; pozostaje po odświeżeniu i ponownym uruchomieniu WMM.
- Bez zmian w statusach Dyspozycji w WM, danych produkcyjnych i API.

## 2026-09-10

- Dodano miniaturki zdjęć na listach Maszyn i Narzędzi.
- Dodano historię Maszyn i Narzędzi widoczną dla zalogowanego brygadzisty.
- WMM przekazuje `X-WMM-Session` przy zwykłych wywołaniach API, dzięki czemu WM może przypisać zmianę do zalogowanego użytkownika zamiast ogólnego autora `WMM`.
- Zmiany dotyczą wyłącznie repozytorium WMM/Cidex-Mobile. Kod desktopowego WM nie został zmieniony.
