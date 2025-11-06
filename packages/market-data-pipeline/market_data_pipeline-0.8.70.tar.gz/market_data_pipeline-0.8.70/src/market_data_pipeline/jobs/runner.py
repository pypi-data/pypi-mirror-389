"""
Job runner for executing market data collection jobs.

This module provides the core job execution logic for both live and backfill
jobs using the new config system from market_data_core. Includes lifecycle
tracking, telemetry, and store integration.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Iterable, Dict, Any
from pathlib import Path

from market_data_core import load_config, ProviderRegistry, Bar

logger = logging.getLogger(__name__)


class JobExecutionError(Exception):
    """Raised when job execution fails."""
    pass


@contextmanager
def tracked_run(cfg, job_name: str, dry_run: bool = False):
    """
    Context manager for tracking job execution lifecycle.
    
    Args:
        cfg: Application configuration
        job_name: Name of the job being executed
        dry_run: If True, skip actual execution and storage writes
    
    Yields:
        tuple: (tracker, run_id) for progress updates
    """
    tracker = None
    run_id = None
    
    try:
        # Initialize job tracking if store is available
        if not dry_run and "primary" in cfg.storage.root:
            try:
                from market_data_store.job_tracking import JobRunTracker
                tracker = JobRunTracker(cfg.storage.root["primary"].uri)
                run_id = tracker.start_run(
                    job_name=job_name,
                    config_fingerprint=cfg.fingerprint,
                    profile=cfg.profile
                )
                logger.info(f"Started job run {run_id} for '{job_name}'")
            except ImportError:
                logger.warning("market_data_store not available, skipping job tracking")
            except Exception as e:
                logger.warning(f"Failed to initialize job tracking: {e}")
        
        yield tracker, run_id
        
        # Mark as successful completion
        if tracker and run_id:
            tracker.complete_run(run_id, status="success")
            logger.info(f"Completed job run {run_id} successfully")
            
    except Exception as ex:
        # Mark as failed completion
        if tracker and run_id:
            tracker.complete_run(run_id, status="failure", error=str(ex))
            logger.error(f"Job run {run_id} failed: {ex}")
        raise


def run_job(config_path: str, job_name: str, profile: Optional[str] = None, dry_run: bool = False) -> None:
    """
    Execute a market data collection job.
    
    Args:
        config_path: Path to the configuration file
        job_name: Name of the job to execute
        profile: Optional profile override (dev/staging/prod)
        dry_run: If True, skip actual execution and storage writes
    
    Raises:
        JobExecutionError: If job execution fails
    """
    try:
        # Load configuration with profile overlay
        logger.info(f"Loading config from {config_path} with profile {profile or 'default'}")
        cfg = load_config(config_path, profile_override=profile)
        
        # Validate job exists
        if job_name not in cfg.jobs.root:
            raise JobExecutionError(f"Job '{job_name}' not found in configuration")
        
        job = cfg.jobs.root[job_name]
        logger.info(f"Executing job '{job_name}' in {job.mode} mode (dry_run={dry_run})")
        
        # Get dataset configuration
        if job.dataset not in cfg.datasets.root:
            raise JobExecutionError(f"Dataset '{job.dataset}' not found for job '{job_name}'")
        
        dataset = cfg.datasets.root[job.dataset]
        logger.info(f"Using dataset '{job.dataset}' with provider '{dataset.provider}'")
        
        # Resolve provider
        provider_registry = ProviderRegistry(cfg.providers)
        provider = provider_registry.resolve(dataset.provider)
        logger.info(f"Resolved provider: {provider.name}")
        
        # Execute job with lifecycle tracking
        with tracked_run(cfg, job_name, dry_run) as (tracker, run_id):
            # Execute job based on mode
            if job.mode == "backfill":
                rows = _execute_backfill_job(provider, dataset, job, tracker, run_id)
            else:
                rows = _execute_live_job(provider, dataset, job, tracker, run_id)
            
            # Write results to storage (unless dry run)
            if not dry_run:
                _write_results(cfg, rows, job_name)
            else:
                logger.info("Dry run mode: skipping storage writes")
        
        logger.info(f"Job '{job_name}' completed successfully")
        
    except Exception as e:
        logger.error(f"Job '{job_name}' failed: {e}")
        raise JobExecutionError(f"Job execution failed: {e}") from e


def _execute_backfill_job(provider, dataset, job, tracker=None, run_id=None) -> Iterable[Bar]:
    """Execute a backfill job with progress tracking."""
    logger.info("Executing backfill job")
    
    if not job.backfill:
        raise JobExecutionError("Backfill job requires backfill specification")
    
    # Execute backfill through provider
    rows = provider.backfill(dataset, job)
    
    # Count rows and update progress
    row_count = 0
    batch_count = 0
    start_time = time.time()
    
    for row in rows:
        row_count += 1
        
        # Update progress every 1000 rows
        if row_count % 1000 == 0:
            batch_count += 1
            logger.info(f"Processed {row_count} rows in {batch_count} batches...")
            
            # Update tracker with progress
            if tracker and run_id:
                try:
                    tracker.update_progress(
                        run_id, 
                        rows_processed=row_count,
                        batches_processed=batch_count,
                        duration_seconds=time.time() - start_time
                    )
                except Exception as e:
                    logger.warning(f"Failed to update progress: {e}")
    
    duration = time.time() - start_time
    logger.info(f"Backfill completed with {row_count} rows in {duration:.2f}s")
    return rows


def _execute_live_job(provider, dataset, job, tracker=None, run_id=None) -> Iterable[Bar]:
    """Execute a live job with progress tracking."""
    logger.info("Executing live job")
    
    # Execute live fetch through provider
    rows = provider.fetch_live(dataset, job)
    
    # Count rows and update progress
    row_count = 0
    start_time = time.time()
    
    for row in rows:
        row_count += 1
    
    duration = time.time() - start_time
    logger.info(f"Live job completed with {row_count} rows in {duration:.2f}s")
    
    # Update tracker with final progress
    if tracker and run_id:
        try:
            tracker.update_progress(
                run_id,
                rows_processed=row_count,
                batches_processed=1,
                duration_seconds=duration
            )
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")
    
    return rows


def _write_results(cfg, rows: Iterable[Bar], job_name: str) -> None:
    """Write job results to configured storage targets."""
    if not cfg.features.write_enabled:
        logger.info("Write disabled by feature flag, skipping storage")
        return
    
    # Write to primary storage
    if "primary" in cfg.storage.root:
        _write_to_primary_storage(cfg.storage.root["primary"], rows)
    
    # Write to lake export if enabled
    if cfg.features.export_enabled and "lake_export" in cfg.storage.root:
        _write_to_lake_export(cfg.storage.root["lake_export"], rows)


def _write_to_primary_storage(storage_config, rows: Iterable[Bar]) -> None:
    """Write bars to primary storage (TimescaleDB)."""
    try:
        # Import here to avoid circular imports
        from market_data_store.client import StoreClient
        
        logger.info("Writing to primary storage")
        client = StoreClient(storage_config.uri)
        client.write_bars(rows, batch_size=storage_config.write.batch_size)
        logger.info("Primary storage write completed")
        
    except ImportError:
        logger.warning("market_data_store not available, skipping primary storage write")
    except Exception as e:
        logger.error(f"Primary storage write failed: {e}")
        raise


def _write_to_lake_export(storage_config, rows: Iterable[Bar]) -> None:
    """Write bars to lake export (S3/Parquet)."""
    try:
        # Import here to avoid circular imports
        from market_data_store.client import LakeClient
        
        logger.info("Writing to lake export")
        client = LakeClient(storage_config)
        client.export(rows)
        logger.info("Lake export completed")
        
    except ImportError:
        logger.warning("market_data_store not available, skipping lake export")
    except Exception as e:
        logger.error(f"Lake export failed: {e}")
        raise
