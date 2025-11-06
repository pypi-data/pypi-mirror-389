"""Main entry point for Volcengine Video Generation MCP Server."""

from fastmcp import FastMCP

from app.config import Config
from app.resources.server_info import get_api_docs, get_models_list, get_server_status
from app.tools.cancel_video import cancel_video_task
from app.tools.create_video import create_video_task
from app.tools.get_video import get_video_task
from app.tools.list_videos import list_video_tasks

# Validate configuration on startup
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please set ARK_API_KEY environment variable")
    exit(1)

# Initialize FastMCP server
mcp = FastMCP(Config.SERVER_NAME)

# Register tools
mcp.tool()(create_video_task)
mcp.tool()(get_video_task)
mcp.tool()(list_video_tasks)
mcp.tool()(cancel_video_task)

# Register resources
mcp.resource("status://server")(get_server_status)
mcp.resource("models://list")(get_models_list)
mcp.resource("docs://api")(get_api_docs)

if __name__ == "__main__":
    mcp.run()
