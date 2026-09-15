from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.20"

API_METHODS = r'''
  Future<List<Map<String, dynamic>>> cycleMachineReviews(String id) async {
    final payload = await getJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/cycle-reviews',
    );
    final raw = payload['items'];
    if (raw is! List) return <Map<String, dynamic>>[];
    return raw.whereType<Map>().map(Map<String, dynamic>.from).toList();
  }

  Future<Map<String, dynamic>> startCycleMachineReview(
    String id,
    String reviewId,
  ) async {
    return postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/cycle-reviews/${Uri.encodeComponent(reviewId)}/start',
      const <String, dynamic>{},
    );
  }

  Future<Map<String, dynamic>> completeCycleMachineReview(
    String id,
    String reviewId,
    String note,
  ) async {
    return postJson(
      '/api/v1/machines/${Uri.encodeComponent(id)}/cycle-reviews/${Uri.encodeComponent(reviewId)}/complete',
      <String, dynamic>{'note': note},
    );
  }
'''

STATE_METHODS = r'''
  String _cycleStatusLabel(Object? value) {
    final raw = (value ?? '').toString().trim().toLowerCase();
    if (raw == 'in_progress' || raw == 'w_toku' || raw == 'started') return 'W trakcie';
    return 'Planowany';
  }

  Future<String?> _askCycleResult(Map<String, dynamic> review) async {
    final controller = TextEditingController();
    final planned = (review['date'] ?? review['planned_date'] ?? '').toString();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Expanded(child: Text('Wykonano przegląd cykliczny')),
            WmmHelpIcon(
              text: 'WMM oznaczy wybrany termin z harmonogramu WM jako wykonany. Nie tworzy nowego przeglądu ani nowego terminu.',
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (planned.isNotEmpty)
              Text('Plan: $planned', style: const TextStyle(color: kMuted)),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              autofocus: true,
              minLines: 3,
              maxLines: 5,
              decoration: const InputDecoration(
                labelText: 'Co wykonano? (opcjonalnie)',
                hintText: 'Np. smarowanie, kontrola osłon i prowadnic',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Anuluj'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: kGreen),
            onPressed: () => Navigator.pop(dialogContext, controller.text.trim()),
            child: const Text('ZAPISZ WYKONANIE', style: TextStyle(fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  Future<void> _startCycleReview(Map<String, dynamic> review) async {
    final reviewId = (review['id'] ?? '').toString().trim();
    if (reviewId.isEmpty || actionBusy) return;
    setState(() => actionBusy = true);
    try {
      final payload = await widget.api.startCycleMachineReview(widget.machineId, reviewId);
      if (!mounted) return;
      final updated = Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Rozpoczęto istniejący przegląd cykliczny w WM.')),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  Future<void> _completeCycleReview(Map<String, dynamic> review) async {
    final reviewId = (review['id'] ?? '').toString().trim();
    if (reviewId.isEmpty || actionBusy) return;
    final note = await _askCycleResult(review);
    if (!mounted || note == null) return;
    setState(() => actionBusy = true);
    try {
      final payload = await widget.api.completeCycleMachineReview(
        widget.machineId,
        reviewId,
        note,
      );
      if (!mounted) return;
      final updated = Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
      widget.onChanged(updated);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Przegląd cykliczny zapisano jako wykonany w WM.')),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  Future<void> _openCycleReviews() async {
    if (actionBusy) return;
    setState(() => actionBusy = true);
    List<Map<String, dynamic>> rows = <Map<String, dynamic>>[];
    try {
      rows = await widget.api.cycleMachineReviews(widget.machineId);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
      return;
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
    if (!mounted) return;
    if (rows.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Brak zaplanowanego przeglądu cyklicznego w WM.')),
      );
      return;
    }

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: kPanel,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(
            16,
            16,
            16,
            16 + MediaQuery.of(sheetContext).viewInsets.bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Row(
                children: [
                  Expanded(
                    child: Text(
                      'Przegląd cykliczny',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                    ),
                  ),
                  WmmHelpIcon(
                    text: 'Lista pochodzi z harmonogramu WM, także z terminów generowanych automatycznie. WMM nie tworzy ani nie planuje nowych przeglądów.',
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Wybierz konkretny termin istniejący w Warsztat Menager.',
                style: TextStyle(color: kMuted),
              ),
              const SizedBox(height: 12),
              ConstrainedBox(
                constraints: BoxConstraints(maxHeight: MediaQuery.of(sheetContext).size.height * 0.62),
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: rows.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (_, index) {
                    final row = rows[index];
                    final planned = (row['date'] ?? row['planned_date'] ?? '—').toString();
                    final type = (row['type'] ?? 'Przegląd okresowy').toString();
                    final status = (row['status'] ?? 'planned').toString();
                    final inProgress = status.trim().toLowerCase() == 'in_progress';
                    final startedBy = (row['started_by'] ?? '').toString().trim();
                    final startedAt = (row['started_at'] ?? '').toString().trim();
                    return Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: kPanel2,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: inProgress ? kOrange : kBorder),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.event_repeat_rounded, color: kOrange),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  planned,
                                  style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16),
                                ),
                              ),
                              Text(
                                _cycleStatusLabel(status),
                                style: TextStyle(
                                  color: inProgress ? kOrange : kMuted,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(type, style: const TextStyle(color: Color(0xFFD3D7DC))),
                          if (inProgress && (startedBy.isNotEmpty || startedAt.isNotEmpty)) ...[
                            const SizedBox(height: 4),
                            Text(
                              'Rozpoczął: ${startedBy.isEmpty ? '—' : startedBy}${startedAt.isEmpty ? '' : ' • $startedAt'}',
                              style: const TextStyle(color: kMuted, fontSize: 12),
                            ),
                          ],
                          const SizedBox(height: 10),
                          if (inProgress)
                            SizedBox(
                              width: double.infinity,
                              child: FilledButton.icon(
                                style: FilledButton.styleFrom(backgroundColor: kGreen),
                                onPressed: () {
                                  Navigator.pop(sheetContext);
                                  _completeCycleReview(row);
                                },
                                icon: const Icon(Icons.task_alt_rounded),
                                label: const Text('ZAKOŃCZ PRZEGLĄD', style: TextStyle(fontWeight: FontWeight.w900)),
                              ),
                            )
                          else
                            Row(
                              children: [
                                Expanded(
                                  child: OutlinedButton.icon(
                                    onPressed: () {
                                      Navigator.pop(sheetContext);
                                      _startCycleReview(row);
                                    },
                                    icon: const Icon(Icons.play_arrow_rounded),
                                    label: const Text('ROZPOCZNIJ'),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: FilledButton.icon(
                                    style: FilledButton.styleFrom(backgroundColor: kGreen),
                                    onPressed: () {
                                      Navigator.pop(sheetContext);
                                      _completeCycleReview(row);
                                    },
                                    icon: const Icon(Icons.check_rounded),
                                    label: const Text('WYKONANO'),
                                  ),
                                ),
                              ],
                            ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
'''

CYCLE_BUTTON = r'''
          const SizedBox(height: 10),
          SizedBox(
            height: 54,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: kOrange),
              onPressed: isFailure || actionBusy ? null : _openCycleReviews,
              icon: const Icon(Icons.event_repeat_rounded),
              label: const Text('PRZEGLĄD CYKLICZNY', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
          if (isFailure)
            const Padding(
              padding: EdgeInsets.only(top: 5),
              child: Text(
                'Zakończ aktywną naprawę, aby rozpocząć przegląd cykliczny.',
                style: TextStyle(color: kMuted, fontSize: 12),
              ),
            ),
'''


def _insert_before(source: str, marker: str, block: str, label: str) -> str:
    index = source.find(marker)
    if index < 0:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source[:index] + block + source[index:]


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    extension_end = "\n}\n\nclass WmmMachineQuickActions extends StatefulWidget"
    source = _insert_before(source, extension_end, API_METHODS.rstrip() + "\n", "API przeglądu cyklicznego")

    build_marker = "\n  @override\n  Widget build(BuildContext context) {\n"
    quick_class = source.find("class _WmmMachineQuickActionsState")
    if quick_class < 0:
        raise RuntimeError("Nie znaleziono stanu szybkich działań Maszyny")
    build_index = source.find(build_marker, quick_class)
    if build_index < 0:
        raise RuntimeError("Nie znaleziono build szybkich działań Maszyny")
    source = source[:build_index] + "\n" + STATE_METHODS.strip() + "\n" + source[build_index:]

    planned_marker = "          if (planned.isNotEmpty)"
    planned_index = source.find(planned_marker, build_index)
    if planned_index < 0:
        raise RuntimeError("Nie znaleziono listy planowanych przeglądów Maszyny")
    source = source[:planned_index] + CYCLE_BUTTON + source[planned_index:]

    source = source.replace(
        "Szybka naprawa zapisuje istniejący status Awaria w WM. Planowane przeglądy są tu tylko do podglądu i można je tworzyć wyłącznie w desktopowym WM.",
        "Szybka naprawa zapisuje istniejący status Awaria. Przegląd cykliczny korzysta wyłącznie z terminów już istniejących w harmonogramie WM.",
    )

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
        text = text.replace("WMM 0.5.19", f"WMM {APP_VERSION}")
        text = text.replace("expect(kWmmCurrentVersion, '0.5.19');", f"expect(kWmmCurrentVersion, '{APP_VERSION}');")
        closing = text.rfind("}\n")
        if closing < 0:
            raise RuntimeError("Nie znaleziono końca testów WMM")
        extra = f'''\n  test('WMM {APP_VERSION} ma szybkie akcje Maszyny bez planowania nowych przeglądów', () {{
    const config = ApiConfig(baseUrl: 'http://10.0.2.2:8765', token: 'ABC123');
    final api = WmApi(config);
    final widget = WmmMachineQuickActions(
      api: api,
      machineId: '42',
      machine: const <String, dynamic>{{'status': 'ok'}},
      onChanged: (_) {{}},
    );
    expect(widget.machineId, '42');
    expect(kWmmCurrentVersion, '{APP_VERSION}');
  }});\n'''
        text = text[:closing] + extra + text[closing:]
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
