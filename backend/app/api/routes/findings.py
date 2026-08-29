"""Finding detail routes — T-109."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Finding

router = APIRouter()


@router.get("/findings/{finding_id}", summary="Full finding detail — T-109")
async def get_finding(finding_id: str, db: Session = Depends(get_db)) -> dict:
    """Return complete finding detail including AI analysis and remediation."""
    finding = db.query(Finding).filter(Finding.id == uuid.UUID(finding_id)).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    history_status = None
    if finding.history:
        latest = max(finding.history, key=lambda h: h.created_at)
        history_status = latest.history_status.value

    analysis = finding.analysis
    remediation = finding.remediation

    return {
        "id": str(finding.id),
        "scan_id": str(finding.scan_id),
        "finding_key": finding.finding_key,
        "tool": finding.tool.value,
        "finding_type": finding.finding_type,
        "severity": finding.severity.value,
        "file_path": finding.file_path,
        "line_start": finding.line_start,
        "line_end": finding.line_end,
        "message": finding.message,
        "rule_id": finding.rule_id,
        "code_snippet": finding.code_snippet,
        "history_status": history_status,
        # Risk analysis
        "risk_score": float(analysis.risk_score) if analysis and analysis.risk_score else None,
        "confidence": float(analysis.confidence) if analysis and analysis.confidence else None,
        "is_true_positive": analysis.is_true_positive if analysis else None,
        # AI analysis (from Agent 3 / Security Intelligence)
        "root_cause": analysis.root_cause if analysis else None,
        "attack_scenario": analysis.attack_scenario if analysis else None,
        "ai_explanation": analysis.ai_explanation if analysis else None,
        "owasp_refs": analysis.owasp_refs if analysis else [],
        "cwe_refs": analysis.cwe_refs if analysis else [],
        "security_recommendations": analysis.security_recommendations if analysis else None,
        # Remediation (from Agent 5)
        "suggested_fix": remediation.suggested_fix if remediation else None,
        "secure_coding_guidance": remediation.secure_coding_guidance if remediation else None,
        "fix_explanation": remediation.fix_explanation if remediation else None,
        "validation_status": remediation.validation_status.value if remediation else None,
    }
