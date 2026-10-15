import re

# Compiled regex patterns for detecting secrets
PATTERNS = [
    # OpenAI API Keys
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "sk-***[REDACTED_API_KEY]***"),
    # Google AI / Gemini API Keys
    (re.compile(r"AIzaSy[a-zA-Z0-9_\-]{33}", re.IGNORECASE), "AIzaSy***[REDACTED_GEMINI_KEY]***"),
    # General API Keys & Passwords in key-value formats
    (
        re.compile(
            r'''(?i)(password|passwd|api_key|apikey|secret|auth_token|access_token)\s*[:=]\s*['"]?([a-zA-Z0-9_\-\.~!@#$%^&*()+=]{6,})['"]?'''
        ),
        r"\1=***[REDACTED_SECRET]***",
    ),
    # Bearer Tokens
    (re.compile(r'''(?i)bearer\s+[a-zA-Z0-9_\-\.~+/]+=*''', re.IGNORECASE), "Bearer ***[REDACTED_BEARER_TOKEN]***"),
]


def redact_sensitive_data(text: str) -> str:
    """Sanitize and redact API keys, passwords, and tokens from strings before persisting to the graph."""
    if not text or not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def contains_sensitive_data(text: str) -> bool:
    """Check if text contains unredacted secrets."""
    if not text or not isinstance(text, str):
        return False
    return any(pattern.search(text) for pattern, _ in PATTERNS)
