"""Core password utility functions."""

import secrets
import string


def check_strength(password: str) -> dict:
    """Check password strength."""
    score = 0
    checks = {
        "length": len(password) >= 8,
        "has_upper": any(c.isupper() for c in password),
        "has_lower": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in string.punctuation for c in password),
    }
    score = sum(checks.values())
    return {
        "score": score,
        "checks": checks,
        "strength": "weak" if score < 3 else "medium" if score < 5 else "strong"
    }


def generate_password(length: int = 16) -> str:
    """Generate secure password."""
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))
