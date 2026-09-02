# Deployment.md — CodeSentinel

> **Scope note:** The source document names deployment-related technologies but does not provide a deployment topology, environment strategy, infrastructure-as-code approach, or scaling plan. This document captures only what is explicitly stated.

## 1. Stated Deployment Technologies
| Concern | Technology (from source) |
|---|---|
| Containerization | Docker — "Isolation and reproducibility" |
| CI/CD | GitHub Actions — "Build, test, deployment" |
| Production Hosting | Cloud / Kubernetes — "Production hosting" |

That is the full extent of deployment-specific detail provided in the source (Section 23, Final Technology Stack).

## 2. What Is Implied by the Broader Architecture
Even though not stated under a "deployment" heading, the following operational requirements are implied elsewhere in the source and are relevant to deployment planning:

- **Asynchronous, queue-based workers**: Redis Queue + Scan Worker(s) (Celery/worker service) must be deployable as separate, horizontally-scalable components from the FastAPI backend, since scans are explicitly long-running and asynchronous (Section 26).
- **Isolated execution environments**: Patch Validation requires spinning up an isolated environment per validation run (apply patch → tests → re-scan) — implying the deployment must support ephemeral, sandboxed container execution, not just a static service fleet.
- **Multiple backing services to provision**: FastAPI backend, PostgreSQL, Redis, Qdrant, and worker processes are all distinct deployable components per the architecture diagram (Section 5).
- **External dependency on GitHub**: the system must be reachable by GitHub Webhooks (inbound) and must be able to call the GitHub API (outbound) — implying the backend needs a publicly reachable webhook endpoint in any deployment environment.

## 3. Explicitly Not Specified
The source document does **not** define:
- Which cloud provider (AWS, GCP, Azure, or other) — only the generic term "Cloud / Kubernetes" is used.
- Kubernetes manifests, Helm charts, or namespace/cluster topology.
- Environment strategy (dev/staging/prod), or how configuration/secrets differ per environment.
- Autoscaling rules or resource sizing for any component (API, workers, Qdrant, PostgreSQL).
- Secrets management approach for deployment-time credentials (GitHub App keys, LLM provider API keys, DB credentials).
- CI/CD pipeline stages beyond "Build, test, deployment" (e.g., what gates a deploy — is it just tests, or also security scanning of CodeSentinel's own code?).
- Blue/green, canary, or rolling deployment strategy.
- Disaster recovery / backup strategy for PostgreSQL or Qdrant.
- Monitoring, logging, or alerting stack.


