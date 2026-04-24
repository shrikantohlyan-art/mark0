from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
# Resolve Python executable from virtual environment
def _resolve_venv_python() -> Path | None:
    """Resolve Python from venv, attempting both .venv and legacy .env"""
    candidates = [
        APP_DIR / ".venv" / "Scripts" / "python.exe",
        APP_DIR / ".venv" / "bin" / "python",
        APP_DIR / ".env" / "Scripts" / "python.exe",
        APP_DIR / ".env" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

# Keep both Path and string forms for compatibility with tests and runtime
CORE_DIR_PATH = APP_DIR / "Core"
CORE_DIR = str(CORE_DIR_PATH)
FRONTEND_DIR_PATH = CORE_DIR_PATH / "static"
FRONTEND_DIR = str(FRONTEND_DIR_PATH)
# Provide both Path and string forms for compatibility
BACKEND_ENTRY_PATH = CORE_DIR_PATH / "main.py"
BACKEND_ENTRY = str(BACKEND_ENTRY_PATH)
FRONTEND_PACKAGE = FRONTEND_DIR_PATH / "index.html"

BACKEND_PORT = 8001
FRONTEND_PORT = BACKEND_PORT
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
BACKEND_HEALTH_URL = f"{BACKEND_URL}/health"
FRONTEND_URL = BACKEND_URL

RUNTIME_LOG_DIR = APP_DIR / "logs" / "runtime"
LOG_PATH = RUNTIME_LOG_DIR / "launcher_bootstrap.log"
BACKEND_CONSOLE_LOG_PATH = RUNTIME_LOG_DIR / "backend.console.log"
BACKEND_WINDOW_TITLE = "Jarvis Backend"
BACKEND_START_ATTEMPTS = 15
BACKEND_START_TIMEOUT_SECONDS = 30
BACKEND_ATTEMPT_DELAY_SECONDS = BACKEND_START_TIMEOUT_SECONDS / BACKEND_START_ATTEMPTS


def log(message: str) -> None:
    RUNTIME_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
    print(line)


def _resolve_python_executable() -> str:
    """Resolve Python executable using multiple fallback strategies"""
    # First, try to use venv python
    venv_python = _resolve_venv_python()
    if venv_python:
        return str(venv_python)
    
    # Second, try system python
    if sys.executable:
        return sys.executable
    
    # Last resort, search PATH
    return shutil.which("python") or "python"


def _resolve_npm_command() -> str:
    if os.name == "nt":
        return shutil.which("npm.cmd") or "npm.cmd"
    return shutil.which("npm") or "npm"


def _subprocess_creation_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _backend_creation_flags() -> int:
    return getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0


def _quote_powershell_literal(value: str) -> str:
    return value.replace("'", "''")


def _open_log_file(name: str):
    RUNTIME_LOG_DIR.mkdir(parents=True, exist_ok=True)
    return open(RUNTIME_LOG_DIR / name, "a", encoding="utf-8")


def _spawn_process(
    command: list[str],
    cwd: str,
    env: dict[str, str],
    stdout_name: str,
    stderr_name: str,
) -> subprocess.Popen:
    stdout_handle = _open_log_file(stdout_name)
    stderr_handle = _open_log_file(stderr_name)
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            creationflags=_subprocess_creation_flags(),
        )
    finally:
        stdout_handle.close()
        stderr_handle.close()
    return process


def _run_powershell(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )


def _get_listener_process(port: int) -> dict[str, object] | None:
    if os.name != "nt":
        return None

    script = rf"""
$connection = Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $connection) {{
    return
}}
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)" | Select-Object ProcessId, Name, CommandLine
if ($null -eq $process) {{
    return
}}
[pscustomobject]@{{
    pid = [int]$process.ProcessId
    name = [string]$process.Name
    commandLine = [string]$process.CommandLine
}} | ConvertTo-Json -Compress
"""
    completed = _run_powershell(script)
    payload = completed.stdout.strip()
    if completed.returncode != 0 or not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _normalize_command_line(info: dict[str, object] | None) -> str:
    return str((info or {}).get("commandLine") or "").lower()


def _is_jarvis_backend_process(info: dict[str, object] | None) -> bool:
    command_line = _normalize_command_line(info)
    root = str(APP_DIR).lower()
    return root in command_line and (
        "-m core.main" in command_line
        or "core.main" in command_line
        or "core\\main.py" in command_line
        or "core/main.py" in command_line
    )


def _is_jarvis_frontend_process(info: dict[str, object] | None) -> bool:
    return False


def _is_jarvis_process(info: dict[str, object] | None, role: str) -> bool:
    if role == "backend":
        return _is_jarvis_backend_process(info)
    if role == "frontend":
        return _is_jarvis_frontend_process(info)
    return False


def _kill_pid_tree(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )


def _tail_log_lines(path: Path, line_count: int = 10) -> list[str]:
    if not path.exists():
        return []
    try:
        raw = path.read_bytes()
        decoded = ""
        for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
            try:
                decoded = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if not decoded:
            decoded = raw.decode("utf-8", errors="ignore")
        return [line.replace("\x00", "") for line in decoded.splitlines()[-line_count:]]
    except Exception:
        return []


def _print_backend_console_tail() -> None:
    print("Last 10 lines of backend console output:")
    lines = _tail_log_lines(BACKEND_CONSOLE_LOG_PATH, line_count=10)
    if not lines:
        print("<no backend console output captured>")
        return
    for line in lines:
        print(line)


def reclaim_port(port: int, role: str) -> None:
    process_info = _get_listener_process(port)
    if not process_info:
        return

    pid = int(process_info.get("pid", 0) or 0)
    name = str(process_info.get("name") or "unknown")
    command_line = str(process_info.get("commandLine") or "").strip()

    if role == "backend" and "python" not in name.lower():
        log(f"Skipping backend port reclaim for non-Python process on port {port}: {name} (PID {pid}).")
        return

    if not _is_jarvis_process(process_info, role):
        raise RuntimeError(
            f"Port {port} is already in use by unrelated process {name} "
            f"(PID {pid}): {command_line or 'command line unavailable'}"
        )

    log(f"Stopping existing Jarvis {role} on port {port} (PID {pid}).")
    _kill_pid_tree(pid)
    time.sleep(1.0)


def force_release_backend_port() -> None:
    command = 'taskkill /F /IM python.exe /FI "WINDOWTITLE eq Jarvis Backend*" /T'
    log(f"Force releasing backend port with: {command}")
    subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    reclaim_port(BACKEND_PORT, "backend")


def _wait_for_http_ready(
    url: str,
    max_attempts: int | None = None,
    attempt_delay_seconds: float | None = None,
    process: subprocess.Popen | None = None,
    label: str = "service",
    timeout_seconds: float | None = None,
) -> None:
    last_error = "service did not respond"

    # Backwards-compatible: allow callers to pass timeout_seconds instead of max_attempts/attempt_delay
    if timeout_seconds is not None and (max_attempts is None or attempt_delay_seconds is None):
        attempt_delay_seconds = attempt_delay_seconds or 2.0
        max_attempts = max_attempts or max(1, int(timeout_seconds / attempt_delay_seconds))

    # Ensure defaults
    if max_attempts is None:
        max_attempts = 15
    if attempt_delay_seconds is None:
        attempt_delay_seconds = 1.5

    for i in range(1, max_attempts + 1):
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"Process exited early with code {process.returncode}")

        print(f"Waiting for {label}... (Attempt {i}/{max_attempts})")

        try:
            request = urllib.request.Request(url, headers={"User-Agent": "JarvisLauncher/1.0"})
            with urllib.request.urlopen(request, timeout=2) as response:
                # Accept any 2xx-4xx as 'service alive'
                if 200 <= getattr(response, 'status', 200) < 500:
                    return
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = str(exc)

        if i < max_attempts:
            time.sleep(attempt_delay_seconds)

    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _build_backend_env() -> dict[str, str]:
    env = dict(os.environ)
    pythonpath = [str(APP_DIR)]
    existing = env.get("PYTHONPATH", "").strip()
    if existing:
        pythonpath.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def validate_layout() -> None:
    required_paths = {
        "Core directory": CORE_DIR,
        "Backend entry": BACKEND_ENTRY,
        "Frontend directory": FRONTEND_DIR,
        "Frontend package": FRONTEND_PACKAGE,
    }
    for label, path in required_paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"{label} not found: {path}")


def _frontend_vite_bin() -> Path:
    return FRONTEND_DIR_PATH / "index.html"


def _frontend_deps_ready() -> bool:
    return _frontend_vite_bin().exists()


def ensure_frontend_dependencies() -> None:
    if not _frontend_deps_ready():
        raise FileNotFoundError(f"Frontend entry not found: {_frontend_vite_bin()}")


def start_backend() -> subprocess.Popen:
    python_executable = _resolve_python_executable()
    env = _build_backend_env()
    BACKEND_CONSOLE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_CONSOLE_LOG_PATH.write_text("", encoding="utf-8")
    log(f"Starting backend from {CORE_DIR} using {python_executable}")

    if os.name == "nt":
        script = (
            f"$Host.UI.RawUI.WindowTitle = '{_quote_powershell_literal(BACKEND_WINDOW_TITLE)}'; "
            f"& '{_quote_powershell_literal(python_executable)}' "
            f"'{_quote_powershell_literal(str(BACKEND_ENTRY))}' 2>&1 | "
            f"Tee-Object -FilePath '{_quote_powershell_literal(str(BACKEND_CONSOLE_LOG_PATH))}' -Append"
        )
        return subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            cwd=CORE_DIR,
            env=env,
            creationflags=_backend_creation_flags(),
        )

    console_handle = BACKEND_CONSOLE_LOG_PATH.open("a", encoding="utf-8")
    try:
        return subprocess.Popen(
            [python_executable, str(BACKEND_ENTRY)],
            cwd=CORE_DIR,
            env=env,
            stdout=console_handle,
            stderr=subprocess.STDOUT,
            creationflags=_backend_creation_flags(),
        )
    finally:
        console_handle.close()


def start_frontend() -> None:
    ensure_frontend_dependencies()
    log(f"Frontend is served by the backend from {FRONTEND_DIR}")


def _terminate_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        if os.name == "nt":
            _kill_pid_tree(process.pid)
            process.wait(timeout=5)
        else:
            process.terminate()
            process.wait(timeout=5)
    except Exception:
        process.kill()


def main() -> int:
    backend_process: subprocess.Popen | None = None

    try:
        log("Launcher bootstrap starting.")
        validate_layout()

        force_release_backend_port()

        backend_process = start_backend()
        _wait_for_http_ready(
            BACKEND_HEALTH_URL,
            max_attempts=BACKEND_START_ATTEMPTS,
            attempt_delay_seconds=BACKEND_ATTEMPT_DELAY_SECONDS,
            process=backend_process,
            label="backend",
        )
        log(f"Backend is healthy at {BACKEND_HEALTH_URL}")

        start_frontend()
        log(f"Frontend is healthy at {FRONTEND_URL}")

        webbrowser.open(FRONTEND_URL)
        log("Browser launched.")
        return 0
    except Exception as exc:
        log(f"Launcher bootstrap failed: {exc}")
        if backend_process is not None:
            _print_backend_console_tail()
        _terminate_process(backend_process)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
