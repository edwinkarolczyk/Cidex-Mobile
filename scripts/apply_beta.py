from pathlib import Path


APP_VERSION = '0.5.10'
APP_CHANNEL = 'BETA'
APP_VISIBLE_NAME = f'Warsztat Menager Mobile {APP_VERSION} {APP_CHANNEL}'
APP_SHORT_NAME = f'WMM {APP_VERSION} {APP_CHANNEL}'


def main() -> None:
    main_file = Path('lib/main.dart')
    source = main_file.read_text(encoding='utf-8')

    # Wersja ma być widoczna użytkownikowi w samej aplikacji, nie tylko w metadanych APK.
    source = source.replace("title: 'Warsztat Menager Mobile'", f"title: '{APP_VISIBLE_NAME}'")
    source = source.replace("Text('Warsztat Menager Mobile'", f"Text('{APP_VISIBLE_NAME}'")
    source = source.replace("'Warsztat Menager Mobile',", f"'{APP_VISIBLE_NAME}',")
    source = source.replace("Warsztat Menager Mobile</", f"{APP_VISIBLE_NAME}</")

    # Jeśli wcześniejszy etap już dopisał samo BETA, uzupełnij numer wersji.
    source = source.replace('Warsztat Menager Mobile BETA', APP_VISIBLE_NAME)
    source = source.replace('WMM BETA', APP_SHORT_NAME)

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
        text = text.replace('android:label="Warsztat Menager Mobile"', f'android:label="{APP_SHORT_NAME}"')
        text = text.replace('android:label="WMM BETA"', f'android:label="{APP_SHORT_NAME}"')
        manifest.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
