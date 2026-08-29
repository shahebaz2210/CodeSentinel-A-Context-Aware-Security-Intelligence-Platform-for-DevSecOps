# CodeSentinel — A Context-Aware Security Intelligence Platform for DevSecOps

<div align="center">

![CodeSentinel](https://img.shields.io/badge/CodeSentinel-Security_Intelligence-00d4aa?style=for-the-badge&logo=shield)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-7c3aed?style=flat-square)

</div>

CodeSentinel is a context-aware security intelligence platform that integrates directly into your GitHub workflow to detect, analyze, and remediate security vulnerabilities using a 5-agent AI pipeline with deterministic risk scoring and policy enforcement.

---

## Architecture Overview

```
GitHub → Webhook → Celery Task → LangGraph Pipeline:
  Agent 1: Repository Analysis    (deterministic parsers + LLM context)
  Agent 2: Security Detection     (Semgrep + Gitleaks + Trivy)
  Agent 3: Security Intelligence  (RAG → OWASP/CWE-grounded LLM)
  Agent 4: Risk & Validation      (LLM factors → Deterministic Risk Engine)
  ★ Policy Gate                   (100% deterministic — no AI in gate)
  Agent 5: Remediation            (LLM suggestions → sandbox validation)
→ Results → PostgreSQL → Frontend Dashboard + GitHub Check Run + PR Comment
```

**Key design invariants:**
- Risk scores computed by a deterministic engine — never by an LLM directly
- Policy gate (PASS/WARNING/BLOCK) is 100% deterministic
- All AI output is clearly labelled; factual scan data is always visually separated from AI analysis
- Suggested fixes are always validated before being trusted (apply → test → rescan)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI 0.115, Python 3.12 |
| Agent Orchestration | LangGraph |
| Task Queue | Celery 5 + Redis |
| Database | PostgreSQL 16 + SQLAlchemy 2 |
| Vector Database | Qdrant |
| AI / LLM | OpenAI API (GPT-4o) |
| Scanners | Semgrep, Gitleaks, Trivy |
| Frontend | Next.js 15, TypeScript |
| CI/CD | GitHub Actions |
| Deployment | Docker + docker-compose |

---

## Prerequisites

Before running locally, ensure you have:

- **Docker Desktop** (v24+)
- **Git**
- A **GitHub OAuth App** with:
  - Authorization callback URL: `http://localhost:8000/auth/github/callback`
  - Scopes: `repo`, `read:user`
- An **OpenAI API key** (GPT-4o or GPT-4o-mini)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/CodeSentinel.git
cd CodeSentinel
```

### 2. Configure environment variables

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and fill in required values

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local
```

**Required variables in `backend/.env`:**

```dotenv
# Database
DATABASE_URL=postgresql+psycopg2://cs_user:cs_password@localhost:5432/codesentinel

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# Security
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">

# GitHub OAuth
GITHUB_CLIENT_ID=<your-github-oauth-app-client-id>
GITHUB_CLIENT_SECRET=<your-github-oauth-app-client-secret>
GITHUB_WEBHOOK_SECRET=<random-secret-for-webhook-verification>

# AI
OPENAI_API_KEY=<your-openai-api-key>
LLM_MODEL=gpt-4o-mini

# App
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000
APP_ENV=development
```

**Required variables in `frontend/.env.local`:**

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start all services

```bash
docker-compose up -d
```

This starts 5 services:
- `postgres` — PostgreSQL 16 (port 5432)
- `redis` — Redis 7 (port 6379)
- `qdrant` — Qdrant vector DB (port 6333)
- `backend` — FastAPI (port 8000)
- `worker` — Celery worker

### 4. Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Index the security knowledge base

```bash
docker-compose exec backend python scripts/index_knowledge_base.py
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## API Documentation

Once the backend is running, interactive API docs are available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/unit -v

# All backend tests
pytest tests/ -v

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend lint
npm run lint
```

---

## Design & Specification Documents

| Document | Description |
|---|---|
| [PRD.md](docs/PRD.md) | Product Requirements |
| [Architecture.md](docs/Architecture.md) | System Architecture |
| [AI-instructions.md](docs/AI-instructions.md) | AI Agent Behaviour Rules |
| [DesignDoc.md](docs/DesignDoc.md) | UI/UX Design System |
| [API.md](docs/API.md) | API Reference |
| [Database.md](docs/Database.md) | Database Schema |
| [Security.md](docs/Security.md) | Security Architecture |
| [Deployment.md](docs/Deployment.md) | Deployment Guide |

---

## Contributing

1. Fork and create a feature branch
2. All CI checks must pass before merge (backend lint/test, frontend lint/typecheck, docker build)
3. Follow the AI behaviour rules in `AI-instructions.md` — especially §7 (no LLM in gates) and §9 (PR framing)

---

## License

MIT License — see [LICENSE](LICENSE)
