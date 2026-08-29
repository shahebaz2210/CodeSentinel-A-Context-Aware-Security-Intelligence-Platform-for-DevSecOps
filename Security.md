# Security.md — CodeSentinel

> This document covers CodeSentinel's **security-relevant design principles as a product** (how it handles findings, risk, patches, and policy) as described in the source. The source document does not include a security section covering CodeSentinel's *own* application security posture (e.g., how it protects its own infrastructure, secrets, or user data) — that is noted as a gap below rather than invented.

## 1. Deterministic Evidence, AI Reasoning — Separation of Concerns
A core, explicitly repeated principle: **deterministic scanners provide the evidence; AI provides contextual reasoning on top of that evidence.** The LLM never fabricates findings — it only explains, prioritizes, and reasons over findings that Semgrep, Gitleaks, or Trivy actually produced.

## 2. Deterministic Risk Scoring
- Inputs to risk assessment: Severity, Exploitability, Confidence, Exposure, Business Impact.
- The **final numerical risk score must be computed by a deterministic backend risk engine**, not chosen arbitrarily by the LLM.
- Rationale (explicit in source): this separation makes the result more **reproducible, auditable, and easier to explain** — a security-relevant property because inconsistent or unauditable risk scores would undermine trust in the gate/policy decisions built on top of them.

## 3. True/False Positive Handling
- The Risk & Validation Agent explicitly produces a **True/False Positive Assessment** as part of its output, alongside exploitability, impact, and confidence.
- This implies the system must not treat every raw scanner hit as a confirmed vulnerability — findings can be assessed and potentially down-weighted or flagged as false positives before reaching the developer as a "real" risk.

## 4. Patch Validation (AI-Generated Fix Safety)
This is the most explicit security control in the source document for AI-generated content:
```
AI Suggested Patch
       ↓
Isolated Environment
       ↓
   Apply Patch
       ↓
   Run Tests
       ↓
    Semgrep
       ↓
    Gitleaks
       ↓
 Dependency Scan
       ↓
   ┌───┴───┐
   ▼       ▼
 PASS     FAIL
   │       │
   ▼       ▼
Show Fix  Reject Fix
```
- Any AI-suggested patch is applied and validated **in an isolated environment** — never applied directly to the developer's live code without validation.
- Validation re-runs the full detection stack (Semgrep, Gitleaks, dependency scan) plus tests, to confirm the fix doesn't introduce a regression or leave the vulnerability unresolved.
- **Explicit rationale**: this prevents an AI-generated fix from being accepted *solely because an LLM produced it* — a direct anti-hallucination / anti-blind-trust control.
- On failure, the fix is **rejected**, not surfaced to the developer as a trustworthy suggestion.

## 5. Deterministic Security Policy Gate
- A **policy engine** (not the LLM) produces the authoritative PASS / WARNING / BLOCK result for a scan.
- The LLM's role is limited to *explaining* findings and policy outcomes in natural language — it does not decide the outcome.
- Example policies given:
  - Critical vulnerability exists → BLOCK
  - Exposed secret exists → BLOCK
  - Risk score below a configured threshold → WARNING or BLOCK (per policy configuration)
  - No critical/high findings → PASS

## 6. Human-in-the-Loop Control (Access/Authority Boundary)
- CodeSentinel **never** auto-approves or auto-merges a Pull Request, regardless of scan outcome.
- A passing/green check result means only that configured automated security checks passed — it explicitly does **not** mean CodeSentinel approved the PR. This distinction must be preserved everywhere the result is surfaced (dashboard, PR comment, GitHub Check).
- Final approval and merge authority rests entirely with the developer/reviewer.

## 7. Secret Detection
- Gitleaks is the designated tool for detecting exposed secrets (API keys, tokens, passwords, private keys) within scanned code.
- An exposed secret finding is explicitly treated as a BLOCK-level policy condition by default (per the example policy list).

## 8. Isolation as a Security Control
- Patch Validation explicitly runs in an **isolated environment**.
- More broadly, the source states: "All long-running scans should execute asynchronously and preferably in isolated containers" (Section 26) — extending the isolation principle to scan execution generally, using Docker.

## 9. Explicitly Not Covered by the Source (Gaps)
The following are standard categories for a "Security.md" but are **not addressed anywhere** in the source document. They are listed here as open items requiring definition — not invented or assumed:
- CodeSentinel's own application security: authentication/authorization model for the dashboard/API, session management, secrets management for its own credentials (e.g., GitHub App private key, LLM API keys, DB credentials).
- Data protection: encryption at rest/in transit for PostgreSQL and Qdrant, and for source code that is cloned/analyzed.
- Tenant/data isolation between different organizations or repositories using the platform.
- Handling of cloned repository source code after a scan completes (retention vs. deletion).
- Compliance/certification targets (SOC 2, ISO 27001, etc.).
- Logging/audit trail requirements for who viewed/accepted a fix or overrode a policy result.
- Rate limiting / abuse prevention on the API or webhook endpoints (beyond the stated "Verify Webhook" step).

These should be defined with security/compliance stakeholders before production deployment.
