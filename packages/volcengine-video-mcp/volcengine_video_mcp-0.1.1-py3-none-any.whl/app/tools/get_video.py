"""Tool for querying video generation task status."""

from fastmcp import Context

from app.client import VolcengineVideoClient


async def get_video_task(task_id: str, ctx: Context | None = None) -> dict:
    """Query the status and result of a video generation task.

    Args:
        task_id: Task ID to query
        ctx: FastMCP context

    Returns:
        dict containing task status, video_url (if succeeded), and other metadata
    """
    if ctx:
        await ctx.info(f"Querying task: {task_id}")

    try:
        async with VolcengineVideoClient() as client:
            result = await client.get_video_task(task_id)

        status = result.get("status")
        if ctx:
            await ctx.info(f"Task status: {status}")

        if status == "succeeded":
            video_url = result.get("content", {}).get("video_url")
            if video_url and ctx:
                await ctx.info(f"Video URL: {video_url}")
                await ctx.info(
                    "Note: Video URL is valid for 24 hours, please download promptly"
                )

        return {"status": "success", "data": result}

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to query task: {e}")
        return {"status": "error", "error": str(e)}
