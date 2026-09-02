# UI/UX.md — CodeSentinel

> **Scope note:** The source document is a *technical* project overview. It defines **what information** the UI must surface, but does not include wireframes, visual design direction, interaction details, component specs, or a detailed information architecture. This document organizes only what is explicitly stated. Anything beyond that (layout, navigation structure, visual style, responsive behavior, exact interaction patterns) is **not specified** and should be defined separately with design input before implementation.

## 1. Confirmed Screens / Views
Based on the source, the product requires at minimum these two UI surfaces, plus the GitHub-native surface:

1. **Developer Dashboard**
2. **Finding Detail View**
3. **GitHub PR Check / Comment** (not a CodeSentinel-hosted UI, but a required touchpoint — GitHub-native)
4. **AI Security Assistant** (conversational interface — form/placement not specified)

## 2. Dashboard — Required Content
The dashboard must expose the following (explicitly listed in source, Section 20):
- Overall security score
- Critical, high, medium, and low findings (counts/breakdown)
- Repository security posture
- PR security status
- Scan history and security trends
- Finding details (entry point into Finding Detail View)
- AI explanation and root cause (summarized or linked)
- OWASP/CWE context
- Suggested remediation
- Developer-controlled PR review workflow (i.e., the UI must make clear that approval/merge is a human action, not something CodeSentinel does)

**Not specified:** page layout, whether this is one page or multiple, chart types for trends, filtering/sorting behavior, multi-repo vs. single-repo view, empty states, loading states.

## 3. Finding Detail View — Required Content
Per finding, the view must show (explicitly listed in source, Section 21):
- Severity
- Risk Score
- Confidence
- File + Line
- Relevant Code (code snippet display)
- Root Cause
- Impact
- Attack Scenario
- CWE
- OWASP
- AI Explanation
- Suggested Fix
- Historical Status (e.g., new / recurring / resolved, per Security Memory)

**Not specified:** whether "Suggested Fix" includes an inline diff view, whether the user can accept/apply a fix from this screen, code syntax highlighting requirements, or how "Historical Status" is visually represented.

## 4. GitHub PR Integration Surface
- Results are surfaced as a **GitHub Check** and/or **PR comment**.
- Messaging must make it explicit that a passing/green check means *configured security checks passed* — **not** that CodeSentinel approved or merged the PR (this distinction is explicitly called out in the source and should be treated as a hard UX requirement, e.g., via wording, not just data).
- Developer/reviewer path from PR result: Approve → Merge, or Request Changes → Developer applies fix → Rescan.

**Not specified:** exact PR comment format/template, whether results are collapsible, whether inline PR review comments are placed on specific lines, or how re-scans update the existing comment vs. posting a new one.

## 5. AI Security Assistant — Interaction Model
- Input: a free-form developer question.
- System retrieves: current findings, repository context, historical scan data, RAG knowledge.
- Output: a contextual, grounded answer.
- Example supported question types (from source, Section 22):
  - "Why is this SQL injection critical?"
  - "Which vulnerabilities were introduced in the latest scan?"
  - "Why did the security score decrease?"
  - "What CWE is associated with this finding?"
  - "What should I fix first?"
  - "Show recurring security issues."

**Not specified:** whether this is a persistent chat panel, a per-finding Q&A box, placement within the dashboard, conversation history/persistence, or streaming vs. non-streaming responses.

## 6. Human-in-the-Loop UX Principle
This is a cross-cutting UX requirement stated repeatedly and explicitly in the source and should govern every relevant screen:
- CodeSentinel must never present itself as having approved, blocked, or merged a PR on its own authority.
- The UI must clearly separate **"security check result"** (PASS/WARNING/BLOCK, produced by the deterministic policy engine) from **"PR approval decision"** (always a human action).
- AI-suggested fixes are **suggestions** — even after passing patch validation, the UI should not present them as automatically applied or as guaranteed-safe, only as "validated" (tests + re-scan passed).


