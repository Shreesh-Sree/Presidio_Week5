"""AlgoQX Studio -- Privacy Center API Endpoints."""

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    PrivacyScanRequest,
    PrivacyScanResponse,
    PIIEntity,
)
from backend.services.privacy_service import PrivacyService

router = APIRouter(prefix="/privacy", tags=["Privacy Center"])
service = PrivacyService()

ENTITY_DESCRIPTIONS = {
    "EMAIL": "Standard email address formatting patterns.",
    "PHONE": "International and regional mobile or phone digit strings.",
    "CREDIT_CARD": "Luhn check verified credit/debit card numbers.",
    "API_KEY": "Standard cloud API bearer credentials (e.g. OpenAI sk-, AWS tokens).",
    "PASSWORD": "Key-value passwords (e.g. password=...) contained in strings.",
    "PAN": "Indian Permanent Account Number format.",
    "AADHAAR": "12-digit Indian Aadhaar government UID identification.",
    "PASSPORT": "Indian government passport serial alphanumeric sequences.",
}


@router.post("/scan", response_model=PrivacyScanResponse)
async def scan_privacy(request: PrivacyScanRequest):
    """Scan and scrub text content of PII entities based on strategy choice."""
    try:
        entities_data = service.detect_pii(request.text, request.entity_types)

        # Generate entities list for response before we mask them
        # (offset indexes are sorted descending to make masking safe, but let's reverse them back for normal viewing)
        entities_res = []
        for e in reversed(entities_data):
            entities_res.append(
                PIIEntity(
                    entity_type=e["entity_type"],
                    value=e["value"],
                    start=e["start"],
                    end=e["end"],
                    confidence=e["confidence"],
                    masked_value="",
                )
            )

        # Apply masking
        masked_text = service.mask_pii(
            request.text, entities_data, request.mask_strategy
        )

        # Add masked values to the entities list
        for e_res, e_data in zip(entities_res, reversed(entities_data)):
            e_res.masked_value = e_data["masked_value"]

        explanation = service.get_explanation()

        return PrivacyScanResponse(
            original_text=request.text,
            masked_text=masked_text,
            entities=entities_res,
            entity_count=len(entities_res),
            explanation=explanation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explanation")
async def get_privacy_explanation():
    """Get conceptual details on LLM PII vulnerabilities."""
    return {"explanation": service.get_explanation()}


@router.get("/entity-types")
async def get_entity_types():
    """Get active dictionary of supported sensitive fields."""
    return {"entity_types": ENTITY_DESCRIPTIONS}


@router.post("/demo", response_model=PrivacyScanResponse)
async def privacy_demo(request: PrivacyScanRequest):
    """Run privacy scan on user-provided text."""
    return await scan_privacy(request)
