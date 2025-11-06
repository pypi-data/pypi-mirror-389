"""
FastAPI routes for orchestration-level ingestion control
Mount these routes in your existing runners/api.py (see instructions below).
"""

from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

# You likely have a DI or app state; for simplicity we hold a module-level singleton
from market_data_pipeline.context import PipelineContext
from market_data_pipeline.orchestration.ingest_orchestrator import IngestOrchestrator

router = APIRouter(prefix="/runtime/ingest", tags=["Ingestion"])

# Singleton orchestrator (you can swap to proper DI if you have it)
_ORCH: Optional[IngestOrchestrator] = None

def get_orchestrator() -> IngestOrchestrator:
    global _ORCH
    if _ORCH is None:
        _ORCH = IngestOrchestrator(ctx=PipelineContext(tenant_id="default"))
    return _ORCH


class StartRequest(BaseModel):
    provider: Literal["synthetic", "ibkr"]
    symbols: Optional[List[str]] = None
    dry_run: Optional[bool] = None
    override_params: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_status(orch: IngestOrchestrator = Depends(get_orchestrator)) -> Dict[str, Any]:
    return orch.status()


@router.post("/start")
async def start_ingest(req: StartRequest, orch: IngestOrchestrator = Depends(get_orchestrator)) -> Dict[str, Any]:
    return await orch.start(
        provider=req.provider,
        symbols=req.symbols,
        dry_run=req.dry_run,
        override_params=req.override_params,
    )


@router.post("/stop")
async def stop_ingest(orch: IngestOrchestrator = Depends(get_orchestrator)) -> Dict[str, Any]:
    return await orch.stop(reason="operator_request")


@router.post("/reload")
async def reload_configs(orch: IngestOrchestrator = Depends(get_orchestrator)) -> Dict[str, Any]:
    return orch.reload()
