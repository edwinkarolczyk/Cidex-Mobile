from __future__ import annotations

from pathlib import Path
import re


DART_RUNTIME = r'''
String _wmmFriendlyNetworkMessage(Object? error, {bool writing = false}) {
  if (error is TimeoutException) {
    return writing
        ? 'WM nie potwierdził zapisu w wymaganym czasie. Sprawdź połączenie przed ponowieniem, aby nie wykonać operacji drugi raz.'
        : 'WM nie odpowiada. Sprawdź Wi-Fi oraz czy Warsztat Menager jest uruchomiony.';
  }
  if (error is SocketException) {
    return 'Brak połączenia z WM. Telefon i komputer muszą być w tej samej sieci lokalnej.';
  }
  final text = (error ?? '').toString().toLowerCase();
  if (text.contains('connection refused') || text.contains('failed host lookup')) {
    return 'Nie można połączyć się z WM. Sprawdź adres komputera, Wi-Fi i uruchomione WM API.';
  }
  if (text.contains('connection reset') || text.contains('connection closed')) {
    return writing
        ? 'Połączenie z WM zostało przerwane podczas zapisu. Sprawdź w WM, czy operacja została zapisana, zanim ponowisz.'
        : 'Połączenie z WM zostało przerwane. WMM spróbuje ponownie automatycznie.';
  }
  return writing
      ? 'Nie udało się wysłać danych do WM. Sprawdź połączenie i spróbuj ponownie.'
      : 'Nie udało się połączyć z Warsztat Menager.';
}

class WmmConnectionMonitor {
  static DateTime? lastSuccess;
  static int consecutiveFailures = 0;

  static void markOnline() {
    lastSuccess = DateTime.now();
    consecutiveFailures = 0;
  }

  static void markFailure() {
    consecutiveFailures += 1;
  }
}

class WmmNotifications {
  static const MethodChannel _channel = MethodChannel('pl.cidex.wmm/notifications');
  static const String _historyKey = 'wmm_notification_history';
  static const String _machinesKey = 'wmm_notification_machines';
  static const String _toolsKey = 'wmm_notification_tools';
  static const String _dispositionsKey = 'wmm_notification_dispositions';
  static const String _seededKey = 'wmm_notification_seeded';
  static const String _enabledKey = 'wmm_notifications_enabled';
  static const String _permissionAskedKey = 'wmm_notifications_permission_asked';

  static Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final enabled = prefs.getBool(_enabledKey) ?? true;
    if (!enabled) return;
    if (prefs.getBool(_permissionAskedKey) == true) return;
    try {
      await _channel.invokeMethod<void>('requestPermission');
    } catch (_) {
      // Centrum powiadomień w aplikacji nadal działa bez zgody systemowej.
    }
    await prefs.setBool(_permissionAskedKey, true);
  }

  static Future<bool> isEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_enabledKey) ?? true;
  }

  static Future<void> setEnabled(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_enabledKey, value);
    if (value) {
      try {
        await _channel.invokeMethod<void>('requestPermission');
      } catch (_) {}
    }
  }

  static Map<String, String> _decodeMap(String raw) {
    if (raw.trim().isEmpty) return <String, String>{};
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map) {
        return decoded.map((key, value) => MapEntry(key.toString(), value.toString()));
      }
    } catch (_) {}
    return <String, String>{};
  }

  static Set<String> _decodeSet(String raw) {
    if (raw.trim().isEmpty) return <String>{};
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) return decoded.map((item) => item.toString()).toSet();
    } catch (_) {}
    return <String>{};
  }

  static String _id(Map<String, dynamic> row) =>
      (row['id'] ?? row['nr_ewid'] ?? row['numer'] ?? row['nr'] ?? row['kod'] ?? '').toString().trim();

  static String _name(Map<String, dynamic> row) =>
      (row['nazwa'] ?? row['name'] ?? row['tytul'] ?? row['obiekt'] ?? '').toString().trim();

  static String _status(Map<String, dynamic> row) =>
      (row['status'] ?? row['status_label'] ?? '').toString().trim();

  static bool _machineAttention(String status) {
    final value = status.toLowerCase();
    return value.contains('awaria') ||
        value.contains('alert') ||
        value.contains('warn') ||
        value.contains('serwis') ||
        value.contains('napraw');
  }

  static bool _toolAttention(String status) {
    final value = status.toLowerCase();
    return value.contains('napraw') ||
        value.contains('ostrzen') ||
        value.contains('zagub') ||
        value.contains('alert') ||
        value.contains('warn');
  }

  static bool _dispositionActive(String status) {
    final value = status.toLowerCase();
    return !{'zamknieta', 'zamknięta', 'zakończona', 'zakończone', 'anulowana', 'archiwum'}.contains(value);
  }

  static Future<void> check(WmApi api) async {
    final prefs = await SharedPreferences.getInstance();
    final seeded = prefs.getBool(_seededKey) ?? false;
    var machines = <Map<String, dynamic>>[];
    var tools = <Map<String, dynamic>>[];
    var dispositions = <Map<String, dynamic>>[];

    try {
      machines = await api.machines();
    } catch (_) {}
    try {
      tools = await api.tools();
    } catch (_) {}
    try {
      dispositions = await api.dispositions();
    } catch (_) {}

    final previousMachines = _decodeMap(prefs.getString(_machinesKey) ?? '');
    final previousTools = _decodeMap(prefs.getString(_toolsKey) ?? '');
    final previousDispositions = _decodeSet(prefs.getString(_dispositionsKey) ?? '');

    final currentMachines = <String, String>{};
    final currentTools = <String, String>{};
    final currentDispositions = <String>{};

    for (final row in machines) {
      final id = _id(row);
      if (id.isEmpty) continue;
      final status = _status(row);
      currentMachines[id] = status;
      final previous = previousMachines[id];
      if (seeded && previous != status && _machineAttention(status)) {
        final name = _name(row);
        await _emit(
          title: 'Maszyna $id wymaga uwagi',
          body: '${name.isEmpty ? 'Maszyna' : name} • ${status.isEmpty ? 'zmiana statusu' : status}',
          kind: 'machine',
          objectId: id,
        );
      }
    }

    for (final row in tools) {
      final id = _id(row);
      if (id.isEmpty) continue;
      final status = _status(row);
      currentTools[id] = status;
      final previous = previousTools[id];
      if (seeded && previous != status && _toolAttention(status)) {
        final name = _name(row);
        await _emit(
          title: 'Narzędzie $id wymaga uwagi',
          body: '${name.isEmpty ? 'Narzędzie' : name} • ${status.isEmpty ? 'zmiana statusu' : status}',
          kind: 'tool',
          objectId: id,
        );
      }
    }

    for (final row in dispositions) {
      final id = _id(row);
      if (id.isEmpty) continue;
      currentDispositions.add(id);
      final status = _status(row);
      if (seeded && !previousDispositions.contains(id) && _dispositionActive(status)) {
        final title = _name(row);
        await _emit(
          title: 'Nowa dyspozycja',
          body: title.isEmpty ? 'Dyspozycja $id' : title,
          kind: 'disposition',
          objectId: id,
        );
      }
    }

    if (machines.isNotEmpty) {
      await prefs.setString(_machinesKey, jsonEncode(currentMachines));
    }
    if (tools.isNotEmpty) {
      await prefs.setString(_toolsKey, jsonEncode(currentTools));
    }
    if (dispositions.isNotEmpty) {
      await prefs.setString(_dispositionsKey, jsonEncode(currentDispositions.toList()));
    }
    if (!seeded && (machines.isNotEmpty || tools.isNotEmpty || dispositions.isNotEmpty)) {
      await prefs.setBool(_seededKey, true);
    }
  }

  static Future<void> _emit({
    required String title,
    required String body,
    required String kind,
    required String objectId,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final now = DateTime.now();
    final rows = await history();
    rows.insert(0, <String, dynamic>{
      'title': title,
      'body': body,
      'kind': kind,
      'object_id': objectId,
      'created_at': now.toIso8601String(),
    });
    if (rows.length > 60) rows.removeRange(60, rows.length);
    await prefs.setString(_historyKey, jsonEncode(rows));

    if (!(prefs.getBool(_enabledKey) ?? true)) return;
    try {
      await _channel.invokeMethod<void>('showNotification', <String, dynamic>{
        'id': now.millisecondsSinceEpoch & 0x7fffffff,
        'title': title,
        'body': body,
      });
    } catch (_) {
      // Historia w WMM jest ważniejsza niż systemowy baner.
    }
  }

  static Future<List<Map<String, dynamic>>> history() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyKey) ?? '';
    if (raw.isEmpty) return <Map<String, dynamic>>[];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        return decoded.whereType<Map>().map(Map<String, dynamic>.from).toList();
      }
    } catch (_) {}
    return <Map<String, dynamic>>[];
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_historyKey);
  }
}

class WmmNotificationsScreen extends StatefulWidget {
  const WmmNotificationsScreen({super.key});

  @override
  State<WmmNotificationsScreen> createState() => _WmmNotificationsScreenState();
}

class _WmmNotificationsScreenState extends State<WmmNotificationsScreen> {
  bool busy = true;
  bool enabled = true;
  List<Map<String, dynamic>> rows = <Map<String, dynamic>>[];

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final history = await WmmNotifications.history();
    final isEnabled = await WmmNotifications.isEnabled();
    if (!mounted) return;
    setState(() {
      rows = history;
      enabled = isEnabled;
      busy = false;
    });
  }

  String _when(String raw) {
    final value = DateTime.tryParse(raw)?.toLocal();
    if (value == null) return '';
    final hh = value.hour.toString().padLeft(2, '0');
    final mm = value.minute.toString().padLeft(2, '0');
    final dd = value.day.toString().padLeft(2, '0');
    final mo = value.month.toString().padLeft(2, '0');
    return '$dd.$mo ${hh}:$mm';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Powiadomienia WMM'),
        actions: [
          IconButton(
            tooltip: 'Wyczyść historię',
            onPressed: rows.isEmpty
                ? null
                : () async {
                    await WmmNotifications.clear();
                    await load();
                  },
            icon: const Icon(Icons.delete_outline_rounded),
          ),
        ],
      ),
      body: busy
          ? const Center(child: CircularProgressIndicator(color: kOrange))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                RoundedCard(
                  child: SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    value: enabled,
                    activeThumbColor: kOrange,
                    title: const Text('Powiadomienia systemowe', style: TextStyle(fontWeight: FontWeight.w900)),
                    subtitle: const Text(
                      'WMM informuje o nowych dyspozycjach oraz zmianach awaryjnych maszyn i narzędzi.',
                      style: TextStyle(color: kMuted),
                    ),
                    onChanged: (value) async {
                      await WmmNotifications.setEnabled(value);
                      if (mounted) setState(() => enabled = value);
                    },
                  ),
                ),
                const SizedBox(height: 12),
                if (rows.isEmpty)
                  const RoundedCard(
                    child: Text('Brak nowych powiadomień.', style: TextStyle(color: kMuted)),
                  )
                else
                  ...rows.map((row) {
                    final title = (row['title'] ?? 'WMM').toString();
                    final body = (row['body'] ?? '').toString();
                    final when = _when((row['created_at'] ?? '').toString());
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: RoundedCard(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.notifications_active_rounded, color: kOrange),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
                                  if (body.isNotEmpty) ...[
                                    const SizedBox(height: 3),
                                    Text(body, style: const TextStyle(color: Color(0xFFC8CDD3))),
                                  ],
                                  if (when.isNotEmpty) ...[
                                    const SizedBox(height: 4),
                                    Text(when, style: const TextStyle(color: kMuted, fontSize: 12)),
                                  ],
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
              ],
            ),
    );
  }
}
'''


KOTLIN_MAIN = r'''package pl.cidex.cidex_mobile

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.pm.PackageManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val bridge = "pl.cidex.wmm/notifications"
    private val alertsChannel = "wmm_alerts"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        createNotificationChannel()
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, bridge).setMethodCallHandler { call, result ->
            when (call.method) {
                "requestPermission" -> {
                    if (Build.VERSION.SDK_INT >= 33 &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                    ) {
                        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 9301)
                    }
                    result.success(true)
                }
                "showNotification" -> {
                    val id = call.argument<Int>("id") ?: 1
                    val title = call.argument<String>("title") ?: "WMM"
                    val body = call.argument<String>("body") ?: ""
                    if (Build.VERSION.SDK_INT >= 33 &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                    ) {
                        result.success(false)
                    } else {
                        val manager = getSystemService(NotificationManager::class.java)
                        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            Notification.Builder(this, alertsChannel)
                        } else {
                            @Suppress("DEPRECATION")
                            Notification.Builder(this)
                        }
                        builder
                            .setSmallIcon(android.R.drawable.stat_notify_more)
                            .setContentTitle(title)
                            .setContentText(body)
                            .setStyle(Notification.BigTextStyle().bigText(body))
                            .setAutoCancel(true)
                        manager.notify(id, builder.build())
                        result.success(true)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                alertsChannel,
                "WMM — alerty warsztatu",
                NotificationManager.IMPORTANCE_DEFAULT,
            )
            channel.description = "Awarie maszyn, narzędzia i nowe dyspozycje z Warsztat Menager"
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }
}
'''


def _replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f'Nie znaleziono punktu montażu: {label}')
    return source.replace(old, new, 1)


def main() -> None:
    main_file = Path('lib/main.dart')
    source = main_file.read_text(encoding='utf-8')

    if "import 'dart:io';\n" not in source:
        source = source.replace("import 'dart:convert';\n", "import 'dart:convert';\nimport 'dart:io';\n", 1)
    if "import 'package:flutter/services.dart';\n" not in source:
        source = source.replace(
            "import 'package:flutter/material.dart';\n",
            "import 'package:flutter/material.dart';\nimport 'package:flutter/services.dart';\n",
            1,
        )

    get_pattern = re.compile(
        r"  Future<Map<String, dynamic>> getJson\(String path\) async \{.*?\n  \}\n\n  Future<Map<String, dynamic>> postJson",
        re.S,
    )
    get_replacement = r'''  Future<Map<String, dynamic>> getJson(String path) async {
    Object? lastError;
    for (var attempt = 0; attempt < 3; attempt++) {
      try {
        final response = await http
            .get(_uri(path), headers: headers)
            .timeout(const Duration(seconds: 7));
        final payload = await _decode(response);
        WmmConnectionMonitor.markOnline();
        return payload;
      } on ApiException {
        rethrow;
      } catch (error) {
        lastError = error;
        WmmConnectionMonitor.markFailure();
        if (attempt < 2) {
          await Future.delayed(Duration(milliseconds: attempt == 0 ? 350 : 900));
        }
      }
    }
    throw ApiException(_wmmFriendlyNetworkMessage(lastError));
  }

  Future<Map<String, dynamic>> postJson'''
    source, count = get_pattern.subn(get_replacement, source, count=1)
    if count != 1:
        raise RuntimeError('Nie znaleziono getJson do stabilizacji')

    source = source.replace(
        "throw ApiException('Nie udało się wysłać danych do Warsztat Menager: $error');",
        "throw ApiException(_wmmFriendlyNetworkMessage(error, writing: true));",
    )
    source = source.replace(
        "throw ApiException('Nie udało się wysłać zdjęcia: $error');",
        "throw ApiException(_wmmFriendlyNetworkMessage(error, writing: true));",
    )
    source = source.replace(
        "throw ApiException('Nie udało się wysłać zdjęcia narzędzia: $error');",
        "throw ApiException(_wmmFriendlyNetworkMessage(error, writing: true));",
    )

    source = _replace_required(
        source,
        'class _HomeScreenState extends State<HomeScreen> {',
        'class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {',
        'lifecycle ekranu głównego',
    )
    source = _replace_required(
        source,
        "  String lastSync = '—';\n",
        "  String lastSync = '—';\n  Timer? _wmmMonitorTimer;\n  bool _wmmBackgroundCheckBusy = false;\n",
        'pola monitoringu WMM',
    )

    init_old = '''  @override
  void initState() {
    super.initState();
    config = widget.initialConfig;
    WidgetsBinding.instance.addPostFrameCallback((_) => refresh());
  }
'''
    init_new = '''  @override
  void initState() {
    super.initState();
    config = widget.initialConfig;
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await WmmNotifications.initialize();
      await refresh();
      await WmmNotifications.check(api);
      _wmmMonitorTimer = Timer.periodic(
        const Duration(seconds: 45),
        (_) => _wmmBackgroundCheck(),
      );
    });
  }

  @override
  void dispose() {
    _wmmMonitorTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      refresh();
      WmmNotifications.check(api);
    }
  }

  Future<void> _wmmBackgroundCheck() async {
    if (_wmmBackgroundCheckBusy || config.token.trim().isEmpty) return;
    _wmmBackgroundCheckBusy = true;
    try {
      await api.info();
      if (!mounted) return;
      setState(() {
        connected = true;
        connectionText = 'WM online • ostatni kontakt ${TimeOfDay.now().format(context)}';
      });
      await WmmNotifications.check(api);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        connected = false;
        connectionText = error.toString();
      });
    } finally {
      _wmmBackgroundCheckBusy = false;
    }
  }
'''
    source = _replace_required(source, init_old, init_new, 'monitor połączenia i lifecycle')

    notifications_tile = '''                  ActionTile(
                    color: kPurple,
                    icon: Icons.notifications_active_rounded,
                    title: 'Powiadomienia',
                    subtitle: 'Alerty z Warsztat Menager',
                    onTap: () => open(const WmmNotificationsScreen()),
                  ),
'''
    tools_marker = '''                  ActionTile(
                    color: kOrange,
                    icon: Icons.handyman_rounded,
                    title: 'Narzędzia',
'''
    if notifications_tile not in source:
        source = _replace_required(
            source,
            tools_marker,
            notifications_tile + tools_marker,
            'kafelek powiadomień',
        )

    source = source.replace(
        "Text('Warsztat Menager Mobile BETA', style: TextStyle(color: kMuted, fontWeight: FontWeight.w700)),",
        "Text('Warsztat Menager Mobile BETA • v0.5.6', style: TextStyle(color: kMuted, fontWeight: FontWeight.w700)),",
        1,
    )

    if 'class WmmNotifications {' not in source:
        source = source.rstrip() + '\n\n' + DART_RUNTIME.strip() + '\n'

    main_file.write_text(source, encoding='utf-8')

    manifest = Path('android/app/src/main/AndroidManifest.xml')
    text = manifest.read_text(encoding='utf-8')
    permission = '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />'
    if permission not in text:
        start = text.find('<manifest')
        end = text.find('>', start)
        if start < 0 or end < 0:
            raise RuntimeError('Nie rozpoznano AndroidManifest.xml')
        text = text[: end + 1] + '\n    ' + permission + text[end + 1 :]
        manifest.write_text(text, encoding='utf-8')

    activity = Path('android/app/src/main/kotlin/pl/cidex/cidex_mobile/MainActivity.kt')
    activity.parent.mkdir(parents=True, exist_ok=True)
    activity.write_text(KOTLIN_MAIN, encoding='utf-8')


if __name__ == '__main__':
    main()
