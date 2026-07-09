"""AlgoQX Studio -- Observability Traces API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db
from backend.database.models import RequestLog

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/traces")
async def list_traces(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetch recent execution traces and logged request metadata."""
    try:
        q = select(RequestLog).order_by(RequestLog.created_at.desc()).limit(limit)
        res = await db.execute(q)
        logs = res.scalars().all()

        return {
            "traces": [
                {
                    "id": log.id,
                    "trace_id": log.trace_id,
                    "module": log.module,
                    "model": log.model,
                    "prompt_style": log.prompt_style,
                    "input_tokens": log.input_tokens,
                    "output_tokens": log.output_tokens,
                    "total_tokens": log.total_tokens,
                    "latency_ms": log.latency_ms,
                    "cost_usd": log.cost_usd,
                    "status": log.status,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces/{trace_id}")
async def get_trace_details(trace_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch granular steps and timeline metrics for a specific transaction trace."""
    try:
        q = select(RequestLog).where(RequestLog.trace_id == trace_id)
        res = await db.execute(q)
        logs = res.scalars().all()

        if not logs:
            raise HTTPException(
                status_code=404, detail=f"Trace with ID {trace_id} not found."
            )

        # Build simulated steps based on the logs for this trace ID
        steps = []
        total_tokens = 0
        total_cost = 0.0
        total_latency = 0.0

        for i, log in enumerate(logs):
            total_tokens += log.total_tokens
            total_cost += log.cost_usd
            total_latency += log.latency_ms

            # Reconstruct pipeline steps
            steps.append(
                {
                    "step_name": f"{log.module.upper()}_CALL_{i+1}",
                    "step_type": "llm_completion",
                    "input_data": log.input_text,
                    "output_data": log.output_text,
                    "tokens": log.total_tokens,
                    "latency_ms": log.latency_ms,
                    "cost_usd": log.cost_usd,
                    "metadata": log.metadata_json or {},
                    "timestamp": log.created_at.isoformat(),
                }
            )

        return {
            "trace_id": trace_id,
            "module": logs[0].module,
            "steps": steps,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_latency_ms": total_latency,
            "created_at": logs[0].created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/replay/{trace_id}")
async def get_replay_data(trace_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full request inputs and parameters to replay the transaction execution."""
    try:
        q = select(RequestLog).where(RequestLog.trace_id == trace_id)
        res = await db.execute(q)
        log = res.scalars().first()

        if not log:
            raise HTTPException(
                status_code=404, detail="Trace not found."
            )

        return {
            "trace_id": trace_id,
            "module": log.module,
            "model": log.model,
            "prompt_style": log.prompt_style,
            "input_text": log.input_text,
            "metadata": log.metadata_json or {},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
