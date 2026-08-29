# AI-instructions.md — CodeSentinel

This document defines behavioral guardrails and responsibilities for each AI component in CodeSentinel, based strictly on the roles and constraints described in the source technical overview. It is intended to guide prompt/agent design, not to introduce new capabilities.

## 1. Core Operating Principle
> "Deterministic scanners provide evidence; AI provides contextual reasoning." (source, Section 26)

Every AI agent in the system must operate under this boundary:
- AI **never** originates a security finding — findings come only from Semgrep, Gitleaks, or Trivy.
- AI **never** decides the final numerical risk score — that is computed by a deterministic backend risk engine from structured risk factors (severity, exploitability, confidence, exposure, business impact).
- AI **never** decides the final PASS/WARNING/BLOCK policy outcome — that is decided by the deterministic policy engine. The LLM may only *explain* the outcome.
- AI **never** approves or merges a Pull Request. That authority belongs exclusively to the human developer/reviewer.
- AI-generated patches are **suggestions only** and must pass isolated Patch Validation (tests + Semgrep + Gitleaks + dependency scan) before being shown as a trustworthy fix — never applied or presented as reliable purely because the LLM produced them.

## 2. Agent 1 — Repository Analysis Agent
**Responsibility:** Understand application structure and context before any finding is interpreted.

**Instructions:**
- Deterministic parsers/tools extract factual repository metadata first (file tree, languages, frameworks, dependencies, config).
- The LLM's role here is to *interpret* that deterministic metadata into a higher-level architectural understanding — not to guess at metadata the parsers didn't extract.
- Output must be structured (example schema from source):
  ```json
  {
    "languages": ["JavaScript", "TypeScript"],
    "frameworks": ["React", "Node.js", "Express"],
    "database": ["PostgreSQL"],
    "authentication": ["JWT"]
  }
  ```

## 3. Agent 2 — Security Detection Agent
**Responsibility:** Coordinate deterministic security scanning (Semgrep, Gitleaks, Trivy).

**Instructions:**
- This agent is orchestration-only — it does not use an LLM to generate or alter findings.
- Must pass raw scanner output to the Finding Normalizer, which converts heterogeneous tool schemas into the unified Finding format (see `Database.md` §1.1) before any downstream AI reasoning occurs.

## 4. Agent 3 — Security Intelligence Agent (RAG)
**Responsibility:** Retrieve and interpret trusted security knowledge to ground AI analysis.

**Instructions:**
- Before generating any explanation, retrieve relevant OWASP/CWE/secure-coding guidance via embedding-based similarity search against the Qdrant knowledge base.
- The LLM's explanation must be **grounded in retrieved documents**, not generated from unaided model memory — this is the explicit purpose of the RAG step ("Retrieved context is supplied to the LLM so that its explanation is grounded in the security knowledge base").
- Flow to follow: Finding → Embedding → Vector Search → Relevant Security Documents → supplied to LLM → Security Intelligence output.

## 5. Agent 4 — Risk & Validation Agent
**Responsibility:** Assess whether a finding is a true or false positive and determine contextual risk factors.

**Instructions:**
- Inputs to consider: the scanner finding, repository context, relevant code, retrieved security knowledge, and historical scan data.
- Output must include: a True/False Positive assessment, exploitability, impact, confidence, and structured risk factors.
- **Do not output a final numerical risk score.** The agent's job ends at producing structured risk *factors* — the deterministic backend risk engine converts those factors into the final score. This separation is explicit and non-negotiable per the source ("the final numerical risk score should be produced by a deterministic backend risk engine from structured risk factors rather than allowing the LLM to arbitrarily choose a score").

## 6. Agent 5 — Remediation Agent
**Responsibility:** Generate context-aware remediation guidance.

**Instructions:**
- Inputs: the vulnerability, the original code, security guidance, and the risk analysis from Agent 4.
- Output: explanation + secure coding guidance + suggested fix.
- Any generated patch must be explicitly framed as a **suggestion** requiring validation — never as a ready-to-merge fix. Downstream systems/UI must not present it as trustworthy until it has passed Patch Validation.

## 7. AI Security Analyst (Cross-Cutting LLM Reasoning Layer)
**Responsibility:** Combine repository context, scanner findings, relevant code, security memory, and RAG knowledge into contextual security analysis.

**Instructions:** Produce, when relevant:
- Vulnerability explanation
- Root-cause analysis
- Potential impact
- Potential attack scenario
- Security recommendations
- Prioritization support

All of the above must be traceable back to the deterministic findings and retrieved knowledge — the analyst explains and contextualizes evidence, it does not invent new evidence.

## 8. AI Security Assistant (Conversational)
**Responsibility:** Answer developer questions grounded in real system data.

**Instructions:**
- For every question, first retrieve: current findings, repository context, historical scan data, and RAG knowledge — then generate the answer from that retrieved context.
- Do not answer purely from model memory/general knowledge when the question is about *this* repository's specific findings, history, or score — the answer must be grounded in retrieved, real data.
- Supported example question types (from source): explaining why a finding is critical, listing what changed in the latest scan, explaining a score change, identifying a CWE, prioritization ("what should I fix first"), and surfacing recurring issues. Answers to these must be derived from actual stored Findings/Security Memory, not generated speculatively.

## 9. Messaging / Framing Rules for All AI Output
Any AI-generated content surfaced to the user (dashboard, PR comment, assistant answer) must respect these framing rules, derived directly from the source's explicit warnings:
- A passing/green check result must never be worded or implied as "CodeSentinel approved this PR" — only that configured automated checks passed.
- A suggested fix must never be worded or implied as safe/final until it has passed Patch Validation; even after validation, it remains a suggestion for the developer to accept.
- Risk scores and policy outcomes shown to the user must be attributed to the deterministic engine/policy layer, not framed as "the AI decided."

## 10. Out of Scope for This Document
The source does not specify actual prompt templates, system prompts, temperature/sampling settings, specific LLM provider, context window management, or token budget constraints for any agent. These should be defined during implementation and are not fabricated here.
