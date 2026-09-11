from __future__ import annotations

from pathlib import Path
import re

APP_VERSION = "0.5.10"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(old, new, 1)


def main() -> None:
    main_file = Path("lib/main.dart")
    source = main_file.read_text(encoding="utf-8")

    if "import 'package:local_auth/local_auth.dart';\n" not in source:
        source = replace_once(
            source,
            "import 'package:flutter/material.dart';\n",
            "import 'package:flutter/material.dart';\nimport 'package:local_auth/local_auth.dart';\n",
            "import local_auth",
        )

    source = replace_once(
        source,
        "const FlutterSecureStorage _wmmSecureStorage = FlutterSecureStorage();\n",
        "const FlutterSecureStorage _wmmSecureStorage = FlutterSecureStorage();\n"
        "final LocalAuthentication _wmmLocalAuth = LocalAuthentication();\n",
        "instancja LocalAuthentication",
    )

    source = replace_once(
        source,
        "  bool rememberPin = false;\n  String error = '';\n",
        "  bool rememberPin = false;\n"
        "  bool biometricEnabled = false;\n"
        "  bool biometricAvailable = false;\n"
        "  bool biometricBusy = false;\n"
        "  String biometricLabel = 'Biometria';\n"
        "  String error = '';\n",
        "pola biometrii",
    )

    source = replace_once(
        source,
        "    final savedRememberPin = prefs.getBool('wmm_remember_pin') ?? false;\n",
        "    final savedRememberPin = prefs.getBool('wmm_remember_pin') ?? false;\n"
        "    final savedBiometricEnabled = prefs.getBool('wmm_biometric_enabled') ?? false;\n",
        "odczyt ustawienia biometrii",
    )

    source = replace_once(
        source,
        "      rememberPin = savedRememberPin && savedRememberLogin;\n"
        "      if (rememberLogin && savedLogin.isNotEmpty) login.text = savedLogin;\n"
        "      if (rememberPin && savedPin.isNotEmpty) pin.text = savedPin;\n"
        "    });\n"
        "  }\n\n"
        "  Future<void> _saveRememberedCredentials(String userLogin, String userPin) async {\n",
        "      rememberPin = savedRememberPin && savedRememberLogin;\n"
        "      biometricEnabled = savedBiometricEnabled && rememberPin;\n"
        "      if (rememberLogin && savedLogin.isNotEmpty) login.text = savedLogin;\n"
        "      if (rememberPin && savedPin.isNotEmpty && !biometricEnabled) pin.text = savedPin;\n"
        "    });\n"
        "    await _refreshBiometricAvailability();\n"
        "    if (!mounted) return;\n"
        "    if (biometricEnabled && biometricAvailable && savedLogin.isNotEmpty && savedPin.isNotEmpty) {\n"
        "      WidgetsBinding.instance.addPostFrameCallback((_) {\n"
        "        if (mounted && !busy && !biometricBusy) _loginWithBiometrics();\n"
        "      });\n"
        "    }\n"
        "  }\n\n"
        "  Future<void> _refreshBiometricAvailability() async {\n"
        "    try {\n"
        "      final supported = await _wmmLocalAuth.isDeviceSupported();\n"
        "      final canCheck = await _wmmLocalAuth.canCheckBiometrics;\n"
        "      final types = supported && canCheck\n"
        "          ? await _wmmLocalAuth.getAvailableBiometrics()\n"
        "          : <BiometricType>[];\n"
        "      if (!mounted) return;\n"
        "      setState(() {\n"
        "        biometricAvailable = supported && canCheck && types.isNotEmpty;\n"
        "        if (types.contains(BiometricType.face)) {\n"
        "          biometricLabel = 'Twarz / biometria';\n"
        "        } else if (types.contains(BiometricType.fingerprint)) {\n"
        "          biometricLabel = 'Odcisk palca';\n"
        "        } else {\n"
        "          biometricLabel = 'Biometria';\n"
        "        }\n"
        "        if (!biometricAvailable) biometricEnabled = false;\n"
        "      });\n"
        "    } catch (_) {\n"
        "      if (!mounted) return;\n"
        "      setState(() {\n"
        "        biometricAvailable = false;\n"
        "        biometricEnabled = false;\n"
        "      });\n"
        "    }\n"
        "  }\n\n"
        "  Future<void> _setBiometricEnabled(bool value) async {\n"
        "    if (value && !biometricAvailable) {\n"
        "      if (mounted) setState(() => error = 'Najpierw skonfiguruj biometrię w Androidzie.');\n"
        "      return;\n"
        "    }\n"
        "    setState(() {\n"
        "      biometricEnabled = value;\n"
        "      if (value) {\n"
        "        rememberLogin = true;\n"
        "        rememberPin = true;\n"
        "      }\n"
        "      error = '';\n"
        "    });\n"
        "    final prefs = await SharedPreferences.getInstance();\n"
        "    await prefs.setBool('wmm_biometric_enabled', value);\n"
        "  }\n\n"
        "  Future<void> _loginWithBiometrics() async {\n"
        "    if (busy || biometricBusy || !biometricAvailable) return;\n"
        "    final prefs = await SharedPreferences.getInstance();\n"
        "    final savedLogin = (prefs.getString('wmm_last_login') ?? '').trim();\n"
        "    final savedPin = (await _wmmSecureStorage.read(key: 'wmm_saved_pin') ?? '').trim();\n"
        "    if (savedLogin.isEmpty || savedPin.isEmpty) {\n"
        "      if (!mounted) return;\n"
        "      setState(() => error = 'Zaloguj się raz loginem i PIN-em, aby aktywować biometrię.');\n"
        "      return;\n"
        "    }\n\n"
        "    setState(() {\n"
        "      biometricBusy = true;\n"
        "      error = '';\n"
        "    });\n"
        "    try {\n"
        "      final authenticated = await _wmmLocalAuth.authenticate(\n"
        "        localizedReason: 'Zaloguj się do Warsztat Menager Mobile',\n"
        "        options: const AuthenticationOptions(\n"
        "          biometricOnly: true,\n"
        "          stickyAuth: true,\n"
        "        ),\n"
        "      );\n"
        "      if (!authenticated || !mounted) return;\n"
        "      login.text = savedLogin;\n"
        "      pin.text = savedPin;\n"
        "      await submit();\n"
        "    } catch (_) {\n"
        "      if (!mounted) return;\n"
        "      setState(() => error = 'Nie udało się potwierdzić biometrii. Użyj PIN-u.');\n"
        "    } finally {\n"
        "      if (mounted) setState(() => biometricBusy = false);\n"
        "    }\n"
        "  }\n\n"
        "  Future<void> _saveRememberedCredentials(String userLogin, String userPin) async {\n",
        "logika biometrii",
    )

    source = replace_once(
        source,
        "    await prefs.setBool('wmm_remember_pin', rememberPin);\n",
        "    await prefs.setBool('wmm_remember_pin', rememberPin);\n"
        "    await prefs.setBool('wmm_biometric_enabled', biometricEnabled && rememberPin);\n",
        "zapis ustawienia biometrii",
    )

    source = replace_once(
        source,
        "                                    rememberPin = value ?? false;\n"
        "                                    if (rememberPin) rememberLogin = true;\n",
        "                                    rememberPin = value ?? false;\n"
        "                                    if (rememberPin) rememberLogin = true;\n"
        "                                    if (!rememberPin) biometricEnabled = false;\n",
        "powiązanie biometrii z zapamiętaniem PIN",
    )

    biometric_ui = """                        CheckboxListTile(\n                          value: biometricEnabled,\n                          contentPadding: EdgeInsets.zero,\n                          controlAffinity: ListTileControlAffinity.leading,\n                          activeColor: kOrange,\n                          secondary: Icon(\n                            biometricLabel.contains('Twarz') ? Icons.face_rounded : Icons.fingerprint_rounded,\n                            color: biometricAvailable ? kOrange : kMuted,\n                          ),\n                          title: const Text('Logowanie biometryczne'),\n                          subtitle: Text(\n                            biometricAvailable\n                                ? '$biometricLabel. PIN pozostaje metodą awaryjną.'\n                                : 'Brak skonfigurowanej biometrii w Androidzie.',\n                            style: const TextStyle(color: kMuted, fontSize: 12),\n                          ),\n                          onChanged: busy || biometricBusy || !biometricAvailable\n                              ? null\n                              : (value) => _setBiometricEnabled(value ?? false),\n                        ),\n                        if (biometricEnabled && biometricAvailable) ...[\n                          const SizedBox(height: 4),\n                          SizedBox(\n                            height: 50,\n                            child: OutlinedButton.icon(\n                              onPressed: busy || biometricBusy ? null : _loginWithBiometrics,\n                              icon: biometricBusy\n                                  ? const SizedBox(\n                                      width: 18,\n                                      height: 18,\n                                      child: CircularProgressIndicator(strokeWidth: 2),\n                                    )\n                                  : const Icon(Icons.fingerprint_rounded),\n                              label: const Text(\n                                'ZALOGUJ BIOMETRIĄ',\n                                style: TextStyle(fontWeight: FontWeight.w900),\n                              ),\n                            ),\n                          ),\n                        ],\n"""
    source = replace_once(
        source,
        "                        if (error.isNotEmpty) ...[\n",
        biometric_ui + "                        if (error.isNotEmpty) ...[\n",
        "UI biometrii",
    )

    source = re.sub(
        r"const String kWmmCurrentVersion = '[^']+';",
        f"const String kWmmCurrentVersion = '{APP_VERSION}';",
        source,
        count=1,
    )
    source = re.sub(
        r"subtitle: 'WMM \d+\.\d+\.\d+ BETA',",
        f"subtitle: 'WMM {APP_VERSION} BETA',",
        source,
        count=1,
    )
    main_file.write_text(source, encoding="utf-8")

    manifest = Path("android/app/src/main/AndroidManifest.xml")
    text = manifest.read_text(encoding="utf-8")
    permission = '<uses-permission android:name="android.permission.USE_BIOMETRIC" />'
    if permission not in text:
        start = text.find("<manifest")
        end = text.find(">", start)
        if start < 0 or end < 0:
            raise RuntimeError("Nie rozpoznano AndroidManifest.xml")
        text = text[: end + 1] + "\n    " + permission + text[end + 1 :]
    manifest.write_text(text, encoding="utf-8")

    activity = Path("android/app/src/main/kotlin/pl/cidex/cidex_mobile/MainActivity.kt")
    kotlin = activity.read_text(encoding="utf-8")
    kotlin = kotlin.replace(
        "import io.flutter.embedding.android.FlutterActivity",
        "import io.flutter.embedding.android.FlutterFragmentActivity",
    )
    kotlin = re.sub(r"class MainActivity\s*:\s*FlutterActivity\(\)", "class MainActivity : FlutterFragmentActivity()", kotlin, count=1)
    if "FlutterFragmentActivity" not in kotlin:
        raise RuntimeError("Nie udało się przełączyć MainActivity na FlutterFragmentActivity")
    activity.write_text(kotlin, encoding="utf-8")


if __name__ == "__main__":
    main()
