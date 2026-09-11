from pathlib import Path


def main() -> None:
    path = Path('lib/main.dart')
    source = path.read_text(encoding='utf-8')

    old = """      final authenticated = await _wmmLocalAuth.authenticate(
        localizedReason: 'Zaloguj się do Warsztat Menager Mobile',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
"""
    new = """      final authenticated = await _wmmLocalAuth.authenticate(
        localizedReason: 'Zaloguj się do Warsztat Menager Mobile',
        biometricOnly: true,
        persistAcrossBackgrounding: true,
      );
"""
    if old not in source:
        raise RuntimeError('Nie znaleziono starego wywołania local_auth')
    source = source.replace(old, new, 1)
    path.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
