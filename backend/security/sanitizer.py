"""AlgoQX Studio -- Prompt Sanitizer."""

from __future__ import annotations


class PromptSanitizer:
    """Sanitizes text by removing or wrapping threat phrases."""

    def sanitize(self, text: str, threat_patterns: list[str]) -> str:
        """Strip matched threat patterns and return safe text."""
        if not text or not threat_patterns:
            return text

        sanitized = text
        for pattern in threat_patterns:
            # Case-insensitive replace
            import re
            try:
                # Compile to ensure clean regex replacement
                rx = re.compile(re.escape(pattern), re.IGNORECASE)
                sanitized = rx.sub("[REMOVED_SECURITY_RISK]", sanitized)
            except Exception:
                # Fallback to direct replacement
                sanitized = sanitized.replace(pattern, "[REMOVED_SECURITY_RISK]")

        return sanitized
