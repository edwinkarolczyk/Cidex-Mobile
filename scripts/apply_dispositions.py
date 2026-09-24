from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.15"

OLD_HOME_TILE = r'''                  ActionTile(
                    color: kOrange,
                    icon: Icons.assignment_turned_in_rounded,
                    title: 'Dyspozycje',
                    subtitle: 'Bieżące zadania z WM',
                    onTap: () => open(
                      WmmSimpleListScreen(
                        title: 'Dyspozycje',
                        icon: Icons.assignment_turned_in_rounded,
                        loader: api.dispositions,
                        primaryKeys: const ['obiekt', 'nazwa', 'id'],
                        secondaryKeys: const ['dyspozycja', 'status', 'termin'],
                      ),
                    ),
                  ),
'''

NEW_HOME_TILE = r'''                  ActionTile(
                    color: kOrange,
                    icon: Icons.assignment_turned_in_rounded,
                    title: 'Dyspozycje',
                    subtitle: 'Zadania, status i priorytet',
                    onTap: () => open(DispositionsScreen(api: api)),
                  ),
'''

DISPOSITION_UI = r'''
String wmmDispositionStatusLabel(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'nowa':
      return 'Nowa';
    case 'w_toku':
      return 'W toku';
    case 'wstrzymana':
      return 'Wstrzymana';
    case 'zamknieta':
      return 'Zakończona';
    default:
      final raw = (value ?? '').toString().trim();
      return raw.isEmpty ? '—' : raw;
  }
}

Color wmmDispositionStatusColor(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'nowa':
      return kBlue;
    case 'w_toku':
      return kOrange;
    case 'wstrzymana':
      return const Color(0xFFD39A22);
    case 'zamknieta':
      return kGreen;
    default:
      return kMuted;
  }
}

String wmmDispositionPriorityLabel(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'niski':
      return 'Niski';
    case 'normalny':
      return 'Normalny';
    case 'wysoki':
      return 'Wysoki';
    case 'krytyczny':
      return 'Krytyczny';
    default:
      final raw = (value ?? '').toString().trim();
      return raw.isEmpty ? 'Normalny' : raw;
  }
}

Color wmmDispositionPriorityColor(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'niski':
      return kGreen;
    case 'wysoki':
      return kOrange;
    case 'krytyczny':
      return kRed;
    default:
      return kBlue;
  }
}

String wmmDispositionTypeLabel(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'maszyna':
      return 'Maszyna';
    case 'narzedzie':
      return 'Narzędzie';
    case 'magazyn':
      return 'Magazyn';
    case 'zlecenie_wykonania':
    case 'zamowienie':
      return 'Zlecenie wykonania';
    default:
      final raw = (value ?? '').toString().trim();
      return raw.isEmpty ? 'Inne' : raw;
  }
}

List<String> wmmDispositionAllowedTargets(String status) {
  switch (status.trim().toLowerCase()) {
    case 'nowa':
      return const ['w_toku'];
    case 'w_toku':
      return const ['wstrzymana', 'zamknieta'];
    case 'wstrzymana':
      return const ['w_toku', 'zamknieta'];
    default:
      return const [];
  }
}

String wmmDispositionAssignment(Map<String, dynamic> item) {
  final everyone = item['dla_wszystkich'] == true ||
      (item['dla_wszystkich'] ?? '').toString().trim().toLowerCase() == 'true';
  if (everyone) return 'Wszyscy';
  final assigned = (item['przypisane_do'] ?? '').toString().trim();
  return assigned.isEmpty ? 'Nieprzypisana' : assigned;
}

int _wmmDispositionStatusRank(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'nowa':
      return 0;
    case 'w_toku':
      return 1;
    case 'wstrzymana':
      return 2;
    case 'zamknieta':
      return 4;
    default:
      return 3;
  }
}

int _wmmDispositionPriorityRank(dynamic value) {
  switch ((value ?? '').toString().trim().toLowerCase()) {
    case 'krytyczny':
      return 0;
    case 'wysoki':
      return 1;
    case 'normalny':
      return 2;
    case 'niski':
      return 3;
    default:
      return 4;
  }
}

class WmmHelpIcon extends StatelessWidget {
  const WmmHelpIcon({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: text,
      visualDensity: VisualDensity.compact,
      constraints: const BoxConstraints(minWidth: 34, minHeight: 34),
      onPressed: () => showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Pomoc'),
          content: Text(text),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('OK'),
            ),
          ],
        ),
      ),
      icon: Container(
        width: 22,
        height: 22,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: kOrange.withValues(alpha: 0.14),
          shape: BoxShape.circle,
          border: Border.all(color: kOrange.withValues(alpha: 0.75)),
        ),
        child: const Text(
          '!',
          style: TextStyle(color: kOrange, fontWeight: FontWeight.w900),
        ),
      ),
    );
  }
}

class WmmDispositionBadge extends StatelessWidget {
  const WmmDispositionBadge({
    super.key,
    required this.label,
    required this.color,
    this.icon,
  });

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.55)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 15, color: color),
            const SizedBox(width: 5),
          ],
          Text(
            label,
            style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class WmmDispositionInfoRow extends StatelessWidget {
  const WmmDispositionInfoRow({
    super.key,
    required this.label,
    required this.value,
    this.help,
  });

  final String label;
  final String value;
  final String? help;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: kMuted, fontSize: 12, fontWeight: FontWeight.w700)),
                const SizedBox(height: 3),
                Text(value.isEmpty ? '—' : value, style: const TextStyle(fontWeight: FontWeight.w800, height: 1.3)),
              ],
            ),
          ),
          if (help != null) WmmHelpIcon(text: help!),
        ],
      ),
    );
  }
}


const String wmmDispositionFilterKey = 'wmm_dispositions_status_filter_v1';

const Map<String, String> wmmDispositionFilters = {
  'all': 'Wszystkie',
  'active': 'Aktywne',
  'nowa': 'Nowe',
  'w_toku': 'W toku',
  'wstrzymana': 'Wstrzymane',
  'zamknieta': 'Zakończone',
};

String wmmDispositionFilterValue(String? value) =>
    wmmDispositionFilters.containsKey(value) ? value! : 'all';

bool wmmDispositionMatchesFilter(Map<String, dynamic> item, String filter) {
  final status = (item['status'] ?? '').toString().trim().toLowerCase();
  switch (wmmDispositionFilterValue(filter)) {
    case 'all':
      return true;
    case 'active':
      return status != 'zamknieta';
    default:
      return status == filter;
  }
}

List<Map<String, dynamic>> wmmVisibleDispositions(
  List<Map<String, dynamic>> items,
  String query,
  String filter,
) {
  final q = query.trim().toLowerCase();
  final rows = items.where((item) {
    if (!wmmDispositionMatchesFilter(item, filter)) return false;
    if (q.isEmpty) return true;
    return [
      'id', 'tytul', 'opis', 'typ_dyspozycji', 'status',
      'priorytet', 'termin', 'przypisane_do', 'wykonuje', 'obiekt_id',
    ].map((key) => (item[key] ?? '').toString().toLowerCase())
        .any((value) => value.contains(q));
  }).map(Map<String, dynamic>.from).toList();

  rows.sort((a, b) {
    final status = _wmmDispositionStatusRank(a['status'])
        .compareTo(_wmmDispositionStatusRank(b['status']));
    if (status != 0) return status;
    final priority = _wmmDispositionPriorityRank(a['priorytet'])
        .compareTo(_wmmDispositionPriorityRank(b['priorytet']));
    if (priority != 0) return priority;
    final at = (a['termin'] ?? '').toString().trim();
    final bt = (b['termin'] ?? '').toString().trim();
    if (at.isEmpty && bt.isNotEmpty) return 1;
    if (at.isNotEmpty && bt.isEmpty) return -1;
    final due = at.compareTo(bt);
    if (due != 0) return due;
    return (a['tytul'] ?? '').toString().toLowerCase()
        .compareTo((b['tytul'] ?? '').toString().toLowerCase());
  });
  return rows;
}

class DispositionsScreen extends StatefulWidget {
  const DispositionsScreen({super.key, required this.api});

  final WmApi api;

  @override
  State<DispositionsScreen> createState() => _DispositionsScreenState();
}

class _DispositionsScreenState extends State<DispositionsScreen> {
  final search = TextEditingController();
  List<Map<String, dynamic>> items = [];
  bool busy = true;
  String error = '';
  String statusFilter = 'all';
  bool filterChangedByUser = false;

  @override
  void initState() {
    super.initState();
    search.addListener(_onSearchChanged);
    _restoreStatusFilter();
    load();
  }

  void _onSearchChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _restoreStatusFilter() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!mounted || filterChangedByUser) return;
      setState(() => statusFilter =
          wmmDispositionFilterValue(prefs.getString(wmmDispositionFilterKey)));
    } catch (_) {
      // Keep the default filter if local preference storage is unavailable.
    }
  }

  Future<void> _setStatusFilter(String value) async {
    filterChangedByUser = true;
    final next = wmmDispositionFilterValue(value);
    setState(() => statusFilter = next);
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(wmmDispositionFilterKey, next);
    } catch (_) {
      // Filtering works for the current session even when persistence fails.
    }
  }

  @override
  void dispose() {
    search.removeListener(_onSearchChanged);
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
      final rows = await widget.api.dispositions();
      if (!mounted) return;
      setState(() => items = rows);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  List<Map<String, dynamic>> get visible =>
      wmmVisibleDispositions(items, search.text, statusFilter);

  @override
  Widget build(BuildContext context) {
    final rows = visible;
    final active = items.where((item) => (item['status'] ?? '').toString().trim().toLowerCase() != 'zamknieta').length;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dyspozycje'),
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
                    hintText: 'Szukaj dyspozycji, obiektu, osoby...',
                    prefixIcon: Icon(Icons.search_rounded),
                  ),
                ),
                const SizedBox(height: 8),
                InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Filtr statusu',
                    prefixIcon: Icon(Icons.filter_list_rounded),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: statusFilter,
                      isExpanded: true,
                      dropdownColor: kPanel,
                      items: wmmDispositionFilters.entries.map((entry) =>
                        DropdownMenuItem<String>(
                          value: entry.key,
                          child: Text(entry.value),
                        ),
                      ).toList(),
                      onChanged: (value) {
                        if (value != null) _setStatusFilter(value);
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Aktywne: $active • Wszystkie: ${items.length}',
                    style: const TextStyle(color: kMuted, fontWeight: FontWeight.w700),
                  ),
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
                        ? const Center(child: Text('Brak dyspozycji.', style: TextStyle(color: kMuted)))
                        : RefreshIndicator(
                            onRefresh: load,
                            color: kOrange,
                            child: ListView.separated(
                              padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
                              itemCount: rows.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 10),
                              itemBuilder: (context, index) {
                                final item = rows[index];
                                final id = (item['id'] ?? '').toString().trim();
                                final title = (item['tytul'] ?? '').toString().trim();
                                final status = (item['status'] ?? '').toString().trim();
                                final priority = (item['priorytet'] ?? '').toString().trim();
                                final type = wmmDispositionTypeLabel(item['typ_dyspozycji']);
                                final objectId = (item['obiekt_id'] ?? '').toString().trim();
                                final due = (item['termin'] ?? '').toString().trim();
                                final assignment = wmmDispositionAssignment(item);
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
                                                builder: (_) => DispositionScreen(api: widget.api, initial: item),
                                              ),
                                            );
                                            await load();
                                          },
                                    child: Padding(
                                      padding: const EdgeInsets.all(15),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Expanded(
                                                child: Text(
                                                  title.isEmpty ? id : title,
                                                  style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 17),
                                                ),
                                              ),
                                              const SizedBox(width: 8),
                                              const Icon(Icons.chevron_right_rounded, color: kMuted),
                                            ],
                                          ),
                                          const SizedBox(height: 9),
                                          Wrap(
                                            spacing: 7,
                                            runSpacing: 7,
                                            children: [
                                              WmmDispositionBadge(
                                                label: wmmDispositionStatusLabel(status),
                                                color: wmmDispositionStatusColor(status),
                                              ),
                                              WmmDispositionBadge(
                                                label: wmmDispositionPriorityLabel(priority),
                                                color: wmmDispositionPriorityColor(priority),
                                                icon: Icons.flag_rounded,
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 10),
                                          Text(
                                            objectId.isEmpty ? type : '$type • $objectId',
                                            style: const TextStyle(color: Color(0xFFD3D7DC), fontWeight: FontWeight.w800),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            'Przypisane: $assignment${due.isEmpty ? '' : ' • Termin: $due'}',
                                            style: const TextStyle(color: kMuted, height: 1.35),
                                          ),
                                          if (id.isNotEmpty) ...[
                                            const SizedBox(height: 4),
                                            Text(id, style: const TextStyle(color: Color(0xFF727A84), fontSize: 11)),
                                          ],
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

class DispositionScreen extends StatefulWidget {
  const DispositionScreen({
    super.key,
    required this.api,
    required this.initial,
  });

  final WmApi api;
  final Map<String, dynamic> initial;

  @override
  State<DispositionScreen> createState() => _DispositionScreenState();
}

class _DispositionScreenState extends State<DispositionScreen> {
  late Map<String, dynamic> item;
  bool actionBusy = false;
  String error = '';

  String get id => (item['id'] ?? '').toString().trim();

  @override
  void initState() {
    super.initState();
    item = Map<String, dynamic>.from(widget.initial);
  }

  Future<void> refresh() async {
    try {
      final rows = await widget.api.dispositions();
      final currentId = id;
      final found = rows.where((row) => (row['id'] ?? '').toString().trim() == currentId).toList();
      if (!mounted) return;
      if (found.isEmpty) {
        setState(() => error = 'Dyspozycja nie istnieje już w WM.');
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

  Future<bool> _confirmFinish() async {
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Zakończyć dyspozycję?'),
        content: const Text('Po zakończeniu dyspozycja będzie zamknięta w Warsztat Menager i nie będzie można wznowić jej z telefonu.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Anuluj')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: kRed),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('ZAKOŃCZ'),
          ),
        ],
      ),
    );
    return result == true;
  }

  Future<void> changeStatus(String target) async {
    if (actionBusy || id.isEmpty) return;
    if (target == 'zamknieta' && !await _confirmFinish()) return;
    setState(() {
      actionBusy = true;
      error = '';
    });
    try {
      final updated = await widget.api.setDispositionStatus(id, target);
      if (!mounted) return;
      setState(() => item = Map<String, dynamic>.from(updated));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Status: ${wmmDispositionStatusLabel(target)}. Zapisano w WM.'),
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

  Widget _actionButton({
    required String label,
    required IconData icon,
    required Color color,
    required VoidCallback? onPressed,
  }) {
    return SizedBox(
      height: 56,
      child: FilledButton.icon(
        style: FilledButton.styleFrom(backgroundColor: color),
        onPressed: onPressed,
        icon: Icon(icon),
        label: Text(label, style: const TextStyle(fontWeight: FontWeight.w900)),
      ),
    );
  }

  List<Widget> _actions(String status) {
    switch (status) {
      case 'nowa':
        return [
          _actionButton(
            label: 'ROZPOCZNIJ',
            icon: Icons.play_arrow_rounded,
            color: kOrange,
            onPressed: actionBusy ? null : () => changeStatus('w_toku'),
          ),
        ];
      case 'w_toku':
        return [
          _actionButton(
            label: 'WSTRZYMAJ',
            icon: Icons.pause_rounded,
            color: const Color(0xFFD39A22),
            onPressed: actionBusy ? null : () => changeStatus('wstrzymana'),
          ),
          const SizedBox(height: 10),
          _actionButton(
            label: 'ZAKOŃCZ',
            icon: Icons.task_alt_rounded,
            color: kRed,
            onPressed: actionBusy ? null : () => changeStatus('zamknieta'),
          ),
        ];
      case 'wstrzymana':
        return [
          _actionButton(
            label: 'W TOKU — WZNÓW',
            icon: Icons.play_arrow_rounded,
            color: kOrange,
            onPressed: actionBusy ? null : () => changeStatus('w_toku'),
          ),
          const SizedBox(height: 10),
          _actionButton(
            label: 'ZAKOŃCZ',
            icon: Icons.task_alt_rounded,
            color: kRed,
            onPressed: actionBusy ? null : () => changeStatus('zamknieta'),
          ),
        ];
      default:
        return const [
          Row(
            children: [
              Icon(Icons.verified_rounded, color: kGreen),
              SizedBox(width: 8),
              Expanded(
                child: Text('Dyspozycja zakończona.', style: TextStyle(color: kGreen, fontWeight: FontWeight.w900)),
              ),
            ],
          ),
        ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = (item['tytul'] ?? '').toString().trim();
    final description = (item['opis'] ?? '').toString().trim();
    final status = (item['status'] ?? '').toString().trim().toLowerCase();
    final priority = (item['priorytet'] ?? '').toString().trim();
    final due = (item['termin'] ?? '').toString().trim();
    final type = wmmDispositionTypeLabel(item['typ_dyspozycji']);
    final objectId = (item['obiekt_id'] ?? '').toString().trim();
    final source = (item['modul_zrodlowy'] ?? '').toString().trim();
    final author = (item['autor'] ?? '').toString().trim();
    final created = (item['utworzono'] ?? '').toString().trim();
    final executor = (item['wykonuje'] ?? '').toString().trim();
    final started = (item['rozpoczal_at'] ?? '').toString().trim();
    final closedBy = (item['zamkniete_przez'] ?? '').toString().trim();
    final closedAt = (item['zamknieto_at'] ?? item['wykonano'] ?? '').toString().trim();
    final notes = (item['uwagi'] ?? '').toString().trim();

    return Scaffold(
      appBar: AppBar(
        title: Text(id.isEmpty ? 'Dyspozycja' : id),
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
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 26),
              children: [
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title.isEmpty ? 'Dyspozycja' : title,
                        style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900, height: 1.2),
                      ),
                      if (id.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(id, style: const TextStyle(color: kMuted, fontSize: 12)),
                      ],
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          WmmDispositionBadge(
                            label: wmmDispositionStatusLabel(status),
                            color: wmmDispositionStatusColor(status),
                            icon: Icons.sync_alt_rounded,
                          ),
                          WmmDispositionBadge(
                            label: wmmDispositionPriorityLabel(priority),
                            color: wmmDispositionPriorityColor(priority),
                            icon: Icons.flag_rounded,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      WmmDispositionInfoRow(
                        label: 'Status',
                        value: wmmDispositionStatusLabel(status),
                        help: 'Status określa etap wykonania dyspozycji. Każda zmiana jest zapisywana bezpośrednio w Warsztat Menager.',
                      ),
                      WmmDispositionInfoRow(
                        label: 'Priorytet',
                        value: wmmDispositionPriorityLabel(priority),
                        help: 'Priorytet wskazuje pilność zadania ustawioną w WM. Krytyczne i wysokie dyspozycje są pokazywane wyżej na liście.',
                      ),
                      WmmDispositionInfoRow(
                        label: 'Przypisanie',
                        value: wmmDispositionAssignment(item),
                        help: 'To osoba lub grupa, do której przypisano dyspozycję w WM. Rozpoczęcie zadania zapisuje także faktycznego wykonawcę.',
                      ),
                      WmmDispositionInfoRow(
                        label: 'Termin',
                        value: due.isEmpty ? 'Brak terminu' : due,
                        help: 'Termin pochodzi z dyspozycji w Warsztat Menager. WMM go tutaj tylko wyświetla i nie zmienia.',
                      ),
                      WmmDispositionInfoRow(
                        label: 'Obiekt',
                        value: objectId.isEmpty ? type : '$type • $objectId',
                      ),
                      if (source.isNotEmpty) WmmDispositionInfoRow(label: 'Moduł źródłowy', value: source),
                      if (author.isNotEmpty || created.isNotEmpty)
                        WmmDispositionInfoRow(
                          label: 'Utworzona',
                          value: [author, created].where((value) => value.isNotEmpty).join(' • '),
                        ),
                      if (executor.isNotEmpty || started.isNotEmpty)
                        WmmDispositionInfoRow(
                          label: 'Wykonuje',
                          value: [executor, started].where((value) => value.isNotEmpty).join(' • '),
                        ),
                      if (closedBy.isNotEmpty || closedAt.isNotEmpty)
                        WmmDispositionInfoRow(
                          label: 'Zamknięta',
                          value: [closedBy, closedAt].where((value) => value.isNotEmpty).join(' • '),
                        ),
                    ],
                  ),
                ),
                if (description.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  RoundedCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Opis', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                        const SizedBox(height: 8),
                        Text(description, style: const TextStyle(color: Color(0xFFD3D7DC), height: 1.45)),
                      ],
                    ),
                  ),
                ],
                if (notes.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  RoundedCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Uwagi', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                        const SizedBox(height: 8),
                        Text(notes, style: const TextStyle(color: Color(0xFFD3D7DC), height: 1.45)),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Row(
                        children: [
                          Expanded(child: Text('Działania', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17))),
                          WmmHelpIcon(
                            text: 'Rozpocznij ustawia dyspozycję jako W toku. Zakończ zamyka ją w WM i zapisuje użytkownika oraz czas wykonania.',
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ..._actions(status),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                WmmDispositionHistory(item: item),
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

class WmmDispositionHistory extends StatelessWidget {
  const WmmDispositionHistory({super.key, required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final rawMeta = item['meta'];
    final meta = rawMeta is Map ? Map<String, dynamic>.from(rawMeta) : <String, dynamic>{};
    final raw = meta['historia_statusow'];
    final rows = (raw is List ? raw : const [])
        .whereType<Map>()
        .map(Map<String, dynamic>.from)
        .toList()
        .reversed
        .toList();

    return RoundedCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(top: 4),
        leading: const Icon(Icons.history_rounded, color: kOrange),
        title: const Text('Historia statusów', style: TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text('${rows.length} zmian', style: const TextStyle(color: kMuted)),
        children: rows.isEmpty
            ? const [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: Text('Brak zmian statusu.', style: TextStyle(color: kMuted)),
                  ),
                ),
              ]
            : rows.map((row) {
                final from = wmmDispositionStatusLabel(row['z']);
                final to = wmmDispositionStatusLabel(row['na']);
                final who = (row['kto'] ?? '').toString().trim();
                final when = (row['kiedy'] ?? '').toString().trim();
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(top: 5),
                        child: Icon(Icons.circle, size: 8, color: kOrange),
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('$from → $to', style: const TextStyle(fontWeight: FontWeight.w900)),
                            Text(
                              [who, when].where((value) => value.isNotEmpty).join(' • '),
                              style: const TextStyle(color: kMuted, fontSize: 12),
                            ),
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

    source = replace_required(source, OLD_HOME_TILE, NEW_HOME_TILE, "kafelek Dyspozycje")
    if "class DispositionsScreen extends StatefulWidget" not in source:
        source = source.rstrip() + "\n\n" + DISPOSITION_UI.strip() + "\n"

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
