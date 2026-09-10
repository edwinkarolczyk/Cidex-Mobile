from pathlib import Path


def main() -> None:
    main_file = Path('lib/main.dart')
    source = main_file.read_text(encoding='utf-8')

    source = source.replace("title: 'Warsztat Menager Mobile'", "title: 'Warsztat Menager Mobile BETA'")
    source = source.replace("Text('Warsztat Menager Mobile'", "Text('Warsztat Menager Mobile BETA'")
    source = source.replace("'Warsztat Menager Mobile',", "'Warsztat Menager Mobile BETA',")
    source = source.replace("Warsztat Menager Mobile</", "Warsztat Menager Mobile BETA</")

    marker = "        'X-WMM-Key': token,\n"
    session_line = "        if (_wmmSessionId.trim().isNotEmpty) 'X-WMM-Session': _wmmSessionId.trim(),\n"
    if session_line not in source:
        if marker not in source:
            raise RuntimeError('Nie znaleziono nagłówków WMM API')
        source = source.replace(marker, marker + session_line, 1)

    photo_old = """  String photoUrl(String relative) {
    if (relative.startsWith('http://') || relative.startsWith('https://')) {
      return relative;
    }
    return '$baseUrl$relative';
  }
"""
    photo_new = """  String photoUrl(String relative) {
    if (relative.startsWith('http://') || relative.startsWith('https://')) {
      return relative;
    }
    if (relative.startsWith('/api/v1/media/')) {
      return '$baseUrl$relative/view';
    }
    return '$baseUrl$relative';
  }
"""
    if photo_old in source:
        source = source.replace(photo_old, photo_new, 1)

    main_file.write_text(source, encoding='utf-8')

    manifest = Path('android/app/src/main/AndroidManifest.xml')
    if manifest.is_file():
        text = manifest.read_text(encoding='utf-8')
        text = text.replace('android:label="Warsztat Menager Mobile"', 'android:label="WMM BETA"')
        manifest.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
