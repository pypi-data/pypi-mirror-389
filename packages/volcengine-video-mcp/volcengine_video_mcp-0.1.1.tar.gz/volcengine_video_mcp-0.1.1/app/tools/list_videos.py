"""Tool for listing video generation tasks."""

from fastmcp import Context

from app.client import VolcengineVideoClient


async def list_video_tasks(
    page_num: int = 1,
    page_size: int = 10,
    status: str | None = None,
    task_ids: list[str] | None = None,
    model: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """List video generation tasks with optional filters.

    Args:
        page_num: Page number (1-500), default 1
        page_size: Page size (1-500), default 10
        status: Filter by status (queued/running/cancelled/succeeded/failed)
        task_ids: Filter by specific task IDs
        model: Filter by model
        ctx: FastMCP context

    Returns:
        dict containing items list and total count
    """
    if ctx:
        await ctx.info(f"Listing tasks (page {page_num}, size {page_size})")
        if status:
            await ctx.info(f"Filtering by status: {status}")
        if task_ids:
            await ctx.info(f"Filtering by task IDs: {', '.join(task_ids)}")

    try:
        async with VolcengineVideoClient() as client:
            result = await client.list_video_tasks(
                page_num=page_num,
                page_size=page_size,
                status=status,
                task_ids=task_ids,
                model=model,
            )

        total = result.get("total", 0)
        items_count = len(result.get("items", []))

        if ctx:
            await ctx.info(f"Found {items_count} tasks (total: {total})")

        return {"status": "success", "data": result}

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list tasks: {e}")
        return {"status": "error", "error": str(e)}
