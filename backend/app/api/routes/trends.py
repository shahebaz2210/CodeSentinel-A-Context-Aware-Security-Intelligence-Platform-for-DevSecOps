"""
Trends endpoint — T-093.
Returns per-scan aggregated security counts for dashboard trend charts.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models import Repository, Scan, Finding, FindingHistory
from app.models.scan import ScanStatus
from app.models.finding_history import HistoryStatus
from app.api.schemas import TrendItem
import structlog

router = APIRouter(prefix="/api/repos", tags=["repos"])
logger = structlog.get_logger()


@router.get("/{repo_id}/trends", response_model=list[TrendItem])
def get_repo_trends(
    repo_id: UUID,
    limit: int = 30,
    db: Session = Depends(get_db),
) -> list[TrendItem]:
    """
    T-093: Per-scan aggregated counts (new, resolved, recurring, score)
    ordered by scan date for dashboard trend charts.
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scans = (
        db.query(Scan)
        .filter(
            Scan.repository_id == repo_id,
            Scan.status == ScanStatus.COMPLETED,
        )
        .order_by(Scan.created_at.asc())
        .limit(limit)
        .all()
    )

    result = []
    for scan in scans:
        # Count findings by history status
        counts = (
            db.query(FindingHistory.history_status, func.count(FindingHistory.id))
            .join(Finding, Finding.id == FindingHistory.finding_id)
            .filter(FindingHistory.scan_id == scan.id)
            .group_by(FindingHistory.history_status)
            .all()
        )
        count_map = {str(status.value): cnt for status, cnt in counts}
        total = sum(count_map.values())

        result.append(
            TrendItem(
                scan_id=scan.id,
                date=scan.created_at,
                security_score=scan.security_score,
                gate_result=scan.gate_result.value if scan.gate_result else None,
                new_findings=count_map.get("new", 0),
                resolved_findings=count_map.get("resolved", 0),
                recurring_findings=count_map.get("recurring", 0),
                total_findings=total,
            )
        )

    return result


@router.get("/{repo_id}/latest-scan")
def get_latest_scan(
    repo_id: UUID,
    db: Session = Depends(get_db),
) -> dict | None:
    """T-111: Return the most recent completed scan for a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scan = (
        db.query(Scan)
        .filter(
            Scan.repository_id == repo_id,
            Scan.status == ScanStatus.COMPLETED,
        )
        .order_by(Scan.created_at.desc())
        .first()
    )

    if not scan:
        return None

    return {
        "scan_id": str(scan.id),
        "repository_id": str(scan.repository_id),
        "scan_type": scan.scan_type.value,
        "status": scan.status.value,
        "security_score": float(scan.security_score) if scan.security_score else None,
        "gate_result": scan.gate_result.value if scan.gate_result else None,
        "started_at": scan.created_at.isoformat() if scan.created_at else None,
        "completed_at": scan.updated_at.isoformat() if scan.updated_at else None,
    }
