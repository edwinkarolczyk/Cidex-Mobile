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
}
