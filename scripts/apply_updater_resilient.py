from __future__ import annotations

from pathlib import Path
import re

APP_VERSION = "0.5.12"


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    start_marker = "  static Future<void> downloadAndInstall(\n"
    end_marker = "\n}\n\nclass WmmUpdateScreen extends StatefulWidget"
    start = source.find(start_marker)
    end = source.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError("Nie znaleziono metody WmmUpdater.downloadAndInstall")

    replacement = r'''  static Future<void> downloadAndInstall(
    WmmReleaseInfo info, {
    required void Function(double value) onProgress,
  }) async {
    final path = await _cachePath();
    final file = File(path);
    if (await file.exists()) await file.delete();

    const maxAttempts = 4;
    Object? lastError;
    var downloaded = false;

    for (var attempt = 1; attempt <= maxAttempts; attempt++) {
      http.Client? client;
      IOSink? sink;
      try {
        var existing = await file.exists() ? await file.length() : 0;
        if (info.apkSize > 0 && existing > info.apkSize) {
          await file.delete();
          existing = 0;
        }
        if (info.apkSize > 0 && existing == info.apkSize) {
          onProgress(1.0);
          downloaded = true;
          break;
        }

        client = http.Client();
        final request = http.Request('GET', Uri.parse(info.apkUrl));
        request.followRedirects = true;
        request.maxRedirects = 10;
        request.headers['Accept'] = 'application/octet-stream';
        request.headers['User-Agent'] = 'Warsztat-Menager-Mobile';
        if (existing > 0) {
          request.headers['Range'] = 'bytes=$existing-';
          if (info.apkSize > 0) {
            onProgress((existing / info.apkSize).clamp(0.0, 1.0).toDouble());
          }
        }

        final response = await client
            .send(request)
            .timeout(const Duration(seconds: 20));

        if (existing > 0 && response.statusCode == 200) {
          // CDN nie przyjął Range. Zaczynamy czysty transfer zamiast doklejać duplikat.
          await file.delete();
          lastError = Exception('Serwer nie obsłużył wznowienia transferu.');
          continue;
        }
        if (response.statusCode != 200 && response.statusCode != 206) {
          throw ApiException(
            'Pobieranie aktualizacji nie powiodło się: HTTP ${response.statusCode}.',
          );
        }

        final expectedTotal = info.apkSize > 0
            ? info.apkSize
            : existing + (response.contentLength ?? 0);
        var received = existing;
        sink = file.openWrite(
          mode: existing > 0 ? FileMode.append : FileMode.write,
        );

        await for (final chunk in response.stream.timeout(
          const Duration(seconds: 45),
        )) {
          sink.add(chunk);
          received += chunk.length;
          if (expectedTotal > 0) {
            onProgress(
              (received / expectedTotal).clamp(0.0, 1.0).toDouble(),
            );
          }
        }
        await sink.flush();
        await sink.close();
        sink = null;

        final finalSize = await file.length();
        if (info.apkSize > 0 && finalSize != info.apkSize) {
          throw Exception(
            'Niepełny plik APK: $finalSize z ${info.apkSize} bajtów.',
          );
        }
        if (finalSize <= 0) {
          throw ApiException('Pobrany plik aktualizacji jest pusty.');
        }

        onProgress(1.0);
        downloaded = true;
        break;
      } on ApiException {
        rethrow;
      } catch (error) {
        lastError = error;
        if (attempt < maxAttempts) {
          await Future<void>.delayed(Duration(seconds: attempt * 2));
        }
      } finally {
        if (sink != null) {
          try {
            await sink.close();
          } catch (_) {}
        }
        client?.close();
      }
    }

    if (!downloaded) {
      throw ApiException(
        'Połączenie zostało przerwane podczas pobierania aktualizacji. '
        'WMM próbował 4 razy i zachował pobraną część pliku do wznowienia. '
        'Sprawdź internet i wybierz „Spróbuj ponownie”.'
        '${lastError == null ? '' : ''}',
      );
    }

    if (!await file.exists() || await file.length() == 0) {
      throw ApiException('Pobrany plik aktualizacji jest pusty.');
    }

    final result = await _channel.invokeMethod<dynamic>(
      'installApk',
      <String, dynamic>{'path': file.path},
    );
    if (result is Map) {
      final map = Map<String, dynamic>.from(result);
      if (map['ok'] == false && map['permission_required'] != true) {
        throw ApiException(
          (map['error'] ?? 'Nie udało się uruchomić instalatora Androida.')
              .toString(),
        );
      }
    }
  }'''

    source = source[:start] + replacement + source[end:]

    # Błąd transferu nie może zasłaniać przycisku ponownej próby.
    source = source.replace(
        "          else if (error.isNotEmpty)\n",
        "          else if (error.isNotEmpty && info == null)\n",
        1,
    )

    retry_anchor = """            const SizedBox(height: 12),\n            if (downloading) ...[\n"""
    retry_ui = """            const SizedBox(height: 12),\n            if (error.isNotEmpty) ...[\n              RoundedCard(\n                child: Text(\n                  error,\n                  style: const TextStyle(color: kRed),\n                ),\n              ),\n              const SizedBox(height: 12),\n            ],\n            if (downloading) ...[\n"""
    if retry_anchor not in source:
        raise RuntimeError("Nie znaleziono miejsca UI dla błędu pobierania")
    source = source.replace(retry_anchor, retry_ui, 1)

    install_catch = """    } catch (e) {\n      if (mounted) setState(() => error = e.toString());\n    } finally {\n      if (mounted) setState(() => downloading = false);\n    }\n"""
    install_catch_new = """    } catch (e) {\n      if (mounted) {\n        setState(() {\n          error = e.toString();\n          message = '';\n        });\n      }\n    } finally {\n      if (mounted) setState(() => downloading = false);\n    }\n"""
    if install_catch not in source:
        raise RuntimeError("Nie znaleziono obsługi błędu instalacji")
    source = source.replace(install_catch, install_catch_new, 1)

    # Wersja raportowana w UI/updaterze ma odpowiadać buildowi.
    source = re.sub(
        r"const String kWmmCurrentVersion = '[^']+';",
        f"const String kWmmCurrentVersion = '{APP_VERSION}';",
        source,
        count=1,
    )
    source = re.sub(
        r"subtitle: 'WMM \d+\.\d+\.\d+ BETA',",
        f"subtitle: 'WMM {APP_VERSION} BETA',",
        source,
        count=1,
    )

    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
