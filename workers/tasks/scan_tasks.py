"""
Main scan Celery task — T-026, T-027, T-087, T-088, T-089.
Orchestrates the full 5-agent LangGraph pipeline for repo and PR scans.
Also handles Security Memory (T-091), GitHub Check Run updates (T-103, T-106).
"""

import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone

import structlog
from google import genai
from google.genai import types as genai_types

from workers.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import (
    Scan, Repository, Finding, FindingAnalysis,
    RemediationSuggestion, PolicyResult, RepositoryContext, FindingHistory,
)
from app.models.scan import ScanStatus, GateResult
from app.models.finding_history import HistoryStatus
from app.agents.repository_analysis_agent import clone_repository
from app.agents.pipeline import build_scan_pipeline, ScanState
from app.services.finding_differ import finding_differ

logger = structlog.get_logger()


def _get_llm_client() -> genai.Client:
    """Create a google.genai Client (shared across all 5 agents in a scan)."""
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


@celery_app.task(bind=True, name="workers.tasks.scan_tasks.run_security_scan")
def run_security_scan(self, scan_id: str) -> dict:
    """
    T-087: Full scan pipeline Celery task.
    Creates a temporary clone dir, runs the 5-agent LangGraph pipeline,
    persists all results to PostgreSQL, and updates GitHub (for PR scans).
    T-088: Error handling updates scan status to failed without crashing worker.
    """
    db = SessionLocal()
    clone_dir = None

    try:
        # Load scan and repository
        scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
        if not scan:
            logger.error("Scan not found", scan_id=scan_id)
            return {"error": "Scan not found"}

        repo = db.query(Repository).filter(Repository.id == scan.repository_id).first()
        if not repo:
            _mark_failed(db, scan, "Repository not found")
            return {"error": "Repository not found"}

        # T-102: Create GitHub Check Run for PR scans
        if scan.scan_type.value == "pr" and scan.pr_number and settings.GITHUB_APP_ID:
            try:
                from app.services.github_service import create_github_check_run
                check_run_id = create_github_check_run(
                    repo_full_name=repo.full_name,
                    head_sha=scan.git_ref,
                    token=repo.github_access_token,
                )
                scan.github_check_run_id = check_run_id
                db.commit()
            except Exception as e:
                logger.warning("Failed to create check run", error=str(e))

        # Update status to running
        scan.status = ScanStatus.RUNNING
        db.commit()
        logger.info("Scan started", scan_id=scan_id, type=scan.scan_type.value)

        # Clone repository
        clone_dir = tempfile.mkdtemp(prefix=f"cs_scan_{scan_id}_")
        clone_repository(repo.clone_url, repo.github_access_token, clone_dir)

        # Fetch PR changed files if PR scan
        pr_changed_files = None
        if scan.scan_type.value == "pr" and scan.pr_number:
            try:
                from app.services.github_service import fetch_pr_changed_files
                pr_changed_files = fetch_pr_changed_files(
                    repo_full_name=repo.full_name,
                    pr_number=scan.pr_number,
                    token=repo.github_access_token,
                )
            except Exception as e:
                logger.warning("Could not fetch PR diff, scanning full repo", error=str(e))

        # Build and run pipeline
        llm_client = _get_llm_client()
        pipeline = build_scan_pipeline(llm_client)

        initial_state: ScanState = {
            "scan_id": scan_id,
            "repository_id": str(scan.repository_id),
            "repo_dir": clone_dir,
            "access_token": repo.github_access_token,
            "clone_url": repo.clone_url,
            "scan_type": scan.scan_type.value,
            "pr_changed_files": pr_changed_files,
            "repository_context": None,
            "findings": None,
            "finding_analyses": None,
            "policy_result": None,
            "remediation_suggestions": None,
            "error": None,
        }

        final_state = pipeline.invoke(initial_state)

        # T-088: Check for pipeline error
        if final_state.get("error"):
            _mark_failed(db, scan, final_state["error"])
            return {"error": final_state["error"]}

        # ── Persist results to PostgreSQL ─────────────────────────────────────

        # Repository context
        if final_state.get("repository_context"):
            ctx_data = final_state["repository_context"]
            ctx = RepositoryContext(
                scan_id=scan.id,
                languages=ctx_data.get("languages", []),
                frameworks=ctx_data.get("frameworks", []),
                databases=ctx_data.get("databases", []),
                authentication=ctx_data.get("authentication", []),
                file_tree_summary=ctx_data.get("file_tree_summary"),
                architecture_summary=ctx_data.get("architecture_summary"),
                raw_context=ctx_data.get("raw_context", {}),
            )
            db.add(ctx)
            db.flush()

        # Findings + analyses + remediation
        finding_db_objects: dict[str, Finding] = {}
        finding_analyses_data = final_state.get("finding_analyses") or []
        remediation_data = {
            r["finding_key"]: r
            for r in (final_state.get("remediation_suggestions") or [])
        }

        for item in finding_analyses_data:
            finding = Finding(
                scan_id=scan.id,
                finding_key=item["finding_key"],
                tool=item["tool"],
                finding_type=item["finding_type"],
                severity=item["severity"],
                file_path=item["file_path"],
                line_start=item.get("line_start"),
                line_end=item.get("line_end"),
                message=item["message"],
                rule_id=item.get("rule_id"),
                code_snippet=item.get("code_snippet"),
                raw_output=item.get("raw_output", {}),
            )
            db.add(finding)
            db.flush()
            finding_db_objects[item["finding_key"]] = finding

            # Finding analysis
            analysis = FindingAnalysis(
                finding_id=finding.id,
                is_true_positive=item.get("is_true_positive"),
                exploitability=item.get("exploitability"),
                impact=item.get("impact"),
                confidence=item.get("confidence"),
                exposure=item.get("exposure"),
                business_impact=item.get("business_impact"),
                risk_score=item.get("risk_score"),
                root_cause=item.get("root_cause"),
                attack_scenario=item.get("attack_scenario"),
                ai_explanation=item.get("ai_explanation"),
                owasp_refs=item.get("owasp_refs", []),
                cwe_refs=item.get("cwe_refs", []),
                security_recommendations=item.get("security_recommendations"),
            )
            db.add(analysis)

            # Remediation suggestion
            remedy = remediation_data.get(item["finding_key"])
            if remedy and not remedy.get("is_false_positive"):
                suggestion = RemediationSuggestion(
                    finding_id=finding.id,
                    suggested_fix=remedy.get("suggested_fix"),
                    secure_coding_guidance=remedy.get("secure_coding_guidance"),
                    fix_explanation=remedy.get("fix_explanation"),
                )
                db.add(suggestion)

        db.flush()

        # T-091: Security Memory — compute finding diff with previous scan
        previous_scan = (
            db.query(Scan)
            .filter(
                Scan.repository_id == scan.repository_id,
                Scan.status == ScanStatus.COMPLETED,
                Scan.id != scan.id,
            )
            .order_by(Scan.created_at.desc())
            .first()
        )

        if previous_scan:
            prev_keys = {f.finding_key for f in previous_scan.findings}
            curr_keys = set(finding_db_objects.keys())
            diff = finding_differ.compute_diff(curr_keys, prev_keys)

            for key, status in diff.items():
                finding_obj = finding_db_objects.get(key)
                if finding_obj:
                    history = FindingHistory(
                        finding_id=finding_obj.id,
                        scan_id=scan.id,
                        history_status=HistoryStatus(status),
                    )
                    db.add(history)
        else:
            # First scan: all findings are "new"
            for finding_obj in finding_db_objects.values():
                history = FindingHistory(
                    finding_id=finding_obj.id,
                    scan_id=scan.id,
                    history_status=HistoryStatus.NEW,
                )
                db.add(history)

        # Persist policy result
        gate_data = final_state.get("policy_result") or {}
        gate_value = gate_data.get("gate", "pass")
        gate_enum = GateResult(gate_value)

        policy_db = PolicyResult(
            scan_id=scan.id,
            gate_result=gate_enum,
            triggered_rules=gate_data.get("triggered_rules", []),
            findings_summary=gate_data.get("findings_summary", {}),
        )
        db.add(policy_db)

        # Compute overall security score (inverse of average risk score, normalized)
        risk_scores = [
            float(item.get("risk_score", 50))
            for item in finding_analyses_data
            if item.get("is_true_positive", True)
        ]
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            security_score = max(0, round(100 - avg_risk, 2))
        else:
            security_score = 100.0  # No findings = perfect score

        scan.status = ScanStatus.COMPLETED
        scan.security_score = security_score
        scan.gate_result = gate_enum
        db.commit()

        logger.info(
            "Scan completed",
            scan_id=scan_id,
            findings=len(finding_analyses_data),
            gate=gate_value,
            score=security_score,
        )

        # T-103/T-106: Update GitHub Check Run and post PR comment
        if scan.scan_type.value == "pr" and scan.pr_number:
            try:
                from app.services.github_service import (
                    update_github_check_run,
                    post_github_pr_comment,
                )
                dashboard_url = f"{settings.FRONTEND_URL}/scans/{scan_id}"
                update_github_check_run(
                    repo_full_name=repo.full_name,
                    check_run_id=scan.github_check_run_id,
                    gate_result=gate_value,
                    summary=f"Security scan: {gate_value.upper()} — {len(finding_analyses_data)} finding(s)",
                    details_url=dashboard_url,
                    token=repo.github_access_token,
                )
                post_github_pr_comment(
                    repo_full_name=repo.full_name,
                    pr_number=scan.pr_number,
                    gate_result=gate_value,
                    findings_summary=gate_data.get("findings_summary", {}),
                    dashboard_url=dashboard_url,
                    token=repo.github_access_token,
                )
            except Exception as e:
                logger.warning("Failed to update GitHub PR", error=str(e))

        return {"scan_id": scan_id, "status": "completed", "gate": gate_value}

    except Exception as e:
        logger.error("Scan task failed unexpectedly", scan_id=scan_id, error=str(e), exc_info=True)
        if db:
            scan_obj = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
            if scan_obj:
                _mark_failed(db, scan_obj, str(e))
        raise
    finally:
        db.close()
        if clone_dir and os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, ignore_errors=True)


def _mark_failed(db, scan: Scan, error_msg: str) -> None:
    """Mark a scan as failed with error message."""
    scan.status = ScanStatus.FAILED
    scan.error_message = error_msg[:4000]
    db.commit()
    logger.error("Scan marked as failed", scan_id=str(scan.id), error=error_msg[:200])
