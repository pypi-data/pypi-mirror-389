"""
Bundle orchestration API endpoints.

Provides REST endpoints for triggering and monitoring bundle executions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth_jwt import get_current_user_with_role
from ..models.security import UserInfo
from ..bundles import BundleScheduler, load_bundle, ReplayBundleExecutor, ApiClient

log = logging.getLogger(__name__)

router = APIRouter(prefix="/bundles", tags=["bundles"])

# Global scheduler instance (initialized by app)
_scheduler: BundleScheduler | None = None


def set_scheduler(scheduler: BundleScheduler) -> None:
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler


def get_scheduler() -> BundleScheduler:
    """Get the global scheduler instance."""
    if _scheduler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bundle scheduler not initialized",
        )
    return _scheduler


class BundleRunRequest(BaseModel):
    """Request to run a bundle."""

    bundle_path: str
    """Path to the bundle YAML file."""

    immediate: bool = True
    """Execute immediately (default: true)."""


class BundleRunResponse(BaseModel):
    """Response from bundle execution."""

    status: str
    """Execution status: success, failed, started."""

    bundle: str
    """Bundle name."""

    duration: float | None = None
    """Execution duration in seconds (if completed)."""

    jobs_completed: int | None = None
    """Number of jobs completed."""

    error: str | None = None
    """Error message if failed."""


class BundleListResponse(BaseModel):
    """List of scheduled bundles."""

    bundles: list[dict[str, Any]]
    """List of bundle schedules."""


@router.post("/run", response_model=BundleRunResponse)
async def run_bundle(
    request: BundleRunRequest,
    user: UserInfo = Depends(get_current_user_with_role("operator")),
) -> BundleRunResponse:
    """
    Execute a bundle workflow immediately.

    Requires **operator** or **admin** role.

    Args:
        request: Bundle run request with path
        user: Authenticated user (from JWT/API key)

    Returns:
        Execution result

    Raises:
        404: Bundle file not found
        500: Execution failed
    """
    log.info(f"Bundle run requested by {user.username}: {request.bundle_path}")

    path = Path(request.bundle_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bundle not found: {request.bundle_path}",
        )

    try:
        scheduler = get_scheduler()
        result = await scheduler.run_bundle_now(request.bundle_path)

        log.info(f"Bundle execution completed: {result.get('status')}")

        return BundleRunResponse(
            status=result.get("status", "unknown"),
            bundle=result.get("bundle", "unknown"),
            duration=result.get("duration"),
            jobs_completed=result.get("jobs_completed"),
            error=result.get("error"),
        )

    except Exception as e:
        log.exception(f"Bundle execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bundle execution failed: {str(e)}",
        )


@router.get("/scheduled", response_model=BundleListResponse)
async def list_scheduled_bundles(
    user: UserInfo = Depends(get_current_user_with_role("viewer")),
) -> BundleListResponse:
    """
    List all scheduled bundles.

    Requires **viewer**, **operator**, or **admin** role.

    Args:
        user: Authenticated user (from JWT/API key)

    Returns:
        List of scheduled bundles
    """
    log.debug(f"Scheduled bundles requested by {user.username}")

    scheduler = get_scheduler()

    # Return schedule information
    bundles = [
        {
            "path": schedule["path"],
            "interval": schedule["interval"],
            "last_run": schedule["last_run"],
            "immediate": schedule.get("immediate", False),
        }
        for schedule in scheduler._schedules
    ]

    return BundleListResponse(bundles=bundles)


@router.get("/config/{bundle_name}")
async def get_bundle_config(
    bundle_name: str,
    user: UserInfo = Depends(get_current_user_with_role("viewer")),
) -> dict[str, Any]:
    """
    Get bundle configuration by name.

    Requires **viewer**, **operator**, or **admin** role.

    Args:
        bundle_name: Bundle name (e.g., "phase6_replay_bundle")
        user: Authenticated user (from JWT/API key)

    Returns:
        Bundle configuration dictionary

    Raises:
        404: Bundle not found
    """
    log.debug(f"Bundle config requested by {user.username}: {bundle_name}")

    # Look for bundle in config/bundles/
    bundle_path = Path(f"config/bundles/{bundle_name}.yaml")

    if not bundle_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bundle not found: {bundle_name}",
        )

    try:
        config = load_bundle(bundle_path)
        return config
    except Exception as e:
        log.exception(f"Failed to load bundle config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load bundle: {str(e)}",
        )


@router.post("/schedule")
async def schedule_bundle(
    request: BundleRunRequest,
    interval: int = 3600,
    user: UserInfo = Depends(get_current_user_with_role("admin")),
) -> dict[str, Any]:
    """
    Schedule a bundle for recurring execution.

    Requires **admin** role.

    Args:
        request: Bundle schedule request
        interval: Execution interval in seconds (default: 3600 = 1 hour)
        user: Authenticated user (from JWT/API key)

    Returns:
        Schedule confirmation

    Raises:
        404: Bundle not found
    """
    log.info(f"Bundle schedule requested by {user.username}: {request.bundle_path}")

    path = Path(request.bundle_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bundle not found: {request.bundle_path}",
        )

    scheduler = get_scheduler()
    scheduler.schedule_bundle(
        bundle_path=request.bundle_path,
        interval=interval,
        immediate=request.immediate,
    )

    return {
        "status": "scheduled",
        "bundle_path": request.bundle_path,
        "interval": interval,
        "immediate": request.immediate,
    }

