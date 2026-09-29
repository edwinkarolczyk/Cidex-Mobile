from __future__ import annotations

from pathlib import Path


def replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    source = replace_required(
        source,
        "  bool _wmmBackgroundCheckBusy = false;\n",
        "  bool _wmmBackgroundCheckBusy = false;\n"
        "  bool _resumeSessionCheckBusy = false;\n",
        "flaga kontroli sesji po powrocie",
    )

    source = replace_required(
        source,
        "      refresh();\n"
        "      WmmNotifications.check(api);\n"
        "      _openPendingSystemNotification();\n",
        "      unawaited(_checkSessionAfterResume());\n",
        "obsługa resumed po wszystkich patchach WMM",
    )

    resume_method = """  Future<void> _checkSessionAfterResume() async {
    if (_resumeSessionCheckBusy || !mounted || _wmmSessionId.trim().isEmpty) {
      return;
    }
    _resumeSessionCheckBusy = true;
    try {
      setState(() {
        busy = true;
        connectionText = 'Sprawdzanie sesji WMM...';
      });

      final state = await _wmmCheckSession(config);
      if (!mounted) return;

      if (state == WmmSessionCheckState.expired) {
        _stopWmmPresence();
        _wmmCurrentUser = <String, dynamic>{};
        setState(() {
          connected = false;
          busy = false;
          connectionText = wmmSessionStateLabel(state);
        });
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(
            builder: (_) => WmmLoginGate(
              initialConfig: config,
              initialNotice: 'Sesja WMM wygasła. Zaloguj się ponownie.',
            ),
          ),
          (route) => false,
        );
        return;
      }

      if (state == WmmSessionCheckState.offline) {
        setState(() {
          connected = false;
          busy = false;
          connectionText = kWmmOfflineHelp;
        });
        return;
      }

      setState(() {
        connected = true;
        busy = false;
        connectionText = wmmSessionStateLabel(state);
      });
      await refresh();
      if (mounted) {
        await WmmNotifications.check(api);
        await _openPendingSystemNotification();
      }
    } finally {
      _resumeSessionCheckBusy = false;
    }
  }

"""

    source = replace_required(
        source,
        "  Future<void> _openPendingSystemNotification() async {\n",
        resume_method + "  Future<void> _openPendingSystemNotification() async {\n",
        "metoda sprawdzania sesji po resumed",
    )

    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
