"""Patch validation routes — T-081, T-082."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Finding, RemediationSuggestion
from app.models.remediation_suggestion import ValidationStatus

router = APIRouter()


@router.post("/findings/{finding_id}/validate", summary="Trigger patch validation — T-081")
async def trigger_patch_validation(finding_id: str, db: Session = Depends(get_db)) -> dict:
    """Enqueue patch validation as async Celery task and return task ID."""
    from workers.tasks.validation_tasks import validate_patch

    finding = db.query(Finding).filter(Finding.id == uuid.UUID(finding_id)).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    if not finding.remediation or not finding.remediation.suggested_fix:
        raise HTTPException(status_code=400, detail="No suggested fix available for this finding")

    # Mark as pending
    finding.remediation.validation_status = ValidationStatus.PENDING
    db.commit()

    task = validate_patch.apply_async(
        kwargs={
            "finding_id": finding_id,
            "suggestion_id": str(finding.remediation.id),
        },
        queue="validations",
    )
    finding.remediation.validation_celery_task_id = task.id
    db.commit()

    return {"task_id": task.id, "finding_id": finding_id, "status": "pending"}


@router.get("/validations/{task_id}", summary="Get validation status — T-082")
async def get_validation_status(task_id: str) -> dict:
    """Return current patch validation task status."""
    from workers.celery_app import celery_app
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
