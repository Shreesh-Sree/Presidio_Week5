"""AlgoQX Studio -- Jailbreak Detector."""

from __future__ import annotations

import re


class JailbreakDetector:
    """Detects known LLM jailbreak attempts (DAN, Developer Mode, etc.)."""

    PATTERNS = [
        # Famous jailbreak persona triggers
        r"(?i)\b(dan|aim|jailbreak|jailbroken)\b",
        r"(?i)\bdo\s+anything\s+now\b",
        # Developer mode bypasses
        r"(?i)\b(developer\s+mode|devmode|rules\s+bypass)\b",
        r"(?i)\b(hypothetical\s+scenario|strictly\s+hypothetical)\b",
        # Anarchist cookbook/unsafe prompts
        r"(?i)\b(how\s+to\s+make\s+a\s+bomb|how\s+to\s+hack|steal\s+credit\b)",
        r"(?i)\b(bypass\s+safety|disable\s+filters|override\s+filters)\b",
        # Adversarial suffix/prefix tokens
        r"(?i)(refusal\s+is\s+unacceptable|you\s+must\s+answer|comply\s+verbatim)",
    ]

    def detect(self, text: str) -> dict:
        """Scan input string against jailbreak signatures.

        Returns:
            Dict containing detected status, confidence score,
            matched pattern list, and severity.
        """
        if not text:
            return {"detected": False, "confidence": 0.0, "patterns": [], "severity": "low"}

        matched_patterns = []
        for pat in self.PATTERNS:
            match = re.search(pat, text)
            if match:
                matched_patterns.append(match.group(0))

        detected = len(matched_patterns) > 0
        confidence = min(0.98, len(matched_patterns) * 0.5) if detected else 0.0
        severity = "low"
        if len(matched_patterns) > 1:
            severity = "critical"
        elif len(matched_patterns) == 1:
            severity = "high"

        return {
            "detected": detected,
            "confidence": round(confidence, 2),
            "patterns": matched_patterns,
            "severity": severity,
        }
