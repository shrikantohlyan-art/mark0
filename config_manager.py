#!/usr/bin/env python3
"""
JARVIS configuration manager.

- Loads `.env` (if python-dotenv is installed)
- Loads `config.yaml` (requires PyYAML)
- Provides dot-notation access via `get("backend.port")`
"""

from __future__ import annotations

import copy
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("jarvis.config")

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _get_nested(data: dict[str, Any], path: str, default: Any = None) -> Any:
    if not path:
        return default
    node: Any = data
    for part in str(path).split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def _set_nested(data: dict[str, Any], path: str, value: Any) -> None:
    parts = [p for p in str(path or "").split(".") if p]
    if not parts:
        return
    node: Any = data
    for part in parts[:-1]:
        if not isinstance(node, dict):
            return
        if part not in node or not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    if isinstance(node, dict):
        node[parts[-1]] = value


def _read_text_best_effort(path: Path) -> str:
    raw = path.read_bytes()
    # Null-byte corruption has been observed in this repo; strip it.
    return raw.decode("utf-8", errors="ignore").replace("\x00", "")


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required but could not be imported.")
    if not path.exists():
        return {}
    try:
        text = _read_text_best_effort(path)
        data = yaml.safe_load(text) if text.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("Failed to load YAML config %s: %s", path, exc)
        return {}


def _dump_yaml(data: dict[str, Any]) -> str:
    if yaml is None:
        raise RuntimeError("PyYAML is required but could not be imported.")
    return yaml.safe_dump(
        data or {},
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )


class ConfigManager:
    """
    Central config manager.

    This class intentionally stays lightweight and avoids importing project modules.
    """

    DEFAULT_CONFIG: dict[str, Any] = {
        "backend": {
            "host": "127.0.0.1",
            "port": 8001,
            "debug": False,
            "workers": 1,
            "reload": False,
        },
        "frontend": {"host": "localhost", "port": 5173, "debug": False},
        "models": {
            "default": "gemini-2.5-flash",
            "ollama_host": "localhost",
            "ollama_port": 11434,
            "preferred_model_order": [
                "phi:latest",
                "qwen2.5:7b",
                "llama3:8b",
                "deepseek-r1:8b",
                "qwen3.5:latest",
            ],
            "model_timeouts": {
                "phi:latest": 30,
                "qwen2.5:7b": 60,
                "llama3:8b": 60,
                "deepseek-r1:8b": 90,
                "qwen3.5:latest": 120,
            },
        },
        "timeouts": {
            "chat_request_seconds": 120,
            "local_model_seconds": 120,
            "api_call_seconds": 30,
        },
        "logging": {
            "level": "INFO",
            "path": "logs",
            "file": "jarvis.log",
            "max_bytes": 10485760,
            "backup_count": 5,
        },
        "features": {
            "enable_voice": True,
            "enable_code_execution": True,
            "use_local_models": True,
            "use_cloud_models": True,
            "fallback_to_cloud": True,
            "enable_legacy_agent_fallback": False,
        },
        "autonomy": {
            "policy": "supervised",
            "trusted_commands": [
                "open_application",
                "get_current_time",
                "get_weather",
                "search_web",
                "take_screenshot",
                "get_system_info",
                "read_file",
                "list_directory",
                "play_music",
            ],
        },
        "cloud": {
            "call_limits": {
                "per_request": 1,
                "per_session": 100,
                "per_minute": 10,
                "per_hour": 600,
            }
        },
    }

    def __init__(
        self,
        config_path: Optional[Path] = None,
        *,
        env_path: Optional[Path] = None,
    ) -> None:
        self.config_path = Path(
            config_path
            or os.environ.get("JARVIS_CONFIG_PATH")
            or DEFAULT_CONFIG_PATH
        )
        self.env_path = Path(
            env_path or os.environ.get("JARVIS_ENV_PATH") or DEFAULT_ENV_PATH
        )

        if callable(load_dotenv):
            load_dotenv(self.env_path, override=False)

        self.config: dict[str, Any] = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> dict[str, Any]:
        loaded = _load_yaml(self.config_path)
        merged = _deep_merge(self.DEFAULT_CONFIG, loaded)
        if not self.config_path.exists():
            # First boot: persist defaults so users have something to edit.
            self._write_yaml(self.config_path, merged)
        return merged

    def _write_yaml(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _dump_yaml(data)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)

    def _apply_env_overrides(self) -> None:
        mappings: list[tuple[str, str, str]] = [
            ("JARVIS_BACKEND_HOST", "backend.host", "str"),
            ("JARVIS_BACKEND_PORT", "backend.port", "int"),
            ("JARVIS_FRONTEND_HOST", "frontend.host", "str"),
            ("JARVIS_FRONTEND_PORT", "frontend.port", "int"),
            ("JARVIS_DEFAULT_MODEL", "models.default", "str"),
            ("OLLAMA_HOST", "models.ollama_host", "str"),
            ("OLLAMA_PORT", "models.ollama_port", "int"),
            ("JARVIS_LOG_LEVEL", "logging.level", "str"),
            ("JARVIS_LOG_PATH", "logging.path", "str"),
            ("ENABLE_VOICE", "features.enable_voice", "bool"),
            ("ENABLE_CODE_EXECUTION", "features.enable_code_execution", "bool"),
            ("USE_LOCAL_MODELS", "features.use_local_models", "bool"),
            ("USE_CLOUD_MODELS", "features.use_cloud_models", "bool"),
            ("FALLBACK_TO_CLOUD", "features.fallback_to_cloud", "bool"),
            ("AUTONOMY_POLICY", "autonomy.policy", "str"),
            ("CLOUD_CALL_LIMIT_PER_REQUEST", "cloud.call_limits.per_request", "int"),
            ("CLOUD_CALL_LIMIT_PER_SESSION", "cloud.call_limits.per_session", "int"),
            ("CLOUD_CALLS_PER_MINUTE", "cloud.call_limits.per_minute", "int"),
            ("CLOUD_CALLS_PER_HOUR", "cloud.call_limits.per_hour", "int"),
        ]

        for env_name, key, kind in mappings:
            raw = os.environ.get(env_name)
            if raw is None or str(raw).strip() == "":
                continue
            if kind == "int":
                try:
                    value: Any = int(str(raw).strip())
                except Exception:
                    continue
            elif kind == "bool":
                value = _parse_bool(raw, default=False)
            else:
                value = str(raw)
            _set_nested(self.config, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        if "." in str(key):
            return _get_nested(self.config, key, default)
        if isinstance(self.config, dict):
            return self.config.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        if "." in str(key):
            _set_nested(self.config, key, value)
            return
        if isinstance(self.config, dict):
            self.config[key] = value

    def merge(self, overrides: dict[str, Any]) -> None:
        if isinstance(overrides, dict):
            self.config = _deep_merge(self.config, overrides)

    def save(self) -> bool:
        try:
            self._write_yaml(self.config_path, self.config)
            return True
        except Exception as exc:
            logger.error("Failed to save config: %s", exc)
            return False

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self.config if isinstance(self.config, dict) else {})

    def validate(self) -> bool:
        backend_port = self.get("backend.port", 8001)
        frontend_port = self.get("frontend.port", 5173)
        try:
            backend_port = int(backend_port)
            frontend_port = int(frontend_port)
        except Exception:
            return False
        if not (1 <= backend_port <= 65535):
            return False
        if not (1 <= frontend_port <= 65535):
            return False
        return True

    @staticmethod
    def from_file(path: Path) -> "ConfigManager":
        return ConfigManager(config_path=path)


_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


def init_config(config_path: Optional[Path] = None) -> ConfigManager:
    global _config_instance
    _config_instance = ConfigManager(config_path=config_path)
    return _config_instance


__all__ = ["ConfigManager", "get_config", "init_config"]
