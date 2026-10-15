import re
from typing import Any

# Allowed alphanumeric and underscore characters for labels and property keys
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def sanitize_identifier(identifier: str) -> str:
    """Validate that Cypher identifiers (labels, relationship types) contain only safe characters."""
    if not SAFE_IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(f"Unsafe Cypher identifier detected: '{identifier}'")
    return identifier


def validate_query_parameters(params: dict[str, Any]) -> None:
    """Ensure all parameters passed to Cypher queries are properly typed and bounded."""
    for key, value in params.items():
        if not SAFE_IDENTIFIER_PATTERN.match(key):
            raise ValueError(f"Invalid parameter key: '{key}'")
        if isinstance(value, str) and len(value) > 20000:
            raise ValueError(f"Parameter '{key}' exceeds maximum allowable size (20,000 chars)")
