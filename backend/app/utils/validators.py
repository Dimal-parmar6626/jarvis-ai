"""Input validators."""

import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_strong_password(password: str) -> bool:
    """Password must be at least 8 chars with at least one digit and one letter."""
    return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Strip leading/trailing whitespace and truncate to max_length."""
    return text.strip()[:max_length]


def is_safe_file_path(path: str, base_dir: Optional[str] = None) -> bool:
    """Ensure file path does not contain path traversal sequences."""
    if ".." in path or path.startswith("/etc") or path.startswith("/proc"):
        return False
    return True
