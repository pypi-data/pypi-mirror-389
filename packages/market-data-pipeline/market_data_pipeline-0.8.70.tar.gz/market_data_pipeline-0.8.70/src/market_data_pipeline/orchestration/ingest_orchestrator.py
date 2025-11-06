"""
Ingestion Orchestrator
- Wraps existing ProviderRegistry and UnifiedRuntime to start/stop ingestion safely
- Applies high-level policy gates (dry-run, write mode)
- Emits Prometheus metrics (or falls back to no-op if not available)
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Literal

from fastapi import HTTPException

# --- Try to integrate with your existing metrics layer; fallback to prometheus_client ---
try:
    from market_data_pipeline.metrics import registry as _mdp_metrics_registry
    from prometheus_client import Counter, Gauge
except Exception:
    _mdp_metrics_registry = None
    from prometheus_client import Counter, Gauge  # type: ignore

# Existing components
from market_data_pipeline.adapters.providers.provider_registry import ProviderRegistry
from market_data_pipeline.runtime.unified_runtime import UnifiedRuntime
from market_data_pipeline.context import PipelineContext


@dataclass
class OrchestratorConfig:
    providers: Dict[str, Any]
    write_path: Dict[str, Any]
    store_sync: Dict[str, Any]
    guards: Dict[str, Any]


class IngestOrchestrator:
    """
    High-level control for turning ingestion on/off with provider selection and policy gates.
    """

    def __init__(
        self,
        ctx: Optional[PipelineContext] = None,
        config_dir: str = "configs",
        state_dir: str = "state/ingestion",
    ) -> None:
        self.ctx = ctx or PipelineContext(tenant_id="default")
        self.config_dir = Path(config_dir)
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self._load_configs()

        self.runtime = UnifiedRuntime(self.ctx)   # reuses your existing runtime management
        self.provider_registry = ProviderRegistry(self.ctx)

        # Internal run state
        self._active_provider: Optional[str] = None
        self._active_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._dry_run: bool = bool(self.policy.get("write_path", {}).get("dry_run", False))

        # Metrics
        self.ingest_active = Gauge(
            "ingest_active", "Ingestion activity (1=running,0=stopped)", ["provider"]
        )
        self.ingest_starts_total = Counter(
            "ingest_starts_total", "Total ingestion start attempts", ["provider"]
        )
        self.ingest_stops_total = Counter(
            "ingest_stops_total", "Total ingestion stops", ["provider", "reason"]
        )
        self.ingest_errors_total = Counter(
            "ingest_errors_total", "Total ingestion errors", ["provider", "stage"]
        )
        self.ingest_writes_suppressed_total = Counter(
            "ingest_writes_suppressed_total",
            "Suppressed writes due to dry-run or disabled write-path",
            ["reason"]
        )

    # --------------------
    # Config handling
    # --------------------
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        import yaml
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_configs(self) -> None:
        providers_cfg = self._load_yaml(self.config_dir / "data_providers.yaml")
        policy_cfg = self._load_yaml(self.config_dir / "ingestion_policy.yaml")

        # Normalize shapes
        self.providers = providers_cfg.get("providers", {})
        self.policy = {
            "write_path": policy_cfg.get("write_path", {}),
            "store_sync": policy_cfg.get("store_sync", {"mode": "bus"}),
            "guards": policy_cfg.get("guards", {}),
        }

    def reload(self) -> Dict[str, Any]:
        self._load_configs()
        return {
            "providers": list(self.providers.keys()),
            "policy": self.policy,
        }

    # --------------------
    # Public API
    # --------------------
    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "active_provider": self._active_provider,
            "dry_run": self._dry_run,
            "policy": self.policy,
            "providers": self.providers,
        }

    async def start(
        self,
        provider: Literal["synthetic", "ibkr"],
        symbols: Optional[List[str]] = None,
        dry_run: Optional[bool] = None,
        override_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self._running:
            raise HTTPException(status_code=409, detail=f"Ingestion already running (provider={self._active_provider})")

        if provider not in self.providers:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not configured")

        cfg = dict(self.providers.get(provider) or {})
        if symbols is not None:
            cfg["symbols"] = symbols
        if override_params:
            cfg.update(override_params)

        # Guards
        g = self.policy.get("guards", {})
        if g.get("require_provider_enabled", True) and not cfg.get("enabled", False):
            raise HTTPException(status_code=400, detail=f"Provider '{provider}' is disabled by config")
        if g.get("require_symbols_nonempty", True) and not cfg.get("symbols"):
            raise HTTPException(status_code=400, detail="Symbols list must be non-empty")

        # Policy
        write_enabled = bool(self.policy.get("write_path", {}).get("enabled", True))
        self._dry_run = bool(self.policy.get("write_path", {}).get("dry_run", False) if dry_run is None else dry_run)
        if not write_enabled or self._dry_run:
            reason = "dry_run" if self._dry_run else "write_path_disabled"
            self.ingest_writes_suppressed_total.labels(reason=reason).inc()

        # Create source via registry
        try:
            source = self.provider_registry.create(provider_name=provider, params=cfg)
        except Exception as e:
            self.ingest_errors_total.labels(provider=provider, stage="create_source").inc()
            raise HTTPException(status_code=500, detail=f"Failed to create provider source: {e}") from e

        # Register into runtime: runtime will run producers/consumers the way your pipeline expects
        try:
            await self.runtime.register_source(source, dry_run=self._dry_run, store_mode=self.policy.get("store_sync", {}).get("mode", "bus"))
        except Exception as e:
            self.ingest_errors_total.labels(provider=provider, stage="register_runtime").inc()
            raise HTTPException(status_code=500, detail=f"Failed to register source with runtime: {e}") from e

        # Start runtime
        try:
            await self.runtime.start()
        except Exception as e:
            self.ingest_errors_total.labels(provider=provider, stage="runtime_start").inc()
            raise HTTPException(status_code=500, detail=f"Failed to start runtime: {e}") from e

        # Track state
        self._active_provider = provider
        self._running = True
        self.ingest_active.labels(provider=provider).set(1)
        self.ingest_starts_total.labels(provider=provider).inc()

        # Auto-stop support
        max_secs = int(self.policy.get("write_path", {}).get("max_runtime_seconds", 0) or 0)
        if max_secs > 0:
            # fire-and-forget stop after duration
            asyncio.create_task(self._auto_stop_after(max_secs, provider))

        # Persist a tiny state record
        self._persist_state()

        return {"status": "started", "provider": provider, "dry_run": self._dry_run, "store_mode": self.policy.get("store_sync", {}).get("mode", "bus")}

    async def stop(self, reason: str = "operator_request") -> Dict[str, Any]:
        if not self._running:
            return {"status": "idle"}

        provider = self._active_provider or "unknown"
        try:
            await self.runtime.stop()
        except Exception:
            # swallow to ensure we still reset our own state
            self.ingest_errors_total.labels(provider=provider, stage="runtime_stop").inc()

        # Reset
        self._running = False
        self._active_provider = None
        self.ingest_active.labels(provider=provider).set(0)
        self.ingest_stops_total.labels(provider=provider, reason=reason).inc()
        self._persist_state()

        return {"status": "stopped", "reason": reason}

    # --------------------
    # Internals
    # --------------------
    async def _auto_stop_after(self, seconds: int, provider: str) -> None:
        try:
            await asyncio.sleep(seconds)
            # Only stop if still running with same provider
            if self._running and self._active_provider == provider:
                await self.stop(reason="auto_duration_reached")
        except Exception:
            self.ingest_errors_total.labels(provider=provider, stage="auto_stop").inc()

    def _persist_state(self) -> None:
        state_file = self.state_dir / "ingest_state.json"
        payload = self.status()
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception:
            # best-effort only
            pass
