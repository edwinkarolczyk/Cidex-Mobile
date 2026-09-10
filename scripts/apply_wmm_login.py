from pathlib import Path


def main() -> None:
    main_file = Path('lib/main.dart')
    login_template = Path('template/wmm_login.dart')

    source = main_file.read_text(encoding='utf-8')
    if "import 'dart:async';\n" not in source:
        source = source.replace(
            "import 'dart:convert';\n",
            "import 'dart:async';\nimport 'dart:convert';\n",
            1,
        )
    if "import 'package:flutter_secure_storage/flutter_secure_storage.dart';\n" not in source:
        source = source.replace(
            "import 'package:flutter/material.dart';\n",
            "import 'package:flutter/material.dart';\nimport 'package:flutter_secure_storage/flutter_secure_storage.dart';\n",
            1,
        )

    needle = '      home: HomeScreen(initialConfig: initialConfig),\n'
    replacement = '      home: WmmLoginGate(initialConfig: initialConfig),\n'
    if needle not in source:
        raise RuntimeError('Nie znaleziono punktu montażu WMM LoginGate')
    source = source.replace(needle, replacement, 1)

    login_source = login_template.read_text(encoding='utf-8').strip()
    if 'class WmmLoginGate ' in source:
        raise RuntimeError('WMM LoginGate jest już w lib/main.dart')
    source = source.rstrip() + '\n\n' + login_source + '\n'
    main_file.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
