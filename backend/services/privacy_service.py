"""AlgoQX Studio -- PII detection and masking service."""

from __future__ import annotations

import hashlib
import re


class PrivacyService:
    """Detects and masks PII tokens (emails, credit cards, Aadhaar, PAN cards, etc.)."""

    # Regex definitions for major PII types
    PATTERNS = {
        "EMAIL": r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        "API_KEY": r"\b(sk-[a-zA-Z0-9]{20,}|api[_-]key[_-][a-zA-Z0-9]{16,}|AIzaSy[a-zA-Z0-9_-]{33})\b",
        "PASSWORD": r"(?i)\b(password|pwd|secret)\s*[:=]\s*['\"]?([a-zA-Z0-9!@#$%^&*()_+]{6,})['\"]?",
        "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        "AADHAAR": r"\b[2-9]{1}[0-9]{3}\s*[0-9]{4}\s*[0-9]{4}\b",
        "PASSPORT": r"\b[A-Z]{1}[0-9]{7}\b",
    }

    def detect_pii(self, text: str, entity_types: list[str]) -> list[dict]:
        """Scan string and locate PII bounding boxes with confidence estimates."""
        if not text:
            return []

        found_entities = []
        for entity_type in entity_types:
            pattern = self.PATTERNS.get(entity_type)
            if not pattern:
                continue

            for match in re.finditer(pattern, text):
                val = match.group(0)

                # Post-validate credit card via luhn check
                if entity_type == "CREDIT_CARD" and not self._luhn_check(val):
                    continue

                # Parse specific capture offsets for PASSWORD pattern to extract password
                start, end = match.start(), match.end()
                matched_val = val
                if entity_type == "PASSWORD":
                    matched_val = match.group(2)
                    start = match.start(2)
                    end = match.end(2)

                found_entities.append(
                    {
                        "entity_type": entity_type,
                        "value": matched_val,
                        "start": start,
                        "end": end,
                        "confidence": 0.95,
                        "masked_value": "",
                    }
                )

        # Sort entities by start index descending to prevent offset index drifts during masking
        found_entities.sort(key=lambda x: x["start"], reverse=True)
        return found_entities

    def mask_pii(
        self, text: str, entities: list[dict], strategy: str = "redact"
    ) -> str:
        """Replace detected PII spans with designated masking markers."""
        if not text or not entities:
            return text

        masked = text
        for ent in entities:
            start, end = ent["start"], ent["end"]
            original_val = ent["value"]

            # Compute masked value based on selected strategy
            if strategy == "redact":
                m_val = f"[{ent['entity_type']}_REDACTED]"
            elif strategy == "hash":
                h = hashlib.sha256(original_val.encode()).hexdigest()[:8]
                m_val = f"[{ent['entity_type']}_HASH_{h}]"
            elif strategy == "mask":
                if len(original_val) <= 4:
                    m_val = "*" * len(original_val)
                else:
                    m_val = "*" * (len(original_val) - 4) + original_val[-4:]
            else:
                m_val = f"[{ent['entity_type']}]"

            ent["masked_value"] = m_val
            masked = masked[:start] + m_val + masked[end:]

        return masked

    def _luhn_check(self, card_num: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        digits = [int(d) for d in card_num if d.isdigit()]
        if len(digits) < 13 or len(digits) > 16:
            return False
        checksum = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = digit * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += digit
        return checksum % 10 == 0

    def get_explanation(self) -> str:
        """Provide detailed technical explanation of why PII filtering is critical."""
        return (
            "Sending Personally Identifiable Information (PII) or system secrets to cloud-hosted LLM endpoints "
            "presents serious security, compliance, and privacy risks.\n\n"
            "1. Data Leakage: Once tokens are transmitted to an external API, they can be saved in inference logs "
            "or cached inside the model hosting platform.\n"
            "2. Compliance Violations: Standard data regulations (GDPR, HIPAA, SOC2) strictly forbid passing "
            "raw identity numbers (SSN, Aadhaar, PAN) or bank credentials to unverified sub-processors without consent.\n"
            "3. Training Ingestion: Public LLM creators may utilize user query prompt logs in future weight fine-tuning updates, "
            "creating risks of the model reproducing private data in outputs to other users."
        )
