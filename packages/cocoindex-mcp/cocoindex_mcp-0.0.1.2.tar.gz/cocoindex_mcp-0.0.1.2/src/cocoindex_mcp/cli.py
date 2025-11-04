"""Command-line interface for the cocoindex MCP server."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable

from cocoindex_mcp import __version__, config
from cocoindex_mcp.db import DatabaseConnectionError, DatabaseConfigError, ensure_database_ready
from cocoindex_mcp.runtime import prepare

DESCRIPTION = "Run the cocoindex semantic code search MCP server over stdio."
ENVIRONMENT_HELP = """Environment Variables:
  COCOINDEX_DATABASE_URL  PostgreSQL connection string pointing at your cocoindex database (required)

Tools:
  cocoindex_search        Search for semantic code matches.
  cocoindex_info          Return metadata about the server and configuration hints.

Examples:
  uvx --from yalattas/cocoindex-mcp cocoindex-mcp --help
  uvx --from yalattas/cocoindex-mcp cocoindex-mcp --env COCOINDEX_DATABASE_URL=postgres://user:pass@localhost:5432/cocoindex
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cocoindex-mcp",
        description=DESCRIPTION,
        epilog=ENVIRONMENT_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"cocoindex-mcp {__version__}",
        help="Show the installed version and exit.",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity for the MCP server (default: INFO).",
    )

    return parser


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level, logging.INFO))


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    _configure_logging(args.log_level)

    prepare()

    try:
        ensure_database_ready()
    except (DatabaseConfigError, DatabaseConnectionError) as exc:
        parser.exit(status=2, message=f"{exc}\n")

    mcp_server = config.mcp

    try:
        mcp_server.run()
    except KeyboardInterrupt:  # pragma: no cover - graceful shutdown
        parser.exit(status=130)
    except Exception as exc:  # pragma: no cover - propagate unexpected failures
        parser.exit(status=1, message=f"Server stopped with error: {exc}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
