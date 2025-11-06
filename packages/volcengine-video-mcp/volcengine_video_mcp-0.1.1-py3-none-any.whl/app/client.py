"""HTTP client for Volcengine Video Generation API."""

from typing import Any

import httpx

from app.config import Config


class VolcengineVideoClient:
    """HTTP client for interacting with Volcengine Video Generation API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """Initialize the client.

        Args:
            api_key: Volcengine API key (defaults to Config.ARK_API_KEY)
            base_url: API base URL (defaults to Config.ARK_BASE_URL)
        """
        self.api_key = api_key or Config.ARK_API_KEY
        self.base_url = base_url or Config.ARK_BASE_URL

        if not self.api_key:
            raise ValueError("API key is required")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout=30.0,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def create_video_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a video generation task.

        Args:
            payload: Request payload containing model, content, etc.

        Returns:
            dict containing task_id

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = await self.client.post(Config.TASKS_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()

    async def get_video_task(self, task_id: str) -> dict[str, Any]:
        """Get status and result of a video generation task.

        Args:
            task_id: The task ID to query

        Returns:
            dict containing task status and result

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = await self.client.get(f"{Config.TASKS_ENDPOINT}/{task_id}")
        response.raise_for_status()
        return response.json()

    async def list_video_tasks(
        self,
        page_num: int | None = None,
        page_size: int | None = None,
        status: str | None = None,
        task_ids: list[str] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """List video generation tasks with optional filters.

        Args:
            page_num: Page number (1-500)
            page_size: Page size (1-500)
            status: Filter by status (queued/running/cancelled/succeeded/failed)
            task_ids: Filter by task IDs
            model: Filter by model

        Returns:
            dict containing items list and total count

        Raises:
            httpx.HTTPError: If the request fails
        """
        params: dict[str, Any] = {}

        if page_num is not None:
            params["page_num"] = page_num
        if page_size is not None:
            params["page_size"] = page_size
        if status:
            params["filter.status"] = status
        if model:
            params["filter.model"] = model
        if task_ids:
            # Multiple task_ids are sent as separate query parameters
            params["filter.task_ids"] = task_ids

        response = await self.client.get(Config.TASKS_ENDPOINT, params=params)
        response.raise_for_status()
        return response.json()

    async def delete_video_task(self, task_id: str) -> dict[str, Any]:
        """Cancel or delete a video generation task.

        Args:
            task_id: The task ID to cancel/delete

        Returns:
            Empty dict on success

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = await self.client.delete(f"{Config.TASKS_ENDPOINT}/{task_id}")
        response.raise_for_status()
        return response.json()
