from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.34"


def replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    old_row = """              return Padding(
                padding: const EdgeInsets.only(top: 5),
                child: Row(
                  children: [
                    const Icon(Icons.circle, size: 7, color: kOrange),
                    const SizedBox(width: 8),
                    Expanded(child: Text('$date • $type • $sourceLabel', style: const TextStyle(fontSize: 13))),
                  ],
                ),
              );
"""
    new_row = """              final status = (row['status'] ?? 'planned').toString().trim().toLowerCase();
              final inProgress = status == 'in_progress';
              return Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: kPanel2,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: inProgress ? kOrange : kBorder),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.event_available_rounded, size: 18, color: kOrange),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '$date • $type • $sourceLabel',
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Expanded(
                            child: Text(
                              'Oznacz ten istniejący wpis z WM jako wykonany.',
                              style: TextStyle(color: kMuted, fontSize: 12),
                            ),
                          ),
                          const WmmHelpIcon(
                            text: 'WYKONANO zapisuje wykonanie w tym samym przeglądzie WM: datę, login i opcjonalną notatkę. Nie tworzy nowego przeglądu ani duplikatu.',
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      SizedBox(
                        height: 42,
                        child: FilledButton.icon(
                          style: FilledButton.styleFrom(backgroundColor: kGreen),
                          onPressed: actionBusy ? null : () => _completeCycleReview(row),
                          icon: Icon(inProgress ? Icons.task_alt_rounded : Icons.check_circle_rounded),
                          label: Text(
                            inProgress ? 'ZAKOŃCZ PRZEGLĄD' : 'WYKONANO',
                            style: const TextStyle(fontWeight: FontWeight.w900),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
"""
    source = replace_required(source, old_row, new_row, "akcja WYKONANO przy widocznym przeglądzie")

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
        text = text.replace("WMM 0.5.23", f"WMM {APP_VERSION}")
        closing = text.rfind("}\n")
        if closing >= 0:
            extra = f"""\n  test('WMM {APP_VERSION} pozwala oznaczyć widoczny przegląd jako wykonany', () {{\n    expect(kWmmCurrentVersion, '{APP_VERSION}');\n  }});\n"""
            text = text[:closing] + extra + text[closing:]
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
