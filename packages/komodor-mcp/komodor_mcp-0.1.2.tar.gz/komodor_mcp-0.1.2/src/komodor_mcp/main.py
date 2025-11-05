"""Main entry point for Komodor MCP server."""

import argparse
import os

import structlog
import uvicorn
from mcp.server.fastmcp import FastMCP

from komodor_mcp.config import config, logger
from komodor_mcp.prompts import register_prompts
from komodor_mcp.resources import register_resources
from komodor_mcp.server import create_app
from komodor_mcp.tools import register_tools

# Enable remote debugging
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    import debugpy

    try:
        debugpy.listen(("0.0.0.0", 5678))
        print("Debugger listening on port 5678")
        print("Attach your debugger to localhost:5678")
    except RuntimeError as e:
        if "already been called" in str(e):
            print("Debugger already listening on port 5678")
        else:
            raise

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

mcp = FastMCP("Komodor")
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def run_stdio_server() -> None:
    """Run the MCP server using stdio transport."""
    mcp.run(transport="stdio")


def run_http_server() -> None:
    """Run the MCP server using HTTP transport."""
    logger.info("Starting Komodor MCP Server (HTTP transport)")
    logger.info(
        f"Server will be available at http://{config.MCP_SERVER_HOST}:{config.MCP_SERVER_PORT}"
    )
    app = create_app(mcp=mcp)
    uvicorn.run(
        app, host=config.MCP_SERVER_HOST, port=config.MCP_SERVER_PORT, log_level="info"
    )


def main() -> None:
    """Start the MCP server with specified transport."""
    parser = argparse.ArgumentParser(description="Komodor MCP Server")
    parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
        help="Transport mode: http (default) or stdio for local development",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        config.MCP_TRANSPORT = "stdio"
        run_stdio_server()
    elif args.transport == "http":
        config.MCP_TRANSPORT = "http"
        run_http_server()
    else:
        raise ValueError(f"Invalid transport: {args.transport}")


if __name__ == "__main__":
    main()
