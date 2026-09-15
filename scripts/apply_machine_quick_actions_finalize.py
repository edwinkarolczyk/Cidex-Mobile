from pathlib import Path
import re


APP_VERSION = "0.5.19"


def _remove_between(source: str, start_marker: str, end_marker: str, label: str) -> str:
    start = source.find(start_marker)
    if start < 0:
        raise RuntimeError(f"Nie znaleziono początku: {label}")
    end = source.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"Nie znaleziono końca: {label}")
    return source[:start] + source[end:]


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    # Lint z 0.5.18.
    source = source.replace("return '${minutes} min';", "return '$minutes min';", 1)

    # WMM nie może tworzyć planowanych przeglądów. Planowanie zostaje wyłącznie w WM.
    source = re.sub(
        r"const List<String> wmmMachineReviewTypes = <String>\[.*?\];\n\n",
        "",
        source,
        count=1,
        flags=re.S,
    )

    source = _remove_between(
        source,
        "  Future<Map<String, dynamic>> addPlannedMachineReview(",
        "\n}\n\nclass WmmMachineQuickActions",
        "API dodawania przeglądu",
    )

    source = _remove_between(
        source,
        "  String _dateText(DateTime value) =>",
        "\n\n  Future<String?> _askStartNote()",
        "pomocnicza data przeglądu",
    )

    source = _remove_between(
        source,
        "  Future<void> _addPlannedReview() async {",
        "\n\n  @override\n  Widget build(BuildContext context)",
        "formularz dodawania przeglądu",
    )

    review_button_start = """          const SizedBox(height: 10),
          SizedBox(
            height: 54,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: kOrange),
              onPressed: actionBusy ? null : _addPlannedReview,
"""
    review_button_end = "          if (planned.isNotEmpty)"
    source = _remove_between(
        source,
        review_button_start,
        review_button_end,
        "przycisk dodawania przeglądu",
    )

    source = source.replace(
        "Najbliższe planowane",
        "Przeglądy zaplanowane w WM",
    )
    source = source.replace(
        "Te przyciski korzystają wyłącznie z funkcji, które już istnieją w module Maszyny WM. Wpisy z telefonu są oznaczone [WMM] w istniejących uwagach lub opisach.",
        "Szybka naprawa zapisuje istniejący status Awaria w WM. Planowane przeglądy są tu tylko do podglądu i można je tworzyć wyłącznie w desktopowym WM.",
    )

    # Następna wersja bez widocznego napisu BETA.
    source = re.sub(
        r"const String kWmmCurrentVersion = '[^']+';",
        f"const String kWmmCurrentVersion = '{APP_VERSION}';",
        source,
        count=1,
    )
    source = re.sub(
        r"Warsztat Menager Mobile \d+\.\d+\.\d+ BETA",
        f"Warsztat Menager Mobile {APP_VERSION}",
        source,
    )
    source = re.sub(
        r"WMM \d+\.\d+\.\d+ BETA",
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
        old_extra = r'''  test('WMM 0.5.18 używa wyłącznie typów przeglądów istniejących w WM', () {
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
        text = text.replace(old_extra, "")
        text = text.replace("WMM 0.5.18", f"WMM {APP_VERSION}")
        text = text.replace("expect(kWmmCurrentVersion, '0.5.18');", f"expect(kWmmCurrentVersion, '{APP_VERSION}');")
        closing = text.rfind("}\n")
        if closing < 0:
            raise RuntimeError("Nie znaleziono końca testów WMM")
        extra = f'''\n  test('WMM {APP_VERSION} ma szybką naprawę i tylko podgląd planowanych przeglądów', () {{
    expect(wmmMachineStatusCode('Awaria'), 'warn');
    expect(wmmMachineStatusCode('warn'), 'warn');
    expect(wmmMachineStatusCode('Sprawna'), 'ok');
    expect(kWmmCurrentVersion, '{APP_VERSION}');
  }});\n'''
        text = text[:closing] + extra + text[closing:]
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
