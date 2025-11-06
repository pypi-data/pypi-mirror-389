"""
Prometheus metrics for bundle orchestration.

Exports metrics for bundle runs, durations, and failures.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# Bundle execution metrics
bundle_runs_total = Counter(
    "bundle_runs_total",
    "Total number of bundle runs by outcome",
    ["bundle", "status"],
)

bundle_duration_seconds = Histogram(
    "bundle_duration_seconds",
    "Duration of bundle runs in seconds",
    ["bundle"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
)

bundle_failures_total = Counter(
    "bundle_failures_total",
    "Total number of bundle failures",
    ["bundle"],
)

# Job-level metrics
bundle_job_duration_seconds = Histogram(
    "bundle_job_duration_seconds",
    "Duration of individual bundle jobs",
    ["bundle", "job"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120),
)

bundle_api_calls_total = Counter(
    "bundle_api_calls_total",
    "Total API calls made by bundles",
    ["bundle", "api", "method", "status"],
)

