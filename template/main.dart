import 'package:flutter/material.dart';

void main() {
  runApp(const CidexMobileApp());
}

class CidexMobileApp extends StatelessWidget {
  const CidexMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    const orange = Color(0xFFFF7A00);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'CIDEX Mobile',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D0F12),
        colorScheme: ColorScheme.fromSeed(
          seedColor: orange,
          brightness: Brightness.dark,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF111419),
          foregroundColor: Colors.white,
          centerTitle: false,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String lastSync = 'Tryb DEMO — WM nie jest podłączony';

  void open(Widget page) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
  }

  void demoMessage(String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 18, 16, 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const BrandHeader(),
              const SizedBox(height: 18),
              _ConnectionCard(text: lastSync),
              const SizedBox(height: 18),
              const Text(
                'Szybkie działania',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 12),
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.15,
                children: [
                  ActionTile(
                    color: const Color(0xFFFF7A00),
                    icon: Icons.calendar_month_rounded,
                    title: 'Planista',
                    subtitle: 'Zlecenia i terminy',
                    onTap: () => open(const PlannerScreen()),
                  ),
                  ActionTile(
                    color: const Color(0xFF16A05D),
                    icon: Icons.qr_code_scanner_rounded,
                    title: 'Skanuj QR',
                    subtitle: 'Szybki dostęp do maszyny',
                    onTap: () => open(const QrDemoScreen()),
                  ),
                  ActionTile(
                    color: const Color(0xFF1677D2),
                    icon: Icons.precision_manufacturing_rounded,
                    title: 'Maszyny',
                    subtitle: 'Lista i wyszukiwarka',
                    onTap: () => open(const MachinesScreen()),
                  ),
                  ActionTile(
                    color: const Color(0xFF7A48C8),
                    icon: Icons.add_a_photo_rounded,
                    title: 'Dodaj zdjęcie',
                    subtitle: 'Dokumentuj i raportuj',
                    onTap: () => demoMessage('Demo: aparat zostanie podłączony w kolejnym etapie.'),
                  ),
                  ActionTile(
                    color: const Color(0xFFD43B32),
                    icon: Icons.warning_amber_rounded,
                    title: 'Zgłoś awarię',
                    subtitle: 'Szybkie zgłoszenie',
                    onTap: () => open(const MachineScreen()),
                  ),
                  ActionTile(
                    color: const Color(0xFF4A515A),
                    icon: Icons.refresh_rounded,
                    title: 'Odśwież',
                    subtitle: 'Synchronizuj z WM',
                    onTap: () {
                      setState(() {
                        lastSync = 'Odświeżono demo — brak aktywnego API CIDEX';
                      });
                    },
                  ),
                ],
              ),
              const SizedBox(height: 18),
              const CurrentValuesCard(),
            ],
          ),
        ),
      ),
    );
  }
}

class BrandHeader extends StatelessWidget {
  const BrandHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 54,
          height: 54,
          decoration: BoxDecoration(
            color: const Color(0xFF20242A),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFFF7A00), width: 1.2),
          ),
          child: const Icon(Icons.build_circle_rounded, color: Color(0xFFFF7A00), size: 34),
        ),
        const SizedBox(width: 12),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(text: 'CID', style: TextStyle(color: Colors.white)),
                    TextSpan(text: 'EX', style: TextStyle(color: Color(0xFFFF7A00))),
                    TextSpan(text: ' Mobile', style: TextStyle(color: Color(0xFFD3D7DC))),
                  ],
                ),
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900),
              ),
              SizedBox(height: 2),
              Text('Warsztat pod kontrolą', style: TextStyle(color: Color(0xFF949AA3))),
            ],
          ),
        ),
        const Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text('Cidex', style: TextStyle(fontWeight: FontWeight.w700)),
            Text('Warsztat WM', style: TextStyle(fontSize: 12, color: Color(0xFF9298A1))),
          ],
        ),
      ],
    );
  }
}

class _ConnectionCard extends StatelessWidget {
  const _ConnectionCard({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF171A1F),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2C323A)),
      ),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: const BoxDecoration(color: Color(0xFFFFB020), shape: BoxShape.circle),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('CIDEX API', style: TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(text, style: const TextStyle(color: Color(0xFFA1A7B0), fontSize: 12)),
              ],
            ),
          ),
          const Icon(Icons.wifi_tethering_rounded, color: Color(0xFFFFB020)),
        ],
      ),
    );
  }
}

class ActionTile extends StatelessWidget {
  const ActionTile({
    super.key,
    required this.color,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final Color color;
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, size: 34, color: Colors.white),
              const Spacer(),
              Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.white70)),
            ],
          ),
        ),
      ),
    );
  }
}

class CurrentValuesCard extends StatelessWidget {
  const CurrentValuesCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF171A1F),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF2C323A)),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Podgląd aktualnych wartości', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          SizedBox(height: 12),
          _ValueRow(label: 'Aktywne zlecenia', value: '128', valueColor: Color(0xFFFF7A00)),
          _ValueRow(label: 'Maszyny wymagające uwagi', value: '3', valueColor: Color(0xFFD43B32)),
          _ValueRow(label: 'Autor zapisów mobilnych', value: 'Cidex', valueColor: Color(0xFF58B5FF)),
          SizedBox(height: 8),
          Text(
            'Dane są demonstracyjne. Prawdziwe wartości pojawią się po podłączeniu CIDEX API.',
            style: TextStyle(fontSize: 12, color: Color(0xFF8F959E)),
          ),
        ],
      ),
    );
  }
}

class _ValueRow extends StatelessWidget {
  const _ValueRow({required this.label, required this.value, required this.valueColor});
  final String label;
  final String value;
  final Color valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(child: Text(label, style: const TextStyle(color: Color(0xFFB9BEC6)))),
          Text(value, style: TextStyle(fontWeight: FontWeight.w900, color: valueColor)),
        ],
      ),
    );
  }
}

class PlannerScreen extends StatelessWidget {
  const PlannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final orders = [
      ('ZP/2026/041', 'Hak prosty', '100 szt.', '12.09.2026', const Color(0xFF16A05D)),
      ('ZP/2026/042', 'Rama', '80 szt.', '13.09.2026', const Color(0xFFFFB020)),
      ('ZP/2026/043', 'Szafka', '24 szt.', '15.09.2026', const Color(0xFF1677D2)),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Planista')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: orders.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final o = orders[index];
          return Container(
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(
              color: const Color(0xFF171A1F),
              borderRadius: BorderRadius.circular(16),
              border: Border(left: BorderSide(color: o.$5, width: 5)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(o.$1, style: const TextStyle(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text(o.$2, style: const TextStyle(fontSize: 17)),
                      const SizedBox(height: 6),
                      Text('${o.$3} • wysyłka ${o.$4}', style: const TextStyle(color: Color(0xFF989EA7))),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded),
              ],
            ),
          );
        },
      ),
    );
  }
}

class QrDemoScreen extends StatelessWidget {
  const QrDemoScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Skanuj QR')),
      body: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: const Color(0xFF171A1F),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0xFFFF7A00), width: 2),
                ),
                child: const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.qr_code_2_rounded, size: 170, color: Colors.white),
                    SizedBox(height: 22),
                    Text('M42', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900)),
                    SizedBox(height: 12),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 24),
                      child: Text(
                        'W wersji na telefon aparat odczyta prawdziwy QR. W emulatorze użyj przycisku DEMO.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Color(0xFFA5ABB4)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 58,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(backgroundColor: const Color(0xFFFF7A00)),
                onPressed: () {
                  Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MachineScreen()));
                },
                icon: const Icon(Icons.qr_code_scanner_rounded),
                label: const Text('SYMULUJ SKAN M42', style: TextStyle(fontWeight: FontWeight.w900)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class MachinesScreen extends StatelessWidget {
  const MachinesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Maszyny')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          MachineListTile(
            id: 'M42',
            name: 'BLELL',
            location: 'Hala A • Stanowisko 3',
            status: 'Awaria',
            statusColor: const Color(0xFFD43B32),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MachineScreen())),
          ),
          const SizedBox(height: 10),
          const MachineListTile(
            id: 'M27',
            name: 'CJ6250YC',
            location: 'Hala B • Tokarki',
            status: 'Sprawna',
            statusColor: Color(0xFF16A05D),
          ),
        ],
      ),
    );
  }
}

class MachineListTile extends StatelessWidget {
  const MachineListTile({
    super.key,
    required this.id,
    required this.name,
    required this.location,
    required this.status,
    required this.statusColor,
    this.onTap,
  });

  final String id;
  final String name;
  final String location;
  final String status;
  final Color statusColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFF171A1F),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(color: statusColor.withOpacity(0.16), borderRadius: BorderRadius.circular(14)),
                child: Icon(Icons.precision_manufacturing_rounded, color: statusColor),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('$id — $name', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),
                    const SizedBox(height: 4),
                    Text(location, style: const TextStyle(color: Color(0xFF969CA5))),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(color: statusColor, borderRadius: BorderRadius.circular(99)),
                child: Text(status, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MachineScreen extends StatelessWidget {
  const MachineScreen({super.key});

  void message(BuildContext context, String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }

  void showPhotoDemo(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: const Color(0xFF171A1F),
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Dodaj zdjęcie', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
              const SizedBox(height: 14),
              ListTile(
                leading: const Icon(Icons.photo_camera_rounded, color: Color(0xFF16A05D)),
                title: const Text('Zrób zdjęcie'),
                subtitle: const Text('Demo — aparat będzie podpięty później'),
                onTap: () => Navigator.pop(context),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_rounded, color: Color(0xFF7A48C8)),
                title: const Text('Wybierz z galerii'),
                subtitle: const Text('Demo — galeria będzie podpięta później'),
                onTap: () => Navigator.pop(context),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Maszyna 42 — BLELL')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 74,
                  height: 74,
                  decoration: BoxDecoration(
                    color: const Color(0xFF20242A),
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: const Icon(Icons.precision_manufacturing_rounded, size: 43, color: Color(0xFFFF7A00)),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Frezarka CNC', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
                      SizedBox(height: 5),
                      Text('Hala A • Stanowisko 3', style: TextStyle(color: Color(0xFF9AA0A9))),
                      SizedBox(height: 5),
                      Text('Nr ewidencyjny: M42', style: TextStyle(color: Color(0xFF9AA0A9))),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(color: const Color(0xFFD43B32), borderRadius: BorderRadius.circular(99)),
                  child: const Text('AWARIA', style: TextStyle(fontWeight: FontWeight.w900)),
                ),
              ],
            ),
            const SizedBox(height: 18),
            const Text('Dane z WM (aktualne)', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            const Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                InfoCard(label: 'Status', value: 'Awaria', color: Color(0xFFD43B32), icon: Icons.warning_rounded),
                InfoCard(label: 'Przebieg', value: '1 248 h', color: Color(0xFF58B5FF), icon: Icons.timer_outlined),
                InfoCard(label: 'Ostatni serwis', value: '12.01.2026', color: Color(0xFF16A05D), icon: Icons.build_rounded),
                InfoCard(label: 'Następny przegląd', value: '20.09.2026', color: Color(0xFFFFB020), icon: Icons.event_rounded),
              ],
            ),
            const SizedBox(height: 18),
            const Text('Działania', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: BigActionButton(
                    color: const Color(0xFF16A05D),
                    icon: Icons.add_a_photo_rounded,
                    text: 'Dodaj zdjęcie',
                    onTap: () => showPhotoDemo(context),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: BigActionButton(
                    color: const Color(0xFFD43B32),
                    icon: Icons.warning_amber_rounded,
                    text: 'Zgłoś awarię',
                    onTap: () => message(context, 'Demo: zgłoszenie awarii nie jest jeszcze zapisywane.'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: BigActionButton(
                    color: const Color(0xFF1677D2),
                    icon: Icons.note_add_rounded,
                    text: 'Dodaj uwagę',
                    onTap: () => message(context, 'Demo: uwaga nie jest jeszcze zapisywana.'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: BigActionButton(
                    color: const Color(0xFFFF7A00),
                    icon: Icons.handyman_rounded,
                    text: 'Serwis / przegląd',
                    onTap: () => message(context, 'Demo: moduł serwisu będzie podpięty po akceptacji UI.'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            const Text('Ostatnie zdjęcia', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            const SizedBox(height: 10),
            SizedBox(
              height: 96,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: 4,
                separatorBuilder: (_, __) => const SizedBox(width: 10),
                itemBuilder: (context, index) {
                  if (index == 3) {
                    return InkWell(
                      onTap: () => showPhotoDemo(context),
                      child: Container(
                        width: 96,
                        decoration: BoxDecoration(
                          color: const Color(0xFF20242A),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFF3A4048)),
                        ),
                        child: const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.add_a_photo_rounded, color: Color(0xFFFF7A00)),
                            SizedBox(height: 5),
                            Text('Dodaj', style: TextStyle(fontSize: 12)),
                          ],
                        ),
                      ),
                    );
                  }
                  return Container(
                    width: 96,
                    decoration: BoxDecoration(
                      color: const Color(0xFF252A31),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Icon(
                      index == 0 ? Icons.settings_rounded : index == 1 ? Icons.cable_rounded : Icons.emergency_rounded,
                      size: 40,
                      color: index == 2 ? const Color(0xFFD43B32) : const Color(0xFF8E959E),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: const Color(0xFF171A1F), borderRadius: BorderRadius.circular(14)),
              child: const Row(
                children: [
                  Icon(Icons.info_outline_rounded, color: Color(0xFF58B5FF)),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Zmiany z aplikacji mobilnej będą oznaczane w WM autorem: Cidex.',
                      style: TextStyle(color: Color(0xFFB7BCC4)),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class InfoCard extends StatelessWidget {
  const InfoCard({
    super.key,
    required this.label,
    required this.value,
    required this.color,
    required this.icon,
  });

  final String label;
  final String value;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final width = (MediaQuery.of(context).size.width - 42) / 2;
    return Container(
      width: width,
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(color: const Color(0xFF171A1F), borderRadius: BorderRadius.circular(15)),
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontSize: 11, color: Color(0xFF969CA5))),
                const SizedBox(height: 2),
                Text(value, style: TextStyle(fontWeight: FontWeight.w900, color: color)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class BigActionButton extends StatelessWidget {
  const BigActionButton({
    super.key,
    required this.color,
    required this.icon,
    required this.text,
    required this.onTap,
  });

  final Color color;
  final IconData icon;
  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 16),
          child: Column(
            children: [
              Icon(icon, color: Colors.white, size: 28),
              const SizedBox(height: 7),
              Text(text, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w900)),
            ],
          ),
        ),
      ),
    );
  }
}
