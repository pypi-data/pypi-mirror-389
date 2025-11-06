"""
Standalone entry point for bundle orchestration.

Run scheduled bundles with:
    python -m market_data_orchestrator.bundles.main
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from pathlib import Path

from ..logging_config import configure_logging
from .core.scheduler import BundleScheduler

logger = logging.getLogger(__name__)


def get_api_urls() -> dict[str, str]:
    """
    Get API service URLs from environment.

    Returns:
        Mapping of service names to base URLs
    """
    return {
        "pipeline": os.getenv("ORCH_BUNDLE_PIPELINE_URL", "http://localhost:8083"),
        "store": os.getenv("ORCH_BUNDLE_STORE_URL", "http://localhost:8082"),
    }


def get_bundle_schedules() -> list[dict]:
    """
    Get bundle schedules from environment.

    Returns:
        List of schedule configurations

    Environment Variables:
        ORCH_BUNDLE_SCHEDULES: Comma-separated list of "path:interval:immediate"
            Example: "config/bundles/replay.yaml:3600:true,config/bundles/export.yaml:7200:false"
    """
    schedules_str = os.getenv("ORCH_BUNDLE_SCHEDULES", "")

    if not schedules_str:
        # Default schedule
        return [
            {
                "path": "config/bundles/phase6_replay_bundle.yaml",
                "interval": 3600,
                "immediate": False,
            }
        ]

    schedules = []
    for schedule_def in schedules_str.split(","):
        parts = schedule_def.strip().split(":")
        if len(parts) >= 1:
            path = parts[0]
            interval = int(parts[1]) if len(parts) > 1 else 3600
            immediate = parts[2].lower() == "true" if len(parts) > 2 else False

            schedules.append({
                "path": path,
                "interval": interval,
                "immediate": immediate,
            })

    return schedules


async def main() -> None:
    """Main entry point for bundle orchestration."""
    configure_logging()

    logger.info("=" * 60)
    logger.info("Phase 6 - Bundle Orchestrator Starting")
    logger.info("=" * 60)

    api_urls = get_api_urls()
    logger.info(f"API URLs: {api_urls}")

    scheduler = BundleScheduler(api_urls)

    # Load schedules from environment
    schedules = get_bundle_schedules()

    for schedule in schedules:
        path = Path(schedule["path"])
        if path.exists():
            scheduler.schedule_bundle(
                bundle_path=schedule["path"],
                interval=schedule["interval"],
                immediate=schedule["immediate"],
            )
            logger.info(
                f"Scheduled: {schedule['path']} "
                f"(interval={schedule['interval']}s, immediate={schedule['immediate']})"
            )
        else:
            logger.warning(f"Bundle not found, skipping: {schedule['path']}")

    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start scheduler
    await scheduler.start()

    logger.info("Bundle orchestrator running (press Ctrl+C to stop)")

    # Wait for shutdown signal
    await shutdown_event.wait()

    # Cleanup
    logger.info("Stopping scheduler...")
    await scheduler.stop()

    logger.info("Bundle orchestrator stopped")


if __name__ == "__main__":
    asyncio.run(main())

