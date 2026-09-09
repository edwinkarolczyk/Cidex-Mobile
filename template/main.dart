import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';

const kOrange = Color(0xFFFF7A00);
const kGreen = Color(0xFF16A05D);
const kBlue = Color(0xFF1677D2);
const kPurple = Color(0xFF7A48C8);
const kRed = Color(0xFFD43B32);
const kPanel = Color(0xFF171A1F);
const kPanel2 = Color(0xFF20242A);
const kBorder = Color(0xFF2C323A);
const kMuted = Color(0xFF969DA7);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final config = await ApiConfig.load();
  runApp(CidexMobileApp(initialConfig: config));
}

class ApiConfig {
  const ApiConfig({required this.baseUrl, required this.token});

  final String baseUrl;
  final String token;

  static Future<ApiConfig> load() async {
    final prefs = await SharedPreferences.getInstance();
    return ApiConfig(
      baseUrl: prefs.getString('cidex_api_url') ?? 'http://10.0.2.2:8765',
      token: prefs.getString('cidex_api_token') ?? '',
    );
  }

  Future<void> save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('cidex_api_url', baseUrl.trim());
    await prefs.setString('cidex_api_token', token.trim());
  }
}

class ApiException implements Exception {
  ApiException(this.message);
  final String message;

  @override
  String toString() => message;
}

class CidexApi {
  CidexApi(ApiConfig config)
      : baseUrl = config.baseUrl.trim().replaceFirst(RegExp(r'/+$'), ''),
        token = config.token.trim();

  final String baseUrl;
  final String token;

  Map<String, String> get headers => {
        'Accept': 'application/json',
        'X-Cidex-Token': token,
      };

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> _decode(http.Response response) async {
    Map<String, dynamic> payload = {};
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) {
        payload = decoded;
      }
    } catch (_) {
      // Błąd HTTP poniżej poda czytelniejszy komunikat.
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        payload['error']?.toString() ??
            'CIDEX API: błąd HTTP ${response.statusCode}.',
      );
    }
    if (payload['ok'] == false) {
      throw ApiException(payload['error']?.toString() ?? 'Operacja nieudana.');
    }
    return payload;
  }

  Future<Map<String, dynamic>> getJson(String path) async {
    try {
      final response = await http
          .get(_uri(path), headers: headers)
          .timeout(const Duration(seconds: 8));
      return _decode(response);
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Brak połączenia z CIDEX API: $error');
    }
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body,
  ) async {
    try {
      final response = await http
          .post(
            _uri(path),
            headers: {
              ...headers,
              'Content-Type': 'application/json; charset=utf-8',
            },
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 10));
      return _decode(response);
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Nie udało się wysłać danych do CIDEX: $error');
    }
  }

  Future<Map<String, dynamic>> info() => getJson('/api/v1/info');

  Future<List<Map<String, dynamic>>> orders() async {
    final payload = await getJson('/api/v1/planista/orders');
    return _items(payload);
  }

  Future<List<Map<String, dynamic>>> machines() async {
    final payload = await getJson('/api/v1/machines');
    return _items(payload);
  }

  Future<Map<String, dynamic>> machine(String id) async {
    final payload = await getJson('/api/v1/machines/${Uri.encodeComponent(id)}');
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<Map<String, dynamic>> resolveQr(String code) async {
    final uri = _uri('/api/v1/qr/resolve').replace(
      queryParameters: {'code': code},
    );
    try {
      final response = await http
          .get(uri, headers: headers)
          .timeout(const Duration(seconds: 8));
      final payload = await _decode(response);
      return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Nie udało się odczytać kodu QR: $error');
    }
  }

  Future<Map<String, dynamic>> setStatus(
    String id,
    String status,
    String note,
  ) async {
    final payload = await postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/status',
      {'status': status, 'note': note},
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<Map<String, dynamic>> addNote(String id, String note) async {
    final payload = await postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/note',
      {'note': note},
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<Map<String, dynamic>> uploadPhoto(String id, XFile file) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        _uri('/api/v1/machines/${Uri.encodeComponent(id)}/photos'),
      );
      request.headers.addAll(headers);
      request.files.add(await http.MultipartFile.fromPath('photo', file.path));
      final streamed = await request.send().timeout(const Duration(seconds: 25));
      final response = await http.Response.fromStream(streamed);
      final payload = await _decode(response);
      return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Nie udało się wysłać zdjęcia: $error');
    }
  }

  String photoUrl(String relative) {
    if (relative.startsWith('http://') || relative.startsWith('https://')) {
      return relative;
    }
    return '$baseUrl$relative';
  }

  List<Map<String, dynamic>> _items(Map<String, dynamic> payload) {
    final raw = payload['items'];
    if (raw is! List) return [];
    return raw.whereType<Map>().map(Map<String, dynamic>.from).toList();
  }
}

class CidexMobileApp extends StatelessWidget {
  const CidexMobileApp({super.key, required this.initialConfig});

  final ApiConfig initialConfig;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'CIDEX Mobile',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D0F12),
        colorScheme: ColorScheme.fromSeed(
          seedColor: kOrange,
          brightness: Brightness.dark,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF111419),
          foregroundColor: Colors.white,
          centerTitle: false,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: kPanel2,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: const BorderSide(color: kBorder),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: const BorderSide(color: kBorder),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: const BorderSide(color: kOrange, width: 1.4),
          ),
        ),
      ),
      home: HomeScreen(initialConfig: initialConfig),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.initialConfig});
  final ApiConfig initialConfig;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late ApiConfig config;
  bool busy = false;
  bool connected = false;
  String connectionText = 'Sprawdzanie połączenia...';
  String activeOrders = '—';
  String machinesAttention = '—';
  String lastSync = '—';

  CidexApi get api => CidexApi(config);

  @override
  void initState() {
    super.initState();
    config = widget.initialConfig;
    WidgetsBinding.instance.addPostFrameCallback((_) => refresh());
  }

  Future<void> refresh() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      if (config.token.trim().isEmpty) {
        throw ApiException('Ustaw token z okna CIDEX API.');
      }
      await api.info();
      final results = await Future.wait([api.orders(), api.machines()]);
      final orders = results[0];
      final machines = results[1];
      final active = orders.where((item) {
        final status = (item['status'] ?? '').toString().toLowerCase();
        return !{'zakończone', 'anulowane', 'archiwum'}.contains(status);
      }).length;
      final attention = machines.where((item) {
        final status = (item['status'] ?? '').toString();
        return status == 'warn' || status == 'alert';
      }).length;
      if (!mounted) return;
      setState(() {
        connected = true;
        connectionText = 'Połączono z CIDEX na komputerze';
        activeOrders = '$active';
        machinesAttention = '$attention';
        lastSync = TimeOfDay.now().format(context);
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        connected = false;
        connectionText = error.toString();
      });
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> openSettings() async {
    final updated = await Navigator.of(context).push<ApiConfig>(
      MaterialPageRoute(builder: (_) => SettingsScreen(config: config)),
    );
    if (updated == null) return;
    setState(() => config = updated);
    await refresh();
  }

  void open(Widget page) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
  }

  void pickMachineFor(String action) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Wybierz maszynę, a następnie użyj „$action”.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
    open(MachinesScreen(api: api));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: refresh,
          color: kOrange,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 28),
            children: [
              BrandHeader(onSettings: openSettings),
              const SizedBox(height: 18),
              ConnectionCard(
                text: connectionText,
                connected: connected,
                busy: busy,
              ),
              const SizedBox(height: 18),
              const Text(
                'Szybkie działania',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 12),
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.12,
                children: [
                  ActionTile(
                    color: kOrange,
                    icon: Icons.calendar_month_rounded,
                    title: 'Planista',
                    subtitle: 'Aktualne zlecenia WM',
                    onTap: () => open(PlannerScreen(api: api)),
                  ),
                  ActionTile(
                    color: kGreen,
                    icon: Icons.qr_code_scanner_rounded,
                    title: 'Skanuj QR',
                    subtitle: 'Otwórz maszynę po ID',
                    onTap: () => open(QrScannerScreen(api: api)),
                  ),
                  ActionTile(
                    color: kBlue,
                    icon: Icons.precision_manufacturing_rounded,
                    title: 'Maszyny',
                    subtitle: 'Lista z aktualnego WM',
                    onTap: () => open(MachinesScreen(api: api)),
                  ),
                  ActionTile(
                    color: kPurple,
                    icon: Icons.add_a_photo_rounded,
                    title: 'Dodaj zdjęcie',
                    subtitle: 'Aparat lub galeria',
                    onTap: () => pickMachineFor('Dodaj zdjęcie'),
                  ),
                  ActionTile(
                    color: kRed,
                    icon: Icons.warning_amber_rounded,
                    title: 'Zgłoś awarię',
                    subtitle: 'Maszyna + opis',
                    onTap: () => pickMachineFor('Zgłoś awarię'),
                  ),
                  ActionTile(
                    color: const Color(0xFF4A515A),
                    icon: Icons.refresh_rounded,
                    title: 'Odśwież',
                    subtitle: lastSync == '—' ? 'Synchronizuj z WM' : 'Ostatnio $lastSync',
                    onTap: refresh,
                  ),
                ],
              ),
              const SizedBox(height: 18),
              CurrentValuesCard(
                activeOrders: activeOrders,
                machinesAttention: machinesAttention,
                connected: connected,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class BrandHeader extends StatelessWidget {
  const BrandHeader({super.key, required this.onSettings});
  final VoidCallback onSettings;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 54,
          height: 54,
          decoration: BoxDecoration(
            color: kPanel2,
            borderRadius: BorderRadius.circular(17),
            border: Border.all(color: kOrange, width: 1.2),
          ),
          child: const Icon(Icons.build_circle_rounded, color: kOrange, size: 34),
        ),
        const SizedBox(width: 12),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(text: 'CID', style: TextStyle(color: Colors.white)),
                    TextSpan(text: 'EX', style: TextStyle(color: kOrange)),
                    TextSpan(text: ' Mobile', style: TextStyle(color: Color(0xFFD3D7DC))),
                  ],
                ),
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900),
              ),
              SizedBox(height: 2),
              Text('Warsztat pod kontrolą', style: TextStyle(color: kMuted)),
            ],
          ),
        ),
        IconButton.filledTonal(
          tooltip: 'Ustawienia połączenia',
          onPressed: onSettings,
          icon: const Icon(Icons.settings_rounded),
        ),
      ],
    );
  }
}

class ConnectionCard extends StatelessWidget {
  const ConnectionCard({
    super.key,
    required this.text,
    required this.connected,
    required this.busy,
  });

  final String text;
  final bool connected;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final color = busy ? const Color(0xFFFFB020) : (connected ? kGreen : kRed);
    return RoundedCard(
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('CIDEX API', style: TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(text, style: const TextStyle(color: kMuted, fontSize: 12)),
              ],
            ),
          ),
          if (busy)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2, color: kOrange),
            )
          else
            Icon(Icons.wifi_tethering_rounded, color: color),
        ],
      ),
    );
  }
}

class ActionTile extends StatelessWidget {
  const ActionTile({
    super.key,
    required this.color,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final Color color;
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, size: 34, color: Colors.white),
              const Spacer(),
              Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text(
                subtitle,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12, color: Colors.white70),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class CurrentValuesCard extends StatelessWidget {
  const CurrentValuesCard({
    super.key,
    required this.activeOrders,
    required this.machinesAttention,
    required this.connected,
  });

  final String activeOrders;
  final String machinesAttention;
  final bool connected;

  @override
  Widget build(BuildContext context) {
    return RoundedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Podgląd aktualnych wartości', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          ValueRow(label: 'Aktywne zlecenia', value: activeOrders, valueColor: kOrange),
          ValueRow(label: 'Maszyny wymagające uwagi', value: machinesAttention, valueColor: kRed),
          const ValueRow(label: 'Autor zapisów mobilnych', value: 'Cidex', valueColor: Color(0xFF58B5FF)),
          const SizedBox(height: 8),
          Text(
            connected
                ? 'Wartości pobrano z bieżącego WM_ROOT przez CIDEX API.'
                : 'Brak połączenia. Ustaw adres komputera i token w ustawieniach.',
            style: const TextStyle(fontSize: 12, color: kMuted),
          ),
        ],
      ),
    );
  }
}

class ValueRow extends StatelessWidget {
  const ValueRow({
    super.key,
    required this.label,
    required this.value,
    required this.valueColor,
  });

  final String label;
  final String value;
  final Color valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(child: Text(label, style: const TextStyle(color: Color(0xFFB9BEC6)))),
          Text(value, style: TextStyle(fontWeight: FontWeight.w900, color: valueColor)),
        ],
      ),
    );
  }
}

class RoundedCard extends StatelessWidget {
  const RoundedCard({super.key, required this.child, this.padding = const EdgeInsets.all(16)});
  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: kPanel,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: kBorder),
      ),
      child: child,
    );
  }
}

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, required this.config});
  final ApiConfig config;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController url;
  late final TextEditingController token;
  bool testing = false;
  String result = '';

  @override
  void initState() {
    super.initState();
    url = TextEditingController(text: widget.config.baseUrl);
    token = TextEditingController(text: widget.config.token);
  }

  @override
  void dispose() {
    url.dispose();
    token.dispose();
    super.dispose();
  }

  ApiConfig current() => ApiConfig(baseUrl: url.text.trim(), token: token.text.trim());

  Future<void> testConnection() async {
    setState(() {
      testing = true;
      result = 'Sprawdzanie...';
    });
    try {
      final payload = await CidexApi(current()).info();
      if (!mounted) return;
      setState(() {
        result = 'Połączono. API ${payload['api_version'] ?? ''}, autor ${payload['author'] ?? 'Cidex'}.';
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => result = error.toString());
    } finally {
      if (mounted) setState(() => testing = false);
    }
  }

  Future<void> save() async {
    final value = current();
    if (value.baseUrl.isEmpty || value.token.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Adres API i token są wymagane.')),
      );
      return;
    }
    await value.save();
    if (!mounted) return;
    Navigator.of(context).pop(value);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Połączenie z CIDEX')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const RoundedCard(
            child: Text(
              'Emulator: http://10.0.2.2:8765\nTelefon: wpisz adres LAN pokazany przez run_api.bat / Cidex_Api.exe.\n\nToken skopiuj z okna serwera CIDEX.',
              style: TextStyle(color: Color(0xFFC5CBD2), height: 1.5),
            ),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: url,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(
              labelText: 'Adres CIDEX API',
              hintText: 'http://10.0.2.2:8765',
              prefixIcon: Icon(Icons.lan_rounded),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: token,
            decoration: const InputDecoration(
              labelText: 'Token CIDEX',
              prefixIcon: Icon(Icons.key_rounded),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 54,
            child: FilledButton.icon(
              onPressed: testing ? null : testConnection,
              icon: testing
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.wifi_find_rounded),
              label: const Text('TESTUJ POŁĄCZENIE', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
          if (result.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(result, style: const TextStyle(color: kMuted)),
          ],
          const SizedBox(height: 12),
          SizedBox(
            height: 54,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: kOrange),
              onPressed: save,
              icon: const Icon(Icons.save_rounded),
              label: const Text('ZAPISZ', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
        ],
      ),
    );
  }
}

class PlannerScreen extends StatefulWidget {
  const PlannerScreen({super.key, required this.api});
  final CidexApi api;

  @override
  State<PlannerScreen> createState() => _PlannerScreenState();
}

class _PlannerScreenState extends State<PlannerScreen> {
  List<Map<String, dynamic>> items = [];
  bool busy = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final rows = await widget.api.orders();
      if (!mounted) return;
      setState(() => items = rows.reversed.toList());
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Color statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'zakończone':
        return kGreen;
      case 'w trakcie':
        return kBlue;
      case 'wstrzymane':
      case 'anulowane':
        return kRed;
      default:
        return kOrange;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Planista'),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      body: busy
          ? const Center(child: CircularProgressIndicator(color: kOrange))
          : error.isNotEmpty
              ? ErrorState(message: error, onRetry: load)
              : RefreshIndicator(
                  onRefresh: load,
                  color: kOrange,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final order = items[index];
                      final status = (order['status'] ?? 'nowe').toString();
                      return RoundedCard(
                        padding: EdgeInsets.zero,
                        child: Container(
                          padding: const EdgeInsets.all(15),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(20),
                            border: Border(left: BorderSide(color: statusColor(status), width: 5)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      'Zlec. wew: ${order['zlec_wew'] ?? '—'}',
                                      style: const TextStyle(fontWeight: FontWeight.w900),
                                    ),
                                  ),
                                  StatusPill(text: status, color: statusColor(status)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                '${order['produkt'] ?? 'Brak produktu'}',
                                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                              ),
                              const SizedBox(height: 7),
                              Text(
                                'Warsztatowe: ${order['id'] ?? '—'}  •  Ilość: ${fmtNumber(order['ilosc'])}',
                                style: const TextStyle(color: Color(0xFFB8BEC6)),
                              ),
                              if ((order['termin'] ?? '').toString().isNotEmpty)
                                Text(
                                  'Termin: ${order['termin']}',
                                  style: const TextStyle(color: kMuted),
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

class MachinesScreen extends StatefulWidget {
  const MachinesScreen({super.key, required this.api});
  final CidexApi api;

  @override
  State<MachinesScreen> createState() => _MachinesScreenState();
}

class _MachinesScreenState extends State<MachinesScreen> {
  final search = TextEditingController();
  List<Map<String, dynamic>> items = [];
  bool busy = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    load();
    search.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final rows = await widget.api.machines();
      if (!mounted) return;
      setState(() => items = rows);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  List<Map<String, dynamic>> get visible {
    final q = search.text.trim().toLowerCase();
    if (q.isEmpty) return items;
    return items.where((item) {
      return ['id', 'nr_ewid', 'nazwa', 'typ', 'hala', 'lokalizacja']
          .map((key) => (item[key] ?? '').toString().toLowerCase())
          .any((value) => value.contains(q));
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final rows = visible;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Maszyny'),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 6),
            child: TextField(
              controller: search,
              decoration: const InputDecoration(
                hintText: 'Szukaj ID, nazwy, typu, hali...',
                prefixIcon: Icon(Icons.search_rounded),
              ),
            ),
          ),
          Expanded(
            child: busy
                ? const Center(child: CircularProgressIndicator(color: kOrange))
                : error.isNotEmpty
                    ? ErrorState(message: error, onRetry: load)
                    : RefreshIndicator(
                        onRefresh: load,
                        color: kOrange,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(16),
                          itemCount: rows.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            final item = rows[index];
                            final color = machineStatusColor((item['status'] ?? '').toString());
                            return Material(
                              color: kPanel,
                              borderRadius: BorderRadius.circular(20),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(20),
                                onTap: () async {
                                  await Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => MachineScreen(
                                        api: widget.api,
                                        machineId: (item['id'] ?? '').toString(),
                                      ),
                                    ),
                                  );
                                  load();
                                },
                                child: Container(
                                  padding: const EdgeInsets.all(15),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: kBorder),
                                  ),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 48,
                                        height: 48,
                                        decoration: BoxDecoration(
                                          color: color.withValues(alpha: 0.16),
                                          borderRadius: BorderRadius.circular(15),
                                        ),
                                        child: Icon(Icons.precision_manufacturing_rounded, color: color),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              '${item['id'] ?? '—'} — ${item['nazwa'] ?? ''}',
                                              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              '${item['typ'] ?? '—'} • Hala ${item['hala'] ?? '—'}',
                                              style: const TextStyle(color: kMuted),
                                            ),
                                          ],
                                        ),
                                      ),
                                      StatusPill(text: '${item['status_label'] ?? item['status'] ?? '—'}', color: color),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}

class QrScannerScreen extends StatefulWidget {
  const QrScannerScreen({super.key, required this.api});
  final CidexApi api;

  @override
  State<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends State<QrScannerScreen> {
  final controller = MobileScannerController();
  final manual = TextEditingController(text: 'CIDEX:MACHINE:42');
  bool resolving = false;
  bool scanned = false;
  String error = '';

  @override
  void dispose() {
    controller.dispose();
    manual.dispose();
    super.dispose();
  }

  Future<void> resolve(String code) async {
    if (resolving || code.trim().isEmpty) return;
    setState(() {
      resolving = true;
      error = '';
    });
    try {
      final item = await widget.api.resolveQr(code.trim());
      if (!mounted) return;
      final id = (item['id'] ?? '').toString();
      if (id.isEmpty) throw ApiException('QR nie zawiera poprawnego ID maszyny.');
      await controller.stop();
      if (!mounted) return;
      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => MachineScreen(api: widget.api, machineId: id)),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = e.toString();
        scanned = false;
      });
      await controller.start();
    } finally {
      if (mounted) setState(() => resolving = false);
    }
  }

  void onDetect(BarcodeCapture capture) {
    if (scanned || resolving || capture.barcodes.isEmpty) return;
    final value = capture.barcodes.first.rawValue;
    if (value == null || value.trim().isEmpty) return;
    scanned = true;
    resolve(value);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Skanuj QR maszyny')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AspectRatio(
            aspectRatio: 1,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  MobileScanner(controller: controller, onDetect: onDetect),
                  IgnorePointer(
                    child: Container(
                      margin: const EdgeInsets.all(46),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: kOrange, width: 3),
                      ),
                    ),
                  ),
                  if (resolving)
                    Container(
                      color: Colors.black54,
                      child: const Center(child: CircularProgressIndicator(color: kOrange)),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            'Skieruj aparat na kod QR naklejony na maszynie.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Color(0xFFC4CAD1), fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 16),
          const Divider(color: kBorder),
          const SizedBox(height: 10),
          const Text('Test w emulatorze / ręczne ID', style: TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          TextField(
            controller: manual,
            decoration: const InputDecoration(
              labelText: 'ID lub treść QR',
              prefixIcon: Icon(Icons.qr_code_2_rounded),
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 54,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: kGreen),
              onPressed: resolving ? null : () => resolve(manual.text),
              icon: const Icon(Icons.open_in_new_rounded),
              label: const Text('OTWÓRZ MASZYNĘ', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
          if (error.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(error, style: const TextStyle(color: kRed)),
          ],
        ],
      ),
    );
  }
}

class MachineScreen extends StatefulWidget {
  const MachineScreen({super.key, required this.api, required this.machineId});
  final CidexApi api;
  final String machineId;

  @override
  State<MachineScreen> createState() => _MachineScreenState();
}

class _MachineScreenState extends State<MachineScreen> {
  final picker = ImagePicker();
  Map<String, dynamic> machine = {};
  bool busy = true;
  bool actionBusy = false;
  String error = '';

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final item = await widget.api.machine(widget.machineId);
      if (!mounted) return;
      setState(() => machine = item);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void snack(String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }

  Future<String?> askText(String title, String hint, {bool required = true}) async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 2,
          maxLines: 5,
          decoration: InputDecoration(hintText: hint),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Anuluj')),
          FilledButton(
            onPressed: () {
              final value = controller.text.trim();
              if (required && value.isEmpty) return;
              Navigator.pop(dialogContext, value);
            },
            child: const Text('Zapisz'),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  Future<void> setStatus(String status) async {
    final requiresNote = status != 'Sprawna';
    final note = await askText(
      status == 'Awaria' ? 'Zgłoś awarię' : 'Serwis / przegląd',
      requiresNote ? 'Krótko opisz powód...' : 'Opcjonalna uwaga',
      required: requiresNote,
    );
    if (note == null) return;
    await runAction(() => widget.api.setStatus(widget.machineId, status, note), 'Status zapisany w WM.');
  }

  Future<void> addNote() async {
    final note = await askText('Dodaj uwagę', 'Wpisz uwagę do maszyny...');
    if (note == null) return;
    await runAction(() => widget.api.addNote(widget.machineId, note), 'Uwaga dodana jako Cidex.');
  }

  Future<void> choosePhoto() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 18),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.photo_camera_rounded, color: kPurple),
                title: const Text('Zrób zdjęcie aparatem'),
                onTap: () => Navigator.pop(sheetContext, ImageSource.camera),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_rounded, color: kBlue),
                title: const Text('Wybierz z galerii'),
                onTap: () => Navigator.pop(sheetContext, ImageSource.gallery),
              ),
            ],
          ),
        ),
      ),
    );
    if (source == null) return;
    final file = await picker.pickImage(
      source: source,
      imageQuality: 85,
      maxWidth: 1920,
    );
    if (file == null) return;
    await runAction(() => widget.api.uploadPhoto(widget.machineId, file), 'Zdjęcie zapisane przy maszynie.');
  }

  Future<void> runAction(
    Future<Map<String, dynamic>> Function() operation,
    String success,
  ) async {
    if (actionBusy) return;
    setState(() => actionBusy = true);
    try {
      final item = await operation();
      if (!mounted) return;
      setState(() => machine = item);
      snack(success);
    } catch (e) {
      if (mounted) snack(e.toString());
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (busy) {
      return Scaffold(
        appBar: AppBar(title: Text('Maszyna ${widget.machineId}')),
        body: const Center(child: CircularProgressIndicator(color: kOrange)),
      );
    }
    if (error.isNotEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text('Maszyna ${widget.machineId}')),
        body: ErrorState(message: error, onRetry: load),
      );
    }

    final status = (machine['status'] ?? '').toString();
    final color = machineStatusColor(status);
    final current = Map<String, dynamic>.from(machine['status_current'] as Map? ?? const {});
    final photos = (machine['photos'] as List? ?? const []).whereType<Map>().map(Map<String, dynamic>.from).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('Maszyna ${machine['id'] ?? widget.machineId}'),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      body: Stack(
        children: [
          RefreshIndicator(
            onRefresh: load,
            color: kOrange,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 60,
                            height: 60,
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.16),
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Icon(Icons.precision_manufacturing_rounded, color: color, size: 34),
                          ),
                          const SizedBox(width: 13),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${machine['nazwa'] ?? 'Maszyna'}',
                                  style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
                                ),
                                const SizedBox(height: 3),
                                Text('${machine['typ'] ?? '—'}', style: const TextStyle(color: kMuted)),
                              ],
                            ),
                          ),
                          StatusPill(text: '${machine['status_label'] ?? status}', color: color),
                        ],
                      ),
                      const SizedBox(height: 16),
                      InfoRow(icon: Icons.tag_rounded, label: 'Nr ewid.', value: '${machine['nr_ewid'] ?? machine['id'] ?? '—'}'),
                      InfoRow(icon: Icons.factory_rounded, label: 'Hala', value: '${machine['hala'] ?? '—'}'),
                      InfoRow(
                        icon: Icons.location_on_rounded,
                        label: 'Lokalizacja',
                        value: (machine['lokalizacja'] ?? '').toString().isEmpty ? '—' : '${machine['lokalizacja']}',
                      ),
                      InfoRow(
                        icon: Icons.event_available_rounded,
                        label: 'Najbliższy przegląd',
                        value: (machine['next_review'] ?? '').toString().isEmpty ? '—' : '${machine['next_review']}',
                      ),
                      if ((current['note'] ?? '').toString().trim().isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(13),
                          decoration: BoxDecoration(
                            color: kPanel2,
                            borderRadius: BorderRadius.circular(15),
                          ),
                          child: Text(
                            '${current['note']}',
                            style: const TextStyle(color: Color(0xFFD3D7DD), height: 1.35),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 1.45,
                  children: [
                    MachineActionButton(color: kPurple, icon: Icons.add_a_photo_rounded, text: 'Dodaj zdjęcie', onTap: choosePhoto),
                    MachineActionButton(color: kRed, icon: Icons.warning_amber_rounded, text: 'Zgłoś awarię', onTap: () => setStatus('Awaria')),
                    MachineActionButton(color: kBlue, icon: Icons.note_add_rounded, text: 'Dodaj uwagę', onTap: addNote),
                    MachineActionButton(color: kOrange, icon: Icons.build_circle_rounded, text: 'Serwis / przegląd', onTap: () => setStatus('Serwis / przegląd')),
                  ],
                ),
                if (status != 'ok') ...[
                  const SizedBox(height: 10),
                  SizedBox(
                    height: 52,
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        await runAction(
                          () => widget.api.setStatus(widget.machineId, 'Sprawna', ''),
                          'Maszyna oznaczona jako sprawna.',
                        );
                      },
                      icon: const Icon(Icons.check_circle_rounded, color: kGreen),
                      label: const Text('OZNACZ JAKO SPRAWNĄ'),
                    ),
                  ),
                ],
                const SizedBox(height: 18),
                Row(
                  children: [
                    const Expanded(
                      child: Text('Ostatnie zdjęcia', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
                    ),
                    Text('${photos.length}', style: const TextStyle(color: kMuted)),
                  ],
                ),
                const SizedBox(height: 10),
                if (photos.isEmpty)
                  const RoundedCard(
                    child: Text('Brak zdjęć przy bieżących zdarzeniach tej maszyny.', style: TextStyle(color: kMuted)),
                  )
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 10,
                      crossAxisSpacing: 10,
                      childAspectRatio: 1.15,
                    ),
                    itemCount: photos.length,
                    itemBuilder: (context, index) {
                      final photo = photos[index];
                      final url = widget.api.photoUrl((photo['url'] ?? '').toString());
                      return ClipRRect(
                        borderRadius: BorderRadius.circular(18),
                        child: Container(
                          color: kPanel2,
                          child: Image.network(
                            url,
                            headers: widget.api.headers,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.broken_image_rounded, color: kMuted)),
                          ),
                        ),
                      );
                    },
                  ),
                const SizedBox(height: 12),
                const Text(
                  'Zapisy wykonane z telefonu używają autora „Cidex”.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: kMuted, fontSize: 12),
                ),
              ],
            ),
          ),
          if (actionBusy)
            Positioned.fill(
              child: ColoredBox(
                color: Colors.black45,
                child: const Center(child: CircularProgressIndicator(color: kOrange)),
              ),
            ),
        ],
      ),
    );
  }
}

class MachineActionButton extends StatelessWidget {
  const MachineActionButton({
    super.key,
    required this.color,
    required this.icon,
    required this.text,
    required this.onTap,
  });

  final Color color;
  final IconData icon;
  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(19),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(19),
        child: Padding(
          padding: const EdgeInsets.all(13),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: Colors.white, size: 28),
              const SizedBox(height: 8),
              Text(text, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14)),
            ],
          ),
        ),
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.text, required this.color});
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.8)),
      ),
      child: Text(
        text,
        style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 11),
      ),
    );
  }
}

class InfoRow extends StatelessWidget {
  const InfoRow({super.key, required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Icon(icon, size: 18, color: kMuted),
          const SizedBox(width: 8),
          Expanded(child: Text(label, style: const TextStyle(color: kMuted))),
          Flexible(child: Text(value, textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w700))),
        ],
      ),
    );
  }
}

class ErrorState extends StatelessWidget {
  const ErrorState({super.key, required this.message, required this.onRetry});
  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_rounded, size: 60, color: kRed),
            const SizedBox(height: 14),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Color(0xFFC6CCD3))),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('SPRÓBUJ PONOWNIE'),
            ),
          ],
        ),
      ),
    );
  }
}

Color machineStatusColor(String status) {
  switch (status.toLowerCase()) {
    case 'ok':
    case 'sprawna':
      return kGreen;
    case 'alert':
    case 'serwis / przegląd':
      return kOrange;
    case 'warn':
    case 'awaria':
      return kRed;
    default:
      return kBlue;
  }
}

String fmtNumber(dynamic value) {
  if (value is num && value == value.roundToDouble()) return value.toInt().toString();
  return '${value ?? '—'}';
}
