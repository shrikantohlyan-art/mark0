from __future__ import annotations

from datetime import datetime
from pathlib import Path

from launcher_bootstrap import main as bootstrap_main

LOG_PATH = Path(__file__).resolve().parent / "logs" / "runtime" / "launcher.log"


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def main() -> int:
    log("Launcher starting.")
    return bootstrap_main()


if __name__ == "__main__":
    raise SystemExit(main())
