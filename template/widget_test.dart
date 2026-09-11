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

  test('WMM 0.5.10 pokazuje statusy maszyn jak WM', () {
    expect(wmmMachineStatusLabel('ok'), 'Sprawna');
    expect(wmmMachineStatusLabel('alert'), 'Serwis / przegląd');
    expect(wmmMachineStatusLabel('warn'), 'Awaria');
    expect(wmmMachineStatusLabel('warm'), 'Awaria');
  });

  test('WMM 0.5.10 ma centrum powiadomień z klientem WM', () {
    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    final screen = WmmNotificationsScreen(api: api);
    expect(screen.api, same(api));
  });

  test('WMM 0.5.10 porównuje wersje aktualizacji', () {
    expect(kWmmCurrentVersion, '0.5.10');
    expect(wmmCompareVersions('0.5.10', '0.5.9'), greaterThan(0));
    expect(wmmCompareVersions('0.5.10', '0.5.10'), 0);
    expect(wmmCompareVersions('0.5.9', '0.5.10'), lessThan(0));
  });
}
