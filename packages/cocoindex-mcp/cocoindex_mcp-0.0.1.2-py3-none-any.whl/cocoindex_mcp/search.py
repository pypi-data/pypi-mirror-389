"""Cocoindex search operations exposed via MCP."""

import os
from typing import Any, Dict, List, Optional

import cocoindex
import numpy as np
from numpy.typing import NDArray

from cocoindex_mcp.db import DatabaseConnectionError, DatabaseConfigError, get_connection
from cocoindex_mcp.runtime import prepare

DEFAULT_LIMIT = 10
SEARCH_LIMIT_MAX = 50


@cocoindex.transform_flow()
def code_to_embedding(
    text: cocoindex.DataSlice[str],
) -> cocoindex.DataSlice[NDArray[np.float32]]:
    """Embed the text using a SentenceTransformer model."""

    return text.transform(
        cocoindex.functions.SentenceTransformerEmbed(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
    )


@cocoindex.flow_def(name="CodeEmbedding")
def code_embedding_flow(
    flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope
) -> None:
    """Define the flow that embeds files into a vector database."""

    data_scope["files"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path=os.path.join("..", ".."),
            included_patterns=["*.py", "*.rs", "*.toml", "*.md", "*.mdx"],
            excluded_patterns=["**/.*", "target", "**/node_modules"],
        )
    )
    code_embeddings = data_scope.add_collector()

    with data_scope["files"].row() as file:
        file["language"] = file["filename"].transform(
            cocoindex.functions.DetectProgrammingLanguage()
        )
        file["chunks"] = file["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language=file["language"],
            chunk_size=1000,
            min_chunk_size=300,
            chunk_overlap=300,
        )
        with file["chunks"].row() as chunk:
            chunk["embedding"] = chunk["text"].call(code_to_embedding)
            code_embeddings.collect(
                filename=file["filename"],
                location=chunk["location"],
                code=chunk["text"],
                embedding=chunk["embedding"],
                start=chunk["start"],
                end=chunk["end"],
            )

    code_embeddings.export(
        "code_embeddings",
        cocoindex.targets.Postgres(),
        primary_key_fields=["filename", "location"],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="embedding",
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
            )
        ],
    )


@code_embedding_flow.query_handler(
    result_fields=cocoindex.QueryHandlerResultFields(
        embedding=["embedding"], score="score"
    )
)
def search(query: str, limit: int = DEFAULT_LIMIT) -> cocoindex.QueryOutput:
    """Search for code snippets in the cocoindex database using semantic similarity."""

    prepare()

    limit = max(1, min(limit, SEARCH_LIMIT_MAX))

    table_name = cocoindex.utils.get_target_default_name(
        code_embedding_flow, "code_embeddings"
    )

    query_vector = code_to_embedding.eval(query)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT filename, code, embedding, embedding <=> %s AS distance, start, "end"
                FROM {table_name} ORDER BY distance LIMIT %s
            """,
                (query_vector, limit),
            )
            rows = cur.fetchall()

    return cocoindex.QueryOutput(
        query_info=cocoindex.QueryInfo(
            embedding=query_vector,
            similarity_metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
        ),
        results=[
            {
                "filename": row[0],
                "code": row[1],
                "embedding": row[2],
                "score": 1.0 - row[3],
                "start": row[4],
                "end": row[5],
            }
            for row in rows
        ],
    )


def _extract_line(value: Any) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, dict):
        maybe_line = value.get("line")
        if maybe_line is None:
            return None
        try:
            return int(maybe_line)
        except (TypeError, ValueError):
            return None

    if isinstance(value, (list, tuple)):
        for candidate in value:
            try:
                return int(candidate)
            except (TypeError, ValueError):
                continue
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def search_simple(query: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """Return a simplified view of the search results suitable for MCP tools."""

    try:
        result = search(query, limit)
    except (DatabaseConfigError, DatabaseConnectionError) as exc:
        return [{"error": str(exc)}]
    except Exception as exc:  # pragma: no cover - surfaced back to the caller
        return [{"error": f"Search failed: {exc}"}]

    simplified: List[Dict[str, Any]] = []
    for item in result.results:
        start_line = _extract_line(item.get("start"))
        end_line = _extract_line(item.get("end"))
        simplified.append(
            {
                "filename": item.get("filename"),
                "code": item.get("code"),
                "score": float(item.get("score", 0.0)),
                "start_line": start_line,
                "end_line": end_line,
            }
        )

    return simplified