from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.16"

OLD_HOME_TILE = r'''                  ActionTile(
                    color: kOrange,
                    icon: Icons.inventory_2_rounded,
                    title: 'Magazyn',
                    subtitle: 'Podgląd stanów',
                    onTap: () => open(
                      WmmSimpleListScreen(
                        title: 'Magazyn',
                        icon: Icons.inventory_2_rounded,
                        loader: api.warehouse,
                        primaryKeys: const ['nazwa', 'name', 'id', 'kod'],
                        secondaryKeys: const ['ilosc', 'stan', 'lokalizacja'],
                      ),
                    ),
                  ),
'''

NEW_HOME_TILE = r'''                  ActionTile(
                    color: kOrange,
                    icon: Icons.inventory_2_rounded,
                    title: 'Magazyn',
                    subtitle: 'Stany i przyjęcia materiału',
                    onTap: () => open(WarehouseScreen(api: api)),
                  ),
'''

WAREHOUSE_API_OLD = r'''  Future<List<Map<String, dynamic>>> warehouse() async {
    final payload = await getJson('/api/v1/warehouse');
    return _items(payload);
  }
}
'''

WAREHOUSE_API_NEW = r'''  Future<List<Map<String, dynamic>>> warehouse() async {
    final payload = await getJson('/api/v1/warehouse');
    return _items(payload);
  }

  Future<Map<String, dynamic>> receiveWarehouse(
    String id,
    num qty, {
    String document = '',
    String supplier = '',
    String note = '',
  }) async {
    final payload = await postJson(
      '/api/v1/warehouse/${Uri.encodeComponent(id)}/receive',
      {
        'qty': qty,
        'document': document,
        'supplier': supplier,
        'note': note,
      },
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }
}
'''

WAREHOUSE_UI = r'''
String wmmWarehouseItemId(Map<String, dynamic> item) =>
    (item['id'] ?? item['kod'] ?? item['symbol'] ?? '').toString().trim();

String wmmWarehouseName(Map<String, dynamic> item) =>
    (item['nazwa'] ?? item['name'] ?? wmmWarehouseItemId(item)).toString().trim();

String wmmWarehouseUnit(Map<String, dynamic> item) =>
    (item['jednostka'] ?? item['unit'] ?? '').toString().trim();

String wmmWarehouseLocation(Map<String, dynamic> item) =>
    (item['lokalizacja'] ?? item['miejsce'] ?? '').toString().trim();

double wmmWarehouseStock(Map<String, dynamic> item) {
  final value = item['stan'] ?? item['ilosc'] ?? 0;
  if (value is num) return value.toDouble();
  return double.tryParse(value.toString().replaceAll(',', '.')) ?? 0;
}

List<Map<String, dynamic>> wmmWarehouseReceipts(Map<String, dynamic> item) {
  final raw = item['receipts'];
  if (raw is! List) return const [];
  return raw.whereType<Map>().map(Map<String, dynamic>.from).toList();
}

String wmmWarehouseNumber(num value) {
  final number = value.toDouble();
  if (number == number.roundToDouble()) return number.toInt().toString();
  return number.toStringAsFixed(3).replaceFirst(RegExp(r'0+$'), '').replaceFirst(RegExp(r'\.$'), '');
}

class WarehouseScreen extends StatefulWidget {
  const WarehouseScreen({super.key, required this.api});

  final WmApi api;

  @override
  State<WarehouseScreen> createState() => _WarehouseScreenState();
}

class _WarehouseScreenState extends State<WarehouseScreen> {
  final search = TextEditingController();
  List<Map<String, dynamic>> items = [];
  bool busy = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    search.addListener(_onSearch);
    load();
  }

  void _onSearch() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    search.removeListener(_onSearch);
    search.dispose();
    super.dispose();
  }

  Future<void> load() async {
    if (mounted) {
      setState(() {
        busy = true;
        error = '';
      });
    }
    try {
      final rows = await widget.api.warehouse();
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
    final rows = items.where((item) {
      if (q.isEmpty) return true;
      return [
        'id',
        'kod',
        'symbol',
        'nazwa',
        'name',
        'rodzaj',
        'typ',
        'rozmiar',
        'lokalizacja',
        'miejsce',
        'jednostka',
      ].map((key) => (item[key] ?? '').toString().toLowerCase()).any((value) => value.contains(q));
    }).map(Map<String, dynamic>.from).toList();
    rows.sort((a, b) => wmmWarehouseName(a).toLowerCase().compareTo(wmmWarehouseName(b).toLowerCase()));
    return rows;
  }

  @override
  Widget build(BuildContext context) {
    final rows = visible;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Magazyn'),
        actions: [
          IconButton(onPressed: busy ? null : load, tooltip: 'Odśwież', icon: const Icon(Icons.refresh_rounded)),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 4),
            child: Column(
              children: [
                TextField(
                  controller: search,
                  decoration: const InputDecoration(
                    hintText: 'Szukaj kodu, nazwy, rozmiaru, lokalizacji...',
                    prefixIcon: Icon(Icons.search_rounded),
                  ),
                ),
                const SizedBox(height: 8),
                const Row(
                  children: [
                    Icon(Icons.lock_outline_rounded, color: kGreen, size: 18),
                    SizedBox(width: 7),
                    Expanded(
                      child: Text(
                        'Kartoteka surowca jest tylko do odczytu. WMM może wyłącznie przyjąć dostawę do istniejącej pozycji.',
                        style: TextStyle(color: kMuted, fontSize: 12, height: 1.3),
                      ),
                    ),
                    WmmHelpIcon(
                      text: 'Z telefonu nie zmienisz nazwy, kodu, wymiaru ani jednostki surowca. Nowe surowce i edycję kartoteki wykonuje się tylko w desktopowym Warsztat Menager.',
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: busy
                ? const Center(child: CircularProgressIndicator(color: kOrange))
                : error.isNotEmpty
                    ? ErrorState(message: error, onRetry: load)
                    : rows.isEmpty
                        ? const Center(child: Text('Brak pozycji magazynowych.', style: TextStyle(color: kMuted)))
                        : RefreshIndicator(
                            onRefresh: load,
                            color: kOrange,
                            child: ListView.separated(
                              padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
                              itemCount: rows.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 10),
                              itemBuilder: (context, index) {
                                final item = rows[index];
                                final id = wmmWarehouseItemId(item);
                                final name = wmmWarehouseName(item);
                                final unit = wmmWarehouseUnit(item);
                                final stock = wmmWarehouseStock(item);
                                final location = wmmWarehouseLocation(item);
                                final size = (item['rozmiar'] ?? '').toString().trim();
                                return Material(
                                  color: kPanel,
                                  borderRadius: BorderRadius.circular(20),
                                  child: InkWell(
                                    borderRadius: BorderRadius.circular(20),
                                    onTap: id.isEmpty
                                        ? null
                                        : () async {
                                            await Navigator.of(context).push(
                                              MaterialPageRoute(
                                                builder: (_) => WarehouseItemScreen(api: widget.api, initial: item),
                                              ),
                                            );
                                            await load();
                                          },
                                    child: Padding(
                                      padding: const EdgeInsets.all(15),
                                      child: Row(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Container(
                                            width: 46,
                                            height: 46,
                                            decoration: BoxDecoration(
                                              color: kOrange.withValues(alpha: 0.12),
                                              borderRadius: BorderRadius.circular(14),
                                            ),
                                            child: const Icon(Icons.inventory_2_rounded, color: kOrange),
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Text(name.isEmpty ? id : name, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                                                const SizedBox(height: 3),
                                                Text(
                                                  [id, size].where((value) => value.isNotEmpty).join(' • '),
                                                  style: const TextStyle(color: kMuted, fontSize: 12),
                                                ),
                                                const SizedBox(height: 8),
                                                Text(
                                                  'Stan: ${wmmWarehouseNumber(stock)}${unit.isEmpty ? '' : ' $unit'}',
                                                  style: const TextStyle(color: kGreen, fontWeight: FontWeight.w900, fontSize: 15),
                                                ),
                                                if (location.isNotEmpty) ...[
                                                  const SizedBox(height: 3),
                                                  Text('Lokalizacja: $location', style: const TextStyle(color: Color(0xFFD3D7DC))),
                                                ],
                                              ],
                                            ),
                                          ),
                                          const Icon(Icons.chevron_right_rounded, color: kMuted),
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

class WarehouseItemScreen extends StatefulWidget {
  const WarehouseItemScreen({super.key, required this.api, required this.initial});

  final WmApi api;
  final Map<String, dynamic> initial;

  @override
  State<WarehouseItemScreen> createState() => _WarehouseItemScreenState();
}

class _WarehouseItemScreenState extends State<WarehouseItemScreen> {
  late Map<String, dynamic> item;
  bool actionBusy = false;
  String error = '';

  String get id => wmmWarehouseItemId(item);

  @override
  void initState() {
    super.initState();
    item = Map<String, dynamic>.from(widget.initial);
  }

  Future<void> refresh() async {
    try {
      final rows = await widget.api.warehouse();
      final currentId = id.toLowerCase();
      final found = rows.where((row) => wmmWarehouseItemId(row).toLowerCase() == currentId).toList();
      if (!mounted) return;
      if (found.isEmpty) {
        setState(() => error = 'Pozycja nie istnieje już w Magazynie WM.');
        return;
      }
      setState(() {
        item = Map<String, dynamic>.from(found.first);
        error = '';
      });
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    }
  }

  Future<Map<String, String>?> _askReceipt() async {
    final qty = TextEditingController();
    final document = TextEditingController();
    final supplier = TextEditingController();
    final note = TextEditingController();
    final unit = wmmWarehouseUnit(item);
    final result = await showDialog<Map<String, String>>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Expanded(child: Text('Przyjmij materiał')),
            WmmHelpIcon(
              text: 'Przyjęcie zwiększa wyłącznie stan istniejącego surowca. Kod, nazwa, rozmiar i jednostka pozostają bez zmian.',
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
              const SizedBox(height: 10),
              TextField(
                controller: document,
                decoration: const InputDecoration(
                  labelText: 'Dokument / nr dostawy (opcjonalnie)',
                  prefixIcon: Icon(Icons.description_outlined),
                ),
              ),
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
                controller: note,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Uwaga (opcjonalnie)',
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
    document.dispose();
    supplier.dispose();
    note.dispose();
    return result;
  }

  Future<void> receive() async {
    if (actionBusy || id.isEmpty) return;
    final values = await _askReceipt();
    if (values == null) return;
    final qty = double.tryParse((values['qty'] ?? '').replaceAll(',', '.'));
    if (qty == null || qty <= 0) return;
    final unit = wmmWarehouseUnit(item);
    final before = wmmWarehouseStock(item);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Potwierdź przyjęcie'),
        content: Text(
          'Dodać +${wmmWarehouseNumber(qty)}${unit.isEmpty ? '' : ' $unit'} do ${wmmWarehouseName(item)}?\n\nStan: ${wmmWarehouseNumber(before)} → ${wmmWarehouseNumber(before + qty)}${unit.isEmpty ? '' : ' $unit'}',
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
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Przyjęto +${wmmWarehouseNumber(qty)}${unit.isEmpty ? '' : ' $unit'}. Nowy stan: ${wmmWarehouseNumber(wmmWarehouseStock(item))}${unit.isEmpty ? '' : ' $unit'}.',
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

  Widget _info(String label, String value, {String? help}) {
    return WmmDispositionInfoRow(label: label, value: value.isEmpty ? '—' : value, help: help);
  }

  @override
  Widget build(BuildContext context) {
    final name = wmmWarehouseName(item);
    final unit = wmmWarehouseUnit(item);
    final stock = wmmWarehouseStock(item);
    final location = wmmWarehouseLocation(item);
    final kind = (item['rodzaj'] ?? item['typ'] ?? '').toString().trim();
    final size = (item['rozmiar'] ?? '').toString().trim();
    final length = (item['dlugosc'] ?? item['długość'] ?? '').toString().trim();
    final section = (item['sekcja'] ?? '').toString().trim();
    final receipts = wmmWarehouseReceipts(item);

    return Scaffold(
      appBar: AppBar(
        title: Text(id.isEmpty ? 'Pozycja Magazynu' : id),
        actions: [
          IconButton(onPressed: actionBusy ? null : refresh, tooltip: 'Odśwież', icon: const Icon(Icons.refresh_rounded)),
        ],
      ),
      body: Stack(
        children: [
          RefreshIndicator(
            onRefresh: refresh,
            color: kOrange,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 28),
              children: [
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.inventory_2_rounded, color: kOrange, size: 36),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(name.isEmpty ? id : name, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 21)),
                                const SizedBox(height: 3),
                                Text(id, style: const TextStyle(color: kMuted)),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        '${wmmWarehouseNumber(stock)}${unit.isEmpty ? '' : ' $unit'}',
                        style: const TextStyle(color: kGreen, fontWeight: FontWeight.w900, fontSize: 30),
                      ),
                      const Text('Aktualny stan', style: TextStyle(color: kMuted, fontWeight: FontWeight.w700)),
                      if (location.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            const Icon(Icons.place_outlined, color: kMuted, size: 18),
                            const SizedBox(width: 6),
                            Expanded(child: Text(location, style: const TextStyle(fontWeight: FontWeight.w800))),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Row(
                        children: [
                          Expanded(child: Text('Kartoteka surowca — tylko odczyt', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16))),
                          WmmHelpIcon(
                            text: 'Te dane pochodzą z Warsztat Menager i nie są edytowalne w telefonie. Dzięki temu przyjęcie dostawy nie zmieni przypadkiem kartoteki surowca.',
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      _info('Kod / ID', id),
                      _info('Nazwa', name),
                      if (kind.isNotEmpty) _info('Rodzaj', kind),
                      if (size.isNotEmpty) _info('Rozmiar', size),
                      if (length.isNotEmpty) _info('Długość', length),
                      _info(
                        'Jednostka',
                        unit.isEmpty ? 'Brak w kartotece' : unit,
                        help: 'Jednostka jest pobierana z WM i pozostaje niezmienna podczas przyjęcia. Wpisujesz wyłącznie ilość w tej jednostce.',
                      ),
                      if (section.isNotEmpty) _info('Sekcja', section),
                      _info('Lokalizacja', location.isEmpty ? 'Brak lokalizacji' : location),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 60,
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(backgroundColor: kGreen),
                    onPressed: actionBusy ? null : receive,
                    icon: const Icon(Icons.add_box_rounded, size: 26),
                    label: const Text('PRZYJMIJ MATERIAŁ', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                  ),
                ),
                const SizedBox(height: 8),
                const Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Przyjęcie tylko zwiększa stan istniejącej pozycji.',
                        style: TextStyle(color: kMuted, fontSize: 12),
                      ),
                    ),
                    WmmHelpIcon(
                      text: 'Każde przyjęcie zapisuje ilość, użytkownika i czas w historii Magazynu. W tej wersji WMM nie obsługuje wydania ani korekty stanu.',
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                WarehouseReceiptHistory(receipts: receipts, unit: unit),
                if (error.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(error, style: const TextStyle(color: kRed, fontWeight: FontWeight.w700)),
                ],
              ],
            ),
          ),
          if (actionBusy)
            Positioned.fill(
              child: IgnorePointer(
                child: Container(
                  color: Colors.black.withValues(alpha: 0.18),
                  alignment: Alignment.center,
                  child: const CircularProgressIndicator(color: kOrange),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class WarehouseReceiptHistory extends StatelessWidget {
  const WarehouseReceiptHistory({super.key, required this.receipts, required this.unit});

  final List<Map<String, dynamic>> receipts;
  final String unit;

  @override
  Widget build(BuildContext context) {
    return RoundedCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(top: 4),
        leading: const Icon(Icons.history_rounded, color: kOrange),
        title: const Text('Historia przyjęć', style: TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text('${receipts.length} wpisów', style: const TextStyle(color: kMuted)),
        children: receipts.isEmpty
            ? const [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: Text('Brak zapisanych przyjęć.', style: TextStyle(color: kMuted)),
                  ),
                ),
              ]
            : receipts.map((row) {
                final qtyRaw = row['qty'] ?? row['ilosc'] ?? 0;
                final qty = qtyRaw is num
                    ? qtyRaw.toDouble()
                    : double.tryParse(qtyRaw.toString().replaceAll(',', '.')) ?? 0;
                final when = (row['ts'] ?? row['timestamp'] ?? row['data'] ?? '').toString().trim();
                final who = (row['user'] ?? row['kto'] ?? '').toString().trim();
                final document = (row['document'] ?? row['dokument'] ?? '').toString().trim();
                final supplier = (row['supplier'] ?? row['dostawca'] ?? '').toString().trim();
                final note = (row['comment'] ?? row['uwaga'] ?? '').toString().trim();
                final rowUnit = (row['jednostka'] ?? unit).toString().trim();
                final details = [document, supplier, note].where((value) => value.isNotEmpty).join(' • ');
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(top: 4),
                        child: Icon(Icons.add_circle_rounded, color: kGreen, size: 18),
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '+${wmmWarehouseNumber(qty)}${rowUnit.isEmpty ? '' : ' $rowUnit'}',
                              style: const TextStyle(color: kGreen, fontWeight: FontWeight.w900),
                            ),
                            Text(
                              [who, when].where((value) => value.isNotEmpty).join(' • '),
                              style: const TextStyle(color: kMuted, fontSize: 12),
                            ),
                            if (details.isNotEmpty) ...[
                              const SizedBox(height: 3),
                              Text(details, style: const TextStyle(color: Color(0xFFD3D7DC), fontSize: 12)),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
      ),
    );
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

    source = replace_required(source, OLD_HOME_TILE, NEW_HOME_TILE, "kafelek Magazyn")
    source = replace_required(source, WAREHOUSE_API_OLD, WAREHOUSE_API_NEW, "API przyjęcia Magazynu")
    if "class WarehouseScreen extends StatefulWidget" not in source:
        source = source.rstrip() + "\n\n" + WAREHOUSE_UI.strip() + "\n"

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
