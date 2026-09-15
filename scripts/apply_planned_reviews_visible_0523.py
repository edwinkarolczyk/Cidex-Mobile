from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.23"


def replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    fields_old = """class _WmmMachineQuickActionsState extends State<WmmMachineQuickActions> {
  Timer? _ticker;
  bool actionBusy = false;
"""
    fields_new = """class _WmmMachineQuickActionsState extends State<WmmMachineQuickActions> {
  Timer? _ticker;
  bool actionBusy = false;
  List<Map<String, dynamic>> _serverPlannedReviews = <Map<String, dynamic>>[];
  bool _plannedLoading = true;
  String _plannedError = '';
"""
    source = replace_required(source, fields_old, fields_new, "stan listy przeglądów")

    state_start = source.find("class _WmmMachineQuickActionsState")
    init_start = source.find("  @override\n  void initState() {", state_start)
    if init_start < 0:
        raise RuntimeError("Nie znaleziono initState szybkich działań Maszyny")
    super_marker = "    super.initState();\n"
    super_pos = source.find(super_marker, init_start)
    if super_pos < 0:
        raise RuntimeError("Nie znaleziono super.initState")
    insert_pos = super_pos + len(super_marker)
    source = source[:insert_pos] + (
        "    WidgetsBinding.instance.addPostFrameCallback((_) {\n"
        "      if (mounted) _loadPlannedReviews();\n"
        "    });\n"
    ) + source[insert_pos:]

    method_marker = "  DateTime? get _repairStartedAt {\n"
    methods = r'''
  List<Map<String, dynamic>> get _visiblePlannedReviews {
    if (_serverPlannedReviews.isNotEmpty) return _serverPlannedReviews;
    return _plannedReviews;
  }

  Future<void> _loadPlannedReviews() async {
    if (!mounted) return;
    setState(() {
      _plannedLoading = true;
      _plannedError = '';
    });
    try {
      final rows = await widget.api.cycleMachineReviews(widget.machineId);
      if (!mounted) return;
      rows.sort((a, b) =>
          (a['planned_date'] ?? a['date'] ?? '').toString().compareTo(
              (b['planned_date'] ?? b['date'] ?? '').toString()));
      setState(() {
        _serverPlannedReviews = rows;
        _plannedLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _serverPlannedReviews = <Map<String, dynamic>>[];
        _plannedLoading = false;
        _plannedError = e.toString();
      });
    }
  }

  @override
  void didUpdateWidget(covariant WmmMachineQuickActions oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.machineId != widget.machineId) {
      _loadPlannedReviews();
    }
  }

'''
    source = replace_required(source, method_marker, methods + method_marker, "ładowanie przeglądów z WM")

    source = replace_required(
        source,
        "    final planned = _plannedReviews;\n",
        "    final planned = _visiblePlannedReviews;\n",
        "widoczna lista przeglądów",
    )

    review_list_marker = "          if (planned.isNotEmpty) ...[\n"
    review_status = """          if (_plannedLoading) ...[
            const SizedBox(height: 12),
            const LinearProgressIndicator(color: kOrange),
            const SizedBox(height: 5),
            const Text('Pobieranie przeglądów zaplanowanych z WM…', style: TextStyle(color: kMuted, fontSize: 12)),
          ],
          if (!_plannedLoading && _plannedError.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Nie udało się pobrać przeglądów z WM: $_plannedError', style: const TextStyle(color: kRed, fontSize: 12)),
            const SizedBox(height: 6),
            OutlinedButton.icon(
              onPressed: actionBusy ? null : _loadPlannedReviews,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('ODŚWIEŻ PRZEGLĄDY'),
            ),
          ],
          if (!_plannedLoading && _plannedError.isEmpty && planned.isEmpty) ...[
            const SizedBox(height: 12),
            const Text('Brak aktywnych przeglądów zaplanowanych w WM.', style: TextStyle(color: kMuted, fontSize: 12)),
          ],
          if (planned.isNotEmpty) ...[
"""
    source = replace_required(source, review_list_marker, review_status, "status listy przeglądów")

    row_old = """              final type = (row['type'] ?? 'Przegląd').toString();
              final date = (row['planned_date'] ?? '').toString();
"""
    row_new = """              final type = (row['type'] ?? 'Przegląd').toString();
              final date = (row['planned_date'] ?? row['date'] ?? '').toString();
              final sourceLabel = (row['source_label'] ??
                      ((row['source'] ?? '').toString().toLowerCase() == 'cycle'
                          ? 'Cykliczny'
                          : 'Ręczny / zaplanowany w WM'))
                  .toString();
"""
    source = replace_required(source, row_old, row_new, "źródło przeglądu na karcie")
    source = replace_required(
        source,
        "Expanded(child: Text('$date • $type', style: const TextStyle(fontSize: 13))),",
        "Expanded(child: Text('$date • $type • $sourceLabel', style: const TextStyle(fontSize: 13))),",
        "opis przeglądu na karcie",
    )

    start_success_old = """      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Rozpoczęto istniejący zaplanowany przegląd w WM.')),
"""
    start_success_new = """      widget.onChanged(updated);
      await _loadPlannedReviews();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Rozpoczęto istniejący zaplanowany przegląd w WM.')),
"""
    source = replace_required(source, start_success_old, start_success_new, "odświeżenie po rozpoczęciu przeglądu")

    complete_success_old = """      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Zaplanowany przegląd zapisano jako wykonany w WM.')),
"""
    complete_success_new = """      widget.onChanged(updated);
      await _loadPlannedReviews();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Zaplanowany przegląd zapisano jako wykonany w WM.')),
"""
    source = replace_required(source, complete_success_old, complete_success_new, "odświeżenie po wykonaniu przeglądu")

    source = re.sub(
        r"const String kWmmCurrentVersion = '[^']+';",
        f"const String kWmmCurrentVersion = '{APP_VERSION}';",
        source,
        count=1,
    )
    source = re.sub(
        r"Warsztat Menager Mobile \d+\.\d+\.\d+(?: BETA)?",
        f"Warsztat Menager Mobile {APP_VERSION}",
        source,
    )
    source = re.sub(
        r"WMM \d+\.\d+\.\d+(?: BETA)?",
        f"WMM {APP_VERSION}",
        source,
    )
    source = source.replace(" BETA", "")
    path.write_text(source, encoding="utf-8")

    manifest = Path("android/app/src/main/AndroidManifest.xml")
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        text = re.sub(
            r'android:label="WMM(?: \d+\.\d+\.\d+)?(?: BETA)?"',
            f'android:label="WMM {APP_VERSION}"',
            text,
            count=1,
        )
        manifest.write_text(text, encoding="utf-8")

    test = Path("test/widget_test.dart")
    if test.is_file():
        text = test.read_text(encoding="utf-8")
        text = re.sub(
            r"expect\(kWmmCurrentVersion, '\d+\.\d+\.\d+'\);",
            f"expect(kWmmCurrentVersion, '{APP_VERSION}');",
            text,
        )
        text = text.replace("WMM 0.5.22", f"WMM {APP_VERSION}")
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
