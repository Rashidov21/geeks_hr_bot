"""
Shared utility functions for handlers
"""
import re
from typing import Tuple


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    pattern = r"^\+?[1-9]\d{6,14}$"
    return bool(re.match(pattern, cleaned))


def validate_age(age_str: str) -> Tuple[bool, int | None]:
    """Validate age input. Returns (is_valid, age_value)."""
    try:
        age = int(age_str.strip())
        if 16 <= age <= 100:
            return True, age
        return False, None
    except ValueError:
        return False, None


def validate_name(name: str) -> bool:
    """Validate name input (non-empty, reasonable length)."""
    name = name.strip()
    # Allow letters, spaces, apostrophes, and hyphens
    return 2 <= len(name) <= 100 and bool(re.match(r"^[\w\s'\-]+$", name, re.UNICODE))
