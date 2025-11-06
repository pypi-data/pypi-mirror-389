"""Server information resources."""

import json

from app.config import Config


def get_server_status() -> str:
    """Get server status information."""
    status = {
        "server_name": Config.SERVER_NAME,
        "version": Config.SERVER_VERSION,
        "api_base_url": Config.ARK_BASE_URL,
        "api_version": Config.API_VERSION,
        "status": "running",
        "features": [
            "Text-to-Video generation",
            "Image-to-Video generation (first frame)",
            "Image-to-Video generation (first & last frame)",
            "Image-to-Video generation (reference images)",
            "Task status query",
            "Batch task listing",
            "Task cancellation/deletion",
        ],
    }
    return json.dumps(status, indent=2, ensure_ascii=False)


def get_models_list() -> str:
    """Get list of supported models."""
    models_info = {
        "supported_models": [
            {
                "id": "doubao-seedance-1-0-pro",
                "full_id": Config.SUPPORTED_MODELS["doubao-seedance-1-0-pro"],
                "capabilities": [
                    "Text-to-Video",
                    "Image-to-Video (first frame)",
                    "Image-to-Video (first & last frame)",
                ],
                "max_duration": "12s",
                "default_resolution": "1080p",
            },
            {
                "id": "doubao-seedance-1-0-pro-fast",
                "full_id": Config.SUPPORTED_MODELS["doubao-seedance-1-0-pro-fast"],
                "capabilities": [
                    "Text-to-Video",
                    "Image-to-Video (first frame)",
                ],
                "max_duration": "12s",
                "default_resolution": "1080p",
                "note": "Faster generation speed",
            },
            {
                "id": "doubao-seedance-1-0-lite-t2v",
                "full_id": Config.SUPPORTED_MODELS["doubao-seedance-1-0-lite-t2v"],
                "capabilities": ["Text-to-Video"],
                "max_duration": "10s",
                "default_resolution": "720p",
            },
            {
                "id": "doubao-seedance-1-0-lite-i2v",
                "full_id": Config.SUPPORTED_MODELS["doubao-seedance-1-0-lite-i2v"],
                "capabilities": [
                    "Image-to-Video (first frame)",
                    "Image-to-Video (first & last frame)",
                    "Image-to-Video (reference images 1-4)",
                ],
                "max_duration": "10s",
                "default_resolution": "720p",
            },
        ],
        "legacy_models": [
            {
                "id": "wan2-1-14b-t2v",
                "note": "Being phased out",
            },
            {
                "id": "wan2-1-14b-i2v",
                "note": "Being phased out",
            },
            {
                "id": "wan2-1-14b-flf2v",
                "note": "Being phased out",
            },
        ],
    }
    return json.dumps(models_info, indent=2, ensure_ascii=False)


def get_api_docs() -> str:
    """Get API usage documentation."""
    docs = """# Volcengine Video Generation API Documentation

## Overview

This MCP server provides access to Volcengine (Doubao) Video Generation API.
It supports text-to-video and image-to-video generation with multiple models.

## Tools

### create_video_task

Create a new video generation task.

**Parameters:**
- `model` (required): Model ID
- `prompt` (required): Text description for video generation
- `image_url`: Single image URL for image-to-video
- `first_frame_url`: First frame image URL
- `last_frame_url`: Last frame image URL
- `reference_image_urls`: List of 1-4 reference images
- `resolution`: 480p/720p/1080p
- `ratio`: 16:9/4:3/1:1/3:4/9:16/21:9/keep_ratio/adaptive
- `duration`: Video duration in seconds (2-12)
- `frames`: Number of frames (29-289, must satisfy 25+4n)
- `fps`: Frame rate (16/24)
- `seed`: Random seed
- `camera_fixed`: Whether to fix camera
- `watermark`: Whether to include watermark
- `return_last_frame`: Whether to return last frame image
- `callback_url`: Callback URL for completion notification

**Returns:**
```json
{
  "status": "success",
  "data": {
    "id": "cgt-2025******-****"
  }
}
```

### get_video_task

Query task status and result.

**Parameters:**
- `task_id` (required): Task ID to query

**Returns:**
```json
{
  "status": "success",
  "data": {
    "id": "cgt-2025******-****",
    "model": "doubao-seedance-1-0-pro-250528",
    "status": "succeeded",
    "content": {
      "video_url": "https://...",
      "last_frame_url": "https://..."
    },
    "seed": 10,
    "resolution": "720p",
    "ratio": "16:9",
    "duration": 5,
    "framespersecond": 24,
    "usage": {
      "completion_tokens": 108900,
      "total_tokens": 108900
    }
  }
}
```

### list_video_tasks

List tasks with optional filters.

**Parameters:**
- `page_num`: Page number (default 1)
- `page_size`: Page size (default 10)
- `status`: Filter by status
- `task_ids`: Filter by task IDs
- `model`: Filter by model

### cancel_video_task

Cancel or delete a task.

**Parameters:**
- `task_id` (required): Task ID to cancel/delete

## Task Status

- `queued`: Waiting in queue
- `running`: Currently generating
- `succeeded`: Completed successfully
- `failed`: Failed
- `cancelled`: Cancelled (auto-deleted after 24h)

## Important Notes

1. **Video URL Expiration**: Generated video URLs are valid for 24 hours only
2. **Historical Data**: Only last 7 days of data can be queried
3. **Cancellation**: Only `queued` tasks can be cancelled
4. **Async Processing**: Video generation is asynchronous, poll status for results

## Example Usage

### Text-to-Video
```python
create_video_task(
    model="doubao-seedance-1-0-pro",
    prompt="一只猫在草地上玩耍",
    duration=5,
    ratio="16:9"
)
```

### Image-to-Video (First Frame)
```python
create_video_task(
    model="doubao-seedance-1-0-pro",
    prompt="镜头慢慢推进",
    image_url="https://example.com/image.jpg",
    duration=5
)
```

### Image-to-Video (First & Last Frame)
```python
create_video_task(
    model="doubao-seedance-1-0-pro",
    prompt="从开始到结束的过渡",
    first_frame_url="https://example.com/first.jpg",
    last_frame_url="https://example.com/last.jpg",
    duration=5
)
```
"""
    return docs
