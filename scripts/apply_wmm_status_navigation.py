from __future__ import annotations

from pathlib import Path


DART_EXTRA = r'''
String wmmMachineStatusLabel(dynamic raw) {
  final value = (raw ?? '').toString().trim();
  switch (value.toLowerCase()) {
    case 'ok':
    case 'sprawna':
    case 'sprawne':
    case 'sprawny':
    case 'dziala':
    case 'działa':
      return 'Sprawna';
    case 'alert':
    case 'serwis':
    case 'przeglad':
    case 'przegląd':
    case 'serwis/przeglad':
    case 'serwis/przegląd':
    case 'serwis / przegląd':
      return 'Serwis / przegląd';
    case 'warn':
    case 'warm':
    case 'warning':
    case 'awaria':
    case 'uszkodzona':
    case 'uszkodzone':
    case 'stop':
      return 'Awaria';
    default:
      return value.isEmpty ? '—' : value;
  }
}

Future<void> wmmOpenNotificationTarget(
  BuildContext context,
  WmApi api,
  String kind,
  String objectId,
) async {
  final type = kind.trim().toLowerCase();
  final id = objectId.trim();
  if (id.isEmpty || !context.mounted) return;

  Widget? target;
  if (type == 'machine') {
    target = MachineScreen(api: api, machineId: id);
  } else if (type == 'tool') {
    target = ToolScreen(api: api, toolId: id);
  } else if (type == 'disposition') {
    target = WmmDispositionNotificationScreen(api: api, dispositionId: id);
  }
  if (target == null || !context.mounted) return;
  await Navigator.of(context).push(MaterialPageRoute(builder: (_) => target!));
}

class WmmDispositionNotificationScreen extends StatefulWidget {
  const WmmDispositionNotificationScreen({
    super.key,
    required this.api,
    required this.dispositionId,
  });

  final WmApi api;
  final String dispositionId;

  @override
  State<WmmDispositionNotificationScreen> createState() => _WmmDispositionNotificationScreenState();
}

class _WmmDispositionNotificationScreenState extends State<WmmDispositionNotificationScreen> {
  Map<String, dynamic> row = <String, dynamic>{};
  bool busy = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    load();
  }

  String _id(Map<String, dynamic> item) =>
      (item['id'] ?? item['nr'] ?? item['numer'] ?? item['kod'] ?? '').toString().trim();

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final rows = await widget.api.dispositions();
      final needle = widget.dispositionId.trim().toLowerCase();
      final found = rows.where((item) => _id(item).toLowerCase() == needle).toList();
      if (!mounted) return;
      if (found.isEmpty) {
        setState(() => error = 'Nie znaleziono dyspozycji ${widget.dispositionId} w aktualnym WM.');
      } else {
        setState(() => row = found.first);
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Dyspozycja ${widget.dispositionId}')),
      body: busy
          ? const Center(child: CircularProgressIndicator(color: kOrange))
          : error.isNotEmpty
              ? ErrorState(message: error, onRetry: load)
              : RefreshIndicator(
                  onRefresh: load,
                  color: kOrange,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      RoundedCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: row.entries.map((entry) {
                            final value = entry.value;
                            if (value is Map || value is List) return const SizedBox.shrink();
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 5),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  SizedBox(
                                    width: 118,
                                    child: Text(entry.key, style: const TextStyle(color: kMuted)),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      (value ?? '—').toString(),
                                      style: const TextStyle(fontWeight: FontWeight.w700),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ],
                  ),
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
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val bridge = "pl.cidex.wmm/notifications"
    private val alertsChannel = "wmm_alerts"
    private var notificationsBridge: MethodChannel? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        createNotificationChannel()
        val channel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, bridge)
        notificationsBridge = channel
        channel.setMethodCallHandler { call, result ->
            when (call.method) {
                "requestPermission" -> {
                    if (Build.VERSION.SDK_INT >= 33 &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                    ) {
                        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 9301)
                    }
                    result.success(true)
                }
                "takeNotificationTarget" -> {
                    result.success(takeNotificationTarget())
                }
                "showNotification" -> {
                    val id = call.argument<Int>("id") ?: 1
                    val title = call.argument<String>("title") ?: "WMM"
                    val body = call.argument<String>("body") ?: ""
                    val kind = call.argument<String>("kind") ?: ""
                    val objectId = call.argument<String>("objectId") ?: ""
                    if (Build.VERSION.SDK_INT >= 33 &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                    ) {
                        result.success(false)
                    } else {
                        val tapIntent = Intent(this, MainActivity::class.java).apply {
                            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
                            putExtra("wmm_notification_kind", kind)
                            putExtra("wmm_notification_object_id", objectId)
                        }
                        val pendingIntent = PendingIntent.getActivity(
                            this,
                            id,
                            tapIntent,
                            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
                        )
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
                            .setContentIntent(pendingIntent)
                            .setAutoCancel(true)
                        manager.notify(id, builder.build())
                        result.success(true)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        notificationTarget(intent)?.let { target ->
            notificationsBridge?.invokeMethod("notificationTap", target)
            clearNotificationTarget(intent)
        }
    }

    private fun notificationTarget(source: Intent = intent): Map<String, String>? {
        val kind = source.getStringExtra("wmm_notification_kind")?.trim().orEmpty()
        val objectId = source.getStringExtra("wmm_notification_object_id")?.trim().orEmpty()
        if (kind.isEmpty() || objectId.isEmpty()) return null
        return mapOf("kind" to kind, "objectId" to objectId)
    }

    private fun clearNotificationTarget(source: Intent = intent) {
        source.removeExtra("wmm_notification_kind")
        source.removeExtra("wmm_notification_object_id")
    }

    private fun takeNotificationTarget(): Map<String, String>? {
        val target = notificationTarget() ?: return null
        clearNotificationTarget()
        return target
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


def replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f'Nie znaleziono punktu montażu: {label}')
    return source.replace(old, new, 1)


def main() -> None:
    main_file = Path('lib/main.dart')
    source = main_file.read_text(encoding='utf-8')

    source = replace_required(
        source,
        "StatusPill(text: '${item['status_label'] ?? item['status'] ?? '—'}', color: color),",
        "StatusPill(text: wmmMachineStatusLabel(item['status_label'] ?? item['status']), color: color),",
        'status maszyny na liście',
    )
    source = replace_required(
        source,
        "StatusPill(text: '${machine['status_label'] ?? status}', color: color),",
        "StatusPill(text: wmmMachineStatusLabel(machine['status_label'] ?? status), color: color),",
        'status maszyny w szczegółach',
    )

    machine_notification_old = """          body: '${name.isEmpty ? 'Maszyna' : name} • ${status.isEmpty ? 'zmiana statusu' : status}',
          kind: 'machine',
"""
    machine_notification_new = """          body: '${name.isEmpty ? 'Maszyna' : name} • ${wmmMachineStatusLabel(status)}',
          kind: 'machine',
"""
    source = replace_required(
        source,
        machine_notification_old,
        machine_notification_new,
        'polski status w powiadomieniu maszyny',
    )

    source = replace_required(
        source,
        "      await _channel.invokeMethod<void>('requestPermission');\n",
        "      _channel.setMethodCallHandler((call) async {\n"
        "        if (call.method != 'notificationTap') return;\n"
        "        final args = Map<String, dynamic>.from(call.arguments as Map? ?? const {});\n"
        "        final kind = (args['kind'] ?? '').toString();\n"
        "        final objectId = (args['objectId'] ?? '').toString();\n"
        "        if (kind.isNotEmpty && objectId.isNotEmpty) onTap?.call(kind, objectId);\n"
        "      });\n"
        "      await _channel.invokeMethod<void>('requestPermission');\n",
        'obsługa kliknięcia powiadomienia z Androida',
    )

    source = replace_required(
        source,
        "class WmmNotifications {\n  static const MethodChannel _channel = MethodChannel('pl.cidex.wmm/notifications');\n",
        "class WmmNotifications {\n"
        "  static const MethodChannel _channel = MethodChannel('pl.cidex.wmm/notifications');\n"
        "  static void Function(String kind, String objectId)? onTap;\n",
        'callback powiadomienia',
    )

    history_marker = """  static Future<List<Map<String, dynamic>>> history() async {
"""
    take_target = """  static Future<Map<String, String>?> takeLaunchTarget() async {
    try {
      final raw = await _channel.invokeMethod<dynamic>('takeNotificationTarget');
      if (raw is! Map) return null;
      final map = Map<String, dynamic>.from(raw);
      final kind = (map['kind'] ?? '').toString().trim();
      final objectId = (map['objectId'] ?? '').toString().trim();
      if (kind.isEmpty || objectId.isEmpty) return null;
      return <String, String>{'kind': kind, 'objectId': objectId};
    } catch (_) {
      return null;
    }
  }

"""
    source = replace_required(source, history_marker, take_target + history_marker, 'odczyt celu powiadomienia')

    source = replace_required(
        source,
        "        'body': body,\n      });",
        "        'body': body,\n        'kind': kind,\n        'objectId': objectId,\n      });",
        'cel w powiadomieniu systemowym',
    )

    source = replace_required(
        source,
        "class WmmNotificationsScreen extends StatefulWidget {\n  const WmmNotificationsScreen({super.key});\n",
        "class WmmNotificationsScreen extends StatefulWidget {\n"
        "  const WmmNotificationsScreen({super.key, required this.api});\n"
        "  final WmApi api;\n",
        'API ekranu powiadomień',
    )
    source = replace_required(
        source,
        "onTap: () => open(const WmmNotificationsScreen()),",
        "onTap: () => open(WmmNotificationsScreen(api: api)),",
        'otwieranie ekranu powiadomień',
    )

    notification_card_old = """                    return Padding(
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
"""
    notification_card_new = """                    final kind = (row['kind'] ?? '').toString();
                    final objectId = (row['object_id'] ?? '').toString();
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: kind.isEmpty || objectId.isEmpty
                            ? null
                            : () => wmmOpenNotificationTarget(context, widget.api, kind, objectId),
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
                              if (kind.isNotEmpty && objectId.isNotEmpty)
                                const Padding(
                                  padding: EdgeInsets.only(top: 2),
                                  child: Icon(Icons.chevron_right_rounded, color: kMuted),
                                ),
                            ],
                          ),
                        ),
                      ),
                    );
"""
    source = replace_required(
        source,
        notification_card_old,
        notification_card_new,
        'klikane powiadomienia w WMM',
    )

    source = replace_required(
        source,
        "    WidgetsBinding.instance.addObserver(this);\n    WidgetsBinding.instance.addPostFrameCallback((_) async {\n      await WmmNotifications.initialize();",
        "    WidgetsBinding.instance.addObserver(this);\n"
        "    WmmNotifications.onTap = (kind, objectId) {\n"
        "      if (mounted) wmmOpenNotificationTarget(context, api, kind, objectId);\n"
        "    };\n"
        "    WidgetsBinding.instance.addPostFrameCallback((_) async {\n"
        "      await WmmNotifications.initialize();",
        'callback na ekranie głównym',
    )
    source = replace_required(
        source,
        "      await WmmNotifications.check(api);\n      _wmmMonitorTimer = Timer.periodic(",
        "      await WmmNotifications.check(api);\n"
        "      await _openPendingSystemNotification();\n"
        "      _wmmMonitorTimer = Timer.periodic(",
        'otwarcie powiadomienia po starcie',
    )
    source = replace_required(
        source,
        "  void dispose() {\n    _wmmMonitorTimer?.cancel();\n    WidgetsBinding.instance.removeObserver(this);",
        "  void dispose() {\n"
        "    _wmmMonitorTimer?.cancel();\n"
        "    WmmNotifications.onTap = null;\n"
        "    WidgetsBinding.instance.removeObserver(this);",
        'czyszczenie callbacku',
    )
    source = replace_required(
        source,
        "      refresh();\n      WmmNotifications.check(api);\n    }\n  }\n\n  Future<void> _wmmBackgroundCheck() async {",
        "      refresh();\n"
        "      WmmNotifications.check(api);\n"
        "      _openPendingSystemNotification();\n"
        "    }\n"
        "  }\n\n"
        "  Future<void> _openPendingSystemNotification() async {\n"
        "    final target = await WmmNotifications.takeLaunchTarget();\n"
        "    if (!mounted || target == null) return;\n"
        "    await wmmOpenNotificationTarget(\n"
        "      context,\n"
        "      api,\n"
        "      target['kind'] ?? '',\n"
        "      target['objectId'] ?? '',\n"
        "    );\n"
        "  }\n\n"
        "  Future<void> _wmmBackgroundCheck() async {",
        'otwarcie powiadomienia po wznowieniu',
    )

    if 'String wmmMachineStatusLabel(dynamic raw)' not in source:
        source = source.rstrip() + '\n\n' + DART_EXTRA.strip() + '\n'
    main_file.write_text(source, encoding='utf-8')

    activity = Path('android/app/src/main/kotlin/pl/cidex/cidex_mobile/MainActivity.kt')
    activity.parent.mkdir(parents=True, exist_ok=True)
    activity.write_text(KOTLIN_MAIN, encoding='utf-8')


if __name__ == '__main__':
    main()
