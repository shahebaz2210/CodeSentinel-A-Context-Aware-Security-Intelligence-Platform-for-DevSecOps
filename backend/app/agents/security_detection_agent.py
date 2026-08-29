"""
Security Detection Agent — Agent 2 (Phase 2) — T-044.
Orchestrates Semgrep, Gitleaks, and Trivy scanners.
This agent is orchestration-only: no LLM involved, no findings generated/altered by AI.
"""

import structlog
from app.scanners.semgrep_scanner import run_semgrep, NormalizedFinding
from app.scanners.gitleaks_scanner import run_gitleaks
from app.scanners.trivy_scanner import run_trivy

logger = structlog.get_logger()


def run_security_detection_agent(
    repo_dir: str,
    pr_changed_files: list[str] | None = None,
) -> list[NormalizedFinding]:
    """
    T-044: Run all three scanners and return deduplicated normalized findings.
    If pr_changed_files is provided (PR scan mode — T-100), only those files are analyzed.
    """
    logger.info("Agent 2: Security Detection starting", pr_mode=pr_changed_files is not None)

    semgrep_findings = run_semgrep(repo_dir)
    gitleaks_findings = run_gitleaks(repo_dir)
    trivy_findings = run_trivy(repo_dir)

    all_findings = semgrep_findings + gitleaks_findings + trivy_findings

    # T-100: Filter to PR changed files if in PR scan mode
    if pr_changed_files:
        changed_set = set(pr_changed_files)
        all_findings = [
            f for f in all_findings
            if any(f.file_path.endswith(cf) or cf in f.file_path for cf in changed_set)
        ]

    # Deduplicate by finding_key
    seen_keys: set[str] = set()
    deduplicated: list[NormalizedFinding] = []
    for finding in all_findings:
        if finding.finding_key not in seen_keys:
            seen_keys.add(finding.finding_key)
            deduplicated.append(finding)

    logger.info(
        "Agent 2: Security Detection complete",
        semgrep=len(semgrep_findings),
        gitleaks=len(gitleaks_findings),
        trivy=len(trivy_findings),
        total_unique=len(deduplicated),
    )
    return deduplicated
