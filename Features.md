# Features.md — CodeSentinel

This document lists all features explicitly described in the source technical overview, grouped by capability area. No features have been added beyond what the source specifies.

## 1. Repository Scan
- Full repository/codebase analysis
- Technology and dependency identification
- Static code security analysis
- Secret detection
- Dependency vulnerability analysis
- Historical comparison with previous scans
- Context-aware AI security report

## 2. Pull Request Scan
- Webhook-triggered scan on PR creation/update
- Analysis limited to PR diff + changed files (plus relevant surrounding context)
- Automated GitHub Check / PR comment with results
- Does **not** auto-approve or auto-merge — informational/gating only

## 3. Repository Analysis Agent (Phase 1)
- Clone repository
- Build file tree
- Language detection
- Framework detection
- Dependency detection
- Architecture analysis
- Produces structured "Repository Context" object, e.g.:
  ```json
  {
    "languages": ["JavaScript", "TypeScript"],
    "frameworks": ["React", "Node.js", "Express"],
    "database": ["PostgreSQL"],
    "authentication": ["JWT"]
  }
  ```
- Deterministic parsers extract factual metadata; the LLM interprets metadata into higher-level architectural understanding.

## 4. Security Detection Agent (Phase 2)
- Coordinates three deterministic scanners:
  - **Semgrep** — static application-code security analysis, insecure coding patterns
  - **Gitleaks** — exposed secrets (API keys, tokens, passwords, private keys)
  - **Trivy** — dependency and configuration vulnerability scanning

## 5. Finding Normalization
- Converts heterogeneous scanner outputs (Semgrep, Gitleaks, Trivy) into one unified finding schema, e.g.:
  ```json
  {
    "finding_id": "F-1024",
    "tool": "semgrep",
    "type": "SQL_INJECTION",
    "severity": "HIGH",
    "file": "src/auth/login.js",
    "line_start": 42,
    "line_end": 42,
    "message": "Potential SQL injection"
  }
  ```

## 6. Security Intelligence Agent (Phase 3) — RAG
- Curated security knowledge base: OWASP guidance, CWE information, secure-coding guidance
- Document processing → chunking → embedding → stored in Qdrant
- Findings converted to embeddings and matched via vector similarity search
- Retrieved documents grounded the LLM's explanation (reduces hallucination risk)

## 7. Embeddings & Vector Database
- Qdrant used specifically for semantic retrieval of security knowledge (RAG layer)
- Explicitly **not** a replacement for PostgreSQL — PostgreSQL holds structured application/scan state; Qdrant holds embeddings for semantic search only

## 8. Security Memory (Historical Tracking)
- PostgreSQL stores scan history per repository across multiple scans
- Tracks and classifies findings as:
  - New
  - Resolved
  - Recurring
  - Unchanged
  - Security improvements
  - Security regressions

## 9. Risk & Validation Agent (Phase 4)
- Inputs: scanner finding + repository context + relevant code + security knowledge + historical context
- Outputs: True/False Positive assessment, exploitability, impact, confidence, and structured risk factors
- **Deterministic Risk Engine** computes the final numerical score from: severity + exploitability + confidence + exposure + business impact — not chosen freely by the LLM
- Goal: reproducible, auditable, explainable risk scores

## 10. AI Security Analyst (LLM Reasoning Layer)
- Combines repository context, scanner findings, relevant code, security memory, and RAG knowledge
- Produces:
  - Vulnerability explanation
  - Root-cause analysis
  - Potential impact
  - Potential attack scenario
  - Security recommendations
  - Prioritization support

## 11. Remediation Agent (Phase 5)
- Inputs: vulnerability + original code + security guidance + risk analysis
- Output: explanation + secure coding guidance + suggested fix
- Generated patches are treated as **suggestions**, not automatically trustworthy

## 12. Patch Validation
- AI-suggested patch applied in an **isolated environment**
- Runs: tests → Semgrep → Gitleaks → dependency scan
- PASS → fix shown to developer; FAIL → fix rejected
- Prevents an AI-generated fix from being trusted purely because an LLM produced it

## 13. AI Security Gate (Policy Engine)
- Deterministic organizational policy engine evaluates scan results
- Produces PASS / WARNING / BLOCK
- LLM may explain the outcome, but the policy engine determines the actual result
- Example policies:
  - Critical vulnerability exists → BLOCK
  - Exposed secret exists → BLOCK
  - Risk score below configured threshold → WARNING or BLOCK (per policy)
  - No critical/high findings → PASS

## 14. Human-in-the-Loop PR Approval
- CodeSentinel posts assessment as a PR Check/Comment only
- Developer/reviewer makes the Approve vs. Request Changes decision
- Approve → Merge; Request Changes → Developer fixes → Rescan
- A passing/green result means configured checks passed — **not** that CodeSentinel approved/merged

## 15. PR Automation
- GitHub Webhook triggers scan automatically on PR create/update
- Pipeline: verify webhook → create scan → get PR diff/changed files → run security pipeline → security gate → GitHub Check/Comment → developer decides
- Automation scope is limited to the security workflow only; approval/merge remain manual

## 16. Dashboard
Frontend dashboard exposes:
- Overall security score
- Critical / high / medium / low findings breakdown
- Repository security posture
- PR security status
- Scan history and security trends
- Finding details
- AI explanation and root cause
- OWASP/CWE context
- Suggested remediation
- Developer-controlled PR review workflow

## 17. Finding Detail View
Per-finding view includes:
- Severity
- Risk Score
- Confidence
- File + Line
- Relevant Code
- Root Cause
- Impact
- Attack Scenario
- CWE
- OWASP
- AI Explanation
- Suggested Fix
- Historical Status

## 18. AI Security Assistant (Conversational)
- Operates over: current findings, repository context, historical scan data, security knowledge base (RAG)
- Flow: developer question → retrieve findings/context/history/RAG knowledge → LLM → contextual answer
- Example questions supported:
  - "Why is this SQL injection critical?"
  - "Which vulnerabilities were introduced in the latest scan?"
  - "Why did the security score decrease?"
  - "What CWE is associated with this finding?"
  - "What should I fix first?"
  - "Show recurring security issues."

---
> No additional features (e.g., team management, notifications/alerts channel integrations like Slack, billing, SSO beyond GitHub OAuth, multi-repo comparison dashboards, or exportable compliance reports) are specified in the source document. These are intentionally omitted rather than assumed.
