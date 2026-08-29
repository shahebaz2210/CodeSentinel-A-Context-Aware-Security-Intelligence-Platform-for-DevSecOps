# Techstack.md — CodeSentinel

This is the finalized technology stack exactly as specified in the source document (Section 23, "Final Technology Stack"). No substitutions or additions have been made.

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js + React + TypeScript | Security dashboard |
| Styling | Tailwind CSS | UI |
| Backend | FastAPI | REST APIs and orchestration interface |
| Authentication | GitHub OAuth / GitHub App | GitHub access |
| Git Integration | GitHub API | Repository and PR operations |
| Events | GitHub Webhooks | Automatic PR scan triggers |
| Orchestration | LangGraph | Multi-agent workflow/state |
| LLM | Configurable LLM provider | AI reasoning |
| Agent Runtime | Python | Agent implementation |
| Static Analysis | Semgrep | Code security |
| Secret Detection | Gitleaks | Secret detection |
| Dependency Scanning | Trivy | Dependency/security scanning |
| Database | PostgreSQL | Application state and security memory |
| Queue | Redis | Background scan jobs |
| Workers | Celery / worker service | Long-running scans |
| Embeddings | Embedding model (unspecified/configurable) | Semantic representation |
| Vector DB | Qdrant | RAG retrieval |
| RAG | Custom / LangChain | Security knowledge retrieval |
| Containers | Docker | Isolation and reproducibility |
| CI/CD | GitHub Actions | Build, test, deployment |
| Deployment | Cloud / Kubernetes | Production hosting |

## Notes on Ambiguity (explicitly left open by the source)
- **LLM provider**: described only as "Configurable LLM provider" — no specific vendor (OpenAI, Anthropic, etc.) or model is named.
- **Embedding model**: not named — left as a general "Embedding model" component.
- **Cloud provider**: "Cloud / Kubernetes" is generic — no specific provider (AWS/GCP/Azure) or managed Kubernetes service is specified.
- **RAG implementation**: described as "Custom / LangChain" — the source does not commit to one or the other; this should be clarified during technical design.

## Cross-cutting Architectural Decisions (stated in source)
- PostgreSQL and Qdrant serve **distinct, non-overlapping roles**: PostgreSQL for structured application/scan state, Qdrant strictly for embeddings/semantic retrieval — Qdrant is explicitly *not* a substitute for PostgreSQL.
- All long-running scans should run **asynchronously**, via Redis queue + Celery/worker service, preferably inside isolated containers (Docker).
- LangGraph is the designated orchestrator for the 5-agent pipeline (Repository Analysis → Security Detection → Security Intelligence → Risk & Validation → Remediation).
