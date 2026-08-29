"""
GitHub service — PR Check Runs, PR Comments, PR diff fetching.
T-099, T-102, T-103, T-104, T-105, T-106, T-107.
"""

import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()

GITHUB_API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ── T-099: Fetch PR changed files ──────────────────────────────────────────────

def fetch_pr_changed_files(repo_full_name: str, pr_number: int, token: str) -> list[str]:
    """T-099: Return list of file paths changed in a PR."""
    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}/files",
            headers=_headers(token),
            params={"per_page": 100},
        )
    if resp.status_code != 200:
        logger.warning("Failed to fetch PR files", status=resp.status_code)
        return []
    return [f["filename"] for f in resp.json() if f.get("status") != "removed"]


# ── T-102: Create GitHub Check Run ─────────────────────────────────────────────

def create_github_check_run(repo_full_name: str, head_sha: str, token: str) -> int | None:
    """T-102: Create an in-progress GitHub Check Run for a PR scan."""
    with httpx.Client() as client:
        resp = client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/check-runs",
            headers=_headers(token),
            json={
                "name": "CodeSentinel Security Scan",
                "head_sha": head_sha,
                "status": "in_progress",
                "output": {
                    "title": "Security scan in progress...",
                    "summary": "CodeSentinel is analyzing your changes for security vulnerabilities.",
                },
            },
        )
    if resp.status_code not in (200, 201):
        logger.warning("Failed to create check run", status=resp.status_code)
        return None
    return resp.json().get("id")


# ── T-103: Update GitHub Check Run ─────────────────────────────────────────────

def update_github_check_run(
    repo_full_name: str,
    check_run_id: int | None,
    gate_result: str,
    summary: str,
    details_url: str,
    token: str,
) -> None:
    """T-103: Mark the Check Run as completed with conclusion based on gate result."""
    if not check_run_id:
        return

    # Map gate to GitHub conclusion
    conclusion_map = {"pass": "success", "warning": "neutral", "block": "failure"}
    conclusion = conclusion_map.get(gate_result, "neutral")

    with httpx.Client() as client:
        resp = client.patch(
            f"{GITHUB_API}/repos/{repo_full_name}/check-runs/{check_run_id}",
            headers=_headers(token),
            json={
                "status": "completed",
                "conclusion": conclusion,
                "details_url": details_url,
                "output": {
                    "title": f"Security checks {conclusion}",
                    "summary": summary,
                },
            },
        )
    if resp.status_code not in (200, 201):
        logger.warning("Failed to update check run", status=resp.status_code)


# ── T-104: Post GitHub PR Comment ─────────────────────────────────────────────

def post_github_pr_comment(
    repo_full_name: str,
    pr_number: int,
    gate_result: str,
    findings_summary: dict,
    dashboard_url: str,
    token: str,
) -> None:
    """
    T-104: Post a PR comment with security check results.
    T-105: Comment NEVER uses the word 'approved' — only 'checks passed' or 'N issues found'.
    T-107: Comment always ends with a dashboard link, never contains an embedded approval judgment.
    """
    total = findings_summary.get("total", 0)
    by_severity = findings_summary.get("by_severity", {})

    # T-105: Framing rules — never say "approved"
    if gate_result == "pass":
        status_line = "✅ **Security checks passed** — no policy violations detected."
    elif gate_result == "warning":
        status_line = f"⚠️ **Security warning** — {total} issue(s) found requiring attention."
    else:  # block
        status_line = f"🚫 **Security check failed** — {total} issue(s) found that must be addressed."

    severity_breakdown = " | ".join(
        f"**{k.upper()}**: {v}"
        for k, v in by_severity.items()
        if v > 0
    )

    # T-107: Body never implies CodeSentinel approved the PR
    body = f"""## 🛡️ CodeSentinel Security Report

{status_line}

{f"**Findings:** {severity_breakdown}" if severity_breakdown else ""}

> ℹ️ A passing check means configured automated security checks passed — **CodeSentinel does not approve or merge pull requests.** The decision to approve and merge remains entirely with the reviewer.

📊 **[View full security report]({dashboard_url})**
"""

    with httpx.Client() as client:
        resp = client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers=_headers(token),
            json={"body": body},
        )
    if resp.status_code not in (200, 201):
        logger.warning("Failed to post PR comment", status=resp.status_code)
    else:
        logger.info("PR comment posted", pr=pr_number, gate=gate_result)
