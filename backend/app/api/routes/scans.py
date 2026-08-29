"""Scan management routes — T-027, T-028, T-108, T-110, T-111."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Scan, Repository, Finding, FindingAnalysis, FindingHistory
from app.models.scan import ScanType, ScanStatus
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/scans", summary="Create and enqueue a new scan — T-027")
async def create_scan(
    repo_id: str,
    scan_type: str = "repo",
    pr_number: int | None = None,
    git_ref: str | None = None,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> dict:
    """Create a Scan record and enqueue the Celery scan task."""
    from workers.tasks.scan_tasks import run_security_scan

    repo = db.query(Repository).filter(Repository.id == uuid.UUID(repo_id)).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scan = Scan(
        repository_id=repo.id,
        scan_type=ScanType(scan_type),
        status=ScanStatus.PENDING,
        pr_number=pr_number,
        git_ref=git_ref,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Enqueue async Celery task
    task = run_security_scan.apply_async(
        kwargs={"scan_id": str(scan.id)},
        queue="scans",
    )
    scan.celery_task_id = task.id
    db.commit()

    logger.info("Scan created and enqueued", scan_id=str(scan.id), task_id=task.id)
    return {
        "scan_id": str(scan.id),
        "status": scan.status.value,
        "celery_task_id": task.id,
    }


@router.get("/scans/{scan_id}", summary="Poll scan status — T-028")
async def get_scan(scan_id: str, db: Session = Depends(get_db)) -> dict:
    """Return current scan status and metadata."""
    scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "scan_id": str(scan.id),
        "repository_id": str(scan.repository_id),
        "scan_type": scan.scan_type.value,
        "status": scan.status.value,
        "pr_number": scan.pr_number,
        "git_ref": scan.git_ref,
        "security_score": float(scan.security_score) if scan.security_score else None,
        "gate_result": scan.gate_result.value if scan.gate_result else None,
        "error_message": scan.error_message,
        "started_at": scan.created_at.isoformat(),
        "completed_at": scan.updated_at.isoformat() if scan.status == ScanStatus.COMPLETED else None,
    }


@router.get("/scans/{scan_id}/findings", summary="Get all findings for a scan — T-108")
async def get_scan_findings(scan_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Return normalized findings sorted by severity with analysis and history joined."""
    scan = db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings = sorted(scan.findings, key=lambda f: severity_order.get(f.severity.value, 99))

    result = []
    for f in findings:
        history_status = None
        if f.history:
            latest = max(f.history, key=lambda h: h.created_at)
            history_status = latest.history_status.value

        result.append({
            "id": str(f.id),
            "finding_type": f.finding_type,
            "tool": f.tool.value,
            "severity": f.severity.value,
            "file_path": f.file_path,
            "line_start": f.line_start,
            "line_end": f.line_end,
            "message": f.message,
            "code_snippet": f.code_snippet,
            "history_status": history_status,
            "risk_score": float(f.analysis.risk_score) if f.analysis and f.analysis.risk_score else None,
        })
    return result


@router.get("/repos/{repo_id}/scans", summary="List scans for a repository — T-110")
async def list_repo_scans(
    repo_id: str, page: int = 1, limit: int = 20, db: Session = Depends(get_db)
) -> dict:
    """Return paginated scan history for a repository."""
    offset = (page - 1) * limit
    scans = (
        db.query(Scan)
        .filter(Scan.repository_id == uuid.UUID(repo_id))
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(Scan).filter(Scan.repository_id == uuid.UUID(repo_id)).count()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "scans": [
            {
                "scan_id": str(s.id),
                "scan_type": s.scan_type.value,
                "status": s.status.value,
                "security_score": float(s.security_score) if s.security_score else None,
                "gate_result": s.gate_result.value if s.gate_result else None,
                "started_at": s.created_at.isoformat(),
                "completed_at": s.updated_at.isoformat() if s.status == ScanStatus.COMPLETED else None,
            }
            for s in scans
        ],
    }


@router.get("/repos/{repo_id}/latest-scan", summary="Get latest completed scan — T-111")
async def get_latest_scan(repo_id: str, db: Session = Depends(get_db)) -> dict | None:
    """Return the most recent completed scan for a repository."""
    scan = (
        db.query(Scan)
        .filter(
            Scan.repository_id == uuid.UUID(repo_id),
            Scan.status == ScanStatus.COMPLETED,
        )
        .order_by(Scan.created_at.desc())
        .first()
    )
    if not scan:
        return None
    return {
        "scan_id": str(scan.id),
        "scan_type": scan.scan_type.value,
        "security_score": float(scan.security_score) if scan.security_score else None,
        "gate_result": scan.gate_result.value if scan.gate_result else None,
        "completed_at": scan.updated_at.isoformat(),
    }


@router.get("/repos/{repo_id}/trends", summary="Security score trends — T-093")
async def get_repo_trends(repo_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Return per-scan aggregated stats ordered by scan date for trend charts."""
    scans = (
        db.query(Scan)
        .filter(
            Scan.repository_id == uuid.UUID(repo_id),
            Scan.status == ScanStatus.COMPLETED,
        )
        .order_by(Scan.created_at.asc())
        .all()
    )
    result = []
    for s in scans:
        new_count = sum(
            1 for f in s.findings
            if any(h.history_status.value == "new" for h in f.history)
        )
        resolved_count = sum(
            1 for f in s.findings
            if any(h.history_status.value == "resolved" for h in f.history)
        )
        recurring_count = sum(
            1 for f in s.findings
            if any(h.history_status.value == "recurring" for h in f.history)
        )
        result.append({
            "scan_id": str(s.id),
            "date": s.created_at.isoformat(),
            "security_score": float(s.security_score) if s.security_score else None,
            "gate_result": s.gate_result.value if s.gate_result else None,
            "new_findings": new_count,
            "resolved_findings": resolved_count,
            "recurring_findings": recurring_count,
            "total_findings": len(s.findings),
        })
    return result
