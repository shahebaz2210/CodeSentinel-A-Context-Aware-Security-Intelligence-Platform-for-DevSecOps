"""GitHub Webhook receiver — T-095, T-096, T-097, T-098."""

import hashlib
import hmac
from fastapi import APIRouter, Request, HTTPException, Header
from app.core.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter()


def verify_github_webhook_signature(payload_bytes: bytes, signature_header: str | None, secret: str) -> bool:
    """T-096: Verify GitHub webhook HMAC-SHA256 signature."""
    if not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@router.post("/github", summary="Receive GitHub webhook events — T-095")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
) -> dict:
    """T-095: Receive and verify GitHub webhook payloads."""
    payload_bytes = await request.body()

    # T-096: Verify webhook signature
    if not verify_github_webhook_signature(
        payload_bytes, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET
    ):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Webhook signature verification failed")

    # T-097: Only process pull_request events
    if x_github_event != "pull_request":
        return {"status": "ignored", "event": x_github_event}

    payload = await request.json()
    action = payload.get("action")
    if action not in ("opened", "synchronize"):
        return {"status": "ignored", "action": action}

    # T-098: Extract PR info and create scan
    from app.db.session import SessionLocal
    from app.models import Repository, Scan
    from app.models.scan import ScanType, ScanStatus
    from workers.tasks.scan_tasks import run_security_scan
    import uuid

    pr = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})

    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(
            Repository.github_id == repo_data["id"]
        ).first()

        if not repo:
            logger.warning("Webhook received for unregistered repo", repo=repo_data.get("full_name"))
            return {"status": "ignored", "reason": "repository_not_registered"}

        scan = Scan(
            repository_id=repo.id,
            scan_type=ScanType.PR,
            status=ScanStatus.PENDING,
            pr_number=pr.get("number"),
            git_ref=pr.get("head", {}).get("sha"),
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        task = run_security_scan.apply_async(
            kwargs={"scan_id": str(scan.id)},
            queue="scans",
        )
        scan.celery_task_id = task.id
        db.commit()

        logger.info("PR scan created from webhook", scan_id=str(scan.id), pr=pr.get("number"))
        return {"status": "accepted", "scan_id": str(scan.id)}
    finally:
        db.close()
