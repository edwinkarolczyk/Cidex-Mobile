from __future__ import annotations

from pathlib import Path
import shutil


API_NEEDLE = """  Future<List<Map<String, dynamic>>> orders() async {
    final payload = await getJson('/api/v1/planista/orders');
    return _items(payload);
  }

  Future<List<Map<String, dynamic>>> machines() async {
"""

API_REPLACEMENT = """  Future<List<Map<String, dynamic>>> orders() async {
    final payload = await getJson('/api/v1/planista/orders');
    return _items(payload);
  }

  Future<List<Map<String, dynamic>>> products() async {
    final payload = await getJson('/api/v1/planista/products');
    return _items(payload);
  }

  Future<Map<String, dynamic>> createOrder({
    required String productCode,
    required num quantity,
    required String externalNo,
    String dueDate = '',
    String notes = '',
  }) async {
    final payload = await postJson(
      '/api/v1/planista/orders',
      {
        'product_code': productCode,
        'quantity': quantity,
        'external_no': externalNo,
        'due_date': dueDate,
        'notes': notes,
      },
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<List<Map<String, dynamic>>> machines() async {
"""

PLANNER_NEEDLE = """    return Scaffold(
      appBar: AppBar(
        title: const Text('Planista'),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      body: busy
"""

PLANNER_REPLACEMENT = """    return Scaffold(
      appBar: AppBar(
        title: const Text('Planista'),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: kOrange,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_rounded),
        label: const Text('DODAJ ZLECENIE', style: TextStyle(fontWeight: FontWeight.w900)),
        onPressed: () async {
          final created = await Navigator.of(context).push<bool>(
            MaterialPageRoute(builder: (_) => AddOrderScreen(api: widget.api)),
          );
          if (created == true) await load();
        },
      ),
      body: busy
"""

BRAND_HEADER_OLD = """              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(text: 'CID', style: TextStyle(color: Colors.white)),
                    TextSpan(text: 'EX', style: TextStyle(color: kOrange)),
                    TextSpan(text: ' Mobile', style: TextStyle(color: Color(0xFFD3D7DC))),
                  ],
                ),
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900),
              ),
              SizedBox(height: 2),
              Text('Warsztat pod kontrolą', style: TextStyle(color: kMuted)),
"""

BRAND_HEADER_NEW = """              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(text: 'WM', style: TextStyle(color: Colors.white)),
                    TextSpan(text: 'M', style: TextStyle(color: kOrange)),
                  ],
                ),
                style: TextStyle(fontSize: 29, fontWeight: FontWeight.w900, letterSpacing: 0.6),
              ),
              SizedBox(height: 2),
              Text('Warsztat Menager Mobile', style: TextStyle(color: kMuted, fontWeight: FontWeight.w700)),
"""

HEADER_ICON_OLD = """          child: const Icon(Icons.build_circle_rounded, color: kOrange, size: 34),
"""

HEADER_ICON_NEW = """          child: const Stack(
            alignment: Alignment.center,
            children: [
              Icon(Icons.settings_rounded, color: Color(0xFF9A9A9A), size: 42),
              Positioned(right: 3, top: 4, child: Icon(Icons.assignment_rounded, color: Color(0xFF353A3F), size: 25)),
              Positioned(left: 7, bottom: 6, child: Icon(Icons.build_rounded, color: kOrange, size: 29)),
            ],
          ),
"""


def _replace_required(source: str, needle: str, replacement: str, label: str) -> str:
    if needle not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(needle, replacement, 1)


def _apply_wmm_branding(source: str) -> str:
    source = source.replace("title: 'CIDEX Mobile'", "title: 'Warsztat Menager Mobile'")
    source = source.replace("Połączono z CIDEX na komputerze", "Połączono z Warsztat Menager")
    source = source.replace("const Text('CIDEX API'", "const Text('WMM'")
    source = source.replace("CIDEX API: błąd HTTP", "WMM: błąd HTTP")
    source = source.replace("Brak połączenia z CIDEX API:", "Brak połączenia z WMM:")
    source = source.replace("Nie udało się wysłać danych do CIDEX:", "Nie udało się wysłać danych z WMM:")
    source = source.replace("Połączenie z CIDEX", "Połączenie WMM")
    source = source.replace("Adres CIDEX API", "Adres serwera WMM")
    source = source.replace("Token CIDEX", "Token WMM")
    source = source.replace("Token skopiuj z okna serwera CIDEX.", "Token skopiuj z okna WMM na komputerze.")
    source = source.replace(
        "Wartości pobrano z bieżącego WM_ROOT przez CIDEX API.",
        "Wartości pobrano z Warsztat Menager przez WMM.",
    )
    source = source.replace(
        "const ValueRow(label: 'Autor zapisów mobilnych', value: 'Cidex'",
        "const ValueRow(label: 'Źródło operacji mobilnych', value: 'WMM'",
    )
    source = source.replace("Uwaga dodana jako Cidex.", "Uwaga dodana przez WMM.")
    source = source.replace(
        "Zapisy wykonane z telefonu używają autora „Cidex”.",
        "Zapisy z telefonu są wykonywane przez WMM.",
    )
    source = source.replace(
        "result = 'Połączono. API ${payload['api_version'] ?? ''}, autor ${payload['author'] ?? 'Cidex'}.';",
        "result = 'Połączono z WMM. API ${payload['api_version'] ?? ''}.';",
    )

    source = _replace_required(source, BRAND_HEADER_OLD, BRAND_HEADER_NEW, "nagłówek WMM")
    source = _replace_required(source, HEADER_ICON_OLD, HEADER_ICON_NEW, "znak WMM")

    # Motyw Warsztat Menager: kafle i przyciski robocze są grafitowe,
    # a kolor zostaje akcentem ikony/statusu zamiast pełnego tła.
    source = source.replace(
        "return Material(\n      color: color,\n      borderRadius: BorderRadius.circular(22),",
        "return Material(\n      color: kPanel,\n      borderRadius: BorderRadius.circular(22),",
    )
    source = source.replace(
        "return Material(\n      color: color,\n      borderRadius: BorderRadius.circular(19),",
        "return Material(\n      color: kPanel,\n      borderRadius: BorderRadius.circular(19),",
    )
    source = source.replace("Icon(icon, size: 34, color: Colors.white)", "Icon(icon, size: 34, color: color)")
    source = source.replace("Icon(icon, color: Colors.white, size: 28)", "Icon(icon, color: color, size: 28)")
    source = source.replace(
        "style: const TextStyle(fontSize: 12, color: Colors.white70),",
        "style: const TextStyle(fontSize: 12, color: kMuted),",
    )
    return source


def _apply_add_order_branding(source: str) -> str:
    source = source.replace("CIDEX API", "WMM")
    source = source.replace("CIDEX blokuje", "WMM blokuje")
    source = source.replace("CIDEX nie zmienia", "WMM nie zmienia")
    source = source.replace("Autor: Cidex.", "Źródło: WMM.")
    source = source.replace("Autor wpisu w historii: Cidex", "Źródło aplikacji: WMM")
    return source


def main() -> None:
    Path("lib").mkdir(exist_ok=True)
    Path("test").mkdir(exist_ok=True)

    source = Path("template/main.dart").read_text(encoding="utf-8")
    source = source.replace(
        "      return _decode(response);",
        "      return await _decode(response);",
    )
    source = _replace_required(source, API_NEEDLE, API_REPLACEMENT, "CidexApi Planista")
    source = _replace_required(source, PLANNER_NEEDLE, PLANNER_REPLACEMENT, "Planner FAB")
    source = _apply_wmm_branding(source)

    add_order = Path("template/planista_add.dart").read_text(encoding="utf-8")
    add_order = _apply_add_order_branding(add_order)
    source = source.rstrip() + "\n\n" + add_order.strip() + "\n"
    Path("lib/main.dart").write_text(source, encoding="utf-8")

    shutil.copyfile("template/pubspec.yaml", "pubspec.yaml")
    shutil.copyfile("template/widget_test.dart", "test/widget_test.dart")


if __name__ == "__main__":
    main()
