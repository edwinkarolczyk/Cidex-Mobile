from __future__ import annotations

from pathlib import Path
import re

MANIFEST = Path("android/app/src/main/AndroidManifest.xml")
ICON = Path("android/app/src/main/res/drawable/wmm_launcher.xml")

WMM_ICON_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#0D0F12"
        android:pathData="M0,0h24v24h-24z" />
    <path
        android:fillColor="#A6A6A6"
        android:pathData="M19.43,12.98c0.04,-0.32 0.07,-0.65 0.07,-0.98s-0.02,-0.66 -0.07,-0.98l2.11,-1.65c0.19,-0.15 0.24,-0.42 0.12,-0.64l-2,-3.46c-0.12,-0.22 -0.37,-0.31 -0.6,-0.22l-2.49,1c-0.52,-0.4 -1.08,-0.73 -1.69,-0.98L14.5,2.42C14.47,2.18 14.25,2 14,2h-4c-0.25,0 -0.46,0.18 -0.5,0.42L9.12,5.07c-0.61,0.25 -1.17,0.59 -1.69,0.98l-2.49,-1c-0.23,-0.08 -0.48,0 -0.6,0.22l-2,3.46c-0.13,0.22 -0.07,0.49 0.12,0.64l2.11,1.65c-0.04,0.32 -0.08,0.66 -0.08,0.98s0.03,0.66 0.08,0.98l-2.11,1.65c-0.19,0.15 -0.24,0.42 -0.12,0.64l2,3.46c0.12,0.22 0.37,0.31 0.6,0.22l2.49,-1c0.52,0.4 1.08,0.73 1.69,0.98l0.38,2.65c0.04,0.24 0.25,0.42 0.5,0.42h4c0.25,0 0.46,-0.18 0.5,-0.42l0.38,-2.65c0.61,-0.25 1.17,-0.58 1.69,-0.98l2.49,1c0.23,0.08 0.48,0 0.6,-0.22l2,-3.46c0.12,-0.22 0.07,-0.49 -0.12,-0.64zM12,15.5A3.5,3.5 0,1 1,12,8a3.5,3.5 0,0 1,0,7.5z" />
    <group
        android:scaleX="0.62"
        android:scaleY="0.62"
        android:translateX="8.8"
        android:translateY="2.4">
        <path
            android:fillColor="#33383D"
            android:pathData="M19,3h-4.18C14.4,1.84 13.3,1 12,1s-2.4,0.84-2.82,2H5c-1.1,0-2,0.9-2,2v16c0,1.1 0.9,2 2,2h14c1.1,0 2,-0.9 2,-2V5c0,-1.1-0.9,-2-2,-2zm-7,0c0.55,0 1,0.45 1,1s-0.45,1-1,1-1,-0.45-1,-1 0.45,-1 1,-1zm2,16H7v-2h7v2zm3,-4H7v-2h10v2zm0,-4H7V9h10v2z" />
    </group>
    <group
        android:scaleX="0.72"
        android:scaleY="0.72"
        android:translateX="0.8"
        android:translateY="7.0">
        <path
            android:fillColor="#FF7A00"
            android:pathData="M22.7,19l-9.1,-9.1c0.9,-2.3 0.4,-5 -1.5,-6.9 -2,-2 -5,-2.4 -7.3,-1.3L9,5.9 5.9,9 1.6,4.7C0.4,7 0.9,10 2.9,12c1.9,1.9 4.6,2.4 6.9,1.5l9.1,9.1c0.4,0.4 1,0.4 1.4,0l2.3,-2.3c0.5,-0.3 0.5,-0.9 0.1,-1.3z" />
    </group>
</vector>
"""


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
        block = re.sub(
            r'android:label="[^"]*"',
            'android:label="Warsztat Menager Mobile"',
            block,
            count=1,
        )
        block = re.sub(
            r'android:icon="[^"]*"',
            'android:icon="@drawable/wmm_launcher"',
            block,
            count=1,
        )
        if "android:roundIcon" in block:
            block = re.sub(
                r'android:roundIcon="[^"]*"',
                'android:roundIcon="@drawable/wmm_launcher"',
                block,
                count=1,
            )
        else:
            block = block[:-1] + '\n        android:roundIcon="@drawable/wmm_launcher">'
        if "android:usesCleartextTraffic" not in block:
            block = block[:-1] + '\n        android:usesCleartextTraffic="true">'
        return block

    text = re.sub(r"<application\b[^>]*>", patch_application, text, count=1)
    MANIFEST.write_text(text, encoding="utf-8")

    ICON.parent.mkdir(parents=True, exist_ok=True)
    ICON.write_text(WMM_ICON_XML, encoding="utf-8")


if __name__ == "__main__":
    main()
