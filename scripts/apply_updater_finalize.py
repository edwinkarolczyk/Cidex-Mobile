from pathlib import Path


def main() -> None:
    path = Path('lib/main.dart')
    source = path.read_text(encoding='utf-8')

    old = "      apk ??= assets.where((item) => (item['name'] ?? '').toString().toLowerCase().endsWith('.apk')).firstOrNull;\n"
    new = """      if (apk == null) {\n        for (final item in assets) {\n          if ((item['name'] ?? '').toString().toLowerCase().endsWith('.apk')) {\n            apk = item;\n            break;\n          }\n        }\n      }\n"""
    if old in source:
        source = source.replace(old, new, 1)

    source = source.replace(
        "onProgress((received / total).clamp(0.0, 1.0));",
        "onProgress((received / total).clamp(0.0, 1.0).toDouble());",
        1,
    )

    path.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
