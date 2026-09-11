from __future__ import annotations

from pathlib import Path


def main() -> None:
    path = Path('android/app/build.gradle.kts')
    if not path.is_file():
        raise RuntimeError('Brak android/app/build.gradle.kts')

    source = path.read_text(encoding='utf-8')

    if 'import java.util.Properties' not in source:
        source = 'import java.util.Properties\nimport java.io.FileInputStream\n\n' + source

    props = '''\nval wmmKeystoreProperties = Properties()\nval wmmKeystorePropertiesFile = rootProject.file("key.properties")\nif (wmmKeystorePropertiesFile.exists()) {\n    FileInputStream(wmmKeystorePropertiesFile).use { wmmKeystoreProperties.load(it) }\n}\n\n'''
    if 'val wmmKeystoreProperties = Properties()' not in source:
        marker = 'android {\n'
        if marker not in source:
            raise RuntimeError('Nie znaleziono bloku android w build.gradle.kts')
        source = source.replace(marker, props + marker, 1)

    signing = '''    signingConfigs {\n        create("wmmRelease") {\n            keyAlias = wmmKeystoreProperties["keyAlias"] as String\n            keyPassword = wmmKeystoreProperties["keyPassword"] as String\n            storeFile = file(wmmKeystoreProperties["storeFile"] as String)\n            storePassword = wmmKeystoreProperties["storePassword"] as String\n        }\n    }\n\n'''
    if 'create("wmmRelease")' not in source:
        marker = '    buildTypes {\n'
        if marker not in source:
            raise RuntimeError('Nie znaleziono buildTypes w build.gradle.kts')
        source = source.replace(marker, signing + marker, 1)

    old = 'signingConfig = signingConfigs.getByName("debug")'
    new = 'signingConfig = signingConfigs.getByName("wmmRelease")'
    if old in source:
        source = source.replace(old, new, 1)
    elif new not in source:
        raise RuntimeError('Nie znaleziono konfiguracji podpisu release')

    path.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
