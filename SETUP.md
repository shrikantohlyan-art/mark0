## Setup (Windows)

### Requirements

- Python 3.8+ (3.10+ recommended)
- (Optional) Ollama for local LLM fallback
- (Optional) Node.js 18+ if you want the web UI (`Interface/web`)

### 1) Create venv + install deps

```bat
cd Mark-XXX
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) Configure `.env`

```bat
copy .env.example .env
```

Minimum:
- `GEMINI_API_KEY_1=...` (you can provide multiple numbered keys)

Optional:
- `FIRECRAWL_API_KEY=...`

### 3) Configure `config.yaml`

Key settings:
- `backend.host`, `backend.port`
- `models.default` (Gemini model name)
- `models.preferred_model_order` (Ollama model fallback order)
- `models.model_timeouts` (per-model timeouts)
- `features.*` toggles (voice, code execution, local/cloud models)
- `autonomy.policy` (supervised/authorized/full)

### 4) Ollama (Optional)

1. Install Ollama
2. Start it: `ollama serve`
3. Pull at least one model from your `models.preferred_model_order`, for example:
   - `ollama pull phi:latest`

### 5) Run

- `START_JARVIS.bat` (recommended)
- Or:
```bat
.\.venv\Scripts\python.exe launcher_bootstrap.py
```

Backend:
- Docs: `http://127.0.0.1:8001/docs`
- Health: `http://127.0.0.1:8001/health`

