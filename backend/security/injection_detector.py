"""AlgoQX Studio -- Prompt Injection Detector."""

from __future__ import annotations

import re


class InjectionDetector:
    """Detects prompt injection attempts using regex pattern matching."""

    PATTERNS = [
        # Override directives
        r"(?i)\bignore\b.*\b(previous|instructions|above|directives)\b",
        r"(?i)\bdisregard\b.*\b(previous|instructions|above|system)\b",
        r"(?i)\bclear\b.*\b(memory|context|instructions)\b",
        # Roleplay injections
        r"(?i)\byou\b.*\b(now|act as|pretend to be|assume the role of)\b",
        r"(?i)\bnew\b.*\b(persona|instructions|rules|identity)\b",
        # System prompt leakage attempts
        r"(?i)\breveal\b.*\b(system|instructions|prompt|hidden|secret)\b",
        r"(?i)\bshow\b.*\b(what is above|your prompt|original instructions)\b",
        # SQL Injection patterns (for DB components)
        r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|drop\s+table)",
        # Command execution markers
        r"(?i)(rm\s+-rf|format\s+c:|sudo\s+|chmod\s+\+x)",
    ]

    def detect(self, text: str) -> dict:
        """Scan input string against prompt injection signatures.

        Returns:
            Dict containing detected boolean status, confidence score,
            matched pattern list, and threat severity classification.
        """
        if not text:
            return {"detected": False, "confidence": 0.0, "patterns": [], "severity": "low"}

        matched_patterns = []
        for pat in self.PATTERNS:
            match = re.search(pat, text)
            if match:
                matched_patterns.append(match.group(0))

        detected = len(matched_patterns) > 0
        confidence = min(0.95, len(matched_patterns) * 0.45) if detected else 0.0
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
