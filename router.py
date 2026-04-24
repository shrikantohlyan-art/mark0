"""
JARVIS Router - Intelligent Model & Tool Routing
Routes requests to appropriate LLM (Gemini or Ollama) based on intent and capabilities.
"""

import json
import logging
import time
from typing import Optional
from pathlib import Path
from http_client import HttpClient

logger = logging.getLogger(__name__)

from Core import settings

try:
    from google import genai
except ImportError:
    genai = None

def _load_model_routing_config() -> tuple[list[str], dict[str, int], str]:
    """
    Load model routing config from `config.yaml` via `Core.settings`.

    Falls back to safe defaults if config is missing/invalid.
    """

    default_model_name = "gemini-2.5-flash"

    # Defaults tuned for RTX 3050 6GB (local Ollama models)
    default_order = [
        "phi:latest",  # ~1.6GB - fastest, simple tasks
        "qwen2.5:7b",  # ~4.7GB - best balance
        "llama3:8b",  # ~4.7GB - good general
        "deepseek-r1:8b",  # ~5.2GB - reasoning/math
        "qwen3.5:latest",  # ~6.6GB - last resort (may use CPU)
    ]
    default_timeouts: dict[str, int] = {
        "phi:latest": 30,
        "qwen2.5:7b": 60,
        "llama3:8b": 60,
        "deepseek-r1:8b": 90,
        "qwen3.5:latest": 120,
    }

    try:
        cfg = settings.get_settings()

        preferred_any = cfg.get("models.preferred_model_order", default_order)
        if isinstance(preferred_any, list):
            preferred_clean = [str(x).strip() for x in preferred_any if str(x).strip()]
            preferred_order = preferred_clean or default_order
        else:
            preferred_order = default_order

        timeouts_any = cfg.get("models.model_timeouts", default_timeouts)
        timeouts_clean: dict[str, int] = {}
        if isinstance(timeouts_any, dict):
            for k, v in timeouts_any.items():
                key = str(k).strip()
                if not key:
                    continue
                try:
                    timeouts_clean[key] = int(v)
                except Exception:
                    continue

        model_name = str(cfg.get("models.default", default_model_name)).strip() or default_model_name

        merged_timeouts = dict(default_timeouts)
        merged_timeouts.update(timeouts_clean)

        return preferred_order, merged_timeouts, model_name
    except Exception:
        return default_order, default_timeouts, default_model_name


PREFERRED_MODEL_ORDER, MODEL_TIMEOUTS, GEMINI_MODEL_NAME = _load_model_routing_config()

# ===== SYSTEM COMMAND DETECTION =====
SYSTEM_COMMAND_PREFIXES = [
    "open ",
    "close ",
    "launch ",
    "run ",
    "start ",
    "kill ",
    "check system",
    "system check",
    "check my pc",
    "system scan",
    "pc specs",
    "my specs",
    "system info",
    "create file",
    "delete file",
    "read file",
    "write to file",
    "what time",
    "current time",
    "time now",
    "what date",
    "take screenshot",
    "screenshot",
    "search google",
    "search youtube",
    "open youtube",
    "open chrome",
    "open spotify",
    "open netflix",
    "open discord",
    "type ",
    "click ",
    "press ",
    "scroll ",
    "copy ",
    "paste",
    "select all",
    "volume up",
    "volume down",
    "mute",
    "unmute",
    "shutdown",
    "restart",
    "sleep",
    "lock screen",
    "weather",
    "ping",
    "install ",
    "uninstall ",
    "go to ",
    "navigate to ",
    "visit ",
    "download ",
    "upload ",
    "fill form",
    "login to",
    "open website",
    "play ",
    "pause",
    "stop music",
    "send whatsapp",
    "send email",
    "set alarm",
    "set timer",
    "set reminder",
    "translate ",
    "convert ",
    "calculate ",
    "math ",
]

WEB_KEYWORDS = [
    "search",
    "look up",
    "find online",
    "find",
    "google",
    "youtube",
    "browse",
    "check website",
    "fetch",
    "scrape",
    "web page",
    "url",
    "news",
    "weather",
    "stock price",
    "bitcoin",
    "crypto",
]


class HybridRouter:
    """
    Hybrid router combining Ollama (local) and Gemini (cloud).
    - Tries local models first (faster, privacy)
    - Falls back to Gemini for complex tasks
    - Auto-rotates Gemini API keys on rate limits
    """

    _ace_class = None  # cached JarvisACE class (or False if unavailable)

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.gemini_api_keys = list(settings.GEMINI_API_KEYS or [])
        self.gemini_key_index = 0
        self.gemini_consecutive_failures = 0
        self.gemini_client = None
        self.gemini_model_name = GEMINI_MODEL_NAME
        self.last_gemini_error = None
        self.mode = "hybrid"
        self._hardware_recommended = []

        # Available Ollama models (will be checked lazily on first use)
        self.available_ollama_models = []
        self._ollama_checked = False
        self.ollama_healthy = False
        self.gemini_blocked_until = 0.0

        # Load hardware profile for auto-configuration
        hw_profile = Path(__file__).parent / "config" / "hardware_profile.json"
        if hw_profile.exists():
            try:
                hw = json.loads(hw_profile.read_text())
                self.mode = hw.get("mode", "hybrid")
                self._hardware_recommended = hw.get("recommended_local", [])
            except Exception:
                self.mode = "hybrid"
                self._hardware_recommended = []

        # Initialize Gemini
        if self.gemini_api_keys:
            self._initialize_gemini()
        # Optionally probe Ollama at startup when local models are enabled
        try:
            if settings.USE_LOCAL_MODELS:
                self.check_ollama_health()
        except Exception:
            # Do not let startup health checks crash the runtime
            self.ollama_healthy = False

    def _get_ollama_models(self):
        """Lazily check Ollama models once"""
        if self._ollama_checked:
            return self.available_ollama_models

        try:
            response = HttpClient.get(
                f"{settings.OLLAMA_URL}/api/tags",
                timeout=5,
                quiet=True,
                max_retries=0,
            )
            if response.status_code == 200:
                data = response.json()
                self.available_ollama_models = [
                    m["name"] for m in data.get("models", [])
                ]
        except Exception:
            self.available_ollama_models = []

        self._ollama_checked = True
        return self.available_ollama_models

    def _check_ollama_models(self):
        """Discover available Ollama models"""
        return self._get_ollama_models()

    def _initialize_gemini(self):
        """Initialize Gemini API client"""
        # Do not raise on gemini init failures - mark client unhealthy and record error
        if not self.gemini_api_keys:
            self.gemini_client = None
            self.last_gemini_error = "No Gemini API keys configured"
            logger.info("Gemini disabled: no API keys configured")
            return

        if not genai:
            # google-genai not installed; do not crash the runtime
            self.gemini_client = None
            self.last_gemini_error = "google-genai package not installed"
            logger.warning(
                "google-genai package not available; Gemini disabled: %s",
                self.last_gemini_error,
            )
            return

        try:
            api_key = self.gemini_api_keys[self.gemini_key_index]
            client = genai.Client(api_key=api_key)
            if client:
                self.gemini_client = client
                self.last_gemini_error = None
                logger.info(
                    "Gemini client initialized with configured key index %d",
                    self.gemini_key_index,
                )
            else:
                self.gemini_client = None
                self.last_gemini_error = (
                    "Gemini client initialization returned falsy client"
                )
                logger.warning(
                    "Gemini client init returned falsy client; disabling gemini: %s",
                    self.last_gemini_error,
                )
        except Exception as exc:
            # Record the error but allow the application to continue running
            self.gemini_client = None
            self.last_gemini_error = str(exc)
            logger.warning("Gemini client initialization failed: %s", exc)

    def _detect_system_command(self, prompt: str) -> bool:
        """Backward-compatible alias for older diagnostics/tests."""
        return self._is_system_command(prompt)

    def _should_route_to_gemini(self, prompt: str) -> bool:
        """Backward-compatible helper for older diagnostics/tests."""
        requested_model = self._detect_requested_model(prompt)
        return requested_model == "gemini" or self._needs_web_search(prompt)

    def _detect_requested_model(self, prompt: str) -> Optional[str]:
        """
        Detect if user explicitly requested a specific model.
        Examples: "use gemini", "use qwen", "use phi"
        Returns model name or None.
        """
        prompt_lower = prompt.lower()

        # Check for explicit model requests
        if "use gemini" in prompt_lower or "use google" in prompt_lower:
            return "gemini"

        for model_name in PREFERRED_MODEL_ORDER:
            base_name = model_name.split(":")[0]
            if f"use {base_name}" in prompt_lower:
                return model_name

        return None

    def _is_system_command(self, prompt: str) -> bool:
        """Check if prompt is a system command"""
        prompt_lower = prompt.lower().strip()
        return any(
            prompt_lower == prefix.lower().strip()
            or prompt_lower.startswith(prefix.lower().strip() + " ")
            for prefix in SYSTEM_COMMAND_PREFIXES
        )

    def _needs_web_search(self, prompt: str) -> bool:
        """Check if prompt needs web search capability"""
        prompt_lower = prompt.lower()

        # Check for web-related keywords
        if any(keyword in prompt_lower for keyword in WEB_KEYWORDS):
            return True

        # Check for URLs
        if "http://" in prompt or "https://" in prompt:
            return True

        return False

    def test_gemini(self) -> bool:
        """Test Gemini connectivity"""
        if not self.gemini_client or not self.gemini_api_keys:
            return False

        attempts = max(1, len(self.gemini_api_keys))
        last_error = None
        for _ in range(attempts):
            try:
                self.gemini_client.models.generate_content(
                    model=self.gemini_model_name, contents="Say OK"
                )
                self.gemini_consecutive_failures = 0
                self.last_gemini_error = None
                return True
            except Exception as exc:
                last_error = str(exc)
                self.last_gemini_error = last_error
                error_str = str(exc).lower()
                if ("429" in error_str or "rate limit" in error_str) and len(
                    self.gemini_api_keys
                ) > 1:
                    self.gemini_key_index = (self.gemini_key_index + 1) % len(
                        self.gemini_api_keys
                    )
                    self._initialize_gemini()
                    continue
                return False

        self.last_gemini_error = last_error
        return False

    def _call_gemini(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """
        Call Gemini API with current key.
        Auto-rotate keys on failure.
        """
        if not self.gemini_api_keys:
            return None

        # Respect temporary cooldown if Gemini was recently blocked due to quota
        blocked_until = float(getattr(self, "gemini_blocked_until", 0.0) or 0.0)
        if blocked_until > time.time():
            self.last_gemini_error = "Gemini temporarily blocked due to quota"
            logger.warning("Gemini call blocked until %s", blocked_until)
            return None

        # Enforce cloud model budget limits (global guard)
        try:
            from Core.model_budget import budget as model_budget
        except Exception:
            model_budget = None

        if model_budget is not None and not model_budget.can_call():
            self.last_gemini_error = "Cloud model budget exhausted"
            logger.warning("Cloud model budget exhausted; blocking Gemini call")
            return None

        # Limit attempts to avoid quota-draining rotation loops.
        attempts = 1
        for _ in range(attempts):
            if not self.gemini_client:
                self._initialize_gemini()

            try:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model_name,
                    contents=prompt,
                    config={
                        "temperature": 0.7,
                        "max_output_tokens": 4096,
                    },
                )

                self.gemini_consecutive_failures = 0
                self.last_gemini_error = None
                result = response.text if response else None

                if result:
                    # record cloud usage for budget accounting
                    try:
                        if model_budget is not None:
                            model_budget.record_call()
                    except Exception:
                        pass
                    self._record_learning(prompt, result)

                logger.info("HybridRouter: gemini returned result (len=%d)", len(str(result or "")))
                return result

            except Exception as e:
                self.last_gemini_error = str(e)
                error_str = str(e).lower()
                # Treat quota/exhausted responses as fatal for short cooldown
                if ("429" in error_str) or ("resource_exhausted" in error_str) or ("quota" in error_str):
                    self.gemini_consecutive_failures += 1
                    # Temporarily block Gemini to avoid hammering quota (even if multiple keys exist).
                    self.gemini_blocked_until = time.time() + 300
                    logger.warning(
                        "HybridRouter: Gemini returned quota error; blocking Gemini until %s: %s",
                        self.gemini_blocked_until,
                        e,
                    )
                    return None
                # Otherwise rotate key and retry (limited by attempts)
                if len(self.gemini_api_keys) > 1:
                    self.gemini_key_index = (self.gemini_key_index + 1) % len(
                        self.gemini_api_keys
                    )
                    self._initialize_gemini()
                    continue
                self.gemini_consecutive_failures += 1
                return None

        self.gemini_consecutive_failures += 1
        return None

    def _record_learning(self, prompt: str, result: str) -> None:
        """Record a successful result for ACE learning (best-effort)."""
        if HybridRouter._ace_class is False:
            return
        if HybridRouter._ace_class is None:
            try:
                from Core.ace_wrapper import JarvisACE

                HybridRouter._ace_class = JarvisACE
            except ImportError:
                HybridRouter._ace_class = False
                return
        try:
            ace = HybridRouter._ace_class(api_key=self.gemini_api_keys[0])
            ace.learn_from_result(prompt, result, success=True)
        except Exception as exc:
            logger.debug("ACE learning failed: %s", exc)

    def _call_ollama(self, prompt: str, model: str, timeout: int) -> Optional[str]:
        """Call local Ollama model"""
        try:
            response = HttpClient.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    },
                },
                timeout=timeout,
            )

            if response and getattr(response, "status_code", None) == 200:
                return response.json().get("response")
            logger.warning(
                "Ollama returned status %s for model %s",
                getattr(response, "status_code", "?"),
                model,
            )

        except Exception as exc:
            # Do not let Ollama connection errors crash the backend - return
            # a clear user-facing message instead so the UI can surface it.
            logger.error("Ollama call failed for model %s: %s", model, exc)
            return (
                "Local AI node unreachable. Please ensure Ollama is running on port 11434 "
                "and the requested model is pulled."
            )

        return None

    def process_input_with_auto_model(
        self, prompt: str, long_task_mode: bool = False
    ) -> dict:
        """
        Process input with automatic model selection.

        Returns:
        {
            "ok": bool,
            "chat": str,
            "model": str,
            "source": str  # "gemini", "ollama", "system"
        }
        """

        cloud_calls = 0
        cloud_limit = int(getattr(settings, "CLOUD_CALL_LIMIT_PER_REQUEST", 1))
        result = None

        # Graceful handling for custom frameworks (e.g., DeerFlow)
        try:
            prompt_lower = prompt.lower()
            custom_frameworks = ["deerflow", "deer_flow", "deer-flow"]
            for fw in custom_frameworks:
                if fw in prompt_lower:
                    try:
                        import importlib

                        importlib.import_module(fw.replace("-", ""))
                    except Exception:
                        return {
                            "ok": False,
                            "chat": f"Requested framework '{fw}' is not connected. Please ensure it is installed and configured or choose a different model.",
                            "model": None,
                            "source": "system",
                        }
        except Exception:
            # Non-fatal: continue to normal routing
            pass

        # 1. CHECK FOR SYSTEM COMMANDS
        if self._is_system_command(prompt):
            return {
                "ok": True,
                "chat": "SYSTEM_COMMAND",
                "model": "system-tools",
                "source": "system",
            }

        # 2. CHECK FOR EXPLICIT MODEL REQUEST
        requested_model = self._detect_requested_model(prompt)
        if requested_model == "gemini" and settings.USE_CLOUD_MODELS:
            if cloud_calls >= cloud_limit:
                self.last_gemini_error = "Per-request cloud call limit reached"
            else:
                cloud_calls += 1
                result = self._call_gemini(prompt)
            if result:
                return {
                    "ok": True,
                    "chat": result,
                    "model": self.gemini_model_name,
                    "source": "gemini",
                }

        if requested_model and requested_model in PREFERRED_MODEL_ORDER:
            timeout = MODEL_TIMEOUTS.get(requested_model, settings.LOCAL_MODEL_TIMEOUT)
            result = self._call_ollama(prompt, requested_model, timeout)
            if result:
                return {
                    "ok": True,
                    "chat": result,
                    "model": requested_model,
                    "source": "ollama",
                }

        # 3. CHECK FOR WEB SEARCH NEEDS
        if self._needs_web_search(prompt):
            # Local-first: prefer Ollama/local models for web-style prompts
            if settings.USE_LOCAL_MODELS:
                ollama_models = self._get_ollama_models()
                for model in PREFERRED_MODEL_ORDER:
                    if model not in ollama_models:
                        continue
                    timeout = MODEL_TIMEOUTS.get(model, settings.LOCAL_MODEL_TIMEOUT)
                    result = self._call_ollama(prompt, model, timeout)
                    if result:
                        return {
                            "ok": True,
                            "chat": result,
                            "model": model,
                            "source": "ollama",
                        }

            # Cloud fallback: use Gemini only when local models are not available
            if settings.USE_CLOUD_MODELS and settings.FALLBACK_TO_CLOUD:
                # Consult deterministic decision helper before falling back to cloud
                if not self.should_use_cloud(prompt):
                    self.last_gemini_error = "should_use_cloud prevented cloud usage"
                elif cloud_calls >= cloud_limit:
                    self.last_gemini_error = "Per-request cloud call limit reached"
                else:
                    cloud_calls += 1
                    result = self._call_gemini(prompt)
                if result:
                    return {
                        "ok": True,
                        "chat": result,
                        "model": self.gemini_model_name,
                        "source": "gemini",
                    }

        # 4. DEFAULT: TRY OLLAMA SEQUENTIALLY
        ollama_models = self._get_ollama_models()
        if settings.USE_LOCAL_MODELS and ollama_models:
            for model in PREFERRED_MODEL_ORDER:
                if model not in ollama_models:
                    continue

                timeout = MODEL_TIMEOUTS.get(model, settings.LOCAL_MODEL_TIMEOUT)
                result = self._call_ollama(prompt, model, timeout)
                if result:
                    return {
                        "ok": True,
                        "chat": result,
                        "model": model,
                        "source": "ollama",
                    }

        # 5. FALLBACK: TRY GEMINI
        if settings.USE_CLOUD_MODELS and settings.FALLBACK_TO_CLOUD:
            # Respect deterministic decision helper before making cloud calls
            if not self.should_use_cloud(prompt):
                self.last_gemini_error = "should_use_cloud prevented cloud usage"
            elif cloud_calls >= cloud_limit:
                self.last_gemini_error = "Per-request cloud call limit reached"
            else:
                cloud_calls += 1
                result = self._call_gemini(prompt)
            if result:
                return {
                    "ok": True,
                    "chat": result,
                    "model": self.gemini_model_name,
                    "source": "gemini",
                }

        # 6. EVERYTHING FAILED
        return {
            "ok": False,
            "chat": "Error: Could not reach any model. Check Ollama is running or internet is available.",
            "model": None,
            "source": None,
        }

    async def generate_response(self, prompt: str, use_json: bool = False, long_task_mode: bool = False):
        """Async helper to generate a conversational response.

        If `use_json` is True, the method will prepend a small instruction
        requesting the model to return only valid JSON.
        Returns the raw chat string produced by the underlying local/cloud model.
        """
        import asyncio

        wrapped = prompt
        if use_json:
            wrapped = (
                "Return ONLY a valid JSON array describing the tools to execute for the "
                "following user request. Do NOT include any explanatory text or markdown.\n"
                f"User request:\n{prompt}\n\nReturn only JSON array."
            )

        try:
            # process_input_with_auto_model is synchronous; run in thread
            result = await asyncio.to_thread(self.process_input_with_auto_model, wrapped, long_task_mode)
            if isinstance(result, dict):
                return result.get("chat") or ""
            return str(result)
        except Exception as e:
            logger.exception("generate_response failed: %s", e)
            return ""

    def should_use_cloud(self, prompt: str, local_confidence: Optional[float] = None) -> bool:
        """Deterministic decision helper whether to use cloud models.

        Rules:
        - If cloud models disabled, return False
        - If user explicitly requested Gemini, return True
        - If prompt needs web search and no local models, return True
        - If local_confidence is provided and < 0.5, prefer cloud
        - System commands prefer local
        - Default: prefer local (False)
        """
        if not settings.USE_CLOUD_MODELS:
            return False

        prompt_lower = prompt.lower()
        if "use gemini" in prompt_lower or "use google" in prompt_lower:
            return True

        if self._needs_web_search(prompt):
            ollama_models = self._get_ollama_models()
            if not settings.USE_LOCAL_MODELS or not ollama_models:
                return True
            return False

        if local_confidence is not None and local_confidence < 0.5:
            return True

        if self._is_system_command(prompt):
            return False

        return False

    def check_ollama_health(self, probe_prompt: str = "Say OK", timeout: int = 5) -> bool:
        """Probe Ollama availability and a simple model generation."""
        try:
            models = self._get_ollama_models()
            if not models:
                self.ollama_healthy = False
                return False

            # Pick the first preferred model available, else the first model
            chosen = None
            for m in PREFERRED_MODEL_ORDER:
                if m in models:
                    chosen = m
                    break
            if not chosen:
                chosen = models[0]

            # Try a tiny generation
            resp = HttpClient.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={"model": chosen, "prompt": probe_prompt, "stream": False},
                timeout=timeout,
                quiet=True,
            )
            if resp and resp.status_code == 200:
                self.ollama_healthy = True
                return True

        except Exception:
            pass

        self.ollama_healthy = False
        return False


# ===== DEFAULT INSTANCE =====
_router_instance = None


def get_router() -> HybridRouter:
    """Get or create the global router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = HybridRouter()
    return _router_instance
