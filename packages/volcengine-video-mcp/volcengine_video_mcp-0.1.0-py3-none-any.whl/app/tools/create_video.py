"""Tool for creating video generation tasks."""

from fastmcp import Context

from app.client import VolcengineVideoClient
from app.config import Config


async def create_video_task(
    model: str,
    prompt: str,
    image_url: str | None = None,
    first_frame_url: str | None = None,
    last_frame_url: str | None = None,
    reference_image_urls: list[str] | None = None,
    resolution: str | None = None,
    ratio: str | None = None,
    duration: int | None = None,
    frames: int | None = None,
    fps: int | None = None,
    seed: int | None = None,
    camera_fixed: bool = False,
    watermark: bool = False,
    return_last_frame: bool = False,
    callback_url: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Create a video generation task.

    Args:
        model: Model ID (e.g., "doubao-seedance-1-0-pro")
        prompt: Text description for video generation
        image_url: Single image URL for image-to-video (first frame)
        first_frame_url: First frame image URL
        last_frame_url: Last frame image URL
        reference_image_urls: List of reference image URLs (1-4 images)
        resolution: Video resolution (480p/720p/1080p)
        ratio: Aspect ratio (16:9/4:3/1:1/3:4/9:16/21:9/keep_ratio/adaptive)
        duration: Video duration in seconds (2-12)
        frames: Number of frames (29-289, must satisfy 25+4n)
        fps: Frame rate (16/24)
        seed: Random seed (-1 to 2^32-1)
        camera_fixed: Whether to fix camera
        watermark: Whether to include watermark
        return_last_frame: Whether to return last frame image
        callback_url: Callback URL for task completion
        ctx: FastMCP context

    Returns:
        dict with task_id
    """
    # Convert short model name to full model ID
    full_model_id = Config.SUPPORTED_MODELS.get(model, model)

    if ctx:
        await ctx.info(f"Creating video task with model: {model} (ID: {full_model_id})")

    # Build content array
    content = []

    # Add text content
    text_parts = [prompt]

    # Add text command parameters
    if resolution:
        text_parts.append(f"--resolution {resolution}")
    if ratio:
        text_parts.append(f"--ratio {ratio}")
    if duration:
        text_parts.append(f"--duration {duration}")
    if frames:
        text_parts.append(f"--frames {frames}")
    if fps:
        text_parts.append(f"--framespersecond {fps}")
    if seed is not None and seed != -1:
        text_parts.append(f"--seed {seed}")
    if camera_fixed:
        text_parts.append("--camerafixed true")
    if watermark:
        text_parts.append("--watermark true")

    content.append({"type": "text", "text": " ".join(text_parts)})

    # Add image content
    if reference_image_urls:
        # Reference images mode (1-4 images)
        for img_url in reference_image_urls:
            content.append({
                "type": "image_url",
                "image_url": {"url": img_url},
                "role": "reference_image",
            })
    elif first_frame_url and last_frame_url:
        # First and last frame mode
        content.append({
            "type": "image_url",
            "image_url": {"url": first_frame_url},
            "role": "first_frame",
        })
        content.append({
            "type": "image_url",
            "image_url": {"url": last_frame_url},
            "role": "last_frame",
        })
    elif image_url or first_frame_url:
        # Single image (first frame) mode
        img = image_url or first_frame_url
        content.append({
            "type": "image_url",
            "image_url": {"url": img},
            "role": "first_frame",
        })

    # Build request payload
    payload = {"model": full_model_id, "content": content}

    if return_last_frame:
        payload["return_last_frame"] = True

    if callback_url:
        payload["callback_url"] = callback_url

    try:
        async with VolcengineVideoClient() as client:
            if ctx:
                await ctx.info(f"Client base_url: {client.base_url}")
                await ctx.info(f"Client API key: {client.api_key[:20]}...")
                await ctx.info(f"Request payload: {payload}")

            result = await client.create_video_task(payload)

        if ctx:
            await ctx.info(f"Task created successfully: {result.get('id')}")

        return {"status": "success", "data": result}

    except Exception as e:
        error_msg = (
            f"Failed to create task: {e}\n"
            f"Debug info:\n"
            f"- Config API Key: {Config.ARK_API_KEY[:20]}...\n"
            f"- Config Base URL: {Config.ARK_BASE_URL}\n"
            f"- Model: {full_model_id}\n"
            f"- Payload: {payload}"
        )
        if ctx:
            await ctx.error(error_msg)
        return {"status": "error", "error": error_msg}
