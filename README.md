## JARVIS (Mark-XXX)

Local-first AI assistant with a FastAPI backend, optional web UI, and tool/model routing (Gemini + Ollama).

### Quick Start

1. Prereqs
   - Python 3.8+ (3.10+ recommended)
   - (Optional) Ollama for local models: https://ollama.com
   - (Optional) Node.js 18+ for the web UI (Interface/web)

2. Install (Windows)
```bat
cd Mark-XXX
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

3. Configure
   - Put secrets in `.env` (Gemini keys, optional Firecrawl, etc.)
   - Adjust runtime config in `config.yaml` (ports, model order, feature flags)

4. Run
   - Easiest: `START_JARVIS.bat`
   - Or: `.\.venv\Scripts\python.exe launcher_bootstrap.py`

Backend OpenAPI docs: `http://127.0.0.1:8001/docs`

### Architecture (High Level)

- `Jarvis.pyw` -> `launcher_bootstrap.py`
  - starts backend (`Core/main.py`) and (optionally) the UI in `Interface/web`
- `router.py`
  - routes prompts to local Ollama models or Gemini (cloud), based on intent and availability
- `Core/`
  - runtime orchestration, tool router, providers, voice helpers, memory modules, etc.
- `config_manager.py` + `config.yaml`
  - config loading (YAML + `.env`) with dot-notation access

### Tests

```bat
cd Mark-XXX
.\.venv\Scripts\python.exe -m pytest tests -q
```

### Notes

- Local model order and timeouts are configured via `config.yaml`:
  - `models.preferred_model_order`
  - `models.model_timeouts`
- Keep runtime artifacts out of git:
  - `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.db`, `*.zip`, `downloads/`, `models/`

