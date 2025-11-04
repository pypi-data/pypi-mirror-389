"""Database helpers for the cocoindex MCP server."""

from __future__ import annotations

import os
from contextlib import contextmanager
from functools import cache
from typing import Iterator
from urllib.parse import urlsplit, urlunsplit

from pgvector.psycopg import register_vector
from psycopg import OperationalError
from psycopg_pool import ConnectionPool, PoolTimeout

ENV_VAR = "COCOINDEX_DATABASE_URL"


class DatabaseConfigError(RuntimeError):
    """Raised when the database connection URL is missing."""


class DatabaseConnectionError(RuntimeError):
    """Raised when connecting to the database fails."""


def _database_url() -> str:
    value = os.getenv(ENV_VAR)
    if not value:
        raise DatabaseConfigError(
            "COCOINDEX_DATABASE_URL is not set. Provide a Postgres connection string, "
            "for example: postgres://user:password@host:5432/database"
        )
    return value


def _mask_connection(url: str) -> str:
    try:
        parsed = urlsplit(url)
        netloc = parsed.hostname or "localhost"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        redacted = urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
        return redacted or "postgres://<host>/<database>"
    except Exception:  # pragma: no cover - defensive
        return "postgres://<host>/<database>"


@cache
def connection_pool() -> ConnectionPool:
    """Create or return the shared connection pool."""

    return ConnectionPool(conninfo=_database_url())


@contextmanager
def get_connection() -> Iterator:
    """Yield a database connection with pgvector registered."""

    url = None
    try:
        url = _database_url()
        with connection_pool().connection() as conn:
            register_vector(conn)
            yield conn
    except DatabaseConfigError:
        raise
    except (OperationalError, PoolTimeout) as exc:
        masked = _mask_connection(url or "")
        raise DatabaseConnectionError(
            f"Could not connect to Postgres at {masked}. Check credentials and availability."
        ) from exc
    except Exception as exc:  # pragma: no cover - unexpected failures
        masked = _mask_connection(url or "")
        raise DatabaseConnectionError(
            f"Unexpected database error while connecting to {masked}: {exc}"
        ) from exc


def ensure_database_ready() -> None:
    """Eagerly verify that a database connection can be established."""

    with get_connection():
        pass
