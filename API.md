# API.md — CodeSentinel

> **Scope note:** The source document specifies that the backend is **FastAPI** and exposes **REST APIs**, and it describes specific *flows* that require API calls (create scan, receive webhook, fetch PR diff, etc.). It does **not** provide a formal API contract — no endpoint paths, HTTP verbs, request/response payloads, auth headers, versioning scheme, or error format are defined. This document lists only the API *surface* implied by the described flows, without inventing exact routes, payload shapes, or status codes. Treat the endpoint names below as **conceptual groupings**, not a finalized spec.

## 1. Confirmed Backend Characteristics
- Framework: **FastAPI**
- Role (per source): "REST APIs and orchestration interface"
- Auth to GitHub: **GitHub OAuth / GitHub App**
- GitHub integration: **GitHub API** (repository + PR operations) and **GitHub Webhooks** (event triggers)

## 2. API Surface Implied by Described Flows

### 2.1 GitHub Authentication
- Flow described: "GitHub Integration — OAuth / API / Webhooks" as the entry layer before the FastAPI backend.
- Implies: an OAuth callback / GitHub App installation flow to obtain access to a developer's repositories.
- **Not specified**: exact OAuth scopes requested, token storage/refresh mechanism, or installation vs. user-token model.

### 2.2 Repository Scan Creation
Flow (Section 5, 24): `Developer → GitHub Integration → FastAPI Backend → Create Scan → Redis Queue → Scan Worker → Orchestrator`

Implied capability:
- An endpoint to **create a scan** for a selected repository, which enqueues the job to Redis for asynchronous processing rather than processing synchronously.

### 2.3 Pull Request Webhook Handling
Flow (Section 4.2, 19): `GitHub Webhook → Verify Webhook → Create Scan → Get PR Diff + Changed Files → Run Security Pipeline → Security Gate → GitHub Check / Comment`

Implied capability:
- A **webhook receiver endpoint** that:
  1. Verifies the incoming GitHub webhook (signature validation implied by the explicit "Verify Webhook" step).
  2. Creates a scan scoped to the PR.
  3. Triggers retrieval of the PR diff and changed files via the GitHub API.
  4. Enqueues the security pipeline run.
- After pipeline completion, the backend must call back to GitHub (via GitHub API) to **post a Check run and/or PR comment**.

### 2.4 Scan / Findings Retrieval
Implied by the Dashboard and Finding Detail View requirements (Sections 20–21):
- Capability to **retrieve scan results** for a repository (score, findings by severity, posture, trends).
- Capability to **retrieve a single finding's full detail** (severity, risk score, confidence, file/line, relevant code, root cause, impact, attack scenario, CWE, OWASP, AI explanation, suggested fix, historical status).

### 2.5 AI Security Assistant
Flow (Section 22): `Developer Question → Retrieve Findings/Repo Context/History/RAG → LLM → Contextual Answer`

Implied capability:
- An endpoint accepting a **free-form question** (optionally scoped to a repository/scan/finding) and returning an LLM-generated, RAG-grounded answer.

### 2.6 Remediation / Patch Validation
Flow (Section 15–16): Remediation Agent produces a suggested fix; Patch Validation applies it in an isolated environment and runs tests + Semgrep + Gitleaks + dependency scan.

Implied capability:
- Retrieval of a **suggested fix** for a given finding.
- A **patch validation trigger/status** capability — since validation runs in an isolated environment and produces PASS/FAIL, this is likely an asynchronous operation with a status to poll or a callback/event, though the source does not specify the mechanism.

## 3. Explicitly Out of Scope / Undefined
The source document does **not** define:
- Concrete endpoint paths (e.g., `/api/v1/scans`) — none are given in the source; any such paths in other documentation would be inferred, not sourced.
- Request/response JSON schemas for any endpoint (only the *internal* Finding and Repository Context objects are shown, as data models — not as API payloads).
- Authentication scheme for API consumers (e.g., bearer tokens, session cookies) beyond "GitHub OAuth / GitHub App" for GitHub access itself.
- Pagination, filtering, or sorting conventions.
- API versioning strategy.
- Rate limiting.
- Error response format / status code conventions.
- Whether the AI Security Assistant responses are streamed or returned as a single response.

## 4. Recommendation
Before implementation, a formal OpenAPI/Swagger contract should be authored covering the six capability groups above (2.1–2.6), with explicit request/response schemas, auth requirements, and error handling — none of which are present in the source material.
