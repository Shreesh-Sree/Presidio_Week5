"""AlgoQX Studio -- Analytics Dashboard API Endpoints."""

import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db
from backend.database.models import RequestLog
from backend.models.schemas import AnalyticsSummary
from backend.services import observability_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Fetch aggregated execution stats, counts, costs, and averages across all modules."""
    try:
        data = await observability_service.get_analytics_summary(db)
        # Time series data comes from observability service
        # No hardcoded mock values
        return AnalyticsSummary(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests-over-time")
async def get_requests_over_time(db: AsyncSession = Depends(get_db)):
    """Get time-series requests count breakdown for trend plotting."""
    try:
        data = await observability_service.get_requests_over_time(db)
        return {"requests": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-usage")
async def get_model_usage(db: AsyncSession = Depends(get_db)):
    """Get percentage breakdown of target model executions."""
    try:
        q = await db.execute(
            select(RequestLog.model, func.count(RequestLog.id))
            .group_by(RequestLog.model)
        )
        res = q.all()
        return {"usage": [{"model": r[0], "count": r[1]} for r in res]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
