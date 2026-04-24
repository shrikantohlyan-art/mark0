#!/usr/bin/env python3
"""Comprehensive diagnostic scan for the current Jarvis Mark-XXX layout."""

from pathlib import Path
import py_compile
import sys


def print_check(ok: bool, message: str) -> None:
    print(f"    {'OK' if ok else 'FAIL'} {message}")


print("=" * 70)
print("JARVIS MARK-XXX - DIAGNOSTIC SCAN")
print("=" * 70)

print(f"\n[1] Python version: {sys.version.split()[0]}")

print("\n[2] Environment Configuration")
env_path = Path(".env")
if env_path.exists():
    content = env_path.read_text(encoding="utf-8")
    has_gemini = any(f"GEMINI_API_KEY_{i}=" in content for i in range(1, 6)) or "GEMINI_API_KEY=" in content
    has_ollama = "OLLAMA_HOST=" in content or "OLLAMA_PORT=" in content
    print_check(True, ".env file exists")
    print_check(has_gemini, "Gemini API keys configured")
    print_check(has_ollama, "Ollama configuration present")
else:
    print_check(False, ".env file not found")

print("\n[3] Core Files")
required_files = [
    "router.py",
    "run_server.py",
    "tools.py",
    "requirements.txt",
    "Core/main.py",
    "Core/settings.py",
    "Core/tools/browser_agent.py",
    "Core/hardware_scanner.py",
    "Core/ace_wrapper.py",
]
for file in required_files:
    print_check(Path(file).exists(), file)

print("\n[4] Core Settings Module")
try:
    from Core import settings

    print_check(True, "Core.settings imported successfully")
    print(f"       BACKEND_HOST: {settings.BACKEND_HOST}")
    print(f"       BACKEND_PORT: {settings.BACKEND_PORT}")
    print(f"       AUTONOMY_POLICY: {settings.AUTONOMY_POLICY}")
except Exception as exc:
    print_check(False, f"Failed to import Core.settings: {exc}")

print("\n[5] Syntax Check")
for file in ["router.py", "run_server.py", "Core/main.py", "Core/tools/web_tools.py"]:
    try:
        py_compile.compile(file, doraise=True)
        print_check(True, f"{file} has no syntax errors")
    except py_compile.PyCompileError as exc:
        print_check(False, f"{file} syntax error: {exc}")

print("\n[6] Requirements")
try:
    requirements = Path("requirements.txt").read_text(encoding="utf-8").splitlines()
    requirements = [line.strip() for line in requirements if line.strip() and not line.startswith("#")]
    critical = ["fastapi", "uvicorn", "pydantic", "google-genai", "requests", "ace-framework"]
    for package in critical:
        print_check(any(package in req for req in requirements), f"{package} listed")
except Exception as exc:
    print_check(False, f"Could not read requirements.txt: {exc}")

print("\n[7] Router Verification")
try:
    router_content = Path("router.py").read_text(encoding="utf-8")
    checks = {
        "genai.Client(": "Real google-genai client initialization",
        'config={': "google-genai config argument",
        "hardware_profile.json": "hardware profile auto-config",
        "ace.learn_from_result": "ACE learning hook",
    }
    for token, label in checks.items():
        print_check(token in router_content, label)
except Exception as exc:
    print_check(False, f"Unable to inspect router.py: {exc}")

print("\n[8] Main/Web Tool Wiring")
try:
    main_content = Path("Core/main.py").read_text(encoding="utf-8")
    web_content = Path("Core/tools/web_tools.py").read_text(encoding="utf-8")
    print_check("research_topic" in main_content, "Deep research is wired in Core.main")
    print_check('execute_tool("browser", "run"' in main_content, "Browser agent is used for YouTube tasks")
    print_check("def research_topic" in web_content, "Firecrawl research helper exists")
    print_check("def open_website" in web_content, "open_website compatibility helper exists")
except Exception as exc:
    print_check(False, f"Unable to inspect main/web tools: {exc}")

print("\n[9] Common Issues Scan")
issues = []
for file in ["router.py", "Core/main.py", "Core/hardware_scanner.py"]:
    try:
        content = Path(file).read_text(encoding="utf-8")
        if "self.gemini_client = True" in content:
            issues.append(f"Boolean Gemini client bug still present in {file}")
        if "google.generativeai" in content:
            issues.append(f"Legacy google.generativeai import still present in {file}")
    except Exception as exc:
        issues.append(f"Could not scan {file}: {exc}")

if issues:
    for issue in issues:
        print_check(False, issue)
else:
    print_check(True, "No critical legacy issues found in scanned files")

print("\n[10] Configuration Files")
for cfg in ["config/hardware_profile.json", "config/autonomy_settings.json"]:
    print_check(Path(cfg).exists(), cfg)

print("\n" + "=" * 70)
print("DIAGNOSTIC SCAN COMPLETE")
print("=" * 70)
