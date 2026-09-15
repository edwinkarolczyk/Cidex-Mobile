from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.22"


def _replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    source = _replace_required(
        source,
        "class _WmmHomeVersionBannerState extends State<WmmHomeVersionBanner>\n    with SingleTickerProviderStateMixin {",
        "class _WmmHomeVersionBannerState extends State<WmmHomeVersionBanner>\n    with SingleTickerProviderStateMixin, WidgetsBindingObserver {",
        "obserwator cyklu życia bannera aktualizacji",
    )

    source = _replace_required(
        source,
        "  WmmReleaseInfo? latestInfo;\n  bool checking = true;\n",
        "  WmmReleaseInfo? latestInfo;\n  bool checking = true;\n  String updateError = '';\n",
        "stan błędu aktualizacji",
    )

    source = _replace_required(
        source,
        "    _pulse = AnimationController(\n      vsync: this,\n      duration: const Duration(milliseconds: 850),\n      value: 1,\n    );\n    _check();\n",
        "    _pulse = AnimationController(\n      vsync: this,\n      duration: const Duration(milliseconds: 850),\n      value: 1,\n    );\n    WidgetsBinding.instance.addObserver(this);\n    _check();\n",
        "rejestracja obserwatora aktualizacji",
    )

    source = _replace_required(
        source,
        "  Future<void> _check() async {\n    try {\n",
        "  Future<void> _check() async {\n    if (mounted) {\n      setState(() {\n        checking = true;\n        updateError = '';\n      });\n    }\n    try {\n",
        "jawne rozpoczęcie sprawdzania aktualizacji",
    )

    source = _replace_required(
        source,
        "    } catch (_) {\n      if (!mounted) return;\n      setState(() => checking = false);\n      _pulse.stop();\n      _pulse.value = 1;\n    }\n  }\n\n  @override\n  void dispose() {\n    _pulse.dispose();\n    super.dispose();\n  }\n",
        "    } catch (_) {\n      if (!mounted) return;\n      setState(() {\n        checking = false;\n        updateError = 'Nie udało się sprawdzić aktualizacji.';\n      });\n      _pulse.stop();\n      _pulse.value = 1;\n    }\n  }\n\n  @override\n  void didChangeAppLifecycleState(AppLifecycleState state) {\n    if (state == AppLifecycleState.resumed && !checking) {\n      _check();\n    }\n  }\n\n  @override\n  void dispose() {\n    WidgetsBinding.instance.removeObserver(this);\n    _pulse.dispose();\n    super.dispose();\n  }\n",
        "odświeżenie aktualizacji po powrocie do aplikacji",
    )

    old_row = """                  Row(
                    children: [
                      const Icon(
                        Icons.check_circle_rounded,
                        color: kGreen,
                        size: 15,
                      ),
                      const SizedBox(width: 7),
                      Expanded(
                        child: Text(
                          'Aktualna wersja: WMM $kWmmCurrentVersion',
                          style: const TextStyle(
                            color: kGreen,
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      if (checking)
                        const SizedBox(
                          width: 13,
                          height: 13,
                          child: CircularProgressIndicator(
                            strokeWidth: 1.6,
                            color: kMuted,
                          ),
                        ),
                    ],
                  ),
"""
    new_row = """                  Row(
                    children: [
                      const Icon(
                        Icons.check_circle_rounded,
                        color: kGreen,
                        size: 15,
                      ),
                      const SizedBox(width: 7),
                      Expanded(
                        child: Text(
                          'Aktualna wersja: WMM $kWmmCurrentVersion',
                          style: const TextStyle(
                            color: kGreen,
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      if (checking)
                        const SizedBox(
                          width: 13,
                          height: 13,
                          child: CircularProgressIndicator(
                            strokeWidth: 1.6,
                            color: kMuted,
                          ),
                        )
                      else
                        IconButton(
                          visualDensity: VisualDensity.compact,
                          tooltip: 'Sprawdź aktualizacje',
                          onPressed: _check,
                          icon: const Icon(Icons.refresh_rounded, size: 18, color: kMuted),
                        ),
                    ],
                  ),
                  if (updateError.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        '$updateError Dotknij ↻, aby spróbować ponownie.',
                        style: const TextStyle(color: kRed, fontSize: 11, fontWeight: FontWeight.w700),
                      ),
                    ),
"""
    source = _replace_required(source, old_row, new_row, "ręczne odświeżanie aktualizacji")

    source = source.replace(
        "          'X-GitHub-Api-Version': '2022-11-28',\n",
        "          'X-GitHub-Api-Version': '2022-11-28',\n          'Cache-Control': 'no-cache',\n          'Pragma': 'no-cache',\n",
        1,
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
        text = text.replace("WMM 0.5.21", f"WMM {APP_VERSION}")
        text = text.replace("expect(kWmmCurrentVersion, '0.5.21');", f"expect(kWmmCurrentVersion, '{APP_VERSION}');")
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
