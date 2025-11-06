# Volcengine Video Generation MCP Server

MCP (Model Context Protocol) server for Volcengine (Doubao/豆包) Video Generation API - Seedance models.

## Features

- ✅ **Text-to-Video Generation** - Generate videos from text prompts
- ✅ **Image-to-Video Generation** - Animate images with multiple modes:
  - First frame mode
  - First & last frame mode
  - Reference images mode (1-4 images)
- ✅ **Task Management** - Query, list, and cancel video generation tasks
- ✅ **Comprehensive Parameters** - Full control over resolution, ratio, duration, FPS, etc.
- ✅ **MCP Resources** - Server status, models list, and API documentation

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd volcengine-video-mcp
```

2. Install dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your Volcengine API key
```

Required environment variables:
- `ARK_API_KEY`: Your Volcengine API key ([Get one here](https://console.volcengine.com/ark))
- `ARK_BASE_URL`: (Optional) API base URL, defaults to `https://ark.cn-beijing.volces.com`

## Usage

### Running the Server

```bash
# Using uv
uv run python app/main.py

# Or if installed with pip
python app/main.py
```

### Using with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "volcengine-video": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/volcengine-video-mcp",
        "run",
        "python",
        "app/main.py"
      ],
      "env": {
        "ARK_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Tools

### create_video_task

Create a video generation task.

**Example - Text-to-Video:**
```python
create_video_task(
    model="doubao-seedance-1-0-pro",
    prompt="一只可爱的猫在草地上玩耍,阳光明媚",
    duration=5,
    ratio="16:9",
    resolution="1080p"
)
```

**Example - Image-to-Video (First Frame):**
```python
create_video_task(
    model="doubao-seedance-1-0-pro",
    prompt="镜头慢慢推进,展示更多细节",
    image_url="https://example.com/image.jpg",
    duration=5
)
```

**Example - Image-to-Video (First & Last Frame):**
```python
create_video_task(
    model="doubao-seedance-1-0-pro",
    prompt="从白天到夜晚的过渡",
    first_frame_url="https://example.com/day.jpg",
    last_frame_url="https://example.com/night.jpg",
    duration=8
)
```

**Parameters:**
- `model` (required): Model ID (see supported models below)
- `prompt` (required): Text description for video generation
- `image_url`: Single image URL for first-frame mode
- `first_frame_url`: First frame image URL
- `last_frame_url`: Last frame image URL
- `reference_image_urls`: List of 1-4 reference images
- `resolution`: 480p/720p/1080p
- `ratio`: 16:9/4:3/1:1/3:4/9:16/21:9/keep_ratio/adaptive
- `duration`: Video duration in seconds (2-12)
- `frames`: Number of frames (29-289, must satisfy 25+4n)
- `fps`: Frame rate (16/24)
- `seed`: Random seed (-1 to 2^32-1)
- `camera_fixed`: Whether to fix camera
- `watermark`: Whether to include watermark
- `return_last_frame`: Whether to return last frame image
- `callback_url`: Callback URL for task completion notification

### get_video_task

Query status and result of a video generation task.

```python
get_video_task(task_id="cgt-2025******-****")
```

### list_video_tasks

List video generation tasks with optional filters.

```python
list_video_tasks(
    page_num=1,
    page_size=10,
    status="succeeded"  # queued/running/cancelled/succeeded/failed
)
```

### cancel_video_task

Cancel or delete a video generation task.

```python
cancel_video_task(task_id="cgt-2025******-****")
```

## Resources

### status://server

Get server status and capabilities.

### models://list

Get list of supported models and their capabilities.

### docs://api

Get comprehensive API documentation.

## Supported Models

### Seedance Pro Series

- **doubao-seedance-1-0-pro** - High quality, supports all generation modes, max 12s
- **doubao-seedance-1-0-pro-fast** - Faster generation, text-to-video and first-frame mode

### Seedance Lite Series

- **doubao-seedance-1-0-lite-t2v** - Text-to-video, max 10s
- **doubao-seedance-1-0-lite-i2v** - Image-to-video with reference images support

## Important Notes

⚠️ **Video URL Expiration**: Generated video URLs are valid for 24 hours only. Download promptly!

⚠️ **Historical Data**: Only last 7 days of task history can be queried.

⚠️ **Cancellation Limits**: Only `queued` tasks can be cancelled. Running tasks cannot be cancelled.

⚠️ **Async Processing**: Video generation is asynchronous. Poll task status for results.

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Project Structure

```
volcengine-video-mcp/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── client.py            # HTTP client for Volcengine API
│   ├── tools/               # MCP tools
│   │   ├── create_video.py
│   │   ├── get_video.py
│   │   ├── list_videos.py
│   │   └── cancel_video.py
│   └── resources/           # MCP resources
│       └── server_info.py
├── tests/                   # Test suite
│   ├── test_config.py
│   └── test_resources.py
├── pyproject.toml          # Project configuration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Task Status Flow

```
queued → running → succeeded
                 ↘ failed

queued → cancelled (auto-deleted after 24h)
```

## License

MIT License

## Links

- [Volcengine Video Generation API Documentation](https://www.volcengine.com/docs/82379/1520757)
- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Specification](https://modelcontextprotocol.io/)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For issues and questions:
- Create an issue in this repository
- Contact Volcengine support for API-related questions
