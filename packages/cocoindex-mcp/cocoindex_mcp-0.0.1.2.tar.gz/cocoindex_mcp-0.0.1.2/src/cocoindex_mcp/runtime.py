"""Runtime helpers for preparing the cocoindex MCP server."""

from __future__ import annotations

import functools

from dotenv import load_dotenv

import cocoindex


@functools.lru_cache(maxsize=1)
def prepare() -> None:
    """Ensure environment variables and cocoindex runtime are initialized."""

    load_dotenv()
    cocoindex.init()
