"""
Bundle scheduler for recurring job execution.

Supports cron-style scheduling for automated replay and export workflows.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

from .bundle_loader import load_bundle
from .http_client import ApiClient

logger = logging.getLogger(__name__)


class BundleScheduler:
    """
    Cron-style scheduler for bundle execution.

    Manages scheduled and on-demand execution of bundle workflows.

    Example:
        >>> api_urls = {"pipeline": "http://localhost:8083", "store": "http://localhost:8082"}
        >>> scheduler = BundleScheduler(api_urls)
        >>> scheduler.schedule_bundle("config/bundles/replay.yaml", interval=3600)
        >>> await scheduler.start()
    """

    def __init__(
        self,
        api_urls: dict[str, str],
        executor_factory: Callable[[ApiClient], object] | None = None,
    ):
        """
        Initialize bundle scheduler.

        Args:
            api_urls: Mapping of service names to base URLs
            executor_factory: Optional factory function for creating executors
        """
        self.api = ApiClient(api_urls)
        self._executor_factory = executor_factory
        self._schedules: list[dict] = []
        self._running = False
        self._task: asyncio.Task | None = None

        logger.info("BundleScheduler initialized")

    def schedule_bundle(
        self,
        bundle_path: str | Path,
        interval: int = 3600,
        immediate: bool = False,
    ) -> None:
        """
        Schedule a bundle for recurring execution.

        Args:
            bundle_path: Path to bundle YAML file
            interval: Execution interval in seconds (default: 1 hour)
            immediate: Execute immediately on startup
        """
        schedule = {
            "path": str(bundle_path),
            "interval": interval,
            "immediate": immediate,
            "last_run": 0.0,
        }
        self._schedules.append(schedule)

        logger.info(
            f"Scheduled bundle {bundle_path} with interval {interval}s "
            f"(immediate={immediate})"
        )

    async def run_bundle_now(self, bundle_path: str | Path) -> dict:
        """
        Execute a bundle immediately (ad-hoc execution).

        Args:
            bundle_path: Path to bundle YAML file

        Returns:
            Execution result dictionary

        Raises:
            Exception: If bundle execution fails
        """
        logger.info(f"Running bundle on-demand: {bundle_path}")

        config = load_bundle(bundle_path)

        # Import here to avoid circular dependency
        from ..jobs.replay_bundle_executor import ReplayBundleExecutor

        if self._executor_factory:
            executor = self._executor_factory(self.api)
        else:
            executor = ReplayBundleExecutor(self.api)

        result = await executor.run_bundle(config)
        return result

    async def _run_scheduled_bundles(self) -> None:
        """Background task that runs scheduled bundles."""
        logger.info("Scheduler background task started")

        # Run immediate bundles on startup
        for schedule in self._schedules:
            if schedule["immediate"]:
                try:
                    await self.run_bundle_now(schedule["path"])
                except Exception as e:
                    logger.exception(f"Failed to run immediate bundle {schedule['path']}: {e}")

        # Main scheduling loop
        while self._running:
            current_time = asyncio.get_event_loop().time()

            for schedule in self._schedules:
                time_since_last = current_time - schedule["last_run"]

                if time_since_last >= schedule["interval"]:
                    try:
                        logger.debug(f"Triggering scheduled bundle: {schedule['path']}")
                        await self.run_bundle_now(schedule["path"])
                        schedule["last_run"] = current_time
                    except Exception as e:
                        logger.exception(f"Scheduled bundle failed {schedule['path']}: {e}")

            # Sleep for a short interval and check again
            await asyncio.sleep(5)

        logger.info("Scheduler background task stopped")

    async def start(self) -> None:
        """Start the scheduler background task."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_scheduled_bundles())

        logger.info(f"Scheduler started with {len(self._schedules)} scheduled bundle(s)")

    async def stop(self) -> None:
        """Stop the scheduler background task."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.api.close()

        logger.info("Scheduler stopped")

    async def __aenter__(self) -> BundleScheduler:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

