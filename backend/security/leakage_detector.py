"""AlgoQX Studio -- System Prompt Leakage Detector."""

from __future__ import annotations

import re


class LeakageDetector:
    """Detects attempts to leak the system prompt instructions."""

    PATTERNS = [
        # Explicit system prompt dump queries
        r"(?i)\bshow\b.*\b(system\s+prompt|system\s+instructions|system\s+message)\b",
        r"(?i)\breveal\b.*\b(system\s+prompt|system\s+instructions|system\s+message)\b",
        # Verbatim repetition requests
        r"(?i)\brepeat\b.*\b(above|instructions\s+verbatim|initial\s+prompt)\b",
        r"(?i)\bwhat\s+is\s+your\s+system\s+prompt\b",
        r"(?i)\bwrite\b.*\b(system\s+prompt|hidden\s+instruction)\b",
        r"(?i)\boutput\b.*\b(your\s+initial\s+prompt|rules\s+above)\b",
        r"(?i)\bhow\b.*\b(were\s+you\s+programmed|were\s+you\s+configured)\b",
    ]

    def detect(self, text: str) -> dict:
        """Scan input string against system prompt leakage queries.

        Returns:
            Dict containing detected status, confidence score,
            matched patterns list, and severity.
        """
        if not text:
            return {"detected": False, "confidence": 0.0, "patterns": [], "severity": "low"}

        matched_patterns = []
        for pat in self.PATTERNS:
            match = re.search(pat, text)
            if match:
                matched_patterns.append(match.group(0))

        detected = len(matched_patterns) > 0
        confidence = min(0.95, len(matched_patterns) * 0.6) if detected else 0.0
        severity = "low"
        if len(matched_patterns) > 1:
            severity = "high"
        elif len(matched_patterns) == 1:
            severity = "medium"

        return {
            "detected": detected,
            "confidence": round(confidence, 2),
            "patterns": matched_patterns,
            "severity": severity,
        }
