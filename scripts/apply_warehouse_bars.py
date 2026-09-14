from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.17"

HELPERS = r'''
bool wmmWarehouseUsesBars(Map<String, dynamic> item) =>
    wmmWarehouseUnit(item).trim().toLowerCase() == 'mm';

double? wmmWarehouseBarsTotal(String countText, String lengthText) {
  final count = double.tryParse(countText.trim().replaceAll(',', '.'));
  final length = double.tryParse(lengthText.trim().replaceAll(',', '.'));
  if (count == null || length == null || count <= 0 || length <= 0) return null;
  if ((count - count.roundToDouble()).abs() > 0.000000001) return null;
  return count.round() * length;
}
'''

ASK_RECEIPT = r'''  Future<Map<String, String>?> _askReceipt() async {
    final qty = TextEditingController();
    final barCount = TextEditingController();
    final barLength = TextEditingController();
    final document = TextEditingController();
    final supplier = TextEditingController();
    final note = TextEditingController();
    final unit = wmmWarehouseUnit(item);
    final barMode = wmmWarehouseUsesBars(item);
    final result = await showDialog<Map<String, String>>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Expanded(child: Text('Przyjmij materiał')),
            WmmHelpIcon(
              text: 'Przyjęcie zwiększa wyłącznie stan istniejącego surowca. Dla materiału liczonego w mm podaj liczbę pełnych sztang i długość jednej sztangi, tak samo jak w desktopowym WM.',
            ),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${wmmWarehouseName(item)} • $id', style: const TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              Text(
                'Aktualny stan: ${wmmWarehouseNumber(wmmWarehouseStock(item))}${unit.isEmpty ? '' : ' $unit'}',
                style: const TextStyle(color: kGreen, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 16),
              if (barMode) ...[
                TextField(
                  controller: barCount,
                  autofocus: true,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Liczba sztang',
                    prefixIcon: Icon(Icons.view_stream_outlined),
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: barLength,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Długość sztangi [mm]',
                    suffixText: 'mm',
                    prefixIcon: Icon(Icons.straighten_rounded),
                  ),
                ),
                const SizedBox(height: 7),
                const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline_rounded, size: 17, color: kMuted),
                    SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'WMM policzy: liczba sztang × długość sztangi. Wynik zostanie dodany do stanu w mm dokładnie jak w WM.',
                        style: TextStyle(color: kMuted, fontSize: 12, height: 1.3),
                      ),
                    ),
                  ],
                ),
              ] else ...[
                TextField(
                  controller: qty,
                  autofocus: true,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Ilość przyjęta',
                    suffixText: unit.isEmpty ? null : unit,
                    prefixIcon: const Icon(Icons.add_circle_outline_rounded),
                  ),
                ),
              ],
              const SizedBox(height: 10),
              TextField(
                controller: supplier,
                decoration: const InputDecoration(
                  labelText: 'Dostawca (opcjonalnie)',
                  prefixIcon: Icon(Icons.local_shipping_outlined),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: document,
                decoration: const InputDecoration(
                  labelText: 'Numer dokumentu (opcjonalnie)',
                  prefixIcon: Icon(Icons.description_outlined),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: note,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Komentarz (opcjonalnie)',
                  prefixIcon: Icon(Icons.notes_rounded),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.lock_outline_rounded, size: 17, color: kMuted),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Jednostka: ${unit.isEmpty ? 'z WM' : unit} — nie można jej tutaj zmienić.',
                      style: const TextStyle(color: kMuted, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Anuluj')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: kOrange),
            onPressed: () {
              if (barMode) {
                final total = wmmWarehouseBarsTotal(barCount.text, barLength.text);
                final count = double.tryParse(barCount.text.trim().replaceAll(',', '.'));
                final length = double.tryParse(barLength.text.trim().replaceAll(',', '.'));
                if (count == null || count <= 0 || (count - count.roundToDouble()).abs() > 0.000000001) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    const SnackBar(content: Text('Liczba sztang musi być dodatnią liczbą całkowitą.')),
                  );
                  return;
                }
                if (length == null || length <= 0 || total == null) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    const SnackBar(content: Text('Podaj długość sztangi większą od zera.')),
                  );
                  return;
                }
                Navigator.pop(dialogContext, {
                  'qty': total.toString(),
                  'bar_count': count.round().toString(),
                  'bar_length': length.toString(),
                  'document': document.text.trim(),
                  'supplier': supplier.text.trim(),
                  'note': note.text.trim(),
                });
                return;
              }

              final parsed = double.tryParse(qty.text.trim().replaceAll(',', '.'));
              if (parsed == null || parsed <= 0) {
                ScaffoldMessenger.of(dialogContext).showSnackBar(
                  const SnackBar(content: Text('Podaj ilość większą od zera.')),
                );
                return;
              }
              Navigator.pop(dialogContext, {
                'qty': qty.text.trim(),
                'document': document.text.trim(),
                'supplier': supplier.text.trim(),
                'note': note.text.trim(),
              });
            },
            child: const Text('DALEJ', style: TextStyle(fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
    qty.dispose();
    barCount.dispose();
    barLength.dispose();
    document.dispose();
    supplier.dispose();
    note.dispose();
    return result;
  }
'''

RECEIVE = r'''  Future<void> receive() async {
    if (actionBusy || id.isEmpty) return;
    final values = await _askReceipt();
    if (!mounted || values == null) return;
    final qty = double.tryParse((values['qty'] ?? '').replaceAll(',', '.'));
    if (qty == null || qty <= 0) return;
    final unit = wmmWarehouseUnit(item);
    final before = wmmWarehouseStock(item);
    final barCount = values['bar_count'] ?? '';
    final barLengthRaw = values['bar_length'] ?? '';
    final barLength = double.tryParse(barLengthRaw.replaceAll(',', '.'));
    final barSummary = barCount.isNotEmpty && barLength != null
        ? '$barCount szt. × ${wmmWarehouseNumber(barLength)} mm = ${wmmWarehouseNumber(qty)} mm\n\n'
        : '';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Potwierdź przyjęcie'),
        content: Text(
          '${barSummary}Dodać +${wmmWarehouseNumber(qty)}${unit.isEmpty ? '' : ' $unit'} do ${wmmWarehouseName(item)}?\n\nStan: ${wmmWarehouseNumber(before)} → ${wmmWarehouseNumber(before + qty)}${unit.isEmpty ? '' : ' $unit'}',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Anuluj')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: kGreen),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('PRZYJMIJ', style: TextStyle(fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() {
      actionBusy = true;
      error = '';
    });
    try {
      final updated = await widget.api.receiveWarehouse(
        id,
        qty,
        document: values['document'] ?? '',
        supplier: values['supplier'] ?? '',
        note: values['note'] ?? '',
      );
      if (!mounted) return;
      setState(() => item = Map<String, dynamic>.from(updated));
      final receiptText = barCount.isNotEmpty && barLength != null
          ? '$barCount sztang × ${wmmWarehouseNumber(barLength)} mm = +${wmmWarehouseNumber(qty)} mm.'
          : 'Przyjęto +${wmmWarehouseNumber(qty)}${unit.isEmpty ? '' : ' $unit'}.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '$receiptText Nowy stan: ${wmmWarehouseNumber(wmmWarehouseStock(item))}${unit.isEmpty ? '' : ' $unit'}.',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => error = e.toString());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), behavior: SnackBarBehavior.floating),
      );
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }
'''


def replace_function(source: str, start: str, end: str, replacement: str, label: str) -> str:
    begin = source.find(start)
    if begin < 0:
        raise RuntimeError(f"Nie znaleziono początku: {label}")
    finish = source.find(end, begin)
    if finish < 0:
        raise RuntimeError(f"Nie znaleziono końca: {label}")
    return source[:begin] + replacement + "\n" + source[finish:]


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    marker = "String wmmWarehouseNumber(num value) {"
    if "bool wmmWarehouseUsesBars(" not in source:
        index = source.find(marker)
        if index < 0:
            raise RuntimeError("Nie znaleziono helperów Magazynu")
        source = source[:index] + HELPERS.strip() + "\n\n" + source[index:]

    source = replace_function(
        source,
        "  Future<Map<String, String>?> _askReceipt() async {",
        "  Future<void> receive() async {",
        ASK_RECEIPT.rstrip(),
        "formularz przyjęcia",
    )
    source = replace_function(
        source,
        "  Future<void> receive() async {",
        "  Widget _info(",
        RECEIVE.rstrip(),
        "zapis przyjęcia",
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

    test = Path("test/widget_test.dart")
    if test.is_file():
        text = test.read_text(encoding="utf-8")
        text = text.replace("WMM 0.5.16", "WMM 0.5.17")
        text = text.replace("expect(kWmmCurrentVersion, '0.5.16');", "expect(kWmmCurrentVersion, '0.5.17');")
        text = text.replace("wmmCompareVersions('0.5.16', '0.5.15')", "wmmCompareVersions('0.5.17', '0.5.16')")
        text = text.replace("wmmCompareVersions('0.5.16', '0.5.16')", "wmmCompareVersions('0.5.17', '0.5.17')")
        text = text.replace("wmmCompareVersions('0.5.15', '0.5.16')", "wmmCompareVersions('0.5.16', '0.5.17')")
        closing = text.rfind("}\n")
        if closing < 0:
            raise RuntimeError("Nie znaleziono końca testów WMM")
        extra = r'''
  test('WMM 0.5.17 liczy dostawę sztang tak samo jak WM', () {
    expect(wmmWarehouseUsesBars({'jednostka': 'mm'}), isTrue);
    expect(wmmWarehouseUsesBars({'jednostka': 'szt'}), isFalse);
    expect(wmmWarehouseBarsTotal('10', '6000'), 60000);
    expect(wmmWarehouseBarsTotal('2', '1234.5'), 2469);
    expect(wmmWarehouseBarsTotal('2.5', '6000'), isNull);
    expect(wmmWarehouseBarsTotal('0', '6000'), isNull);
  });
'''
        text = text[:closing] + extra + text[closing:]
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
