import 'package:cidex_mobile/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('CIDEX Mobile ma klienta API i formularz dodawania zlecenia', () {
    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'test');
    final api = CidexApi(config);
    final screen = AddOrderScreen(api: api);

    expect(api.baseUrl, 'http://10.0.2.2:8765');
    expect(screen.api, same(api));
    expect(fmtNumber(5.0), '5');
  });
}
