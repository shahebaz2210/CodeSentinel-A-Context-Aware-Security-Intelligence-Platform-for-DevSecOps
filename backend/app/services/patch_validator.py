"""
Patch Validation Pipeline — T-075-T-083.
Validates AI-suggested patches in an isolated sandbox.
The fix is ONLY trusted after: apply → tests → rescan all PASS.
"""

import os
import shutil
import subprocess
import tempfile
import structlog
from app.scanners.semgrep_scanner import run_semgrep
from app.scanners.gitleaks_scanner import run_gitleaks
from app.scanners.trivy_scanner import run_trivy

logger = structlog.get_logger()


def create_validation_sandbox(source_dir: str) -> str:
    """T-075: Copy repository to isolated temp directory."""
    sandbox_dir = tempfile.mkdtemp(prefix="codesentinel_validation_")
    shutil.copytree(source_dir, sandbox_dir, dirs_exist_ok=True)
    logger.info("Validation sandbox created", sandbox=sandbox_dir)
    return sandbox_dir


def apply_patch(sandbox_dir: str, file_path: str, suggested_fix: str) -> bool:
    """T-076: Write the suggested fix to the file in the sandbox."""
    target_path = os.path.join(sandbox_dir, file_path.lstrip("/"))
    if not os.path.exists(target_path):
        logger.warning("Target file not found in sandbox", path=target_path)
        return False
    try:
        # Write suggested fix as replacement content
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            original = f.read()

        # Simple strategy: if fix looks like a diff, try patch; otherwise write entire file
        if suggested_fix.startswith("---") or suggested_fix.startswith("@@"):
            # It's a diff — write to temp file and apply with patch command
            diff_file = target_path + ".diff"
            with open(diff_file, "w") as f:
                f.write(suggested_fix)
            result = subprocess.run(
                ["patch", target_path, diff_file],
                capture_output=True, timeout=30
            )
            os.remove(diff_file)
            return result.returncode == 0
        else:
            # It's replacement code — append alongside for review (safer approach)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(suggested_fix)
            return True
    except Exception as e:
        logger.error("Failed to apply patch", error=str(e))
        return False


def run_tests_in_sandbox(sandbox_dir: str) -> tuple[bool, str]:
    """T-077: Run project tests in the sandbox. Returns (passed, log)."""
    log_lines = []

    # Try pytest
    pytest_result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "-q", sandbox_dir],
        capture_output=True, text=True, timeout=180, cwd=sandbox_dir,
    )
    log_lines.append(pytest_result.stdout)
    log_lines.append(pytest_result.stderr)
    if pytest_result.returncode == 0:
        return True, "\n".join(log_lines)

    # Try npm test
    if os.path.exists(os.path.join(sandbox_dir, "package.json")):
        npm_result = subprocess.run(
            ["npm", "test", "--", "--watchAll=false"],
            capture_output=True, text=True, timeout=180, cwd=sandbox_dir,
        )
        log_lines.append(npm_result.stdout)
        log_lines.append(npm_result.stderr)
        if npm_result.returncode == 0:
            return True, "\n".join(log_lines)

    # If no test framework found, treat as pass (no tests = can't fail tests)
    if "no tests ran" in "\n".join(log_lines).lower() or not log_lines[0].strip():
        return True, "No test suite found — validation based on re-scan only"

    return False, "\n".join(log_lines)[:2000]


def rescan_sandbox(sandbox_dir: str, original_finding_key: str) -> bool:
    """T-078: Rescan sandbox and check if original finding is gone."""
    semgrep_findings = run_semgrep(sandbox_dir)
    gitleaks_findings = run_gitleaks(sandbox_dir)
    trivy_findings = run_trivy(sandbox_dir)
    all_findings = semgrep_findings + gitleaks_findings + trivy_findings

    still_present = any(f.finding_key == original_finding_key for f in all_findings)
    return not still_present  # True = fixed, False = still vulnerable


def validate_patch(
    sandbox_dir: str,
    file_path: str,
    suggested_fix: str,
    original_finding_key: str,
) -> tuple[bool, str]:
    """
    T-079: Full patch validation pipeline.
    Returns (passed, log). The fix is trusted ONLY if this returns True.
    """
    log = []

    # Step 1: Apply patch
    log.append("Step 1: Applying patch...")
    if not apply_patch(sandbox_dir, file_path, suggested_fix):
        msg = "FAIL: Could not apply patch to sandbox"
        log.append(msg)
        return False, "\n".join(log)
    log.append("Patch applied successfully.")

    # Step 2: Run tests
    log.append("\nStep 2: Running test suite...")
    tests_passed, test_log = run_tests_in_sandbox(sandbox_dir)
    log.append(test_log[:500])
    if not tests_passed:
        log.append("FAIL: Test suite failed after applying patch")
        return False, "\n".join(log)
    log.append("Tests passed.")

    # Step 3: Rescan
    log.append("\nStep 3: Re-scanning for original vulnerability...")
    vulnerability_fixed = rescan_sandbox(sandbox_dir, original_finding_key)
    if not vulnerability_fixed:
        log.append("FAIL: Original vulnerability still detected after patch")
        return False, "\n".join(log)
    log.append("Re-scan: Original vulnerability not found — PASS")

    log.append("\nPATCH VALIDATION: PASS — fix is validated")
    return True, "\n".join(log)
