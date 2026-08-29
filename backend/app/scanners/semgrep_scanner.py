"""
Semgrep scanner wrapper — T-038, T-041.
Runs Semgrep and normalizes output to the unified Finding schema.
"""

import subprocess
import json
import hashlib
from dataclasses import dataclass
from typing import Any
import structlog

logger = structlog.get_logger()


@dataclass
class NormalizedFinding:
    """Unified finding schema from any scanner."""
    finding_key: str
    tool: str
    finding_type: str
    severity: str
    file_path: str
    line_start: int | None
    line_end: int | None
    message: str
    rule_id: str | None
    code_snippet: str | None
    raw_output: dict[str, Any]


def _severity_map(semgrep_severity: str) -> str:
    mapping = {
        "ERROR": "high",
        "WARNING": "medium",
        "INFO": "low",
        "CRITICAL": "critical",
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
    }
    return mapping.get(semgrep_severity.upper(), "medium")


def run_semgrep(target_dir: str, config: str = "auto") -> list[NormalizedFinding]:
    """T-038 + T-041: Run Semgrep and normalize output to unified Finding schema."""
    try:
        result = subprocess.run(
            ["semgrep", "--config", config, "--json", "--no-git-ignore", target_dir],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode not in (0, 1):  # 0=success, 1=findings found
            logger.warning("Semgrep exited with error", stderr=result.stderr[:500])
            return []

        raw = json.loads(result.stdout) if result.stdout.strip() else {}
        findings_raw = raw.get("results", [])
    except subprocess.TimeoutExpired:
        logger.error("Semgrep timed out")
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error("Semgrep failed", error=str(e))
        return []

    normalized = []
    for r in findings_raw:
        path = r.get("path", "")
        line_start = r.get("start", {}).get("line")
        finding_type = r.get("check_id", "SEMGREP_FINDING").split(".")[-1].upper()
        key_raw = f"semgrep:{finding_type}:{path}:{line_start}"
        finding_key = hashlib.sha256(key_raw.encode()).hexdigest()[:16]

        normalized.append(NormalizedFinding(
            finding_key=finding_key,
            tool="semgrep",
            finding_type=finding_type,
            severity=_severity_map(r.get("extra", {}).get("severity", "WARNING")),
            file_path=path,
            line_start=line_start,
            line_end=r.get("end", {}).get("line"),
            message=r.get("extra", {}).get("message", "Semgrep finding"),
            rule_id=r.get("check_id"),
            code_snippet=r.get("extra", {}).get("lines"),
            raw_output=r,
        ))

    logger.info("Semgrep scan complete", findings=len(normalized))
    return normalized
