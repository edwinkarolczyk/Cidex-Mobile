from pathlib import Path


def main() -> None:
    path = Path('lib/main.dart')
    source = path.read_text(encoding='utf-8')
    source = source.replace("return '$dd.$mo ${hh}:$mm';", "return '$dd.$mo $hh:$mm';")
    path.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
