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

class WmmHistorySection extends StatelessWidget {
  const WmmHistorySection({super.key, required this.history, required this.title});

  final dynamic history;
  final String title;

  @override
  Widget build(BuildContext context) {
    final rows = (history as List? ?? const [])
        .whereType<Map>()
        .map(Map<String, dynamic>.from)
        .toList()
        .reversed
        .take(20)
        .toList();

    return RoundedCard(
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(top: 6),
        leading: const Icon(Icons.history_rounded, color: kOrange),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text('${rows.length} ostatnich wpisów', style: const TextStyle(color: kMuted)),
        children: rows.isEmpty
            ? const [
                Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Brak historii.', style: TextStyle(color: kMuted)),
                  ),
                ),
              ]
            : rows.map((row) {
                final when = (row['kiedy'] ?? row['created_at'] ?? '').toString().trim();
                final who = (row['kto'] ?? row['author'] ?? '—').toString().trim();
                final what = (row['co'] ?? row['action'] ?? 'zmiana').toString().trim();
                final note = (row['uwaga'] ?? row['note'] ?? '').toString().trim();
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(top: 4),
                        child: Icon(Icons.circle, size: 8, color: kOrange),
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(what, style: const TextStyle(fontWeight: FontWeight.w800)),
                            if (note.isNotEmpty)
                              Text(note, style: const TextStyle(color: Color(0xFFC6CBD1))),
                            Text(
                              [when, who].where((value) => value.isNotEmpty).join(' • '),
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
