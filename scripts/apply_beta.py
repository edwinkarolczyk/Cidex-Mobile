from pathlib import Path


def main() -> None:
    main_file = Path('lib/main.dart')
    source = main_file.read_text(encoding='utf-8')

    source = source.replace("title: 'Warsztat Menager Mobile'", "title: 'Warsztat Menager Mobile BETA'")
    source = source.replace("Text('Warsztat Menager Mobile'", "Text('Warsztat Menager Mobile BETA'")
    source = source.replace("'Warsztat Menager Mobile',", "'Warsztat Menager Mobile BETA',")

    marker = "        'X-WMM-Key': token,\n"
    session_line = "        if (_wmmSessionId.trim().isNotEmpty) 'X-WMM-Session': _wmmSessionId.trim(),\n"
    if session_line not in source:
        if marker not in source:
            raise RuntimeError('Nie znaleziono nagłówków WMM API')
        source = source.replace(marker, marker + session_line, 1)

    main_file.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
