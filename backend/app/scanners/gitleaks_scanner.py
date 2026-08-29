"""
Gitleaks scanner wrapper — T-039, T-042.
Runs Gitleaks and normalizes output to the unified Finding schema.
"""

import subprocess
import json
import hashlib
import structlog
from app.scanners.semgrep_scanner import NormalizedFinding

logger = structlog.get_logger()


def run_gitleaks(target_dir: str) -> list[NormalizedFinding]:
    """T-039 + T-042: Run Gitleaks and normalize output to unified Finding schema."""
    try:
        result = subprocess.run(
            [
                "gitleaks",
                "detect",
                "--source", target_dir,
                "--report-format", "json",
                "--report-path", "/tmp/gitleaks-report.json",
                "--no-git",
                "--exit-code", "0",  # don't fail process on findings
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        logger.error("Gitleaks timed out")
        return []
    except FileNotFoundError:
        logger.error("Gitleaks not found — install gitleaks binary")
        return []

    # Read the report file
    try:
        with open("/tmp/gitleaks-report.json", "r") as f:
            content = f.read().strip()
        findings_raw = json.loads(content) if content else []
        if not isinstance(findings_raw, list):
            findings_raw = []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Gitleaks report not parseable", error=str(e))
        return []

    normalized = []
    for r in findings_raw:
        path = r.get("File", "")
        line = r.get("StartLine")
        finding_type = r.get("RuleID", "SECRET_EXPOSURE").upper().replace("-", "_")
        key_raw = f"gitleaks:{finding_type}:{path}:{line}"
        finding_key = hashlib.sha256(key_raw.encode()).hexdigest()[:16]

        normalized.append(NormalizedFinding(
            finding_key=finding_key,
            tool="gitleaks",
            finding_type=finding_type,
            severity="critical",  # Exposed secrets are always critical per policy
            file_path=path,
            line_start=line,
            line_end=r.get("EndLine"),
            message=f"Exposed secret: {r.get('Description', r.get('RuleID', 'Unknown'))}",
            rule_id=r.get("RuleID"),
            code_snippet=r.get("Secret", "")[:200] if r.get("Secret") else None,
            raw_output=r,
        ))

    logger.info("Gitleaks scan complete", findings=len(normalized))
    return normalized
