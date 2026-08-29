"""
Knowledge Base Indexer Script — T-052, T-053.
Reads all documents from knowledge_base/, chunks them, embeds, and upserts into Qdrant.

Usage:
    python scripts/index_knowledge_base.py
    python scripts/index_knowledge_base.py --force-recreate
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.rag_service import (
    KNOWLEDGE_BASE_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    chunk_documents,
    embed_text,
    qdrant_client,
)

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import structlog

logger = structlog.get_logger()
EMBEDDING_DIM = 1536  # text-embedding-3-small


def detect_metadata(source: str, chunk_text: str) -> dict:
    """Extract OWASP/CWE IDs from file path and chunk text."""
    import re
    owasp_match = re.search(r"(A\d{2}:\d{4})", source + chunk_text)
    cwe_match = re.search(r"(CWE-\d+)", source + chunk_text)

    doc_type = "secure_coding"
    if "owasp" in source.lower():
        doc_type = "owasp"
    elif "cwe" in source.lower():
        doc_type = "cwe"

    return {
        "document_type": doc_type,
        "owasp_id": owasp_match.group(1) if owasp_match else None,
        "cwe_id": cwe_match.group(1) if cwe_match else None,
    }


def collect_documents() -> list[dict]:
    """T-052: Read all documents from knowledge_base/."""
    docs = []
    kb_path = Path(KNOWLEDGE_BASE_DIR)

    for ext in ("*.md", "*.txt"):
        for file_path in kb_path.rglob(ext):
            try:
                text = file_path.read_text(encoding="utf-8")
                rel_path = str(file_path.relative_to(kb_path))
                docs.append({"source": rel_path, "text": text})
                logger.info("Found document", source=rel_path, chars=len(text))
            except Exception as e:
                logger.warning("Could not read file", path=str(file_path), error=str(e))

    return docs


def ensure_collection(client: QdrantClient, force_recreate: bool = False) -> None:
    """Ensure the Qdrant collection exists with the correct schema."""
    existing = [c.name for c in client.get_collections().collections]

    if force_recreate and COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Deleted existing collection", collection=COLLECTION_NAME)
        existing = []

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection", collection=COLLECTION_NAME)


def index_knowledge_base(force_recreate: bool = False) -> int:
    """
    T-052: Main indexer — chunk, embed, upsert.
    Returns number of vectors indexed.
    """
    client = qdrant_client()
    ensure_collection(client, force_recreate=force_recreate)

    documents = collect_documents()
    if not documents:
        logger.warning("No documents found in knowledge_base/")
        return 0

    # Chunk all documents
    all_chunks = []
    for doc in documents:
        chunks = chunk_documents([doc["text"]], chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

    logger.info("Total chunks to index", count=len(all_chunks))

    # Embed and upsert in batches
    BATCH_SIZE = 20
    total_indexed = 0

    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        points = []

        for chunk in batch:
            try:
                vector = embed_text(chunk["text"])
                meta = detect_metadata(chunk["source"], chunk["text"])

                # Stable point ID from content hash
                content_hash = hashlib.md5(
                    f"{chunk['source']}_{chunk['chunk_index']}_{chunk['text'][:100]}".encode()
                ).hexdigest()
                point_id = int(content_hash[:8], 16)  # 32-bit int from hash

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "text": chunk["text"],
                            "source": chunk["source"],
                            "chunk_index": chunk["chunk_index"],
                            "total_chunks": chunk["total_chunks"],
                            **meta,
                        },
                    )
                )
            except Exception as e:
                logger.error("Failed to embed chunk", error=str(e), source=chunk["source"])

        if points:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            total_indexed += len(points)
            logger.info("Batch upserted", batch=i // BATCH_SIZE + 1, count=len(points))

    logger.info(
        "Knowledge base indexing complete",
        total_vectors=total_indexed,
        collection=COLLECTION_NAME,
    )
    return total_indexed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index CodeSentinel knowledge base into Qdrant")
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Delete and recreate the Qdrant collection before indexing",
    )
    args = parser.parse_args()

    count = index_knowledge_base(force_recreate=args.force_recreate)
    print(f"\n✅ Indexed {count} vectors into '{COLLECTION_NAME}'")
    if count == 0:
        print("⚠️  No vectors indexed — check that knowledge_base/ contains .md files")
        sys.exit(1)
