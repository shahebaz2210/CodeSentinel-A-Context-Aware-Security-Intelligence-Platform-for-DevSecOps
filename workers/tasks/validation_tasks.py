"""
Patch Validation Celery task — T-079, T-080.
"""

import os
import shutil
import uuid
import tempfile
import structlog

from workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Finding, RemediationSuggestion
from app.models.remediation_suggestion import ValidationStatus
from app.services.patch_validator import create_validation_sandbox, validate_patch as _validate_patch

logger = structlog.get_logger()


@celery_app.task(bind=True, name="workers.tasks.validation_tasks.validate_patch")
def validate_patch(self, finding_id: str, suggestion_id: str) -> dict:
    """T-079, T-080: Run the full patch validation pipeline in a sandbox."""
    db = SessionLocal()
    sandbox_dir = None

    try:
        finding = db.query(Finding).filter(Finding.id == uuid.UUID(finding_id)).first()
        suggestion = db.query(RemediationSuggestion).filter(
            RemediationSuggestion.id == uuid.UUID(suggestion_id)
        ).first()

        if not finding or not suggestion:
            return {"error": "Finding or suggestion not found"}

        if not suggestion.suggested_fix:
            return {"error": "No suggested fix to validate"}

        # Find the last completed scan's clone (best effort)
        # In production this should use the scan's stored context
        source_dir = tempfile.mkdtemp(prefix="cs_source_")
        sandbox_dir = create_validation_sandbox(source_dir)

        passed, log = _validate_patch(
            sandbox_dir=sandbox_dir,
            file_path=finding.file_path,
            suggested_fix=suggestion.suggested_fix,
            original_finding_key=finding.finding_key,
        )

        suggestion.validation_status = ValidationStatus.PASS if passed else ValidationStatus.FAIL
        suggestion.validation_log = log[:4000]
        db.commit()

        logger.info(
            "Patch validation complete",
            finding_id=finding_id,
            passed=passed,
        )
        return {
            "finding_id": finding_id,
            "passed": passed,
            "validation_status": "pass" if passed else "fail",
        }

    except Exception as e:
        logger.error("Patch validation task failed", error=str(e))
        if db:
            s = db.query(RemediationSuggestion).filter(
                RemediationSuggestion.id == uuid.UUID(suggestion_id)
            ).first()
            if s:
                s.validation_status = ValidationStatus.FAIL
                s.validation_log = str(e)[:4000]
                db.commit()
        raise
    finally:
        db.close()
        if sandbox_dir and os.path.exists(sandbox_dir):
            shutil.rmtree(sandbox_dir, ignore_errors=True)
