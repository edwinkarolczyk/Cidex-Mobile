from pathlib import Path


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")
    old = "return '${minutes} min';"
    new = "return '$minutes min';"
    if old not in source:
        raise RuntimeError("Nie znaleziono interpolacji czasu szybkiej naprawy")
    source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
