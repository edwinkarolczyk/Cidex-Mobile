from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.18"

DART = r'''
const List<String> wmmMachineReviewTypes = <String>[
  'Przegląd okresowy',
  'Serwis planowany',
  'Konserwacja',
  'Kalibracja',
  'Czyszczenie',
  'Inne',
];

String wmmMachineStatusCode(Object? value) {
  final raw = (value ?? '').toString().trim().toLowerCase();
  if (raw == 'warn' || raw == 'warm' || raw == 'warning' || raw == 'awaria') return 'warn';
  if (raw == 'alert' || raw.contains('serwis') || raw.contains('przegl')) return 'alert';
  return 'ok';
}

extension WmmMachineQuickApi on WmApi {
  Future<Map<String, dynamic>> startQuickRepair(String id, String note) async {
    final payload = await postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/quick-repair/start',
      {'note': note},
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<Map<String, dynamic>> finishQuickRepair(String id, String note) async {
    return postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/quick-repair/finish',
      {'note': note},
    );
  }

  Future<Map<String, dynamic>> addPlannedMachineReview(
    String id, {
    required String type,
    required String plannedDate,
    String description = '',
  }) async {
    return postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/reviews',
      {
        'type': type,
        'planned_date': plannedDate,
        'description': description,
      },
    );
  }
}

class WmmMachineQuickActions extends StatefulWidget {
  const WmmMachineQuickActions({
    super.key,
    required this.api,
    required this.machineId,
    required this.machine,
    required this.onChanged,
  });

  final WmApi api;
  final String machineId;
  final Map<String, dynamic> machine;
  final ValueChanged<Map<String, dynamic>> onChanged;

  @override
  State<WmmMachineQuickActions> createState() => _WmmMachineQuickActionsState();
}

class _WmmMachineQuickActionsState extends State<WmmMachineQuickActions> {
  Timer? _ticker;
  bool actionBusy = false;

  @override
  void initState() {
    super.initState();
    _ticker = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted && wmmMachineStatusCode(widget.machine['status']) == 'warn') {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  List<Map<String, dynamic>> get _plannedReviews {
    final raw = widget.machine['reviews'];
    if (raw is! List) return const [];
    final rows = raw
        .whereType<Map>()
        .map(Map<String, dynamic>.from)
        .where((row) => (row['status'] ?? '').toString().trim().toLowerCase() == 'planned')
        .toList();
    rows.sort((a, b) =>
        (a['planned_date'] ?? '').toString().compareTo((b['planned_date'] ?? '').toString()));
    return rows;
  }

  DateTime? get _repairStartedAt {
    final current = widget.machine['status_current'];
    if (current is! Map) return null;
    return DateTime.tryParse((current['started_at'] ?? '').toString())?.toLocal();
  }

  String _elapsedLabel() {
    final started = _repairStartedAt;
    if (started == null) return '';
    final duration = DateTime.now().difference(started);
    if (duration.isNegative) return '';
    final totalMinutes = duration.inMinutes;
    final days = totalMinutes ~/ 1440;
    final hours = (totalMinutes % 1440) ~/ 60;
    final minutes = totalMinutes % 60;
    if (days > 0) return '${days}d ${hours}h ${minutes}m';
    if (hours > 0) return '${hours}h ${minutes}m';
    return '${minutes} min';
  }

  String _dateText(DateTime value) =>
      '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';

  Future<String?> _askStartNote() async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Expanded(child: Text('Szybka naprawa')),
            WmmHelpIcon(
              text: 'Rozpoczęcie ustawia istniejący w WM status Awaria. WM od tej chwili mierzy czas trwania statusu tak samo jak przy zmianie wykonanej na komputerze.',
            ),
          ],
        ),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'Co naprawiamy? (opcjonalnie)',
            hintText: 'Np. uszkodzony czujnik krańcowy',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Anuluj')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: kRed),
            onPressed: () => Navigator.pop(dialogContext, controller.text.trim()),
            child: const Text('ROZPOCZNIJ', style: TextStyle(fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  Future<String?> _askFinishNote() async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Expanded(child: Text('Zakończ naprawę')),
            WmmHelpIcon(
              text: 'Zakończenie przywraca istniejący status Sprawna. WM zamknie okres Awarii i zapisze jego czas w historii statusów maszyny.',
            ),
          ],
        ),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'Co zostało naprawione?',
            hintText: 'Np. wymieniono czujnik i sprawdzono działanie',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Anuluj')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: kGreen),
            onPressed: () {
              final text = controller.text.trim();
              if (text.isEmpty) {
                ScaffoldMessenger.of(dialogContext).showSnackBar(
                  const SnackBar(content: Text('Wpisz krótko, co zostało naprawione.')),
                );
                return;
              }
              Navigator.pop(dialogContext, text);
            },
            child: const Text('ZAKOŃCZ', style: TextStyle(fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  Future<void> _startRepair() async {
    final note = await _askStartNote();
    if (!mounted || note == null) return;
    setState(() => actionBusy = true);
    try {
      final updated = await widget.api.startQuickRepair(widget.machineId, note);
      if (!mounted) return;
      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Rozpoczęto naprawę. Status Awaria zapisano w WM.')),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  Future<void> _finishRepair() async {
    final note = await _askFinishNote();
    if (!mounted || note == null) return;
    setState(() => actionBusy = true);
    try {
      final payload = await widget.api.finishQuickRepair(widget.machineId, note);
      if (!mounted) return;
      final updated = Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
      final duration = (payload['duration_minutes'] as num?)?.toInt() ?? 0;
      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Naprawa zakończona w WM${duration > 0 ? ' • czas: $duration min' : ''}.'),
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  Future<void> _addPlannedReview() async {
    String selectedType = wmmMachineReviewTypes.first;
    DateTime selectedDate = DateTime.now();
    final description = TextEditingController();

    final values = await showDialog<Map<String, String>>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Expanded(child: Text('Dodaj przegląd planowany')),
              WmmHelpIcon(
                text: 'Lista typów jest dokładnie taka sama jak w Warsztat Menager. WMM zapisuje zwykły ręczny przegląd planowany i nie tworzy nowego rodzaju serwisu.',
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                DropdownButtonFormField<String>(
                  initialValue: selectedType,
                  decoration: const InputDecoration(labelText: 'Typ przeglądu'),
                  items: wmmMachineReviewTypes
                      .map((value) => DropdownMenuItem<String>(value: value, child: Text(value)))
                      .toList(),
                  onChanged: (value) {
                    if (value != null) selectedType = value;
                  },
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.calendar_month_rounded),
                        label: Text('Data: ${_dateText(selectedDate)}'),
                        onPressed: () async {
                          final picked = await showDatePicker(
                            context: dialogContext,
                            initialDate: selectedDate,
                            firstDate: DateTime(2020, 1, 1),
                            lastDate: DateTime(DateTime.now().year + 10, 12, 31),
                          );
                          if (picked != null) {
                            setDialogState(() => selectedDate = picked);
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 6),
                    const WmmHelpIcon(
                      text: 'To pole zapisuje istniejące planned_date przeglądu w WM. Termin będzie widoczny w tej samej liście przeglądów co wpisy dodane na komputerze.',
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: description,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Zakres / opis (opcjonalnie)',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Anuluj')),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: kOrange),
              onPressed: () => Navigator.pop(dialogContext, <String, String>{
                'type': selectedType,
                'date': _dateText(selectedDate),
                'description': description.text.trim(),
              }),
              child: const Text('DODAJ', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ],
        ),
      ),
    );
    description.dispose();
    if (!mounted || values == null) return;

    setState(() => actionBusy = true);
    try {
      final payload = await widget.api.addPlannedMachineReview(
        widget.machineId,
        type: values['type'] ?? wmmMachineReviewTypes.first,
        plannedDate: values['date'] ?? '',
        description: values['description'] ?? '',
      );
      if (!mounted) return;
      final updated = Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Przegląd planowany zapisano w WM.')),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isFailure = wmmMachineStatusCode(widget.machine['status']) == 'warn';
    final planned = _plannedReviews;
    final elapsed = _elapsedLabel();
    final current = widget.machine['status_current'];
    final currentNote = current is Map ? (current['note'] ?? '').toString().trim() : '';

    return RoundedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Row(
            children: [
              Expanded(
                child: Text('Szybkie działania WM', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),
              ),
              WmmHelpIcon(
                text: 'Te przyciski korzystają wyłącznie z funkcji, które już istnieją w module Maszyny WM. Wpisy z telefonu są oznaczone [WMM] w istniejących uwagach lub opisach.',
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (isFailure) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: kRed.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: kRed.withValues(alpha: 0.35)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AKTYWNA AWARIA / NAPRAWA', style: TextStyle(color: kRed, fontWeight: FontWeight.w900)),
                  if (elapsed.isNotEmpty) Text('Czas: $elapsed', style: const TextStyle(fontWeight: FontWeight.w800)),
                  if (currentNote.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(currentNote, style: const TextStyle(color: Color(0xFFD3D7DC))),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              height: 54,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(backgroundColor: kGreen),
                onPressed: actionBusy ? null : _finishRepair,
                icon: const Icon(Icons.task_alt_rounded),
                label: const Text('ZAKOŃCZ NAPRAWĘ', style: TextStyle(fontWeight: FontWeight.w900)),
              ),
            ),
          ] else ...[
            SizedBox(
              height: 54,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(backgroundColor: kRed),
                onPressed: actionBusy ? null : _startRepair,
                icon: const Icon(Icons.build_circle_rounded),
                label: const Text('SZYBKA NAPRAWA', style: TextStyle(fontWeight: FontWeight.w900)),
              ),
            ),
          ],
          const SizedBox(height: 10),
          SizedBox(
            height: 54,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: kOrange),
              onPressed: actionBusy ? null : _addPlannedReview,
              icon: const Icon(Icons.event_available_rounded),
              label: const Text('DODAJ PRZEGLĄD PLANOWANY', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
          if (planned.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text('Najbliższe planowane', style: TextStyle(color: kMuted, fontWeight: FontWeight.w800)),
            const SizedBox(height: 5),
            ...planned.take(4).map((row) {
              final type = (row['type'] ?? 'Przegląd').toString();
              final date = (row['planned_date'] ?? '').toString();
              return Padding(
                padding: const EdgeInsets.only(top: 5),
                child: Row(
                  children: [
                    const Icon(Icons.circle, size: 7, color: kOrange),
                    const SizedBox(width: 8),
                    Expanded(child: Text('$date • $type', style: const TextStyle(fontSize: 13))),
                  ],
                ),
              );
            }),
          ],
          if (actionBusy) ...[
            const SizedBox(height: 12),
            const LinearProgressIndicator(color: kOrange),
          ],
        ],
      ),
    );
  }
}
'''


def _insert_in_machine_scope(source: str) -> str:
    scope = "class _MachineScreenState extends State<MachineScreen> {"
    start = source.find(scope)
    if start < 0:
        raise RuntimeError("Nie znaleziono karty Maszyny")
    tail = source[start:]
    marker = """                const SizedBox(height: 14),
                GridView.count(
"""
    if marker not in tail:
        raise RuntimeError("Nie znaleziono miejsca szybkich działań Maszyny")
    replacement = """                const SizedBox(height: 14),
                WmmMachineQuickActions(
                  api: widget.api,
                  machineId: widget.machineId,
                  machine: machine,
                  onChanged: (updated) {
                    if (!mounted) return;
                    setState(() => machine = Map<String, dynamic>.from(updated));
                  },
                ),
                const SizedBox(height: 14),
                GridView.count(
"""
    tail = tail.replace(marker, replacement, 1)
    return source[:start] + tail


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    if "class WmmMachineQuickActions extends StatefulWidget" not in source:
        source = source.rstrip() + "\n\n" + DART.strip() + "\n"
    source = _insert_in_machine_scope(source)

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
        text = text.replace("WMM 0.5.17", "WMM 0.5.18")
        text = text.replace("expect(kWmmCurrentVersion, '0.5.17');", "expect(kWmmCurrentVersion, '0.5.18');")
        closing = text.rfind("}\n")
        if closing < 0:
            raise RuntimeError("Nie znaleziono końca testów WMM")
        extra = r'''
  test('WMM 0.5.18 używa wyłącznie typów przeglądów istniejących w WM', () {
    expect(wmmMachineReviewTypes, const [
      'Przegląd okresowy',
      'Serwis planowany',
      'Konserwacja',
      'Kalibracja',
      'Czyszczenie',
      'Inne',
    ]);
    expect(wmmMachineStatusCode('Awaria'), 'warn');
    expect(wmmMachineStatusCode('warn'), 'warn');
    expect(wmmMachineStatusCode('Sprawna'), 'ok');
  });
'''
        text = text[:closing] + extra + text[closing:]
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
