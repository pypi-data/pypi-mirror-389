"""
Phase 5 – Replay API Endpoints

REST API for controlling tick replay jobs.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/replay", tags=["Replay"])

# Global replayer instance (initialized in main app)
_replayer = None


def set_replayer(replayer):
    """Set global replayer instance."""
    global _replayer
    _replayer = replayer


def get_replayer():
    """Dependency to get replayer instance."""
    if _replayer is None:
        raise HTTPException(status_code=503, detail="Replayer not initialized")
    return _replayer


class ReplayRequestModel(BaseModel):
    """Request to start a tick replay."""

    provider: str = Field(..., description="Provider name (e.g., 'ibkr')")
    symbols: List[str] = Field(..., description="List of symbols to replay")
    start: datetime = Field(..., description="Start timestamp (UTC)")
    end: datetime = Field(..., description="End timestamp (UTC)")
    speed: float = Field(
        1.0, description="Replay speed (1.0=real-time, 0=burst)", ge=0
    )


class ReplayStatusModel(BaseModel):
    """Status of a replay job."""

    run_id: int
    job_name: str
    provider: str
    status: str
    symbols: List[str]
    rows_written: int
    min_ts: datetime | None
    max_ts: datetime | None
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    metadata: dict | None


@router.post("/ticks", response_model=ReplayStatusModel, status_code=202)
async def start_tick_replay(
    req: ReplayRequestModel, replayer=Depends(get_replayer)
):
    """
    Start a new tick replay job.

    Replays historical ticks from tick_data table back onto the event bus
    at configurable speed. Downstream consumers process replayed ticks
    just like live ticks.

    Args:
        req: Replay request parameters

    Returns:
        Initial job status with run_id for tracking

    Example:
        POST /v1/replay/ticks
        {
            "provider": "ibkr",
            "symbols": ["NVDA", "AAPL"],
            "start": "2025-11-03T14:00:00Z",
            "end": "2025-11-03T15:00:00Z",
            "speed": 10.0
        }
    """
    try:
        from market_data_pipeline.replay import TickReplayRequest

        replay_req = TickReplayRequest(
            provider=req.provider,
            symbols=req.symbols,
            start=req.start,
            end=req.end,
            speed=req.speed,
        )

        run_id = await replayer.start_replay(replay_req)
        status = await replayer.get_status(run_id)

        return ReplayStatusModel(**status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticks/{run_id}", response_model=ReplayStatusModel)
async def get_replay_status(run_id: int, replayer=Depends(get_replayer)):
    """
    Get status of a replay job.

    Args:
        run_id: Job run ID

    Returns:
        Current job status

    Example:
        GET /v1/replay/ticks/42
    """
    try:
        status = await replayer.get_status(run_id)
        return ReplayStatusModel(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticks", response_model=List[ReplayStatusModel])
async def list_recent_replays(
    limit: int = 20, replayer=Depends(get_replayer)
):
    """
    List recent replay jobs.

    Args:
        limit: Maximum number of jobs to return (default 20)

    Returns:
        List of recent replay job statuses

    Example:
        GET /v1/replay/ticks?limit=10
    """
    # This would need a new method in TickReplayer
    # For now, return empty list as a placeholder
    # TODO: Implement list_replays() in TickReplayer
    return []

