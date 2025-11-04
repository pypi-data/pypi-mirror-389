from __future__ import annotations

from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from cocoindex_mcp import runtime
from cocoindex_mcp.search import SEARCH_LIMIT_MAX, search_simple

SERVER_NAME = "cocoindex-mcp"
ENVIRONMENT_VARIABLES = {
    "COCOINDEX_DATABASE_URL": "PostgreSQL connection string pointing to your cocoindex database (required)",
}


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""

    runtime.prepare()

    server = FastMCP(SERVER_NAME)

    @server.tool()
    def cocoindex_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search cocoindex for code snippets using semantic similarity."""

        capped_limit = max(1, min(limit, SEARCH_LIMIT_MAX))
        return search_simple(query, capped_limit)

    @server.tool()
    def cocoindex_info() -> Dict[str, Any]:
        """Return metadata about the cocoindex MCP server."""

        return {
            "name": SERVER_NAME,
            "description": "Semantic code search over a cocoindex Postgres database.",
            "environment": ENVIRONMENT_VARIABLES,
            "tools": {
                "cocoindex_search": {
                    "description": "Search for code by natural language or code snippets.",
                    "parameters": {
                        "query": "The natural language or code query to search for.",
                        "limit": f"Maximum number of results to return (1-{SEARCH_LIMIT_MAX}).",
                    },
                }
            },
            "maintainer": {
                "username": "yalattas",
                "email": "y.alattas@gmail.com",
            },
        }

    return server


mcp = create_server()