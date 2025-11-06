from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

from market_data_pipeline.runtime.unified_runtime import UnifiedRuntime
from market_data_pipeline.settings.runtime_unified import (
    RuntimeModeEnum,
    UnifiedRuntimeSettings,
)
from market_data_pipeline.jobs.runner import run_job, JobExecutionError


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mdp",
        description="Market Data Pipeline CLI (Unified Runtime)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # Legacy unified runtime command
    run = sub.add_parser("run", help="Run a pipeline/runtime job.")
    run.add_argument("--mode", choices=[m.value for m in RuntimeModeEnum], required=False)
    run.add_argument("--config", type=str, required=True, help="Path to YAML/JSON config")
    run.add_argument("--job", type=str, default="default", help="Job name (for DAG)")

    # New job execution command
    job_run = sub.add_parser("job", help="Execute a market data collection job using new config system.")
    job_run.add_argument("--config", type=str, required=True, help="Path to configuration file")
    job_run.add_argument("--job", type=str, required=True, help="Job name to execute")
    job_run.add_argument("--profile", type=str, help="Profile override (dev/staging/prod)")
    job_run.add_argument("--dry-run", action="store_true", help="Validate config and show what would be executed")

    # Live job execution
    live_cmd = sub.add_parser("live", help="Execute live market data collection jobs.")
    live_cmd.add_argument("--config", type=str, required=True, help="Path to configuration file")
    live_cmd.add_argument("--job", type=str, required=True, help="Job name to execute")
    live_cmd.add_argument("--profile", type=str, help="Profile override (dev/staging/prod)")
    live_cmd.add_argument("--dry-run", action="store_true", help="Validate config and show what would be executed")

    # Backfill job execution
    backfill_cmd = sub.add_parser("backfill", help="Execute historical backfill jobs.")
    backfill_cmd.add_argument("--config", type=str, required=True, help="Path to configuration file")
    backfill_cmd.add_argument("--job", type=str, required=True, help="Job name to execute")
    backfill_cmd.add_argument("--profile", type=str, help="Profile override (dev/staging/prod)")
    backfill_cmd.add_argument("--dry-run", action="store_true", help="Validate config and show what would be executed")

    # Config validation command
    validate = sub.add_parser("validate", help="Validate configuration file.")
    validate.add_argument("--config", type=str, required=True, help="Path to configuration file")
    validate.add_argument("--profile", type=str, help="Profile to validate")

    # Streaming commands
    stream = sub.add_parser("stream", help="Stream processing commands")
    stream_sub = stream.add_subparsers(dest="stream_command", required=True)
    
    # Stream produce command
    stream_produce = stream_sub.add_parser("produce", help="Start a producer")
    stream_produce.add_argument("--config", type=str, required=True, help="Streaming configuration file")
    stream_produce.add_argument("--provider", choices=["synthetic", "ibkr"], required=True, help="Provider to use")
    
    # Stream micro-batch command
    stream_micro_batch = stream_sub.add_parser("micro-batch", help="Start micro-batcher")
    stream_micro_batch.add_argument("--config", type=str, required=True, help="Streaming configuration file")
    stream_micro_batch.add_argument("--window", type=str, default="2s", help="Window size (e.g., 2s, 5s)")
    
    # Stream inference command
    stream_inference = stream_sub.add_parser("infer", help="Start inference")
    stream_inference.add_argument("--config", type=str, required=True, help="Streaming configuration file")
    stream_inference.add_argument("--adapter", choices=["rules", "sklearn"], help="Adapter to use")
    
    # Stream tail command
    stream_tail = stream_sub.add_parser("tail", help="Tail a stream")
    stream_tail.add_argument("--topic", default="mdp.events", help="Topic to tail")
    stream_tail.add_argument("--limit", type=int, default=50, help="Number of messages to show")
    
    # Stream replay command
    stream_replay = stream_sub.add_parser("replay", help="Replay historical data")
    stream_replay.add_argument("--config", type=str, required=True, help="Streaming configuration file")
    stream_replay.add_argument("--dataset", required=True, help="Dataset to replay")
    stream_replay.add_argument("--from", required=True, help="Start date")
    stream_replay.add_argument("--to", required=True, help="End date")

    # Stubs to extend later
    sub.add_parser("list", help="List known jobs (stub)")
    status = sub.add_parser("status", help="Get job status (stub)")
    status.add_argument("--job", type=str, default="default")

    return p.parse_args(argv)


async def _run_cmd(args: argparse.Namespace) -> int:
    if args.command == "list":
        print("Jobs: [example] (stub)")
        return 0

    if args.command == "status":
        print(f"Status for job '{args.job}': RUNNING (stub)")
        return 0

    if args.command == "validate":
        return _validate_config(args)

    if args.command == "job":
        return _execute_job(args)

    if args.command == "live":
        return _execute_live_job(args)

    if args.command == "backfill":
        return _execute_backfill_job(args)

    if args.command == "stream":
        return await _execute_stream_command(args)

    # Legacy unified runtime command (renamed to avoid conflict)
    if args.command == "legacy":
        settings = UnifiedRuntimeSettings.from_file(args.config)
        if args.mode:
            # override config mode from CLI if provided
            settings = settings.model_copy(update={"mode": RuntimeModeEnum(args.mode)})

        logger.info(f"Starting UnifiedRuntime in mode={settings.mode.value}")
        async with UnifiedRuntime(settings) as rt:
            # Classic: will delegate to existing service/runner
            # DAG:     will delegate to DagRuntime (builder/registry used internally)
            await rt.run(name=getattr(args, "job", "default"))
        logger.info("UnifiedRuntime finished.")
        return 0

    return 1


def _validate_config(args: argparse.Namespace) -> int:
    """Validate configuration file."""
    try:
        from market_data_core import load_config
        
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        
        logger.info(f"Validating configuration: {config_path}")
        cfg = load_config(str(config_path), profile_override=args.profile)
        
        logger.info(f"✅ Configuration valid!")
        logger.info(f"   Profile: {cfg.profile}")
        logger.info(f"   Providers: {len(cfg.providers.root)}")
        logger.info(f"   Datasets: {len(cfg.datasets.root)}")
        logger.info(f"   Jobs: {len(cfg.jobs.root)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return 1


def _execute_job(args: argparse.Namespace) -> int:
    """Execute a market data collection job."""
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        
        logger.info(f"Executing job '{args.job}' with config '{config_path}'")
        if args.profile:
            logger.info(f"Using profile: {args.profile}")
        
        run_job(str(config_path), args.job, args.profile, dry_run=getattr(args, 'dry_run', False))
        logger.info("✅ Job completed successfully")
        return 0
        
    except JobExecutionError as e:
        logger.error(f"❌ Job execution failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


def _execute_live_job(args: argparse.Namespace) -> int:
    """Execute a live market data collection job."""
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        
        logger.info(f"Executing live job '{args.job}' with config '{config_path}'")
        if args.profile:
            logger.info(f"Using profile: {args.profile}")
        
        if getattr(args, 'dry_run', False):
            logger.info("🔍 Dry run mode: validating configuration and showing execution plan")
            return _show_execution_plan(config_path, args.job, args.profile)
        
        run_job(str(config_path), args.job, args.profile, dry_run=False)
        logger.info("✅ Live job completed successfully")
        return 0
        
    except JobExecutionError as e:
        logger.error(f"❌ Live job execution failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


def _execute_backfill_job(args: argparse.Namespace) -> int:
    """Execute a backfill market data collection job."""
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        
        logger.info(f"Executing backfill job '{args.job}' with config '{config_path}'")
        if args.profile:
            logger.info(f"Using profile: {args.profile}")
        
        if getattr(args, 'dry_run', False):
            logger.info("🔍 Dry run mode: validating configuration and showing execution plan")
            return _show_execution_plan(config_path, args.job, args.profile)
        
        run_job(str(config_path), args.job, args.profile, dry_run=False)
        logger.info("✅ Backfill job completed successfully")
        return 0
        
    except JobExecutionError as e:
        logger.error(f"❌ Backfill job execution failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


def _show_execution_plan(config_path: Path, job_name: str, profile: str = None) -> int:
    """Show execution plan for dry run mode."""
    try:
        from market_data_core import load_config
        
        cfg = load_config(str(config_path), profile_override=profile)
        
        if job_name not in cfg.jobs.root:
            logger.error(f"Job '{job_name}' not found in configuration")
            return 1
        
        job = cfg.jobs.root[job_name]
        dataset = cfg.datasets.root[job.dataset]
        provider = cfg.providers.root[dataset.provider]
        
        logger.info("📋 Execution Plan:")
        logger.info(f"   Job: {job_name}")
        logger.info(f"   Mode: {job.mode}")
        logger.info(f"   Dataset: {job.dataset}")
        logger.info(f"   Provider: {dataset.provider} ({provider.type})")
        logger.info(f"   Symbols: {dataset.symbols}")
        logger.info(f"   Interval: {dataset.interval}")
        
        if job.mode == "backfill" and job.backfill:
            logger.info(f"   Backfill: {job.backfill.from_} to {job.backfill.to}")
            logger.info(f"   Chunk: {job.backfill.chunk}")
        
        logger.info(f"   Storage: {list(cfg.storage.root.keys())}")
        logger.info(f"   Features: write_enabled={cfg.features.write_enabled}, export_enabled={cfg.features.export_enabled}")
        
        logger.info("✅ Configuration valid - ready for execution")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to show execution plan: {e}")
        return 1


async def _execute_stream_command(args: argparse.Namespace) -> int:
    """Execute streaming commands."""
    try:
        from market_data_pipeline.streaming.cli import StreamingCLI
        import yaml
        
        # Load streaming configuration
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create CLI instance
        cli = StreamingCLI()
        
        try:
            # Connect to bus
            bus_config = config.get("bus", {})
            if bus_config.get("type") == "redis":
                from market_data_pipeline.streaming.redis_bus import RedisStreamBus
                redis_config = bus_config.get("redis", {})
                cli.bus = RedisStreamBus(
                    uri=redis_config.get("uri", "redis://localhost:6379/0"),
                    events_stream=redis_config.get("stream", "mdp.events"),
                    signals_stream=redis_config.get("signals_stream", "mdp.signals")
                )
                await cli.bus.connect()
            
            # Execute command
            if args.stream_command == "produce":
                await cli.start_producer(config, args.provider)
            elif args.stream_command == "micro-batch":
                logger.warning("Micro-batcher requires store client integration (not implemented in this example)")
                return 1
            elif args.stream_command == "infer":
                logger.warning("Inference requires store client integration (not implemented in this example)")
                return 1
            elif args.stream_command == "tail":
                await cli.tail_stream(args.topic, args.limit)
            elif args.stream_command == "replay":
                await cli.replay_data(args.dataset, getattr(args, 'from'), args.to)
            
            # Keep running for producers/consumers
            if args.stream_command in ["produce", "micro-batch", "infer"]:
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutting down...")
            
            return 0
            
        except Exception as e:
            logger.error(f"Streaming command failed: {e}")
            return 1
        finally:
            await cli.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Streaming command error: {e}")
        return 1


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    try:
        exit_code = asyncio.run(_run_cmd(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as exc:
        logger.exception(f"mdp failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

