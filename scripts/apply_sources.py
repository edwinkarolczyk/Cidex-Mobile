from __future__ import annotations

from pathlib import Path
import shutil


def main() -> None:
    Path("lib").mkdir(exist_ok=True)
    Path("test").mkdir(exist_ok=True)

    source = Path("template/main.dart").read_text(encoding="utf-8")
    source = source.replace(
        "      return _decode(response);",
        "      return await _decode(response);",
    )
    Path("lib/main.dart").write_text(source, encoding="utf-8")

    shutil.copyfile("template/pubspec.yaml", "pubspec.yaml")
    shutil.copyfile("template/widget_test.dart", "test/widget_test.dart")


if __name__ == "__main__":
    main()
