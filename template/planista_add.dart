class AddOrderScreen extends StatefulWidget {
  const AddOrderScreen({super.key, required this.api});

  final CidexApi api;

  @override
  State<AddOrderScreen> createState() => _AddOrderScreenState();
}

class _AddOrderScreenState extends State<AddOrderScreen> {
  final externalNo = TextEditingController();
  final quantity = TextEditingController(text: '1');
  final dueDate = TextEditingController();
  final notes = TextEditingController();

  List<Map<String, dynamic>> products = [];
  String selectedProduct = '';
  bool loadingProducts = true;
  bool saving = false;
  String error = '';

  @override
  void initState() {
    super.initState();
    loadProducts();
  }

  @override
  void dispose() {
    externalNo.dispose();
    quantity.dispose();
    dueDate.dispose();
    notes.dispose();
    super.dispose();
  }

  Future<void> loadProducts() async {
    setState(() {
      loadingProducts = true;
      error = '';
    });
    try {
      final rows = await widget.api.products();
      if (!mounted) return;
      setState(() {
        products = rows;
        if (rows.length == 1) {
          selectedProduct = (rows.first['kod'] ?? '').toString();
        }
      });
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loadingProducts = false);
    }
  }

  Future<void> pickDate() async {
    final now = DateTime.now();
    final selected = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 5),
      helpText: 'Data wysyłki',
      cancelText: 'ANULUJ',
      confirmText: 'WYBIERZ',
    );
    if (selected == null || !mounted) return;
    dueDate.text = '${selected.year.toString().padLeft(4, '0')}-${selected.month.toString().padLeft(2, '0')}-${selected.day.toString().padLeft(2, '0')}';
  }

  Future<void> save() async {
    if (saving) return;
    final external = externalNo.text.trim();
    final product = selectedProduct.trim();
    final qty = double.tryParse(quantity.text.trim().replaceAll(',', '.'));

    if (external.isEmpty) {
      setState(() => error = 'Podaj numer Zlecenia wew.');
      return;
    }
    if (product.isEmpty) {
      setState(() => error = 'Wybierz produkt z aktualnej kartoteki WM.');
      return;
    }
    if (qty == null || qty <= 0) {
      setState(() => error = 'Ilość musi być liczbą większą od zera.');
      return;
    }

    setState(() {
      saving = true;
      error = '';
    });
    try {
      final order = await widget.api.createOrder(
        productCode: product,
        quantity: qty,
        externalNo: external,
        dueDate: dueDate.text.trim(),
        notes: notes.text.trim(),
      );
      if (!mounted) return;
      final id = (order['id'] ?? '').toString();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Dodano zlecenie warsztatowe ${id.isEmpty ? '' : id}. Autor: Cidex.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> help(String title, String text) async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: Text(text),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Widget labelWithHelp(String label, String helpText) {
    return Row(
      children: [
        Expanded(
          child: Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
        ),
        IconButton(
          visualDensity: VisualDensity.compact,
          tooltip: 'Wyjaśnienie',
          onPressed: () => help(label, helpText),
          icon: const Icon(Icons.info_outline_rounded, color: kOrange, size: 21),
        ),
      ],
    );
  }

  String productLabel(Map<String, dynamic> item) {
    final code = (item['kod'] ?? '').toString().trim();
    final name = (item['nazwa'] ?? '').toString().trim();
    if (name.isEmpty || name == code) return code;
    return '$code — $name';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dodaj zlecenie')),
      body: Stack(
        children: [
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const RoundedCard(
                child: Text(
                  'Zlecenie zostanie zapisane bezpośrednio w istniejącym formacie Planisty WM przez CIDEX API. Nie są tworzone nowe pola ani rezerwacje materiałowe.',
                  style: TextStyle(color: Color(0xFFC8CED5), height: 1.45),
                ),
              ),
              const SizedBox(height: 14),
              labelWithHelp(
                'Zlecenie wew *',
                'Numer zlecenia wewnętrznego używany do rozpoznania pozycji. CIDEX blokuje przypadkowy duplikat tego numeru dla tego samego produktu.',
              ),
              TextField(
                controller: externalNo,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  hintText: 'np. 2026/154',
                  prefixIcon: Icon(Icons.confirmation_number_outlined),
                ),
              ),
              const SizedBox(height: 10),
              labelWithHelp(
                'Produkt *',
                'Lista pochodzi bezpośrednio z kartoteki produktów WM. Zapis nastąpi po istniejącym kodzie produktu, bez tworzenia nowego produktu.',
              ),
              if (loadingProducts)
                const RoundedCard(
                  child: Row(
                    children: [
                      SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: kOrange)),
                      SizedBox(width: 12),
                      Text('Pobieranie produktów z WM...'),
                    ],
                  ),
                )
              else if (products.isEmpty)
                RoundedCard(
                  child: Row(
                    children: [
                      const Expanded(child: Text('Brak produktów w bieżącym WM_ROOT.')),
                      IconButton(onPressed: loadProducts, icon: const Icon(Icons.refresh_rounded)),
                    ],
                  ),
                )
              else
                DropdownButtonFormField<String>(
                  initialValue: selectedProduct.isEmpty ? null : selectedProduct,
                  isExpanded: true,
                  decoration: const InputDecoration(prefixIcon: Icon(Icons.inventory_2_outlined)),
                  hint: const Text('Wybierz produkt'),
                  items: products
                      .map(
                        (item) => DropdownMenuItem<String>(
                          value: (item['kod'] ?? '').toString(),
                          child: Text(productLabel(item), overflow: TextOverflow.ellipsis),
                        ),
                      )
                      .toList(),
                  onChanged: saving ? null : (value) => setState(() => selectedProduct = value ?? ''),
                ),
              const SizedBox(height: 10),
              labelWithHelp(
                'Ilość *',
                'Podaj ilość zlecaną do wykonania. CIDEX nie zmienia przy tym stanów magazynowych ani nie tworzy rezerwacji materiału.',
              ),
              TextField(
                controller: quantity,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(prefixIcon: Icon(Icons.numbers_rounded)),
              ),
              const SizedBox(height: 10),
              labelWithHelp(
                'Data wysyłki',
                'Opcjonalny termin zapisany do istniejącego pola terminu zlecenia. Możesz wybrać datę z kalendarza albo pozostawić pole puste.',
              ),
              TextField(
                controller: dueDate,
                readOnly: true,
                onTap: pickDate,
                decoration: InputDecoration(
                  hintText: 'rrrr-mm-dd',
                  prefixIcon: const Icon(Icons.event_rounded),
                  suffixIcon: dueDate.text.isEmpty
                      ? const Icon(Icons.calendar_month_rounded)
                      : IconButton(
                          tooltip: 'Wyczyść termin',
                          onPressed: () => setState(dueDate.clear),
                          icon: const Icon(Icons.close_rounded),
                        ),
                ),
              ),
              const SizedBox(height: 10),
              labelWithHelp(
                'Uwagi',
                'Krótka informacja dodatkowa do zlecenia. Zostanie zapisana w istniejącym polu uwag WM.',
              ),
              TextField(
                controller: notes,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(
                  hintText: 'Opcjonalne uwagi...',
                  prefixIcon: Icon(Icons.notes_rounded),
                ),
              ),
              if (error.isNotEmpty) ...[
                const SizedBox(height: 12),
                RoundedCard(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.error_outline_rounded, color: kRed),
                      const SizedBox(width: 10),
                      Expanded(child: Text(error, style: const TextStyle(color: Color(0xFFFFB8B3)))),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 16),
              SizedBox(
                height: 60,
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(backgroundColor: kOrange),
                  onPressed: saving || loadingProducts ? null : save,
                  icon: const Icon(Icons.add_task_rounded),
                  label: const Text('DODAJ ZLECENIE DO WM', style: TextStyle(fontWeight: FontWeight.w900)),
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Autor wpisu w historii: Cidex',
                textAlign: TextAlign.center,
                style: TextStyle(color: kMuted, fontSize: 12),
              ),
            ],
          ),
          if (saving)
            Positioned.fill(
              child: ColoredBox(
                color: Colors.black45,
                child: const Center(child: CircularProgressIndicator(color: kOrange)),
              ),
            ),
        ],
      ),
    );
  }
}
