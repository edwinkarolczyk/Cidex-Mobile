from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.14"

# Ten patch działa jako ostatni etap generowania i uruchamia sprawdzanie GitHuba już na LoginGate.

def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    gate_marker = "class _WmmLoginGateState extends State<WmmLoginGate> {\n"
    gate_start = source.find(gate_marker)
    if gate_start < 0:
        raise RuntimeError("Nie znaleziono WmmLoginGate")

    tail = source[gate_start:]
    anchor = (
        "                  const SizedBox(height: 28),\n"
        "                  RoundedCard(\n"
    )
    replacement = (
        "                  const SizedBox(height: 10),\n"
        "                  WmmHomeVersionBanner(\n"
        "                    onOpenUpdates: () => Navigator.of(context).push(\n"
        "                      MaterialPageRoute(\n"
        "                        builder: (_) => const WmmUpdateScreen(),\n"
        "                      ),\n"
        "                    ),\n"
        "                  ),\n"
        "                  const SizedBox(height: 18),\n"
        "                  RoundedCard(\n"
    )
    if anchor not in tail:
        raise RuntimeError("Nie znaleziono miejsca na sprawdzanie aktualizacji przy starcie")
    tail = tail.replace(anchor, replacement, 1)
    source = source[:gate_start] + tail

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
