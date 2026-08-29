"""
Trivy scanner wrapper — T-040, T-043.
Runs Trivy filesystem scan and normalizes output to the unified Finding schema.
"""

import subprocess
import json
import hashlib
import structlog
from app.scanners.semgrep_scanner import NormalizedFinding

logger = structlog.get_logger()

SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
    "UNKNOWN": "info",
}


def run_trivy(target_dir: str) -> list[NormalizedFinding]:
    """T-040 + T-043: Run Trivy fs scan and normalize output to unified Finding schema."""
    try:
        result = subprocess.run(
            [
                "trivy",
                "fs",
                "--format", "json",
                "--scanners", "vuln,secret,misconfig",
                "--quiet",
                target_dir,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        raw = json.loads(result.stdout) if result.stdout.strip() else {}
    except subprocess.TimeoutExpired:
        logger.error("Trivy timed out")
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error("Trivy failed", error=str(e))
        return []

    normalized = []
    results = raw.get("Results", [])

    for target_result in results:
        target_path = target_result.get("Target", "")

        # Vulnerability findings
        for vuln in target_result.get("Vulnerabilities", []) or []:
            cve_id = vuln.get("VulnerabilityID", "UNKNOWN")
            pkg = vuln.get("PkgName", "unknown")
            severity = SEVERITY_MAP.get(vuln.get("Severity", "UNKNOWN"), "info")
            key_raw = f"trivy:{cve_id}:{pkg}:{target_path}"
            finding_key = hashlib.sha256(key_raw.encode()).hexdigest()[:16]

            normalized.append(NormalizedFinding(
                finding_key=finding_key,
                tool="trivy",
                finding_type=f"DEPENDENCY_{cve_id.replace('-', '_')}",
                severity=severity,
                file_path=target_path,
                line_start=None,
                line_end=None,
                message=(
                    f"{cve_id} in {pkg}@{vuln.get('InstalledVersion', '?')} "
                    f"(fixed in {vuln.get('FixedVersion', 'N/A')}): "
                    f"{vuln.get('Title', vuln.get('Description', ''))[:200]}"
                ),
                rule_id=cve_id,
                code_snippet=None,
                raw_output=vuln,
            ))

        # Misconfiguration findings
        for misconfig in target_result.get("Misconfigurations", []) or []:
            check_id = misconfig.get("ID", "UNKNOWN")
            severity = SEVERITY_MAP.get(misconfig.get("Severity", "UNKNOWN"), "info")
            key_raw = f"trivy:misconfig:{check_id}:{target_path}"
            finding_key = hashlib.sha256(key_raw.encode()).hexdigest()[:16]

            normalized.append(NormalizedFinding(
                finding_key=finding_key,
                tool="trivy",
                finding_type=f"MISCONFIG_{check_id.replace('-', '_')}",
                severity=severity,
                file_path=target_path,
                line_start=misconfig.get("CauseMetadata", {}).get("StartLine"),
                line_end=misconfig.get("CauseMetadata", {}).get("EndLine"),
                message=f"{misconfig.get('Title', '')}: {misconfig.get('Description', '')}",
                rule_id=check_id,
                code_snippet=misconfig.get("CauseMetadata", {}).get("Code", {}).get("Lines", [{}])[0].get("Content") if misconfig.get("CauseMetadata", {}).get("Code") else None,
                raw_output=misconfig,
            ))

    logger.info("Trivy scan complete", findings=len(normalized))
    return normalized
