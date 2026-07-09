"""AlgoQX Studio -- Observability Service.

Provides request tracing, timeline generation, and metric collection
for full pipeline observability.
"""

from __future__ import annotations

import datetime
import time
import uuid
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import RequestLog


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return f"trace-{uuid.uuid4().hex[:16]}"


class RequestTracer:
    """Traces a request through the pipeline, recording steps and metrics."""

    def __init__(self, module: str, trace_id: str | None = None):
        self.trace_id = trace_id or generate_trace_id()
        self.module = module
        self.steps: list[dict[str, Any]] = []
        self._start_time = time.perf_counter()
        self._step_start: float | None = None

    def start_step(self, step_name: str, step_type: str, input_data: Any = None) -> None:
        """Mark the beginning of a pipeline step."""
        self._step_start = time.perf_counter()
        self.steps.append({
            "step_name": step_name,
            "step_type": step_type,
            "input_data": _safe_truncate(input_data),
            "output_data": None,
            "tokens": 0,
            "latency_ms": 0.0,
            "cost_usd": 0.0,
            "metadata": {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

    def end_step(
        self,
        output_data: Any = None,
        tokens: int = 0,
        cost_usd: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark the end of the current pipeline step."""
        if self.steps and self._step_start is not None:
            elapsed = (time.perf_counter() - self._step_start) * 1000
            step = self.steps[-1]
            step["output_data"] = _safe_truncate(output_data)
            step["tokens"] = tokens
            step["latency_ms"] = round(elapsed, 2)
            step["cost_usd"] = cost_usd
            step["metadata"] = metadata or {}
            self._step_start = None

    @property
    def total_tokens(self) -> int:
        return sum(s.get("tokens", 0) for s in self.steps)

    @property
    def total_cost(self) -> float:
        return sum(s.get("cost_usd", 0.0) for s in self.steps)

    @property
    def total_latency_ms(self) -> float:
        return round((time.perf_counter() - self._start_time) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        """Export trace data as a dictionary."""
        return {
            "trace_id": self.trace_id,
            "module": self.module,
            "steps": self.steps,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "total_latency_ms": self.total_latency_ms,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


async def log_request(
    db: AsyncSession,
    trace_id: str,
    module: str,
    model: str,
    input_text: str = "",
    output_text: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: float = 0.0,
    cost_usd: float = 0.0,
    prompt_style: str | None = None,
    status: str = "success",
    error_message: str | None = None,
    metadata: dict | None = None,
) -> RequestLog:
    """Persist a request log entry to the database."""
    log = RequestLog(
        trace_id=trace_id,
        module=module,
        model=model,
        prompt_style=prompt_style,
        input_text=input_text[:2000] if input_text else "",
        output_text=output_text[:2000] if output_text else "",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        status=status,
        error_message=error_message,
        metadata_json=metadata,
    )
    db.add(log)
    await db.flush()
    return log


async def get_analytics_summary(db: AsyncSession) -> dict[str, Any]:
    """Compute aggregated analytics from request logs."""
    # Total requests
    total_q = await db.execute(select(func.count(RequestLog.id)))
    total_requests = total_q.scalar() or 0

    if total_requests == 0:
        return {
            "total_requests": 0,
            "avg_latency_ms": 0.0,
            "avg_cost_usd": 0.0,
            "avg_tokens": 0.0,
            "total_cost_usd": 0.0,
            "model_usage": {},
            "prompt_style_usage": {},
            "module_usage": {},
            "security_threats": 0,
            "hallucination_rate": 0.0,
            "requests_over_time": [],
            "cost_over_time": [],
        }

    # Averages
    avg_lat = await db.execute(select(func.avg(RequestLog.latency_ms)))
    avg_cost = await db.execute(select(func.avg(RequestLog.cost_usd)))
    avg_tok = await db.execute(select(func.avg(RequestLog.total_tokens)))
    total_cost = await db.execute(select(func.sum(RequestLog.cost_usd)))

    # Model usage
    model_q = await db.execute(
        select(RequestLog.model, func.count(RequestLog.id))
        .group_by(RequestLog.model)
    )
    model_usage = {row[0]: row[1] for row in model_q.all()}

    # Prompt style usage
    style_q = await db.execute(
        select(RequestLog.prompt_style, func.count(RequestLog.id))
        .where(RequestLog.prompt_style.isnot(None))
        .group_by(RequestLog.prompt_style)
    )
    style_usage = {row[0]: row[1] for row in style_q.all()}

    # Module usage
    mod_q = await db.execute(
        select(RequestLog.module, func.count(RequestLog.id))
        .group_by(RequestLog.module)
    )
    module_usage = {row[0]: row[1] for row in mod_q.all()}

    # Security threats count
    from backend.database.models import SecurityEvent
    sec_q = await db.execute(select(func.count(SecurityEvent.id)))
    security_threats = sec_q.scalar() or 0

    # Populate time series data from actual requests
    requests_over_time = await _get_requests_over_time(db)
    cost_over_time = await _get_cost_over_time(db)

    return {
        "total_requests": total_requests,
        "avg_latency_ms": round(avg_lat.scalar() or 0, 2),
        "avg_cost_usd": round(avg_cost.scalar() or 0, 6),
        "avg_tokens": round(avg_tok.scalar() or 0, 1),
        "total_cost_usd": round(total_cost.scalar() or 0, 6),
        "model_usage": model_usage,
        "prompt_style_usage": style_usage,
        "module_usage": module_usage,
        "security_threats": security_threats,
        "hallucination_rate": 0.0,
        "requests_over_time": requests_over_time,
        "cost_over_time": cost_over_time,
    }


async def _get_requests_over_time(db: AsyncSession) -> list[dict]:
    """Get request counts aggregated by day for the last 30 days."""
    data = []
    now = datetime.datetime.now()
    
    for i in range(29, -1, -1):
        day = now - datetime.timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        
        q = await db.execute(
            select(func.count(RequestLog.id))
            .where(RequestLog.created_at >= day_start)
            .where(RequestLog.created_at < day_end)
        )
        count = q.scalar() or 0
        data.append({"date": day_str, "requests": count})
    
    return data


async def _get_cost_over_time(db: AsyncSession) -> list[dict]:
    """Get total cost aggregated by day for the last 30 days."""
    data = []
    now = datetime.datetime.now()
    
    for i in range(29, -1, -1):
        day = now - datetime.timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        
        q = await db.execute(
            select(func.sum(RequestLog.cost_usd))
            .where(RequestLog.created_at >= day_start)
            .where(RequestLog.created_at < day_end)
        )
        cost = q.scalar() or 0.0
        data.append({"date": day_str, "cost": round(cost, 6)})
    
    return data


async def get_requests_over_time(db: AsyncSession) -> list[dict]:
    """Get time-series requests count breakdown for trend plotting."""
    return await _get_requests_over_time(db)


def _safe_truncate(data: Any, max_length: int = 500) -> Any:
    """Truncate data for safe storage in traces."""
    if isinstance(data, str) and len(data) > max_length:
        return data[:max_length] + "..."
    return data
