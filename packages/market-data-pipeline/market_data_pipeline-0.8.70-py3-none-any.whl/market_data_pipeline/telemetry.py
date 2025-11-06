"""
Telemetry and metrics collection for market data pipeline.

This module provides Prometheus metrics, heartbeat tracking, and observability
features for the job execution system.
"""

import logging
import time
from typing import Optional, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)


class PipelineTelemetry:
    """Telemetry collector for pipeline metrics and heartbeats."""
    
    def __init__(self, port: int = 9090, registry: Optional[CollectorRegistry] = None):
        """
        Initialize telemetry system.
        
        Args:
            port: Port for Prometheus metrics server
            registry: Optional custom Prometheus registry
        """
        self.port = port
        self.registry = registry or CollectorRegistry()
        self._server_started = False
        
        # Initialize metrics
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Job execution metrics
        self.job_runs_total = Counter(
            'pipeline_job_runs_total',
            'Total number of job runs',
            ['job_name', 'status'],
            registry=self.registry
        )
        
        self.job_duration_seconds = Histogram(
            'pipeline_job_duration_seconds',
            'Duration of job execution in seconds',
            ['job_name', 'mode'],
            registry=self.registry
        )
        
        # Data processing metrics
        self.rows_written_total = Counter(
            'pipeline_rows_written_total',
            'Total number of rows written to storage',
            ['job_name', 'provider'],
            registry=self.registry
        )
        
        self.batches_processed_total = Counter(
            'pipeline_batches_total',
            'Total number of batches processed',
            ['job_name', 'provider'],
            registry=self.registry
        )
        
        # Provider metrics
        self.provider_requests_total = Counter(
            'pipeline_provider_requests_total',
            'Total number of provider requests',
            ['provider', 'status'],
            registry=self.registry
        )
        
        self.provider_rate_limit_violations = Counter(
            'pipeline_provider_rate_limit_violations_total',
            'Total number of rate limit violations',
            ['provider'],
            registry=self.registry
        )
        
        # Active job tracking
        self.active_jobs = Gauge(
            'pipeline_active_jobs',
            'Number of currently active jobs',
            ['job_name'],
            registry=self.registry
        )
        
        # Storage metrics
        self.storage_write_duration_seconds = Histogram(
            'pipeline_storage_write_duration_seconds',
            'Duration of storage write operations',
            ['storage_type'],
            registry=self.registry
        )
        
        self.storage_write_errors_total = Counter(
            'pipeline_storage_write_errors_total',
            'Total number of storage write errors',
            ['storage_type', 'error_type'],
            registry=self.registry
        )
    
    def start_server(self):
        """Start the Prometheus metrics server."""
        if not self._server_started:
            try:
                start_http_server(self.port, registry=self.registry)
                self._server_started = True
                logger.info(f"Prometheus metrics server started on port {self.port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")
                raise
    
    def record_job_start(self, job_name: str, mode: str):
        """Record job start event."""
        self.active_jobs.labels(job_name=job_name).inc()
        logger.debug(f"Recorded job start: {job_name} ({mode})")
    
    def record_job_completion(self, job_name: str, mode: str, status: str, duration: float):
        """Record job completion event."""
        self.job_runs_total.labels(job_name=job_name, status=status).inc()
        self.job_duration_seconds.labels(job_name=job_name, mode=mode).observe(duration)
        self.active_jobs.labels(job_name=job_name).dec()
        logger.debug(f"Recorded job completion: {job_name} ({status}) in {duration:.2f}s")
    
    def record_rows_written(self, job_name: str, provider: str, count: int):
        """Record rows written to storage."""
        self.rows_written_total.labels(job_name=job_name, provider=provider).inc(count)
        logger.debug(f"Recorded {count} rows written for {job_name}")
    
    def record_batch_processed(self, job_name: str, provider: str, batch_size: int):
        """Record batch processing."""
        self.batches_processed_total.labels(job_name=job_name, provider=provider).inc()
        logger.debug(f"Recorded batch processed for {job_name}: {batch_size} rows")
    
    def record_provider_request(self, provider: str, status: str):
        """Record provider request."""
        self.provider_requests_total.labels(provider=provider, status=status).inc()
        logger.debug(f"Recorded provider request: {provider} ({status})")
    
    def record_rate_limit_violation(self, provider: str):
        """Record rate limit violation."""
        self.provider_rate_limit_violations.labels(provider=provider).inc()
        logger.warning(f"Rate limit violation recorded for {provider}")
    
    def record_storage_write(self, storage_type: str, duration: float, success: bool, error_type: str = None):
        """Record storage write operation."""
        self.storage_write_duration_seconds.labels(storage_type=storage_type).observe(duration)
        
        if not success:
            self.storage_write_errors_total.labels(
                storage_type=storage_type, 
                error_type=error_type or "unknown"
            ).inc()
            logger.warning(f"Storage write error recorded: {storage_type} ({error_type})")
        else:
            logger.debug(f"Storage write completed: {storage_type} in {duration:.2f}s")


# Global telemetry instance
_telemetry: Optional[PipelineTelemetry] = None


def get_telemetry() -> Optional[PipelineTelemetry]:
    """Get the global telemetry instance."""
    return _telemetry


def init_telemetry(port: int = 9090, registry: Optional[CollectorRegistry] = None) -> PipelineTelemetry:
    """Initialize global telemetry instance."""
    global _telemetry
    _telemetry = PipelineTelemetry(port=port, registry=registry)
    return _telemetry


def record_job_metrics(job_name: str, mode: str, status: str, duration: float, 
                      rows_written: int = 0, provider: str = None):
    """Record job execution metrics."""
    if _telemetry:
        _telemetry.record_job_completion(job_name, mode, status, duration)
        if rows_written > 0 and provider:
            _telemetry.record_rows_written(job_name, provider, rows_written)


def record_provider_metrics(provider: str, status: str, rate_limit_violation: bool = False):
    """Record provider interaction metrics."""
    if _telemetry:
        _telemetry.record_provider_request(provider, status)
        if rate_limit_violation:
            _telemetry.record_rate_limit_violation(provider)


def record_storage_metrics(storage_type: str, duration: float, success: bool, error_type: str = None):
    """Record storage operation metrics."""
    if _telemetry:
        _telemetry.record_storage_write(storage_type, duration, success, error_type)
