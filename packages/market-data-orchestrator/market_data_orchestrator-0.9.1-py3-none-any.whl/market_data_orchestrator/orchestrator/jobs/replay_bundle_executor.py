"""
Replay bundle executor for coordinated replay → signal → export workflows.

Executes bundle specifications by orchestrating API calls to pipeline and store services.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ..core.http_client import ApiClient
from ..core.prometheus import (
    bundle_api_calls_total,
    bundle_duration_seconds,
    bundle_failures_total,
    bundle_job_duration_seconds,
    bundle_runs_total,
)

logger = logging.getLogger(__name__)


class ReplayBundleExecutor:
    """
    Executes replay bundle workflows.

    Coordinates multi-step workflows across pipeline and store services:
    1. Start replay job
    2. Poll for completion
    3. Trigger export job

    Example:
        >>> client = ApiClient({"pipeline": "...", "store": "..."})
        >>> executor = ReplayBundleExecutor(client)
        >>> result = await executor.run_bundle(bundle_config)
    """

    def __init__(self, api_client: ApiClient):
        """
        Initialize executor with API client.

        Args:
            api_client: Configured API client for service communication
        """
        self.api = api_client
        logger.info("ReplayBundleExecutor initialized")

    async def run_bundle(self, bundle_cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a bundle workflow end-to-end.

        Args:
            bundle_cfg: Bundle configuration dictionary

        Returns:
            Execution result with status and metrics

        Raises:
            KeyError: If bundle config is malformed
            Exception: If any job step fails
        """
        bundle_name = bundle_cfg.get("bundle_name", "unknown")
        start_time = time.time()

        logger.info(f"Starting bundle: {bundle_name}")
        bundle_runs_total.labels(bundle=bundle_name, status="started").inc()

        try:
            # Execute bundle jobs sequentially
            jobs = bundle_cfg.get("jobs", [])
            if not jobs:
                raise ValueError(f"Bundle {bundle_name} has no jobs defined")

            context = {}  # Store results from previous jobs

            for job in jobs:
                job_name = job.get("name", "unnamed")
                job_type = job.get("type", "api")

                logger.info(f"[{bundle_name}] Executing job: {job_name} (type={job_type})")

                if job_type == "api":
                    result = await self._execute_api_job(job, context, bundle_name)
                    context[job_name] = result

                elif job_type == "wait":
                    await self._execute_wait_job(job, context, bundle_name)

                else:
                    raise ValueError(f"Unknown job type: {job_type}")

            # Bundle completed successfully
            duration = time.time() - start_time
            bundle_duration_seconds.labels(bundle=bundle_name).observe(duration)
            bundle_runs_total.labels(bundle=bundle_name, status="success").inc()

            logger.info(f"Bundle {bundle_name} completed successfully in {duration:.2f}s")

            return {
                "status": "success",
                "bundle": bundle_name,
                "duration": duration,
                "jobs_completed": len(jobs),
            }

        except Exception as e:
            duration = time.time() - start_time
            bundle_failures_total.labels(bundle=bundle_name).inc()
            bundle_runs_total.labels(bundle=bundle_name, status="failed").inc()

            logger.exception(f"Bundle {bundle_name} failed after {duration:.2f}s: {e}")

            return {
                "status": "failed",
                "bundle": bundle_name,
                "duration": duration,
                "error": str(e),
            }

    async def _execute_api_job(
        self,
        job: dict[str, Any],
        context: dict[str, Any],
        bundle_name: str,
    ) -> dict[str, Any]:
        """
        Execute an API call job.

        Args:
            job: Job configuration
            context: Context from previous jobs
            bundle_name: Name of the bundle

        Returns:
            API response dictionary
        """
        job_name = job["name"]
        api = job["api"]
        method = job["method"]
        endpoint = job["endpoint"]
        payload = job.get("payload", {})

        job_start = time.time()

        try:
            # Template substitution for endpoint and payload
            endpoint = self._substitute_templates(endpoint, context)
            payload = self._substitute_templates(payload, context)

            logger.debug(f"[{job_name}] {method} {api}{endpoint}")

            response = await self.api.request(api, method, endpoint, payload)

            job_duration = time.time() - job_start
            bundle_job_duration_seconds.labels(bundle=bundle_name, job=job_name).observe(job_duration)
            bundle_api_calls_total.labels(
                bundle=bundle_name,
                api=api,
                method=method,
                status="success",
            ).inc()

            logger.info(f"[{job_name}] Completed in {job_duration:.2f}s")
            return response

        except Exception as e:
            bundle_api_calls_total.labels(
                bundle=bundle_name,
                api=api,
                method=method,
                status="failed",
            ).inc()
            logger.error(f"[{job_name}] Failed: {e}")
            raise

    async def _execute_wait_job(
        self,
        job: dict[str, Any],
        context: dict[str, Any],
        bundle_name: str,
    ) -> None:
        """
        Execute a wait/poll job.

        Args:
            job: Job configuration with check_endpoint and success_when
            context: Context from previous jobs
            bundle_name: Name of the bundle

        Raises:
            TimeoutError: If polling exceeds max attempts
            Exception: If check endpoint fails
        """
        job_name = job["name"]
        depends_on = job.get("depends_on")
        check_endpoint = job["check_endpoint"]
        success_when = job.get("success_when", 'status == "success"')
        poll_interval = job.get("poll_interval", 10)
        max_attempts = job.get("max_attempts", 60)

        # Template substitution for check endpoint
        check_endpoint = self._substitute_templates(check_endpoint, context)

        logger.info(
            f"[{job_name}] Waiting for condition: {success_when} "
            f"(poll={poll_interval}s, max={max_attempts})"
        )

        for attempt in range(max_attempts):
            try:
                # Assume check endpoint is on same API as the job we're waiting for
                # For simplicity, extract API from depends_on job
                api = self._get_api_from_context(depends_on, context)

                status = await self.api.request(api, "GET", check_endpoint)

                # Simple condition evaluation (just check status field)
                if self._evaluate_condition(status, success_when):
                    logger.info(f"[{job_name}] Condition met after {attempt + 1} attempts")
                    return

                if status.get("status") == "failed":
                    raise RuntimeError(f"Job {depends_on} failed: {status.get('error', 'unknown')}")

            except Exception as e:
                logger.warning(f"[{job_name}] Check failed (attempt {attempt + 1}): {e}")

            await asyncio.sleep(poll_interval)

        raise TimeoutError(
            f"[{job_name}] Timeout after {max_attempts} attempts "
            f"({max_attempts * poll_interval}s)"
        )

    def _substitute_templates(self, obj: Any, context: dict[str, Any]) -> Any:
        """
        Recursively substitute template variables in strings.

        Supports {{ variable.path }} syntax.

        Args:
            obj: Object to process (str, dict, list, etc.)
            context: Template context dictionary

        Returns:
            Object with substituted values
        """
        if isinstance(obj, str):
            # Simple template substitution: {{ start_replay.run_id }}
            for key, value in context.items():
                template = f"{{{{ {key}.run_id }}}}"
                if template in obj:
                    run_id = value.get("run_id") if isinstance(value, dict) else None
                    if run_id:
                        obj = obj.replace(template, str(run_id))
            return obj

        elif isinstance(obj, dict):
            return {k: self._substitute_templates(v, context) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._substitute_templates(item, context) for item in obj]

        else:
            return obj

    def _evaluate_condition(self, data: dict[str, Any], condition: str) -> bool:
        """
        Evaluate a simple condition expression.

        Supports: status == "success", status == "failed", etc.

        Args:
            data: Data dictionary to evaluate against
            condition: Condition expression string

        Returns:
            True if condition is met
        """
        # Simple evaluation: status == "success"
        if "==" in condition:
            field, value = condition.split("==")
            field = field.strip()
            value = value.strip().strip('"\'')
            return data.get(field) == value

        return False

    def _get_api_from_context(self, job_name: str | None, context: dict[str, Any]) -> str:
        """
        Get the API service name from context (heuristic).

        Args:
            job_name: Name of job to look up
            context: Execution context

        Returns:
            API service name (defaults to "pipeline")
        """
        # Simple heuristic: assume pipeline for replay jobs
        # Could be enhanced to store API in context
        return "pipeline"

