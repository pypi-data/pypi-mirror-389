"""Cocoindex MCP server package."""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - best effort during development
    __version__ = version("cocoindex-mcp")
except PackageNotFoundError:  # pragma: no cover - local checkout
    __version__ = "0.dev0"

from .config import create_server, mcp  # noqa: E402  (imported late for registration)

__all__ = ["__version__", "create_server", "mcp"]
