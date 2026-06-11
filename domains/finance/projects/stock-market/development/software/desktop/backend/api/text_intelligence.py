"""
Text Intelligence API — Layer 6 (text sources).

Extract market signals from FOMC statements, earnings transcripts, or arbitrary
user-pasted text, and optionally apply them to the prediction engine. Uses the
active local LLM when present, otherwise a transparent keyword heuristic.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeTextRequest(BaseModel):
    text: str
    source_type: str = "generic"   # generic | fomc | earnings
    title: str = ""
    apply: bool = False
    expires_days: int = 14


@router.post("/analyze")
def analyze_text(req: AnalyzeTextRequest):
    """Extract (and optionally apply) market signals from financial text."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=422, detail="text cannot be empty")
    try:
        from backend.models.text_signal_extractor import (
            extract_signals_from_text, apply_text_signals,
        )
        result = extract_signals_from_text(req.text, req.source_type, req.title)
        applied = 0
        if req.apply and result["signals"]:
            applied = apply_text_signals(
                result["signals"], result["source_type"], req.title, req.expires_days
            )
        return {**result, "signal_count": len(result["signals"]), "applied": applied}
    except Exception as e:
        logger.error("analyze_text failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
