from __future__ import annotations

from pathlib import Path
import re


APP_VERSION = "0.5.12"

BANNER_WIDGET = r'''
class WmmHomeVersionBanner extends StatefulWidget {
  const WmmHomeVersionBanner({
    super.key,
    required this.onOpenUpdates,
  });

  final VoidCallback onOpenUpdates;

  @override
  State<WmmHomeVersionBanner> createState() => _WmmHomeVersionBannerState();
}

class _WmmHomeVersionBannerState extends State<WmmHomeVersionBanner>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;
  WmmReleaseInfo? latestInfo;
  bool checking = true;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 850),
      value: 1,
    );
    _check();
  }

  Future<void> _check() async {
    try {
      final info = await WmmUpdater.latest();
      if (!mounted) return;
      final newer = info != null && WmmUpdater.isNewer(info);
      setState(() {
        latestInfo = info;
        checking = false;
      });
      if (newer) {
        _pulse.repeat(reverse: true);
      } else {
        _pulse.stop();
        _pulse.value = 1;
      }
    } catch (_) {
      if (!mounted) return;
      setState(() => checking = false);
      _pulse.stop();
      _pulse.value = 1;
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final info = latestInfo;
    final newer = info != null && WmmUpdater.isNewer(info);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: widget.onOpenUpdates,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 4),
          child: AnimatedBuilder(
            animation: _pulse,
            builder: (context, child) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (newer) ...[
                    Opacity(
                      opacity: 0.45 + (_pulse.value * 0.55),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.system_update_alt_rounded,
                            color: kRed,
                            size: 18,
                          ),
                          const SizedBox(width: 7),
                          Expanded(
                            child: Text(
                              'NOWA WERSJA: WMM ${info.version} BETA',
                              style: const TextStyle(
                                color: kRed,
                                fontSize: 14,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 3),
                  ],
                  Row(
                    children: [
                      const Icon(
                        Icons.check_circle_rounded,
                        color: kGreen,
                        size: 15,
                      ),
                      const SizedBox(width: 7),
                      Expanded(
                        child: Text(
                          'Aktualna wersja: WMM $kWmmCurrentVersion BETA',
                          style: const TextStyle(
                            color: kGreen,
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      if (checking)
                        const SizedBox(
                          width: 13,
                          height: 13,
                          child: CircularProgressIndicator(
                            strokeWidth: 1.6,
                            color: kMuted,
                          ),
                        ),
                    ],
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
'''


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    # Kafelek Aktualizacje znika z siatki. Informacja o wersji trafia pod nagłówek.
    update_tile_pattern = re.compile(
        r"                  ActionTile\(\n"
        r"                    color: kBlue,\n"
        r"                    icon: Icons\.system_update_alt_rounded,\n"
        r"                    title: 'Aktualizacje',\n"
        r"                    subtitle: 'WMM \d+\.\d+\.\d+ BETA',\n"
        r"                    onTap: \(\) => open\(const WmmUpdateScreen\(\)\),\n"
        r"                  \),\n"
    )
    source, removed = update_tile_pattern.subn("", source, count=1)
    if removed != 1:
        raise RuntimeError("Nie znaleziono kafelka Aktualizacje do przeniesienia")

    header_anchor = (
        "              BrandHeader(onSettings: openSettings),\n"
        "              const SizedBox(height: 18),\n"
    )
    header_replacement = (
        "              BrandHeader(onSettings: openSettings),\n"
        "              const SizedBox(height: 6),\n"
        "              WmmHomeVersionBanner(\n"
        "                onOpenUpdates: () => open(const WmmUpdateScreen()),\n"
        "              ),\n"
        "              const SizedBox(height: 14),\n"
    )
    if header_anchor not in source:
        raise RuntimeError("Nie znaleziono miejsca pod nagłówkiem WMM")
    source = source.replace(header_anchor, header_replacement, 1)

    widget_anchor = "class ConnectionCard extends StatelessWidget {\n"
    if widget_anchor not in source:
        raise RuntimeError("Nie znaleziono miejsca dla wskaźnika wersji")
    source = source.replace(widget_anchor, BANNER_WIDGET.strip() + "\n\n" + widget_anchor, 1)

    # Jedno źródło wersji dla nagłówka i aktualizatora.
    source = re.sub(
        r"const String kWmmCurrentVersion = '[^']+';",
        f"const String kWmmCurrentVersion = '{APP_VERSION}';",
        source,
        count=1,
    )
    source = re.sub(
        r"Warsztat Menager Mobile \d+\.\d+\.\d+ BETA",
        f"Warsztat Menager Mobile {APP_VERSION} BETA",
        source,
    )

    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
