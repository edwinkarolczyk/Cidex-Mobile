class WmmPairingData {
  const WmmPairingData({required this.baseUrl, required this.key});

  final String baseUrl;
  final String key;

  static WmmPairingData parse(String raw) {
    final value = raw.trim();
    if (value.isEmpty) {
      throw ApiException('Kod QR jest pusty.');
    }

    if (value.startsWith('{')) {
      try {
        final decoded = jsonDecode(value);
        if (decoded is Map) {
          final host = (decoded['host'] ?? '').toString().trim();
          final port = (decoded['port'] ?? '8765').toString().trim();
          final key = (decoded['key'] ?? decoded['token'] ?? '').toString().trim();
          if (host.isNotEmpty) {
            return WmmPairingData(
              baseUrl: _normalizeHost(host, port),
              key: key,
            );
          }
        }
      } catch (_) {
        // Spróbuj formatu URI poniżej.
      }
    }

    final uri = Uri.tryParse(value);
    if (uri != null && uri.scheme.toLowerCase() == 'wmm') {
      final host = (uri.queryParameters['host'] ?? '').trim();
      final port = (uri.queryParameters['port'] ?? '8765').trim();
      final key = (uri.queryParameters['key'] ?? uri.queryParameters['token'] ?? '').trim();
      if (host.isEmpty) {
        throw ApiException('QR WMM nie zawiera adresu hosta.');
      }
      return WmmPairingData(baseUrl: _normalizeHost(host, port), key: key);
    }

    throw ApiException('To nie jest kod połączenia Warsztat Menager Mobile.');
  }

  static String _normalizeHost(String host, String port) {
    final cleanHost = host.trim().replaceFirst(RegExp(r'/+$'), '');
    if (cleanHost.startsWith('http://') || cleanHost.startsWith('https://')) {
      final parsed = Uri.tryParse(cleanHost);
      if (parsed != null && parsed.hasPort) return cleanHost;
      return '$cleanHost:$port';
    }
    return 'http://$cleanHost:$port';
  }
}

class WmmPairingScannerScreen extends StatefulWidget {
  const WmmPairingScannerScreen({super.key});

  @override
  State<WmmPairingScannerScreen> createState() => _WmmPairingScannerScreenState();
}

class _WmmPairingScannerScreenState extends State<WmmPairingScannerScreen> {
  final controller = MobileScannerController();
  bool handled = false;
  String error = '';

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  void onDetect(BarcodeCapture capture) {
    if (handled || capture.barcodes.isEmpty) return;
    final raw = capture.barcodes.first.rawValue;
    if (raw == null || raw.trim().isEmpty) return;
    try {
      final data = WmmPairingData.parse(raw);
      handled = true;
      Navigator.of(context).pop(
        ApiConfig(baseUrl: data.baseUrl, token: data.key),
      );
    } catch (e) {
      setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Połącz WMM z Warsztat Menager')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const RoundedCard(
            child: Text(
              'Na komputerze otwórz kod QR połączenia WMM. Zeskanowanie kodu ustawi adres serwera i klucz automatycznie — niczego nie trzeba przepisywać.',
              style: TextStyle(color: Color(0xFFC5CBD2), height: 1.45),
            ),
          ),
          const SizedBox(height: 14),
          AspectRatio(
            aspectRatio: 1,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(22),
              child: MobileScanner(controller: controller, onDetect: onDetect),
            ),
          ),
          if (error.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(error, textAlign: TextAlign.center, style: const TextStyle(color: kRed)),
          ],
        ],
      ),
    );
  }
}

extension WmmApiExtension on WmApi {
  Future<List<Map<String, dynamic>>> tools() async {
    final payload = await getJson('/api/v1/tools');
    return _items(payload);
  }

  Future<Map<String, dynamic>> tool(String id) async {
    final payload = await getJson('/api/v1/tools/${Uri.encodeComponent(id)}');
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<Map<String, dynamic>> setToolStatus(String id, String status, String note) async {
    final payload = await postJson(
      '/api/v1/tools/${Uri.encodeComponent(id)}/status',
      {'status': status, 'note': note},
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<Map<String, dynamic>> uploadToolPhoto(String id, XFile file) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        _uri('/api/v1/tools/${Uri.encodeComponent(id)}/photos'),
      );
      request.headers.addAll(headers);
      request.files.add(await http.MultipartFile.fromPath('photo', file.path));
      final streamed = await request.send().timeout(const Duration(seconds: 25));
      final response = await http.Response.fromStream(streamed);
      final payload = await _decode(response);
      return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('Nie udało się wysłać zdjęcia narzędzia: $error');
    }
  }

  Future<List<Map<String, dynamic>>> dispositions() async {
    final payload = await getJson('/api/v1/dispositions');
    return _items(payload);
  }

  Future<Map<String, dynamic>> setDispositionStatus(String id, String status) async {
    final payload = await postJson(
      '/api/v1/dispositions/${Uri.encodeComponent(id)}/status',
      {'status': status},
    );
    return Map<String, dynamic>.from(payload['item'] as Map? ?? const {});
  }

  Future<List<Map<String, dynamic>>> warehouse() async {
    final payload = await getJson('/api/v1/warehouse');
    return _items(payload);
  }
}

class ToolsScreen extends StatefulWidget {
  const ToolsScreen({super.key, required this.api});
  final WmApi api;

  @override
  State<ToolsScreen> createState() => _ToolsScreenState();
}

class _ToolsScreenState extends State<ToolsScreen> {
  final search = TextEditingController();
  List<Map<String, dynamic>> items = [];
  bool busy = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    search.addListener(() => setState(() {}));
    load();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final rows = await widget.api.tools();
      if (!mounted) return;
      setState(() => items = rows);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  List<Map<String, dynamic>> get visible {
    final q = search.text.trim().toLowerCase();
    if (q.isEmpty) return items;
    return items.where((item) {
      return ['id', 'nr', 'numer', 'nazwa', 'typ', 'status', 'lokalizacja']
          .map((key) => (item[key] ?? '').toString().toLowerCase())
          .any((value) => value.contains(q));
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final rows = visible;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Narzędzia'),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 6),
            child: TextField(
              controller: search,
              decoration: const InputDecoration(
                hintText: 'Szukaj numeru, nazwy, statusu...',
                prefixIcon: Icon(Icons.search_rounded),
              ),
            ),
          ),
          Expanded(
            child: busy
                ? const Center(child: CircularProgressIndicator(color: kOrange))
                : error.isNotEmpty
                    ? ErrorState(message: error, onRetry: load)
                    : RefreshIndicator(
                        onRefresh: load,
                        color: kOrange,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(16),
                          itemCount: rows.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            final item = rows[index];
                            final id = (item['id'] ?? item['nr'] ?? item['numer'] ?? '').toString();
                            return Material(
                              color: kPanel,
                              borderRadius: BorderRadius.circular(20),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(20),
                                onTap: id.isEmpty
                                    ? null
                                    : () async {
                                        await Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => ToolScreen(api: widget.api, toolId: id),
                                          ),
                                        );
                                        load();
                                      },
                                child: Padding(
                                  padding: const EdgeInsets.all(15),
                                  child: Row(
                                    children: [
                                      const Icon(Icons.handyman_rounded, color: kOrange, size: 32),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              '${id.isEmpty ? '—' : id} — ${item['nazwa'] ?? item['name'] ?? ''}',
                                              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              '${item['status_label'] ?? item['status'] ?? '—'} • ${item['lokalizacja'] ?? '—'}',
                                              style: const TextStyle(color: kMuted),
                                            ),
                                          ],
                                        ),
                                      ),
                                      const Icon(Icons.chevron_right_rounded, color: kMuted),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}

class ToolScreen extends StatefulWidget {
  const ToolScreen({super.key, required this.api, required this.toolId});
  final WmApi api;
  final String toolId;

  @override
  State<ToolScreen> createState() => _ToolScreenState();
}

class _ToolScreenState extends State<ToolScreen> {
  final picker = ImagePicker();
  Map<String, dynamic> tool = {};
  bool busy = true;
  bool actionBusy = false;
  String error = '';

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final row = await widget.api.tool(widget.toolId);
      if (!mounted) return;
      setState(() => tool = row);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<String?> askNote(String title) async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(hintText: 'Krótka uwaga...'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Anuluj')),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, controller.text.trim()),
            child: const Text('Zapisz'),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  Future<void> setStatus(String status) async {
    final note = await askNote(status);
    if (note == null) return;
    await runAction(
      () => widget.api.setToolStatus(widget.toolId, status, note),
      'Status narzędzia zapisany w WM.',
    );
  }

  Future<void> choosePhoto() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera_rounded, color: kOrange),
              title: const Text('Zrób zdjęcie aparatem'),
              onTap: () => Navigator.pop(sheetContext, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_rounded),
              title: const Text('Wybierz z galerii'),
              onTap: () => Navigator.pop(sheetContext, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (source == null) return;
    final file = await picker.pickImage(source: source, imageQuality: 85, maxWidth: 1920);
    if (file == null) return;
    await runAction(
      () => widget.api.uploadToolPhoto(widget.toolId, file),
      'Zdjęcie zapisane przy narzędziu.',
    );
  }

  Future<void> runAction(Future<Map<String, dynamic>> Function() operation, String message) async {
    if (actionBusy) return;
    setState(() => actionBusy = true);
    try {
      final row = await operation();
      if (!mounted) return;
      setState(() => tool = row);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), behavior: SnackBarBehavior.floating),
        );
      }
    } finally {
      if (mounted) setState(() => actionBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (busy) {
      return Scaffold(
        appBar: AppBar(title: Text('Narzędzie ${widget.toolId}')),
        body: const Center(child: CircularProgressIndicator(color: kOrange)),
      );
    }
    if (error.isNotEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text('Narzędzie ${widget.toolId}')),
        body: ErrorState(message: error, onRetry: load),
      );
    }

    final photos = (tool['photos'] as List? ?? const [])
        .whereType<Map>()
        .map(Map<String, dynamic>.from)
        .toList();

    return Scaffold(
      appBar: AppBar(title: Text('Narzędzie ${tool['id'] ?? widget.toolId}')),
      body: Stack(
        children: [
          RefreshIndicator(
            onRefresh: load,
            color: kOrange,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                RoundedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${tool['nazwa'] ?? tool['name'] ?? 'Narzędzie'}',
                        style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 12),
                      InfoRow(icon: Icons.tag_rounded, label: 'Numer', value: '${tool['nr'] ?? tool['numer'] ?? tool['id'] ?? '—'}'),
                      InfoRow(icon: Icons.info_outline_rounded, label: 'Status', value: '${tool['status_label'] ?? tool['status'] ?? '—'}'),
                      InfoRow(icon: Icons.location_on_rounded, label: 'Lokalizacja', value: '${tool['lokalizacja'] ?? '—'}'),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 1.45,
                  children: [
                    MachineActionButton(color: kOrange, icon: Icons.add_a_photo_rounded, text: 'Dodaj zdjęcie', onTap: choosePhoto),
                    MachineActionButton(color: kRed, icon: Icons.build_rounded, text: 'Do naprawy', onTap: () => setStatus('do naprawy')),
                    MachineActionButton(color: kOrange, icon: Icons.content_cut_rounded, text: 'Do ostrzenia', onTap: () => setStatus('do ostrzenia')),
                    MachineActionButton(color: kGreen, icon: Icons.check_circle_rounded, text: 'Dostępne', onTap: () => setStatus('dostępne')),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    const Expanded(child: Text('Zdjęcia', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900))),
                    Text('${photos.length}', style: const TextStyle(color: kMuted)),
                  ],
                ),
                const SizedBox(height: 10),
                if (photos.isEmpty)
                  const RoundedCard(child: Text('Brak zdjęć przy narzędziu.', style: TextStyle(color: kMuted)))
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 10,
                      crossAxisSpacing: 10,
                      childAspectRatio: 1.15,
                    ),
                    itemCount: photos.length,
                    itemBuilder: (context, index) {
                      final photo = photos[index];
                      final url = widget.api.photoUrl((photo['url'] ?? '').toString());
                      return ClipRRect(
                        borderRadius: BorderRadius.circular(18),
                        child: Image.network(
                          url,
                          headers: widget.api.headers,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => const ColoredBox(
                            color: kPanel2,
                            child: Center(child: Icon(Icons.broken_image_rounded, color: kMuted)),
                          ),
                        ),
                      );
                    },
                  ),
              ],
            ),
          ),
          if (actionBusy)
            const Positioned.fill(
              child: ColoredBox(
                color: Colors.black45,
                child: Center(child: CircularProgressIndicator(color: kOrange)),
              ),
            ),
        ],
      ),
    );
  }
}

class WmmSimpleListScreen extends StatefulWidget {
  const WmmSimpleListScreen({
    super.key,
    required this.title,
    required this.icon,
    required this.loader,
    required this.primaryKeys,
    required this.secondaryKeys,
  });

  final String title;
  final IconData icon;
  final Future<List<Map<String, dynamic>>> Function() loader;
  final List<String> primaryKeys;
  final List<String> secondaryKeys;

  @override
  State<WmmSimpleListScreen> createState() => _WmmSimpleListScreenState();
}

class _WmmSimpleListScreenState extends State<WmmSimpleListScreen> {
  List<Map<String, dynamic>> items = [];
  bool busy = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = '';
    });
    try {
      final rows = await widget.loader();
      if (!mounted) return;
      setState(() => items = rows);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String firstValue(Map<String, dynamic> item, List<String> keys) {
    for (final key in keys) {
      final value = (item[key] ?? '').toString().trim();
      if (value.isNotEmpty) return value;
    }
    return '—';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        actions: [IconButton(onPressed: load, icon: const Icon(Icons.refresh_rounded))],
      ),
      body: busy
          ? const Center(child: CircularProgressIndicator(color: kOrange))
          : error.isNotEmpty
              ? ErrorState(message: error, onRetry: load)
              : RefreshIndicator(
                  onRefresh: load,
                  color: kOrange,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final item = items[index];
                      return RoundedCard(
                        child: Row(
                          children: [
                            Icon(widget.icon, color: kOrange, size: 30),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(firstValue(item, widget.primaryKeys), style: const TextStyle(fontWeight: FontWeight.w900)),
                                  const SizedBox(height: 4),
                                  Text(firstValue(item, widget.secondaryKeys), style: const TextStyle(color: kMuted)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
