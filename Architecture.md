# Architecture.md — CodeSentinel

All diagrams and structure below are reproduced/organized directly from the source technical overview.

## 1. High-Level System Architecture
```
Developer
  │
  ├──────────── Repository Scan
  │
  └──────────── Pull Request
        │
        ▼
  GitHub Integration
  (OAuth / API / Webhooks)
        │
        ▼
  FastAPI Backend
        │
        ▼
    Create Scan
        │
        ▼
    Redis Queue
        │
        ▼
    Scan Worker
        │
        ▼
    Orchestrator (LangGraph)
        │
  ┌─────┼─────┐
  ▼     ▼     ▼
Agent 1 Agent 2 Agent 3
Repo    Security Security
Analysis Detection Intelligence
        │
  Embeddings + Qdrant
        │
        ▼
      LLM/RAG
        │
        ▼
     Agent 4
  Risk & Validation
        │
        ▼
     Agent 5
  Remediation
        │
        ▼
  Patch Validation
        │
        ▼
Dashboard / GitHub / Report
        │
        ▼
    Developer
```

## 2. End-to-End Flow (both scan types converge on one pipeline)
```
DEVELOPER
  │
  ┌─────────────┴──────────────┐
  │                             │
  ▼                             ▼
Repository Scan            Pull Request
  │                             │
  │                      GitHub Webhook
  │                             │
  └─────────────┬──────────────┘
                ▼
          GitHub Layer
                │
                ▼
         FastAPI Backend
                │
                ▼
            Create Scan
                │
                ▼
            Redis Queue
                │
                ▼
            Scan Worker
                │
                ▼
            ORCHESTRATOR
                │
                ▼
     Agent 1: Repository Analysis
                │
                ▼
     Agent 2: Security Detection
                │
                ▼
        Normalized Findings
                │
                ▼
     Agent 3: Security Intelligence
                │
                ▼
        Embeddings + Qdrant
                │
                ▼
           OWASP / CWE
                │
                ▼
             LLM / RAG
                │
                ▼
     Agent 4: Risk & Validation
                │
                ▼
      Deterministic Risk Engine
                │
                ▼
       Security Policy Gate
                │
                ▼
       Agent 5: Remediation
                │
                ▼
          Suggested Fix
                │
                ▼
         Patch Validation
                │
                ▼
   Dashboard / GitHub / Report
                │
                ▼
            DEVELOPER
                │
     ┌─────────┴─────────┐
     ▼                   ▼
  APPROVE          REQUEST CHANGES
     │                   │
     ▼                   ▼
   MERGE            FIX + RESCAN
```

## 3. Component Responsibilities

### 3.1 Multi-Agent Pipeline (orchestrated via LangGraph)
| Agent | Primary Responsibility | Main Inputs / Outputs |
|---|---|---|
| Agent 1 — Repository Analysis | Understand application structure and context | Repository → Repository Context |
| Agent 2 — Security Detection | Coordinate deterministic security scanning | Code → Semgrep/Gitleaks/Trivy Findings |
| Agent 3 — Security Intelligence | Retrieve and interpret trusted security knowledge | Findings → RAG/Vector Search → Security Context |
| Agent 4 — Risk & Validation | Assess finding validity and contextual risk | Finding + Context → Risk Factors |
| Agent 5 — Remediation | Generate context-aware remediation guidance | Finding + Context → Suggested Fix |

### 3.2 Supporting Infrastructure
- **FastAPI Backend** — REST API layer and orchestration entry point.
- **Redis Queue + Scan Worker(s) (Celery/worker service)** — decouples request handling from long-running scan execution; enables async processing.
- **PostgreSQL** — structured application state + historical security memory (Security Memory).
- **Qdrant** — vector store for embeddings, used strictly for RAG/semantic retrieval over the security knowledge base (OWASP/CWE/secure coding guidance).
- **Docker** — isolation/reproducibility, including the isolated environment used for Patch Validation.
- **GitHub Actions** — CI/CD for CodeSentinel itself (build, test, deployment).

## 4. Architectural Design Principles (explicit in source, Section 26)
- Deterministic scanners provide evidence; AI provides contextual reasoning — the two are not conflated.
- RAG grounds AI analysis in curated security knowledge rather than relying on model memory alone.
- PostgreSQL stores structured application and security history.
- Qdrant stores embeddings for semantic security-knowledge retrieval only.
- The final numerical risk score is generated through deterministic rules, not open-ended LLM judgment.
- Generated patches are suggestions and must be validated before being trusted.
- PR approval and merge remain completely under developer/reviewer control at all times.
- Repository and PR scans share the same core security-analysis pipeline (no divergent logic paths).
- All long-running scans should execute asynchronously, preferably in isolated containers.

## 5. Project Positioning (why this architecture, per source Section 27)
CodeSentinel is explicitly positioned as **more than an LLM-based code scanner**. Its architectural differentiation comes from the *integration* of:
- GitHub (source of truth for code + PRs)
- Deterministic DevSecOps scanners (evidence layer)
- Repository context (Agent 1)
- Historical security memory (PostgreSQL)
- Embeddings/vector search (Qdrant)
- RAG (grounding layer)
- Multi-agent reasoning (LangGraph orchestration)
- Deterministic policy enforcement (Security Gate)
- AI-assisted remediation (Agent 5 + Patch Validation)
- Human-in-the-loop developer decision-making (final control point)

## 6. Explicitly Out of Scope in Source
The document does not specify: network topology, service-to-service auth, scaling strategy per component, observability/monitoring stack, or a formal deployment topology beyond "Cloud / Kubernetes." See `Deployment.md` for what is and isn't defined there.
