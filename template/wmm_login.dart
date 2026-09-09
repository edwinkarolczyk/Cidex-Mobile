class WmmLoginGate extends StatefulWidget {
  const WmmLoginGate({super.key, required this.initialConfig});

  final ApiConfig initialConfig;

  @override
  State<WmmLoginGate> createState() => _WmmLoginGateState();
}

class _WmmLoginGateState extends State<WmmLoginGate> {
  late ApiConfig config;
  final login = TextEditingController();
  final pin = TextEditingController();
  bool busy = false;
  bool obscurePin = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    config = widget.initialConfig;
    _loadLastLogin();
  }

  Future<void> _loadLastLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final value = (prefs.getString('wmm_last_login') ?? '').trim();
    if (!mounted || value.isEmpty) return;
    login.text = value;
  }

  @override
  void dispose() {
    login.dispose();
    pin.dispose();
    super.dispose();
  }

  Future<void> openConnectionSettings() async {
    final updated = await Navigator.of(context).push<ApiConfig>(
      MaterialPageRoute(builder: (_) => SettingsScreen(config: config)),
    );
    if (updated == null || !mounted) return;
    setState(() {
      config = updated;
      error = '';
    });
  }

  Future<void> submit() async {
    if (busy) return;
    final userLogin = login.text.trim();
    final userPin = pin.text.trim();
    if (userLogin.isEmpty || userPin.isEmpty) {
      setState(() => error = 'Wpisz login i PIN z Warsztat Menager.');
      return;
    }

    setState(() {
      busy = true;
      error = '';
    });

    try {
      final base = config.baseUrl.trim().replaceFirst(RegExp(r'/+$'), '');
      final response = await http
          .post(
            Uri.parse('$base/api/v1/auth/login'),
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json; charset=utf-8',
              if (config.token.trim().isNotEmpty) 'X-WMM-Key': config.token.trim(),
            },
            body: jsonEncode({'login': userLogin, 'pin': userPin}),
          )
          .timeout(const Duration(seconds: 10));

      Map<String, dynamic> payload = {};
      try {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is Map<String, dynamic>) payload = decoded;
      } catch (_) {}

      if (response.statusCode < 200 || response.statusCode >= 300 || payload['ok'] != true) {
        throw ApiException(
          payload['error']?.toString() ?? 'Logowanie nie powiodło się.',
        );
      }

      final user = Map<String, dynamic>.from(payload['user'] as Map? ?? const {});
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('wmm_last_login', userLogin);

      // PIN nie jest zapisywany na telefonie.
      pin.clear();
      if (!mounted) return;

      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => HomeScreen(initialConfig: config),
          settings: RouteSettings(
            arguments: {
              'wmm_user': user,
            },
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(22),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Center(
                    child: Container(
                      width: 82,
                      height: 82,
                      decoration: BoxDecoration(
                        color: kPanel2,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: kOrange, width: 1.4),
                      ),
                      child: const Stack(
                        alignment: Alignment.center,
                        children: [
                          Icon(Icons.settings_rounded, color: Color(0xFF9A9A9A), size: 58),
                          Positioned(left: 13, bottom: 12, child: Icon(Icons.build_rounded, color: kOrange, size: 38)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'WMM',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 34, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Warsztat Menager Mobile',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: kMuted, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 28),
                  RoundedCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          'Zaloguj się do Warsztat Menager',
                          style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Użyj tego samego loginu i PIN-u co w WM na komputerze.',
                          style: TextStyle(color: kMuted, height: 1.35),
                        ),
                        const SizedBox(height: 18),
                        TextField(
                          controller: login,
                          textInputAction: TextInputAction.next,
                          autofillHints: const [AutofillHints.username],
                          decoration: const InputDecoration(
                            labelText: 'Login',
                            prefixIcon: Icon(Icons.person_rounded),
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: pin,
                          obscureText: obscurePin,
                          keyboardType: TextInputType.number,
                          textInputAction: TextInputAction.done,
                          onSubmitted: (_) => submit(),
                          decoration: InputDecoration(
                            labelText: 'PIN',
                            prefixIcon: const Icon(Icons.lock_rounded),
                            suffixIcon: IconButton(
                              onPressed: () => setState(() => obscurePin = !obscurePin),
                              icon: Icon(obscurePin ? Icons.visibility_rounded : Icons.visibility_off_rounded),
                            ),
                          ),
                        ),
                        if (error.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          Text(error, style: const TextStyle(color: kRed, fontWeight: FontWeight.w700)),
                        ],
                        const SizedBox(height: 18),
                        SizedBox(
                          height: 56,
                          child: FilledButton.icon(
                            style: FilledButton.styleFrom(backgroundColor: kOrange),
                            onPressed: busy ? null : submit,
                            icon: busy
                                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                                : const Icon(Icons.login_rounded),
                            label: const Text('ZALOGUJ', style: TextStyle(fontWeight: FontWeight.w900)),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextButton.icon(
                    onPressed: busy ? null : openConnectionSettings,
                    icon: const Icon(Icons.qr_code_scanner_rounded, color: kOrange),
                    label: const Text('POŁĄCZENIE / SKAN QR'),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'PIN służy tylko do zalogowania i nie jest zapisywany w telefonie.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: kMuted, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
