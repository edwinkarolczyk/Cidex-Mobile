from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.13"

HELPERS = r'''
Map<String, String>? wmmParseObjectQr(String raw) {
  final value = raw.trim();
  if (value.isEmpty) return null;

  final orderMatch = RegExp(
    r'^(?:WM|WMM|CIDEX):PLANISTA:(?:ORDER|ZLECENIE):(.+)$',
    caseSensitive: false,
  ).firstMatch(value);
  if (orderMatch != null) {
    final id = (orderMatch.group(1) ?? '').trim();
    if (id.isEmpty) return null;
    return <String, String>{'entity': 'order', 'id': id};
  }

  final match = RegExp(
    r'^(?:CIDEX|WMM):(MACHINE|MASZYNA|TOOL|NARZEDZIE|NARZĘDZIE):(.+)$',
    caseSensitive: false,
  ).firstMatch(value);
  if (match == null) return null;

  final kind = (match.group(1) ?? '').toLowerCase();
  final id = (match.group(2) ?? '').trim();
  if (id.isEmpty) return null;
  final entity = kind == 'machine' || kind == 'maszyna' ? 'machine' : 'tool';
  return <String, String>{'entity': entity, 'id': id};
}

String wmmQrEntity(Map<String, dynamic> item) =>
    (item['entity'] ?? '').toString().trim().toLowerCase();

String wmmQrObjectId(Map<String, dynamic> item) {
  for (final key in const ['id', 'nr_ewid', 'numer', 'nr']) {
    final value = (item[key] ?? '').toString().trim();
    if (value.isNotEmpty) return value;
  }
  return '';
}
'''

OLD_RESOLVE = r'''  Future<void> resolve(String code) async {
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
'''

NEW_RESOLVE = r'''  Future<void> resolve(String code) async {
    if (resolving || code.trim().isEmpty) return;
    setState(() {
      resolving = true;
      error = '';
    });
    try {
      final raw = code.trim();
      final hinted = wmmParseObjectQr(raw);
      String entity;
      String id;

      if (hinted != null) {
        entity = hinted['entity'] ?? '';
        id = hinted['id'] ?? '';
      } else {
        final item = await widget.api.resolveQr(raw);
        if (!mounted) return;
        entity = wmmQrEntity(item);
        id = wmmQrObjectId(item);
      }

      if (id.isEmpty) {
        throw ApiException('QR nie zawiera poprawnego ID obiektu.');
      }
      if (entity != 'machine' && entity != 'tool' && entity != 'order') {
        throw ApiException('Nie rozpoznano typu obiektu z kodu QR.');
      }

      await controller.stop();
      if (!mounted) return;
      if (entity == 'machine') {
        await Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => MachineScreen(api: widget.api, machineId: id),
          ),
        );
      } else if (entity == 'tool') {
        await Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => ToolScreen(api: widget.api, toolId: id),
          ),
        );
      } else {
        await Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => PlanistaOrderScreen(
              api: widget.api,
              initial: <String, dynamic>{'id': id},
            ),
          ),
        );
      }
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
'''


def replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    scanner_anchor = "class QrScannerScreen extends StatefulWidget {\n"
    if "Map<String, String>? wmmParseObjectQr" not in source:
        source = replace_required(
            source,
            scanner_anchor,
            HELPERS.strip() + "\n\n" + scanner_anchor,
            "funkcje rozpoznawania QR",
        )

    source = replace_required(source, OLD_RESOLVE, NEW_RESOLVE, "obsługa QR maszyny/narzędzia/zlecenia")
    source = source.replace(
        "final manual = TextEditingController(text: 'CIDEX:MACHINE:42');",
        "final manual = TextEditingController();",
        1,
    )
    source = source.replace("subtitle: 'Otwórz maszynę po ID',", "subtitle: 'Maszyna lub narzędzie',", 1)
    source = source.replace("appBar: AppBar(title: const Text('Skanuj QR maszyny')),", "appBar: AppBar(title: const Text('Skanuj QR')),", 1)
    source = source.replace(
        "'Skieruj aparat na kod QR naklejony na maszynie.',",
        "'Skieruj aparat na QR maszyny, narzędzia albo zlecenia Planisty. WMM rozpozna typ automatycznie.',",
        1,
    )
    source = source.replace(
        "label: const Text('OTWÓRZ MASZYNĘ', style: TextStyle(fontWeight: FontWeight.w900)),",
        "label: const Text('OTWÓRZ OBIEKT', style: TextStyle(fontWeight: FontWeight.w900)),",
        1,
    )

    source = re.sub(
        r"const String kWmmCurrentVersion = '[^']+';",
        f"const String kWmmCurrentVersion = '{APP_VERSION}';",
        source,
        count=1,
    )
    source = re.sub(
        r"Warsztat Menager Mobile \d+\.\d+\.\d+ BETA",
        f"Warsztat Menager Mobile {APP_VERSION} BETA",
        source,
    )

    path.write_text(source, encoding="utf-8")

    manifest = Path("android/app/src/main/AndroidManifest.xml")
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        text = re.sub(
            r'android:label="WMM(?: \d+\.\d+\.\d+)? BETA"',
            f'android:label="WMM {APP_VERSION} BETA"',
            text,
            count=1,
        )
        manifest.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
