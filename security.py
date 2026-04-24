"""
Security utilities for JARVIS
"""
import os
import re
import hashlib
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def sanitize_env_vars() -> Dict[str, str]:
    """
    Create a sanitized copy of environment variables with sensitive data redacted.
    
    Useful for subprocess calls to prevent accidental credential leakage.
    
    Returns:
        Dictionary of environment variables with sensitive keys redacted
    """
    env = os.environ.copy()
    sensitive_patterns = [
        r'.*(KEY|SECRET|PASSWORD|TOKEN|API|CREDENTIAL|AUTH).*',
        r'.*(DB_|DATABASE_).*',
        r'.*(AWS_|AZURE_|GCP_).*'
    ]
    
    redacted_env = {}
    for key, value in env.items():
        should_redact = any(
            re.match(pattern, key, re.IGNORECASE)
            for pattern in sensitive_patterns
        )
        
        if should_redact:
            redacted_env[key] = '***REDACTED***'
            logger.debug(f"Redacted environment variable: {key}")
        else:
            redacted_env[key] = value
    
    return redacted_env


def get_safe_env_vars() -> Dict[str, str]:
    """
    Get a truly safe copy of environment variables for subprocess execution.
    Only includes non-sensitive variables.
    
    Returns:
        Dictionary of safe environment variables
    """
    safe_keys = [
        'PATH', 'HOME', 'USER', 'USERNAME', 'TEMP', 'TMP',
        'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV',
        'LANG', 'LC_ALL', 'TIMEZONE'
    ]
    
    env = os.environ.copy()
    safe_env = {k: v for k, v in env.items() if k in safe_keys}
    
    return safe_env


def hash_sensitive_data(data: str, algorithm: str = 'sha256') -> str:
    """
    Hash sensitive data for secure comparison.
    
    Args:
        data: Data to hash
        algorithm: Hashing algorithm (sha256, md5, etc.)
    
    Returns:
        Hexadecimal hash string
    """
    if algorithm == 'sha256':
        return hashlib.sha256(data.encode()).hexdigest()
    elif algorithm == 'md5':
        return hashlib.md5(data.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def mask_credential(credential: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive credential, showing only first and last few characters.
    
    Args:
        credential: Credential to mask
        visible_chars: Number of characters to show at start/end
    
    Returns:
        Masked credential string
    """
    if len(credential) <= visible_chars * 2:
        return '*' * len(credential)
    
    return credential[:visible_chars] + '*' * (len(credential) - visible_chars * 2) + credential[-visible_chars:]


def get_file_permissions(file_path: str) -> oct:
    """
    Get file permissions in octal format.
    
    Args:
        file_path: Path to file
    
    Returns:
        Octal file permissions
    """
    try:
        return oct(os.stat(file_path).st_mode)[-3:]
    except OSError as e:
        logger.error(f"Error getting permissions for {file_path}: {e}")
        return None


def check_file_security(file_path: str) -> Dict[str, bool]:
    """
    Check if a file has secure permissions.
    
    Args:
        file_path: Path to file
    
    Returns:
        Dictionary with security checks
    """
    path = Path(file_path)
    checks = {}
    
    if not path.exists():
        return {"exists": False}
    
    try:
        stat_info = path.stat()
        mode = stat_info.st_mode
        
        # Check if world-readable
        checks["world_readable"] = bool(mode & 0o004)
        
        # Check if world-writable
        checks["world_writable"] = bool(mode & 0o002)
        
        # Check if group-writable
        checks["group_writable"] = bool(mode & 0o020)
        
        # Check if executable
        checks["executable"] = bool(mode & 0o111)
        
        # Check if file is owned by current user (Unix-like systems)
        try:
            current_uid = os.getuid()
            checks["owned_by_user"] = stat_info.st_uid == current_uid
        except AttributeError:
            # Windows doesn't have getuid
            checks["owned_by_user"] = True
        
        return checks
    
    except Exception as e:
        logger.error(f"Error checking file security for {file_path}: {e}")
        return {"error": str(e)}


def scan_for_sensitive_data(text: str) -> list:
    """
    Scan text for potential sensitive data patterns.
    
    Args:
        text: Text to scan
    
    Returns:
        List of detected sensitive patterns
    """
    patterns = {
        "api_key": r"api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9\-_]{20,}",
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "private_key": r"-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY",
        "password": r"password\s*[:=]\s*['\"][^'\"]{6,}",
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
    }
    
    found = []
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found.append({
                "type": pattern_name,
                "count": len(matches),
                "pattern": pattern
            })
    
    return found


def validate_file_path(file_path: str, allowed_dirs: list = None) -> bool:
    """
    Validate that a file path is safe (not using directory traversal, etc.).
    
    Args:
        file_path: Path to validate
        allowed_dirs: List of allowed base directories
    
    Returns:
        True if path is safe, False otherwise
    """
    try:
        path = Path(file_path).resolve()
        
        # Check for null bytes (path traversal attempt)
        if '\x00' in str(path):
            logger.warning(f"Null byte detected in path: {file_path}")
            return False
        
        # Check against allowed directories if specified
        if allowed_dirs:
            allowed_paths = [Path(d).resolve() for d in allowed_dirs]
            if not any(path.is_relative_to(allowed) for allowed in allowed_paths):
                logger.warning(f"Path outside allowed directories: {file_path}")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error validating path {file_path}: {e}")
        return False
