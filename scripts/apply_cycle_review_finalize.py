from pathlib import Path


def main() -> None:
    path = Path("lib/main.dart")
    source = path.read_text(encoding="utf-8")

    source = source.replace(
        "onPressed: isFailure || actionBusy ? null : _openCycleReviews,",
        "onPressed: wmmMachineStatusCode(widget.machine['status']) == 'warn' || actionBusy ? null : _openCycleReviews,",
        1,
    )
    source = source.replace(
        "if (isFailure)\n            const Padding(",
        "if (wmmMachineStatusCode(widget.machine['status']) == 'warn')\n            const Padding(",
        1,
    )

    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
