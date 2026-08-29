"""
RAG Knowledge Base utilities — T-050, T-051, T-052, T-054.

Handles document chunking, embedding, Qdrant indexing, and semantic search
over the OWASP/CWE/secure-coding security knowledge base.
"""

import os
import uuid
from pathlib import Path
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from google import genai
from google.genai import types
from app.core.config import settings
import structlog

logger = structlog.get_logger()


# ── T-050: Document chunking ──────────────────────────────────────────────────

def chunk_documents(
    text: str,
    chunk_size: int = None,
    overlap: int = None,
    source_metadata: dict | None = None,
) -> list[dict[str, Any]]:
    """T-050: Split text into overlapping chunks with metadata."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    chunks = []
    words = text.split()
    start = 0
    chunk_index = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_text = " ".join(words[start:end])
        chunk = {
            "text": chunk_text,
            "chunk_index": chunk_index,
            "metadata": source_metadata or {},
        }
        chunks.append(chunk)
        if end >= len(words):
            break
        start += chunk_size - overlap
        chunk_index += 1

    return chunks


# ── T-051: Embedding utility (Google text-embedding-004) ─────────────────────

_genai_client: genai.Client | None = None


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return _genai_client


def embed_text(text: str) -> list[float]:
    """T-051: Embed a document chunk for indexing (768-dim, text-embedding-004)."""
    client = _get_genai_client()
    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text[:8000],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return result.embeddings[0].values


def embed_query(text: str) -> list[float]:
    """Embed a search query with retrieval_query task_type (better recall)."""
    client = _get_genai_client()
    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text[:2000],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values


# ── Qdrant client ─────────────────────────────────────────────────────────────

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection_exists(client: QdrantClient) -> None:
    """Create Qdrant collection if it does not exist."""
    collections = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Qdrant collection created", name=settings.QDRANT_COLLECTION_NAME)


# ── T-052: Knowledge base indexing script ─────────────────────────────────────

def index_knowledge_base(knowledge_base_dir: str | None = None) -> int:
    """
    T-052: Read all docs from knowledge_base/, chunk, embed, and upsert to Qdrant.
    Returns the total number of chunks indexed.
    """
    if knowledge_base_dir is None:
        knowledge_base_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")

    client = get_qdrant_client()
    ensure_collection_exists(client)

    total_indexed = 0
    kb_path = Path(knowledge_base_dir)

    for doc_file in kb_path.rglob("*.md"):
        # Determine document type from folder name
        parts = doc_file.relative_to(kb_path).parts
        doc_type = parts[0] if len(parts) > 1 else "general"

        with open(doc_file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        if len(text.strip()) < 50:
            continue

        metadata = {
            "source": str(doc_file.name),
            "document_type": doc_type,
            "file_path": str(doc_file.relative_to(kb_path)),
        }

        # Extract OWASP/CWE IDs from filename or content
        fname = doc_file.name.upper()
        if "OWASP" in fname:
            metadata["owasp_id"] = fname.replace(".MD", "").replace("_", "-")
        if "CWE" in fname:
            metadata["cwe_id"] = fname.replace(".MD", "").replace("_", "-")

        chunks = chunk_documents(text, source_metadata=metadata)

        points = []
        for chunk in chunks:
            if len(chunk["text"].split()) < 10:
                continue
            try:
                vector = embed_text(chunk["text"])
                point_id = str(uuid.uuid4())
                points.append(PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={**chunk["metadata"], "text": chunk["text"], "chunk_index": chunk["chunk_index"]},
                ))
            except Exception as e:
                logger.warning("Failed to embed chunk", error=str(e), source=metadata["source"])

        if points:
            client.upsert(collection_name=settings.QDRANT_COLLECTION_NAME, points=points)
            total_indexed += len(points)
            logger.info("Indexed document", source=metadata["source"], chunks=len(points))

    logger.info("Knowledge base indexing complete", total_chunks=total_indexed)
    return total_indexed


# ── T-054: Semantic search ────────────────────────────────────────────────────

def search_knowledge(query_text: str, top_k: int = None) -> list[dict[str, Any]]:
    """T-054: Embed query and perform similarity search against Qdrant."""
    top_k = top_k or settings.RAG_TOP_K
    client = get_qdrant_client()

    query_vector = embed_query(query_text)  # use retrieval_query task_type for better recall
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "text": r.payload.get("text", ""),
            "source": r.payload.get("source", ""),
            "document_type": r.payload.get("document_type", ""),
            "owasp_id": r.payload.get("owasp_id"),
            "cwe_id": r.payload.get("cwe_id"),
            "score": r.score,
        }
        for r in results
    ]
