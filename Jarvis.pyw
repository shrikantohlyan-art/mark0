from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_LAUNCHER = _ROOT / "launcher_bootstrap.py"


def _resolve_repo_python() -> Path | None:
    candidates = [
        _ROOT / ".venv" / "Scripts" / "python.exe",
        _ROOT / ".venv" / "bin" / "python",
        _ROOT / ".env" / "Scripts" / "python.exe",
        _ROOT / ".env" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    if sys.executable:
        return Path(sys.executable)
    return None


def _show_launch_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, message, "Jarvis Launch Error", 0x10)
    except Exception:
        pass


def _launch() -> int:
    python_executable = _resolve_repo_python()
    if not python_executable or not python_executable.exists():
        _show_launch_error(
            "Jarvis could not find its project Python interpreter.\n"
            "Expected .venv\\Scripts\\python.exe next to Jarvis.pyw."
        )
        return 1

    current_python = Path(sys.executable).resolve() if sys.executable else None
    target_python = python_executable.resolve()

    if current_python == target_python:
        if str(_ROOT) not in sys.path:
            sys.path.insert(0, str(_ROOT))
        from launcher_bootstrap import main as bootstrap_main

        return int(bootstrap_main())

    try:
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if sys.platform == "win32" else 0
        subprocess.Popen(
            [str(target_python), str(_LAUNCHER)],
            cwd=str(_ROOT),
            creationflags=creationflags,
        )
        return 0
    except Exception as exc:
        _show_launch_error(f"Jarvis failed to launch.\n\n{exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(_launch())
