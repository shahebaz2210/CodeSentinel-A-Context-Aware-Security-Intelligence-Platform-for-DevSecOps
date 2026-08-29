# Product Requirements Document (PRD)

## 1. Project Name
**CodeSentinel** — *A Context-Aware Security Intelligence Platform for DevSecOps*

## 2. Purpose
CodeSentinel is an AI-powered DevSecOps security intelligence platform designed to help developers **identify, understand, prioritize, and remediate** application-security issues. It combines deterministic security scanners with repository context, historical security memory, embeddings/vector search, retrieval-augmented generation (RAG), multi-agent reasoning, a deterministic security policy gate, and AI-assisted remediation.

The platform supports two scanning modes:
- **Repository Scan** — full codebase assessment.
- **Pull Request (PR) Scan** — focused analysis of changed code, triggered automatically via GitHub webhook.

For PRs, CodeSentinel analyzes the change and reports its security posture, but **final approval and merge decisions remain entirely with the developer/reviewer** — CodeSentinel never auto-approves or auto-merges.

## 3. Problem Statement
Modern development practices and AI-assisted coding increase software delivery speed but also increase the probability of introducing security vulnerabilities. Traditional DevSecOps scanners are effective at *detecting* many issues, but their raw output can be difficult for developers to interpret in application context. Developers need more than a finding — they need to understand:

1. Root cause
2. Exploitability
3. Impact
4. Priority
5. The appropriate remediation

**Problem funnel (as defined in the source spec):**
```
Vulnerability Detection
        ↓
Understanding the Vulnerability
        ↓
Assessing Actual Risk
        ↓
Finding the Correct Fix
        ↓
Validating the Fix
```

## 4. Target Users
Based on the source material, the platform is designed around:
- **Developers** — write code, create PRs, need context-rich, actionable security feedback.
- **Reviewers / Maintainers** — approve or reject PRs; retain final merge authority.
- **Security-conscious engineering teams / organizations** — need repository-wide security posture, historical trend tracking, and organizational policy enforcement (via the Security Gate).

> Note: The source document does not specify company size, industry vertical, or a named buyer persona (e.g., "security engineer" vs. "platform engineering team" as a distinct role). This PRD treats "developer/reviewer" as the primary user, per explicit and repeated references in the source.

## 5. Proposed Solution (Summary)
CodeSentinel provides a context-aware security analysis pipeline that combines conventional security tooling with AI reasoning. The system:
1. Establishes repository or PR context.
2. Runs security scanners (Semgrep, Gitleaks, Trivy).
3. Normalizes findings into a common schema.
4. Retrieves relevant security knowledge via RAG (OWASP, CWE, secure-coding guidance).
5. Evaluates risk using a deterministic risk engine.
6. Generates AI-assisted remediation guidance.
7. Validates any suggested patch in an isolated environment before it's shown as trustworthy.
8. Applies a deterministic policy gate (PASS / WARNING / BLOCK).
9. Surfaces everything on a developer dashboard and/or directly on the GitHub PR.

## 6. Core Features
| # | Feature | Description |
|---|---------|-------------|
| 1 | Repository Scan | Full codebase, dependency, secret, and configuration analysis |
| 2 | Pull Request Scan | Automated, webhook-triggered scan of PR diffs/changed files |
| 3 | Multi-Agent Security Pipeline | 5-agent pipeline: Repository Analysis → Security Detection → Security Intelligence → Risk & Validation → Remediation |
| 4 | Finding Normalization | Unifies Semgrep/Gitleaks/Trivy outputs into one schema |
| 5 | RAG-Grounded Security Intelligence | Embeddings + Qdrant vector search over OWASP/CWE/secure coding guidance |
| 6 | Security Memory | Historical PostgreSQL-backed scan comparison (new/resolved/recurring/unchanged findings) |
| 7 | Deterministic Risk Scoring | Risk score computed by a backend rules engine (not the LLM) from severity, exploitability, confidence, exposure, business impact |
| 8 | AI-Assisted Remediation | Explanation + secure coding guidance + suggested fix per finding |
| 9 | Patch Validation | AI-suggested patches tested in an isolated environment (tests + re-scan) before being shown as trustworthy |
| 10 | AI Security Policy Gate | Deterministic PASS/WARNING/BLOCK evaluation against org security policy |
| 11 | Human-in-the-Loop PR Approval | CodeSentinel never merges; developer/reviewer retains full control |
| 12 | Developer Dashboard | Security score, findings by severity, posture, trends, finding detail views |
| 13 | AI Security Assistant | Conversational Q&A over current findings, repo context, history, and RAG knowledge |

## 7. User Stories
Derived directly from the described workflows and capabilities:

- As a **developer**, I want to trigger a full repository scan so that I can understand my project's overall security posture.
- As a **developer**, I want my Pull Requests to be automatically scanned when created or updated so that I get security feedback without extra manual steps.
- As a **developer**, I want each finding explained in plain language (root cause, impact, attack scenario) so that I don't have to interpret raw scanner output.
- As a **developer**, I want a suggested fix for a finding so that I can remediate it faster.
- As a **developer**, I want AI-suggested patches to be validated (tests + re-scan) before I trust them, so that I don't apply an unsafe fix.
- As a **reviewer**, I want the PR check/comment to show a clear security result (PASS/WARNING/BLOCK) so I can decide whether to approve.
- As a **reviewer**, I want to retain final approval/merge authority regardless of the scan result, so automation never overrides human judgment.
- As a **developer**, I want to see how my security score changed over time (new, resolved, recurring, regressed findings) so I can track improvement or regression.
- As a **developer**, I want to ask a conversational assistant questions like "why is this critical?" or "what should I fix first?" so I can get contextual answers without digging through raw findings.
- As an **organization**, I want deterministic security policies (e.g., "critical vulnerability → BLOCK", "exposed secret → BLOCK") enforced automatically on every scan so that policy compliance isn't dependent on manual review.

> Note: The source document does not include stories for user account management, team/org administration, billing, or onboarding flows. These are not defined and are intentionally excluded here.

## 8. User Flows

### 8.1 Repository Scan Flow
```
Developer selects a GitHub repository → Full assessment starts
→ Repository Analysis (Agent 1) → Security Detection (Agent 2)
→ Finding Normalization → Security Intelligence / RAG (Agent 3)
→ Risk & Validation (Agent 4) → Deterministic Risk Engine
→ Security Policy Gate → Remediation (Agent 5) → Patch Validation
→ Dashboard / Report → Developer reviews results
```

### 8.2 Pull Request Scan Flow
```
Developer creates/updates PR → GitHub Webhook fires
→ CodeSentinel Backend verifies webhook → Creates scan
→ Fetches PR diff + changed files → Security Pipeline runs
→ Security Gate evaluates result → GitHub Check / PR Comment posted
→ Developer/Reviewer reviews → Approve & Merge, or Request Changes → Fix → Rescan
```

### 8.3 AI Security Assistant Flow
```
Developer asks a question → System retrieves current findings,
repository context, historical scan data, and RAG knowledge
→ LLM generates a contextual answer → Answer returned to developer
```

## 9. Requirements

### 9.1 Functional Requirements
- Support Repository Scan and PR Scan, sharing the same core security pipeline.
- Integrate with GitHub via OAuth/GitHub App, GitHub API, and GitHub Webhooks.
- Run static code analysis (Semgrep), secret detection (Gitleaks), and dependency/config scanning (Trivy).
- Normalize all scanner outputs into a unified finding schema.
- Retrieve grounding security knowledge (OWASP, CWE, secure coding guidance) via embeddings + Qdrant vector search (RAG).
- Store structured application state and historical security memory in PostgreSQL.
- Compute the final numerical risk score deterministically (backend rules engine), not via unconstrained LLM output.
- Generate AI explanations covering: vulnerability explanation, root cause, impact, attack scenario, recommendations, and prioritization support.
- Generate AI-assisted remediation guidance (explanation + secure coding guidance + suggested fix).
- Validate any suggested patch in an isolated environment (apply patch → run tests → re-run Semgrep/Gitleaks/dependency scan) before presenting it as trustworthy; reject on failure.
- Evaluate a deterministic security policy gate producing PASS / WARNING / BLOCK.
- Post scan results as a GitHub Check and/or PR comment.
- Preserve human-in-the-loop control: CodeSentinel never auto-approves or auto-merges a PR.
- Provide a dashboard surfacing security score, severity breakdown, posture, trends, and finding detail views.
- Provide a conversational AI Security Assistant that can answer questions grounded in current findings, repo context, history, and RAG knowledge.
- Execute long-running scans asynchronously via a queue (Redis) and worker processes (Celery/worker service), preferably in isolated containers.
- Orchestrate the multi-agent pipeline (5 agents) using LangGraph.

### 9.2 Non-Functional Requirements (as explicitly stated in source)
- **Reproducibility/Auditability**: risk scoring must be deterministic and explainable, not an arbitrary LLM output.
- **Isolation**: patch validation and (preferably) scan execution occur in isolated/containerized environments.
- **Asynchronicity**: all long-running scans should be non-blocking/async.

> Note: The source document does not specify concrete NFRs such as latency/SLA targets, uptime targets, concurrency/throughput limits, data retention periods, or compliance certifications (e.g., SOC 2). These are **not defined** and should not be assumed.

## 10. Edge Cases
Only edge cases implied or directly stated in the source are listed. Others are not defined:

- **PR scan triggered but webhook verification fails** — the flow explicitly includes a "Verify Webhook" step, implying invalid/unverified webhooks must be handled (rejected) before scan creation.
- **AI-suggested patch fails validation** (tests fail, or re-scan still shows the issue) → patch must be **rejected**, not shown as a trustworthy fix ("PASS/FAIL" branch in Patch Validation flow).
- **Finding may be a false positive** — the Risk & Validation Agent explicitly produces a "True/False Positive Assessment," implying the system must handle and surface findings determined to be false positives rather than treating every scanner hit as a confirmed vulnerability.
- **Recurring/unchanged findings across scans** — Security Memory explicitly tracks new, resolved, recurring, and unchanged vulnerabilities, implying the system must correctly diff findings between scans of the same repository.
- **Policy Gate boundary conditions** — example policies given are: critical vulnerability → BLOCK; exposed secret → BLOCK; risk score below configured threshold → WARNING or BLOCK per policy; no critical/high findings → PASS. Threshold configuration mechanics are not detailed further.
- **A "PASS" result does not imply approval** — the spec explicitly warns that a passing/green result only means configured security checks passed, not that CodeSentinel approved or merged the PR. This must be clearly communicated in the UI/PR comment to avoid misinterpretation.

> Note: The source document does not address other common edge cases (e.g., scanner tool failure/timeout, huge monorepo scan limits, private/forked-repo PR permissions, rate limiting, duplicate webhook delivery, partial pipeline failure recovery). These should be clarified with stakeholders before implementation and are intentionally left undefined here rather than invented.

## 11. MVP Scope
The source document is framed as a "Finalized Technical Project Overview" describing the full target system, and does not explicitly delineate an MVP subset vs. a later phase. Based strictly on the system's own internal phase structure (Phases 1–5 are presented as the core pipeline that must exist for the system to function end-to-end), a defensible MVP boundary is:

**Included (core pipeline, required for any working version):**
- GitHub OAuth/App integration + repository selection
- Repository Scan (Phase 1: Repository Analysis Agent)
- Security Detection (Phase 2: Semgrep, Gitleaks, Trivy) + Finding Normalization
- Security Intelligence via RAG (Phase 3: embeddings + Qdrant + OWASP/CWE knowledge base)
- Risk & Validation Agent + Deterministic Risk Engine (Phase 4)
- Remediation Agent (Phase 5)
- Security Policy Gate (PASS/WARNING/BLOCK)
- Basic dashboard: security score, findings list, finding detail view
- PostgreSQL-backed scan storage (single scan, no trend history yet)

**Likely later-phase / not explicitly scoped as MVP by the source:**
- PR Scan automation via GitHub Webhooks (a distinct, more complex integration layer)
- Patch Validation in an isolated sandbox
- Historical trend comparison across multiple scans (Security Memory)
- AI Security Assistant (conversational Q&A)

> This MVP split is an inference based on system dependency order, not an explicit statement in the source document. It should be validated with the product owner before being treated as final.
