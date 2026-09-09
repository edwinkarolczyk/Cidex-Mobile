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


def _replace_required(source: str, needle: str, replacement: str, label: str) -> str:
    if needle not in source:
        raise RuntimeError(f"Nie znaleziono punktu montażu: {label}")
    return source.replace(needle, replacement, 1)


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

    add_order = Path("template/planista_add.dart").read_text(encoding="utf-8")
    source = source.rstrip() + "\n\n" + add_order.strip() + "\n"
    Path("lib/main.dart").write_text(source, encoding="utf-8")

    shutil.copyfile("template/pubspec.yaml", "pubspec.yaml")
    shutil.copyfile("template/widget_test.dart", "test/widget_test.dart")


if __name__ == "__main__":
    main()
