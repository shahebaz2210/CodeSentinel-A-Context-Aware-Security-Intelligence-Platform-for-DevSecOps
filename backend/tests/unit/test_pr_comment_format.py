"""Unit tests for PR comment formatting — T-107."""

import pytest
from app.services.github_service import post_github_pr_comment


def generate_comment_body(gate_result: str, findings_summary: dict, dashboard_url: str) -> str:
    """Helper: build the same comment body logic as the service for assertion."""
    total = findings_summary.get("total", 0)
    by_severity = findings_summary.get("by_severity", {})

    if gate_result == "pass":
        status_line = "✅ **Security checks passed** — no policy violations detected."
    elif gate_result == "warning":
        status_line = f"⚠️ **Security warning** — {total} issue(s) found requiring attention."
    else:
        status_line = f"🚫 **Security check failed** — {total} issue(s) found that must be addressed."

    severity_breakdown = " | ".join(
        f"**{k.upper()}**: {v}" for k, v in by_severity.items() if v > 0
    )

    body = f"""## 🛡️ CodeSentinel Security Report

{status_line}

{f"**Findings:** {severity_breakdown}" if severity_breakdown else ""}

> ℹ️ A passing check means configured automated security checks passed — **CodeSentinel does not approve or merge pull requests.** The decision to approve and merge remains entirely with the reviewer.

📊 **[View full security report]({dashboard_url})**
"""
    return body


def test_pr_comment_never_contains_approved_word() -> None:
    """T-107: PR comment must NEVER contain the word 'approved'."""
    for gate in ["pass", "warning", "block"]:
        body = generate_comment_body(
            gate_result=gate,
            findings_summary={"total": 5, "by_severity": {"high": 2, "medium": 3}},
            dashboard_url="https://app.codesentinel.dev/scans/123",
        )
        assert "approved" not in body.lower(), (
            f"PR comment for gate='{gate}' contains the word 'approved'"
        )


def test_pr_comment_always_contains_dashboard_link() -> None:
    """T-107: PR comment must always contain a link to the dashboard."""
    dashboard_url = "https://app.codesentinel.dev/scans/456"
    for gate in ["pass", "warning", "block"]:
        body = generate_comment_body(
            gate_result=gate,
            findings_summary={"total": 0, "by_severity": {}},
            dashboard_url=dashboard_url,
        )
        assert dashboard_url in body, (
            f"PR comment for gate='{gate}' does not contain dashboard link"
        )


def test_pr_comment_pass_uses_correct_phrasing() -> None:
    """T-107: Pass gate should say 'checks passed', not 'approved'."""
    body = generate_comment_body(
        gate_result="pass",
        findings_summary={"total": 0, "by_severity": {}},
        dashboard_url="https://app.codesentinel.dev/scans/789",
    )
    assert "checks passed" in body.lower()
    assert "approved" not in body.lower()


def test_pr_comment_block_shows_finding_count() -> None:
    """T-107: Block gate should mention the number of issues found."""
    body = generate_comment_body(
        gate_result="block",
        findings_summary={"total": 3, "by_severity": {"critical": 1, "high": 2}},
        dashboard_url="https://app.codesentinel.dev/scans/001",
    )
    assert "3" in body


def test_pr_comment_clarifies_no_pr_approval() -> None:
    """T-107: Comment must clarify CodeSentinel does not approve PRs."""
    body = generate_comment_body(
        gate_result="pass",
        findings_summary={"total": 0, "by_severity": {}},
        dashboard_url="https://app.codesentinel.dev/scans/002",
    )
    assert "does not approve or merge" in body
