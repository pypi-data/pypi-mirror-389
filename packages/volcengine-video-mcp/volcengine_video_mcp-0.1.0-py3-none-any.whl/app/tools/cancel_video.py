"""Tool for canceling or deleting video generation tasks."""

from fastmcp import Context

from app.client import VolcengineVideoClient


async def cancel_video_task(task_id: str, ctx: Context | None = None) -> dict:
    """Cancel or delete a video generation task.

    Behavior depends on task status:
    - queued: Cancel the task (status becomes "cancelled")
    - running: Not supported
    - succeeded/failed: Delete task record (no longer queryable)
    - cancelled: Auto-deleted after 24 hours

    Args:
        task_id: Task ID to cancel/delete
        ctx: FastMCP context

    Returns:
        dict with success status
    """
    if ctx:
        await ctx.info(f"Canceling/deleting task: {task_id}")

    try:
        # Query task status first to provide better feedback
        async with VolcengineVideoClient() as client:
            try:
                task = await client.get_video_task(task_id)
                status = task.get("status")

                if ctx:
                    await ctx.info(f"Current task status: {status}")

                if status == "running":
                    return {
                        "status": "error",
                        "error": "Cannot cancel running tasks",
                    }

                if status == "cancelled":
                    return {
                        "status": "error",
                        "error": "Task is already cancelled and will be auto-deleted in 24h",
                    }

            except Exception:
                # Task might not exist, proceed with delete anyway
                pass

            # Perform delete operation
            await client.delete_video_task(task_id)

        if ctx:
            await ctx.info(f"Task {task_id} cancelled/deleted successfully")

        return {
            "status": "success",
            "message": "Task cancelled/deleted successfully",
        }

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to cancel/delete task: {e}")
        return {"status": "error", "error": str(e)}
