from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse


async def health_endpoint(request: Request) -> JSONResponse:
    """Health check endpoint for the MCP server."""
    try:
        return JSONResponse(
            {
                "status": "healthy",
            }
        )
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=500)


def create_app(mcp: FastMCP) -> Starlette:
    # Use FastMCP's own app which already has proper MCP routing
    app = mcp.streamable_http_app()
    # Add our health endpoint to the FastMCP app
    app.add_route("/health", health_endpoint, methods=["GET"])
    return app
