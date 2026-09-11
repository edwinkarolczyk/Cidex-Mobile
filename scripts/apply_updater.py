from __future__ import annotations

from pathlib import Path

APP_VERSION = "0.5.8"

DART_EXTRA = r'''
const String kWmmCurrentVersion = '0.5.8';
const String kWmmReleaseApi = 'https://api.github.com/repos/edwinkarolczyk/Cidex-Mobile/releases/latest';

int wmmCompareVersions(String left, String right) {
  List<int> parts(String value) {
    final match = RegExp(r'(\d+)\.(\d+)\.(\d+)').firstMatch(value);
    if (match == null) return const <int>[0, 0, 0];
    return <int>[
      int.tryParse(match.group(1) ?? '') ?? 0,
      int.tryParse(match.group(2) ?? '') ?? 0,
      int.tryParse(match.group(3) ?? '') ?? 0,
    ];
  }

  final a = parts(left);
  final b = parts(right);
  for (var i = 0; i < 3; i++) {
    if (a[i] != b[i]) return a[i].compareTo(b[i]);
  }
  return 0;
}

class WmmReleaseInfo {
  const WmmReleaseInfo({
    required this.version,
    required this.apkUrl,
    required this.apkSize,
    required this.title,
  });

  final String version;
  final String apkUrl;
  final int apkSize;
  final String title;
}

class WmmUpdater {
  static const MethodChannel _channel = MethodChannel('pl.cidex.wmm/updater');
  static bool _startupPromptShown = false;

  static Future<WmmReleaseInfo?> latest() async {
    try {
      final response = await http.get(
        Uri.parse(kWmmReleaseApi),
        headers: const <String, String>{
          'Accept': 'application/vnd.github+json',
          'User-Agent': 'Warsztat-Menager-Mobile',
          'X-GitHub-Api-Version': '2022-11-28',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 404) return null;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException('Nie udało się sprawdzić aktualizacji: HTTP ${response.statusCode}.');
      }

      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is! Map) return null;
      final map = Map<String, dynamic>.from(decoded);
      final title = (map['name'] ?? map['tag_name'] ?? '').toString().trim();
      final versionMatch = RegExp(r'(\d+\.\d+\.\d+)').firstMatch(title);
      final version = versionMatch?.group(1) ?? '';
      if (version.isEmpty) return null;

      final assets = (map['assets'] as List? ?? const <dynamic>[])
          .whereType<Map>()
          .map(Map<String, dynamic>.from)
          .toList();
      Map<String, dynamic>? apk;
      for (final item in assets) {
        final name = (item['name'] ?? '').toString();
        if (name == 'WMM-BETA.apk') {
          apk = item;
          break;
        }
      }
      apk ??= assets.where((item) => (item['name'] ?? '').toString().toLowerCase().endsWith('.apk')).firstOrNull;
      if (apk == null) return null;
      final apkUrl = (apk['browser_download_url'] ?? '').toString().trim();
      if (apkUrl.isEmpty) return null;

      return WmmReleaseInfo(
        version: version,
        apkUrl: apkUrl,
        apkSize: (apk['size'] as num?)?.toInt() ?? 0,
        title: title.isEmpty ? 'WMM $version BETA' : title,
      );
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Nie udało się sprawdzić aktualizacji WMM: $error');
    }
  }

  static bool isNewer(WmmReleaseInfo info) =>
      wmmCompareVersions(info.version, kWmmCurrentVersion) > 0;

  static Future<void> checkAndPrompt(BuildContext context) async {
    if (_startupPromptShown) return;
    try {
      final info = await latest();
      if (info == null || !isNewer(info) || !context.mounted) return;
      _startupPromptShown = true;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Dostępna aktualizacja WMM'),
          content: Text(
            'Masz WMM $kWmmCurrentVersion BETA. Dostępna jest wersja ${info.version} BETA.\n\n'
            'WMM może pobrać APK z GitHuba i uruchomić instalator Androida.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Później'),
            ),
            FilledButton.icon(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const WmmUpdateScreen()),
                );
              },
              icon: const Icon(Icons.system_update_alt_rounded),
              label: const Text('Aktualizuj'),
            ),
          ],
        ),
      );
    } catch (_) {
      // Sprawdzenie przy starcie nie może blokować pracy WMM.
    }
  }

  static Future<String> _cachePath() async {
    try {
      final path = await _channel.invokeMethod<String>('getCachePath');
      if (path != null && path.trim().isNotEmpty) return path.trim();
    } catch (_) {}
    return '${Directory.systemTemp.path}/WMM-BETA-update.apk';
  }

  static Future<void> downloadAndInstall(
    WmmReleaseInfo info, {
    required void Function(double value) onProgress,
  }) async {
    final path = await _cachePath();
    final file = File(path);
    if (await file.exists()) await file.delete();

    final client = http.Client();
    IOSink? sink;
    try {
      final request = http.Request('GET', Uri.parse(info.apkUrl));
      request.headers['Accept'] = 'application/octet-stream';
      request.headers['User-Agent'] = 'Warsztat-Menager-Mobile';
      final response = await client.send(request).timeout(const Duration(seconds: 20));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException('Pobieranie aktualizacji nie powiodło się: HTTP ${response.statusCode}.');
      }
      final total = response.contentLength ?? info.apkSize;
      var received = 0;
      sink = file.openWrite();
      await for (final chunk in response.stream) {
        sink.add(chunk);
        received += chunk.length;
        if (total > 0) onProgress((received / total).clamp(0.0, 1.0));
      }
      await sink.flush();
      await sink.close();
      sink = null;

      if (!await file.exists() || await file.length() == 0) {
        throw ApiException('Pobrany plik aktualizacji jest pusty.');
      }
      onProgress(1.0);

      final result = await _channel.invokeMethod<dynamic>(
        'installApk',
        <String, dynamic>{'path': file.path},
      );
      if (result is Map) {
        final map = Map<String, dynamic>.from(result);
        if (map['ok'] == false && map['permission_required'] != true) {
          throw ApiException((map['error'] ?? 'Nie udało się uruchomić instalatora Androida.').toString());
        }
      }
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Nie udało się pobrać lub uruchomić aktualizacji: $error');
    } finally {
      if (sink != null) await sink.close();
      client.close();
    }
  }
}

class WmmUpdateScreen extends StatefulWidget {
  const WmmUpdateScreen({super.key});

  @override
  State<WmmUpdateScreen> createState() => _WmmUpdateScreenState();
}

class _WmmUpdateScreenState extends State<WmmUpdateScreen> {
  WmmReleaseInfo? latestInfo;
  bool checking = true;
  bool downloading = false;
  double progress = 0;
  String error = '';
  String message = '';

  @override
  void initState() {
    super.initState();
    check();
  }

  Future<void> check() async {
    setState(() {
      checking = true;
      error = '';
      message = '';
    });
    try {
      final info = await WmmUpdater.latest();
      if (!mounted) return;
      setState(() => latestInfo = info);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => checking = false);
    }
  }

  Future<void> install() async {
    final info = latestInfo;
    if (info == null || downloading) return;
    setState(() {
      downloading = true;
      progress = 0;
      error = '';
      message = 'Pobieranie aktualizacji…';
    });
    try {
      await WmmUpdater.downloadAndInstall(
        info,
        onProgress: (value) {
          if (mounted) setState(() => progress = value);
        },
      );
      if (!mounted) return;
      setState(() {
        message = 'APK pobrane. Android uruchomi instalator. Jeśli pojawi się ekran „Instaluj nieznane aplikacje”, zezwól WMM — instalator otworzy się po powrocie.';
      });
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => downloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final info = latestInfo;
    final newer = info != null && WmmUpdater.isNewer(info);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Aktualizacje WMM'),
        actions: [
          IconButton(
            onPressed: checking || downloading ? null : check,
            tooltip: 'Sprawdź ponownie',
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          RoundedCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Aktualna wersja', style: TextStyle(color: kMuted)),
                const SizedBox(height: 4),
                const Text(
                  'WMM $kWmmCurrentVersion BETA',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 14),
                const Text('Najnowsza wersja z GitHuba', style: TextStyle(color: kMuted)),
                const SizedBox(height: 4),
                Text(
                  checking ? 'Sprawdzanie…' : (info == null ? 'Brak opublikowanej wersji' : 'WMM ${info.version} BETA'),
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (checking)
            const Center(child: CircularProgressIndicator(color: kOrange))
          else if (error.isNotEmpty)
            RoundedCard(child: Text(error, style: const TextStyle(color: kRed)))
          else if (info == null)
            const RoundedCard(
              child: Text(
                'Na GitHubie nie ma jeszcze wersji opublikowanej dla automatycznych aktualizacji.',
                style: TextStyle(color: kMuted),
              ),
            )
          else if (!newer)
            const RoundedCard(
              child: Row(
                children: [
                  Icon(Icons.check_circle_rounded, color: kGreen),
                  SizedBox(width: 10),
                  Expanded(child: Text('Masz najnowszą wersję WMM.')),
                ],
              ),
            )
          else ...[
            RoundedCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Dostępna aktualizacja ${info.version} BETA',
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'WMM pobierze APK bezpośrednio z GitHub Releases. Po pobraniu Android poprosi tylko o potwierdzenie aktualizacji.',
                    style: TextStyle(color: Color(0xFFC8CDD3), height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (downloading) ...[
              LinearProgressIndicator(value: progress > 0 ? progress : null, color: kOrange),
              const SizedBox(height: 8),
              Text('${(progress * 100).round()}%', textAlign: TextAlign.center),
            ],
            const SizedBox(height: 10),
            SizedBox(
              height: 54,
              child: FilledButton.icon(
                onPressed: downloading ? null : install,
                icon: const Icon(Icons.download_rounded),
                label: Text(downloading ? 'POBIERANIE…' : 'POBIERZ I ZAINSTALUJ'),
              ),
            ),
          ],
          if (message.isNotEmpty) ...[
            const SizedBox(height: 12),
            RoundedCard(child: Text(message, style: const TextStyle(color: Color(0xFFC8CDD3)))),
          ],
        ],
      ),
    );
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

    if "import 'dart:io';\n" not in source:
        source = source.replace("import 'dart:convert';\n", "import 'dart:convert';\nimport 'dart:io';\n", 1)
    if "import 'package:flutter/services.dart';\n" not in source:
        source = source.replace(
            "import 'package:flutter/material.dart';\n",
            "import 'package:flutter/material.dart';\nimport 'package:flutter/services.dart';\n",
            1,
        )

    source = replace_required(
        source,
        "      await WmmNotifications.initialize();\n      await refresh();\n",
        "      await WmmNotifications.initialize();\n      WmmUpdater.checkAndPrompt(context);\n      await refresh();\n",
        'sprawdzenie aktualizacji przy starcie',
    )

    tools_marker = '''                  ActionTile(
                    color: kOrange,
                    icon: Icons.handyman_rounded,
                    title: 'Narzędzia',
'''
    update_tile = '''                  ActionTile(
                    color: kBlue,
                    icon: Icons.system_update_alt_rounded,
                    title: 'Aktualizacje',
                    subtitle: 'WMM 0.5.8 BETA',
                    onTap: () => open(const WmmUpdateScreen()),
                  ),
'''
    if update_tile not in source:
        source = replace_required(source, tools_marker, update_tile + tools_marker, 'kafelek aktualizacji')

    if 'class WmmUpdater {' not in source:
        source = source.rstrip() + '\n\n' + DART_EXTRA.strip() + '\n'

    main_file.write_text(source, encoding='utf-8')

    manifest = Path('android/app/src/main/AndroidManifest.xml')
    text = manifest.read_text(encoding='utf-8')
    permission = '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />'
    if permission not in text:
        start = text.find('<manifest')
        end = text.find('>', start)
        if start < 0 or end < 0:
            raise RuntimeError('Nie rozpoznano AndroidManifest.xml')
        text = text[: end + 1] + '\n    ' + permission + text[end + 1 :]

    provider = '''        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/wmm_file_paths" />
        </provider>
'''
    if 'androidx.core.content.FileProvider' not in text:
        text = text.replace('    </application>', provider + '    </application>', 1)
    manifest.write_text(text, encoding='utf-8')

    paths = Path('android/app/src/main/res/xml/wmm_file_paths.xml')
    paths.parent.mkdir(parents=True, exist_ok=True)
    paths.write_text(
        '''<?xml version="1.0" encoding="utf-8"?>\n<paths xmlns:android="http://schemas.android.com/apk/res/android">\n    <cache-path name="wmm_updates" path="." />\n</paths>\n''',
        encoding='utf-8',
    )

    activity = Path('android/app/src/main/kotlin/pl/cidex/cidex_mobile/MainActivity.kt')
    kotlin = activity.read_text(encoding='utf-8')
    for marker, addition in (
        ('import android.content.Intent\n', 'import android.content.Intent\nimport android.net.Uri\nimport android.provider.Settings\n'),
        ('import io.flutter.plugin.common.MethodChannel\n', 'import io.flutter.plugin.common.MethodChannel\nimport androidx.core.content.FileProvider\nimport java.io.File\n'),
    ):
        if addition not in kotlin:
            kotlin = kotlin.replace(marker, addition, 1)

    kotlin = replace_required(
        kotlin,
        '    private val alertsChannel = "wmm_alerts"\n',
        '    private val alertsChannel = "wmm_alerts"\n'
        '    private val updaterBridge = "pl.cidex.wmm/updater"\n'
        '    private var pendingApkPath: String? = null\n',
        'pola updatera Android',
    )
    kotlin = replace_required(
        kotlin,
        '        createNotificationChannel()\n',
        '        createNotificationChannel()\n        setupUpdaterChannel(flutterEngine)\n',
        'kanał updatera Android',
    )

    updater_methods = r'''
    private fun setupUpdaterChannel(flutterEngine: FlutterEngine) {
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, updaterBridge).setMethodCallHandler { call, result ->
            when (call.method) {
                "getCachePath" -> {
                    result.success(File(cacheDir, "WMM-BETA-update.apk").absolutePath)
                }
                "installApk" -> {
                    val path = call.argument<String>("path")?.trim().orEmpty()
                    if (path.isEmpty()) {
                        result.success(mapOf("ok" to false, "error" to "Brak pliku APK."))
                        return@setMethodCallHandler
                    }
                    val file = File(path)
                    if (!file.isFile) {
                        result.success(mapOf("ok" to false, "error" to "Nie znaleziono pobranego APK."))
                        return@setMethodCallHandler
                    }
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !packageManager.canRequestPackageInstalls()) {
                        pendingApkPath = file.absolutePath
                        val settingsIntent = Intent(
                            Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                            Uri.parse("package:$packageName"),
                        )
                        startActivity(settingsIntent)
                        result.success(mapOf("ok" to false, "permission_required" to true))
                    } else {
                        launchApkInstaller(file.absolutePath)
                        result.success(mapOf("ok" to true))
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun launchApkInstaller(path: String) {
        val file = File(path)
        if (!file.isFile) return
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", file)
        val installIntent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        startActivity(installIntent)
    }

    override fun onResume() {
        super.onResume()
        val path = pendingApkPath ?: return
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O || packageManager.canRequestPackageInstalls()) {
            pendingApkPath = null
            launchApkInstaller(path)
        }
    }

'''
    kotlin = replace_required(
        kotlin,
        '    private fun createNotificationChannel() {\n',
        updater_methods + '    private fun createNotificationChannel() {\n',
        'metody updatera Android',
    )
    activity.write_text(kotlin, encoding='utf-8')


if __name__ == '__main__':
    main()
