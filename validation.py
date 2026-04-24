"""
Input validation utilities for JARVIS
"""
from typing import Any, Optional
import re
import logging

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


VALID_CHAT_PROVIDERS = ["gemini", "openai", "ollama", "grok", "local"]


class ChatMessage(BaseModel):
    """Lightweight validated chat history item."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {"user", "assistant", "model"}
        role = str(v or "").strip().lower()
        if role not in valid_roles:
            raise ValueError(f"Role must be one of {sorted(valid_roles)}")
        return role

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        content = str(v or "").strip()
        if not content:
            raise ValueError("Message content cannot be empty")
        if len(content) > 10000:
            raise ValueError("Message content exceeds maximum length of 10000 characters")
        return content


class ChatRequest(BaseModel):
    """Validated chat request model."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    prompt: str
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    messages: list[ChatMessage] = Field(default_factory=list)
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    attachments: list[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    long_task_mode: bool = False
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt content."""
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        if len(v) > 10000:
            raise ValueError('Prompt exceeds maximum length of 10000 characters')
        if len(v.strip()) < 1:
            raise ValueError('Prompt contains only whitespace')
        return v.strip()
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider name."""
        provider = str(v or "").strip().lower()
        if provider not in VALID_CHAT_PROVIDERS:
            raise ValueError(f"Provider must be one of {VALID_CHAT_PROVIDERS}")
        return "ollama" if provider == "local" else provider
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: Optional[float]) -> Optional[float]:
        """Validate temperature parameter."""
        if v is not None:
            if not 0.0 <= v <= 2.0:
                raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_tokens parameter."""
        if v is not None:
            if not 1 <= v <= 32000:
                raise ValueError('Max tokens must be between 1 and 32000')
        return v

    @field_validator("attachments")
    @classmethod
    def validate_attachments(cls, v: list[str]) -> list[str]:
        attachments = [str(item or "").strip() for item in list(v or []) if str(item or "").strip()]
        if len(attachments) > 4:
            raise ValueError("Attachments are limited to 4 items")
        return attachments


class TTSRequest(BaseModel):
    """Validated text-to-speech request model."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    text: str
    voice: str = "en-GB-RyanNeural"
    rate: float = 1.0
    pitch: float = 1.0
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate TTS text."""
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        if len(v) > 5000:
            raise ValueError('Text exceeds maximum length of 5000 characters')
        return v.strip()
    
    @field_validator('rate')
    @classmethod
    def validate_rate(cls, v: float) -> float:
        """Validate speech rate."""
        if not 0.5 <= v <= 2.0:
            raise ValueError('Rate must be between 0.5 and 2.0')
        return v
    
    @field_validator('pitch')
    @classmethod
    def validate_pitch(cls, v: float) -> float:
        """Validate speech pitch."""
        if not 0.5 <= v <= 2.0:
            raise ValueError('Pitch must be between 0.5 and 2.0')
        return v


class ModelRequest(BaseModel):
    """Validated model request model."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    provider: str
    model: str
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider name."""
        provider = str(v or "").strip().lower()
        if provider not in VALID_CHAT_PROVIDERS:
            raise ValueError(f"Provider must be one of {VALID_CHAT_PROVIDERS}")
        return "ollama" if provider == "local" else provider
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model name."""
        if not v or not v.strip():
            raise ValueError('Model name cannot be empty')
        if len(v) > 100:
            raise ValueError('Model name too long')
        # Allow alphanumeric, hyphens, underscores, slashes, dots
        if not re.match(r'^[a-zA-Z0-9\-_/\.]+$', v):
            raise ValueError('Invalid model name format')
        return v.strip()


# Common voice-transcription variants of "hey jarvis" / "ok jarvis" / wake words.
# The STT engine often mishears the wake word, so we strip fuzzy variants
# BEFORE the prompt reaches the router / fact handler / skill matcher.
_WAKE_WORD_PATTERN = re.compile(
    r"^\s*(?:"
    r"(?:hey|hi|hai|ok|okay|yo|oye|arey|a|the)\s+"
    r"(?:jarvis|tarvis|jarwis|jarvas|jarbus|javis|jarvish|service|services|office|jar\s*vis|j\s*a\s*r\s*vis)"
    r"|his\s+office"          # very common mis-transcription
    r"|hey\s+service"
    r"|a\s+jarvis"
    r"|reservation"           # mishear of "hey jarvis" / "let's"
    r"|jarvis"                # bare "jarvis" at start
    r")"
    r"[\s,.:;!?-]*",
    re.IGNORECASE,
)


def _strip_wake_word(prompt: str) -> str:
    """Strip leading wake-word (and common mis-transcriptions) from a voice prompt."""
    if not prompt:
        return prompt
    cleaned = _WAKE_WORD_PATTERN.sub("", prompt, count=1).strip()
    # If stripping leaves nothing, keep the original (user may have just said "jarvis")
    return cleaned if cleaned else prompt.strip()


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize prompt by removing potential injection attempts and voice-noise.

    Args:
        prompt: Raw prompt text

    Returns:
        Sanitized prompt
    """
    # Remove any JSON/Action tags similar to what TTS endpoint does
    prompt = re.sub(r'<[^>]+>', '', prompt)  # Remove XML/HTML tags
    prompt = re.sub(r'{[^}]+}', '', prompt)  # Remove JSON-like braces
    prompt = re.sub(r'\[/[\w]+\]', '', prompt)  # Remove closing tags

    # Strip fuzzy wake-word prefix from voice transcription so it doesn't
    # pollute router/fact/skill extractors downstream.
    prompt = _strip_wake_word(prompt)

    return prompt.strip()
