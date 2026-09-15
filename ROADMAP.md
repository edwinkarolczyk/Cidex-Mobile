# WMM — roadmap

## Zasada zgodności z Warsztat Menager

WMM ma korzystać z funkcji i modelu danych, które już istnieją w Warsztat Menager. Nie dodajemy nowych typów statusów, serwisów ani równoległego modelu danych tylko na potrzeby telefonu; zmiany po stronie WM mają ograniczać się do bezpiecznego API/mostu do istniejących funkcji, chyba że osobno zapadnie decyzja o rozwoju samego WM.

## Najbliższe wydanie — stabilizacja 0.6.0

**Status: następny etap.**

Zakres:

- stabilizacja połączenia po utracie Wi-Fi / zmianie sieci;
- ponawianie operacji bez dublowania zapisów;
- czytelne komunikaty błędów bez technicznych wyjątków;
- historia / informacja o ostatniej synchronizacji;
- przejścia z powiadomień do konkretnego obiektu tam, gdzie obecny model WMM już to obsługuje;
- test pełnej ścieżki `QR → akcja → zapis w WM`;
- bez dokładania nowych funkcji biznesowych do desktopowego WM.

### Branding następnego wydania

Przy następnym wydaniu usunąć widoczny napis **`BETA`** z nazwy aplikacji, etykiety Androida, nagłówków/ekranów oraz tytułu release. Numer wersji ma pozostać widoczny, np. `WMM 0.6.0`.

## Powiadomienie o awarii na wybrany telefon

**Status: planowane — osobny etap po ustabilizowaniu bieżących akcji Maszyn.**

Cel: z WMM/WM móc skierować informację o awarii konkretnej maszyny do wybranego użytkownika lub zarejestrowanego telefonu WMM.

Zakres docelowy:

- wybór odbiorcy spośród użytkowników / zarejestrowanych urządzeń WMM;
- komunikat np. `Maszyna 42 — AWARIA` z nazwą maszyny i krótką uwagą;
- kliknięcie powiadomienia otwiera bezpośrednio kartę właściwej maszyny w WMM;
- zapis źródła i czasu wysłania bez tworzenia nowego typu awarii — awaria nadal pozostaje zwykłym istniejącym statusem WM;
- pierwsza wersja może działać po LAN, gdy WMM jest aktywne i połączone z WM;
- niezawodne powiadomienia przy wygaszonym ekranie lub zamkniętej aplikacji wymagają osobnego mechanizmu push i rejestracji urządzeń;
- mechanizm push wdrażamy oddzielnie, bez mieszania go z obecnym zapisem napraw i przeglądów.

## Bieżący punkt odniesienia

WMM 0.5.18: szybka naprawa oraz dodawanie planowanego przeglądu korzystają z istniejącego modelu Maszyn WM. Następne prace nad powiadomieniami nie mogą łamać tej kompatybilności.
