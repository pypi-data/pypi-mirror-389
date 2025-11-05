from mcp.server.fastmcp import FastMCP

from .api_client import create_authenticated_client


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("komodor://clusters")
    async def clusters() -> list[str]:
        """Get clusters information."""
        try:
            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.get_clusters()
                if response and hasattr(response, "data"):
                    return [cluster.name for cluster in response.data.clusters]
                else:
                    raise Exception("No cluster data available")
        except Exception as e:
            raise Exception(f"Failed to get clusters: {str(e)}") from e
