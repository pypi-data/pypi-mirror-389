"""
Async HTTP client for multi-service API communication.

Provides a unified interface for calling pipeline and store APIs.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ApiClient:
    """
    Async HTTP client for orchestrator API calls.

    Manages connections to multiple services (pipeline, store) and provides
    a unified interface for making requests.

    Example:
        >>> client = ApiClient({
        ...     "pipeline": "http://localhost:8083",
        ...     "store": "http://localhost:8082"
        ... })
        >>> result = await client.request("pipeline", "POST", "/v1/replay/ticks", {...})
    """

    def __init__(
        self,
        base_urls: dict[str, str],
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize API client with service base URLs.

        Args:
            base_urls: Mapping of service names to base URLs
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self._clients: dict[str, httpx.AsyncClient] = {}
        self._timeout = timeout
        self._max_retries = max_retries

        for service, base_url in base_urls.items():
            self._clients[service] = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                follow_redirects=True,
            )
            logger.info(f"Initialized API client for {service}: {base_url}")

    async def request(
        self,
        api: str,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to a service API.

        Args:
            api: Service name (must be in base_urls)
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Optional JSON payload for request body

        Returns:
            JSON response from the API

        Raises:
            KeyError: If api service is not configured
            httpx.HTTPStatusError: If request fails with non-2xx status
            httpx.RequestError: If network error occurs
        """
        if api not in self._clients:
            raise KeyError(f"Unknown API service: {api} (available: {list(self._clients.keys())})")

        client = self._clients[api]

        for attempt in range(self._max_retries):
            try:
                logger.debug(f"[{api}] {method} {endpoint} (attempt {attempt + 1}/{self._max_retries})")

                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()
                logger.info(f"[{api}] {method} {endpoint} -> {response.status_code}")
                return result

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"[{api}] HTTP {e.response.status_code}: {method} {endpoint} -> {e.response.text}"
                )
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.RequestError as e:
                logger.error(f"[{api}] Network error: {method} {endpoint} -> {e}")
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)

        raise RuntimeError(f"Failed to request {api} {method} {endpoint} after {self._max_retries} attempts")

    async def close(self) -> None:
        """Close all HTTP client connections."""
        logger.info("Closing API clients...")
        await asyncio.gather(*[client.aclose() for client in self._clients.values()])
        logger.info("API clients closed")

    async def __aenter__(self) -> ApiClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

