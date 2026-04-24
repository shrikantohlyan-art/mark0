from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path

import launcher_bootstrap as bootstrap

LOG_PATH = bootstrap.RUNTIME_LOG_DIR / "guardian.log"


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
    print(line)


def backend_healthy(timeout_seconds: float = 2.0) -> bool:
    request = urllib.request.Request(
        bootstrap.BACKEND_HEALTH_URL,
        headers={"User-Agent": "JarvisGuardian/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return 200 <= getattr(response, "status", 200) < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        return False


def ensure_backend_running() -> bool:
    if backend_healthy():
        return False

    log("Backend health probe failed. Attempting recovery.")
    bootstrap.reclaim_port(bootstrap.BACKEND_PORT, "backend")

    if backend_healthy():
        log("Backend recovered before restart completed.")
        return False

    process = bootstrap.start_backend()
    # Use timeout_seconds for compatibility with tests expecting this keyword
    bootstrap._wait_for_http_ready(
        bootstrap.BACKEND_HEALTH_URL,
        timeout_seconds=30,
        process=process,
    )
    log("Backend restarted successfully.")
    return True


def run_guardian_loop(interval_seconds: float = 30.0) -> None:
    log("Guardian watchdog active.")
    while True:
        try:
            ensure_backend_running()
        except Exception as exc:
            log(f"Recovery attempt failed: {exc}")
        time.sleep(interval_seconds)


def main() -> int:
    run_guardian_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
