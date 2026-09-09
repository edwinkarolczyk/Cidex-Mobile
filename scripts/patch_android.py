from __future__ import annotations

from pathlib import Path
import re

MANIFEST = Path("android/app/src/main/AndroidManifest.xml")


def main() -> None:
    if not MANIFEST.is_file():
        raise SystemExit(f"Brak manifestu Android: {MANIFEST}")

    text = MANIFEST.read_text(encoding="utf-8")
    permissions = []
    for permission in (
        "android.permission.INTERNET",
        "android.permission.CAMERA",
    ):
        marker = f'android:name="{permission}"'
        if marker not in text:
            permissions.append(
                f'    <uses-permission android:name="{permission}" />\n'
            )

    if permissions:
        start = text.find("<manifest")
        end = text.find(">", start)
        if start < 0 or end < 0:
            raise SystemExit("Nie rozpoznano struktury AndroidManifest.xml")
        text = text[: end + 1] + "\n" + "".join(permissions) + text[end + 1 :]

    def patch_application(match: re.Match[str]) -> str:
        block = match.group(0)
        if "android:usesCleartextTraffic" not in block:
            block = block[:-1] + '\n        android:usesCleartextTraffic="true">'
        return block

    text = re.sub(r"<application\b[^>]*>", patch_application, text, count=1)
    text = text.replace('android:label="cidex_mobile"', 'android:label="CIDEX Mobile"')
    MANIFEST.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
