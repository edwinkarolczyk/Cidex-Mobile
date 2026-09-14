from pathlib import Path


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")
    old = """    final values = await _askReceipt();
    if (values == null) return;
    final qty = double.tryParse((values['qty'] ?? '').replaceAll(',', '.'));
"""
    new = """    final values = await _askReceipt();
    if (!mounted || values == null) return;
    final qty = double.tryParse((values['qty'] ?? '').replaceAll(',', '.'));
"""
    if old not in source:
        raise RuntimeError("Nie znaleziono miejsca ochrony mounted dla przyjęcia Magazynu")
    source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
