# CodeSentinel — Knowledge Base Indexing Guide

The Security Knowledge Base provides RAG (Retrieval-Augmented Generation) context to the
Security Intelligence Agent (Agent 3) and the AI Security Assistant.

It is stored in Qdrant (vector database) under the collection `security_knowledge`.

---

## Document Sources

Knowledge base documents are stored in:

```
backend/app/knowledge_base/
├── owasp/
│   └── OWASP-TOP-10-2021.md       # OWASP Top 10 categories
├── cwe/
│   └── CWE-COMMON-WEAKNESSES.md   # CWE descriptions for top weaknesses
└── secure_coding/
    └── SECURE-CODING-GUIDELINES.md # Secure coding practices
```

---

## Running the Indexer

### First-time setup (index all documents)

```bash
# From the backend directory or inside the backend container
python scripts/index_knowledge_base.py
```

Or via Docker:

```bash
docker-compose exec backend python scripts/index_knowledge_base.py
```

### What the indexer does

1. **Reads** all `.md` and `.txt` files from `knowledge_base/` recursively
2. **Chunks** each document into overlapping 512-token windows (64-token overlap)
3. **Embeds** each chunk using `text-embedding-3-small` (OpenAI)
4. **Upserts** all chunks into the `security_knowledge` Qdrant collection
5. **Sets metadata** on each vector: `source`, `document_type`, `owasp_id` (if applicable), `cwe_id` (if applicable)

---

## Adding New Documents

### Adding a new OWASP document

1. Create a new `.md` file in `backend/app/knowledge_base/owasp/`
2. Use the same structure as existing files: `## A0X:YYYY - Category Name` headings
3. Include the OWASP ID in the heading so the indexer can extract it as metadata
4. Re-run the indexer

### Adding a new CWE document

1. Create a new `.md` file in `backend/app/knowledge_base/cwe/`
2. Use `## CWE-NNN: Name` headings
3. Re-run the indexer

### Adding secure coding guidelines

1. Create a new `.md` file in `backend/app/knowledge_base/secure_coding/`
2. Organize with `##` section headings for different topics
3. Re-run the indexer

---

## Verifying Qdrant Collection Health

### Check collection exists and has vectors

```bash
curl http://localhost:6333/collections/security_knowledge | python -m json.tool
```

Expected response includes:
```json
{
  "result": {
    "status": "green",
    "vectors_count": <N>,
    "points_count": <N>
  }
}
```

### Test a search query

```python
from app.services.rag_service import search_knowledge

results = search_knowledge("SQL injection prevention", top_k=3)
for r in results:
    print(r['source'], r['score'], r['text'][:100])
```

### Via Docker

```bash
docker-compose exec backend python -c "
from app.services.rag_service import search_knowledge
results = search_knowledge('SQL injection')
print(f'Retrieved {len(results)} documents')
for r in results:
    print(f'  [{r[\"score\"]:.3f}] {r[\"source\"]}: {r[\"text\"][:80]}')
"
```

---

## Re-indexing

Re-running the indexer is safe — it **upserts** (not inserts), so duplicate documents
are updated, not duplicated. The `point_id` is derived from a hash of the chunk content,
ensuring idempotent indexing.

To force a full re-index (delete and recreate collection):

```bash
docker-compose exec backend python scripts/index_knowledge_base.py --force-recreate
```

---

## Chunk Configuration

Chunking parameters can be adjusted in `app/services/rag_service.py`:

```python
CHUNK_SIZE = 512     # tokens per chunk
CHUNK_OVERLAP = 64   # overlap between consecutive chunks
```

Larger chunks → better context per retrieval, but higher token usage in LLM prompts.
Smaller chunks → more precise retrieval, but may lose surrounding context.

---

## Qdrant Collection Schema

Each vector point has the following payload schema:

```json
{
  "text": "The chunked document text",
  "source": "owasp/OWASP-TOP-10-2021.md",
  "document_type": "owasp",
  "owasp_id": "A03:2021",
  "cwe_id": "CWE-89",
  "chunk_index": 2,
  "total_chunks": 5
}
```
