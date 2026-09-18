import 'package:cidex_mobile/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('WMM ma klienta WM i formularz dodawania zlecenia', () {
    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    final screen = AddOrderScreen(api: api);

    expect(api.baseUrl, 'http://10.0.2.2:8765');
    expect(screen.api, same(api));
    expect(fmtNumber(5.0), '5');
    expect(api.headers['X-WMM-Key'], 'ABC123');
    expect(api.headers['X-Cidex-Token'], 'ABC123');
  });

  test('WMM odczytuje kod QR połączenia z WM', () {
    final pairing = WmmPairingData.parse(
      'WMM://CONNECT?host=192.168.1.50&port=8765&key=AB12CD',
    );

    expect(pairing.baseUrl, 'http://192.168.1.50:8765');
    expect(pairing.key, 'AB12CD');
  });

  test('WMM 0.5.16 pokazuje statusy maszyn jak WM', () {
    expect(wmmMachineStatusLabel('ok'), 'Sprawna');
    expect(wmmMachineStatusLabel('alert'), 'Serwis / przegląd');
    expect(wmmMachineStatusLabel('warn'), 'Awaria');
    expect(wmmMachineStatusLabel('warm'), 'Awaria');
  });

  test('WMM opisuje historię narzędzia po polsku i ze szczegółami', () {
    final status = <String, dynamic>{
      'ts': '2026-09-17T07:49:00',
      'by': 'Edwin',
      'action': 'status_changed',
      'z': 'Przegląd',
      'na': 'W ostrzeniu',
    };
    final task = <String, dynamic>{
      'ts': '2026-09-17T07:48:30',
      'by': 'Edwin',
      'action': 'task_done',
      'title': 'Demontaż elementów trących',
    };

    expect(wmmHistoryActionLabel(status), 'Zmiana statusu');
    expect(wmmHistoryDetails(status), 'Przegląd → W ostrzeniu');
    expect(wmmHistoryActionLabel(task), 'Zadanie wykonane');
    expect(wmmHistoryDetails(task), 'Demontaż elementów trących');
  });

  test('WMM grupuje historię z tej samej minuty i tego samego autora', () {
    final groups = wmmHistoryGroups(<Map<String, dynamic>>[
      {'ts': '2026-09-17T07:48:10', 'by': 'Edwin', 'action': 'task_added', 'title': 'Kontrola'},
      {'ts': '2026-09-17T07:48:50', 'by': 'Edwin', 'action': 'task_done', 'title': 'Kontrola'},
      {'ts': '2026-09-17T07:49:00', 'by': 'Edwin', 'action': 'status_changed', 'z': 'Przegląd', 'na': 'W ostrzeniu'},
      {'ts': '2026-09-17T07:50:00', 'by': '', 'action': 'info'},
    ]);

    expect(groups.length, 2);
    expect((groups.last['items'] as List).length, 2);
  });

  test('WMM 0.5.16 ma centrum powiadomień z klientem WM', () {
    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    final screen = WmmNotificationsScreen(api: api);
    expect(screen.api, same(api));
  });

  test('WMM 0.5.16 porównuje wersje aktualizacji', () {
    expect(kWmmCurrentVersion, '0.5.16');
    expect(wmmCompareVersions('0.5.16', '0.5.15'), greaterThan(0));
    expect(wmmCompareVersions('0.5.16', '0.5.16'), 0);
    expect(wmmCompareVersions('0.5.15', '0.5.16'), lessThan(0));
  });

  test('WMM 0.5.16 rozpoznaje QR maszyny i narzędzia', () {
    expect(
      wmmParseObjectQr('CIDEX:MACHINE:42'),
      {'entity': 'machine', 'id': '42'},
    );
    expect(
      wmmParseObjectQr('WMM:MASZYNA:71'),
      {'entity': 'machine', 'id': '71'},
    );
    expect(
      wmmParseObjectQr('WMM:TOOL:001'),
      {'entity': 'tool', 'id': '001'},
    );
    expect(
      wmmParseObjectQr('WMM:NARZEDZIE:500'),
      {'entity': 'tool', 'id': '500'},
    );
    expect(wmmQrEntity({'entity': 'tool'}), 'tool');
    expect(wmmQrObjectId({'nr_ewid': '42'}), '42');
  });

  test('WMM 0.5.16 ma baner aktualizacji dostępny przed logowaniem', () {
    final banner = WmmHomeVersionBanner(onOpenUpdates: () {});
    expect(banner.onOpenUpdates, isNotNull);
  });

  test('WMM 0.5.16 ma pełny obieg Dyspozycji zgodny z WM', () {
    expect(wmmDispositionStatusLabel('nowa'), 'Nowa');
    expect(wmmDispositionStatusLabel('w_toku'), 'W toku');
    expect(wmmDispositionStatusLabel('wstrzymana'), 'Wstrzymana');
    expect(wmmDispositionStatusLabel('zamknieta'), 'Zakończona');

    expect(wmmDispositionAllowedTargets('nowa'), ['w_toku']);
    expect(wmmDispositionAllowedTargets('w_toku'), ['wstrzymana', 'zamknieta']);
    expect(wmmDispositionAllowedTargets('wstrzymana'), ['w_toku', 'zamknieta']);
    expect(wmmDispositionAllowedTargets('zamknieta'), isEmpty);

    expect(wmmDispositionPriorityLabel('krytyczny'), 'Krytyczny');
    expect(wmmDispositionTypeLabel('maszyna'), 'Maszyna');
    expect(wmmDispositionTypeLabel('narzedzie'), 'Narzędzie');
    expect(
      wmmDispositionAssignment({'dla_wszystkich': true, 'przypisane_do': 'Edwin'}),
      'Wszyscy',
    );
    expect(
      wmmDispositionAssignment({'dla_wszystkich': false, 'przypisane_do': 'Edwin'}),
      'Edwin',
    );

    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    final list = DispositionsScreen(api: api);
    final detail = DispositionScreen(
      api: api,
      initial: const {'id': 'DYSP-TEST', 'status': 'nowa'},
    );
    expect(list.api, same(api));
    expect(detail.api, same(api));
    expect(detail.initial['id'], 'DYSP-TEST');
  });

  test('WMM 0.5.16 ma Magazyn z przyjęciem bez edycji kartoteki', () {
    const row = <String, dynamic>{
      'kod': 'SR001',
      'nazwa': 'Pręt fi8',
      'jednostka': 'kg',
      'stan': 12.5,
      'lokalizacja': 'Regał A1',
      'receipts': [
        {'qty': 2.5, 'user': 'edwin', 'ts': '2026-09-14T09:00:00'},
      ],
    };

    expect(wmmWarehouseItemId(row), 'SR001');
    expect(wmmWarehouseName(row), 'Pręt fi8');
    expect(wmmWarehouseUnit(row), 'kg');
    expect(wmmWarehouseStock(row), 12.5);
    expect(wmmWarehouseLocation(row), 'Regał A1');
    expect(wmmWarehouseReceipts(row), hasLength(1));
    expect(wmmWarehouseNumber(12.5), '12.5');

    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    final list = WarehouseScreen(api: api);
    final detail = WarehouseItemScreen(api: api, initial: row);
    expect(list.api, same(api));
    expect(detail.api, same(api));
    expect(wmmWarehouseItemId(detail.initial), 'SR001');
  });
  test('WMM zachowuje request-id do bezpiecznego ponowienia zapisu', () {
    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    const path = '/api/v1/tools/001/status';
    const payload = '{"status":"READY","note":""}';

    final first = api.beginWriteRequest(path, payload);
    final retry = api.beginWriteRequest(path, payload);
    expect(retry, first);
    expect(api.writeHeaders(first)['X-WMM-Request-ID'], first);

    api.completeWriteRequest(path, payload);
    final next = api.beginWriteRequest(path, payload);
    expect(next, isNot(first));
    api.completeWriteRequest(path, payload);
  });

  test('WMM rozpoznaje aktualny status po kodzie albo etykiecie', () {
    const option = <String, dynamic>{'id': 'READY', 'name': 'Dostępne'};
    expect(wmmToolStatusIsCurrent(const {'status': 'READY'}, option), isTrue);
    expect(wmmToolStatusIsCurrent(const {'status': 'Dostępne'}, option), isTrue);
    expect(wmmToolStatusIsCurrent(const {'status_label': 'Dostępne'}, option), isTrue);
    expect(wmmToolStatusIsCurrent(const {'status': 'Do naprawy'}, option), isFalse);
  });

}
