from __future__ import annotations

from pathlib import Path


RUNTIME_HELPERS = r'''
Map<String, dynamic> _wmmCurrentUser = <String, dynamic>{};

bool get _wmmIsForeman {
  final role = (_wmmCurrentUser['role'] ?? '').toString().trim().toLowerCase();
  final rank = (_wmmCurrentUser['rank'] ?? '').toString().trim().toLowerCase();
  return role == 'brygadzista' || role.contains('brygadz') || rank.contains('brygadz');
}

class WmmObjectThumb extends StatelessWidget {
  const WmmObjectThumb({
    super.key,
    required this.api,
    required this.photos,
    required this.icon,
    required this.accent,
    this.size = 48,
  });

  final WmApi api;
  final dynamic photos;
  final IconData icon;
  final Color accent;
  final double size;

  Map<String, dynamic>? get _lastPhoto {
    final rows = (photos as List? ?? const [])
        .whereType<Map>()
        .map(Map<String, dynamic>.from)
        .toList();
    return rows.isEmpty ? null : rows.last;
  }

  @override
  Widget build(BuildContext context) {
    final photo = _lastPhoto;
    final relative = (photo?['url'] ?? '').toString().trim();
    final fallback = Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(15),
      ),
      child: Icon(icon, color: accent, size: size * 0.58),
    );
    if (relative.isEmpty) return fallback;

    final provider = ResizeImage(
      NetworkImage(api.photoUrl(relative), headers: api.headers),
      width: (size * 3).round(),
    );
    return ClipRRect(
      borderRadius: BorderRadius.circular(15),
      child: Image(
        image: provider,
        width: size,
        height: size,
        fit: BoxFit.cover,
        gaplessPlayback: true,
        errorBuilder: (_, __, ___) => fallback,
      ),
    );
  }
}

String wmmHistoryActionLabel(Map<String, dynamic> row) {
  final raw = (row['co'] ?? row['action'] ?? row['typ'] ?? '').toString().trim();
  final key = raw.toLowerCase();
  if (key.startsWith('status:')) return 'Zmiana statusu';
  const labels = <String, String>{
    'status_changed': 'Zmiana statusu',
    'task_added': 'Dodano zadanie',
    'task_done': 'Zadanie wykonane',
    'task_note': 'Notatka do zadania',
    'visit': 'Wizyta',
    'cycle_closed': 'Zakończono wizytę',
  };
  if (labels.containsKey(key)) return labels[key]!;
  if (raw.isEmpty) return 'Zmiana';
  final readable = raw.replaceAll('_', ' ');
  return '${readable[0].toUpperCase()}${readable.substring(1)}';
}

String wmmHistoryDetails(Map<String, dynamic> row) {
  final action = (row['action'] ?? row['typ'] ?? '').toString().trim().toLowerCase();
  final rawWhat = (row['co'] ?? '').toString().trim();
  final direct = (row['details'] ?? row['uwaga'] ?? row['note'] ?? '').toString().trim();
  if (direct.isNotEmpty) return direct;
  if (action == 'status_changed' || row['z'] != null || row['na'] != null) {
    final before = (row['z'] ?? row['from'] ?? '').toString().trim();
    final after = (row['na'] ?? row['to'] ?? row['status'] ?? '').toString().trim();
    if (before.isNotEmpty && after.isNotEmpty) return '$before → $after';
    return after.isNotEmpty ? after : before;
  }
  if (action == 'task_added' || action == 'task_done' || action == 'task_note') {
    return (row['title'] ?? row['task'] ?? row['task_id'] ?? '').toString().trim();
  }
  if (action == 'visit' || action == 'cycle_closed') {
    return (row['comment'] ?? row['komentarz'] ?? row['status'] ?? '').toString().trim();
  }
  if (rawWhat.toLowerCase().startsWith('status:')) {
    return rawWhat.substring(rawWhat.indexOf(':') + 1).trim();
  }
  return (row['comment'] ?? row['status'] ?? '').toString().trim();
}

String wmmHistoryWhen(Map<String, dynamic> row) =>
    (row['ts'] ?? row['kiedy'] ?? row['created_at'] ?? '').toString().trim();

String wmmHistoryWho(Map<String, dynamic> row) =>
    (row['by'] ?? row['kto'] ?? row['author'] ?? row['changed_by'] ?? '').toString().trim();

String wmmHistoryMinuteKey(Map<String, dynamic> row) {
  final value = wmmHistoryWhen(row).replaceFirst('T', ' ');
  return value.length >= 16 ? value.substring(0, 16) : value;
}

bool wmmHistoryIsMeaningful(Map<String, dynamic> row) {
  final raw = (row['co'] ?? row['action'] ?? row['typ'] ?? '').toString().trim().toLowerCase();
  if (wmmHistoryDetails(row).isNotEmpty) return true;
  return !<String>{
    '',
    'info',
    'status_changed',
    'task_added',
    'task_done',
    'task_note',
    'visit',
    'cycle_closed',
  }.contains(raw);
}

List<Map<String, dynamic>> wmmHistoryGroups(dynamic history) {
  final rows = (history as List? ?? const [])
      .whereType<Map>()
      .map(Map<String, dynamic>.from)
      .toList()
      .reversed;
  final groups = <Map<String, dynamic>>[];
  for (final row in rows) {
    if (!wmmHistoryIsMeaningful(row)) continue;
    final minute = wmmHistoryMinuteKey(row);
    final who = wmmHistoryWho(row);
    final key = '$minute|$who';
    if (groups.isEmpty || groups.last['key'] != key) {
      groups.add(<String, dynamic>{
        'key': key,
        'when': minute,
        'who': who,
        'items': <Map<String, dynamic>>[],
      });
    }
    (groups.last['items'] as List<Map<String, dynamic>>).add(row);
  }
  return groups;
}

class WmmHistorySection extends StatefulWidget {
  const WmmHistorySection({super.key, required this.history, required this.title});

  final dynamic history;
  final String title;

  @override
  State<WmmHistorySection> createState() => _WmmHistorySectionState();
}

class _WmmHistorySectionState extends State<WmmHistorySection> {
  bool showAll = false;

  @override
  Widget build(BuildContext context) {
    final groups = wmmHistoryGroups(widget.history);
    final visible = showAll ? groups : groups.take(10).toList();

    return RoundedCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(top: 6),
        leading: const Icon(Icons.history_rounded, color: kOrange),
        title: Text(widget.title, style: const TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text('${groups.length} grup historii', style: const TextStyle(color: kMuted)),
        children: groups.isEmpty
            ? const [
                Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Brak historii.', style: TextStyle(color: kMuted)),
                  ),
                ),
              ]
            : [
                ...visible.map((group) {
                final when = (group['when'] ?? '').toString();
                final who = (group['who'] ?? '').toString();
                final items = group['items'] as List<Map<String, dynamic>>;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        [when, who].where((value) => value.isNotEmpty).join(' • '),
                        style: const TextStyle(color: kMuted, fontSize: 12, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 6),
                      ...items.map((row) {
                        final title = wmmHistoryActionLabel(row);
                        final details = wmmHistoryDetails(row);
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 7),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Padding(
                                padding: EdgeInsets.only(top: 5),
                                child: Icon(Icons.circle, size: 7, color: kOrange),
                              ),
                              const SizedBox(width: 9),
                              Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
                            if (details.isNotEmpty)
                              Text(details, style: const TextStyle(color: Color(0xFFC6CBD1))),
                          ],
                        )),
                            ],
                          ),
                        );
                      }),
                    ],
                  ),
                );
              }),
              if (groups.length > 10)
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed: () => setState(() => showAll = !showAll),
                    child: Text(showAll ? 'Pokaż mniej' : 'Pokaż całą historię (${groups.length})'),
                  ),
                ),
            ],
      ),
    );
  }
}
'''


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f'Nie znaleziono punktu montażu: {label}')
    return source.replace(old, new, 1)


def _replace_in_scope(source: str, scope_marker: str, old: str, new: str, label: str) -> str:
    start = source.find(scope_marker)
    if start < 0:
        raise RuntimeError(f'Nie znaleziono zakresu: {label}')
    tail = source[start:]
    if old not in tail:
        raise RuntimeError(f'Nie znaleziono punktu montażu: {label}')
    tail = tail.replace(old, new, 1)
    return source[:start] + tail


def _apply_runtime_enhancements(source: str) -> str:
    source = _replace_once(
        source,
        "        'X-Cidex-Token': token,\n      };",
        "        'X-Cidex-Token': token,\n        if (_wmmSessionId.trim().isNotEmpty) 'X-WMM-Session': _wmmSessionId.trim(),\n      };",
        'nagłówek sesji WMM',
    )
    source = _replace_once(
        source,
        "      _startWmmPresence(config, sessionId, heartbeatSeconds);",
        "      _wmmCurrentUser = user;\n      _startWmmPresence(config, sessionId, heartbeatSeconds);",
        'zapamiętanie użytkownika WMM',
    )

    machine_thumb_old = """                                      Container(
                                        width: 48,
                                        height: 48,
                                        decoration: BoxDecoration(
                                          color: color.withValues(alpha: 0.16),
                                          borderRadius: BorderRadius.circular(15),
                                        ),
                                        child: Icon(Icons.precision_manufacturing_rounded, color: color),
                                      ),
"""
    machine_thumb_new = """                                      WmmObjectThumb(
                                        api: widget.api,
                                        photos: item['photos'],
                                        icon: Icons.precision_manufacturing_rounded,
                                        accent: color,
                                      ),
"""
    source = _replace_in_scope(
        source,
        'class _MachinesScreenState',
        machine_thumb_old,
        machine_thumb_new,
        'miniatura maszyny',
    )

    tool_thumb_old = """                                      const Icon(Icons.handyman_rounded, color: kOrange, size: 32),
"""
    tool_thumb_new = """                                      WmmObjectThumb(
                                        api: widget.api,
                                        photos: item['photos'],
                                        icon: Icons.handyman_rounded,
                                        accent: kOrange,
                                      ),
"""
    source = _replace_in_scope(
        source,
        'class _ToolsScreenState',
        tool_thumb_old,
        tool_thumb_new,
        'miniatura narzędzia',
    )

    machine_history_old = """                const SizedBox(height: 14),
                GridView.count(
"""
    machine_history_new = """                if (_wmmIsForeman) ...[
                  const SizedBox(height: 14),
                  WmmHistorySection(history: machine['historia'], title: 'Historia maszyny'),
                ],
                const SizedBox(height: 14),
                GridView.count(
"""
    source = _replace_in_scope(
        source,
        'class _MachineScreenState',
        machine_history_old,
        machine_history_new,
        'historia maszyny dla brygadzisty',
    )

    tool_history_old = """                const SizedBox(height: 12),
                GridView.count(
"""
    tool_history_new = """                if (_wmmIsForeman) ...[
                  const SizedBox(height: 12),
                  WmmHistorySection(history: tool['historia'], title: 'Historia narzędzia'),
                ],
                const SizedBox(height: 12),
                GridView.count(
"""
    source = _replace_in_scope(
        source,
        'class _ToolScreenState',
        tool_history_old,
        tool_history_new,
        'historia narzędzia dla brygadzisty',
    )

    if 'class WmmObjectThumb extends StatelessWidget' not in source:
        source = source.rstrip() + '\n\n' + RUNTIME_HELPERS.strip() + '\n'
    return source


def main() -> None:
    main_file = Path('lib/main.dart')
    login_template = Path('template/wmm_login.dart')

    source = main_file.read_text(encoding='utf-8')
    if "import 'dart:async';\n" not in source:
        source = source.replace(
            "import 'dart:convert';\n",
            "import 'dart:async';\nimport 'dart:convert';\n",
            1,
        )
    if "import 'package:flutter_secure_storage/flutter_secure_storage.dart';\n" not in source:
        source = source.replace(
            "import 'package:flutter/material.dart';\n",
            "import 'package:flutter/material.dart';\nimport 'package:flutter_secure_storage/flutter_secure_storage.dart';\n",
            1,
        )

    needle = '      home: HomeScreen(initialConfig: initialConfig),\n'
    replacement = '      home: WmmLoginGate(initialConfig: initialConfig),\n'
    if needle not in source:
        raise RuntimeError('Nie znaleziono punktu montażu WMM LoginGate')
    source = source.replace(needle, replacement, 1)

    login_source = login_template.read_text(encoding='utf-8').strip()
    if 'class WmmLoginGate ' in source:
        raise RuntimeError('WMM LoginGate jest już w lib/main.dart')
    source = source.rstrip() + '\n\n' + login_source + '\n'
    source = _apply_runtime_enhancements(source)
    main_file.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
