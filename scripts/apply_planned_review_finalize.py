from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.21"


def _replace_required(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    # 0.5.21: po QR pokazujemy każdy istniejący plan WM, nie tylko source=cycle.
    source = source.replace("/cycle-reviews", "/planned-reviews")

    source = source.replace(
        "Wykonano przegląd cykliczny",
        "Wykonano zaplanowany przegląd",
    )
    source = source.replace(
        "WMM oznaczy wybrany termin z harmonogramu WM jako wykonany. Nie tworzy nowego przeglądu ani nowego terminu.",
        "WMM oznaczy wybrany, istniejący termin z WM jako wykonany. Lista obejmuje wpisy ręczne i cykliczne; telefon nie tworzy nowego planu.",
    )
    source = source.replace(
        "Rozpoczęto istniejący przegląd cykliczny w WM.",
        "Rozpoczęto istniejący zaplanowany przegląd w WM.",
    )
    source = source.replace(
        "Przegląd cykliczny zapisano jako wykonany w WM.",
        "Zaplanowany przegląd zapisano jako wykonany w WM.",
    )
    source = source.replace(
        "Brak zaplanowanego przeglądu cyklicznego w WM.",
        "Brak zaplanowanych przeglądów tej maszyny w WM.",
    )
    source = source.replace(
        "'Przegląd cykliczny'",
        "'Przeglądy zaplanowane'",
        1,
    )
    source = source.replace(
        "Lista pochodzi z harmonogramu WM, także z terminów generowanych automatycznie. WMM nie tworzy ani nie planuje nowych przeglądów.",
        "Lista pochodzi bezpośrednio z WM: zawiera ręcznie zaplanowane wpisy oraz terminy cykliczne generowane z harmonogramu. WMM nie tworzy nowych planów.",
    )
    source = source.replace(
        "Wybierz konkretny termin istniejący w Warsztat Menager.",
        "Wybierz konkretny zaplanowany wpis istniejący w Warsztat Menager.",
    )
    source = source.replace(
        "label: const Text('PRZEGLĄD CYKLICZNY', style: TextStyle(fontWeight: FontWeight.w900)),",
        "label: const Text('PRZEGLĄD ZAPLANOWANY', style: TextStyle(fontWeight: FontWeight.w900)),",
    )
    source = source.replace(
        "Zakończ aktywną naprawę, aby rozpocząć przegląd cykliczny.",
        "Zakończ aktywną naprawę, aby rozpocząć zaplanowany przegląd.",
    )
    source = source.replace(
        "Szybka naprawa zapisuje istniejący status Awaria. Przegląd cykliczny korzysta wyłącznie z terminów już istniejących w harmonogramie WM.",
        "Szybka naprawa zapisuje istniejący status Awaria. Przegląd zaplanowany pokazuje wyłącznie wpisy już istniejące w WM — ręczne i cykliczne.",
    )

    status_block = """                    final status = (row['status'] ?? 'planned').toString();
                    final inProgress = status.trim().toLowerCase() == 'in_progress';
                    final startedBy = (row['started_by'] ?? '').toString().trim();
"""
    status_replacement = """                    final status = (row['status'] ?? 'planned').toString();
                    final inProgress = status.trim().toLowerCase() == 'in_progress';
                    final sourceValue = (row['source'] ?? 'manual').toString().trim().toLowerCase();
                    final sourceLabel = (row['source_label'] ??
                            (sourceValue == 'cycle' ? 'Cykliczny' : 'Ręczny / zaplanowany w WM'))
                        .toString();
                    final startedBy = (row['started_by'] ?? '').toString().trim();
"""
    source = _replace_required(source, status_block, status_replacement, "etykieta źródła przeglądu")

    type_line = """                          Text(type, style: const TextStyle(color: Color(0xFFD3D7DC))),
"""
    type_replacement = """                          Text(type, style: const TextStyle(color: Color(0xFFD3D7DC))),
                          const SizedBox(height: 2),
                          Text(sourceLabel, style: const TextStyle(color: kMuted, fontSize: 12)),
"""
    source = _replace_required(source, type_line, type_replacement, "widoczna informacja ręczny/cykliczny")

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
        text = text.replace("WMM 0.5.20", f"WMM {APP_VERSION}")
        text = text.replace("expect(kWmmCurrentVersion, '0.5.20');", f"expect(kWmmCurrentVersion, '{APP_VERSION}');")
        test.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
